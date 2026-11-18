"""Curtailment added back to the fleet checks (design 0014, check 5; Nov 17, 2026: "I don't want anything double counted").

EIA-923's net generation is what plants delivered, so a resource factor fitted to it has the grid's curtailment taken out. A supply scenario
then takes curtailment out again: PV and wind serve the campus first and their surplus is exported with no credit (supply/scenario.py). A
factor fitted to delivered output counted curtailment twice. The checks now add each plant's balancing authority's 2024 curtailment back
to its generation before the factor is fitted, so the scenario's own dispatch is the only place curtailment is counted.

Rates, share of potential generation curtailed in 2024, by EIA-930 balancing authority code:
  solar  Berkeley Lab, U.S. Utility-Scale Solar 2025 Data Update (Seel, Mulvaney Kemp et al.), slide "Solar curtailment varied by region in
         2024": ERCOT 7.1%, CAISO 3.7%, SPP 2.8% [V]. "Most ISOs and regions do not yet report curtailment"; the rest are taken as 0 [A].
  wind   Berkeley Lab, Land-Based Wind Energy Technology Update, 2025 Edition, figure file p. 47, "Wind curtailment and penetration rates by
         ISO": SPP 10.5% (stated) [V]; ERCOT about 4.6%, MISO 3.4%, NYISO 1.1%, CAISO 0.7%, ISO-NE 0.65% read off the bars [F, about
         +/-0.2 points]; PJM's 2024 bar too small to read, 0 [A]. Balancing authorities outside the ISOs report none and are taken as 0 [A].
The annual rate is spread evenly over the months [A]; curtailment is seasonal (spring in Texas and the Southwest), so the monthly tables
still show its shape.
"""
import pandas as pd

RATES = {
    "solar": {"ERCO": 0.071, "CISO": 0.037, "SWPP": 0.028},
    "wind": {"SWPP": 0.105, "ERCO": 0.046, "MISO": 0.034, "NYIS": 0.011, "CISO": 0.007, "ISNE": 0.0065, "PJM": 0.0},
}


def gross(pl, kind, plant_sheet):
    """pl with 'gen' and month columns 1-12 raised to what the plants would have delivered without curtailment, and 'ba' and 'curtailed'
    columns; 'gen_net' keeps EIA-923's delivered figure. plant_sheet: EIA-860's 2___Plant workbook."""
    ba = pd.read_excel(plant_sheet, header=1).set_index("Plant Code")["Balancing Authority Code"]
    out = pl.copy()
    out["ba"] = ba.reindex(out.index).fillna("").astype(str).str.strip()
    out["curtailed"] = out["ba"].map(RATES[kind]).fillna(0.0)
    out["gen_net"] = out["gen"]
    for c in ["gen", *range(1, 13)]:
        if c in out:
            out[c] = out[c] / (1.0 - out["curtailed"])
    return out
