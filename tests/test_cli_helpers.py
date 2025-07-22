import pandas as pd
import sys
from dgi.cli_helpers import render_screen_table


def test_render_screen_table_importerror(monkeypatch, capsys):
    # Simulate ImportError for rich
    sys_modules_backup = sys.modules.copy()
    sys.modules["rich"] = None
    sys.modules["rich.console"] = None
    sys.modules["rich.table"] = None
    try:
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
        render_screen_table(df)
        out = capsys.readouterr().out
        assert "The 'rich' package is required" in out
    finally:
        sys.modules.clear()
        sys.modules.update(sys_modules_backup)
