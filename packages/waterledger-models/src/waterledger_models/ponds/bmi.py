"""CSDMS Basic Model Interface (BMI 2.0, with get_state/set_state) for a cooling pond (design 0024, part 2): a plant's heat into a built pond,
step by step, the pond keeping its volume, temperature and dissolved mass from one step to the next. waterledger_models.ponds.physics has the
physics.

One pond is one scalar grid point. Its state carries with get_state and set_state, so a scenario can start from a warm-up's pond.

Configuration (a YAML file, or the same keys as a dict passed to initialize):
    area_m2: 2.0e6                 the pond's surface area at its operating volume, m2 (required)
    depth_m: 4.0                   its mean depth at the operating volume, m (required); the operating volume is area x depth
    heat_mw: 500                   the plant's heat into the pond, MW; or, for a data center,
    it_capacity_mw: 100            IT capacity, its heat IT x utilization x heat factor (the lake design's parameters, central values unless given)
    time_step: 3600                seconds (hourly default; daily works, the heat balance is solved implicitly)
    end_time: 31536000             seconds; default one year
    humidity: relative | specific  which humidity inputs are read (default relative)
    initial_temperature: 20        C; default the first step's air temperature
    initial_volume_share: 1.0      share of the operating volume at the start
    initial_concentration: {chloride: 0.03}     kg m-3 in the pond at the start (default 0)
    parameters: {coc: 4, seepage_mm_day: 1, max_supply_c: 35, ...}   physics.POND_PARAMETERS, and utilization and heat_factor
A heat set through set_value on water_user__waste_heat_power is used instead of heat_mw or it_capacity_mw from then on, as any input holds
until it is set again; setting it to NaN goes back to the configured heat.

Variables (one scalar grid point, float64):
    input   atmosphere_bottom_air__temperature                          degC     air temperature; rain falls at it [A]
    input   atmosphere_bottom_air_water_vapor__relative_saturation      percent  (humidity: relative)
    input   atmosphere_bottom_air_water_vapor__mass_fraction            kg kg-1  (humidity: specific)
    input   land_surface_air__pressure                                  Pa       default 101325
    input   atmosphere_bottom_air_flow__speed                           m s-1    wind at wind_height_m (default 10 m)
    input   land_surface_radiation~incoming~shortwave__energy_flux      W m-2
    input   land_surface_radiation~incoming~longwave__energy_flux       W m-2
    input   atmosphere_water__liquid_equivalent_precipitation_rate      mm s-1   rain on the pond
    input   water_user__waste_heat_power                                MW       the plant's heat; NaN (the default) is the configured heat
    input   water_user_intake_water__temperature                        degC     the makeup's temperature; NaN (the default) is the air's [A]
    input   water_user_water__withdrawal_volume_flux_limit              m3 s-1   the most makeup this step; infinity (the default) is none
    input   water_user__dry_mode_flag                                   1        1: no makeup this step (a limit of zero)
    input   water_user_intake_water_<name>__mass_concentration          kg m-3   in the makeup, for dissolved_solids, chloride, phosphorus
    output  water_user_water__withdrawal_volume_flux                    m3 s-1   makeup
    output  water_user_water__gain_volume_flux                          m3 s-1   rain on the pond
    output  water_user_water__consumption_volume_flux                   m3 s-1   the pond's evaporation, all of it (Andrew, Nov 26)
    output  water_user_water__natural_evaporation_volume_flux           m3 s-1   what the same pond with no plant heat would evaporate
    output  water_user_water__forced_evaporation_volume_flux            m3 s-1   the plant's share: the two above's difference
    output  water_user_water__return_volume_flux                        m3 s-1   the two returns below together
    output  water_user_water__stream_return_volume_flux                 m3 s-1   blowdown and spill, to a stream
    output  water_user_water__ground_return_volume_flux                 m3 s-1   seepage through the bed
    output  water_user_water__volume                                    m3       water in the pond at the step's end (the storage role, 0010)
    output  water_user_water__volume_change_rate                        m3 s-1   its change over the step
    output  water_user_return_water__temperature                        degC     the pond's temperature: the returns leave at it
    output  pond_water_surface__area                                    m2
    output  water_user__unremoved_heat_power                            MW       the plant's heat not taken: the pond below its lowest
                                                                                 workable volume
    output  water_user__setpoint_lost_time                              h        steps with the pond above the plant's highest supply
                                                                                 temperature or below its lowest volume, summed since
                                                                                 initialize
    output  water_user_return_water_<name>__mass_flux                   kg s-1   dissolved mass in the returns
    output  water_user_ground_return_water_<name>__mass_flux            kg s-1   the part of it in seepage
    output  water_user_stored_water_<name>__mass                        kg       dissolved mass in the pond
Every step: withdrawal + gain = consumption + return + volume change rate; each constituent's intake mass = its return mass + its stored
mass's change; and the pond's heat closes (physics.step's terms).
"""
import math

import numpy as np

