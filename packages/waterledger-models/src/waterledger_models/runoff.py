"""Runoff water quality before and after a campus is built: annual runoff and pollutant loads, the construction years,
road salt, generator fuel, runoff heat and what cooling-water blowdown carries to a sewer plant.

Screening level, for a review or a public estimate, not a calibrated model:
  runoff   Simple Method (Schueler 1987), split by surface: R = P x 0.9 x Rv, with Rv by land cover from the Runoff Reduction technical memo
           (Hirschman, Collins and Schueler 2008, Table 4): 0.95 impervious, 0.20 turf and 0.03 forest on hydrologic soil group B (by soil group later).
           Cropland has no value there: 0.20 [A], as turf, since row crop curve numbers on soil group B (78-81, TR-55) are above lawn's (61-69)
  loads    each land cover reports what leaves an acre in a year, by whatever water carries it. A site's own soils, slopes, drainage and practices can move these a lot.
           developed  surface: L (lb/yr) = 0.226 x R (in) x C (mg/L) x A (ac), one whole-site C by land use (NSQD 4.02), since outfalls already hold roofs, paving and landscaping;
                      below ground: the natural yield on the pervious share [A]
           farmland   phosphorus and nitrogen: USDA CEAP's modeled loss per acre by production region, surface and below ground (tile drains and deep percolation), checked against MANAGE's measurements
           natural    phosphorus and nitrogen: measured yields of undeveloped basins (Clark et al. 2000), national
  controls two cases, everywhere: no controls, and typical wet pond performance on the captured share of runoff, on the surface part only. Treated C = max(C x (1 - removal), floor)
           80% TSS is what wet ponds typically do, in any state (CWP 2000, as printed in SEMCOG 2008 Table 9.5), and also the level Michigan's post-construction standard asks for
           (EGLE MS4 permits, Kent County Drain Commissioner rules). Phosphorus and nitrogen: CWP 2007's wet pond quartiles. Infiltration is the stronger option, and nitrogen it soaks in goes to groundwater, not away
  sediment two bases, on purpose. Today on soil and the construction years are yields, tons an acre a year, because runoff x concentration doesn't capture soil scoured off the
           ground: gross erosion x a delivery ratio [A]. The finished site is runoff x concentration, because roofs, paving and established lawn aren't scouring.
           Screening estimates: a study with site soils, slopes and sediment modeling would do better
PARAMS is the single source of every value; Water Ledger reads it from waters.json and the Water Review reads it here.
"""

from waterledger_models import hydrology

LB = 0.226          # lb per (ac x in x mg/L)
GAL_PER_AC_IN = 27154.0
PJ = 0.9            # share of rain events that produce runoff (Simple Method)

# Whole-site event mean concentrations, mg/L, [lo, mid, hi], arithmetic means, NSQD 4.02 (Pitt, Maestre and Clary 2018; TP p.39, TKN p.31, NO2+NO3 p.36; TN = TKN + NO2+NO3): institutional, commercial, industrial [A].
# Outfalls drain mixed land, so one value for the site replaces values by surface. TSS from the database's file (commercial 118, industrial 152; institutional's 144 rests on 13 sites), with NSQD 1.1's commercial mean, 96, low.
# Built land takes the campus's values, so a change between them comes from impervious share and not a choice of class [A].
_ROOF_SHARE = 0.40
_EMC = {"developed": {"tss": [96, 118, 152], "tp": [0.20, 0.31, 0.40], "tn": [1.9, 2.7, 3.1], "sources": ["nsqd402", "nsqd11"]}}

