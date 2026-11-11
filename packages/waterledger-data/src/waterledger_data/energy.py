"""Electric utilities in any state (national tier): retail service territories (HIFLD, Oak Ridge National Laboratory; the
live copy is PNNL's, since HIFLD Open closed on Aug 26, 2025), joined to places by area; each utility's balancing
authority; and the water used at power plants per kWh there (Siddik et al. 2024, tables/grid_water_2022.csv). Sales,
customers and peaks come from EIA-861 by state (power.utility_loads). Cached under <cache>/energy/."""
import csv, json, os, re

import geopandas as gpd
import shapely

from waterledger_data.config import CACHE
from waterledger_data.places import _get

RAW = os.path.join(CACHE, "energy")
TERRITORIES = "https://eedgis.pnnl.gov/arcgis/rest/services/Hosted/Electric_Service_Territories/FeatureServer/0/query"
ALBERS = 5070
TABLE = os.path.join(os.path.dirname(__file__), "tables", "grid_water_2022.csv")
STATE_TABLE = os.path.join(os.path.dirname(__file__), "tables", "state_power_water_2024.csv")
FUEL_TABLE = os.path.join(os.path.dirname(__file__), "tables", "state_fuel_water_2024.csv")

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


L_KWH_TO_GAL_MWH = 1000 / 3.785411784
# Natural gas combined cycle with cooling towers: Macknick et al. 2012, Table 2 consumption, Table 3 withdrawal; a technology, not a state's mix
NEW_GAS = {"label": "Gas plants", "gal_mwh": 205, "lo": 130, "hi": 300, "wd_gal_mwh": 255, "wd_lo": 150, "wd_hi": 283, "sources": ["macknick2012"],
           "note": "Natural gas combined cycle with cooling towers"}


def pv_share(state=None):
    """PV's share of wind and solar generation in 2024: a state's own, from EIA, for any state in the table with either. A state with neither has no mix of
    its own, and takes the U.S. share, the only figure that favors no state (None asks for it directly)."""
    rows = list(csv.DictReader(open(STATE_TABLE)))
    for r in rows:
        if r["state"] == state and r["pv_share_of_wind_solar"]:
            return float(r["pv_share_of_wind_solar"])
    solar = sum(float(r["solar_share"] or 0) * float(r["net_gen_mwh"]) for r in rows)
    wind = sum(float(r["wind_share"] or 0) * float(r["net_gen_mwh"]) for r in rows)
    return solar / (solar + wind)


def wind_solar(pv_share):
    """The 'wind and solar' option weighted by a state's own 2024 wind and solar generation (pv_share = PV's share of the two):
    Macknick et al. 2012, wind 0 and PV 1 (0 to 5) gal/MWh, withdrawal equal to consumption."""
    g = lambda v: round(pv_share * v, 2)
    return {"label": "Wind and solar", "gal_mwh": g(1), "lo": 0, "hi": g(5), "wd_gal_mwh": g(1), "wd_lo": 0, "wd_hi": g(5),
            "sources": ["macknick2012", "eia_sep2024"], "note": f"Wind 0 and utility solar about 1 (0 to 5) for panel washing, weighted by the state's 2024 wind and solar generation (PV {round(100 * pv_share)}%)"}


def withdrawal_split(wd_gal_mwh, saline_gal_mwh):
    """A power option's withdrawal split into whole gallons of fresh and saline water that add back to it."""
    saline = min(round(saline_gal_mwh), wd_gal_mwh)
    return {"wd_fresh_gal_mwh": wd_gal_mwh - saline, "wd_saline_gal_mwh": saline}


COOLING_WORDS = (("once", "once-through"), ("tower", "towers"), ("pond", "cooling reservoirs"), ("dry", "dry"))


def fuel_options(state, name):
    """A state's coal and nuclear plants as power options, for each it has: Macknick et al. 2012 factors for how they are cooled (EIA-860, by water body), weighted by
    their 2024 generation (docs/methods/power_water/fuels.py). {"coal": factors, "nuclear": factors}, without a fuel the state did not generate with in 2024."""
    out = {}
    for r in csv.DictReader(open(FUEL_TABLE)):
        if r["state"] != state:
            continue
        g, fuel = lambda k: round(float(r[k])), r["fuel"]
        wd = g("withdrawn_gal_mwh")
        how = ", ".join(f"{round(100 * float(r['share_' + k]))}% {w}" for k, w in COOLING_WORDS if round(100 * float(r["share_" + k])))
        out[r["fuel"]] = {"label": f"{name}'s {fuel} plants", "gal_mwh": g("consumed_gal_mwh"), "lo": g("consumed_lo"), "hi": g("consumed_hi"),
                          "wd_gal_mwh": wd, "wd_lo": g("withdrawn_lo"), "wd_hi": g("withdrawn_hi"), **withdrawal_split(wd, wd * float(r["saline_share"])),
                          "sources": ["macknick2012", "eia923_2024"],
                          "note": f"Macknick factors for how {name}'s {fuel} plants are cooled, weighted by 2024 generation: {how}"}
    return out


