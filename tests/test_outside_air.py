"""The outside air design (model 1.17, design 0022): its halls' air, pads and trim chillers close, hour by hour, across the draws and all weather."""
import numpy as np
import pytest

from waterledger_models.datacenter import physics as ph

T = np.arange(-30.0, 48.0, 0.5)
DESIGN_DB = 33.0
PLANT_DRAWS = {k: {**{n: v[:, None] for n, v in ph.sample_parameters(100, plant=k).items()}, "design_db": DESIGN_DB} for k in ph.PLANTS}


def _weather(rh):
    r = np.full_like(T, rh)
    return ph.wet_bulb(T, r), r


@pytest.mark.parametrize("plant", ph.PLANTS)
@pytest.mark.parametrize("rh", [5.0, 40.0, 90.0])
def test_the_halls_air_closes(plant, rh):
    """Mixing reaches the supply air floor; the supply never goes above the operator's setting; the pads' cooling is what the water's latent heat takes;
    the pads never cool below the wet-bulb; no cooling water at or below the setting; the trim chillers carry only what the pads can't."""
    p = PLANT_DRAWS[plant]
    W, R = _weather(rh)
    h = ph.outside_air_hall(T, W, p, R)
    floor, switch, ret = p["supply_air"], ph.outside_air_switch(p), p["supply_air"] + p["air_rise"]
    mixing = T < floor
    np.testing.assert_allclose(np.where(mixing, h["share"] * T + (1 - h["share"]) * ret, floor) * np.ones_like(h["share"]), floor * np.ones_like(h["share"]), rtol=1e-12)
    assert ((h["share"] > 0) & (h["share"] <= 1)).all()
    assert (h["supply"] <= switch + 1e-12).all() and (h["supply"] >= floor - 1e-12).all()
    np.testing.assert_allclose(h["m"] * ph.CP_AIR * h["pads"], h["evap"] / 3600.0 * ph.KG_GAL * ph.LATENT_KJ, rtol=1e-12, atol=1e-15)
    assert (h["pads"] <= np.maximum(T - W, 0.0) + 1e-12).all()
    assert (np.where(T <= switch, h["evap"], 0.0) == 0).all()
    # the air leaves the pads and trim at the setting in every hot hour: outside - pads - trim = setting
    hot = T > switch
    trim_k = h["trim"] / (h["m"] * ph.CP_AIR)
    np.testing.assert_allclose(np.where(hot, T - h["pads"] - trim_k, switch) * np.ones_like(trim_k), switch * np.ones_like(trim_k), rtol=1e-12)
    assert (np.where(h["trim"] > 0, h["pads"] >= p["assist_eff"] * np.maximum(T - W, 0.0) - 1e-12, True)).all()


@pytest.mark.parametrize("plant", ph.PLANTS)
def test_every_kw_is_accounted_for(plant):
    """Facility power = IT and its losses + the halls' fans + trim chillers and their pump + the liquid racks' dry loop; what isn't heat rejection fans is heat."""
    p = PLANT_DRAWS[plant]
    W, R = _weather(40.0)
    power, heat = ph.hourly_heat_power(T, W, "outside_air", p, R)
    h = ph.outside_air_hall(T, W, p, R)
    q = 1 / p["ups"] + 1 / (1 - p["dist_loss"]) - 1 + p["light"]
    air = (1 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    chiller, pumps, fans = ph._loop(1 - air + 0.0 * T, p["liquid_water"], T, W, T, 0.0, "dry", p)
    np.testing.assert_allclose(power, q + h["fan"] + h["chiller"] + chiller + pumps + fans, rtol=1e-12)
    np.testing.assert_allclose(power - heat, fans * np.ones_like(power), rtol=1e-12, atol=1e-15)
    assert (power >= 1.0).all()


@pytest.mark.parametrize("plant", ph.PLANTS)
def test_no_more_water_than_towers_unless_hotter_than_the_return_air(plant):
    """The pads cool all the halls' air, towers only the heat. In an hour hotter than the halls' return air (the setting + the air rise) cooling the
    outside air to the setting takes more than the heat itself, so there, in very dry air, the design can evaporate more than towers would: physics, kept
    (design 0022). In every other hour it takes less."""
    p = PLANT_DRAWS[plant]
    hotter = T > ph.outside_air_switch(p) + p["air_rise"]
    for rh in (5.0, 40.0, 90.0):
        W, R = _weather(rh)
        oa = ph.hourly_rates(T, W, "outside_air", p, R)[1]
        towers = ph.hourly_rates(T, W, "towers", p, R)[1]
        assert (np.where(hotter, True, oa <= towers + 1e-12)).all()


def test_a_hot_hour_by_hand():
    """35 C at 20% relative humidity, central parameters, shared plant: the hall air's flow, the pads' cooling and their water, by hand."""
    p = ph.central_parameters()
    t, rh = np.array([35.0]), np.array([20.0])
    wb = ph.wet_bulb(t, rh)
    h = ph.outside_air_hall(t, wb, p, rh)
    q = 1 / p["ups"] + 1 / (1 - p["dist_loss"]) - 1 + p["light"]
    air = (1 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    m = (q - (1 - air)) / (1.01 * p["air_rise"])                           # kg/s per IT kW
    switch = max(p["switch_setting"], p["supply_air"] + p["switch_margin"], p["supply_air"])
    pads = min(35.0 - switch, p["assist_eff"] * (35.0 - wb[0]))             # the pads reach the setting: 35 C on a wet-bulb near 19 C
    assert pads == pytest.approx(35.0 - switch) and h["trim"][0] == 0.0
    gal = m * 1.01 * pads / 2450.0 * 3600.0 / 3.78541
    assert h["evap"][0] == pytest.approx(gal, rel=1e-12)
    assert gal == pytest.approx(0.090, abs=0.005)                          # about 0.34 L per IT kWh in that hour


def test_a_water_limit_moves_the_pads_duty_to_the_trim_chillers():
    p = {**ph.central_parameters(), **ph.central_limits(), "design_db": DESIGN_DB}
    t, rh = np.array([38.0, 42.0]), np.array([30.0, 30.0])
    wb = ph.wet_bulb(t, rh)
    full = ph.outside_air_hall(t, wb, p, rh)
    half = ph.outside_air_hall(t, wb, {**p, "wet_frac": 0.5}, rh)
    assert (half["evap"] < full["evap"]).all() and (half["trim"] > full["trim"]).all()
    free = ph.hourly_limited(t, wb, "outside_air", p, np.inf, rh)
    limited = ph.hourly_limited(t, wb, "outside_air", p, 0.5 * free["withdrawn"], rh)
    assert (limited["withdrawn"] <= 0.5 * free["withdrawn"] * (1 + 1e-6)).all() and (limited["power"] > free["power"]).all()
