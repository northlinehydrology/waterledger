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
def test_water_taken_is_water_used_up_and_returned(design):
    w, c, r = _rates(design)
    assert np.allclose(w, c + r)
    assert (w >= 0).all() and (c >= 0).all() and (r >= -1e-12).all()


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_all_electricity_leaves_as_heat(design):
    """Facility power = heat through the water or coil + heat rejection fans, whose heat goes straight to the exhaust air."""
    power, heat = ph.hourly_heat_power(T, W, design, DRAWS)
    assert (heat > 1.0).all() and (power >= heat).all()
    q = 1 / DRAWS["ups"] + 1 / (1 - DRAWS["dist_loss"]) - 1 + DRAWS["light"]
    air = (1 - DRAWS["liquid_share"]) + DRAWS["liquid_share"] * DRAWS["liquid_air_share"]
    crah = ph._fan_kw(q * air / (ph.CP_AIR * DRAWS["air_rise"]), DRAWS["crah_pa"], DRAWS["fan_eff"])
    wet = ph._wet_share(T, design, DRAWS)
    coil = T - (DRAWS["assist_eff"] * np.maximum(T - W, 0) * (T >= DRAWS["assist_on"]) if design == "assist" else 0.0)
    water = DRAWS["supply_air"] + DRAWS["air_rise"] - DRAWS["air_rise"] / DRAWS["coil_eff"]
    in_water, fans = q + crah, 0.0
    for load, supply in ((q * air + crah, water), (q * (1 - air), DRAWS["liquid_water"])):
        chiller, pumps, f = ph._loop(load, supply, T, W, coil, wet, design, DRAWS)
        in_water, fans = in_water + chiller + pumps, fans + f
    assert np.allclose(heat, in_water) and np.allclose(power, in_water + fans)


def test_no_chiller_or_fan_power_makes_heat_from_nothing():
    """In free cooling with towers, heat is the IT load, its losses, the fans in the air stream and the pumps, nothing else."""
    p = {**CENTRAL, "liquid_share": 0.0}
    power, heat = ph.hourly_heat_power(np.array([0.0]), np.array([-2.0]), "towers", p)
    q = 1 / p["ups"] + 1 / (1 - p["dist_loss"]) - 1 + p["light"]
    assert q < heat[0] < q * 1.08 and power[0] > heat[0]


@pytest.mark.parametrize("design", ["hybrid", "towers"])
def test_evaporation_carries_no_more_heat_than_there_is(design):
    """Latent heat in the evaporation + sensible heat to the air = the wet share of the heat; the rest goes through the coil."""
    p = DRAWS
    w, c, r = _rates(design)
    btu = ph.KWH_BTU * ph.hourly_heat_power(T, W, design, p)[1]
    wet = ph._wet_share(T, design, p)
    circ = btu * wet / (ph.LB_GAL * p["range_f"])
    evap = c - circ * p["drift"] - p["fill_gal_per_mw"] * p["topup"] / 365 / (24000 * p["utilization"])
    assert (evap * ph.LB_GAL * ph.HFG <= btu * wet + 1e-9).all()
    assert (evap >= -1e-12).all()


def test_assist_evaporation_is_the_air_side_energy_balance():
    p = CENTRAL
    t, wb = np.array([32.0]), np.array([20.0])
    w, c, r = ph.hourly_rates(t, wb, "assist", p)
    top = p["fill_gal_per_mw"] * p["topup"] / 365 / (24000 * p["utilization"])
    btu = ph.KWH_BTU * ph.hourly_heat_power(t, wb, "assist", p)[1]
    depr = p["assist_eff"] * 12.0
    assert (c - top) * ph.LB_GAL * ph.HFG == pytest.approx(btu * depr / (p["assist_on"] + p["assist_dt_air"] - 32.0 + depr))
    assert r == pytest.approx((c - top) * p["assist_bleed"])


@pytest.mark.parametrize("design", ["hybrid", "towers"])
def test_dissolved_solids_leave_as_they_come(design):
    """Makeup x solids = (blowdown + drift) x cycles x solids, at the tower."""
    p = DRAWS
    w, c, r = _rates(design)
    btu = ph.KWH_BTU * ph.hourly_heat_power(T, W, design, p)[1]
    wet = ph._wet_share(T, design, p)
    drift = btu * wet / (ph.LB_GAL * p["range_f"]) * p["drift"]
    top = p["fill_gal_per_mw"] * p["topup"] / 365 / (24000 * p["utilization"])
    assert np.allclose(w - top, (r + drift) * p["coc"])


def test_no_drift_or_blowdown_without_a_wet_tower():
    for design in ("dry",):
        w, c, r = ph.hourly_rates(T, W, design, CENTRAL)
        assert np.allclose(r, 0.0) and np.allclose(w, c)
    t = np.array([CENTRAL["hybrid_on"] - 1.0])
    w, c, r = ph.hourly_rates(t, t - 5, "hybrid", CENTRAL)
    assert r == pytest.approx(0.0)
    assert w[0] == pytest.approx(CENTRAL["fill_gal_per_mw"] * CENTRAL["topup"] / 365 / (24000 * CENTRAL["utilization"]))


def test_tower_flow_in_the_two_equations_is_the_same_water():
    """The tower pumps' flow (kg/s per kW) and the drift's circulating flow (gal per kWh) come from one heat balance."""
    p = {**CENTRAL, "liquid_share": 0.0}
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