BA_FUEL_TABLE = os.path.join(os.path.dirname(__file__), "tables", "ba_fuel_water_2024.csv")


def ba_fuel_water(ba):
    """Water at power plants per MWh by EIA-930 fuel class and month in a balancing authority, 2024 (design 0008; built by
    docs/methods/power_water/ba_fuels.py): {fuel: {"consumed", "withdrawn", "withdrawn_saline"}} of 12 monthly gal/MWh
    arrays, January first. A class the BA doesn't generate takes the U.S. factor; one with no water (hydro, solar, wind,
    storage) is zero. None for a BA not in the table (Alaska and Hawaii have none in EIA-930)."""
    import numpy as np
    rows = list(csv.DictReader(open(BA_FUEL_TABLE)))
    us = {r["fuel"]: r for r in rows if r["ba"] == "US"}
    mine = [r for r in rows if r["ba"] == ba]
    if not mine:
        return None
    zero = {"consumed_gal_mwh": "0", "withdrawn_gal_mwh": "0", "withdrawn_saline_gal_mwh": "0"}
    out = {}
    for fuel in ("coal", "gas", "nuclear", "oil", "hydro", "solar", "wind", "geothermal", "storage", "other", "unknown"):
        by_m = {int(r["month"]): r for r in mine if r["fuel"] == fuel and r["consumed_gal_mwh"] != ""}
        src = [by_m.get(m) or us.get("other" if fuel == "unknown" else fuel) or zero for m in range(1, 13)]
        out[fuel] = {k: np.array([float(s[f"{k}_gal_mwh"]) for s in src]) for k in ("consumed", "withdrawn", "withdrawn_saline")}
    return out


def state_power_water(state):
    """Water at power plants per kWh of electricity used in a state, 2024, from plant-reported data (EIA-923 cooling water and
    EIA-860, flagged reports replaced by Macknick et al. 2012 medians, blended with the main balancing authority by the state's
    net import share, then updated with the 2022 plant reports and Siddik et al. 2024 on the same basis; docs/methods/power_water): {"consumed", "consumed_lo", "consumed_hi", "withdrawn", "withdrawn_lo",
    "withdrawn_hi" (L/kWh), "withdrawn_fresh", "withdrawn_saline" (L/kWh, adding to "withdrawn"; saline includes brackish), "main_ba", "import_share", "wind_share", "solar_share", "pv_share_of_wind_solar", "year"}, or None."""
    num = lambda v: float(v) if v not in ("", None) else None
    for r in csv.DictReader(open(STATE_TABLE)):
        if r["state"] == state and r["consumed_l_per_kwh"]:
            return {"consumed": num(r["consumed_l_per_kwh"]), "consumed_lo": num(r["consumed_lo"]), "consumed_hi": num(r["consumed_hi"]),
                    "withdrawn": num(r["withdrawn_l_per_kwh"]), "withdrawn_lo": num(r["withdrawn_lo"]), "withdrawn_hi": num(r["withdrawn_hi"]),
                    "withdrawn_fresh": num(r["withdrawn_fresh_l_per_kwh"]), "withdrawn_saline": num(r["withdrawn_saline_l_per_kwh"]),
                    "main_ba": r["main_ba"], "import_share": num(r["import_share"]), "wind_share": num(r["wind_share"]),
                    "solar_share": num(r["solar_share"]), "pv_share_of_wind_solar": num(r["pv_share_of_wind_solar"]), "year": 2024}
    return None


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
    from waterledger_data.power import utility_rtos
    rto = utility_rtos()

    def ba(a):
        # the territory layer's control area; where it gives none (Texas delivery companies are listed as NOT AVAILABLE), the one RTO
        # EIA-861 lists the utility in
        uid = int(a["id"]) if str(a["id"]).isdigit() else None
        return BALANCING_AUTHORITIES.get(a["cntrl_area"]) or rto.get(uid)

    rows = [{"eia_id": int(f["a"]["id"]) if str(f["a"]["id"]).isdigit() else None, "name": f["a"]["name"], "type": f["a"]["type"],
             "balancing_authority": ba(f["a"]), "geometry": _polygon(f["rings"])} for f in json.load(open(path))]
    g = gpd.GeoDataFrame(rows, geometry="geometry", crs=4326)
    return g[g.geometry.notna() & ~g.geometry.is_empty].reset_index(drop=True)


def in_order(utilities):
    """A place's utilities, the largest share first; a tie goes to the lower EIA id, then the name, so a snapshot's checksum changes only when its data does. Shares tie often (1.0 where territories overlap)."""
    return sorted(utilities, key=lambda u: (-(u.get("share") or 0), u.get("eia_id") is None, u.get("eia_id") or 0, u.get("name") or ""))


# The territory layer gives the Western Area Power Administration one control area wherever it draws it (WALC, the Desert
# Southwest's). In the upper Great Plains its region joined the Southwest Power Pool's integrated system in 2015, so there it is SWPP.
WAPA_BY_STATE = {"MN": "SWPP", "IA": "SWPP", "ND": "SWPP", "SD": "SWPP", "NE": "SWPP"}


