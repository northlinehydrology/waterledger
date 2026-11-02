"""Write tests/data/water_ledger_west_michigan.json: West Michigan's estimates from the per-run loop (cooling.run_location), as the Michigan build writes them, rounded to 5 decimal places as
published. test_reproduction.py checks the ensembles against them. Rerun only on a deliberate model change (a new MODEL_VERSION or draw count). It takes several minutes and one Open-Meteo request.

    uv run python tests/reproduction_reference.py
"""
import datetime, json, os

from waterledger_models import MODEL_VERSION
from waterledger_models.datacenter import cooling as cw
from waterledger_models.datacenter.ensemble import STATS
from waterledger_models.datacenter.physics import DRAWS
from waterledger_models.weather import fetch_open_meteo

HERE = os.path.dirname(__file__)
LAT, LON = 42.88, -85.52
OTHERS = ("wue_l_per_kwh", "wue_makeup_l_per_kwh", "utilization")


def kept(key):
    """The flows the ensembles report by stat, and water use effectiveness and utilization."""
    flow, _, stat = key.partition("_")
    return key in OTHERS or (flow in ("withdrawn", "consumed", "returned") and stat in STATS)


if __name__ == "__main__":
    w = fetch_open_meteo(LAT, LON, cache=os.path.join(HERE, ".cache", "west_michigan.json"))
    times = [str(t)[:16] for t in w.time.values]
    runs = cw.run_location(times, w.air_temperature.values.tolist(), w.relative_humidity.values.tolist(), n=DRAWS, mw=100.0)
    per_100mw = {d: {k: {q: round(v, 5) for q, v in r.items()} for k, r in stats.items() if kept(k)} for d, stats in runs.items()}
    out = {"source": "waterledger_models.datacenter.cooling.run_location, the loop behind Michigan's estimates.json", "model_version": MODEL_VERSION, "generated": datetime.date.today().isoformat(),
           "region": {"name": "West Michigan", "station": "Grand Rapids area", "lat": LAT, "lon": LON},
           "note": f"West Michigan's estimates per 100 MW of IT capacity (cooling water with loop top-ups; p10/p50/p90 over {DRAWS} runs, seed 7, and the central run), rounded to 5 decimal places as published, "
                   f"and the {DRAWS} staff water draws [core people, people per MW, gallons per person a day, share used up, maintenance base, maintenance per MW, maintenance share used up], seed 13, which Water Ledger adds at the campus's size.",
           "per_100mw": per_100mw, "staff_runs": cw.staff_runs(DRAWS)}
    json.dump(out, open(os.path.join(HERE, "data", "water_ledger_west_michigan.json"), "w"), indent=0)
    print("wrote tests/data/water_ledger_west_michigan.json")
