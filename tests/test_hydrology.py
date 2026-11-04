"""Screening hydrology against textbook values."""
import math

import numpy as np
import pytest

from waterledger_models import hydrology as h


def test_curve_number_runoff():
    assert h.scs_runoff_in(0.7, 72) == 0.0                     # below the initial abstraction (0.78 in)
    assert h.scs_runoff_in(5.0, 98) == pytest.approx(4.76, abs=0.01)        # TR-55: 5 in on pavement
    assert h.scs_runoff_in(5.0, 72) == pytest.approx(2.20, abs=0.01)        # S = 3.89 in, Ia = 0.78 in
    assert h.composite_runoff_in(5.0, 0.5, h.CN_POST_PERV) > h.composite_runoff_in(5.0, 0.0, h.CN_PRE_PERV)


def test_well_function_table():
    # the exponential integral E1 (Abramowitz and Stegun Table 5.1)
    for u, w in ((1e-4, 8.63322470), (1e-2, 4.03792957), (0.1, 1.82292395), (1.0, 0.21938393), (5.0, 0.00114829559)):
        assert h.well_function(u) == pytest.approx(w, rel=1e-7)


def test_theis_and_glover():
    s = h.theis_drawdown(q=1e5, transmissivity=5000, storativity=1e-3, r=500, t=30)
    assert s == pytest.approx(1e5 / (4 * math.pi * 5000) * h.well_function(500 ** 2 * 1e-3 / (4 * 5000 * 30)))
    assert 0 < h.stream_depletion(3000, 5000, 0.15, 90) < h.stream_depletion(3000, 5000, 0.15, 365) < 1


def test_erfc_matches_the_standard_library():
    x = np.concatenate([np.linspace(-6, 26, 64001), [0.0, 1.4999999, 1.5, 1.5000001, np.inf]])
    ref = np.array([math.erfc(v) for v in x])
    got = h.erfc(x)
    normal = ref > 1e-300
    np.testing.assert_allclose(got[normal], ref[normal], rtol=1e-13, atol=0)
    assert np.all(got[~normal] < 1e-299) and np.all((got >= 0) & (got <= 2))


def test_stream_depletion_on_arrays_matches_the_scalar_form():
    """Ten years of hourly responses in one call, the same values as one call per hour (Glover and Balmer with math.erfc)."""
    t = np.arange(1, 10 * 8760 + 1) / 24.0                     # days
    for d, tr, s in ((300.0, 500.0, 0.1), (3000.0, 5000.0, 0.15), (50.0, 20.0, 0.2)):
        share = h.stream_depletion(d, tr, s, t)
        assert share.shape == t.shape and np.all(np.diff(share) >= 0) and np.all((share >= 0) & (share < 1))
        idx = np.r_[0:200, 200:t.size:97]
        scalar = np.array([math.erfc(math.sqrt(d * d * s / (4 * tr * x))) for x in t[idx]])
        np.testing.assert_allclose(share[idx], scalar, rtol=1e-12, atol=1e-300)
        assert h.stream_depletion(d, tr, s, float(t[idx[250]])) == pytest.approx(scalar[250], rel=1e-12)
    assert isinstance(h.stream_depletion(300.0, 500.0, 0.1, 60.0), float)
    assert h.stream_depletion(300.0, 500.0, 0.1, np.array([0.0, 1.0]))[0] == 0.0          # nothing from the stream at the start
    grid = h.stream_depletion(np.array([[100.0], [1000.0]]), 500.0, 0.1, np.array([10.0, 100.0, 1000.0]))
    assert grid.shape == (2, 3) and np.all(grid[0] > grid[1])  # nearer streams give more, distances by times
