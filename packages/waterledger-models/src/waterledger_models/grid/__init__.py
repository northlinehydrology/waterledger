"""The grid component (design 0008): water at the power plants supplying a water user's electricity, hour by hour, at
grid level. One component for every water user: it takes any user's hourly electricity and the hour's air temperature
at the user and returns the plants' water, consumed and withdrawn. It knows a balancing authority (BA) only through a
GridTable; it never names a plant.

A GridTable is fit from the BA's own hours (waterledger_data.grid930.intensity: EIA-930 generation by fuel x plant
water by fuel and month) paired with the temperature at the user's location in the same hours. Within each month and
UTC hour, the hours are split into temperature bins (quintiles by default), and each bin keeps:
    average   the plants' water per MWh of the BA's generation in those hours, weighted by generation, so the table
              applied to the fit hours gives back their water exactly;
    marginal  the water per MWh of added generation (Siler-Evans et al. 2012): the slope of the hour-to-hour change in
              the BA's plant water against the change in its generation, by month and bin. The slope is Theil-Sen's (the
              median of the pairwise slopes; Theil 1950, Sen 1968), which a few bad hours can't move: up to 29% of the pairs
              can be wrong without carrying it off (model 1.17; before, an ordinary least-squares slope, which single-hour
              spikes in EIA-930 carried to 2,500-3,000 gal/MWh in AZPS). Only pairs of hours the caller marks as pairable
              are used (`pair_ok`: waterledger_data.grid930.intensity screens spikes, dropouts and gaps). Where a bin has
              too few hour pairs or no spread in generation, the month's average stands in.
A factor outside the range of the BA's fuel factors for its month (`bounds`) is reported, never changed: fit() warns and
lists it in the table's meta["outside"]. An average can't leave the range unless a class's generation is negative (pumped
hydro, batteries); a marginal slope can if, as the BA's generation rises, a water-free class falls while a thermal class
rises by more.
Applied to the user's own hours, over any run of years, the table gives the water at the plants in each hour, so a hot
hour meets the grid's own hot-hour mix. Imports are not counted (the BA's own plants); the table says so in `note`.

    plant_water(table, mw, month, hour_utc, temp_c)   gal/h for each hour, average and marginal, consumed and withdrawn
    fit(...), GridTable.save(path), GridTable.load(path)
"""
from dataclasses import dataclass, field

import numpy as np

import warnings

BINS = 5
MIN_PAIRS = 60                 # hour pairs a month and bin needs for its own marginal slope
MAX_PAIRWISE = 500_000         # pairwise slopes in a Theil-Sen median; above it, a fixed sample of them


@dataclass(frozen=True)
class GridTable:
    ba: str
    edges: np.ndarray                      # (12, 24, bins - 1) temperature edges within each month and UTC hour, degC
    consumed: np.ndarray                   # (12, 24, bins) gal/MWh, average
    withdrawn: np.ndarray                  # (12, 24, bins) gal/MWh, average
    marginal_consumed: np.ndarray          # (12, bins) gal/MWh of added generation
    marginal_withdrawn: np.ndarray         # (12, bins)
    years: tuple = ()
    note: str = "the BA's own generation; imports not counted"
    meta: dict = field(default_factory=dict)

    def save(self, path):
        np.savez_compressed(path, ba=self.ba, edges=self.edges, consumed=self.consumed, withdrawn=self.withdrawn,
                            marginal_consumed=self.marginal_consumed, marginal_withdrawn=self.marginal_withdrawn,
                            years=np.array(self.years), note=self.note)

    @classmethod
    def load(cls, path):
        with np.load(path, allow_pickle=False) as z:
            return cls(ba=str(z["ba"]), edges=z["edges"], consumed=z["consumed"], withdrawn=z["withdrawn"],
                       marginal_consumed=z["marginal_consumed"], marginal_withdrawn=z["marginal_withdrawn"],
                       years=tuple(int(y) for y in z["years"]), note=str(z["note"]))


def calendar(hour_utc):
    """(month 0-11, hour of day 0-23, year) of hours since 1970-01-01 UTC."""
    h = np.asarray(hour_utc).astype("datetime64[h]")
    return (h.astype("datetime64[M]").astype(int) % 12, h.astype(int) % 24,
            h.astype("datetime64[Y]").astype(int) + 1970)


def _bin(edges, month, hod, temp_c):
    e = edges[month, hod]                                   # (n, bins - 1)
    return (np.asarray(temp_c)[:, None] > e).sum(axis=1)


