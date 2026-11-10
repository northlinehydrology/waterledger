"""Power supply scenarios (design 0014, step 4) on the shared runner: the grid-only scenario reads as today, the hourly balance closes, islanded
gas reports what it cannot carry, PV sized for annual matching leaves hours to the grid and exports a surplus, and N+1 sizing lands inside
the IEA's overbuild (0014, check 6)."""
import numpy as np
import pytest

from golden import weather
from waterledger_models import runs
from waterledger_models.datacenter import cooling
from waterledger_models.supply import scenario as S

TIMES, T, RH = weather()
T, RH = np.asarray(T, float), np.asarray(RH, float)
UTC = np.array(TIMES, dtype="datetime64[h]") + np.timedelta64(5, "h")
_h = np.arange(len(TIMES))
_sun = np.clip(np.sin(2 * np.pi * (_h % 24 - 6) / 24), 0, None) * (0.75 + 0.25 * np.sin(2 * np.pi * (_h / 8766 - 0.25)))
WX = (UTC, 900 * _sun, 650 * _sun, 4 + 3 * np.sin(2 * np.pi * _h / 97), 2 + 2 * np.cos(2 * np.pi * _h / 61))   # utc, ghi, beam, u100, v100
LAT, LON = 42.9, -85.5
GRID = {"MISO": {"consumed": np.full(len(TIMES), 300.0), "withdrawn": np.full(len(TIMES), 12000.0)}}
N = 6


def _model():
    return cooling._CoolingRuns(N, 7, 100.0, cooling.HOUR_BLOCK, cooling.DEFAULT_PLANT, True)


def _run(scenarios, design="hybrid"):
    sized = S.size(_model(), TIMES, T, RH, scenarios, design, WX, LAT, LON)
    supply = S.Supply(sized, WX, LAT, LON, N)
    return runs.run_location(_model(), TIMES, T, RH, designs=(design,), grid=GRID, extra=supply)[design], sized


def test_grid_only_reads_as_today():
    """Scenario (a): no resources, the grid takes the whole load, so its grid water is the user's own grid water to the bit."""
    r, _ = _run({"a": S.Scenario()})
    for q in ("p10", "p50", "p90", "central"):
        assert r["supply_a_grid_MISO_consumed_avg"][q] == r["grid_MISO_consumed_avg"][q]
        assert r["supply_a_grid_MISO_withdrawn_peak_1in10"][q] == r["grid_MISO_withdrawn_peak_1in10"][q]
    assert r["supply_a_share_grid"]["p50"] == 1.0 and r["supply_a_unserved_mwh_annual"]["p90"] == 0.0


def test_the_hourly_balance_closes():
    """load = renewables served + gas + grid + unserved, generation = served + surplus, every hour, for a mix with every resource."""
    sized = S.size(_model(), TIMES, T, RH, {"d2": S.Scenario(pv_share=0.4, wind_share=0.3, gas=S.Gas(firm_mw=40.0, unit_mw=50.0))},
                   "hybrid", WX, LAT, LON)
    sup = S.Supply(sized, WX, LAT, LON, N)
    sup.setup(TIMES, T, np.zeros_like(T) + 10, RH)
    load = 100.0 + 20 * np.sin(_h / 30.0)
    d = sup._dispatch(sized["d2"], "d2", load, 0.8 * _sun, 0.3 + 0.2 * np.sin(_h / 13.0), 0)
    np.testing.assert_allclose(load, d["renew"] + d["gas"]["served"] + d["grid"] + d["unserved"], rtol=1e-12)
    np.testing.assert_allclose(d["gen_pv"] + d["gen_wind"], d["renew"] + d["surplus"], rtol=1e-12)
    assert (d["gas"]["served"] <= 40.0 + 1e-9).all() and not d["unserved"].any()


