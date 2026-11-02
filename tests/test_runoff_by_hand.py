"""Runoff worked by hand, with the numbers written out here, not read from the code's constants, so a wrong constant in the code fails.
A 200-acre site, half of it roofs and paving afterward, in 36 inches of rain a year."""
from pathlib import Path

import pytest

from waterledger_models import hydrology, runoff

R_IMP = 36 * 0.9 * 0.95     # 30.78 in a year off roofs and paving
R_TURF = 36 * 0.9 * 0.20    # 6.48 in off turf
R_WOODS = 36 * 0.9 * 0.03   # 0.972 in off woods


def test_runoff_depths_by_cover():
    assert R_IMP == pytest.approx(30.78) and R_TURF == pytest.approx(6.48) and R_WOODS == pytest.approx(0.972)
    assert runoff.runoff_in(36, 0.5) == pytest.approx(0.5 * 30.78 + 0.5 * 6.48)      # 18.63
    assert runoff.runoff_in(36, 0.02, "farm") == pytest.approx(0.02 * 30.78 + 0.98 * 6.48)     # farmland as turf [A]: 6.966
    assert runoff.runoff_in(36, 0.01, "woods") == pytest.approx(0.01 * 30.78 + 0.99 * 0.972)   # 1.27008
    assert runoff.runoff_in(36, 0.60, "built") == pytest.approx(0.60 * 30.78 + 0.40 * 6.48)    # 21.06


def test_runoff_volume_before_and_after():
    L = runoff.loads(200, 36)["runoff_gal"]
    assert L["after"][1] == pytest.approx(200 * 18.63 * 27154)                   # 101,175,804 gallons
    assert L["now"][1] == pytest.approx(200 * 6.966 * 27154)                     # 37,830,953 gallons
    assert L["after"][1] / L["now"][1] == pytest.approx(18.63 / 6.966)           # 2.67 times, not 7
    w = runoff.loads(200, 36, before="woods")["runoff_gal"]
    assert w["now"][1] == pytest.approx(200 * 1.27008 * 27154)                   # woods shed far less than fields


def test_water_closes_runoff_stays_a_part_of_the_rain():
    for cover in ("turf", "farm", "woods", "built"):
        for imp in (0.0, 0.5, 1.0):
            assert 0 < runoff.runoff_in(36, imp, cover) < 36


def test_row_crops_shed_more_than_lawn_in_a_storm():
    assert hydrology.CN_PRE_PERV == 78 and hydrology.CN_POST_PERV == 65
    s = 1000 / 78 - 10                                                           # 2.8205 in; TR-55
    assert hydrology.scs_runoff_in(5, 78) == pytest.approx((5 - 0.2 * s) ** 2 / (5 + 0.8 * s))
    assert hydrology.scs_runoff_in(5, 78) > hydrology.scs_runoff_in(5, 65)


def test_farmland_phosphorus_and_nitrogen_are_ceaps_loss_per_acre():
    # North Central: (59.6 + 32.1 + 25 + 11) thousand tons x 2,000 lb / 123,296 thousand acres = 2.07 lb; (157 + 196 + 1,025 + 491) -> 30.3 lb. Tables A-1, A-17 to A-20
    assert runoff.nutrient_yield("farm", "tp", "MI")[1] == pytest.approx(2.0716, abs=1e-3)
    assert runoff.nutrient_yield("farm", "tn", "OH")[1] == pytest.approx(30.32, abs=0.01)
    assert runoff.loads(200, 36, state="MI")["tp_lb"]["now"][1] == pytest.approx(200 * 2.0716, abs=0.2)
    # a state with no region assigned takes the national row, not Michigan's
    assert runoff.nutrient_yield("farm", "tn", "DC")[1] == pytest.approx(29.1, abs=0.05)
    # the low is the mean on acres under the thresholds, the high the mean on acres over the dominant pathway's plus the other's mean
    assert runoff.nutrient_yield("farm", "tp", "MI")[0] == pytest.approx(32.1 * 2000 / 109656 + 11 * 2000 / 83232, abs=1e-2)
    assert runoff.nutrient_yield("farm", "tp", "MI")[2] == pytest.approx(59.6 * 2000 / 13640 + 36 * 2000 / 123296, abs=1e-2)
    # nitrogen by water: surface 5.73 of 30.3
    L = runoff.loads(200, 36, state="MI")["tn_lb"]
    assert L["now_surface"][1] == pytest.approx(200 * 353 * 2000 / 123296, abs=0.5)
    assert "now_surface" not in runoff.loads(200, 36, "woods")["tn_lb"]


