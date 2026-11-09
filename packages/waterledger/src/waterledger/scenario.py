"""A scenario: a proposal of a given kind at any Michigan place, before anything is filed. Public data only.

Reads Water Ledger's data files (<site>/mi/data/*.json), which waterledger.states.mi writes, so anything built on this
package and the public page use the same numbers; estimate() mirrors the page's est(). Without a local site, the files
waterledger.org publishes are downloaded once and cached (PUBLISHED), so the package works on its own.
"""
import json, math, os

from waterledger_data.config import CACHE, SITE

DATA = os.path.join(SITE, "mi", "data")
PUBLISHED = "https://waterledger.org/mi/data/{name}.json"     # the same files, as published
DESIGNS = {"dry": "Closed loop (designed to use no water for cooling)", "hybrid": "Hybrid", "towers": "Cooling towers", "lake": "Lake-source (once-through)"}
SOURCE_LABEL = {"muni": "a public water system", "wells": "new wells in the aquifer", "lake": "lake surface water"}
DEST_LABEL = {"sewer": "the public sewer", "septic": "a septic system on site", "water": "a river or lake (its own discharge)", "reuse": "treatment and reuse on site"}
SYS_POP = 3300    # [A] a "sizable" public water system serves more than this many people (EPA's medium size and up; as waterledger_data.supply)
SEWER_KM = 10     # [A] with no public water system mapped, a large sewer plant this close is assumed reachable by an extension
LAND_LABEL = {"farm": "farm fields", "woods": "woods or meadow", "built": "existing development"}
_cache = {}


def data(name):
    """One of Michigan's data files: the local site's if there is one, else Michigan's snapshot (data.waterledger.org, which
    carries the site files as published), else the file waterledger.org publishes (downloaded once)."""
    if name not in _cache:
        path = os.path.join(DATA, name + ".json")
        if not os.path.exists(path):
            try:
                from waterledger.national.data import fetch_snapshot
                path = os.path.join(fetch_snapshot("MI"), "michigan", name + ".json")
            except Exception:                                           # noqa: BLE001  no snapshot reachable: the published file
                path = os.path.join(CACHE, "published", "mi", name + ".json")
            if not os.path.exists(path):
                import urllib.request
                os.makedirs(os.path.dirname(path), exist_ok=True)
                req = urllib.request.Request(PUBLISHED.format(name=name), headers={"User-Agent": "waterledger (python package)"})
                with urllib.request.urlopen(req, timeout=120) as r, open(path, "wb") as f:
                    f.write(r.read())
        _cache[name] = json.load(open(path))
    return _cache[name]


def place(gid):
    p = next((x for x in data("places")["places"] if x["g"] == str(gid)), None)
    if p is None:
        raise KeyError(f"No Michigan place with GEOID {gid}")
    b = p["n"].rsplit(" ", 2)[0] if p["n"].endswith("charter township") else p["n"].rsplit(" ", 1)[0]
    p = dict(p, base=b if p["k"] == "city" else b + (" Charter Township" if p["k"] == "charter township" else " Township"))
    return p


def find(name, county=None):
    """GEOID of a place by name ('Gaines', 'Gaines charter township'), optionally within a county."""
    name = name.lower()
    hits = [p for p in data("places")["places"] if p["n"].lower().startswith(name) and (county is None or p["c"].lower() == county.lower())]
    exact = [p for p in hits if p["n"].lower() == name]
    if exact:
        return exact[0]["g"]
    if len(hits) != 1:
        raise KeyError(f"{name!r} matches {[p['n'] + ', ' + p['c'] for p in hits[:6]] or 'nothing'}; give the full name (e.g. 'saline township') or the GEOID")
    return hits[0]["g"]


def lonlat(p):
    from waterledger.states.mi import KX, LAT1, LON0, SC
    return p["x"] / (KX * SC) + LON0, LAT1 - p["y"] / SC


def band(stat, x):
    return {"lo": stat["p10"] * x, "mid": stat["p50"] * x, "hi": stat["p90"] * x}


