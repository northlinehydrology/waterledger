"""`waterledger era5 check ST`: design 0005's leave-one-station-out check, for any state, with a pass or fail.

Two parts, as docs/methods/qm-check's cv_weather and cv_places did for the first four states:
- Weather. Every qualifying station (ISD under one ID or linked, and ECCC) in the state or within 100 km of one of its places is held
  out in turn, with any other within 5 km. Its cell (the land rule's) gets the method as decided: shore cells corrected from the shore
  stations left, and from model 1.9 land cells from the land stations left within 100 km. The cell is compared with the station on the station's own hours: the 0.4% design
  dry-bulb, the 0.4% wet bulb, the mean summer afternoon, the mean dew point and, from model 1.10, the 1-in-10-year peak day's mean wet bulb.
- Places. For up to `n` stations in the state, the nearest place within PLACE_KM, through the cooling model: the place's cell
  (corrected without that station) against the station's own record (cooling.run_location, 400 draws, seed 7, per 100 MW).

The criteria (CRITERIA) are the worst of the four states accepted so far (Michigan, Ohio, Virginia, Texas; Nov 4, 2026) plus a
margin: a new state passes when ERA5 and the correction do about as well there as in a state already published. A fail is a method
question for Andrew (an elevation correction on land cells in a mountain state, say). This command reports it and changes nothing.
"""
import datetime, json, os, sys

import numpy as np

from waterledger_data import era5
from waterledger_data.config import CACHE

CHECK = os.path.join(CACHE, "era5", "check")
R_KM, HOLD_KM, PLACE_KM = 100.0, 5.0, 30.0
STATS = [(d, s) for d in ("towers", "hybrid", "assist") for s in ("withdrawn_avg", "withdrawn_peak_1in10")]

# (id, what it tests, limit, how the limit was set). The four states: docs/methods/qm-check/cv_weather.json and cv_places_summary.json,
# each state's stations being those in it or within 100 km of its places, its places those of the station check within 30 km of a station.
CRITERIA = [
    ("W1", "land stations held out, at least", 5, "too few to judge below this"),
    ("W2", "land cells: median |error| in the 0.4% design dry-bulb, C, at most", 0.75, "four states 0.30-0.68 (Virginia); +0.07"),
    ("W3", "land cells: |mean error| in the design dry-bulb, C, at most", 0.5, "four states 0.07-0.33 (Texas); +0.17"),
    ("W4", "land cells: median |error| in the 0.4% wet bulb, C, at most", 0.4, "four states 0.10-0.25 (Virginia); +0.15"),
    ("W5", "corrected shore cells (3 or more): median |error| in the design dry-bulb, C, at most", 0.5, "four states 0.19-0.32 (Michigan); +0.18"),
    ("W6", "corrected shore cells (3 or more): median |error| no worse than uncorrected", None, "the reason to correct"),
    ("W7", "corrected cells: |mean error| in the 1-in-10-year peak day's mean wet bulb, C, at most", 0.5,
     "model 1.10 [A]: qm-2's Michigan peak days ran 0.72 C humid, mapping the dew point brought Michigan and Ohio to 0.23 (methods log, Nov 8, 2026)"),
    ("P1", "places sampled, at least", 5, "too few to judge below this"),
    ("P2", "places: median |difference| in the hybrid average day, %, at most", 8.0, "four states 1.9-4.6 (Virginia); +3.4"),
    ("P3", "places: |mean difference| in the hybrid average day, %, at most", 6.0, "four states 0.6-4.9 (Virginia); +1.1"),
    ("P4", "places: median |difference| in the hybrid peak day, %, at most", 6.0, "four states 0.5-3.2 (Virginia); +2.8"),
    ("P5", "places: median |difference| in towers' average day, %, at most", 2.0, "four states 0.03-0.22; +1.8"),
]


def _say(msg):
    print(msg, file=sys.stderr, flush=True)


def _km(a, b, c, d):
    from waterledger_models.quantile_mapping import km
    return float(km(a, b, c, d))