# USDA NRCS (2022), Conservation Practices on Cultivated Cropland, CEAP II, thousands of acres and tons a year by production region: Tables A-1, A-17 to A-20, as
# (acres, surface N, subsurface N, sediment P, soluble P); after the acres, each as (acres above the threshold, tons on them, tons on the rest).
_CEAP = {
    "atlantic_gulf": (13825, (481, 7, 16), (8260, 254, 39), (1606, 6.0, 3.3), (9527, 5, 1)),
    "california": (3913, (49, 1, 2), (1311, 70, 10), (61, 0.2, 0.5), (665, 1, 0.2)),
    "east_central": (10166, (1770, 30, 18), (5055, 145, 34), (2743, 12.4, 2.7), (7486, 4, 0.5)),
    "lower_miss_texas_gulf": (20916, (2277, 29, 40), (9886, 273, 74), (2845, 9.3, 6.8), (16233, 11, 1)),
    "north_central": (123296, (9039, 157, 196), (38371, 1025, 491), (13640, 59.6, 32.1), (40064, 25, 11)),
    "northeast": (7597, (1047, 17, 12), (3769, 126, 25), (2334, 10.9, 1.9), (4478, 2, 1)),
    "northern_plains": (51130, (11442, 153, 92), (9988, 285, 128), (4730, 12.0, 14.6), (748, 0.3, 2)),
    "northwest": (13438, (606, 10, 21), (2684, 115, 21), (836, 3.2, 2.1), (877, 1, 0.4)),
    "south_central": (5107, (1326, 21, 9), (2045, 76, 17), (1221, 4.4, 1.7), (2586, 2, 0.3)),
    "southern_central_plains": (62732, (5764, 69, 132), (6784, 202, 108), (3476, 11.1, 17.1), (1405, 1, 2)),
    "southwest": (3183, (143, 2, 5), (764, 29, 4), (138, 0.4, 0.5), (292, 0, 0.1)),
    "national": (315303, (33946, 497, 541), (88914, 2601, 949), (33630, 129, 83), (84361, 51, 19)),
}