def flow(D, region, cool, key, mw):
    """A water flow at `mw` MW of IT capacity, lo/mid/hi in MGD (million gallons for *_annual_mg): the per-100 MW model results scaled
    to the size, plus staff water at that size, which grows more slowly than the computers (model 1.2). The two ranges are added
    end to end, which makes the range a little wide. Same as WQ.flow on the page."""
    from waterledger_models.datacenter.cooling import staff_q
    b = band(D["regions"][region]["per_100mw"][cool][key], mw / 100)
    s = staff_q(D["staff"]["runs"], mw)[key.split("_")[0]]
    k = 365.25 if key.endswith("_mg") else 1.0          # annual_mg and worst_year_mg are million gallons a year
    return {"lo": b["lo"] + s["p10"] * k, "mid": b["mid"] + s["p50"] * k, "hi": b["hi"] + s["p90"] * k}


GRID_KINDS = ("consumed", "withdrawn", "marginal_consumed", "marginal_withdrawn")


def grid_water(D, region, cool, mw, ba):
    """Water at the power plants of balancing authority `ba` for the campus's own hourly electricity (design 0008, model 1.11), lo/mid/hi MGD at
    `mw` MW of IT capacity: {kind: {"avg", "peak_day"}} for consumed and withdrawn, on the BA's average hourly mix and on its marginal one. None for
    lake-source cooling, a BA the cell's run didn't cover, or data from before model 1.11."""
    if cool == "lake" or not ba:
        return None
    r = D["regions"][region]["per_100mw"].get(cool) or {}
    if f"grid_{ba}_consumed_avg" not in r:
        return None
    return {k: {"avg": band(r[f"grid_{ba}_{k}_avg"], mw / 100), "peak_day": band(r[f"grid_{ba}_{k}_peak_1in10"], mw / 100)} for k in GRID_KINDS}


def electricity(D, region, cool, mw):
    """Facility electricity at `mw` MW of IT capacity at a region's weather, lo/mid/hi: {"mw", "peak_mw", "pue", "peak_pue"}, and "peak_day_mw"
    where the results have it (model 1.9; not lake-source cooling), or None for data from before model 1.4. Lake-source cooling has its own heat balance (lake.run_lake), the same at every region. Same as WQ.elec on the page."""
    per_100mw = D["regions"][region]["per_100mw"]
    r = (D["lake_source"].get("power") or per_100mw["towers"]) if cool == "lake" else per_100mw[cool]      # data from before model 1.5: towers stood in
    if "power_mw_avg" not in r:
        return None
    out = {"mw": band(r["power_mw_avg"], mw / 100), "peak_mw": band(r["power_mw_peak_1in10"], mw / 100), "pue": band(r["pue_avg"], 1.0), "peak_pue": band(r["pue_peak_1in10"], 1.0)}
    if "power_mw_peak_day_1in10" in r:
        out["peak_day_mw"] = band(r["power_mw_peak_day_1in10"], mw / 100)
    return out


def pue_by_design(regions, lake=None):
    """One PUE per design across a state's regions, for what cannot wait for a place (turning a utility contract's MW into computing capacity, at
    the hottest-hour value): {design: {"lo", "mid", "hi", "basis"}}. `lake`: the lake-source results' power block, where a state has them."""
    mean = lambda d, k, q: sum(x["per_100mw"][d][k][q] for x in regions.values()) / len(regions)
    out = {d: {"lo": round(mean(d, "pue_avg", "p10"), 3), "mid": round(mean(d, "pue_avg", "p50"), 3), "hi": round(mean(d, "pue_peak_1in10", "p50"), 3),
               "basis": "Hourly heat balance at this state's weather (model 1.4): annual PUE, 10th and 50th percentiles, and the 1-in-10-year hottest hour; averaged over its regions"}
           for d in next(iter(regions.values()))["per_100mw"]}
    if lake:
        out["lake"] = {"lo": round(lake["pue_avg"]["p10"], 3), "mid": round(lake["pue_avg"]["p50"], 3), "hi": round(lake["pue_peak_1in10"]["p50"], 3),
                       "basis": "Heat balance with the lake water colder than the loops: no chillers or heat rejection fans"}
    return out


def cell(cid):
    """An ERA5 cell's results (model 1.8, design 0004): the site's data/cells/<cell>.json, else Michigan's format 3 snapshot's
    (data.waterledger.org, fetched when needed and checked), else the file waterledger.org publishes."""
    name = f"cells/{cid}"
    if name not in _cache and not os.path.exists(os.path.join(DATA, name + ".json")):
        try:
            from waterledger.national.data import SnapshotData, fetch_snapshot
            sd = SnapshotData("MI", fetch_snapshot("MI"))
            if sd.format() >= 3:
                _cache[name] = sd.cell(cid)
        except Exception:                                               # noqa: BLE001  no snapshot reachable: the published file
            pass
    return data(name)


