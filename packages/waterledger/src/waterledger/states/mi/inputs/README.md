# Michigan's hand-kept inputs

`egle_water_use_<year>.csv`: EGLE's yearly reported water use by facility, with facility names removed, since some are individual farms. EGLE's site refuses scripted downloads, so each year's file is downloaded by hand and reduced:

    python -m waterledger.states.mi.egle egle_water_use_facility_2025.xlsx packages/waterledger/src/waterledger/states/mi/inputs/egle_water_use_2025.csv

`Golf` is 1 for irrigation facilities whose names mark them as golf or country clubs, worked out before the names are removed. The newest year here is what Michigan's build reads.
