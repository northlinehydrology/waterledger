"""County water use (waterledger_data.wateruse): each layer's arithmetic, category mapping and basis, on small fixtures."""

import pytest

from waterledger_data import wateruse as wu


def test_categories_are_fixed():
    assert wu.CATEGORIES[-1] == "total" and len(set(wu.CATEGORIES)) == len(wu.CATEGORIES)
    assert set(wu.USGS_CATS) | {"other", "total"} == set(wu.CATEGORIES)


def test_usgs_sums_fresh_saline_ground_surface():
    row = {"County Name": "Test County", "PS-WGWFr": 1.0, "PS-WGWSa": 0.5, "PS-WSWFr": 10.0, "PS-WSWSa": float("nan"),
           "CO-WGWFr": float("nan"), "CO-WSWFr": float("nan"),                    # not estimated: left out, not zero
           "IC-WGWFr": 2.0, "IC-WSWFr": 0.0, "IG-WGWFr": 0.3, "IG-WSWFr": 0.2, "IR-WGWFr": 0.1, "IR-WSWFr": float("nan"),
           "IT-WGWFr": 2.4, "IT-WSWFr": 0.2,                                         # irrigation total: not counted twice
           "PO-WSWFr": 4.0, "PC-WGWFr": 0.25, "PC-WSWSa": 0.75, "DO-WGWFr": 3.0, "DO-PSDel": 9.0}
    r = wu.usgs_record(row, [c for c in row if "-W" in c])
    assert r["mgd"]["public_supply"] == 11.5 and r["ground_mgd"]["public_supply"] == 1.5 and r["surface_mgd"]["public_supply"] == 10.0
    assert "commercial" not in r["mgd"]
    assert r["mgd"]["irrigation"] == 2.1 and r["mgd"]["golf"] == 0.5
    assert r["mgd"]["thermoelectric"] == 5.0 and r["mgd"]["domestic"] == 3.0
    assert r["mgd"]["total"] == pytest.approx(11.5 + 2.1 + 0.5 + 5.0 + 3.0)
    assert r["ground_mgd"]["total"] + r["surface_mgd"]["total"] == pytest.approx(r["mgd"]["total"])
    assert r["delivered_to_homes_mgd"] == 9.0
    assert list(r["mgd"])[-1] == "total"


def test_usgs_basis_is_an_estimate():
    b = wu.USGS_BASIS
    assert b["kind"] == "estimate" and b["measure"] == "withdrawals" and b["year"] == 2015 and b["doi"] == "10.5066/P14Q6AVK"