DEFAULT_PLANT = "shared"      # waterledger_models.datacenter.physics.DEFAULT_PLANT, without importing the models here


def for_plant(rec, plant=DEFAULT_PLANT):
    """A cell's or region's results for a cooling plant (model 1.10): per_100mw holds the default plant's, per_100mw_plants the others'. Data from before
    model 1.10 has one plant, its own, and only that one can be asked for."""
    if plant == rec.get("plant", DEFAULT_PLANT):
        return rec
    other = rec.get("per_100mw_plants", {})
    if plant not in other:
        raise ValueError(f"these results have no {plant!r} plant: they have {[rec.get('plant', DEFAULT_PLANT), *other]} (results from before model 1.10 have one)")
    return {**rec, "per_100mw": other[plant], "plant": plant}


def cooling(p, D=None, plant=DEFAULT_PLANT):
    """(D, the key its regions are read by) for a place's cooling. Model 1.8 site data names the place's ERA5 cell (p["e"]), whose results
    come from cells/ and stand in D's regions under the cell's id, as the page loads them; before, the place's region's (p["r"]). The
    region stays the place's for rainfall, road salt and golf. `plant`: the cooling plant inside the building (model 1.10, for_plant)."""
    D = D or data("estimates")
    cid = p.get("e")
    if not cid:
        return {**D, "regions": {**D["regions"], p["r"]: for_plant(D["regions"][p["r"]], plant)}}, p["r"]
    return {**D, "regions": {**D.get("regions", {}), cid: for_plant(cell(cid), plant)}}, cid


def estimate(p, mw, cool, dest, region=None, plant=DEFAULT_PLANT):
    """Water taken, evaporated or lost, and sent out (MGD, lo/mid/hi), as on the page."""
    D = data("estimates")
    if region is None:
        D, region = cooling(p, D, plant)
    if cool == "lake":
        return lake_estimate(D, p["gl"]["lake"], region, mw, dest)
    return cooling_estimate(D, region, cool, mw, dest)


def lake_estimate(D, lake, region, mw, dest):
    """Lake-source cooling on one of the Great Lakes, from D["lake_source"]. What goes to the sewer or septic is a closed-loop campus's, which is the region's."""
    L = D["lake_source"][lake]
    x = mw / 100
    w = band(L["withdrawn"], x)
    return {"lake": True, "wAvg": w, "wPeak": w, "wAnn": {k: v * 365.25 for k, v in w.items()}, "cAvg": band(L["evap_avg"], x),
            "cPeak": band(L["evap_peak_month"], x), "rAvg": w, "rPeak": w, "wMonth": w, "c90": band(L["evap_peak_month"], x), "sewer": cooling_estimate(D, region, "dry", mw, "septic" if dest == "septic" else "sewer")["sewer"], "reuse": False}


def check_lake(place_name, great_lake, cool, src):
    """Lake surface water and lake-source cooling need a Great Lake within about 5 km, and lake-source cooling needs the lake as its source, in every state."""
    if (src == "lake" or cool == "lake") and not great_lake:
        raise ValueError(f"{place_name} is not within about 5 km of a Great Lake; lake surface water and lake-source cooling are not options there")
    if cool == "lake" and src != "lake":
        raise ValueError("Lake-source cooling needs lake surface water as the source")


