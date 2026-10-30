"""A state build on a machine with no cached EIA-861 downloads it instead of failing (build-state, Oct 30, 2026)."""
import os

import pandas as pd

from waterledger_data import power


def test_utility_rtos_downloads_when_nothing_is_cached(tmp_path, monkeypatch):
    monkeypatch.setattr(power, "RAW", str(tmp_path))

    def fetch(year):
        os.makedirs(tmp_path / f"eia861_{year}")
        pd.DataFrame([["title", "", ""], ["Utility Number", "ERCOT", "PJM"], [1, "Y", "N"], [2, "N", "Y"], [3, "Y", "Y"]]).to_excel(
            tmp_path / f"eia861_{year}" / f"Utility_Data_{year}.xlsx", header=False, index=False)

    monkeypatch.setattr(power, "fetch_eia861", fetch)
    assert power.utility_rtos() == {1: "ERCO", 2: "PJM"}
