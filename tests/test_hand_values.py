"""Values worked by hand from the equations, with the numbers written out here, not read from the code's constants, so a wrong constant in the code fails."""
import numpy as np
import pytest

from waterledger_models.datacenter import lake, physics as ph

C = ph.central_parameters()
# one kW of heat, with no losses, fans, pumps or outside air, in free cooling at 10 C
SIMPLE = {**C, "ups": 1.0, "dist_loss": 0.0, "light": 0.0, "liquid_share": 0.0, "crah_pa": 0.0, "oa_cfm_per_mw": 0.0, "pump_econ_kpa": 0.0,
          "pump_chw_kpa": 0.0, "pump_tower_kpa": 0.0, "tower_fan_pa": 0.0, "er_adj": 0.0, "coc": 5.0, "range_f": 10.0, "drift": 0.0001, "fill_gal_per_mw": 0.0}
T, WB, RH = np.array([10.0]), np.array([5.0]), np.array([50.0])


def test_tower_water_by_hand():
    # evaporative ratio at 10 C: 1 - (-0.279 + 0.109 - 3.45 + 26.7) / 100 = 0.7692
    # evaporation: 1 kWh = 3412.14 BTU x 0.7692 / 1050 BTU/lb / 8.34 lb/gal = 0.29973 gal
    # drift: 3412.14 / (8.34 x 10) x 0.0001 = 0.004091 gal
    # blowdown + drift = 0.29973 / 4 = 0.074933, so blowdown = 0.070842
    w, c, r = ph.hourly_rates(T, WB, "towers", SIMPLE, RH)
    assert c[0] == pytest.approx(0.29973 + 0.004091, rel=2e-4)
    assert r[0] == pytest.approx(0.070842, rel=2e-4)
    assert w[0] == pytest.approx(0.29973 + 0.074933, rel=2e-4)


def test_outside_air_by_hand():
    # 1,000 cfm per MW at full use: 1 cfm per kW = 0.000471947 m3/s x 1.15 kg/m3 = 0.00054274 kg/s per kW
    # outside at 30 C and 80%: saturation 0.6112 exp(17.62 x 30 / 273.12) = 4.2337 kPa, vapor 3.3870 kPa, humidity 0.622 x 3.3870 / 97.938 = 0.021510
    # indoors at the 15 C dew point: saturation 1.7017 kPa, humidity 0.622 x 1.7017 / 99.623 = 0.010625, so 0.010885 kg/kg comes out
    # condensate: 0.00054274 x 3600 s x 0.010885 = 0.021268 kg per kWh, / 3.78541 kg/gal = 0.0056184 gal
    # latent heat: 0.00054274 x 2450 kJ/kg x 0.010885 = 0.014474 kW per kW
    # sensible: 0.00054274 x 1.01 x (30 - 31) = -0.00054816 kW per kW, with the supply air at 31 C
    p = {**C, "oa_cfm_per_mw": 1000.0, "utilization": 1.0, "supply_air": 31.0, "humidify_share": 1.0}
    t, rh = np.array([30.0]), np.array([80.0])
    wb = ph.wet_bulb(t, rh)
    assert ph.hourly_water_with_air(t, wb, p, rh)[1][0] == pytest.approx(0.0056184, rel=1e-3)
    outside, latent = ph.hourly_outside_air_heat(t, wb, p, rh)
    assert latent[0] == pytest.approx(0.014474, rel=1e-3)
    assert outside[0] == pytest.approx(-0.00054816, rel=1e-3)


def test_humidifier_by_hand():
    # outside at -20 C and 50%: saturation 0.6112 exp(17.62 x -20 / 223.12) = 0.12597 kPa, vapor 0.062985, humidity 0.00038688
    # the -9 C dew point: saturation 0.31047 kPa, humidity 0.0019117, so 0.0015248 kg/kg goes in, all of it with humidifiers at full share
    # water: 0.00054274 x 3600 x 0.0015248 / 3.78541 = 0.00078703 gal per kWh
    p = {**C, "oa_cfm_per_mw": 1000.0, "utilization": 1.0, "humidify_share": 1.0}
    t, rh = np.array([-20.0]), np.array([50.0])
    assert ph.hourly_water_with_air(t, ph.wet_bulb(t, rh), p, rh)[0][0] == pytest.approx(0.00078703, rel=2e-3)


def test_lake_by_hand():
    # 100 MW x 0.65 x 1.11 = 72.15 MW of heat. Flow at an 8 C rise: 72.15e6 / (1000 x 4186 x 8) = 2.1545 m3/s
    # at 10 C and 10 mph: es(10.5) - es(9.5) = 0.8228 mb/C by Magnus, f = 7.0e-7 g/(cm2 s mb)
    # evaporation 585 x f x 0.8228 = 3.3694e-4; conduction 585 x f x 0.6687 = 2.7382e-4; radiation 4 x 0.97 x 1.3542e-12 x 283.15^3 = 1.1928e-4 cal/(cm2 s C)
    # share to evaporation 3.3694 / 7.3004 = 0.46154, or 72.15e6 x 0.46154 / (2.45e6 J/kg x 1000 kg/m3) = 0.013592 m3/s
    assert lake.withdrawal_m3s(100, 0.65, 1.11, 8.0) == pytest.approx(2.1545, rel=1e-3)
    assert lake.evaporation_ratio(10.0, 10.0) == pytest.approx(0.46154, rel=2e-3)
    assert lake.forced_evaporation_m3s(100, 0.65, 1.11, 10.0, 10.0) == pytest.approx(0.013592, rel=2e-3)
