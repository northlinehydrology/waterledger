"""Site: a facility at a place, with its choices: where its water comes from, where its wastewater goes, and the land it
covers. Choices left as None take the defaults waterledger.org starts with for that place and design."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from waterledger import comparisons, levels, scenario, states
from waterledger.estimate import Estimate
from waterledger.facilities import AnyFacility
from waterledger.facilities.data_center import local_weather  # noqa: F401  its old home
from waterledger.place import Place


POWER_ALIASES = {"mi_mix": "state_mix"}     # Michigan's name for the state's own mix before 3.9.0; it still works


class _PowerPlants(dict):
    """est.power_plants: {option: water at power plants}, which also answers to an option's old name."""

    def __missing__(self, key):
        if key in POWER_ALIASES:
            return self[POWER_ALIASES[key]]
        raise KeyError(key)

    def __contains__(self, key):
        return super().__contains__(POWER_ALIASES.get(key, key))

    def get(self, key, default=None):
        return super().get(POWER_ALIASES.get(key, key), default)


class Site(BaseModel):
    """A proposed facility at a place. Estimate it with site.estimate()."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    place: Place
    facility: AnyFacility
    source: Literal["muni", "wells", "lake"] | None = Field(None, description="public water system, new wells, or lake surface water")
    wastewater: Literal["sewer", "septic", "water", "reuse"] | None = Field(None, description="public sewer, septic, its own discharge, or reuse on site")
    acres: float | None = Field(None, gt=0, description="land developed, acres")
    land_before: Literal["farm", "woods", "built"] | None = None
    impervious: float = Field(0.5, ge=0, le=1, description="share of the developed land under roofs and paving")
    power: str | None = Field(None, description="what supplies the electricity, one of the state's options in est.power_plants; None: the state's own mix")

    def estimate(self, weather="region", supply=None, supply_draws=400, storm_years=None) -> Estimate:
        """Water taken, evaporated or lost, and returned, as the state's provider computes it (same numbers as waterledger.org). weather="local" runs the
        model at the place instead of using its region's stored results: Open-Meteo's best match (ERA5, ERA5-Land and, from 2017, IFS HRES), the grid point nearest the place, an 8 MB download once and about 30 seconds
        each run. It is not measured on-site weather. Outside Michigan the stored results use NOAA stations, so
        "local" also changes the kind of weather data, and the brief reports stations giving hybrid and assist estimates 4-50% higher. Not for lake-source cooling.

        supply: {name: waterledger_models.supply.scenario.Scenario}, power supply scenarios at the place (design 0014), in est.supply: run at the
        place's ERA5 cell with `supply_draws` draws, a few seconds to a minute (the cell's radiation and wind are fetched once, about 30 seconds).
        storm_years: a design storm (NOAA Atlas 14 return period, years) for PV's runoff before and after."""
        if weather not in ("region", "local"):
            raise ValueError(f"weather must be 'region' or 'local', not {weather!r}")
        est = self.facility.results(self, weather)
        ref = states.provider(self.place.state).reference(self.place)
        power = POWER_ALIASES.get(self.power, self.power) or ref["power"]
        if power not in ref["power_options"]:
            raise ValueError(f"power must be one of {sorted(ref['power_options'])}, not {power!r}")
        est = est.model_copy(update={"site": est.site.model_copy(update={"power": power}), "comparisons": comparisons.comparisons(est, ref), "equivalents": comparisons.equivalents(est, ref), "before_after": comparisons.site_before_after(est, ref), "site_loads": comparisons.site_runoff_loads(est, ref), "household_wells": comparisons.wells_summary(self.place.context().supply.household_wells),
                                      "power_plants": _PowerPlants(comparisons.plant_waters(est.electricity, ref["power_options"])) if est.electricity else {}, "not_covered": ref.get("not_covered", {})})
        est = est.model_copy(update={"levels": levels.site_levels(est, ref)})
        if supply:
            from waterledger.supply import estimate_supply
            est = est.model_copy(update={"supply": estimate_supply(est, supply, n=supply_draws, storm_years=storm_years)})
        return est

    def by_design(self, designs=("dry", "hybrid", "towers")):
        """The same facility with each design, on this site's power option: water evaporated at the site and at power plants, electricity, and which evaporates least."""
        ref = states.provider(self.place.state).reference(self.place)
        power = POWER_ALIASES.get(self.power, self.power) or ref["power"]
        results = {}
        for k in designs:
            e = self.model_copy(update={"facility": self.facility.with_design(k)}).estimate()
            results[k] = (e.water, e.electricity)
        return comparisons.compare_designs(results, ref["power_options"], power, ref["power"])

    def to_bmi_config(self, path=None, forcing=None, end_time=None, design_db=None, parameters=None):
        """The BMI component that runs this site step by step, and its configuration: (entry point, config dict). With `path`,
        the config is also written there as YAML. `forcing` is an optional weather file (Open-Meteo JSON for the hourly
        cooling component, a daily lake-temperature CSV for the lake-source one); without it, inputs come through set_value, and a hybrid
        needs `design_db`, the location's 0.4% design dry-bulb in C, which a forcing file otherwise supplies
        (waterledger_models.weather.design_dry_bulb computes it from the place's hourly record). `parameters` adds to the component's parameters:
        a battery cell plant without a forcing file needs its design enthalpy, {"design_h": ...} (waterledger_models.battery.physics.for_location).

            entry, cfg = site.to_bmi_config("site.yaml")
            m = CoolingWaterBmi(); m.initialize(cfg)      # or m.initialize("site.yaml")
        """
        entry, cfg = self.facility.bmi_config(forcing=forcing, end_time=end_time, design_db=design_db)
        if parameters:
            cfg["parameters"] = {**cfg.get("parameters", {}), **{k: float(v) for k, v in parameters.items()}}
        if path:
            import yaml
            with open(path, "w") as fh:
                yaml.safe_dump(cfg, fh, sort_keys=False)
        return entry, cfg
