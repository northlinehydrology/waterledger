"""docs/methods/sensitivity/sensitivity.py runs on the model as it stands: the location's design dry-bulb reaches hybrid, and its peak day is the package's, at average load over the load factor."""
import importlib.util
from pathlib import Path

import numpy as np

spec = importlib.util.spec_from_file_location("sensitivity", Path(__file__).parents[1] / "docs" / "methods" / "sensitivity" / "sensitivity.py")
sa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sa)


def test_outputs_match_the_package_on_every_design():
    wx, space = sa.load_weather(), sa.cooling_space()
    sa.check_against_package(wx, space, np.random.default_rng(1))


def test_the_peak_is_at_the_peak_load_and_full_capacity_is_the_upper_case():
    wx, space = sa.load_weather(), sa.cooling_space()
    X = sa.scale(np.random.default_rng(2).random((4, len(space))), space)
    out = sa.cooling_outputs(wx, "towers", X, space)
    assert (out["withdrawn_avg"] < out["withdrawn_peak_1in10"]).all() and (out["withdrawn_peak_1in10"] < out["withdrawn_peak_full_capacity"]).all()
    # a tower's water follows its load closely, so the two peaks differ by about their loads
    names = [s[0] for s in space]
    u = X[:, names.index("utilization")] / X[:, names.index("load_factor")]
    np.testing.assert_allclose(out["withdrawn_peak_1in10"] / out["withdrawn_peak_full_capacity"], u, rtol=0.05)


def test_the_parameters_are_read_from_the_package():
    names = [s[0] for s in sa.cooling_space()]
    assert {"load_factor", "switch_margin", "hybrid_full_offset"} <= set(names) and "hybrid_on" not in names
