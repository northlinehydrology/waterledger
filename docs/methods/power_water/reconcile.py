"""Reconcile plant-based balancing-authority (BA) water intensities with Siddik et al. (2024), 2022.

Rebuilds the plant table of states.py for any year, reconstructs Siddik et al.'s consumption-based intensity (their Eq. 1-3)
from public EIA data, and splits the gap between their published 2022 value and our 2024 value into steps:

  O24  ours, 2024: screened plant water / all BA net generation, EIA-923 (generation-based)
  O22  the same for 2022                                                     O22 - O24 = year
  G22  O22's water as fuel factors x EIA-930 hourly fuel mix                 G22 - O22 = generation data
  C22  G22 with one-step imports (Eq. 3, EIA-930 interchange)                C22 - G22 = boundary
  R0   C22 with raw reports (no screening)                                   R0  - C22 = screening
  K    R0 with non-reporting generation at the national fuel-month average   K   - R0  = non-reporter fill
  F    K with plants reporting zero for the year treated as non-reporting    F   - K   = zero reports (consumption only)
  S    Siddik et al. published value (WCI_NH, WWI_NH)                        S   - F   = residual

Inputs in $WL_POWER_WORK: detail_all.pkl (2024 cooling detail, states.py), dl2022/ and dl2024/ with the EIA cooling detail, EIA-923
(x923/) and EIA-930 six-month BALANCE and INTERCHANGE files; $WL_SIDDIK_CSV, HydroShare v1.1 hourly data for 2022.
Output: recon_ba_2022_2024.csv beside this script. Run: WL_POWER_WORK=... python reconcile.py
"""
import glob, os
import numpy as np
import pandas as pd
import states as S

H = os.path.dirname(os.path.abspath(__file__))
D = os.environ.get('WL_POWER_WORK', os.path.join(H, 'work'))
SID = os.environ.get('WL_SIDDIK_CSV', '/Users/andrew/northline/engine/data/raw/lit/water_impact_consumption_2022_v1.1.csv')
L = 3.78541 / 1000                 # (million gal x 1e6 / MWh) x L = L/kWh
FUELS = ['coal', 'gas', 'nuclear', 'oil', 'hydro', 'solar', 'wind', 'other']
THERMAL = ['coal', 'gas', 'nuclear', 'oil', 'other']
FUEL = {'COL': 'coal', 'WOC': 'coal', 'NG': 'gas', 'NUC': 'nuclear', 'DFO': 'oil', 'RFO': 'oil', 'PC': 'oil', 'WOO': 'oil', 'HYC': 'hydro',
        'HPS': 'hydro', 'SUN': 'solar', 'WND': 'wind'}
MON = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
GROUPS930 = {'coal': ['Coal'], 'gas': ['Natural Gas'], 'nuclear': ['Nuclear'], 'oil': ['Petroleum'], 'hydro': ['Hydropower', 'Pumped Storage'],
             'solar': ['Solar'], 'wind': ['Wind'], 'other': ['Other Fuel', 'Geothermal', 'Battery Storage', 'Other Energy Storage', 'Unknown Energy Storage'],
             'unk': ['Unknown Fuel']}
MAJOR = ['PJM', 'MISO', 'ERCO', 'SWPP', 'SOCO', 'CISO', 'TVA', 'NYIS', 'FPL', 'ISNE', 'DUK', 'CPLE']


def cached(name, build):
    path = os.path.join(D, name)
    if not os.path.exists(path):
        build().to_pickle(path)
    return pd.read_pickle(path)


