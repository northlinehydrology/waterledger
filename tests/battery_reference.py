"""Write tests/data/battery_before_runner.json: the battery cell plant Monte Carlo's results as they were before it moved onto the shared runner
(waterledger_models.runs, design 0010, step 2a): every design, the lake on Lake Michigan's GLERL temperatures, NMC and LFP, full and sampled
utilization, with two balancing authorities whose water per MWh changes hour by hour, on the stored two years of West Michigan weather, 10 draws.
test_runs.py holds the runner to it. Written once, before the move (Nov 10, 2026, waterledger 3.16.0); not rerun.

    uv run python tests/battery_reference.py
"""
import json
import os

from golden import weather
from runner_reference import grid
from waterledger_models.battery import plant

HERE = os.path.dirname(__file__)
N = 10
LAKE = json.load(open(os.path.join(HERE, "data", "water_ledger_lakes.json")))["Lake Michigan"]["temps"]


def results():
    times, t, rh = weather()
    g = grid(len(times))
    return {f"{chem}_{util}": plant.run_location(times, t, rh, n=N, gwh=10.0, utilization=util, water_temps=LAKE, chemistry=chem, grid=g)
            for chem in ("nmc", "lfp") for util in ("full", "sampled")}


if __name__ == "__main__":
    json.dump(results(), open(os.path.join(HERE, "data", "battery_before_runner.json"), "w"), indent=0)
    print("wrote tests/data/battery_before_runner.json")
