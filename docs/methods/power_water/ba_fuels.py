"""Power-plant water per MWh by balancing authority, EIA-930 fuel class and month, 2024 (design 0007, part 1, step 2).

Inputs (read-only, in $WL_POWER_WORK as for states.py; run states.py first):
  out/plants_2024.csv          each plant's 2024 water, as reported and adjusted (states.py)
  detail_all.pkl               EIA cooling water detail, 2024 (states.py caches it)
  dl/f923/EIA923_Schedules_2_3_4_5_M_12_2024_Final.xlsx, Page 1: monthly net generation by plant and fuel, with each
                               plant's balancing authority (https://www.eia.gov/electricity/data/eia923/)
Output: packages/waterledger-data/src/waterledger_data/tables/ba_fuel_water_2024.csv

Method
  plant water by month   = the plant's adjusted 2024 water (states.py) x its month's share of its reported water, or of
                           its cooled generation where it reported none (a plant whose water was replaced)
  by fuel class          = each plant-month's water split across EIA-930's thermal classes (coal, gas, oil, nuclear,
                           geothermal, other) by that month's net generation by fuel (EIA-923); a month with none uses
                           the plant's year
  generation             = all of a class's net generation in the BA and month (EIA-923), plants with no water included,
                           so a gas factor carries the combustion turbines that use none
  factor                 = water / generation, gal/MWh; basis "month". A month whose class generation is under a quarter
                           of the class's monthly mean, or not positive, takes the BA's annual factor (basis "year"); a
                           class with no generation in the BA takes the U.S. factor for the class (ba "US", basis "us")
  hydro, solar, wind, storage: 0 (reservoir evaporation is not counted, as in the state table)
  withdrawal at least consumption, plant by plant [A]: three plants report consumption with no withdrawal (Stanton,
                           FL; Kings Mountain, NC; Ingleside Cogeneration, TX), most likely reclaimed or utility water that
                           EIA's withdrawal leaves out. The state table keeps their withdrawal at zero; this one doesn't
  a month's factors x the BA's EIA-923 generation give back the BA's plant water, apart from the fallbacks: checked here
"""
import os

import numpy as np
import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
D = os.environ.get('WL_POWER_WORK', os.path.join(H, 'work'))
OUT = os.path.join(H, '..', '..', '..', 'packages', 'waterledger-data', 'src', 'waterledger_data', 'tables', 'ba_fuel_water_2024.csv')
W, C = 'Water Withdrawal Volume (Million Gallons)', 'Water Consumption Volume (Million Gallons)'
GEN = ['Net Generation from Steam Turbines (MWh)', 'Net Generation Associated with Single Shaft Combined Cycle Units (MWh)',
       'Net Generation Associated with Combined Cycle Gas Turbines (MWh)']
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
THERMAL = ('coal', 'gas', 'oil', 'nuclear', 'geothermal', 'other')
NO_WATER = ('hydro', 'solar', 'wind', 'storage')
# EIA-923 fuel codes -> EIA-930 classes (EIA-930 counts petroleum coke as petroleum and other gases as other)
FUEL = {**dict.fromkeys(['BIT', 'SUB', 'LIG', 'ANT', 'RC', 'WC', 'SGC', 'SC'], 'coal'), 'NG': 'gas',
        **dict.fromkeys(['DFO', 'RFO', 'JF', 'KER', 'WO', 'PC', 'RG'], 'oil'), 'NUC': 'nuclear', 'WAT': 'hydro',
        'SUN': 'solar', 'WND': 'wind', 'GEO': 'geothermal', 'MWH': 'storage'}


def fuel_class(code):
    return FUEL.get(str(code).strip(), 'other')