def theil_sen(y, x, seed=0):
    """Theil-Sen slope of y on x: the median of the slopes between every two points with different x (a fixed random sample of
    MAX_PAIRWISE of them where there are more). NaN if no two x differ."""
    y, x = np.asarray(y, dtype=float), np.asarray(x, dtype=float)
    n = len(x)
    if n * (n - 1) // 2 <= MAX_PAIRWISE:
        i, j = np.triu_indices(n, 1)
    else:
        rng = np.random.default_rng(seed)
        i, j = rng.integers(0, n, MAX_PAIRWISE), rng.integers(0, n, MAX_PAIRWISE)
    dx = x[j] - x[i]
    keep = dx != 0
    return float(np.median((y[j] - y[i])[keep] / dx[keep])) if keep.any() else np.nan


def fit(ba, hour_utc, consumed, withdrawn, generation, temp_c, bins=BINS, pair_ok=None, bounds=None):
    """A GridTable from a BA's hourly intensity (gal/MWh), generation (MW) and the user's air temperature (degC) on the
    same UTC hours. Hours with any of them missing are left out. `pair_ok` (bool per hour), where given, marks the hours that
    may be differenced with the hour before; `bounds` ({"consumed": (lo, hi), "withdrawn": (lo, hi)}, 12 monthly values each),
    the range of the BA's fuel factors, against which every factor is checked (module docstring)."""
    hour_utc = np.asarray(hour_utc)
    consumed, withdrawn, generation, temp_c = (np.asarray(a, dtype=float) for a in (consumed, withdrawn, generation, temp_c))
    month, hod, year = calendar(hour_utc)
    ok = np.isfinite(consumed) & np.isfinite(withdrawn) & np.isfinite(generation) & np.isfinite(temp_c) & (generation > 0)
    edges = np.full((12, 24, bins - 1), np.nan)
    avg = {k: np.full((12, 24, bins), np.nan) for k in ("consumed", "withdrawn")}
    q = np.linspace(0, 100, bins + 1)[1:-1]
    for m in range(12):
        for h in range(24):
            s = ok & (month == m) & (hod == h)
            if not s.any():
                continue
            edges[m, h] = np.percentile(temp_c[s], q)
            b = (temp_c[s][:, None] > edges[m, h]).sum(axis=1)
            g = generation[s]
            for k, x in (("consumed", consumed[s]), ("withdrawn", withdrawn[s])):
                whole = np.sum(x * g) / np.sum(g)
                for i in range(bins):
                    gi = g[b == i]
                    avg[k][m, h, i] = np.sum(x[b == i] * gi) / np.sum(gi) if gi.sum() > 0 else whole

    # marginal: hour-to-hour changes, binned by the later hour's month and temperature bin
    mc, mw = np.full((12, bins), np.nan), np.full((12, bins), np.nan)
    pairable = ok[1:] & ok[:-1] & (np.diff(hour_utc) == 1)
    if pair_ok is not None:
        pairable &= np.asarray(pair_ok, dtype=bool)[1:]
    nxt = np.flatnonzero(pairable) + 1
    b_all = np.zeros(len(hour_utc), dtype=int)
    has_edges = ok & np.isfinite(edges[month, hod]).all(axis=1)
    b_all[has_edges] = _bin(edges, month[has_edges], hod[has_edges], temp_c[has_edges])
    dg = generation[nxt] - generation[nxt - 1]
    for k, x, out in (("consumed", consumed, mc), ("withdrawn", withdrawn, mw)):
        w = x * generation
        dw = w[nxt] - w[nxt - 1]
        for m in range(12):
            month_avg = np.nanmean(avg[k][m])
            for i in range(bins):
                s = (month[nxt] == m) & (b_all[nxt] == i)
                slope = theil_sen(dw[s], dg[s]) if s.sum() >= MIN_PAIRS else np.nan
                out[m, i] = slope if np.isfinite(slope) else month_avg
    years = tuple(int(y) for y in np.unique(year[ok]))
    outside = check(avg, {"consumed": mc, "withdrawn": mw}, bounds) if bounds else []
    if outside:
        warnings.warn(f"{ba}: {len(outside)} grid factors outside the range of its fuel factors, e.g. {outside[0]}", stacklevel=2)
    return GridTable(ba=ba, edges=edges, consumed=avg["consumed"], withdrawn=avg["withdrawn"],
                     marginal_consumed=mc, marginal_withdrawn=mw, years=years, meta={"outside": outside})


