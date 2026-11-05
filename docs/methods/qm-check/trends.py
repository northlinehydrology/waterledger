"""Station against cell trends, 1995-2024: the least-squares slope of annual mean T and Td (C per decade) at each anchor station and at
its cell on the station's own hours, and the 0.4% dry-bulb of the first and last 15 years. Writes trends.json. Usage: python trends.py OUT"""
import json, os, sys
import numpy as np

import anchors as A

HERE = os.path.dirname(os.path.abspath(__file__))


def slope(years, x):
    ys = np.unique(years)
    m = np.array([x[years == y].mean() for y in ys])
    return float(np.polyfit(ys, m, 1)[0] * 10)


if __name__ == "__main__":
    out = sys.argv[1]
    scratch, _ = A.setup(out)
    rows = []
    for s in A.load_anchors(out):
        et, ee, ed = A.era5(scratch, s["cell"])
        on = np.isin(et, s["times"])
        yr_s = np.asarray(s["times"], dtype="datetime64[Y]").astype(int) + 1970
        yr_e = np.asarray(et[on], dtype="datetime64[Y]").astype(int) + 1970
        half = lambda y, x, a, b: float(np.quantile(x[(y >= a) & (y <= b)], 0.996))
        rows.append({"id": s["id"], "name": s["name"], "cell_land": s["cell_land"],
                     "t_station": slope(yr_s, s["t"]), "t_cell": slope(yr_e, ee[on]),
                     "td_station": slope(yr_s, s["td"]), "td_cell": slope(yr_e, ed[on]),
                     "ddb_change_station": half(yr_s, s["t"], 2010, 2024) - half(yr_s, s["t"], 1995, 2009),
                     "ddb_change_cell": half(yr_e, ee[on], 2010, 2024) - half(yr_e, ee[on], 1995, 2009)})
        A._series.pop(s["cell"], None)
    json.dump(rows, open(os.path.join(HERE, "trends.json"), "w"), indent=1)
    d = lambda k: np.array([r[k] for r in rows])
    for v in ("t", "td"):
        diff = d(f"{v}_cell") - d(f"{v}_station")
        print(f"{v}: station {np.median(d(v + '_station')):+.2f}, cell {np.median(d(v + '_cell')):+.2f} C/decade (medians); cell - station median {np.median(diff):+.2f}, 10-90% {np.quantile(diff, .1):+.2f} to {np.quantile(diff, .9):+.2f}")
    diff = d("ddb_change_cell") - d("ddb_change_station")
    print(f"0.4% dry-bulb, 2010-24 minus 1995-2009: station median {np.median(d('ddb_change_station')):+.2f}, cell {np.median(d('ddb_change_cell')):+.2f}; difference 10-90% {np.quantile(diff, .1):+.2f} to {np.quantile(diff, .9):+.2f}")
