"""Which places are in the areas a state's water rules name, where those areas don't follow county lines: waterledger/rules/<st>_areas.json.

    uv run python tools/rule_areas.py az va tx pa [--cache DIR]

A rule can apply only inside an area drawn on something other than counties: Arizona's Active Management Areas (groundwater basins), Virginia's Eastern
Virginia Groundwater Management Area (whole counties and cities, and the parts of eight counties east of Interstate 95), Texas's groundwater
conservation districts, Pennsylvania's Southeastern Ground Water Protected Area. For each, this reads the official boundary, every place's Census
outline (counties, incorporated places and county subdivisions, TIGERweb, generalized), and the share of each place's area inside the area, measured
in an equal-area projection (EPSG:5070). A place is "in" at 95% or more and "part" from 5%; under 5% it is left out. The rules file's lines name the
group (`areas = ["ama"]`), and a place partly inside sees both rules, the one inside and the one outside (levels.withdrawal_both).

Nothing here changes an estimate. Rerun when an area or a boundary file changes; the output records each source and the date it was read.
"""
import argparse, datetime, io, json, os, re, sys, urllib.parse, urllib.request, zipfile

import geopandas as gpd
import pandas as pd
import shapely
from shapely.geometry import LineString, MultiLineString, shape
from shapely.ops import split, unary_union

UA = "waterledger-rule-areas/1.0 (+https://github.com/northlinehydrology/waterledger)"
TIGER = "https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb"
OUT = os.path.join(os.path.dirname(__file__), "..", "packages", "waterledger", "src", "waterledger", "rules")
IN, PART = 0.95, 0.05
FIPS = {"az": "04", "va": "51", "tx": "48", "pa": "42"}
SOURCES = {
    "adwr_ama_ina": ("ADWR Active Management Areas and Irrigation Non-Expansion Areas (AMA_INA_2024)", "Arizona Department of Water Resources",
                     "https://services.arcgis.com/C34zQ7veRS0V1t04/arcgis/rest/services/AMA_INA_2024/FeatureServer/0"),
    "twdb_gcd": ("Groundwater Conservation Districts of Texas (TWDB_GCD_NOV2019; boundaries approximate)", "Texas Water Development Board",
                 "https://www.twdb.texas.gov/mapping/gisdata/doc/GCD_Shapefiles.zip"),
    "drbc_gwpa": ("Southeastern Pennsylvania Ground Water Protected Area boundary (sepa_gwpa_bnd)", "Delaware River Basin Commission",
                  "https://nj.gov/drbc/library/documents/GIS/gwpabnd.zip"),
    "tiger_counties": ("TIGERweb counties", "U.S. Census Bureau", f"{TIGER}/State_County/MapServer/1"),
    "tiger_i95": ("TIGERweb primary roads (Interstate 95)", "U.S. Census Bureau", f"{TIGER}/Transportation/MapServer/2"),
}


def _get(url, cache, name, binary=False):
    p = os.path.join(cache, name)
    if not os.path.exists(p):
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=180) as r:
            open(p, "wb").write(r.read())
    return open(p, "rb").read() if binary else json.load(open(p))


def _arcgis(layer, where, cache, name, fields="*", offset=0.0005):
    """Every feature of an ArcGIS layer as a GeoDataFrame in EPSG:4326, paged."""
    feats, start = [], 0
    while True:
        q = urllib.parse.urlencode({"where": where, "outFields": fields, "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": offset,
                                    "geometryPrecision": 5, "resultOffset": start, "resultRecordCount": 1000, "f": "geojson"})
        d = _get(f"{layer}/query?{q}", cache, f"{name}_{start}.json")
        feats += d.get("features", [])
        if len(d.get("features", [])) < 1000:
            break
        start += 1000
    g = gpd.GeoDataFrame.from_features(feats, crs=4326)
    if len(g) and g.geom_type.isin(["Polygon", "MultiPolygon"]).any():
        g["geometry"] = shapely.make_valid(g.geometry.values)          # generalized outlines can self-touch
    return g


def _zip_shp(url, cache, name):
    z = zipfile.ZipFile(io.BytesIO(_get(url, cache, name, binary=True)))
    d = os.path.join(cache, name + "_x")
    z.extractall(d)
    shp = [os.path.join(r, f) for r, _, fs in os.walk(d) for f in fs if f.endswith(".shp")][0]
    g = gpd.read_file(shp).to_crs(4326)
    g["geometry"] = shapely.make_valid(g.geometry.values)
    return g


def places(st, cache):
    """Counties, incorporated places and county subdivisions with their GEOIDs, as Water Ledger keys them."""
    f = FIPS[st]
    c = _arcgis(f"{TIGER}/State_County/MapServer/1", f"STATE='{f}'", cache, f"{st}_counties", "GEOID,NAME")
    p = _arcgis(f"{TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/4", f"STATE='{f}'", cache, f"{st}_places", "GEOID,NAME")
    s = _arcgis(f"{TIGER}/Places_CouSub_ConCity_SubMCD/MapServer/1", f"STATE='{f}'", cache, f"{st}_cousubs", "GEOID,NAME")
    return pd.concat([c, p, s], ignore_index=True)[["GEOID", "NAME", "geometry"]]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def areas_az(cache):
    d = _arcgis(SOURCES["adwr_ama_ina"][2], "1=1", cache, "az_ama_ina", "BASIN_NAME")
    out = []
    for _, r in d.iterrows():
        n = r["BASIN_NAME"].strip().title().replace("Ama", "Active Management Area").replace("Ina", "Irrigation Non-Expansion Area")
        out.append(("ama" if r["BASIN_NAME"].strip().endswith("AMA") else "ina", n, r.geometry, "adwr_ama_ina"))
    return out


