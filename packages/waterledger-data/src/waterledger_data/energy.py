"""Electric utilities in any state (national tier): retail service territories (HIFLD, Oak Ridge National Laboratory; the
live copy is PNNL's, since HIFLD Open closed on Aug 26, 2025), joined to places by area; each utility's balancing
authority; and the water used at power plants per kWh there (Siddik et al. 2024, tables/grid_water_2022.csv). Sales,
customers and peaks come from EIA-861 by state (power.utility_loads). Cached under <cache>/energy/."""
import csv, json, os

import geopandas as gpd
import shapely

from waterledger_data.config import CACHE
from waterledger_data.places import _get

RAW = os.path.join(CACHE, "energy")
TERRITORIES = "https://eedgis.pnnl.gov/arcgis/rest/services/Hosted/Electric_Service_Territories/FeatureServer/0/query"
ALBERS = 5070
TABLE = os.path.join(os.path.dirname(__file__), "tables", "grid_water_2022.csv")

# HIFLD control area names -> EIA-930 balancing authority codes (as in the grid water table). Areas without a code in
# the table (New Brunswick, Hawaii, Alaska, OVEC, Electric Energy Inc., PowerSouth, New Smyrna Beach) map to None.
BALANCING_AUTHORITIES = {
    "MIDCONTINENT INDEPENDENT TRANSMISSION SYSTEM OPERATOR, INC..": "MISO", "SOUTHWEST POWER POOL": "SWPP",
    "PJM INTERCONNECTION, LLC": "PJM", "TENNESSEE VALLEY AUTHORITY": "TVA", "SOUTHERN COMPANY SERVICES, INC. - TRANS": "SOCO",
    "ELECTRIC RELIABILITY COUNCIL OF TEXAS, INC.": "ERCO", "BONNEVILLE POWER ADMINISTRATION": "BPAT", "ISO NEW ENGLAND INC.": "ISNE",
    "ASSOCIATED ELECTRIC COOPERATIVE, INC.": "AECI", "WESTERN AREA POWER ADMINISTRATION - ROCKY MOUNTAIN REGION": "WACM",
    "NEW YORK INDEPENDENT SYSTEM OPERATOR": "NYIS", "DUKE ENERGY PROGRESS EAST": "CPLE", "DUKE ENERGY CAROLINAS": "DUK",
    "PACIFICORP - EAST": "PACE", "CALIFORNIA INDEPENDENT SYSTEM OPERATOR": "CISO",
    "WESTERN AREA POWER ADMINISTRATION - DESERT SOUTHWEST REGION": "WALC", "PUBLIC SERVICE COMPANY OF COLORADO": "PSCO",
    "SOUTH CAROLINA PUBLIC SERVICE AUTHORITY": "SC", "PUBLIC SERVICE COMPANY OF NEW MEXICO": "PNM",
    "LOUISVILLE GAS AND ELECTRIC COMPANY AND KENTUCKY UTILITIES": "LGEE", "DUKE ENERGY FLORIDA INC": "FPC",
    "ARIZONA PUBLIC SERVICE COMPANY": "AZPS", "NEVADA POWER COMPANY": "NEVP", "NORTHWESTERN ENERGY (NWMT)": "NWMT",
    "FLORIDA MUNICIPAL POWER POOL": "FMPP", "AVISTA CORPORATION": "AVA", "SEMINOLE ELECTRIC COOPERATIVE": "SEC",
    "WESTERN AREA POWER ADMINISTRATION UGP WEST": "WAUW", "SOUTHWESTERN POWER ADMINISTRATION": "SPA",
    "BALANCING AUTHORITY OF NORTHERN CALIFORNIA": "BANC", "FLORIDA POWER & LIGHT COMPANY": "FPL",
    "SOUTH CAROLINA ELECTRIC & GAS COMPANY": "SCEG", "PUGET SOUND ENERGY": "PSEI", "LOS ANGELES DEPARTMENT OF WATER AND POWER": "LDWP",
    "PACIFICORP - WEST": "PACW", "IDAHO POWER COMPANY": "IPCO", "TAMPA ELECTRIC COMPANY": "TEC", "PUD NO. 1 OF DOUGLAS COUNTY": "DOPD",
    "CITY OF TACOMA, DEPARTMENT OF PUBLIC UTILITIES, LIGHT DIVISION": "TPWR", "PORTLAND GENERAL ELECTRIC COMPANY": "PGE",
    "SALT RIVER PROJECT": "SRP", "TUCSON ELECTRIC POWER COMPANY": "TEPC", "JEA": "JEA", "SOUTHEASTERN POWER ADMINISTRATION": "SEPA",
    "IMPERIAL IRRIGATION DISTRICT": "IID", "PUBLIC UTILITY DISTRICT NO. 2 OF GRANT COUNTY, WASHINGTON": "GCPD", "CITY OF HOMESTEAD": "HST",
    "TURLOCK IRRIGATION DISTRICT": "TIDC", "SEATTLE CITY LIGHT": "SCL", "PUBLIC UTILITY DISTRICT NO. 1 OF CHELAN COUNTY": "CHPD",
    "GAINESVILLE REGIONAL UTILITIES": "GVL", "CITY OF TALLAHASSEE": "TAL", "EL PASO ELECTRIC COMPANY": "EPE",
}


