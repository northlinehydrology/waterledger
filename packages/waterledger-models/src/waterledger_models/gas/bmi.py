"""CSDMS Basic Model Interface (BMI 2.0) for a new gas plant (design 0014), so a coupling framework can drive it hour by hour: set the demand it is
asked to serve and the hour's weather (and, for the lake design, the lake's surface temperature), call update(), read what it served, what it could
not, its fuel and the water it withdrew, consumed and returned, and where the return went. Outputs change only on update(), as for the other
water users' components (waterledger_models.datacenter.bmi, waterledger_models.battery.bmi).

One plant is one scalar grid point and one parameter set (the central values by default, any overridable). Every unit is up: outages are the
Monte Carlo's (gas.plant, physics.outages), not a coupled run's.

Configuration (a YAML file, or the same keys as a dict passed to initialize):
    technology: cc | ct | engine | fuel_cell        (default cc)
    design: towers | hybrid | assist | dry | lake | none   (one of physics.DESIGNS[technology]; default the technology's first)
    units: 2                                         (identical units)
    unit_mw: 300                                     (each unit's net rating at ISO, MW)
    nox: dln | water                                 (default dln; water injection for turbines)
    inlet_cooling: false                             (inlet evaporative cooling, turbines)
    time_step: 3600, end_time: 31536000              (seconds)
    humidity: relative | specific                    (which humidity inputs it reads; default relative)
    parameters: {coc: 4, design_db: 31.0, ...}       (overrides of the central values; hybrid and assist need design_db, the place's 0.4%
                                                      design dry-bulb, C, from its hourly record: heat_rejection.design_dry_bulb)

Variables (all on the one scalar grid point, float64):
    input   power_plant__electric_power_demand                         MW       the output asked of the plant this step [A: name]
    input   atmosphere_bottom_air__temperature                         degC
    input   atmosphere_bottom_air_water_vapor__relative_saturation     percent  (humidity: relative)
    input   atmosphere_bottom_air_water_vapor__mass_fraction           kg kg-1  (humidity: specific)
    input   land_surface_air__pressure                                 Pa       (humidity: specific)
    input   lake_water_surface__temperature                            degC     the lake design's intake, standing for it [A]
    input   atmosphere_bottom_air_flow__speed                          m s-1    wind over the lake (lake design)
    output  water_user_water__withdrawal_volume_flux                   m3 s-1
    output  water_user_water__gain_volume_flux                         m3 s-1   always 0
    output  water_user_water__consumption_volume_flux                  m3 s-1
    output  water_user_water__return_volume_flux                       m3 s-1   the two returns below together
    output  water_user_water__sewer_return_volume_flux                 m3 s-1   tower blowdown, the demineralizer's reject
    output  water_user_water__source_return_volume_flux                m3 s-1   the lake design's once-through water less its forced evaporation
    output  power_plant__electric_power_output                         MW       net output served
    output  power_plant__unserved_electric_power                       MW       demand the available units could not carry
    output  water_user__electric_power                                 MW       the plant's own auxiliary load (from its own output)
    output  water_user__fuel_power                                     MW       gas burned, HHV
    output  atmosphere_bottom_air__wet_bulb_temperature                degC
Withdrawal equals consumption plus return, and return equals the sewer's plus the source's, every step.
"""

from waterledger_models import heat_rejection as hr
from waterledger_models import once_through as ot
from waterledger_models.datacenter.bmi import HUMIDITY, ScalarPointBmi, read_config
from waterledger_models.gas import physics as gp
from waterledger_models.weather import relative_humidity

INPUTS = {
    "power_plant__electric_power_demand": "MW",
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
    "power_plant__electric_power_output": "MW",
    "power_plant__unserved_electric_power": "MW",
    "water_user__electric_power": "MW",
    "water_user__fuel_power": "MW",
    "atmosphere_bottom_air__wet_bulb_temperature": "degC",
}
WATER = {"withdrawn": "water_user_water__withdrawal_volume_flux", "consumed": "water_user_water__consumption_volume_flux",
         "returned": "water_user_water__return_volume_flux", "to_sewer": "water_user_water__sewer_return_volume_flux",
         "to_source": "water_user_water__source_return_volume_flux"}
