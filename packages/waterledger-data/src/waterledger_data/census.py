"""Places in any state from the Census Bureau (TIGERweb), for the national tier (design 0001, decision 6; design 0002).

A state's places are the units that decide land use:
  incorporated places    cities, towns, villages and boroughs (FUNCSTAT A), and the balance of a consolidated city
                         (FUNCSTAT F, "Indianapolis city (balance)"): the land the consolidated government governs outside
                         the cities that keep their own (Louisville, Nashville, Augusta, Athens, Butte and Milford too)
  county subdivisions    only those the Census marks as active governments (FUNCSTAT A): the townships and towns of the
                         roughly 20 states that have them. Fictitious subdivisions (F) that repeat a city are skipped, as
                         are statistical (S) and nonfunctioning (N) ones such as Texas census county divisions and
                         Virginia magisterial districts.
  counties               every county, standing for the unincorporated land it governs. Independent cities (Virginia's,
                         Baltimore, St. Louis, Carson City) are county-equivalents too; they are listed once, as cities,
                         and still used to assign counties.

Each comes with its Census GEOID (7 digits for places, 10 for subdivisions, 5 for counties), name, kind (from the Census
name, e.g. "city", "charter township", "County"), internal point, county, and a generalized boundary. Responses are
cached under <cache>/census/.
"""
import hashlib
import json, os

import geopandas as gpd
import shapely

from waterledger_data.config import CACHE
from waterledger_data.places import TIGER, _get

RAW = os.path.join(CACHE, "census")
LAYERS = {"place": f"{TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/4/query",
          "cousub": f"{TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/1/query",
          "county": f"{TIGER}/State_County/MapServer/1/query"}
SIMPLIFY_DEG = 0.0003           # about 30 m: enough for joins with water systems and watersheds
# A state's places rule (design 0011): where a state's places are not the default above. Michigan's are its county subdivisions with land, its
# cities included: a Michigan city is also a county subdivision (LSAD 25), and Water Ledger Michigan has used those subdivision GEOIDs since
# October 2026 (public API: wl.place(geoid=...) and saved scenarios use them). Villages sit inside townships and are left out, as are counties
# (all of Michigan is in a city or township); both are a later question.
PLACE_RULES = {"26": {"cousub_lsad": ("25", "44", "49"), "places": False, "counties": False}}


def places_key(places):
    """A short key for a set of places, for caches worked out place by place: their GEOIDs and, where the frame has them, their outlines. A cache
    written for another set (Census places before 3.16.0 had no consolidated city balances) or for other outlines of the same places (Michigan's
    snapshot outlines before design 0011 against Census's) is not read for this one."""
    h = hashlib.sha256(",".join(sorted(str(g) for g in places.geoid)).encode())
    if "geometry" in places:
        for g, geom in sorted(zip(places.geoid.astype(str), places.geometry), key=lambda x: x[0]):
            h.update(shapely.to_wkb(geom) if geom is not None else b"-")
    return h.hexdigest()[:10]


def _features(kind, state_fips):
    """Every active feature of one layer in a state, with geometry in WGS84, paged and cached. The cache file is named for the query
    as well as the state and layer, so a query that changes (3.16.0 added consolidated cities' balances) fetches afresh instead of
    reading a file the old query wrote."""
    rule = PLACE_RULES.get(state_fips, {})
    where = f"STATE='{state_fips}'" + {"county": "", "cousub": (" AND LSADC IN (" + ",".join(f"'{c}'" for c in rule["cousub_lsad"]) + ") AND AREALAND>0"
                                                                 if "cousub_lsad" in rule else " AND FUNCSTAT='A'"),
                                       "place": " AND (FUNCSTAT='A' OR (FUNCSTAT='F' AND NAME LIKE '%(balance)'))"}[kind]
    params = {"where": where, "outFields": "GEOID,NAME,BASENAME,LSADC,FUNCSTAT,INTPTLAT,INTPTLON", "returnGeometry": "true", "outSR": 4326,
              "maxAllowableOffset": SIMPLIFY_DEG, "geometryPrecision": 5, "orderByFields": "GEOID", "f": "json"}
    key = hashlib.sha256(json.dumps([LAYERS[kind], params], sort_keys=True).encode()).hexdigest()[:10]
    path = os.path.join(RAW, f"{state_fips}_{kind}_{key}.json")
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    out, offset = [], 0
    while True:
        d = _get(LAYERS[kind], {**params, "resultOffset": offset, "resultRecordCount": 500}, post=True)
        feats = d.get("features", [])
        out += [{"a": f["attributes"], "rings": f["geometry"]["rings"]} for f in feats if f.get("geometry")]
        if len(feats) < 500 and not d.get("exceededTransferLimit"):
            break
        offset += len(feats)
    os.makedirs(RAW, exist_ok=True)
    json.dump(out, open(path, "w", encoding="utf-8"))
    return out


