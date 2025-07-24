import pytest
import pandas as pd
from typing import Any, List
from dgi.models import CompanyData
from dgi.validation import DgiRowValidator, PydanticRowValidation
from dgi.repositories.csv import CsvCompanyDataRepository
from dgi.screener import Screener
from dgi.scoring import DefaultScoring


def make_screener(csv_path: str) -> Screener:
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    repo = CsvCompanyDataRepository(csv_path, validator)
    return Screener(repo)


def test_load_universe_valid(tmp_path: Any) -> None:
    csv = tmp_path / "fundamentals.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,0.6,20,8,5\n"
        "MSFT,Microsoft,Tech,Software,0.8,35,10,7\n"
    )
    screener = make_screener(str(csv))
    df = screener.load_universe()
    expected_columns = [
        "symbol",
        "name",
        "sector",
        "industry",
        "dividend_yield",
        "payout",
        "dividend_cagr",
        "fcf_yield",
    ]
    assert list(df.columns) == expected_columns
    assert df.shape[0] == 2
    for col in ["dividend_yield", "payout", "dividend_cagr", "fcf_yield"]:
        assert df[col].dtype == float


def test_load_universe_invalid_all_rows(tmp_path: Any) -> None:
    csv = tmp_path / "invalid.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,not_a_number,20,8,5\n"
        "MSFT,Microsoft,Tech,Software,not_a_number,35,10,7\n"
    )
    screener = make_screener(str(csv))
    with pytest.raises(
        ValueError,
        match="(Validation errors:|Missing expected columns|No valid rows found)",
    ):
        screener.load_universe()


def test_load_universe_mixed_valid_invalid(tmp_path: Any) -> None:
    csv = tmp_path / "mixed.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,not_a_number,20,8,5\n"  # invalid
        "GOOG,Google,Tech,Software,1.2,30,12,8\n"  # valid
    )
    screener = make_screener(str(csv))
    df = screener.load_universe()
    assert df.shape[0] == 1
    assert df.iloc[0]["symbol"] == "GOOG"


def test_apply_filters() -> None:
    df = pd.DataFrame(
        {
            "symbol": ["A", "B"],
            "dividend_yield": [2.0, 1.0],
            "payout": [40.0, 60.0],
            "dividend_cagr": [7.0, 3.0],
            "name": ["n1", "n2"],
            "sector": ["s1", "s2"],
            "industry": ["i1", "i2"],
            "fcf_yield": [4.0, 2.0],
        }
    )
    # Create a mock repository for the test
    from unittest.mock import Mock

    mock_repo = Mock()
    screener = Screener(mock_repo)  # Mock repo for filtering
    filtered = screener.apply_filters(df, min_yield=1.5, max_payout=50.0, min_cagr=5.0)
    assert filtered.shape[0] == 1
    assert filtered.iloc[0]["symbol"] == "A"


def test_score() -> None:
    row = pd.Series(
        {
            "dividend_cagr": 10.0,  # 0.5 normalized
            "fcf_yield": 10.0,  # 0.5 normalized
            "payout": 50.0,  # 0.5 normalized
        }
    )
    scoring = DefaultScoring()
    company = CompanyData(
        symbol="A",
        name="A",
        sector="A",
        industry="A",
        dividend_yield=2.0,
        payout_ratio=row["payout"],
        dividend_growth_5y=row["dividend_cagr"],
        fcf_yield=row["fcf_yield"],
    )
    s = scoring.score(company)
    assert abs(s - 0.16666666666666666) < 1e-6  # (0.5 + 0.5 - 0.5) / 3


def test_load_universe_invalid_types(tmp_path: Any) -> None:
    csv = tmp_path / "bad_types.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,not_a_number,20,8,5\n"  # invalid dividend_yield
        "MSFT,Microsoft,Tech,Software,0.8,thirtyfive,10,7\n"  # invalid payout
        "GOOG,Google,Tech,Software,1.2,30,12,8\n"  # valid row
    )
    screener = make_screener(str(csv))
    df = screener.load_universe()
    assert df.shape[0] == 1
    assert df.iloc[0]["symbol"] == "GOOG"


