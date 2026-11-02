"""Runoff water quality before and after a campus is built: annual runoff and pollutant loads, the construction years,
road salt, generator fuel, runoff heat and what cooling-water blowdown carries to a sewer plant.

Screening level, for a review or a public estimate, not a calibrated model:
  runoff   Simple Method (Schueler 1987), split by surface: R = P x 0.9 x Rv, with Rv by land cover from the Runoff Reduction technical memo
           (Hirschman, Collins and Schueler 2008, Table 4): 0.95 impervious, 0.20 turf and 0.03 forest on hydrologic soil group B (by soil group later).
           Cropland has no value there: 0.20 [A], as turf, since row crop curve numbers on soil group B (78-81, TR-55) are above lawn's (61-69)
  loads    L (lb/yr) = 0.226 x R (in) x C (mg/L) x A (ac), with mean concentrations C by surface
  controls two cases, everywhere: no controls, and typical wet pond performance on the captured share of runoff (removal from the Center for Watershed
           Protection's national database, 2000, as printed in SEMCOG 2008 Table 9.5). 80% TSS is what wet ponds typically do, in any state, and also the
           level Michigan's post-construction standard asks for (EGLE MS4 permits, Kent County Drain Commissioner rules). Infiltration is the stronger option
  sediment two bases, on purpose. Today on soil and the construction years are yields, tons an acre a year, because runoff x concentration doesn't capture soil scoured off the
           ground: gross erosion x a delivery ratio [A]. The finished site is runoff x concentration, because roofs, paving and established lawn aren't scouring.
           Screening estimates: a study with site soils, slopes and sediment modeling would do better. Farmland phosphorus stays runoff x concentration, which holds its particulate part;
           tile-drain nitrate is not counted, so farmland nitrogen here is low
PARAMS is the single source of every value; Water Ledger reads it from waters.json and the Water Review reads it here.
"""

from waterledger_models import hydrology

LB = 0.226          # lb per (ac x in x mg/L)
GAL_PER_AC_IN = 27154.0
PJ = 0.9            # share of rain events that produce runoff (Simple Method)

# Loads need the mean concentration, not the geometric mean or median: for a lognormal, mean = median x sqrt(1 + COV^2).
def _mean(median, cov):
    return median * (1 + cov * cov) ** 0.5


# NSQD v1.1 (Maestre and Pitt 2005), Table 3: [median, COV] at outfalls, across U.S. municipalities. TN is TKN + NO2+NO3, each its own mean.
_NSQD = {"commercial": {"tss": (43, 2.0), "tp": (0.22, 1.2), "tkn": (1.5, 0.9), "no": (0.6, 1.1)},
         "industrial": {"tss": (81, 1.6), "tp": (0.25, 1.4), "tkn": (1.4, 1.1), "no": (0.69, 0.92)},
         "freeways": {"tss": (99, 2.6), "tp": (0.25, 1.8), "tkn": (2.0, 1.4), "no": (0.28, 1.2)},
         # Open space's TP COV (3.5, on 68 events) reflects a few extreme values, so mixed open space's 1.1 is used with open space's median [A]
         "open_space": {"tss": (48.5, 1.5), "tp": (0.31, 1.1), "tkn": (0.74, 0.9), "no": (0.59, 0.9)},
         "mixed_open": {"tss": (78, 1.6), "tp": (0.25, 1.1), "tkn": (1.1, 0.9), "no": (0.7, 0.8)}}


def _nsqd(use, k):
    u = _NSQD[use]
    return _mean(*u[k]) if k != "tn" else _mean(*u["tkn"]) + _mean(*u["no"])


def _nsqd3(k, uses):
    return [_nsqd(u, k) for u in uses]


