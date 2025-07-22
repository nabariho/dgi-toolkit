import typer
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.validation import DgiRowValidator
from dgi.scoring import DefaultScoring
from dgi.filtering import DefaultFilter
from dgi.screener import Screener
from dgi.portfolio import build

app = typer.Typer(help="DGI Toolkit CLI: screen stocks and build portfolios.")


@app.command()
def screen(
    csv_path: str = typer.Option(
        "data/fundamentals_small.csv", help="Path to fundamentals CSV"
    ),
    min_yield: float = typer.Option(0.0, help="Minimum dividend yield"),
    max_payout: float = typer.Option(100.0, help="Maximum payout ratio"),
    min_cagr: float = typer.Option(0.0, help="Minimum dividend CAGR"),
):
    """
    Screen stocks from a fundamentals CSV using DGI criteria.
    """
    repo = CsvCompanyDataRepository(csv_path, DgiRowValidator())
    screener = Screener(
        repo, scoring_strategy=DefaultScoring(), filter_strategy=DefaultFilter()
    )
    df = screener.load_universe()
    filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)
    typer.echo(filtered)


@app.command()
def build_portfolio(
    csv_path: str = typer.Option(
        "data/fundamentals_small.csv", help="Path to fundamentals CSV"
    ),
    top_n: int = typer.Option(10, help="Number of stocks in portfolio"),
    weighting: str = typer.Option("equal", help="Weighting method: 'equal' or 'score'"),
    min_yield: float = typer.Option(0.0, help="Minimum dividend yield"),
    max_payout: float = typer.Option(100.0, help="Maximum payout ratio"),
    min_cagr: float = typer.Option(0.0, help="Minimum dividend CAGR"),
):
    """
    Build a DGI portfolio from a fundamentals CSV.
    """
    repo = CsvCompanyDataRepository(csv_path, DgiRowValidator())
    screener = Screener(
        repo, scoring_strategy=DefaultScoring(), filter_strategy=DefaultFilter()
    )
    df = screener.load_universe()
    filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)
    scored = screener.add_scores(filtered)
    port = build(scored, top_n, weighting)
    typer.echo(port)


if __name__ == "__main__":
    app()