def test_wet_ponds_treat_the_captured_surface_runoff_down_to_a_floor():
    L = runoff.loads(200, 36)
    # surface at 50% impervious: 0.226 x 200 x 18.63 in x C; below ground the natural yield on 100 pervious acres
    sp, bp = 0.226 * 200 * 18.63 * 0.31, 100 * 0.076
    assert L["tp_lb"]["after"][1] == pytest.approx(sp + bp, abs=0.1)
    assert L["tp_lb"]["pond"][1] == pytest.approx(bp + sp * (1 - 0.85 * 0.52), abs=0.1)      # 0.149 mg/L treated, above the 0.13 floor
    sn, bn = 0.226 * 200 * 18.63 * 2.7, 100 * 0.77
    assert L["tn_lb"]["pond"][1] == pytest.approx(bn + sn * (1 - 0.85 * 0.31), abs=0.5)
    assert L["tss_t"]["pond"][1] == pytest.approx(L["tss_t"]["after"][1] * (1 - 0.85 * 0.80))
    # at the low end the floor holds: 0.20 x (1 - 0.76) = 0.048 mg/L would be below 0.13
    s0, b0 = 0.226 * 200 * 18.63 * 0.20, 100 * 0.043
    assert L["tp_lb"]["pond"][0] == pytest.approx(b0 + s0 * (1 - 0.95 + 0.95 * 0.13 / 0.20), abs=0.1)


def test_infiltration_keeps_runoff_reduction_and_removal_apart_and_its_nitrogen_goes_somewhere():
    L = runoff.loads(200, 36)
    s, b = 0.226 * 200 * 18.63 * 2.7, 100 * 0.77
    # middle: 85% captured, 70% of that soaks in, 15% off the rest
    assert L["tn_lb"]["infiltration"][1] == pytest.approx(b + s * (0.15 + 0.85 * 0.30 * 0.85), abs=0.5)
    assert L["tn_lb"]["to_ground"][1] == pytest.approx(s * 0.85 * 0.70, abs=0.5)
    # what isn't in the stream went to the ground or was treated
    treated = s * 0.85 * 0.30 * 0.15
    assert L["tn_lb"]["after"][1] == pytest.approx(L["tn_lb"]["infiltration"][1] + L["tn_lb"]["to_ground"][1] + treated, abs=0.5)
    assert L["runoff_gal"]["infiltration"][1] == pytest.approx(L["runoff_gal"]["after"][1] * (1 - 0.85 * 0.70))


def test_both_stormwater_cases_are_in_the_rows():
    from waterledger.comparisons import before_after
    from waterledger.estimate import Range
    W = Range(p10=1, p50=1, p90=1)
    rows = {r.key: r for r in before_after("wells", "water", W, W, W, W, 200, 36, "farm", 0.5, 300)}
    L = runoff.loads(200, 36, "farm", 0.5)
    assert rows["mud"].controls == "typical_wet_pond" and rows["mud"].after == pytest.approx(L["tss_t"]["pond"][1])
    assert rows["mud_no_controls"].controls == "none" and rows["mud_no_controls"].after == pytest.approx(L["tss_t"]["after"][1])
    assert rows["p"].after == pytest.approx(L["tp_lb"]["pond"][1]) and rows["p_no_controls"].after == pytest.approx(L["tp_lb"]["after"][1])
    assert rows["n"].after == pytest.approx(L["tn_lb"]["pond"][1]) and rows["n_no_controls"].after == pytest.approx(L["tn_lb"]["after"][1])
    assert rows["n"].today == rows["n_no_controls"].today == pytest.approx(L["tn_lb"]["now"][1]) and rows["n"].unit == "pounds a year"
    assert rows["mud"].today == rows["mud_no_controls"].today == rows["build"].today == rows["build_basin"].today
    assert rows["build"].controls == "none" and rows["build_basin"].controls == "sediment_basin"
    assert rows["soil_moved"].today is None


