"""Place-by-place tables from model 1.17 runs (in memory on branch model-1.17, saved under runs/model1.17/). p50 per 100 MW of IT. As tables.py, with the outside air design."""
import json, os
S = os.path.dirname(os.path.abspath(__file__))
R = f"{S}/runs/model1.17"
places = [("Grand Rapids, MI", f"{R}/43.00_-85.75.json", "MISO"), ("Loudoun County, VA", f"{R}/39.00_-77.50.json", "PJM"),
          ("Dallas, TX", f"{R}/32.75_-96.75.json", "ERCO"), ("Phoenix, AZ", f"{R}/33.50_-112.00.json", "SRP"), ("Phoenix east, AZ", f"{R}/33.00_-111.25.json", "AZPS")]
P = lambda d, plant: d["per_100mw"] if plant == "shared" else d["per_100mw_plants"][plant]
print("## A. PUE, year average and hottest hour, and power MW per 100 MW IT\n")
print("| Place | Plant | Dry PUE avg | Assist | Hybrid | Towers | Outside air | Dry over towers, avg | Hottest hour MW: dry / assist / hybrid / towers | Dry over towers, hottest hour |")
print("|---|---|---|---|---|---|---|---|---|---|")
for name, f, ba in places:
    if not os.path.exists(f): continue
    d = json.load(open(f, encoding="utf-8"))
    for plant in ("shared", "warm", "chilled"):
        s = P(d, plant); g = lambda des, k: s[des][k]["p50"]
        pa = [g(x, "pue_avg") for x in ("dry", "assist", "hybrid", "towers", "outside_air")]
        pk = [g(x, "power_mw_peak_1in10") for x in ("dry", "assist", "hybrid", "towers")]
        print(f"| {name} | {plant} | {pa[0]:.3f} | {pa[1]:.3f} | {pa[2]:.3f} | {pa[3]:.3f} | {pa[4]:.3f} | {(pa[0]/pa[3]-1)*100:+.1f}% | {pk[0]:.1f} / {pk[1]:.1f} / {pk[2]:.1f} / {pk[3]:.1f} | {pk[0]-pk[3]:+.1f} MW ({(pk[0]/pk[3]-1)*100:+.1f}%) |")
print("\n## B. Campus of 1 GW IT (scaled x10): annual energy, peak capacity, water\n")
print("| Place | Plant | Avg MW dry / towers | Extra GWh a year, dry | Hottest hour MW dry / towers | Extra MW at the hottest hour | Peak-day MW dry / towers | p10-p90 of dry over towers, hottest hour |")
print("|---|---|---|---|---|---|---|---|")
for name, f, ba in places:
    if not os.path.exists(f): continue
    d = json.load(open(f, encoding="utf-8"))
    for plant in ("shared", "warm", "chilled"):
        s = P(d, plant); g = lambda des, k, q="p50": s[des][k][q] * 10
        dm = g("dry", "power_mw_avg") - g("towers", "power_mw_avg")
        print(f"| {name} | {plant} | {g('dry','power_mw_avg'):.0f} / {g('towers','power_mw_avg'):.0f} | {dm*8.76:.0f} | {g('dry','power_mw_peak_1in10'):.0f} / {g('towers','power_mw_peak_1in10'):.0f} | {g('dry','power_mw_peak_1in10')-g('towers','power_mw_peak_1in10'):+.0f} | {g('dry','power_mw_peak_day_1in10'):.0f} / {g('towers','power_mw_peak_day_1in10'):.0f} | p10 {g('dry','power_mw_peak_1in10','p10')-g('towers','power_mw_peak_1in10','p10'):+.0f}, p90 {g('dry','power_mw_peak_1in10','p90')-g('towers','power_mw_peak_1in10','p90'):+.0f} |")
print("\n## C. Water: towers' own vs the power plants' water for dry's extra electricity, MGD per 100 MW IT, average day (peak day in brackets)\n")
print("| Place | BA | Plant | Towers consumed on site | Grid consumed, dry / towers | Dry's extra grid water, average mix | same, marginal mix | Extra as share of towers' own | Grid withdrawn, extra for dry |")
print("|---|---|---|---|---|---|---|---|---|")
for name, f, ba0 in places:
    if not os.path.exists(f): continue
    d = json.load(open(f, encoding="utf-8"))
    for ba in d["grid"]["bas"]:
        for plant in ("shared", "chilled"):
            s = P(d, plant); g = lambda des, k: s[des][k]["p50"]
            if f"grid_{ba}_consumed_avg" not in s["dry"]: continue
            on, onp = g("towers", "consumed_avg"), g("towers", "consumed_peak_1in10")
            gd, gt = g("dry", f"grid_{ba}_consumed_avg"), g("towers", f"grid_{ba}_consumed_avg")
            gdp, gtp = g("dry", f"grid_{ba}_consumed_peak_1in10"), g("towers", f"grid_{ba}_consumed_peak_1in10")
            md = g("dry", f"grid_{ba}_marginal_consumed_avg") - g("towers", f"grid_{ba}_marginal_consumed_avg")
            wd = g("dry", f"grid_{ba}_withdrawn_avg") - g("towers", f"grid_{ba}_withdrawn_avg")
            print(f"| {name} | {ba} | {plant} | {on:.3f} ({onp:.3f}) | {gd:.3f} / {gt:.3f} | {gd-gt:+.3f} ({gdp-gtp:+.3f}) | {md:+.3f} | {(gd-gt)/on*100:.1f}% ({(gdp-gtp)/onp*100:.1f}%) | {wd:+.2f} |")
