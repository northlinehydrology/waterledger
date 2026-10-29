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


def estimate(site):
    """Water use for a site at a Michigan place, through waterledger.scenario (the page's est())."""
    from waterledger.estimate import Estimate, Flow, Range, WaterUse
    f = site.facility
    S = sc.scenario(site.place.geoid, mw=f.it_mw, cool=f.cooling, src=site.source, dest=site.wastewater, acres=site.acres,
                    before=site.land_before, imp=site.impervious)
    E, R = S["E"], Range.from_band
    water = WaterUse(withdrawn=Flow(avg=R(E["wAvg"]), peak_day=R(E["wPeak"])), withdrawn_annual_mg=R(E["wAnn"]),
                     consumed=Flow(avg=R(E["cAvg"]), peak_day=R(E["cPeak"])), returned=Flow(avg=R(E["rAvg"]), peak_day=R(E["rPeak"])),
                     to_sewer=R(E["sewer"]), lake_source=E["lake"], reuse=E["reuse"])
    resolved = site.model_copy(update={"source": S["src"], "wastewater": S["dest"], "acres": S["acres"], "land_before": S["before"]})
    D = sc.data("estimates")
    return Estimate(site=resolved, water=water, model_version=D["model_version"], data_date=D["generated"])
