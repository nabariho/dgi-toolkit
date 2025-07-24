"""Base classes for LLM providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class ProviderType(Enum):
    """Supported LLM provider types."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""

    provider: ProviderType
    model: str
    api_key: str | None = None
    temperature: float = 0.1
    max_tokens: int | None = None
    timeout: int = 30
    max_retries: int = 2
    # Provider-specific settings
    extra_params: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.extra_params is None:
            self.extra_params = {}


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    def __init__(self, config: LLMConfig) -> None:
        self.config = config
        self._client: Any | None = None

    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider-specific client."""

    @property
    def client(self) -> Any:
        """Lazy-loaded client instance."""
        if self._client is None:
            self._client = self._initialize_client()
        return self._client

    @abstractmethod
    def create_agent(self, tools: list[Any], **kwargs: Any) -> Any:
        """Create an agent with the specified tools."""

    @abstractmethod
    def validate_api_key(self) -> bool:
        """Validate that the API key is present and potentially valid."""

    @abstractmethod
    def get_model_info(self) -> dict[str, Any]:
        """Get information about the current model."""

    def get_config_summary(self) -> dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
        }
