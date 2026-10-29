"""Trace any U.S. watershed (HUC12) downstream or upstream and list the assessed and impaired waters along the way, with their
causes and whether a cleanup plan (TMDL) covers each: USGS Watershed Boundary Dataset and EPA ATTAINS (with EPA's national
assessment-unit-to-HUC12 crosswalk). Works across state lines. Formerly the attains-trace package.

    from waterledger_data.trace import ServiceNetwork, trace
    t = trace("040500060505", "downstream", ServiceNetwork())
    t.path, t.impaired, t.cause_summary()

The same tracer runs against the live services, a PostGIS mirror (waterledger_data.trace.postgis; pip install
"waterledger-data[postgis]"), or a test fake. Command line: waterledger-trace HUC12.
"""
from .trace import ServiceNetwork, Trace, downstream_path, trace, upstream_network

__all__ = ["ServiceNetwork", "Trace", "downstream_path", "trace", "upstream_network"]
