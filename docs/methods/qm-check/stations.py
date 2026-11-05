"""The anchor stations for the quantile-mapping prototype: every ISD station spanning 1995-2024 (climate.isd_stations), every ISD site
whose record covers it only across a change of ID (climate.isd_sites, decided Nov 4, 2026) and every Canadian site with hourly records
covering it (climate.eccc_sites), in Michigan, Ohio, Virginia or Texas, or within 100 km of a place in them, that passes the snapshots'
rule (climate.isd_hourly or eccc_hourly: 85% of hours with temperature and dew point, the same screens and gap filling). Each qualifying station's hourly record goes to OUT/stations/<id>.npz
(local standard time, T and dew point in C) and the list, with elevation from isd-history, to OUT/stations.json.
Usage: python stations.py OUT [workers]"""
import csv, json, os, sys
from concurrent.futures import ProcessPoolExecutor
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1]
B = 17.625, 243.04                                     # Magnus (Alduchov and Eskridge 1996), as isd_hourly uses


def dew_point(t, rh):
    g = np.log(np.asarray(rh) / 100) + B[0] * t / (B[1] + t)
    return B[1] * g / (B[0] - g)


def candidates():
    from waterledger_data import climate
    p = np.array([(float(r["lat"]), float(r["lon"])) for r in csv.DictReader(open(os.path.join(HERE, "..", "era5-check", "cell_assignment.csv")))])
    la, lo = np.radians(p[:, 0]), np.radians(p[:, 1])
    elev = {}
    for r in csv.DictReader(open(os.path.join(climate.RAW, "isd", "isd-history.csv"))):
        elev[f"{r['USAF']}-{r['WBAN']}"] = float(r["ELEV(M)"]) if r["ELEV(M)"] not in ("", "-999", "-999.0", "-0999.0") else None
    out = []
    sites = [{**s, "source": "isd-linked" if "parts" in s else "isd", "elev_m": elev.get(s["id"])} for s in climate.isd_sites()]
    for s in sites + [{**s, "source": "eccc"} for s in climate.eccc_sites()]:
        a, b = np.radians(s["lat"]), np.radians(s["lon"])
        d = 12742 * np.arcsin(np.sqrt(np.sin((la - a) / 2) ** 2 + np.cos(a) * np.cos(la) * np.sin((lo - b) / 2) ** 2))
        if s["state"] in ("MI", "OH", "VA", "TX") or d.min() <= 100:
            out.append(s)
    return out


def one(s):
    from waterledger_data import climate
    path = os.path.join(OUT, "stations", s["id"] + ".npz")
    if os.path.exists(path):
        z = np.load(path)
        return {**s, "share_observed": float(z["share"])}
    try:
        got = (climate.eccc_hourly if s["source"] == "eccc" else climate.isd_hourly)(s)
    except Exception as e:                              # a station whose files will not download is left out, and said so
        return {**s, "error": repr(e)[:200]}
    if not got:
        return {**s, "qualifies": False}
    times, t, rh, share, screen = got
    t = np.array(t)
    np.savez_compressed(path, times=np.array(times), t=t, td=dew_point(t, rh), share=share)
    return {**s, "share_observed": share, "screen": screen}


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "stations"), exist_ok=True)
    c = candidates()
    with ProcessPoolExecutor(int(sys.argv[2]) if len(sys.argv) > 2 else 8) as pool:
        got = list(pool.map(one, c))
    for g in got:
        g["qualifies"] = "share_observed" in g
    json.dump(got, open(os.path.join(OUT, "stations.json"), "w"), indent=1, default=str)
    print(len(c), "candidates,", sum(g["qualifies"] for g in got), "qualify,", sum("error" in g for g in got), "errors")
