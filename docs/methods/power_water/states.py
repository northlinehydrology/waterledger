"""Statewide power-plant water per MWh of each state's 2024 net generation, from EIA's 2024 thermoelectric cooling
water data (EIA-923 Schedule 8D, detail file), with plant flags and a Macknick-filled adjusted case.

Inputs (read-only):
  eia_cooling_detail_2024.xlsx ($WL_EIA_COOLING_DETAIL, or <work>/; cached as <work>/detail_all.pkl)
  <work>/dl/api/state_gen_2024.json     EIA API v2 electric-power-operational-data, all sectors, annual 2024
  <work>/dl/api/facility_gen_2024.json  EIA API v2 facility-fuel, fuel ALL, prime mover ALL, annual 2024
Outputs: <work>/out/states_2024.csv, <work>/out/plants_2024.csv

Method
  water per plant  = sum over unique (plant, cooling ID, month) rows (the detail file repeats cooling-system water on every
                     generator row, and repeats plant-level 'PLANT' water across generators)
  cooled gen       = sum over unique (plant, generator ID, month) of steam + single-shaft CC + CC gas turbine net generation;
                     if zero while water is reported, the plant's total 2024 net generation (facility-fuel API) is used
  cooling class    = cooling type carrying most of the plant's withdrawal (ON/OC -> once-through, RC -> pond,
                     RI/RN/RF -> tower, DC -> dry, HRI -> hybrid)
  flags            = cons > withdrawal; cons > 1,500 gal/MWh; cons == 0 for once-through or pond with withdrawal > 0;
                     withdrawal > 25,000 gal/MWh for tower or pond (recirculation reported as withdrawal);
                     water reported with no generation anywhere
  adjusted         = flagged consumption (and flagged recirculating withdrawal) replaced by Macknick et al. 2012 median
                     (Table 2 consumption, Table 3 withdrawal) for the plant's technology and cooling class x cooled gen
  bottom-up        = Macknick median for every reporting plant's technology/cooling x its cooled gen
  intensity        = state totals / state 2024 net generation (all sources, EIA)
"""
import json, os
import numpy as np
import pandas as pd

H = os.path.dirname(os.path.abspath(__file__))
D = os.environ.get('WL_POWER_WORK', os.path.join(H, 'work'))
L_PER_GAL = 3.78541
W, C = 'Water Withdrawal Volume (Million Gallons)', 'Water Consumption Volume (Million Gallons)'
GEN = ['Net Generation from Steam Turbines (MWh)', 'Net Generation Associated with Single Shaft Combined Cycle Units (MWh)',
       'Net Generation Associated with Combined Cycle Gas Turbines (MWh)']

# Macknick et al. 2012 medians, gal/MWh: (consumption Table 2/1, withdrawal Table 3). [A] marks a stand-in.
MK = {
    ('nuclear', 'once'): (269, 44350), ('nuclear', 'tower'): (672, 1101), ('nuclear', 'pond'): (610, 7050),
    ('coal', 'once'): (250, 36350), ('coal', 'tower'): (687, 1005), ('coal', 'pond'): (545, 12225),
    ('ngcc', 'once'): (100, 11380), ('ngcc', 'tower'): (205, 255), ('ngcc', 'pond'): (240, 5950), ('ngcc', 'dry'): (2, 2),
    ('gas_steam', 'once'): (240, 35000), ('gas_steam', 'tower'): (826, 1203), ('gas_steam', 'pond'): (545, 12225),  # pond [A] coal pond
    ('bio', 'once'): (300, 35000), ('bio', 'tower'): (553, 878), ('bio', 'pond'): (390, 450), ('bio', 'dry'): (35, 35),
    ('coal', 'dry'): (2, 2), ('gas_steam', 'dry'): (2, 2), ('nuclear', 'dry'): (2, 2),   # [A] dry ~ NGCC dry
}
TECH = {'Natural Gas Fired Combined Cycle': 'ngcc', 'Conventional Steam Coal': 'coal', 'Natural Gas Steam Turbine': 'gas_steam',
        'Wood/Wood Waste Biomass': 'bio', 'Nuclear': 'nuclear', 'Petroleum Liquids': 'gas_steam', 'Other Gases': 'gas_steam',
        'Other Waste Biomass': 'bio', 'Petroleum Coke': 'coal', 'Municipal Solid Waste': 'bio',
        'Coal Integrated Gasification Combined Cycle': 'coal', 'Natural Gas Fired Combustion Turbine': 'ngcc', 'All Other': 'gas_steam',
        'Solar Thermal without Energy Storage': 'csp', 'Solar Thermal with Energy Storage': 'csp'}
COOL = {'ON': 'once', 'OC': 'once', 'RC': 'pond', 'RI': 'tower', 'RN': 'tower', 'RF': 'tower', 'DC': 'dry', 'HR': 'tower', 'OT': 'tower'}


def factor(tech, cool):
    if tech == 'csp':
        return (906, 906) if cool != 'dry' else (78, 78)        # Macknick Table 1, trough tower / dry
    return MK.get((tech, cool), MK.get(('ngcc' if tech == 'ngcc' else tech, 'tower'), (205, 255)))


