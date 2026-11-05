"""The prototype's ways of carrying a correction, on the package's quantile mapping (waterledger_models.quantile_mapping, which ships in
model 1.8 and holds the method: T and dew-point depression, month by 3-hour block, 99 quantiles, additive deltas).

Ways (`how`), from the stations within R_KM of the cell's center, at most K, weighted 1/d^2 (d at least 5 km):
- "bias":   the stations' own cell biases (station quantile - its cell's quantile), averaged and added to the target cell.
- "target": the stations' quantiles averaged, and the target cell mapped onto them.
- "lapse":  as "target", with each station's temperature moved to the target cell's ERA5 elevation at 6.5 C per km.
`shore_only=True` takes only shore stations (their own cell under 90% land), the rule decided Nov 4, 2026; the package's default.
`sources` limits the stations to those sources ("isd", "isd-linked", "eccc"), to see what each set adds.
A cell with no station within R_KM is left as it is."""
from waterledger_models import quantile_mapping as Q
from waterledger_models.quantile_mapping import K, LAPSE, P, R_KM, SHORE_LAND, apply, bins, fit, km, rh_from  # noqa: F401


def weights(lat, lon, anchors, r_km=R_KM, k=K, nearest_only=False, shore_only=False, sources=None):
    if sources:
        anchors = [a for a in anchors if a.get("source", "isd") in sources]
    return Q.weights(lat, lon, anchors, r_km, 1 if nearest_only else k, shore_only)


def delta(target, anchors, how, **kw):
    """The delta (2, 12, 8, 99) for a target {lat, lon, qe, elev_m}, from anchors [{lat, lon, cell_land, qt, qe, elev_m}]; None if no station is near."""
    src = kw.pop("sources", None)
    if src:
        anchors = [a for a in anchors if a.get("source", "isd") in src]
    if how in ("target", "lapse"):
        nearest = kw.pop("nearest_only", False)
        return Q.delta(target, anchors, lapse=how == "lapse", k=1 if nearest else kw.pop("k", K), shore_only=kw.pop("shore_only", False), **kw)
    ws = weights(target["lat"], target["lon"], anchors, **kw)
    return sum(w * (a["qt"] - a["qe"]) for a, w in ws) if ws else None
