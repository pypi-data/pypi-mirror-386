"""Ordinances LLM Configurations"""

import os
from collections import Counter
from abc import ABC, abstractmethod
from functools import partial, cached_property

import openai
from elm import ApiBase
from langchain_text_splitters.character import RecursiveCharacterTextSplitter

from compass.services.openai import OpenAIService
from compass.utilities import RTS_SEPARATORS
from compass.exceptions import COMPASSValueError


class LLMConfig(ABC):
    """Abstract base class representing a single LLM configuration"""

    def __init__(
        self,
        name,
        llm_call_kwargs=None,
        llm_service_rate_limit=500000,
        text_splitter_chunk_size=10_000,
        text_splitter_chunk_overlap=500,
    ):
        """

        Parameters
        ----------
        name : str
            Name of LLM.
        llm_call_kwargs : dict, optional
            Keyword arguments to be passed to the llm service ``call``
            method (i.e. `llm_service.call(**kwargs)`).
            Should *not* contain the following keys:

                - usage_tracker
                - usage_sub_label
                - messages

            These arguments are provided by the LLM Caller object.
            By default, ``None``.
        llm_service_rate_limit : int, optional
            Token rate limit (i.e. tokens per minute) of LLM service
            being used. By default, ``10_000``.
        text_splitter_chunk_size : int, optional
            Chunk size used to split the ordinance text. Parsing is
            performed on each individual chunk. Units are in token count
            of the model in charge of parsing ordinance text. Keeping
            this value low can help reduce token usage since (free)
            heuristics checks may be able to throw away irrelevant
            chunks of text before passing to the LLM.
            By default, ``10000``.
        text_splitter_chunk_overlap : int, optional
            Overlap of consecutive chunks of the ordinance text. Parsing
            is performed on each individual chunk. Units are in token
            count of the model in charge of parsing ordinance text.
            By default, ``1000``.
        """
        self.name = name
        self.llm_call_kwargs = {"timeout": 300, "temperature": 0}
        self.llm_call_kwargs.update(llm_call_kwargs or {})
        self.llm_service_rate_limit = llm_service_rate_limit
        self.text_splitter_chunk_size = text_splitter_chunk_size
        self.text_splitter_chunk_overlap = text_splitter_chunk_overlap

    @cached_property
    def text_splitter(self):
        """:class:`~langchain_text_splitters.character.RecursiveCharacterTextSplitter`: Text splitter for ordinance text"""  # noqa: W505, E501
        return RecursiveCharacterTextSplitter(
            RTS_SEPARATORS,
            chunk_size=self.text_splitter_chunk_size,
            chunk_overlap=self.text_splitter_chunk_overlap,
            length_function=partial(ApiBase.count_tokens, model=self.name),
            is_separator_regex=True,
        )

    @property
    @abstractmethod
    def llm_service(self):
        """LLMService: Object that can be used to submit calls to LLM"""
        raise NotImplementedError


class OpenAIConfig(LLMConfig):
    """OpenAI LLM configuration"""

    SUPPORTED_CLIENTS = {
        "openai": openai.AsyncOpenAI,
        "azure": openai.AsyncAzureOpenAI,
    }
    """Currently-supported OpenAI LLM clients"""

    _OPENAI_MODEL_NAMES = Counter()

    def __init__(
        self,
        name="gpt-4o-mini",
        llm_call_kwargs=None,
        llm_service_rate_limit=500000,
        text_splitter_chunk_size=10_000,
        text_splitter_chunk_overlap=500,
        client_type="azure",
        client_kwargs=None,
        tag=None,
    ):
        """

        Parameters
        ----------
        name : str, optional
            Name of OpenAI LLM. By default, ``"gpt-4o"``.
        llm_call_kwargs : dict, optional
            Keyword arguments to be passed to the llm service ``call``
            method (i.e. `llm_service.call(**kwargs)`).
            Should *not* contain the following keys:

                - usage_tracker
                - usage_sub_label
                - messages

            These arguments are provided by the LLM Caller object.
            By default, ``None``.
        llm_service_rate_limit : int, optional
            Token rate limit (i.e. tokens per minute) of LLM service
            being used. By default, ``10_000``.
        text_splitter_chunk_size : int, optional
            Chunk size used to split the ordinance text. Parsing is
            performed on each individual chunk. Units are in token count
            of the model in charge of parsing ordinance text. Keeping
            this value low can help reduce token usage since (free)
            heuristics checks may be able to throw away irrelevant
            chunks of text before passing to the LLM.
            By default, ``10000``.
        text_splitter_chunk_overlap : int, optional
            Overlap of consecutive chunks of the ordinance text. Parsing
            is performed on each individual chunk. Units are in token
            count of the model in charge of parsing ordinance text.
            By default, ``1000``.
        client_type : str, default="azure"
            Type of client to set up for this calling instance. Must be
            one of :obj:`OpenAIConfig.SUPPORTED_CLIENTS`.
            By default, ``"azure"``.
        client_kwargs : dict, optional
            Keyword-value pairs to pass to underlying LLM client. These
            typically include things like API keys and endpoints.
            By default, ``None``.
        tag : str, optional
            Optional tag to distinguish this model config from another
            model config for the same model `name`. This is useful if
            you have the same model (e.g. `gpt-4o-mini`) running on two
            different endpoints. If you have duplicate model names and
            don't specify this tag, one will be created for you. By
            default, ``None``.
        """
        super().__init__(
            name=name,
            llm_call_kwargs=llm_call_kwargs,
            llm_service_rate_limit=llm_service_rate_limit,
            text_splitter_chunk_size=text_splitter_chunk_size,
            text_splitter_chunk_overlap=text_splitter_chunk_overlap,
        )
        self.client_type = client_type.casefold()
        self._client_kwargs = client_kwargs or {}
        self._tag = tag or ""

        self._validate_client_type()
        self._validate_tag()

    def _validate_client_type(self):
        """Validate that user input a known client type"""
        if self.client_type not in self.SUPPORTED_CLIENTS:
            msg = (
                f"Unknown client type: {self.client_type!r}. Supported "
                f"clients: {list(self.SUPPORTED_CLIENTS)}"
            )
            raise COMPASSValueError(msg)

    def _validate_tag(self):
        """Update tag if needed"""
        self._OPENAI_MODEL_NAMES.update([self.name])
        num_models = self._OPENAI_MODEL_NAMES.get(self.name, 1)
        if num_models > 1 and not self._tag:
            self._tag = f"{num_models - 1}"

        if self._tag and not self._tag.startswith("-"):
            self._tag = f"-{self._tag}"

    @cached_property
    def client_kwargs(self):
        """dict: Parameters to pass to client initializer"""
        if self.client_type == "azure":
            arg_env_pairs = [
                ("api_key", "AZURE_OPENAI_API_KEY"),
                ("api_version", "AZURE_OPENAI_VERSION"),
                ("azure_endpoint", "AZURE_OPENAI_ENDPOINT"),
            ]
            for key, env_var in arg_env_pairs:
                if self._client_kwargs.get(key) is None:
                    self._client_kwargs[key] = os.environ.get(env_var)

        return self._client_kwargs

    @cached_property
    def llm_service(self):
        """LLMService: Object that can be used to submit calls to LLM"""
        client = self.SUPPORTED_CLIENTS[self.client_type](**self.client_kwargs)
        return OpenAIService(
            client,
            self.name,
            rate_limit=self.llm_service_rate_limit,
            service_tag=self._tag,
        )