from waterledger_models.datacenter import lake
from waterledger_models.datacenter.bmi import CONSTITUENTS, DRY_MODE, INTAKE, LIMIT, RETURN_MASS, ScalarPointBmi, read_config
from waterledger_models.ponds import physics
from waterledger_models.weather import relative_humidity

TEMP = "atmosphere_bottom_air__temperature"
RH = "atmosphere_bottom_air_water_vapor__relative_saturation"
Q = "atmosphere_bottom_air_water_vapor__mass_fraction"
PRESSURE = "land_surface_air__pressure"
WIND = "atmosphere_bottom_air_flow__speed"
SW = "land_surface_radiation~incoming~shortwave__energy_flux"
LW = "land_surface_radiation~incoming~longwave__energy_flux"
RAIN = "atmosphere_water__liquid_equivalent_precipitation_rate"
HEAT = "water_user__waste_heat_power"
MAKEUP_T = "water_user_intake_water__temperature"
GROUND_MASS = "water_user_ground_return_water_{}__mass_flux"
STORED_MASS = "water_user_stored_water_{}__mass"

INPUTS = {
    TEMP: "degC", RH: "percent", Q: "kg kg-1", PRESSURE: "Pa", WIND: "m s-1", SW: "W m-2", LW: "W m-2", RAIN: "mm s-1", HEAT: "MW",
    MAKEUP_T: "degC", LIMIT: "m3 s-1", DRY_MODE: "1",
    **{INTAKE.format(k): "kg m-3" for k in CONSTITUENTS},
}
OUTPUTS = {
    "water_user_water__withdrawal_volume_flux": "m3 s-1",
    "water_user_water__gain_volume_flux": "m3 s-1",
    "water_user_water__consumption_volume_flux": "m3 s-1",
    "water_user_water__natural_evaporation_volume_flux": "m3 s-1",
    "water_user_water__forced_evaporation_volume_flux": "m3 s-1",
    "water_user_water__return_volume_flux": "m3 s-1",
    "water_user_water__stream_return_volume_flux": "m3 s-1",
    "water_user_water__ground_return_volume_flux": "m3 s-1",
    "water_user_water__volume": "m3",
    "water_user_water__volume_change_rate": "m3 s-1",
    "water_user_return_water__temperature": "degC",
    "pond_water_surface__area": "m2",
    "water_user__unremoved_heat_power": "MW",
    "water_user__setpoint_lost_time": "h",
    **{RETURN_MASS.format(k): "kg s-1" for k in CONSTITUENTS},
    **{GROUND_MASS.format(k): "kg s-1" for k in CONSTITUENTS},
    **{STORED_MASS.format(k): "kg" for k in CONSTITUENTS},
}
HUMIDITY = ("relative", "specific")