# Event mean concentrations, mg/L: [lo, mid, hi], means. A national source where one has the surface (NSQD); the choices are in the methods log.
# NSQD has outfalls, not surfaces: pavement takes commercial, industrial and freeway outfalls as its range. Marquette's parking lots (USGS WRIR 97-4242 Table 4: 110 clean,
# 138 with data the authors mark unreliable, geometric means) and MPCA's commercial 75 are not used; Marquette's clean figure as a mean, about 208, falls inside the range.
# Roofs have no national source: Marquette's commercial roofs (geometric means 24, 0.09, TKN 1.7 + NO 0.57) as means at NSQD commercial's COVs, MPCA's values as the low end.
# Turf: MPCA open space low, NSQD open space mid, mixed open space high. Marquette's lawns (TSS 262, TP 2.33) and Madison's (TP 2.67) are not used: a few fertilized lawns, source-area samples.
ROOF_MEAN = {"tss": _mean(24, 2.0), "tp": _mean(0.09, 1.2), "tn": _mean(1.7, 0.9) + _mean(0.57, 1.1)}
_PAVED, _ROOF_SHARE = ("commercial", "industrial", "freeways"), 0.40
_EMC = {
    "roof": {"tss": [20, ROOF_MEAN["tss"], ROOF_MEAN["tss"]], "tp": [0.03, ROOF_MEAN["tp"], ROOF_MEAN["tp"]], "tn": [1.5, ROOF_MEAN["tn"], ROOF_MEAN["tn"]], "sources": ["usgs_marquette", "mpca_emc", "nsqd11"]},
    "paved": {k: _nsqd3(k, _PAVED) for k in ("tss", "tp", "tn")} | {"sources": ["nsqd11"]},
    "turf": {"tss": [21, _nsqd("open_space", "tss"), _nsqd("mixed_open", "tss")], "tp": [0.19, _nsqd("open_space", "tp"), _mean(0.31, 3.5)], "tn": [1.5, _nsqd("open_space", "tn"), _nsqd("mixed_open", "tn")], "sources": ["mpca_emc", "stepl", "nsqd11"]},
    # Row crops have no national mean: MPCA recommends no TSS EMC (range 50-160, its middle 100 [A]). TP: MPCA's review median 0.533 mid, as a mean at COV 1 high [A], STEPL's 0.3 low. TN 1.9 (STEPL)
    "farm": {"tss": [50, 100, 160], "tp": [0.3, 0.533, _mean(0.533, 1.0)], "tn": [1.9, 1.9, 1.9], "sources": ["mpca_emc", "stepl"], "assumed": True},
    "woods": {"tss": [26, 72, 140], "tp": [0.03, 0.09, 0.45], "tn": [0.2, 0.2, 0.2], "sources": ["mpca_emc", "stepl"]},
}
# Land already built: its roofs and paving as the campus's are, at the campus's roof share
_EMC["built"] = {k: [_ROOF_SHARE * _EMC["roof"][k][i] + (1 - _ROOF_SHARE) * _EMC["paved"][k][i] for i in range(3)] for k in ("tss", "tp", "tn")} | {"sources": ["nsqd11", "usgs_marquette"]}

# Sheet and rill erosion on cropland, tons an acre a year, 2022: [total cropland's median, total cropland's mean, cultivated cropland's mean].
# USDA NRCS, 2022 National Resources Inventory Summary Report, Table 15. A state not there (Alaska, D.C.) takes the national row.
CROPLAND_EROSION_US = [1.26, 2.67, 3.01]
CROPLAND_EROSION = {
    "AL": [0.89, 3.23, 4.14], "AR": [2.73, 3.04, 3.17], "AZ": [0.19, 0.36, 0.42], "CA": [0.1, 0.38, 0.41], "CO": [1.25, 1.7, 1.97], "CT": [0.98, 3.45,
    6.64], "DE": [0.76, 1.52, 1.54], "FL": [0.09, 1.09, 1.49], "GA": [3.46, 4.52, 5.37], "HI": [1.11, 2.14, 2.23], "IA": [2.76, 5.65, 5.88], "ID":
    [1.18, 2.19, 2.56], "IL": [2.18, 4.24, 4.29], "IN": [1.32, 2.72, 2.81], "KS": [1.51, 2.1, 2.19], "KY": [1.52, 3.44, 4.27], "LA": [1.68, 2.18,
    2.29], "MA": [0.04, 0.59, 2.77], "MD": [1.21, 3.52, 3.96], "ME": [0.42, 1.21, 2.34], "MI": [0.58, 1.62, 1.88], "MN": [0.82, 1.88, 2.04], "MO":
    [2.5, 4.95, 6.21], "MS": [3.09, 4.24, 4.52], "MT": [0.42, 0.73, 0.87], "NC": [1.97, 3.19, 3.54], "ND": [0.57, 0.87, 0.92], "NE": [1.22, 2.94,
    3.09], "NH": [0.14, 0.61, 2.04], "NJ": [1.3, 2.45, 3.25], "NM": [0.34, 0.56, 0.7], "NV": [0.02, 0.06, 0.1], "NY": [0.6, 2.05, 3.34], "OH": [1.14,
    2.16, 2.3], "OK": [1.9, 2.59, 2.78], "OR": [0.6, 1.29, 1.64], "PA": [1.65, 3.19, 4.3], "RI": [0.94, 0.96, 1.67], "SC": [1.43, 2.12, 2.45], "SD":
    [0.76, 1.4, 1.59], "TN": [1.84, 3.92, 5.21], "TX": [1.5, 1.99, 2.11], "UT": [0.18, 0.63, 1.18], "VA": [1.1, 2.38, 3.56], "VT": [0.21, 1.47, 4.33],
    "WA": [1.78, 4.11, 4.84], "WI": [2.08, 4.69, 5.25], "WV": [0.29, 0.86, 2.5], "WY": [0.12, 0.44, 1.02]}

