"""Facilities: what is proposed. A data center now; other large water users (battery plants, chip fabs, food processing,
hydrogen) later, each as its own type with the same shape, so Site and Estimate don't change when one is added."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

COOLING = Literal["dry", "assist", "hybrid", "towers", "lake"]


class Facility(BaseModel):
    """A proposed large water user. Subclasses set `kind` and their own inputs."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: str


class DataCenter(Facility):
    """A data center campus: computing capacity and cooling design.

    cooling: dry (closed loop, no water for cooling), assist (dry coolers with adiabatic pre-cooling in warm weather),
    hybrid (dry most of the year, evaporative in warm weather), towers (cooling towers all year) or lake (lake-source,
    once through; only within about 5 km of a Great Lake)."""
    kind: Literal["data_center"] = "data_center"
    it_mw: float = Field(gt=0, le=10000, description="IT (computing) capacity at buildout, MW")
    cooling: COOLING = Field("dry", description="cooling design")
