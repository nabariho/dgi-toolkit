"""Anthropic LLM provider implementation."""

import os
from typing import Any, Dict, List
from langchain.agents import initialize_agent, AgentType
from langchain_anthropic import ChatAnthropic
from langchain.tools import BaseTool

from .base import LLMProvider, LLMConfig, ProviderType


class AnthropicProvider(LLMProvider):
    """Anthropic (Claude) LLM provider implementation."""

    def __init__(self, config: LLMConfig):
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

        return ChatAnthropic(**client_kwargs)

    def create_agent(self, tools: List[BaseTool], **kwargs) -> Any:
        """Create a LangChain agent with Anthropic."""
        # Claude models use tools rather than OpenAI functions
        default_kwargs = {
            "agent": AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            "verbose": True,
            "handle_parsing_errors": True,
            "max_iterations": 3,
        }
        default_kwargs.update(kwargs)

        return initialize_agent(tools=tools, llm=self.client, **default_kwargs)

    def validate_api_key(self) -> bool:
        """Validate that the Anthropic API key is present."""
        api_key = self.config.api_key or os.getenv("ANTHROPIC_API_KEY")
        return api_key is not None and len(api_key.strip()) > 0

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Anthropic model."""
        return {
            "provider": "Anthropic",
            "model": self.config.model,
            "supports_functions": True,  # Claude 3+ supports tool calling
            "supports_streaming": True,
            "context_window": self._get_context_window(),
            "pricing_tier": self._get_pricing_tier(),
        }

    def _get_context_window(self) -> int:
        """Get context window size for the model."""
        context_windows = {
            "claude-3-5-sonnet-20241022": 200000,
            "claude-3-5-sonnet-20240620": 200000,
            "claude-3-5-haiku-20241022": 200000,
            "claude-3-opus-20240229": 200000,
            "claude-3-sonnet-20240229": 200000,
            "claude-3-haiku-20240307": 200000,
            "claude-2.1": 200000,
            "claude-2.0": 100000,
            "claude-instant-1.2": 100000,
        }
        return context_windows.get(self.config.model, 100000)

    def _get_pricing_tier(self) -> str:
        """Get pricing tier for the model."""
        if "haiku" in self.config.model.lower():
            return "low-cost"
        elif "opus" in self.config.model.lower():
            return "premium"
        elif "sonnet" in self.config.model.lower():
            return "standard"
        else:
            return "standard"