def grid_water():
    """{balancing authority: {"consumed_excl_hydro", "consumed_incl_hydro", "withdrawn_excl_hydro"} in L/kWh, 2022}."""
    return {r["ba"]: {"consumed_excl_hydro": float(r["consumed_l_per_kwh_excl_hydro"]), "consumed_incl_hydro": float(r["consumed_l_per_kwh_incl_hydro"]),
                      "withdrawn_excl_hydro": float(r["withdrawn_l_per_kwh_excl_hydro"])} for r in csv.DictReader(open(TABLE))}


def territories(state, bounds):
    """Retail service territories intersecting a state's bounding box (minx, miny, maxx, maxy), as a GeoDataFrame:
    eia_id, name, type, balancing_authority, geometry (WGS84)."""
    path = os.path.join(RAW, f"{state}_territories.json")
    if not os.path.exists(path):
        x0, y0, x1, y1 = bounds
        out, offset = [], 0
        while True:
            d = _get(TERRITORIES, {"where": "1=1", "geometry": f"{x0},{y0},{x1},{y1}", "geometryType": "esriGeometryEnvelope", "inSR": 4326,
                                   "spatialRel": "esriSpatialRelIntersects", "outFields": "id,name,type,cntrl_area,customers,year",
                                   "returnGeometry": "true", "outSR": 4326, "maxAllowableOffset": 0.001, "geometryPrecision": 5,
                                   "resultOffset": offset, "resultRecordCount": 200, "orderByFields": "objectid", "f": "json"}, post=True)
            feats = d.get("features", [])
            out += [{"a": f["attributes"], "rings": f["geometry"]["rings"]} for f in feats if f.get("geometry")]
            if len(feats) < 200 and not d.get("exceededTransferLimit"):
                break
            offset += len(feats)
        os.makedirs(RAW, exist_ok=True)
        json.dump(out, open(path, "w"))
    from waterledger_data.census import _polygon
    rows = [{"eia_id": int(f["a"]["id"]) if str(f["a"]["id"]).isdigit() else None, "name": f["a"]["name"], "type": f["a"]["type"],
             "balancing_authority": BALANCING_AUTHORITIES.get(f["a"]["cntrl_area"]), "geometry": _polygon(f["rings"])} for f in json.load(open(path))]
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=4326)
    return g[g.geometry.notna() & ~g.geometry.is_empty].reset_index(drop=True)


def utilities_by_place(state, places):
    """For each place, the utilities whose territory covers part of it, the largest share first:
    {geoid: [{eia_id, name, type, balancing_authority, share}]}; shares of at least 1% (territories overlap where utilities share
    ground, so shares can add to more than 1)."""
    path = os.path.join(RAW, f"{state}_by_place.json")
    if os.path.exists(path):
        return json.load(open(path))
    t = territories(state, tuple(places.total_bounds)).to_crs(ALBERS)
    t["geometry"] = shapely.make_valid(t.geometry.values)
    pl = places[["geoid", "geometry"]].to_crs(ALBERS)
    pl["geometry"] = shapely.make_valid(pl.geometry.values)
    pairs = gpd.sjoin(pl, t, how="inner", predicate="intersects")
    gp = pl.set_index("geoid").geometry
    inter = shapely.intersection(gp.loc[pairs.geoid].values, t.geometry.values[pairs.index_right.values])
    pairs["share"] = shapely.area(inter) / shapely.area(gp.loc[pairs.geoid].values)
    out = {}
    for r in pairs[pairs.share >= 0.01].sort_values("share", ascending=False).itertuples():
        ba = r.balancing_authority if isinstance(r.balancing_authority, str) else None      # pandas turns None into NaN
        out.setdefault(r.geoid, []).append({"eia_id": None if r.eia_id != r.eia_id else int(r.eia_id), "name": r.name, "type": r.type,
                                            "balancing_authority": ba, "share": round(float(r.share), 3)})
    os.makedirs(RAW, exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


def loads(state):
    """EIA-861 sales, customers and peaks by utility for a state ({eia_id: {...}}, power.utility_loads), downloading the newest
    year EIA has posted if none is cached."""
    import datetime

    from waterledger_data import power
    try:
        year = power.eia_year()
    except FileNotFoundError:
        year = None
        for y in range(datetime.date.today().year - 1, datetime.date.today().year - 4, -1):
            try:
                power.fetch_eia861(y)
                year = y
                break
            except Exception:
                continue
        if year is None:
            return {}
    return power.utility_loads(year, state)


def ranked(utilities, loads_):
    """A place's utilities in the order to show them: by EIA customers in the state (AEP Ohio before the City of Columbus's
    own small utility; Austin Energy before the cooperatives around it). HIFLD draws many territories as whole counties, so
    area shares overstate small utilities and are kept as "may serve", not as the share served."""
    cust = lambda u: (loads_.get(u["eia_id"]) or {}).get("customers") or 0
    return sorted(utilities, key=lambda u: -cust(u))
