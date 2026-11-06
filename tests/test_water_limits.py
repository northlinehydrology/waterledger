"""Water limits, dry mode and return loads on the cooling model (design 0006): with no limit nothing changes, to the bit; under any limit the
heat still goes (to dry coolers and chillers, or is reported as not removed), water, energy and dissolved mass close, and the limit is met."""
import numpy as np
import pytest

from waterledger_models.datacenter import physics as ph

T = np.arange(-25.0, 46.0, 1.0)
RH = np.full_like(T, 55.0)
W = ph.wet_bulb(T, RH)
DESIGN_DB = 33.0
DRAWS = {**{k: v[:, None] for k, v in ph.sample_parameters(60).items()}, **ph.central_limits(), "design_db": DESIGN_DB}
CENTRAL = {**ph.central_parameters(), **ph.central_limits(), "design_db": DESIGN_DB}


def _limits(design, p=DRAWS):
    w = ph.hourly_rates(T, W, design, p, RH)[0]
    return [np.inf, 0.75 * w.max(), 0.3 * w.max(), 0.0]


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_no_limit_changes_nothing(design):
    w, c, r = ph.hourly_rates(T, W, design, DRAWS, RH)
    power, heat = ph.hourly_heat_power(T, W, design, DRAWS, RH)
    o = ph.hourly_limited(T, W, design, DRAWS, np.inf, RH)
    for a, b in ((o["withdrawn"], w), (o["consumed"], c), (o["returned"], r), (o["power"], power), (o["heat"], heat), (o["removed"], heat)):
        assert np.array_equal(a, np.broadcast_to(b, a.shape))
    assert (o["unremoved"] == 0).all() and (o["shed"] == 0).all() and (o["wet_frac"] == 1).all()


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_the_limit_is_met(design):
    for limit in _limits(design):
        o = ph.hourly_limited(T, W, design, DRAWS, limit, RH)
        cooling = o["withdrawn"] - o["topup"] - o["humidify"]
        assert (cooling <= np.maximum(limit - o["topup"] - o["humidify"], 0.0) * (1 + 1e-9) + 1e-15).all()


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_water_closes_under_any_limit(design):
    for limit in _limits(design):
        o = ph.hourly_limited(T, W, design, DRAWS, limit, RH)
        assert np.allclose(o["withdrawn"] + o["condensate"], o["consumed"] + o["returned"])
        assert all((o[k] >= -1e-12).all() for k in ("evap", "drift", "blow", "withdrawn", "consumed", "returned"))


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_heat_is_removed_or_reported(design):
    for limit in _limits(design):
        o = ph.hourly_limited(T, W, design, DRAWS, limit, RH)
        assert np.allclose(o["removed"] + o["unremoved"], o["heat"])
        assert ((o["shed"] >= 0) & (o["shed"] <= 1)).all() and ((o["wet_frac"] >= 0) & (o["wet_frac"] <= 1)).all()


@pytest.mark.parametrize("design", ("assist", "hybrid"))
def test_energy_closes_at_the_limited_wet_share(design):
    """Where nothing is shed, the hour is hourly_heat_power's at the limited wet share, whose energy closes (test_balances); its power is that hour's."""
    limit = _limits(design)[2]
    o = ph.hourly_limited(T, W, design, DRAWS, limit, RH)
    power, heat = ph.hourly_heat_power(T, W, design, {**DRAWS, "wet_frac": o["wet_frac"]}, RH)
    kept = o["shed"] == 0
    assert np.allclose(o["power"][kept], power[kept]) and np.allclose(o["heat"][kept], heat[kept])


@pytest.mark.parametrize("design", ("assist", "hybrid"))
def test_electricity_rises_as_the_limit_tightens(design):
    w = ph.hourly_rates(T, W, design, CENTRAL, RH)[0]
    powers = [ph.hourly_limited(T, W, design, CENTRAL, f * w.max(), RH)["power"] for f in (np.inf, 1.0, 0.6, 0.3, 0.0)]
    for a, b in zip(powers, powers[1:]):
        assert (b >= a - 1e-9).all()


@pytest.mark.parametrize("design", ("assist", "hybrid"))
def test_dry_mode_runs_as_the_dry_design(design):
    """A limit of zero takes all the evaporative duty away: the plant runs as dry coolers and chillers, the dry design's power, where its capacity holds."""
    o = ph.hourly_limited(T, W, design, CENTRAL, 0.0, RH)
    dry = ph.hourly_heat_power(T, W, "dry", CENTRAL, RH)[0]
    kept = o["shed"] == 0
    assert np.allclose(o["power"][kept], dry[kept])
    assert np.allclose(o["evap"], 0.0)


def test_towers_shed_what_the_limit_cannot_cool():
    w = ph.hourly_rates(T, W, "towers", CENTRAL, RH)[0]
    o = ph.hourly_limited(T, W, "towers", CENTRAL, 0.5 * w.max(), RH)
    hot = T > 30
    assert (o["unremoved"][hot] > 0).all() and (o["power"][hot] < ph.hourly_heat_power(T, W, "towers", CENTRAL, RH)[0][hot]).all()
    assert (ph.hourly_limited(T, W, "towers", CENTRAL, 0.0, RH)["shed"] == 1).all()


def test_dry_capacity_runs_out_only_in_heat_past_the_design_point():
    """Dry mode on a hot record: no heat is left in cool hours, and what is left in hot ones grows as the air warms past the design dry-bulb."""
    p = {**CENTRAL, "dry_capacity_margin": 0.0, "dry_derate_per_k": 0.04, "utilization": 0.80}
    o = ph.hourly_limited(T, W, "hybrid", p, 0.0, RH)
    assert (o["unremoved"][T <= DESIGN_DB] == 0).all()
    assert (o["unremoved"][T > DESIGN_DB] >= 0).all() and o["unremoved"][-1] > 0
    assert (np.diff(o["unremoved"][T > DESIGN_DB]) >= -1e-12).all()


@pytest.mark.parametrize("design", ph.DESIGNS)
def test_dissolved_mass_closes(design):
    """Every gallon taken for cooling carries its dissolved mass to the sewer, the air or what stays behind; evaporation carries none."""
    for limit in _limits(design):
        o = ph.hourly_limited(T, W, design, DRAWS, limit, RH)
        sewer, drift, left = ph.dissolved_mass_split(o)
        assert np.allclose(sewer + drift + left, o["withdrawn"])
        assert all((x >= -1e-12).all() for x in (sewer, drift, left))


def test_blowdown_concentrates_by_the_cycles():
    """Towers: blowdown's concentration is the intake's times the cycles of concentration, and drift's share of the mass is drift's share of the liquid
    leaving, drift x circulation x (cycles - 1) / evaporation: a few percent (about 1-16% across the ranges), since blowdown is small beside the flow
    the drift share is taken of."""
    o = ph.hourly_limited(T, W, "towers", CENTRAL, np.inf, RH)
    sewer, drift, _ = ph.dissolved_mass_split(o)
    hot = o["blow"] > 0
    assert np.allclose(sewer[hot] / o["blow"][hot], CENTRAL["coc"])
    assert np.allclose(drift[hot] / o["drift"][hot], CENTRAL["coc"])
    share = drift[hot] / (sewer[hot] + drift[hot])
    assert np.allclose(share, o["drift"][hot] * (CENTRAL["coc"] - 1) / o["evap"][hot])
    assert ((share > 0.01) & (share < 0.10)).all()
