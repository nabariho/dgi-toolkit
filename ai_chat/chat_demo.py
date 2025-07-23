"""Chat demo script for DGI toolkit with configurable LLM providers.

This script demonstrates how to use different LLM providers (OpenAI, Anthropic)
with the DGI screener tool to answer natural language questions about dividend growth investing.
"""

import os
import sys
from typing import List
from dgi.providers import create_provider_from_env, get_available_providers
from ai_chat.screener_tool import screen_dividends


def create_dgi_agent() -> any:
    """Create a LangChain agent with DGI screening capabilities."""

    try:
        # Create provider from environment configuration
        provider = create_provider_from_env(
            temperature=0.1,  # Low temperature for consistent financial analysis
            timeout=30,  # Keep timeouts low for CI efficiency
            max_retries=2,
        )

        # Validate API key
        if not provider.validate_api_key():
            available = get_available_providers()
            provider_info = available[provider.config.provider.value]
            api_key_env = provider_info["api_key_env"]

            print(f"❌ ERROR: {api_key_env} environment variable is required")
            print(f"Please set your {provider.config.provider.value} API key:")
            print(f"export {api_key_env}='your-api-key-here'")
            sys.exit(1)

        # Display provider information
        model_info = provider.get_model_info()
        print(f"🔧 Using {model_info['provider']} - {model_info['model']}")
        print(
            f"   Context: {model_info['context_window']:,} tokens | Tier: {model_info['pricing_tier']}"
        )

        # Create agent with DGI screening tool
        tools = [screen_dividends]

        agent = provider.create_agent(tools)

        return agent, provider

    except Exception as e:
        print(f"❌ Failed to create provider: {e}")
        print("\n💡 Available providers:")
        available = get_available_providers()
        for name, info in available.items():
            print(f"   {name}: {info['api_key_env']} required")
        sys.exit(1)


def show_provider_info():
    """Display information about available providers and current configuration."""
    print("🔧 Provider Configuration")
    print("-" * 30)

    # Show current environment settings
    current_provider = os.getenv("DGI_LLM_PROVIDER", "openai")
    current_model = os.getenv("DGI_LLM_MODEL", "default")

    print(f"Current Provider: {current_provider}")
    print(f"Current Model: {current_model}")
    print()

    # Show available options
    available = get_available_providers()
    print("📋 Available Providers:")
    for name, info in available.items():
        status = "✅" if os.getenv(info["api_key_env"]) else "❌"
        print(f"  {status} {name.upper()}")
        print(f"     Default: {info['default_model']}")
        print(f"     API Key: {info['api_key_env']}")
        print(f"     Models: {', '.join(info['supported_models'][:3])}...")
        print()

    print("⚙️  To switch providers:")
    print("export DGI_LLM_PROVIDER=anthropic")
    print("export DGI_LLM_MODEL=claude-3-5-haiku-20241022")
    print()


def demo_queries() -> List[str]:
    """Get demonstration queries for the DGI agent."""
    return [
        "Show me technology stocks with at least 5% five-year dividend CAGR",
        "Find the top 5 dividend stocks with yield above 3% and payout ratio below 60%",
        "What are the best dividend growth stocks in the current data?",
        "Screen for conservative dividend stocks with low payout ratios under 50%",
    ]


def run_chat_demo():
    """Run the interactive chat demo."""
    print("🚀 DGI Toolkit AI Chat Demo")
    print("=" * 50)

    # Show provider configuration
    show_provider_info()

    print("Initializing AI agent with DGI screening capabilities...")

    try:
        agent, provider = create_dgi_agent()
        print("✅ Agent initialized successfully!")
        print()

        # Show available demo queries
        queries = demo_queries()
        print("💡 Try these example queries:")
        for i, query in enumerate(queries, 1):
            print(f"  {i}. {query}")
        print()

        # Interactive loop
        while True:
            print("-" * 50)
            user_input = input(
                "🤖 Ask about dividend stocks (or 'quit' to exit): "
            ).strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Thanks for using DGI Toolkit AI Chat!")
                break

            if user_input.lower() in ["config", "providers"]:
                show_provider_info()
                continue

            if not user_input:
                continue

            try:
                print(f"\n🔍 Processing: {user_input}")
                print("🧠 AI Reasoning:")

                # Run the agent
                response = agent.run(user_input)

                print("\n📊 Final Answer:")
                print(response)
                print()

            except Exception as e:
                print(f"\n❌ Error processing query: {e}")
                print("Please try rephrasing your question or check your API key.")
                print()

    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_chat_demo()