def _ceap(region):
    """Loss per acre, lb a year, [lo, mid, hi], for a CEAP region. Middle: the region's mean, surface plus below ground. Low: the mean on acres meeting CEAP's thresholds.
    High: the mean on acres above the threshold of the pathway that carries most of it, plus the other pathway's mean. Low and high show the spread between fields [A]."""
    acres, *rest = _CEAP[region]
    pa = lambda t, a: t * 2000 / a
    def spread(dominant, other):
        mean_d, mean_o = pa(dominant[1] + dominant[2], acres), pa(other[1] + other[2], acres)
        low = pa(dominant[2], acres - dominant[0]) + pa(other[2], acres - other[0])
        return [low, mean_d + mean_o, pa(dominant[1], dominant[0]) + mean_o]
    surf_n, sub_n, sed_p, sol_p = rest
    return {"tn": spread(sub_n, surf_n), "tp": spread(sed_p, sol_p), "tn_surface": [pa(surf_n[2], acres - surf_n[0]), pa(surf_n[1] + surf_n[2], acres), pa(surf_n[1], surf_n[0])]}


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
    # Farmland and natural land, lb an acre a year, [lo, mid, hi]. Farm: CEAP by region; a state takes the region holding most of its cropland [A], from Fig. 2; CEAP publishes no boundaries, so not by place. A state without one takes the national row.
    # Natural: Clark, Mueller and Mast 2000, Table 1, 63 undeveloped basins, medians of basin means with quartiles (kg/km2 converted). One national value: it is small against every other land cover, and regional readings only exist off a chart. Dry places run lower.
    "nutrient_yield": {"farm": {k: _ceap(k) for k in _CEAP}, "farm_region": {"MI": "north_central", "OH": "north_central", "VA": "east_central", "TX": "southern_central_plains"},
                       "natural": {"tp": [0.043, 0.076, 0.107], "tn": [0.40, 0.77, 1.96]}, "sources": ["ceap2022", "clark2000", "manage"]},
    # Yields today, a screening estimate: gross erosion x delivery. Delivery [A]: about a third leaves a site of a few hundred acres, the rest settling at field edges and in swales, as in published
    # area relations (0.33 at half a square mile, Stewart et al. 1978, read only in excerpt); an agricultural figure of 25% +/-15% is reported there too. Woods: EPA MM8 Table 8.1's natural range, 0.01-1.0, its geometric middle 0.1 [A].
    "sediment_yield": {"delivery": [0.2, 0.33, 0.5], "farm_gross": {"national": CROPLAND_EROSION_US, "by_state": CROPLAND_EROSION}, "woods_gross": [0.01, 0.1, 1.0], "sources": ["nri2022", "epa_mm8"]},
    "before_imp": {"farm": 0.02, "woods": 0.01, "built": 0.60},     # [A] impervious share of the land as it is now
    "after": {"imp": 0.50, "imp_range": [0.40, 0.60], "roof_share": _ROOF_SHARE},   # [A] roofs and paving; roofs as a share of that
    # Removal by practice, [lo, mid, hi], with concentration floors. Captured share of annual runoff [A]. Wet ponds: sediment SEMCOG Table 9.5; phosphorus and nitrogen CWP 2007 Table 2 (quartiles and median).
    # Floors: median effluent in the BMP Database (2012 Chesapeake summary, Table 11; nitrogen counts TKN alone). Infiltration: runoff reduction and pollutant removal kept apart (Runoff Reduction memo Tables 2-3, 7), 0.7 its middle [A];
    # sediment at the pond's 80%, which gives about SEMCOG's 95% in all. "standard" is Michigan's rule, for its pages.
    "controls": {
        "captured": [0.75, 0.85, 0.95],
        "pond": {"tss": [0.80, 0.80, 0.80], "tp": [0.39, 0.52, 0.76], "tn": [0.16, 0.31, 0.41], "sources": ["semcog_lid", "cwp2007"]},
        "infiltration": {"tss": 0.80, "tp": 0.25, "tn": 0.15, "volume": [0.5, 0.7, 0.9], "sources": ["runoff_reduction2008", "semcog_lid"]},
        "floor": {"tss": 0, "tp": 0.13, "tn": 1.1, "sources": ["bmpdb2012"]},
        "standard_sources": ["egle_ms4", "kcdc_rules"],
        "standard": "Treat the first inch of runoff or 90% of runoff-producing storms with at least 80% TSS removal (or 80 mg/L), and hold peak rate and volume to pre-development for storms up to the 2-year, 24-hour event",
    },
    # Construction, a screening estimate; "permits" is Michigan's, for its pages. t_per_ac_yr: gross erosion (EPA MM8 Table 8.1, Wisconsin's 30-200). delivery [A]: below a field's, because a site isn't all bare all year, and set so the middle, 20 t/ac, sits among yields
    # measured leaving active sites (Helsel 1985, 15-25; Lee and Ziegler 2010, 15-19 with controls; Franklin County, Florida, 30, in Table 8.1). basin_removal: EPA MM8 Table 8.5, sediment basins average 70%, low 42%; perforated risers' 94% as the high end.
    "construction": {"t_per_ac_yr": [30, 100, 200], "delivery": [0.1, 0.2, 0.33], "basin_removal": [0.42, 0.70, 0.94], "years": [1, 2, 3], "sources": ["epa_mm8", "epa_fact26", "helsel1985", "lee_ziegler2010"],
                     # Phosphorus in the sediment [A], a share by weight: 0.08% is what CEAP implies for sediment leaving North Central fields (1.49 lb on 0.96 tons an acre), a soil already fertilized and enriched by sorting; half that low. An example for the pages, not a measured load
                     "soil_p": [0.0004, 0.0006, 0.0008],
                     "permits": "Part 91 soil erosion permit for 1 acre or more, or within 500 ft of a lake or stream; construction storm water permit-by-rule (R 323.2190) with a Notice of Coverage above 5 acres and weekly inspection by a certified operator"},
    # Road salt on parking and drives: lb per 1,000 sq ft per event (MPCA targets; practice is often higher) x events per winter [A], in every state: the median winter's days with
    # precipitation at 1 C or below x 0.6, +/-50%. The 0.6 [A]: a salting event is taken to be a day with measurable snow, and 0.6 is NOAA's 1991-2020 normal days with 0.1 in or more of snow over
    # those days, median 0.62 at 17 stations in Michigan, Ohio, Virginia and Texas (0.39-0.74), and 0.60 without Michigan's. Under 2 such days a winter there is no salt season to speak of. chronic_mg_l is Michigan's Rule 57, for its pages; no calculation reads it.
    "salt": {"lb_per_ksf": [0.75, 1.5, 3.0], "events_per_day": 0.6, "events_range": 0.5, "min_days": 2, "paved_share": 0.60, "chloride_share": 0.607,
             "chronic_mg_l": 150, "sources": ["mpca_salt", "noaa_normals", "egle_rule57"]},
    # Backup generators: diesel at full load (Cat 3516C, 133.6 gal/h at 2,000 ekW) x hours stored on site [A]
    "fuel": {"gal_per_mwh": 66.8, "hours": [12, 48, 72], "gen_mw_per_it_mw": 1.2, "unit_mw": 2.5, "spcc_gal": 1320,
             "sources": ["cat3516c", "uptime2014", "amazon_mo2026", "wyofile2025", "cfr112"]},
    # Runoff heat: summer runoff from pavement averages about 25 C (77 F) vs a 68 F (20 C) coldwater limit in June-August, which is Michigan's (R 323.1075), for its pages
    "heat": {"paved_c": 24.9, "forest_c": 21.5, "cold_limit_f": 68, "cold_rise_f": 2, "sources": ["herb2007", "rule75", "stefan2010"]},
    # Cooling-tower blowdown: dissolved solids = makeup x cycles, at the cooling model's cycles (physics.RANGES["coc"], its ends and middle); phosphate inhibitors up to ~6.5 mg/L as P. Makeup's
    # dissolved solids are round figures for lake water and groundwater [A], and real water differs by place, more so outside the Great Lakes. The plant limit of 1 mg/L is Michigan's (Rule 60), for its pages.
    "blowdown": {"makeup_tds": {"lake": 170, "ground": 400}, "cycles": [3, 4.5, 6], "p_mg_l": [0, 3, 6.5], "plant_p_limit": 1.0,
                 "sources": ["epa_wsaw", "jea2024", "rule60", "egle_dc_faq"]},
}


