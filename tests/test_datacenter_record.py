"""The data center Monte Carlo against its record from before the shared pieces moved (design 0010's standard treatment: assist's pads to
heat_rejection, grid water to grid.RunWater, then the shared runner). Every cooling plant and design, compiled and NumPy, with two balancing
authorities whose water per MWh changes hour by hour. The record was written on macOS, where the first two moves matched it to the bit; the runner
works power from the hourly MW, so power_mw_avg and power_mw_peak_1in10 differ in the last bit (at most 4.1e-16 relative), and CI's Linux NumPy
differs in the last bit of some values, so it is held to 1e-12 of each."""
import json
import os

import numpy as np

import runner_reference

HERE = os.path.dirname(__file__)


def test_the_data_center_monte_carlo_matches_its_record():
    want = json.load(open(os.path.join(HERE, "data", "datacenter_before_runner.json")))
    got = json.loads(json.dumps(runner_reference.results()))

    def walk(a, b, path):
        if isinstance(b, dict):
            assert b.keys() <= a.keys(), path          # names may be added (3.x: additions only); every recorded one keeps its value
            for k in b:
                walk(a[k], b[k], f"{path}/{k}")
        else:
            np.testing.assert_allclose(a, b, rtol=1e-12, atol=0, err_msg=path)

    walk(got, want, "")
