"""Ordinances LLM Calling classes"""

import logging

from compass.utilities import llm_response_as_json
from compass.utilities.enums import LLMUsageCategory


logger = logging.getLogger(__name__)
_JSON_INSTRUCTIONS = "Return your answer as a dictionary in JSON format"


class BaseLLMCaller:
    """Class to support LLM calling functionality

    Purpose:
        Helper classes to call LLMs.
    Responsibilities:
        1. Use a service (e.g.
           :class:`~compass.services.openai.OpenAIService`) to query an
           LLM.
        2. Maintain a useful context to simplify LLM query.

            - Typically these classes are initialized with a single LLM
              model (and optionally a usage tracker)
            - This context is passed to every ``Service.call``
              invocation, allowing user to focus on only the message.

        3. Track message history (ChatLLMCaller) or convert output into
           JSON (StructuredLLMCaller).

    Key Relationships:
        Delegates most of work to underlying ``Service`` class.
    """

    def __init__(self, llm_service, usage_tracker=None, **kwargs):
        """

        Parameters
        ----------
        llm_service : Service
            LLM service used for queries.
        usage_tracker : UsageTracker, optional
            Optional tracker instance to monitor token usage during
            LLM calls. By default, ``None``.
        **kwargs
            Keyword arguments to be passed to the underlying service
            processing function (i.e. ``llm_service.call(**kwargs)``).
            Should **not** contain the following keys:

                - usage_sub_label
                - messages

            These arguments are provided by this caller object.
        """
        self.llm_service = llm_service
        self.usage_tracker = usage_tracker
        self.kwargs = kwargs


class LLMCaller(BaseLLMCaller):
    """Simple LLM caller, with no memory and no parsing utilities

    See Also
    --------
    ChatLLMCaller
        Chat-like LLM calling functionality.
    StructuredLLMCaller
        Structured (JSON) LLM calling functionality.
    """

    async def call(
        self, sys_msg, content, usage_sub_label=LLMUsageCategory.DEFAULT
    ):
        """Call LLM

        Parameters
        ----------
        sys_msg : str
            The LLM system message.
        content : str
            Your chat message for the LLM.
        usage_sub_label : str, optional
            Label to store token usage under. By default, ``"default"``.

        Returns
        -------
        str or None
            The LLM response, as a string, or ``None`` if something went
            wrong during the call.
        """
        return await self.llm_service.call(
            usage_tracker=self.usage_tracker,
            usage_sub_label=usage_sub_label,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": content},
            ],
            **self.kwargs,
        )


class ChatLLMCaller(BaseLLMCaller):
    """Class to support chat-like LLM calling functionality

    See Also
    --------
    LLMCaller
        Simple LLM caller, with no memory and no parsing utilities.
    StructuredLLMCaller
        Structured (JSON) LLM calling functionality.
    """

    def __init__(
        self, llm_service, system_message, usage_tracker=None, **kwargs
    ):
        """

        Parameters
        ----------
        llm_service : compass.services.base.Service
            LLM service used for queries.
        system_message : str
            System message to use for chat with LLM.
        usage_tracker : UsageTracker, optional
            Optional tracker instance to monitor token usage during
            LLM calls. By default, ``None``.
        **kwargs
            Keyword arguments to be passed to the underlying service
            processing function (i.e. `llm_service.call(**kwargs)`).
            Should *not* contain the following keys:

                - usage_sub_label
                - messages

            These arguments are provided by this caller object.
        """
        super().__init__(llm_service, usage_tracker, **kwargs)
        self.messages = [{"role": "system", "content": system_message}]

    async def call(self, content, usage_sub_label=LLMUsageCategory.CHAT):
        """Chat with the LLM

        Parameters
        ----------
        content : str
            Your chat message for the LLM.
        usage_sub_label : str, optional
            Label to store token usage under. By default, ``"chat"``.

        Returns
        -------
        str or None
            The LLM response, as a string, or ``None`` if something went
            wrong during the call.
        """
        self.messages.append({"role": "user", "content": content})

        response = await self.llm_service.call(
            usage_tracker=self.usage_tracker,
            usage_sub_label=usage_sub_label,
            messages=self.messages,
            **self.kwargs,
        )
        if response is None:
            self.messages = self.messages[:-1]
            return None

        self.messages.append({"role": "assistant", "content": response})
        return response


class StructuredLLMCaller(BaseLLMCaller):
    """Class to support structured (JSON) LLM calling functionality

    See Also
    --------
    LLMCaller
        Simple LLM caller, with no memory and no parsing utilities.
    ChatLLMCaller
        Chat-like LLM calling functionality.
    """

    async def call(
        self, sys_msg, content, usage_sub_label=LLMUsageCategory.DEFAULT
    ):
        """Call LLM for structured data retrieval

        Parameters
        ----------
        sys_msg : str
            The LLM system message. If this text does not contain the
            instruction text "Return your answer as a dictionary in JSON
            format", it will be added.
        content : str
            LLM call content (typically some text to extract info from).
        usage_sub_label : str, optional
            Label to store token usage under. By default, ``"default"``.

        Returns
        -------
        dict
            Dictionary containing the LLM-extracted features. Dictionary
            may be empty if there was an error during the LLM call.
        """
        sys_msg = _add_json_instructions_if_needed(sys_msg)

        response = await self.llm_service.call(
            usage_tracker=self.usage_tracker,
            usage_sub_label=usage_sub_label,
            messages=[
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": content},
            ],
            **self.kwargs,
        )
        return llm_response_as_json(response) if response else {}


def _add_json_instructions_if_needed(system_message):
    """Add JSON instruction to system message if needed"""
    if "JSON format" not in system_message:
        logger.debug(
            "JSON instructions not found in system message. Adding..."
        )
        system_message = f"{system_message}\n{_JSON_INSTRUCTIONS}."
        logger.debug("New system message:\n%s", system_message)
    return system_message
