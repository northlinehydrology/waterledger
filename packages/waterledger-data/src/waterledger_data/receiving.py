"""Receiving waters in any state (national tier): which USGS watersheds (HUC12, HUC8) each place covers, a statewide table of
EPA ATTAINS impairments by HUC12 for site maps (placed with EPA's own assessment-unit-to-HUC12 crosswalk, so no state ID
convention is needed; Michigan's builder reads the HUC12 out of the unit ID instead), and the downstream path from any
HUC12, across state lines, through the watershed tracer (waterledger_data.trace). Cached under <cache>/receiving/."""
import collections, json, os

import geopandas as gpd

from waterledger_data.config import CACHE
from waterledger_data.places import _get
from waterledger_data.waters import ATTAINS, GROUPS, ORDER, WBD6

RAW = os.path.join(CACHE, "receiving")
WBD = WBD6.rsplit("/", 2)[0]                    # The National Map WBD MapServer
ALBERS = 5070


def _cached(name, fn):
    path = os.path.join(RAW, name)
    if not os.path.exists(path):
        os.makedirs(RAW, exist_ok=True)
        json.dump(fn(), open(path, "w"))
    return json.load(open(path))


def _paged(url, where, fields, order, page=2000, geometry=False):
    rows, off = [], 0
    while True:
        p = {"where": where, "outFields": fields, "returnGeometry": "true" if geometry else "false", "resultOffset": off,
             "resultRecordCount": page, "orderByFields": order, "f": "json"}
        if geometry:
            p.update(outSR=4326, maxAllowableOffset=0.0005, geometryPrecision=5)
        feats = _get(url, p, post=True).get("features", [])          # retries on timeouts
        rows += [{**f["attributes"], **({"rings": f["geometry"]["rings"]} if geometry and f.get("geometry") else {})} for f in feats]
        if len(feats) < page:
            return rows
        off += page


def organization(state):
    """The state's ATTAINS organization id and reporting cycle, e.g. ('21OHIO', 2024)."""
    def fetch():
        d = _get(f"{ATTAINS}/2/query", {"where": f"state='{state}' AND orgtype='State'", "outFields": "organizationid,reportingcycle",
                                        "returnDistinctValues": "true", "returnGeometry": "false", "f": "json"}, post=True)
        a = d["features"][0]["attributes"]
        return [a["organizationid"], a["reportingcycle"]]
    return tuple(_cached(f"{state}_org.json", fetch))


def huc12_links(state):
    """{huc12: {"huc12", "name", "tohuc"}} for every HUC12 touching the state."""
    rows = _cached(f"{state}_wbd_links.json", lambda: _paged(f"{WBD}/6/query", f"states LIKE '%{state}%'", "huc12,name,tohuc", "huc12", 500))
    return {r["huc12"]: r for r in rows}


def huc_polygons(state, level=12):
    """HUC12 (or HUC8) polygons touching the state, as a GeoDataFrame (huc, name, geometry)."""
    from waterledger_data.census import _polygon
    layer, field = {12: (6, "huc12"), 8: (4, "huc8")}[level]
    rows = _cached(f"{state}_wbd_huc{level}.json", lambda: _paged(f"{WBD}/{layer}/query", f"states LIKE '%{state}%'", f"{field},name",
                                                                   field, 500, geometry=True))
    g = gpd.GeoDataFrame([{"huc": r[field], "name": r["name"], "geometry": _polygon(r["rings"])} for r in rows if r.get("rings")],
                         geometry="geometry", crs=4326)
    return g[g.geometry.notna()].reset_index(drop=True)


