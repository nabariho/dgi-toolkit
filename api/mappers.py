"""Data mappers for DGI Toolkit API."""

import time
from typing import Any

import pandas as pd

from .logging_config import get_logger
from .schemas.responses import ScreenResponse, StockResponse

logger = get_logger(__name__)


class StockMapper:
    """Mapper for converting between business logic and API data structures."""

    @staticmethod
    def dataframe_to_stock_response(df_row: pd.Series) -> StockResponse:
        """Convert DataFrame row to StockResponse.

        Args:
            df_row: Pandas Series containing stock data

        Returns:
            StockResponse instance

        Raises:
            ValueError: If required fields are missing or invalid
        """
        try:
            return StockResponse(
                symbol=str(df_row["symbol"]),
                name=str(df_row["name"]),
                sector=str(df_row["sector"]),
                industry=str(df_row["industry"]),
                dividend_yield=float(df_row["dividend_yield"]),
                payout=float(df_row["payout"]),
                dividend_cagr=float(df_row["dividend_cagr"]),
                fcf_yield=float(df_row["fcf_yield"]),
                score=float(df_row["score"]),
            )
        except KeyError as e:
            raise ValueError(f"Missing required field in DataFrame: {e}") from e
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid data type in DataFrame: {e}") from e

    @staticmethod
    def dataframe_to_stock_responses(df: pd.DataFrame) -> list[StockResponse]:
        """Convert DataFrame to list of StockResponse objects.

        Args:
            df: Pandas DataFrame containing stock data

        Returns:
            List of StockResponse instances
        """
        if df.empty:
            return []

        stocks = []
        for _, row in df.iterrows():
            try:
                stock = StockMapper.dataframe_to_stock_response(row)
                stocks.append(stock)
            except ValueError as e:
                logger.warning(f"Skipping invalid stock row: {e}")
                continue

        return stocks

    @staticmethod
    def validate_dataframe_structure(df: pd.DataFrame) -> bool:
        """Validate that DataFrame has required columns for stock data.

        Args:
            df: Pandas DataFrame to validate

        Returns:
            True if valid, False otherwise
        """
        required_columns = {
            "symbol",
            "name",
            "sector",
            "industry",
            "dividend_yield",
            "payout",
            "dividend_cagr",
            "fcf_yield",
            "score",
        }

        missing_columns = required_columns - set(df.columns)
        if missing_columns:
            logger.error(f"DataFrame missing required columns: {missing_columns}")
            return False

        return True


class ScreenResponseMapper:
    """Mapper for creating screen response with metadata."""

    @staticmethod
    def create_screen_response(
        stocks: list[StockResponse],
        filters_applied: dict[str, Any],
        processing_time_ms: float | None = None,
    ) -> ScreenResponse:
        """Create a complete screen response.

        Args:
            stocks: List of stock responses
            filters_applied: Dictionary of filters that were applied
            processing_time_ms: Request processing time in milliseconds

        Returns:
            ScreenResponse instance
        """
        return ScreenResponse(
            stocks=stocks,
            total_count=len(stocks),
            filters_applied=filters_applied,
            processing_time_ms=processing_time_ms,
        )

    @staticmethod
    def create_filters_dict(
        min_yield: float,
        max_payout: float,
        min_cagr: float,
        top_n: int,
    ) -> dict[str, Any]:
        """Create filters dictionary for response.

        Args:
            min_yield: Minimum dividend yield
            max_payout: Maximum payout ratio
            min_cagr: Minimum dividend CAGR
            top_n: Number of top stocks

        Returns:
            Dictionary of applied filters
        """
        return {
            "min_yield": min_yield,
            "max_payout": max_payout,
            "min_cagr": min_cagr,
            "top_n": top_n,
        }


class PerformanceTracker:
    """Utility for tracking request processing time."""

    def __init__(self):
        """Initialize performance tracker."""
        self.start_time = None

    def start(self) -> None:
        """Start timing."""
        self.start_time = time.time()

    def end(self) -> float:
        """End timing and return elapsed time in milliseconds.

        Returns:
            Elapsed time in milliseconds
        """
        if self.start_time is None:
            return 0.0

        elapsed_seconds = time.time() - self.start_time
        return elapsed_seconds * 1000  # Convert to milliseconds
