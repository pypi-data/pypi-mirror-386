"""Ordinance document content Validation logic

These are primarily used to validate that a legal document applies to a
particular technology (e.g. Solar Energy Conversion System).
"""

import logging

from compass.common import BaseTextExtractor
from compass.validation.content import Heuristic
from compass.llm.calling import StructuredLLMCaller
from compass.utilities.enums import LLMUsageCategory
from compass.utilities.parsing import merge_overlapping_texts


logger = logging.getLogger(__name__)


_LARGE_SEF_SYNONYMS = (
    "solar panels, solar energy conversion systems (SECS), solar energy "
    "facilities (SEF), solar energy farms (SEF), solar farms (SF), "
    "utility-scale solar energy systems (USES), commercial solar energy "
    "systems (CSES), ground-mounted solar energy systems (GSES), "
    "alternate energy systems (AES), commercial energy production "
    "systems (CEPCS), or similar"
)
_SEARCH_TERMS_AND = (
    "zoning, siting, setback, system design, and operational "
    "requirements/restrictions"
)
_SEARCH_TERMS_OR = _SEARCH_TERMS_AND.replace("and", "or")
_IGNORE_TYPES = (
    "CSP, private, residential, roof-mounted, micro, small, or medium sized"
)


class SolarHeuristic(Heuristic):
    """Perform a heuristic check for mention of solar farms in text"""

    NOT_TECH_WORDS = [
        "concentrated solar",
        "csp",
        "micro secs",
        "small secs",
        "mini secs",
        "private secs",
        "personal secs",
        "psecs",
        "solaris",
        "small solar",
        "micro solar",
        "mini solar",
        "private solar",
        "personal solar",
        "swecs",
        "solar break",
        "solar damage",
        "solar data",
        "solar resource",
    ]
    """Words and phrases that indicate text is NOT about solar farms"""
    GOOD_TECH_KEYWORDS = ["solar", "setback"]
    """Words that indicate we should keep a chunk for analysis"""
    GOOD_TECH_ACRONYMS = ["secs", "sef", "ses", "cses"]
    """Acronyms for solar farms that we want to capture"""
    GOOD_TECH_PHRASES = [
        "commercial solar energy system",
        "solar energy conversion",
        "solar energy system",
        "solar panel",
        "solar farm",
        "solar energy farm",
        "utility solar energy system",
    ]
    """Phrases that indicate text is about solar farms"""


