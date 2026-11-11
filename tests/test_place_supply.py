"""Power supply scenarios at a place (design 0014, step 6): est.supply. Offline with the place's weather and grid stood in for; the live test
runs Gaines on its own ERA5 cell."""
from types import SimpleNamespace

import numpy as np
import pytest

from golden import weather
from waterledger import supply
from waterledger.facility import DataCenter
from waterledger.national import era5 as E
from waterledger_models.supply import scenario as S

TIMES, T, RH = weather()
_h = np.arange(len(TIMES))
_sun = np.clip(np.sin(2 * np.pi * (_h % 24 - 6) / 24), 0, None)
WX = (np.array(TIMES, dtype="datetime64[h]") + np.timedelta64(5, "h"), 900 * _sun, 650 * _sun, 4 + 3 * np.sin(_h / 15.0), 2 + np.cos(_h / 9.0))


@pytest.fixture
def stand_ins(monkeypatch):
    monkeypatch.setattr(supply, "place_weather", lambda place: ("42.75_-85.50", TIMES, list(T), list(RH), WX, {"applied": False}))
    monkeypatch.setattr(E, "grid_factors", lambda cid, times, temps, bas: {b: {k: np.full(len(times), v) for k, v in
                        {"consumed": 300.0, "withdrawn": 12000.0, "marginal_consumed": 280.0, "marginal_withdrawn": 11000.0}.items()} for b in bas})


def _est(cooling="hybrid", ba="MISO"):
    climate = SimpleNamespace(rain_in=34.0, design_storms_in={"10": 3.6})
    place = SimpleNamespace(lat=42.85, lon=-85.6, state="MI", context=lambda: SimpleNamespace(climate=climate))
    site = SimpleNamespace(place=place, facility=DataCenter(it_mw=100, cooling=cooling), land_before="farm")
    return SimpleNamespace(site=site, grid_water=SimpleNamespace(balancing_authority=ba))


def test_est_supply_bands_at_the_sites_size(stand_ins):
    out = supply.estimate_supply(_est(), {"a": S.Scenario(), "b": S.Scenario(residual="none", gas=S.Gas("engine", "dry", unit_mw=20.0)),
                                          "c": S.Scenario(pv_share=1.0)}, n=6, storm_years=10)
    a, b, c = out["a"], out["b"], out["c"]
    assert a.share_grid.p50 == 1.0 and a.grid_water.balancing_authority == "MISO" and a.grid_water.consumed.p50 > 0
    assert b.share_gas.p50 > 0.99 and b.grid_water is None and b.gas["units"] >= 2 and b.local_consumed.p90 == 0.0
    assert 0 < c.share_pv.p50 < 1 and c.pv_mw > 100 and c.land["pv"]["fenced_acres"] > 0 and "storm_mg" in c.land["pv"]
    assert a.grid_water.consumed.p50 > c.grid_water.consumed.p50          # PV takes part of the grid's share
    for s in out.values():
        total = s.share_pv.p50 + s.share_wind.p50 + s.share_gas.p50 + s.share_grid.p50     # medians of separate shares, less any unserved load
        assert 0.99 < total <= 1.0 + 1e-9
        s.model_dump_json()


def test_lake_source_and_other_types_say_why(stand_ins):
    with pytest.raises(ValueError, match="Lake-source"):
        supply.estimate_supply(_est("lake"), {"a": S.Scenario()}, n=4)


@pytest.mark.live
def test_gaines_on_its_own_cell():
    """Gaines Charter Township, 300 MW hybrid: the grid-only scenario's grid water is the estimate's own, within the draws' sampling."""
    import waterledger as wl
    site = wl.Site(place=wl.place("Gaines charter township, MI"), facility=wl.DataCenter(it_mw=300, cooling="hybrid"))
    est = site.estimate(supply={"a": S.Scenario(), "c2": S.Scenario(pv_share=0.6, wind_share=0.6)}, supply_draws=100)
    assert est.supply["a"].grid_water.consumed.p50 == pytest.approx(est.grid_water.consumed.p50, rel=0.05)
    assert est.supply["c2"].share_grid.p50 < 0.5
