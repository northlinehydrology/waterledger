"""Where the electricity goes, by design and plant, at central parameters, on a cell's corrected ERA5 weather (model 1.16 code, read only).
Year average (at the central utilization) and the hottest hour (the year's highest-PUE hour, median over the 30 years, full capacity), kW per IT kW."""
import json, os, sys
import numpy as np
from waterledger.national import era5 as E
from waterledger_models import heat_rejection as hr
from waterledger_models.datacenter import physics as P
cid, ids = sys.argv[1], sys.argv[2].split(",")
A = os.path.join(E.CACHE, "era5", "anchors")
st = []
for i in ids:
    m = json.load(open(os.path.join(A, i + ".json")))
    st.append({**m, "shore_land": m.get("shore_land", m["cell_land"]), "qt": np.load(os.path.join(A, f"{i}.t-td.npy"))})
times, t, rh, note = E.weather(cid, st)
tdb, rh = np.array(t), np.array(rh)
twb = hr.wet_bulb(tdb, rh)
years = np.array([x[:4] for x in times])

def parts(design, p):
    q = 1.0 + (1.0 / p["ups"] - 1.0) + (1.0 / (1.0 - p["dist_loss"]) - 1.0) + p["light"]
    air = (1.0 - p["liquid_share"]) + p["liquid_share"] * p["liquid_air_share"]
    kg_s = P._outside_air(tdb, twb, p, rh)[0]
    room = q - (1.0 - air)
    crah = hr._fan_kw(room / (P.CP_AIR * p["air_rise"]) + kg_s, p["crah_pa"], p["fan_eff"])
    outside, latent = P.hourly_outside_air_heat(tdb, twb, p, rh)
    coil_air = hr.coil_air(tdb, twb, design, p, P.switch_point(p))
    wet = P._wet_share(tdb, design, p)
    air_load = room + crah + outside
    ch = pu = fa = 0.0 * tdb
    for load, supply in ((np.maximum(air_load, 0.0), P.air_loop_water(p)), (1.0 - air + np.minimum(air_load, 0.0), p["liquid_water"]), (latent, P.DEHUMIDIFY_WATER)):
        c, pm, f = hr.loop(load, supply, tdb, twb, coil_air, wet, design, p)
        ch, pu, fa = ch + c, pu + pm, fa + f
    base = q + crah
    return {"base": base + 0 * tdb, "chiller": ch, "pumps": pu, "fans": fa, "total": base + ch + pu + fa}

out = {"cell": cid, "correction": note["applied"], "design_db": float(P.design_dry_bulb(tdb)), "tdb_p99": float(np.quantile(tdb, 0.99)), "twb_p99": float(np.quantile(twb, 0.99)), "rows": {}}
for plant in P.PLANTS:
    p = P.for_location(P.central_parameters(plant), tdb)
    for d in P.DESIGNS:
        r = parts(d, p)
        tot = r["total"]
        # the hottest hour by PUE each year, median over years
        idx = [np.flatnonzero(years == y)[np.argmax(tot[years == y])] for y in np.unique(years)]
        pk = idx[int(np.argsort([tot[i] for i in idx])[len(idx) // 2])]
        out["rows"][f"{plant}/{d}"] = {"avg": {k: float(v.mean()) for k, v in r.items()}, "peak": {k: float(v[pk]) for k, v in r.items()},
                                     "peak_tdb": float(tdb[pk]), "peak_twb": float(twb[pk]), "chiller_hours_share": float((r["chiller"] > 1e-4).mean()),
                                     "switch": float(P.switch_point(p)), "loop_water": float(P.air_loop_water(p))}
json.dump(out, open(sys.argv[3], "w"), indent=1)
print(cid, "corrected", note["applied"], "design_db %.1f" % out["design_db"])
for k, v in out["rows"].items():
    a, b = v["avg"], v["peak"]
    print(f"{k:16s} avg tot {a['total']:.3f} ch {a['chiller']:.3f} pu {a['pumps']:.3f} fa {a['fans']:.3f} | peak tot {b['total']:.3f} ch {b['chiller']:.3f} pu {b['pumps']:.3f} fa {b['fans']:.3f} at {v['peak_tdb']:.1f}/{v['peak_twb']:.1f} C | chiller hrs {v['chiller_hours_share']:.2f} switch {v['switch']:.1f} loop {v['loop_water']:.1f}")
