"""Chiller COP (designs 0015 and 0021): the model's form against ASHRAE 90.1's reference curves, the rating bands it was set to, and the second law.
The curves and the fit are in docs/methods/chillers/fit_chillers.py, which this test reads, so the record of the fit and the check are one."""
import importlib.util
import os

import numpy as np
import pytest

from waterledger_models import heat_rejection as hr

_SPEC = importlib.util.spec_from_file_location("fit_chillers", os.path.join(os.path.dirname(__file__), "..", "docs", "methods", "chillers", "fit_chillers.py"))
fit = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(fit)

C = fit.C
RATING_WATER = (C(44.0) - 2.0, C(85.0) + fit.AHRI_RANGE + 2.0)     # evaporating and condensing, C
RATING_AIR = (C(44.0) - 2.0, C(95.0) + 12.0)


def water(eta, evap, cond):
    return hr.chiller_cop(cond, evap, eta, hr.WATER_CHILLER_LOSS, min_lift=hr.WATER_MIN_LIFT)


def air(eta, evap, cond, cap=np.inf):
    return hr.chiller_cop(cond, evap, eta, hr.AIR_CHILLER_LOSS, cap)


def test_the_fitted_losses_are_the_fit_scripts():
    t, x = np.meshgrid(np.linspace(40, 54, 15), np.linspace(60, 85, 26))
    (loss, _), rms, top = fit.fit(fit.WATER["centrifugal"], fit.RATED_WATER, (44.0, 85.0), (t.ravel(), x.ravel()), lambda cw: cw + fit.AHRI_RANGE + 2.0)
    assert loss == pytest.approx(hr.WATER_CHILLER_LOSS, abs=5e-5) and rms < 0.01 and top < 0.03


def test_water_cooled_follows_90_1_over_its_range():
    """Code-minimum centrifugal (COP 6.28 at AHRI's rating point): within 3% of 90.1's curve everywhere on it (the fit's largest error is 2.6%)."""
    eta = fit.eta_for(fit.RATED_WATER, hr.WATER_CHILLER_LOSS, *RATING_WATER)
    coef = fit.WATER["centrifugal"]
    for tw in np.linspace(40, 54, 8):
        for cw in np.linspace(60, 85, 11):
            ref = fit.RATED_WATER * fit.eir(coef, 44, 85) / fit.eir(coef, tw, cw)
            assert water(eta, C(tw) - 2.0, C(cw) + fit.AHRI_RANGE + 2.0) == pytest.approx(ref, rel=0.03)


def test_air_cooled_follows_90_1_over_its_range():
    """Code-minimum screw (COP 2.96): RMS within 5%, largest within 18%, over 90.1's water and the hours chillers run (air 15-46 C). The largest
    (17.9%, the model above the curve) is at the coolest corner, 15 C air on 12.2 C water, where the sampled cap (5-7.6) often holds the COP; above
    25 C air it is 11%. Design 0015 gave 14% on its own grid."""
    eta = fit.eta_for(2.96, hr.AIR_CHILLER_LOSS, *RATING_AIR)
    coef = fit.AIR["screw"]
    t, x = np.meshgrid(np.linspace(40, 54, 15), np.linspace(fit.F(15.0), 115, 57))
    ref = 2.96 * fit.eir(coef, 44, 95) / fit.eir(coef, t, x)
    r = air(eta, C(t) - 2.0, C(x) + 12.0) / ref - 1
    assert np.sqrt(np.mean(r ** 2)) < 0.05 and np.max(np.abs(r)) < 0.18


def test_the_ranges_keep_their_rating_bands():
    """Water-cooled 5.33-6.70 at AHRI's rating point, the band through model 1.16 (code minimum +/-11%); air-cooled 2.96-3.61 (EER 10.1 up)."""
    lo, hi = hr.EQUIPMENT["carnot_water"]
    assert water(lo, *RATING_WATER) == pytest.approx(5.33, abs=0.01) and water(hi, *RATING_WATER) == pytest.approx(6.70, abs=0.01)
    lo, hi = hr.EQUIPMENT["carnot_air"]
    assert air(lo, *RATING_AIR) == pytest.approx(2.96, abs=0.01) and air(hi, *RATING_AIR) == pytest.approx(3.61, abs=0.01)


@pytest.mark.parametrize("kind", ["water", "air"])
def test_never_above_carnot(kind):
    """With the loss, the lift term's coefficient may pass 1 (water-cooled) and the COP still stays below Carnot's, at every lift and evaporator
    temperature a loop has, at both ends of the range."""
    lift = np.linspace(0.5, 60.0, 400)
    for eta in hr.EQUIPMENT[f"carnot_{kind}"]:
        for evap in (0.0, 5.0, 15.0, 25.0, 30.0):
            cop = water(eta, evap, evap + lift) if kind == "water" else air(eta, evap, evap + lift, 7.6)
            assert np.all(cop < (evap + 273.15) / lift)


@pytest.mark.parametrize("kind", ["water", "air"])
def test_falls_as_the_lift_rises(kind):
    lift = np.linspace(0.5, 60.0, 400)
    eta = np.mean(hr.EQUIPMENT[f"carnot_{kind}"])
    cop = water(eta, 18.0, 18.0 + lift) if kind == "water" else air(eta, 18.0, 18.0 + lift, 7.6)
    assert np.all(np.diff(cop) <= 0) and np.all(np.diff(cop)[lift[1:] > hr.WATER_MIN_LIFT + 0.2] < 0)


def test_water_cooled_gains_nothing_below_90_1s_smallest_lift():
    """Below 12.89 K the COP holds at its value there (design 0021): about 90.1's code-minimum 10.8 at that corner."""
    eta = fit.eta_for(fit.RATED_WATER, hr.WATER_CHILLER_LOSS, *RATING_WATER)
    at_floor = water(eta, C(54.0) - 2.0, C(54.0) - 2.0 + hr.WATER_MIN_LIFT)
    assert water(eta, C(54.0) - 2.0, C(54.0) - 2.0 + 3.0) == at_floor
    assert at_floor == pytest.approx(fit.RATED_WATER * fit.eir(fit.WATER["centrifugal"], 44, 85) / fit.eir(fit.WATER["centrifugal"], 54, 60), rel=0.03)
