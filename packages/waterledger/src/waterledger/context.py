"""Context: the public water facts around a place, split by the question people ask. Each category is its own object with
its own sources; `provider` says whether its values came from the national tier or a state's own data."""
from pydantic import BaseModel, ConfigDict


class _Category(BaseModel):
    model_config = ConfigDict(frozen=True)
    provider: str                       # "national" or a state code ("MI") whose own data replaced the national layer
    sources: list[str] = []             # source ids, as cited on waterledger.org's methods pages


class Jurisdiction(_Category):
    """Who decides, under what rules."""
    name: str
    kind: str
    county: str | None = None
    state: str
    rules: list[dict] = []              # state and federal rules with citations (per-state rules files, in progress)


class WaterSystem(BaseModel):
    pwsid: str
    name: str
    population: int | None = None
    connections: int | None = None
    share_of_place: float | None = None


class Supply(_Category):
    """Where the water comes from."""
    systems: list[WaterSystem] = []                 # public water systems mapped in the place
    nearest_system: WaterSystem | None = None       # with none mapped: the nearest sizable one
    nearest_system_km: float | None = None
    county_use_mgd: dict[str, float] = {}           # reported withdrawals in the county by use, million gallons a day
    household_wells: dict | None = None             # wells in glacial deposits and bedrock: count, depth, water level (ft)


class SewerPlant(BaseModel):
    npdes: str
    name: str
    design_mgd: float | None = None
    flow_mgd: float | None = None
    km: float
    receiving_water: str | None = None
    combined_sewer: bool = False
    lagoon: bool = False


class Wastewater(_Category):
    """Where used water goes."""
    plants: list[SewerPlant] = []                   # nearest first; the place's own plant first if it has one


class Watershed(BaseModel):
    huc12: str
    name: str
    share_of_place: float | None = None


class Reach(BaseModel):
    huc12: str
    name: str
    impairments: list[str] = []                     # plain-language groups (e.g. "Bacteria (E. coli)")
    tmdl: list[str] = []                            # the groups with a TMDL (cleanup plan) in place
    coldwater_streams: list[str] = []


class Receiving(_Category):
    """What is downstream."""
    watersheds: list[Watershed] = []
    basin: Watershed | None = None                  # the HUC8
    great_lake: str | None = None                   # within about 5 km of a Great Lake
    downstream: list[Reach] = []                    # from the place's main watershed, following the water


class Climate(_Category):
    """The weather behind demand and runoff."""
    region: str
    region_name: str
    station: str
    rain_in: float | None = None                    # county mean annual precipitation, 1991-2020
    design_storms_in: dict[str, float] = {}         # 24-hour depths by return period in years (NOAA Atlas 14)


class Utility(BaseModel):
    name: str
    type: str
    share_of_place: float
    customers: int | None = None
    avg_mw: float | None = None
    summer_peak_mw: float | None = None


class Energy(_Category):
    """The power behind a facility."""
    utilities: list[Utility] = []


class Context(BaseModel):
    """All categories for one place (land is planned). A category is None where the national tier doesn't have it yet for
    that state (climate and energy arrive in design 0002 steps 4 and 5)."""
    model_config = ConfigDict(frozen=True)
    place: "Place"
    jurisdiction: Jurisdiction
    supply: Supply
    wastewater: Wastewater
    receiving: Receiving
    climate: Climate | None = None
    energy: Energy | None = None


from waterledger.place import Place  # noqa: E402

Context.model_rebuild()
