"""New gas plants (design 0014): a hypothetical plant's output, fuel, heat and water hour by hour, for the demand it serves.

    physics   the hourly heat and water balance by technology (cc, ct, engine, fuel_cell) and cooling design, on the shared heat rejection
    plant     the Monte Carlo at one location through the shared runner (waterledger_models.runs)
"""
from waterledger_models.gas import physics, plant  # noqa: F401
