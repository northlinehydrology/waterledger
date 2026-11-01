"""Power plant water by hand: classification by water body, fresh and saline withdrawal, and coal and nuclear options in every state (model 1.7)."""
import csv
import os

import pytest

from waterledger import comparisons as cm
from waterledger.estimate import Range
from waterledger_data import energy as en

POWER_WATER = os.path.join(os.path.dirname(__file__), "..", "docs", "methods", "power_water")


def _rows(name):
    return list(csv.DictReader(open(os.path.join(POWER_WATER, name))))


def _plant(code):
    return next(r for r in _rows("flagged_plants_2024.csv") if int(r["Plant Code"]) == code)


def test_north_anna_is_a_reservoir_and_surry_stays_once_through():
    """Macknick nuclear medians x 2024 generation. North Anna, 16,023,784 MWh at the pond medians: 7,050 gal/MWh is 112,967.7 Mgal withdrawn, not its
    reported 871,586; 610 gal/MWh is 9,774.5 Mgal consumed. Surry draws from the brackish James River: its 587,686.8 Mgal stands, all of it saline."""
    na, su = _plant(6168), _plant(3806)
    assert na["cool"] == "pond" and float(na["wd_adj"]) == pytest.approx(112967.7, abs=0.1) and float(na["cons_adj"]) == pytest.approx(9774.5, abs=0.1)
    assert float(na["wd_saline_adj"]) == 0
    assert su["cool"] == "once" and float(su["wd_adj"]) == pytest.approx(587686.8) and float(su["wd_saline_adj"]) == pytest.approx(587686.8)
    assert float(su["cons_adj"]) == pytest.approx(12921543 * 269 / 1e6, abs=0.01)


def test_the_pond_median_holds_up_against_the_heat_a_reactor_rejects():
    """North Anna's 610 gal/MWh against the energy balance, not against Macknick: at 33% efficiency a reactor rejects 2.03 MWh of heat per MWh sent out, 7.3 GJ.
    If a cooling lake evaporates away three quarters of it, at 2.45 MJ/kg, that is 2,240 kg, or 591 gallons. The once-through median, 269, would leave most of the heat unaccounted for."""
    heat_j = (1 / 0.33 - 1) * 3.6e9
    assert heat_j == pytest.approx(7.31e9, rel=0.01)
    gallons = 0.75 * heat_j / 2.45e6 / 3.78541
    assert gallons == pytest.approx(591, abs=2) and 560 <= gallons <= 720       # Macknick's nuclear pond range


def test_virginias_state_figure_by_hand():
    """North Anna 112,968 + Surry 587,687 + Chesterfield 59,530 + the other plants 9,241 = 769,426 Mgal; over 102,698,615 MWh, 7,492 gal/MWh or 28.36 L/kWh."""
    va = next(r for r in csv.DictReader(open(en.STATE_TABLE)) if r["state"] == "VA")
    assert float(va["withdrawn_state_l_per_kwh"]) == pytest.approx(769426e6 / 102698615 * 3.78541 / 1000, abs=0.02)


def test_michigan_and_ohio_have_no_built_reservoir_but_texas_does():
    w = _rows("cooling_water_bodies.csv")
    built = {s: {r["plant"] for r in w if r["state"] == s and r["class"] == "reservoir"} for s in ("MI", "OH", "VA", "TX")}
    assert built["MI"] == set() and built["OH"] == set() and built["VA"] == {"North Anna"}
    assert {"W A Parish", "Sim Gideon", "Lost Pines 1 Power Project", "Knox Lee", "Mountain Creek"} <= built["TX"]
    for r in w:     # a saline source can't be a built cooling lake
        assert not (r["class"] == "reservoir" and r["salinity"] == "saline")


def test_fresh_and_saline_add_to_withdrawn_in_every_state():
    for r in csv.DictReader(open(en.STATE_TABLE)):
        if not r["withdrawn_l_per_kwh"]:
            continue
        w = en.state_power_water(r["state"])
        assert w is None or w["withdrawn_fresh"] + w["withdrawn_saline"] == pytest.approx(w["withdrawn"], abs=0.002)
        assert w is None or (w["withdrawn_fresh"] >= 0 and w["withdrawn_saline"] >= 0)
    assert en.state_power_water("MI")["withdrawn_saline"] == 0


def test_withdrawal_split_keeps_whole_gallons_that_add_up():
    assert en.withdrawal_split(8148, 4989.6) == {"wd_fresh_gal_mwh": 3158, "wd_saline_gal_mwh": 4990}
    assert en.withdrawal_split(100, 0) == {"wd_fresh_gal_mwh": 100, "wd_saline_gal_mwh": 0}


def test_michigan_nuclear_by_hand():
    """Cook 18,025 GWh once-through, Fermi 8,256 GWh towers: 68.59% and 31.41%. 0.6859 x 269 + 0.3141 x 672 = 396; 0.6859 x 44,350 + 0.3141 x 1,101 = 30,766.
    Ends: 0.6859 x 100 + 0.3141 x 581 = 251; 0.6859 x 400 + 0.3141 x 845 = 540."""
    n = en.fuel_options("MI", "Michigan")["nuclear"]
    assert n["gal_mwh"] == 396 and n["wd_gal_mwh"] == pytest.approx(30766, abs=3)
    assert (n["lo"], n["hi"]) == (251, 540) and n["label"] == "Michigan's nuclear plants"


