"""Hourly demand and generation by fuel for every balancing authority in the lower 48: EIA-930, the Hourly Electric Grid
Monitor (https://www.eia.gov/electricity/gridmonitor/). Read from EIA's six-month balance files, which need no key, and
kept as one file a balancing authority under <cache>/grid930/ (design 0008, part 1).

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


# Screening the hours (model 1.17). EIA's adjusted columns still carry single-hour spikes and dropouts (AZPS "other" at 6.1 GW for
# one hour against a usual 31 MW; PJM gas at 21 MW for one hour against about 25 GW) and gaps (AZPS nuclear NaN). An hour is screened,
# and left out of the averages and of every hour-to-hour pair it touches, where one fuel class
#   spikes: for 1 to SPIKE_HOURS hours it runs above (or below) both neighbouring hours by more than SPIKE_K times the class's own
#           99th-percentile hourly change in the BA (its 1-in-100-hour ramp), and by more than FLOOR of the BA's median generation.
#           SPIKE_K is set from all 67 BAs, 2019-2025: in the large fleets (MISO, SWPP, ERCO, PJM, SOCO, TVA coal, gas, wind, solar)
#           the largest such reversal is 0.9-3.4 ramps, and the pooled tail of reversals falls steeply to about 8 ramps and flattens
#           beyond (the artifacts); artifacts confirmed by eye sit at 4.9 (PJM gas to 21 MW) and 6.4 (AZPS gas to 5,905 MW from
#           1,093), so k = 4 sits above every large fleet's natural hours and below the artifacts.
#   drops out: a coal, gas, nuclear, oil or geothermal fleet falls to DROPOUT or less of both neighbours for 1 to SPIKE_HOURS hours,
#           the neighbours above FLOOR; whole fleets can't stop and restart that fast (minimum run times). Not applied to "other",
#           which held batteries before July 2024, nor to hydro, solar, wind or storage.
#   has a gap: a class is NaN in a run of hours with the class generating (above FLOOR) on both sides. A NaN run without that (a
#           class not reported, as AZPS nuclear after EIA moved Palo Verde to SRP in December 2019) is read as 0 MW, but the hour
#           where a class starts or stops being reported is not paired with the hour before (its change is a reporting change).
SPIKE_K = 4.0
SPIKE_HOURS = 3
DROPOUT = 0.1
FLOOR = 0.01
DROPOUT_CLASSES = ("coal", "gas", "nuclear", "oil", "geothermal")


def _reversals(x, length):
    """For runs of `length` hours starting at each hour: how far the run sits beyond both neighbouring hours (above both or below
    both; 0 otherwise), and whether it falls to DROPOUT of both. NaN neighbours give 0."""
    n = len(x)
    r, low = np.zeros(n), np.zeros(n, dtype=bool)
    if n < length + 2:
        return r, low
    before, after = x[:n - length - 1], x[length + 1:]
    run = np.vstack([x[1 + i:n - length + i] for i in range(length)])
    near = np.minimum(before, after)
    with np.errstate(invalid="ignore"):
        beyond = np.maximum(run.min(axis=0) - np.maximum(before, after), near - run.max(axis=0))
        drop = run.max(axis=0) <= DROPOUT * near
    r[1:n - length] = np.where(np.isfinite(beyond), np.maximum(beyond, 0), 0)
    low[1:n - length] = drop & np.isfinite(near)
    return r, low


def screen(d):
    """Hours to leave out of a BA's fit (see SPIKE_K above): {"hour_ok": bool per hour, False for a screened hour; "pair_ok": bool
    per hour, False where the hour is not to be differenced with the hour before; "screened": {class: hours screened}; "floor_mw"}.
    `d` as hourly() gives it."""
    n = len(d["hour"])
    gen = np.nansum(np.vstack([d[k] for k in FUELS]), axis=0)
    floor = FLOOR * float(np.median(gen[gen > 0])) if (gen > 0).any() else 0.0
    hour_ok, pair_ok, screened = np.ones(n, dtype=bool), np.ones(n, dtype=bool), {}
    contiguous = np.r_[False, np.diff(d["hour"]) == 1]
    for cls in FUELS:
        x = np.asarray(d[cls], dtype=float)
        if not np.isfinite(x).any():
            continue
        bad = np.zeros(n, dtype=bool)
        # gaps, and the hours where a class starts or stops being reported
        nan = np.isnan(x)
        change = np.flatnonzero(np.diff(nan.astype(int))) + 1
        pair_ok[change] = False
        starts = change[nan[change]]
        for a in np.r_[[0] if nan[0] else [], starts].astype(int):
            b = a + int(np.argmin(nan[a:])) if not nan[a:].all() else n
            if 0 < a and b < n and abs(x[a - 1]) > floor and abs(x[b]) > floor:
                bad[a:b] = True
        # spikes and dropouts
        step = np.abs(np.diff(x))
        step = step[np.isfinite(step)]
        ramp = max(float(np.quantile(step, 0.99)) if step.size else 0.0, floor)
        for length in range(1, SPIKE_HOURS + 1):
            r, low = _reversals(x, length)
            hit = (r > floor) & ((r > SPIKE_K * ramp) | (low & (cls in DROPOUT_CLASSES)))
            for i in range(length):
                bad[np.flatnonzero(hit) + i] = True
        if bad.any():
            screened[cls] = int(bad.sum())
        hour_ok &= ~bad
    pair_ok &= contiguous & hour_ok & np.r_[False, hour_ok[:-1]]
    return {"hour_ok": hour_ok, "pair_ok": pair_ok, "screened": screened, "floor_mw": floor}


def intensity(ba, factors=None):
    """Water at power plants per MWh of a balancing authority's own generation, hour by hour (design 0008, part 1, step 3):
    {"hour", "consumed", "withdrawn", "withdrawn_saline" (gal/MWh), "generation" (MW), "pair_ok", "screened", "bounds"}. Each hour is the sum
    over fuel classes of generation x the class's factor for the month (energy.ba_fuel_water), over net generation. Imports are
    not counted: the hour is the BA's own plants. An hour with no net generation, or under 1% of the BA's median, is NaN, and so
    is an hour screen() leaves out (a spike, a dropout or a gap); a class not reported in an hour is 0 MW. "pair_ok" marks the
    hours that may be differenced with the hour before (model 1.17), "screened" counts the screened hours by class, and "bounds"
    gives {"consumed": (lo, hi), "withdrawn": (lo, hi)}, 12 monthly values each: the lowest and highest factor among the classes
    with generation in the BA in that month, which the BA's average and marginal factors are checked against."""
    from waterledger_data import energy
    f = factors or energy.ba_fuel_water(ba)
    if f is None:
        raise KeyError(f"no plant water factors for {ba!r}")
    d = hourly(ba)
    month = (d["hour"].astype("datetime64[h]").astype("datetime64[M]").astype(int) % 12)
    gen = np.nansum(np.vstack([d[k] for k in FUELS]), axis=0)
    have = ~np.all(np.isnan(np.vstack([d[k] for k in FUELS])), axis=0)
    sc = screen(d)
    ok = have & sc["hour_ok"] & (gen > 0.01 * np.nanmedian(np.where(have, gen, np.nan)))
    out = {"hour": d["hour"], "generation": np.where(ok, gen, np.nan), "pair_ok": sc["pair_ok"] & ok & np.r_[False, ok[:-1]],
           "screened": sc["screened"]}
    for k in ("consumed", "withdrawn", "withdrawn_saline"):
        water = sum(np.nan_to_num(d[fuel]) * f[fuel][k][month] for fuel in FUELS)
        out[k] = np.where(ok, water / np.where(ok, gen, 1.0), np.nan)
    runs = [[fuel for fuel in FUELS if np.any(np.nan_to_num(d[fuel][ok & (month == m)]) > 0)] for m in range(12)]
    out["bounds"] = {}
    for k in ("consumed", "withdrawn"):
        v = [[f[fuel][k][m] for fuel in runs[m]] or [np.nan] for m in range(12)]
        out["bounds"][k] = (np.array([min(x) for x in v]), np.array([max(x) for x in v]))
    return out
