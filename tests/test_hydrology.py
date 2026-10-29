"""Screening hydrology against textbook values."""
import math

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
