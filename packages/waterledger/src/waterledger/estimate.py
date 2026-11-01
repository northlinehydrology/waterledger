"""Estimates: what the model says a site would take, use up and send back, as ranges (p10, p50, p90 of the Monte Carlo)."""
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from waterledger.site import Site


class Range(BaseModel):
    """The range across assumptions: p10 and p90 bracket 80% of the Monte Carlo runs across the parameter ranges, which are not a probability that the real value falls inside; p50 is the middle estimate. Full values, not rounded for display."""
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
    """Water a site takes (withdrawn), evaporates or loses (consumed: evaporation, drift, top-ups, humidifiers, staff use) and sends out as wastewater (returned).
    On the middle estimate withdrawn + condensate = consumed + returned; condensate comes out of the outside air, not a water system. Flows in million gallons a day; annual in million gallons."""
    model_config = ConfigDict(frozen=True)
    withdrawn: Flow
    withdrawn_annual_mg: Range
    consumed: Flow
    returned: Flow
    to_sewer: Range                      # to the wastewater destination; with a septic system, without the condensate, which is assumed to go to a site drain or stormwater [A]
    lake_source: bool = False
    reuse: bool = False
    withdrawn_peak_full_capacity: Range | None = None   # the upper case: the peak day with every computer at capacity all day; peak_day is at average utilization
    condensate: Flow | None = None       # also in returned and to_sewer; none for lake-source's lake water or data from before model 1.5
    withdrawn_max_month: Range | None = None    # the highest month's average day: the period of Part 327's 30-day test. Lake-source: constant, as the withdrawal
    consumed_max_90day: Range | None = None     # the highest 90 straight days' average: the Compact's period. None for data from before model 1.7. Lake-source: its highest month, which is no lower


def water_use(E):
    """WaterUse from the lo/mid/hi form waterledger.scenario gives."""
    R = Range.from_band
    return WaterUse(withdrawn=Flow(avg=R(E["wAvg"]), peak_day=R(E["wPeak"])), withdrawn_annual_mg=R(E["wAnn"]),
                    consumed=Flow(avg=R(E["cAvg"]), peak_day=R(E["cPeak"])), returned=Flow(avg=R(E["rAvg"]), peak_day=R(E["rPeak"])),
                    to_sewer=R(E["sewer"]), lake_source=E["lake"], reuse=E["reuse"],
                    condensate=Flow(avg=R(E["condAvg"]), peak_day=R(E["condPeak"])) if "condAvg" in E else None,
                    withdrawn_peak_full_capacity=R(E["wPeakFull"]) if "wPeakFull" in E else None,
                    withdrawn_max_month=R(E["wMonth"]) if "wMonth" in E else None, consumed_max_90day=R(E["c90"]) if "c90" in E else None)


def electricity(e):
    """Electricity from waterledger.scenario.electricity's form; None for data from before model 1.4."""
    R = Range.from_band
    return Electricity(avg_mw=R(e["mw"]), peak_mw=R(e["peak_mw"]), pue=R(e["pue"]), peak_pue=R(e["peak_pue"])) if e else None


class Electricity(BaseModel):
    """A site's electricity, from the hourly heat balance at its weather (model 1.4). avg_mw: computers at their average utilization, plus cooling
    and losses. peak_mw: the 1-in-10-year hottest hour with every computer at capacity. pue and peak_pue: facility power over IT power."""
    model_config = ConfigDict(frozen=True)
    avg_mw: Range
    peak_mw: Range
    pue: Range
    peak_pue: Range


class Percent(BaseModel):
    """A percent on an average day and on a 1-in-10-year peak day, each a range like the water it comes from."""
    model_config = ConfigDict(frozen=True)
    avg: Range
    peak_day: Range | None = None


class Comparison(BaseModel):
    """An estimate against something already there. `measure` and `basis` say what it compares, because a percent of connections is not a
    percent of water use."""
    model_config = ConfigDict(frozen=True)
    against: str
    name: str
    measure: str
    existing: float
    unit: str
    percent: Percent
    basis: str


