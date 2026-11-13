"""Battery cell plants on the facility contract (design 0010, step 6; the model is design 0009's, waterledger_models.battery). A cell plant has no
stored results, so it is run at the place every time: the place's hourly weather from Open-Meteo's best match (1995-2024, the file a data center's
weather="local" uses, downloaded once), GLERL's lake temperatures for the lake design, and the place's balancing authority's power plant water hour
by hour, as a data center's cell runs take it. About 20 seconds a design after the downloads."""
import datetime
from typing import Literal

from pydantic import Field

from waterledger.facilities.base import Facility, register

DESIGN = Literal["dry", "assist", "hybrid", "towers", "lake"]


def _band(stat, x=1.0):
    return {"lo": stat["p10"] * x, "mid": stat["p50"] * x, "hi": stat["p90"] * x}


def _closed(w, r, c):
    """Consumed on the middle estimate as withdrawn less returned, so the books close (a cell plant has no gain); its range the model's own, widened
    only if that falls outside, as waterledger.scenario.cooling_estimate does for data centers."""
    m = max(0.0, w["mid"] - r["mid"])
    return {"lo": min(c["lo"], m), "mid": m, "hi": max(c["hi"], m)}


def lake_temperatures(lake):
    """GLERL's daily long-term average surface temperatures for a Great Lake, by day of year (366), as the national lake-source results read them
    (fetched once into the cache)."""
    import os

    import pandas as pd

    from waterledger.national.climate import LAKE_TEMPERATURES
    from waterledger_data import climate
    from waterledger_data.config import CACHE
    from waterledger_models import once_through
    T = pd.read_csv(climate._fetch(once_through.GLERL, os.path.join(CACHE, "climate", "glerl_lt_avg_temp.csv")), skiprows=[1])
    return T[T["lake"] == LAKE_TEMPERATURES[lake]].sort_values("dayOfYear")["temperature"].values.astype(float)


def place_weather(place):
    """(times, temperature C, relative humidity %) at the place: Open-Meteo's best match, 1995-2024, local standard time."""
    from waterledger_data.climate import hourly_weather
    return hourly_weather(place.lat, place.lon, "1995-01-01", "2024-12-31", f"place_{place.geoid}")