def gen923(y):
    def build():
        f = glob.glob(os.path.join(D, f'dl{y}', 'x923', 'EIA923_Schedules_2_3_4_5_*.xlsx'))[0]
        x = pd.read_excel(f, sheet_name='Page 1 Generation and Fuel Data', header=5)
        x.columns = [str(c).replace('\n', ' ').strip() for c in x.columns]
        return x
    g = cached(f'gf923_{y}.pkl', build)
    g = g[g['Plant Id'] != 99999].copy()
    g['fuel'] = g['MER Fuel Type Code'].map(FUEL).fillna('other')
    g['ba'] = g['Balancing Authority Code'].replace('', np.nan)
    g['ba'] = g['Plant Id'].map(g.dropna(subset=['ba']).groupby('Plant Id').ba.first())
    for m in MON:
        g['Netgen ' + m] = pd.to_numeric(g['Netgen ' + m], errors='coerce').fillna(0)
    g['gen'] = pd.to_numeric(g['Net Generation (Megawatthours)'], errors='coerce').fillna(0)
    return g


def detail(y):
    if y == 2024:
        return pd.read_pickle(os.path.join(D, 'detail_all.pkl')).copy()
    def build():
        x = pd.read_excel(glob.glob(os.path.join(D, f'dl{y}', 'Cooling_Boiler_Generator_Data_Detail_*.xlsx'))[0], header=2)
        x.columns = [str(c).strip() for c in x.columns]
        return x
    return cached(f'detail_{y}.pkl', build).copy()


def plants(y):
    """Plant table with the same rules as states.py (2024 reproduces its 181 flags and totals). Generation fallback from EIA-923."""
    d = detail(y)
    d['Month'] = d['Month'].astype(str)
    for c in [S.W, S.C] + S.GEN:
        d[c] = S.num(d[c])
    d['code'] = d['860 Cooling Type 1'].astype(str).str.extract(r'\((\w+)\)')[0].str[:2]
    d['cool'] = d['code'].map(S.COOL)
    d['tech'] = d['Generator Primary Technology'].map(S.TECH)
    d['net'] = d[S.GEN].sum(axis=1)
    wtr = d.drop_duplicates(['Plant Code', 'Cooling ID', 'Month'])
    gen = d.drop_duplicates(['Plant Code', 'Generator ID', 'Month'])
    pw = wtr.groupby(['State', 'Plant Code', 'Plant Name']).agg(wd=(S.W, 'sum'), cons=(S.C, 'sum')).reset_index()
    mw = wtr.groupby(['Plant Code', 'Month']).agg(wd=(S.W, 'sum'), cons=(S.C, 'sum')).reset_index()
    pg = gen.groupby('Plant Code').agg(cooled_gen=('net', 'sum')).reset_index()
    ct = d[d.cool.notna()].groupby(['Plant Code', 'cool']).agg(w=(S.W, 'sum'), n=('cool', 'size')).reset_index()
    ct = ct.sort_values(['Plant Code', 'w', 'n'], ascending=[True, False, False]).drop_duplicates('Plant Code')[['Plant Code', 'cool']]
    tg = gen.groupby(['Plant Code', 'tech']).agg(g=('net', 'sum'), n=('tech', 'size')).reset_index()
    tg = tg.sort_values(['Plant Code', 'g', 'n'], ascending=[True, False, False]).drop_duplicates('Plant Code')[['Plant Code', 'tech']]
    p = pw.merge(pg, on='Plant Code', how='left').merge(ct, on='Plant Code', how='left').merge(tg, on='Plant Code', how='left')
    g = gen923(y)
    p['plant_gen'] = p['Plant Code'].map(g.groupby('Plant Id').gen.sum()).fillna(0.0)
    p['gen_basis'] = np.where(p.cooled_gen > 0, p.cooled_gen, p.plant_gen)
    p = p[(p.wd > 0) | (p.cons > 0) | (p.gen_basis > 0)].copy()
    p['wd_gpm'] = np.where(p.gen_basis > 0, p.wd * 1e6 / p.gen_basis, np.nan)
    p['c_gpm'] = np.where(p.gen_basis > 0, p.cons * 1e6 / p.gen_basis, np.nan)
    fl, ca, wa = [], [], []
    for r in p.itertuples():
        f = []
        mc, mw_ = S.factor(r.tech, r.cool)
        g_ = max(r.gen_basis, 0.0)
        if r.cons > r.wd * 1.001 and r.wd > 0:
            f.append('cons>withdrawal')
        if r.c_gpm == r.c_gpm and r.c_gpm > 1500:
            f.append('cons>1500gal/MWh')
        if r.cons == 0 and r.wd > 0 and r.cool in ('once', 'pond'):
            f.append(f'zero cons ({r.cool})')
        if r.wd_gpm == r.wd_gpm and r.cool in ('tower', 'pond') and r.wd_gpm > 25000:
            f.append('withdrawal>25000')
        if g_ == 0 and (r.wd > 0 or r.cons > 0):
            f.append('water, no generation')
        fl.append('; '.join(f))
        c = mc * g_ / 1e6 if any(x.startswith(('cons>', 'zero cons')) for x in f) else r.cons
        w = mw_ * g_ / 1e6 if any(x.startswith('withdrawal>') for x in f) else r.wd
        ca.append(min(c, w) if w > 0 else c)
        wa.append(w)
    p['flag'], p['cons_adj'], p['wd_adj'] = fl, ca, wa
    pf = g.groupby(['Plant Id', 'fuel']).gen.sum().reset_index()
    p['fuel'] = p['Plant Code'].map(pf[pf.fuel.isin(THERMAL)].sort_values('gen', ascending=False).drop_duplicates('Plant Id').set_index('Plant Id').fuel)
    p['ba'] = p['Plant Code'].map(g.dropna(subset=['ba']).groupby('Plant Id').ba.first())
    return p, g, mw


