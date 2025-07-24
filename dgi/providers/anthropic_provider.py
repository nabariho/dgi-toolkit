"""Anthropic LLM provider implementation."""

import os
from typing import Any

from langchain.agents import AgentType, initialize_agent
from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic

from .base import LLMConfig, LLMProvider, ProviderType


class AnthropicProvider(LLMProvider):
    """Anthropic LLM provider implementation."""

    def __init__(self, config: LLMConfig) -> None:
        if config.provider != ProviderType.ANTHROPIC:
            raise ValueError(f"Invalid provider type: {config.provider}")
        super().__init__(config)

    def _initialize_client(self) -> ChatAnthropic:
        """Initialize the Anthropic client."""
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")

        if not api_key:
            raise ValueError(
                "Anthropic API key is required. Set ANTHROPIC_API_KEY environment variable "
                "or provide api_key in config."
            )

        # Build client kwargs with proper types
        client_kwargs: dict[str, Any] = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
            "anthropic_api_key": api_key,
        }

        # Add max_tokens if specified
        if self.config.max_tokens:
            client_kwargs["max_tokens"] = self.config.max_tokens

        # Add any extra parameters
        if self.config.extra_params:
            client_kwargs.update(self.config.extra_params)

        return ChatAnthropic(**client_kwargs)

    def create_agent(self, tools: list[BaseTool], **kwargs: Any) -> Any:
        """Create a LangChain agent with Anthropic."""
        default_kwargs: dict[str, Any] = {
            "agent": AgentType.OPENAI_FUNCTIONS,  # Works with Anthropic too
            "verbose": True,
            "handle_parsing_errors": True,
            "max_iterations": 3,
        }
        default_kwargs.update(kwargs)

        return initialize_agent(tools=tools, llm=self.client, **default_kwargs)

    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current Anthropic model."""
        return {
            "provider": "Anthropic",
            "model": self.config.model,
            "supports_functions": True,
            "context_window": self._get_context_window(),
            "pricing_tier": self._get_pricing_tier(),
        }

    def _get_context_window(self) -> int:
        """Get context window size for the current model."""
        model_context_windows = {
            "claude-3-5-sonnet-20241022": 200000,
            "claude-3-5-haiku-20241022": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
            "claude-instant-1.2": 100000,
        }
        return model_context_windows.get(self.config.model, 200000)

    def _get_pricing_tier(self) -> str:
        """Get pricing tier for the current model."""
        model = self.config.model
        if "haiku" in model:
            return "low-cost"
        elif "sonnet" in model:
            return "standard"
        elif "opus" in model:
            return "premium"
        else:
            return "standard"

    def validate_api_key(self) -> bool:
        """Validate that the API key is present and potentially valid."""
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        return api_key is not None and len(api_key) > 0
