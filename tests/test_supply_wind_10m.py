"""Wind from a forcing's 10 m wind (design 0018, section 2): the month-by-hour shear table recovers a known shear, the chain from 10 m reads as
ERA5's chain from 100 m when the table carries the same exponent, the day-night shape follows the table, and no hour beats the Betz limit."""
import numpy as np
import pytest

from waterledger_models.supply import wind

T = np.arange(np.datetime64("2021-01-01T00"), np.datetime64("2024-01-01T00"), np.timedelta64(1, "h"))
LON = -85.3
CENTRAL = {"shear_scale": 1.0, "losses": 0.15, "resource": 1.0}


def _known_table():
    m, h = np.meshgrid(np.arange(12), np.arange(24), indexing="ij")
    night = (h < 7) | (h >= 19)
    return np.where(night, 0.29, 0.16) + 0.01 * np.cos(2 * np.pi * m / 12)


def test_shear_table_recovers_a_known_shear():
    rng = np.random.default_rng(4)
    u10, v10 = rng.weibull(2.0, len(T)) * 4.0, rng.normal(0, 1.5, len(T))
    alpha = _known_table()[wind.month(T), wind.solar_hour(T, LON)]
    k = 10.0 ** alpha
    tab = wind.shear_table(T, LON, u10, v10, u10 * k, v10 * k)
    assert tab.shape == (12, 24) and np.abs(tab - _known_table()).max() < 1e-12


def test_from_10m_reads_as_the_era5_chain_with_the_same_shear():
    """10 m to the hub at alpha is 10 m to 100 m at alpha and then 100 m to the hub at alpha: wind.hourly on the 100 m speed it implies."""
    rng = np.random.default_rng(5)
    u10, v10 = rng.weibull(2.0, len(T)) * 4.5, np.zeros(len(T))
    tab = np.full((12, 24), 0.2)
    got = wind.hourly_from_10m(T, LON, u10, v10, tab, CENTRAL)
    want = wind.hourly(u10 * 10.0 ** 0.2, v10, {"alpha": 0.2, "losses": 0.15, "resource": 1.0})
    assert np.abs(got - want).max() < 1e-12


def test_night_shear_moves_the_energy_into_the_night():
    """The same 10 m wind every hour: with the table's stronger night shear, nights make more than days."""
    u10 = np.full(len(T), 5.0)
    out = wind.hourly_from_10m(T, LON, u10, np.zeros(len(T)), _known_table(), CENTRAL)
    h = wind.solar_hour(T, LON)
    night, day = (h < 5) | (h >= 21), (h >= 10) & (h < 15)
    assert out[night].mean() > 1.5 * out[day].mean()
    draws = wind.hourly_from_10m(T, LON, u10, np.zeros(len(T)), _known_table(),
                                 {"shear_scale": np.array([[0.85], [1.15]]), "losses": np.array([[0.15]]), "resource": np.array([[1.0]])})
    assert draws.shape == (2, len(T)) and draws[1].sum() > draws[0].sum()


@pytest.mark.parametrize("rho", [0.95, 1.0, 1.1, 1.225, 1.3, 1.45])
def test_no_hour_beats_the_betz_limit(rho):
    """The energy bound: the turbine never makes more than 16/27 of the wind's kinetic energy through its rotor at the hour's air density, over
    the densities of U.S. wind sites below about 2,000 m [A]; the curve is at 1.225 kg/m3 and is not corrected for density."""
    v = np.linspace(0.1, 30.0, 6000)
    power = wind.power_curve(v) * wind.RATED_KW * 1e3
    betz = 16 / 27 * 0.5 * rho * np.pi * (wind.ROTOR_M / 2) ** 2 * v ** 3
    assert (power <= betz).all()


def test_the_table_needs_every_month_and_hour():
    short = T[:24 * 20]
    with pytest.raises(ValueError):
        wind.shear_table(short, LON, np.ones(len(short)), np.zeros(len(short)), np.ones(len(short)), np.zeros(len(short)))
