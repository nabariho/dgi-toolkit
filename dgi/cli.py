import typer
import logging
import json
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.validation import DgiRowValidator
from dgi.scoring import DefaultScoring
from dgi.filtering import DefaultFilter
from dgi.screener import Screener
from dgi.portfolio import build
from dgi.config import get_config
from dgi.cli_helpers import render_screen_table

config = get_config()


# Structured logging setup
class JsonFormatter(logging.Formatter):
    def format(self, record):
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
    csv_path: str = typer.Option(config.DATA_PATH, help="Path to fundamentals CSV"),
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
    """
    Screen stocks by yield, payout, and dividend CAGR, and display a rich table sorted by score.
    """
    # Parameter validation
    if min_yield < 0 or max_payout < 0 or min_cagr < 0:
        typer.echo(
            "[ERROR] min_yield, max_payout, and min_cagr must all be non-negative.",
            err=True,
        )
        raise typer.Exit(code=1)
    try:
        try:
            # Try importing rich to check if it's available
            import rich  # noqa: F401
        except ImportError:
            typer.echo(
                "[ERROR] The 'rich' package is required for table output. Please install it.",
                err=True,
            )
            raise typer.Exit(code=1)
        repo = CsvCompanyDataRepository(csv_path, DgiRowValidator())
        screener = Screener(
            repo, scoring_strategy=DefaultScoring(), filter_strategy=DefaultFilter()
        )
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
