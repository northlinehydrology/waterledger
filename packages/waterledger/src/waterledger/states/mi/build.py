"""Build Water Ledger Michigan's data files: <site>/mi/data/*.json.

Public data only. Every value carries a source id from SOURCES. Run from the repo root:
    python -m waterledger.states.mi              (or: waterledger build mi)
"""
import datetime, json, math, os

import pandas as pd

from waterledger_data import energy, places as pl
from waterledger_data.wastewater import OWN_KM
from waterledger_models.datacenter import cooling as cw
from waterledger_models.datacenter.physics import DRAWS
from waterledger_data.config import CACHE, SITE as SITE_ROOT, setting

from waterledger.comparisons import HOUSEHOLD_GPD, it_mw_from_contract
from waterledger_data import wateruse
from waterledger.levels import LEVELS  # noqa: F401  re-exported
from waterledger.citations import CONTEXT, PARAM_SOURCES, SHORT, SOURCES  # noqa: F401  moved (design 0011); re-exported here
from waterledger.states.mi.provider import SALT_DAYS
from waterledger_models import MODEL_VERSION, snapshot_model  # noqa: F401  MODEL_VERSION re-exported (waterledger.states.mi); snapshot_model() labels the numbers (MODELS)
STATE = "mi"      # Water Ledger is organized by state: site/waterledger/<state>/
SITE = os.path.join(SITE_ROOT, STATE)
OUT = os.path.join(SITE, "data", "estimates.json")
OUT_PLACES = os.path.join(SITE, "data", "places.json")
OUT_MAP = os.path.join(SITE, "data", "map.json")
OUT_WATERS = os.path.join(SITE, "data", "waters.json")
OUT_POWER = os.path.join(SITE, "data", "power.json")
RAW_BASE = CACHE
RAW_PLACES = os.path.join(RAW_BASE, "places")
RAW = os.path.join(RAW_BASE, "lit")

REGIONS = {
    "southeast": {"name": "Southeast Michigan", "station": "Ann Arbor area", "lat": 42.25, "lon": -83.60},
    "southwest": {"name": "Southwest Michigan", "station": "Kalamazoo area", "lat": 42.29, "lon": -85.59},
    "west": {"name": "West Michigan", "station": "Grand Rapids area", "lat": 42.88, "lon": -85.52, "cache": "gaines"},
    "central": {"name": "Central Michigan", "station": "Lansing area", "lat": 42.73, "lon": -84.55},
    "thumb": {"name": "Saginaw Valley and the Thumb", "station": "Saginaw area", "lat": 43.42, "lon": -83.95},
    "north": {"name": "Northwest Michigan", "station": "Traverse City area", "lat": 44.76, "lon": -85.62},
    "northeast": {"name": "Northeast Michigan", "station": "Alpena area", "lat": 45.06, "lon": -83.43},
    "up": {"name": "Central and Western Upper Peninsula", "station": "Marquette area", "lat": 46.54, "lon": -87.40},
}




# Water at the power plants for Michigan's mix: the same table and rules as every state (energy.state_power_water; model 1.3,
# docs/methods/power_water): EIA's 2024 plant-reported cooling water over Michigan's 2024 net generation, flagged reports (Midland
# Cogeneration's consumption above 2,000 gal/MWh; zero consumption at Cook, Campbell, Belle River and other once-through plants;
# pond circulation) replaced by Macknick et al. medians; no import blend (Michigan is a net exporter). Range over reported, adjusted,
# Macknick bottom-up and Siddik's MISO 2022 values. MISO figures are Siddik et al.'s 2022 dataset, load-weighted, as a cross-check.
L_KWH_TO_GAL_MWH = energy.L_KWH_TO_GAL_MWH
_MI = energy.state_power_water("MI")
POWER = {
    "consumed_l_per_kwh": {"michigan_mix": round(_MI["consumed"], 2), "miso_excl_hydro": 1.57, "miso_incl_hydro": 3.84,
                           "range": [round(_MI["consumed_lo"], 2), round(_MI["consumed_hi"], 2)],
                           "sources": ["eia923_2024", "eia_mi", "macknick2012", "siddik2024"]},
    "withdrawn_l_per_kwh": {"value": round(_MI["withdrawn"], 1), "range": [round(_MI["withdrawn_lo"], 1), round(_MI["withdrawn_hi"], 1)],
                            "returned_share_note": "about 98% returned to the Great Lakes and rivers, warmer", "sources": ["eia923_2024", "eia_mi", "macknick2012"]},
}