TOLERANCE = 0.5                # gal/MWh: the fuel factors are kept to two decimals


def check(avg, marginal, bounds):
    """Factors outside the BA's fuel-factor range for their month: [(kind, month 1-12, where, value, lo, hi)], where is
    ("hour", h, bin) for an average and ("bin", bin) for a marginal."""
    out = []
    for k, (lo, hi) in bounds.items():
        lo, hi = np.asarray(lo, dtype=float), np.asarray(hi, dtype=float)
        for m in range(12):
            a = avg[k][m]
            for h, i in zip(*np.nonzero(np.isfinite(a) & ((a < lo[m] - TOLERANCE) | (a > hi[m] + TOLERANCE)))):
                out.append((k, m + 1, ("hour", int(h), int(i)), round(float(a[h, i]), 1), round(float(lo[m]), 1), round(float(hi[m]), 1)))
            r = marginal[k][m]
            for i in np.flatnonzero(np.isfinite(r) & ((r < lo[m] - TOLERANCE) | (r > hi[m] + TOLERANCE))):
                out.append((f"marginal_{k}", m + 1, ("bin", int(i)), round(float(r[i]), 1), round(float(lo[m]), 1), round(float(hi[m]), 1)))
    return out


def lookup(table, month, hour_utc_of_day, temp_c):
    """Average and marginal gal/MWh for hours given by month (0-11), UTC hour of day (0-23) and air temperature."""
    month, hod = np.asarray(month, dtype=int), np.asarray(hour_utc_of_day, dtype=int)
    b = _bin(table.edges, month, hod, temp_c)
    return {"consumed": table.consumed[month, hod, b], "withdrawn": table.withdrawn[month, hod, b],
            "marginal_consumed": table.marginal_consumed[month, b], "marginal_withdrawn": table.marginal_withdrawn[month, b]}


def plant_water(table, mw, month, hour_utc_of_day, temp_c):
    """Water at the plants for a user's hourly electricity (MW, each hour one hour long): gal/h for each hour, average and
    marginal, consumed and withdrawn."""
    f = lookup(table, month, hour_utc_of_day, temp_c)
    mw = np.asarray(mw, dtype=float)
    return {k: mw * v for k, v in f.items()}


class RunWater:
    """Water at the power plants in a location's Monte Carlo, the one function every water user's runs call (design 0010's standard treatment).

    grid: {BA: {kind: gal/MWh for each hour}}, from lookup on each BA's GridTable; day_index, ndays and year_starts as the run's daily statistics
    have them (each hour's day, the number of days, each year's first day). stats(mw, mw_peak) takes one run's hourly electricity at its own load
    and at its peak-day load, MW, and gives grid_<BA>_<kind>_avg, the average day's plant water, and grid_<BA>_<kind>_peak_1in10, the 1-in-10-year
    peak day at the peak load, MGD. Hour by hour, plant water = MW x gal/MWh, so a year of it is the year's electricity times its
    generation-weighted factor."""

    def __init__(self, grid, day_index, ndays, year_starts):
        self.keys = [f"grid_{ba}_{kind}" for ba, factors in grid.items() for kind in factors]
        self.factors = np.vstack([np.asarray(f, dtype=float) for factors in grid.values() for f in factors.values()])   # (BA x kind, hour)
        self.ndays, self.year_starts = ndays, np.asarray(year_starts)
        # daily sums by reshape where the hours are whole days in order, which is faster; otherwise by each hour's day
        whole = len(day_index) == 24 * ndays and np.array_equal(day_index, np.repeat(np.arange(ndays), 24))
        self._daily = ((lambda x: x.reshape(len(x), ndays, 24).sum(axis=2)) if whole else
                       (lambda x: np.vstack([np.bincount(day_index, weights=row, minlength=ndays) for row in x])))

    def stats(self, mw, mw_peak):
        day_avg, day_peak = self._daily(self.factors * mw), self._daily(self.factors * mw_peak)
        avg = day_avg.sum(axis=1) / self.ndays / 1e6
        peak = np.quantile(np.maximum.reduceat(day_peak, self.year_starts, axis=1), 0.9, axis=1) / 1e6
        out = {}
        for i, key in enumerate(self.keys):
            out[f"{key}_avg"], out[f"{key}_peak_1in10"] = float(avg[i]), float(peak[i])
        return out
