"""Runoff water quality before and after a campus is built: annual runoff and pollutant loads, the construction years,
road salt, generator fuel, runoff heat and what cooling-water blowdown carries to a sewer plant.

Screening level, for a review or a public estimate, not a calibrated model:
  runoff   Simple Method (Schueler 1987), split by surface: R = P x 0.9 x Rv, with Rv by land cover from the Runoff Reduction technical memo
           (Hirschman, Collins and Schueler 2008, Table 4): 0.95 impervious, 0.20 turf and 0.03 forest on hydrologic soil group B (by soil group later).
           Cropland has no value there: 0.20 [A], as turf, since row crop curve numbers on soil group B (78-81, TR-55) are above lawn's (61-69)
  loads    L (lb/yr) = 0.226 x R (in) x C (mg/L) x A (ac), with event mean concentrations C by surface
  controls Michigan's post-construction standard (treat the first inch or 90% of storms, 80% TSS removal; EGLE MS4 permits,
           Kent County Drain Commissioner rules), applied to the captured share of runoff with wet-pond removal rates;
           infiltration as the stronger option
  sediment before and after is on one basis: what runoff carries, runoff x concentration. Farmland too, including its phosphorus; tile-drain nitrate is
           not counted, so farmland nitrogen here is low. The construction years: bare ground at turf's coefficient [A], at the farmland concentration
           times EPA's 10-20 (construction sites shed 10 to 20 times what farmland does). Gross erosion off bare ground (soil_moved) is a different
           quantity, soil loosened rather than soil carried off, and is reported on its own
PARAMS is the single source of every value; Water Ledger reads it from waters.json and the Water Review reads it here.
"""

from waterledger_models import hydrology

LB = 0.226          # lb per (ac x in x mg/L)
GAL_PER_AC_IN = 27154.0
PJ = 0.9            # share of rain events that produce runoff (Simple Method)

