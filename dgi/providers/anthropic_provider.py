"""Anthropic LLM provider implementation."""

import os
from typing import Any, Dict, List
from langchain.agents import initialize_agent, AgentType
from langchain_anthropic import ChatAnthropic
from langchain.tools import BaseTool

from .base import LLMProvider, LLMConfig, ProviderType


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
        client_kwargs: Dict[str, Any] = {
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

    def create_agent(self, tools: List[BaseTool], **kwargs: Any) -> Any:
        """Create a LangChain agent with Anthropic."""
        default_kwargs: Dict[str, Any] = {
            "agent": AgentType.OPENAI_FUNCTIONS,  # Works with Anthropic too
            "verbose": True,
            "handle_parsing_errors": True,
            "max_iterations": 3,
        }
        default_kwargs.update(kwargs)

        return initialize_agent(tools=tools, llm=self.client, **default_kwargs)

    def validate_api_key(self) -> bool:
        """Validate that the API key is present and potentially valid."""
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        return api_key is not None and len(api_key) > 0

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }
