"""The levels and verdicts waterledger.org shows a reader: how large a campus is against what is there, and how an estimate reads against a reported figure.
The bands are this project's reading of the numbers, not regulations [A]; where a reviewed rule sets a line (a state's withdrawal rules, the Great Lakes Compact), the line comes from the state's context
(context.withdrawals, from waterledger.rules); a state whose rules aren't reviewed has no lines, and says so (Estimate.not_covered). The calculator is a what-if: nothing here changes an estimate. A display words the levels. The paid review's ratings are its own and are not here."""
import decimal
import math

LEVELS = {"water_system_pct": [2, 10],        # campus at its peak, as homes, percent of a system's connections: small under the first, large from the second [A]
          "sewer_spare_pct": [10, 50],        # campus at its peak, percent of a plant's spare room [A]
          "small_system": {"connections": 5000, "peak_share": 0.25},     # few connections, or a campus a quarter of them at its peak [A]
          "near_design": 0.85,                # a plant averaging this share of its design flow is close to its size [A]
          "peak_differs": 1.15,               # a peak this far above the average is worth saying [A]
          "sediment_about_same": [0.8, 1.25]}  # finished site's sediment against today's, within which "about as much" is fair [A]

# USGS Circular 1441 (Dieter et al. 2018): 39,000 Mgal/d of public supply to 283 million people in 2015, about 138 gallons a person a day, businesses and losses included
PUBLIC_SUPPLY_GPCD = 39000e6 / 283e6
NOT_REVIEWED_NOTE = "This state's water rules are not yet reviewed, so no legal line or level is shown. The estimate stands as it is."
# Michigan's permit lines in plain words, for data written before 3.26.0 (MCL 324.32723); a state's rules file carries its own (waterledger.rules)
PERMIT_NOTES = {"permit": "The estimated need exceeds Michigan's 2 million gallons a day. A new or increased withdrawal above that needs a water withdrawal permit from EGLE before it starts.",
                "zone_c": "The estimated need exceeds 1 million gallons a day. In a Zone C area, a new or increased withdrawal above that needs a permit from EGLE."}


def people_supplied(mgd):
    """Water as the public supply of about this many people, at the national figure per person."""
    return mgd * 1e6 / PUBLIC_SUPPLY_GPCD


def _bands(v, b):
    return "small" if v < b[0] else "mid" if v < b[1] else "large"


def water_system(peak_pct):
    return _bands(peak_pct, LEVELS["water_system_pct"])


def sewer(full, peak_pct):
    """A plant at its design size is large whatever the campus adds. Without its flow, there is nothing to rate: info."""
    return "large" if full else "info" if peak_pct is None else _bands(peak_pct, LEVELS["sewer_spare_pct"])


def _lines(W):
    """A state's withdrawal lines, low to high. Data written before 3.26.0 (Michigan's context.withdrawals) has the lines as keys."""
    if W.get("lines"):
        return sorted(W["lines"], key=lambda x: x["mgd"])
    if "permit_mgd" not in W:
        return []
    return [{"key": "register", "mgd": W["register_mgd"], "level": "mid", "at_least": True},
            {"key": "zone_c", "mgd": W["zone_c_permit_mgd"], "level": "mid", "flag": PERMIT_NOTES["zone_c"]},
            {"key": "permit", "mgd": W["permit_mgd"], "level": "large", "flag": PERMIT_NOTES["permit"]}]


