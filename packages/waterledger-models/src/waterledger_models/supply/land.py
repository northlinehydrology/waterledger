"""Land, runoff and construction water for hypothetical new solar and wind projects (design 0014, decision 2's note; research note sec. 9; the
defaults agreed by Andrew Nov 10, 2026). By size, so worked once for a scenario's sized project, not per draw; reported apart from annual operating
water (decision 11). The site's runoff and sediment go through the shared waterledger_models.runoff, as for any developed site.

Solar:
  array area        5.5 acres per MW AC with single-axis tracking, 3.6 fixed (LBNL 2019 medians of 4.2 and 2.8 per MW DC at an inverter
                    loading ratio of 1.3 [A]); the fenced area is the array over 0.7 [A], roads, pads and the substation 4% of it [A]
  imperviousness    the array's effective impervious share on vegetated ground by row orientation, 0.10 along the contours, 0.20 diagonal,
                    0.45 across them, and 0.60 on gravel (Mile High Flood District 2023, Tables 4 and 7); roads and pads counted impervious
  ground            curve number 69 under and between the panels on soil group B (TR-55 open space, fair: one soil group up for compaction [A])
  construction      the fenced area disturbed (Maryland's rule), 0.6 of it bare for a year [A], sediment by runoff.construction's yields;
                    dust control water 0.5 acre-feet per MW [A] (0-5.7, the desert Southwest's peak year at the top)
Wind:
  land              34.5 ha per MW in the project, 0.3 ha per MW permanently disturbed (pads, roads), counted impervious, 0.7 ha per MW
                    disturbed for construction (Denholm et al. 2009, NREL/TP-6A2-45834); only the permanent area changes runoff
  construction      the permanent and temporary areas bare for a year [A]; foundation concrete 700 m3 per turbine [A] (386-1,334 sourced)
                    with about 30,000 gallons of mix water [A] (16,000-67,000), turbines of the IEA 3.4 MW reference size
"""
import numpy as np

from waterledger_models import runoff
from waterledger_models.supply import wind as wind_model

ARRAY_ACRES_PER_MW = {"tracking": 5.5, "fixed": 3.6}
FENCED_OVER_ARRAY = 1 / 0.7
ROADS_SHARE = 0.04
ARRAY_IMPERVIOUS = {"contour": 0.10, "diagonal": 0.20, "across": 0.45, "gravel": 0.60}
CN_UNDER_PANELS = 69
BARE_SHARE = 0.6
DUST_AF_PER_MW = 0.5
WIND_HA_PER_MW = {"total": 34.5, "permanent": 0.3, "temporary": 0.7}
FOUNDATION_M3 = 700.0
FOUNDATION_GAL = 30000.0
ACRES_PER_HA = 2.47105
GAL_PER_AF = 325851.0


def pv_site(mw_ac, mount="tracking", rows="contour"):
    """A PV project's areas, acres, and its effective impervious share over the fenced area."""
    if mount not in ARRAY_ACRES_PER_MW:
        raise ValueError(f"mount must be one of {tuple(ARRAY_ACRES_PER_MW)}")
    if rows not in ARRAY_IMPERVIOUS:
        raise ValueError(f"rows must be one of {tuple(ARRAY_IMPERVIOUS)}")
    array = mw_ac * ARRAY_ACRES_PER_MW[mount]
    fenced = array * FENCED_OVER_ARRAY
    roads = ROADS_SHARE * fenced
    imp = (min(array, fenced - roads) * ARRAY_IMPERVIOUS[rows] + roads) / fenced
    return {"array_acres": array, "fenced_acres": fenced, "roads_acres": roads, "impervious_share": imp,
            "disturbed_acres": fenced, "bare_acres": BARE_SHARE * fenced}


def wind_site(mw):
    turbines = int(np.ceil(mw / (wind_model.RATED_KW / 1000.0) - 1e-9))
    ha = {k: v * mw for k, v in WIND_HA_PER_MW.items()}
    return {"turbines": turbines, "total_acres": ha["total"] * ACRES_PER_HA, "permanent_acres": ha["permanent"] * ACRES_PER_HA,
            "temporary_acres": ha["temporary"] * ACRES_PER_HA, "bare_acres": (ha["permanent"] + ha["temporary"]) * ACRES_PER_HA}


def footprint(scenario, rain_in, storm_in=None, before="farm", state=None, rows="contour"):
    """A sized scenario's renewables (supply.scenario.size): {"pv": ..., "wind": ...}, each with its areas, the change in annual runoff and
    sediment on the land it changes (runoff.loads, [lo, mid, hi]: "now" as `before`, "after" built), a storm's runoff before and after where
    storm_in is given (runoff.storm_mg, MG), and one-time construction: sediment from a year of bare ground (runoff.construction, tons, without
    and with basins) and water (gallons). rain_in: the place's annual rain; before: the land as it is ("farm", "woods", ...)."""
    out = {}
    if scenario.pv_mw:
        s = pv_site(scenario.pv_mw, scenario.pv_mount, rows)
        loads = runoff.loads(s["fenced_acres"], rain_in, before, imp=s["impervious_share"], state=state)
        pv = {**s, "runoff_gal": loads["runoff_gal"], "tss_t": loads["tss_t"],
              "construction_sediment_t": runoff.construction(s["bare_acres"]),
              "construction_sediment_with_basins_t": runoff.construction_with_basin(s["bare_acres"]),
              "construction_water_gal": scenario.pv_mw * DUST_AF_PER_MW * GAL_PER_AF}
        if storm_in is not None:
            pv["storm_mg"] = {"before": runoff.storm_mg(s["fenced_acres"], storm_in, imp=0.0, cn_pervious=runoff.hydrology.CN_PRE_PERV),
                              "after": runoff.storm_mg(s["fenced_acres"], storm_in, imp=s["impervious_share"], cn_pervious=CN_UNDER_PANELS)}
        out["pv"] = pv
    if scenario.wind_mw:
        s = wind_site(scenario.wind_mw)
        loads = runoff.loads(s["permanent_acres"], rain_in, before, imp=1.0, state=state)
        out["wind"] = {**s, "runoff_gal": loads["runoff_gal"], "tss_t": loads["tss_t"],
                       "construction_sediment_t": runoff.construction(s["bare_acres"]),
                       "construction_sediment_with_basins_t": runoff.construction_with_basin(s["bare_acres"]),
                       "construction_water_gal": s["turbines"] * FOUNDATION_GAL, "foundation_concrete_m3": s["turbines"] * FOUNDATION_M3}
    return out
