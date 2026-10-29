"""Site: a facility at a place, with its choices: where its water comes from, where its wastewater goes, and the land it
covers. Choices left as None take the defaults waterledger.org starts with for that place and design."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from waterledger import states
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
        return states.provider(self.place.state).estimate(self)