def tables(y):
    p, g, mw = plants(y)
    ml = g.drop(columns=['gen']).melt(id_vars=['Plant Id', 'fuel', 'ba'], value_vars=['Netgen ' + m for m in MON], var_name='mon', value_name='g')
    ml['m'] = ml.mon.str.replace('Netgen ', '').map({m: i + 1 for i, m in enumerate(MON)})
    mw = mw.copy()
    mw['m'] = pd.to_numeric(mw.Month)
    mw = mw.merge(p[['Plant Code', 'fuel', 'cons', 'wd', 'cons_adj', 'wd_adj']].rename(columns={'cons': 'cy', 'wd': 'wy'}), on='Plant Code')
    pm = ml.groupby(['Plant Id', 'm']).g.sum().rename('pg').reset_index()
    mw = mw.merge(pm, left_on=['Plant Code', 'm'], right_on=['Plant Id', 'm'], how='left')
    share = (mw.pg / mw['Plant Code'].map(pm.groupby('Plant Id').pg.sum())).clip(lower=0)
    # screened month = reported month scaled to the plant's screened year; a zero year is spread by the plant's monthly generation
    mw['cons_s'] = np.where(mw.cy > 0, mw.cons * mw.cons_adj / mw.cy.replace(0, np.nan), mw.cons_adj * share)
    mw['wd_s'] = np.where(mw.wy > 0, mw.wd * mw.wd_adj / mw.wy.replace(0, np.nan), mw.wd_adj * share)
    mw[['cons_s', 'wd_s']] = mw[['cons_s', 'wd_s']].fillna(0)
    return p, g, ml, mw