# Electricity overhead by cooling design: LBNL 2024 Fig. 4.4, large-scale facilities, simulated annual PUE (figure-read medians and boxes,
# U.S. climates). Closed loop spans LBNL's two waterless large-scale systems: liquid-cooled IT with dry coolers (about 1.10) and dry coolers
# with an air-cooled chiller (about 1.20). Lake-source is not in LBNL; the cooling-tower range stands in for it [estimate].
# Water at power plants per MWh, by what supplies the campus: consumed (gal_mwh, lo, hi) and withdrawn (wd_gal_mwh, wd_lo, wd_hi), gallons per
# MWh. Macknick et al. 2012 medians and ranges (Table 2 consumption, Table 3 withdrawal; wind and PV withdrawal equals consumption, p. 6)
# unless noted.
POWER_SUPPLY = {
    "state_mix": {"label": "Michigan's current mix", "gal_mwh": round(_MI["consumed"] * L_KWH_TO_GAL_MWH), "lo": round(_MI["consumed_lo"] * L_KWH_TO_GAL_MWH),
               "hi": round(_MI["consumed_hi"] * L_KWH_TO_GAL_MWH), "wd_gal_mwh": round(_MI["withdrawn"] * L_KWH_TO_GAL_MWH),
               "wd_lo": round(_MI["withdrawn_lo"] * L_KWH_TO_GAL_MWH), "wd_hi": round(_MI["withdrawn_hi"] * L_KWH_TO_GAL_MWH),
               **energy.withdrawal_split(round(_MI["withdrawn"] * L_KWH_TO_GAL_MWH), _MI["withdrawn_saline"] * L_KWH_TO_GAL_MWH),
               "sources": ["eia923_2024", "eia_mi", "macknick2012"],
               "note": f"{_MI['consumed']:.2f} L/kWh consumed ({_MI['consumed_lo']:.2f} to {_MI['consumed_hi']:.2f}) and {_MI['withdrawn']:.0f} L/kWh withdrawn ({_MI['withdrawn_lo']:.0f} to {_MI['withdrawn_hi']:.0f}): EIA's 2024 plant-reported cooling water over Michigan's 2024 generation, flagged and missing reports filled with Macknick factors, updated with 2022 reports (docs/methods/power_water)"},
    "new_gas": energy.NEW_GAS,
    **energy.fuel_options("MI", "Michigan"),      # the same method as every state
    "renew": energy.wind_solar(_MI["pv_share_of_wind_solar"]),     # Michigan's own wind and solar mix (other states pass theirs)
    "miso": {"label": "MISO grid average", "gal_mwh": 415, "lo": 415, "hi": 415, "wd_gal_mwh": 15080, "wd_lo": 15080, "wd_hi": 15080, "sources": ["siddik2024"],
             "note": "1.57 L/kWh consumed and 57.1 L/kWh withdrawn, MISO excluding hydropower consumption, 2022 (Siddik et al. dataset, load-weighted)"},
}


TRACKER_MUNI = {"gaines": ("Gaines charter township", "Kent"), "lowell": ("Lowell charter township", "Kent"), "dorr": ("Dorr township", "Allegan"),
                "ypsi": ("Ypsilanti charter township", "Washtenaw"), "augusta": ("Augusta charter township", "Washtenaw"), "saline": ("Saline township", "Washtenaw"),
                "vanburen": ("Van Buren charter township", "Wayne"), "lyon": ("Lyon charter township", "Oakland"), "southfield": ("Southfield city", "Oakland"),
                "howell": ("Howell township", "Livingston")}

LON0, LON1, LAT0, LAT1 = -90.5, -82.3, 41.65, 48.35
KX, SC = math.cos(math.radians(45)), 60.0


def proj(lon, lat):
    return round((lon - LON0) * KX * SC, 1), round((LAT1 - lat) * SC, 1)


def _dp(pts, tol):
    if len(pts) < 3:
        return pts
    (x1, y1), (x2, y2) = pts[0], pts[-1]
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy) or 1e-9
    i, dmax = 0, 0
    for k, (x, y) in enumerate(pts[1:-1], 1):
        d = abs(dy * x - dx * y + x2 * y1 - y2 * x1) / L
        if d > dmax:
            i, dmax = k, d
    if dmax > tol:
        return _dp(pts[:i + 1], tol)[:-1] + _dp(pts[i:], tol)
    return [pts[0], pts[-1]]


