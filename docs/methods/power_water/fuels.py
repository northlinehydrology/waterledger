"""Each state's coal and nuclear plants as a power option: Macknick et al. (2012) factors for how they are cooled, weighted by their 2024 generation.

The medians are used, not the plants' own reports, because a single plant's report can swing a small state's option (a coal plant reporting 57 gal/MWh
through towers), and these options describe a kind of plant rather than one year's filings. The plants' screened reports are kept beside them as a check.
Run after states.py. Output: tables/state_fuel_water_2024.csv.
"""
import os
import numpy as np
import pandas as pd
import states as S

TAB = os.path.join(S.H, '..', '..', '..', 'packages', 'waterledger-data', 'src', 'waterledger_data', 'tables', 'state_fuel_water_2024.csv')


def main():
    p = pd.read_csv(os.path.join(S.D, 'out', 'plants_2024.csv'))
    p = p[p.tech.isin(['coal', 'nuclear']) & (p.gen_basis > 0)].copy()
    p['cool'] = p.cool.fillna('tower')      # as states.factor treats a plant with no cooling type
    rows = []
    for (st, tech), g in p.groupby(['State', 'tech']):
        w = g.gen_basis / g.gen_basis.sum()
        med = [S.MK[(tech, c)] for c in g.cool]
        rng = [S.MK_RANGE[(tech, c)] for c in g.cool]
        wd = sum(x * m[1] for x, m in zip(w, med))
        rows.append({'state': st, 'fuel': tech, 'gen_mwh': round(g.gen_basis.sum()), 'n_plants': len(g),
                     **{f'share_{c}': round(float(w[g.cool == c].sum()), 4) for c in ('once', 'tower', 'pond', 'dry')},
                     'consumed_gal_mwh': round(sum(x * m[0] for x, m in zip(w, med)), 1),
                     'consumed_lo': round(sum(x * r[0][0] for x, r in zip(w, rng)), 1), 'consumed_hi': round(sum(x * r[0][1] for x, r in zip(w, rng)), 1),
                     'withdrawn_gal_mwh': round(wd, 1),
                     'withdrawn_lo': round(sum(x * r[1][0] for x, r in zip(w, rng)), 1), 'withdrawn_hi': round(sum(x * r[1][1] for x, r in zip(w, rng)), 1),
                     'saline_share': round(sum(x * m[1] * s for x, m, s in zip(w, med, g.saline_share)) / wd, 4) if wd else 0.0,
                     'reported_consumed_gal_mwh': round(g.cons_adj.sum() * 1e6 / g.gen_basis.sum(), 1),
                     'reported_withdrawn_gal_mwh': round(g.wd_adj.sum() * 1e6 / g.gen_basis.sum(), 1)})
    o = pd.DataFrame(rows).sort_values(['state', 'fuel'])
    o.to_csv(TAB, index=False, lineterminator='\n')
    pd.set_option('display.width', 250, 'display.max_columns', 30)
    print(o[o.state.isin(['MI', 'OH', 'VA', 'TX'])].to_string(index=False))


if __name__ == '__main__':
    main()
