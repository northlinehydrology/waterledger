"""Data centers on the facility contract (design 0010, step 3). Their numbers are the state providers' and the stored results', as before the
contract: `results` asks the place's provider, as Site.estimate did. Splitting the providers to the place side waits for design 0011 (Andrew, Nov 12,
2026: battery plants now, the provider split with Michigan's move onto the base path)."""
from typing import Literal

from pydantic import Field

from waterledger.facilities.base import Facility, register

COOLING = Literal["dry", "assist", "hybrid", "towers", "lake"]


def local_weather(est):
    """The estimate with its water and electricity from the model run at the place's own point on Open-Meteo's best match, the way a state's builder runs a region."""
    from waterledger import scenario
    from waterledger.estimate import electricity, water_use
    from waterledger_data.climate import hourly_weather
    from waterledger_models.datacenter import cooling
    p, f = est.site.place, est.site.facility
    if f.cooling == "lake":
        raise ValueError("Lake-source cooling does not depend on air weather; weather='local' does not apply")
    t, T, RH = hourly_weather(p.lat, p.lon, "1995-01-01", "2024-12-31", f"place_{p.geoid}")
    D = {"regions": {"local": {"per_100mw": cooling.run_location(t, T, RH, mw=100.0, plant=f.plant)}}, "staff": {"runs": cooling.staff_runs()}}
    return est.model_copy(update={"water": water_use(scenario.cooling_estimate(D, "local", f.cooling, f.it_mw, est.site.wastewater)),
                                  "electricity": electricity(scenario.electricity(D, "local", f.cooling, f.it_mw)), "weather": "local"})


@register
class DataCenter(Facility):
    """A data center campus: computing capacity and cooling design.

    cooling: dry (closed loop, no water for cooling), assist (dry coolers with adiabatic pre-cooling in warm weather),
    hybrid (dry most of the year, evaporative in warm weather), towers (cooling towers all year) or lake (lake-source,
    once through; only within about 5 km of a Great Lake). plant: the cooling plant inside the building, which sets the loops' water
    temperatures (model 1.10): shared (one facility water loop for air and liquid cooling, the default), warm (a separate warm-water
    loop for liquid-cooled computers) or chilled (a conventional chilled-water plant); data from before model 1.10 has only its own."""
    kind: Literal["data_center"] = "data_center"
    it_mw: float = Field(gt=0, le=10000, description="IT (computing) capacity at buildout, MW")
    cooling: COOLING = Field("dry", description="cooling design")
    plant: Literal["shared", "warm", "chilled"] = Field("shared", description="the cooling plant inside the building (model 1.10): one facility water loop for "
                                                                                 "air and liquid cooling (shared, the default), a separate warm-water loop for "
                                                                                 "liquid cooling (warm), or a conventional chilled-water plant (chilled)")

    DESIGNS = ("dry", "assist", "hybrid", "towers", "lake")
    EVAPORATIVE = ("towers", "hybrid")
    DESIGN_FIELD = "cooling"

    @property
    def size(self):
        return (self.it_mw, "MW of IT capacity")

    def results(self, site, weather="region"):
        """The state's provider's estimate (its stored results for the place, the page's rules), or with weather="local" the model run at the place."""
        from waterledger import states
        est = states.provider(site.place.state).estimate(site)
        return local_weather(est) if weather == "local" else est

    def bmi_config(self, forcing=None, end_time=None, design_db=None):
        if self.cooling == "lake":
            entry = "waterledger_models.datacenter.bmi:LakeCoolingBmi"
            cfg = {"it_capacity_mw": self.it_mw, "end_time": end_time or 365 * 86400}
        else:
            entry = "waterledger_models.datacenter.bmi:CoolingWaterBmi"
            cfg = {"design": self.cooling, "plant": self.plant, "it_capacity_mw": self.it_mw, "time_step": 3600, "end_time": end_time or 365 * 86400}
        if forcing:
            cfg["forcing"] = str(forcing)
        if design_db is not None and self.cooling != "lake":
            cfg["parameters"] = {"design_db": float(design_db)}
        return entry, cfg

    def backup_generator_mw(self):
        """Backup generators at the ratio to IT capacity runoff.fuel uses."""
        from waterledger_models.runoff import PARAMS
        return self.it_mw * PARAMS["fuel"]["gen_mw_per_it_mw"]

    def cooling_blowdown(self, est):
        """Towers: what goes back is nearly all blowdown, so the returned water on the middle estimate."""
        return est.water.returned.avg.p50 if self.cooling == "towers" else None