def by_huc12(state):
    """Impairments of the assessed waters in each HUC12, with whether a TMDL covers each, and the downstream HUC12, in the
    format Water Ledger Michigan uses: {huc12: {"n": name, "t": tohuc, "a": assessed (0/1), "i": [[group, tmdl, waters]]}}."""
    org, cycle = organization(state)
    au_huc = _cached(f"{state}_attains_huc12.json", lambda: _paged(f"{ATTAINS}/7/query", f"organizationid='{org}'",
                                                                    "assessmentunitidentifier,huc12,isassessed", "OBJECTID"))
    params = _cached(f"{state}_attains_params.json", lambda: _paged(f"{ATTAINS}/8/query", f"organizationid='{org}'",
                                                                     "assessmentunitidentifier,parametergroupname,parameterstatus,parametercategorycode", "OBJECTID"))
    names = {}
    for layer in (0, 1, 2):
        for r in _cached(f"{state}_attains_names_{layer}.json", lambda layer=layer: _paged(
                f"{ATTAINS}/{layer}/query", f"organizationid='{org}'", "assessmentunitidentifier,assessmentunitname", "OBJECTID")):
            names[r["assessmentunitidentifier"]] = r["assessmentunitname"]
    hucs = collections.defaultdict(set)
    assessed = set()
    for r in au_huc:
        hucs[r["assessmentunitidentifier"]].add(r["huc12"])
        if r["isassessed"] == "Y":
            assessed.add(r["huc12"])
    found = collections.defaultdict(lambda: collections.defaultdict(lambda: {"tmdl": 0, "w": set()}))
    for r in params:
        if r["parameterstatus"] not in ("Cause", "Observed effect"):
            continue
        g = GROUPS.get(r["parametergroupname"])
        if not g:
            continue
        name = names.get(r["assessmentunitidentifier"]) or ""
        for h in hucs.get(r["assessmentunitidentifier"], ()):
            e = found[h][g]
            e["tmdl"] |= int(r["parametercategorycode"] == "4A")
            if name:
                e["w"].add(name.title() if name.isupper() else name)
    links = huc12_links(state)
    out = {}
    for h, L in links.items():
        rec = {"n": L["name"], "t": L["tohuc"] if L["tohuc"] in links else None, "a": int(h in assessed)}
        if h in found:
            rec["i"] = [[g, found[h][g]["tmdl"], sorted(found[h][g]["w"])[:3]] for g in ORDER if g in found[h]]
        out[h] = rec
    return out


def downstream(huc12, hops=100, network=None):
    """The HUC12s the water passes through from `huc12`, to the outlet and across state lines, with the impairments of the
    assessed waters in each: [{code, name, listings: [[group, tmdl, []]], assessed}], via the watershed tracer
    (waterledger_data.trace). `group` is one of waters.ORDER; `tmdl` is 1 when every unit listing that cause has a TMDL."""
    from waterledger_data.trace import ServiceNetwork, trace
    t = trace(huc12, "downstream", network or ServiceNetwork(), max_hops=hops)
    if t.path.empty:
        return []
    by_huc = collections.defaultdict(lambda: collections.defaultdict(list))
    if len(t.causes):
        c = t.causes.merge(t.waters[["assessmentunitidentifier", "huc12"]].drop_duplicates(), on="assessmentunitidentifier")
        for r in c.itertuples():
            g = GROUPS.get(r.parametergroupname)
            if g:
                by_huc[r.huc12][g].append(str(r.parametercategorycode).upper().startswith("4A"))
    assessed = set(t.waters.loc[t.waters["isassessed"] == "Y", "huc12"])
    return [{"code": r.huc12, "name": r.name, "assessed": r.huc12 in assessed,
             "listings": [[g, int(all(by_huc[r.huc12][g])), []] for g in ORDER if g in by_huc[r.huc12]]}
            for r in t.path.itertuples()]


def watersheds_by_place(state, places):
    """For each place, the HUC12s it covers (largest share first) and its HUC8: {geoid: {"h12": [{code, name, share}], "h8": {code, name}}}."""
    path = os.path.join(RAW, f"{state}_by_place.json")
    if os.path.exists(path):
        return json.load(open(path))
    import shapely
    pl = places[["geoid", "geometry"]].to_crs(ALBERS)
    pl["geometry"] = shapely.make_valid(pl.geometry.values)
    out = {}
    for level in (12, 8):
        hu = huc_polygons(state, level).to_crs(ALBERS)
        hu["geometry"] = shapely.make_valid(hu.geometry.values)
        pairs = gpd.sjoin(pl, hu, how="inner", predicate="intersects")
        gp = pl.set_index("geoid").geometry
        inter = shapely.intersection(gp.loc[pairs.geoid].values, hu.geometry.values[pairs.index_right.values])
        pairs["share"] = shapely.area(inter) / shapely.area(gp.loc[pairs.geoid].values)
        for r in pairs[pairs.share >= 0.01].sort_values("share", ascending=False).itertuples():
            e = out.setdefault(r.geoid, {"h12": [], "h8": None})
            if level == 12:
                e["h12"].append({"code": r.huc, "name": r.name, "share": round(float(r.share), 3)})
            elif e["h8"] is None:
                e["h8"] = {"code": r.huc, "name": r.name}
    os.makedirs(RAW, exist_ok=True)
    json.dump(out, open(path, "w"))
    return out
