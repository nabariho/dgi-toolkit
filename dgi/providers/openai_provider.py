"""OpenAI LLM provider implementation."""

import os
from typing import Any, Dict, List
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool

from .base import LLMProvider, LLMConfig, ProviderType


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider implementation."""

    def __init__(self, config: LLMConfig):
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

        client_kwargs = {
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
        client_kwargs.update(self.config.extra_params)

        return ChatOpenAI(**client_kwargs)

    def create_agent(self, tools: List[BaseTool], **kwargs) -> Any:
        """Create a LangChain agent with OpenAI."""
        default_kwargs = {
            "agent": AgentType.OPENAI_FUNCTIONS,
            "verbose": True,
            "handle_parsing_errors": True,
            "max_iterations": 3,
        }
        default_kwargs.update(kwargs)

        return initialize_agent(tools=tools, llm=self.client, **default_kwargs)

    def validate_api_key(self) -> bool:
        """Validate that the OpenAI API key is present."""
        api_key = self.config.api_key or os.getenv("OPENAI_API_KEY")
        return api_key is not None and len(api_key.strip()) > 0

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the OpenAI model."""
        return {
            "provider": "OpenAI",
            "model": self.config.model,
            "supports_functions": True,
            "supports_streaming": True,
            "context_window": self._get_context_window(),
            "pricing_tier": self._get_pricing_tier(),
        }

    def _get_context_window(self) -> int:
        """Get context window size for the model."""
        context_windows = {
            "gpt-4o": 128000,
            "gpt-4o-mini": 128000,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 16385,
        }
        return context_windows.get(self.config.model, 4096)

    def _get_pricing_tier(self) -> str:
        """Get pricing tier for the model."""
        if "mini" in self.config.model.lower():
            return "low-cost"
        elif "gpt-4" in self.config.model.lower():
            return "premium"
        else:
            return "standard"
