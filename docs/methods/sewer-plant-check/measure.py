import sys
from waterledger_data import wastewater as ww
old = lambda rows: sorted(rows, key=lambda q: (not q["own"], q["km"]))
nm = lambda q: q.get("name") or q.get("n")
tot = 0
for st in sys.argv[1:]:
    out = []
    if st == "MI":
        import waterledger.scenario as sc
        P = sc.data("places")["places"]
        for p in P:
            b = sc._plants_near(p)
            if b and nm(old(b)[0]) != nm(b[0]):
                a = old(b)[0]; out.append((p["n"], p["c"], nm(a), round(a["km"], 1), a["design"], "->", nm(b[0]), round(b[0]["km"], 1), b[0]["design"], "own" if b[0]["own"] else "system" if b[0]["system"] else "?"))
        n = len(P)
    else:
        from waterledger.national.data import state_data
        from waterledger.national import provider as pv
        sd = state_data(st, fallback="fail"); pl = pv._places(st).set_index("geoid"); plants = sd.plants(); n = len(pl)
        for g, r in pl.iterrows():
            b = ww.nearest(plants, r.lat, r.lon, r.base, km=pv.PLANTS_KM, township="township" in r["name"].lower(), system=ww.main_system(sd.systems_for(g)))
            if b and nm(old(b)[0]) != nm(b[0]):
                a = old(b)[0]; out.append((r["name"], nm(a), round(a["km"], 1), a["design_mgd"], "->", nm(b[0]), round(b[0]["km"], 1), b[0]["design_mgd"], "own" if b[0]["own"] else "system" if b[0]["system"] else "?"))
    tot += len(out)
    print(f"== {st}: {len(out)} of {n} places change their first plant")
    for o in out: print("  ", o)
print("total", tot)
