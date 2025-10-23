"""Wind ordinance structured parsing class"""

import asyncio
import logging
from copy import deepcopy
from itertools import chain
from warnings import warn

import pandas as pd

from compass.llm.calling import BaseLLMCaller, ChatLLMCaller
from compass.extraction.features import SetbackFeatures
from compass.common import (
    EXTRACT_ORIGINAL_TEXT_PROMPT,
    run_async_tree,
    run_async_tree_with_bm,
    empty_output,
    setup_async_decision_tree,
    setup_base_setback_graph,
    setup_participating_owner,
    setup_graph_extra_restriction,
    setup_graph_permitted_use_districts,
)
from compass.extraction.wind.graphs import (
    WES_SYSTEM_SIZE_REMINDER,
    setup_graph_wes_types,
    setup_multiplier,
    setup_conditional_min,
    setup_conditional_max,
)
from compass.utilities.enums import LLMUsageCategory
from compass.warn import COMPASSWarning
from compass.pb import COMPASS_PB


logger = logging.getLogger(__name__)
DEFAULT_SYSTEM_MESSAGE = (
    "You are a legal scholar informing a wind energy developer about local "
    "zoning ordinances."
)
SETBACKS_SYSTEM_MESSAGE = (
    f"{DEFAULT_SYSTEM_MESSAGE} "
    "For the duration of this conversation, only focus on ordinances "
    "relating to setbacks from {feature}; do not respond based on any text "
    "related to {ignore_features}. "
    f"Please only consider ordinances for {WES_SYSTEM_SIZE_REMINDER}"
)
RESTRICTIONS_SYSTEM_MESSAGE = (
    f"{DEFAULT_SYSTEM_MESSAGE} "
    "For the duration of this conversation, only focus on "
    "ordinances relating to {restriction} for "
    f"{WES_SYSTEM_SIZE_REMINDER}"
)
PERMITTED_USE_SYSTEM_MESSAGE = (
    f"{DEFAULT_SYSTEM_MESSAGE} "
    "For the duration of this conversation, only focus on permitted uses for "
    f"{WES_SYSTEM_SIZE_REMINDER}"
)
EXTRA_NUMERICAL_RESTRICTIONS = {
    "other wecs": (
        "**minimum** required separation distance with other existing or "
        "planned wind energy conversion systems"
    ),
    "noise": "maximum noise level allowed",
    "maximum height": "maximum turbine height allowed",
    "maximum project size": (
        "maximum project size or total installation allowed"
    ),
    "minimum lot size": "**minimum** lot, parcel, or tract size allowed",
    "maximum lot size": "**maximum** lot, parcel, or tract size allowed",
    "shadow flicker": "maximum shadow flicker allowed",
    "tower density": "**minimum** allowed spacing between individual turbines",
    "blade clearance": "minimum blade clearance allowed",
}
EXTRA_QUALITATIVE_RESTRICTIONS = {
    "color": "color or finish requirements",
    "decommissioning": "decommissioning requirements",
    "lighting": "lighting requirements",
    "prohibitions": "prohibitions, moratoria, or bans",
    "visual impact": "visual impact **assessment** requirements",
    "repowering": (
        "requirements or regulations specific to **repowering** of the system"
    ),
    "climbing prevention": "climbing prevention requirements",
    "signage": "signage requirements",
    "soil": "soil, erosion, and/or sediment control requirements",
}
UNIT_CLARIFICATIONS = {
    "noise": (
        "For the purposes of this extraction, assume the standard units "
        "for noise are 'dBA'."
    ),
    "shadow flicker": (
        "For the purposes of this extraction, assume the standard units "
        "for shadow flicker are 'hr/year'."
    ),
    "tower density": (
        "For the purposes of this extraction, assume the standard units "
        "for spacing between individual turbines are one of the following: "
        "'tip-height-multiplier', 'hub-height-multiplier', "
        "'rotor-diameter-multiplier', 'feet', or 'meters'."
    ),
    "minimum lot size": (
        "Minimum lot size should **always** be specified as an area value."
    ),
    "maximum lot size": (
        "Maximum lot size should **always** be specified as an area value."
    ),
}
ER_CLARIFICATIONS = {
    "maximum project size": (
        "Maximum project size is typically specified as a maximum system "
        "size value or as a maximum number of turbines."
    ),
    "shadow flicker": (
        "If the text prohibits shadow, treat this as a max value of 0 "
        "hours per year."
    ),
    "tower density": (
        "Do **not** try to infer the spacing requirement based on other "
        "restrictions such as setbacks from facility perimeters, property "
        "lines, etc."
    ),
}
_FEATURE_TO_OWNED_TYPE = {
    "structures": "structure",
    "property line": "property",
}


