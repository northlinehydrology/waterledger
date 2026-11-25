"""A state's own layers on the national base (design 0011). Every state is built by one builder from national sources; a state can add a
layer of its own that either adds something the base doesn't have (household wells, trout streams) or replaces the base for that state where
its own source measures better (MPSC's utility territories, Michigan's reading of EGLE's assessment units, Michigan's salt regions). Each is
registered here by state and category, written into the state's snapshot (layers.json, listed in its manifest), and read by the national
provider wherever a snapshot has it; nothing in the provider asks which state it is.

Two layers are registered where their kind of data already lives: county water use (wateruse.STATE_LAYERS) and the golf course figure
(wateruse.GOLF). describe() lists them with the rest.

    layers.for_state("MI")             the state's layers: [Layer(category, mode, sources, note)]
    layers.build("MI", places)         {category: data} for the snapshot
    layers.describe("MI")              the manifest's "layers": [{category, mode, sources, note}]

Formats (keys are the base's: GEOIDs for places, HUC12 codes for reaches):
    household_wells      {geoid: {drift_n, drift_depth_ft, drift_level_ft, rock_n, rock_depth_ft, rock_level_ft}}
    coldwater_streams    {huc12: [stream names]}
    impairments          {huc12: {"assessed": bool, "listings": [[group, tmdl 0/1, [waters]]]}}
    utilities            {geoid: [{eia_id, name, type, share, balancing_authority, order}]}, in the order to show them
    salt_regions         {"regions": {id: {name, station, salt_days}}, "places": {geoid: id}}
"""
import dataclasses
import math

from waterledger_data.config import CACHE  # noqa: F401  (the sources below cache under it)


@dataclasses.dataclass(frozen=True)
class Layer:
    category: str
    mode: str                  # "adds" or "replaces"
    sources: tuple
    note: str
    build: object = None       # build(places) -> data; None where the layer lives elsewhere (water use, golf)


# ---------------------------------------------------------------------------------------------------------------------------------- Michigan

# Michigan's road-salt regions: groups of counties, each county in the region whose point is nearest its own, with one long-record NOAA
# station each. Kept over NOAA's climate divisions (design 0011, measured Nov 9 and Nov 25, 2026): closer at 274 places to 137, with the
# eastern Upper Peninsula split off on NOAA division 2's station (Pellston), which misses the held-out stations there by 12.0 days against
# the old Upper Peninsula region's 28.0.
MI_REGIONS = {
    "southeast": {"name": "Southeast Michigan", "station": "Ann Arbor area", "lat": 42.25, "lon": -83.60},
    "southwest": {"name": "Southwest Michigan", "station": "Kalamazoo area", "lat": 42.29, "lon": -85.59},
    "west": {"name": "West Michigan", "station": "Grand Rapids area", "lat": 42.88, "lon": -85.52, "cache": "gaines"},
    "central": {"name": "Central Michigan", "station": "Lansing area", "lat": 42.73, "lon": -84.55},
    "thumb": {"name": "Saginaw Valley and the Thumb", "station": "Saginaw area", "lat": 43.42, "lon": -83.95},
    "north": {"name": "Northwest Michigan", "station": "Traverse City area", "lat": 44.76, "lon": -85.62},
    "northeast": {"name": "Northeast Michigan", "station": "Alpena area", "lat": 45.06, "lon": -83.43},
    "up": {"name": "Central and Western Upper Peninsula", "station": "Marquette area", "lat": 46.54, "lon": -87.40},
}
MI_EASTERN_UP = {"id": "eup", "name": "Eastern Upper Peninsula", "station": "Pellston area", "division": "2002"}
# Median winter's days with precipitation at 1 C or below, by region, from NOAA ISD-Lite 2005-2024 (the national method,
# waterledger.national.climate._median_cold_precip_days): Ann Arbor 725374-94889, Kalamazoo 726357-94815, Grand Rapids 726350-94860, Lansing
# 725390-14836, Saginaw 726379-14845, Traverse City 726387-14850, Alpena 726390-94849, Hancock 727440-14858 for the Upper Peninsula, and
# Pellston 727347-14841 (NOAA division 2's station) for the eastern Upper Peninsula; a live test recomputes them.
MI_SALT_DAYS = {"southeast": 59, "southwest": 64, "west": 72, "central": 71, "thumb": 64, "north": 89, "northeast": 88, "up": 119, "eup": 93}


def mi_nearest_region(lat, lon):
    """The Michigan region whose point is nearest (lat, lon), by the same flat distance Michigan's builder has used."""
    return min(MI_REGIONS, key=lambda k: (lat - MI_REGIONS[k]["lat"]) ** 2 + ((lon - MI_REGIONS[k]["lon"]) * math.cos(math.radians(lat))) ** 2)


def mi_county_regions(counties):
    """{county FIPS: region id} from counties [{geoid, lat, lon}]: the nearest region's, or the eastern Upper Peninsula for NOAA division 2's
    counties."""
    from waterledger_data import divisions
    cd = divisions.county_divisions()
    return {c["geoid"]: MI_EASTERN_UP["id"] if cd.get(c["geoid"]) == MI_EASTERN_UP["division"] else mi_nearest_region(c["lat"], c["lon"])
            for c in counties}