class SolarOrdinanceTextCollector(StructuredLLMCaller):
    """Check text chunks for ordinances and collect them if they do"""

    CONTAINS_ORD_PROMPT = (
        "You extract structured data from text. Return your answer in JSON "
        "format (not markdown). Your JSON file must include exactly two "
        "keys. The first key is 'solar_reqs', which is a string that "
        f"summarizes all {_SEARCH_TERMS_AND} that are explicitly enacted "
        "in the legal text for solar energy systems for a given jurisdiction. "
        "Note that solar energy bans are an important restriction to track. "
        "Include any **closely related provisions** if they clearly pertain "
        "to the **development, operation, modification, or removal** of solar "
        "energy systems (or solar panels). "
        "All restrictions should be enforceable - ignore any text that only "
        "provides a legal definition of the regulation. If the text does not "
        f"specify any concrete {_SEARCH_TERMS_OR} for a wind energy system, "
        "set this key to `null`. The last key is '{key}', which is a boolean "
        "that is set to True if the text excerpt explicitly details "
        f"{_SEARCH_TERMS_OR} for a solar energy system and False otherwise."
    )
    """Prompt to check if chunk contains SEF ordinance info"""

    IS_UTILITY_SCALE_PROMPT = (
        "You are a legal scholar that reads ordinance text and determines "
        f"whether it applies to {_SEARCH_TERMS_OR} for **large "
        "solar energy systems**. Large solar energy systems (SES) may "
        f"also be referred to as {_LARGE_SEF_SYNONYMS}. "
        "Your client is a commercial solar developer that does not "
        f"care about ordinances related to {_IGNORE_TYPES} solar energy "
        "systems. Ignore any text related to such systems. "
        "Return your answer as a dictionary in JSON format (not markdown). "
        "Your JSON file must include exactly two keys. The first key is "
        "'summary' which contains a string that summarizes the types of "
        "solar energy systems the text applies to (if any). The second key "
        "is '{key}', which is a boolean that is set to True if any part of "
        f"the text excerpt details {_SEARCH_TERMS_OR} for the **large solar "
        "energy conversion systems** (or similar) that the client is "
        "interested in and False otherwise."
    )
    """Prompt to check if chunk is for utility-scale SEF"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ordinance_chunks = {}

    async def check_chunk(self, chunk_parser, ind):
        """Check a chunk at a given ind to see if it contains ordinance

        Parameters
        ----------
        chunk_parser : ParseChunksWithMemory
            Instance that contains a ``parse_from_ind`` method.
        ind : int
            Index of the chunk to check.

        Returns
        -------
        bool
            Boolean flag indicating whether or not the text in the chunk
            contains large solar energy farm ordinance text.
        """
        contains_ord_info = await chunk_parser.parse_from_ind(
            ind,
            key="contains_ord_info",
            llm_call_callback=self._check_chunk_contains_ord,
        )
        if not contains_ord_info:
            logger.debug("Text at ind %d does not contain ordinance info", ind)
            return False

        logger.debug("Text at ind %d does contain ordinance info", ind)

        is_utility_scale = await chunk_parser.parse_from_ind(
            ind,
            key="x",
            llm_call_callback=self._check_chunk_is_for_utility_scale,
        )
        if not is_utility_scale:
            logger.debug("Text at ind %d is not for utility-scale SEF", ind)
            return False

        logger.debug("Text at ind %d is for utility-scale SEF", ind)

        _store_chunk(chunk_parser, ind, self._ordinance_chunks)
        logger.debug("Added text at ind %d to ordinances", ind)

        return True

    @property
    def contains_ord_info(self):
        """bool: Flag indicating whether text contains ordinance info"""
        return bool(self._ordinance_chunks)

    @property
    def ordinance_text(self):
        """str: Combined ordinance text from the individual chunks"""
        logger.debug(
            "Grabbing %d ordinance chunk(s) from original text at these "
            "indices: %s",
            len(self._ordinance_chunks),
            list(self._ordinance_chunks),
        )

        text = [
            self._ordinance_chunks[ind]
            for ind in sorted(self._ordinance_chunks)
        ]
        return merge_overlapping_texts(text)

    async def _check_chunk_contains_ord(self, key, text_chunk):
        """Call LLM on a chunk of text to check for ordinance"""
        content = await self.call(
            sys_msg=self.CONTAINS_ORD_PROMPT.format(key=key),
            content=text_chunk,
            usage_sub_label=(LLMUsageCategory.DOCUMENT_CONTENT_VALIDATION),
        )
        logger.debug("LLM response: %s", content)
        return content.get(key, False)

    async def _check_chunk_is_for_utility_scale(self, key, text_chunk):
        """Call LLM on a chunk of text to check for utility scale"""
        content = await self.call(
            sys_msg=self.IS_UTILITY_SCALE_PROMPT.format(key=key),
            content=text_chunk,
            usage_sub_label=(LLMUsageCategory.DOCUMENT_CONTENT_VALIDATION),
        )
        logger.debug("LLM response: %s", content)
        return content.get(key, False)


class SolarPermittedUseDistrictsTextCollector(StructuredLLMCaller):
    """Check text chunks for permitted solar districts; collect them"""

    DISTRICT_PROMPT = (
        "You are a legal scholar that reads ordinance text and determines "
        "whether it explicitly contains relevant information to determine the "
        "districts (and especially the district names) where large solar "
        "energy farms are a permitted use (primary, special, accessory, or "
        "otherwise), as well as the districts where large solar energy farms "
        "are prohibited entirely. Large solar energy systems (SES) may also "
        f"be referred to as {_LARGE_SEF_SYNONYMS}. "
        "Do not make any inferences; only answer based on information that "
        "is explicitly stated in the text. "
        "Note that relevant information may sometimes be found in tables. "
        "Return your answer as a dictionary in JSON format (not markdown). "
        "Your JSON file must include exactly two keys. The first key is "
        "'districts' which contains a string that lists all of the district "
        "names for which the text explicitly permits **large solar energy "
        "farms** (if any). The last key is '{key}', which is a boolean that "
        "is set to True if any part of the text excerpt provides information "
        "on districts where **large solar energy farms** (or similar) are a "
        "permitted use and False otherwise."
    )
    """Prompt to check if chunk contains info on permitted districts"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._district_chunks = {}

    async def check_chunk(self, chunk_parser, ind):
        """Check a chunk to see if it contains permitted uses

        Parameters
        ----------
        chunk_parser : ParseChunksWithMemory
            Instance that contains a ``parse_from_ind`` method.
        ind : int
            Index of the chunk to check.

        Returns
        -------
        bool
            Boolean flag indicating whether or not the text in the chunk
            contains large solar energy farm permitted use text.
        """

        key = "contains_district_info"
        content = await self.call(
            sys_msg=self.DISTRICT_PROMPT.format(key=key),
            content=chunk_parser.text_chunks[ind],
            usage_sub_label=(
                LLMUsageCategory.DOCUMENT_PERMITTED_USE_CONTENT_VALIDATION
            ),
        )
        logger.debug("LLM response: %s", content)
        contains_district_info = content.get(key, False)

        if contains_district_info:
            _store_chunk(chunk_parser, ind, self._district_chunks)
            logger.debug("Text at ind %d contains district info", ind)
            return True

        logger.debug("Text at ind %d does not contain district info", ind)
        return False

    @property
    def contains_district_info(self):
        """bool: Flag indicating whether text contains district info"""
        return bool(self._district_chunks)

    @property
    def permitted_use_district_text(self):
        """str: Combined permitted use districts text from the chunks"""
        logger.debug(
            "Grabbing %d permitted use chunk(s) from original text at these "
            "indices: %s",
            len(self._district_chunks),
            list(self._district_chunks),
        )

        text = [
            self._district_chunks[ind] for ind in sorted(self._district_chunks)
        ]
        return merge_overlapping_texts(text)


