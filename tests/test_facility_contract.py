"""The facility contract (design 0010): every registered type gives what Site and Estimate read, and nothing downstream reads a type's own fields.
The conformance tests run over every type in the registry, so a new type is held to them by registering it."""
import pytest

import waterledger as wl
from waterledger.facilities import REGISTRY, AnyFacility, BatteryCellPlant, DataCenter, Facility

EXAMPLES = {"data_center": DataCenter(it_mw=300, cooling="towers"), "battery_cell_plant": BatteryCellPlant(capacity_gwh=40)}


def test_every_type_has_an_example():
    assert set(EXAMPLES) == set(REGISTRY)


@pytest.mark.parametrize("kind", sorted(REGISTRY))
def test_type_declares_the_contract(kind):
    f = EXAMPLES[kind]
    cls = type(f)
    assert cls is REGISTRY[kind] and issubclass(cls, Facility) and f.kind == kind
    assert cls.DESIGNS and set(cls.EVAPORATIVE) <= set(cls.DESIGNS) and f.design_name in cls.DESIGNS
    value, unit = f.size
    assert value > 0 and isinstance(unit, str) and unit
    for d in cls.DESIGNS:
        g = f.with_design(d)
        assert g.design_name == d and type(g) is cls
    with pytest.raises(ValueError, match="no design"):
        f.with_design("steam")


@pytest.mark.parametrize("kind", sorted(REGISTRY))
def test_bmi_config_initializes(kind):
    import importlib
    f = EXAMPLES[kind]
    for d in f.DESIGNS:
        entry, cfg = f.with_design(d).bmi_config(design_db=31.5, end_time=7200)
        if kind == "battery_cell_plant":       # without a forcing file a cell plant needs its design enthalpy too
            cfg["parameters"] = {**cfg.get("parameters", {}), "design_h": 70.0}
        mod, name = entry.split(":")
        m = getattr(importlib.import_module(mod), name)()
        m.initialize(cfg)
        assert m.get_end_time() == 7200
        m.finalize()


def test_site_reads_any_type_and_a_dict_without_kind_is_a_data_center():
    from pydantic import TypeAdapter
    A = TypeAdapter(AnyFacility)
    assert isinstance(A.validate_python({"it_mw": 100}), DataCenter)
    assert isinstance(A.validate_python({"kind": "battery_cell_plant", "capacity_gwh": 10}), BatteryCellPlant)
    with pytest.raises(Exception):
        A.validate_python({"kind": "battery_cell_plant", "it_mw": 10})


def test_hooks_default_to_none():
    class Bare(Facility):
        kind: str = "bare"
    assert Bare().backup_generator_mw() is None and Bare().cooling_blowdown(None) is None


def test_data_center_hooks():
    from waterledger_models import runoff
    f = DataCenter(it_mw=300)
    assert runoff.generators(f.backup_generator_mw()) == runoff.fuel(300)
    assert BatteryCellPlant(capacity_gwh=40).backup_generator_mw() is None     # none until a source sizes them [A]


def test_battery_refuses_septic_and_reuse():
    """Checked before any data is read, so no place is needed."""
    f = BatteryCellPlant(capacity_gwh=10)
    for w in ("septic", "reuse"):
        site = type("S", (), {"wastewater": w, "place": None})()
        with pytest.raises(ValueError, match="sewer' or 'water'"):
            f.results(site)


# with place data and weather (nightly)

PLACES = ("Gaines charter township, MI", "Columbus city, OH", "Austin city, TX")


@pytest.mark.live
@pytest.mark.parametrize("query", PLACES)
@pytest.mark.parametrize("kind", sorted(REGISTRY))
def test_estimate_conforms(kind, query):
    """Every type at a place: the roles are there, the books close on the middle estimate, and the comparisons, before and after, loads and levels come
    from the roles alone."""
    est = wl.Site(place=wl.place(query), facility=EXAMPLES[kind]).estimate()
    w, e = est.water, est.electricity
    gain = w.condensate.avg.p50 if w.condensate else 0.0
    assert w.withdrawn.avg.p50 + gain == pytest.approx(w.consumed.avg.p50 + w.returned.avg.p50, rel=1e-9)
    for r in (w.withdrawn.avg, w.consumed.avg, w.returned.avg, w.withdrawn.peak_day, e.avg_mw, e.peak_mw):
        assert 0 <= r.p10 <= r.p50 <= r.p90
    assert w.withdrawn.peak_day.p50 >= w.withdrawn.avg.p50 and e.peak_mw.p50 >= e.avg_mw.p50
    assert est.site.source in ("muni", "wells") and est.site.wastewater in ("sewer", "septic", "water")
    assert est.before_after and est.site_loads and est.levels and est.power_plants
    assert est.equivalents is not None


@pytest.mark.live
def test_battery_designs_order_and_lake():
    p = wl.place("Muskegon city, MI")
    est = {d: wl.Site(place=p, facility=BatteryCellPlant(capacity_gwh=40, design=d), source="lake" if d == "lake" else None).estimate() for d in BatteryCellPlant.DESIGNS}
    w = {d: e.water.withdrawn.avg.p50 for d, e in est.items()}
    assert w["dry"] < min(w["assist"], w["hybrid"]) and max(w["assist"], w["hybrid"]) < w["towers"] < w["lake"]
    lake = est["lake"].water
    assert lake.lake_source and lake.to_source is not None and lake.to_source.p50 > 0.9 * lake.returned.avg.p50
    towers = est["towers"]
    blow = [r for r in towers.site_loads if r.key == "cooling_p"]
    assert blow and 0 < towers.extras["blowdown_avg"].p50 < towers.water.to_sewer.p50
    assert not [r for r in towers.before_after if r.key == "fuel"]          # no backup generators sized for a cell plant [A]
    assert towers.electricity.pue is None and towers.electricity.fuel_mw.p50 > 0
    assert est["dry"].grid_water is not None and est["lake"].grid_water is None


@pytest.mark.live
def test_battery_by_design():
    c = wl.Site(place=wl.place("Gaines charter township, MI"), facility=BatteryCellPlant(capacity_gwh=40)).by_design()
    assert set(c.designs) == {"dry", "hybrid", "towers"} and c.designs["dry"].evaporated.p50 < c.designs["towers"].evaporated.p50
