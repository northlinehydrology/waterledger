"""Run the battery cell plant model at the U.S. plants whose DOE environmental assessments project their water, each at its own location and
size at full output, and print the model's 80% range beside the projection (design 0009's check, not a fit: nothing is tuned to these).
Downloads ten years of hourly weather per location on first run (cached in .cache/)."""
from waterledger_models.battery import plant
from waterledger_models.weather import fetch_open_meteo

# name: (lat, lon, GWh/yr, design, the projection in MGD by role, source). Every figure is a projection made before the plant was built.
PLANTS = {
    "Ultium, Delta Twp (Lansing), MI": (42.71, -84.65, 43.75, "towers", {"withdrawn": "1.5-1.7", "consumed": "0.94-1.14", "to_sewer": "0.56"},
                                        "DOE/EA-2189-S1, p. 19"),
    "Ultium, Spring Hill, TN (50 GWh/yr)": (35.75, -86.93, 50.0, "towers", {"withdrawn": "1.4", "withdrawn_peak_1in10": "1.85"},
                                            "DOE/EA-2189, p. 14; size from GM, unverified"),
    "BlueOval SK, Stanton, TN": (35.47, -89.38, 45.0, "towers", {"withdrawn": "1.2", "consumed": "0.87", "to_sewer": "0.33"},
                                 "DOE/EA-2201, p. 22"),
    "BlueOval SK, Glendale, KY": (37.60, -85.90, 82.0, "towers", {"withdrawn": "2.4", "consumed": "1.74", "to_sewer": "0.66"},
                                  "DOE/EA-2201, p. 36"),
    "StarPlus, Kokomo, IN (maximum)": (40.45, -86.10, 67.0, "towers", {"withdrawn_peak_1in10": "2.59"}, "DOE/EA-2263, p. 12"),
    "KORE Power, Buckeye, AZ": (33.40, -112.60, 12.0, "towers", {"withdrawn": "0.45"}, "DOE/EA-2222, p. 8; phase not stated"),
}
STATS = {"withdrawn": "withdrawn_avg", "consumed": "consumed_avg", "to_sewer": "to_sewer_avg", "withdrawn_peak_1in10": "withdrawn_peak_1in10"}

if __name__ == "__main__":
    for name, (lat, lon, gwh, design, ea, source) in PLANTS.items():
        w = fetch_open_meteo(lat, lon, start="2015-01-01", end="2024-12-31", cache=f".cache/{lat}_{lon}_2015.json")
        times = [str(t)[:16] for t in w["time"].values]
        r = plant.run_location(times, w["air_temperature"].values, w["relative_humidity"].values, n=200, gwh=gwh, designs=(design,))[design]
        print(f"{name}, {gwh:g} GWh/yr, {design} ({source})")
        for role, projected in ea.items():
            s = r[STATS[role]]
            print(f"  {role:22s} model {s['p10']:.2f}-{s['p90']:.2f} MGD (median {s['p50']:.2f}); projected {projected}")