def cooling_estimate(D, region, cool, mw, dest):
    """Water taken, evaporated or lost, and sent out for an air- or water-cooled campus (MGD, lo/mid/hi), from model results in D
    ({"regions": {region: {"per_100mw": ...}}, "staff": {"runs": ...}}): the page's est() for every design but lake-source.
    The national tier uses it with climate divisions as the regions."""
    F = lambda key: flow(D, region, cool, key, mw)
    per_100mw = D["regions"][region]["per_100mw"][cool]
    C = lambda key: band(per_100mw[key], mw / 100) if key in per_100mw else {"lo": 0.0, "mid": 0.0, "hi": 0.0}    # data from before model 1.5 has none
    E = {"lake": False, "wAvg": F("withdrawn_avg"), "wPeak": F("withdrawn_peak_1in10"), "wAnn": F("withdrawn_annual_mg"),
         "cAvg": F("consumed_avg"), "cPeak": F("consumed_peak_1in10"), "rAvg": F("returned_avg"),
         "rPeak": F("returned_peak_1in10"), "condAvg": C("condensate_avg"), "condPeak": C("condensate_peak_1in10"), "reuse": False}
    # no rounding here (the site rounds what it shows). Separate medians do not add up, so on the middle estimate withdrawn and returned stay the model's own medians
    # and evaporated or lost is what is left, so the books close: withdrawn + condensate = consumed + returned. Its range stays the model's own, widened only if that falls outside
    for k_c, k_w, k_r, k_n in (("cAvg", "wAvg", "rAvg", "condAvg"), ("cPeak", "wPeak", "rPeak", "condPeak")):
        m = max(0.0, E[k_w]["mid"] + E[k_n]["mid"] - E[k_r]["mid"])
        E[k_c] = {"lo": min(E[k_c]["lo"], m), "mid": m, "hi": max(E[k_c]["hi"], m)}
    if "withdrawn_max_month" in per_100mw:           # the rules' own periods: Part 327's 30 days and the Compact's 90 (data from before model 1.7 has no 90-day figure)
        E["wMonth"] = F("withdrawn_max_month")
    if "consumed_max_90day" in per_100mw:
        E["c90"] = F("consumed_max_90day")
    E["sewer"] = E["rAvg"]
    if dest == "septic":        # condensate is clean water and would not go to a drainfield: a site drain or stormwater [A]. It stays in the returned water, so the books close
        E["sewer"] = {k: max(E["rAvg"][k] - E["condAvg"][k], 0.0) for k in ("lo", "mid", "hi")}
        E["sewer"]["lo"], E["sewer"]["hi"] = min(E["sewer"]["lo"], E["sewer"]["mid"]), max(E["sewer"]["hi"], E["sewer"]["mid"])
    if "withdrawn_peak_full_capacity" in per_100mw and dest != "reuse":
        E["wPeakFull"] = F("withdrawn_peak_full_capacity")
    if dest == "reuse":
        E["full"] = {"wAvg": E["wAvg"], "rAvg": E["rAvg"]}
        # the condensate is reused too; where it covers everything, nothing is taken. Each end is worked from separate model outputs, so the range is put back in order
        def taken(a, b):
            v = {k: max(a[k] - b[k], 0.0) for k in ("lo", "mid", "hi")}
            return {"lo": min(v.values()), "mid": v["mid"], "hi": max(v.values())}
        E["wAvg"], E["wPeak"] = taken(E["cAvg"], E["condAvg"]), taken(E["wPeak"], E["rPeak"])
        if "wMonth" in E:          # the share reuse saves on an average day, in the highest month too [A]
            E["wMonth"] = {k: E["wMonth"][k] * E["wAvg"][k] / max(E["full"]["wAvg"][k], 1e-12) for k in ("lo", "mid", "hi")}
        E["wAnn"] = {k: v * 365.25 for k, v in E["wAvg"].items()}
        E["rAvg"] = E["rPeak"] = E["sewer"] = {"lo": 0, "mid": 0, "hi": 0}
        E["reuse"] = True
    return E


def septic_rule(gpd):
    """Michigan's rules for sanitary sewage to a septic system (Part 22: R 323.2210, 2211, 2216), as on the page (WQ.septicRule). `gpd` is what goes to the system, without
    condensate (a septic estimate's to_sewer)."""
    return ("the county health department approves the design; no state permit is needed under 6,000 gallons a day" if gpd < 6000
            else "it falls under a state permit-by-rule (6,000 to 10,000 gallons a day): the county health department approves it, and the flow is metered and reported to EGLE each year" if gpd < 10000
            else "it needs a groundwater discharge permit from EGLE (above 10,000 gallons a day)")


def _plants_near(p, km=40):
    """Sewer plants for a place by the rule every state has (wastewater.nearest): the place's own first, then any of 0.5 MGD or more, nearest first, by true distance. The site's data gives places and plants in
    map coordinates, to about 200 m. WQ.plants on the page has to work out the same distance."""
    from waterledger_data import waters as wi
    from waterledger_data.wastewater import distance_km, is_own
    st = wi.place_stem(p["n"])
    lon, lat = lonlat(p)
    rows = []
    for q in data("waters")["plants"]:
        q_lon, q_lat = lonlat(q)
        d = distance_km(lat, lon, q_lat, q_lon)
        rows.append({**q, "km": d, "own": is_own(q["city"] == st, d)})
    return sorted([q for q in rows if q["km"] <= km and (q["own"] or (q["design"] or 0) >= 0.5)], key=lambda q: (not q["own"], q["km"]))


