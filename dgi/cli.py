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
):
    repo = CsvCompanyDataRepository(csv_path, DgiRowValidator())
    screener = Screener(
        repo, scoring_strategy=DefaultScoring(), filter_strategy=DefaultFilter()
    )
    df = screener.load_universe()
    filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)
    typer.echo(filtered)


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
):
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
