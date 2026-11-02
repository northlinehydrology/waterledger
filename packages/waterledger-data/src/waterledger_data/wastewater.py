"""Sewer plants in any state: EPA's Clean Watersheds Needs Survey 2022 for every wastewater plant (design flow and location; HydroShare compilation, Hodson et al. 2026), with EPA ECHO's
last-year average flow, receiving water, major/minor and combined-sewer status where an NPDES permit matches. One rule in every state: a plant in the survey stays unless there is positive evidence it is not a running plant.
A terminated or missing permit alone is not that evidence, as permits get renumbered and moved between general and individual permits (Otsego, Michigan: MI0023744 terminated, MI0060260 effective).
Left out: records that name themselves a project or only a collection system (Austin's "5 Year CIP", 152 MGD; East China, Michigan's "REG CS"), and plants whose permits are all terminated or gone from ECHO, with no live sewer permit
at that location, and a live plant at least as large in the same city to have taken the flow (see replaced) (Austin's Govalle; Chesapeake-Elizabeth, Virginia Beach). ECHO's "Expired" is not closed (Cincinnati's Mill Creek, 221 MGD).
ECHO flows that don't fit the plant's design flow are dropped (unit errors are common at small plants). Cached under <cache>/wastewater/."""
import collections, csv, json, math, os, re, urllib.request

from waterledger_data.config import CACHE
from waterledger_data.waters import CWNS, ECHO, ECHO_COLS, _get, echo_rows

RAW = os.path.join(CACHE, "wastewater")
CWNS_RAW = os.path.join(CACHE, "waters")          # the national CWNS tables, shared with Michigan's builder


def _cwns(table):
    path = os.path.join(CWNS_RAW, f"cwns2022_{table}.csv")
    if not os.path.exists(path):
        os.makedirs(CWNS_RAW, exist_ok=True)
        urllib.request.urlretrieve(f"{CWNS}/{table}.csv", path)
    return csv.DictReader(open(path))


def _echo(state):
    path = os.path.join(RAW, f"{state}_echo_potw.json")
    if not os.path.exists(path):
        rows = echo_rows(state, _get)
        os.makedirs(RAW, exist_ok=True)
        json.dump(rows, open(path, "w"))
    return json.load(open(path))


def _echo_by_permit(state, permits):
    """ECHO's records for permit numbers, asked for by number, a hundred at a time. Cached for the state."""
    path = os.path.join(RAW, f"{state}_echo_by_permit.json")
    if not os.path.exists(path):
        rows, permits = [], sorted(permits)
        for i in range(0, len(permits), 100):
            q = _get(f"{ECHO}.get_facilities", {"output": "JSON", "p_pid": ",".join(permits[i:i + 100]), "responseset": 1000})["Results"]
            if int(q.get("QueryRows") or 0):
                rows += _get(f"{ECHO}.get_qid", {"output": "JSON", "qid": q["QueryID"], "pageno": 1, "responseset": 1000, "qcolumns": ECHO_COLS})["Results"].get("Facilities", [])
        os.makedirs(RAW, exist_ok=True)
        json.dump(rows, open(path, "w"))
    return json.load(open(path))


# Words that mark a sewer plant's permit in ECHO, and permits at the same spot that aren't one
SEWER_PERMIT = re.compile(r"WWTP|WTTP|WWSL|WWTF|WWTL|\bSTP\b|WRRF|WPC|\bWRF\b|\bWRP\b|SEWAGE|SEWER|LAGOON|POTW|WASTEWATER|SANITATION")
NOT_SEWER = re.compile(r"MS4|CAFO|STORM")
STORMWATER_PERMIT = re.compile(r"^[A-Z]{2}[RSU]")      # NPDES stormwater general permits (TXR, MIS) and unpermitted sites (MIU), whatever the holder is called
NEAR_MILES = 1.5


