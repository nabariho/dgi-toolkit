"""Tests for API mappers module."""

import pandas as pd
import pytest

from api.mappers import PerformanceTracker, ScreenResponseMapper, StockMapper
from api.schemas.responses import ScreenResponse, StockResponse


class TestStockMapper:
    """Test StockMapper functionality."""

    def test_dataframe_to_stock_response_valid(self):
        """Test converting valid DataFrame row to StockResponse."""
        # Create a valid DataFrame row
        data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "dividend_yield": 0.005,  # 0.5% as decimal
            "payout": 25.0,
            "dividend_cagr": 0.052,  # 5.2% as decimal (must be <= 1.0)
            "fcf_yield": 3.8,
            "score": 0.85,
        }
        df_row = pd.Series(data)

        # Convert to StockResponse
        result = StockMapper.dataframe_to_stock_response(df_row)

        # Verify result
        assert isinstance(result, StockResponse)
        assert result.symbol == "AAPL"
        assert result.name == "Apple Inc."
        assert result.sector == "Technology"
        assert result.industry == "Consumer Electronics"
        assert result.dividend_yield == 0.005  # 0.5% as decimal
        assert result.payout == 25.0
        assert result.dividend_cagr == 0.052  # 5.2% as decimal
        assert result.fcf_yield == 3.8
        assert result.score == 0.85

    def test_dataframe_to_stock_response_missing_field(self):
        """Test converting DataFrame row with missing field raises ValueError."""
        # Create DataFrame row with missing field
        data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "dividend_yield": 0.5,
            "payout": 25.0,
            "dividend_cagr": 5.2,
            "fcf_yield": 3.8,
            # Missing "score" field
        }
        df_row = pd.Series(data)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Missing required field in DataFrame"):
            StockMapper.dataframe_to_stock_response(df_row)

    def test_dataframe_to_stock_response_invalid_type(self):
        """Test converting DataFrame row with invalid data type raises ValueError."""
        # Create DataFrame row with invalid type
        data = {
            "symbol": "AAPL",
            "name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "dividend_yield": "invalid",  # Should be float
            "payout": 25.0,
            "dividend_cagr": 5.2,
            "fcf_yield": 3.8,
            "score": 0.85,
        }
        df_row = pd.Series(data)

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid data type in DataFrame"):
            StockMapper.dataframe_to_stock_response(df_row)

    def test_dataframe_to_stock_responses_empty(self):
        """Test converting empty DataFrame returns empty list."""
        df = pd.DataFrame()

        result = StockMapper.dataframe_to_stock_responses(df)

        assert result == []

    def test_dataframe_to_stock_responses_valid(self):
        """Test converting valid DataFrame to list of StockResponse objects."""
        # Create valid DataFrame
        data = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "dividend_yield": 0.005,  # 0.5% as decimal
                "payout": 25.0,
                "dividend_cagr": 0.052,  # 5.2% as decimal
                "fcf_yield": 3.8,
                "score": 0.85,
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "sector": "Technology",
                "industry": "Software",
                "dividend_yield": 0.008,  # 0.8% as decimal
                "payout": 30.0,
                "dividend_cagr": 0.061,  # 6.1% as decimal
                "fcf_yield": 4.2,
                "score": 0.92,
            },
        ]
        df = pd.DataFrame(data)

        result = StockMapper.dataframe_to_stock_responses(df)

        # Verify result
        assert len(result) == 2
        assert all(isinstance(stock, StockResponse) for stock in result)
        assert result[0].symbol == "AAPL"
        assert result[1].symbol == "MSFT"

    def test_dataframe_to_stock_responses_with_invalid_rows(self):
        """Test converting DataFrame with some invalid rows skips them."""
        # Create DataFrame with one valid and one invalid row
        data = [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "dividend_yield": 0.005,  # 0.5% as decimal
                "payout": 25.0,
                "dividend_cagr": 0.052,  # 5.2% as decimal
                "fcf_yield": 3.8,
                "score": 0.85,
            },
            {
                "symbol": "INVALID",
                "name": "Invalid Corp",
                "sector": "Technology",
                "industry": "Software",
                "dividend_yield": "invalid",  # Invalid type
                "payout": 30.0,
                "dividend_cagr": 0.061,  # 6.1% as decimal
                "fcf_yield": 4.2,
                "score": 0.92,
            },
        ]
        df = pd.DataFrame(data)

        result = StockMapper.dataframe_to_stock_responses(df)

        # Should only include the valid row
        assert len(result) == 1
        assert result[0].symbol == "AAPL"

    def test_validate_dataframe_structure_valid(self):
        """Test validating DataFrame with all required columns returns True."""
        # Create DataFrame with all required columns
        data = {
            "symbol": ["AAPL"],
            "name": ["Apple Inc."],
            "sector": ["Technology"],
            "industry": ["Consumer Electronics"],
            "dividend_yield": [0.005],  # 0.5% as decimal
            "payout": [25.0],
            "dividend_cagr": [0.052],  # 5.2% as decimal
            "fcf_yield": [3.8],
            "score": [0.85],
        }
        df = pd.DataFrame(data)

        result = StockMapper.validate_dataframe_structure(df)

        assert result is True

    def test_validate_dataframe_structure_missing_columns(self):
        """Test validating DataFrame with missing columns returns False."""
        # Create DataFrame with missing columns
        data = {
            "symbol": ["AAPL"],
            "name": ["Apple Inc."],
            "sector": ["Technology"],
            "industry": ["Consumer Electronics"],
            "dividend_yield": [0.5],
            "payout": [25.0],
            "dividend_cagr": [5.2],
            "fcf_yield": [3.8],
            # Missing "score" column
        }
        df = pd.DataFrame(data)

        result = StockMapper.validate_dataframe_structure(df)

        assert result is False