class Equivalents(BaseModel):
    """An estimate in things people know. Homes at `home_gpd`, the state's own water for a home (USGS 2015 over ACS 2015 households); golf courses at the state's typical course; electricity homes at the state's
    average residential use. `homes` and `golf_courses` count water taken on an average day, or for lake-source cooling what the lake loses.
    `evaporated_share` is the percent of the water taken that evaporates, from the middle estimates. None where a state's data doesn't have the value.
    Full values: waterledger.org works these out from the rounded water it shows, so its figures can differ by that rounding."""
    model_config = ConfigDict(frozen=True)
    homes: Range
    homes_peak_day: Range
    home_gpd: float | None = None
    golf_courses: Range | None = None
    golf_course_gpd: float | None = None
    evaporated_share: float
    electricity_homes: Range | None = None
    electricity_homes_peak: Range | None = None
    share_of_home_customers: Range | None = None


class BeforeAfterRow(BaseModel):
    """One row of what changes at a place with the campus: today, after (with its range across assumptions where there is one) and the percent added to today's
    figure where that means something. `unit` says what the numbers are; a row with no `today` is new to the place."""
    model_config = ConfigDict(frozen=True)
    key: str
    today: float | None = None
    after: float
    after_low: float | None = None
    after_high: float | None = None
    today_low: float | None = None
    today_high: float | None = None
    percent: float | None = None
    controls: str | None = None     # for a load: "typical_wet_pond" or "none"
    unit: str


class PlantWater(BaseModel):
    """Water at power plants for a site's average electricity under one power option, MGD: what they evaporate, what they withdraw, and what they
    return on the middle estimates. Withdrawn water is mostly returned, warmer, to lakes and rivers, so it is never added to a site's own water."""
    model_config = ConfigDict(frozen=True)
    option: str
    label: str
    consumed: Range
    withdrawn: Range
    returned: float
    withdrawn_fresh: float | None = None    # of withdrawn's middle estimate, where the option's plants are known: fresh and saline (with brackish) add to it
    withdrawn_saline: float | None = None
    sources: list[str] = []


class DesignTotal(BaseModel):
    """One cooling design at a site: water evaporated at the campus and at power plants, MGD, and its electricity, MW."""
    model_config = ConfigDict(frozen=True)
    design: str
    evaporated: Range
    at_power_plants: Range
    avg_mw: Range
    peak_mw: Range

    @property
    def total(self):
        """Evaporated at the campus and at power plants, middle estimates."""
        return self.evaporated.p50 + self.at_power_plants.p50


class DesignComparison(BaseModel):
    """The same campus with each cooling design, on one power option. `best` evaporates least in total. `thirstiest_power` is the option other than wind and solar and the state's
    starting mix that uses the most water. The closed_loop figures compare closed loop with cooling towers; None unless both designs are among them."""
    model_config = ConfigDict(frozen=True)
    power: str
    designs: dict[str, DesignTotal]
    best: str
    thirstiest_power: str | None = None
    closed_loop_more_power_pct: float | None = None
    closed_loop_more_peak_mw: float | None = None
    closed_loop_saves_on_site: float | None = None


class WellsSummary(BaseModel):
    """Household wells on record for a place, by the aquifer most draw from: `main` is "drift" (glacial deposits) or "rock" (bedrock). Depth and water level (ft) are that aquifer's
    averages. `other_share` is the percent drawing from the other."""
    model_config = ConfigDict(frozen=True)
    wells: int
    main: str
    depth_ft: float
    water_level_ft: float | None = None
    other_share: float


class Estimate(BaseModel):
    """What the model says about a site: its water use and electricity (none where the data predate model 1.4), with every choice resolved
    (defaults filled in), the model version that produced it and the date of the data behind it."""
    model_config = ConfigDict(frozen=True)
    site: "Site"
    water: WaterUse
    electricity: Electricity | None = None
    comparisons: list[Comparison] = []
    equivalents: Equivalents | None = None
    before_after: list[BeforeAfterRow] = []
    household_wells: WellsSummary | None = None
    levels: dict[str, Any] = {}    # what a reader sees, by card (waterledger.levels): words, numbers and flags. Never changes an estimate
    not_covered: dict[str, str] = {}   # what isn't covered yet for this state, in words: labeled, not silently empty
    power_plants: dict[str, PlantWater] = {}    # every power option for the state; site.power says which one the site uses
    weather: str = "region"     # "region": the stored results for the place's weather region or division; "local": the model run at the place (ERA5)
    model_version: str
    data_date: str