def test_one_concentration_for_the_whole_site():
    E = runoff.PARAMS["emc"]["developed"]
    assert E["tp"] == [0.20, 0.31, 0.40] and E["tn"] == [1.9, 2.7, 3.1] and E["tss"] == [96, 118, 152]


def test_the_finished_site_sits_among_published_rates():
    # 1-2 lb of phosphorus and about 10-14 lb of nitrogen an acre a year at 36 inches: EPA Region 1 and Hampton Roads run about 1-1.7 and 8-19
    L = runoff.loads(200, 36)
    assert 1 < L["tp_lb"]["after"][1] / 200 < 2 and 8 < L["tn_lb"]["after"][1] / 200 < 19


def test_after_by_hand():
    L = runoff.loads(200, 36)["tss_t"]["after"][1]
    # 200 ac x 18.63 in x 118 mg/L x 0.226 / 2,000
    assert L == pytest.approx(0.226 * 200 * 18.63 * 118 / 2000, rel=1e-3)      # 49.7 tons


def test_a_home_from_usgs_water_and_census_households():
    from waterledger_data import wateruse
    # Two counties: 3 + 1 and 5 + 1 million gallons a day into Vermont's 254,865 households of 2015: 10,000,000 / 254,865
    layer = {"counties": {"a": {"delivered_to_homes_mgd": 3.0, "mgd": {"domestic": 1.0}}, "b": {"delivered_to_homes_mgd": 5.0, "mgd": {"domestic": 1.0}}}}
    assert wateruse.home_gpd("VT", layer) == pytest.approx(39.2364, abs=1e-3)
    assert wateruse.home_gpd("VT", {"counties": {"a": {"mgd": {}}}}) is None     # nothing to say, not zero
    assert len(wateruse.HOUSEHOLDS_2015) == 51                                   # every state and D.C.
    assert wateruse.HOUSEHOLDS_2015["MI"] == 3858532 and wateruse.HOUSEHOLDS_2015["TX"] == 9421412


def test_homes_and_the_water_system_use_the_state_value():
    from waterledger import comparisons as cm
    from waterledger.context import WaterSystem
    from waterledger.estimate import Flow, Range
    assert cm.water_homes(1.73) == pytest.approx(1.73e6 / 300)                   # EPA's family
    assert cm.water_homes(1.73, 173) == pytest.approx(10000)                     # 1,730,000 gallons at 173 a home
    r = Range(p10=1.73, p50=1.73, p90=1.73)
    c = cm.water_system_share(Flow(avg=r, peak_day=r), [WaterSystem(pwsid="x", name="X", population=1, connections=50000, share_of_place=1.0)], 173)
    assert c.percent.avg.p50 == pytest.approx(20)                                # 10,000 homes of 50,000 connections
    assert "173 gallons" in c.basis


def _month_water(month, peak, avg_c=1.0, c90=None):
    from waterledger.estimate import Flow, Range, WaterUse
    r = lambda v: Range(p10=v, p50=v, p90=v)
    f = Flow(avg=r(0.5), peak_day=r(peak))
    return WaterUse(withdrawn=f, withdrawn_annual_mg=r(1), consumed=Flow(avg=r(avg_c), peak_day=r(avg_c)), returned=f, to_sewer=r(0.1), withdrawn_max_month=r(month), consumed_max_90day=r(c90) if c90 else None)


def _levels(water, rules, lake=None, basin=None):
    from types import SimpleNamespace as NS

    from waterledger import levels as lv
    ctx = NS(wastewater=NS(plants=[]), receiving=NS(great_lake=lake, great_lakes_basin=basin))
    est = NS(site=NS(place=NS(context=lambda: ctx), source="wells", wastewater="water"), water=water, comparisons=[])
    W = {"register_mgd": 0.1, "zone_c_permit_mgd": 1.0, "permit_mgd": 2.0, "compact_use_mgd": 5.0, "low_mgd": 0.5, "high_mgd": 5.0}
    return lv.site_levels(est, {"withdrawals": W, "state_rules": rules})


