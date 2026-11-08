"""Model 1.9's cooling runs: the cooling Monte Carlo on each place's ERA5 cell (design 0004), corrected toward nearby stations by quantile
mapping (design 0005; shore cells from model 1.8, land cells from 1.9), one result file per cell. `waterledger era5 run ST --part k/n --workers 10` runs one part by hand.

    state_cells(ST)         {cell: {"cell": era5.cell's record, "places": [geoid, ...]}} for every place in the state's snapshot
    part(cells, k, n)       the k-th of n parts: the cells in id order, cut into n runs of near-equal size
    anchors(cells)          the stations that can correct these cells, qualified and fitted once (cached)
    run_part(ST, k, n)      fetch the part's weather, correct it, run each cell and write CACHE/era5/runs/model<RUN_MODEL>/<cell>.json

A cell's result is written the moment it finishes, so a stopped part resumes where it stopped. With R2 set up (waterledger_data.r2:
WATERLEDGER_R2=wrangler, or R2 credentials in the environment), each raw cell series is uploaded as it is fetched and each result as it
is written, both skipped when R2 already has the same file; and before a part starts, results and raw series already in R2 are pulled,
so a part can be restarted on another machine. An upload that fails warns and leaves the local file; it never stops the run.
"""
import json, os, re, sys

import numpy as np

from waterledger_data import era5
from waterledger_data.config import CACHE

RUN_MODEL = "1.9"           # the cooling model on ERA5 cell weather, corrected toward stations near the shore and, from 1.9, inland; from 1.10 each cooling plant: what these runs are for
SEED, MW = 7, 100.0


