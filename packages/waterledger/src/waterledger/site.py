"""Site: a facility at a place, with its choices: where its water comes from, where its wastewater goes, and the land it
covers. Choices left as None take the defaults waterledger.org starts with for that place and design."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from waterledger import comparisons, scenario, states
from waterledger.estimate import Estimate, electricity, water_use
from waterledger.facility import DataCenter
from waterledger.place import Place


def local_weather(est):
    """The estimate with its water and electricity from the model run at the place's own ERA5 grid cell, the way a state's builder runs a region."""
    from waterledger_data.climate import hourly_weather
    from waterledger_models.datacenter import cooling
    p, f = est.site.place, est.site.facility
    if f.cooling == "lake":
        raise ValueError("Lake-source cooling does not depend on air weather; weather='local' does not apply")
    t, T, RH = hourly_weather(p.lat, p.lon, "1995-01-01", "2024-12-31", f"place_{p.geoid}")
    D = {"regions": {"local": {"per_100mw": cooling.run_location(t, T, RH, mw=100.0)}}, "staff": {"runs": cooling.staff_runs()}}
    return est.model_copy(update={"water": water_use(scenario.cooling_estimate(D, "local", f.cooling, f.it_mw, est.site.wastewater)),
                                  "electricity": electricity(scenario.electricity(D, "local", f.cooling, f.it_mw)), "weather": "local"})


class Site(BaseModel):
    """A proposed facility at a place. Estimate it with site.estimate()."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    place: Place
    facility: DataCenter
    source: Literal["muni", "wells", "lake"] | None = Field(None, description="public water system, new wells, or lake surface water")
    wastewater: Literal["sewer", "septic", "water", "reuse"] | None = Field(None, description="public sewer, septic, its own discharge, or reuse on site")
    acres: float | None = Field(None, gt=0, description="land developed, acres")
    land_before: Literal["farm", "woods", "built"] | None = None
    impervious: float = Field(0.5, ge=0, le=1, description="share of the developed land under roofs and paving")
    power: str | None = Field(None, description="what supplies the electricity, one of the state's options in est.power_plants; None: the state's own mix")

    def estimate(self, weather="region") -> Estimate:
        """Water taken, used up and returned, as the state's provider computes it (same numbers as waterledger.org). weather="local" runs the
        model at the place instead of using its region's stored results: ERA5 reanalysis, the grid cell nearest the place, an 8 MB download once and about 30 seconds
        each run. It is not measured on-site weather. Outside Michigan the stored results use NOAA stations, so
        "local" also changes the kind of weather data, and the brief reports stations giving hybrid and assist estimates 4-50% higher. Not for lake-source cooling."""
        if weather not in ("region", "local"):
            raise ValueError(f"weather must be 'region' or 'local', not {weather!r}")
        est = states.provider(self.place.state).estimate(self)
        if weather == "local":
            est = local_weather(est)
        ref = states.provider(self.place.state).reference(self.place)
        power = self.power or ref["power"]
        if power not in ref["power_options"]:
            raise ValueError(f"power must be one of {sorted(ref['power_options'])}, not {power!r}")
        return est.model_copy(update={"site": est.site.model_copy(update={"power": power}), "comparisons": comparisons.comparisons(est, ref), "equivalents": comparisons.equivalents(est, ref), "before_after": comparisons.site_before_after(est, ref), "household_wells": comparisons.wells_summary(self.place.context().supply.household_wells),
                                      "power_plants": comparisons.plant_waters(est.electricity, ref["power_options"]) if est.electricity else {}})

    def by_design(self, designs=("dry", "hybrid", "towers")):
        """The same campus with each cooling design, on this site's power option: water evaporated at the campus and at power plants, electricity, and which evaporates least."""
        ref = states.provider(self.place.state).reference(self.place)
        power = self.power or ref["power"]
        results = {}
        for k in designs:
            e = self.model_copy(update={"facility": self.facility.model_copy(update={"cooling": k})}).estimate()
            results[k] = (e.water, e.electricity)
        return comparisons.compare_designs(results, ref["power_options"], power, ref["power"])

    def to_bmi_config(self, path=None, forcing=None, end_time=None):
        """The BMI component that runs this site step by step, and its configuration: (entry point, config dict). With `path`,
        the config is also written there as YAML. `forcing` is an optional weather file (Open-Meteo JSON for the hourly
        cooling component, a daily lake-temperature CSV for the lake-source one); without it, inputs come through set_value.

            entry, cfg = site.to_bmi_config("site.yaml")
            m = CoolingWaterBmi(); m.initialize("site.yaml")
        """
        f = self.facility
        if f.cooling == "lake":
            entry = "waterledger_models.datacenter.bmi:LakeCoolingBmi"
            cfg = {"it_capacity_mw": f.it_mw, "end_time": end_time or 365 * 86400}
        else:
            entry = "waterledger_models.datacenter.bmi:CoolingWaterBmi"
            cfg = {"design": f.cooling, "it_capacity_mw": f.it_mw, "time_step": 3600, "end_time": end_time or 365 * 86400}
        if forcing:
            cfg["forcing"] = str(forcing)
        if path:
            import yaml
            with open(path, "w") as fh:
                yaml.safe_dump(cfg, fh, sort_keys=False)
        return entry, cfg
