"""station-distance-check.md, rerun on model 1.7 with ERA5's nearest cell as a third column.

For each sample place: the published point's p50 from the 2026-11-02.2 snapshot (its division's station, or Michigan's region point), the nearest
qualifying ISD station searched from the place's own point (same rule as the snapshots), and ERA5 at the place's nearest 0.25-degree cell
(1995-2024, local standard time from longitude, RH from T and Td by the stations' Magnus form). run_location, 400 draws, seed 7, per 100 MW.
Writes station_check.json. Usage: python station_check.py ERA5_DIR OUT.json [workers]"""
import json, math, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np

from waterledger_data.config import CACHE
SNAP = os.path.join(CACHE, "snapshots")       # the 2026-11-02.2 snapshots, cached by the package
SAMPLE = {"TX": ["4805000", "4865000", "4863500", "4819000", "4824000", "4803000", "4835000", "4845000"],
          "VA": ["5182000", "5109816", "51107", "5167000", "5168000"],
          "OH": ["3944856", "3977000", "3915000", "3916000", "3918000"],
          "MI": ["2614765820", "2605341060", "2608131240"]}
STATS = [(d, s) for d in ("towers", "hybrid", "assist") for s in ("withdrawn_avg", "withdrawn_peak_1in10")]


def km(a, b, c, d):
    p = math.pi / 180
    h = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def pick(res):
    return {f"{d}.{s}": res[d][s]["p50"] for d, s in STATS}


def era5(path):
    from waterledger_models.weather import to_local_standard
    h = json.load(open(path))
    lon = h["longitude"]
    times, keep = to_local_standard(h["hourly"]["time"], lon, "1995-01-01", "2024-12-31")
    t = np.array(h["hourly"]["temperature_2m"])[keep]
    d = np.array(h["hourly"]["dew_point_2m"])[keep]
    a = lambda x: np.exp(17.625 * x / (243.04 + x))
    return times, t, np.clip(100 * a(d) / a(t), 1, 100)


def run(job):
    kind, key, arg = job
    from waterledger_models.datacenter import cooling as cw
    from waterledger_models.datacenter.physics import design_dry_bulb
    if kind == "era5":
        times, t, rh = era5(arg)
    else:
        from waterledger_data import climate
        got = climate.isd_hourly(arg)
        times, t, rh = got[0], np.array(got[1]), np.array(got[2])
    res = cw.run_location(times, t, rh)
    return kind, key, {**pick(res), "design_db": design_dry_bulb(t), "mean_t": float(np.mean(t)), "mean_rh": float(np.mean(rh)), "hours": len(t)}


if __name__ == "__main__":
    era5_dir, out_path = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 12
    from waterledger_data import climate
    stations = climate.isd_stations()
    rows, jobs = [], []
    for st, ids in SAMPLE.items():
        places = json.load(open(f"{SNAP}/{st}/2026-11-02.2/places.json"))["places"]
        places = places if isinstance(places, dict) else {p["geoid"]: p for p in places}
        clim = json.load(open(f"{SNAP}/{st}/2026-11-02.2/climate.json"))["divisions"]
        for g in ids:
            p = places[g]
            div = clim[p["division"]]
            lat, lon = float(p["lat"]), float(p["lon"])
            cell = (round(lat * 4) / 4, round(lon * 4) / 4)
            near = None
            for d_km, s in sorted((km(lat, lon, s["lat"], s["lon"]), s) for s in stations):
                if d_km > 250:
                    break
                got = climate.isd_hourly(s)
                if got:
                    near = {**s, "km": round(d_km, 1), "share_observed": round(got[3], 3)}
                    break
            row = {"state": st, "geoid": g, "name": p["name"], "lat": lat, "lon": lon,
                   "published": {"point": div.get("station") or div.get("name"), "station_id": div.get("station_id"), "km": round(km(lat, lon, div["lat"], div["lon"]), 1),
                                 **pick(div["per_100mw"])},
                   "nearest_station": near, "era5_cell": {"lat": cell[0], "lon": cell[1], "km": round(km(lat, lon, *cell), 1)}}
            rows.append(row)
            jobs.append(("era5", g, os.path.join(era5_dir, f"{cell[0]:.2f}_{cell[1]:.2f}.json")))
            if near and near["id"] != div.get("station_id"):
                jobs.append(("station", g, near))
    # one published point rerun from its station record, to show the runs here reproduce the snapshot
    oh = json.load(open(f"{SNAP}/OH/2026-11-02.2/climate.json"))["divisions"]["3301"]
    jobs.append(("check", "OH 3301", next(s for s in stations if s["id"] == oh["station_id"])))
    with ProcessPoolExecutor(workers) as pool:
        done = list(pool.map(run, [(("station" if k == "check" else k), key, a) for k, key, a in jobs]))
    by = {}
    for (k0, key, _), (kind, _, res) in zip(jobs, done):
        by[(k0, key)] = res
    for r in rows:
        r["era5"] = by[("era5", r["geoid"])]
        r["nearest"] = by.get(("station", r["geoid"]))         # None: the published station is already the nearest qualifying one
    check = {"published": pick(oh["per_100mw"]), "rerun": by[("check", "OH 3301")]}
    json.dump({"rows": rows, "reproduction_check": check}, open(out_path, "w"), indent=1)
    print("wrote", out_path, len(rows), "places,", len(jobs), "runs")