def nutrient_yield(before, k, state=None):
    """Phosphorus ("tp") or nitrogen ("tn") leaving farmland or natural land, lb an acre a year, [lo, mid, hi]. `state`: a postal code, for farmland's CEAP region; without one, or for a state not assigned, the national row."""
    Y = PARAMS["nutrient_yield"]
    return Y["natural"][k] if before == "woods" else Y["farm"][Y["farm_region"].get(state, "national")][k]


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


def loads(acres, rain_in, before="farm", imp=None, state=None):
    """Annual runoff (gallons) and loads (TSS tons, TP lb, TN lb) now, after with no controls, after with typical wet ponds and after with infiltration, each [lo, mid, hi].
    Sediment today on farmland or woods is a yield (sediment_yield), phosphorus and nitrogen there too (nutrient_yield). Developed land is runoff x concentration, with the natural yield below its pervious share.
    Also: "tn_lb" "now_surface", the part of farmland's nitrogen in surface runoff, and "to_ground", the nitrogen infiltration sends to groundwater."""
    P = PARAMS
    imp = P["after"]["imp"] if imp is None else imp
    i0, C, cap, nat = P["before_imp"][before], P["controls"], P["controls"]["captured"], P["nutrient_yield"]["natural"]
    depth = lambda share: runoff_in(rain_in, share)     # inches over the whole site, developed
    out = {"runoff_gal": {}, "tss_t": {}, "tp_lb": {}, "tn_lb": {}}
    out["runoff_gal"]["now"] = [acres * runoff_in(rain_in, i0, before) * GAL_PER_AC_IN] * 3
    out["runoff_gal"]["after"] = [acres * depth(imp) * GAL_PER_AC_IN] * 3
    for k, unit in (("tss", "tss_t"), ("tp", "tp_lb"), ("tn", "tn_lb")):
        div = 2000 if k == "tss" else 1
        emc, below = P["emc"]["developed"][k], [0, 0, 0] if k == "tss" else nat[k]
        surface = lambda share: [LB * acres * depth(share) * emc[i] / div for i in range(3)]
        if before == "built":
            s0 = surface(i0)
            now = [s0[i] + acres * (1 - i0) * below[i] for i in range(3)]
        elif k == "tss":        # the yield on the soil, runoff x concentration on what's paved already
            y = sediment_yield(before, state)
            now = [LB * acres * i0 * rain_in * PJ * P["rv"]["imp"] * emc[i] / div + acres * (1 - i0) * y[i] for i in range(3)]
        else:
            now = [acres * x for x in nutrient_yield(before, k, state)]
        s1, b1 = surface(imp), [acres * (1 - imp) * x for x in below]
        after = [s1[i] + b1[i] for i in range(3)]
        pond, infil, ground = [], [], []
        for i in range(3):
            j = 2 - i       # lo pairs with the most capture and removal, hi with the least
            treated = max(emc[i] * (1 - C["pond"][k][j]), C["floor"][k]) / emc[i]
            pond.append(b1[i] + s1[i] * (1 - cap[j] + cap[j] * min(treated, 1)))
            soaked = C["infiltration"]["volume"][j]
            infil.append(b1[i] + s1[i] * (1 - cap[j] + cap[j] * (1 - soaked) * (1 - C["infiltration"][k])))
            ground.append(s1[i] * cap[j] * soaked)
        out[unit] = {"now": now, "after": after, "pond": pond, "infiltration": infil}
        if k == "tn":
            out[unit]["to_ground"] = ground
            if before == "farm":
                Y = P["nutrient_yield"]
                out[unit]["now_surface"] = [acres * x for x in Y["farm"][Y["farm_region"].get(state, "national")]["tn_surface"]]
    out["runoff_gal"]["pond"] = out["runoff_gal"]["after"]
    out["runoff_gal"]["infiltration"] = [out["runoff_gal"]["after"][0] * (1 - cap[2 - i] * C["infiltration"]["volume"][2 - i]) for i in range(3)]
    return out


