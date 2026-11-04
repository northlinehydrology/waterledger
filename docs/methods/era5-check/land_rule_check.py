"""The station check's part-water places on the land rule (Nov 3, 2026), and, as a sensitivity only, on the nearest cell
at least 90% land. Same runs as station_check.py (model 1.7, run_location, 400 draws, seed 7, per 100 MW).
Fetch the cells first: python -I era5_fetch.py ERA5_DIR lat,lon ... (the cells this prints with --cells).
Writes land_rule_results.json beside this file. Usage: python land_rule_check.py SCRATCH ERA5_DIR [--cells]"""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor

import land_rule as lr
from station_check import run

HERE = os.path.dirname(os.path.abspath(__file__))
PLACES = ["3944856", "5182000", "3916000", "2614765820", "3977000"]     # Lorain, Virginia Beach, Cleveland, Port Huron, Toledo

if __name__ == "__main__":
    lr.load(sys.argv[1])
    era5_dir = sys.argv[2]
    d = json.load(open(os.path.join(HERE, "station_check_results.json")))
    rows = [r for g in PLACES for r in d["rows"] if r["geoid"] == g]
    for r in rows:
        ni, nj = round(r["lat"] * 4), round(r["lon"] * 4)
        cells = {"nearest": (ni, nj),
                 "rule": lr.nearest_land(r["lat"], r["lon"]) if lr.land(ni, nj) < lr.LAND else (ni, nj),
                 "land_0.9": lr.nearest_land(r["lat"], r["lon"], 0.9) if lr.land(ni, nj) < 0.9 else (ni, nj)}
        r["cells"] = {k: {"cell": lr.cid(*c), "km": round(lr.km(r["lat"], r["lon"], c[0] / 4, c[1] / 4), 1), "land": round(lr.land(*c), 3)}
                      for k, c in cells.items()}
    if "--cells" in sys.argv:
        print(" ".join(sorted({c["cell"].replace("_", ",") for r in rows for c in r["cells"].values()})))
        sys.exit()
    todo = sorted({c["cell"] for r in rows for c in r["cells"].values()} - {r["cells"]["nearest"]["cell"] for r in rows})
    with ProcessPoolExecutor(6) as pool:
        done = dict(zip(todo, (res for _, _, res in pool.map(run, [("era5", c, os.path.join(era5_dir, c + ".json")) for c in todo]))))
    out = []
    for r in rows:
        res = {k: (r["era5"] if c["cell"] == r["cells"]["nearest"]["cell"] else done[c["cell"]]) for k, c in r["cells"].items()}
        out.append({k: r[k] for k in ("state", "geoid", "name", "lat", "lon", "published", "nearest_station", "cells")} |
                   {"station": r["nearest"] or r["published"], "era5": res})
    json.dump({"rows": out}, open(os.path.join(HERE, "land_rule_results.json"), "w"), indent=1)
    print("wrote land_rule_results.json,", len(todo), "new cells run")
