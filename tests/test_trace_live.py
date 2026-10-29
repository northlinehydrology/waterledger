"""The tracer against the live EPA and USGS services (nightly; pytest -m live)."""

import pytest

from waterledger_data.trace import ServiceNetwork, trace

pytestmark = pytest.mark.live


def test_plaster_creek_to_lake_michigan():
    t = trace("040500060505", "downstream", ServiceNetwork())
    assert t.path["huc12"].iloc[0] == "040500060505"
    assert t.path["name"].str.contains("Grand River").any()
    assert len(t.impaired) > 0 and len(t.cause_summary()) > 0
