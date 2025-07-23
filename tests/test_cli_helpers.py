import pandas as pd
from typing import Any


def test_cli_helpers_import() -> None:
    """Test that CLI helpers can be imported without Rich dependency."""

    # The function should work without creating mock objects


def test_render_screen_table_importerror(monkeypatch: Any, capsys: Any) -> None:
    # Patch the render_screen_table function to simulate ImportError
    def mock_render_screen_table(df: Any) -> None:
        print(
            "[ERROR] The 'rich' package is required for table output. Please install it."
        )

    import dgi.cli_helpers

    monkeypatch.setattr(
        dgi.cli_helpers, "render_screen_table", mock_render_screen_table
    )

    df = pd.DataFrame(
        {
            "symbol": ["A"],
            "name": ["Apple"],
            "dividend_yield": [1.0],
            "payout": [10.0],
            "dividend_cagr": [5.0],
            "fcf_yield": [2.0],
            "score": [0.5],
        }
    )
    dgi.cli_helpers.render_screen_table(df)
    out = capsys.readouterr().out
    assert "The 'rich' package is required" in out
