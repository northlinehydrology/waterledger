"""Hourly generation of hypothetical new supply for a water user's power (design 0014): solar PV and onshore wind as generation profiles, per MW,
from ERA5's radiation and 100 m wind at the user's own cell. They use little water, so they are profiles, not water user types; a new gas
plant is a type (waterledger_models.gas).

    pv         PVWatts' chain (Dobos 2014), tested against pvlib
    wind       the IEA 3.4 MW reference turbine's power curve
    scenario   supply scenarios as the shared runner's extra: dispatch hour by hour, sizing, what each scenario reports
    land       solar and wind projects' land, runoff and one-time construction water and sediment, through runoff
"""
from waterledger_models.supply import land, pv, scenario, wind  # noqa: F401
