"""Quantile mapping of an ERA5 cell's hourly weather to nearby weather stations (design 0005, decided Nov 4, 2026, model 1.8, for shore cells;
land cells added Nov 6, 2026, model 1.9).

What is corrected: air temperature T and the dew point Td (C), each by an additive delta read off its own quantile (qm-3, model 1.10).
Td is kept at or below the corrected T, so relative humidity stays at or below 100%. RH comes from T and Td by the Magnus form the stations use.
Through model 1.9 (qm-1, qm-2) the second variable was the dew-point depression D = T - Td. Mapped apart from T, D let a hot-day temperature
correction carry the dew point up with it: at model 1.9's checked places the corrected peak days ran 0.72 C (Michigan) and 0.35 C (Ohio) above
their stations in wet-bulb, with about 37 more hours a year above a 22 C wet-bulb. Mapping Td itself brought both to 0.23 C (methods log,
Nov 8, 2026).

Bins: calendar month (fitted on that month and the months either side, applied to that month) by 3-hour block of local standard time,
12 x 8 = 96 bins; 99 quantiles in each (1% to 99%), deltas held constant beyond them.

Which cells, from which stations (Andrew's decisions, Nov 4 and Nov 6, 2026):
- Every cell is corrected where a station is near enough. Model 1.8 corrected only cells under SHORE_LAND (90%) land; from model 1.9
  land cells (at least 90% land) are corrected too, from the land stations (whose own nearest cell is at least SHORE_LAND land) within
  R_KM, at most K, weighted 1/d^2, as shore cells are from shore stations (the methods log, Nov 6: Wisconsin's inland cells ran about
  0.6 C cool; held out across the five states, the correction brings land cells closer to their stations). A land cell with no land
  station that near is left as it is and flagged.
- A shore cell is corrected only from shore stations: stations whose own nearest cell is under SHORE_LAND land (Nov 5: the nearest cell,
  not the land rule's, which moves the stations right on the water inland, Corpus Christi NAS among them). A shore cell is corrected from the shore stations within R_KM of its center, at most K, weighted 1/d^2 (d at least
  5 km), and with no shore station that near it is left as it is and flagged.
- The stations' quantiles are averaged and the cell mapped onto them, each station's temperature moved to the cell's ERA5 elevation at
  LAPSE (the "lapse" way of the prototype)."""
import numpy as np

P = (np.arange(99) + 1) / 100
MAGNUS = 17.625, 243.04                 # Alduchov and Eskridge (1996), as climate.isd_hourly uses
R_KM, K, LAPSE = 100.0, 4, -6.5e-3      # search radius, stations at most, C per m
SHORE_LAND = 0.9                        # cells under this land fraction are corrected; stations whose cell is under it anchor them
METHOD = "qm-3"                         # qm-1 (model 1.8): shore cells only, T and D; qm-2 (1.9): land cells too; qm-3 (1.10): T and Td
FIT = "t-td"                            # what fit() returns quantiles of; cached station fits are keyed by it (qm-1 and qm-2 fitted T and D, "t-d")
LAND_FROM_LAND = True                   # land cells from land stations only (whose own nearest cell is at least SHORE_LAND land), as shore cells from shore ones


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
    """Quantiles of T and Td in each bin: array (2, 12, 8, 99). `keep`: a boolean mask of the hours to fit on."""
    m, b = bins(times)
    x = np.stack([np.asarray(t, float), np.asarray(td, float)])
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
    x = np.stack([np.asarray(t, float), np.asarray(td, float)])
    out = x.copy()
    for mo in range(12):
        for bl in range(8):
            sel = (m == mo) & (b == bl)
            for v in range(2):
                out[v, sel] = x[v, sel] + np.interp(x[v, sel], qe[v, mo, bl], delta[v, mo, bl])
    return out[0], np.minimum(out[1], out[0])


def km(a, b, c, d):
    p = np.pi / 180
    h = np.sin((c - a) * p / 2) ** 2 + np.cos(a * p) * np.cos(c * p) * np.sin((d - b) * p / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(h))


def is_shore_station(station):
    """A station anchors shore cells when its own nearest cell is under SHORE_LAND land: `shore_land`, else `cell_land` for a record
    that has only that (the prototype's, and tests')."""
    return station.get("shore_land", station["cell_land"]) < SHORE_LAND


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
    reason: "cell under 90% land" or "cell at least 90% land" when applied; "no shore station within 100 km" or "no land station within 100 km" when not.
    `cell`: {lat, lon, land, elev_m}; its ERA5 quantiles are fitted on `times` here."""
    t, td = np.asarray(t, float), np.asarray(td, float)
    note = {"method": METHOD, "applied": False, "stations": []}
    shore = cell["land"] < SHORE_LAND
    pool = stations if shore or not LAND_FROM_LAND else [s for s in stations if not is_shore_station(s)]
    ws = weights(cell["lat"], cell["lon"], pool, r_km, k, shore_only=shore)
    if not ws:
        return t, td, note | {"reason": f"no {'shore' if shore else 'land' if LAND_FROM_LAND else ''} station within {r_km:.0f} km".replace("  ", " ")}
    qe = fit(times, t, td)
    tc, tdc = apply(times, t, td, qe, delta({**cell, "qe": qe}, pool, r_km=r_km, k=k, shore_only=shore))
    used = [(s["id"], s.get("name"), round(float(km(cell["lat"], cell["lon"], s["lat"], s["lon"])), 1), round(float(w), 3)) for s, w in ws]
    return tc, tdc, note | {"applied": True, "reason": f"cell {'under' if shore else 'at least'} {SHORE_LAND:.0%} land", "stations": used}