def test_the_compact_follows_the_basin_not_the_shore():
    inland = _levels(_month_water(1.5, 3.0, 6.0), False, basin=True)      # Akron: not on a lake, in the basin
    assert inland["great_lakes"] == "large" and inland["great_lakes_where"] == "basin"
    assert _levels(_month_water(1.5, 3.0, 1.0), False, lake="Lake Erie", basin=True)["great_lakes_where"] == "shore"
    assert "great_lakes" not in _levels(_month_water(1.5, 3.0, 6.0), False, basin=False)     # Columbus


def test_part_327_is_tested_on_the_highest_month_with_the_peak_beside_it():
    # 1.5 MGD in the highest month is under the 2 MGD permit line; a 3 MGD peak day alone is over it
    x = _levels(_month_water(1.5, 3.0), True)
    assert x["withdrawal_line"] == "zone_c" and x["withdrawal_period"] == "highest_month" and x["withdrawal_line_peak_day"] == "permit"


def test_the_compact_is_tested_on_the_highest_90_days():
    # 4 MGD on average, 6 MGD over the highest 90 days: over the Compact's 5
    assert _levels(_month_water(1, 1, 4.0, 6.0), True, "Michigan")["great_lakes"] == "large"
    x = _levels(_month_water(1, 1, 4.0), True, "Michigan")       # no 90-day figure in data from before model 1.7
    assert x["great_lakes"] == "small" and x["great_lakes_period"] == "average"


def test_90_day_stat_by_hand():
    import numpy as np

    from waterledger_models.datacenter import cooling, ensemble
    # 200 days at 1 MGD, with 30 days at 4 MGD: the best 30 days average 4, the best 90 (30 x 4 + 60 x 1) / 90 = 2
    daily = np.ones(200)
    daily[50:80] = 4.0
    years = np.array(["2020"] * 200)
    months = np.array([f"2020-{i // 30 + 1:02d}" for i in range(200)])
    out = cooling.daily_stats(np.arange(200), 200, years, daily * 1e6, np.ones(200), months)
    assert out["max_90day"] == pytest.approx(2.0)
    d = daily.reshape(1, -1)
    st = ensemble._stats(d, d, years, months)[0]
    assert st[ensemble.STATS.index("max_90day")] == pytest.approx(2.0)
    assert st[ensemble.STATS.index("max_90day")] <= st[ensemble.STATS.index("peak_1in10")]


def test_no_invented_lines_where_rules_arent_reviewed():
    from waterledger.levels import PUBLIC_SUPPLY_GPCD, people_supplied
    from waterledger.national.provider import NOT_COVERED, WITHDRAWALS
    assert PUBLIC_SUPPLY_GPCD == pytest.approx(137.81, abs=0.01)                 # 39,000 million gallons a day / 283 million people
    assert people_supplied(1.3781) == pytest.approx(10000, abs=1)                # 1,378,100 gallons at 137.81
    assert set(WITHDRAWALS) == {"compact_use_mgd"} and "state_rules" in NOT_COVERED
    x = _levels(_month_water(1.5, 3.0), False)
    assert "withdrawal" not in x and "withdrawal_line" not in x and "withdrawal_flag" not in x
    assert x["withdrawal_mgd"] == 0.5 and x["withdrawal_peak_day_mgd"] == 3.0 and x["withdrawal_people_peak_day"] == pytest.approx(3e6 / 137.81, rel=1e-3)     # 21,769 people
    assert "not yet reviewed" in x["withdrawal_note"]