def _ring_path(ring, tol, minpts=4):
    p = [proj(*c[:2]) for c in ring]
    p = p[:-1] if p[0] == p[-1] else p
    m = len(p) // 2
    p = _dp(p[:m + 1], tol)[:-1] + _dp(p[m:] + [p[0]], tol)[:-1]
    if len(p) < minpts:
        return ""
    return "M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in p) + "Z"


def _geom_path(geom, tol, minpts=4):
    polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
    return "".join(_ring_path(r, tol, minpts) for poly in polys for r in poly)


def nearest_region(lat, lon):
    def d(r):
        return (lat - r["lat"]) ** 2 + ((lon - r["lon"]) * math.cos(math.radians(lat))) ** 2
    return min(REGIONS, key=lambda k: d(REGIONS[k]))


def build_map(counties):
    adm = json.load(open(os.path.join(RAW_PLACES, "adm50.json"), encoding="utf-8"))
    mi = [f["geometry"] for f in adm["features"] if f["properties"].get("name") == "Michigan" and f["properties"].get("admin") == "United States of America"][0]
    lakes = json.load(open(os.path.join(RAW_PLACES, "lakes50.json"), encoding="utf-8"))
    lk = [f["geometry"] for f in lakes["features"] if f["properties"].get("name") in ("Lake Superior", "Lake Michigan", "Lake Huron", "Lake Erie", "Lake Saint Clair")]
    W, H = proj(LON1, LAT0)
    out = {"viewBox": f"0 0 {W} {H}", "land": _geom_path(mi, 0.25), "lakes": "".join(_geom_path(g, 0.35, 6) for g in lk),
           "counties": {}, "stations": {k: dict(zip(("x", "y"), proj(r["lon"], r["lat"]))) for k, r in REGIONS.items()},
           "source": "County lines: U.S. Census TIGERweb; shoreline and lakes: Natural Earth 1:50m"}
    for c in counties:
        out["counties"][c["geoid"]] = {"name": c["name"], "region": nearest_region(c["lat"], c["lon"]),
                                       "d": "".join(_ring_path(r, 0.2, 3) for r in c["rings"])}
    return out


def great_lake_near(bounds):
    """The nearest Great Lake within 5 km of each municipal boundary, by the rule every state has (waterledger_data.greatlakes)."""
    import geopandas as gpd
    from waterledger_data import greatlakes
    from waterledger_data.census import _polygon
    return greatlakes.near(gpd.GeoDataFrame([{"geoid": g, "geometry": _polygon(rings)} for g, rings in bounds.items()], geometry="geometry", crs=4326))


def near_systems(munis, enrich):
    """For each place with no water system mapped, the nearest sizable one, by the rule every state has (waterledger_data.supply.nearest_sizable), in the places file's form."""
    from waterledger_data import supply
    empty = pd.DataFrame([{"geoid": m["geoid"], "lat": m["lat"], "lon": m["lon"]} for m in munis if not enrich.get(m["geoid"], {}).get("water")])
    return {g: {"pwsid": w["pwsid"], "name": w["name"], "pop": w["population"], "connections": w["connections"], "km": km} for g, (w, km) in supply.nearest_sizable("MI", empty).items()}


def build_places(counties, munis, enrich, cmap, shore=None, near=None):
    shore, near = shore or {}, near or {}
    cname = {c["geoid"]: c["name"] for c in counties}
    out = []
    for m in munis:
        e = enrich.get(m["geoid"], {})
        x, y = proj(m["lon"], m["lat"])
        ws = e.get("watershed", {})
        out.append({"g": m["geoid"], "n": m["name"], "k": m["kind"], "c": cname.get(m["county_fips"], ""), "cf": m["county_fips"],
                    "r": cmap["counties"].get(m["county_fips"], {}).get("region") or nearest_region(m["lat"], m["lon"]), "e": cell_for(m["lon"], m["lat"]), "x": x, "y": y,
                    "w": e.get("water", []), "h12": ws.get("huc12"), "h8": ws.get("huc8"), "gl": shore.get(m["geoid"]), "near": near.get(m["geoid"])})
    out.sort(key=lambda p: (p["n"].lower(), p["c"]))
    return out


# EGLE's reported withdrawals moved to waterledger_data.wateruse (design 0011): the same functions, under their old names here until this builder retires
from waterledger_data.wateruse import EGLE_GROUPS as USE_GROUPS, egle_use_file, michigan_groups as county_uses  # noqa: E402,F401


