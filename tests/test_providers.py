"""Tests for LLM provider abstraction."""

import os
import pytest
from unittest.mock import patch

from dgi.providers import (
    LLMConfig,
    ProviderType,
    OpenAIProvider,
    AnthropicProvider,
    create_provider,
    create_provider_from_env,
    get_available_providers,
)


class TestLLMConfig:
    """Test LLM configuration class."""

    def test_config_creation(self):
        """Test basic config creation."""
        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            api_key="test-key",
            temperature=0.2,
        )

        assert config.provider == ProviderType.OPENAI
        assert config.model == "gpt-4o-mini"
        assert config.api_key == "test-key"
        assert config.temperature == 0.2
        assert config.extra_params == {}

    def test_config_defaults(self):
        """Test config with default values."""
        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
        )

        assert config.api_key is None
        assert config.temperature == 0.1
        assert config.timeout == 30
        assert config.max_retries == 2
        assert config.extra_params == {}


class TestProviderFactory:
    """Test provider factory functions."""

    def test_create_provider_openai(self):
        """Test creating OpenAI provider."""
        provider = create_provider("openai", model="gpt-4o-mini", api_key="test-key")

        assert isinstance(provider, OpenAIProvider)
        assert provider.config.provider == ProviderType.OPENAI
        assert provider.config.model == "gpt-4o-mini"

    def test_create_provider_anthropic(self):
        """Test creating Anthropic provider."""
        provider = create_provider(
            ProviderType.ANTHROPIC,
            model="claude-3-5-haiku-20241022",
            api_key="test-key",
        )

        assert isinstance(provider, AnthropicProvider)
        assert provider.config.provider == ProviderType.ANTHROPIC
        assert provider.config.model == "claude-3-5-haiku-20241022"

    def test_create_provider_invalid(self):
        """Test creating provider with invalid type."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_provider("invalid_provider")

    def test_create_provider_defaults(self):
        """Test creating provider with default models."""
        # OpenAI with defaults
        provider = create_provider("openai", api_key="test")
        assert provider.config.model == "gpt-4o-mini"

        # Anthropic with defaults
        provider = create_provider("anthropic", api_key="test")
        assert provider.config.model == "claude-3-5-sonnet-20241022"

    @patch.dict(
        os.environ,
        {
            "DGI_LLM_PROVIDER": "anthropic",
            "DGI_LLM_MODEL": "claude-3-5-haiku-20241022",
        },
    )
    def test_create_provider_from_env(self):
        """Test creating provider from environment variables."""
        provider = create_provider_from_env(api_key="test-key")

        assert isinstance(provider, AnthropicProvider)
        assert provider.config.model == "claude-3-5-haiku-20241022"

    @patch.dict(os.environ, {}, clear=True)
    def test_create_provider_from_env_defaults(self):
        """Test creating provider from env with defaults."""
        provider = create_provider_from_env(api_key="test-key")

        assert isinstance(provider, OpenAIProvider)
        assert provider.config.model == "gpt-4o-mini"

    def test_get_available_providers(self):
        """Test getting available provider information."""
        providers = get_available_providers()

        assert "openai" in providers
        assert "anthropic" in providers

        # Check OpenAI info
        openai_info = providers["openai"]
        assert openai_info["default_model"] == "gpt-4o-mini"
        assert openai_info["api_key_env"] == "OPENAI_API_KEY"
        assert "gpt-4o" in openai_info["supported_models"]
        assert openai_info["capabilities"]["function_calling"] is True

        # Check Anthropic info
        anthropic_info = providers["anthropic"]
        assert anthropic_info["default_model"] == "claude-3-5-sonnet-20241022"
        assert anthropic_info["api_key_env"] == "ANTHROPIC_API_KEY"
        assert "claude-3-5-sonnet-20241022" in anthropic_info["supported_models"]


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""

    def test_provider_creation(self):
        """Test OpenAI provider creation."""
        config = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-4o-mini", api_key="test-key"
        )
        provider = OpenAIProvider(config)

        assert provider.config == config

    def test_invalid_provider_type(self):
        """Test creation with invalid provider type."""
        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,  # Wrong type
            model="gpt-4o-mini",
        )

        with pytest.raises(ValueError, match="Invalid provider type"):
            OpenAIProvider(config)

    def test_validate_api_key(self):
        """Test API key validation."""
        config = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-4o-mini", api_key="test-key"
        )
        provider = OpenAIProvider(config)

        assert provider.validate_api_key() is True

    def test_validate_api_key_missing(self):
        """Test API key validation when missing."""
        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
        )
        provider = OpenAIProvider(config)

        with patch.dict(os.environ, {}, clear=True):
            assert provider.validate_api_key() is False

    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"})
    def test_validate_api_key_from_env(self):
        """Test API key validation from environment."""
        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
        )
        provider = OpenAIProvider(config)

        assert provider.validate_api_key() is True

    def test_get_model_info(self):
        """Test getting model information."""
        config = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-4o-mini", api_key="test-key"
        )
        provider = OpenAIProvider(config)

        info = provider.get_model_info()

        assert info["provider"] == "OpenAI"
        assert info["model"] == "gpt-4o-mini"
        assert info["supports_functions"] is True
        assert info["context_window"] == 128000  # gpt-4o-mini context window
        assert info["pricing_tier"] == "low-cost"

    def test_get_config_summary(self):
        """Test getting configuration summary."""
        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            temperature=0.3,
            max_tokens=1000,
        )
        provider = OpenAIProvider(config)

        summary = provider.get_config_summary()

        assert summary["provider"] == "openai"
        assert summary["model"] == "gpt-4o-mini"
        assert summary["temperature"] == 0.3
        assert summary["max_tokens"] == 1000


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""

    def test_provider_creation(self):
        """Test Anthropic provider creation."""
        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )
        provider = AnthropicProvider(config)

        assert provider.config == config

    def test_invalid_provider_type(self):
        """Test creation with invalid provider type."""
        config = LLMConfig(
            provider=ProviderType.OPENAI,  # Wrong type
            model="claude-3-5-sonnet-20241022",
        )

        with pytest.raises(ValueError, match="Invalid provider type"):
            AnthropicProvider(config)

    def test_validate_api_key(self):
        """Test API key validation."""
        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key="test-key",
        )
        provider = AnthropicProvider(config)

        assert provider.validate_api_key() is True

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"})
    def test_validate_api_key_from_env(self):
        """Test API key validation from environment."""
        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
        )
        provider = AnthropicProvider(config)

        assert provider.validate_api_key() is True

    def test_get_model_info(self):
        """Test getting model information."""
        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-haiku-20241022",
            api_key="test-key",
        )
        provider = AnthropicProvider(config)

        info = provider.get_model_info()

        assert info["provider"] == "Anthropic"
        assert info["model"] == "claude-3-5-haiku-20241022"
        assert info["supports_functions"] is True
        assert info["context_window"] == 200000  # Claude 3.5 context window
        assert info["pricing_tier"] == "low-cost"  # Haiku is low-cost