def test_flags_when_an_estimate_exceeds_a_permit_line():
    # 2.5 in the highest month and 3 on the peak day: over 2 on both
    x = _levels(_month_water(2.5, 3.0), True)
    assert x["withdrawal_flag"] == "permit" and x["withdrawal_flag_peak_day"] == "permit" and "2 million gallons" in x["withdrawal_flag_note"]
    # 0.5 in the highest month, 3 on the peak day: no flag on the rule's period, a flag on the peak day
    x = _levels(_month_water(0.5, 3.0), True)
    assert x["withdrawal_flag"] is None and x["withdrawal_flag_peak_day"] == "permit" and x["withdrawal_line"] == "register"
    x = _levels(_month_water(0.5, 0.9), True)                                     # under every permit line: no flag, no note
    assert x["withdrawal_flag"] is None and x["withdrawal_flag_peak_day"] is None and "withdrawal_flag_note" not in x


@pytest.mark.parametrize("name", ["Gaines charter township, MI", "Jerome Township, OH"])
def test_no_level_or_limit_changes_any_estimated_value(name, monkeypatch):
    import waterledger as wl
    from waterledger import levels as lv
    site = lambda: wl.Site(place=wl.place(name), facility=wl.DataCenter(it_mw=300, cooling="towers"), source="wells")
    numbers = lambda e: e.model_dump(exclude={"levels"})
    base = site().estimate()
    real = lv.site_levels
    seen = []
    # every line and band pushed to one extreme and then the other, reviewed or not. site_levels is what reads them
    for line in (0.0, 1e9):
        lines = {"register_mgd": line, "zone_c_permit_mgd": line, "permit_mgd": line, "compact_use_mgd": line or 1e-6}
        for rules in (True, False):
            monkeypatch.setattr(lv, "site_levels", lambda e, ref, lines=lines, rules=rules: seen.append(real(e, {**ref, "withdrawals": lines, "state_rules": rules})) or seen[-1])
            monkeypatch.setattr(lv, "LEVELS", {**lv.LEVELS, "water_system_pct": [line, line], "sewer_spare_pct": [line, line]})
            assert numbers(site().estimate()) == numbers(base)
    assert seen[0]["withdrawal_line"] == "permit" and seen[2]["withdrawal_line"] == "below" and "withdrawal_line" not in seen[1]      # the lines did reach the levels


def test_salt_events_one_method():
    # Grand Rapids' 72 days a winter x 0.6 = 43.2 events, +/-50%; 1 day: no salt season
    assert runoff.salt_events(72) == pytest.approx([21.6, 43.2, 64.8])
    assert runoff.salt_events(2) == pytest.approx([0.6, 1.2, 1.8]) and runoff.salt_events(1) == [0, 0, 0]


def test_salt_tons_by_hand():
    # 200 ac x 0.5 x 0.6 paved = 60 ac = 2,613.6 thousand sq ft; x 1.5 lb x 40 events / 2,000 lb a ton = 78.408 tons
    s = runoff.salt(200, 0.5, [20, 40, 60])
    assert s["salt_t"][1] == pytest.approx(78.408) and s["chloride_t"][1] == pytest.approx(78.408 * 0.607)


def test_michigan_salt_by_its_own_winters():
    import waterledger as wl
    from waterledger import states
    p = wl.place("Gaines charter township, MI")          # West Michigan, Grand Rapids' 72 days
    assert states.provider("MI").reference(p)["salt_events"] == pytest.approx([21.6, 43.2, 64.8])


def test_incorporated_places_count_as_built():
    from waterledger.place import Place
    make = lambda kind, level=None: Place(geoid="1", name="x", kind=kind, level=level, state="OH", lat=0, lon=0)
    assert make("city", "place").incorporated and make("village", "place").incorporated and make("town", "place").incorporated
    assert not make("cdp", "place").incorporated and not make("township", "township").incorporated and not make("county", "county").incorporated
    assert not make("town", "township").incorporated       # New England's towns are county subdivisions
    assert make("village").incorporated and not make("charter township").incorporated      # data without a level


def test_one_land_default_for_every_state():
    import waterledger as wl
    from waterledger.scenario import land_default
    assert land_default(True) == (50, "built") and land_default(False) == (200, "farm")
    for name in ("comparisons", "national/provider"):      # no copy of its own, and no test on a kind that leaves out villages and towns
        src = (Path(wl.__file__).parent / f"{name}.py").read_text()
        assert "land_default(" in src and "place.kind)" not in src and "50 if city" not in src


