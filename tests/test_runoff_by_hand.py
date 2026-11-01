"""Runoff worked by hand, with the numbers written out here, not read from the code's constants, so a wrong constant in the code fails.
A 200-acre site, half of it roofs and paving afterward, in 36 inches of rain a year."""
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


def test_farmland_sediment_is_runoff_times_concentration():
    L = runoff.loads(200, 36)["tss_t"]["now"][1]
    # fields 196 ac x 6.48 in x farm 100 mg/L, paved part 4 ac x 30.78 in x built 113.17 mg/L: at 0.226 lb per ac-in-mg/L and 2,000 lb a ton
    assert L == pytest.approx(0.226 * (196 * 6.48 * 100 + 4 * 30.78 * 113.17) / 2000, rel=1e-3)     # 16.1 tons, 0.08 tons an acre


def test_farmland_phosphorus_is_runoff_times_concentration_alone():
    L = runoff.loads(200, 36)["tp_lb"]["now"][1]
    # 0.533 mg/L on the fields, 0.314 on the paved part: 0.40 x 0.1406 + 0.60 x 0.430. 163 lb: no soil phosphorus on top of the concentration, which already holds it
    assert L == pytest.approx(0.226 * (196 * 6.48 * 0.533 + 4 * 30.78 * 0.3144), rel=1e-3)


def test_construction_on_the_same_basis_as_today_at_epas_ratio():
    c = runoff.construction(200, 36)
    assert c[1] == pytest.approx(0.226 * 200 * 6.48 * 1500 / 2000)                    # 219.7 tons, 1.1 tons an acre
    # EPA Fact Sheet 2.6: construction sheds 10-20 times what farmland does. Farmland alone, no paved part, same acres
    farm = [0.226 * 200 * 6.48 * x / 2000 for x in (50, 100, 160)]
    assert [round(c[i] / farm[i], 6) for i in range(3)] == [10, 15, 20]
    assert runoff.soil_moved(200) == [6000, 20000, 40000]                             # 30, 100 and 200 tons an acre, gross


def test_sediment_water_and_soil_stay_in_proportion_with_rain():
    assert runoff.construction(200, 18)[1] == pytest.approx(runoff.construction(200, 36)[1] / 2)
    assert runoff.loads(200, 18)["tss_t"]["now"][1] == pytest.approx(runoff.loads(200, 36)["tss_t"]["now"][1] / 2)


def test_wet_ponds_remove_the_databases_share_of_the_captured_runoff():
    L = runoff.loads(200, 36)
    # mid capture 85%; removal 80% TSS, 51% TP, 33% TN (CWP 2000, SEMCOG Table 9.5)
    assert L["tss_t"]["pond"][1] == pytest.approx(L["tss_t"]["after"][1] * (1 - 0.85 * 0.80))
    assert L["tp_lb"]["pond"][1] == pytest.approx(L["tp_lb"]["after"][1] * (1 - 0.85 * 0.51))
    assert L["tn_lb"]["pond"][1] == pytest.approx(L["tn_lb"]["after"][1] * (1 - 0.85 * 0.33))


def test_both_stormwater_cases_are_in_the_rows():
    from waterledger.comparisons import before_after
    from waterledger.estimate import Range
    W = Range(p10=1, p50=1, p90=1)
    rows = {r.key: r for r in before_after("wells", "water", W, W, W, W, 200, 36, "farm", 0.5, 300)}
    L = runoff.loads(200, 36, "farm", 0.5)
    assert rows["mud"].controls == "typical_wet_pond" and rows["mud"].after == pytest.approx(L["tss_t"]["pond"][1])
    assert rows["mud_no_controls"].controls == "none" and rows["mud_no_controls"].after == pytest.approx(L["tss_t"]["after"][1])
    assert rows["p"].after == pytest.approx(L["tp_lb"]["pond"][1]) and rows["p_no_controls"].after == pytest.approx(L["tp_lb"]["after"][1])
    assert rows["mud"].today == rows["mud_no_controls"].today == rows["build"].today
    assert rows["soil_moved"].today is None