TREE_RINGS = 64     # above this many rings, combine them pairwise in a balanced tree: one at a time costs the square of the count, and a Great
                    # Lakes shore HUC12 has 23,000 island rings (about an hour each, 7.4 hours for Michigan's watersheds; design 0011, Nov 25, 2026)


def _xor(parts):
    if len(parts) == 1:
        return parts[0]
    mid = len(parts) // 2
    return _xor(parts[:mid]).symmetric_difference(_xor(parts[mid:]))


def _polygon(rings):
    """Census (or WBD) rings as one shapely geometry, even-odd (holes and separate parts), cleaned of any self-intersection."""
    parts = [shapely.make_valid(shapely.Polygon(r)) for r in rings if len(r) >= 4]
    if not parts:
        return None
    if len(parts) > TREE_RINGS:
        return _xor(parts)
    geom = parts[0]
    for p in parts[1:]:
        geom = geom.symmetric_difference(p)
    return geom


def _base_kind(a):
    """(base name, kind). A consolidated city's balance carries its whole name as its base ("Indianapolis city (balance)"):
    its base is the name before "city" ("Indianapolis") and its kind city, or the whole name before "(balance)" and kind
    consolidated government where no "city" ends it (Louisville/Jefferson County metro government)."""
    base, name = a["BASENAME"], a["NAME"]
    if name.endswith(" (balance)"):
        whole = name.removesuffix(" (balance)")
        return (whole.removesuffix(" city"), "city") if whole.endswith(" city") else (whole, "consolidated government")
    return base, name[len(base):].strip() if name.startswith(base) else name


def places(state_fips):
    """A state's places (by its PLACE_RULES entry where it has one) as a GeoDataFrame: geoid, name (as Census writes it), base, kind, level (place, township or county),
    county and county_fips (for places and townships, the county holding the internal point), lat, lon, geometry (WGS84)."""
    rows = []
    rule = PLACE_RULES.get(state_fips, {})
    for kind in ("place", "cousub", "county"):
        if kind == "place" and rule.get("places") is False:
            continue
        for f in _features(kind, state_fips):
            a = f["a"]
            base, kind_ = _base_kind(a)
            rows.append({"geoid": a["GEOID"], "name": a["NAME"], "base": base, "kind": kind_,
                         "level": {"place": "place", "cousub": "township", "county": "county"}[kind],
                         "lat": float(a["INTPTLAT"]), "lon": float(a["INTPTLON"]), "geometry": _polygon(f["rings"])})
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=4326)
    counties = g[g.level == "county"][["geoid", "base", "geometry"]].rename(columns={"geoid": "county_fips", "base": "county"})
    pts = gpd.GeoDataFrame(g[["geoid"]], geometry=gpd.points_from_xy(g.lon, g.lat), crs=4326)
    hit = gpd.sjoin(pts, counties, how="left", predicate="within").drop_duplicates("geoid").set_index("geoid")
    g["county"] = g.geoid.map(hit["county"])
    g["county_fips"] = g.geoid.map(hit["county_fips"])
    is_county = g.level == "county"
    g.loc[is_county, "county"] = g.loc[is_county, "base"]
    g.loc[is_county, "county_fips"] = g.loc[is_county, "geoid"]
    g = g[~(is_county & (g.kind.str.lower() == "city"))]          # independent cities: already listed as places
    if rule.get("counties") is False:                              # used to assign counties, not listed (PLACE_RULES)
        g = g[~is_county.loc[g.index]]
    return g.sort_values(["name", "county"]).reset_index(drop=True)


def state_at(lat, lon):
    """The state FIPS code at a point (Census counties layer), or None offshore or outside the U.S."""
    d = _get(LAYERS["county"], {"geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": 4326,
                                "spatialRel": "esriSpatialRelIntersects", "outFields": "STATE", "returnGeometry": "false", "f": "json"})
    f = d.get("features", [])
    return f[0]["attributes"]["STATE"] if f else None


def place_at(lat, lon, state_fips=None):
    """The GEOID of the most local government at a point: a city, town or village if the point is in one, else a township
    where townships govern, else the county."""
    state_fips = state_fips or state_at(lat, lon)
    if state_fips is None:
        return None
    g = places(state_fips)
    hit = g[g.contains(shapely.Point(lon, lat))]
    if not len(hit):
        return None
    rank = {"place": 0, "township": 1, "county": 2}
    return hit.assign(r=hit.level.map(rank)).sort_values("r").iloc[0].geoid
