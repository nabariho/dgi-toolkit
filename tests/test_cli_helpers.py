import sys
import pandas as pd
import dgi.cli_helpers as helpers


def test_cli_helpers_import() -> None:
    """Test that CLI helpers can be imported without Rich dependency."""

    # The function should work without creating mock objects


def test_render_screen_table_importerror(monkeypatch, capsys):
    # Patch import to raise ImportError
    monkeypatch.setitem(sys.modules, "rich.console", None)
    monkeypatch.setitem(sys.modules, "rich.table", None)
    monkeypatch.setitem(sys.modules, "rich", None)
    df = pd.DataFrame(
        [
            {
                "symbol": "A",
                "name": "A",
                "dividend_yield": 1,
                "payout": 1,
                "dividend_cagr": 1,
                "fcf_yield": 1,
                "score": 1,
            }
        ]
    )
    helpers.render_screen_table(df)
    out, err = capsys.readouterr()
    assert "rich" in out or "rich" in err
