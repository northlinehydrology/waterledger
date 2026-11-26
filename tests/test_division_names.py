"""NOAA's own names for climate divisions (design 0011, for every state), from NOAA's division map."""
from waterledger_data import divisions


def test_noaa_names():
    assert divisions.division_name("2008", "MI") == "Southwest Lower"
    assert divisions.division_name("2002", "MI") == "East Upper"
    assert divisions.division_name("4404", "VA") == "Northern"


def test_every_contiguous_division_is_named_once():
    import csv
    rows = list(csv.DictReader(open(divisions.NAMES_FILE, encoding="utf-8")))
    assert len(rows) == 344 and len({r["division"] for r in rows}) == 344 and all(r["name"] for r in rows)


def test_a_division_not_in_the_table_keeps_the_old_label():
    assert divisions.division_name("5099", "AK") == "AK climate division 99"