# --- stations ---

def candidates(state, places):
    """Every ISD (one ID or linked) and ECCC site in the state or within R_KM of one of its places, inside the shipped grid, with its cell."""
    from waterledger.national.era5 import _elevations
    from waterledger_data import climate
    from waterledger_models.quantile_mapping import km
    pl = np.array([(float(p["lat"]), float(p["lon"])) for p in places])
    elev = _elevations()
    sites = [{**s, "source": "isd-linked" if "parts" in s else "isd", "elev_m": elev.get(s.get("fallback_for", s["id"]))} for s in climate.isd_sites()]
    sites += [{**s, "source": "eccc"} for s in climate.eccc_sites()]
    out = []
    for s in sites:
        if s["state"] != state.upper() and km(s["lat"], s["lon"], pl[:, 0], pl[:, 1]).min() > R_KM:
            continue
        try:
            c = era5.cell(s["lat"], s["lon"])
        except ValueError:
            continue
        out.append({**s, "cell": c["id"], "cell_land": c["land"], "shore_land": era5.cell(s["lat"], s["lon"], land=None)["land"]})
    return out


def record(site):
    """A station's screened record under the snapshots' rule, cached in CHECK/stations: {**site, times, t, td}, or None if it fails."""
    from waterledger_data import climate
    d = os.path.join(CHECK, "stations")
    os.makedirs(d, exist_ok=True)
    meta_p, data_p = os.path.join(d, site["id"] + ".json"), os.path.join(d, site["id"] + ".npz")
    if os.path.exists(meta_p):
        meta = json.load(open(meta_p))
        if not meta["qualifies"]:
            return None
        if os.path.exists(data_p):
            z = np.load(data_p)
            return {**site, **meta, "times": [str(x) for x in z["times"]], "t": z["t"], "td": z["td"]}
    got = (climate.eccc_hourly if site["source"] == "eccc" else climate.isd_hourly)(site)
    meta = {"qualifies": bool(got)}
    if not got:
        json.dump(meta, open(meta_p, "w"))
        return None
    times, t, rh, share, screen = got
    t = np.asarray(t, float)
    g = np.log(np.asarray(rh, float) / 100) + era5.MAGNUS[0] * t / (era5.MAGNUS[1] + t)
    td = era5.MAGNUS[1] * g / (era5.MAGNUS[0] - g)
    np.savez_compressed(data_p, times=np.array(times), t=t, td=td)
    meta |= {"share_observed": share, "screen": screen}
    json.dump(meta, open(meta_p, "w"), default=str)
    return {**site, **meta, "times": list(times), "t": t, "td": td}


def qualified(cands):
    """The candidates' records that pass the rule; a linked fallback (climate.isd_sites' "fallback_for") only where its station fails."""
    out, failed = [], set()
    for s in [s for s in cands if "fallback_for" not in s] + [s for s in cands if "fallback_for" in s]:
        if "fallback_for" in s and s["fallback_for"] not in failed:
            continue
        r = record(s)
        if r:
            out.append(r)
        else:
            failed.add(s["id"])
    return out


# --- the two checks ---

def weather_stats(times, t, td):
    from waterledger_models.datacenter.physics import wet_bulb
    times, t, td = np.asarray(times), np.asarray(t, float), np.asarray(td, float)
    summer_pm = np.array([x[5:7] in ("06", "07", "08") and 12 <= int(x[11:13]) < 18 for x in times])
    wb = wet_bulb(t, era5.rh_from(t, td))
    days, at = np.unique(np.array([x[:10] for x in times]), return_inverse=True)
    day_wb = np.bincount(at, wb) / np.bincount(at)
    years = np.array([d[:4] for d in days])
    return {"ddb": float(np.quantile(t, 0.996)), "wb": float(np.quantile(wb, 0.996)),
            "summer_pm": float(t[summer_pm].mean()), "td": float(td.mean()),
            "wb_peak_day": float(np.quantile([day_wb[years == y].max() for y in np.unique(years)], 0.9))}