GREAT_LAKE_BY_HUC4 = {"0401": "Lake Superior", "0402": "Lake Superior", "0418": "Lake Superior", "0403": "Lake Michigan", "0404": "Lake Michigan",
                      "0405": "Lake Michigan", "0406": "Lake Michigan", "0419": "Lake Michigan", "0407": "Lake Huron", "0408": "Lake Huron",
                      "0420": "Lake Huron", "0424": "Lake Huron", "0409": "Lake St. Clair and the Detroit River", "0410": "Lake Erie"}


WATER_SOURCES = {"nsqd402", "ceap2022", "clark2000", "manage", "cwp2007", "bmpdb2012", "nri2022", "helsel1985", "lee_ziegler2010", "runoff_reduction2008", "nsqd11", "noaa_normals", "attains2026", "mi_part22", "mdnr_trout", "noaa_cag", "echo", "cwns2022", "egle_ms4", "kcdc_rules",
                 "semcog_lid", "epa_fact26", "epa_mm8", "part91", "mpca_salt", "egle_rule57", "cat3516c", "uptime2014", "amazon_mo2026",
                 "wyofile2025", "cfr112", "herb2007", "stefan2010", "rule75", "jea2024", "rule60", "egle_dc_faq", "wleb_dap", "simple_method", "nrcs_tr55",
                 "usgs_wbd", "epa_wsaw", "noaa_atlas14", "wellogic", "wwat", "mcl327"}


def build_waters():
    """site/waterledger/mi/data/waters.json: receiving-water impairments by HUC12 (with downstream links), sewer plants,
    county rainfall and the runoff water quality parameters. Public data only."""
    from waterledger_data import waters as wi
    from waterledger_models import runoff as rq
    from waterledger_data import receiving as rc
    h12 = wi.by_huc12()
    trout = wi.trout_by_huc12()
    for k, v in h12.items():
        v["gl"] = GREAT_LAKE_BY_HUC4.get(k[:4])
        if k in trout:
            v["tr"] = [trout[k]["n"], trout[k]["names"]]
    # past the state line, as every other state's paths go (a reach the tracer adds is marked "o"), from each place's main watershed
    h12 = rc.past_the_line(h12, sorted({p["h12"][0]["code"] for p in json.load(open(OUT_PLACES, encoding="utf-8"))["places"] if p["h12"]}))
    plants = []
    for p in wi.potws():
        x, y = proj(p["lon"], p["lat"])
        # ECHO's past-year average flow is kept only where it is plausible against the design flow (unit errors are common at lagoons)
        if p["flow_mgd"] and not (p["design_mgd"] and 0.1 <= p["flow_mgd"] / p["design_mgd"] <= 1.3):
            p["flow_mgd"] = None
        plants.append({"id": p["id"], "n": p["name"], "city": p["city"].lower(), "x": x, "y": y, "major": p["major"], "cso": p["cso"],
                       "lagoon": p["lagoon"], "flow": p["flow_mgd"], "design": p["design_mgd"], "recv": (p["receiving"] or "").title(), "h12": p["huc12"]})
    # household wells by place: [drift wells, drift depth ft, drift water level ft, rock wells, rock depth, rock water level] (EGLE Wellogic)
    wells, HW = {}, wi.household_wells()
    for p in json.load(open(OUT_PLACES, encoding="utf-8"))["places"]:
        w = HW.get((p["c"], wi.place_stem(p["n"])))
        if w:
            d, r = w.get("drift", {}), w.get("rock", {})
            wells[p["g"]] = [d.get("n", 0), d.get("depth"), d.get("swl"), r.get("n", 0), r.get("depth"), r.get("swl")]
    data = {"generated": datetime.date.today().isoformat(), "cycle": 2026, "groups": wi.LABELS, "wells": wells, "h12": h12, "plants": plants, "rain_in": wi.county_precip(), "rain_median_in": rq.rain_median(wi.county_precip()), "plant_rule": {"own_km": OWN_KM}, "runoff": {**rq.PARAMS, "salt": {**rq.PARAMS["salt"], "events_by_region": {k: rq.salt_events(d) for k, d in SALT_DAYS.items()}}},
            "sources": {k: {"citation": c, "url": u, "short": SHORT.get(k, k)} for k, (c, u) in SOURCES.items() if k in WATER_SOURCES}}
    with open(OUT_WATERS, "w", encoding="utf-8") as f:
        json.dump(round_tree(data, 3), f, separators=(",", ":"))
    print("wrote", OUT_WATERS, os.path.getsize(OUT_WATERS), "bytes;", sum(1 for v in h12.values() if "i" in v), "HUC12s with listings;", len(plants), "plants")


