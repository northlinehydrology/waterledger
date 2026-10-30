"""State totals from EIA-861 (waterledger_data.power): retail sales and residential use for any state. Runs where an
EIA-861 year is on disk (the cache a state build fills); skipped otherwise."""
import pytest

from waterledger_data import power

YEAR = power.latest_eia861(download=False)
pytestmark = pytest.mark.skipif(YEAR is None, reason="no EIA-861 year on disk")


def test_michigan_total_is_bundled_plus_energy_only():
    import pandas as pd
    s = power._sales(YEAR)
    mi = s[(s.state == "MI") & s.part.isin(["A", "B"])].mwh.sum()          # Michigan's figure as it was first computed
    assert power.michigan_retail_mwh(YEAR) == power.state_retail_mwh("MI", YEAR) == pytest.approx(float(mi))
    assert pd.notna(mi) and 8e7 < mi < 1.2e8                                 # about 100 TWh a year


@pytest.mark.parametrize("state, lo, hi", [("MI", 550, 750), ("OH", 750, 1000), ("VA", 950, 1200), ("TX", 1000, 1300)])
def test_residential_use_is_plausible(state, lo, hi):
    r = power.residential(state, YEAR)
    assert r["customers"] > 1_000_000 and lo < r["kwh_month"] < hi
    assert r["kwh_month"] == pytest.approx(r["mwh"] * 1000 / r["customers"] / 12, abs=0.1)


def test_texas_counts_its_retail_providers():
    s = power._sales(YEAR)
    assert (s[s.state == "TX"].part == "D").any()                            # ERCOT's retail electric providers file as Part D
    assert power.state_retail_mwh("TX", YEAR) > 4e8
