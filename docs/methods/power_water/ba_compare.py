"""Generation-based 2024 BA water intensity from plant data (states.py output) vs Siddik 2022 table (consumption-based)."""
import json, os, pandas as pd, numpy as np
D=os.environ.get('WL_POWER_WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'work'))
pl=pd.read_excel(os.path.join(D,'dl/eia860/x/2___Plant_Y2024.xlsx'),header=1)
ba=pl.set_index('Plant Code')['Balancing Authority Code']
fac=pd.DataFrame(json.load(open(os.path.join(D,'dl/api/facility_gen_2024.json'))))
fac['generation']=pd.to_numeric(fac.generation,errors='coerce'); fac['plantCode']=fac.plantCode.astype(int)
fg=fac.groupby('plantCode').generation.sum()
gen_ba=fg.groupby(fg.index.map(ba)).sum()
p=pd.read_csv(os.path.join(D,'out/plants_2024.csv')); p['ba']=p['Plant Code'].map(ba)
L=3.78541/1000
agg=p.groupby('ba')[['wd','cons','wd_adj','cons_adj','cons_bu','wd_bu']].sum()
t=pd.read_csv('/Users/andrew/repos/waterledger/packages/waterledger-data/src/waterledger_data/tables/grid_water_2022.csv').set_index('ba')
o=pd.DataFrame({'gen_twh_2024':gen_ba/1e6})
for c in agg: o[c+'_l_kwh']=agg[c]*1e6/gen_ba*L
o=o.join(t,how='inner')
o['cons_ratio_siddik_to_adj']=o.consumed_l_per_kwh_excl_hydro/o.cons_adj_l_kwh
o['wd_ratio_siddik_to_rep']=o.withdrawn_l_per_kwh_excl_hydro/o.wd_l_kwh
o=o.sort_values('gen_twh_2024',ascending=False)
o.round(3).to_csv(os.path.join(D,'out/ba_compare_2024.csv'))
pd.set_option('display.width',250,'display.max_rows',80)
print(o[['gen_twh_2024','twh_2022','cons_l_kwh','cons_adj_l_kwh','cons_bu_l_kwh','consumed_l_per_kwh_excl_hydro','wd_l_kwh','wd_adj_l_kwh','withdrawn_l_per_kwh_excl_hydro','cons_ratio_siddik_to_adj','wd_ratio_siddik_to_rep']].round(2).to_string())