@register
class BatteryCellPlant(Facility):
    """A battery cell plant (a gigafactory: electrodes, dry rooms, formation), sized in GWh a year of cells, the industry's unit (design 0009).

    design: how the plant rejects its heat, on the equipment shared with data centers: dry (dry coolers and air-cooled chillers), assist (dry
    coolers with adiabatic pads in warm weather), hybrid, towers (wet cooling towers, as at most plants in DOE's environmental assessments, the
    default [A]) or lake (once through; only within about 5 km of a Great Lake). chemistry: "nmc" (nickel cathodes, NMC and NCA) or "lfp".
    utilization: "full" (the plant at its rated output) or "sampled" (output drawn from the model's range). settings: parameters fixed in
    every run, from the plant's own documents (waterledger_models.battery.physics.PARAMETERS)."""
    kind: Literal["battery_cell_plant"] = "battery_cell_plant"
    capacity_gwh: float = Field(gt=0, le=1000, description="cell capacity at buildout, GWh a year")
    design: DESIGN = Field("towers", description="heat rejection design")
    chemistry: Literal["nmc", "lfp"] = Field("nmc", description="cathode chemistry: nmc (NMC and NCA) or lfp")
    utilization: Literal["full", "sampled"] = Field("full", description="full output, or output sampled from the model's range")
    settings: dict[str, float] = Field(default_factory=dict, description="parameters fixed in every run, from the plant's own documents")

    DESIGNS = ("dry", "assist", "hybrid", "towers", "lake")
    EVAPORATIVE = ("towers", "hybrid")

    @property
    def size(self):
        return (self.capacity_gwh, "GWh/yr of cells")

    def results(self, site, weather="region", n=None, seed=7):
        """The model run at the place, whichever `weather` (a cell plant has no stored results by region; the estimate says weather="local").
        Source and wastewater default by the rules every type shares (national.provider.default_source and default_wastewater); with no sewer in
        reach, a cell plant's process and boiler wastewater goes to its own treatment and discharge, never a septic system [A]. Its wastewater
        goes where the site sends it: to the sewer, or with wastewater="water" to a stream under its own permit; the volume is the same."""
        from waterledger import scenario as sc
        from waterledger.estimate import Electricity, Estimate, Range, grid_water, water_use
        from waterledger.national import era5 as E
        from waterledger.national import provider as nat
        from waterledger_models import MODEL_VERSION
        from waterledger_models.battery import plant
        place, d = site.place, self.design
        if site.wastewater in ("septic", "reuse"):
            raise ValueError(f"A battery cell plant's process and boiler wastewater can't go to a {'septic system' if site.wastewater == 'septic' else 'reuse system'}"
                             " in this model: wastewater must be 'sewer' or 'water' (its own discharge)")
        ctx = place.context()
        lake = ctx.receiving.great_lake
        sc.check_lake(place.name, lake, d, site.source)
        times, T, RH = place_weather(place)
        ba = nat.place_ba(ctx)
        grid = E.grid_factors_at(place.lon, times, T, [ba]) if ba and d != "lake" else {}
        r = plant.run_location(times, T, RH, **({"n": n} if n else {}), seed=seed, gwh=self.capacity_gwh, utilization=self.utilization, designs=(d,),
                               settings=dict(self.settings) or None, water_temps=lake_temperatures(lake) if d == "lake" else None,
                               chemistry=self.chemistry, grid=grid or None, discharge="sewer")[d]
        B = lambda k: _band(r[k])
        evap = d in self.EVAPORATIVE
        src = site.source or nat.default_source(ctx, evap)
        dest = site.wastewater or nat.default_wastewater(ctx, evap, lambda: r["to_sewer_avg"]["p50"], far="water")
        w, wp, rr, rp = B("withdrawn_avg"), B("withdrawn_peak_1in10"), B("returned_avg"), B("returned_peak_1in10")
        E_ = {"lake": d == "lake", "reuse": False, "wAvg": w, "wPeak": wp, "wAnn": B("withdrawn_annual_mg"), "rAvg": rr, "rPeak": rp,
              "cAvg": _closed(w, rr, B("consumed_avg")), "cPeak": _closed(wp, rp, B("consumed_peak_1in10")), "sewer": B("to_sewer_avg"),
              "wMonth": B("withdrawn_max_month"), "c90": B("consumed_max_90day"), "wPeakFull": B("withdrawn_peak_full_capacity")}
        water = water_use(E_)
        if d == "lake":
            water = water.model_copy(update={"to_source": Range.from_band(B("to_source_avg"))})
        R = lambda k: Range.from_band(B(k))
        power = Electricity(avg_mw=R("power_mw_avg"), peak_mw=R("power_mw_peak_1in10"), peak_day_mw=R("power_mw_peak_day_1in10"), fuel_mw=R("fuel_mw_avg"))
        kinds = ("consumed", "withdrawn", "marginal_consumed", "marginal_withdrawn")
        g = {k: {"avg": B(f"grid_{ba}_{k}_avg"), "peak_day": B(f"grid_{ba}_{k}_peak_1in10")} for k in kinds} if ba and f"grid_{ba}_consumed_avg" in r else None
        extras = {k: R(k) for k in ("site_kwh_per_kwh", "withdrawn_l_per_kwh", "consumed_l_per_kwh", "blowdown_avg") if k in r}
        acres, before = sc.land_default(place.incorporated)
        resolved = site.model_copy(update={"source": src, "wastewater": dest, "acres": site.acres or acres, "land_before": site.land_before or before})
        return Estimate(site=resolved, water=water, electricity=power, grid_water=grid_water(g, ba), weather="local", extras=extras,
                        model_version=MODEL_VERSION, data_date=datetime.date.today().isoformat())

    def bmi_config(self, forcing=None, end_time=None, design_db=None):
        cfg = {"design": self.design, "capacity_gwh": self.capacity_gwh, "chemistry": self.chemistry, "time_step": 3600, "end_time": end_time or 365 * 86400}
        if forcing:
            cfg["forcing"] = str(forcing)
        params = {**self.settings, **({"design_db": float(design_db)} if design_db is not None and self.design != "lake" else {})}
        if params:
            cfg["parameters"] = params
        return "waterledger_models.battery.bmi:BatteryCellBmi", cfg

    def cooling_blowdown(self, est):
        """Towers: the cooling towers' own blowdown (the model's blowdown_avg), not the process and staff water that go back with it."""
        b = est.extras.get("blowdown_avg")
        return b.p50 if self.design == "towers" and b is not None else None
