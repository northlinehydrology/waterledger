"""Leave-one-station-out check of station correction on land cells (cells at least 90% land), in the five states.

For each state: every qualifying station in it or within 100 km of one of its places (era5_check.candidates and qualified), held
out in turn with any other within 5 km. Its cell (the land rule's), when a land cell, is corrected from the stations left by each way
below, and compared with the held-out station on its own hours. Shore cells are left to the decided rule and not reported here.
Usage: python land_cv.py OUT ST [ST ...]"""
import json, os, sys
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from waterledger.national import era5_check as C
from waterledger.national.era5 import state_places
from waterledger_data import era5
from waterledger_models import quantile_mapping as Q

LAND = 0.9
WAYS = {
    "none": None,
    "any_100": dict(r_km=100, k=4, shore_only=False),
    "any_50": dict(r_km=50, k=4, shore_only=False),
    "nearest_100": dict(r_km=100, k=1, shore_only=False),
    "land_100": dict(r_km=100, k=4, land_only=True),
    "land_50": dict(r_km=50, k=4, land_only=True),
    "land_100_nolapse": dict(r_km=100, k=4, land_only=True, lapse=False),
}


def delta(cell, stations, r_km, k, shore_only=False, land_only=False, lapse=True):
    pool = [s for s in stations if s["shore_land"] >= LAND] if land_only else stations
    return Q.delta(cell, pool, lapse=lapse, r_km=r_km, k=k, shore_only=shore_only)


def run_state(st, out):
    places = state_places(st)
    cands = C.candidates(st, places)
    cached = lambda s: os.path.exists(os.path.join(C.CHECK, "stations", s["id"] + ".json"))
    skip = [s["id"] for s in cands if s["source"] == "eccc" and not cached(s)]
    cands = [s for s in cands if s["id"] not in skip]       # ECCC's API retries empty years for minutes; uncached ECCC sites are shore stations here
    if skip:
        C._say(f"{st}: skipped uncached ECCC {skip}")
    C._say(f"{st}: {len(cands)} candidates")
    import time
    def rec(s):
        if "fallback_for" in s:
            return
        t0 = time.time(); r = C.record(s)
        if time.time() - t0 > 5:
            C._say(f"  {s['id']} {s['source']} {s.get('name')}: {time.time() - t0:.0f} s, {'ok' if r else 'fails'}")
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(rec, cands))
    C._say(f"{st}: records done")
    stations = C.qualified(cands)
    for s in stations:
        s["qt"] = Q.fit(s["times"], s["t"], s["td"])
    land = [s for s in stations if s["cell_land"] >= LAND]
    C._say(f"{st}: {len(stations)} qualify, {len(land)} on land cells")
    missing = sorted({s["cell"] for s in land if not era5.raw_path(s["cell"])})
    if missing:
        C._say(f"{st}: fetching {len(missing)} cells")
        era5.fetch(missing)
    rows = []
    for s in land:
        times, t, td = era5.local(s["cell"])
        times = np.asarray(times)
        on = np.isin(times, np.asarray(s["times"]))
        truth = C.weather_stats(s["times"], s["t"], s["td"])
        cell = C._cell(s["cell"])
        qe = Q.fit(times, t, td)
        rest = C._rest(stations, s)
        res = {}
        for name, kw in WAYS.items():
            d = None if kw is None else delta({**cell, "qe": qe}, rest, **kw)
            tc, tdc = (t, td) if d is None else Q.apply(times, t, td, qe, d)
            got = C.weather_stats(times[on], tc[on], tdc[on])
            res[name] = {k: got[k] - truth[k] for k in got} | {"corrected": d is not None}
        rows.append({k: s.get(k) for k in ("id", "name", "state", "source", "lat", "lon", "elev_m", "cell", "cell_land", "shore_land")}
                    | {"cell_elev_m": cell["elev_m"], "ways": res})
    json.dump(rows, open(os.path.join(out, f"{st}.json"), "w"), indent=1, default=float)
    return rows


def summary(rows):
    out = {}
    for w in WAYS:
        e = lambda k: np.array([r["ways"][w][k] for r in rows])
        out[w] = {k: (float(np.median(np.abs(e(k)))), float(e(k).mean())) for k in ("ddb", "wb", "summer_pm", "td")}
        out[w]["corrected"] = int(sum(r["ways"][w]["corrected"] for r in rows))
    return out


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    allrows = []
    for st in sys.argv[2:]:
        rows = run_state(st.upper(), out)
        allrows += rows
        s = summary(rows)
        print(f"== {st.upper()} ({len(rows)} land stations)", flush=True)
        for w, v in s.items():
            print(f"  {w:18s} n={v['corrected']:3d}  " + "  ".join(f"{k} {v[k][0]:.2f} ({v[k][1]:+.2f})" for k in ("ddb", "wb", "summer_pm", "td")), flush=True)
    seen = {}
    for r in allrows:
        seen.setdefault(r["id"], r)
    s = summary(list(seen.values()))
    print(f"== all five, distinct stations ({len(seen)})", flush=True)
    for w, v in s.items():
        print(f"  {w:18s} n={v['corrected']:3d}  " + "  ".join(f"{k} {v[k][0]:.2f} ({v[k][1]:+.2f})" for k in ("ddb", "wb", "summer_pm", "td")), flush=True)