def build_power():
    """site/waterledger/mi/data/power.json: the electric utilities serving each place (MPSC territories, with the share of the place each
    covers) and each utility's load (EIA-861: yearly Michigan retail sales as an average MW, and summer and winter peaks where reported),
    plus Michigan's total retail sales. Public data only."""
    from waterledger_data import power as pw
    T, L, year = pw.territories(), pw.utility_loads(), pw.eia_year()
    idx = {q["name"]: i for i, q in enumerate(T)}
    utils = []
    for q in T:
        e = L[pw.EIA_ID[q["name"]]]
        utils.append({"n": q["name"], "type": q["type"], "cust": e["customers"], "avg_mw": round(e["mwh"] / 8760, 1),
                      "summer_mw": e["summer_mw"], "winter_mw": e["winter_mw"]})
    bounds = json.load(open(os.path.join(RAW_PLACES, "boundaries.json"), encoding="utf-8"))
    by_place = {}
    for p in json.load(open(OUT_PLACES, encoding="utf-8"))["places"]:
        rings = bounds.get(p["g"])
        if rings:
            by_place[p["g"]] = [[idx[n], sh] for sh, n in pw.place_utilities(rings, T)]
    mi = pw.michigan_retail_mwh()
    data = {"generated": datetime.date.today().isoformat(), "eia_year": year, "michigan": {"mwh": round(mi), "avg_mw": round(mi / 8760)},
            "utilities": utils, "places": by_place,
            "sources": {k: {"citation": c, "url": u, "short": SHORT.get(k, k)} for k, (c, u) in SOURCES.items() if k in ("mpsc_territory", "eia861")}}
    with open(OUT_POWER, "w", encoding="utf-8") as f:
        json.dump(data, f, separators=(",", ":"))
    print("wrote", OUT_POWER, os.path.getsize(OUT_POWER), "bytes;", len(utils), "utilities;", sum(1 for v in by_place.values() if v), "places with a utility")


def round_tree(x, nd=5):
    if isinstance(x, dict):
        return {k: round_tree(v, nd) for k, v in x.items()}
    if isinstance(x, float):
        return round(x, nd)
    return x


def cell_for(lon, lat):
    """A place's ERA5 cell (design 0004's land rule) from the point Michigan's snapshot carries for it: its page position, back in
    degrees and rounded to five places, the point `waterledger era5 run MI` assigned its cell from."""
    from waterledger import scenario as sc
    from waterledger_data import era5
    x, y = proj(lon, lat)
    lo, la = sc.lonlat({"x": x, "y": y})
    return era5.cell(round(la, 5), round(lo, 5))["id"]


def write_cells(ids, runs_dir=None):
    """The site's data/cells/<cell>.json for the cells Michigan's places use, from their runs (CACHE/era5/runs/model1.8), the same
    records a format 3 snapshot carries (national.cells.record); {cell: record}."""
    from waterledger.national import cells
    from waterledger.national.snapshot import _write
    got = {cid: cells.record(run) for cid, run in cells.runs(sorted(ids), runs_dir).items()}
    os.makedirs(os.path.join(SITE, "data", "cells"), exist_ok=True)
    for cid, rec in got.items():
        _write(os.path.join(SITE, "data", "cells", f"{cid}.json"), rec)
    return got


