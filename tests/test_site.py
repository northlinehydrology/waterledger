"""site.estimate() gives the same numbers as waterledger.org's calculator (waterledger.scenario.estimate, the page's est())."""
import pytest

import waterledger as wl
from waterledger import scenario as sc

PLACES = ["Gaines charter township", "Saline township", "Van Buren charter township", "Southfield city", "Acme township"]


@pytest.mark.parametrize("name", PLACES)
@pytest.mark.parametrize("cooling", ["dry", "assist", "hybrid", "towers"])
def test_matches_the_page(name, cooling):
    p = wl.place(f"{name}, MI")
    est = wl.Site(place=p, facility=wl.DataCenter(it_mw=300, cooling=cooling)).estimate()
    S = sc.scenario(p.geoid, mw=300, cool=cooling)
    assert (est.site.source, est.site.wastewater) == (S["src"], S["dest"])
    E = S["E"]
    for got, key in ((est.water.withdrawn.avg, "wAvg"), (est.water.withdrawn.peak_day, "wPeak"), (est.water.consumed.avg, "cAvg"),
                     (est.water.returned.avg, "rAvg"), (est.water.withdrawn_annual_mg, "wAnn"), (est.water.to_sewer, "sewer")):
        assert (got.p10, got.p50, got.p90) == (E[key]["lo"], E[key]["mid"], E[key]["hi"])


def test_lake_source_and_json():
    p = wl.place("Acme township, MI")       # on Grand Traverse Bay
    est = wl.Site(place=p, facility=wl.DataCenter(it_mw=100, cooling="lake"), source="lake").estimate()
    assert est.water.lake_source and est.model_version == "1.2"
    assert wl.Estimate.model_validate_json(est.model_dump_json()) == est
