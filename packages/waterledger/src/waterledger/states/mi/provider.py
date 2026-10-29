"""Michigan's provider: answers for Michigan places from Water Ledger Michigan's data files (the same ones waterledger.org/mi
reads), through waterledger.scenario, so the package and the page agree."""
from waterledger import scenario as sc


def find(name, county=None):
    return sc.find(name, county)


def place(geoid):
    from waterledger.place import Place
    r = sc.place(geoid)
    lon, lat = sc.lonlat(r)
    return Place(geoid=r["g"], name=r["base"], kind=r["k"], state="MI", county=r["c"], county_fips=r["cf"], lat=round(lat, 4), lon=round(lon, 4))