def main(n=DRAWS):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    # model 1.8: each place's cooling comes from its ERA5 cell's run (design 0004; `waterledger era5 run MI`), not from the eight regions'
    # Open-Meteo runs; the regions stay, for road salt, golf and their names on the page
    regions = {rid: {"name": r["name"], "station": r["station"], "lat": r["lat"], "lon": r["lon"]} for rid, r in REGIONS.items()}
    munis = pl.municipalities()
    at = {m["geoid"]: cell_for(m["lon"], m["lat"]) for m in munis}
    cells = write_cells(set(at.values()))
    county = {c["geoid"]: c["name"] for c in pl.counties()}
    named = lambda name, cty: at[next(m["geoid"] for m in munis if m["name"].lower() == name and county.get(m["county_fips"]) == cty)]

    staff = cw.staff_runs(n)
    Dv = {"regions": cells, "staff": {"runs": staff}}
    from waterledger.scenario import band, flow, pue_by_design
    west, van_buren, saline = named("grand rapids city", "Kent"), named("van buren charter township", "Wayne"), named("saline township", "Washtenaw")
    lowell, gaines = named("lowell charter township", "Kent"), named("gaines charter township", "Kent")
    s2 = lambda v: f"{(round(v) if v < 100 else round(v / 10 ** (math.floor(math.log10(v)) - 1)) * 10 ** (math.floor(math.log10(v)) - 1)):,.0f}"
    gal = lambda b: f"about {s2(b['mid'] * 1e6)} gal/day ({s2(b['lo'] * 1e6)} to {s2(b['hi'] * 1e6)} across our assumptions)"
    util = cells[west]["per_100mw"]["dry"]["utilization"]["p50"]
    w300 = flow(Dv, west, "dry", "withdrawn_avg", 300)
    lkwh = w300["mid"] * 1e6 * 3.78541 / (300 * 1000 * util * 24)
    hyb = lambda key: flow(Dv, west, "hybrid", key, 300)["mid"] * 1e6 / 300
    # Van Buren: 1 GW of DTE contract over three buildings, one open loop; computers = contract / top of each design's PUE range [A]
    pue_design = pue_by_design(cells)
    it_t, it_d = it_mw_from_contract(1000 / 3, pue_design["towers"]["hi"]), it_mw_from_contract(2000 / 3, pue_design["dry"]["hi"])
    st = cw.staff_q(staff, it_t + it_d)
    vb = {k: band(cells[van_buren]["per_100mw"]["towers"][f"withdrawn_{k}"], it_t / 100)["mid"] + band(cells[van_buren]["per_100mw"]["dry"][f"withdrawn_{k}"], it_d / 100)["mid"]
          + st["withdrawn"]["p50"] for k in ("avg", "peak_1in10")}
    saline_it = it_mw_from_contract(1400, pue_design["dry"]["hi"])
    mx = lambda r: f"{r:.1f}".removesuffix(".0") if r < 10 else s2(r)          # a multiple, as on the page (WQ.mult)
    low, gb, sal, sw = (flow(Dv, lowell, "dry", "withdrawn_avg", 300), flow(Dv, gaines, "dry", "withdrawn_avg", 100),
                        flow(Dv, saline, "dry", "withdrawn_avg", saline_it), flow(Dv, gaines, "dry", "withdrawn_avg", 320))
    l500 = flow(Dv, lowell, "dry", "withdrawn_avg", 500)
    inside = lambda v, b: b["lo"] <= v <= b["hi"]
    not_counted = "landscape watering, humidification for designs that cool with outside air, and other site uses this page does not count"
    validation = [
        {"check": "Cooling towers, water use per IT kWh (makeup basis)", "published": "LBNL 2024 large tower-based facilities: median ~2.0–2.2 L/kWh, range ~1.75–2.75 (U.S. climates)",
         "ours": f"{cells[west]['per_100mw']['towers']['wue_makeup_l_per_kwh']['p10']:.2f}–{cells[west]['per_100mw']['towers']['wue_makeup_l_per_kwh']['p90']:.2f} L/kWh (Grand Rapids)",
         "reading": "Below LBNL's median, and mostly below its range: partly a cool climate, and mainly because LBNL evaporates all the heat while this model uses the evaporative ratio USGS uses, which leaves a share of it as sensible heat in the air. A stated departure, argued from the air's heat balance and disclosed fleets, with no metered tower site to settle it.", "sources": ["lbnl2024", "usgs2013"]},
        {"check": "Hybrid / evaporative assist (consumed)", "published": "Lei et al. 2025, climate zone 5A: ~0.1 (efficient) to ~0.7 (inefficient) L/kWh; operators 0.1–0.3",
         "ours": f"{cells[west]['per_100mw']['hybrid']['wue_l_per_kwh']['p10']:.2f}–{cells[west]['per_100mw']['hybrid']['wue_l_per_kwh']['p90']:.2f} L/kWh (Grand Rapids)",
         "reading": "At or just below the efficient end of the published range, as expected in a cold climate.", "sources": ["lei2025", "lbnl2024"]},
        {"check": "Dry (no evaporation), water taken per IT kWh", "published": "~0–0.1 L/kWh for designs that use no water for cooling (staff use, and humidification where outside air is used)",
         "ours": f"About {lkwh:.3f} L/kWh at 300 MW, Grand Rapids, staff water included",
         "reading": "Inside the range, near the bottom: these designs recirculate indoor air, so the humidification behind the top of LBNL's range is not counted. A weak check on its own; the Michigan figures below say more.", "sources": ["lbnl2024"]},
        {"check": "Observed utility data, Northern Virginia (per MW of facility power capacity)", "published": "Air-cooled ~150 gal/day/MW; mixed (~60–70% water-cooled) 800–1,006 average, 2,435–3,060 peak day; evaporative peak up to 8,500",
         "ours": f"Per MW of IT capacity at 300 MW, Grand Rapids: dry ~{w300['mid'] * 1e6 / 300:,.0f}; hybrid ~{hyb('withdrawn_avg'):,.0f} average and ~{hyb('withdrawn_peak_1in10'):,.0f} on a 1-in-10 peak day",
         "reading": f"Dry is far below the metered air-cooled figure: the Virginia sites are older, many cool with outside air, and metered totals include {not_counted}; ICPRB's per-MW basis is facility capacity, not computing capacity. Hybrid is the same order of magnitude as the mixed sites.", "sources": ["icprb2025", "icprb2026"]},
        {"check": "Google data center fleet, 2025", "published": "~0.94 L per kWh of facility electricity (10,523 million gallons over 42.4 TWh, all climates and designs)",
         "ours": "Between our hybrid and cooling-tower estimates, as expected for a mixed global fleet", "reading": "Consistent.", "sources": ["google2026"]},
        {"check": "Van Buren Township (Google; 1 GW DTE contract, three buildings, one open loop)", "published": "Developer estimate 2–3.6 MGD (township FAQ, Jan 2026)",
         "ours": f"About {vb['avg']:.1f} MGD average, {vb['peak_1in10']:.1f} MGD 1-in-10 peak (one building's third of the contract with cooling towers, about {it_t:,.0f} MW of computers; two-thirds closed loop, about {it_d:,.0f} MW; Van Buren's own cell)",
         "reading": "Inside the developer's range." if 2.0 <= vb["avg"] <= 3.6 else "Outside the developer's range.", "sources": []},
        {"check": "Lowell Charter Township (Microsoft), closed loop", "published": "About 6,000 gal/day (2.2 million gallons a year) excluding cooling, a Microsoft projection reported locally; size not published; primary document not yet located",
         "ours": f"{gal(low)} at 300 MW, the starting size; {gal(l500)} at 500 MW",
         "reading": f"The reported figure is about {mx(0.006027 / low['mid'])} times ours at 300 MW, " + ("inside" if inside(0.006027, low) else "outside") + " our range across assumptions there, and " + ("inside" if inside(0.006027, l500) else "outside") + " it at 500 MW. The campus's size is not published, and ours counts staff water and loop top-ups only.", "sources": ["lowell_firstlook"]},
        {"check": "Gaines Township (Microsoft), per building", "published": "About 2,000 gal/day per building (Microsoft, as reported by Sun and News, not re-verified); building size and count not published",
         "ours": f"{gal(gb)} for one 100 MW building",
         "reading": f"The reported figure is about {mx(0.002 / gb['mid'])} times our middle estimate, " + ("inside" if inside(0.002, gb) else "outside") + " our range across assumptions.", "sources": ["gaines_sunnews"]},
        {"check": "Saline Township (Related Digital for Oracle and OpenAI; 1.4 GW DTE contract), closed loop", "published": "About 20,000 gal/day at the start of operations, a developer estimate as reported locally; primary document not yet located",
         "ours": f"{gal(sal)} at full build-out, about {saline_it:,.0f} MW of computers",
         "reading": f"The reported figure is about {mx(0.02 / sal['mid'])} times ours and " + ("inside" if inside(0.02, sal) else "above") + " our range across assumptions, although it is for the start of operations and ours is for the full campus. It may include uses this page does not count, such as landscape watering, process water or a phased first fill; the primary document has not been found.", "sources": ["saline_post"]},
        {"check": "Switch data center, Gaines Township (operating since 2017; metered, not projected)", "published": "About 10 million gallons in 2024, about 27,000 gal/day, as a township official reported; design 320 MW; actual load and cooling design not public",
         "ours": f"{gal(sw)} for a closed loop at 320 MW and 50–80% load",
         "reading": f"Metered use is about {mx(0.0274 / sw['mid'])} times ours. Switch's cooling design and actual load are not public, and a metered total includes {not_counted}. Metered use at an operating site can run well above an applicant's projection.", "sources": ["wgvu_switch"]},
    ]
    print("VALIDATION"); [print(" ", v["check"], "|", v["ours"]) for v in validation]

    cnt = pl.counties()
    munis = pl.municipalities()
    bounds = pl.boundaries(cnt)
    enr = pl.enrich(munis, bounds)
    cmap = build_map(cnt)
    places = build_places(cnt, munis, enr, cmap, great_lake_near(bounds), near_systems(munis, enr))
    # a region's cooling, where the page has a region and no place (its starting view, the region menu, the methods page's table): the cell at the
    # region's own point ("Grand Rapids area"), which its name describes; the cell most of its places use if no place shares that one
    from waterledger import scenario as sc
    from waterledger.national.cells import for_regions
    pts = {rid: sc.lonlat(dict(zip(("x", "y"), proj(r["lon"], r["lat"])))) for rid, r in regions.items()}       # as the places' points are made
    for rid, cid in for_regions(pts, [(p["r"], p["e"]) for p in places]).items():
        regions[rid]["cell"] = cid
    storms = pl.county_design_storms(cnt)
    tracker_muni = {}
    for tid, (name, county) in TRACKER_MUNI.items():
        hit = [p["g"] for p in places if p["n"].lower() == name.lower() and p["c"] == county]
        tracker_muni[tid] = hit[0] if hit else None
    with open(OUT_PLACES, "w", encoding="utf-8") as f:
        json.dump({"source": "Municipalities: U.S. Census TIGERweb county subdivisions; water systems: EPA Community Water System Service Area Boundaries (reported or modeled); watersheds: USGS Watershed Boundary Dataset", "places": places}, f, separators=(",", ":"))
    with open(OUT_MAP, "w", encoding="utf-8") as f:
        json.dump(cmap, f, separators=(",", ":"))
    print("places", len(places), os.path.getsize(OUT_PLACES), "map", os.path.getsize(OUT_MAP), "tracker", tracker_muni)

    uses, n_golf, golf_stats = county_uses()
    lake_t = pd.read_csv(os.path.join(RAW, "glerl_lt_avg_temp.csv"), skiprows=[1])
    from waterledger.national.climate import lake_results
    lake_src = lake_results(["Lake Michigan", "Lake Superior", "Lake Huron", "Lake Erie", "Lake St. Clair"], lake_t, n)
    pue_design = pue_by_design(cells, lake_src["power"])
    data = {
        "model_version": snapshot_model(),
        "generated": datetime.date.today().isoformat(),
        "units": "MGD = million gallons per day; per_100mw values are per 100 MW of IT capacity at the sampled utilization",
        "percentiles": "p10/p50/p90 over a Monte Carlo of the parameter ranges; central = all parameters at mid-range",
        "designs": cw.LABELS,
        "parameters": {k: {"range": list(v), "sources": PARAM_SOURCES.get(k, [])}
                       for k, v in list(cw.RANGES.items()) + [("topup", cw.TOPUP)] + [("staff_" + k, v) for k, v in cw.STAFF.items()]},
        "regions": regions,         # model 1.8: the regions' names and points, for salt, golf and the map; cooling is each place's cell (data/cells/<e>.json)
        "cells": {"count": len(cells), "path": "cells/{cell}.json", "model_version": snapshot_model(), "rule": "nearest ERA5 cell at least half land; shore cells corrected (designs 0004, 0005)"},
        "staff": {"runs": staff, "note": "Non-cooling water per run: [core people, people per MW of IT capacity, gallons per person a day, share lost, maintenance gallons a day, maintenance gallons a day per MW, maintenance share lost]; "
                                         "added to the per_100mw results at the campus's size (scenario.flow, WQ.flow)"},
        "power": POWER,
        "pue_design": pue_design,
        "power_supply": POWER_SUPPLY,
        "home_customers": 4538056,   # EIA-861 2025, Michigan residential customers
        "size_examples": {"van_buren": it_t + it_d, "saline": saline_it},   # computing capacity of two proposals, from their contracts (MW)
        "home_kwh_month": 634.9,   # EIA-861 2025, Michigan (model 1.3; was 618.2 from EIA's 2024 Table 5A)
        "context": {**CONTEXT, "household_gpd": {"value": wateruse.home_gpd("MI"), "epa_family_gpd": HOUSEHOLD_GPD, "note": "USGS 2015 water to homes over ACS 2015 households; EPA WaterSense's figure for a family is more than 300 gallons a day", "sources": ["usgs_wu2015", "acs2015", "epa_watersense"]}},
        "county_uses_mgd": uses,
        "lake_source": lake_src,
        "county_golf_courses": n_golf,
        "golf": golf_stats,
        "tracker_muni": tracker_muni,
        "county_storms_in": storms,
        "region_meta": {k: {"name": r["name"], "station": r["station"]} for k, r in REGIONS.items()},
        "validation": validation,
        "sources": {k: {"citation": c, "url": u, "short": SHORT.get(k, k)} for k, (c, u) in SOURCES.items()},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(round_tree(data), f, separators=(",", ":"))
    print("wrote", OUT, os.path.getsize(OUT), "bytes")

