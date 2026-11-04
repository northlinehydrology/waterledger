"""Shared loading for the prototype: qualifying anchor stations with their quantiles and their cells' quantiles, and ERA5 cell series.
OUT is the folder stations.py wrote; ERA5 cells are OUT/../era5/<cell>.json (era5_fetch.py); the land-sea mask and ERA5 orography in
OUT/../lsm/ (lsm_fetch.py, orog_m.npy)."""
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "era5-check"))
import land_rule as lr                                  # noqa: E402
import qm                                               # noqa: E402


def setup(out):
    scratch = os.path.dirname(os.path.abspath(out))
    lr.load(scratch)
    return scratch, np.load(os.path.join(scratch, "lsm", "orog_m.npy"))


def cell_of(lat, lon):
    """The land rule's cell (decision 3 of design 0004) as (id, lat, lon, land)."""
    ni, nj = round(lat * 4), round(lon * 4)
    ci, cj = lr.nearest_land(lat, lon) if lr.land(ni, nj) < lr.LAND else (ni, nj)
    return lr.cid(ci, cj), ci / 4, cj / 4, lr.land(ci, cj)


def elev(orog, clat, clon):
    return float(orog[360 - round(clat * 4), (round(clon * 4) + 1440) % 1440])


_series = {}


def era5(scratch, cell):
    """(times, T, Td) at a cell in local standard time, 1995-2024."""
    if cell not in _series:
        from waterledger_models.weather import to_local_standard
        h = json.load(open(os.path.join(scratch, "era5", cell + ".json")))
        times, keep = to_local_standard(h["hourly"]["time"], h["longitude"], "1995-01-01", "2024-12-31")
        _series[cell] = (np.array(times), np.array(h["hourly"]["temperature_2m"])[keep], np.array(h["hourly"]["dew_point_2m"])[keep])
    return _series[cell]


def anchors(out, orog):
    """Qualifying stations with their record, their cell, the station's quantiles `qt` and its cell's `qe`, both on the station's hours."""
    scratch = os.path.dirname(os.path.abspath(out))
    got = []
    for s in json.load(open(os.path.join(out, "stations.json"))):
        if not s.get("qualifies"):
            continue
        z = np.load(os.path.join(out, "stations", s["id"] + ".npz"))
        cid, clat, clon, land = cell_of(s["lat"], s["lon"])
        et, ee, ed = era5(scratch, cid)
        on = np.isin(et, z["times"])
        got.append({**s, "times": z["times"], "t": z["t"], "td": z["td"], "cell": cid, "cell_lat": clat, "cell_lon": clon,
                    "cell_land": land, "cell_elev_m": elev(orog, clat, clon),
                    "qt": qm.fit(z["times"], z["t"], z["td"]), "qe": qm.fit(et, ee, ed, keep=on)})
    return got


def cache_anchors(out):
    """anchors() once, saved to OUT/anchors.pkl for the worker processes."""
    import pickle
    path = os.path.join(out, "anchors.pkl")
    if not os.path.exists(path):
        _, orog = setup(out)
        pickle.dump(anchors(out, orog), open(path, "wb"))
    return path


def load_anchors(out):
    import pickle
    return pickle.load(open(cache_anchors(out), "rb"))