def _rest(stations, held):
    return [s for s in stations if s["id"] != held["id"] and _km(s["lat"], s["lon"], held["lat"], held["lon"]) > HOLD_KM]


def _cell(cid):
    i, j = era5.indexes(cid)
    return {"lat": i / 4, "lon": j / 4, "land": era5.land(cid), "elev_m": era5.elevation(cid)}


def weather_check(stations):
    """One row per station: the decided rule on its cell, without it, against it; and the cell uncorrected."""
    from waterledger_models import quantile_mapping as Q
    rows = []
    for s in stations:
        times, t, td = era5.local(s["cell"])
        tc, tdc, note = Q.correct(times, t, td, _cell(s["cell"]), _rest(stations, s))
        on = np.isin(np.asarray(times), np.asarray(s["times"]))
        truth = weather_stats(s["times"], s["t"], s["td"])
        raw = weather_stats(np.asarray(times)[on], t[on], td[on])
        dec = weather_stats(np.asarray(times)[on], tc[on], tdc[on])
        rows.append({k: s.get(k) for k in ("id", "name", "state", "source", "lat", "lon", "elev_m", "cell", "cell_land")} | {
            "station": truth, "uncorrected": {k: raw[k] - truth[k] for k in raw}, "decided": {k: dec[k] - truth[k] for k in dec},
            "corrected": note["applied"], "reason": note["reason"], "anchors": note["stations"]})
    return rows


