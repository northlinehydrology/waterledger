"""CSDMS Basic Model Interface (BMI 2.0) for the battery cell plant model (design 0009), so a coupling framework can drive it hour by hour: set
air temperature and humidity (and, for the lake design, the lake's surface temperature), call update(), read the water withdrawn, consumed and
returned, where the return goes, and the plant's electricity and fuel. update() computes the step from the current time to the next from the
inputs set for it; outputs change only on update(), as for the data center components (waterledger_models.datacenter.bmi).

One plant is one scalar grid point. A run uses a single parameter set (the central values by default, any of them overridable in the
configuration file); the Monte Carlo lives in waterledger_models.battery.plant.

Configuration (a YAML file, or the same keys as a dict passed to initialize):
    design: dry | assist | hybrid | towers | lake   (default towers)
    capacity_gwh: 10                            (cell capacity, GWh/yr; sets the plant's energy, its staff and so everything else)
    chemistry: nmc | lfp                        (default nmc, for NMC and NCA; lfp takes the central lfp_factor unless one is set)
    time_step: 3600                             (seconds; the model is hourly)
    end_time: 31536000                          (seconds; default one year)
    humidity: relative | specific               (default relative: which humidity inputs the component reads)
    forcing: path/to/open_meteo.json            (optional; otherwise inputs come from set_value each step; relative humidity)
    parameters: {coc: 3, utilization: 0.8, ...} (optional overrides of the central values: physics.PARAMETERS; utilization defaults to 1.0,
                                                 full output, the headline)
    parameters: {design_db: 31.0, design_h: 70.0}
                                                (the place's 0.4% design dry-bulb, C, and design enthalpy, kJ per kg of dry air, from its whole
                                                 hourly record. A forcing file supplies both; when the framework supplies the weather, compute
                                                 them once with physics.for_location(params, tdb_record, rh_record). design_h sizes the
                                                 outdoor air load in every design; design_db places a hybrid's switch.)

Variables (all on the one scalar grid point, float64):
    input   atmosphere_bottom_air__temperature                         degC     air (dry-bulb) temperature
    input   atmosphere_bottom_air_water_vapor__relative_saturation     percent  relative humidity (humidity: relative)
    input   atmosphere_bottom_air_water_vapor__mass_fraction           kg kg-1  specific humidity (humidity: specific)
    input   land_surface_air__pressure                                 Pa       surface pressure (humidity: specific)
    input   lake_water_surface__temperature                            degC     the lake's surface temperature, standing for the intake's [A]
                                                                                (lake design; not read otherwise)
    input   atmosphere_bottom_air_flow__speed                          m s-1    wind over the lake, for the forced evaporation (lake design;
                                                                                default the middle of the range)
    output  water_user_water__withdrawal_volume_flux                   m3 s-1   cooling make-up or once-through water, process water and staff water
    output  water_user_water__gain_volume_flux                         m3 s-1   always 0: coil condensate is not counted [A] (physics)
    output  water_user_water__consumption_volume_flux                  m3 s-1   evaporation and drift, the lake's forced evaporation, anode slurry
                                                                                water, water shipped off in NMP, boiler steam, the lost share of
                                                                                staff water
    output  water_user_water__return_volume_flux                       m3 s-1   the two returns below together
    output  water_user_water__sewer_return_volume_flux                 m3 s-1   to the sewer: blowdown, the purification's reject, other purified
                                                                                water, boiler blowdown, the rest of staff water
    output  water_user_water__source_return_volume_flux                m3 s-1   to the source: the lake design's once-through water less its forced
                                                                                evaporation; 0 for the other designs
    output  water_user__electric_power                                 MW       the plant's electricity, the cooling plant's included
    output  water_user__fuel_power                                     MW       fuel burned on site: ovens, boilers, heaters
    output  atmosphere_bottom_air__wet_bulb_temperature                degC     wet-bulb temperature (Stull 2011)
Withdrawal always equals consumption plus return, and return equals the sewer's plus the source's, every step. Water limits and dissolved mass,
which the data center component takes (design 0006), are not here yet: they need the plant's limited physics, and come with it.
"""

from waterledger_models import heat_rejection as hr
from waterledger_models import once_through as ot
from waterledger_models.battery import physics as bp
from waterledger_models.datacenter.bmi import HUMIDITY, ScalarPointBmi, read_config
from waterledger_models.weather import from_open_meteo_json, relative_humidity

INPUTS = {
    "atmosphere_bottom_air__temperature": "degC",
    "atmosphere_bottom_air_water_vapor__relative_saturation": "percent",
    "atmosphere_bottom_air_water_vapor__mass_fraction": "kg kg-1",
    "land_surface_air__pressure": "Pa",
    "lake_water_surface__temperature": "degC",
    "atmosphere_bottom_air_flow__speed": "m s-1",
}
OUTPUTS = {
    "water_user_water__withdrawal_volume_flux": "m3 s-1",
    "water_user_water__gain_volume_flux": "m3 s-1",
    "water_user_water__consumption_volume_flux": "m3 s-1",
    "water_user_water__return_volume_flux": "m3 s-1",
    "water_user_water__sewer_return_volume_flux": "m3 s-1",
    "water_user_water__source_return_volume_flux": "m3 s-1",
    "water_user__electric_power": "MW",
    "water_user__fuel_power": "MW",
    "atmosphere_bottom_air__wet_bulb_temperature": "degC",
}
WATER = {"withdrawn": "water_user_water__withdrawal_volume_flux", "consumed": "water_user_water__consumption_volume_flux",
         "returned": "water_user_water__return_volume_flux", "to_sewer": "water_user_water__sewer_return_volume_flux",
         "to_source": "water_user_water__source_return_volume_flux"}