def construction(acres_disturbed):
    """Sediment leaving bare ground in a year of construction, tons, no controls: gross erosion x delivery, a yield. A screening estimate."""
    c = PARAMS["construction"]
    return [acres_disturbed * c["t_per_ac_yr"][i] * c["delivery"][i] for i in range(3)]


def construction_with_basin(acres_disturbed):
    """The same with sediment basins taking the whole site's runoff [A]; the low end pairs with the most removal."""
    r = PARAMS["construction"]["basin_removal"]
    return [x * (1 - r[2 - i]) for i, x in enumerate(construction(acres_disturbed))]


def construction_p(acres_disturbed, basin=True):
    """Phosphorus in the sediment leaving a year of construction, lb, [lo, mid, hi], with sediment basins or without. A rough figure [A]."""
    sed = construction_with_basin(acres_disturbed) if basin else construction(acres_disturbed)
    return [x * 2000 * s for x, s in zip(sed, PARAMS["construction"]["soil_p"])]


def cooling_p(flow_mgd):
    """Phosphorus a year in wastewater from cooling, lb, by inhibitor dose [lo, mid, hi], and what a plant at the limit in PARAMS would pass."""
    B = PARAMS["blowdown"]
    return {"lb_yr": [p * flow_mgd * 8.34 * 365 for p in B["p_mg_l"]], "at_plant_limit_lb_yr": B["plant_p_limit"] * flow_mgd * 8.34 * 365}


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


def storm_mg(acres, storm_in, imp=None, cn_pervious=None):
    """Runoff from one storm of `storm_in` inches on the finished site, million gallons (curve numbers, not the Simple Method, which is for the year).
    Not routed: a volume, not a peak. cn_pervious: the pervious part's curve number (hydrology.CN_POST_PERV unless given, as for a solar array's
    ground, design 0014)."""
    imp = PARAMS["after"]["imp"] if imp is None else imp
    cn = hydrology.CN_POST_PERV if cn_pervious is None else cn_pervious
    return hydrology.composite_runoff_in(storm_in, imp, cn) * acres * GAL_PER_AC_IN / 1e6


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