def factors(ml, mw, numer='raw', fill=False, zero_missing=False):
    """Water per kWh of each fuel by BA and month (L/kWh). Water goes to the plant's main fuel.
    fill: non-reporting generation at the national fuel-month ratio over all reporting plants (none for 'other').
    zero_missing: consumption-side, plants with zero water for the year are treated as non-reporting."""
    cols = {'cons': 'c', 'wd': 'w'} if numer == 'raw' else {'cons_s': 'c', 'wd_s': 'w'}
    pf = ml.groupby(['Plant Id', 'fuel', 'ba', 'm']).g.sum().reset_index()
    a = mw[['Plant Code', 'm', 'fuel'] + list(cols)].rename(columns={**cols, 'fuel': 'df'}).groupby(['Plant Code', 'm', 'df'], as_index=False)[['c', 'w']].sum()
    pf = pf.merge(a, left_on=['Plant Id', 'm'], right_on=['Plant Code', 'm'])
    pf = pf[pf.fuel == pf.df]
    ann = pf.groupby('Plant Id')[['c', 'w']].sum()
    t = pd.DataFrame(ml.groupby(['ba', 'fuel', 'm']).g.sum().rename('G'))
    idx = t.index.droplevel('ba')
    for v, src in [('gc', 'c'), ('gw', 'w')]:
        q = pf
        if zero_missing:
            q = pf[pf['Plant Id'].isin(ann.index[ann[src] > 0])]
        pos = q[q.g > 0]
        ww = q.groupby(['ba', 'fuel', 'm'])[src].sum().reindex(t.index).fillna(0) * 1e6 * L
        gr = pos.groupby(['ba', 'fuel', 'm']).g.sum().reindex(t.index).fillna(0)
        allp = pf[pf.g > 0].groupby(['fuel', 'm'])[[src, 'g']].sum()
        nat = pd.Series((allp[src] * 1e6 * L / allp.g).reindex(idx).values, index=t.index).fillna(0)
        nat = nat.where(t.index.get_level_values('fuel') != 'other', 0.0)
        x = nat if fill else 0 * nat
        t[v] = (ww + x * (t.G - gr).clip(lower=0)) / t.G.where(t.G > 0)
    t = t[t.index.get_level_values('fuel').isin(THERMAL)]
    return t[['gc', 'gw']].fillna(0)


def load930(y):
    def nm(s):
        return pd.to_numeric(s.astype(str).str.replace(',', ''), errors='coerce')
    def build_b():
        b = pd.concat([pd.read_csv(os.path.join(D, f'dl{y}', f'EIA930_BALANCE_{y}_{h}.csv'), low_memory=False) for h in ['Jan_Jun', 'Jul_Dec']], ignore_index=True)
        o = pd.DataFrame({'ba': b['Balancing Authority'], 't': pd.to_datetime(b['UTC Time at End of Hour'], format='%m/%d/%Y %I:%M:%S %p'),
                          'D': nm(b['Demand (MW) (Adjusted)']), 'NG': nm(b['Net Generation (MW) (Adjusted)'])})
        adj = [c for c in b.columns if c.startswith('Net Generation (MW) from') and c.endswith('(Adjusted)')]
        for v, words in GROUPS930.items():        # EIA split solar, wind, hydro and storage into more columns from July 2024
            cols = [c for c in adj if any(w in c for w in words)]
            o[v] = pd.concat([nm(b[c]) for c in cols], axis=1).sum(axis=1, min_count=1)
        return o
    def build_i():
        i = pd.concat([pd.read_csv(os.path.join(D, f'dl{y}', f'EIA930_INTERCHANGE_{y}_{h}.csv'), low_memory=False,
                                   usecols=['Balancing Authority', 'Directly Interconnected Balancing Authority', 'Interchange (MW)', 'UTC Time at End of Hour'])
                       for h in ['Jan_Jun', 'Jul_Dec']], ignore_index=True)
        i.columns = ['ba', 'diba', 'x', 't']
        i['x'] = nm(i.x)
        i['t'] = pd.to_datetime(i.t, format='%m/%d/%Y %I:%M:%S %p')
        return i
    b = cached(f'bal930_{y}a.pkl', build_b)
    it = cached(f'int930_{y}.pkl', build_i)
    g = b[FUELS].fillna(0).clip(lower=0)
    tot = g.sum(axis=1).replace(0, np.nan)
    r = g.div(tot, axis=0).fillna(0)
    r['ba'], r['t'], r['D'], r['NG'] = b.ba.values, b.t.values, b.D.values, b.NG.values
    r['m'] = (r.t - pd.Timedelta(hours=1)).dt.month
    return r, it