def generation():
    x = pd.read_excel(os.path.join(D, 'dl', 'f923', 'EIA923_Schedules_2_3_4_5_M_12_2024_Final.xlsx'),
                      sheet_name='Page 1 Generation and Fuel Data', header=5)
    x.columns = [' '.join(str(c).split()) for c in x.columns]
    net = [f'Netgen {m}' for m in MONTHS]
    x = x[['Plant Id', 'Balancing Authority Code', 'Reported Fuel Type Code', *net]].copy()
    x['fuel'] = x['Reported Fuel Type Code'].map(fuel_class)
    long = x.melt(id_vars=['Plant Id', 'Balancing Authority Code', 'fuel'], value_vars=net, var_name='m', value_name='mwh')
    long['month'] = long['m'].str.split().str[1].map({m: i + 1 for i, m in enumerate(MONTHS)})
    long['mwh'] = pd.to_numeric(long['mwh'], errors='coerce').fillna(0.0)
    return long.rename(columns={'Plant Id': 'plant', 'Balancing Authority Code': 'ba'})[['plant', 'ba', 'fuel', 'month', 'mwh']]


def plant_months():
    """Adjusted 2024 water by plant and month: consumed, withdrawn, withdrawn saline (MG)."""
    p = pd.read_csv(os.path.join(D, 'out', 'plants_2024.csv')).rename(columns={'Plant Code': 'plant'})
    d = pd.read_pickle(os.path.join(D, 'detail_all.pkl'))
    d['month'] = pd.to_numeric(d['Month'], errors='coerce')
    for c in [W, C] + GEN:
        d[c] = pd.to_numeric(d[c], errors='coerce').fillna(0.0)
    wtr = d.drop_duplicates(['Plant Code', 'Cooling ID', 'Month']).groupby(['Plant Code', 'month'])[W].sum()
    gen = d.drop_duplicates(['Plant Code', 'Generator ID', 'Month']).assign(net=lambda t: t[GEN].sum(axis=1)) \
           .groupby(['Plant Code', 'month']).net.sum()
    wtr = {k: v.droplevel(0) for k, v in wtr.groupby(level=0)}
    gen = {k: v.droplevel(0) for k, v in gen.groupby(level=0)}
    rows = []
    for r in p.itertuples():
        shape = wtr.get(r.plant)
        if shape is None or shape.clip(lower=0).sum() <= 0:
            shape = gen.get(r.plant)
        if shape is None or shape.clip(lower=0).sum() <= 0:
            shape = pd.Series(1.0, index=range(1, 13))
        shape = shape.clip(lower=0).reindex(range(1, 13), fill_value=0.0)
        shape = shape / shape.sum()
        wd = max(r.wd_adj, r.cons_adj)      # [A] a plant reporting consumption with no withdrawal took at least that much
        for m, s in shape.items():
            rows.append((r.plant, m, r.cons_adj * s, wd * s, r.wd_saline_adj * s, r.tech))
    return pd.DataFrame(rows, columns=['plant', 'month', 'cons', 'wd', 'wd_saline', 'tech'])


TECH_CLASS = {'coal': 'coal', 'ngcc': 'gas', 'gas_steam': 'gas', 'nuclear': 'nuclear', 'bio': 'other', 'csp': 'other'}


