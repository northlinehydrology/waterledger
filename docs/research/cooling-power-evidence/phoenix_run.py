"""Model 1.16 run for one cell in memory, as era5.run_part does it, without writing to the cache. Output JSON to the scratchpad."""
import json, os, sys, time
import numpy as np
from waterledger.national import era5 as E
from waterledger_models.datacenter import cooling
from waterledger_models.datacenter.physics import DRAWS
cid, ids, bas, out = sys.argv[1], sys.argv[2].split(","), sys.argv[3].split(","), sys.argv[4]
A = os.path.join(E.CACHE, "era5", "anchors")
stations = []
for i in ids:
    meta = json.load(open(os.path.join(A, i + ".json")))
    assert meta["qualifies"], i
    stations.append({**meta, "shore_land": meta.get("shore_land", meta["cell_land"]), "qt": np.load(os.path.join(A, f"{i}.t-td.npy"))})
t0 = time.time()
times, temps, rhs, note = E.weather(cid, stations)
grid = E.grid_factors(cid, times, temps, bas)
print("weather", note["applied"], note.get("change"), "grid", list(grid), flush=True)
res = cooling.run_plants(times, temps, rhs, n=DRAWS, seed=E.SEED, mw=E.MW, grid=grid)
rec = {"cell": cid, "model_version": E.RUN_MODEL, "draws": DRAWS, "seed": E.SEED, "correction": {k: v for k, v in note.items() if k != "stations"},
       "grid": {"bas": bas}, "design_dry_bulb_c": float(cooling.design_dry_bulb(np.array(temps))) if hasattr(cooling, "design_dry_bulb") else None, **E.by_plant(res)}
json.dump(rec, open(out, "w"), default=float)
print("done", round(time.time() - t0), "s")