def areas_tx(cache):
    d = _zip_shp(SOURCES["twdb_gcd"][2], cache, "tx_gcd.zip")
    return [("gcd", r["DISTNAME"].title().replace("Gcd", "GCD"), r.geometry, "twdb_gcd") for _, r in d[d["CSTATUS"] == "C"].iterrows()]


def areas_pa(cache):
    d = _zip_shp(SOURCES["drbc_gwpa"][2], cache, "pa_gwpa.zip")
    return [("sepa_gwpa", "Southeastern Pennsylvania Ground Water Protected Area", unary_union(d.geometry), "drbc_gwpa")]


# 9VAC25-600-20(A): the Eastern Virginia Groundwater Management Area
VA_WHOLE = ["51036", "51057", "51073", "51093", "51095", "51099", "51097", "51101", "51103", "51115", "51119", "51127", "51133", "51149", "51159", "51175",
            "51181", "51183", "51193", "51199", "51550", "51620", "51650", "51670", "51700", "51710", "51735", "51740", "51800", "51810", "51830"]
VA_EAST_OF_I95 = ["51033", "51041", "51059", "51085", "51087", "51153", "51177", "51179"]   # Caroline, Chesterfield, Fairfax, Hanover, Henrico, Prince William, Spotsylvania, Stafford
VA_SHORE = ["51001", "51131"]                                                                 # 9VAC25-600-20(B): Accomack, Northampton


def areas_va(cache):
    c = _arcgis(SOURCES["tiger_counties"][2], "STATE='51'", cache, "va_counties", "GEOID,NAME").set_index("GEOID")
    r = _arcgis(SOURCES["tiger_i95"][2], "RTTYP='I' AND BASENAME='95'", cache, "i95", "BASENAME", offset=0.0001)
    i95 = unary_union(list(r.geometry))
    east = []
    for g in VA_EAST_OF_I95:
        poly = c.loc[g, "geometry"]
        line = i95.intersection(poly.buffer(0.05))
        if line.is_empty:
            raise SystemExit(f"Interstate 95 not found across county {g}: check the TIGERweb query")
        for piece in split(poly, line).geoms:
            p = piece.representative_point()
            # east of the line: the nearest point on I-95 lies to the west of the piece's interior point
            near = shapely.ops.nearest_points(i95, p)[0]
            if p.x > near.x:
                east.append(piece)
    gwma = unary_union([c.loc[g, "geometry"] for g in VA_WHOLE] + east)
    shore = unary_union([c.loc[g, "geometry"] for g in VA_SHORE])
    return [("gwma", "Eastern Virginia Groundwater Management Area", gwma, "tiger_counties"),
            ("gwma", "Eastern Shore Groundwater Management Area", shore, "tiger_counties")]


def membership(pl, areas):
    """{geoid: {group: {"share": s, "names": [...]}}}: each place's share of area inside each group's areas, 5% and up."""
    P = pl.to_crs(5070)
    P["geometry"] = shapely.make_valid(P.geometry.values)               # generalized outlines can self-touch
    P["a"] = P.geometry.area
    out = {}
    for group in sorted({a[0] for a in areas}):
        polys = [(n, shapely.make_valid(gpd.GeoSeries([g], crs=4326).to_crs(5070).iloc[0])) for k, n, g, _ in areas if k == group]
        union = unary_union([g for _, g in polys])
        idx = P.sindex.query(union, predicate="intersects")
        for i in idx:
            row = P.iloc[i]
            if row["a"] <= 0:
                continue
            share = row.geometry.intersection(union).area / row["a"]
            if share < PART:
                continue
            names = [n for n, g in polys if row.geometry.intersection(g).area / row["a"] >= PART]
            out.setdefault(row["GEOID"], {})[group] = {"share": round(min(share, 1.0), 3), "names": names}
    return out


def build(st, cache):
    os.makedirs(cache, exist_ok=True)
    areas = {"az": areas_az, "va": areas_va, "tx": areas_tx, "pa": areas_pa}[st](cache)
    m = membership(places(st, cache), areas)
    used = sorted({a[3] for a in areas} | ({"tiger_i95"} if st == "va" else set()))
    doc = {"state": st.upper(), "read": datetime.date.today().isoformat(), "in": IN, "part": PART,
           "groups": {g: sorted({n for k, n, _, _ in areas if k == g}) for g in sorted({a[0] for a in areas})},
           "sources": {k: dict(zip(("title", "publisher", "url"), SOURCES[k])) for k in used},
           "places": dict(sorted(m.items()))}
    p = os.path.join(OUT, f"{st}_areas.json")
    json.dump(doc, open(p, "w"), indent=0, sort_keys=False, ensure_ascii=False)
    n_in = sum(1 for v in m.values() for x in v.values() if x["share"] >= IN)
    print(f"{st.upper()}: {len(m)} places in an area ({n_in} wholly), groups {list(doc['groups'])} -> {os.path.relpath(p)}")


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("states", nargs="+")
    a.add_argument("--cache", default=os.path.join(os.path.dirname(__file__), "..", ".cache", "rule_areas"))
    o = a.parse_args()
    for st in o.states:
        build(st.lower(), o.cache)
