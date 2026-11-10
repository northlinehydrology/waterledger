"""Write tests/data/datacenter_before_runner.json: the data center Monte Carlo's results, as they were before it moved onto the shared runner
(waterledger_models.runs, design 0010's standard treatment): every cooling plant and design on the stored two years of West Michigan weather,
12 draws, with two balancing authorities whose water per MWh changes hour by hour, through the compiled kernel and through physics.py.
test_runs.py holds the runner to it. Written once, before the move (Nov 10, 2026); not rerun.

    uv run python tests/runner_reference.py
"""
import json
import os

import numpy as np

from golden import weather
from waterledger_models.datacenter import cooling as cw

HERE = os.path.dirname(__file__)
N = 12


def grid(n_hours):
    h = np.arange(n_hours)
    day, year = np.sin(2 * np.pi * h / 24), np.sin(2 * np.pi * h / 8766)
    return {"MISO": {"consumed": 300 + 40 * day + 25 * year, "withdrawn": 12000 + 900 * day},
            "PJM": {"consumed": 280 + 30 * year, "marginal_consumed": 180 + 20 * day}}


def results():
    times, t, rh = weather()
    g = grid(len(times))
    return {"compiled": cw.run_plants(times, t, rh, n=N, mw=100.0, grid=g),
            "numpy": {"shared": cw.run_location(times, t, rh, n=N, mw=100.0, plant="shared", compiled=False, grid=g)}}


if __name__ == "__main__":
    json.dump(results(), open(os.path.join(HERE, "data", "datacenter_before_runner.json"), "w"), indent=0)
    print("wrote tests/data/datacenter_before_runner.json")
