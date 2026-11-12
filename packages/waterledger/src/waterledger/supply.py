"""Power supply scenarios at a place (design 0014, step 6): est.supply, what serves the campus's hourly electricity there and the water it takes,
as bands at the site's size.

Supply needs the campus's own hours, so it runs at the place every time and is not stored (decision 9). The place's ERA5 cell gives the weather
(the cell the snapshots' runs use, corrected toward stations as they are: national.era5.weather) and the radiation and 100 m wind for PV and
wind (waterledger_data.era5.supply); the campus's Monte Carlo runs there through the shared runner with the scenarios as its extra
(waterledger_models.supply.scenario); the residual's grid water uses the place's balancing authority, fit on the cell's own hours as the cell
runs fit it (national.era5.grid_factors); renewables' land and runoff use the place's rain and the site's land before.

Supply reads only the facility's hourly electricity, so it is the same for every water user type; it waits on design 0010's facility contract
only for types other than data centers. Lake-source cooling has no air weather to run, as with weather="local".
"""
from waterledger.estimate import GridWater, Range, SupplyScenarioEstimate

DRAWS = 400


def _r(res, key):
    v = res.get(key)
    return Range(p10=v["p10"], p50=v["p50"], p90=v["p90"]) if v else None


LOW_WIND_NOTE = ("This place's ERA5 cell averages {ms:.1f} m/s at 100 m, under {low} m/s. Checked against EIA's 2024 fleet, wind plants on cells "
                 "this calm delivered 1.5 times the model or more: they sit on ridges and passes the 0.25-degree cell smooths out. The wind "
                 "figures here are likely low by an unknown amount; a site's own wind measurements would settle it.")


def place_weather(place):
    """(cell id, times, temp_c, rh_pct, supply weather, correction note) at the place's ERA5 cell: the snapshots' cell and correction."""
    from waterledger.national import era5 as E
    from waterledger_data import era5
    c = era5.cell(place.lat, place.lon)
    cid = c["id"]
    era5.fetch([cid])
    era5.fetch_supply([cid])
    stations = E.anchors({cid: {"cell": {k: c[k] for k in ("id", "lat", "lon", "land")}}})
    times, t, rh, note = E.weather(cid, stations)
    st, utc, ghi, beam, u, v = era5.supply(cid)
    if list(st) != list(times):
        raise ValueError(f"ERA5 cell {cid}: the supply hours don't match the weather's")
    return cid, times, t, rh, (utc, ghi, beam, u, v), note


def estimate_supply(est, scenarios, n=DRAWS, seed=7, storm_years=None):
    """{name: SupplyScenarioEstimate} for an estimate's site and the scenarios ({name: supply.scenario.Scenario}, sized here). storm_years: a
    design storm's return period (NOAA Atlas 14, the place's context) for PV runoff before and after; None leaves the storm out."""
    from waterledger.national import era5 as E
    from waterledger_models import runs
    from waterledger_models.datacenter import cooling
    from waterledger_models.supply import land, scenario as S
    site, f = est.site, est.site.facility
    if f.kind != "data_center":
        raise NotImplementedError("supply scenarios at a place run for data centers until design 0010's facility contract")
    if f.cooling == "lake":
        raise ValueError("Lake-source cooling does not depend on air weather; supply scenarios at a place need it")
    cid, times, t, rh, wx, note = place_weather(site.place)
    from waterledger.national.provider import place_ba
    ba = est.grid_water.balancing_authority if est.grid_water else place_ba(site.place.context())    # a cell run before 3.18.0 may lack it
    grid = E.grid_factors(cid, times, t, [ba]) if ba else {}
    model = lambda: cooling._CoolingRuns(n, seed, f.it_mw, cooling.HOUR_BLOCK, f.plant, True)
    lat, lon = site.place.lat, site.place.lon
    sized = S.size(model(), times, t, rh, scenarios, f.cooling, wx, lat, lon)
    res = runs.run_location(model(), times, t, rh, designs=(f.cooling,), grid=grid or None, extra=S.Supply(sized, wx, lat, lon, n))[f.cooling]
    ctx = site.place.context()
    rain = ctx.climate.rain_in if ctx.climate else None
    storm = ctx.climate.design_storms_in.get(str(storm_years)) if (storm_years and ctx.climate) else None
    from waterledger_models.supply import wind as W
    wind_ms, calm = W.low_wind(wx[3], wx[4])
    out = {}
    for name, sc in sized.items():
        pre = f"supply_{name}_"
        R = lambda k: _r(res, pre + k)
        flow = lambda role: {"avg": R(f"gas_{role}_avg"), "peak_day": R(f"gas_{role}_peak_1in10")} if R(f"gas_{role}_avg") else None
        g = None
        if ba and R(f"grid_{ba}_consumed_avg"):
            g = GridWater(balancing_authority=ba, consumed=R(f"grid_{ba}_consumed_avg"), withdrawn=R(f"grid_{ba}_withdrawn_avg"),
                          consumed_peak_day=R(f"grid_{ba}_consumed_peak_1in10"), withdrawn_peak_day=R(f"grid_{ba}_withdrawn_peak_1in10"),
                          marginal_consumed=R(f"grid_{ba}_marginal_consumed_avg"), marginal_withdrawn=R(f"grid_{ba}_marginal_withdrawn_avg"),
                          marginal_consumed_peak_day=R(f"grid_{ba}_marginal_consumed_peak_1in10"),
                          marginal_withdrawn_peak_day=R(f"grid_{ba}_marginal_withdrawn_peak_1in10"))
        foot = land.footprint(sc, rain, storm, site.land_before or "farm", site.place.state) if rain and (sc.pv_mw or sc.wind_mw) else {}
        out[name] = SupplyScenarioEstimate(
            residual=sc.residual, pv_mw=sc.pv_mw, wind_mw=sc.wind_mw, gas=dict(vars(sc.gas)) if sc.gas else None,
            share_pv=R("share_pv"), share_wind=R("share_wind"), share_gas=R("share_gas"), share_grid=R("share_grid"),
            annual_matching=R("annual_matching"), unserved_hours_annual=R("unserved_hours_annual"), unserved_mwh_annual=R("unserved_mwh_annual"),
            unserved_run_max_hours=R("unserved_run_max_hours"), surplus_mwh_annual=R("surplus_mwh_annual"), pv_cf=R("pv_cf") if sc.pv_mw else None, wind_cf=R("wind_cf") if sc.wind_mw else None,
            local_withdrawn=R("local_withdrawn_avg"), local_consumed=R("local_consumed_avg"),
            gas_withdrawn=flow("withdrawn"), gas_consumed=flow("consumed"),
            gas_returned={k: R(f"gas_{k}_avg") for k in ("to_sewer", "to_source", "to_stream")} if sc.gas else None,
            grid_water=g, land=_plain(foot), weather={"cell": cid, "correction": bool(note.get("applied")), "draws": n, "wind_100m_mean_ms": round(wind_ms, 2)},
            notes=[LOW_WIND_NOTE.format(ms=wind_ms, low=W.LOW_WIND_MS)] if (sc.wind_mw and calm) else [])
    return out


def _plain(x):
    """Footprint values as plain floats and lists, for a JSON-safe estimate."""
    import numpy as np
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return float(x) if isinstance(x, (np.floating, float)) else x
