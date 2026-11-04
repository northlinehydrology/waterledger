"""Stations whose record runs under more than one ID (design 0005, Nov 4, 2026): ISD pieces linked by USAF or WBAN, ECCC pieces by place
and name, and the frames read from them. Offline: small hand-written station lists and reports."""
import gzip

import pytest

from waterledger_data import climate

HEAD = '"USAF","WBAN","STATION NAME","CTRY","STATE","ICAO","LAT","LON","ELEV(M)","BEGIN","END"\n'


def _history(tmp_path, rows):
    p = tmp_path / "isd" / "isd-history.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(HEAD + "".join(",".join(f'"{x}"' for x in r) + "\n" for r in rows))


@pytest.fixture
def raw(tmp_path, monkeypatch):
    monkeypatch.setattr(climate, "RAW", str(tmp_path))
    return tmp_path


def test_isd_pieces_sharing_a_usaf_join_into_one_site(raw):
    _history(raw, [
        ("725214", "99999", "LORAIN CO RGNL", "US", "OH", "KLPR", "+41.350", "-082.183", "+0242.0", "19950101", "20051231"),
        ("725214", "04849", "LORAIN COUNTY RGNL AIRPORT", "US", "OH", "KLPR", "+41.346", "-082.179", "+0241.0", "20060101", "20250827"),
        ("725240", "14820", "CLEVELAND-HOPKINS INTERNATIONAL AP", "US", "OH", "KCLE", "+41.406", "-081.852", "+0236.8", "19730101", "20250826"),
    ])
    s = {x["id"]: x for x in climate.isd_sites()}
    assert "parts" not in s["725240-14820"]                                  # spans the period under one ID: as isd_stations gives it
    lorain = s["725214-04849"]
    assert lorain["name"] == "Lorain County Rgnl Airport" and [p["id"] for p in lorain["parts"]] == ["725214-04849", "725214-99999"]


def test_isd_pieces_are_not_joined_far_apart_without_a_wban_or_short_of_the_share(raw):
    _history(raw, [
        ("722540", "13904", "AUSTIN-BERGSTROM", "US", "TX", "", "+30.183", "-097.680", "+0150.0", "19990101", "20250827"),
        ("722540", "13958", "AUSTIN CAMP MABRY", "US", "TX", "", "+30.321", "-097.760", "+0204.0", "19730101", "19971231"),   # same USAF, 17 km
        ("720001", "99999", "AWOS A", "US", "MI", "", "+44.000", "-084.000", "+0300.0", "19900101", "20051231"),
        ("720001", "99999", "AWOS A", "US", "MI", "", "+44.000", "-084.000", "+0300.0", "20060101", "20250827"),               # no WBAN
        ("725384", "99999", "ST CLAIR CO INTL", "US", "MI", "KPHN", "+42.917", "-082.533", "+0198.0", "19940718", "19971231"),
        ("725384", "04888", "ST CLAIR COUNTY INTL ARPT", "US", "MI", "KPHN", "+42.911", "-082.529", "+0195.1", "20060101", "20250825"),  # 1998-2005 missing: 73%
    ])
    assert climate.isd_sites() == []


def _lite(raw, sid, year, rows):
    p = raw / "isd" / "lite" / f"{sid}-{year}.gz"
    p.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(p, "wt") as f:
        for (mo, d, h, t, td) in rows:
            f.write(f"{year} {mo:02d} {d:02d} {h:02d} {t} {td} 0 0 0 0 0 0\n")


def test_a_linked_sites_frame_reads_each_piece_for_its_own_years_newest_first(raw):
    _lite(raw, "725214-04849", 2006, [(1, 1, 0, 50, 10), (1, 1, 1, 60, 20)])
    _lite(raw, "725214-99999", 2005, [(12, 31, 23, 30, -10)])
    _lite(raw, "725214-99999", 2006, [(1, 1, 0, 99, 99), (1, 1, 2, 70, 30)])     # the old ID's overlap: its hour 0 loses to the new ID's
    site = {"id": "725214-04849", "parts": [{"id": "725214-04849", "begin": "20060101", "end": "20250827"},
                                           {"id": "725214-99999", "begin": "19980428", "end": "20061231"}]}
    f = climate._isd_frame(site, [2005, 2006])
    assert list(f.index.strftime("%Y-%m-%d %H")) == ["2006-01-01 00", "2006-01-01 01", "2005-12-31 23", "2006-01-01 02"]
    assert f.loc["2006-01-01 00:00", "T"] == 5.0 and f.loc["2005-12-31 23:00", "Td"] == -1.0


INVENTORY = ['Modified Date: 2026-09-30 23:30 UTC', '"disclaimer"', '"disclaimer"',
             '"Name","Province","Climate ID","Station ID","WMO ID","TC ID","Latitude (Decimal Degrees)","Longitude (Decimal Degrees)","Latitude",'
             '"Longitude","Elevation (m)","First Year","Last Year","HLY First Year","HLY Last Year","DLY First Year","DLY Last Year","MLY First Year","MLY Last Year"']


def _inventory(raw, rows):
    p = raw / "eccc" / "station-inventory.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = [",".join(f'"{x}"' for x in (n, "ONTARIO", cid, "1", "", "", la, lo, "", "", el, "", "", h0, h1, "", "", "", "")) for n, cid, la, lo, el, h0, h1 in rows]
    p.write_text("\n".join(INVENTORY + body) + "\n", encoding="utf-8-sig")


def test_eccc_pieces_at_one_place_with_one_name_join(raw):
    _inventory(raw, [
        ("SARNIA AIRPORT", "6127514", "42.99", "-82.3", "180.6", "1967", "2005"),
        ("SARNIA CHRIS HADFIELD A", "6127518", "43", "-82.31", "181", "2005", "2010"),
        ("SARNIA", "6127510", "43", "-82.31", "181.4", "2009", "2026"),
        ("SARNIA POLYSAR", "6127520", "42.95", "-82.43", "189", "1959", "1973"),             # no hourly years in the period
        ("CORUNNA", "6121234", "42.99", "-82.31", "180", "1990", "2026"),                    # 1 km away, another name: its own site
        ("ERIEAU (AUT)", "613KLLM", "42.25", "-81.9", "178", "1994", "2023"),                 # ends before 2024
    ])
    s = {x["id"]: x for x in climate.eccc_sites()}
    assert set(s) == {"eccc-6127510", "eccc-6121234"}
    assert [p["id"] for p in s["eccc-6127510"]["parts"]] == ["6127510", "6127518", "6127514"]
    assert s["eccc-6127510"]["name"] == "Sarnia" and s["eccc-6127510"]["elev_m"] == 181.4


def test_eccc_frame_leaves_out_missing_values(raw):
    p = raw / "eccc" / "hourly" / "6127514-2000.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("x,y,UTC_DATE,TEMP,TEMP_FLAG,DEW_POINT_TEMP,DEW_POINT_TEMP_FLAG\n"
                 "-82.3,42.99,2000-07-05T10:00:00,13.5,,13.4,\n"
                 "-82.3,42.99,2000-07-05T11:00:00,,M,,M\n"
                 "-82.3,42.99,2000-07-05T12:00:00,14.0,E,12.0,\n"
                 "-82.3,42.99,2000-07-05T13:00:00,15.0,,,M\n")
    f = climate._eccc_frame({"parts": [{"id": "6127514", "begin": "19670101", "end": "20051231"}]}, [2000])
    assert list(f.index.strftime("%H")) == ["10", "12"] and list(f["T"]) == [13.5, 14.0]
