"""Validation rows: a state's own published or reported figures beside the model's estimate for the same case (design 0011, decision 9), so
any state can carry them. Each state's rows are a function of the cooling results by ERA5 cell, the staff-water draws and a lookup from a
place (name, county) to its cell, so the "ours" column is worked out from the same numbers the state's pages show. The methods page shows
them (estimates.json `validation`). Michigan's are the first; a state with none returns [].

    validation.rows("MI", cells, staff, cell_of)      # cells: {cell id: record}; staff: staff_runs; cell_of(name, county) -> cell id
"""
import math

from waterledger.comparisons import it_mw_from_contract


def michigan(cells, staff, named):
    """Michigan's rows: LBNL, Lei, ICPRB and Google figures, and the Van Buren, Lowell, Gaines, Saline and Switch figures reported locally."""
    from waterledger.scenario import band, flow, pue_by_design
    from waterledger_models.datacenter import cooling as cw
    Dv = {"regions": cells, "staff": {"runs": staff}}
    west, van_buren, saline = named("grand rapids city", "Kent"), named("van buren charter township", "Wayne"), named("saline township", "Washtenaw")
    lowell, gaines = named("lowell charter township", "Kent"), named("gaines charter township", "Kent")
    s2 = lambda v: f"{(round(v) if v < 100 else round(v / 10 ** (math.floor(math.log10(v)) - 1)) * 10 ** (math.floor(math.log10(v)) - 1)):,.0f}"
    gal = lambda b: f"about {s2(b['mid'] * 1e6)} gal/day ({s2(b['lo'] * 1e6)} to {s2(b['hi'] * 1e6)} across our assumptions)"
    util = cells[west]["per_100mw"]["dry"]["utilization"]["p50"]
    w300 = flow(Dv, west, "dry", "withdrawn_avg", 300)
    lkwh = w300["mid"] * 1e6 * 3.78541 / (300 * 1000 * util * 24)
    hyb = lambda key: flow(Dv, west, "hybrid", key, 300)["mid"] * 1e6 / 300
    # Van Buren: 1 GW of DTE contract over three buildings, one open loop; computers = contract / top of each design's PUE range [A]
    pue_design = pue_by_design(cells)
    it_t, it_d = it_mw_from_contract(1000 / 3, pue_design["towers"]["hi"]), it_mw_from_contract(2000 / 3, pue_design["dry"]["hi"])
    st = cw.staff_q(staff, it_t + it_d)
    vb = {k: band(cells[van_buren]["per_100mw"]["towers"][f"withdrawn_{k}"], it_t / 100)["mid"] + band(cells[van_buren]["per_100mw"]["dry"][f"withdrawn_{k}"], it_d / 100)["mid"]
          + st["withdrawn"]["p50"] for k in ("avg", "peak_1in10")}
    saline_it = it_mw_from_contract(1400, pue_design["dry"]["hi"])
    mx = lambda r: f"{r:.1f}".removesuffix(".0") if r < 10 else s2(r)          # a multiple, as on the page (WQ.mult)
    low, gb, sal, sw = (flow(Dv, lowell, "dry", "withdrawn_avg", 300), flow(Dv, gaines, "dry", "withdrawn_avg", 100),
                        flow(Dv, saline, "dry", "withdrawn_avg", saline_it), flow(Dv, gaines, "dry", "withdrawn_avg", 320))
    l500 = flow(Dv, lowell, "dry", "withdrawn_avg", 500)
    inside = lambda v, b: b["lo"] <= v <= b["hi"]
    not_counted = "landscape watering, humidification for designs that cool with outside air, and other site uses this page does not count"
    validation = [
        {"check": "Cooling towers, water use per IT kWh (makeup basis)", "published": "LBNL 2024 large tower-based facilities: median ~2.0–2.2 L/kWh, range ~1.75–2.75 (U.S. climates)",
         "ours": f"{cells[west]['per_100mw']['towers']['wue_makeup_l_per_kwh']['p10']:.2f}–{cells[west]['per_100mw']['towers']['wue_makeup_l_per_kwh']['p90']:.2f} L/kWh (Grand Rapids)",
         "reading": "Below LBNL's median, and mostly below its range: partly a cool climate, and mainly because LBNL evaporates all the heat while this model uses the evaporative ratio USGS uses, which leaves a share of it as sensible heat in the air. A stated departure, argued from the air's heat balance and disclosed fleets, with no metered tower site to settle it.", "sources": ["lbnl2024", "usgs2013"]},
        {"check": "Hybrid / evaporative assist (consumed)", "published": "Lei et al. 2025, climate zone 5A: ~0.1 (efficient) to ~0.7 (inefficient) L/kWh; operators 0.1–0.3",
         "ours": f"{cells[west]['per_100mw']['hybrid']['wue_l_per_kwh']['p10']:.2f}–{cells[west]['per_100mw']['hybrid']['wue_l_per_kwh']['p90']:.2f} L/kWh (Grand Rapids)",
         "reading": "At or just below the efficient end of the published range, as expected in a cold climate.", "sources": ["lei2025", "lbnl2024"]},
        {"check": "Dry (no evaporation), water taken per IT kWh", "published": "~0–0.1 L/kWh for designs that use no water for cooling (staff use, and humidification where outside air is used)",
         "ours": f"About {lkwh:.3f} L/kWh at 300 MW, Grand Rapids, staff water included",
         "reading": "Inside the range, near the bottom: these designs recirculate indoor air, so the humidification behind the top of LBNL's range is not counted. A weak check on its own; the Michigan figures below say more.", "sources": ["lbnl2024"]},
        {"check": "Observed utility data, Northern Virginia (per MW of facility power capacity)", "published": "Air-cooled ~150 gal/day/MW; mixed (~60–70% water-cooled) 800–1,006 average, 2,435–3,060 peak day; evaporative peak up to 8,500",
         "ours": f"Per MW of IT capacity at 300 MW, Grand Rapids: dry ~{w300['mid'] * 1e6 / 300:,.0f}; hybrid ~{hyb('withdrawn_avg'):,.0f} average and ~{hyb('withdrawn_peak_1in10'):,.0f} on a 1-in-10 peak day",
         "reading": f"Dry is far below the metered air-cooled figure: the Virginia sites are older, many cool with outside air, and metered totals include {not_counted}; ICPRB's per-MW basis is facility capacity, not computing capacity. Hybrid is the same order of magnitude as the mixed sites.", "sources": ["icprb2025", "icprb2026"]},
        {"check": "Google data center fleet, 2025", "published": "~0.94 L per kWh of facility electricity (10,523 million gallons over 42.4 TWh, all climates and designs)",
         "ours": "Between our hybrid and cooling-tower estimates, as expected for a mixed global fleet", "reading": "Consistent.", "sources": ["google2026"]},
        {"check": "Van Buren Township (Google; 1 GW DTE contract, three buildings, one open loop)", "published": "Developer estimate 2–3.6 MGD (township FAQ, Jan 2026)",
         "ours": f"About {vb['avg']:.1f} MGD average, {vb['peak_1in10']:.1f} MGD 1-in-10 peak (one building's third of the contract with cooling towers, about {it_t:,.0f} MW of computers; two-thirds closed loop, about {it_d:,.0f} MW; Van Buren's own cell)",
         "reading": "Inside the developer's range." if 2.0 <= vb["avg"] <= 3.6 else "Outside the developer's range.", "sources": []},
        {"check": "Lowell Charter Township (Microsoft), closed loop", "published": "About 6,000 gal/day (2.2 million gallons a year) excluding cooling, a Microsoft projection reported locally; size not published; primary document not yet located",
         "ours": f"{gal(low)} at 300 MW, the starting size; {gal(l500)} at 500 MW",
         "reading": f"The reported figure is about {mx(0.006027 / low['mid'])} times ours at 300 MW, " + ("inside" if inside(0.006027, low) else "outside") + " our range across assumptions there, and " + ("inside" if inside(0.006027, l500) else "outside") + " it at 500 MW. The campus's size is not published, and ours counts staff water and loop top-ups only.", "sources": ["lowell_firstlook"]},
        {"check": "Gaines Township (Microsoft), per building", "published": "About 2,000 gal/day per building (Microsoft, as reported by Sun and News, not re-verified); building size and count not published",
         "ours": f"{gal(gb)} for one 100 MW building",
         "reading": f"The reported figure is about {mx(0.002 / gb['mid'])} times our middle estimate, " + ("inside" if inside(0.002, gb) else "outside") + " our range across assumptions.", "sources": ["gaines_sunnews"]},
        {"check": "Saline Township (Related Digital for Oracle and OpenAI; 1.4 GW DTE contract), closed loop", "published": "About 20,000 gal/day at the start of operations, a developer estimate as reported locally; primary document not yet located",
         "ours": f"{gal(sal)} at full build-out, about {saline_it:,.0f} MW of computers",
         "reading": f"The reported figure is about {mx(0.02 / sal['mid'])} times ours and " + ("inside" if inside(0.02, sal) else "above") + " our range across assumptions, although it is for the start of operations and ours is for the full campus. It may include uses this page does not count, such as landscape watering, process water or a phased first fill; the primary document has not been found.", "sources": ["saline_post"]},
        {"check": "Switch data center, Gaines Township (operating since 2017; metered, not projected)", "published": "About 10 million gallons in 2024, about 27,000 gal/day, as a township official reported; design 320 MW; actual load and cooling design not public",
         "ours": f"{gal(sw)} for a closed loop at 320 MW and 50–80% load",
         "reading": f"Metered use is about {mx(0.0274 / sw['mid'])} times ours. Switch's cooling design and actual load are not public, and a metered total includes {not_counted}. Metered use at an operating site can run well above an applicant's projection.", "sources": ["wgvu_switch"]},
    ]
    return validation


ROWS = {"MI": michigan}


def rows(state, cells, staff, named):
    """The state's validation rows, or [] where it has none yet."""
    fn = ROWS.get(state.upper())
    return fn(cells, staff, named) if fn else []