def near_system(p):
    """The nearest sizable public water system to a place, by the rule every state has (waterledger_data.supply.nearest_sizable): from the place's point to the edge of the system's service
    area. Michigan's builder stores it as the place's "near" (WQ.nearSystem reads the same). Data from before 3.9.0 has none, and the rule then was center to center: serving more
    than SYS_POP people and covering at least a quarter of a city or township (map coordinates, 1/60 degree = 1.852 km)."""
    if "near" in p:
        return {"w": p["near"], "place": None, "km": p["near"]["km"]} if p["near"] else None
    best = None
    for q in data("places")["places"]:
        if q["g"] == p["g"] or not q["w"]:
            continue
        for w in q["w"]:
            if (w.get("pop") or 0) <= SYS_POP or (w.get("share") or 0) < 0.25:
                continue
            km = math.hypot(q["x"] - p["x"], q["y"] - p["y"]) * 1.852
            if best is None or km < best["km"]:
                best = {"w": w, "place": q, "km": km}
    return best


def src_for(p, cool):
    """Where a campus's water most likely comes from [A], as on the page (WQ.srcFor). A system EPA maps in the place. With none
    mapped: closed loop from a sizable system within SEWER_KM (it extends its pipes); towers and hybrid from new wells, which avoid a
    utility's peak-day limits; nothing within reach, new wells."""
    if p["w"]:
        return {"src": "muni", "near": None, "reach": False}
    near = near_system(p)
    reach = bool(near) and near["km"] <= SEWER_KM
    return {"src": "muni" if reach and cool not in ("towers", "hybrid") else "wells", "near": near, "reach": reach}


def dest_for(p, cool, sew_mgd):
    """Where a campus's wastewater most likely goes [A], as on the page (WQ.destFor). The sewer when EPA maps a public water system in the place (its plant within 40 km),
    or a plant is within SEWER_KM;
    evaporative blowdown only if it fits in the plant's spare design flow. Otherwise closed loop's mostly sanitary flow goes to a
    septic system on site, and blowdown to the campus's own treatment plant and a stream. The plant is in the page's form (n, design, flow, km)."""
    pls = _plants_near(p)
    q = pls[0] if pls else None
    evap = cool in ("towers", "hybrid")
    reach = bool(q) and (bool(p["w"]) or q["km"] <= SEWER_KM)
    room = q["design"] - q["flow"] if q and q.get("flow") else None
    why = "far" if not reach else "full" if evap and room is not None and sew_mgd > room else ""
    return {"dest": ("water" if evap else "septic") if why else "sewer", "q": q, "sys": bool(p["w"]), "room": room, "why": why}


def land_default(incorporated):
    """(acres, what the land is today) a site starts with [A], in every state: incorporated places (Place.incorporated: cities, villages, towns) a smaller, built-up site; others farmland."""
    return (50, "built") if incorporated else (200, "farm")


def scenario(gid, mw=None, cool="dry", src=None, dest=None, acres=None, before=None, imp=0.5, power="state_mix", h12=0, name=None, plant=DEFAULT_PLANT):
    p = place(gid)
    # the page's starting settings for a place [A]: cities a smaller campus on a smaller, built-up site; townships 300 MW on farmland
    city = p["k"] == "city"
    mw = mw or (100 if city else 300)
    src = src or src_for(p, cool)["src"]   # the page's starting water source for the place and cooling design
    check_lake(p["base"], p.get("gl"), cool, src)
    if not dest:
        dest = dest_for(p, cool, estimate(p, mw, cool, "sewer", plant=plant)["sewer"]["mid"])["dest"]
    start_acres, start_land = land_default(city)
    before = before or start_land
    acres = acres or start_acres
    return {"place": p, "mw": mw, "cool": cool, "src": src, "dest": dest, "acres": acres, "before": before, "imp": imp, "power": power,
            "h12": min(h12, len(p["h12"]) - 1) if p["h12"] else None, "name": name, "plant": plant, "E": estimate(p, mw, cool, dest, plant=plant)}