TO_M3S = 1.0 / ot.GAL_M3 / 3600.0      # gallons in the hour to m3 s-1


class GasPlantBmi(ScalarPointBmi):
    """BMI 2.0 wrapper around waterledger_models.gas.physics: a new gas plant's output, fuel and water, hour by hour."""

    INPUTS = INPUTS
    OUTPUTS = OUTPUTS
    _name = "Gas plant water model"

    def __init__(self):
        super().__init__()
        self._tech, self._design, self._n_units, self._unit_mw = "cc", "towers", 2, 300.0
        self._humidity, self._inlet = "relative", False
        self._params = gp.central_parameters("cc", "towers")

    def initialize(self, config_file=None):
        cfg = read_config(config_file)
        self._tech = cfg.get("technology", "cc")
        if self._tech not in gp.TECHNOLOGIES:
            raise ValueError(f"technology must be one of {gp.TECHNOLOGIES}")
        self._design = cfg.get("design", gp.DESIGNS[self._tech][0])
        nox = cfg.get("nox", "dln")
        r = gp.ranges(self._tech, self._design, nox)            # checks the design and the NOx setting
        self._humidity = cfg.get("humidity", "relative")
        if self._humidity not in HUMIDITY:
            raise ValueError(f"humidity must be one of {HUMIDITY}")
        self._n_units, self._unit_mw = int(cfg.get("units", 2)), float(cfg.get("unit_mw", 300.0))
        self._inlet = bool(cfg.get("inlet_cooling", False))
        given = {k: float(v) for k, v in (cfg.get("parameters") or {}).items()}
        unknown = set(given) - set(r) - {"design_db"}
        if unknown:
            raise ValueError(f"unknown parameters: {sorted(unknown)}")
        self._params = {**gp.central_parameters(self._tech, self._design, nox), **given}
        if self._design in ("hybrid", "assist") and "design_db" not in self._params:
            raise ValueError("a hybrid or assist condenser needs the place's design dry-bulb: set design_db (heat_rejection.design_dry_bulb)")
        self._dt = float(cfg.get("time_step", 3600.0))
        self._end = float(cfg.get("end_time", 365 * 86400.0))
        self._time = 0.0
        for v in self._values.values():
            v[:] = 0.0
        if "wind_mph" in self._params:
            self._values["atmosphere_bottom_air_flow__speed"][0] = self._params["wind_mph"] / ot.MPH_PER_MS
        self._set.clear()

    def _compute(self):
        v = self._values
        tdb = v["atmosphere_bottom_air__temperature"].copy()
        if self._humidity == "specific":
            rh = relative_humidity(tdb, v["atmosphere_bottom_air_water_vapor__mass_fraction"], v["land_surface_air__pressure"])
        else:
            rh = v["atmosphere_bottom_air_water_vapor__relative_saturation"].copy()
        twb = hr.wet_bulb(tdb, rh)
        lake = self._design == "lake"
        p = {**self._params, "wind_mph": float(v["atmosphere_bottom_air_flow__speed"][0]) * ot.MPH_PER_MS} if lake else self._params
        h = gp.hourly(v["power_plant__electric_power_demand"].copy(), tdb, twb, rh, self._tech, self._design, p, self._n_units, self._unit_mw,
                      self._inlet, v["lake_water_surface__temperature"].copy() if lake else None)
        for key, name in WATER.items():                           # the physics gives gallons in the hour: a rate, whatever the step
            v[name][0] = h[key][0] * TO_M3S
        v["power_plant__electric_power_output"][0] = h["served"][0]
        v["power_plant__unserved_electric_power"][0] = h["unserved"][0]
        v["water_user__electric_power"][0] = h["aux"][0]
        v["water_user__fuel_power"][0] = h["fuel"][0]
        v["atmosphere_bottom_air__wet_bulb_temperature"][0] = twb[0]
