"""Site: a facility at a place, with its choices: where its water comes from, where its wastewater goes, and the land it
covers. Choices left as None take the defaults waterledger.org starts with for that place and design."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from waterledger import comparisons, states
from waterledger.estimate import Estimate
from waterledger.facility import DataCenter
from waterledger.place import Place


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

    def estimate(self) -> Estimate:
        """Water taken, used up and returned, as the state's provider computes it (same numbers as waterledger.org)."""
        est = states.provider(self.place.state).estimate(self)
        return est.model_copy(update={"comparisons": comparisons.comparisons(est)})

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
