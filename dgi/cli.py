import json
import logging

import typer

from dgi.cli_helpers import render_screen_table
from dgi.config import get_config
from dgi.filtering import DefaultFilter
from dgi.models.company import CompanyData
from dgi.portfolio import build
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.scoring import DefaultScoring
from dgi.screener import Screener
from dgi.validation import DgiRowValidator, PydanticRowValidation

config = get_config()


# Structured logging setup
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logging.basicConfig(level=config.LOG_LEVEL, handlers=[handler])

app = typer.Typer(help="DGI Toolkit CLI: screen stocks and build portfolios.")


@app.command()
def screen(
    min_yield: float = typer.Option(0.02, help="Minimum dividend yield"),
    max_payout: float = typer.Option(80.0, help="Maximum payout ratio (percentage)"),
    min_cagr: float = typer.Option(0.05, help="Minimum dividend CAGR"),
    csv_path: str | None = typer.Option(
        None, help="Path to CSV file (defaults to config)"
    ),
) -> None:
    """Screen companies using DGI criteria and display results in a rich table."""
    # Parameter validation
    if min_yield < 0 or max_payout < 0 or min_cagr < 0:
        typer.echo(
            "[ERROR] min_yield, max_payout, and min_cagr must all be non-negative.",
            err=True,
        )
        raise typer.Exit(code=1)
    try:
        # Just check if rich is available by trying to import it
        import rich  # noqa: F401
    except ImportError:
        typer.echo(
            "[ERROR] The 'rich' package is required for table output. Please install it.",
            err=True,
        )
        raise typer.Exit(code=1)
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    data_path = csv_path or config.DATA_PATH  # Use provided path or default
    repo = CsvCompanyDataRepository(data_path, validator)
    screener = Screener(
        repo, scoring_strategy=DefaultScoring(), filter_strategy=DefaultFilter()
    )

    try:
        df = screener.load_universe()
        filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)
        scored = screener.add_scores(filtered)
        if scored.empty:
            typer.echo("[INFO] No stocks matched the filter criteria.")
            raise typer.Exit(code=0)
        scored = scored.sort_values("score", ascending=False)
        render_screen_table(scored)
    except Exception as e:
        typer.echo(f"[ERROR] {e}", err=True)
        raise typer.Exit(code=1)


@app.command()
def build_portfolio(
    csv_path: str = typer.Option(config.DATA_PATH, help="Path to fundamentals CSV"),
    top_n: int = typer.Option(10, help="Number of stocks in portfolio"),
    weighting: str = typer.Option("equal", help="Weighting method: 'equal' or 'score'"),
    min_yield: float = typer.Option(
        config.DEFAULT_MIN_YIELD, help="Minimum dividend yield"
    ),
    max_payout: float = typer.Option(
        config.DEFAULT_MAX_PAYOUT, help="Maximum payout ratio"
    ),
    min_cagr: float = typer.Option(
        config.DEFAULT_MIN_CAGR, help="Minimum dividend CAGR"
    ),
) -> None:
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    repo = CsvCompanyDataRepository(csv_path, validator)
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