def is_project(name):
    """A survey record that names itself a capital project, or only a collection system, not a plant."""
    n = name.upper()
    return bool(re.search(r"\bCIP\b|CAPITAL|\bYEAR\b", n)) or bool(re.search(r"\bCS$|COLLECTION SYSTEM$", n.strip()) and not re.search(r"\bPLANT\b|TREATMENT", n) and not SEWER_PERMIT.search(n))


def replaced(name, design, largest_live):
    """Whether a plant with no live permit looks closed, its flow taken by a live plant at least as large in the survey's city. The survey's city is a mailing city, so this isn't asked of a plant under 0.5 MGD,
    which may be a village's or a subdivision's lagoon (Sand Lake, Michigan, mails from Grand Rapids), or one whose name gives its own township (Hamburg Twp, mailing from Whitmore Lake)."""
    return design >= 0.5 and largest_live >= design and not re.search(r"\bTWP\b|TOWNSHIP", name.upper())


def live_permit_at(rows, name, city):
    """Of ECHO's permits near a plant, a live one for a sewer plant of the same town or name: the renumbered permit, or None."""
    n, c = name.upper().split(), (city or "").upper()
    for r in rows:
        held = (r.get("CWPName") or "").upper()
        if r["CWPPermitStatusDesc"] != "Terminated" and SEWER_PERMIT.search(held) and not NOT_SEWER.search(held) and not STORMWATER_PERMIT.match(r.get("SourceID") or "") and ((c and c in held) or (n and len(n[0]) > 2 and n[0] in held)):
            return r
    return None


def _echo_near(state, places):
    """ECHO's permits within about NEAR_MILES of each {key: (lat, lon)}. Cached for the state, key by key, so a stopped build resumes."""
    path = os.path.join(RAW, f"{state}_echo_near.json")
    got = json.load(open(path)) if os.path.exists(path) else {}
    for k, (lat, lon) in places.items():
        if k in got:
            continue
        q = _get(f"{ECHO}.get_facilities", {"output": "JSON", "p_c1lat": lat + NEAR_MILES / 69, "p_c1lon": lon - NEAR_MILES / 53, "p_c2lat": lat - NEAR_MILES / 69, "p_c2lon": lon + NEAR_MILES / 53, "responseset": 1000})["Results"]
        got[k] = _get(f"{ECHO}.get_qid", {"output": "JSON", "qid": q["QueryID"], "pageno": 1, "responseset": 1000, "qcolumns": ECHO_COLS})["Results"].get("Facilities", []) if int(q.get("QueryRows") or 0) else []
        os.makedirs(RAW, exist_ok=True)
        json.dump(got, open(path, "w"))
    return got