class TestScreenResponseMapper:
    """Test ScreenResponseMapper functionality."""

    def test_create_screen_response(self):
        """Test creating screen response with all parameters."""
        # Create sample stock responses
        stocks = [
            StockResponse(
                symbol="AAPL",
                name="Apple Inc.",
                sector="Technology",
                industry="Consumer Electronics",
                dividend_yield=0.005,  # 0.5% as decimal
                payout=25.0,
                dividend_cagr=0.052,  # 5.2% as decimal
                fcf_yield=3.8,
                score=0.85,
            ),
            StockResponse(
                symbol="MSFT",
                name="Microsoft Corporation",
                sector="Technology",
                industry="Software",
                dividend_yield=0.008,  # 0.8% as decimal
                payout=30.0,
                dividend_cagr=0.061,  # 6.1% as decimal
                fcf_yield=4.2,
                score=0.92,
            ),
        ]

        filters_applied = {
            "min_yield": 0.003,  # 0.3% as decimal
            "max_payout": 80.0,
            "min_cagr": 0.05,  # 5.0% as decimal
            "top_n": 10,
        }

        processing_time_ms = 150.5

        result = ScreenResponseMapper.create_screen_response(
            stocks, filters_applied, processing_time_ms
        )

        # Verify result
        assert isinstance(result, ScreenResponse)
        assert result.stocks == stocks
        assert result.total_count == 2
        assert result.filters_applied.min_yield == 0.003
        assert result.filters_applied.max_payout == 80.0
        assert result.filters_applied.min_cagr == 0.05
        assert result.filters_applied.top_n == 10
        assert result.processing_time_ms == 150.5

    def test_create_screen_response_no_processing_time(self):
        """Test creating screen response without processing time."""
        stocks = []
        filters_applied = {
            "min_yield": 0.0,
            "max_payout": 100.0,
            "min_cagr": 0.0,
            "top_n": 10,
        }

        result = ScreenResponseMapper.create_screen_response(
            stocks, filters_applied, 0.0
        )

        # Verify result
        assert isinstance(result, ScreenResponse)
        assert result.stocks == []
        assert result.total_count == 0
        assert result.filters_applied.min_yield == 0.0
        assert result.filters_applied.max_payout == 100.0
        assert result.filters_applied.min_cagr == 0.0
        assert result.filters_applied.top_n == 10
        assert result.processing_time_ms == 0.0

    def test_create_filters_dict(self):
        """Test creating filters dictionary."""
        result = ScreenResponseMapper.create_filters_dict(
            min_yield=0.005,  # 0.5% as decimal
            max_payout=80.0,
            min_cagr=0.05,  # 5.0% as decimal
            top_n=10,
        )

        # Verify result
        expected = {
            "min_yield": 0.005,
            "max_payout": 80.0,
            "min_cagr": 0.05,
            "top_n": 10,
        }
        assert result == expected


class TestPerformanceTracker:
    """Test PerformanceTracker functionality."""

    def test_performance_tracker_initialization(self):
        """Test PerformanceTracker initialization."""
        tracker = PerformanceTracker()

        assert tracker.start_time is None

    def test_performance_tracker_start_end(self):
        """Test starting and ending performance tracking."""
        tracker = PerformanceTracker()

        # Start tracking
        tracker.start()
        assert tracker.start_time is not None

        # End tracking
        elapsed = tracker.end()
        assert isinstance(elapsed, float)
        assert elapsed >= 0.0

    def test_performance_tracker_end_without_start(self):
        """Test ending tracking without starting returns 0."""
        tracker = PerformanceTracker()

        elapsed = tracker.end()

        assert elapsed == 0.0

    def test_performance_tracker_multiple_starts(self):
        """Test multiple starts overwrite previous start time."""
        tracker = PerformanceTracker()

        # First start
        tracker.start()
        first_start = tracker.start_time

        # Small delay to ensure different timestamps
        import time

        time.sleep(0.001)  # 1ms delay

        # Second start
        tracker.start()
        second_start = tracker.start_time

        # Should be different (overwritten)
        assert first_start != second_start

        elapsed = tracker.end()
        assert elapsed >= 0.0
