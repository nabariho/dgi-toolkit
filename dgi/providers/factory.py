"""Factory for creating LLM providers based on configuration."""

import os
from typing import Dict, Any, Optional

from .base import LLMProvider, LLMConfig, ProviderType
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


# Default model configurations for each provider
DEFAULT_MODELS = {
    ProviderType.OPENAI: "gpt-4o-mini",
    ProviderType.ANTHROPIC: "claude-3-5-sonnet-20241022",
}

# Environment variable mapping for API keys
API_KEY_ENV_VARS = {
    ProviderType.OPENAI: "OPENAI_API_KEY",
    ProviderType.ANTHROPIC: "ANTHROPIC_API_KEY",
}


def create_provider(
    provider_type: str | ProviderType,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs,
) -> LLMProvider:
    """Create an LLM provider instance.

    Args:
        provider_type: Provider type ("openai", "anthropic", or ProviderType enum)
        model: Model name (uses default if not specified)
        api_key: API key (uses environment variable if not specified)
        **kwargs: Additional configuration parameters

    Returns:
        Configured LLMProvider instance

    Raises:
        ValueError: If provider type is unsupported or configuration is invalid

    Examples:
        # Create OpenAI provider with defaults
        provider = create_provider("openai")

        # Create Anthropic provider with custom model
        provider = create_provider(
            "anthropic",
            model="claude-3-5-haiku-20241022",
            temperature=0.2
        )

        # Create with explicit configuration
        provider = create_provider(
            ProviderType.OPENAI,
            model="gpt-4o",
            api_key="sk-...",
            max_tokens=1000
        )
    """
    # Convert string to enum if needed
    if isinstance(provider_type, str):
        try:
            provider_type = ProviderType(provider_type.lower())
        except ValueError:
            supported = [p.value for p in ProviderType]
            raise ValueError(
                f"Unsupported provider: {provider_type}. Supported: {supported}"
            )

    # Use default model if not specified
    if model is None:
        model = DEFAULT_MODELS[provider_type]

    # Create configuration
    config = LLMConfig(provider=provider_type, model=model, api_key=api_key, **kwargs)

    # Create provider instance
    if provider_type == ProviderType.OPENAI:
        return OpenAIProvider(config)
    elif provider_type == ProviderType.ANTHROPIC:
        return AnthropicProvider(config)
    else:
        raise ValueError(f"Provider not implemented: {provider_type}")


def create_provider_from_env(
    provider_env_var: str = "DGI_LLM_PROVIDER",
    model_env_var: str = "DGI_LLM_MODEL",
    **kwargs,
) -> LLMProvider:
    """Create provider from environment variables.

    Args:
        provider_env_var: Environment variable name for provider type
        model_env_var: Environment variable name for model
        **kwargs: Additional configuration parameters

    Returns:
        Configured LLMProvider instance

    Environment Variables:
        DGI_LLM_PROVIDER: Provider type ("openai", "anthropic")
        DGI_LLM_MODEL: Model name (optional, uses defaults)
        OPENAI_API_KEY: OpenAI API key
        ANTHROPIC_API_KEY: Anthropic API key

    Examples:
        # Set environment and create provider
        os.environ["DGI_LLM_PROVIDER"] = "anthropic"
        os.environ["DGI_LLM_MODEL"] = "claude-3-5-haiku-20241022"
        provider = create_provider_from_env()
    """
    provider_str = os.getenv(provider_env_var, "openai")
    model = os.getenv(model_env_var)

    return create_provider(provider_type=provider_str, model=model, **kwargs)


def get_available_providers() -> Dict[str, Dict[str, Any]]:
    """Get information about all available providers.

    Returns:
        Dictionary with provider information including default models,
        required environment variables, and capabilities.
    """
    return {
        "openai": {
            "default_model": DEFAULT_MODELS[ProviderType.OPENAI],
            "api_key_env": API_KEY_ENV_VARS[ProviderType.OPENAI],
            "supported_models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-4",
                "gpt-3.5-turbo",
            ],
            "capabilities": {
                "function_calling": True,
                "streaming": True,
                "vision": True,  # gpt-4o supports vision
            },
        },
        "anthropic": {
            "default_model": DEFAULT_MODELS[ProviderType.ANTHROPIC],
            "api_key_env": API_KEY_ENV_VARS[ProviderType.ANTHROPIC],
            "supported_models": [
                "claude-3-5-sonnet-20241022",
                "claude-3-5-sonnet-20240620",
                "claude-3-5-haiku-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ],
            "capabilities": {
                "function_calling": True,
                "streaming": True,
                "vision": True,  # Claude 3+ supports vision
            },
        },
    }