PARAMS = {
    # the impairments a site's runoff can add to, of the groups ATTAINS listings fall in (waterledger_data.waters.ORDER): not bacteria or mercury in fish
    "listed_groups": ["sed", "nut", "temp", "salt", "do", "bio", "flow", "oil", "metal"],
    "units": {"lb_per_ac_in_mg_l": LB, "gal_per_ac_in": GAL_PER_AC_IN, "runoff_event_share": PJ},
    # A single storm by curve number (hydrology.composite_runoff_in), hydrologic soil group B: lawn after, pavement [estimate]
    "curve_numbers": {"pervious_after": hydrology.CN_POST_PERV, "impervious": hydrology.CN_IMP, "sources": ["nrcs_tr55"]},
    # Runoff coefficients by land cover: Runoff Reduction memo Table 4, soil group B. farm [A]: no cropland value there; not below turf (see above)
    "rv": {"imp": 0.95, "turf": 0.20, "farm": 0.20, "woods": 0.03, "sources": ["simple_method", "runoff_reduction2008"]},
    "emc": _EMC,
    # Yields today, a screening estimate: gross erosion x delivery. Delivery [A]: about a third leaves a site of a few hundred acres, the rest settling at field edges and in swales, as in published
    # area relations (0.33 at half a square mile, Stewart et al. 1978, read only in excerpt); an agricultural figure of 25% +/-15% is reported there too. Woods: EPA MM8 Table 8.1's natural range, 0.01-1.0, its geometric middle 0.1 [A].
    "sediment_yield": {"delivery": [0.2, 0.33, 0.5], "farm_gross": {"national": CROPLAND_EROSION_US, "by_state": CROPLAND_EROSION}, "woods_gross": [0.01, 0.1, 1.0], "sources": ["nri2022", "epa_mm8"]},
    "before_imp": {"farm": 0.02, "woods": 0.01, "built": 0.60},     # [A] impervious share of the land as it is now
    "after": {"imp": 0.50, "imp_range": [0.40, 0.60], "roof_share": _ROOF_SHARE},   # [A] roofs and paving; roofs as a share of that
    # Removal by practice (share removed): the national database's medians, SEMCOG Table 9.5. Captured share of annual runoff [A]. "standard" is Michigan's rule, for its pages.
    "controls": {
        "captured": [0.75, 0.85, 0.95],
        "pond": {"tss": 0.80, "tp": 0.51, "tn": 0.33, "sources": ["semcog_lid"]},
        "infiltration": {"tss": 0.95, "tp": 0.70, "tn": 0.51, "volume": 0.5, "sources": ["semcog_lid"]},
        "standard_sources": ["egle_ms4", "kcdc_rules"],
        "standard": "Treat the first inch of runoff or 90% of runoff-producing storms with at least 80% TSS removal (or 80 mg/L), and hold peak rate and volume to pre-development for storms up to the 2-year, 24-hour event",
    },
    # Construction, a screening estimate. t_per_ac_yr: gross erosion (EPA MM8 Table 8.1, Wisconsin's 30-200). delivery [A]: below a field's, because a site isn't all bare all year, and set so the middle, 20 t/ac, sits among yields
    # measured leaving active sites (Helsel 1985, 15-25; Lee and Ziegler 2010, 15-19 with controls; Franklin County, Florida, 30, in Table 8.1). basin_removal: EPA MM8 Table 8.5, sediment basins average 70%, low 42%; perforated risers' 94% as the high end.
    "construction": {"t_per_ac_yr": [30, 100, 200], "delivery": [0.1, 0.2, 0.33], "basin_removal": [0.42, 0.70, 0.94], "years": [1, 2, 3], "sources": ["epa_mm8", "epa_fact26", "helsel1985", "lee_ziegler2010"],
                     "permits": "Part 91 soil erosion permit for 1 acre or more, or within 500 ft of a lake or stream; construction storm water permit-by-rule (R 323.2190) with a Notice of Coverage above 5 acres and weekly inspection by a certified operator"},
    # Road salt on parking and drives: lb per 1,000 sq ft per event (MPCA targets; practice is often higher) x events per winter [A], in every state: the median winter's days with
    # precipitation at 1 C or below x 0.6, +/-50%. The 0.6 [A]: a salting event is taken to be a day with measurable snow, and 0.6 is NOAA's 1991-2020 normal days with 0.1 in or more of snow over
    # those days, median 0.62 at 17 stations in Michigan, Ohio, Virginia and Texas (0.39-0.74), and 0.60 without Michigan's. Under 2 such days a winter there is no salt season to speak of.
    "salt": {"lb_per_ksf": [0.75, 1.5, 3.0], "events_per_day": 0.6, "events_range": 0.5, "min_days": 2, "paved_share": 0.60, "chloride_share": 0.607,
             "chronic_mg_l": 150, "sources": ["mpca_salt", "noaa_normals", "egle_rule57"]},
    # Backup generators: diesel at full load (Cat 3516C, 133.6 gal/h at 2,000 ekW) x hours stored on site [A]
    "fuel": {"gal_per_mwh": 66.8, "hours": [12, 48, 72], "gen_mw_per_it_mw": 1.2, "unit_mw": 2.5, "spcc_gal": 1320,
             "sources": ["cat3516c", "uptime2014", "amazon_mo2026", "wyofile2025", "cfr112"]},
    # Runoff heat: summer runoff from pavement averages about 25 C (77 F) vs a 68 F (20 C) coldwater limit in June-August
    "heat": {"paved_c": 24.9, "forest_c": 21.5, "cold_limit_f": 68, "cold_rise_f": 2, "sources": ["herb2007", "rule75", "stefan2010"]},
    # Cooling-tower blowdown: dissolved solids = makeup x cycles, at the cooling model's cycles (physics.RANGES["coc"], its ends and middle); phosphate inhibitors up to ~6.5 mg/L as P. Makeup's
    # dissolved solids are round figures for lake water and groundwater [A], and real water differs by place, more so outside the Great Lakes. The plant limit of 1 mg/L is Michigan's (Rule 60), for its pages.
    "blowdown": {"makeup_tds": {"lake": 170, "ground": 400}, "cycles": [3, 4.5, 6], "p_mg_l": [0, 3, 6.5], "plant_p_limit": 1.0,
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


def sediment_yield(before, state=None):
    """Sediment leaving soil-covered land today, tons an acre a year, [lo, mid, hi]: gross erosion x delivery. A screening estimate. `state`: a postal code, for farmland's NRI rate; without one, or for a state NRI doesn't have, the national rate."""
    Y = PARAMS["sediment_yield"]
    gross = Y["woods_gross"] if before == "woods" else Y["farm_gross"]["by_state"].get(state, Y["farm_gross"]["national"])
    return [gross[i] * Y["delivery"][i] for i in range(3)]


def loads(acres, rain_in, before="farm", imp=None, roof_share=None, state=None):
    """Annual runoff (gallons) and loads (TSS tons, TP lb, TN lb) now, after with no controls, after with typical wet ponds
    and after with infiltration. Each value is [lo, mid, hi]. Sediment today on farmland or woods is a yield (sediment_yield); everything else is runoff x concentration."""
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
        if k == "tss" and before in ("farm", "woods"):
            y = sediment_yield(before, state)
            now = [LB * acres * i0 * r_imp * _w(now_imp, i) / div + acres * (1 - i0) * y[i] for i in range(3)]
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


def construction(acres_disturbed):
    """Sediment leaving bare ground in a year of construction, tons, no controls: gross erosion x delivery, a yield. A screening estimate."""
    c = PARAMS["construction"]
    return [acres_disturbed * c["t_per_ac_yr"][i] * c["delivery"][i] for i in range(3)]


def construction_with_basin(acres_disturbed):
    """The same with sediment basins taking the whole site's runoff [A]; the low end pairs with the most removal."""
    r = PARAMS["construction"]["basin_removal"]
    return [x * (1 - r[2 - i]) for i, x in enumerate(construction(acres_disturbed))]


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


def salt_events(days):
    """Road salt events a winter, [lo, mid, hi], from the median winter's days with precipitation at 1 C or below, at a station or a weather grid cell. One method for every state."""
    S = PARAMS["salt"]
    mid = S["events_per_day"] * days if days >= S["min_days"] else 0.0
    return [(1 - S["events_range"]) * mid, mid, (1 + S["events_range"]) * mid]


def salt(acres, imp, events):
    """Road salt a winter on parking and drives (tons of salt) and the chloride in it. `events`: [lo, mid, hi] events a winter at the place (salt_events)."""
    S, A = PARAMS["salt"], PARAMS["after"]
    imp = A["imp"] if imp is None else imp
    paved_ksf = acres * imp * (1 - A["roof_share"]) * 43.56
    t = [paved_ksf * S["lb_per_ksf"][i] * events[i] / 2000 for i in range(3)]
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