def _wapa(state, out):
    ba = WAPA_BY_STATE.get(state.upper())
    if ba:
        for us in out.values():
            for u in us:
                if (u.get("name") or "").upper().startswith("WAPA"):
                    u["balancing_authority"] = ba
    return out


def utilities_by_place(state, places):
    """For each place, the utilities whose territory covers part of it, the largest share first:
    {geoid: [{eia_id, name, type, balancing_authority, share}]}; shares of at least 1% (territories overlap where utilities share
    ground, so shares can add to more than 1)."""
    path = os.path.join(RAW, f"{state}_by_place.json")
    if os.path.exists(path):
        out = json.load(open(path))
        missing = [u for us in out.values() for u in us if not u["balancing_authority"]]
        if missing:                         # caches written before the EIA-861 fallback (territories) have none for these
            from waterledger_data.power import utility_rtos
            rto = utility_rtos()
            for u in missing:
                u["balancing_authority"] = rto.get(u["eia_id"])
        return {g: in_order(us) for g, us in _wapa(state, out).items()}
    t = territories(state, tuple(places.total_bounds)).to_crs(ALBERS)
    t["geometry"] = shapely.make_valid(t.geometry.values)
    pl = places[["geoid", "geometry"]].to_crs(ALBERS)
    pl["geometry"] = shapely.make_valid(pl.geometry.values)
    pairs = gpd.sjoin(pl, t, how="inner", predicate="intersects")
    gp = pl.set_index("geoid").geometry
    inter = shapely.intersection(gp.loc[pairs.geoid].values, t.geometry.values[pairs.index_right.values])
    pairs["share"] = shapely.area(inter) / shapely.area(gp.loc[pairs.geoid].values)
    out = {}
    for r in pairs[pairs.share >= 0.01].itertuples():
        ba = r.balancing_authority if isinstance(r.balancing_authority, str) else None      # pandas turns None into NaN
        out.setdefault(r.geoid, []).append({"eia_id": None if r.eia_id != r.eia_id else int(r.eia_id), "name": r.name, "type": r.type,
                                            "balancing_authority": ba, "share": round(float(r.share), 3)})
    out = {g: in_order(us) for g, us in _wapa(state, out).items()}
    os.makedirs(RAW, exist_ok=True)
    json.dump(out, open(path, "w"))
    return out


def loads(state):
    """EIA-861 sales, customers and peaks by utility for a state ({eia_id: {...}}, power.utility_loads), downloading the newest
    year EIA has posted if none is cached."""
    from waterledger_data import power
    year = power.latest_eia861()
    if year is None:
        return {}
    return power.utility_loads(year, state)


OWN_MIN_SHARE = 0.5            # a place's own utility covers at least half of it in the territory layer
OWN_MIN_DENSITY = 100.0        # and has at least this many EIA customers per km2 of the place it covers [A]: Columbus, Ohio's own utility
                               # (about 30) serves a part of the city, the towns' and small cities' own utilities 150 or more


def _words(s):
    return re.findall(r"[a-z]+", (s or "").lower())


def is_own(u, place, loads_):
    """Whether `u` is the place's own utility: a municipal or investor-owned utility named for it (Madison Gas & Electric in Madison, the City of
    Coldwater's in Coldwater; cooperatives are named for counties and regions, so never), covering at least OWN_MIN_SHARE of the place, with at
    least OWN_MIN_DENSITY customers per km2 of what it covers. `place`: {"base": its name without its kind, "km2": its area}."""
    b, w = _words(place["base"]), _words(u.get("name"))
    if not b or (u.get("type") or "").upper() == "COOPERATIVE" or (u.get("share") or 0) < OWN_MIN_SHARE:
        return False
    if not any(w[i:i + len(b)] == b for i in range(len(w) - len(b) + 1)):
        return False
    cust = (loads_.get(u["eia_id"]) or {}).get("customers") or 0
    return cust >= OWN_MIN_DENSITY * place["km2"] * u["share"]


def ranked(utilities, loads_, place=None):
    """A place's utilities in the order to show them: by EIA customers in the state (AEP Ohio before the City of Columbus's
    own small utility; Austin Energy before the cooperatives around it). HIFLD draws many territories as whole counties, so
    area shares overstate small utilities and are kept as "may serve", not as the share served. Ties (delivery-only utilities report no customers) go to the larger share, then the name,
    so a rebuild keeps the same order. With `place` ({"base", "km2"}; model 1.9), the place's own utility (is_own) comes first: a large utility
    drawn over whole counties otherwise outranks the city's own (Wisconsin Power & Light in Madison, Consumers Energy in Coldwater)."""
    cust = lambda u: (loads_.get(u["eia_id"]) or {}).get("customers") or 0
    own = (lambda u: is_own(u, place, loads_)) if place else (lambda u: False)
    return sorted(utilities, key=lambda u: (not own(u), -cust(u), -(u.get("share") or 0), u.get("name") or ""))
