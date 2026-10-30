"""Proposed state power-plant water: 2024 plant data updated with the 2022 evidence on the same basis (reconciliation.md).

For each state and water type (L/kWh):
  E1 = current central value (state_power_water_2024.csv) + non-reporting steam and combined-cycle generation at Macknick et al. tower medians
  E2 = E1 with every plant's 2024 intensity replaced by its 2022 intensity (screened, at 2024 generation), times r for the main balancing
       authority, r = Siddik et al. published 2022 value / our reconstruction of it (recon_ba_2022_2024.csv)
  posterior: lognormal, precision-weighted mean of E1 and E2
  variances: plant-by-plant 2024-2022 differences, split into reporting noise and real change with the 2023 data; (ln r)^2 on E2;
             shared error from the literature and from Macknick-filled plants, added to the interval only

Run reconcile.py first. Inputs in $WL_POWER_WORK as there, plus dl2023/, out/ba_compare_2024.csv, out/states_2024.csv, dl/eia860/x/2___Plant_Y2024.xlsx,
dl/api/facility_gen_2024.json. Output: state_power_water_combined_2024.csv beside this script.
"""
import json, os
import numpy as np
import pandas as pd
import reconcile as X
import states as S

H, D, L = X.H, X.D, X.L
TAB = os.environ.get('WL_STATE_TABLE', os.path.join(H, '..', '..', '..', 'packages', 'waterledger-data', 'src', 'waterledger_data', 'tables', 'state_power_water_2024.csv'))
SIG_LIT = {'c': np.log(1.08), 'w': np.log(1.24)}   # Diehl and Harris (2014): EIA-reported total consumption 8% below, withdrawal 24% above, the model estimates
SIG_MACKNICK = 0.35                                # [A] Macknick Table 2 nuclear once-through 100-400 gal/MWh: ln(400/100)/4, about a 95% range
SIG_FILL = 0.5                                     # [A] non-reporting plants' cooling is unknown (dry to tower), so half the fill is one standard deviation
SIG_FLOOR = 0.02                                   # [A] smallest relative year-to-year error, for states where few plants change
BIO = {'WWW', 'MLG', 'ORW', 'OBS', 'OBG', 'AB', 'BLQ', 'LFG', 'MSW', 'OBL', 'SLW', 'WDL', 'WDS'}


def nonreporter_fill():
    """Generation at plants outside the cooling data: steam and combined cycle at tower medians; combustion turbines, engines and the rest at zero."""
    p, g, _ = X.plants(2024)
    n = g[~g['Plant Id'].isin(set(p['Plant Code']))].copy()
    pm, mer = n['Reported Prime Mover'], n['MER Fuel Type Code']
    n['tech'] = None
    n.loc[pm.isin(['CA', 'CT', 'CS']), 'tech'] = 'ngcc'
    st = pm.eq('ST')
    n.loc[st & mer.isin(['COL', 'WOC']), 'tech'] = 'coal'
    n.loc[st & mer.isin(['NG', 'OOG', 'DFO', 'RFO', 'PC', 'WOO']), 'tech'] = 'gas_steam'
    n.loc[st & mer.isin(BIO | {'OTH'}), 'tech'] = 'bio'
    n = n[n.tech.notna()]
    n['fc'] = n.gen.clip(lower=0) * n.tech.map(lambda t: S.MK[(t, 'tower')][0]) / 1e6
    n['fw'] = n.gen.clip(lower=0) * n.tech.map(lambda t: S.MK[(t, 'tower')][1]) / 1e6
    return n


def plant_years():
    """Water at 2024 generation using each year's screened plant intensity; a plant missing a year keeps its 2024 intensity."""
    p24, _, _ = X.plants(2024)
    t = p24[['State', 'Plant Code', 'Plant Name', 'gen_basis', 'cons_adj', 'wd_adj', 'flag']].copy()
    t = t.rename(columns={'cons_adj': 'c24', 'wd_adj': 'w24', 'gen_basis': 'g'})
    for y in (2023, 2022):
        q, _, _ = X.plants(y)
        q = q[q.gen_basis > 0].set_index('Plant Code')
        t[f'has{y}'] = t['Plant Code'].isin(q.index)
        for k, col in [('c', 'cons_adj'), ('w', 'wd_adj')]:
            t[f'{k}{y}'] = (t['Plant Code'].map(q[col] / q.gen_basis) * t.g).fillna(t[f'{k}24'])
    return t


def drift_share(t, k):
    """Split the 2024-2022 difference into noise and real change: D(lag) = 2 noise + lag x drift (random walk), plants with all three years."""
    a = t[t.has2022 & t.has2023]
    d1 = ((a[f'{k}24'] - a[f'{k}2023']) ** 2).sum()
    d2 = ((a[f'{k}24'] - a[f'{k}2022']) ** 2).sum()
    return float(np.clip((d2 - d1) / d2, 0, 1)), d1, d2


