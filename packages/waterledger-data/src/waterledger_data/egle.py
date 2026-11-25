"""Reduce EGLE's yearly facility water-use file to what Michigan's water-use layer (wateruse.michigan) needs, with facility names removed.

    python -m waterledger_data.egle egle_water_use_facility_2025.xlsx packages/waterledger-data/src/waterledger_data/tables/egle_water_use_2025.csv

Golf courses are irrigation facilities whose names mark them as golf or country clubs, so that flag is worked out here, while the names are at hand.
"""
import os, sys

import pandas as pd

GOLF = r"golf|country club|\bC\.?C\.?\b|links"
COLUMNS = ["County", "Purpose", "Golf", "Gallons from Great Lakes", "Gallons from Inland Surface Water", "Gallons from Groundwater", "Total Gallons", "Year"]


def reduce(path, out):
    df = pd.read_excel(path, sheet_name="Sheet1")
    df["Golf"] = ((df["Purpose"] == "Irrigation") & df["Facility"].astype(str).str.contains(GOLF, case=False, regex=True)).astype(int)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    df[COLUMNS].to_csv(out, index=False)
    return out


if __name__ == "__main__":
    print(reduce(sys.argv[1], sys.argv[2]))