def test_a_mean_from_a_median_and_cov():
    # lognormal: mean / median = sqrt(1 + COV^2). NSQD commercial TSS: 43 x sqrt(1 + 2.0^2) = 43 x 2.2361
    assert runoff._mean(43, 2.0) == pytest.approx(96.15, abs=0.01)
    E = runoff.PARAMS["emc"]
    assert [round(x, 1) for x in E["paved"]["tss"]] == [96.2, 152.8, 275.8]      # commercial 43, COV 2.0; industrial 81, 1.6; freeways 99, 2.6
    assert [round(x, 3) for x in E["paved"]["tp"]] == [0.344, 0.430, 0.515]      # 0.22, 1.2; 0.25, 1.4; 0.25, 1.8
    assert E["paved"]["tn"][0] == pytest.approx(1.5 * 1.3454 + 0.6 * 1.4866, abs=0.001)    # TKN + NO2+NO3, each a mean: 2.91
    assert E["roof"]["tss"][1] == pytest.approx(53.67, abs=0.01)                 # Marquette 24 at COV 2.0
    assert E["turf"]["tss"][1] == pytest.approx(87.43, abs=0.01)                 # open space 48.5, COV 1.5


def test_the_finished_site_reads_like_a_commercial_or_industrial_outfall():
    # Load-weighted concentration with no controls, checked against NSQD's outfalls, which the surfaces were not fitted to as a whole: between commercial's 96 and industrial's 153
    L = runoff.loads(200, 36)
    c = L["tss_t"]["after"][1] * 2000 / (0.226 * 200 * 18.63)
    assert 96 < c < 153
    # and 0.2-0.3 tons and 1-2 lb of phosphorus an acre a year, the usual range for commercial land
    assert 0.2 < L["tss_t"]["after"][1] / 200 < 0.3 and 1 < L["tp_lb"]["after"][1] / 200 < 2


def test_after_with_means_by_hand():
    L = runoff.loads(200, 36)["tss_t"]["after"][1]
    # 100 ac x 30.78 in x (0.4 x 53.67 + 0.6 x 152.83 = 113.17) + 100 ac x 6.48 in x 87.43
    assert L == pytest.approx(0.226 * (100 * 30.78 * 113.17 + 100 * 6.48 * 87.43) / 2000, rel=1e-3)      # 45.7 tons


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


def _levels(water, rules, lake=None):
    from types import SimpleNamespace as NS

    from waterledger import levels as lv
    ctx = NS(wastewater=NS(plants=[]), receiving=NS(great_lake=lake))
    est = NS(site=NS(place=NS(context=lambda: ctx), source="wells", wastewater="water"), water=water, comparisons=[])
    W = {"register_mgd": 0.1, "zone_c_permit_mgd": 1.0, "permit_mgd": 2.0, "compact_use_mgd": 5.0, "low_mgd": 0.5, "high_mgd": 5.0}
    return lv.site_levels(est, {"withdrawals": W, "state_rules": rules})


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
    st = ensemble._stats(daily.reshape(1, -1), years, months)[0]
    assert st[ensemble.STATS.index("max_90day")] == pytest.approx(2.0)
    assert st[ensemble.STATS.index("max_90day")] <= st[ensemble.STATS.index("peak_1in10")]


def test_neutral_bands_are_not_michigans_lines():
    from waterledger.national.provider import NOT_COVERED, WITHDRAWAL_BANDS
    # 3,300 people x 140 gallons a day = 462,000; 33,000 people x 140 = 4,620,000: about 0.5 and 5 MGD
    assert 3300 * 140 / 1e6 == pytest.approx(0.462) and 33000 * 140 / 1e6 == pytest.approx(4.62)
    assert WITHDRAWAL_BANDS["low_mgd"] == 0.5 and WITHDRAWAL_BANDS["high_mgd"] == 5.0
    assert not {"register_mgd", "zone_c_permit_mgd", "permit_mgd"} & set(WITHDRAWAL_BANDS)
    assert "mcl327" not in WITHDRAWAL_BANDS["sources"] and "state_rules" in NOT_COVERED


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