def sample(state, places, stations, n):
    """Up to n (station, place) pairs: for each station in the state, the nearest place within PLACE_KM, one per cell; up to half from
    shore cells, then land cells, each in station id order."""
    pairs, cells = [], set()
    for s in sorted((s for s in stations if s["state"] == state.upper()), key=lambda s: s["id"]):
        best = min(places, key=lambda p: _km(s["lat"], s["lon"], float(p["lat"]), float(p["lon"])))
        d = _km(s["lat"], s["lon"], float(best["lat"]), float(best["lon"]))
        c = era5.cell(float(best["lat"]), float(best["lon"]))["id"]
        if d <= PLACE_KM and c not in cells:
            cells.add(c)
            pairs.append((s, {**best, "cell": c, "km": round(d, 1)}))
    shore = [x for x in pairs if era5.land(x[1]["cell"]) < 0.9]
    land = [x for x in pairs if era5.land(x[1]["cell"]) >= 0.9]
    take = shore[: max((n + 1) // 2, n - len(land))]
    return take + land[: n - len(take)]


def places_check(pairs, stations, workers=6, draws=None, run=None):
    """Each sampled place's cell, corrected without its station, and the station's own record, through the cooling model."""
    from concurrent.futures import ProcessPoolExecutor

    from waterledger_models import quantile_mapping as Q
    from waterledger_models.datacenter import cooling
    from waterledger_models.datacenter.physics import DRAWS
    run, draws = run or cooling.run_location, draws or DRAWS
    jobs, notes = [], []
    for s, p in pairs:
        times, t, td = era5.local(p["cell"])
        tc, tdc, note = Q.correct(times, t, td, _cell(p["cell"]), _rest(stations, s))
        jobs += [(s["times"], list(s["t"]), list(era5.rh_from(s["t"], s["td"]))), (times, list(tc), list(era5.rh_from(tc, tdc)))]
        notes.append(note)
    kw = dict(n=draws, seed=7, mw=100.0)
    if workers <= 1:
        res = [run(*j, **kw) for j in jobs]
    else:
        with ProcessPoolExecutor(workers) as pool:
            futs = [pool.submit(run, *j, **kw) for j in jobs]
            res = [f.result() for f in futs]
    rows = []
    for i, ((s, p), note) in enumerate(zip(pairs, notes)):
        ref, got = res[2 * i], res[2 * i + 1]
        diff = {f"{d}.{x}": 100 * (got[d][x]["p50"] / ref[d][x]["p50"] - 1) for d, x in STATS}
        rows.append({"place": p["name"], "geoid": p["geoid"], "cell": p["cell"], "cell_land": era5.land(p["cell"]), "station": s["name"],
                     "station_id": s["id"], "km": p["km"], "corrected": note["applied"], "reason": note["reason"], "anchors": note["stations"],
                     "difference_pct": diff})
    return rows


# --- the verdict ---

def judge(weather, places):
    """([{id, test, limit, basis, value, pass}], passed). `places` None (not run): the place criteria aren't judged and the check can't
    pass. A shore criterion with fewer than 3 corrected shore cells is not judged (pass None) and doesn't fail the check."""
    land = [r for r in weather if r["cell_land"] >= 0.9]
    shore = [r for r in weather if r["cell_land"] < 0.9 and r["corrected"]]
    med = lambda x: float(np.median(np.abs(x))) if len(x) else None
    e = lambda rows, way, k: np.array([r[way][k] for r in rows])
    v = {"W1": len(land), "W2": med(e(land, "decided", "ddb")), "W3": abs(float(e(land, "decided", "ddb").mean())) if land else None,
         "W4": med(e(land, "decided", "wb"))}
    corrected = [r for r in weather if r["corrected"] and "wb_peak_day" in r["decided"]]
    if corrected:
        v["W7"] = abs(float(e(corrected, "decided", "wb_peak_day").mean()))
    if len(shore) >= 3:
        v["W5"] = med(e(shore, "decided", "ddb"))
        v["W6"] = [v["W5"], med(e(shore, "uncorrected", "ddb"))]
    if places is not None:
        h = np.array([r["difference_pct"]["hybrid.withdrawn_avg"] for r in places])
        v |= {"P1": len(places), "P2": med(h), "P3": abs(float(h.mean())) if len(h) else None,
              "P4": med([r["difference_pct"]["hybrid.withdrawn_peak_1in10"] for r in places]),
              "P5": med([r["difference_pct"]["towers.withdrawn_avg"] for r in places])}
    out = []
    for cid, test, limit, basis in CRITERIA:
        x = v.get(cid)
        if cid not in v:
            ok = None
        elif cid in ("W1", "P1"):
            ok = x >= limit
        elif cid == "W6":
            ok = x[0] <= x[1]
        else:
            ok = x is not None and x <= limit
        out.append({"id": cid, "test": test, "limit": limit, "basis": basis, "value": x, "pass": ok})
    return out, places is not None and all(c["pass"] is not False for c in out)


def markdown(rep):
    f = lambda x: "-" if x is None else (f"{x:.2f}" if isinstance(x, float) else str(x))
    L = [f"# ERA5 check: {rep['state']}", "",
         f"**{rep['verdict'].upper()}** ({rep['date']}; model {rep['model_version']}; design 0005's leave-one-station-out check; "
         f"{rep['stations']} stations).", "", "| Criterion | Test | Limit | Value | Pass | Limit set from |", "|---|---|---|---|---|---|"]
    for c in rep["criteria"]:
        val = " vs ".join(f(x) for x in c["value"]) if isinstance(c["value"], list) else f(c["value"])
        L.append(f"| {c['id']} | {c['test']} | {f(c['limit'])} | {val} | {'not judged' if c['pass'] is None else ('yes' if c['pass'] else '**no**')} | {c['basis']} |")
    W = rep["weather"]
    L += ["", "## Weather at the held-out stations", "", "Median absolute error (mean error), C, against the station on its own hours.", "",
          "| Stations | Way | Design dry-bulb | 0.4% wet bulb | Summer afternoon T | Mean dew point |", "|---|---|---|---|---|---|"]
    groups = [("land cells, corrected", [r for r in W if r["cell_land"] >= 0.9 and r["corrected"]], ["uncorrected", "decided"]),
              ("land cells, no station", [r for r in W if r["cell_land"] >= 0.9 and not r["corrected"]], ["uncorrected"]),
              ("shore cells, corrected", [r for r in W if r["cell_land"] < 0.9 and r["corrected"]], ["uncorrected", "decided"]),
              ("shore cells, no shore station", [r for r in W if r["cell_land"] < 0.9 and not r["corrected"]], ["uncorrected"])]
    for name, rows, ways in groups:
        for w in ways if rows else []:
            cells = [f"{np.median(np.abs(x)):.2f} ({x.mean():+.2f})" for x in (np.array([r[w][k] for r in rows]) for k in ("ddb", "wb", "summer_pm", "td"))]
            L.append(f"| {name} ({len(rows)}) | {w} | " + " | ".join(cells) + " |")
    L += ["", "| Station | Source | Cell land | Design dry-bulb error (C) | Corrected from |", "|---|---|---|---|---|"]
    for r in sorted(W, key=lambda r: r["cell_land"]):
        L.append(f"| {r['name']}, {r['state']} | {r['source']} | {r['cell_land']:.2f} | {r['decided']['ddb']:+.2f} | "
                 + (", ".join(f"{a[1]} {a[2]:.0f} km" for a in r["anchors"]) or r["reason"]) + " |")
    if rep["places"] is not None:
        L += ["", "## Places through the cooling model", "", "The place's cell against the station's own record, p50 per 100 MW, % difference.", "",
              "| Place | Station (km) | Cell land | " + " | ".join(f"{d} {'avg' if s.endswith('avg') else 'peak'}" for d, s in STATS) + " |",
              "|---|---|---|" + "---|" * len(STATS)]
        for r in rep["places"]:
            L.append(f"| {r['place']} | {r['station']} ({r['km']:.0f}) | {r['cell_land']:.2f} | "
                     + " | ".join(f"{r['difference_pct'][f'{d}.{s}']:+.0f}" for d, s in STATS) + " |")
    else:
        L += ["", "Places were not run (--weather-only), so the check can't pass."]
    L += ["", "A fail is a method question for Andrew; the command changes nothing. Criteria: `waterledger.national.era5_check.CRITERIA`."]
    return "\n".join(L) + "\n"


def run_check(state, out=None, n=12, workers=6, draws=None, weather_only=False, places=None, stations=None, run=None, fetch=None):
    """The check for `state`. Writes check.json and check.md to `out` (default CHECK/<ST>/) and returns the report. `places`, `stations`
    (records with times, t and td), `run` and `fetch` stand in for the snapshot, the station records, the model and era5.fetch in tests."""
    from waterledger.national.era5 import RUN_MODEL, state_places
    from waterledger_models import quantile_mapping as Q
    state = state.upper()
    places = places if places is not None else state_places(state)
    if stations is None:
        cands = candidates(state, places)
        _say(f"{state}: {len(cands)} candidate stations")
        stations = qualified(cands)
    for s in stations:
        s["qt"] = Q.fit(s["times"], s["t"], s["td"])
    _say(f"{state}: {len(stations)} stations qualify")
    pairs = [] if weather_only else sample(state, places, stations, n)
    need = sorted({s["cell"] for s in stations} | {p["cell"] for _, p in pairs})
    missing = [c for c in need if not era5.raw_path(c)]
    if missing:
        (fetch or era5.fetch)(missing)
    weather = weather_check(stations)
    pl = None if weather_only else places_check(pairs, stations, workers, draws, run)
    criteria, ok = judge(weather, pl)
    rep = {"state": state, "date": datetime.date.today().isoformat(), "model_version": RUN_MODEL, "verdict": "pass" if ok else "fail",
           "criteria": criteria, "stations": len(stations), "weather": weather, "places": pl}
    out = out or os.path.join(CHECK, state)
    os.makedirs(out, exist_ok=True)
    json.dump(rep, open(os.path.join(out, "check.json"), "w"), indent=1, default=float)
    open(os.path.join(out, "check.md"), "w").write(markdown(rep))
    _say(f"{state}: {rep['verdict']}; {os.path.join(out, 'check.md')}")
    return rep