def eq3(r, it, G):
    """Siddik Eq. 3: one-step imports at each exporter's hourly generation intensity; imports from outside EIA-930's U.S. BAs dropped and
    the mix normalized over known sources (this reproduces their published mix). Returns load-weighted consumption-based and
    generation-weighted intensity by BA."""
    x = r[['ba', 't', 'm', 'D', 'NG']].copy()
    a = G.reset_index().pivot_table(index=['ba', 'm'], columns='fuel', values=['gc', 'gw'], fill_value=0)
    ix = pd.MultiIndex.from_arrays([r.ba, r.m])
    for v in ['gc', 'gw']:
        arr = np.zeros(len(r))
        for f in THERMAL:
            if (v, f) in a.columns:
                arr += r[f].values * a[(v, f)].reindex(ix).fillna(0).values
        x[v] = arr
    gi = x.set_index(['ba', 't'])[['gc', 'gw']]
    im = it[it.x < 0].copy()
    im['q'] = -im.x
    im = im.merge(gi, left_on=['diba', 't'], right_index=True, how='left')
    qall = im.groupby(['ba', 't']).q.sum().rename('qall')
    k = im.dropna(subset=['gc']).copy()
    k['qc'], k['qw'] = k.q * k.gc, k.q * k.gw
    y = x.set_index(['ba', 't']).join(qall).join(k.groupby(['ba', 't'])[['q', 'qc', 'qw']].sum()).fillna({'qall': 0, 'q': 0, 'qc': 0, 'qw': 0})
    y['ret'] = (y.D - y.qall).clip(lower=0)
    den = (y.ret + y.q).where(lambda s: s > 0)
    y['wci'], y['wwi'] = (y.ret * y.gc + y.qc) / den, (y.ret * y.gw + y.qw) / den
    z = y.reset_index()
    z = z[z.D > 0]
    ng = z.NG.clip(lower=0)
    return pd.DataFrame({'cc': (z.wci * z.D).groupby(z.ba).sum() / z.D.where(z.wci.notna()).groupby(z.ba).sum(),
                         'cw': (z.wwi * z.D).groupby(z.ba).sum() / z.D.where(z.wwi.notna()).groupby(z.ba).sum(),
                         'gc': (z.gc * ng).groupby(z.ba).sum() / ng.groupby(z.ba).sum(), 'gw': (z.gw * ng).groupby(z.ba).sum() / ng.groupby(z.ba).sum()})


def plant_based(p, g):
    gb = g.groupby('ba').gen.sum()
    a = p.groupby('ba')[['cons_adj', 'wd_adj']].sum()
    return pd.DataFrame({'c': a.cons_adj * 1e6 * L / gb, 'w': a.wd_adj * 1e6 * L / gb, 'twh': gb / 1e6})


def siddik():
    def build():
        df = pd.read_csv(SID, index_col=0)
        rows = []
        for ba, q in df.groupby('balancing_authority'):
            w = q.elec_cons.fillna(0)
            rows.append({'ba': ba, 'twh': w.sum() / 1e6, 'c': (q.wci_zero * w).sum() / w[q.wci_zero.notna()].sum(), 'w': (q.wwi_zero * w).sum() / w[q.wwi_zero.notna()].sum()})
        return pd.DataFrame(rows).set_index('ba')
    return cached('siddik_ba_2022.pkl', build)


