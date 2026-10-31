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


class CountyWaterUse(BaseModel):
    """Water already used in the place's county, by category, from one source, with that source's basis. Categories are
    public_supply, domestic, commercial, industrial, irrigation, golf, livestock, aquaculture, mining, thermoelectric, other
    and total; a category the source has no value for is absent, not zero."""
    model_config = ConfigDict(frozen=True)
    county: str | None = None
    county_fips: str
    source: str                                     # source id, e.g. "usgs_wu2015", "odnr_wwfr", "twdb_wus", "va_deq_awrr", "egle2025"
    citation: str
    url: str | None = None
    year: int
    kind: str                                       # "reported" (by the users, to the state) or "estimate" (USGS's 2015 estimates)
    measure: str                                    # "withdrawals", or "use" (TWDB: intake less sales; power plants' consumption)
    units: str = "Mgal/d"
    mgd: dict[str, float] = {}
    ground_mgd: dict[str, float] = {}
    surface_mgd: dict[str, float] = {}
    reuse_mgd: dict[str, float] = {}                # Texas
    delivered_to_homes_mgd: float | None = None     # USGS: public supply delivered to homes in the county
    threshold: str | None = None                    # who has to report
    categories: dict[str, str] = {}                 # what each category holds in the source's own terms
    caveats: list[str] = []


class Supply(_Category):
    """Where the water comes from."""
    systems: list[WaterSystem] = []                 # public water systems mapped in the place
    nearest_system: WaterSystem | None = None       # with none mapped: the nearest sizable one
    nearest_system_km: float | None = None
    county_use_mgd: dict[str, float] = {}           # water used in the county by category, million gallons a day (as county_water_use.mgd;
                                                    # Michigan: EGLE's reported withdrawals under its own labels)
    county_water_use: CountyWaterUse | None = None  # the state's own county figures where Water Ledger has them, else USGS's 2015 estimates
    county_water_use_usgs: CountyWaterUse | None = None   # USGS's 2015 estimates (withdrawals and deliveries to homes), for comparison
    household_wells: dict | None = None             # wells in glacial deposits and bedrock: count, depth, water level (ft)


class SewerPlant(BaseModel):
    npdes: str
    name: str
    design_mgd: float | None = None
    flow_mgd: float | None = None
    km: float
    receiving_water: str | None = None
    own: bool = False               # the place's own plant (wastewater.is_own)
    combined_sewer: bool = False
    lagoon: bool = False


class Wastewater(_Category):
    """Where used water goes."""
    plants: list[SewerPlant] = []                   # the place's own first if it has one (wastewater.is_own), then nearest first


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
    share_of_place: float                           # national tier: the territory's overlap ("may serve"; HIFLD often draws counties)
    customers: int | None = None
    avg_mw: float | None = None
    summer_peak_mw: float | None = None
    balancing_authority: str | None = None          # EIA-930 code, e.g. "PJM"
    power_plant_water_l_per_kwh: float | None = None    # grid region's water consumed at power plants, 2022, excluding hydropower (Siddik et al.)


class PowerPlantWater(BaseModel):
    """Water at power plants per kWh used in the state, 2024, from plant-reported data (model 1.3; docs/methods/power_water)."""
    consumed_l_per_kwh: float
    consumed_range: tuple[float, float]
    withdrawn_l_per_kwh: float
    withdrawn_range: tuple[float, float]
    main_balancing_authority: str | None = None
    import_share: float | None = None              # net interstate imports / in-state use; their water at the main BA's rate
    year: int = 2024


class Energy(_Category):
    """The power behind a facility."""
    utilities: list[Utility] = []
    power_plant_water: PowerPlantWater | None = None    # the state's own figure; utilities carry their grid region's 2022 value


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