# Event mean concentrations, mg/L: [lo, mid, hi]. Mid is the Michigan source where one exists.
PARAMS = {
    # the impairments a site's runoff can add to, of the groups ATTAINS listings fall in (waterledger_data.waters.ORDER): not bacteria or mercury in fish
    "listed_groups": ["sed", "nut", "temp", "salt", "do", "bio", "flow", "oil", "metal"],
    "units": {"lb_per_ac_in_mg_l": LB, "gal_per_ac_in": GAL_PER_AC_IN, "runoff_event_share": PJ},
    # A single storm by curve number (hydrology.composite_runoff_in), hydrologic soil group B: lawn after, pavement [estimate]
    "curve_numbers": {"pervious_after": hydrology.CN_POST_PERV, "impervious": hydrology.CN_IMP, "sources": ["nrcs_tr55"]},
    # Runoff coefficients by land cover: Runoff Reduction memo Table 4, soil group B. farm [A]: no cropland value there; not below turf (see above)
    "rv": {"imp": 0.95, "turf": 0.20, "farm": 0.20, "woods": 0.03, "sources": ["simple_method", "runoff_reduction2008"]},
    "emc": {
        # Marquette, Michigan source areas (USGS WRIR 97-4242, Table 4, geometric means); TN = TKN + NO2+NO3
        "roof": {"tss": [20, 24, 24], "tp": [0.03, 0.09, 0.09], "tn": [1.5, 2.3, 2.3], "sources": ["usgs_marquette", "mpca_emc"]},
        "paved": {"tss": [75, 138, 201], "tp": [0.2, 0.21, 0.25], "tn": [1.5, 1.8, 2.5], "sources": ["usgs_marquette", "mpca_emc", "nsqd", "stepl"]},
        "turf": {"tss": [11, 21, 70], "tp": [0.15, 0.19, 0.19], "tn": [1.5, 1.5, 1.5], "sources": ["mpca_emc", "stepl"]},
        # Row crops: MPCA recommends no TSS EMC (range 50-160); TP 0.3 (STEPL) to 0.53 (MPCA review median); TN 1.9 (STEPL)
        "farm": {"tss": [50, 100, 160], "tp": [0.3, 0.3, 0.53], "tn": [1.9, 1.9, 1.9], "sources": ["mpca_emc", "stepl"], "assumed": True},
        "woods": {"tss": [26, 72, 140], "tp": [0.03, 0.09, 0.45], "tn": [0.2, 0.2, 0.2], "sources": ["mpca_emc", "stepl"]},
        "built": {"tss": [75, 75, 201], "tp": [0.2, 0.2, 0.25], "tn": [2.0, 2.0, 2.5], "sources": ["mpca_emc", "stepl", "nsqd"]},
    },
    "before_imp": {"farm": 0.02, "woods": 0.01, "built": 0.60},     # [A] impervious share of the land as it is now
    "after": {"imp": 0.50, "imp_range": [0.40, 0.60], "roof_share": 0.40},   # [A] roofs and paving; roofs as a share of that
    # Michigan post-construction standard and removal by practice (share removed). Captured share of annual runoff [A].
    "controls": {
        "captured": [0.75, 0.85, 0.95],
        "pond": {"tss": 0.80, "tp": 0.51, "tn": 0.26, "sources": ["egle_ms4", "kcdc_rules", "bmpdb2020"]},
        "infiltration": {"tss": 0.95, "tp": 0.70, "tn": 0.51, "volume": 0.5, "sources": ["semcog_lid", "kcdc_rules"]},
        "standard": "Treat the first inch of runoff or 90% of runoff-producing storms with at least 80% TSS removal (or 80 mg/L), and hold peak rate and volume to pre-development for storms up to the 2-year, 24-hour event",
    },
    # Construction. emc_tss: farmland's concentration x EPA's ratio of construction to farmland, end for end (50 x 10, 100 x 15, 160 x 20), on bare ground at rv_bare [A].
    # t_per_ac_yr: gross erosion, soil moved off bare ground before any of it is delivered (EPA MM8 Table 8.1, a Wisconsin range of 30-200), not on the same basis as a load.
    "construction": {"emc_tss": [500, 1500, 3200], "rv_bare": 0.20, "t_per_ac_yr": [30, 100, 200], "ratio_to_farm": [10, 15, 20], "years": [1, 2, 3], "sources": ["epa_fact26", "epa_mm8", "mpca_emc"],
                     "permits": "Part 91 soil erosion permit for 1 acre or more, or within 500 ft of a lake or stream; construction storm water permit-by-rule (R 323.2190) with a Notice of Coverage above 5 acres and weekly inspection by a certified operator"},
    # Road salt on parking and drives: lb per 1,000 sq ft per event (MPCA targets; practice is often higher) x events per winter [A]
    "salt": {"lb_per_ksf": [0.75, 1.5, 3.0], "events": [20, 40, 60], "paved_share": 0.60, "chloride_share": 0.607,
             "chronic_mg_l": 150, "sources": ["mpca_salt", "egle_rule57"]},
    # Backup generators: diesel at full load (Cat 3516C, 133.6 gal/h at 2,000 ekW) x hours stored on site [A]
    "fuel": {"gal_per_mwh": 66.8, "hours": [12, 48, 72], "gen_mw_per_it_mw": 1.2, "unit_mw": 2.5, "spcc_gal": 1320,
             "sources": ["cat3516c", "uptime2014", "amazon_mo2026", "wyofile2025", "cfr112"]},
    # Runoff heat: summer runoff from pavement averages about 25 C (77 F) vs a 68 F (20 C) coldwater limit in June-August
    "heat": {"paved_c": 24.9, "forest_c": 21.5, "cold_limit_f": 68, "cold_rise_f": 2, "sources": ["herb2007", "rule75", "stefan2010"]},
    # Cooling-tower blowdown: dissolved solids = makeup x cycles; phosphate inhibitors up to ~6.5 mg/L as P; plant limit 1 mg/L
    "blowdown": {"makeup_tds": {"lake": 170, "ground": 400}, "cycles": [3, 5, 7], "p_mg_l": [0, 3, 6.5], "plant_p_limit": 1.0,
                 "sources": ["epa_wsaw", "jea2024", "rule60", "egle_dc_faq"]},
}


def _w(lst, i):
    return lst[i] if isinstance(lst, list) else lst


def _rv_pervious(cover):
    """Runoff coefficient of a land use's pervious part: built land's is turf."""
    return PARAMS["rv"]["turf" if cover == "built" else cover]


def runoff_in(rain_in, imp, cover="turf"):
    """Annual runoff depth (in) from the whole site, with `cover` ("turf", "farm", "woods" or "built") on what isn't impervious."""
    return rain_in * PJ * (PARAMS["rv"]["imp"] * imp + _rv_pervious(cover) * (1 - imp))


