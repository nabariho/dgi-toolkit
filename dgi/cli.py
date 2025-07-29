import json
import logging

import typer

from dgi.cli_helpers import render_screen_table
from dgi.config import get_config
from dgi.factory import create_repository, create_screener
from dgi.portfolio import build
from dgi.services.validation_service import ValidationService

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
    min_yield: float = typer.Option(
        config.DEFAULT_MIN_YIELD, help="Minimum dividend yield"
    ),
    max_payout: float = typer.Option(
        config.DEFAULT_MAX_PAYOUT, help="Maximum payout ratio (percentage)"
    ),
    min_cagr: float = typer.Option(
        config.DEFAULT_MIN_CAGR, help="Minimum dividend CAGR"
    ),
    csv_path: str | None = typer.Option(
        None, help="Path to CSV file (defaults to config)"
    ),
) -> None:
    """Screen companies using DGI criteria and display results in a rich table."""
    try:
        # Comprehensive input validation using service layer
        min_yield = ValidationService.validate_yield_rate(min_yield, "min_yield")
        max_payout = ValidationService.validate_percentage(max_payout, "max_payout")
        min_cagr = ValidationService.validate_cagr(min_cagr, "min_cagr")

        # Validate file path if provided
        if csv_path:
            csv_path = ValidationService.validate_file_path(
                csv_path, allowed_extensions=[".csv"]
            )

        # Check if rich is available
        import rich  # noqa: F401
    except ImportError as e:
        typer.echo(
            "[ERROR] The 'rich' package is required for table output. Please install it.",
            err=True,
        )
        raise typer.Exit(code=1) from e
    except ValueError as e:
        typer.echo(f"[ERROR] Validation error: {e!s}", err=True)
        raise typer.Exit(code=1) from e

    data_path = csv_path or config.DATA_PATH  # Use provided path or default

    try:
        # Log sanitized inputs for debugging
        logging.info(
            f"Screening with parameters: min_yield={ValidationService.sanitize_for_logging(str(min_yield))}, "
            f"max_payout={ValidationService.sanitize_for_logging(str(max_payout))}, "
            f"min_cagr={ValidationService.sanitize_for_logging(str(min_cagr))}, "
            f"data_path={ValidationService.sanitize_for_logging(data_path)}"
        )

        # Use factory to create dependencies with proper interfaces
        repo = create_repository(data_path, "production")
        screener = create_screener(repo, factory_name="production")

        # Load data and apply screening pipeline
        df = screener.load_universe()
        filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)
        scored = screener.add_scores(filtered)

        if scored.empty:
            typer.echo("[INFO] No companies match the screening criteria.")
            return

        # Sort by score descending
        result = scored.sort_values("score", ascending=False)
        render_screen_table(result)

    except FileNotFoundError as e:
        typer.echo(
            f"[ERROR] CSV file not found: {ValidationService.sanitize_for_logging(data_path)}. Please check the file path.",
            err=True,
        )
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(
            f"[ERROR] {ValidationService.sanitize_for_logging(str(e))}", err=True
        )
        raise typer.Exit(code=1) from e


@app.command()
def build_portfolio(
    csv_path: str = typer.Option(config.DATA_PATH, help="Path to fundamentals CSV"),
    top_n: int = typer.Option(
        config.DEFAULT_TOP_N, help="Number of stocks in portfolio"
    ),
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
    try:
        # Comprehensive input validation using service layer
        csv_path = ValidationService.validate_file_path(
            csv_path, allowed_extensions=[".csv"]
        )
        top_n = ValidationService.validate_portfolio_size(top_n, "top_n")
        weighting = ValidationService.validate_weighting_method(weighting, "weighting")
        min_yield = ValidationService.validate_yield_rate(min_yield, "min_yield")
        max_payout = ValidationService.validate_percentage(max_payout, "max_payout")
        min_cagr = ValidationService.validate_cagr(min_cagr, "min_cagr")

        # Log sanitized inputs for debugging
        logging.info(
            f"Building portfolio with parameters: csv_path={ValidationService.sanitize_for_logging(csv_path)}, "
            f"top_n={ValidationService.sanitize_for_logging(str(top_n))}, weighting={ValidationService.sanitize_for_logging(weighting)}, "
            f"min_yield={ValidationService.sanitize_for_logging(str(min_yield))}, max_payout={ValidationService.sanitize_for_logging(str(max_payout))}, "
            f"min_cagr={ValidationService.sanitize_for_logging(str(min_cagr))}"
        )

    except ValueError as e:
        typer.echo(f"[ERROR] Validation error: {e!s}", err=True)
        raise typer.Exit(code=1) from e

    try:
        # Use factory to create dependencies
        repo = create_repository(csv_path, "production")
        screener = create_screener(repo, factory_name="production")
        df = screener.load_universe()
        filtered = screener.apply_filters(df, min_yield, max_payout, min_cagr)
        scored = screener.add_scores(filtered)
        port = build(scored, top_n, weighting)
        typer.echo(port)
    except FileNotFoundError as e:
        typer.echo(
            f"[ERROR] CSV file not found: {ValidationService.sanitize_for_logging(csv_path)}. Please check the file path.",
            err=True,
        )
        raise typer.Exit(code=1) from e
    except Exception as e:
        typer.echo(
            f"[ERROR] {ValidationService.sanitize_for_logging(str(e))}", err=True
        )
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
