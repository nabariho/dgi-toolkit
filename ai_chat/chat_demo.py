"""Chat demo script for DGI toolkit with GPT-4o integration.

This script demonstrates how to use GPT-4o with the DGI screener tool
to answer natural language questions about dividend growth investing.
"""

import os
import sys
from typing import List
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI
from langchain.tools import BaseTool
from ai_chat.screener_tool import screen_dividends


def create_dgi_agent() -> any:
    """Create a LangChain agent with DGI screening capabilities."""

    # Check for OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable is required")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Initialize GPT-4o-mini for cost efficiency (as per tech notes)
    model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(
        model=model_name,
        temperature=0.1,  # Low temperature for consistent financial analysis
        timeout=30,  # Keep timeouts low for CI efficiency
        max_retries=2,
    )

    # Create agent with DGI screening tool
    tools: List[BaseTool] = [screen_dividends]

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,  # Show reasoning steps
        handle_parsing_errors=True,
        max_iterations=3,  # Limit iterations for cost control
    )

    return agent


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
    print("Initializing GPT-4o agent with DGI screening capabilities...")

    try:
        agent = create_dgi_agent()
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
