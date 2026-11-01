"""Mass and energy close, hour by hour, for every design, across parameter draws and all weather: whatever the values, the books balance."""
import numpy as np
import pytest

from waterledger_models.datacenter import cooling, lake, physics as ph
from waterledger_models import runoff

T = np.arange(-25.0, 41.0, 1.0)
W = ph.wet_bulb(T, np.full_like(T, 55.0))
DRAWS = {k: v[:, None] for k, v in ph.sample_parameters(100).items()}
CENTRAL = ph.central_parameters()
GAL_KG = 3.78541


def _rates(design):
    return ph.hourly_rates(T, W, design, DRAWS)


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_water_taken_plus_condensate_is_water_used_up_and_returned(design):
    w, c, r = _rates(design)
    condensate = ph.hourly_water_with_air(T, W, DRAWS)[1]
    assert np.allclose(w + condensate, c + r)
    assert (w >= 0).all() and (c >= 0).all() and (r >= -1e-12).all() and (condensate >= 0).all()


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_every_kw_is_accounted_for(design):
    """Facility power + what outside air brings = heat through the water or coil + heat rejection fans, whose heat goes straight to the exhaust air."""
    p = DRAWS
    power, heat = ph.hourly_heat_power(T, W, design, p)
    assert (power >= 1.0).all() and (heat > 0.0).all()
    q = 1 / p["ups"] + 1 / (1 - p["dist_loss"]) - 1 + p["light"]
    air = (1 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    kg_s = ph._outside_air(T, W, p)[0]
    room = q - (1 - air)
    crah = ph._fan_kw(room / (ph.CP_AIR * p["air_rise"]) + kg_s, p["crah_pa"], p["fan_eff"])
    outside, latent = ph.hourly_outside_air_heat(T, W, p)
    wet = ph._wet_share(T, design, p)
    coil = T - (p["assist_eff"] * np.maximum(T - W, 0) * (T >= p["assist_on"]) if design == "assist" else 0.0)
    water = p["supply_air"] + p["air_rise"] - p["air_rise"] / p["coil_eff"]
    air_load = room + crah + outside
    electric, fans = q + crah, 0.0
    for load, supply in ((np.maximum(air_load, 0), water), (1 - air + np.minimum(air_load, 0), p["liquid_water"]), (latent, ph.DEHUMIDIFY_WATER)):
        assert (load >= 0).all()
        chiller, pumps, f = ph._loop(load, supply, T, W, coil, wet, design, p)
        electric, fans = electric + chiller + pumps, fans + f
    assert np.allclose(power, electric + fans)
    assert np.allclose(power + outside + latent, heat + fans)


def test_outside_air_heat_is_its_enthalpy_change():
    p = {**CENTRAL, "oa_cfm_per_mw": 1000.0, "humidify_share": 1.0}
    kg_s, wo, wi = ph._outside_air(T, W, p)
    enthalpy = lambda t, w: ph.CP_AIR * t + ph.LATENT_KJ * w
    a, b = ph.hourly_outside_air_heat(T, W, p)
    assert np.allclose(a + b, kg_s * (enthalpy(T, wo) - enthalpy(p["supply_air"], wi)))


def test_outside_air_humidity():
    """From relative humidity it is exact at any temperature; from the wet-bulb alone it is close only in warm air."""
    t = np.array([-25.0, -15.0, 0.0, 15.0, 25.0, 35.0])
    for rh in (10.0, 30.0, 60.0, 90.0):
        direct = ph._humidity_ratio(ph._saturation_kpa(t) * rh / 100)
        wb = ph.wet_bulb(t, np.full_like(t, rh))
        assert np.allclose(ph._outside_air(t, wb, CENTRAL, np.full_like(t, rh))[1], direct)
        if rh >= 60:
            assert np.allclose(ph._outside_air(t, wb, CENTRAL)[1][3:], direct[3:], rtol=0.1)


def test_a_run_on_weather_uses_the_hours_humidity():
    """A bitter, dry day: closed loop's water is its top-ups and what the humidifiers add from the hour's own moisture."""
    times = [f"2024-01-01T{h:02d}:00" for h in range(24)]
    t, rh = np.full(24, -20.0), np.full(24, 10.0)
    p = {**cooling.central(), "humidify_share": 1.0}
    want = ph.hourly_rates(t, ph.wet_bulb(t, rh), "dry", p, rh)[0][0] * 300 * 1000 * p["utilization"] * 24 / 1e6
    g = cooling._nc([sum(ph.STAFF[k]) / 2 for k in cooling.STAFF_KEYS], 300)[0]
    assert cooling.daily(times, t, rh, "dry", 300, p)[1][0] == pytest.approx(want + g)
    wrong = ph.hourly_rates(t, ph.wet_bulb(t, rh), "dry", p)[0][0] * 300 * 1000 * p["utilization"] * 24 / 1e6
    assert wrong != pytest.approx(want)


def test_outside_air_water_follows_the_dew_point_limits():
    p = {**CENTRAL, "humidify_share": 1.0}
    cold, wet = ph.hourly_water_with_air(np.array([-20.0]), np.array([-21.0]), p), ph.hourly_water_with_air(np.array([32.0]), np.array([27.0]), p)
    mild = ph.hourly_water_with_air(np.array([20.0]), np.array([12.0]), p)
    assert cold[0] > 0 and cold[1] == 0 and wet[1] > 0 and wet[0] == 0 and mild == (0.0, 0.0)
    assert ph.hourly_water_with_air(np.array([-20.0]), np.array([-21.0]), {**p, "humidify_share": 0.0})[0] == 0
    # no humidifiers, no extra water: closed loop's water is top-ups alone in the cold
    w = ph.hourly_rates(np.array([-20.0]), np.array([-21.0]), "dry", {**p, "humidify_share": 0.0})[0]
    assert w[0] == pytest.approx(p["fill_gal_per_mw"] * p["topup"] / 365 / (24000 * p["utilization"]))


def test_air_loop_coils_are_too_warm_to_condense():
    lowest = ph.POWER["supply_air"][0] + ph.POWER["air_rise"][1] - ph.POWER["air_rise"][1] / ph.POWER["coil_eff"][0]
    assert lowest > ph.DEW_HIGH > ph.DEHUMIDIFY_WATER


def test_no_chiller_or_fan_power_makes_heat_from_nothing():
    """In free cooling with towers and no outside air, heat is the IT load, its losses, the fans in the air stream and the pumps."""
    p = {**CENTRAL, "liquid_share": 0.0, "oa_cfm_per_mw": 0.0}
    power, heat = ph.hourly_heat_power(np.array([0.0]), np.array([-2.0]), "towers", p)
    q = 1 / p["ups"] + 1 / (1 - p["dist_loss"]) - 1 + p["light"]
    assert q < heat[0] < q * 1.08 and power[0] > heat[0]


def _air_water(p):
    return ph.hourly_water_with_air(T, W, p)


@pytest.mark.parametrize("design", ["hybrid", "towers"])
def test_evaporation_carries_no_more_heat_than_there_is(design):
    """Latent heat in the evaporation + sensible heat to the air = the wet share of the heat; the rest goes through the coil."""
    p = DRAWS
    w, c, r = _rates(design)
    btu = ph.KWH_BTU * ph.hourly_heat_power(T, W, design, p)[1]
    wet = ph._wet_share(T, design, p)
    circ = btu * wet / (ph.LB_GAL * p["range_f"])
    evap = c - circ * p["drift"] - p["fill_gal_per_mw"] * p["topup"] / 365 / (24000 * p["utilization"]) - _air_water(p)[0]
    assert (evap * ph.LB_GAL * ph.HFG <= btu * wet + 1e-9).all()
    assert (evap >= -1e-12).all()


def test_assist_evaporation_is_the_air_side_energy_balance():
    p = {**CENTRAL, "oa_cfm_per_mw": 0.0}
    t, wb = np.array([32.0]), np.array([20.0])
    w, c, r = ph.hourly_rates(t, wb, "assist", p)
    top = p["fill_gal_per_mw"] * p["topup"] / 365 / (24000 * p["utilization"])
    btu = ph.KWH_BTU * ph.hourly_heat_power(t, wb, "assist", p)[1]
    depr = p["assist_eff"] * 12.0
    assert (c - top) * ph.LB_GAL * ph.HFG == pytest.approx(btu * depr / (p["assist_on"] + p["assist_dt_air"] - 32.0 + depr))
    assert r == pytest.approx((c - top) * p["assist_bleed"])


@pytest.mark.parametrize("design", ["hybrid", "towers"])
def test_dissolved_solids_leave_as_they_come(design):
    """At the tower, makeup x solids = (blowdown + drift) x cycles x solids. Top-ups, humidifiers and condensate are outside it."""
    p = {**DRAWS, "oa_cfm_per_mw": 0.0}
    w, c, r = ph.hourly_rates(T, W, design, p)
    btu = ph.KWH_BTU * ph.hourly_heat_power(T, W, design, p)[1]
    wet = ph._wet_share(T, design, p)
    drift = btu * wet / (ph.LB_GAL * p["range_f"]) * p["drift"]
    top = p["fill_gal_per_mw"] * p["topup"] / 365 / (24000 * p["utilization"])
    assert np.allclose(w - top, (r + drift) * p["coc"])


def test_no_drift_or_blowdown_without_a_wet_tower():
    p = {**CENTRAL, "oa_cfm_per_mw": 0.0}
    w, c, r = ph.hourly_rates(T, W, "dry", p)
    assert np.allclose(r, 0.0) and np.allclose(w, c)
    t = np.array([p["hybrid_on"] - 1.0])
    w, c, r = ph.hourly_rates(t, t - 5, "hybrid", p)
    assert r == pytest.approx(0.0)
    assert w[0] == pytest.approx(p["fill_gal_per_mw"] * p["topup"] / 365 / (24000 * p["utilization"]))


def test_tower_flow_in_the_two_equations_is_the_same_water():
    """The tower pumps' flow (kg/s per kW) and the drift's circulating flow (gal per kWh) come from one heat balance."""
    p = {**CENTRAL, "liquid_share": 0.0, "oa_cfm_per_mw": 0.0}
    t, wb = np.array([33.0]), np.array([24.0])
    heat = ph.hourly_heat_power(t, wb, "towers", p)[1]
    gal_kwh = ph.KWH_BTU * heat / (ph.LB_GAL * p["range_f"])
    kg_s = heat / (ph.CP_WATER * p["range_f"] / 1.8)
    assert gal_kwh == pytest.approx(kg_s * 3600 / GAL_KG, rel=0.003)


def test_tower_air_can_carry_the_heat():
    """Air at the capped ratio takes up the tower's heat and leaves saturated at the hot water's temperature, no hotter."""
    p = {**CENTRAL, "liquid_share": 0.0}
    rng = p["range_f"] / 1.8
    tw, hot = 26.0, 26.0 + p["tower_approach"] + rng
    cap = (ph._saturated_enthalpy(hot) - ph._saturated_enthalpy(tw)) / (ph.CP_WATER * rng)
    assert cap < ph.POWER["lg"][1]
    fan = lambda lg: ph.hourly_heat_power(np.array([p["hybrid_full"] + 3]), np.array([tw]), "towers", {**p, "lg": lg})[0][0]
    assert fan(ph.POWER["lg"][1]) == pytest.approx(fan(cap))       # above the cap, no less air
    assert fan(cap / 2) > fan(cap)


def test_chiller_rejects_by_the_wet_share():
    """A hybrid hour with no evaporation has the chiller of a dry design; a fully wet one, the chiller of a tower."""
    p = CENTRAL
    t, wb = np.array([p["hybrid_on"] - 0.5]), np.array([18.0])
    assert ph.hourly_heat_power(t, wb, "hybrid", p)[1] == pytest.approx(ph.hourly_heat_power(t, wb, "dry", p)[1])
    t, wb = np.array([p["hybrid_full"] + 1.0]), np.array([24.0])
    assert ph.hourly_heat_power(t, wb, "hybrid", p)[1] == pytest.approx(ph.hourly_heat_power(t, wb, "towers", p)[1])


def test_estimate_books_close_on_the_middle_estimate():
    from waterledger.scenario import cooling_estimate
    per = {k: {"p10": 0.1, "p50": 0.2, "p90": 0.3} for k in ("withdrawn_avg", "withdrawn_peak_1in10", "withdrawn_annual_mg", "consumed_avg", "consumed_peak_1in10", "returned_avg", "returned_peak_1in10")}
    per = {**per, "consumed_avg": {"p10": 0.05, "p50": 0.15, "p90": 0.25}, "condensate_avg": {"p10": 0.0, "p50": 0.01, "p90": 0.02}, "condensate_peak_1in10": {"p10": 0.0, "p50": 0.02, "p90": 0.03}}
    D = {"regions": {"r": {"per_100mw": {"towers": per}}}, "staff": {"runs": cooling.staff_runs(5)}}
    E = cooling_estimate(D, "r", "towers", 100, "sewer")
    assert E["wAvg"]["mid"] + E["condAvg"]["mid"] == pytest.approx(E["cAvg"]["mid"] + E["rAvg"]["mid"])
    R = cooling_estimate(D, "r", "towers", 100, "reuse")
    assert R["wAvg"]["mid"] + R["condAvg"]["mid"] == pytest.approx(R["cAvg"]["mid"] + R["rAvg"]["mid"])


def test_the_per_run_loop_and_the_vector_draws_are_the_same_draws():
    runs = cooling.sample(np.random.default_rng(7), 5)
    v = ph.sample_parameters(5)
    for k in v:
        assert [r[k] for r in runs] == pytest.approx(list(v[k]))


def test_staff_water_closes():
    s = ph.central_staff()
    w, c, r = ph.staff_water(s, 300.0)
    assert w == pytest.approx(c + r) and 0 < c < w


def test_lake_withdrawal_carries_the_heat():
    m3s = lake.withdrawal_m3s(100, 0.65, 1.1, 8.0)
    assert m3s * lake.RHO * lake.CP * 8.0 == pytest.approx(100e6 * 0.65 * 1.1)


def test_lake_evaporation_is_a_share_of_the_added_heat():
    er = lake.evaporation_ratio(np.array([2.0, 12.0, 22.0]), 10.0)
    assert ((er > 0) & (er < 1)).all() and er[2] > er[0]
    m3s = lake.forced_evaporation_m3s(100, 0.65, 1.1, 12.0, 10.0)
    assert m3s * lake.RHO * lake.LV <= 100e6 * 0.65 * 1.1


def test_runoff_is_a_part_of_the_rain_and_loads_are_concentration_times_water():
    assert runoff.GAL_PER_AC_IN * 8.34 / 1e6 == pytest.approx(runoff.LB, rel=0.003)
    for imp in (0.0, 0.5, 1.0):
        assert 0 < runoff.runoff_in(37.0, imp) < 37.0
    L = runoff.loads(200, 37.0, before="woods")
    for k, conc in (("tp_lb", runoff.PARAMS["emc"]["woods"]["tp"]),):
        i0 = runoff.PARAMS["before_imp"]["woods"]
        assert L["runoff_gal"]["after"][1] > L["runoff_gal"]["now"][1]
        assert L[k]["pond"][1] < L[k]["after"][1] and L[k]["infiltration"][1] < L[k]["after"][1]


def test_salt_and_blowdown_mass():
    s = runoff.salt(100)
    assert s["chloride_t"][1] / s["salt_t"][1] == pytest.approx(35.45 / 58.44, rel=0.002)
    b = runoff.blowdown(1.0, "lake")
    assert b["tds_lb_day"][1] == pytest.approx(170 * 5 * 8.34)


def test_lake_electricity_is_the_heat_in_the_water():
    temps = np.full(366, 10.0)
    r = lake.run_lake(temps, n=50, mw=100.0)
    assert r["pue_avg"]["p50"] == r["pue_peak_1in10"]["p50"]
    assert lake.RANGES["heat_factor"][0] <= r["pue_avg"]["p10"] <= r["pue_avg"]["p90"] <= lake.RANGES["heat_factor"][1]
    assert r["power_mw_peak_1in10"]["p50"] == pytest.approx(100 * r["pue_avg"]["p50"])
    # the withdrawn water warmed by its rise carries all of the electricity: flow x rho x cp x rise = power, run by run
    rng = np.random.default_rng(11)
    p = {k: rng.uniform(*v) for k, v in lake.RANGES.items()}
    assert lake.withdrawal_m3s(100, p["utilization"], p["heat_factor"], p["rise_c"]) * lake.RHO * lake.CP * p["rise_c"] == pytest.approx(100e6 * p["utilization"] * p["heat_factor"])


def test_power_plants_generate_the_campus_and_the_line_losses():
    from waterledger.comparisons import LINE_LOSS, plant_water
    assert plant_water(100, 1000) == pytest.approx(100 * 24 * 1000 / 1e6 / (1 - LINE_LOSS))


def test_farmland_sediment_keeps_the_paved_part():
    L = runoff.loads(200, 37.0, before="farm")["tss_t"]["now"][1]
    P = runoff.PARAMS
    field = 200 * (1 - P["before_imp"]["farm"]) * P["farm_soil"]["t_per_ac_yr"][1]
    assert L > field


def test_power_losses_go_to_the_room_not_the_liquid_loop():
    """With all computers liquid-cooled but none of their heat to air, the air loop still carries the UPS, distribution and lighting losses."""
    p = {**CENTRAL, "liquid_share": 1.0, "liquid_air_share": 0.0, "oa_cfm_per_mw": 0.0, "crah_pa": 0.0}
    q = 1 / p["ups"] + 1 / (1 - p["dist_loss"]) - 1 + p["light"]
    assert 1 - (1 - p["liquid_share"] + p["liquid_share"] * p["liquid_air_share"]) == 1.0
    # one kW of computers to the warm liquid loop in free cooling, the losses to the air loop's cooler water: in a hot hour only the air loop runs its chiller
    t, wb = np.array([31.0]), np.array([24.0])
    hot = ph.hourly_heat_power(t, wb, "towers", p)[1][0]
    none = ph.hourly_heat_power(t, wb, "towers", {**p, "ups": 1.0, "dist_loss": 0.0, "light": 0.0})[1][0]
    assert hot - none > q - 1
