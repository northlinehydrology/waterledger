"""The grid component (design 0008, part 1, step 4) on synthetic hours: the table gives back the fit hours' water, a hot
hour meets the hot-hour mix, and the marginal slope finds the plant that follows load."""
import warnings

import numpy as np
import pytest

from waterledger_models import grid

H0 = int(np.datetime64("2021-01-01T00", "h").astype(int))


def synthetic(years=3, seed=0):
    """A BA with a flat base plant (500 gal/MWh) and a gas plant (200 gal/MWh) that follows load; load rises with
    temperature, so hot hours run more gas and have a lower average intensity."""
    rng = np.random.default_rng(seed)
    hour = np.arange(H0, H0 + years * 8760)
    month, hod, _ = grid.calendar(hour)
    temp = 10 + 12 * np.sin(2 * np.pi * (month - 3) / 12) + 5 * np.sin(2 * np.pi * (hod - 15) / 24) + rng.normal(0, 3, hour.size)
    base = np.full(hour.size, 1000.0)
    gas = 400 + 40 * np.clip(temp - 10, 0, None) + rng.normal(0, 20, hour.size)
    gen = base + gas
    consumed = (base * 500 + gas * 200) / gen
    withdrawn = (base * 800 + gas * 250) / gen
    return hour, consumed, withdrawn, gen, temp


def test_gives_back_the_fit_hours_water():
    hour, c, w, g, t = synthetic()
    tab = grid.fit("TEST", hour, c, w, g, t)
    month, hod, _ = grid.calendar(hour)
    f = grid.lookup(tab, month, hod, t)
    assert np.sum(f["consumed"] * g) == pytest.approx(np.sum(c * g), rel=1e-9)
    assert np.sum(f["withdrawn"] * g) == pytest.approx(np.sum(w * g), rel=1e-9)


def test_hot_hours_meet_the_hot_mix():
    hour, c, w, g, t = synthetic()
    tab = grid.fit("TEST", hour, c, w, g, t)
    july, three_pm = 6, 20                    # 20 UTC
    assert tab.consumed[july, three_pm, -1] < tab.consumed[july, three_pm, 0]     # more gas when hot


def test_marginal_is_the_load_following_plant():
    hour, c, w, g, t = synthetic()
    tab = grid.fit("TEST", hour, c, w, g, t)
    assert np.nanmedian(tab.marginal_consumed) == pytest.approx(200, rel=0.05)
    assert np.nanmedian(tab.marginal_withdrawn) == pytest.approx(250, rel=0.05)


def test_plant_water_scales_with_load():
    hour, c, w, g, t = synthetic()
    tab = grid.fit("TEST", hour, c, w, g, t)
    month, hod, _ = grid.calendar(hour[:48])
    a = grid.plant_water(tab, np.full(48, 100.0), month, hod, t[:48])
    b = grid.plant_water(tab, np.full(48, 200.0), month, hod, t[:48])
    assert np.allclose(b["consumed"], 2 * a["consumed"])


def test_temperatures_outside_the_fit_take_the_end_bins():
    hour, c, w, g, t = synthetic()
    tab = grid.fit("TEST", hour, c, w, g, t)
    f = grid.lookup(tab, np.array([6, 6]), np.array([20, 20]), np.array([-60.0, 60.0]))
    assert f["consumed"][0] == tab.consumed[6, 20, 0] and f["consumed"][1] == tab.consumed[6, 20, -1]


def test_save_and_load(tmp_path):
    hour, c, w, g, t = synthetic(years=1)
    tab = grid.fit("TEST", hour, c, w, g, t)
    p = tmp_path / "t.npz"
    tab.save(p)
    back = grid.GridTable.load(p)
    assert back.ba == "TEST" and back.years == tab.years
    assert np.array_equal(back.consumed, tab.consumed) and np.array_equal(back.marginal_withdrawn, tab.marginal_withdrawn)


