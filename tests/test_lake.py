"""Lake-source cooling: the vectorized ensemble reproduces Water Ledger's published lake estimates and its per-run loop."""
import json, os

import numpy as np
import pytest

from waterledger_models.datacenter import lake

REF = json.load(open(os.path.join(os.path.dirname(__file__), "data", "water_ledger_lakes.json")))


@pytest.mark.parametrize("name", sorted(REF))
def test_ensemble_reproduces_published_lakes(name):
    """Same NOAA GLERL temperatures, same seed: Water Ledger's published lake-source estimates (model 1.2)."""
    ds = lake.run_lake_ensemble(REF[name]["temps"], n=200)
    for var in ("withdrawn", "evap_avg", "evap_peak_month", "er_avg"):
        for q, pct in (("p10", 10), ("p50", 50), ("p90", 90)):
            np.testing.assert_allclose(np.percentile(ds[var].values, pct), REF[name]["res"][var][q], rtol=1e-12)


@pytest.mark.parametrize("name", sorted(REF))
def test_per_run_loop_reproduces_published_lakes(name):
    res = lake.run_lake(REF[name]["temps"], n=200)
    for var, qs in REF[name]["res"].items():
        for q, v in qs.items():
            np.testing.assert_allclose(res[var][q], v, rtol=1e-12)


def test_evaporation_share_rises_with_temperature():
    er = lake.evaporation_ratio(np.linspace(0, 25, 26), 10.0)
    assert np.all(np.diff(er) > 0) and er.min() > 0.2 and er.max() < 1
