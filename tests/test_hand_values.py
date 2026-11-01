"""Values worked by hand from the equations, with the numbers written out here, not read from the code's constants, so a wrong constant in the code fails."""
import numpy as np
import pytest

from waterledger_models.datacenter import cooling, lake, physics as ph

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


def test_peak_day_by_hand():
    # Average load 0.75 of capacity, load factor 0.94: 0.75 / 0.94 = 0.79787 of capacity on the peak day. EPRI's co-location pair: 0.57 / 0.88 = 0.64773.
    assert ph.peak_utilization({"utilization": 0.75, "load_factor": 0.94}) == pytest.approx(0.79787, rel=1e-4)
    assert ph.peak_utilization({"utilization": 0.57, "load_factor": 0.88}) == pytest.approx(0.64773, rel=1e-4)
    assert ph.peak_utilization({"utilization": 0.95, "load_factor": 0.90}) == 1.0     # never above capacity


def test_peak_day_in_the_model():
    """One steady day of weather, towers. The peak day's evaporation scales with its load: at the middle, 0.65 / 0.91 = 0.71429 of capacity against 0.65 on average,
    a factor of 1 / 0.91 = 1.0989. Loop top-ups and outside air go with capacity, not load, so towers come in a little under that and closed loop stays put."""
    t = [f"2023-07-{d:02d}T{h:02d}:00" for d in range(1, 4) for h in range(24)]
    r = cooling.run_location(t, [25.0] * 72, [60.0] * 72, n=8, mw=100.0)
    tw = r["towers"]
    assert tw["withdrawn_peak_1in10"]["central"] / tw["withdrawn_avg"]["central"] == pytest.approx(1 / 0.91, rel=2e-3)
    assert tw["withdrawn_peak_full_capacity"]["central"] / tw["withdrawn_avg"]["central"] == pytest.approx(1 / 0.65, rel=4e-3)
    assert r["dry"]["withdrawn_peak_1in10"]["central"] == pytest.approx(r["dry"]["withdrawn_avg"]["central"], rel=1e-9)


def test_design_dry_bulb_by_hand():
    # 1,000 hours at 1, 2, ... 1000 C, so the 0.4% is the temperature with 4 hours above it: position 0.996 x 999 = 995.004 between 1 and 1000, which is 996.004 C
    assert ph.design_dry_bulb(np.arange(1.0, 1001.0)) == pytest.approx(996.004)


def test_hybrid_ramp_runs_to_the_locations_own_design_temperature():
    p = {**C, "switch_on": 24.0, "hybrid_full_offset": 0.0}
    # Houston-like, design dry-bulb 36.7: at 30.35 C the ramp is (30.35 - 24) / (36.7 - 24) = 0.5. Michigan-like, 31.0: (27.5 - 24) / (31 - 24) = 0.5
    assert ph._wet_share(np.array([30.35]), "hybrid", {**p, "design_db": 36.7})[0] == pytest.approx(0.5)
    assert ph._wet_share(np.array([27.5]), "hybrid", {**p, "design_db": 31.0})[0] == pytest.approx(0.5)
    # design dry-bulb 23 is under the 24 C switch: wet mode runs over the 1 K above the switch, half at 24.5 and all of it at 25
    cool = {**p, "design_db": 23.0}
    assert ph._wet_share(np.array([24.0, 24.5, 25.0, 30.0]), "hybrid", cool) == pytest.approx([0.0, 0.5, 1.0, 1.0])


def test_switch_point_by_hand():
    # Air loop water = supply air + air rise - air rise / coil effectiveness = 31 + 16.65 - 16.65 / 0.8 = 26.8375 C. Half the computers liquid-cooled, with 20% of their
    # heat still going to air: the air share is 0.5 + 0.5 x 0.2 = 0.6. Weighted supply 0.6 x 26.8375 + 0.4 x 38.5 = 31.5025 C; less the 7.5 K approach, 24.0025 C.
    mid = {**C, "supply_air": 31.0, "air_rise": 16.65, "coil_eff": 0.8, "liquid_share": 0.5, "liquid_air_share": 0.2, "liquid_water": 38.5, "dc_approach": 7.5, "switch_margin": 0.0}
    assert ph.loop_limit(mid) == pytest.approx(24.0025)
    assert ph.switch_point(mid) == pytest.approx(24.0025)
    assert ph.switch_point({**mid, "switch_margin": 2.0}) == pytest.approx(26.0025)
    # All air, 27 C supply: 27 + 19.4 - 19.4 / 0.7 = 18.686 C, less 10 K = 8.686 C, below any published setting, so 70 F (21.1 C)
    cold = {**mid, "supply_air": 27.0, "air_rise": 19.4, "coil_eff": 0.7, "liquid_share": 0.0, "dc_approach": 10.0}
    assert ph.loop_limit(cold) == pytest.approx(8.686, abs=1e-3)
    assert ph.switch_point(cold) == pytest.approx(21.1)
    # All liquid at 45 C with 10% to air on a 26.8375 C air loop: 0.1 x 26.8375 + 0.9 x 45 = 43.18 C, less 5 K = 38.18 C, above 95 F, so 35.1 C
    warm = {**mid, "liquid_share": 1.0, "liquid_air_share": 0.1, "liquid_water": 45.0, "dc_approach": 5.0}
    assert ph.loop_limit(warm) == pytest.approx(38.184, abs=1e-3)
    assert ph.switch_point(warm) == pytest.approx(35.1)
    # An operator's setting wins
    assert ph.switch_point({**mid, "switch_on": 27.8}) == 27.8


def test_assist_water_at_the_loop_switch_by_hand():
    # Setting 24 C, 30 C air at 21 C wet-bulb, effectiveness 0.75: the pads take 0.75 x 9 = 6.75 K off the air. The fans slow until the air leaves at 24 + 11 = 35 C,
    # so of 1 kW of heat the share to evaporation is 6.75 / (35 - 30 + 6.75) = 0.57447. No outside air, no losses: 3412.14 x 0.57447 / 1050 / 8.34 = 0.22385 gal per IT kWh.
    p = {**SIMPLE, "switch_on": 24.0, "assist_eff": 0.75, "assist_dt_air": 11.0, "assist_bleed": 0.0, "topup": 0.0}
    t, wb = np.array([30.0]), np.array([21.0])
    heat = ph.hourly_heat_power(t, wb, "assist", p)[1]
    w = ph.hourly_rates(t, wb, "assist", p, heat=np.array([1.0]))[0]
    assert w[0] == pytest.approx(0.22385, rel=1e-3)
    assert ph.hourly_rates(np.array([23.9]), wb, "assist", p, heat=np.array([1.0]))[0][0] == pytest.approx(0.0)     # below the setting, no evaporation
    assert heat[0] > 0


def test_lake_carries_usgs_error_by_hand():
    # USGS's 21% for the Great Lakes on the 0.013592 m3/s worked above: 0.79 x 0.013592 = 0.010738 and 1.21 x 0.013592 = 0.016446, with the flow through unchanged
    assert lake.RANGES["evap_error"] == (0.79, 1.21)
    assert lake.forced_evaporation_m3s(100, 0.65, 1.11, 10.0, 10.0, 0.79) == pytest.approx(0.010738, rel=2e-3)
    assert lake.forced_evaporation_m3s(100, 0.65, 1.11, 10.0, 10.0, 1.21) == pytest.approx(0.016446, rel=2e-3)
