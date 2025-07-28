"""Tests for the service layer business logic."""

import pandas as pd
import pytest

from dgi.exceptions import DataValidationError, ScreeningError
from dgi.models import CompanyData
from dgi.services.portfolio_service import PortfolioService
from dgi.services.screening_service import ScreeningService
from dgi.services.validation_service import ValidationService


class TestScreeningService:
    """Test cases for ScreeningService business logic."""

    def test_calculate_composite_score_basic(self):
        """Test basic composite score calculation."""
        company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=0.05,
            payout_ratio=30.0,
            dividend_growth_5y=0.10,
            fcf_yield=8.0,
        )

        score = ScreeningService.calculate_composite_score(company)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_validate_screening_parameters_valid(self):
        """Test valid screening parameters."""
        service = ScreeningService()
        service.validate_screening_parameters(
            min_yield=0.02, max_payout=80.0, min_cagr=0.05, top_n=10
        )
        # Should not raise any exception

    def test_validate_screening_parameters_invalid_yield(self):
        """Test invalid minimum yield."""
        with pytest.raises(
            DataValidationError, match="Minimum yield must be non-negative"
        ):
            service = ScreeningService()
            service.validate_screening_parameters(
                min_yield=-0.01, max_payout=80.0, min_cagr=0.05, top_n=10
            )

    def test_validate_screening_parameters_invalid_payout(self):
        """Test invalid maximum payout ratio."""
        with pytest.raises(
            DataValidationError, match="Maximum payout ratio must be between 0 and 200"
        ):
            service = ScreeningService()
            service.validate_screening_parameters(
                min_yield=0.02, max_payout=250.0, min_cagr=0.05, top_n=10
            )

    def test_apply_dgi_criteria_empty_dataframe(self):
        """Test applying criteria to empty DataFrame."""
        df = pd.DataFrame()
        service = ScreeningService()
        result = service.apply_dgi_criteria(df, 0.02, 80.0, 0.05)

        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_apply_dgi_criteria_with_data(self):
        """Test applying criteria to DataFrame with data."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B", "C"],
                "dividend_yield": [0.03, 0.01, 0.05],
                "payout_ratio": [50.0, 90.0, 30.0],
                "dividend_cagr": [0.08, 0.02, 0.12],
            }
        )

        service = ScreeningService()
        result = service.apply_dgi_criteria(df, 0.02, 80.0, 0.05)

        assert len(result) == 2  # Only A and C should pass
        assert "A" in result["symbol"].values
        assert "C" in result["symbol"].values
        assert "B" not in result["symbol"].values

    def test_score_dataframe_empty(self):
        """Test scoring empty DataFrame."""
        df = pd.DataFrame()
        service = ScreeningService()
        result = service.score_dataframe(df)

        assert result.empty
        assert "score" not in result.columns

    def test_score_dataframe_with_data(self):
        """Test scoring DataFrame with data."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B"],
                "dividend_yield": [0.05, 0.03],
                "payout_ratio": [30.0, 50.0],
                "dividend_cagr": [0.10, 0.08],
                "fcf_yield": [8.0, 6.0],
                "sector": ["Technology", "Healthcare"],
                "industry": ["Software", "Pharma"],
            }
        )

        service = ScreeningService()
        result = service.score_dataframe(df)

        assert "score" in result.columns
        assert all(0.0 <= score <= 1.0 for score in result["score"])

    def test_get_top_stocks_empty(self):
        """Test getting top stocks from empty DataFrame."""
        df = pd.DataFrame()
        result = ScreeningService.get_top_stocks(df, 5)

        assert result.empty

    def test_get_top_stocks_with_scores(self):
        """Test getting top stocks with scores."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B", "C"],
                "score": [0.8, 0.6, 0.9],
            }
        )

        result = ScreeningService.get_top_stocks(df, 2)

        assert len(result) == 2
        assert result.iloc[0]["symbol"] == "C"  # Highest score first
        assert result.iloc[1]["symbol"] == "A"

    def test_validate_screening_results_valid(self):
        """Test validating valid screening results."""
        df = pd.DataFrame(
            {
                "symbol": ["A"],
                "dividend_yield": [0.05],
                "payout": [30.0],
                "dividend_cagr": [0.10],
            }
        )

        ScreeningService.validate_screening_results(df)
        # Should not raise any exception

    def test_validate_screening_results_missing_columns(self):
        """Test validating screening results with missing columns."""
        df = pd.DataFrame(
            {
                "symbol": ["A"],
                "dividend_yield": [0.05],
                # Missing payout and dividend_cagr
            }
        )

        with pytest.raises(ScreeningError, match="Missing required columns"):
            ScreeningService.validate_screening_results(df)

    def test_rows_to_dataframe_empty(self):
        """Test converting empty rows to DataFrame."""
        rows = []
        result = ScreeningService.rows_to_dataframe(rows)

        assert result.empty
        assert isinstance(result, pd.DataFrame)

    def test_rows_to_dataframe_with_data(self):
        """Test converting rows to DataFrame."""
        rows = [
            {"symbol": "A", "yield": 0.05},
            {"symbol": "B", "yield": 0.03},
        ]

        result = ScreeningService.rows_to_dataframe(rows)

        assert len(result) == 2
        assert list(result["symbol"]) == ["A", "B"]

    def test_apply_screening_criteria_empty(self):
        """Test applying screening criteria to empty DataFrame."""
        df = pd.DataFrame()
        result = ScreeningService.apply_screening_criteria(df, 0.02, 80.0, 0.05)

        assert result.empty

    def test_apply_screening_criteria_with_data(self):
        """Test applying screening criteria to DataFrame with data."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B", "C"],
                "dividend_yield": [0.03, 0.01, 0.05],
                "payout": [50.0, 90.0, 30.0],
                "dividend_cagr": [0.08, 0.02, 0.12],
            }
        )

        result = ScreeningService.apply_screening_criteria(df, 0.02, 80.0, 0.05)

        assert len(result) == 2  # Only A and C should pass
        assert "A" in result["symbol"].values
        assert "C" in result["symbol"].values

    def test_convert_to_response_format_empty(self):
        """Test converting empty DataFrame to response format."""
        df = pd.DataFrame()
        result = ScreeningService.convert_to_response_format(df)

        assert result == []

    def test_convert_to_response_format_with_data(self):
        """Test converting DataFrame to response format."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B"],
                "dividend_yield": [0.05, 0.03],
                "score": [0.8, 0.6],
            }
        )

        result = ScreeningService.convert_to_response_format(df)

        assert len(result) == 2
        assert result[0]["symbol"] == "A"
        assert result[0]["dividend_yield"] == 0.05
        assert result[0]["score"] == 0.8


class TestPortfolioService:
    """Test cases for PortfolioService business logic."""

    def test_calculate_equal_weights_empty(self):
        """Test calculating equal weights for empty DataFrame."""
        df = pd.DataFrame()
        result = PortfolioService.calculate_equal_weights(df)

        assert result.empty
        assert "weight" not in result.columns

    def test_calculate_equal_weights_with_data(self):
        """Test calculating equal weights for DataFrame with data."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B", "C"],
                "score": [0.8, 0.6, 0.9],
            }
        )

        result = PortfolioService.calculate_equal_weights(df)

        assert "weight" in result.columns
        assert all(weight == 1.0 / 3 for weight in result["weight"])

    def test_calculate_score_weights_empty(self):
        """Test calculating score weights for empty DataFrame."""
        df = pd.DataFrame()
        result = PortfolioService.calculate_score_weights(df)

        assert result.empty
        assert "weight" not in result.columns

    def test_calculate_score_weights_with_data(self):
        """Test calculating score weights for DataFrame with data."""
        df = pd.DataFrame(
            {
                "symbol": ["A", "B", "C"],
                "score": [0.8, 0.6, 0.9],
            }
        )

        result = PortfolioService.calculate_score_weights(df)

        assert "weight" in result.columns
        total_score = 0.8 + 0.6 + 0.9
        assert result.loc[result["symbol"] == "A", "weight"].iloc[0] == pytest.approx(
            0.8 / total_score
        )
        assert result.loc[result["symbol"] == "B", "weight"].iloc[0] == pytest.approx(
            0.6 / total_score
        )
        assert result.loc[result["symbol"] == "C", "weight"].iloc[0] == pytest.approx(
            0.9 / total_score
        )


class TestValidationService:
    """Test cases for ValidationService business logic."""

    def test_validate_company_data_valid(self):
        """Test validating valid company data."""
        company = CompanyData(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            industry="Software",
            dividend_yield=0.05,
            payout_ratio=30.0,
            dividend_growth_5y=0.10,
            fcf_yield=8.0,
        )

        ValidationService.validate_company_data(company)
        # Should not raise any exception

    def test_sanitize_company_name(self):
        """Test sanitizing company name."""
        name = "  Test Company & Co.  "
        result = ValidationService.sanitize_company_name(name)

        assert result == "Test Company & Co."
        assert isinstance(result, str)

    def test_validate_symbol_valid(self):
        """Test validating valid symbol."""
        assert ValidationService.validate_symbol("AAPL") is True
        assert ValidationService.validate_symbol("MSFT") is True

    def test_validate_symbol_invalid(self):
        """Test validating invalid symbol."""
        assert ValidationService.validate_symbol("") is False
        assert ValidationService.validate_symbol("A" * 10) is False  # Too long
