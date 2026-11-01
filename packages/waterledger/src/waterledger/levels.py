"""The levels and verdicts waterledger.org shows a reader: how large a campus is against what is there, and how an estimate reads against a reported figure.
The bands are this project's reading of the numbers, not regulations [A]; where a rule sets a line (Michigan's Part 327, the Great Lakes Compact), the line comes from the state's context
(context.withdrawals). A display words the levels. The paid review's ratings are its own and are not here."""
import decimal
import math

LEVELS = {"water_system_pct": [2, 10],        # campus at its peak, as homes, percent of a system's connections: small under the first, large from the second [A]
          "sewer_spare_pct": [10, 50],        # campus at its peak, percent of a plant's spare room [A]
          "small_system": {"connections": 5000, "peak_share": 0.25},     # few connections, or a campus a quarter of them at its peak [A]
          "near_design": 0.85,                # a plant averaging this share of its design flow is close to its size [A]
          "peak_differs": 1.15,               # a peak this far above the average is worth saying [A]
          "sediment_about_same": [0.8, 1.25]}  # finished site's sediment against today's, within which "about as much" is fair [A]


def _bands(v, b):
    return "small" if v < b[0] else "mid" if v < b[1] else "large"


def water_system(peak_pct):
    return _bands(peak_pct, LEVELS["water_system_pct"])


def sewer(full, peak_pct):
    """A plant at its design size is large whatever the campus adds. Without its flow, there is nothing to rate: info."""
    return "large" if full else "info" if peak_pct is None else _bands(peak_pct, LEVELS["sewer_spare_pct"])


def withdrawal(peak_mgd, W, rules=True):
    """(level, line) for water pumped at a site, on its peak day. Where a state's rules are reviewed, `line` is the rule that applies: "below", "register", "zone_c" or "permit". Elsewhere
    the same numbers are only low and high bands: "low", "moderate" or "high". W: context.withdrawals."""
    if not rules:
        return ("small", "low") if peak_mgd < W["register_mgd"] else ("mid", "moderate") if peak_mgd <= W["permit_mgd"] else ("large", "high")
    return (("small", "below") if peak_mgd < W["register_mgd"] else ("mid", "register") if peak_mgd <= W["zone_c_permit_mgd"]
            else ("mid", "zone_c") if peak_mgd <= W["permit_mgd"] else ("large", "permit"))


def compact_share(evaporated_mgd, W):
    """Water leaving the Great Lakes basin, percent of the consumptive use at which the other states review a project."""
    return 100 * evaporated_mgd / W["compact_use_mgd"]


def compact(share):
    return "small" if share < 100 else "large"


def small_system(connections, peak_homes):
    """A system this campus could strain: few connections, or a campus a quarter of them at its peak. False where connections aren't known."""
    S = LEVELS["small_system"]
    return bool(connections) and (connections < S["connections"] or peak_homes > S["peak_share"] * connections)


def near_design(flow, design):
    return bool(flow) and flow >= LEVELS["near_design"] * design


def peak_differs(avg, peak):
    return peak > avg * LEVELS["peak_differs"]


def sediment_change(now, after):
    lo, hi = LEVELS["sediment_about_same"]
    return "less" if after < now * lo else "more" if after > now * hi else "same"


def _mult(r):
    """A multiple as a reader sees it: one decimal below 10, two significant figures above."""
    if r < 10:
        s = f"{decimal.Decimal(repr(r)).quantize(decimal.Decimal('0.1'), rounding=decimal.ROUND_HALF_UP)}"    # 1.15 reads 1.2, as a browser rounds it
        return s.removesuffix(".0")
    p = 10 ** (math.floor(math.log10(r)) - 1)
    return f"{math.floor(r / p + 0.5) * p:,.0f}"


def compare(ask, ours, at_least=False):
    """A reported figure against an estimate on the same basis, in words. ask: [low, high] MGD as reported; ours: a Range; at_least: the report says "more than". The estimate is not fitted to it."""
    a, b, mid = ask[0], ask[1], ours.p50
    inside = ours.p10 <= b and ours.p90 >= a
    if at_least:
        return ("Our middle estimate is above the reported minimum." if mid >= a
                else f"The reported minimum is about {_mult(a / mid)} times our middle estimate" + (", inside our likely range." if inside else ", above our likely range."))
    if a <= mid <= b:
        return "Our middle estimate is about the same as the reported figure." if a == b else "Our middle estimate is inside the reported range."
    k = mid / b if mid > b else a / mid
    if k < 1.15:
        return "Our middle estimate is about the same as the reported figure."
    return ((f"Our middle estimate is about {_mult(k)} times the reported figure" if mid > b else f"The reported figure is about {_mult(k)} times our middle estimate")
            + (", which is inside our likely range." if inside else ", outside our likely range."))


def site_levels(est, ref):
    """The levels a reader sees for an estimate, by card; a card that doesn't apply is left out."""
    from waterledger import comparisons as cm
    out, s, w = {}, est.site, est.water
    ctx = s.place.context()
    W = ref.get("withdrawals")
    by = {c.against: c for c in est.comparisons}
    if "water_system" in by and by["water_system"].percent:
        out["water_system"] = water_system(by["water_system"].percent.peak_day.p50)
    if s.wastewater == "sewer" and not w.reuse and ctx.wastewater.plants:
        room = cm.sewer_room(ctx.wastewater.plants[0])
        out["sewer"] = sewer(room is not None and room <= 0, by["sewer_spare_room"].percent.peak_day.p50 if "sewer_spare_room" in by else None)
    if W and s.source == "wells":
        out["withdrawal"], out["withdrawal_line"] = withdrawal(w.withdrawn.peak_day.p50, W, ref.get("state_rules", False))
    if W and ctx.receiving.great_lake:
        out["great_lakes"] = compact(compact_share(w.consumed.avg.p50, W))
    return out