def main():
    p22, g22, ml22, mw22 = tables(2022)
    p24, g24, ml24, mw24 = tables(2024)
    r22, it22 = load930(2022)
    r24, it24 = load930(2024)
    s = siddik()
    o22, o24 = plant_based(p22, g22), plant_based(p24, g24)
    ours22 = eq3(r22, it22, factors(ml22, mw22, 'adj'))
    ours24 = eq3(r24, it24, factors(ml24, mw24, 'adj'))
    r0 = eq3(r22, it22, factors(ml22, mw22, 'raw'))
    k = eq3(r22, it22, factors(ml22, mw22, 'raw', fill=True))
    f = eq3(r22, it22, factors(ml22, mw22, 'raw', fill=True, zero_missing=True))
    out = pd.DataFrame({'twh_siddik_2022': s.twh, 'S_c': s.c, 'S_w': s.w})
    for sfx, gv, cv, ov in [('c', 'gc', 'cc', 'c'), ('w', 'gw', 'cw', 'w')]:
        out[f'O24_{sfx}'] = o24[ov]
        out[f'C24_{sfx}'] = ours24[cv]
        out[f'O22_{sfx}'] = o22[ov]
        out[f'G22_{sfx}'] = ours22[gv]
        out[f'C22_{sfx}'] = ours22[cv]
        out[f'R0_{sfx}'] = r0[cv]
        out[f'K_{sfx}'] = k[cv]
    out['F_c'] = f.cc
    out['F_w'] = k.cw        # withdrawal is reproduced without the zero rule; few plants report zero withdrawal
    for sfx in 'cw':
        out[f'd_year_{sfx}'] = out[f'O22_{sfx}'] - out[f'O24_{sfx}']
        out[f'd_gendata_{sfx}'] = out[f'G22_{sfx}'] - out[f'O22_{sfx}']
        out[f'd_boundary_{sfx}'] = out[f'C22_{sfx}'] - out[f'G22_{sfx}']
        out[f'd_screening_{sfx}'] = out[f'R0_{sfx}'] - out[f'C22_{sfx}']
        out[f'd_nonreporter_{sfx}'] = out[f'K_{sfx}'] - out[f'R0_{sfx}']
        out[f'd_zero_{sfx}'] = out[f'F_{sfx}'] - out[f'K_{sfx}']
        out[f'd_residual_{sfx}'] = out[f'S_{sfx}'] - out[f'F_{sfx}']
        out[f'gap_{sfx}'] = out[f'S_{sfx}'] - out[f'O24_{sfx}']
        out[f'r_{sfx}'] = out[f'S_{sfx}'] / out[f'F_{sfx}']
    out = out.sort_values('twh_siddik_2022', ascending=False)
    out.round(4).to_csv(os.path.join(H, 'recon_ba_2022_2024.csv'))
    pd.set_option('display.width', 250, 'display.max_rows', 100, 'display.max_columns', 40)
    big = out[out.twh_siddik_2022 > 10]
    w = big.twh_siddik_2022
    for sfx in 'cw':
        print(f'\n{"consumed" if sfx == "c" else "withdrawn"}: reproduction, weighted abs error {(abs(big["F_"+sfx]-big["S_"+sfx])*w).sum()/(big["S_"+sfx]*w).sum():.3f}, r {np.corrcoef(big["F_"+sfx],big["S_"+sfx])[0,1]:.3f}')
        ds = ['d_year', 'd_gendata', 'd_boundary', 'd_screening', 'd_nonreporter', 'd_zero', 'd_residual']
        print(out.loc[MAJOR, [f'S_{sfx}', f'O24_{sfx}', f'gap_{sfx}'] + [f'{d}_{sfx}' for d in ds]].round(3).to_string())
        tot = pd.Series({d: (big[f'{d}_{sfx}'] * w).sum() / w.sum() for d in ds})
        print('load-weighted, BAs over 10 TWh:', tot.round(3).to_dict(), 'gap', round((big[f'gap_{sfx}'] * w).sum() / w.sum(), 3))
        print('24 boundary (C24-O24):', (out.loc[MAJOR, f'C24_{sfx}'] - out.loc[MAJOR, f'O24_{sfx}']).round(3).to_dict())


if __name__ == '__main__':
    main()
