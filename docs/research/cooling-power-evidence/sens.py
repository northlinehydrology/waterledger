"""One at a time: dry minus towers, year-average PUE and hottest-hour PUE (median year), at central parameters on a cell's corrected weather."""
import json, os, sys
import numpy as np
from waterledger.national import era5 as E
from waterledger_models import heat_rejection as hr
from waterledger_models.datacenter import physics as P
cid, ids = sys.argv[1], sys.argv[2].split(",")
A = os.path.join(E.CACHE, "era5", "anchors")
st = [{**m, "shore_land": m.get("shore_land", m["cell_land"]), "qt": np.load(os.path.join(A, f"{i}.t-td.npy"))}
      for i in ids for m in [json.load(open(os.path.join(A, i + ".json"), encoding="utf-8"))]]
times, t, rh, note = E.weather(cid, st)
tdb, rh = np.array(t), np.array(rh); twb = hr.wet_bulb(tdb, rh)
years = np.array([x[:4] for x in times]); yi = [np.flatnonzero(years == y) for y in np.unique(years)]
def stats(d, p):
    pw, _ = P.hourly_heat_power(tdb, twb, d, p, rh)
    return pw.mean(), float(np.median([pw[i].max() for i in yi]))
def gap(plant="shared", **kw):
    p = P.for_location({**P.central_parameters(plant), **kw}, tdb)
    if plant != "warm" and P.SHARED[plant]:
        p = P.with_plant(p, plant)
    a, b = stats("dry", p), stats("towers", p)
    return a, b
rows = [("central", {}), ("supply_air 24", {"supply_air": 24.0}), ("supply_air 30", {"supply_air": 30.0}),
        ("liquid_share 0", {"liquid_share": 0.0}), ("liquid_share 1", {"liquid_share": 1.0}),
        ("carnot_air 0.571", {"carnot_air": 0.571}), ("carnot_air 0.761", {"carnot_air": 0.761}),
        ("air_cop_cap 5", {"air_cop_cap": 5.0}), ("air_cop_cap 7.6", {"air_cop_cap": 7.6}),
        ("dc_approach 5", {"dc_approach": 5.0}), ("dc_approach 10", {"dc_approach": 10.0}),
        ("water_rise 5", {"water_rise": 5.0}), ("water_rise 10", {"water_rise": 10.0}),
        ("tower_approach 2.8", {"tower_approach": 2.8}), ("tower_approach 6.7", {"tower_approach": 6.7}),
        ("ups 0.99", {"ups": 0.99})]
print(cid)
for lab, kw in rows:
    (da, dp), (ta, tp) = gap(**kw)
    print(f"{lab:20s} dry {da:.3f}/{dp:.3f} towers {ta:.3f}/{tp:.3f}  gap avg {da-ta:+.3f} ({(da/ta-1)*100:+.1f}%) peak {dp-tp:+.3f} ({(dp/tp-1)*100:+.1f}%)")
