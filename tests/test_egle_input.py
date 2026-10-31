"""Michigan's EGLE input carries no facility names, and the build reads it."""
import csv
import pathlib

from waterledger.states.mi.egle import COLUMNS

HERE = pathlib.Path(__file__).parent.parent / "data" / "inputs" / "mi"


def test_no_names_in_the_committed_file():
    for path in HERE.glob("egle_water_use_*.csv"):
        with open(path, newline="") as f:
            rows = csv.DictReader(f)
            assert rows.fieldnames == COLUMNS
            assert "Facility" not in rows.fieldnames and "SubFacility" not in rows.fieldnames
