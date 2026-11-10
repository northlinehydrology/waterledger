"""Hourly generation of hypothetical new supply for a water user's power (design 0014): solar PV and onshore wind as generation profiles, per MW,
from ERA5's radiation and 100 m wind at the user's own cell. They use little water, so they are profiles, not water user types; a new gas
plant is a type (waterledger_models.gas).

    pv     PVWatts' chain (Dobos 2014), tested against pvlib
    wind   the IEA 3.4 MW reference turbine's power curve
"""
from waterledger_models.supply import pv, wind  # noqa: F401