def plants(state):
    """A state's wastewater plants: [{id (NPDES), name, city, lat, lon, design_mgd, flow_mgd, major, cso, receiving, huc12, lagoon}]."""
    fac = {r["CWNS_ID"]: r for r in _cwns("FACILITIES") if r["STATE_CODE"] == state and r["INFRASTRUCTURE_TYPE"] == "Wastewater"}
    flow = {r["CWNS_ID"]: float(r["CURRENT_DESIGN_FLOW"]) for r in _cwns("FLOW")
            if r["STATE_CODE"] == state and r["FLOW_TYPE"] == "Total Flow" and r["CURRENT_DESIGN_FLOW"]}
    loc = {r["CWNS_ID"]: r for r in _cwns("PHYSICAL_LOCATION") if r["STATE_CODE"] == state and r["LATITUDE"]}
    permits, state_permit = collections.defaultdict(list), set()
    for r in _cwns("FACILITY_PERMIT"):
        if r["STATE_CODE"] == state:
            permits[r["CWNS_ID"]].append(r["PERMIT_NUMBER"].strip())
            if r["PERMIT_TYPE"].startswith(("State", "Land Application")):
                state_permit.add(r["CWNS_ID"])
    reports = {r["SourceID"]: r for r in _echo(state)}
    unlisted = {pm for cid in fac if cid in flow and cid in loc and cid not in state_permit for pm in permits[cid] if pm not in reports}
    reports.update({r["SourceID"]: r for r in (_echo_by_permit(state, unlisted) if unlisted else [])})
    echo = {k: r for k, r in reports.items() if r["CWPPermitStatusDesc"] != "Terminated"}
    usable = [c for c in fac if c in flow and c in loc and not is_project(fac[c]["FACILITY_NAME"])]
    found = {c: next((echo[pm] for pm in permits[c] if pm in echo), None) for c in usable}
    doubtful = [c for c in usable if found[c] is None and c not in state_permit and permits[c]]            # every permit terminated or gone from ECHO
    near = _echo_near(state, {c: (float(loc[c]["LATITUDE"]), float(loc[c]["LONGITUDE"])) for c in doubtful}) if doubtful else {}
    for c in doubtful:
        found[c] = live_permit_at(near.get(c, []), fac[c]["FACILITY_NAME"], loc[c]["CITY"])
    largest_live = collections.defaultdict(float)                                                          # by the survey's city
    for c in usable:
        if found[c] is not None:
            largest_live[loc[c]["CITY"].upper()] = max(largest_live[loc[c]["CITY"].upper()], flow[c])
    out = []
    for cid in usable:
        fr, e = fac[cid], found[cid]
        if cid in doubtful and e is None and replaced(fr["FACILITY_NAME"], flow[cid], largest_live[loc[cid]["CITY"].upper()]):
            continue
        design = flow[cid] or None          # a few plants report a design flow of 0: treated as unknown
        f_echo = float(e["PastCalYrAverageFlow"]) if e and e["PastCalYrAverageFlow"] else None
        if f_echo and (design is None or not 0.1 <= f_echo / design <= 1.3):
            f_echo = None
        name = fr["FACILITY_NAME"].upper()
        out.append({"id": (e or {}).get("SourceID") or (permits[cid] or [cid])[0], "name": name, "city": loc[cid]["CITY"],
                    "lat": float(loc[cid]["LATITUDE"]), "lon": float(loc[cid]["LONGITUDE"]), "design_mgd": design, "flow_mgd": f_echo,
                    "major": bool(e and e["CWPMajorMinorStatusFlag"] == "M"), "cso": bool(e and e["CWPCsoFlag"] == "Y"),
                    "receiving": (e or {}).get("CWPStateWaterBodyName"), "huc12": (e or {}).get("RadWBDHuc12"),
                    "lagoon": bool(re.search(r"LAGOON|WWSL|STABILIZATION", name))})
    return out


# A place's own plant, in every state [A]: a plant carrying the place's name, if it is this close. Beyond this a shared name is mostly coincidence (Sandusky County
# and Sandusky city's plant, 37 km; Ohio has 39 Jackson Townships), and the nearest plant is the more reasonable guess. It is also the distance a sewer is assumed to reach.
OWN_KM = 10


def distance_km(a_lat, a_lon, b_lat, b_lon):
    """Great-circle km."""
    dlat, dlon = math.radians(b_lat - a_lat), math.radians(b_lon - a_lon)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(a_lat)) * math.cos(math.radians(b_lat)) * math.sin(dlon / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def is_own(same_name, km):
    """Whether a plant with the place's name is the place's own."""
    return bool(same_name) and km <= OWN_KM


def nearest(plants_, lat, lon, city=None, km=40, min_design=0.5):
    """Plants within `km` of a point: the place's own first (is_own), then any other plant of at least `min_design` MGD design flow, nearest first. The survey's city is
    a mailing city, so a name match is not perfect (Austin's South Austin Regional plant is listed in Del Valle). Distances are great-circle km."""
    rows = []
    for q in plants_:
        d = distance_km(lat, lon, q["lat"], q["lon"])
        own = is_own(bool(city) and (q["city"] or "").lower() == city.lower(), d)
        if d <= km and (own or (q["design_mgd"] or 0) >= min_design):
            rows.append({**q, "km": d, "own": own})
    return sorted(rows, key=lambda q: (not q["own"], q["km"]))
