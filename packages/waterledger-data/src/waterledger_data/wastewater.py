"""Sewer plants in any state: EPA's Clean Watersheds Needs Survey 2022 for every wastewater plant (design flow and location; HydroShare compilation, Hodson et al. 2026), with EPA ECHO's
last-year average flow, receiving water, major/minor and combined-sewer status where an NPDES permit matches. One rule in every state, Michigan's included: a plant counts unless the survey gives it no permit at all,
which leaves out capital-project and collection-system records (Austin's "5 Year CIP", 152 MGD), or ECHO has terminated every permit it has. ECHO's "Expired" is not closed: Cincinnati's Mill Creek
(221 MGD) and Mount Pleasant, Michigan, are both listed so and running. A permit ECHO doesn't list stays too, which keeps general-permit lagoons and state groundwater permits (Fremont, Michigan; Fort Bliss, Texas). ECHO flows that don't fit the plant's
design flow are dropped (unit errors are common at small plants). Cached under <cache>/wastewater/."""
import collections, csv, json, math, os, re, urllib.request

from waterledger_data.config import CACHE
from waterledger_data.waters import CWNS, ECHO, ECHO_COLS, _get

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
        q = _get(f"{ECHO}.get_facilities", {"output": "JSON", "p_st": state, "p_pcomp": "POT", "responseset": 1000})["Results"]
        rows, page = [], 1
        while True:
            r = _get(f"{ECHO}.get_qid", {"output": "JSON", "qid": q["QueryID"], "pageno": page, "responseset": 1000, "qcolumns": ECHO_COLS})["Results"]
            rows += r.get("Facilities", [])
            if len(rows) >= int(q["QueryRows"]) or not r.get("Facilities"):
                break
            page += 1
        os.makedirs(RAW, exist_ok=True)
        json.dump(rows, open(path, "w"))
    return json.load(open(path))


def plants(state):
    """A state's wastewater plants: [{id (NPDES), name, city, lat, lon, design_mgd, flow_mgd, major, cso, receiving, huc12, lagoon}]."""
    reports = {r["SourceID"]: r for r in _echo(state)}
    echo = {k: r for k, r in reports.items() if r["CWPPermitStatusDesc"] != "Terminated"}
    fac = {r["CWNS_ID"]: r for r in _cwns("FACILITIES") if r["STATE_CODE"] == state and r["INFRASTRUCTURE_TYPE"] == "Wastewater"}
    flow = {r["CWNS_ID"]: float(r["CURRENT_DESIGN_FLOW"]) for r in _cwns("FLOW")
            if r["STATE_CODE"] == state and r["FLOW_TYPE"] == "Total Flow" and r["CURRENT_DESIGN_FLOW"]}
    loc = {r["CWNS_ID"]: r for r in _cwns("PHYSICAL_LOCATION") if r["STATE_CODE"] == state and r["LATITUDE"]}
    permits = collections.defaultdict(list)
    for r in _cwns("FACILITY_PERMIT"):
        if r["STATE_CODE"] == state:
            permits[r["CWNS_ID"]].append(r["PERMIT_NUMBER"].strip())
    out = []
    for cid, fr in fac.items():
        if cid not in flow or cid not in loc:
            continue
        if not permits[cid] or all(pm in reports and pm not in echo for pm in permits[cid]):       # no permit: capital projects, collection systems. All terminated: closed
            continue
        e = next((echo[pm] for pm in permits[cid] if pm in echo), None)
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
