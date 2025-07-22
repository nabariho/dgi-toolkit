# screener.py

import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel, ValidationError, validator
from typing import List, Dict, Any
import logging

# from typing import Any  # Remove unused import

logger = logging.getLogger(__name__)


class DgiRow(BaseModel):
    symbol: str
    name: str
    sector: str
    industry: str
    dividend_yield: float
    payout: float
    dividend_cagr: float
    fcf_yield: float

    @validator("dividend_yield", "payout", "dividend_cagr", "fcf_yield", pre=True)
    def must_be_number(cls, v: Any) -> float:
        if isinstance(v, (int, float)):
            return float(v)
        try:
            return float(v)
        except Exception:
            raise ValueError(f"Value '{v}' is not a valid number")


def load_universe(csv_path: str = "data/fundamentals_small.csv") -> DataFrame:
    """
    Load the raw fundamentals universe for dividend growth investing analysis.

    Business use:
    This function ingests a CSV of stock fundamentals (including yield, payout,
    and dividend CAGR) into a DataFrame for further screening and analysis. It
    ensures all columns are loaded with the correct types, providing a reliable
    starting point for building DGI watchlists and running filters.

    Expects columns: symbol, name, sector, industry, dividend_yield, payout,
    dividend_cagr, fcf_yield
    Raises ValueError if any validation fails
    """
    required_columns = [
        "symbol",
        "name",
        "sector",
        "industry",
        "dividend_yield",
        "payout",
        "dividend_cagr",
        "fcf_yield",
    ]
    df_raw = pd.read_csv(csv_path, dtype=str)  # Load all as str for validation
    missing = [col for col in required_columns if col not in df_raw.columns]
    if missing:
        ms = ", ".join(missing)
        logger.error("Missing columns: %s", ms)
        em = f"Missing required columns in CSV: {ms}"
        raise ValueError(em)

    valid_rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    for row_num, (_, row) in enumerate(df_raw.iterrows(), start=2):
        try:
            validated = DgiRow(**row.to_dict())
            valid_rows.append(validated.dict())
        except ValidationError as e:
            error_msg = f"Row {row_num}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
    if errors:
        logger.error(
            "CSV validation errors found in %s:\n%s",
            csv_path,
            "\n".join(errors),
        )
        raise ValueError("CSV validation errors:\n" + "\n".join(errors))
    logger.info(f"Successfully loaded {len(valid_rows)} valid rows from {csv_path}")
    return pd.DataFrame(valid_rows)


def apply_filters(
    df: DataFrame,
    min_yield: float = 0.0,
    max_payout: float = 100.0,
    min_cagr: float = 0.0,
) -> DataFrame:
    """
    Filter stocks by key dividend growth criteria for DGI portfolio selection.

    Business use:
    This function screens the universe for stocks that meet minimum yield,
    maximum payout ratio, and minimum dividend CAGR requirements. It helps
    analysts and investors quickly narrow down to candidates that fit a DGI
    strategy, supporting repeatable, rules-based watchlist construction.
    """
    filtered = df[
        (df["dividend_yield"] >= min_yield)
        & (df["payout"] <= max_payout)
        & (df["dividend_cagr"] >= min_cagr)
    ]
    return filtered


def score(row: pd.Series[Any]) -> float:
    """
    Calculate a composite score for DGI stock quality based on growth, payout,
    and free cash flow yield.

    Business use:
    This scoring function enables ranking and comparison of stocks by combining
    dividend growth (CAGR), free cash flow yield, and payout ratio into a single
    normalized metric. It supports quantitative screening, ranking, and
    prioritization of DGI candidates for further research or portfolio inclusion.
    """
    cagr_norm = min(max(row["dividend_cagr"] / 20.0, 0.0), 1.0)
    fcf_norm = min(max(row["fcf_yield"] / 20.0, 0.0), 1.0)
    payout_norm = min(max(row["payout"] / 100.0, 0.0), 1.0)
    composite = cagr_norm + fcf_norm - payout_norm
    composite = composite / 3.0
    result = max(0.0, min(composite, 1.0))
    return float(result)
