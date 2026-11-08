"""CSDMS Basic Model Interface (BMI 2.0) for the grid component (design 0007): water at the power plants supplying a water
user's electricity, step by step. Couple it to any user that reports water_user__electric_power (CoolingWaterBmi does).

Configuration (a YAML file, or the same keys as a dict passed to initialize):
    table: path/to/grid_table.npz      a GridTable (waterledger_models.grid.fit) for the user's balancing authority and location
    start: "2024-07-01T00"             UTC time of the first step (sets the month and hour each step looks up)
    time_step: 3600                    seconds
    end_time: 31536000                 seconds; default one year

Variables (one scalar grid point, float64):
    input   water_user__electric_power                              MW      the user's electricity this step
    input   atmosphere_bottom_air__temperature                      degC    air temperature at the user this step
    output  power_plant_water__consumption_volume_flux              m3 s-1  water evaporated at the plants, average mix
    output  power_plant_water__withdrawal_volume_flux               m3 s-1  water taken in at the plants, average mix
    output  power_plant_water__marginal_consumption_volume_flux     m3 s-1  the same at the plants that follow added load
    output  power_plant_water__marginal_withdrawal_volume_flux      m3 s-1
    output  power_plant_water__consumption_intensity                gal MWh-1  the step's average factor, for reporting
Water at the plants is the user's electricity times the step's factor: no state carries from one step to the next.
"""
import numpy as np

from waterledger_models.datacenter.bmi import ScalarPointBmi, read_config
from waterledger_models.grid import GridTable, lookup

GAL_PER_M3 = 264.17205235814845

INPUTS = {"water_user__electric_power": "MW", "atmosphere_bottom_air__temperature": "degC"}
OUTPUTS = {
    "power_plant_water__consumption_volume_flux": "m3 s-1",
    "power_plant_water__withdrawal_volume_flux": "m3 s-1",
    "power_plant_water__marginal_consumption_volume_flux": "m3 s-1",
    "power_plant_water__marginal_withdrawal_volume_flux": "m3 s-1",
    "power_plant_water__consumption_intensity": "gal MWh-1",
}
_FLUX = {"consumed": "power_plant_water__consumption_volume_flux", "withdrawn": "power_plant_water__withdrawal_volume_flux",
         "marginal_consumed": "power_plant_water__marginal_consumption_volume_flux",
         "marginal_withdrawn": "power_plant_water__marginal_withdrawal_volume_flux"}


class GridWaterBmi(ScalarPointBmi):
    """BMI 2.0 wrapper around waterledger_models.grid: power plant water for a user's electricity."""

    INPUTS = INPUTS
    OUTPUTS = OUTPUTS
    _name = "Grid power plant water"

    def __init__(self):
        super().__init__()
        self._table = None
        self._start = None

    def initialize(self, config_file=None):
        cfg = read_config(config_file)
        if "table" not in cfg:
            raise ValueError("the grid component needs a table: a GridTable file (waterledger_models.grid.fit)")
        self._table = cfg["table"] if isinstance(cfg["table"], GridTable) else GridTable.load(cfg["table"])
        if "start" not in cfg:
            raise ValueError("the grid component needs start: the UTC time of the first step")
        self._start = np.datetime64(str(cfg["start"]), "s")
        self._dt = float(cfg.get("time_step", 3600.0))
        self._end = float(cfg.get("end_time", 365 * 86400.0))
        self._time = 0.0
        for v in self._values.values():
            v[:] = 0.0
        self._set.clear()

    def _compute(self):
        t = (self._start + np.timedelta64(int(self._time), "s")).astype("datetime64[h]")
        month = np.array([t.astype("datetime64[M]").astype(int) % 12])
        hod = np.array([t.astype(int) % 24])
        f = lookup(self._table, month, hod, np.array([self._values["atmosphere_bottom_air__temperature"][0]]))
        mwh_per_s = self._values["water_user__electric_power"][0] / 3600.0
        for k, name in _FLUX.items():
            self._values[name][0] = mwh_per_s * float(f[k][0]) / GAL_PER_M3
        self._values["power_plant_water__consumption_intensity"][0] = float(f["consumed"][0])

    def finalize(self):
        self._table = None