def main():
    g = generation()
    pm = plant_months()
    ba_of = g.groupby('plant').ba.agg(lambda v: v.mode().iat[0] if v.notna().any() else None)

    # split each plant-month's water across thermal classes by that month's generation, else the plant's year
    th = g[g.fuel.isin(THERMAL) & (g.mwh > 0)]
    by_m = {k: v.droplevel([0, 1]) for k, v in th.groupby(['plant', 'month', 'fuel']).mwh.sum().groupby(level=[0, 1])}
    by_y = {k: v.droplevel(0) for k, v in th.groupby(['plant', 'fuel']).mwh.sum().groupby(level=0)}
    parts = []
    for r in pm.itertuples():
        sh = by_m.get((r.plant, r.month))
        if sh is None:
            sh = by_y.get(r.plant)
        if sh is None:
            sh = pd.Series({TECH_CLASS.get(r.tech, 'other'): 1.0})
        sh = sh / sh.sum()
        for f, s in sh.items():
            parts.append((r.plant, ba_of.get(r.plant), f, r.month, r.cons * s, r.wd * s, r.wd_saline * s))
    w = pd.DataFrame(parts, columns=['plant', 'ba', 'fuel', 'month', 'cons', 'wd', 'wd_saline'])
    unmatched = w[w.ba.isna()]
    print(f"plant water with no EIA-923 BA: {unmatched.wd.sum():.0f} MG withdrawn of {w.wd.sum():.0f}")

    wm = w.dropna(subset=['ba']).groupby(['ba', 'fuel', 'month'])[['cons', 'wd', 'wd_saline']].sum()
    gm = g.dropna(subset=['ba']).groupby(['ba', 'fuel', 'month']).mwh.sum()
    t = pd.concat([gm, wm], axis=1).fillna(0.0).reset_index()

    gpm = lambda mg, mwh: mg * 1e6 / mwh
    rows = []
    us = t[t.fuel.isin(THERMAL)].groupby('fuel')[['mwh', 'cons', 'wd', 'wd_saline']].sum()
    for (ba, fuel), grp in t.groupby(['ba', 'fuel']):
        yr = grp[['mwh', 'cons', 'wd', 'wd_saline']].sum()
        if fuel in NO_WATER:
            for m in range(1, 13):
                mwh = grp.loc[grp.month == m, 'mwh'].sum()
                rows.append((ba, fuel, m, mwh, 0.0, 0.0, 0.0, 'none'))
            continue
        for m in range(1, 13):
            row = grp[grp.month == m]
            mwh = row.mwh.sum()
            if mwh > 0.25 * yr.mwh / 12 and mwh > 0:
                src, basis = row[['mwh', 'cons', 'wd', 'wd_saline']].sum(), 'month'
            elif yr.mwh > 0:
                src, basis = yr, 'year'
            else:
                src, basis = us.loc[fuel] if fuel in us.index else None, 'us'
            if src is None or src.mwh <= 0:
                rows.append((ba, fuel, m, mwh, np.nan, np.nan, np.nan, 'missing'))
                continue
            rows.append((ba, fuel, m, mwh, gpm(src.cons, src.mwh), gpm(src.wd, src.mwh), gpm(src.wd_saline, src.mwh), basis))
    for fuel, src in us.iterrows():
        rows.append(('US', fuel, 0, src.mwh, gpm(src.cons, src.mwh), gpm(src.wd, src.mwh), gpm(src.wd_saline, src.mwh), 'us'))
    out = pd.DataFrame(rows, columns=['ba', 'fuel', 'month', 'gen_mwh', 'consumed_gal_mwh', 'withdrawn_gal_mwh',
                                      'withdrawn_saline_gal_mwh', 'basis'])
    out = out.round({'gen_mwh': 0, 'consumed_gal_mwh': 2, 'withdrawn_gal_mwh': 2, 'withdrawn_saline_gal_mwh': 2})
    out.to_csv(OUT, index=False)

    # check: factors x generation give back each BA's plant water
    chk = out[out.ba != 'US'].assign(c=lambda o: o.consumed_gal_mwh.fillna(0) * o.gen_mwh / 1e6,
                                     wdr=lambda o: o.withdrawn_gal_mwh.fillna(0) * o.gen_mwh / 1e6).groupby('ba')[['c', 'wdr']].sum()
    got = wm.groupby('ba')[['cons', 'wd']].sum()
    j = chk.join(got, how='outer').fillna(0.0)
    j['cons_ratio'] = j.c / j.cons.where(j.cons > 0)
    j['wd_ratio'] = j.wdr / j.wd.where(j.wd > 0)
    pd.set_option('display.width', 200, 'display.max_rows', 100)
    print(j.sort_values('wd', ascending=False).round(3).head(25).to_string())
    print(out[(out.ba == 'MISO') & out.fuel.isin(THERMAL)].pivot_table(index='month', columns='fuel', values='consumed_gal_mwh').round(0).to_string())
    print(out.basis.value_counts().to_string())


if __name__ == '__main__':
    main()
