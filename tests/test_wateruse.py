"""County water use (waterledger_data.wateruse): each layer's arithmetic, category mapping and basis, on small fixtures."""
import json, math

import pytest

from waterledger_data import wateruse as wu

FIPS_OH = {"Franklin County": "39049", "FRANKLIN": "39049", "Van Wert County": "39161", "VAN WERT": "39161"}
FIPS_TX = {"Travis County": "48453", "TRAVIS": "48453"}
FIPS_VA = {"Loudoun County": "51107", "LOUDOUN": "51107", "Richmond city": "51760", "RICHMOND CITY": "51760",
           "Richmond County": "51159", "RICHMOND": "51159", "Bedford County": "51019", "BEDFORD": "51019"}


def test_categories_are_fixed():
    assert wu.CATEGORIES[-1] == "total" and len(set(wu.CATEGORIES)) == len(wu.CATEGORIES)
    assert set(wu.USGS_CATS) | {"other", "total"} == set(wu.CATEGORIES)
    assert set(wu.OHIO_CATS.values()) <= set(wu.CATEGORIES)
    assert {c for c, _ in wu.TWDB_CATS.values()} <= set(wu.CATEGORIES)


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


TWDB_CSV = (
    '﻿RWP27DraftDataTimestamp,Year,CountyName,Population,Municipal,Manufacturing,Mining,Power,Irrigation,LiveStock,'
    'Muni_GW,Muni_SW,Muni_RU,MFG_Gw,MFG_SW,MFG_RU,Mining_GW,Mining_SW,Mining_RU,Power_GW,Power_SW,Power_RU,Irrig_GW,Irrig_SW,Irrig_RU,'
    'Livestock_GW,Livestock_SW,Livestock_RU,Year1,Population1\n'
    '"10/29/2026 9:32:46 PM \nRevised as Additional or More Accurate Data Becomes Available\nReport FileName: SumFinal_CountyrReportWithReuse",'
    '2024,TRAVIS,"1,363,767","209,045","15,409",133,"1,909","1,758",467,"19,511","184,052","5,482",586,"12,243","2,580",0,133,0,'
    '114,417,"1,378","1,672",86,0,93,374,0,2024,"31,290,831"\n')


def test_texas_converts_acre_feet(tmp_path):
    p = tmp_path / "county_2024_2026-10-29.csv"
    p.write_text(TWDB_CSV, encoding="utf-8")
    t = wu.texas(path=str(p), fips=FIPS_TX)
    b = t["basis"]
    assert (b["year"], b["kind"], b["measure"], b["retrieved"]) == (2024, "estimate", "use", "2026-10-29")
    r = t["counties"]["48453"]
    assert r["source_values"]["Municipal"] == {"total": 209045, "ground": 19511, "surface": 184052, "reuse": 5482}
    assert r["source_values"]["Total"]["total"] == 228721
    mgd = lambda af: af * 325851.429 / 1e6 / 366
    assert r["mgd"]["public_supply"] == pytest.approx(mgd(209045), abs=1e-3)
    assert r["mgd"]["total"] == pytest.approx(mgd(228721), abs=5e-3)
    assert r["ground_mgd"]["industrial"] == pytest.approx(mgd(586), abs=1e-3)       # TWDB's MFG_Gw header
    assert r["reuse_mgd"]["thermoelectric"] == pytest.approx(mgd(1378), abs=1e-3)
    assert r["population"] == 1363767
    with pytest.raises(ValueError, match="not 2023"):
        wu.texas(year=2023, path=str(p), fips=FIPS_TX)


def test_virginia_localities_and_former_cities():
    table = {"year": 2024, "url": "u", "retrieved": "2026-10-30", "pdf_sha256": "x",
             "rows": [["Loudoun County", 1.59, 15.61, 17.19], ["City of Richmond", 0.02, 69.72, 69.75], ["Richmond County", 0.32, 0.0, 0.32],
                      ["City of Bedford", 1.3, 17.84, 19.14], ["Bedford County", 0.0, 0.0, 0.0]]}
    v = wu.virginia(table=table, fips=FIPS_VA)
    C = v["counties"]
    assert v["basis"]["kind"] == "reported" and v["basis"]["year"] == 2024
    assert C["51107"]["mgd"] == {"total": 17.19} and C["51107"]["ground_mgd"] == {"total": 1.59}
    assert C["51760"]["name"] == "Richmond city" and C["51760"]["mgd"]["total"] == 69.75
    assert C["51159"]["mgd"]["total"] == 0.32
    assert C["51019"]["mgd"]["total"] == 19.14 and set(C["51019"]["source_values"]) == {"City of Bedford", "Bedford County"}
    with pytest.raises(ValueError, match="Atlantis"):
        wu.virginia(table={**table, "rows": [["City of Atlantis", 0, 0, 0]]}, fips=FIPS_VA)


