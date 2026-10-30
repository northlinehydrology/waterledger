"""Recompute every row of grid_water_2022.csv from the Siddik et al. 2024 v1.1 CSV (2022), load-weighted (elec_cons)."""
import pandas as pd
src='/Users/andrew/northline/engine/data/raw/lit/water_impact_consumption_2022_v1.1.csv'
tab='/Users/andrew/repos/waterledger/packages/waterledger-data/src/waterledger_data/tables/grid_water_2022.csv'
df=pd.read_csv(src,index_col=0)
rows=[]
for ba,g in df.groupby('balancing_authority'):
    w=g.elec_cons.fillna(0); ok=w>0
    r={'ba':ba,'hours':len(g),'twh':w.sum()/1e6}
    for c in ['wci_zero','wci_primary','wwi','wwi_zero']:
        m=ok&g[c].notna(); r[c]=(g.loc[m,c]*w[m]).sum()/w[m].sum() if w[m].sum()>0 else float('nan')
        r[c+'_mean']=g[c].mean()
    rows.append(r)
mine=pd.DataFrame(rows).set_index('ba')
t=pd.read_csv(tab).set_index('ba')
j=t.join(mine,how='outer')
pairs=[('consumed_l_per_kwh_excl_hydro','wci_zero'),('consumed_l_per_kwh_incl_hydro','wci_primary'),('withdrawn_l_per_kwh_excl_hydro','wwi_zero'),('twh_2022','twh')]
bad=[]
for ba,r in j.iterrows():
    for a,b in pairs:
        if pd.isna(r[a]) or pd.isna(r[b]) or abs(r[a]-r[b])>max(0.0006,0.001*abs(r[b])):
            bad.append((ba,a,r[a],b,r[b],r.get(b+'_mean')))
print('table rows',len(t),'source BAs',len(mine))
for x in bad: print('DIFF',x)
j.to_csv('../out/table_check.csv')
pd.set_option('display.width',200,'display.max_rows',100)
print(j[['consumed_l_per_kwh_excl_hydro','wci_zero','consumed_l_per_kwh_incl_hydro','wci_primary','withdrawn_l_per_kwh_excl_hydro','wwi_zero','wwi','twh_2022','twh','hours']].round(4).to_string())
