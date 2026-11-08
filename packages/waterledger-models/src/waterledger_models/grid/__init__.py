"""The grid component (design 0007): water at the power plants supplying a water user's electricity, hour by hour, at
grid level. One component for every water user: it takes any user's hourly electricity and the hour's air temperature
at the user and returns the plants' water, consumed and withdrawn. It knows a balancing authority (BA) only through a
GridTable; it never names a plant.

A GridTable is fit from the BA's own hours (waterledger_data.grid930.intensity: EIA-930 generation by fuel x plant
water by fuel and month) paired with the temperature at the user's location in the same hours. Within each month and
UTC hour, the hours are split into temperature bins (quintiles by default), and each bin keeps:
    average   the plants' water per MWh of the BA's generation in those hours, weighted by generation, so the table
              applied to the fit hours gives back their water exactly;
    marginal  the water per MWh of added generation (Siler-Evans et al. 2012): the slope of the hour-to-hour change in
              the BA's plant water against the change in its generation, by month and bin. Where a bin has too few hour
              pairs or no spread in generation, the month's average stands in.
Applied to the user's own hours, over any run of years, the table gives the water at the plants in each hour, so a hot
hour meets the grid's own hot-hour mix. Imports are not counted (the BA's own plants); the table says so in `note`.

    plant_water(table, mw, month, hour_utc, temp_c)   gal/h for each hour, average and marginal, consumed and withdrawn
    fit(...), GridTable.save(path), GridTable.load(path)
"""
from dataclasses import dataclass, field

import numpy as np

BINS = 5
MIN_PAIRS = 60                 # hour pairs a month and bin needs for its own marginal slope


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


def fit(ba, hour_utc, consumed, withdrawn, generation, temp_c, bins=BINS):
    """A GridTable from a BA's hourly intensity (gal/MWh), generation (MW) and the user's air temperature (degC) on the
    same UTC hours. Hours with any of them missing are left out."""
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
    nxt = np.flatnonzero(ok[1:] & ok[:-1] & (np.diff(hour_utc) == 1)) + 1
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
                if s.sum() >= MIN_PAIRS and np.var(dg[s]) > 0:
                    out[m, i] = np.cov(dw[s], dg[s])[0, 1] / np.var(dg[s], ddof=1)
                else:
                    out[m, i] = month_avg
    years = tuple(int(y) for y in np.unique(year[ok]))
    return GridTable(ba=ba, edges=edges, consumed=avg["consumed"], withdrawn=avg["withdrawn"],
                     marginal_consumed=mc, marginal_withdrawn=mw, years=years)


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
