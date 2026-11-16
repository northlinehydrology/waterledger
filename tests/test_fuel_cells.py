"""Fuel cells as data centers use them (design 0019): solid oxide on gas, the heat rate by age from EIA's plants inside or above the data sheet's
range, start-up water consumed and closing the water balance, the age a setting and never state, and a modular plant's reserve share."""
import numpy as np
import pytest

from waterledger_models import heat_rejection as hr
from waterledger_models.gas import physics as gp
from waterledger_models.supply import scenario as S

DATASHEET = (5811.0, 7127.0)      # Bloom Energy Server 6.5, Btu/kWh HHV, new stacks to before they are swapped


def _weather(n=24 * 30):
    h = np.arange(n)
    tdb = 15 + 12 * np.sin(2 * np.pi * h / 24)
    rh = np.full(n, 60.0)
    return tdb, hr.wet_bulb(tdb, rh), rh


def test_the_heat_rate_is_solid_oxides_never_better_than_new_stacks():
    """F3: at central parameters, fuel per MWh between the data sheet's new-stack figure and EIA's aged fleet; every age band inside the range."""
    lo, hi = gp.TECH["fuel_cell"]["heat_rate"]
    assert DATASHEET[0] < lo < DATASHEET[1] < hi <= 7500.0
    tdb, twb, rh = _weather()
    p = gp.central_parameters("fuel_cell", "dry")
    h = gp.hourly(30.0, tdb, twb, rh, "fuel_cell", "dry", p, 100, 0.325)
    rate = h["fuel"].sum() / h["served"].sum() * gp.KWH_BTU
    assert lo <= rate <= hi * (1 + p["part_load_half"])
    for a, b, (x, y) in gp.AGE_HEAT_RATE:
        assert lo <= x < y <= hi


def test_age_is_a_setting_that_narrows_the_draws():
    assert gp.heat_rate_for_age(1) == (6600.0, 7000.0) and gp.heat_rate_for_age(8) == (7200.0, 7500.0)
    young, old = (gp.central_parameters("fuel_cell", "dry", age_years=a)["heat_rate"] for a in (2, 7))
    assert young < gp.central_parameters("fuel_cell", "dry")["heat_rate"] < old
    with pytest.raises(ValueError, match="fuel cells"):
        gp.ranges("cc", "towers", age_years=3)
    with pytest.raises(ValueError):
        gp.heat_rate_for_age(-1)


def test_age_holds_no_state():
    """The same hour gives the same answer wherever it falls in a run: nothing carries from one hour to the next."""
    tdb, twb, rh = _weather()
    p = gp.central_parameters("fuel_cell", "dry", age_years=4)
    whole = gp.hourly(30.0, tdb, twb, rh, "fuel_cell", "dry", p, 100, 0.325)
    tail = gp.hourly(30.0, tdb[100:], twb[100:], rh[100:], "fuel_cell", "dry", p, 100, 0.325)
    for k in ("fuel", "withdrawn", "consumed", "served"):
        assert np.array_equal(whole[k][100:], tail[k])


def test_start_up_water_is_consumed_and_the_balances_close():
    tdb, twb, rh = _weather()
    p = gp.central_parameters("fuel_cell", "dry")
    h = gp.hourly(30.0, tdb, twb, rh, "fuel_cell", "dry", p, 100, 0.325)
    assert np.allclose(h["process"], p["process_water"] * h["served"])
    assert np.allclose(h["withdrawn"], h["consumed"] + h["returned"]) and np.allclose(h["withdrawn"], h["process"])
    assert not h["returned"].any()
    assert np.allclose(h["fuel"], h["served"] + h["aux"] + h["condenser"] + h["other"]) and (h["other"] > 0).all()
    gal_per_mwh = h["withdrawn"].sum() / h["served"].sum()
    assert gp.TECH["fuel_cell"]["process_water"][0] <= gal_per_mwh <= gp.TECH["fuel_cell"]["process_water"][1]


def test_a_modular_plant_carries_a_reserve_share_not_one_spare():
    """920 servers needed at 0.935 availability: 1,017 built, the fewest with fewer than 920 up in under 1 hour in 10,000 (binomial); N + k for
    the large-unit technologies."""
    assert gp.units_for("fuel_cell", 920 * 0.325, 0.325, 0.935) == 1017
    assert gp.units_for("fuel_cell", 920 * 0.325, 0.325, 0.97) == 971
    assert gp.units_for("cc", 600.0, 300.0, 0.935, k=1) == 3
    assert gp.unit_mw("fuel_cell") == 0.325 and gp.unit_mw("cc") == 300.0 and gp.unit_mw("fuel_cell", 1.0) == 1.0
    assert gp.outage_hours("fuel_cell") == 24.0 and gp.outage_hours("ct") == gp.OUTAGE_HOURS


def test_an_islanded_campus_on_fuel_cells_is_sized_by_servers():
    from golden import weather
    from waterledger_models.datacenter import cooling
    times, t, rh = weather()
    t, rh = np.asarray(t, float), np.asarray(rh, float)
    utc = np.array(times, dtype="datetime64[h]") + np.timedelta64(5, "h")
    wx = (utc, np.zeros(len(times)), np.zeros(len(times)), np.full(len(times), 5.0), np.zeros(len(times)))
    model = cooling._CoolingRuns(6, 7, 100.0, cooling.HOUR_BLOCK, cooling.DEFAULT_PLANT, True)
    sized = S.size(model, times, t, rh, {"fc": S.Scenario(residual="none", gas=S.Gas(technology="fuel_cell", design="dry"))}, "hybrid", wx, 42.9, -85.5)
    g = sized["fc"].gas
    assert g.unit_mw == 0.325
    assert 300 < g.units < 700           # a 100 MW campus's 1-in-10-year highest hour, about 110-150 MW, in 325 kW servers with a reserve share
