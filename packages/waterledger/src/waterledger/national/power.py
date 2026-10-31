"""A state's power options outside Michigan: what could supply a campus, each with its water at power plants in gallons per MWh, consumed (gal_mwh, lo, hi)
and withdrawn (wd_gal_mwh, wd_lo, wd_hi). Factors are kept to the gallon: their ranges run tens of percent, and they are quoted as written."""
from waterledger import states
from waterledger_data import energy as en

# EIA balancing authority codes as readers know them
GRID_NAMES = {"ERCO": "ERCOT", "SWPP": "SPP", "MISO": "MISO", "PJM": "PJM", "LGEE": "LG&E and KU", "EPE": "El Paso Electric",
              "PNM": "PNM", "TVA": "TVA", "SOCO": "Southern Company", "DUK": "Duke Energy Carolinas", "CPLE": "Duke Energy Progress",
              "ISNE": "ISO New England", "NYIS": "NYISO", "CISO": "CAISO", "BPAT": "BPA", "SPA": "SPA"}


def grid_name(ba):
    return GRID_NAMES.get(ba, ba)


def options(state, grid_water, order=None):
    """{option: factors}: the state's own mix where its plants' reports allow (energy.state_power_water), then its grid regions (`order`, or as
    `grid_water` lists them), new gas plants, and wind and solar weighted by the state's own generation."""
    name = states.NAMES[state]
    g_ = lambda v: round(v * en.L_KWH_TO_GAL_MWH)
    SW, out = en.state_power_water(state), {}
    if SW:
        out["state_mix"] = {"label": f"{name}'s current mix", "gal_mwh": g_(SW["consumed"]), "lo": g_(SW["consumed_lo"]), "hi": g_(SW["consumed_hi"]),
                            "wd_gal_mwh": g_(SW["withdrawn"]), "wd_lo": g_(SW["withdrawn_lo"]), "wd_hi": g_(SW["withdrawn_hi"]),
                            "sources": ["eia923_2024", "eia_sep2024", "macknick2012", "siddik2024"],
                            "note": f"{SW['consumed']:.2f} L/kWh consumed ({SW['consumed_lo']:.2f} to {SW['consumed_hi']:.2f}) and {SW['withdrawn']:.0f} withdrawn "
                                    f"({SW['withdrawn_lo']:.0f} to {SW['withdrawn_hi']:.0f}): {name}'s plants' 2024 reports to EIA, flagged and missing reports filled with "
                                    f"Macknick factors, updated with 2022 reports" + (f", {round(100 * SW['import_share'])}% imported at the {grid_name(SW['main_ba'])} rate" if SW["import_share"] else "")}
    for b in order or grid_water:
        g, w = g_(grid_water[b]["consumed_excl_hydro"]), g_(grid_water[b]["withdrawn_excl_hydro"])
        out[b.lower()] = {"label": f"{grid_name(b)} grid average", "gal_mwh": g, "lo": g, "hi": g, "wd_gal_mwh": w, "wd_lo": w, "wd_hi": w, "sources": ["siddik2024"],
                          "note": f"{grid_water[b]['consumed_excl_hydro']:.2f} L/kWh consumed and {grid_water[b]['withdrawn_excl_hydro']:.0f} withdrawn, {grid_name(b)} excluding hydropower (2022)"}
    out["new_gas"] = dict(en.NEW_GAS)
    out["renew"] = en.wind_solar(SW["pv_share_of_wind_solar"]) if SW else en.wind_solar(en.state_power_water("MI")["pv_share_of_wind_solar"])
    return out
