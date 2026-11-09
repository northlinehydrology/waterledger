"""The grid component (design 0008, part 1, step 4) on synthetic hours: the table gives back the fit hours' water, a hot
hour meets the hot-hour mix, and the marginal slope finds the plant that follows load."""
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
