"""Physical sanity of the cooling equations (ported from dc-cooling-water): bounds, trends and the water balance."""
import numpy as np
import pytest

from waterledger_models.datacenter import physics as model


def synthetic_weather(days=730, seed=0):
    """Two years of hourly weather with a seasonal and daily cycle, Michigan-like."""
    rng = np.random.default_rng(seed)
    h = np.arange(days * 24)
    t = 9 + 14 * np.sin(2 * np.pi * (h / 24 - 110) / 365.25) + 5 * np.sin(2 * np.pi * (h % 24 - 9) / 24) + rng.normal(0, 2, h.size)
    rh = np.clip(70 - 15 * np.sin(2 * np.pi * (h % 24 - 9) / 24) + rng.normal(0, 8, h.size), 15, 100)
    time = np.datetime64("2001-01-01T00:00") + h.astype("timedelta64[h]")
    return time, t, rh


def test_wet_bulb_not_above_dry_bulb():
    # Stull (2011) is least accurate for cold, very dry air (about +0.9 C at -20 C and 10% RH); test its good range
    t = np.linspace(-10, 38, 49)
    for rh in (20, 50, 90):
        assert np.all(model.wet_bulb(t, rh) <= t + 0.3)


def test_evaporative_ratio_bounds_and_trend():
    t = np.linspace(-20, 40, 61)
    er = model.evaporative_ratio(t)
    assert er.min() >= 0.55 and er.max() <= 1.0
    assert er[-1] > er[0]          # warmer air: more of the heat leaves as evaporation


@pytest.mark.parametrize("design", model.DESIGNS)
def test_water_balance(design):
    t, rh = np.array([-20.0, 0.0, 15.0, 28.0, 33.0]), np.array([50.0, 70.0, 80.0, 85.0, 70.0])     # a bitter hour and humid ones, so humidifiers and condensate both run
    p = model.central_parameters()
    p = model.for_location(p, t)
    w, c, r = model.hourly_rates(t, model.wet_bulb(t, rh), design, p, rh)
    humidify, condensate = model.hourly_water_with_air(t, model.wet_bulb(t, rh), p, rh)
    assert humidify.max() > 0 and condensate.max() > 0
    np.testing.assert_allclose(w + condensate, c + r, rtol=1e-12)
    assert np.all(w > 0) and np.all(c >= 0) and np.all(r >= 0)


def test_dry_design_uses_loop_topups_only():
    _, t, rh = synthetic_weather(30)
    p = {**model.central_parameters(), "oa_cfm_per_mw": 0.0}
    w, c, r = model.hourly_rates(t, model.wet_bulb(t, rh), "dry", p)
    # 7,000 gal per MW, 3% a year, spread over the IT energy at 65% utilization
    topup = 7000 * 0.03 / 365 / (24 * 1000 * 0.65)
    np.testing.assert_allclose(w, topup)
    np.testing.assert_allclose(c, topup)        # leaks are all lost
    np.testing.assert_array_equal(r, 0.0)


def test_staff_water():
    s = model.central_staff()
    w, c, r = model.staff_water(s, 300)
    people, maint = (40 + 0.3 * 300) * 20 / 1e6, (1000 + 11 * 300) / 1e6      # staff plus maintenance (model 1.3)
    assert w == pytest.approx(people + maint)
    assert c == pytest.approx(0.1 * people + 0.09 * maint) and w == pytest.approx(c + r)
    # it grows with the people on site, more slowly than the computers
    assert model.staff_water(s, 1000)[0] < 1000 / 300 * w
    runs = model.sample_staff(50, seed=13)
    for k, (lo, hi) in model.STAFF.items():
        v = runs[f"staff_{k}"]
        assert v.shape == (50,) and v.min() >= lo and v.max() <= hi
    np.testing.assert_array_equal(model.sample_staff(50)["staff_gpcd"], model.sample_staff(200)["staff_gpcd"][:50])


def test_designs_order_by_water_use():
    _, t, rh = synthetic_weather(365)
    p = model.for_location(model.central_parameters(), t)
    tw = model.wet_bulb(t, rh)
    use = {d: model.hourly_rates(t, tw, d, p)[0].mean() for d in model.DESIGNS}
    assert use["dry"] < min(use["assist"], use["hybrid"]) and max(use["assist"], use["hybrid"]) < use["towers"]    # assist and hybrid overlap


def test_each_parameter_has_one_draw_in_each_stratum():
    """Latin hypercube, by hand: with n = 50, each parameter's draws fall one each in 50 equal slices of its range, groups or not."""
    n = 50
    v = model.sample_parameters(n, 7)
    for k, (lo, hi) in [*model.RANGES.items(), ("topup", model.TOPUP), *model.ADIABATIC.items(), *model.POWER.items(), *model.OUTSIDE.items()]:
        assert sorted(np.floor((v[k] - lo) / (hi - lo) * n).astype(int)) == list(range(n)), k


def test_draws_are_reproducible_and_stable():
    a, b = model.sample_parameters(30, 7), model.sample_parameters(30, 7)
    for k in a:
        np.testing.assert_array_equal(a[k], b[k])
    assert not np.array_equal(a["coc"], model.sample_parameters(30, 8)["coc"])
    # one parameter's draws do not depend on what else is sampled
    one = model.latin_hypercube({"coc": model.RANGES["coc"]}, 30, 7)
    two = model.latin_hypercube({"coc": model.RANGES["coc"], "other": (0.0, 1.0)}, 30, 7)
    np.testing.assert_array_equal(one["coc"], two["coc"])


def _rank_corr(x, y):
    rank = lambda a: np.argsort(np.argsort(a))
    return np.corrcoef(rank(x), rank(y))[0, 1]


def test_linked_parameters_move_together():
    """Two members of a group: score = shared + own, equal weights, so covariance 1/12 over variance 2/12, correlation 0.5. Rank correlation is close to it."""
    v = model.sample_parameters(2000, 7)
    assert _rank_corr(v["supply_air"], v["water_rise"]) == pytest.approx(0.5, abs=0.06)
    assert _rank_corr(v["ups"], v["fan_eff"]) == pytest.approx(0.5, abs=0.06)
    assert _rank_corr(v["ups"], v["crah_pa"]) == pytest.approx(-0.5, abs=0.06)       # a good UPS goes with low pressure drops
    assert _rank_corr(v["ups"], v["supply_air"]) == pytest.approx(0.0, abs=0.06)     # different groups
    assert _rank_corr(v["coc"], v["ups"]) == pytest.approx(0.0, abs=0.06)            # not linked


def test_unknown_design():
    with pytest.raises(ValueError):
        model.hourly_rates(np.zeros(3), np.zeros(3), "spray-pond", model.central_parameters())