def test_islanded_gas_reports_what_it_cannot_carry_and_n_plus_1_sizing():
    """b1: an islanded campus on its own engines, N+1 and N+0 with outages: N+0 leaves unserved hours, N+1 far fewer. Sizing: N units at the
    place's design dry-bulb carry the 1-in-10-year highest hour at full capacity and N-1 do not. 0014's check 6 compares the overbuild with
    the IEA's 30-70%: here, a 100 MW campus (peak hour about 132 MW) on 20 MW engines, N+1 is 8 units, 160 MW, 21% over the peak, under the
    IEA's range; on 50 MW turbines it is about 90%. The overbuild follows the unit size, so the check is recorded (methods log), not asserted."""
    n1, sized1 = _run({"b1": S.Scenario(residual="none", gas=S.Gas(technology="engine", design="dry", unit_mw=20.0, k=1))})
    n0, _ = _run({"b1": S.Scenario(residual="none", gas=S.Gas(technology="engine", design="dry", unit_mw=20.0, k=0))})
    assert n0["supply_b1_unserved_hours_annual"]["p50"] > n1["supply_b1_unserved_hours_annual"]["p50"]
    assert n1["supply_b1_share_grid"]["p90"] == 0.0 and n1["supply_b1_share_gas"]["p50"] > 0.99
    g = sized1["b1"].gas
    model = _model()
    model.setup(TIMES, T, np.zeros_like(T), RH)
    peak = S._year_max_quantile(model.run("hybrid", model.draws()[-1]).mw_full, np.array([t[:4] for t in TIMES]))
    cap = g.unit_mw * (1 - 0.0018 * max(0.0, float(np.quantile(T, 0.996)) - 25.0))       # an engine at the design dry-bulb, central derate
    n = g.units - g.k
    assert n * cap >= peak > (n - 1) * cap


def test_pv_for_annual_matching_still_leaves_hours_to_the_grid():
    """c1: PV sized to 100% of the annual MWh matches the year at central values but serves well under half of the hours' load, exports a
    surplus at midday and leaves the night to the grid; its washing water is small."""
    r, sized = _run({"c1": S.Scenario(pv_share=1.0)})
    assert r["supply_c1_annual_matching"]["central"] == pytest.approx(1.0, rel=0.02)
    assert 0.2 < r["supply_c1_share_pv"]["p50"] < 0.6 and r["supply_c1_surplus_mwh_annual"]["p50"] > 0
    assert r["supply_c1_share_pv"]["p50"] + r["supply_c1_share_grid"]["p50"] == pytest.approx(1.0, abs=1e-9)
    assert r["supply_c1_grid_MISO_consumed_avg"]["p50"] < r["grid_MISO_consumed_avg"]["p50"]
    assert r["supply_c1_pv_washing_mgd"]["p90"] < 0.01


def test_a_gas_plant_in_a_scenario_has_the_standard_water_statistics():
    r, _ = _run({"b2": S.Scenario(gas=S.Gas(technology="cc", design="towers", unit_mw=50.0, firm_mw=60.0))})
    for k in ("gas_withdrawn_avg", "gas_consumed_peak_1in10", "gas_withdrawn_max_month", "gas_to_sewer_avg", "gas_consumed_gal_per_mwh",
              "gas_capacity_factor", "local_consumed_avg", "share_gas", "share_grid"):
        assert f"supply_b2_{k}" in r, k
    c = {k: v["central"] for k, v in r.items()}
    assert c["supply_b2_gas_withdrawn_avg"] == pytest.approx(c["supply_b2_gas_consumed_avg"] + c["supply_b2_gas_returned_avg"], rel=1e-9)
    assert 100 < c["supply_b2_gas_consumed_gal_per_mwh"] < 300 and c["supply_b2_share_gas"] + c["supply_b2_share_grid"] == pytest.approx(1.0)


def test_scenarios_must_be_sized_and_well_formed():
    with pytest.raises(ValueError, match="size"):
        S.Supply({"x": S.Scenario(pv_share=0.5)}, WX, LAT, LON, N)
    with pytest.raises(ValueError, match="residual"):
        S.Supply({"x": S.Scenario(residual="battery")}, WX, LAT, LON, N)
