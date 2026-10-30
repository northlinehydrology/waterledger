"""Add net interstate imports (EIA State Electricity Profiles, Table 10, 2024), the main balancing authority, and blended
and range columns to ../out/states_2024.csv (run after states.py and ba_compare.py).

consumption_mwh = total electric industry sales + direct use + estimated losses (Table 10, 2024)
net_imports_mwh = -(net interstate trade) when negative, else 0 (Table 10 sign: negative = net import)
import_share    = net_imports_mwh / consumption_mwh
main_ba         = BA with the most 2024 net generation among the state's plants (EIA-860 plant file x EIA API plant generation)
blend           = (1 - s) * state adjusted + s * main-BA plant-based adjusted
lo/hi           = min/max over {state reported (if no anomaly flags), state adjusted, Macknick bottom-up, blend, Siddik BA 2022}
"""
import json, os
import numpy as np
import openpyxl
import pandas as pd

D = os.environ.get('WL_POWER_WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'work'))


def table10(st):
    path = os.path.join(D, 'dl', 'sep', f'sep_{st}.xlsx')
    if not os.path.exists(path):
        return None
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb['10. Source-Disposition']
    rows, year = {}, None
    for r in ws.iter_rows(values_only=True):
        r = [v for v in r if v is not None]
        if not r:
            continue
        if r[0] == 'Category':
            year = str(r[1]).split()[-1]
        elif isinstance(r[0], str) and len(r) > 1:
            rows[r[0].strip('. ').strip()] = r[1]
    num = lambda k: float(rows[k]) if k in rows and rows[k] not in ('', '.', None) else np.nan
    cons = num('Total electric industry sales') + np.nan_to_num(num('Direct use')) + np.nan_to_num(num('Estimated losses'))
    trade = num('Net interstate trade')
    return {'sep_year': year, 'consumption_mwh': cons, 'net_interstate_trade_mwh': trade,
            'net_imports_mwh': max(0.0, -trade) if trade == trade else np.nan,
            'intl_net_imports_mwh': np.nan_to_num(num('Total international imports')) - np.nan_to_num(num('Total international exports'))}


def main():
    out = pd.read_csv(os.path.join(D, 'out', 'states_2024.csv'))
    out = out[[c for c in out.columns if c == 'net_gen_mwh_2024' or not c.startswith(('sep_year', 'consumption_mwh', 'net_', 'intl_',
                                                             'import_share', 'main_ba', 'ba_', 'siddik_', 'consumed_', 'withdrawn_', 'import_data'))]]
    # main BA by in-state generation
    pl = pd.read_excel(os.path.join(D, 'dl/eia860/x/2___Plant_Y2024.xlsx'), header=1)
    fac = pd.DataFrame(json.load(open(os.path.join(D, 'dl/api/facility_gen_2024.json'))))
    fac['generation'] = pd.to_numeric(fac.generation, errors='coerce'); fac['plantCode'] = fac.plantCode.astype(int)
    g = fac.groupby(['plantCode', 'state']).generation.sum().reset_index()
    g['ba'] = g.plantCode.map(pl.set_index('Plant Code')['Balancing Authority Code'])
    bs = g.groupby(['state', 'ba']).generation.sum().reset_index().sort_values('generation', ascending=False)
    main_ba = bs.drop_duplicates('state').set_index('state').ba
    tot = bs.groupby('state').generation.sum()
    main_share = bs.drop_duplicates('state').set_index('state').generation / tot
    bc = pd.read_csv(os.path.join(D, 'out', 'ba_compare_2024.csv'), index_col=0)

    recs = []
    for r in out.itertuples():
        t = table10(r.state) or {}
        ba = main_ba.get(r.state)
        b = bc.loc[ba] if ba in bc.index else None
        recs.append({**t, 'import_data_missing': not t or t.get('consumption_mwh') != t.get('consumption_mwh'),
                     'main_ba': ba, 'main_ba_share_of_state_gen': round(float(main_share.get(r.state, np.nan)), 3),
                     'ba_plant_cons_adj_l_kwh': None if b is None else b.cons_adj_l_kwh,
                     'ba_plant_wd_adj_l_kwh': None if b is None else b.wd_adj_l_kwh,
                     'siddik_ba_cons_excl_hydro_l_kwh': None if b is None else b.consumed_l_per_kwh_excl_hydro,
                     'siddik_ba_wd_excl_hydro_l_kwh': None if b is None else b.withdrawn_l_per_kwh_excl_hydro})
    out = pd.concat([out.reset_index(drop=True), pd.DataFrame(recs)], axis=1)
    out['import_share'] = (out.net_imports_mwh / out.consumption_mwh).round(4)
    s = out.import_share.fillna(0.0)
    for k, st, ba, rep, bu, sid in [('consumed', 'cons_l_kwh_adj', 'ba_plant_cons_adj_l_kwh', 'cons_l_kwh_rep', 'cons_l_kwh_macknick_bu', 'siddik_ba_cons_excl_hydro_l_kwh'),
                                    ('withdrawn', 'wd_l_kwh_adj', 'ba_plant_wd_adj_l_kwh', 'wd_l_kwh_rep', 'wd_l_kwh_macknick_bu', 'siddik_ba_wd_excl_hydro_l_kwh')]:
        bav = pd.to_numeric(out[ba], errors='coerce')
        out[f'{k}_blend'] = np.where(bav.notna(), np.where(out[st].notna(), (1 - s) * out[st] + s * bav, bav), out[st]).round(3)
        # (no in-state reporting plants -> the main BA's plant-based value)
        rep_ok = out[rep].where(out.n_flagged.fillna(0) == 0)          # reported value only where no plant was flagged
        cand = pd.concat([rep_ok, out[st], out[bu], out[f'{k}_blend'], pd.to_numeric(out[sid], errors='coerce')], axis=1)
        out[f'{k}_lo'] = cand.min(axis=1).round(3)
        out[f'{k}_hi'] = cand.max(axis=1).round(3)
    out.to_csv(os.path.join(D, 'out', 'states_2024.csv'), index=False)
    pd.set_option('display.width', 250, 'display.max_rows', 80)
    cols = ['state', 'sep_year', 'consumption_mwh', 'net_imports_mwh', 'import_share', 'main_ba', 'cons_l_kwh_adj', 'ba_plant_cons_adj_l_kwh',
            'consumed_blend', 'consumed_lo', 'consumed_hi', 'wd_l_kwh_adj', 'withdrawn_blend', 'withdrawn_lo', 'withdrawn_hi', 'import_data_missing']
    print(out[cols].to_string())


if __name__ == '__main__':
    main()
