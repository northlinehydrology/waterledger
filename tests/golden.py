"""Write tests/data/golden_cooling.json: the cooling model's results on the stored weather. Rerun only on a deliberate model change
(a new MODEL_VERSION), and say so in the changelog; test_golden.py fails on any other change to the numbers.

    uv run python tests/golden.py
"""
import json, os

from waterledger_models import MODEL_VERSION
from waterledger_models.datacenter import cooling as cw

HERE = os.path.dirname(__file__)


def weather():
    import datetime as dt
    w = json.load(open(os.path.join(HERE, "data", "west_michigan_2023_2024.json")))
    t0 = dt.datetime.fromisoformat(w["start"])
    times = [(t0 + dt.timedelta(hours=k)).strftime("%Y-%m-%dT%H:%M") for k in range(len(w["temperature_2m"]))]
    return times, w["temperature_2m"], w["relative_humidity_2m"]


def results():
    return {"model_version": MODEL_VERSION, "per_100mw": cw.run_location(*weather(), n=40, mw=100.0), "staff": cw.staff_q(cw.staff_runs(40), 300)}


if __name__ == "__main__":
    json.dump(results(), open(os.path.join(HERE, "data", "golden_cooling.json"), "w"), indent=0)
    print("wrote tests/data/golden_cooling.json")
