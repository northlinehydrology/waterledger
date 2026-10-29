"""physics.py is the one home of the cooling model's equations and ranges: the per-run loop (cooling.py) samples the same
draws and computes the same hourly rates, whether parameters are scalars or (runs, 1) arrays. The vectorized draws are
scaled in one step (lo + (hi - lo) * u), so they can differ from rng.uniform in the last bit; hence a 1e-14 tolerance."""
import numpy as np

from waterledger_models.datacenter import cooling as cw, physics as ph


def test_vectorized_draws_match_the_loop():
    loop = cw.sample(np.random.default_rng(7), 50)
    vec = ph.sample_parameters(50, seed=7)
    for k in ph.PARAMETERS:
        np.testing.assert_allclose(vec[k], [r[k] for r in loop], rtol=1e-14)


def test_staff_draws_match_the_loop():
    loop = np.array(cw.staff_runs(50))
    vec = ph.sample_staff(50)
    np.testing.assert_allclose(np.stack([vec[k] for k in ph.STAFF_PARAMETERS], axis=1), loop, rtol=1e-14)


def test_hourly_rates_vectorized_equal_per_run():
    h = np.arange(24 * 30)
    tdb = 18 + 10 * np.sin(2 * np.pi * h / 24)
    twb = ph.wet_bulb(tdb, 60.0)
    vec = {k: v[:, None] for k, v in ph.sample_parameters(12).items()}
    runs = cw.sample(np.random.default_rng(7), 12)
    for design in ph.DESIGNS:
        W, C, R = ph.hourly_rates(tdb, twb, design, vec)
        for i, p in enumerate(runs):
            w, c, r = cw.hourly(tdb, twb, design, p)
            np.testing.assert_allclose(W[i], w, rtol=1e-12, atol=1e-18)
            np.testing.assert_allclose(C[i], c, rtol=1e-12, atol=1e-18)
            np.testing.assert_allclose(R[i], r, rtol=1e-12, atol=1e-18)
