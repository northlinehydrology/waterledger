"""The shared runner (waterledger_models.runs, design 0010, step 2a): every water user type's Monte Carlo through one loop.

- Battery cell plants match their record from before the move (tests/data/battery_before_runner.json; data centers' is test_datacenter_record.py).
  The runner works every power figure from the hourly MW, one formula for every type, so power_mw_avg, power_mw_peak_1in10 and
  power_mw_peak_day_1in10 differ from the types' own loops in the last bit (at most 5e-16 relative on macOS); held to 1e-12.
- Conformance, for every type: the standard names, mass closure in every statistic that sums, grid water closing on the electricity.
- The extra hook hands a caller each draw's hourly electricity.
"""
import json
import os

import numpy as np
import pytest

import battery_reference
from golden import weather
from waterledger_models import runs
from waterledger_models.battery import plant
from waterledger_models.datacenter import cooling

HERE = os.path.dirname(__file__)
TIMES, T, RH = weather()
STANDARD = {f"{role}_{stat}" for role in ("withdrawn", "consumed", "returned") for stat in ("avg", "peak_1in10", "record", "annual_mg")} | {
    f"{role}_{stat}" for role in ("withdrawn", "consumed") for stat in ("max_month", "max_90day", "worst_year_mg")} | {
    "withdrawn_peak_full_capacity", "utilization", "power_mw_avg", "power_mw_peak_1in10", "power_mw_peak_day_1in10"}


def _close(got, want, path=""):
    if isinstance(want, dict):
        assert got.keys() == want.keys(), path
        for k in want:
            _close(got[k], want[k], f"{path}/{k}")
    else:
        np.testing.assert_allclose(got, want, rtol=1e-12, atol=0, err_msg=path)


def test_battery_plants_match_their_record():
    want = json.load(open(os.path.join(HERE, "data", "battery_before_runner.json")))
    _close(json.loads(json.dumps(battery_reference.results())), want)


def _types(grid=None):
    """Every registered type's Monte Carlo on the same weather (data centers per 100 MW, cell plants per 10 GWh/yr)."""
    return {"datacenter": cooling.run_location(TIMES, T, RH, n=6, mw=100.0, grid=grid),
            "battery": plant.run_location(TIMES, T, RH, n=6, gwh=10.0, grid=grid)}


@pytest.fixture(scope="module")
def flat_grid():
    return {"MISO": {"consumed": np.full(len(TIMES), 300.0), "withdrawn": np.full(len(TIMES), 12000.0)}}


def test_every_type_reports_the_standard_results(flat_grid):
    for kind, out in _types(flat_grid).items():
        for design, r in out.items():
            missing = STANDARD - set(r)
            assert not missing, (kind, design, sorted(missing))
            assert {"grid_MISO_consumed_avg", "grid_MISO_withdrawn_peak_1in10"} <= set(r), (kind, design)
            for k, v in r.items():
                assert set(v) == {"p10", "p50", "p90", "central"} and v["p10"] <= v["p50"] <= v["p90"], (kind, design, k)


def test_every_type_closes(flat_grid):
    """Withdrawn (+ condensate) = consumed + returned in each draw's average day and year, and returned = to the sewer + to the source where a type
    splits it; grid water is the electricity times the factor. Checked on the central run, which is one draw end to end."""
    for kind, out in _types(flat_grid).items():
        for design, r in out.items():
            c = {k: v["central"] for k, v in r.items()}
            for stat in ("avg", "annual_mg"):
                gain = c.get(f"condensate_{stat}", 0.0)
                assert c[f"withdrawn_{stat}"] + gain == pytest.approx(c[f"consumed_{stat}"] + c[f"returned_{stat}"], rel=1e-9), (kind, design, stat)
                if f"to_sewer_{stat}" in c:
                    assert c[f"returned_{stat}"] == pytest.approx(c[f"to_sewer_{stat}"] + c[f"to_source_{stat}"], rel=1e-9), (kind, design, stat)
            assert c["grid_MISO_consumed_avg"] == pytest.approx(c["power_mw_avg"] * 300.0 * 24 / 1e6, rel=1e-12), (kind, design)
            assert c["withdrawn_peak_full_capacity"] >= c["withdrawn_avg"] and c["power_mw_peak_1in10"] >= c["power_mw_avg"], (kind, design)


def test_extra_sees_every_draws_hourly_electricity():
    """The hook the power supply scenarios use: called once per draw with that draw's Hours; what it returns is summarized with the rest."""
    seen = []

    def extra(design, p, hours):
        seen.append((design, hours.mw.shape))
        return {"mwh_per_year": float(hours.mw.sum()) / (len(hours.mw) / 8766.0)}

    model = plant._CellPlantRuns(4, 7, 10.0, "full", None, "nmc", None)
    out = runs.run_location(model, TIMES, T, RH, designs=("towers",), extra=extra)["towers"]
    assert len(seen) == 5 and all(s == (len(TIMES),) for _, s in seen)          # four draws and the central run
    assert out["mwh_per_year"]["central"] == pytest.approx(out["power_mw_avg"]["central"] * 8766.0, rel=1e-9)
