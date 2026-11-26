"""Michigan's EGLE input carries no facility names, and the water-use layer reads it."""
import csv
import pathlib

from waterledger_data.egle import COLUMNS

HERE = pathlib.Path(__file__).parent.parent / "packages" / "waterledger-data" / "src" / "waterledger_data" / "tables"


def test_no_names_in_the_committed_file():
    for path in HERE.glob("egle_water_use_*.csv"):
        with open(path, encoding="utf-8", newline="") as f:
            rows = csv.DictReader(f)
            assert rows.fieldnames == COLUMNS
            assert "Facility" not in rows.fieldnames and "SubFacility" not in rows.fieldnames


def test_the_committed_file_is_there():
    assert list(HERE.glob("egle_water_use_*.csv"))