MPH_PER_MS = ot.MPH_PER_MS


class BatteryCellBmi(ScalarPointBmi):
    """BMI 2.0 wrapper around waterledger_models.battery.physics: a battery cell plant's water and energy, hour by hour."""

    INPUTS = INPUTS
    OUTPUTS = OUTPUTS
    _name = "Battery cell plant water model"

    def __init__(self):
        super().__init__()
        self._design = "towers"
        self._humidity = "relative"
        self._gwh = 10.0
        self._params = {**bp.central_parameters(), "utilization": 1.0}
        self._forcing = None

    def initialize(self, config_file=None):
        cfg = read_config(config_file)
        self._design = cfg.get("design", "towers")
        if self._design not in bp.DESIGNS:
            raise ValueError(f"design must be one of {bp.DESIGNS}")
        self._humidity = cfg.get("humidity", "relative")
        if self._humidity not in HUMIDITY:
            raise ValueError(f"humidity must be one of {HUMIDITY}")
        if self._humidity == "specific" and cfg.get("forcing"):
            raise ValueError("a forcing file carries relative humidity: use humidity: relative with it")
        chemistry = cfg.get("chemistry", "nmc")
        if chemistry not in bp.CHEMISTRIES:
            raise ValueError(f"chemistry must be one of {bp.CHEMISTRIES}")
        self._gwh = float(cfg.get("capacity_gwh", 10.0))
        self._dt = float(cfg.get("time_step", 3600.0))
        given = {k: float(v) for k, v in (cfg.get("parameters") or {}).items()}
        unknown = set(given) - set(bp.PARAMETERS) - {"design_db", "design_h", "switch_on"}
        if unknown:
            raise ValueError(f"unknown parameters: {sorted(unknown)}")
        if chemistry != "lfp" and set(given) & set(bp.LFP):
            raise ValueError("lfp_factor is an LFP plant's: use chemistry: lfp")
        lfp = {k: (a + b) / 2 for k, (a, b) in bp.LFP.items()} if chemistry == "lfp" else {}
        self._params = {**bp.central_parameters(), "utilization": 1.0, **lfp, **given}
        self._time = 0.0
        if cfg.get("forcing"):
            w = from_open_meteo_json(cfg["forcing"])
            self._forcing = (w["air_temperature"].values, w["relative_humidity"].values)
            located = bp.for_location(self._params, *self._forcing)
            self._params = {**located, **{k: v for k, v in given.items() if k in ("design_db", "design_h")}}
            self._end = float(cfg.get("end_time", len(self._forcing[0]) * self._dt))
        else:
            self._forcing = None
            self._end = float(cfg.get("end_time", 365 * 86400.0))
        if "design_h" not in self._params:
            raise ValueError("design_h, the place's design enthalpy, is needed: give a forcing file or set it (physics.for_location)")
        if self._design == "hybrid" and "design_db" not in self._params and "switch_on" not in self._params:
            raise ValueError("a hybrid needs the place's design dry-bulb: give a forcing file or set design_db (physics.for_location)")
        for v in self._values.values():
            v[:] = 0.0
        self._values["atmosphere_bottom_air_flow__speed"][0] = self._params["wind_mph"] / MPH_PER_MS
        self._set.clear()

    def _advance(self):
        if self._forcing is not None:
            i = min(int(self._time // self._dt), len(self._forcing[0]) - 1)
            self._force("atmosphere_bottom_air__temperature", self._forcing[0][i])
            self._force("atmosphere_bottom_air_water_vapor__relative_saturation", self._forcing[1][i])

    def _compute(self):
        v = self._values
        tdb = v["atmosphere_bottom_air__temperature"].copy()
        if self._humidity == "specific":
            rh = relative_humidity(tdb, v["atmosphere_bottom_air_water_vapor__mass_fraction"], v["land_surface_air__pressure"])
        else:
            rh = v["atmosphere_bottom_air_water_vapor__relative_saturation"].copy()
        twb = hr.wet_bulb(tdb, rh)
        lake = self._design == "lake"
        p = {**self._params, "wind_mph": float(v["atmosphere_bottom_air_flow__speed"][0]) * MPH_PER_MS} if lake else self._params
        h = bp.hourly(tdb, twb, rh, self._design, p, v["lake_water_surface__temperature"].copy() if lake else None)
        to_m3s = self._gwh / ot.GAL_M3 / 3600.0          # gallons in the hour per GWh/yr to m3 s-1 for the plant
        for key, name in WATER.items():
            v[name][0] = h[key][0] * to_m3s
        v["water_user__electric_power"][0] = h["electricity"][0] * self._gwh / 1000.0
        v["water_user__fuel_power"][0] = h["fuel"][0] * self._gwh / 1000.0
        v["atmosphere_bottom_air__wet_bulb_temperature"][0] = twb[0]

    def finalize(self):
        self._forcing = None