def applies(line, basin=None, source=None, huc=None, county=None, areas=None, inside=True):
    """Whether a line applies at a place: `basin` is whether it is in the Great Lakes basin, `source` the water taken ("ground", "surface" or "lake": a Great Lake itself),
    `huc` the place's main watershed (a HUC code) and `county` its county's five-digit FIPS code. A line with `huc` (HUC prefixes: a river basin commission's basin) or
    `counties` (FIPS codes: a management area made of whole counties) applies only at a place known to be in one of them. A line with `areas` applies
    where `areas` (rules.place_areas) puts the place inside; where the place is partly inside, only when `inside` is True."""
    w, s = line.get("where"), line.get("source")
    if "huc" in line and not (huc and any(str(huc).startswith(h) for h in line["huc"])):
        return False
    if "counties" in line and not (county and str(county) in line["counties"]):
        return False
    if "areas" in line:
        # `areas`: the place's membership (rules.place_areas); a place partly inside takes the line when `inside` (the part inside) and not otherwise
        got = [(areas or {}).get(g, {}).get("status") for g in line["areas"]]
        if not ("in" in got or ("part" in got and inside)):
            return False
    return (w is None or (w == "great_lakes_basin") == bool(basin)) and (s is None or source is None or source in s)


def tested_on(line, q, W=None, peak=False):
    """The water a line is tested on, from q = {"withdrawn_month", "withdrawn_peak", "consumed_90", "consumed_peak"} (MGD): the line's measure ("withdrawn" or "consumed")
    on its period. A capacity line, or `peak`, takes the peak day; a 30- or 90-day line takes the highest month for water withdrawn and the highest 90 days for water used
    up (for a 30-day line, the nearest period the estimate has [A]; the peak day beside it is tested too). Data without the month falls back to the peak day."""
    m = line.get("measure", "withdrawn")
    per = line.get("period", (W or {}).get("period", "30 days"))
    if peak or per == "capacity":
        return q[f"{m}_peak"]
    v = q.get("withdrawn_month") if m == "withdrawn" else q.get("consumed_90")
    return q[f"{m}_peak"] if v is None else v


def withdrawal(mgd, W, basin=None, source=None, peak=False, huc=None, county=None, areas=None, inside=True):
    """(level, line) for water pumped or taken at a site, where a state's rules are reviewed: `line` is the key of the highest line the water exceeds ("below" under all of them),
    from the state's rules (waterledger.rules) as they apply at the place. `mgd` is one number every line is tested on, or the water by measure and period (tested_on).
    W: context.withdrawals."""
    q = mgd if isinstance(mgd, dict) else {"withdrawn_month": mgd, "withdrawn_peak": mgd, "consumed_90": mgd, "consumed_peak": mgd}
    out = ("small", "below")
    for x in _lines(W):
        v = tested_on(x, q, W, peak)
        if applies(x, basin, source, huc, county, areas, inside) and v is not None and (v >= x["mgd"] if x.get("at_least") else v > x["mgd"]):
            out = (x["level"], x["key"])
    return out


def permit_flag(line, W=None):
    """The permit line an estimate exceeds, from withdrawal()'s `line`: its key where the line carries a flag (Michigan: "permit", or "zone_c", which applies only
    in a Zone C area), else None. A flag for the reader. It never changes an estimate."""
    if W is None:
        return line if line in ("permit", "zone_c") else None
    return line if any(x["key"] == line and x.get("flag") for x in _lines(W)) else None


def flag_note(line, W):
    """The sentence a reader sees for a flagged line."""
    return next((x["flag"] for x in _lines(W) if x["key"] == line and x.get("flag")), None)


def compact_share(evaporated_mgd, W):
    """Water leaving the Great Lakes basin, percent of the consumptive use at which the other states review a project. The Compact's period is any 90 days:
    `evaporated_mgd` should be the highest 90 days' average (site_levels)."""
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
                else f"The reported minimum is about {_mult(a / mid)} times our middle estimate" + (", inside the range across our assumptions." if inside else ", above the range across our assumptions."))
    if a <= mid <= b:
        return "Our middle estimate is about the same as the reported figure." if a == b else "Our middle estimate is inside the reported range."
    k = mid / b if mid > b else a / mid
    if k < 1.15:
        return "Our middle estimate is about the same as the reported figure."
    return ((f"Our middle estimate is about {_mult(k)} times the reported figure" if mid > b else f"The reported figure is about {_mult(k)} times our middle estimate")
            + (", which is inside the range across our assumptions." if inside else ", outside the range across our assumptions."))