def test_farmland_sediment_is_a_yield_by_state():
    # NRI 2022: Michigan's cropland 1.62 tons an acre gross x delivery 0.33 = 0.5346; Ohio 2.16, 0.7128; Virginia 2.38, 0.7854; Texas 1.99, 0.6567
    for st, y in (("MI", 0.5346), ("OH", 0.7128), ("VA", 0.7854), ("TX", 0.6567)):
        assert runoff.sediment_yield("farm", st)[1] == pytest.approx(y)
    # the range: Michigan's median 0.58 x 0.2, mean 1.62 x 0.33, cultivated mean 1.88 x 0.5
    assert runoff.sediment_yield("farm", "MI") == pytest.approx([0.116, 0.5346, 0.94])
    assert runoff.sediment_yield("farm", "DC") == runoff.sediment_yield("farm") == pytest.approx([1.26 * 0.2, 2.67 * 0.33, 3.01 * 0.5])    # the national row, not Michigan's
    # 196 acres of field x 0.5346 = 104.78 tons, plus the paved part: 4 ac x 30.78 in x 118 mg/L x 0.226 / 2,000 = 1.64 tons
    assert runoff.loads(200, 36, state="MI")["tss_t"]["now"][1] == pytest.approx(196 * 0.5346 + 0.226 * 4 * 30.78 * 118 / 2000, rel=1e-3)


def test_woods_are_a_yield_and_built_land_a_concentration():
    assert runoff.sediment_yield("woods") == pytest.approx([0.002, 0.033, 0.5])     # 0.01 x 0.2, 0.1 x 0.33, 1.0 x 0.5
    assert runoff.loads(200, 36, "woods")["tss_t"]["now"][1] == pytest.approx(198 * 0.033 + 0.226 * 2 * 30.78 * 118 / 2000, rel=1e-3)
    # built: the whole site at 118 mg/L
    assert runoff.loads(200, 36, "built")["tss_t"]["now"][1] == pytest.approx(0.226 * (120 * 30.78 + 80 * 6.48) * 118 / 2000, rel=1e-3)
    # natural land: Clark's basins, and no pavement term of its own
    assert runoff.loads(200, 36, "woods")["tp_lb"]["now"] == pytest.approx([8.6, 15.2, 21.4]) and runoff.loads(200, 36, "woods")["tn_lb"]["now"][1] == pytest.approx(154)


def test_construction_is_gross_erosion_times_delivery():
    assert runoff.construction(200) == pytest.approx([600, 4000, 13200])            # 30 x 0.1, 100 x 0.2 and 200 x 0.33 tons an acre x 200 acres: 3, 20 and 66
    assert runoff.soil_moved(200) == [6000, 20000, 40000]
    # the middle basin removes 70%; the low end takes the most removal, 94%, and the high end the least, 42%
    assert runoff.construction_with_basin(200) == pytest.approx([600 * 0.06, 4000 * 0.30, 13200 * 0.58])


def test_construction_against_readable_measurements():
    mid = runoff.construction(1)[1]
    # Helsel 1985: 9,580-15,700 tons a square mile a year = 15.0-24.5 tons an acre. Lee and Ziegler 2010 without controls, historic: 2,300-140,000 = 3.6-219
    assert 9580 / 640 <= mid <= 15700 / 640
    assert runoff.construction(1) == pytest.approx([3, 20, 66]) and 66 < 140000 / 640        # the low end, 3, is just under the historic 3.6
    # EPA's 10-20 times farmland: on today's rates this is above it, stated in the methods log. Michigan 20 / 0.5346 = 37; national 20 / 0.8811 = 23
    assert mid / runoff.sediment_yield("farm", "MI")[1] == pytest.approx(37.41, abs=0.01) and mid / runoff.sediment_yield("farm")[1] == pytest.approx(22.70, abs=0.01)


def test_no_construction_concentration_is_left():
    assert not {"emc_tss", "rv_bare", "ratio_to_farm"} & set(runoff.PARAMS["construction"])
