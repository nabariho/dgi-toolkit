import subprocess
import sys
from typing import Any

from dgi.models import CompanyData
from dgi.portfolio import build, summary_stats
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.screener import Screener
from dgi.validation import DgiRowValidator, PydanticRowValidation


def test_cli_help_runs() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "dgi.cli", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Usage" in result.stdout or "usage" in result.stdout


def test_integration_csv_to_portfolio(tmp_path: Any) -> None:
    csv = tmp_path / "integration.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,2.0,40,5,4\n"
        "MSFT,Microsoft,Tech,Software,3.0,50,6,5\n"
        "GOOG,Google,Tech,Software,4.0,60,7,6\n"
    )
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    repo = CsvCompanyDataRepository(str(csv), validator)
    screener = Screener(repo)
    df = screener.load_universe()
    filtered = screener.apply_filters(df, min_yield=2.0, max_payout=60, min_cagr=5.0)
    scored = screener.add_scores(filtered)
    port = build(scored, top_n=2, weighting="score")
    # Merge to get all columns for stats
    merged = port.merge(scored, left_on="ticker", right_on="symbol", how="left")
    stats = summary_stats(merged)
    assert port.shape[0] == 2
    assert "ticker" in port.columns
    assert stats["yield"] > 0
    assert stats["median_cagr"] > 0
    assert stats["mean_payout"] > 0


def test_cli_screen_and_build_portfolio(tmp_path: Any) -> None:
    csv = tmp_path / "cli_integration.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,2.0,40,5,4\n"
        "MSFT,Microsoft,Tech,Software,3.0,50,6,5\n"
        "GOOG,Google,Tech,Software,4.0,60,7,6\n"
    )
    # Test screen command
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dgi.cli",
            "screen",
            "--csv-path",
            str(csv),
            "--min-yield",
            "2.0",
            "--max-payout",
            "60",
            "--min-cagr",
            "5.0",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "AAPL" in result.stdout or "MSFT" in result.stdout or "GOOG" in result.stdout
    # Test build_portfolio command
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dgi.cli",
            "build-portfolio",
            "--csv-path",
            str(csv),
            "--top-n",
            "2",
            "--weighting",
            "score",
            "--min-yield",
            "2.0",
            "--max-payout",
            "60",
            "--min-cagr",
            "5.0",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "ticker" in result.stdout


def test_cli_screen_rich_table_output(tmp_path: Any) -> None:
    csv = tmp_path / "rich_table.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,2.0,40,5,4\n"
        "MSFT,Microsoft,Tech,Software,3.0,50,6,5\n"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dgi.cli",
            "screen",
            "--csv-path",
            str(csv),
            "--min-yield",
            "2.0",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    # Check for Rich table headers and at least one row
    assert "DGI Screen Results" in result.stdout
    assert "Symbol" in result.stdout
    assert "AAPL" in result.stdout or "MSFT" in result.stdout


def test_cli_screen_bad_param(tmp_path: Any) -> None:
    csv = tmp_path / "bad_param.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,2.0,40,5,4\n"
    )
    # Use an invalid parameter (e.g., negative min-yield)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "dgi.cli",
            "screen",
            "--csv-path",
            str(csv),
            "--min-yield",
            "-1.0",
        ],
        capture_output=True,
        text=True,
    )
    # Should exit with code 1 and print an error
    assert (
        result.returncode == 1
        or "[ERROR]" in result.stdout
        or "[ERROR]" in result.stderr
    )
