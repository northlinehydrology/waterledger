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
    assert est.water.lake_source and est.model_version == "1.3"
    assert wl.Estimate.model_validate_json(est.model_dump_json()) == est


def test_to_bmi_config_runs(tmp_path):
    import numpy as np

    from waterledger_models.datacenter.bmi import CoolingWaterBmi
    site = wl.Site(place=wl.place("Gaines charter township, MI"), facility=wl.DataCenter(it_mw=300, cooling="hybrid"))
    entry, cfg = site.to_bmi_config(tmp_path / "site.yaml", end_time=7200)
    assert entry.endswith(":CoolingWaterBmi") and cfg["design"] == "hybrid" and cfg["it_capacity_mw"] == 300
    m = CoolingWaterBmi()
    m.initialize(str(tmp_path / "site.yaml"))
    m.set_value("atmosphere_bottom_air__temperature", np.array([30.0]))
    m.set_value("atmosphere_bottom_air_water_vapor__relative_saturation", np.array([60.0]))
    m.update()
    assert m.get_value("data_center_cooling_water__withdrawal_volume_flux", np.empty(1))[0] > 0
    lake = wl.Site(place=wl.place("Acme township, MI"), facility=wl.DataCenter(it_mw=100, cooling="lake"), source="lake")
    assert lake.to_bmi_config()[0].endswith(":LakeCoolingBmi")