def mi_salt_regions(places):
    from waterledger_data import places as pl
    regions = mi_county_regions(pl.counties())
    meta = {k: {"name": r["name"], "station": r["station"], "salt_days": MI_SALT_DAYS[k]} for k, r in MI_REGIONS.items()}
    meta[MI_EASTERN_UP["id"]] = {"name": MI_EASTERN_UP["name"], "station": MI_EASTERN_UP["station"], "salt_days": MI_SALT_DAYS[MI_EASTERN_UP["id"]]}
    return {"regions": meta, "places": {r.geoid: regions[r.county_fips] for r in places.itertuples() if r.county_fips in regions}}


def mi_household_wells(places):
    """EGLE Wellogic household wells by township, matched to places as Michigan's builder has matched them (county and name stem)."""
    from waterledger_data import waters as wi
    HW, out = wi.household_wells(), {}
    for r in places.itertuples():
        w = HW.get((r.county, wi.place_stem(r.name)))
        if w:
            d, k = w.get("drift", {}), w.get("rock", {})
            out[r.geoid] = {"drift_n": d.get("n", 0), "drift_depth_ft": d.get("depth"), "drift_level_ft": d.get("swl"),
                            "rock_n": k.get("n", 0), "rock_depth_ft": k.get("depth"), "rock_level_ft": k.get("swl")}
    return out


def mi_coldwater_streams(places=None):
    from waterledger_data import waters as wi
    return {h: v["names"] for h, v in wi.trout_by_huc12().items()}


def mi_impairments(places=None):
    """EGLE's 2026 assessment units, each in its own HUC12 (waters.by_huc12, Michigan's recodes): replaces the base's EPA table, which links a
    unit to every HUC12 its catchments touch (design 0011, measured Nov 25, 2026)."""
    from waterledger_data import waters as wi
    return {h: {"assessed": bool(v.get("a")), "listings": v.get("i", [])} for h, v in wi.by_huc12().items()}


def _rings(geom):
    polys = getattr(geom, "geoms", [geom])
    return [[list(c) for c in ring.coords] for p in polys for ring in [p.exterior, *p.interiors]]


def mi_utilities(places):
    """MPSC's territories (measured: the place's top utility lists its county in EIA-861 at 1,540 of 1,540 places, against HIFLD's 837 agreeing
    with MPSC), each with its share of the place, largest first, and the base's balancing authority rule: HIFLD's control area for the
    utility, else the one RTO EIA-861 lists (it gives the seven PJM utilities Michigan's hand list had)."""
    from waterledger_data import energy, power as pw
    T = pw.territories()
    H = energy.territories("MI", tuple(places.total_bounds))
    rto = pw.utility_rtos()
    ba = {}
    for name, eid in pw.EIA_ID.items():
        hit = H[H.eia_id == eid].balancing_authority.dropna()
        ba[name] = hit.iloc[0] if len(hit) else rto.get(eid)
    kind = {q["name"]: q["type"] for q in T}
    out = {}
    for r in places.itertuples():
        if r.geometry is None:
            continue
        us = pw.place_utilities(_rings(r.geometry), T)
        out[r.geoid] = [{"eia_id": pw.EIA_ID.get(n), "name": n, "type": kind.get(n), "share": sh, "balancing_authority": ba.get(n), "order": i}
                        for i, (sh, n) in enumerate(us)]
    return out


REGISTRY = {
    "MI": [
        Layer("household_wells", "adds", ("wellogic",), "EGLE Wellogic household wells by township: aquifer, depth and water level.", mi_household_wells),
        Layer("coldwater_streams", "adds", ("mdnr_trout",), "Michigan DNR designated trout streams by HUC12.", mi_coldwater_streams),
        Layer("impairments", "replaces", ("attains2026",), "EGLE's 2026 assessment units placed in their own HUC12, in place of EPA's table, which links "
              "a unit to every HUC12 its catchments touch.", mi_impairments),
        Layer("utilities", "replaces", ("mpsc_territory",), "MPSC service territories in place of HIFLD's (1,540 of 1,540 places' top utility lists the "
              "county in EIA-861; HIFLD agrees with MPSC at 837).", mi_utilities),
        Layer("salt_regions", "replaces", ("noaa_isd",), "Michigan's eight road-salt regions, with the eastern Upper Peninsula on NOAA division 2's "
              "station, in place of NOAA's climate divisions (closer at more places).", mi_salt_regions),
    ],
}


# the source id of each state's county water-use layer (wateruse.STATE_LAYERS), as its basis names it
WATER_USE_SOURCES = {"MI": "egle2025", "OH": "odnr_wwfr", "TX": "twdb_wus", "VA": "va_deq_awrr"}


def for_state(state):
    return list(REGISTRY.get(state.upper(), []))


def build(state, places):
    """{category: data} for every layer of `state` that a snapshot carries."""
    return {L.category: L.build(places) for L in for_state(state) if L.build}


def describe(state):
    """The manifest's list of a state's layers, the water-use and golf layers included."""
    from waterledger_data import wateruse
    out = [{"category": L.category, "mode": L.mode, "sources": list(L.sources), "note": L.note} for L in for_state(state)]
    st = state.upper()
    if st in wateruse.STATE_LAYERS:
        out.append({"category": "county_water_use", "mode": "replaces", "sources": [WATER_USE_SOURCES[st]], "note": "The state's own county figures, in place of USGS's 2015 estimates."})
    if st in wateruse.GOLF and wateruse.GOLF[st].get("basis") == "state reports":
        out.append({"category": "golf", "mode": "replaces", "sources": wateruse.GOLF[st]["sources"], "note": "The median course the state's reports give, in place of the regional survey."})
    return out
