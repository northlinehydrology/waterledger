"""Quantile mapping of an ERA5 cell's hourly weather to weather stations near the shore (design 0005, decided Nov 4, 2026; model 1.8).

What is corrected: air temperature T and the dew-point depression D = T - Td (C), each by an additive delta read off its own quantile.
D is kept at or above 0 after correction, so the corrected dew point never passes the corrected temperature and relative humidity
stays at or below 100%. RH comes from T and Td by the Magnus form the stations use.

Bins: calendar month (fitted on that month and the months either side, applied to that month) by 3-hour block of local standard time,
12 x 8 = 96 bins; 99 quantiles in each (1% to 99%), deltas held constant beyond them.

Which cells, from which stations (Andrew's decisions, Nov 4, 2026):
- Only cells under SHORE_LAND (90%) land are corrected; cells at least 90% land keep ERA5 as it is.
- A cell is corrected only from shore stations: stations whose own cell (the land rule's, as a place there would get) is itself under
  SHORE_LAND land. A shore cell is corrected from the shore stations within R_KM of its center, at most K, weighted 1/d^2 (d at least
  5 km), and with no shore station that near it is left as it is and flagged.
- The stations' quantiles are averaged and the cell mapped onto them, each station's temperature moved to the cell's ERA5 elevation at
  LAPSE (the "lapse" way of the prototype)."""
import numpy as np

P = (np.arange(99) + 1) / 100
MAGNUS = 17.625, 243.04                 # Alduchov and Eskridge (1996), as climate.isd_hourly uses
R_KM, K, LAPSE = 100.0, 4, -6.5e-3      # search radius, stations at most, C per m
SHORE_LAND = 0.9                        # cells under this land fraction are corrected; stations whose cell is under it anchor them
METHOD = "qm-1"


def rh_from(t, td):
    a = lambda x: np.exp(MAGNUS[0] * x / (MAGNUS[1] + x))
    return np.clip(100 * a(np.asarray(td, float)) / a(np.asarray(t, float)), 1, 100)


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
            q[:, mo, bl] = np.quantile(x[:, near & (b == bl)], P, axis=1).T
    return q


def apply(times, t, td, qe, delta):
    """Correct T and Td: each hour moves by the delta at its own quantile in its bin's ERA5 distribution `qe`. Returns (T, Td), Td <= T."""
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


def is_shore_station(station):
    """A station anchors shore cells when its own cell (`cell_land`, the land rule's cell at the station) is under SHORE_LAND land."""
    return station["cell_land"] < SHORE_LAND


def weights(lat, lon, stations, r_km=R_KM, k=K, shore_only=True):
    """[(station, weight)] for the stations within r_km of (lat, lon), nearest k, 1/d^2; only shore stations unless `shore_only` is false."""
    d = sorted((km(lat, lon, s["lat"], s["lon"]), i) for i, s in enumerate(stations) if not shore_only or is_shore_station(s))
    d = [(x, i) for x, i in d if x <= r_km][:k]
    if not d:
        return []
    w = np.array([1 / max(x, 5.0) ** 2 for x, _ in d])
    return [(stations[i], wi / w.sum()) for (_, i), wi in zip(d, w)]


def delta(cell, stations, lapse=True, **kw):
    """The delta (2, 12, 8, 99) for a cell {lat, lon, qe, elev_m} from stations [{lat, lon, cell_land, qt, elev_m}]; None if none is near.
    `qt` is a station's fit on its own hours; `qe` the cell's ERA5 fit."""
    ws = weights(cell["lat"], cell["lon"], stations, **kw)
    if not ws:
        return None
    tq = []
    for s, w in ws:
        q = s["qt"].copy()
        if lapse and s.get("elev_m") is not None:
            q[0] += LAPSE * (cell["elev_m"] - s["elev_m"])
        tq.append(w * q)
    return sum(tq) - cell["qe"]


def correct(times, t, td, cell, stations, r_km=R_KM, k=K):
    """A cell's hourly (T, Td) corrected under the rule above, and what was done: {method, applied, reason, stations [(id, name, km, weight)]}.
    `cell`: {lat, lon, land, elev_m}; its ERA5 quantiles are fitted on `times` here."""
    t, td = np.asarray(t, float), np.asarray(td, float)
    note = {"method": METHOD, "applied": False, "stations": []}
    if cell["land"] >= SHORE_LAND:
        return t, td, note | {"reason": f"cell at least {SHORE_LAND:.0%} land"}
    ws = weights(cell["lat"], cell["lon"], stations, r_km, k)
    if not ws:
        return t, td, note | {"reason": f"no shore station within {r_km:.0f} km"}
    qe = fit(times, t, td)
    tc, tdc = apply(times, t, td, qe, delta({**cell, "qe": qe}, stations, r_km=r_km, k=k))
    used = [(s["id"], s.get("name"), round(float(km(cell["lat"], cell["lon"], s["lat"], s["lon"])), 1), round(float(w), 3)) for s, w in ws]
    return tc, tdc, note | {"applied": True, "reason": f"cell under {SHORE_LAND:.0%} land", "stations": used}