def test_bmi_matches_plant_water():
    pytest.importorskip("bmipy")
    from waterledger_models.grid.bmi import GAL_PER_M3, GridWaterBmi
    hour, c, w, g, t = synthetic(years=1)
    tab = grid.fit("TEST", hour, c, w, g, t)
    m = GridWaterBmi()
    m.initialize({"table": tab, "start": "2021-07-01T00", "end_time": 3 * 3600})
    temps, out = [30.0, 18.0, 25.0], []
    for x in temps:
        m.set_value("water_user__electric_power", np.array([250.0]))
        m.set_value("atmosphere_bottom_air__temperature", np.array([x]))
        m.update()
        v = np.zeros(1)
        m.get_value("power_plant_water__consumption_volume_flux", v)
        out.append(v[0] * GAL_PER_M3 * 3600)            # gal in the hour
    month, hod, _ = grid.calendar(np.datetime64("2021-07-01T00", "h").astype(int) + np.arange(3))
    want = grid.plant_water(tab, np.full(3, 250.0), month, hod, np.array(temps))["consumed"]
    assert np.allclose(out, want)
    assert m.get_current_time() == 3 * 3600


def _ols(tab_hours, m, i, tab):
    hour, c, w, g, t = tab_hours
    month, hod, _ = grid.calendar(hour)
    b = grid._bin(tab.edges, month, hod, t)
    nxt = np.flatnonzero(np.diff(hour) == 1) + 1
    s = (month[nxt] == m) & (b[nxt] == i)
    dw, dg = (c * g)[nxt] - (c * g)[nxt - 1], g[nxt] - g[nxt - 1]
    return np.cov(dw[s], dg[s])[0, 1] / np.var(dg[s], ddof=1)


def test_a_spike_leaves_the_slope_unchanged():
    """One hour of a 6 GW spike in a 0-water class (AZPS "other", 2019-05-30T23) moved the old least-squares slope by thousands
    of gal/MWh; Theil-Sen's slope doesn't move, screened or not."""
    hour, c, w, g, t = synthetic()
    clean = grid.fit("TEST", hour, c, w, g, t)
    month, hod, _ = grid.calendar(hour)
    b = grid._bin(clean.edges, month, hod, t)
    k = np.flatnonzero((month == 6) & (b == 4))[40]                 # a hot July hour
    g2, c2, w2 = g.copy(), c.copy(), w.copy()
    g2[k] += 6000
    c2[k], w2[k] = c[k] * g[k] / g2[k], w[k] * g[k] / g2[k]        # the spike carries no water, as in the cache
    spiked = grid.fit("TEST", hour, c2, w2, g2, t)
    assert spiked.marginal_consumed[6, 4] == pytest.approx(clean.marginal_consumed[6, 4], rel=0.01)
    assert abs(_ols((hour, c2, w2, g2, t), 6, 4, clean) - clean.marginal_consumed[6, 4]) > 50     # the old slope moved
    ok = np.ones(len(hour), dtype=bool)
    ok[k:k + 2] = False                                             # screened: neither pair touching the hour
    screened = grid.fit("TEST", hour, c2, w2, g2, t, pair_ok=ok)
    assert screened.marginal_consumed[6, 4] == pytest.approx(clean.marginal_consumed[6, 4], rel=0.01)


def test_factors_outside_the_fuel_range_are_reported_not_changed():
    hour, c, w, g, t = synthetic()
    tight = {"consumed": (np.full(12, 250.0), np.full(12, 500.0)), "withdrawn": (np.full(12, 0.0), np.full(12, 800.0))}
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        tab = grid.fit("TEST", hour, c, w, g, t, bounds=tight)
    plain = grid.fit("TEST", hour, c, w, g, t)
    assert np.array_equal(tab.marginal_consumed, plain.marginal_consumed)            # never clipped
    out = tab.meta["outside"]
    assert out and all(k == "marginal_consumed" for k, *_ in out) and caught       # the gas slope (200) is under 250
    assert grid.fit("TEST", hour, c, w, g, t, bounds={k: (np.zeros(12), np.full(12, 1000.0)) for k in tight}).meta["outside"] == []


def test_theil_sen():
    x = np.arange(100.0)
    y = 3 * x + 1
    y[::10] += 1e6                                                   # a tenth of the points wild
    assert grid.theil_sen(y, x) == pytest.approx(3.0)
    assert np.isnan(grid.theil_sen(y, np.ones(100)))
