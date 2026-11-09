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
    once through; only within about 5 km of a Great Lake). plant: the cooling plant inside the building, which sets the loops' water
    temperatures (model 1.10): shared (one facility water loop for air and liquid cooling, the default), warm (a separate warm-water
    loop for liquid-cooled computers) or chilled (a conventional chilled-water plant); data from before model 1.10 has only its own."""
    kind: Literal["data_center"] = "data_center"
    it_mw: float = Field(gt=0, le=10000, description="IT (computing) capacity at buildout, MW")
    cooling: COOLING = Field("dry", description="cooling design")
    plant: Literal["shared", "warm", "chilled"] = Field("shared", description="the cooling plant inside the building (model 1.10): one facility water loop for "
                                                                                 "air and liquid cooling (shared, the default), a separate warm-water loop for "
                                                                                 "liquid cooling (warm), or a conventional chilled-water plant (chilled)")
