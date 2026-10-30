"""Hourly electricity from the heat balance (model 1.4): physical behavior, not values; values are in the golden test."""
import numpy as np
import pytest

from waterledger_models.datacenter import cooling as cw
from waterledger_models.datacenter import physics as ph

C = ph.central_parameters()
TDB = np.array([-10.0, 5.0, 15.0, 25.0, 35.0])
TWB = np.array([-11.0, 3.0, 11.0, 19.0, 24.0])


def pue(design, t=TDB, w=TWB, **over):
    return ph.hourly_heat_power(t, w, design, {**C, **over})[0]


@pytest.mark.parametrize("design", ["dry", "assist", "towers"])
def test_never_falls_as_it_warms(design):
    assert np.all(np.diff(pue(design, liquid_share=0.0)) >= -1e-3)


def test_hybrid_turning_wet_helps_in_the_heat():
    assert pue("hybrid", liquid_share=0.0)[-1] < pue("dry", liquid_share=0.0)[-1]     # it can fall as it warms, once evaporation takes over


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_plausible_range_at_the_ends_of_every_parameter(design):
    for k, (lo, hi) in {**ph.RANGES, **ph.POWER, **ph.ADIABATIC}.items():
        for v in (lo, hi):
            assert np.all((pue(design, **{k: v}) > 1.0) & (pue(design, **{k: v}) < 2.0)), (k, v)


def test_closed_loop_costs_more_in_the_heat_with_air_cooled_computers():
    hot = pue("dry", liquid_share=0.0)[-1] - pue("towers", liquid_share=0.0)[-1]
    cold = pue("dry", liquid_share=0.0)[0] - pue("towers", liquid_share=0.0)[0]
    assert hot > cold and hot > 0


def test_liquid_cooling_lowers_power():
    for d in ph.DESIGNS:
        assert np.all(pue(d, liquid_share=1.0) <= pue(d, liquid_share=0.0) + 1e-9)


def test_chillers_add_heat_only_when_they_run():
    p = {**C, "liquid_share": 0.0}
    power, heat = ph.hourly_heat_power(TDB, TWB, "towers", p)
    q = 1.0 + (1.0 / p["ups"] - 1.0) + (1.0 / (1.0 - p["dist_loss"]) - 1.0) + p["light"]
    assert heat[0] > q and heat[0] == pytest.approx(heat[1])     # free cooling: the load alone
    assert heat[-1] > heat[0]                                    # chiller power joins the load in the heat


def test_every_output_comes_from_the_same_heat():
    w_cold = ph.hourly_rates(TDB, TWB, "towers", C)[1]
    assert np.all(w_cold > 0)
    a = ph.hourly_rates(TDB, TWB, "towers", C)[1]
    b = ph.hourly_rates(TDB, TWB, "towers", {**C, "ups": 0.90})[1]
    assert np.all(b > a)                                         # more losses, more heat, more evaporation


def test_run_location_reports_electricity():
    times = [f"20{y:02d}-07-01T{h:02d}:00" for y in (21, 22) for h in range(24)]
    r = cw.run_location(times, [30.0] * 48, [50.0] * 48, n=8, mw=100.0)
    for d in cw.DESIGNS:
        v = r[d]
        assert 1.0 < v["pue_avg"]["p50"] < 2.0
        assert v["power_mw_avg"]["p50"] < v["power_mw_peak_1in10"]["p50"]        # utilization below 1
        assert v["pue_peak_1in10"]["p50"] >= v["pue_avg"]["p50"] - 1e-9
