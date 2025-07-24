"""Interactive chat demo with DGI Toolkit LLM providers."""

import os
import sys
from typing import Any

# Add the parent directory to Python path to import dgi modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.table import Table
except ImportError:
    print("Please install rich: pip install rich")
    sys.exit(1)

try:
    from dgi.providers.factory import create_provider_from_env, get_available_providers
except ImportError as e:
    print(f"Error importing DGI modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

console = Console()


def show_welcome() -> None:
    """Display welcome message and instructions."""
    welcome_text = """
    🤖 Welcome to DGI Toolkit AI Chat Demo!

    This demo showcases the LLM provider integration capabilities.
    You can chat with different AI models and ask about dividend growth investing.

    Commands:
    • Type your questions naturally
    • Type 'quit' or 'exit' to end the session
    • Type 'help' for more information
    • Type 'info' to see current provider details
    """

    console.print(
        Panel(welcome_text, title="🎯 DGI Toolkit Chat Demo", border_style="cyan")
    )


def show_provider_info(provider: Any) -> None:
    """Display information about the current provider."""
    try:
        config_summary = provider.get_config_summary()
        model_info = provider.get_model_info()

        table = Table(title="Current Provider Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        # Add config information
        for key, value in config_summary.items():
            table.add_row(str(key).replace("_", " ").title(), str(value))

        # Add model information
        for key, value in model_info.items():
            if key not in config_summary:  # Avoid duplicates
                table.add_row(str(key).replace("_", " ").title(), str(value))

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error getting provider info: {e}[/red]")


def run_chat_demo() -> None:
    """Run the interactive chat demonstration."""
    show_welcome()

    try:
        # Create provider from environment variables
        provider = create_provider_from_env()
        console.print(
            f"[green]✅ Successfully initialized {provider.config.provider.value} provider[/green]"
        )

        # Validate API key
        if not provider.validate_api_key():
            console.print(
                "[red]❌ Invalid or missing API key. Please check your environment variables.[/red]"
            )
            console.print("\nRequired environment variables:")
            for provider_type, env_var in [
                ("OpenAI", "OPENAI_API_KEY"),
                ("Anthropic", "ANTHROPIC_API_KEY"),
            ]:
                console.print(f"  • {env_var} (for {provider_type})")
            return

        console.print("[green]✅ API key validated successfully[/green]")

        # Show initial provider info
        show_provider_info(provider)

        # Create a simple agent (you might want to add actual tools here)
        tools: list[Any] = []  # Empty for now, can be extended with DGI-specific tools

        try:
            agent = provider.create_agent(tools, verbose=True)
            console.print("[green]✅ Agent created successfully[/green]")
        except Exception as e:
            console.print(f"[red]❌ Error creating agent: {e}[/red]")
            return

        console.print(
            "\n[cyan]💬 Chat session started! Type your questions below:[/cyan]"
        )

        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]")

                if user_input.lower() in ["quit", "exit", "bye"]:
                    console.print("[yellow]👋 Goodbye![/yellow]")
                    break
                elif user_input.lower() == "help":
                    console.print(
                        """
[cyan]Available commands:[/cyan]
• Ask any question about dividend growth investing
• 'info' - Show current provider configuration
• 'quit'/'exit' - End the chat session

[cyan]Example questions:[/cyan]
• "What makes a good dividend growth stock?"
• "How do I calculate dividend yield?"
• "What's the difference between dividend yield and dividend growth?"
                    """
                    )
                    continue
                elif user_input.lower() == "info":
                    show_provider_info(provider)
                    continue

                # Process the query with the agent
                console.print("[yellow]🤔 Thinking...[/yellow]")

                try:
                    # Use the agent to process the query
                    response = agent.run(user_input)

                    # Display the response
                    console.print(
                        Panel(response, title="🤖 AI Response", border_style="green")
                    )

                except Exception as e:
                    console.print(f"[red]❌ Error processing query: {e}[/red]")
                    console.print(
                        "[yellow]💡 Try rephrasing your question or check your API limits.[/yellow]"
                    )

            except KeyboardInterrupt:
                console.print("\n[yellow]👋 Chat interrupted. Goodbye![/yellow]")
                break
            except Exception as e:
                console.print(f"[red]❌ Unexpected error: {e}[/red]")
                break

    except Exception as e:
        console.print(f"[red]❌ Failed to initialize provider: {e}[/red]")
        console.print(
            "\n[yellow]💡 Make sure you have set the required environment variables:[/yellow]"
        )

        # Show available providers and their requirements
        available = get_available_providers()
        for provider_name, info in available.items():
            console.print(f"  • {provider_name.upper()}: Set {info['api_key_env']}")


if __name__ == "__main__":
    run_chat_demo()