def main():
    tab = pd.read_csv(TAB)
    bc = pd.read_csv(os.path.join(D, 'out', 'ba_compare_2024.csv'), index_col=0)
    st = pd.read_csv(os.path.join(D, 'out', 'states_2024.csv')).set_index('state')
    rec = pd.read_csv(os.path.join(H, 'recon_ba_2022_2024.csv'), index_col=0)
    pl = pd.read_excel(os.path.join(D, 'dl/eia860/x/2___Plant_Y2024.xlsx'), header=1)
    ba860 = pl.set_index('Plant Code')['Balancing Authority Code']
    fac = pd.DataFrame(json.load(open(os.path.join(D, 'dl/api/facility_gen_2024.json'))))
    fac['generation'] = pd.to_numeric(fac.generation, errors='coerce')
    fac['plantCode'] = fac.plantCode.astype(int)
    fg = fac.groupby('plantCode').generation.sum()
    gen_ba = fg.groupby(fg.index.map(ba860)).sum()

    t = plant_years()
    t['ba'] = t['Plant Code'].map(ba860)
    fill = nonreporter_fill()
    fill['ba860'] = fill['Plant Id'].map(ba860)
    gs = tab.set_index('state').net_gen_mwh
    out = []
    phi = {}
    for k in 'cw':
        phi[k], d1, d2 = drift_share(t, k)
        print(f'{k}: lag-1 {d1:.3g}, lag-2 {d2:.3g}, share of the 2-year difference that is real change {phi[k]:.2f}')

    def side(k):
        """By state and BA: L/kWh change from using 2022 intensities, difference variance, fill, and flagged water."""
        d = (t[f'{k}2022'] - t[f'{k}24'])
        flagged = t.flag.fillna('').str.contains('cons>|zero cons' if k == 'c' else 'withdrawal>')
        f = {}
        for name, key, gen, fkey in [('s', 'State', gs, 'Plant State'), ('b', 'ba', gen_ba, 'ba860')]:
            f[name] = pd.DataFrame({'dE': d.groupby(t[key]).sum() * 1e6 * L / gen,
                                    'v': (d ** 2).groupby(t[key]).sum() * (1e6 * L) ** 2 / gen ** 2,
                                    'flag': t[f'{k}24'].where(flagged, 0).groupby(t[key]).sum() * 1e6 * L / gen,
                                    'fill': fill.groupby(fkey)[f'f{k}'].sum() * 1e6 * L / gen})
        return f

    sides = {k: side(k) for k in 'cw'}
    names = {'c': ('consumed', 'consumed_state_l_per_kwh', 'cons_adj_l_kwh', 'cons_l_kwh_macknick_bu', 'siddik_ba_cons_excl_hydro_l_kwh', 'cons_bu_l_kwh'),
             'w': ('withdrawn', 'withdrawn_state_l_per_kwh', 'wd_adj_l_kwh', 'wd_l_kwh_macknick_bu', 'siddik_ba_wd_excl_hydro_l_kwh', 'wd_bu_l_kwh')}
    for r in tab.itertuples():
        row = {'state': r.state, 'main_ba': r.main_ba, 'import_share': r.import_share}
        for k in 'cw':
            nm, col, bcol, bu, sid, bubcol = names[k]
            cur = getattr(r, f'{nm}_l_per_kwh')
            row.update({f'{nm}_current': cur, f'{nm}_current_lo': getattr(r, f'{nm}_lo'), f'{nm}_current_hi': getattr(r, f'{nm}_hi')})
            if not cur == cur:
                continue
            ss = sides[k]['s'].reindex([r.state]).iloc[0].fillna(0)
            has_b = isinstance(r.main_ba, str) and r.main_ba in sides[k]['b'].index
            bb = sides[k]['b'].loc[r.main_ba].fillna(0) if has_b else ss * 0
            a_s, s = getattr(r, col), r.import_share if r.import_share == r.import_share else 0.0
            if not a_s == a_s:      # no reporting plants in the state: main BA alone, as imports.py does
                a_s, s = cur, 1.0
            a_b = bc.loc[r.main_ba, bcol] if has_b and r.main_ba in bc.index else a_s
            wt = lambda x, y: (1 - s) * x + s * y
            e1 = wt(a_s + ss.fill, a_b + bb.fill)
            e2p = wt(a_s + ss.fill + ss.dE, a_b + bb.fill + bb.dE)
            v = (1 - s) ** 2 * ss.v + s ** 2 * bb.v
            rr = rec.loc[r.main_ba, f'r_{k}'] if has_b and r.main_ba in rec.index else np.nan
            rr = rr if rr == rr and rr > 0 else 1.0
            e2 = max(e2p, 1e-6) * rr
            rel1 = np.sqrt((1 - phi[k]) * v / 2) / e1
            rel2 = np.sqrt((1 + phi[k]) * v / 2) / e1
            s1 = max(rel1, SIG_FLOOR)
            s2 = np.sqrt(max(rel2, SIG_FLOOR) ** 2 + np.log(rr) ** 2)
            w2 = (1 / s2 ** 2) / (1 / s1 ** 2 + 1 / s2 ** 2)
            mu = np.exp((1 - w2) * np.log(e1) + w2 * np.log(e2))
            mu_nor = np.exp((1 - w2) * np.log(e1) + w2 * np.log(max(e2p, 1e-6)))
            fshare = wt(ss.flag, bb.flag) / e1
            fillv = wt(ss.fill, bb.fill)
            shared = np.sqrt(SIG_LIT[k] ** 2 + (fshare * SIG_MACKNICK) ** 2 + (fillv / e1 * SIG_FILL) ** 2)
            sp = np.sqrt(1 / (1 / s1 ** 2 + 1 / s2 ** 2) + shared ** 2)
            bu_s = st[bu].get(r.state, np.nan)
            bu_b = bc.loc[r.main_ba, bubcol] if has_b and r.main_ba in bc.index else np.nan
            bu_v = wt((bu_s if bu_s == bu_s else bu_b) + ss.fill, (bu_b if bu_b == bu_b else bu_s) + bb.fill)   # same basis as E1
            sid_v = st[sid].get(r.state, np.nan)
            lo_s, hi_s = mu * np.exp(-1.96 * sp), mu * np.exp(1.96 * sp)
            env = [x for x in (lo_s, hi_s, e1, e2, bu_v) if x == x]
            row.update({f'{nm}_proposed': round(mu, 3), f'{nm}_lo': round(min(env), 3), f'{nm}_hi': round(max(env), 3),
                        f'{nm}_lo_stat': round(lo_s, 3), f'{nm}_hi_stat': round(hi_s, 3),
                        f'{nm}_E1_2024_plants': round(e1, 3), f'{nm}_E2_2022_on_same_basis': round(e2, 3), f'{nm}_E2_before_r': round(e2p, 3),
                        f'{nm}_nonreporter_fill': round(wt(ss.fill, bb.fill), 3), f'{nm}_r_siddik': round(rr, 3), f'{nm}_weight_E2': round(w2, 3),
                        f'{nm}_sigma_E1': round(s1, 3), f'{nm}_sigma_E2': round(s2, 3), f'{nm}_sigma_shared': round(shared, 3),
                        f'{nm}_flagged_share': round(fshare, 3), f'{nm}_proposed_without_r': round(mu_nor, 3),
                        f'{nm}_macknick_bottom_up': round(bu_v, 3) if bu_v == bu_v else np.nan, f'{nm}_siddik_2022_raw': sid_v})
        out.append(row)
    o = pd.DataFrame(out)
    o.to_csv(os.path.join(H, 'state_power_water_combined_2024.csv'), index=False)
    pd.set_option('display.width', 250, 'display.max_columns', 40)
    for nm in ['consumed', 'withdrawn']:
        c = o.dropna(subset=[f'{nm}_proposed'])
        rel = c[f'{nm}_proposed'] / c[f'{nm}_current'] - 1
        print(nm, 'median change', round(rel.median(), 3), 'p10-p90', rel.quantile([.1, .9]).round(3).tolist(), 'median weight on E2', c[f'{nm}_weight_E2'].median(),
              'bottom-up inside stat interval', ((c[f'{nm}_macknick_bottom_up'] >= c[f'{nm}_lo_stat']) & (c[f'{nm}_macknick_bottom_up'] <= c[f'{nm}_hi_stat'])).mean().round(2),
              'median |effect of r|', (c[f'{nm}_proposed'] / c[f'{nm}_proposed_without_r'] - 1).abs().median().round(4))
        print(o.loc[o.state.isin(['MI', 'OH', 'VA', 'TX']), ['state', f'{nm}_current', f'{nm}_current_lo', f'{nm}_current_hi', f'{nm}_proposed', f'{nm}_lo', f'{nm}_hi', f'{nm}_lo_stat', f'{nm}_hi_stat', f'{nm}_E1_2024_plants', f'{nm}_E2_2022_on_same_basis', f'{nm}_weight_E2', f'{nm}_nonreporter_fill']].to_string())


if __name__ == '__main__':
    main()