def default_workers():
    """Cells at once: the machine's performance cores where macOS reports them (10 on Andrew's M3 Max), else every core. With the runs
    worked in hour blocks a cell takes about as long with nine others as alone; more than the performance cores was not measured (0004, section 3)."""
    import subprocess
    try:
        return int(subprocess.run(["sysctl", "-n", "hw.perflevel0.physicalcpu"], capture_output=True, text=True, timeout=5).stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return os.cpu_count() or 1
RUNS = os.path.join(CACHE, "era5", "runs", f"model{RUN_MODEL}")
ANCHORS = os.path.join(CACHE, "era5", "anchors")
R2_RUNS = f"runs/era5/model{RUN_MODEL}"


def _say(msg):
    print(msg, file=sys.stderr, flush=True)


def state_places(state, date=None):
    """The places in the state's snapshot (the latest for this package's model, or `date`), each with geoid, name, level, lat and lon;
    for a state with no snapshot published or cached, the places of its local build (`waterledger build-state ST`), the same set."""
    from waterledger.national.data import _newest_cached, fetch_snapshot
    state = state.upper()
    try:
        folder = fetch_snapshot(state, date)
    except Exception as e:                                  # noqa: BLE001  offline: the newest complete copy we have
        folder = None if date else _newest_cached(state)
        if not folder and not date and state != "MI":       # a state not yet published: its local build's places, the ones its snapshot will carry
            from waterledger.national.data import LiveData
            _say(f"{state}: no snapshot reachable or cached ({type(e).__name__}); using the places of its local build")
            pl = LiveData(state).places()
            return [{"geoid": r.geoid, "name": r.name, "level": r.level, "lat": float(r.lat), "lon": float(r.lon)} for r in pl.itertuples()]
        if not folder:
            raise RuntimeError(f"no {state} snapshot reachable or cached ({type(e).__name__}: {e})") from e
    d = json.load(open(os.path.join(folder, "places.json")))
    rows = d["places"] if isinstance(d, dict) and "places" in d else d
    rows = list(rows.values()) if isinstance(rows, dict) else rows
    return [{k: r[k] for k in ("geoid", "name", "level", "lat", "lon")} for r in rows]


def state_cells(state, date=None, places=None):
    """{cell id: {"cell": era5.cell's record at the cell, "places": [{geoid, name, km, moved}]}} for the state's places."""
    out = {}
    for p in places if places is not None else state_places(state, date):
        c = era5.cell(float(p["lat"]), float(p["lon"]))
        e = out.setdefault(c["id"], {"cell": {k: c[k] for k in ("id", "lat", "lon", "land")}, "places": []})
        e["places"].append({"geoid": p["geoid"], "name": p.get("name"), "km": round(c["km"], 2), "moved": c["moved"],
                            **({"nearest": c["nearest"]["id"], "nearest_km": round(c["nearest"]["km"], 2), "nearest_land": c["nearest"]["land"]} if c["moved"] else {})})
    return dict(sorted(out.items()))


def part(cells, k, n):
    """The k-th (1-based) of n parts of `cells`, in id order, near-equal in size, so parts never overlap and together cover every cell."""
    ids = sorted(cells)
    if not 1 <= k <= n:
        raise ValueError(f"part {k}/{n}: k must be 1 to {n}")
    lo, hi = (k - 1) * len(ids) // n, k * len(ids) // n
    return ids[lo:hi]


def parse_part(text):
    m = re.fullmatch(r"(\d+)/(\d+)", text or "1/1")
    if not m:
        raise ValueError(f"--part {text!r}: give k/n, such as 2/3")
    return int(m[1]), int(m[2])


# --- anchors: the stations that correct the cells (design 0005) -------------------------------------------------------------------

def _elevations():
    """ISD's station elevations (m) by USAF-WBAN, from isd-history."""
    import csv

    from waterledger_data import climate
    path = climate._fetch(climate.ISD_HISTORY, os.path.join(climate.RAW, "isd", "isd-history.csv"))
    bad = ("", "-999", "-999.0", "-0999.0", "+9999.0")
    return {f"{r['USAF']}-{r['WBAN']}": float(r["ELEV(M)"]) for r in csv.DictReader(open(path)) if r["ELEV(M)"] not in bad}


def candidates(cells):
    """The ISD (one ID or linked) and ECCC sites that could correct a cell in `cells`, before the 85% rule: for a shore cell, those within
    R_KM whose own nearest cell is a shore cell; for a land cell (model 1.9), those within R_KM whose own nearest cell is a land cell. `cells`: {id: {"cell": {lat, lon, land}}}.
    A station keeps its land-rule cell (`cell`, `cell_land`) as a place there would get it, and is judged a shore station by its nearest
    (`shore_land`; Nov 5)."""
    from waterledger_data import climate
    from waterledger_models import quantile_mapping as Q
    if not cells:
        return []
    pts = np.array([(c["cell"]["lat"], c["cell"]["lon"]) for c in cells.values()])
    shore = np.array([c["cell"]["land"] < Q.SHORE_LAND for c in cells.values()])
    elev = _elevations()
    sites = [{**s, "source": "isd-linked" if "parts" in s else "isd", "elev_m": elev.get(s.get("fallback_for", s["id"]))} for s in climate.isd_sites()]
    sites += [{**s, "source": "eccc"} for s in climate.eccc_sites()]
    out = []
    for s in sites:
        near_cells = Q.km(pts[:, 0], pts[:, 1], s["lat"], s["lon"]) <= Q.R_KM
        if not near_cells.any():
            continue
        try:
            own, near = era5.cell(s["lat"], s["lon"]), era5.cell(s["lat"], s["lon"], land=None)
        except ValueError:                                  # outside the shipped grid
            continue
        on_shore = near["land"] < Q.SHORE_LAND
        if (near_cells & (shore if on_shore else ~shore)).any():
            out.append({**s, "cell": own["id"], "cell_land": own["land"], "shore_land": near["land"]})
    return out


def anchor(site, store=None):
    """One station qualified under the snapshots' rule and fitted (quantile_mapping.fit on its own hours), cached in ANCHORS as
    <id>.json (and <id>.<quantile_mapping.FIT>.npy, its quantiles): the station record quantile_mapping.correct takes, or None if it fails the 85% rule."""
    from waterledger_data import climate
    from waterledger_models import quantile_mapping as Q
    os.makedirs(ANCHORS, exist_ok=True)
    q_name = f"{site['id']}.{Q.FIT}.npy"                   # the fit is keyed by what it fits (model 1.10: T and Td); a fit of another kind is never reused
    meta_path, q_path = os.path.join(ANCHORS, site["id"] + ".json"), os.path.join(ANCHORS, q_name)
    if not os.path.exists(meta_path) and store:
        store.get(f"anchors/{site['id']}.json", meta_path)
    if not os.path.exists(q_path) and store:
        store.get(f"anchors/{q_name}", q_path)
    if os.path.exists(meta_path):
        meta = json.load(open(meta_path))
        if not meta["qualifies"]:
            return None
        if os.path.exists(q_path):
            return {**meta, "shore_land": site.get("shore_land", meta["cell_land"]), "qt": np.load(q_path)}
    got = (climate.eccc_hourly if site["source"] == "eccc" else climate.isd_hourly)(site)
    keep = ("id", "name", "state", "source", "lat", "lon", "elev_m", "cell", "cell_land", "shore_land", "parts", "fallback_for")
    meta = {k: site[k] for k in keep if k in site} | {"qualifies": bool(got)}
    if got:
        times, t, rh, share, screen = got
        t = np.asarray(t, float)
        g = np.log(np.asarray(rh, float) / 100) + era5.MAGNUS[0] * t / (era5.MAGNUS[1] + t)
        td = era5.MAGNUS[1] * g / (era5.MAGNUS[0] - g)
        np.save(q_path, Q.fit(times, t, td))
        meta |= {"share_observed": share, "screen": screen}
    json.dump(meta, open(meta_path, "w"), indent=1, default=str)
    if store:
        store.put(f"anchors/{site['id']}.json", meta_path)
        if got:
            store.put(f"anchors/{q_name}", q_path)
    return {**meta, "shore_land": site.get("shore_land", meta["cell_land"]), "qt": np.load(q_path)} if got else None


def anchors(cells, store=None):
    """The qualified stations for `cells` (quantile_mapping's station records). A linked fallback (climate.isd_sites' "fallback_for")
    is tried only where its station fails the 85% rule on its own ID, so a station that qualifies keeps its own record."""
    out, failed = [], set()
    cands = candidates(cells)
    for s in [s for s in cands if "fallback_for" not in s] + [s for s in cands if "fallback_for" in s]:
        if "fallback_for" in s and s["fallback_for"] not in failed:
            continue
        a = anchor(s, store)
        if a:
            out.append(a)
        else:
            failed.add(s["id"])
    return out


# --- runs ---------------------------------------------------------------------------------------------------------

def result_path(cid):
    return os.path.join(RUNS, f"{cid}.json")


def _summer_pm(times, t):
    m = np.array([x[5:7] in ("06", "07", "08") and 12 <= int(x[11:13]) < 18 for x in times])
    return float(np.mean(np.asarray(t)[m]))


def weather(cid, stations):
    """A cell's run weather: (times, temp_c, rh_pct, correction note), corrected under 0005 where a station is near enough (a shore cell from
    shore stations within 100 km; from model 1.9 a land cell from land stations within 100 km). The note records what was done and the change it made."""
    from waterledger_models import quantile_mapping as Q
    from waterledger_models.datacenter.physics import design_dry_bulb
    times, t, td = era5.local(cid)
    c = {"lat": era5.indexes(cid)[0] / 4, "lon": era5.indexes(cid)[1] / 4, "land": era5.land(cid), "elev_m": era5.elevation(cid)}
    tc, tdc, note = Q.correct(times, t, td, c, stations)
    if note["applied"]:
        note["change"] = {"design_dry_bulb_c": [design_dry_bulb(t), design_dry_bulb(tc)], "summer_afternoon_c": [_summer_pm(times, t), _summer_pm(times, tc)],
                          "mean_dew_point_c": [float(td.mean()), float(tdc.mean())]}
        by_id = {s["id"]: s for s in stations}
        note["stations"] = [{"id": i, "name": n, "source": by_id[i]["source"], "km": k, "weight": w, "elev_m": by_id[i].get("elev_m")}
                            for i, n, k, w in note["stations"]]
    return times, list(tc), list(era5.rh_from(tc, tdc)), note


def _record(cid, cells, times, temps, note, res, draws):
    from waterledger_models.datacenter.physics import design_dry_bulb
    raw = era5.raw_path(cid)
    meta = json.load(open(raw[:-4] + ".json"))
    c = cells[cid]["cell"]
    return {"cell": cid, "lat": c["lat"], "lon": c["lon"], "land": c["land"], "elev_m": era5.elevation(cid), "model_version": RUN_MODEL,
            "draws": draws, "seed": SEED, "mw": MW, "period": f"{era5.FIRST}-{era5.LAST}", "hours": len(times), "time": "local standard",
            "design_dry_bulb_c": design_dry_bulb(temps), "correction": note,
            "weather": {"source": meta["request"]["source"], "fetched": meta["fetched"], "sha256": meta["sha256"], "attribution": era5.ATTRIBUTION,
                        "citation": era5.CITATION},
            **by_plant(res)}


def by_plant(res):
    """A run's results as a cell record carries them: per_100mw for the default plant, per_100mw_plants for the others (model 1.10). A run of one plant
    (cooling.run_location, or a stand-in in tests) is the default's."""
    from waterledger_models.datacenter.physics import DEFAULT_PLANT, PLANTS
    if not set(res) <= set(PLANTS):
        return {"per_100mw": res}
    return {"plant": DEFAULT_PLANT, "per_100mw": res[DEFAULT_PLANT], "per_100mw_plants": {k: v for k, v in res.items() if k != DEFAULT_PLANT}}


def _raw_keys(cid):
    path = era5.raw_path(cid)
    date = os.path.basename(path)[:-4]
    return [(f"era5/{cid}/{date}.npz", path), (f"era5/{cid}/{date}.json", path[:-4] + ".json")]


def push_raw(store, cid):
    """Upload a cell's raw series and its record to era5/<cell>/<fetch date>, and point era5/<cell>/latest.json at them."""
    ok = all(store.put(k, p) for k, p in _raw_keys(cid))
    if ok:
        store.put(f"era5/{cid}/latest.json", era5.raw_path(cid)[:-4] + ".json")
    return ok


def pull(store, ids):
    """Before a part starts: copy down the results and raw series R2 has and this machine doesn't. Returns (results, raw) counts."""
    from concurrent.futures import ThreadPoolExecutor

    def one(cid):
        res = os.path.exists(result_path(cid)) or store.get(f"{R2_RUNS}/{cid}.json", result_path(cid))
        raw = bool(era5.raw_path(cid))
        if not raw:
            d = os.path.join(era5.RAW, cid)
            latest = os.path.join(d, ".r2-latest.json")
            if store.get(f"era5/{cid}/latest.json", latest):
                date = json.load(open(latest))["fetched"]
                raw = store.get(f"era5/{cid}/{date}.json", os.path.join(d, f"{date}.json")) and store.get(f"era5/{cid}/{date}.npz", os.path.join(d, f"{date}.npz"))
                os.remove(latest)
        return bool(res), bool(raw)
    with ThreadPoolExecutor(8) as pool:
        got = list(pool.map(one, ids))
    return sum(r for r, _ in got), sum(w for _, w in got)


def _ignore_interrupts():
    """A worker's start: Ctrl-C goes to the whole terminal's process group, and only the main process should act on it."""
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _stop(pool):
    """Cancel the cells not started and end the workers now; a cell in progress is lost and runs again next time. The workers are
    taken before shutdown, which forgets them, and ended first, so the pool's manager thread sees them gone and Python's exit, which
    joins that thread, doesn't wait on cells that will never finish."""
    procs = list((getattr(pool, "_processes", None) or {}).values())
    for p in procs:
        p.terminate()
    pool.shutdown(wait=False, cancel_futures=True)
    for p in procs:
        p.join(5)


def run_part(state, k=1, n=1, workers=6, draws=None, store=None, cells=None, run=None, fetch=None):
    """Run part k of n of a state's cells, every cooling plant (cooling.run_plants); return {cell: result path}. `run` and `fetch` stand in for cooling.run_plants and
    era5.fetch in tests; `cells` for state_cells(state).

    Ctrl-C stops it cleanly: the cells not started are cancelled and the workers ended (a cell in progress runs again next time),
    uploads under way finish, and uploads not yet started are dropped with a warning; the next start uploads them, since it sends
    every done cell's result and raw series that R2 doesn't have (skipped by checksum where it does)."""
    from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

    from waterledger_models.datacenter import cooling
    from waterledger_models.datacenter.physics import DRAWS
    draws = draws or DRAWS
    run, fetch = run or cooling.run_plants, fetch or era5.fetch
    cells = cells if cells is not None else state_cells(state)
    ids = part(cells, k, n)
    _say(f"{state.upper()} part {k}/{n}: {len(ids)} cells" + (f"; R2 ({store.name}) on" if store else "; R2 off"))
    if store:
        res, raw = pull(store, ids)
        _say(f"from R2: {res} results, {raw} raw series already there")
    todo = [c for c in ids if not os.path.exists(result_path(c))]
    missing = [c for c in todo if not era5.raw_path(c)]
    if missing:
        _say(f"fetching {len(missing)} cells from the open copy")
        fetch(missing)
    stations = anchors({c: cells[c] for c in todo}, store) if todo else []
    _say(f"{len(ids) - len(todo)} cells done before, {len(todo)} to run; {len(stations)} stations to correct them")
    os.makedirs(RUNS, exist_ok=True)
    out = {c: result_path(c) for c in ids if c not in todo}
    uploads, sent = ThreadPoolExecutor(2), []               # uploads go up while the cells run; put() never raises
    if store:
        for c in ids:                                       # every cell's raw series, and the results already done: skipped by checksum where R2 has them
            if era5.raw_path(c):
                sent.append(uploads.submit(push_raw, store, c))
            if c in out:
                sent.append(uploads.submit(store.put, f"{R2_RUNS}/{c}.json", out[c]))

    def finish(cid, times, temps, note, res):
        path = result_path(cid)
        json.dump(_record(cid, cells, times, temps, note, res, draws), open(path + ".part", "w"))
        os.replace(path + ".part", path)
        out[cid] = path
        if store:
            sent.append(uploads.submit(store.put, f"{R2_RUNS}/{cid}.json", path))
        _say(f"  {cid} done ({len(out)}/{len(ids)})" + (", corrected" if note["applied"] else ""))

    interrupted = False
    try:
        if workers <= 1:
            for cid in todo:
                times, temps, rhs, note = weather(cid, stations)
                finish(cid, times, temps, note, run(times, temps, rhs, n=draws, seed=SEED, mw=MW))
            return out
        pool = ProcessPoolExecutor(workers, initializer=_ignore_interrupts)
        try:
            queue, live = list(todo), {}
            while queue or live:
                while queue and len(live) < 2 * workers:        # weather for a few cells ahead, not the whole part, in memory
                    cid = queue.pop(0)
                    times, temps, rhs, note = weather(cid, stations)
                    live[pool.submit(run, times, temps, rhs, n=draws, seed=SEED, mw=MW)] = (cid, times, temps, note)
                done = next(as_completed(live))
                cid, times, temps, note = live.pop(done)
                finish(cid, times, temps, note, done.result())
        except BaseException:
            _stop(pool)
            raise
        pool.shutdown(wait=True)
        return out
    except KeyboardInterrupt:
        interrupted = True
        _say(f"interrupted: {len(out)} of {len(ids)} cells done and kept; the cells in progress run again next time")
        raise
    finally:
        if interrupted:
            dropped = sum(f.cancel() for f in sent)
            if dropped:
                _say(f"Water Ledger R2: {dropped} uploads not started were dropped; the next start sends them")
            _say("waiting for the uploads under way to finish")
        uploads.shutdown(wait=True)
