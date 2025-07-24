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

    def test_openai_provider_error_on_missing_api_key(self, monkeypatch):
        """Test OpenAIProvider raises ValueError if API key is missing."""
        from dgi.providers.openai_provider import OpenAIProvider
        from dgi.providers.base import LLMConfig, ProviderType

        config = LLMConfig(provider=ProviderType.OPENAI, model="gpt-4o-mini")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        provider = OpenAIProvider(config)
        # Should raise when accessing .client
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            _ = provider.client

    def test_openai_provider_extra_params(self):
        """Test OpenAIProvider passes extra_params to client."""
        from dgi.providers.openai_provider import OpenAIProvider
        from dgi.providers.base import LLMConfig, ProviderType

        config = LLMConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            api_key="test",
            extra_params={"foo": "bar"},
        )
        provider = OpenAIProvider(config)
        # Should not raise
        _ = provider.client

    def test_openai_provider_agent_kwargs(self):
        """Test OpenAIProvider.create_agent accepts extra kwargs."""
        from dgi.providers.openai_provider import OpenAIProvider
        from dgi.providers.base import LLMConfig, ProviderType

        config = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-4o-mini", api_key="test"
        )
        provider = OpenAIProvider(config)
        agent = provider.create_agent([], verbose=False, max_iterations=1)
        assert agent is not None

    def test_openai_provider_context_and_pricing_tiers(self):
        from dgi.providers.openai_provider import OpenAIProvider
        from dgi.providers.base import LLMConfig, ProviderType

        config = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-4-turbo", api_key="test"
        )
        provider = OpenAIProvider(config)
        assert provider._get_context_window() == 128000
        config2 = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-3.5-turbo", api_key="test"
        )
        provider2 = OpenAIProvider(config2)
        assert provider2._get_context_window() == 16385
        config3 = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-unknown", api_key="test"
        )
        provider3 = OpenAIProvider(config3)
        assert provider3._get_context_window() == 4096
        assert provider._get_pricing_tier() == "premium"
        config4 = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-4o-mini", api_key="test"
        )
        provider4 = OpenAIProvider(config4)
        assert provider4._get_pricing_tier() == "low-cost"
        config5 = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-3.5-turbo", api_key="test"
        )
        provider5 = OpenAIProvider(config5)
        assert provider5._get_pricing_tier() == "standard"


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

    def test_anthropic_provider_error_on_missing_api_key(self, monkeypatch):
        """Test AnthropicProvider raises ValueError if API key is missing."""
        from dgi.providers.anthropic_provider import AnthropicProvider
        from dgi.providers.base import LLMConfig, ProviderType

        config = LLMConfig(
            provider=ProviderType.ANTHROPIC, model="claude-3-5-haiku-20241022"
        )
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        provider = AnthropicProvider(config)
        with pytest.raises(ValueError, match="Anthropic API key is required"):
            _ = provider.client

    def test_anthropic_provider_extra_params(self):
        """Test AnthropicProvider passes extra_params to client."""
        from dgi.providers.anthropic_provider import AnthropicProvider
        from dgi.providers.base import LLMConfig, ProviderType

        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-haiku-20241022",
            api_key="test",
            extra_params={"foo": "bar"},
        )
        provider = AnthropicProvider(config)
        _ = provider.client

    def test_anthropic_provider_agent_kwargs(self):
        """Test AnthropicProvider.create_agent accepts extra kwargs."""
        from dgi.providers.anthropic_provider import AnthropicProvider
        from dgi.providers.base import LLMConfig, ProviderType

        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-haiku-20241022",
            api_key="test",
        )
        provider = AnthropicProvider(config)
        agent = provider.create_agent([], verbose=False, max_iterations=1)
        assert agent is not None

    def test_anthropic_provider_context_and_pricing_tiers(self):
        from dgi.providers.anthropic_provider import AnthropicProvider
        from dgi.providers.base import LLMConfig, ProviderType

        config = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-haiku-20241022",
            api_key="test",
        )
        provider = AnthropicProvider(config)
        assert provider._get_context_window() == 200000
        config2 = LLMConfig(
            provider=ProviderType.ANTHROPIC, model="claude-2.0", api_key="test"
        )
        provider2 = AnthropicProvider(config2)
        assert provider2._get_context_window() == 100000
        assert provider._get_pricing_tier() == "low-cost"
        config3 = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-opus-20240229",
            api_key="test",
        )
        provider3 = AnthropicProvider(config3)
        assert provider3._get_pricing_tier() == "premium"
        config4 = LLMConfig(
            provider=ProviderType.ANTHROPIC,
            model="claude-3-5-sonnet-20241022",
            api_key="test",
        )
        provider4 = AnthropicProvider(config4)
        assert provider4._get_pricing_tier() == "standard"
        config5 = LLMConfig(
            provider=ProviderType.ANTHROPIC, model="claude-unknown", api_key="test"
        )
        provider5 = AnthropicProvider(config5)
        assert provider5._get_pricing_tier() == "standard"


class TestProviderBase:
    def test_llmprovider_abstract_methods(self):
        from dgi.providers.base import LLMProvider, LLMConfig, ProviderType

        class DummyProvider(LLMProvider):
            def _initialize_client(self):
                return "client"

            def create_agent(self, tools, **kwargs):
                return "agent"

            def validate_api_key(self):
                return True

            def get_model_info(self):
                return {"foo": "bar"}

        config = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-4o-mini", api_key="test"
        )
        dummy = DummyProvider(config)
        assert dummy.client == "client"
        assert dummy.create_agent([]) == "agent"
        assert dummy.validate_api_key() is True
        assert dummy.get_model_info()["foo"] == "bar"
        assert isinstance(dummy.get_config_summary(), dict)

    def test_llmprovider_config_summary_keys(self):
        from dgi.providers.base import LLMProvider, LLMConfig, ProviderType

        class DummyProvider(LLMProvider):
            def _initialize_client(self):
                return "client"

            def create_agent(self, tools, **kwargs):
                return "agent"

            def validate_api_key(self):
                return True

            def get_model_info(self):
                return {"foo": "bar"}

        config = LLMConfig(
            provider=ProviderType.OPENAI, model="gpt-4o-mini", api_key="test"
        )
        dummy = DummyProvider(config)
        summary = dummy.get_config_summary()
        assert "provider" in summary and "model" in summary


def test_factory_unsupported_provider():
    from dgi.providers.factory import create_provider
    import pytest

    with pytest.raises(ValueError, match="Unsupported provider"):
        create_provider("notarealprovider")
