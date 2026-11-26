"""A digest of every output of every BMI component over a year of hourly steps, to show that a change leaves them alone (design 0024).

Run it on two checkouts and compare the digests:
    uv run python tools/compare_bmi_outputs.py > here.txt
    PYTHONPATH=<other checkout>/packages/waterledger-models/src uv run python tools/compare_bmi_outputs.py > there.txt
    diff here.txt there.txt
Each line is a case and the sha256 of its outputs, step by step, as float64 bytes. The script uses only BMI 2.0 calls, so it runs on
versions before get_state existed. The weather is synthetic and seeded.
"""
import hashlib
import sys

import numpy as np

import waterledger_models
from waterledger_models import grid
from waterledger_models.battery.bmi import BatteryCellBmi
from waterledger_models.datacenter.bmi import CoolingWaterBmi, LakeCoolingBmi
from waterledger_models.gas.bmi import GasPlantBmi
from waterledger_models.grid.bmi import GridWaterBmi

HOURS = 8760
TEMP = "atmosphere_bottom_air__temperature"
RH = "atmosphere_bottom_air_water_vapor__relative_saturation"
LIMIT = "water_user_water__withdrawal_volume_flux_limit"
DRY = "water_user__dry_mode_flag"


def weather(hours=HOURS, seed=0):
    rng = np.random.default_rng(seed)
    h = np.arange(hours)
    t = 11 + 15 * np.sin(2 * np.pi * (h / 24 - 110) / 365.25) + 5 * np.sin(2 * np.pi * (h % 24 - 9) / 24) + rng.normal(0, 2, h.size)
    rh = np.clip(70 - 15 * np.sin(2 * np.pi * (h % 24 - 9) / 24) + rng.normal(0, 8, h.size), 15, 100)
    return t, rh


def grid_table():
    rng = np.random.default_rng(1)
    h0 = int(np.datetime64("2021-01-01T00", "h").astype(int))
    hour = np.arange(h0, h0 + 3 * 8760)
    month, hod, _ = grid.calendar(hour)
    temp = 10 + 12 * np.sin(2 * np.pi * (month - 3) / 12) + 5 * np.sin(2 * np.pi * (hod - 15) / 24) + rng.normal(0, 3, hour.size)
    base, gas = np.full(hour.size, 1000.0), 400 + 40 * np.clip(temp - 10, 0, None) + rng.normal(0, 20, hour.size)
    gen = base + gas
    return grid.fit("TEST", hour, (base * 500 + gas * 200) / gen, (base * 800 + gas * 250) / gen, gen, temp)


def digest(m, inputs):
    """Step m through every hour, setting each hour's inputs, and hash the outputs."""
    h = hashlib.sha256()
    names = m.get_output_var_names()
    out = np.empty(1)
    for i in range(HOURS):
        for k, v in inputs(i).items():
            m.set_value(k, np.array([v], dtype=float))
        m.update()
        for k in names:
            h.update(m.get_value(k, out).tobytes())
    m.finalize()
    return h.hexdigest()


def cases():
    t, rh = weather()
    air = lambda i: {TEMP: t[i], RH: rh[i]}
    yield "lake", LakeCoolingBmi, {"it_capacity_mw": 100, "time_step": 3600, "end_time": HOURS * 3600.0}, \
        lambda i: {"lake_water_surface__temperature": 4 + 18 * max(0.0, np.sin(2 * np.pi * (i / 24 - 120) / 365.25))}
    for design in ("towers", "hybrid", "assist", "dry"):
        cfg = {"design": design, "it_capacity_mw": 300, "parameters": {"design_db": 31.0}}
        yield f"cooling {design}", CoolingWaterBmi, cfg, air
        yield f"cooling {design}, limits and dry mode", CoolingWaterBmi, cfg, \
            lambda i: {**air(i), LIMIT: 0.08 if i % 5 == 0 else np.inf, DRY: 1.0 if i % 11 == 0 else 0.0,
                       "water_user_intake_water_chloride__mass_concentration": 0.03}
    for plant in ("warm", "chilled"):
        yield f"cooling towers, {plant} plant", CoolingWaterBmi, {"design": "towers", "plant": plant, "it_capacity_mw": 100}, air
    for design in ("towers", "hybrid", "lake"):
        cfg = {"design": design, "capacity_gwh": 10, "parameters": {"design_h": 70.0, "design_db": 31.0}}
        yield f"battery {design}", BatteryCellBmi, cfg, \
            (lambda i: {**air(i), "lake_water_surface__temperature": 8.0}) if design == "lake" else air
    demand = lambda i: {**air(i), "power_plant__electric_power_demand": 300 + 250 * np.sin(i / 5.0)}
    for tech, design in (("cc", "towers"), ("cc", "hybrid"), ("cc", "dry"), ("ct", "none")):
        yield f"gas {tech} {design}", GasPlantBmi, {"technology": tech, "design": design, "parameters": {"design_db": 31.0}}, demand
    yield "grid", GridWaterBmi, {"table": grid_table(), "start": "2021-01-01T00"}, \
        lambda i: {"water_user__electric_power": 100 + 50 * np.sin(i / 7.0), TEMP: t[i]}


def main():
    print(f"# waterledger_models from {waterledger_models.__file__}", file=sys.stderr)
    for name, cls, cfg, inputs in cases():
        m = cls()
        try:
            m.initialize({**cfg, "end_time": HOURS * float(cfg.get("time_step", 3600))})
        except (ValueError, KeyError) as e:          # a case a version doesn't support is listed, not hidden
            print(f"{name}\tnot run: {e}")
            continue
        print(f"{name}\t{digest(m, inputs)}")


if __name__ == "__main__":
    main()