class CoolingPondBmi(ScalarPointBmi):
    """BMI 2.0 component for a cooling pond that keeps its volume, temperature and dissolved mass between steps (design 0024)."""

    INPUTS = INPUTS
    OUTPUTS = OUTPUTS
    _name = "Cooling pond"
    _STATE = ("_pond", "_last")

    def __init__(self):
        super().__init__()
        self._params = None
        self._heat_w = 0.0
        self._humidity = "relative"
        self._initial_t = None
        self._pond = None          # the pond's state: volume, temperature (None until the first step), mass, natural_temperature
        self._last = None          # the last step's terms, for the balances (physics.step's fluxes); None before the first step

    def initialize(self, config_file=None):
        cfg = read_config(config_file)
        for key in ("area_m2", "depth_m"):
            if key not in cfg:
                raise ValueError(f"a cooling pond needs {key}: its surface area (m2) and mean depth (m) at the operating volume")
        area, depth = float(cfg["area_m2"]), float(cfg["depth_m"])
        if not (area > 0 and depth > 0):
            raise ValueError("a cooling pond's area and depth must be positive")
        self._humidity = cfg.get("humidity", "relative")
        if self._humidity not in HUMIDITY:
            raise ValueError(f"humidity must be one of {HUMIDITY}")
        given = {k: float(v) for k, v in (cfg.get("parameters") or {}).items()}
        lake_central = {k: (a + b) / 2 for k, (a, b) in lake.RANGES.items() if k in ("utilization", "heat_factor")}
        unknown = set(given) - set(physics.POND_PARAMETERS) - set(lake_central)
        if unknown:
            raise ValueError(f"unknown parameters: {sorted(unknown)}")
        self._params = {**physics.POND_PARAMETERS, **{k: v for k, v in given.items() if k in physics.POND_PARAMETERS},
                        "area_m2": area, "volume_m3": area * depth}
        if self._params["coc"] <= 1.0:
            raise ValueError("coc, the cycles of concentration, must be above 1")
        if "heat_mw" in cfg and "it_capacity_mw" in cfg:
            raise ValueError("give heat_mw or it_capacity_mw, not both")
        if "it_capacity_mw" in cfg:
            p = {**lake_central, **{k: v for k, v in given.items() if k in lake_central}}
            self._heat_w = float(cfg["it_capacity_mw"]) * 1e6 * p["utilization"] * p["heat_factor"]
        else:
            self._heat_w = float(cfg.get("heat_mw", 0.0)) * 1e6
        self._dt = float(cfg.get("time_step", 3600.0))
        self._end = float(cfg.get("end_time", 365 * 86400.0))
        self._time = 0.0
        t0 = cfg.get("initial_temperature")
        self._initial_t = None if t0 is None else float(t0)
        share = float(cfg.get("initial_volume_share", 1.0))
        if not 0 < share <= 1:
            raise ValueError("initial_volume_share must be in (0, 1]")
        conc = {k: float(v) for k, v in (cfg.get("initial_concentration") or {}).items()}
        if set(conc) - set(CONSTITUENTS):
            raise ValueError(f"initial_concentration takes {CONSTITUENTS}")
        v0 = share * self._params["volume_m3"]
        self._pond = {"volume": v0, "temperature": self._initial_t, "natural_temperature": self._initial_t,
                      "mass": {k: conc.get(k, 0.0) * v0 for k in CONSTITUENTS}}
        self._last = None
        for v in self._values.values():
            v[:] = 0.0
        self._values[PRESSURE][0] = 101325.0
        self._values[HEAT][0] = np.nan            # NaN: the configured heat
        self._values[MAKEUP_T][0] = np.nan
        self._values[LIMIT][0] = np.inf
        self._values["water_user_water__volume"][0] = v0
        for k in CONSTITUENTS:
            self._values[STORED_MASS.format(k)][0] = self._pond["mass"][k]
        self._set.clear()

    def _compute(self):
        v, p = self._values, self._params
        air = float(v[TEMP][0])
        pressure = float(v[PRESSURE][0])
        if self._humidity == "specific":
            rh = float(relative_humidity(v[TEMP], v[Q], v[PRESSURE])[0])
        else:
            rh = float(v[RH][0])
        ea = rh / 100.0 * float(physics._es(air))
        heat = float(v[HEAT][0])
        heat_w = self._heat_w if math.isnan(heat) else heat * 1e6
        cap = 0.0 if v[DRY_MODE][0] >= 0.5 else max(float(v[LIMIT][0]), 0.0)
        makeup_c = float(v[MAKEUP_T][0])
        w = {"air": air, "ea": ea, "pressure_hpa": pressure / 100.0, "sw": float(v[SW][0]), "lw": float(v[LW][0]),
             "u2": physics.wind_at_2m(max(float(v[WIND][0]), 0.0), p["wind_height_m"]), "rain": max(float(v[RAIN][0]), 0.0),
             "makeup_c": air if math.isnan(makeup_c) else makeup_c,
             "conc": {k: float(v[INTAKE.format(k)][0]) for k in CONSTITUENTS}}
        s = dict(self._pond)
        if s["temperature"] is None:                     # the first step starts at the air's temperature unless one was given
            s["temperature"] = air
            s["natural_temperature"] = air
        v0 = s["volume"]
        new, f = physics.step(s, w, heat_w, cap, self._dt, p)
        self._pond = new
        self._last = {k: x for k, x in f.items() if not isinstance(x, dict)} | {"mass_in": f["mass_in"], "mass_out": f["mass_out"],
                                                                               "mass_to_ground": f["mass_to_ground"], "volume_before": v0}
        stream = f["blowdown"] + f["spill"]
        v["water_user_water__withdrawal_volume_flux"][0] = f["makeup"]
        v["water_user_water__gain_volume_flux"][0] = f["rain"]
        v["water_user_water__consumption_volume_flux"][0] = f["evaporation"]
        v["water_user_water__natural_evaporation_volume_flux"][0] = f["natural_evaporation"]
        v["water_user_water__forced_evaporation_volume_flux"][0] = f["evaporation"] - f["natural_evaporation"]
        v["water_user_water__stream_return_volume_flux"][0] = stream
        v["water_user_water__ground_return_volume_flux"][0] = f["seepage"]
        v["water_user_water__return_volume_flux"][0] = stream + f["seepage"]
        v["water_user_water__volume"][0] = new["volume"]
        v["water_user_water__volume_change_rate"][0] = (new["volume"] - v0) / self._dt
        v["water_user_return_water__temperature"][0] = new["temperature"]
        v["pond_water_surface__area"][0] = f["area"]
        v["water_user__unremoved_heat_power"][0] = f["heat_unremoved"] / 1e6
        if new["temperature"] > p["max_supply_c"] or not f["running"]:
            v["water_user__setpoint_lost_time"][0] += self._dt / 3600.0
        for k in CONSTITUENTS:
            v[RETURN_MASS.format(k)][0] = f["mass_out"][k]
            v[GROUND_MASS.format(k)][0] = f["mass_to_ground"][k]
            v[STORED_MASS.format(k)][0] = new["mass"][k]

    def finalize(self):
        pass