def test_csv_repository_and_screener(tmp_path: Any) -> None:
    csv = tmp_path / "repo_test.csv"
    csv.write_text(
        "symbol,name,sector,industry,dividend_yield,payout,dividend_cagr,fcf_yield\n"
        "AAPL,Apple,Tech,Hardware,0.6,20,8,5\n"
        "MSFT,Microsoft,Tech,Software,0.8,35,10,7\n"
    )
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    repo = CsvCompanyDataRepository(str(csv), validator)
    screener = Screener(repo)
    df = screener.load_universe()
    assert df.shape[0] == 2
    assert set(df["symbol"]) == {"AAPL", "MSFT"}


def test_companydata_valid() -> None:
    row = CompanyData(
        symbol="AAPL",
        name="Apple",
        sector="Tech",
        industry="Hardware",
        dividend_yield=0.6,
        payout_ratio=20.0,
        dividend_growth_5y=8.0,
        fcf_yield=5.0,
    )
    assert row.symbol == "AAPL"
    assert row.dividend_yield == 0.6


def test_companydata_invalid() -> None:
    # This test intentionally passes the wrong type to check runtime validation.
    with pytest.raises(Exception):
        CompanyData(
            symbol="AAPL",
            name="Apple",
            sector="Tech",
            industry="Hardware",
            dividend_yield="not_a_number",  # type: ignore  # Testing validation
            payout_ratio=20.0,
            dividend_growth_5y=8.0,
            fcf_yield=5.0,
        )


def test_dgirowvalidator_valid() -> None:
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    rows = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "sector": "Tech",
            "industry": "Hardware",
            "dividend_yield": 0.6,
            "payout": 20.0,
            "dividend_cagr": 8.0,
            "fcf_yield": 5.0,
        }
    ]
    valid = validator.validate_rows(rows)
    assert valid[0].symbol == "AAPL"


def test_dgirowvalidator_invalid() -> None:
    validator = DgiRowValidator(CompanyData)
    rows = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "sector": "Tech",
            "industry": "Hardware",
            "dividend_yield": "not_a_number",
            "payout": 20.0,
            "dividend_cagr": 8.0,
            "fcf_yield": 5.0,
        }
    ]
    with pytest.raises(ValueError):
        validator.validate_rows(rows)


def test_screener_empty_repository() -> None:
    from dgi.repositories.base import CompanyDataRepository

    class EmptyRepo(CompanyDataRepository):
        def get_rows(self) -> List[CompanyData]:
            return []

    screener = Screener(EmptyRepo())
    with pytest.raises(ValueError):
        screener.load_universe()


def test_screener_missing_columns(tmp_path: Any) -> None:
    csv = tmp_path / "missing_cols.csv"
    csv.write_text("symbol,name,sector\nAAPL,Apple,Tech\n")
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    repo = CsvCompanyDataRepository(str(csv), validator)
    screener = Screener(repo)
    with pytest.raises(ValueError):
        screener.load_universe()