class StructuredWindParser(BaseLLMCaller):
    """Base class for parsing structured data"""

    def _init_chat_llm_caller(self, system_message):
        """Initialize a ChatLLMCaller instance for the DecisionTree"""
        return ChatLLMCaller(
            self.llm_service,
            system_message=system_message,
            usage_tracker=self.usage_tracker,
            **self.kwargs,
        )

    async def _check_wind_turbine_type(self, text):
        """Get the largest turbine size mentioned in the text"""
        logger.info("Checking turbine types...")
        tree = setup_async_decision_tree(
            setup_graph_wes_types,
            text=text,
            chat_llm_caller=self._init_chat_llm_caller(DEFAULT_SYSTEM_MESSAGE),
        )
        decision_tree_wes_types_out = await run_async_tree(tree)

        largest_system = (
            decision_tree_wes_types_out.get("largest_wes_type")
            or "**large** wind energy systems"
        )
        if not decision_tree_wes_types_out.get("is_large", True):
            logger.info(
                "Did not find utility-scale systems in text. Largest "
                "system found: %r",
                largest_system,
            )
            return None

        logger.info("Largest WES type found in text: %r", largest_system)
        return largest_system


class StructuredWindOrdinanceParser(StructuredWindParser):
    """LLM ordinance document structured data scraping utility

    Purpose:
        Extract structured ordinance data from text.
    Responsibilities:
        1. Extract ordinance values into structured format by executing
           a decision-tree-based chain-of-thought prompt on the text for
           each value to be extracted.
    Key Relationships:
        Uses a StructuredLLMCaller for LLM queries and multiple
        AsyncDecisionTree instances to guide the extraction of
        individual values.
    """

    async def parse(self, text):
        """Parse text and extract structure ordinance data

        Parameters
        ----------
        text : str
            Ordinance text which may or may not contain setbacks for one
            or more features (property lines, structure, roads, etc.).
            Text can also contain other supported regulations (noise,
            shadow-flicker, etc,) which will be extracted as well.

        Returns
        -------
        pandas.DataFrame or None
            DataFrame containing parsed-out ordinance values. Can also
            be ``None`` if a large wind energy system is not found in
            the text.
        """
        largest_wes_type = await self._check_wind_turbine_type(text)
        if not largest_wes_type:
            return None

        outer_task_name = asyncio.current_task().get_name()
        num_to_process = (
            len(SetbackFeatures.DEFAULT_FEATURE_DESCRIPTIONS)
            + len(EXTRA_NUMERICAL_RESTRICTIONS)
            + len(EXTRA_QUALITATIVE_RESTRICTIONS)
        )
        with COMPASS_PB.jurisdiction_sub_prog_bar(outer_task_name) as sub_pb:
            task_id = sub_pb.add_task(
                "Extracting ordinance values...",
                total=num_to_process,
                just_parsed="",
            )
            outputs = await self._parse_all_restrictions_with_pb(
                sub_pb, task_id, text, largest_wes_type, outer_task_name
            )
            sub_pb.update(task_id, completed=num_to_process)
            await asyncio.sleep(1)
            sub_pb.remove_task(task_id)

        return pd.DataFrame(chain.from_iterable(outputs))

    async def _parse_all_restrictions_with_pb(
        self, sub_pb, task_id, text, largest_wes_type, outer_task_name
    ):
        """Parse all ordinance values"""
        feature_parsers = [
            asyncio.create_task(
                self._parse_setback_feature(
                    sub_pb, task_id, text, feature_kwargs, largest_wes_type
                ),
                name=outer_task_name,
            )
            for feature_kwargs in SetbackFeatures()
        ]
        extras_parsers = [
            asyncio.create_task(
                self._parse_extra_restriction(
                    sub_pb,
                    task_id,
                    text,
                    feature_id,
                    r_text,
                    largest_wes_type,
                    is_numerical=True,
                    unit_clarification=UNIT_CLARIFICATIONS.get(feature_id, ""),
                    feature_clarifications=ER_CLARIFICATIONS.get(
                        feature_id, ""
                    ),
                ),
                name=outer_task_name,
            )
            for feature_id, r_text in EXTRA_NUMERICAL_RESTRICTIONS.items()
        ]
        extras_parsers += [
            asyncio.create_task(
                self._parse_extra_restriction(
                    sub_pb,
                    task_id,
                    text,
                    feature_id,
                    r_text,
                    largest_wes_type,
                    is_numerical=False,
                    feature_clarifications=ER_CLARIFICATIONS.get(
                        feature_id, ""
                    ),
                ),
                name=outer_task_name,
            )
            for feature_id, r_text in EXTRA_QUALITATIVE_RESTRICTIONS.items()
        ]
        return await asyncio.gather(*(feature_parsers + extras_parsers))

    async def _parse_extra_restriction(
        self,
        sub_pb,
        task_id,
        text,
        feature_id,
        restriction_text,
        largest_wes_type,
        is_numerical,
        unit_clarification="",
        feature_clarifications="",
    ):
        """Parse a non-setback restriction from the text"""
        logger.debug("Parsing extra feature %r", feature_id)
        system_message = RESTRICTIONS_SYSTEM_MESSAGE.format(
            restriction=restriction_text, tech=largest_wes_type
        )
        tree = setup_async_decision_tree(
            setup_graph_extra_restriction,
            usage_sub_label=LLMUsageCategory.ORDINANCE_VALUE_EXTRACTION,
            is_numerical=is_numerical,
            tech=largest_wes_type,
            feature_id=feature_id,
            restriction=restriction_text,
            text=text,
            chat_llm_caller=self._init_chat_llm_caller(system_message),
            unit_clarification=unit_clarification,
            feature_clarifications=feature_clarifications,
        )
        info = await run_async_tree(tree)
        info.update({"feature": feature_id, "quantitative": is_numerical})
        if is_numerical:
            info = _sanitize_output(info)
        sub_pb.update(task_id, advance=1, just_parsed=feature_id)
        return [info]

    async def _parse_setback_feature(
        self, sub_pb, task_id, text, feature_kwargs, largest_wes_type
    ):
        """Parse values for a setback feature"""
        feature_id = feature_kwargs["feature_id"]
        feature_kwargs["tech"] = largest_wes_type
        logger.debug("Parsing feature %r", feature_id)

        out, base_messages = await self._base_messages(text, **feature_kwargs)
        if not out:
            logger.debug("Did not find ordinance for feature %r", feature_id)
            sub_pb.update(task_id, advance=1, just_parsed=feature_id)
            return empty_output(feature_id)

        if feature_id not in {"structures", "property line"}:
            output = {"feature": feature_id}
            output.update(
                await self._extract_setback_values(
                    text,
                    base_messages=base_messages,
                    **feature_kwargs,
                )
            )
            sub_pb.update(task_id, advance=1, just_parsed=feature_id)
            return [output]

        output = await self._extract_setback_values_for_p_or_np(
            text, base_messages, **feature_kwargs
        )
        sub_pb.update(task_id, advance=1, just_parsed=feature_id)
        return output

    async def _base_messages(self, text, **feature_kwargs):
        """Get base messages for setback feature parsing"""
        system_message = SETBACKS_SYSTEM_MESSAGE.format(**feature_kwargs)
        tree = setup_async_decision_tree(
            setup_base_setback_graph,
            usage_sub_label=LLMUsageCategory.ORDINANCE_VALUE_EXTRACTION,
            text=text,
            chat_llm_caller=self._init_chat_llm_caller(system_message),
            **feature_kwargs,
        )
        out = await run_async_tree(tree, response_as_json=False)
        return out, deepcopy(tree.chat_llm_caller.messages)

    async def _extract_setback_values_for_p_or_np(
        self, text, base_messages, feature_id, **feature_kwargs
    ):
        """Extract setback values for participating ordinances"""
        logger.debug("Checking participating vs non-participating")
        p_np_text = {"participating": "", "non-participating": text}
        decision_tree_participating_out = await self._run_setback_graph(
            setup_participating_owner,
            text,
            base_messages=deepcopy(base_messages),
            owned_type=_FEATURE_TO_OWNED_TYPE[feature_id],
            **feature_kwargs,
        )
        p_np_text.update(decision_tree_participating_out)
        outer_task_name = asyncio.current_task().get_name()
        p_or_np_parsers = [
            asyncio.create_task(
                self._parse_p_or_np_text(
                    key, sub_text, base_messages, feature_id, **feature_kwargs
                ),
                name=outer_task_name,
            )
            for key, sub_text in p_np_text.items()
        ]
        return await asyncio.gather(*p_or_np_parsers)

    async def _parse_p_or_np_text(
        self, p_or_np, sub_text, base_messages, feature_id, **feature_kwargs
    ):
        """Parse participating sub-text for ord values"""
        out_feat_name = f"{feature_id} ({p_or_np})"
        output = {"feature": out_feat_name}
        if not sub_text:
            return output

        feature = feature_kwargs["feature"]
        if (
            p_or_np == "participating"
            or "non-participating"
            in sub_text.casefold().replace("\n", "").replace(" ", "-")
        ):
            feature = f"**{p_or_np}** {feature}"
            feature_kwargs["feature"] = feature

        base_messages = deepcopy(base_messages)
        base_messages[-2]["content"] = EXTRACT_ORIGINAL_TEXT_PROMPT.format(
            feature=feature,
            tech=feature_kwargs["tech"],
            ignore_features=feature_kwargs["ignore_features"],
            feature_clarifications=feature_kwargs.get(
                "feature_clarifications", ""
            ),
        )
        base_messages[-1]["content"] = sub_text

        values = await self._extract_setback_values(
            sub_text,
            base_messages=base_messages,
            **feature_kwargs,
        )
        output.update(values)
        return output

    async def _extract_setback_values(self, text, base_messages, **kwargs):
        """Extract setback values for a given feature from input text"""
        decision_tree_out = await self._run_setback_graph(
            setup_multiplier, text, deepcopy(base_messages), **kwargs
        )
        decision_tree_out = _update_output_keys(decision_tree_out)
        decision_tree_out = _sanitize_output(decision_tree_out)

        if decision_tree_out.get("value") is None:
            return decision_tree_out

        decision_tree_conditional_min_out = await self._run_setback_graph(
            setup_conditional_min, text, deepcopy(base_messages), **kwargs
        )
        decision_tree_out.update(decision_tree_conditional_min_out)
        decision_tree_conditional_max_out = await self._run_setback_graph(
            setup_conditional_max, text, deepcopy(base_messages), **kwargs
        )
        decision_tree_out.update(decision_tree_conditional_max_out)
        return decision_tree_out

    async def _run_setback_graph(
        self, graphs_setup_func, text, base_messages=None, **kwargs
    ):
        """Generic function to run async tree"""
        system_message = SETBACKS_SYSTEM_MESSAGE.format(**kwargs)
        tree = setup_async_decision_tree(
            graphs_setup_func,
            usage_sub_label=LLMUsageCategory.ORDINANCE_VALUE_EXTRACTION,
            text=text,
            chat_llm_caller=self._init_chat_llm_caller(system_message),
            **kwargs,
        )
        if base_messages:
            return await run_async_tree_with_bm(tree, base_messages)
        return await run_async_tree(tree)


