"""Design 0018's check A5, at the Clam River: AORC against ERA5 year by year, 2000-2022, for the 10 m wind and the global horizontal radiation,
and the AORC path's solar and wind capacity factors beside the ERA5 path's.

    WL_POWER_WORK=~/.cache/waterledger/power_water_work uv run --with "zarr<3" --with "numcodecs<0.16" --with s3fs \
        python docs/methods/power_supply/aorc_drift.py

Why: the Clam River study finds the forcing's (AORC's) wind 30-50% above the Cadillac airport anemometer and falling against it after 2014, and
its shortwave 10-16% above the Gaylord pyranometer (the study's weather_correction.py). ERA5 is an independent, homogeneous reference: if AORC's
ratio to it moves over the years, the forcing drifts, and a resource factor fit on 2024 does not hold for every year.

AORC at 44.30 N, 85.30 W (aorc_points.py; one point, each year's store); ERA5 at its cell (44.25_-85.25): the 10 m and 100 m wind from
era5.fetch_shear, the radiation from era5.fetch_supply. Per UTC year: mean 10 m speed and mean global radiation each way and their ratio; the
AORC path's capacity factors (pv.hourly_from_ghi, Erbs, shift 0, tracking; wind.hourly_from_10m with the cell's 1995-2024 shear table) and the
ERA5 path's (pv.hourly, wind.hourly), at central parameters with resource 1.0. Writes aorc_drift.csv next to this file and prints it.

Then the same 10 m wind ratio over 2015-2020 at five more points (the three SURFRAD stations, central Iowa and the Texas plains), to see whether
a step in it is the Clam River's or the forcing's: aorc_wind_break.csv.

Found (Nov 16, 2026): AORC's 10 m wind drops against ERA5's between 2017 and 2018 at five of the six points, by 20-60%, recovering partly by
2020 at some; not on the Texas plains. AORC's shortwave shows no step. AORC v1.1 keeps NLDAS-2's wind through the record (AORC v1.1 methods,
sec. 4.2), and NLDAS-2's is NARR's; no documented change was found.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aorc_points  # noqa: E402
from waterledger_data import era5  # noqa: E402
from waterledger_models.supply import pv, wind  # noqa: E402

HERE = Path(__file__).resolve().parent
LAT, LON = 44.30, -85.30
YEARS = range(2000, 2023)
VARS = ("DSWRF_surface", "UGRD_10maboveground", "VGRD_10maboveground", "TMP_2maboveground")
PV_C = {k: (a + b) / 2 for k, (a, b) in pv.RANGES.items()} | {"resource": 1.0}
W_C = {k: (a + b) / 2 for k, (a, b) in wind.RANGES.items()} | {"resource": 1.0}
W10_C = {"shear_scale": 1.0, "losses": W_C["losses"], "resource": 1.0}


def main():
    cid = era5.cell(LAT, LON)["id"]
    era5.fetch_shear([cid])
    era5.fetch_supply([cid])
    eu, u10, v10, u100, v100 = era5.shear(cid)
    table = wind.shear_table(eu, LON, u10, v10, u100, v100)
    z = np.load(era5.raw_path(cid, era5.RAW_SUPPLY))
    su = np.datetime64(str(z["start_utc"]), "h") + np.arange(len(z["shortwave_radiation"]))
    t2 = np.load(era5.raw_path(cid))
    tu = np.datetime64(str(t2["start_utc"]), "h") + np.arange(len(t2["temperature_2m"]))
    rows = []
    for y in YEARS:
        a = aorc_points.series({"clam": (LAT, LON)}, y, VARS)["clam"]
        utc = a["utc"]
        ghi_a = np.nan_to_num(a["DSWRF_surface"])
        s10_a = np.hypot(a["UGRD_10maboveground"], a["VGRD_10maboveground"])
        ta = a["TMP_2maboveground"] - 273.15
        k = np.searchsorted(eu, utc)
        s10_e = np.hypot(u10[k], v10[k])
        ks = np.searchsorted(su, utc)
        ghi_e, beam_e = z["shortwave_radiation"][ks].astype(float), z["direct_radiation"][ks].astype(float)
        te = t2["temperature_2m"][np.searchsorted(tu, utc)].astype(float)
        pv_a = pv.hourly_from_ghi(utc, LAT, LON, ghi_a, ta, s10_a, PV_C).mean()
        pv_e = pv.hourly(utc, LAT, LON, ghi_e, beam_e, te, np.hypot(u100[k], v100[k]), PV_C).mean()
        w_a = wind.hourly_from_10m(utc, LON, a["UGRD_10maboveground"], a["VGRD_10maboveground"], table, W10_C).mean()
        w_e = wind.hourly(u100[k], v100[k], W_C).mean()
        rows.append({"year": y, "aorc_10m_speed": round(float(s10_a.mean()), 3), "era5_10m_speed": round(float(s10_e.mean()), 3),
                     "wind_10m_ratio": round(float(s10_a.mean() / s10_e.mean()), 3), "aorc_ghi": round(float(ghi_a.mean()), 1),
                     "era5_ghi": round(float(ghi_e.mean()), 1), "ghi_ratio": round(float(ghi_a.mean() / ghi_e.mean()), 3),
                     "pv_cf_aorc": round(float(pv_a), 4), "pv_cf_era5": round(float(pv_e), 4), "wind_cf_aorc": round(float(w_a), 4),
                     "wind_cf_era5": round(float(w_e), 4)})
        print(rows[-1], flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "aorc_drift.csv", index=False)
    print(out.to_string(index=False))
    early, late = out[out.year <= 2013], out[out.year >= 2015]
    for c in ("wind_10m_ratio", "ghi_ratio"):
        print(f"{c}: 2000-2013 mean {early[c].mean():.3f}, 2015-2022 mean {late[c].mean():.3f}")


BREAK_POINTS = {"Clam River MI": (LAT, LON), "Bondville IL": (40.0519, -88.3731), "Penn State PA": (40.7201, -77.9309),
                "Sioux Falls SD": (43.7340, -96.6233), "central Iowa": (42.0, -93.6), "Texas plains": (33.5, -101.5)}


def wind_break(years=range(2015, 2021)):
    cells = {k: era5.cell(*v)["id"] for k, v in BREAK_POINTS.items()}
    era5.fetch_shear(list(cells.values()))
    rows = []
    for k, (lat, lon) in BREAK_POINTS.items():
        eu, u10, v10, *_ = era5.shear(cells[k])
        for y in years:
            name = "clam" if k == "Clam River MI" else "drift_" + k.split()[0].lower()
            a = aorc_points.series({name: (lat, lon)}, y, ("UGRD_10maboveground", "VGRD_10maboveground"))[name]
            sa = np.hypot(a["UGRD_10maboveground"], a["VGRD_10maboveground"]).mean()
            kk = np.searchsorted(eu, a["utc"])
            se = np.hypot(u10[kk], v10[kk]).mean()
            rows.append({"point": k, "year": y, "aorc_10m_speed": round(float(sa), 3), "era5_10m_speed": round(float(se), 3),
                         "ratio": round(float(sa / se), 3)})
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "aorc_wind_break.csv", index=False)
    print(out.pivot(index="point", columns="year", values="ratio").to_string())


if __name__ == "__main__":
    main() if sys.argv[1:] != ["break"] else wind_break()