def loads(acres, rain_in, before="farm", imp=None, roof_share=None):
    """Annual runoff (gallons) and loads (TSS tons, TP lb, TN lb) now, after with no controls, after with Michigan's standard
    (wet ponds) and after with infiltration. Each value is [lo, mid, hi]."""
    P, E = PARAMS, PARAMS["emc"]
    imp = P["after"]["imp"] if imp is None else imp
    roof = P["after"]["roof_share"] if roof_share is None else roof_share
    rv = P["rv"]
    r_imp, r_turf, r_before = rain_in * PJ * rv["imp"], rain_in * PJ * rv["turf"], rain_in * PJ * _rv_pervious(before)
    i0 = P["before_imp"][before]
    out = {"runoff_gal": {}, "tss_t": {}, "tp_lb": {}, "tn_lb": {}}
    out["runoff_gal"]["now"] = [acres * (i0 * r_imp + (1 - i0) * r_before) * GAL_PER_AC_IN] * 3
    out["runoff_gal"]["after"] = [acres * (imp * r_imp + (1 - imp) * r_turf) * GAL_PER_AC_IN] * 3
    for k, unit in (("tss", "tss_t"), ("tp", "tp_lb"), ("tn", "tn_lb")):
        div = 2000 if k == "tss" else 1
        now_perv = E[before][k] if before != "built" else E["turf"][k]
        now_imp = E["built"][k]
        now = [LB * acres * (i0 * r_imp * _w(now_imp, i) + (1 - i0) * r_before * _w(now_perv, i)) / div for i in range(3)]
        after = [LB * acres * (imp * r_imp * (roof * E["roof"][k][i] + (1 - roof) * E["paved"][k][i]) + (1 - imp) * r_turf * E["turf"][k][i]) / div for i in range(3)]
        cap = P["controls"]["captured"]
        # lo pairs with the most capture, hi with the least
        pond = [after[i] * (1 - cap[2 - i] * P["controls"]["pond"][k]) for i in range(3)]
        inf = P["controls"]["infiltration"]
        infil = [after[i] * (1 - cap[2 - i] * (1 - (1 - inf["volume"]) * (1 - inf[k]))) for i in range(3)]
        out[unit] = {"now": now, "after": after, "pond": pond, "infiltration": infil}
    vol_inf = P["controls"]["infiltration"]["volume"]
    out["runoff_gal"]["pond"] = out["runoff_gal"]["after"]
    out["runoff_gal"]["infiltration"] = [out["runoff_gal"]["after"][0] * (1 - P["controls"]["captured"][2 - i] * vol_inf) for i in range(3)]
    return out


def construction(acres_disturbed, rain_in):
    """Sediment runoff carries off bare ground in a year of construction, tons, on the same basis as loads(): runoff x concentration, before controls catch part of it."""
    c = PARAMS["construction"]
    return [LB * acres_disturbed * rain_in * PJ * c["rv_bare"] * x / 2000 for x in c["emc_tss"]]


def soil_moved(acres_disturbed):
    """Gross erosion off bare ground in a year of construction, tons: soil loosened, not all of it carried off the site."""
    return [acres_disturbed * x for x in PARAMS["construction"]["t_per_ac_yr"]]


def rain_median(rain_in):
    """The median county's yearly rain (inches), for a state when no place is chosen."""
    v = sorted(rain_in.values())
    n = len(v)
    return v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2


def listed(listings):
    """The listings a site's runoff can add to, from a watershed's [[group, tmdl, waters], ...]."""
    return [x for x in listings or [] if x[0] in PARAMS["listed_groups"]]


def storm_mg(acres, storm_in, imp=None):
    """Runoff from one storm of `storm_in` inches on the finished site, million gallons (curve numbers, not the Simple Method, which is for the year).
    Not routed: a volume, not a peak."""
    imp = PARAMS["after"]["imp"] if imp is None else imp
    return hydrology.composite_runoff_in(storm_in, imp, hydrology.CN_POST_PERV) * acres * GAL_PER_AC_IN / 1e6


def salt(acres, imp=None, events=None):
    """Road salt a winter on parking and drives (tons of salt) and the chloride in it. `events`: [lo, mid, hi] events a winter where a state has
    its own by region (national.climate.salt_events), else Michigan's assumption."""
    S, A = PARAMS["salt"], PARAMS["after"]
    imp = A["imp"] if imp is None else imp
    paved_ksf = acres * imp * (1 - A["roof_share"]) * 43.56
    ev = S["events"] if events is None else events
    t = [paved_ksf * S["lb_per_ksf"][i] * ev[i] / 2000 for i in range(3)]
    return {"salt_t": t, "chloride_t": [x * S["chloride_share"] for x in t], "paved_ac": acres * imp * (1 - A["roof_share"])}


def fuel(it_mw):
    """Backup generators and diesel stored on site."""
    F = PARAMS["fuel"]
    gen_mw = it_mw * F["gen_mw_per_it_mw"]
    return {"gen_mw": gen_mw, "units": round(gen_mw / F["unit_mw"]), "gal": [gen_mw * F["gal_per_mwh"] * h for h in F["hours"]]}


def blowdown(flow_mgd, source="lake"):
    """Dissolved solids (mg/L, lb/day) and phosphorus (lb/day) in cooling-water blowdown sent to a plant."""
    B = PARAMS["blowdown"]
    tds = [B["makeup_tds"][source] * c for c in B["cycles"]]
    return {"tds_mg_l": tds, "tds_lb_day": [t * flow_mgd * 8.34 for t in tds], "p_lb_day": [p * flow_mgd * 8.34 for p in B["p_mg_l"]]}
