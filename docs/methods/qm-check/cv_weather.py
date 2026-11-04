"""Leave-one-station-out check of the ways to carry a correction (qm.py), on the weather alone, at every anchor station.

Each station in turn is held out with any other station within 5 km of it; its own cell (the land rule's) is corrected from the
stations left, and the corrected cell is compared with the held-out station on the station's own hours: the 0.4% design dry-bulb, the
0.4% wet bulb, the mean summer afternoon (June-August, 12-18 h), the mean dew point, and the mean absolute error over every bin's
quantiles of T and Td. Writes cv_weather.json beside this file. Usage: python cv_weather.py OUT"""
import json, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np

import anchors as A
import qm
from waterledger_models.datacenter.physics import wet_bulb

HERE = os.path.dirname(os.path.abspath(__file__))
WAYS = {"none": None, "bias": dict(how="bias"), "target": dict(how="target"), "lapse": dict(how="lapse"),
        "bias_nearest": dict(how="bias", nearest_only=True), "target_nearest": dict(how="target", nearest_only=True),
        "bias_50km": dict(how="bias", r_km=50), "target_50km": dict(how="target", r_km=50),
        "lapse_shore": dict(how="lapse", shore_only=True), "lapse_shore_isd": dict(how="lapse", shore_only=True, sources=("isd",)),
        "lapse_shore_linked": dict(how="lapse", shore_only=True, sources=("isd", "isd-linked")), "lapse_isd": dict(how="lapse", sources=("isd",))}


def stats(times, t, td):
    m, b = qm.bins(times)
    hour = b * 3
    summer_pm = np.isin(m, (5, 6, 7)) & (hour >= 12) & (hour < 18)
    q = qm.fit(times, t, td)
    return {"ddb": float(np.quantile(t, 0.996)), "wb": float(np.quantile(wet_bulb(t, qm.rh_from(t, td)), 0.996)),
            "summer_pm": float(t[summer_pm].mean()), "td": float(td.mean()), "_q": np.stack([q[0], q[0] - q[1]])}


ST, SCRATCH = None, None


def init(out):
    global ST, SCRATCH
    import pickle
    SCRATCH, _ = A.setup(out)
    ST = pickle.load(open(os.path.join(out, "anchors.pkl"), "rb"))


def one(i):
    st, scratch = ST, SCRATCH
    s0 = st[i]
    rest = [a for a in st if qm.km(a["lat"], a["lon"], s0["lat"], s0["lon"]) > 5]
    et, ee, ed = A.era5(scratch, s0["cell"])
    on = np.isin(et, s0["times"])
    truth = stats(s0["times"], s0["t"], s0["td"])
    target = {"lat": s0["cell_lat"], "lon": s0["cell_lon"], "qe": qm.fit(et, ee, ed), "elev_m": s0["cell_elev_m"]}
    res = {}
    for name, kw in WAYS.items():
        d = None if kw is None else qm.delta(target, rest, **kw)
        tc, tdc = (ee, ed) if d is None else qm.apply(et, ee, ed, target["qe"], d)
        s = stats(et[on], tc[on], tdc[on])
        res[name] = {k: s[k] - truth[k] for k in ("ddb", "wb", "summer_pm", "td")} | {
            "q_mae_t": float(np.abs(s["_q"][0] - truth["_q"][0]).mean()), "q_mae_td": float(np.abs(s["_q"][1] - truth["_q"][1]).mean()),
            "corrected": d is not None}
    near = sorted(qm.km(a["lat"], a["lon"], s0["lat"], s0["lon"]) for a in rest)
    shore = sorted(qm.km(a["lat"], a["lon"], s0["lat"], s0["lon"]) for a in rest if a["cell_land"] < qm.SHORE_LAND)
    return {k: s0.get(k) for k in ("id", "name", "state", "source", "lat", "lon", "elev_m", "cell", "cell_land", "cell_elev_m")} | {
        "shore_within_100km": int(sum(x <= 100 for x in shore)),
        "truth": {k: truth[k] for k in ("ddb", "wb", "summer_pm", "td")}, "nearest_other_km": round(float(near[0]), 1),
        "within_100km": int(sum(x <= 100 for x in near)), "errors": res}


if __name__ == "__main__":
    out = sys.argv[1]
    A.cache_anchors(out)
    n = len(A.load_anchors(out))
    with ProcessPoolExecutor(int(sys.argv[2]) if len(sys.argv) > 2 else 8, initializer=init, initargs=(out,)) as pool:
        rows = list(pool.map(one, range(n)))
    json.dump({"ways": list(WAYS), "rows": rows}, open(os.path.join(HERE, "cv_weather.json"), "w"), indent=1, default=float)
    print("wrote cv_weather.json,", len(rows), "stations")