def test_coal_all_once_through_takes_the_median_itself():
    c = en.fuel_options("MI", "Michigan")["coal"]
    assert (c["gal_mwh"], c["lo"], c["hi"], c["wd_gal_mwh"], c["wd_lo"], c["wd_hi"]) == (250, 100, 317, 36350, 20000, 50000)
    assert c["wd_saline_gal_mwh"] == 0


def test_virginia_nuclear_by_hand():
    """Surry 44.64% once-through, North Anna 55.36% reservoir. 0.4464 x 269 + 0.5536 x 610 = 458; 0.4464 x 44,350 + 0.5536 x 7,050 = 23,701;
    Surry's 19,798 of that is brackish, so 19,798 gal/MWh saline and 3,903 fresh."""
    n = en.fuel_options("VA", "Virginia")["nuclear"]
    assert n["gal_mwh"] == 458 and n["wd_gal_mwh"] == pytest.approx(23701, abs=2)
    assert n["wd_saline_gal_mwh"] == pytest.approx(19798, abs=3) and n["wd_fresh_gal_mwh"] + n["wd_saline_gal_mwh"] == n["wd_gal_mwh"]


def test_texas_nuclear_is_both_reservoirs():
    n = en.fuel_options("TX", "Texas")["nuclear"]
    assert (n["gal_mwh"], n["lo"], n["hi"], n["wd_gal_mwh"], n["wd_lo"], n["wd_hi"]) == (610, 560, 720, 7050, 500, 13000)


def test_ohio_nuclear_is_both_towers():
    n = en.fuel_options("OH", "Ohio")["nuclear"]
    assert (n["gal_mwh"], n["wd_gal_mwh"]) == (672, 1101)


@pytest.mark.parametrize("state,name", [("MI", "Michigan"), ("OH", "Ohio"), ("VA", "Virginia"), ("TX", "Texas")])
def test_thirstiest_power_works_alike(state, name):
    """Same options, same answer: nuclear uses more than coal or new gas in all four. New gas is 205."""
    o = {"mix": {"label": "x", "gal_mwh": 300}, "new_gas": dict(en.NEW_GAS), **en.fuel_options(state, name), "renew": en.wind_solar(0.5)}
    assert cm.thirstiest_power(o, "mix") == "nuclear"


def test_a_state_without_coal_gets_no_coal_option():
    assert "coal" not in en.fuel_options("VT", "Vermont") and "nuclear" not in en.fuel_options("VT", "Vermont")


def test_notes_name_no_plant_or_state_but_their_own():
    assert "Michigan" not in en.NEW_GAS["note"]
    for state, name in (("MI", "Michigan"), ("VA", "Virginia"), ("TX", "Texas")):
        for o in en.fuel_options(state, name).values():
            for word in ("Cook", "Fermi", "Anna", "Surry", "Lake Michigan", "James River"):
                assert word not in o["note"]


def test_solar_weight_is_the_states_own_then_the_countrys():
    """Alaska and Puerto Rico have no plant figure but do have generation. A state with no row takes the U.S. share, worked here over the table: never Michigan's 0.1589."""
    assert en.pv_share("AK") == 0.0593 and en.pv_share("PR") == 0.6293 and en.pv_share("OH") == 0.5865
    rows = list(csv.DictReader(open(en.STATE_TABLE)))
    solar = sum(float(r["solar_share"]) * float(r["net_gen_mwh"]) for r in rows)
    wind = sum(float(r["wind_share"]) * float(r["net_gen_mwh"]) for r in rows)
    assert en.pv_share("ZZ") == pytest.approx(solar / (solar + wind)) and 0.25 < en.pv_share("ZZ") < 0.4


def test_plant_waters_split_at_a_campus():
    """100 MW for a day is 2,400 MWh; over 0.95, 2,526.3 MWh generated. At 400 and 600 gal/MWh, 1.0105 and 1.5158 MGD, adding to 1,000 gal/MWh's 2.5263."""
    class E:
        avg_mw = Range(p10=100, p50=100, p90=100)
    o = {"a": {"label": "a", "gal_mwh": 10, "lo": 10, "hi": 10, "wd_gal_mwh": 1000, "wd_lo": 1000, "wd_hi": 1000, "wd_fresh_gal_mwh": 400, "wd_saline_gal_mwh": 600, "sources": []},
         "b": {"label": "b", "gal_mwh": 10, "lo": 10, "hi": 10, "wd_gal_mwh": 1000, "wd_lo": 1000, "wd_hi": 1000, "sources": []}}
    w = cm.plant_waters(E, o)
    assert w["a"].withdrawn_fresh == pytest.approx(1.0105, abs=1e-4) and w["a"].withdrawn_saline == pytest.approx(1.5158, abs=1e-4)
    assert w["a"].withdrawn_fresh + w["a"].withdrawn_saline == pytest.approx(w["a"].withdrawn.p50) and w["a"].withdrawn.p50 == pytest.approx(2.5263, abs=1e-4)
    assert w["b"].withdrawn_fresh is None and w["b"].withdrawn_saline is None


def test_michigan_utilities_carry_a_balancing_authority():
    from waterledger.states.mi.provider import balancing_authority as ba
    assert ba("DTE Electric Company") == "MISO" and ba("Consumers Energy Company") == "MISO"
    for n in ("Indiana Michigan Power Company", "City of Niles", "City of Sturgis", "Midwest Energy Cooperative"):
        assert ba(n) == "PJM"
    assert en.grid_water()["MISO"]["consumed_excl_hydro"] == 1.5699