class StructuredWindPermittedUseDistrictsParser(StructuredWindParser):
    """LLM permitted use districts  scraping utility

    Purpose:
        Extract structured ordinance data from text.
    Responsibilities:
        1. Extract ordinance values into structured format by executing
           a decision-tree-based chain-of-thought prompt on the text for
           each value to be extracted.
    Key Relationships:
        Uses a StructuredLLMCaller for LLM queries and multiple
        AsyncDecisionTree instances to guide the extraction of
        individual values.
    """

    _LARGE_WES_CLARIFICATION = (
        "Large wind energy systems (WES) may also be referred to as wind "
        "turbines, wind energy conversion systems (WECS), wind energy "
        "facilities (WEF), wind energy turbines (WET), large wind energy "
        "turbines (LWET), utility-scale wind energy turbines (UWET), "
        "commercial wind energy conversion systems (CWECS), alternate "
        "energy systems (AES), commercial energy production systems (CEPCS), "
        "or similar"
    )
    _USE_TYPES = [
        {
            "feature_id": "primary use districts",
            "use_type": (
                "permitted as primary use or similar (e.g., without special "
                "conditions or approval)"
            ),
            "clarifications": (
                "Consider any solar overlay districts as "
                "primary use districts. {wes_clarification}"
            ),
        },
        {
            "feature_id": "special use districts",
            "use_type": (
                "permitted as special use or similar (e.g., requires approval "
                "by the zoning appeals board or meeting certain conditions "
                "like completing a permitting process)"
            ),
            "clarifications": (
                "Consider any solar overlay districts as "
                "primary use and **do not include** them in the output. "
                "{wes_clarification}"
            ),
        },
        {
            "feature_id": "accessory use districts",
            "use_type": (
                "permitted as accessory use or similar (e.g., when integrated "
                "with an existing structure or secondary to another use)"
            ),
            "clarifications": (
                "Consider any solar overlay districts as "
                "primary use and **do not include** them in the output. "
                "{wes_clarification}"
            ),
        },
        {
            "feature_id": "prohibited use districts",
            "use_type": (
                "prohibited or similar (e.g., where wind energy "
                "systems are not allowed or banned)"
            ),
            "clarifications": (
                "Only output specific districts where wind energy systems "
                "are prohibited **unconditionally**. "
                "{wes_clarification}"
            ),
        },
    ]

    async def parse(self, text):
        """Parse text and extract permitted use districts data

        Parameters
        ----------
        text : str
            Permitted use districts text which may or may not contain
            information about allowed uses in one or more districts.

        Returns
        -------
        pandas.DataFrame or None
            DataFrame containing parsed-out allowed-use district names.
            Can also be ``None`` if a large wind energy system is not
            found in the text.
        """
        largest_wes_type = await self._check_wind_turbine_type(text)
        if not largest_wes_type:
            return None

        outer_task_name = asyncio.current_task().get_name()
        with COMPASS_PB.jurisdiction_sub_prog_bar(outer_task_name) as sub_pb:
            task_id = sub_pb.add_task(
                "Extracting permitted uses...",
                total=len(self._USE_TYPES),
                just_parsed="",
            )
            feature_parsers = [
                asyncio.create_task(
                    self._parse_permitted_use_districts(
                        sub_pb,
                        task_id,
                        text,
                        largest_wes_type,
                        **use_type_kwargs,
                    ),
                    name=outer_task_name,
                )
                for use_type_kwargs in self._USE_TYPES
            ]
            outputs = await asyncio.gather(*(feature_parsers))
            sub_pb.update(task_id, completed=len(self._USE_TYPES))
            await asyncio.sleep(1)
            sub_pb.remove_task(task_id)

        return pd.DataFrame(chain.from_iterable(outputs))

    async def _parse_permitted_use_districts(
        self,
        sub_pb,
        task_id,
        text,
        largest_wes_type,
        feature_id,
        use_type,
        clarifications,
    ):
        """Parse a non-setback restriction from the text"""
        logger.debug("Parsing use type: %r", feature_id)
        system_message = PERMITTED_USE_SYSTEM_MESSAGE.format(
            tech=largest_wes_type
        )
        tree = setup_async_decision_tree(
            setup_graph_permitted_use_districts,
            usage_sub_label=LLMUsageCategory.PERMITTED_USE_VALUE_EXTRACTION,
            feature_id=feature_id,
            tech=largest_wes_type,
            clarifications=clarifications.format(
                wes_clarification=self._LARGE_WES_CLARIFICATION
            ),
            text=text,
            use_type=use_type,
            chat_llm_caller=self._init_chat_llm_caller(system_message),
        )
        info = await run_async_tree(tree)
        sub_pb.update(task_id, advance=1, just_parsed=feature_id)
        info.update({"feature": feature_id, "quantitative": True})
        return [info]


def _update_output_keys(output):
    """Standardize output keys

    We could standardize output keys by modifying the LLM prompts, but
    have found that it's more accurate to instruct the LLM to use
    descriptive keys (e.g. "mult_value" instead of "value" or
    "mult_type" instead of "units")
    """

    if "mult_value" not in output:
        return output

    output["value"] = output.pop("mult_value")

    if units := output.get("units"):
        msg = f"Found non-null units value for multiplier: {units}"
        warn(msg, COMPASSWarning)
    output["units"] = output.pop("mult_type", None)

    return output


def _sanitize_output(output):
    """Perform some sanitization on outputs"""
    output = _remove_key_for_empty_value(output, key="units")
    return _remove_key_for_empty_value(output, key="summary")


def _remove_key_for_empty_value(output, key):
    """Remove any output in "key" if no ordinance value found"""
    if output.get("value") is not None or not output.get(key):
        return output

    # at this point, we have some value in "key" but no actual ordinance
    # value, so remove the "key" entry
    output[key] = None
    return output
