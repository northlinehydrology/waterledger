"""Quantile mapping of ERA5 cells to ISD stations, the prototype for design 0005.

What is corrected: air temperature T and the dew-point depression D = T - Td (C), each by an additive delta read off its own
quantile. D is kept at or above 0 after correction, so the corrected dew point never passes the corrected temperature and relative
humidity stays at or below 100%. RH comes from T and Td by the Magnus form the stations use.

Bins: calendar month (fitted on that month and the months either side, applied to that month) by 3-hour block of local standard
time, 12 x 8 = 96 bins; 99 quantiles in each (0.5% to 99.5%), deltas held constant beyond them.

Carrying a correction to a cell: from the anchor stations within R_KM of the cell's center, at most K, weighted 1/d^2 (d at least
5 km). Three ways (`how`):
- "bias":   the stations' own cell biases (station quantile - its cell's quantile), averaged and added to the target cell.
- "target": the stations' quantiles averaged, and the target cell mapped onto them.
- "lapse":  as "target", with each station's temperature moved to the target cell's ERA5 elevation at 6.5 C per km.
A cell with no station within R_KM is left as it is."""
import numpy as np

P = (np.arange(99) + 1) / 100
MAGNUS = 17.625, 243.04
R_KM, K, LAPSE = 100.0, 4, -6.5e-3


def rh_from(t, td):
    a = lambda x: np.exp(MAGNUS[0] * x / (MAGNUS[1] + x))
    return np.clip(100 * a(td) / a(t), 1, 100)


def bins(times):
    """Month (0-11) and 3-hour block (0-7) for ISO local times."""
    t = np.asarray(times, dtype="datetime64[h]")
    month = t.astype("datetime64[M]").astype(int) % 12
    hour = (t - t.astype("datetime64[D]")).astype(int)
    return month, hour // 3


def fit(times, t, td, keep=None):
    """Quantiles of T and D in each bin: array (2, 12, 8, 99). `keep`: a boolean mask of the hours to fit on."""
    m, b = bins(times)
    x = np.stack([np.asarray(t, float), np.asarray(t, float) - np.asarray(td, float)])
    if keep is not None:
        m, b, x = m[keep], b[keep], x[:, keep]
    q = np.empty((2, 12, 8, len(P)))
    for mo in range(12):
        near = (m == mo) | (m == (mo + 1) % 12) | (m == (mo - 1) % 12)
        for bl in range(8):
            sel = near & (b == bl)
            q[:, mo, bl] = np.quantile(x[:, sel], P, axis=1).T
    return q


def apply(times, t, td, qe, delta):
    """Correct T and Td: each hour's value moves by the delta at its own quantile in its bin's ERA5 distribution `qe`."""
    m, b = bins(times)
    x = np.stack([np.asarray(t, float), np.asarray(t, float) - np.asarray(td, float)])
    out = x.copy()
    for mo in range(12):
        for bl in range(8):
            sel = (m == mo) & (b == bl)
            for v in range(2):
                out[v, sel] = x[v, sel] + np.interp(x[v, sel], qe[v, mo, bl], delta[v, mo, bl])
    tc, dc = out[0], np.maximum(out[1], 0.0)
    return tc, tc - dc


def km(a, b, c, d):
    p = np.pi / 180
    h = np.sin((c - a) * p / 2) ** 2 + np.cos(a * p) * np.cos(c * p) * np.sin((d - b) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(h))


def weights(lat, lon, anchors, r_km=R_KM, k=K, nearest_only=False):
    """[(anchor, weight)] for the stations within r_km of (lat, lon), nearest k, 1/d^2."""
    d = sorted((km(lat, lon, a["lat"], a["lon"]), i) for i, a in enumerate(anchors))
    d = [(x, i) for x, i in d if x <= r_km][: 1 if nearest_only else k]
    if not d:
        return []
    w = np.array([1 / max(x, 5.0) ** 2 for x, _ in d])
    return [(anchors[i], wi / w.sum()) for (_, i), wi in zip(d, w)]


def delta(target, anchors, how, **kw):
    """The delta (2, 12, 8, 99) for a target {lat, lon, qe, elev_m}, from anchors [{lat, lon, qt, qe, elev_m}]; None if no station is near."""
    ws = weights(target["lat"], target["lon"], anchors, **kw)
    if not ws:
        return None
    if how == "bias":
        return sum(w * (a["qt"] - a["qe"]) for a, w in ws)
    tq = []
    for a, w in ws:
        q = a["qt"].copy()
        if how == "lapse" and a.get("elev_m") is not None:
            q[0] += LAPSE * (target["elev_m"] - a["elev_m"])
        tq.append(w * q)
    return sum(tq) - target["qe"]