def test_screener_score_edge_cases() -> None:
    scoring = DefaultScoring()

    # Test case 1: Basic scoring with DefaultScoring (normalized)
    company = CompanyData(
        symbol="A",
        name="A",
        sector="A",
        industry="A",
        dividend_yield=2.0,
        payout_ratio=50.0,
        dividend_growth_5y=10.0,
        fcf_yield=10.0,
    )
    # DefaultScoring: cagr_norm(10/20=0.5) + fcf_norm(10/20=0.5) - payout_norm(50/100=0.5) = 0.5
    # Then divided by 3 = 0.5/3 = 0.1667
    cagr_norm = min(max(10.0 / 20.0, 0.0), 1.0)
    fcf_norm = min(max(10.0 / 20.0, 0.0), 1.0)
    payout_norm = min(max(50.0 / 100.0, 0.0), 1.0)
    expected = max(0.0, min((cagr_norm + fcf_norm - payout_norm) / 3.0, 1.0))
    assert scoring.score(company) == expected

    # Test case 2: High values
    company_high = CompanyData(
        symbol="B",
        name="B",
        sector="B",
        industry="B",
        dividend_yield=12.0,
        payout_ratio=20.0,  # Low payout for better score
        dividend_growth_5y=15.0,
        fcf_yield=15.0,
    )
    # DefaultScoring: cagr_norm(15/20=0.75) + fcf_norm(15/20=0.75) - payout_norm(20/100=0.2) = 1.3
    # Then divided by 3 = 1.3/3 = 0.433, clamped to max 1.0
    cagr_norm_high = min(max(15.0 / 20.0, 0.0), 1.0)
    fcf_norm_high = min(max(15.0 / 20.0, 0.0), 1.0)
    payout_norm_high = min(max(20.0 / 100.0, 0.0), 1.0)
    expected_high = max(
        0.0, min((cagr_norm_high + fcf_norm_high - payout_norm_high) / 3.0, 1.0)
    )
    assert scoring.score(company_high) == expected_high

    # Test case 3: String input conversion
    company_str = CompanyData(
        symbol="C",
        name="C",
        sector="C",
        industry="C",
        dividend_yield="3.5",  # type: ignore  # Testing validation
        payout_ratio=45.0,
        dividend_growth_5y=8.0,
        fcf_yield=6.0,
    )
    assert company_str.dividend_yield == 3.5  # Should be converted to float
    # Test the scoring works with converted values
    cagr_norm_str = min(max(8.0 / 20.0, 0.0), 1.0)
    fcf_norm_str = min(max(6.0 / 20.0, 0.0), 1.0)
    payout_norm_str = min(max(45.0 / 100.0, 0.0), 1.0)
    expected_str = max(
        0.0, min((cagr_norm_str + fcf_norm_str - payout_norm_str) / 3.0, 1.0)
    )
    assert scoring.score(company_str) == expected_str


def test_dgirowvalidator_all_invalid() -> None:
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    rows = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "sector": "Tech",
            "industry": "Hardware",
            "dividend_yield": "not_a_number",
            "payout": 20.0,
            "dividend_cagr": 8.0,
            "fcf_yield": 5.0,
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft",
            "sector": "Tech",
            "industry": "Software",
            "dividend_yield": "not_a_number",
            "payout": 30.0,
            "dividend_cagr": 10.0,
            "fcf_yield": 7.0,
        },
    ]
    with pytest.raises(Exception):
        validator.validate_rows(rows)


def test_dgirowvalidator_some_invalid(caplog: Any) -> None:
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    rows = [
        {
            "symbol": "AAPL",
            "name": "Apple",
            "sector": "Tech",
            "industry": "Hardware",
            "dividend_yield": "not_a_number",
            "payout": 20.0,
            "dividend_cagr": 8.0,
            "fcf_yield": 5.0,
        },
        {
            "symbol": "MSFT",
            "name": "Microsoft",
            "sector": "Tech",
            "industry": "Software",
            "dividend_yield": 1.2,
            "payout": 30.0,
            "dividend_cagr": 10.0,
            "fcf_yield": 7.0,
        },
    ]
    valid = validator.validate_rows(rows)
    assert len(valid) == 1
    assert valid[0].symbol == "MSFT"
    assert any(
        "Some rows were invalid and skipped" in r.message for r in caplog.records
    )


def test_companydata_must_be_number_exception() -> None:
    """Test CompanyData must_be_number validator for exception case."""
    with pytest.raises(Exception):
        CompanyData(
            symbol="TEST",
            name="Test",
            sector="Test",
            industry="Test",
            dividend_yield="not_a_number",  # type: ignore  # Testing validation
            payout_ratio=50.0,
            dividend_growth_5y=5.0,
            fcf_yield=3.0,
        )


def test_notebook_pipeline_matches_csv(tmp_path: Any) -> None:
    from dgi.validation import DgiRowValidator
    from dgi.repositories.csv import CsvCompanyDataRepository
    from dgi.screener import Screener
    from dgi.scoring import DefaultScoring

    # Use the real CSV file
    csv_path = "data/fundamentals_small.csv"
    validator = DgiRowValidator(PydanticRowValidation(CompanyData))
    repo = CsvCompanyDataRepository(csv_path, validator)
    screener = Screener(repo, scoring_strategy=DefaultScoring())
    df = screener.load_universe()
    # Print for debug
    print("Loaded DataFrame:")
    print(df)
    print("Dtypes:")
    print(df.dtypes)
    filtered = screener.apply_filters(df, min_yield=0.5, max_payout=60, min_cagr=5.0)
    print("Filtered DataFrame:")
    print(filtered)
    print("Filtered dtypes:")
    print(filtered.dtypes)
    assert (
        filtered.shape[0] == 5
    ), f"Expected 5 rows after filtering, got {filtered.shape[0]}\n{filtered}"