def test_virginia_table_read_from_a_pdf(tmp_path):
    """Table 21 as pypdf reads DEQ's report (the Total row's word may come out split)."""
    canvas = pytest.importorskip("reportlab.pdfgen.canvas")             # a dev dependency, not in the published wheels' tests
    pdf = str(tmp_path / "report.pdf")
    c = canvas.Canvas(pdf)
    c.drawString(40, 800, "Some other page")
    c.showPage()
    lines = ["Table 21: Water Withdrawals Within Localities in 2024 (MGD)",
             "Locality GW Withdrawal SW Withdrawal GW + SW Total Percent of Total Withdrawal"]
    rows = [(f"Locality {i} County", 0.10, 1.00, 1.10, 0.5) for i in range(120)] + [("City of Richmond", 0.02, 69.72, 69.75, 5.46)]
    lines += [f"{n} {g:.2f} {s:.2f} {t:.2f} {p:.2f}" for n, g, s, t, p in rows]
    lines += [f"T otal {sum(r[1] for r in rows):.2f} {sum(r[2] for r in rows):.2f} {sum(r[3] for r in rows):.2f} 100.00"]
    y = 800
    for line in lines:
        c.drawString(40, y, line)
        y -= 12
        if y < 40:
            c.showPage()
            y = 800
    c.save()
    got, total, year = wu.va_table21_rows(pdf)
    assert year == 2024 and len(got) == 121 and got[-1] == ("City of Richmond", 0.02, 69.72, 69.75)
    assert total[1] == pytest.approx(sum(r[2] for r in rows))


def test_state_layers():
    assert set(wu.STATE_LAYERS) == {"OH", "TX", "VA"} and wu.state_layer("WY") is None


def test_snapshot_water_use_reads_and_prefers_the_state(tmp_path, monkeypatch):
    """The provider takes a county's figures from the state's layer when the snapshot has one, else USGS's; a format 1
    snapshot (before water use) gives none."""
    from waterledger.national import data, provider
    basis = lambda src, kind: {"source": src, "citation": src, "year": 2024, "kind": kind, "measure": "withdrawals", "units": "Mgal/d"}
    W = {"format": 1, "national": {"basis": {**basis("usgs_wu2015", "estimate"), "year": 2015}, "counties": {
             "39049": {"name": "Franklin County", "mgd": {"public_supply": 155.82, "total": 188.31}, "delivered_to_homes_mgd": 63.89},
             "39001": {"name": "Adams County", "mgd": {"total": 2.0}}}},
         "state": {"basis": basis("odnr_wwfr", "reported"), "counties": {"39049": {"name": "Franklin County", "mgd": {"total": 252.571}}}}}
    folder = tmp_path / "OH" / "2000-01-01"
    folder.mkdir(parents=True)
    (folder / "wateruse.json").write_text(json.dumps(W))
    (folder / "manifest.json").write_text(json.dumps({"date": "2000-01-01", "files": {"wateruse.json": {}}}))
    sd = data.SnapshotData("OH", str(folder))
    monkeypatch.setattr(provider, "state_data", lambda st: sd)
    use, usgs = provider.county_water_use("OH", "39049")
    assert (use.source, use.kind, use.mgd["total"]) == ("odnr_wwfr", "reported", 252.571)
    assert (usgs.year, usgs.kind, usgs.delivered_to_homes_mgd) == (2015, "estimate", 63.89)
    use, usgs = provider.county_water_use("OH", "39001")
    assert use == usgs and use.source == "usgs_wu2015"
    (folder / "manifest.json").write_text(json.dumps({"date": "2000-01-01", "files": {}}))
    old = data.SnapshotData("OH", str(folder))
    monkeypatch.setattr(provider, "state_data", lambda st: old)
    assert provider.county_water_use("OH", "39049") == (None, None)


def test_days():
    assert wu._days(2024) == 366 and wu._days(2023) == 365 and math.isclose(wu.GAL_PER_ACRE_FOOT, 325851.429)
