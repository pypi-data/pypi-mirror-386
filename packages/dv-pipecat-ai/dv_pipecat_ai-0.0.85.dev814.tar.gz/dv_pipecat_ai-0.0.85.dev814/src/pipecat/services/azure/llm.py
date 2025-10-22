# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Azure OpenAI service implementation for the Pipecat AI framework."""

from typing import Optional

from loguru import logger
from openai import AsyncAzureOpenAI

from pipecat.adapters.services.open_ai_adapter import OpenAILLMInvocationParams
from pipecat.services.openai.llm import OpenAILLMService


class AzureLLMService(OpenAILLMService):
    """A service for interacting with Azure OpenAI using the OpenAI-compatible interface.

    This service extends OpenAILLMService to connect to Azure's OpenAI endpoint while
    maintaining full compatibility with OpenAI's interface and functionality.


    Args:
        api_key: The API key for accessing Azure OpenAI.
        endpoint: The Azure endpoint URL.
        model: The model identifier to use.
        api_version: Azure API version. Defaults to "2024-09-01-preview".
        reasoning_effort: If provided for reasoning models, sets the effort (e.g. "minimal").
        **kwargs: Additional keyword arguments passed to OpenAILLMService.

    """

    def __init__(
        self,
        *,
        api_key: str,
        endpoint: str,
        model: str,
        api_version: str = "2024-09-01-preview",
        reasoning_effort: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the Azure LLM service.

        Args:
            api_key: The API key for accessing Azure OpenAI.
            endpoint: The Azure endpoint URL.
            model: The model identifier to use.
            api_version: Azure API version. Defaults to "2024-09-01-preview".
            **kwargs: Additional keyword arguments passed to OpenAILLMService.
        """
        # Initialize variables before calling parent __init__() because that
        # will call create_client() and we need those values there.
        self._endpoint = endpoint
        self._api_version = api_version
        self._reasoning_effort = reasoning_effort
        super().__init__(api_key=api_key, model=model, **kwargs)

    def create_client(self, api_key=None, base_url=None, **kwargs):
        """Create OpenAI-compatible client for Azure OpenAI endpoint.

        Args:
            api_key: API key for authentication. Uses instance key if None.
            base_url: Base URL for the client. Ignored for Azure implementation.
            **kwargs: Additional keyword arguments. Ignored for Azure implementation.

        Returns:
            AsyncAzureOpenAI: Configured Azure OpenAI client instance.
        """
        logger.debug(f"Creating Azure OpenAI client with endpoint {self._endpoint}")
        azure_deployment = kwargs.pop("azure_deployment", None)
        return AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=self._endpoint,
            api_version=self._api_version,
            azure_deployment=azure_deployment,
        )

    def _is_reasoning_model(self) -> bool:
        """Check if the current model supports reasoning parameters.

        Based on search results:
        - GPT-5, GPT-5-mini, and GPT-5-nano are reasoning models
        - GPT-5-chat is a standard chat model that doesn't use reasoning by default

        Returns:
            True if model supports reasoning parameters.
        """
        model_name_lower = self.model_name.lower()

        # Reasoning-capable models
        reasoning_models = {"gpt-5-nano", "gpt-5", "gpt-5-mini"}
        return model_name_lower in reasoning_models

    def build_chat_completion_params(self, params_from_context: OpenAILLMInvocationParams) -> dict:
        # include base params
        params = super().build_chat_completion_params(params_from_context)

        if self._is_reasoning_model():
            # not required for reasoning models
            for k in ("frequency_penalty", "presence_penalty", "temperature", "top_p"):
                if k in params:
                    params.pop(k, None)
            if self._reasoning_effort:
                params["reasoning_effort"] = self._reasoning_effort
            seed = self._settings.get("seed")
            if seed is not None:
                params["seed"] = seed
        else:
            # Standard models are fine with the defaults from the base class
            pass

        return params
