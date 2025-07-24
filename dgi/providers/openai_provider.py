"""OpenAI LLM provider implementation."""

import os
from typing import Any

from langchain.agents import AgentType, initialize_agent
from langchain.tools import BaseTool
from langchain_openai import ChatOpenAI

from .base import LLMConfig, LLMProvider, ProviderType


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        if config.provider != ProviderType.OPENAI:
            raise ValueError(f"Invalid provider type: {config.provider}")
        super().__init__(config)

    def _initialize_client(self) -> ChatOpenAI:
        """Initialize the OpenAI client."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or provide api_key in config."
            )

        # Build client kwargs with proper types
        client_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
            "api_key": api_key,
        }

        # Add max_tokens if specified
        if self.config.max_tokens:
            client_kwargs["max_tokens"] = self.config.max_tokens

        # Add any extra parameters
        if self.config.extra_params:
            client_kwargs.update(self.config.extra_params)

        return ChatOpenAI(**client_kwargs)

    def create_agent(self, tools: list[BaseTool], **kwargs: Any) -> Any:
        """Create a LangChain agent with OpenAI."""
        default_kwargs: dict[str, Any] = {
            "agent": AgentType.OPENAI_FUNCTIONS,
            "verbose": True,
            "handle_parsing_errors": True,
            "max_iterations": 3,
        }
        default_kwargs.update(kwargs)

        return initialize_agent(tools=tools, llm=self.client, **default_kwargs)

    def validate_api_key(self) -> bool:
        """Validate that the API key is present and potentially valid."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        return api_key is not None and len(api_key) > 0

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
