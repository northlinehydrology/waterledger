"""site.estimate(weather="local"): the model run at the place, through the same code as a region's stored results."""
import numpy as np
import pytest

import waterledger as wl
from waterledger_data import climate


def fake_weather(lat, lon, start, end, name):
    """Two years of hours: warm summers, cool winters, a daily swing."""
    t = np.arange("2023-01-01T00", "2025-01-01T00", dtype="datetime64[h]")
    h = np.arange(len(t))
    T = 10 + 14 * np.sin(2 * np.pi * (h / 8760 - 0.3)) + 5 * np.sin(2 * np.pi * h / 24)
    return [str(x) for x in t], T.tolist(), np.full(len(t), 65.0).tolist()


@pytest.fixture
def gaines(monkeypatch):
    monkeypatch.setattr(climate, "hourly_weather", fake_weather)
    return wl.Site(place=wl.place("Gaines charter township, MI"), facility=wl.DataCenter(it_mw=300, cooling="hybrid"))


def test_marked_and_differs_from_the_region(gaines):
    region, local = gaines.estimate(), gaines.estimate(weather="local")
    assert region.weather == "region" and local.weather == "local"
    assert local.water.withdrawn.avg.p50 != region.water.withdrawn.avg.p50 and local.electricity.pue.p50 > 1
    assert local.site == region.site


def test_adds_up_and_carries_comparisons(gaines):
    w = gaines.estimate(weather="local")
    assert w.water.consumed.avg.p50 + w.water.returned.avg.p50 == pytest.approx(w.water.withdrawn.avg.p50 + w.water.condensate.avg.p50)
    c = w.comparisons[0]
    assert c.percent.avg.p50 == pytest.approx(100 * (w.water.withdrawn.avg.p50 * 1e6 / 300) / c.existing)


def test_lake_source_refuses():
    p = wl.place("Acme township, MI")
    with pytest.raises(ValueError, match="Lake-source"):
        wl.Site(place=p, facility=wl.DataCenter(it_mw=300, cooling="lake"), source="lake").estimate(weather="local")


def test_unknown_weather_refused(gaines):
    with pytest.raises(ValueError, match="weather must be"):
        gaines.estimate(weather="onsite")