class SolarOrdinanceTextExtractor(BaseTextExtractor):
    """Extract succinct ordinance text from input

    Purpose:
        Extract relevant ordinance text from document.
    Responsibilities:
        1. Extract portions from chunked document text relevant to
           particular ordinance type (e.g. solar zoning for
           utility-scale systems).
    Key Relationships:
        Uses a StructuredLLMCaller for LLM queries.
    """

    SOLAR_ENERGY_SYSTEM_FILTER_PROMPT = (
        "# CONTEXT #\n"
        "We want to reduce the provided excerpt to only contain information "
        "about **solar energy systems**. The extracted text will be used for "
        "structured data extraction, so it must be both **comprehensive** "
        "(retaining all relevant details) and **focused** (excluding "
        "unrelated content), with **zero rewriting or paraphrasing**. "
        "Ensure that all retained information is "
        "**directly applicable to solar energy systems** while preserving "
        "full context and accuracy.\n"
        "\n# OBJECTIVE #\n"
        "Extract all text **pertaining to solar energy systems** from the "
        "provided excerpt.\n"
        "\n# RESPONSE #\n"
        "Follow these guidelines carefully:\n"
        "\n1. ## Scope of Extraction ##:\n"
        "- Include **all** text that pertains to** solar energy systems**, "
        "even if they are referred to by different names such as:\n"
        f"\t{_LARGE_SEF_SYNONYMS.capitalize()}.\n"
        "- Explicitly include any text related to **bans or prohibitions** "
        "on solar energy systems.\n"
        "- Explicitly include any text related to the adoption or enactment "
        "date of the ordinance (if any).\n"
        "\n2. ## Exclusions ##:\n"
        "- Do **not** include text that does not pertain to solar energy "
        "systems.\n"
        "\n3. ## Formatting & Structure ##:\n"
        "- **Preserve _all_ section titles, headers, and numberings** for "
        "reference.\n"
        "- **Maintain the original wording, formatting, and structure** to "
        "ensure accuracy.\n"
        "\n4. ## Output Handling ##:\n"
        "- This is a strict extraction task — act like a text filter, **not** "
        "a summarizer or writer.\n"
        "- Do not add, explain, reword, or summarize anything.\n"
        "- The output must be a **copy-paste** of the original excerpt.\n"
        "**Absolutely no paraphrasing or rewriting.**\n"
        "- The output must consist **only** of contiguous or discontiguous "
        "verbatim blocks copied from the input.\n"
        "- If **no relevant text** is found, return the response: "
        "'No relevant text.'"
    )
    """Prompt to extract ordinance text for SEF"""

    async def extract_solar_energy_system_section(self, text_chunks):
        """Extract ordinance text from input text chunks for SEF

        Parameters
        ----------
        text_chunks : list of str
            List of strings, each of which represent a chunk of text.
            The order of the strings should be the order of the text
            chunks.

        Returns
        -------
        str
            Ordinance text extracted from text chunks.
        """
        return await self._process(
            text_chunks=text_chunks,
            instructions=self.SOLAR_ENERGY_SYSTEM_FILTER_PROMPT,
            is_valid_chunk=_valid_chunk,
        )

    @property
    def parsers(self):
        """Iterable of parsers provided by this extractor

        Yields
        ------
        name : str
            Name describing the type of text output by the parser.
        parser : callable
            Async function that takes a ``text_chunks`` input and
            outputs parsed text.
        """
        yield (
            "cleaned_ordinance_text",
            self.extract_solar_energy_system_section,
        )


