import pandas as pd


def render_screen_table(df: pd.DataFrame) -> None:
    try:
        from rich import box
        from rich.console import Console
        from rich.table import Table
    except ImportError:
        print(
            "[ERROR] The 'rich' package is required for table output. Please install it."
        )
        return
    table = Table(title="DGI Screen Results", box=box.SIMPLE_HEAVY)
    table.add_column("Symbol", style="bold cyan")
    table.add_column("Name", style="white")
    table.add_column("Yield", style="green", justify="right")
    table.add_column("Payout", style="magenta", justify="right")
    table.add_column("CAGR", style="yellow", justify="right")
    table.add_column("FCF Yield", style="blue", justify="right")
    table.add_column("Score", style="bold bright_white", justify="right")
    for _, row in df.iterrows():
        table.add_row(
            str(row["symbol"]),
            str(row["name"]),
            f"{row['dividend_yield']:.2f}",
            f"{row['payout']:.2f}",
            f"{row['dividend_cagr']:.2f}",
            f"{row['fcf_yield']:.2f}",
            f"[bold]{row['score']:.3f}[/bold]",
        )
    console = Console()
    console.print(table)
