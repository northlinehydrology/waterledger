"""Estimates: what the model says a site would take, use up and send back, as ranges (p10, p50, p90 of the Monte Carlo)."""
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from waterledger.site import Site


class Range(BaseModel):
    """A likely range: p10 and p90 bracket 80% of the Monte Carlo runs; p50 is the middle estimate."""
    model_config = ConfigDict(frozen=True)
    p10: float
    p50: float
    p90: float

    @classmethod
    def from_band(cls, b):
        """From the lo/mid/hi form the page and waterledger.scenario use."""
        return cls(p10=b["lo"], p50=b["mid"], p90=b["hi"])


class Flow(BaseModel):
    """A water flow, million gallons a day: on an average day and on a 1-in-10-year peak day."""
    model_config = ConfigDict(frozen=True)
    avg: Range
    peak_day: Range


class WaterUse(BaseModel):
    """Water a site takes (withdrawn), uses up (consumed: evaporation, drift, top-ups, staff use) and sends back (returned).
    Withdrawn equals consumed plus returned on the middle estimate. Flows in million gallons a day; annual in million gallons."""
    model_config = ConfigDict(frozen=True)
    withdrawn: Flow
    withdrawn_annual_mg: Range
    consumed: Flow
    returned: Flow
    to_sewer: Range
    lake_source: bool = False
    reuse: bool = False


class Estimate(BaseModel):
    """What the model says about a site: its water use, with every choice resolved (defaults filled in), the model version
    that produced it and the date of the data behind it."""
    model_config = ConfigDict(frozen=True)
    site: "Site"
    water: WaterUse
    model_version: str
    data_date: str
