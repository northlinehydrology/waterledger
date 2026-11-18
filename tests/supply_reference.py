"""Write tests/data/supply_before_aorc.json: the ERA5 supply path's results as they were before the path for a study's own forcing was added
(design 0018): PV (tracking and fixed, central parameters and three draws at once), wind, and supply scenarios with PV, wind and gas on the
shared runner, on the stored two years of West Michigan weather with test_scenarios.py's synthetic radiation and 100 m wind.
test_supply_identity.py holds the ERA5 path to it (to the bit on macOS arm64, within 1e-12 elsewhere). Written from main on macOS arm64: at f370fcc
(Nov 16, 2026), and again at 561740f (Nov 18) when main's own cooling and supply changes came in; never from this branch.

    uv run python tests/supply_reference.py
"""
import json
import os

import numpy as np

from golden import weather

HERE = os.path.dirname(__file__)
LAT, LON = 42.9, -85.5


def inputs():
    times, t, rh = weather()
    t, rh = np.asarray(t, float), np.asarray(rh, float)
    utc = np.array(times, dtype="datetime64[h]") + np.timedelta64(5, "h")
    h = np.arange(len(times))
    sun = np.clip(np.sin(2 * np.pi * (h % 24 - 6) / 24), 0, None) * (0.75 + 0.25 * np.sin(2 * np.pi * (h / 8766 - 0.25)))
    cloud = 0.35 + 0.65 * np.random.default_rng(5).random(len(h))
    ghi, beam = 900 * sun * cloud, 700 * sun * cloud ** 2
    u, v = 4 + 3 * np.sin(2 * np.pi * h / 97), 2 + 2 * np.cos(2 * np.pi * h / 61)
    return times, t, rh, utc, ghi, beam, u, v


def stats(x):
    """Enough of an hourly series to see any change: its sum, a position-weighted sum, its extremes and two stretches of hours, as exact floats."""
    x = np.asarray(x, float)
    flat = x.reshape(-1, x.shape[-1])
    return {"shape": list(x.shape), "sum": [float(r.sum()) for r in flat], "weighted": [float((r * np.arange(r.size)).sum()) for r in flat],
            "max": [float(r.max()) for r in flat], "min": [float(r.min()) for r in flat],
            "jan": [r[0:72].tolist() for r in flat], "jul": [r[4400:4472].tolist() for r in flat]}


def results():
    from waterledger_models import runs
    from waterledger_models.datacenter import cooling
    from waterledger_models.supply import pv, scenario as S, wind
    times, t, rh, utc, ghi, beam, u, v = inputs()
    w100 = np.hypot(u, v)
    central = {k: (a + b) / 2 for k, (a, b) in pv.RANGES.items()}
    draws = {k: np.array([[a], [(a + b) / 2], [b]]) for k, (a, b) in pv.RANGES.items()}
    wdraws = {k: np.array([[a], [(a + b) / 2], [b]]) for k, (a, b) in wind.RANGES.items()}
    out = {"pv_tracking": stats(pv.hourly(utc, LAT, LON, ghi, beam, t, w100, central)),
           "pv_fixed": stats(pv.hourly(utc, LAT, LON, ghi, beam, t, w100, central, mount="fixed")),
           "pv_fixed_tilt_30": stats(pv.hourly(utc, LAT, LON, ghi, beam, t, w100, central, mount="fixed", tilt=30.0)),
           "pv_draws": stats(pv.output(pv.geometry(utc, LAT, LON), ghi, beam, t, w100, draws)),
           "wind_central": stats(wind.hourly(u, v, {k: (a + b) / 2 for k, (a, b) in wind.RANGES.items()})),
           "wind_draws": stats(wind.hourly(u, v, wdraws))}
    scenarios = {"c1": S.Scenario(pv_share=0.6, wind_share=0.4),
                 "d2": S.Scenario(pv_share=0.3, wind_share=0.3, gas=S.Gas(technology="cc", design="towers", unit_mw=60.0, firm_mw=40.0)),
                 "b1": S.Scenario(residual="none", gas=S.Gas(technology="engine", design="dry", unit_mw=18.0))}
    model = lambda: cooling._CoolingRuns(6, 7, 100.0, cooling.HOUR_BLOCK, cooling.DEFAULT_PLANT, True)
    wx = (utc, ghi, beam, u, v)
    sized = S.size(model(), times, t, rh, scenarios, "hybrid", wx, LAT, LON)
    grid = {"MISO": {"consumed": np.full(len(times), 300.0), "withdrawn": np.full(len(times), 12000.0)}}
    r = runs.run_location(model(), times, t, rh, designs=("hybrid",), grid=grid, extra=S.Supply(sized, wx, LAT, LON, 6))["hybrid"]
    out["sizes"] = {k: {"pv_mw": sc.pv_mw, "wind_mw": sc.wind_mw, "units": sc.gas.units if sc.gas else None} for k, sc in sized.items()}
    out["scenarios"] = {k: v for k, v in r.items() if k.startswith("supply_")}
    return out


if __name__ == "__main__":
    json.dump(results(), open(os.path.join(HERE, "data", "supply_before_aorc.json"), "w", encoding="utf-8"), indent=0)
    print("wrote tests/data/supply_before_aorc.json")
