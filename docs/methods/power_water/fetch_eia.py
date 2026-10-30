"""Fetch EIA API v2 data used by states.py into ../dl/api/ (DEMO_KEY; public data)."""
import json, os, subprocess, sys, time
OUT=os.path.join(os.environ.get('WL_POWER_WORK', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'work')),'dl','api')
os.makedirs(OUT,exist_ok=True)
def pages(name,url):
    path=os.path.join(OUT,name+'.json')
    if os.path.exists(path): return
    rows=[];off=0
    while True:
        u=f"{url}&length=5000&offset={off}&api_key=DEMO_KEY"
        r=subprocess.run(['curl','-sS','-g',u],capture_output=True,text=True)
        d=json.loads(r.stdout)['response']; rows+=d['data']
        off+=5000
        if off>=int(d['total']): break
        time.sleep(1)
    json.dump(rows,open(path,'w')); print(name,len(rows))
B='https://api.eia.gov/v2/electricity'
pages('facility_gen_2024',B+'/facility-fuel/data/?frequency=annual&data[0]=generation&facets[fuel2002][]=ALL&facets[primeMover][]=ALL&start=2024&end=2024')
pages('state_gen_2024',B+'/electric-power-operational-data/data/?frequency=annual&data[0]=generation&facets[sectorid][]=99&start=2024&end=2024')
pages('generators_2024_12',B+'/operating-generator-capacity/data/?frequency=monthly&data[0]=nameplate-capacity-mw&start=2024-12&end=2024-12')
