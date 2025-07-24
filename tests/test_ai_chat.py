"""Tests for ai_chat modules: screener_tool and chat_demo."""

import pytest
from ai_chat import screener_tool


def test_screen_dividends_basic():
    """Test the screen_dividends tool returns results with default params."""
    results = screener_tool.screen_dividends.invoke({})
    assert isinstance(results, list)
    assert len(results) > 0
    assert "symbol" in results[0]
    assert "score" in results[0]


def test_screen_dividends_top_n():
    """Test the top_n parameter limits results."""
    results = screener_tool.screen_dividends.invoke({"top_n": 2})
    assert len(results) == 2


def test_screen_dividends_filters():
    """Test filtering by min_yield and min_cagr."""
    results = screener_tool.screen_dividends.invoke(
        {"min_yield": 0.03, "min_cagr": 0.05, "top_n": 5}
    )
    for stock in results:
        assert stock["dividend_yield"] >= 0.03
        assert stock["dividend_growth_5y"] >= 0.05


def test_screen_dividends_error(monkeypatch):
    """Test error handling in screen_dividends tool."""
    # Patch Screener.load_universe to raise
    from dgi.screener import Screener

    monkeypatch.setattr(
        Screener, "load_universe", lambda self: (_ for _ in ()).throw(Exception("fail"))
    )
    results = screener_tool.screen_dividends.invoke({})
    assert isinstance(results, list)
    assert "error" in results[0]


def test_chat_demo_import_and_config(monkeypatch):
    """Test importing chat_demo and running show_provider_info."""
    import ai_chat.chat_demo as chat_demo

    # Should not raise
    chat_demo.show_provider_info()


def test_chat_demo_create_dgi_agent_handles_missing_key(monkeypatch):
    """Test create_dgi_agent handles missing API key gracefully."""
    import ai_chat.chat_demo as chat_demo

    # Patch provider to simulate missing key
    class DummyProvider:
        def validate_api_key(self):
            return False

        class config:
            provider = type("P", (), {"value": "openai"})

        def get_model_info(self):
            return {
                "provider": "OpenAI",
                "model": "gpt-4o-mini",
                "context_window": 128000,
                "pricing_tier": "low-cost",
            }

    monkeypatch.setattr(
        chat_demo, "create_provider_from_env", lambda **kwargs: DummyProvider()
    )
    monkeypatch.setattr(
        chat_demo,
        "get_available_providers",
        lambda: {
            "openai": {
                "api_key_env": "OPENAI_API_KEY",
                "default_model": "gpt-4o-mini",
                "supported_models": ["gpt-4o-mini"],
                "capabilities": {},
            }
        },
    )
    with pytest.raises(SystemExit):
        chat_demo.create_dgi_agent()


def test_chat_demo_demo_queries():
    import ai_chat.chat_demo as chat_demo

    queries = chat_demo.demo_queries()
    assert isinstance(queries, list)
    assert any("dividend" in q.lower() for q in queries)


def test_chat_demo_show_provider_info_runs():
    import ai_chat.chat_demo as chat_demo

    chat_demo.show_provider_info()
