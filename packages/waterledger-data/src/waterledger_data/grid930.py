"""Hourly demand and generation by fuel for every balancing authority in the lower 48: EIA-930, the Hourly Electric Grid
Monitor (https://www.eia.gov/electricity/gridmonitor/). Read from EIA's six-month balance files, which need no key, and
kept as one file a balancing authority under <cache>/grid930/ (design 0007, part 1).

The adjusted columns are used: EIA's own values after its anomaly screening and imputation. Hours are UTC, at the end
of the hour. Fuel classes: coal, gas, nuclear, oil (all petroleum products), hydro (with pumped storage), solar, wind,
geothermal, storage (batteries and other storage), other and unknown. From July 2024 EIA splits hydro from pumped
storage and solar and wind by attached batteries, and adds geothermal and storage; the parts are summed back into the
classes above. Before then geothermal and storage are inside "other" and the two classes are missing (NaN). Pumped
storage and batteries can be negative; they are kept as reported."""
import os

import numpy as np
import pandas as pd

from waterledger_data.config import CACHE
from waterledger_data.fetching import save

RAW = os.path.join(CACHE, "grid930")
URL = "https://www.eia.gov/electricity/gridmonitor/sixMonthFiles/EIA930_BALANCE_{year}_{half}.csv"
HALVES = ("Jan_Jun", "Jul_Dec")
FIRST_YEAR = 2019                     # 2018's files start in July, and the fuel columns are sparse before 2019
FUELS = ("coal", "gas", "nuclear", "oil", "hydro", "solar", "wind", "geothermal", "storage", "other", "unknown")
TOTALS = {"demand": "Demand (MW) (Adjusted)", "net_generation": "Net Generation (MW) (Adjusted)",
          "interchange": "Total Interchange (MW) (Adjusted)"}
COLUMNS = (*TOTALS, *FUELS)
# words in an adjusted "Net Generation (MW) from ..." header -> class; first match wins. EIA's headers carry typos
# ("witho", doubled spaces), so they are matched by word, not exactly.
_WORDS = (("Coal", "coal"), ("Natural Gas", "gas"), ("Nuclear", "nuclear"), ("Petroleum", "oil"), ("Hydropower", "hydro"),
          ("Pumped Storage", "hydro"), ("Solar", "solar"), ("Wind", "wind"), ("Geothermal", "geothermal"),
          ("Battery Storage", "storage"), ("Energy Storage", "storage"), ("Other Fuel", "other"), ("Unknown Fuel", "unknown"))


def fuel_class(header):
    """The fuel class of an adjusted EIA-930 generation header, or None for a column that isn't one."""
    if not (header.startswith("Net Generation (MW) from ") and header.rstrip().endswith("(Adjusted)")):
        return None
    for word, cls in _WORDS:
        if word in header:
            return cls
    raise ValueError(f"EIA-930 header not classed: {header!r}")


def _half_file(year, half):
    path = os.path.join(RAW, "files", f"EIA930_BALANCE_{year}_{half}.csv")
    return save(URL.format(year=year, half=half), path, timeout=600,
                check=lambda d: d[:40].lstrip(b"\xef\xbb\xbf").startswith(b'"Balancing Authority"'))


def _read(path):
    header = pd.read_csv(path, nrows=0).columns
    fuels = {c: fuel_class(c) for c in header if fuel_class(c)}
    df = pd.read_csv(path, thousands=",", low_memory=False,
                     usecols=["Balancing Authority", "UTC Time at End of Hour", *TOTALS.values(), *fuels])
    t = pd.to_datetime(df["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p")
    out = pd.DataFrame({"ba": df["Balancing Authority"], "hour": t.values.astype("datetime64[h]").astype(np.int64)})
    for k, c in TOTALS.items():
        out[k] = pd.to_numeric(df[c], errors="coerce").astype("float32")
    for cls in FUELS:
        cols = [c for c, f in fuels.items() if f == cls]
        num = df[cols].apply(pd.to_numeric, errors="coerce") if cols else None
        out[cls] = (num.sum(axis=1, min_count=1) if cols else np.nan)
        out[cls] = out[cls].astype("float32")
    return out


def build(years=None):
    """Fetch the six-month files for `years` (default 2019 through last year) and write one .npz a balancing authority:
    hour (hours since 1970-01-01 UTC, end of hour), demand, net_generation, interchange and each fuel (MW, NaN where
    EIA has no value). Returns the list of balancing authorities written."""
    import datetime
    years = list(years or range(FIRST_YEAR, datetime.date.today().year))
    parts = [_read(_half_file(y, h)) for y in years for h in HALVES]
    df = pd.concat(parts, ignore_index=True).drop_duplicates(["ba", "hour"]).sort_values(["ba", "hour"])
    os.makedirs(os.path.join(RAW, "ba"), exist_ok=True)
    written = []
    for ba, g in df.groupby("ba", sort=True):
        path = os.path.join(RAW, "ba", f"{ba}.npz")
        np.savez_compressed(path + ".part.npz", years=np.array(years), hour=g["hour"].to_numpy(),
                            **{k: g[k].to_numpy() for k in COLUMNS})
        os.replace(path + ".part.npz", path)
        written.append(ba)
    return written


def hourly(ba):
    """{"hour", "demand", "net_generation", "interchange", <fuel>...} for one balancing authority, as numpy arrays,
    from the cache (build() first)."""
    path = os.path.join(RAW, "ba", f"{ba}.npz")
    if not os.path.exists(path):
        raise FileNotFoundError(f"no EIA-930 file for {ba!r}: run waterledger_data.grid930.build()")
    with np.load(path) as z:
        return {k: z[k] for k in z.files}


def intensity(ba, factors=None):
    """Water at power plants per MWh of a balancing authority's own generation, hour by hour (design 0007, part 1, step 3):
    {"hour", "consumed", "withdrawn", "withdrawn_saline" (gal/MWh), "generation" (MW)}. Each hour is the sum over fuel
    classes of generation x the class's factor for the month (energy.ba_fuel_water), over net generation. Imports are
    not counted: the hour is the BA's own plants. An hour with no net generation, or under 1% of the BA's median, is NaN."""
    from waterledger_data import energy
    f = factors or energy.ba_fuel_water(ba)
    if f is None:
        raise KeyError(f"no plant water factors for {ba!r}")
    d = hourly(ba)
    month = (d["hour"].astype("datetime64[h]").astype("datetime64[M]").astype(int) % 12)
    gen = np.nansum(np.vstack([d[k] for k in FUELS]), axis=0)
    have = ~np.all(np.isnan(np.vstack([d[k] for k in FUELS])), axis=0)
    out = {"hour": d["hour"], "generation": np.where(have, gen, np.nan)}
    ok = have & (gen > 0.01 * np.nanmedian(np.where(have, gen, np.nan)))
    for k in ("consumed", "withdrawn", "withdrawn_saline"):
        water = sum(np.nan_to_num(d[fuel]) * f[fuel][k][month] for fuel in FUELS)
        out[k] = np.where(ok, water / np.where(ok, gen, 1.0), np.nan)
    return out