class SolarPermittedUseDistrictsTextExtractor(BaseTextExtractor):
    """Extract succinct ordinance text from input

    Purpose:
        Extract relevant ordinance text from document.
    Responsibilities:
        1. Extract portions from chunked document text relevant to
           particular ordinance type (e.g. solar zoning for
           utility-scale systems).
    Key Relationships:
        Uses a StructuredLLMCaller for LLM queries.
    """

    _USAGE_LABEL = LLMUsageCategory.DOCUMENT_PERMITTED_USE_DISTRICTS_SUMMARY

    PERMITTED_USES_FILTER_PROMPT = (
        "# CONTEXT #\n"
        "We want to reduce the provided excerpt to only contain information "
        "detailing permitted use(s) for a district. The extracted text will "
        "be used for structured data extraction, so it must be both "
        "**comprehensive** (retaining all relevant details) and **focused** "
        "(excluding unrelated content), with **zero rewriting or "
        "paraphrasing**. Ensure that all retained information "
        "is **directly applicable** to permitted use(s) for one or more "
        "districts while preserving full context and accuracy.\n"
        "\n# OBJECTIVE #\n"
        "Remove all text **not directly pertinent** to permitted use(s) for "
        "a district.\n"
        "\n# RESPONSE #\n"
        "Follow these guidelines carefully:\n"
        "\n1. ## Scope of Extraction ##:\n"
        "- Retain all text defining permitted use(s) for a district, "
        "including:\n"
        "\t- **Primary, Special, Conditional, Accessory, Prohibited, and "
        "any other use types.**\n"
        "\t- **District names and zoning classifications.**\n"
        "- Pay extra attention to any references to **solar energy "
        "facilities** or related terms.\n"
        "- Ensure that **tables, lists, and structured elements** are "
        "preserved as they may contain relevant details.\n"
        "\n2. ## Exclusions ##:\n"
        "- Do **not** include unrelated regulations, procedural details, "
        "or non-use-based restrictions.\n"
        "\n3. ## Formatting & Structure ##:\n"
        "- **Preserve _all_ section titles, headers, and numberings** for "
        "reference, **especially if they contain the district name**.\n"
        "- **Maintain the original wording, formatting, and structure** to "
        "ensure accuracy.\n"
        "\n4. ## Output Handling ##:\n"
        "- This is a strict extraction task — act like a text filter, **not** "
        "a summarizer or writer.\n"
        "- Do not add, explain, reword, or summarize anything.\n"
        "- The output must be a **copy-paste** of the original excerpt.\n"
        "**Absolutely no paraphrasing or rewriting.**\n"
        "- The output must consist **only** of contiguous or discontiguous "
        "verbatim blocks copied from the input.\n"
        "- If **no relevant text** is found, return the response: "
        "'No relevant text.'"
    )
    """Prompt to extract ordinance text for permitted uses"""

    SEF_PERMITTED_USES_FILTER_PROMPT = (
        "# CONTEXT #\n"
        "We want to reduce the provided excerpt to only contain information "
        "detailing **solar energy system** permitted use(s) for a district. "
        "The extracted text will be used for structured data extraction, so "
        "it must be both **comprehensive** (retaining all relevant details) "
        "and **focused** (excluding unrelated content), with **zero rewriting "
        "or paraphrasing**. Ensure that all "
        "retained information is **directly applicable** to permitted use(s) "
        "for solar energy systems in one or more districts while "
        "preserving full context and accuracy.\n"
        "\n# OBJECTIVE #\n"
        "Remove all text **not directly pertinent** to solar energy "
        "conversion system permitted use(s) for a district.\n"
        "\n# RESPONSE #\n"
        "Follow these guidelines carefully:\n"
        "\n1. ## Scope of Extraction ##:\n"
        "- Retain all text defining permitted use(s) for a district, "
        "including:\n"
        "\t- **Primary, Special, Conditional, Accessory, Prohibited, and "
        "any other use types.**\n"
        "\t- **District names and zoning classifications.**\n"
        "- Ensure that **tables, lists, and structured elements** are "
        "preserved as they may contain relevant details.\n"
        "\n2. ## Exclusions ##:\n"
        "- Do not include text that does not pertain at all to solar "
        "energy systems.\n"
        "\n3. ## Formatting & Structure ##:\n"
        "- **Preserve _all_ section titles, headers, and numberings** for "
        "reference, **especially if they contain the district name**.\n"
        "- **Maintain the original wording, formatting, and structure** to "
        "ensure accuracy.\n"
        "\n4. ## Output Handling ##:\n"
        "- This is a strict extraction task — act like a text filter, **not** "
        "a summarizer or writer.\n"
        "- Do not add, explain, reword, or summarize anything.\n"
        "- The output must be a **copy-paste** of the original excerpt.\n"
        "**Absolutely no paraphrasing or rewriting.**\n"
        "- The output must consist **only** of contiguous or discontiguous "
        "verbatim blocks copied from the input.\n"
        "- If **no relevant text** is found, return the response: "
        "'No relevant text.'"
    )
    """Prompt to extract ordinance text for permitted uses for SEF"""

    async def extract_permitted_uses(self, text_chunks):
        """Extract permitted uses text from input text chunks

        Parameters
        ----------
        text_chunks : list of str
            List of strings, each of which represent a chunk of text.
            The order of the strings should be the order of the text
            chunks.

        Returns
        -------
        str
            Ordinance text extracted from text chunks.
        """
        return await self._process(
            text_chunks=text_chunks,
            instructions=self.PERMITTED_USES_FILTER_PROMPT,
            is_valid_chunk=_valid_chunk,
        )

    async def extract_sef_permitted_uses(self, text_chunks):
        """Extract permitted uses text for large SEF from input text

        Parameters
        ----------
        text_chunks : list of str
            List of strings, each of which represent a chunk of text.
            The order of the strings should be the order of the text
            chunks.

        Returns
        -------
        str
            Ordinance text extracted from text chunks.
        """
        return await self._process(
            text_chunks=text_chunks,
            instructions=self.SEF_PERMITTED_USES_FILTER_PROMPT,
            is_valid_chunk=_valid_chunk,
        )

    @property
    def parsers(self):
        """Iterable of parsers provided by this extractor

        Yields
        ------
        name : str
            Name describing the type of text output by the parser.
        parser : callable
            Async function that takes a ``text_chunks`` input and
            outputs parsed text.
        """
        yield "permitted_use_only_text", self.extract_permitted_uses
        yield "districts_text", self.extract_sef_permitted_uses


def _valid_chunk(chunk):
    """True if chunk has content"""
    return chunk and "no relevant text" not in chunk.lower()


def _store_chunk(parser, chunk_ind, store):
    """Store chunk and its neighbors if it is not already stored"""
    for offset in range(1 - parser.num_to_recall, 2):
        ind_to_grab = chunk_ind + offset
        if ind_to_grab < 0 or ind_to_grab >= len(parser.text_chunks):
            continue

        store.setdefault(ind_to_grab, parser.text_chunks[ind_to_grab])