def num(s):
    return pd.to_numeric(s, errors='coerce').fillna(0.0)


def main():
    pkl = os.path.join(D, 'detail_all.pkl')
    if not os.path.exists(pkl):     # EIA's thermoelectric cooling water data, 2024 detail file (https://www.eia.gov/electricity/data/water/)
        x = pd.read_excel(os.environ.get('WL_EIA_COOLING_DETAIL', os.path.join(D, 'eia_cooling_detail_2024.xlsx')), header=2)
        x.columns = [str(c).strip() for c in x.columns]
        os.makedirs(D, exist_ok=True)
        x.to_pickle(pkl)
    d = pd.read_pickle(pkl)
    d['Month'] = d['Month'].astype(str)
    for c in [W, C] + GEN:
        d[c] = num(d[c])
    d['code'] = d['860 Cooling Type 1'].astype(str).str.extract(r'\((\w+)\)')[0].str[:2]
    d['cool'] = d['code'].map(COOL)
    d['tech'] = d['Generator Primary Technology'].map(TECH)
    d['net'] = d[GEN].sum(axis=1)

    wtr = d.drop_duplicates(['Plant Code', 'Cooling ID', 'Month'])
    gen = d.drop_duplicates(['Plant Code', 'Generator ID', 'Month'])
    wt = d[d['Water Type'].notna()].drop_duplicates('Plant Code').set_index('Plant Code')['Water Type']
    wtr = wtr.assign(**{'Water Type': wtr['Water Type'].fillna(wtr['Plant Code'].map(wt))})
    wtr = wtr.assign(wd_fresh=np.where(wtr['Water Type'].astype(str).eq('Fresh'), wtr[W], 0.0),
                     cons_fresh=np.where(wtr['Water Type'].astype(str).eq('Fresh'), wtr[C], 0.0))
    pw = wtr.groupby(['State', 'Plant Code', 'Plant Name']).agg(wd=(W, 'sum'), cons=(C, 'sum'), wd_fresh=('wd_fresh', 'sum'),
                                                                cons_fresh=('cons_fresh', 'sum'),
                                                                water_type=('Water Type', lambda v: '/'.join(sorted(set(map(str, v)))))).reset_index()
    pg = gen.groupby('Plant Code').agg(cooled_gen=('net', 'sum')).reset_index()
    # cooling class: by withdrawal per cooling type where known, else most common among rows
    ct = d[d.cool.notna()].groupby(['Plant Code', 'cool']).agg(w=(W, 'sum'), n=('cool', 'size')).reset_index()
    ct = ct.sort_values(['Plant Code', 'w', 'n'], ascending=[True, False, False]).drop_duplicates('Plant Code')[['Plant Code', 'cool']]
    tg = gen.groupby(['Plant Code', 'tech']).agg(g=('net', 'sum'), n=('tech', 'size')).reset_index()
    tg = tg.sort_values(['Plant Code', 'g', 'n'], ascending=[True, False, False]).drop_duplicates('Plant Code')[['Plant Code', 'tech']]
    p = pw.merge(pg, on='Plant Code', how='left').merge(ct, on='Plant Code', how='left').merge(tg, on='Plant Code', how='left')

    fac = pd.DataFrame(json.load(open(os.path.join(D, 'dl', 'api', 'facility_gen_2024.json'))))
    fac['generation'] = pd.to_numeric(fac['generation'], errors='coerce')
    fac = fac.groupby('plantCode').generation.sum()
    p['plant_gen'] = p['Plant Code'].astype(str).map(fac).fillna(0.0)
    p['gen_basis'] = np.where(p.cooled_gen > 0, p.cooled_gen, p.plant_gen)
    p = p[(p.wd > 0) | (p.cons > 0) | (p.gen_basis > 0)].copy()
    p['wd_gpm'] = np.where(p.gen_basis > 0, p.wd * 1e6 / p.gen_basis, np.nan)
    p['c_gpm'] = np.where(p.gen_basis > 0, p.cons * 1e6 / p.gen_basis, np.nan)

    flags, cons_adj, wd_adj, cons_bu, wd_bu = [], [], [], [], []
    for r in p.itertuples():
        f = []
        mc, mw = factor(r.tech, r.cool)
        g = max(r.gen_basis, 0.0)
        if r.cons > r.wd * 1.001 and r.wd > 0:
            f.append('cons>withdrawal')
        if r.c_gpm == r.c_gpm and r.c_gpm > 1500:
            f.append('cons>1500gal/MWh')
        if r.cons == 0 and r.wd > 0 and r.cool in ('once', 'pond'):
            f.append(f'zero cons ({r.cool})')
        if r.wd_gpm == r.wd_gpm and r.cool in ('tower', 'pond') and r.wd_gpm > 25000:
            f.append(f'withdrawal>{25000} gal/MWh ({r.cool})')
        if g == 0 and (r.wd > 0 or r.cons > 0):
            f.append('water, no generation')
        flags.append('; '.join(f))
        bad_c = any(x.startswith(('cons>', 'zero cons')) for x in f)
        bad_w = any(x.startswith('withdrawal>') for x in f)
        ca = mc * g / 1e6 if bad_c else r.cons
        wa = mw * g / 1e6 if bad_w else r.wd
        cons_adj.append(min(ca, wa) if wa > 0 else ca)
        wd_adj.append(wa)
        cons_bu.append(mc * g / 1e6)
        wd_bu.append(mw * g / 1e6)
    p['flag'], p['cons_adj'], p['wd_adj'], p['cons_bu'], p['wd_bu'] = flags, cons_adj, wd_adj, cons_bu, wd_bu

    sg = pd.DataFrame(json.load(open(os.path.join(D, 'dl', 'api', 'state_gen_2024.json'))))
    sg['generation'] = pd.to_numeric(sg['generation'], errors='coerce') * 1000.0     # thousand MWh -> MWh
    piv = sg.pivot_table(index='location', columns='fueltypeid', values='generation', aggfunc='sum')
    rows = []
    for st, g in p.groupby('State'):
        if st not in piv.index:
            continue
        tot = piv.loc[st, 'ALL']
        gpm = lambda mg: mg * 1e6 / tot
        lk = lambda mg: mg * 1e6 / tot * L_PER_GAL / 1000
        wind = piv.loc[st].get('WND', np.nan); sun = piv.loc[st].get('SUN', np.nan); dpv = piv.loc[st].get('DPV', np.nan)
        fl = g[g['flag'] != '']
        rows.append({
            'state': st, 'net_gen_mwh_2024': round(tot), 'cooled_gen_reporting_mwh': round(g.gen_basis.sum()),
            'wind_mwh': round(np.nan_to_num(wind)), 'solar_utility_mwh': round(np.nan_to_num(sun)), 'solar_small_est_mwh': round(np.nan_to_num(dpv)),
            'wind_share': round(np.nan_to_num(wind) / tot, 4), 'solar_share': round(np.nan_to_num(sun) / tot, 4),
            'pv_share_of_wind_plus_solar': round(np.nan_to_num(sun) / (np.nan_to_num(wind) + np.nan_to_num(sun)), 4) if (np.nan_to_num(wind) + np.nan_to_num(sun)) > 0 else np.nan,
            'wd_mg': round(g.wd.sum()), 'cons_mg': round(g.cons.sum()),
            'wd_gal_mwh_rep': round(gpm(g.wd.sum())), 'cons_gal_mwh_rep': round(gpm(g.cons.sum()), 1),
            'wd_l_kwh_rep': round(lk(g.wd.sum()), 2), 'cons_l_kwh_rep': round(lk(g.cons.sum()), 3),
            'wd_fresh_l_kwh_rep': round(lk(g.wd_fresh.sum()), 2), 'cons_fresh_l_kwh_rep': round(lk(g.cons_fresh.sum()), 3),
            'wd_l_kwh_adj': round(lk(g.wd_adj.sum()), 2), 'cons_l_kwh_adj': round(lk(g.cons_adj.sum()), 3),
            'wd_l_kwh_macknick_bu': round(lk(g.wd_bu.sum()), 2), 'cons_l_kwh_macknick_bu': round(lk(g.cons_bu.sum()), 3),
            'consumed_frac_adj': round(g.cons_adj.sum() / g.wd_adj.sum(), 4) if g.wd_adj.sum() > 0 else np.nan,
            'n_plants': len(g), 'n_flagged': len(fl),
            'flagged': ' | '.join(f"{r['Plant Name']} ({r['Plant Code']}): {r['flag']}; wd {r.wd:.0f} MG, cons {r.cons:.0f} MG, gen {r.gen_basis/1e6:.2f} TWh"
                                  for _, r in fl.sort_values('wd', ascending=False).iterrows()),
        })
    out = pd.DataFrame(rows)
    for st in sorted(set(piv.index) - set(out.state) - {'US'}):      # states with no reporting thermoelectric plant
        if len(st) != 2:
            continue
        tot = piv.loc[st, 'ALL']; wind = np.nan_to_num(piv.loc[st].get('WND', 0)); sun = np.nan_to_num(piv.loc[st].get('SUN', 0))
        out.loc[len(out)] = {'state': st, 'net_gen_mwh_2024': round(tot), 'wind_mwh': round(wind), 'solar_utility_mwh': round(sun),
                             'solar_small_est_mwh': round(np.nan_to_num(piv.loc[st].get('DPV', 0))), 'wind_share': round(wind / tot, 4),
                             'solar_share': round(sun / tot, 4), 'pv_share_of_wind_plus_solar': round(sun / (wind + sun), 4) if wind + sun else np.nan,
                             'n_plants': 0, 'n_flagged': 0, 'flagged': 'no plants in EIA 2024 cooling data'}
    out = out.sort_values('state')
    os.makedirs(os.path.join(D, 'out'), exist_ok=True)
    out.to_csv(os.path.join(D, 'out', 'states_2024.csv'), index=False)
    p.to_csv(os.path.join(D, 'out', 'plants_2024.csv'), index=False)
    pd.set_option('display.width', 250, 'display.max_rows', 80)
    print(out.drop(columns=['flagged']).to_string())


if __name__ == '__main__':
    main()
