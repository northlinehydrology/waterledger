"""County water use (waterledger_data.wateruse): each layer's arithmetic, category mapping and basis, on small fixtures."""

import pytest

from waterledger_data import wateruse as wu


FIPS_OH = {"Franklin County": "39049", "FRANKLIN": "39049", "Van Wert County": "39161", "VAN WERT": "39161"}


def test_categories_are_fixed():
    assert wu.CATEGORIES[-1] == "total" and len(set(wu.CATEGORIES)) == len(wu.CATEGORIES)
    assert set(wu.USGS_CATS) | {"other", "total"} == set(wu.CATEGORIES)
    assert set(wu.OHIO_CATS.values()) <= set(wu.CATEGORIES)


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


def _odnr():
    fac = [{"RegistrationNumber": "A", "Name": "City water", "CountyName": "FRANKLIN", "FacilityPrimaryUseType": "Public"},
           {"RegistrationNumber": "B", "Name": "Quarry", "CountyName": "FRANKLIN", "FacilityPrimaryUseType": "Mineral Extraction"},
           {"RegistrationNumber": "C", "Name": "Frac pond", "CountyName": "FRANKLIN", "FacilityPrimaryUseType": "Hydro Fracturing"},
           {"RegistrationNumber": "D", "Name": "Farm", "CountyName": "VAN WERT", "FacilityPrimaryUseType": "Agriculture"}]
    rows = lambda part: [{"RegistrationNumber": n, "Year": y, "Total": v} for n, y, v in part]
    return {"retrieved": "2026-10-30", "facilities": fac,
            "surface": rows([("A", 2024, 366.0), ("A", 2023, 365.0), ("B", 2024, 36.6), ("D", 2024, 0.0)]),
            "ground": rows([("A", 2024, 732.0), ("B", 2024, 73.2), ("C", 2024, 3.66), ("D", 2024, 18.3), ("D", 2023, 20.0)])}


def test_ohio_totals_by_county_and_use():
    o = wu.ohio(raw=_odnr(), fips=FIPS_OH)
    assert o["basis"]["year"] == 2024 and o["basis"]["kind"] == "reported" and o["basis"]["retrieved"] == "2026-10-30"
    f = o["counties"]["39049"]
    assert f["name"] == "Franklin County"
    assert f["mgd"]["public_supply"] == 3.0                                    # (366 + 732) MG over 366 days (2024 is a leap year)
    assert f["surface_mgd"]["public_supply"] == 1.0 and f["ground_mgd"]["public_supply"] == 2.0
    assert f["mgd"]["mining"] == pytest.approx(0.31)                          # quarry and fracking both count as mining ...
    assert set(f["source_values"]) == {"Public", "Mineral Extraction", "Hydro Fracturing"}    # ... and stay apart here
    assert f["source_values"]["Public"]["total"] == 1098.0
    assert f["mgd"]["total"] == pytest.approx(3.31)
    assert o["counties"]["39161"]["mgd"] == {"irrigation": 0.05, "total": 0.05}
    assert wu.ohio(year=2023, raw=_odnr(), fips=FIPS_OH)["counties"]["39049"]["mgd"]["public_supply"] == 1.0   # 365 days


def test_ohio_unknown_county_fails():
    raw = _odnr()
    raw["facilities"][0]["CountyName"] = "ATLANTIS"
    with pytest.raises(ValueError, match="ATLANTIS"):
        wu.ohio(raw=raw, fips=FIPS_OH)


def test_latest_complete_year_skips_a_partial_year():
    assert wu._latest_complete({2022: 2000, 2023: 2050, 2024: 2040}) == 2024
    assert wu._latest_complete({2022: 2000, 2023: 2050, 2024: 2040, 2025: 300}) == 2024


def test_state_layers():
    assert set(wu.STATE_LAYERS) == {"OH"} and wu.state_layer("WY") is None


def test_days():
    assert wu._days(2024) == 366 and wu._days(2023) == 365