def test_screener_with_default_filter():
    """Test screener uses DefaultFilter by default."""
    from unittest.mock import Mock
    from dgi.repositories.base import CompanyDataRepository
    from dgi.screener import Screener
    from dgi.filtering import DefaultFilter

    repo = Mock(spec=CompanyDataRepository)
    screener = Screener(repo)

    # Check that default filter was set
    assert screener._filter_strategy is not None
    assert isinstance(screener._filter_strategy, DefaultFilter)


def test_screener_with_custom_filter():
    """Test screener accepts custom filter strategy."""
    from unittest.mock import Mock
    from dgi.repositories.base import CompanyDataRepository
    from dgi.screener import Screener
    from dgi.filtering import FilterStrategy

    class TestFilter(FilterStrategy):
        def filter(self, df, min_yield, max_payout, min_cagr):
            # Test filter that returns only first row
            return df.head(1)

    repo = Mock(spec=CompanyDataRepository)
    custom_filter = TestFilter()
    screener = Screener(repo, filter_strategy=custom_filter)

    assert screener._filter_strategy is custom_filter


def test_apply_filters_uses_strategy():
    """Test that apply_filters delegates to the filter strategy."""
    from unittest.mock import Mock
    from dgi.repositories.base import CompanyDataRepository
    from dgi.screener import Screener
    from dgi.filtering import FilterStrategy

    # Mock filter strategy
    mock_filter = Mock(spec=FilterStrategy)
    expected_result = pd.DataFrame({"test": [1, 2, 3]})
    mock_filter.filter.return_value = expected_result

    repo = Mock(spec=CompanyDataRepository)
    screener = Screener(repo, filter_strategy=mock_filter)

    # Test data
    test_df = pd.DataFrame(
        {
            "dividend_yield": [1.0, 2.0, 3.0],
            "payout": [30.0, 40.0, 50.0],
            "dividend_cagr": [5.0, 6.0, 7.0],
        }
    )

    # Call apply_filters
    result = screener.apply_filters(
        test_df, min_yield=2.0, max_payout=60.0, min_cagr=4.0
    )

    # Verify strategy was called with correct parameters
    mock_filter.filter.assert_called_once_with(test_df, 2.0, 60.0, 4.0)

    # Verify result is what strategy returned
    pd.testing.assert_frame_equal(result, expected_result)


def test_default_filter_behavior():
    """Test that DefaultFilter works correctly."""
    from dgi.filtering import DefaultFilter

    filter_strategy = DefaultFilter()

    # Test data with mixed values
    test_df = pd.DataFrame(
        {
            "dividend_yield": [1.0, 2.5, 3.0, 0.5],
            "payout": [30.0, 70.0, 40.0, 90.0],
            "dividend_cagr": [8.0, 3.0, 6.0, 2.0],
        }
    )

    # Apply filters: min_yield=2.0, max_payout=60.0, min_cagr=5.0
    result = filter_strategy.filter(
        test_df, min_yield=2.0, max_payout=60.0, min_cagr=5.0
    )

    # Should only return row with yield>=2.0, payout<=60.0, cagr>=5.0
    # Row 0: yield=1.0 (fail), payout=30.0 (pass), cagr=8.0 (pass) -> FAIL
    # Row 1: yield=2.5 (pass), payout=70.0 (fail), cagr=3.0 (fail) -> FAIL
    # Row 2: yield=3.0 (pass), payout=40.0 (pass), cagr=6.0 (pass) -> PASS
    # Row 3: yield=0.5 (fail), payout=90.0 (fail), cagr=2.0 (fail) -> FAIL

    assert len(result) == 1
    assert result.iloc[0]["dividend_yield"] == 3.0
    assert result.iloc[0]["payout"] == 40.0
    assert result.iloc[0]["dividend_cagr"] == 6.0
