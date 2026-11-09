"""The grid component in the cell runs (design 0008, part 1, step 5; model 1.11): the campus's water at the power plants closes on its own
electricity, the run's local hours meet the grid table's UTC hours, and the estimate reads what the run wrote."""
import json
import os

import numpy as np
import pytest

from waterledger import scenario as sc
from waterledger.estimate import grid_water
from waterledger.national import era5 as E
from waterledger_models.datacenter import cooling

HERE = os.path.dirname(__file__)
_W = json.load(open(os.path.join(HERE, "data", "west_michigan_2023_2024.json")))
TDB = np.array(_W["temperature_2m"], dtype=float)
RH = np.array(_W["relative_humidity_2m"], dtype=float)
TIMES = [str(t)[:13].replace(" ", "T") + ":00" for t in np.datetime64(_W["start"][:13]) + np.arange(len(TDB)).astype("timedelta64[h]")]
KINDS = ("consumed", "withdrawn", "marginal_consumed", "marginal_withdrawn")


def test_plant_water_closes_on_the_campus_electricity():
    """A constant factor: every draw's plant water is its electricity x the factor, on the average day and on the 1-in-10-year peak day."""
    f = {"consumed": 300.0, "withdrawn": 12000.0, "marginal_consumed": 280.0, "marginal_withdrawn": 11000.0}
    grid = {"MISO": {k: np.full(len(TDB), v) for k, v in f.items()}}
    out = cooling.run_location(TIMES, TDB, RH, n=8, plant="shared", grid=grid)
    for design, r in out.items():
        for k, v in f.items():
            for q in ("p10", "p50", "p90", "central"):
                assert r[f"grid_MISO_{k}_avg"][q] == pytest.approx(r["power_mw_avg"][q] * v * 24 / 1e6, rel=1e-12), (design, k, q)
                assert r[f"grid_MISO_{k}_peak_1in10"][q] == pytest.approx(r["power_mw_peak_day_1in10"][q] * v * 24 / 1e6, rel=1e-12), (design, k, q)


def test_without_a_grid_the_results_are_unchanged():
    a = cooling.run_location(TIMES, TDB, RH, n=6, plant="shared")
    b = cooling.run_location(TIMES, TDB, RH, n=6, plant="shared", grid={"MISO": {"consumed": np.zeros(len(TDB))}})
    for d in a:
        assert {k: v for k, v in b[d].items() if not k.startswith("grid_")} == a[d]


def test_hourly_factors_follow_the_hour():
    """A factor twice as high in summer gives more plant water per MWh over the year than the flat one, and less than the summer one."""
    month = np.array([int(t[5:7]) for t in TIMES])
    flat = {"consumed": np.full(len(TDB), 300.0)}
    summer = {"consumed": np.where((month >= 6) & (month <= 8), 600.0, 300.0)}
    r = cooling.run_location(TIMES, TDB, RH, n=6, plant="shared", grid={"A": flat, "B": summer})["hybrid"]
    assert r["grid_A_consumed_avg"]["p50"] < r["grid_B_consumed_avg"]["p50"] < 2 * r["grid_A_consumed_avg"]["p50"]
    assert r["grid_B_consumed_peak_1in10"]["p50"] / r["grid_A_consumed_peak_1in10"]["p50"] == pytest.approx(2.0, rel=0.02)   # the peak day is in summer


def test_local_hours_meet_the_grid_tables_utc_hours(monkeypatch):
    """A BA whose water per MWh is its UTC hour of day: the cell's local standard hours (round(lon / 15) from UTC) read it back shifted."""
    from waterledger_data import grid930
    hours = np.arange(np.datetime64("2019-01-01T00"), np.datetime64("2025-01-01T00"), np.timedelta64(1, "h"))
    hod = hours.astype(int) % 24
    monkeypatch.setattr(grid930, "intensity", lambda ba: {"hour": hours, "consumed": hod.astype(float), "withdrawn": 10.0 * hod,
                                                          "generation": np.full(len(hours), 1000.0)})
    cid = "42.75_-85.50"                                      # 85.5 W: local standard time is UTC - 6 h
    local = (hours + np.timedelta64(-6, "h"))
    times = [str(x)[:16] for x in local.astype("datetime64[m]")]
    t = np.random.default_rng(1).normal(10, 8, len(hours))
    f = E.grid_factors(cid, times, t, ["MISO"])["MISO"]
    utc_hod = (np.array([int(x[11:13]) for x in times]) + 6) % 24
    assert np.allclose(f["consumed"], utc_hod) and np.allclose(f["withdrawn"], 10 * utc_hod)


def test_a_ba_without_hours_is_left_out(monkeypatch):
    from waterledger_data import grid930

    def missing(ba):
        raise FileNotFoundError(ba)
    monkeypatch.setattr(grid930, "intensity", missing)
    assert E.grid_factors("42.75_-85.50", TIMES, TDB, ["XYZ"]) == {}


def test_michigan_cells_take_miso_and_pjm():
    assert E.cell_bas("MI", {"42.75_-85.50": {"places": []}}) == {"42.75_-85.50": ["MISO", "PJM"]}


def test_the_estimate_reads_the_runs_grid_water():
    stat = lambda v: {"p10": 0.8 * v, "p50": v, "p90": 1.2 * v, "central": v}
    rec = {k: stat(1.0) for k in ("power_mw_avg",)}
    rec |= {f"grid_MISO_{k}_{t}": stat(i + 1.0) for i, k in enumerate(KINDS) for t in ("avg", "peak_1in10")}
    D = {"regions": {"c": {"per_100mw": {"hybrid": rec}}}}
    g = sc.grid_water(D, "c", "hybrid", 300, "MISO")
    assert g["consumed"]["avg"]["mid"] == pytest.approx(3.0) and g["marginal_withdrawn"]["peak_day"]["hi"] == pytest.approx(4 * 1.2 * 3)
    G = grid_water(g, "MISO")
    assert G.balancing_authority == "MISO" and G.withdrawn.p50 == pytest.approx(6.0) and G.marginal_consumed_peak_day.p10 == pytest.approx(0.8 * 3 * 3)
    assert sc.grid_water(D, "c", "hybrid", 300, "PJM") is None and sc.grid_water(D, "c", "lake", 300, "MISO") is None