def site_levels(est, ref):
    """The levels a reader sees for an estimate, by card; a card that doesn't apply is left out. Read from the estimate, never written back to it. For well pumping: the number, as the public supply
    of about how many people, and either a reviewed rule's line and flags or a note that the state's rules aren't reviewed."""
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
    if s.source == "wells":
        avg, peak = w.withdrawn.avg.p50, w.withdrawn.peak_day.p50
        out["withdrawal_mgd"], out["withdrawal_peak_day_mgd"] = avg, peak
        out["withdrawal_people"], out["withdrawal_people_peak_day"] = people_supplied(avg), people_supplied(peak)
        if W and ref.get("state_rules", False) and _lines(W):
            # Each reviewed line is tested on its own measure and period (tested_on), and every line on the peak day beside it
            basin = bool(ctx.receiving.great_lake or ctx.receiving.great_lakes_basin)
            q = {"withdrawn_month": w.withdrawn_max_month.p50 if w.withdrawn_max_month is not None else None, "withdrawn_peak": peak,
                 "consumed_90": w.consumed_max_90day.p50 if w.consumed_max_90day is not None else None, "consumed_peak": w.consumed.peak_day.p50}
            sheds = getattr(ctx.receiving, "watersheds", None)                  # the place's main watershed and county, for a line limited to a basin or to counties
            huc, cty = (sheds[0].huc12 if sheds else None), getattr(s.place, "county_fips", None)
            from waterledger import rules as _rules
            ar = _rules.place_areas(getattr(s.place, "state", ""), getattr(s.place, "geoid", None))
            out["withdrawal"], out["withdrawal_line"] = withdrawal(q, W, basin, "ground", huc=huc, county=cty, areas=ar)
            out["withdrawal_period"] = "highest_month" if q["withdrawn_month"] is not None else "peak_day"     # the rules' own periods where the data has the month
            out["withdrawal_line_peak_day"] = withdrawal(q, W, basin, "ground", peak=True, huc=huc, county=cty, areas=ar)[1]
            used = {g for x in _lines(W) for g in x.get("areas", [])}            # only the areas a line names
            ar = {g: v for g, v in ar.items() if g in used}
            if any(v["status"] == "part" for v in ar.values()):
                # the place is partly inside an area a line names: the rule outside it too, and the areas, so a reader sees both
                lo = withdrawal(q, W, basin, "ground", huc=huc, county=cty, areas=ar, inside=False)
                if lo[1] != out["withdrawal_line"]:
                    out["withdrawal_outside"], out["withdrawal_line_outside"] = lo
                    out["withdrawal_areas"] = sorted({n for v in ar.values() if v["status"] == "part" for n in v["names"]})
            flag, flag_peak = permit_flag(out["withdrawal_line"], W), permit_flag(out["withdrawal_line_peak_day"], W)
            out["withdrawal_flag"], out["withdrawal_flag_peak_day"] = flag, flag_peak
            if flag or flag_peak:
                out["withdrawal_flag_note"] = flag_note(flag or flag_peak, W)
        else:
            out["withdrawal_note"] = (W or {}).get("no_line") if ref.get("state_rules", False) and (W or {}).get("no_line") else NOT_REVIEWED_NOTE
    if W and (ctx.receiving.great_lake or ctx.receiving.great_lakes_basin):
        # The Compact covers the basin, not the shore (Akron is in it, Columbus is not). Its period is 90 days. Data from before model 1.7 has only the average
        on_90 = w.consumed_max_90day is not None
        out["great_lakes"] = compact(compact_share(w.consumed_max_90day.p50 if on_90 else w.consumed.avg.p50, W))
        out["great_lakes_period"] = "highest_90_days" if on_90 else "average"
        out["great_lakes_where"] = "shore" if ctx.receiving.great_lake else "basin"
    return out
