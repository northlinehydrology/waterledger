"""Daily statistics shared by every water user model: an hourly series to daily totals, then the average day, the 1-in-10-year peak day (the 90th
percentile of annual maxima), the record day, months and years. Moved from datacenter/cooling.py unchanged (design 0009)."""
import numpy as np


def groups(labels):
    """Each label's run of positions, in label order, for labels already sorted (a run's days, years or months): [slice]. A slice
    picks the same values in the same order as `labels == label`, so a statistic over it is the same to the bit, without a pass over
    every day per label."""
    labels = np.asarray(labels)
    cut = np.r_[0, np.flatnonzero(labels[1:] != labels[:-1]) + 1, len(labels)]
    return [slice(a, b) for a, b in zip(cut[:-1], cut[1:])]


def daily_stats(day_index, ndays, years, gal_per_kwh_hour, kw, months=None, by=None):
    """From hourly gal/kWh and IT kW, compute daily MGD and summary statistics: average day, 1-in-10-year peak day (90th percentile
    of annual maxima), record day, average year, and with `months` (each day's YYYY-MM) the highest month's average day, the highest
    90 straight days' average and the highest calendar year. `by`: (groups(years), groups(months)) when the days are in order, which
    gives the same numbers faster."""
    daily = np.bincount(day_index, weights=gal_per_kwh_hour * kw, minlength=ndays) / 1e6
    in_years = [daily[s] for s in by[0]] if by else [daily[years == y] for y in np.unique(years)]
    ann_max = np.array([d.max() for d in in_years])
    out = {"avg": float(daily.mean()), "peak_1in10": float(np.quantile(ann_max, 0.9)), "record": float(daily.max()),
           "annual_mg": float(daily.mean() * 365.25)}
    if months is not None:
        in_months = [daily[s] for s in by[1]] if by else [daily[months == m] for m in np.unique(months)]
        out["max_month"] = float(max(d.mean() for d in in_months))
        out["max_90day"] = float(np.convolve(daily, np.ones(90) / 90, "valid").max()) if len(daily) >= 90 else float(daily.mean())
        out["worst_year_mg"] = float(max(d.sum() for d in in_years))
    return out


def summarize(days, mgd):
    """Statistics of one daily series (MGD by ISO date), for figures and single-run reports: average day, highest month, 1-in-10-year
    peak day, record day and its date, average and highest year."""
    days, v = np.array(days), np.array(mgd)
    years, months = np.array([d[:4] for d in days]), np.array([d[:7] for d in days])
    ann = [v[years == y] for y in np.unique(years)]
    return {"avg": float(v.mean()), "max_month": float(max(v[months == m].mean() for m in np.unique(months))),
            "peak_1in10": float(np.quantile([a.max() for a in ann], 0.9)), "record": float(v.max()), "record_day": str(days[v.argmax()]),
            "annual_mg": float(v.mean() * 365.25), "worst_year_mg": float(max(a.sum() for a in ann))}
