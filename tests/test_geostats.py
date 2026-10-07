"""The geostatistics engine behind the Map view.

Kriging has the advantage, for testing, of several exact answers.  It
is an exact interpolator; its weights sum to one by construction; with
no spatial structure it must return the mean with a known variance;
with a linear variogram in one dimension it must reproduce the
Brownian bridge -- linear interpolation between the two neighbours,
with variance 2s·ab/(a+b).  Those are checked to machine precision,
which is a stronger test than agreeing with another program, since the
other program might share a mistake.

The fast leave-one-out cross-validation is checked against simply
refitting the system n times.
"""

from __future__ import annotations

import numpy as np
import pytest

from birds.coords import (
    geodetic_to_ecef_km,
    km_per_degree_lat,
    km_per_degree_lon,
)
from birds.geostats import (
    MARGINAL_N,
    MIN_SAMPLES,
    MODELS,
    RELIABLE_N,
    WGS84_PRJ,
    Z95,
    EmpiricalVariogram,
    OrdinaryKriging,
    VariogramModel,
    analyse,
    back_transform,
    cross_validate,
    empirical_variogram,
    fit_variogram,
    hull_mask,
    make_grid,
    merge_coincident,
    read_esri_ascii,
    reliability,
    write_esri_ascii,
)


def _line(x):
    """Points along a straight line, in km, for one-dimensional checks."""
    x = np.asarray(x, float)
    return np.column_stack([x, np.zeros_like(x), np.zeros_like(x)])


def _field(n=80, seed=42, lat0=19.2, lon0=-99.0, side_km=50.0):
    """Random sample locations over a square of *side_km* near lat0."""
    rng = np.random.default_rng(seed)
    xk = rng.uniform(0, side_km, n)
    yk = rng.uniform(0, side_km, n)
    lon = lon0 + xk / km_per_degree_lon(lat0)
    lat = lat0 + yk / km_per_degree_lat(lat0)
    return lon, lat, xk, yk, rng


# ---------------------------------------------------------------------------
# Distances
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("a, b, km", [
    ((0.0, 0.0), (0.0, 1.0), 110.574),    # one degree along a meridian
    ((0.0, 0.0), (1.0, 0.0), 111.320),    # one degree along the equator
    ((0.0, 60.0), (1.0, 60.0), 55.800),   # one degree along 60° N
])
def test_distances_through_the_earth_match_the_surface_at_field_scale(
        a, b, km):
    """The chord over a degree is shorter than the arc by about 1e-5."""
    p, q = geodetic_to_ecef_km([a[0], b[0]], [a[1], b[1]])
    assert np.linalg.norm(p - q) == pytest.approx(km, rel=2e-5)


def test_the_utm_fallback_reads_the_same_ellipsoid_and_agrees_with_pyproj():
    """The constants moved to one definition in birds.coords; the Snyder
    series that stands in for pyproj must not have moved with them."""
    import pandas as pd

    from birds import coords

    if not coords._HAS_PYPROJ:
        pytest.skip("pyproj not installed")
    df = pd.DataFrame({"E": [485000.0, 500000.0, 714000.0],
                       "N": [2148000.0, 2100000.0, 2200000.0]})
    lat_f, lon_f = coords._from_utm_fallback(df, "E", "N", None, None,
                                             14, "N")
    lat_p, lon_p = coords.from_utm(df, "E", "N", fixed_zone=14,
                                   fixed_hemisphere="N")
    assert np.max(np.abs(lat_f - lat_p)) < 1e-8
    assert np.max(np.abs(lon_f - lon_p)) < 1e-8


def test_ecef_places_the_poles_on_the_short_axis():
    """The ellipsoid's polar radius is 6356.752 km."""
    north = geodetic_to_ecef_km([0.0], [90.0])[0]
    assert north[2] == pytest.approx(6356.752, abs=1e-3)
    assert abs(north[0]) < 1e-9 and abs(north[1]) < 1e-9


# ---------------------------------------------------------------------------
# Variogram models
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", MODELS)
def test_a_model_is_zero_at_the_origin_and_jumps_by_the_nugget(kind):
    m = VariogramModel(kind, 0.3, 2.0, 10.0)
    assert m(0.0) == 0.0
    assert m(1e-9) == pytest.approx(0.3, abs=1e-6)


@pytest.mark.parametrize("kind", ["exponential", "gaussian"])
def test_the_range_is_where_the_model_reaches_95_percent(kind):
    """The effective-range convention, for the two that never arrive."""
    m = VariogramModel(kind, 0.0, 1.0, 12.0)
    assert m(12.0) == pytest.approx(1 - np.exp(-3), rel=1e-12)
    assert m(12.0) == pytest.approx(0.95, abs=0.001)


def test_the_spherical_model_reaches_the_sill_at_the_range_and_stays():
    m = VariogramModel("spherical", 0.2, 1.0, 8.0)
    assert m(8.0) == pytest.approx(1.0)
    assert m(50.0) == pytest.approx(1.0)
    assert m(4.0) == pytest.approx(0.2 + 0.8 * (1.5 * 0.5 - 0.5 * 0.125))


@pytest.mark.parametrize("kind", MODELS)
def test_a_model_never_decreases_with_distance(kind):
    h = np.linspace(0, 100, 2001)
    assert np.all(np.diff(VariogramModel(kind, 0.1, 1.0, 20.0)(h)) >= 0)


@pytest.mark.parametrize("args", [
    ("cubic", 0.0, 1.0, 1.0),
    ("spherical", -0.1, 1.0, 1.0),
    ("spherical", 0.5, 0.4, 1.0),
    ("spherical", 0.0, 1.0, 0.0),
])
def test_an_impossible_model_is_refused(args):
    with pytest.raises(ValueError):
        VariogramModel(*args)


# ---------------------------------------------------------------------------
# The experimental variogram
# ---------------------------------------------------------------------------

def test_the_experimental_variogram_by_hand():
    """Three points at 0, 1 and 2 km with values 0, 1 and 3.

    Pairs at 1 km: (0,1) and (1,3), squared differences 1 and 4, so
    γ = (1 + 4) / (2·2) = 1.25.  The pair at 2 km: (0,3), so γ = 9/2.
    """
    emp = empirical_variogram(_line([0, 1, 2]), [0.0, 1.0, 3.0],
                              n_lags=3, max_lag_km=3.0)
    assert emp.lag_km == pytest.approx([1.0, 2.0])
    assert emp.gamma == pytest.approx([1.25, 4.5])
    assert list(emp.pairs) == [2, 1]
    assert emp.variance == pytest.approx(np.var([0, 1, 3], ddof=1))


def test_the_default_lag_limit_is_half_the_largest_separation():
    emp = empirical_variogram(_line([0, 1, 2, 3, 4, 10]),
                              np.arange(6.0), n_lags=4)
    assert emp.max_lag_km == pytest.approx(5.0)
    assert emp.lag_km.max() <= 5.0


def test_the_default_classes_aim_for_thirty_pairs_each():
    lon, lat, *_ = _field(n=80)
    xyz = geodetic_to_ecef_km(lon, lat)
    emp = empirical_variogram(xyz, np.arange(80.0))
    assert 4 <= len(emp.lag_km) <= 15
    assert emp.pairs.sum() >= 30 * len(emp.lag_km) * 0.5


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", MODELS)
def test_the_fit_recovers_a_known_model(kind):
    """From a variogram that is exactly the model, nothing else."""
    true = VariogramModel(kind, 0.2, 1.5, 18.0)
    h = np.linspace(1.5, 30, 14)
    emp = EmpiricalVariogram(h, true(h), np.full(14, 50), 30.0, 1.5)
    fit = fit_variogram(emp, kind)
    assert fit.converged
    assert fit.model.nugget == pytest.approx(0.2, abs=1e-4)
    assert fit.model.sill == pytest.approx(1.5, rel=1e-4)
    assert fit.model.range_km == pytest.approx(18.0, rel=1e-4)


def test_a_fixed_nugget_is_held_fixed():
    true = VariogramModel("exponential", 0.0, 1.0, 10.0)
    h = np.linspace(1, 20, 10)
    emp = EmpiricalVariogram(h, true(h) + 0.3, np.full(10, 40), 20.0, 1.3)
    fit = fit_variogram(emp, "exponential", nugget=0.0)
    assert fit.model.nugget == 0.0


def test_too_few_lag_classes_to_fit_are_refused():
    emp = EmpiricalVariogram(np.array([1.0, 2.0, 3.0]),
                             np.array([0.5, 0.8, 1.0]),
                             np.array([10, 10, 10]), 3.0, 1.0)
    with pytest.raises(ValueError, match="lag classes"):
        fit_variogram(emp, "spherical")


def test_a_variogram_that_never_levels_off_is_flagged():
    """A trend rises past every lag measured; the range has nowhere to
    settle, and the fit says so instead of reporting a range as if it
    meant something."""
    h = np.linspace(1, 20, 10)
    emp = EmpiricalVariogram(h, 0.05 * h ** 1.5, np.full(10, 40), 20.0, 1.0)
    fit = fit_variogram(emp, "spherical")
    assert "upper bound" in fit.message


# ---------------------------------------------------------------------------
# Ordinary kriging: exact answers
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("nugget", [0.0, 0.4])
def test_kriging_honours_the_data_exactly(nugget):
    """At a sampled location: the datum, with no variance -- even with a
    nugget, which makes the surface jump there rather than miss it."""
    rng = np.random.default_rng(3)
    xyz = rng.uniform(0, 30, (12, 3))
    z = rng.normal(size=12)
    ok = OrdinaryKriging(xyz, z,
                         VariogramModel("spherical", nugget, 1.0, 15.0))
    est, var = ok.predict(xyz)
    assert est == pytest.approx(z, abs=1e-10)
    assert var == pytest.approx(np.zeros(12), abs=1e-10)
    lam, mu = ok.weights(xyz[4])
    assert lam == pytest.approx(np.eye(12)[4], abs=1e-10)


@pytest.mark.parametrize("kind", MODELS)
def test_the_weights_sum_to_one(kind):
    """The unbiasedness constraint, at arbitrary targets."""
    rng = np.random.default_rng(5)
    ok = OrdinaryKriging(rng.uniform(0, 40, (15, 3)), rng.normal(size=15),
                         VariogramModel(kind, 0.1, 1.0, 20.0))
    for target in rng.uniform(-10, 50, (6, 3)):
        lam, _mu = ok.weights(target)
        assert lam.sum() == pytest.approx(1.0, abs=1e-12)


def test_with_no_spatial_structure_kriging_returns_the_mean():
    """A pure nugget: the mean everywhere, with variance c₀(1 + 1/n)."""
    rng = np.random.default_rng(7)
    xyz = rng.uniform(0, 30, (9, 3))
    z = rng.normal(size=9)
    c0 = 2.5
    ok = OrdinaryKriging(xyz, z, VariogramModel("spherical", c0, c0, 5.0))
    est, var = ok.predict(rng.uniform(40, 60, (5, 3)))
    assert est == pytest.approx(np.full(5, z.mean()), rel=1e-12)
    assert var == pytest.approx(np.full(5, c0 * (1 + 1 / 9)), rel=1e-12)


def test_midway_between_two_samples_each_weighs_half():
    ok = OrdinaryKriging(_line([0, 10]), [2.0, 6.0],
                         VariogramModel("exponential", 0.0, 1.0, 30.0))
    lam, _ = ok.weights([5.0, 0.0, 0.0])
    assert lam == pytest.approx([0.5, 0.5])


@pytest.mark.parametrize("x0", [1.0, 3.5, 7.0])
def test_a_linear_variogram_reproduces_the_brownian_bridge(x0):
    """In one dimension, γ(h) = s·h is Brownian motion.

    Given its neighbours, the value between them is their linear
    interpolation with variance 2s·ab/(a+b) -- and the samples beyond
    them carry no information at all.  Ordinary kriging has to find
    exactly that.
    """
    s = 0.7
    x = np.array([0.0, 2.0, 5.0, 9.0])
    z = np.array([1.0, 3.0, -2.0, 4.0])
    ok = OrdinaryKriging(_line(x), z,
                         lambda h: np.where(np.asarray(h) > 0, s * h, 0.0))
    est, var = ok.predict(_line([x0]))
    i = np.searchsorted(x, x0) - 1
    a, b = x0 - x[i], x[i + 1] - x0
    assert est[0] == pytest.approx((z[i] * b + z[i + 1] * a) / (a + b),
                                   abs=1e-12)
    assert var[0] == pytest.approx(2 * s * a * b / (a + b), abs=1e-12)
    lam, _ = ok.weights(_line([x0])[0])
    others = np.ones(4, bool)
    others[[i, i + 1]] = False
    assert lam[others] == pytest.approx(np.zeros(2), abs=1e-12)


def test_beyond_the_last_sample_brownian_motion_carries_it_forward():
    s = 0.7
    x = np.array([0.0, 2.0, 5.0, 9.0])
    z = np.array([1.0, 3.0, -2.0, 4.0])
    ok = OrdinaryKriging(_line(x), z,
                         lambda h: np.where(np.asarray(h) > 0, s * h, 0.0))
    est, var = ok.predict(_line([12.0]))
    assert est[0] == pytest.approx(4.0, abs=1e-12)
    assert var[0] == pytest.approx(2 * s * 3.0, abs=1e-12)


def test_uncertainty_grows_away_from_the_samples():
    rng = np.random.default_rng(11)
    xyz = rng.uniform(0, 20, (15, 3))
    ok = OrdinaryKriging(xyz, rng.normal(size=15),
                         VariogramModel("spherical", 0.0, 1.0, 10.0))
    _e, near = ok.predict(xyz[:1] + 0.1)
    _e, far = ok.predict(xyz[:1] + 50.0)
    assert far[0] > near[0]


def test_a_shared_location_is_refused_with_a_way_out():
    with pytest.raises(ValueError, match="merge_coincident"):
        OrdinaryKriging(_line([0, 1, 1]), [1.0, 2.0, 3.0],
                        VariogramModel("spherical", 0.0, 1.0, 5.0))


def test_many_targets_are_solved_in_chunks_with_the_same_answer():
    rng = np.random.default_rng(13)
    ok = OrdinaryKriging(rng.uniform(0, 20, (20, 3)), rng.normal(size=20),
                         VariogramModel("exponential", 0.1, 1.0, 8.0))
    t = rng.uniform(0, 20, (500, 3))
    whole = ok.predict(t, chunk=10_000)
    pieces = ok.predict(t, chunk=37)
    assert pieces[0] == pytest.approx(whole[0], abs=1e-12)
    assert pieces[1] == pytest.approx(whole[1], abs=1e-12)


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", MODELS)
def test_the_fast_cross_validation_equals_refitting_n_times(kind):
    """Dubrule's one-inverse formula against the obvious way."""
    rng = np.random.default_rng(1)
    xyz = rng.uniform(0, 50, (25, 3))
    z = rng.normal(size=25)
    model = VariogramModel(kind, 0.1, 1.0, 20.0)
    cv = cross_validate(OrdinaryKriging(xyz, z, model))
    for i in range(25):
        keep = np.arange(25) != i
        est, var = OrdinaryKriging(xyz[keep], z[keep], model).predict(
            xyz[i:i + 1])
        assert cv.predicted[i] == pytest.approx(est[0], abs=1e-10)
        assert cv.variance[i] == pytest.approx(var[0], abs=1e-10)


def test_the_cross_validation_statistics():
    rng = np.random.default_rng(2)
    xyz = rng.uniform(0, 30, (20, 3))
    z = rng.normal(size=20)
    cv = cross_validate(OrdinaryKriging(
        xyz, z, VariogramModel("spherical", 0.2, 1.0, 12.0)))
    err = cv.predicted - z
    assert cv.mean_error == pytest.approx(err.mean())
    assert cv.rmse == pytest.approx(np.sqrt((err ** 2).mean()))
    assert cv.mean_squared_standardized_error == pytest.approx(
        np.mean(err ** 2 / cv.variance))
    # predicting each sample by the mean of the others, done the long way
    loo_mean = np.array([np.delete(z, i).mean() for i in range(20)])
    assert cv.rmse_of_mean == pytest.approx(
        np.sqrt(np.mean((z - loo_mean) ** 2)))
    assert cv.skill == pytest.approx(1 - (cv.rmse / cv.rmse_of_mean) ** 2)


# ---------------------------------------------------------------------------
# End to end: does it tell structure from noise?
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("kind", MODELS)
def test_kriging_beats_the_mean_on_a_smooth_field(kind):
    """The question a user is really asking of the cross-validation.

    On a smooth field kriging removes nearly all the error of guessing
    the mean -- 98 to 100 % here.
    """
    lon, lat, xk, yk, _ = _field()
    values = np.exp(1 + 0.8 * np.sin(xk / 12) + 0.6 * np.cos(yk / 15))
    cv = analyse(lon, lat, values, model=kind).cross_validation
    assert cv.skill > 0.9


@pytest.mark.parametrize("kind", MODELS)
def test_kriging_adds_nothing_on_noise_and_says_so(kind):
    """On values with no spatial structure skill sits at zero, and the
    kriging variance is honest about it: mean squared standardised
    error near 1."""
    lon, lat, _xk, _yk, rng = _field()
    values = np.exp(rng.normal(1, 0.5, len(lon)))
    cv = analyse(lon, lat, values, model=kind).cross_validation
    assert abs(cv.skill) < 0.1
    assert 0.7 < cv.mean_squared_standardized_error < 1.5


# ---------------------------------------------------------------------------
# The whole analysis
# ---------------------------------------------------------------------------

def test_unusable_rows_are_counted_not_lost():
    lon, lat, xk, _yk, _ = _field(n=30)
    values = 1.0 + xk
    lon[0] = np.nan
    values[1] = -2.0          # cannot be logged
    values[2] = 0.0           # nor this
    a = analyse(lon, lat, values, transform="log")
    assert a.n_input == 30
    assert a.n_excluded == 3
    assert a.n == 27


def test_negative_values_are_kept_when_not_logging():
    lon, lat, xk, _yk, _ = _field(n=30)
    values = xk - 25.0        # half of them negative
    a = analyse(lon, lat, values, transform="none")
    assert a.n_excluded == 0


def test_duplicate_analyses_of_one_outcrop_are_folded_together():
    lon, lat, xk, _yk, _ = _field(n=20)
    lon = np.append(lon, lon[3])
    lat = np.append(lat, lat[3])
    values = np.append(1.0 + xk, 99.0)
    a = analyse(lon, lat, values, transform="none")
    assert a.n_folded == 1
    assert a.n == 20
    i = int(np.argmin(np.hypot(a.lon - lon[3], a.lat - lat[3])))
    assert a.values[i] == pytest.approx((1.0 + xk[3] + 99.0) / 2)


def test_too_few_samples_are_refused():
    lon, lat, xk, _yk, _ = _field(n=MIN_SAMPLES - 1)
    with pytest.raises(ValueError, match="at least"):
        analyse(lon, lat, 1.0 + xk)


def test_identical_values_are_refused():
    lon, lat, *_ = _field(n=20)
    with pytest.raises(ValueError, match="nothing to interpolate"):
        analyse(lon, lat, np.full(20, 3.0))


def test_a_model_set_by_hand_is_used_as_given():
    lon, lat, xk, _yk, _ = _field(n=30)
    mine = VariogramModel("gaussian", 0.05, 0.9, 7.5)
    a = analyse(lon, lat, 1.0 + xk, model=mine)
    assert a.model is mine
    assert a.fit.message == "set by hand"


def test_the_log_surface_is_reported_as_a_median_with_its_interval():
    lon, lat, xk, yk, _ = _field(n=40)
    values = np.exp(1 + 0.5 * np.sin(xk / 10))
    a = analyse(lon, lat, values, transform="log")
    p = a.predict(lon[:5], lat[:5])
    assert p.estimate == pytest.approx(values[:5], rel=1e-8)   # exact there
    q = a.predict([lon.mean()], [lat.mean()])
    assert q.lower[0] < q.estimate[0] < q.upper[0]
    # symmetric in logarithms, not in concentrations
    assert np.log(q.upper[0]) - np.log(q.estimate[0]) == pytest.approx(
        Z95 * q.sd[0])


def test_back_transform_without_logs_is_symmetric():
    centre, lo, hi = back_transform(np.array([5.0]), np.array([1.0]), "none")
    assert (centre[0], lo[0], hi[0]) == pytest.approx((5.0, 5 - Z95, 5 + Z95))


def test_the_prediction_keeps_the_shape_of_the_grid():
    lon, lat, xk, _yk, _ = _field(n=30)
    a = analyse(lon, lat, 1.0 + xk)
    g = make_grid(lon.min(), lon.max(), lat.min(), lat.max(), cells_across=20)
    glon, glat = g.mesh()
    p = a.predict(glon, glat)
    assert p.estimate.shape == glon.shape == (g.nrows, g.ncols)


@pytest.mark.parametrize("n, word", [
    (MARGINAL_N - 1, "little value"),
    (MARGINAL_N, "marginal"),
    (RELIABLE_N, "reliable"),
])
def test_the_reliability_verdict_follows_webster_and_oliver(n, word):
    assert word in reliability(n)


# ---------------------------------------------------------------------------
# Grid, hull, export
# ---------------------------------------------------------------------------

def test_the_grid_covers_the_frame_in_square_cells():
    g = make_grid(-99.5, -98.0, 18.9, 19.3, cells_across=60)
    assert g.cell_deg == pytest.approx(1.5 / 60)
    assert g.west + g.ncols * g.cell_deg >= -98.0 - 1e-12
    assert g.south + g.nrows * g.cell_deg >= 19.3 - 1e-12
    assert g.lat_centres[0] < g.lat_centres[-1]            # row 0 is south
    assert g.lon_centres[0] == pytest.approx(-99.5 + g.cell_deg / 2)


def test_the_hull_keeps_inside_and_drops_outside():
    lon = np.array([0.0, 1.0, 0.0, 1.0, 0.5])
    lat = np.array([0.0, 0.0, 1.0, 1.0, 0.5])
    inside = hull_mask(lon, lat, np.array([0.5, 0.9, 1.5, -0.2]),
                       np.array([0.5, 0.1, 0.5, 0.5]))
    assert list(inside) == [True, True, False, False]


def test_a_buffer_lets_the_surface_run_past_the_hull():
    lon = np.array([0.0, 1.0, 0.0, 1.0])
    lat = np.array([0.0, 0.0, 1.0, 1.0])
    km = float(km_per_degree_lon(0.5))
    point = (np.array([1.05]), np.array([0.5]))         # 0.05° east
    assert not hull_mask(lon, lat, *point)[0]
    assert hull_mask(lon, lat, *point, buffer_km=0.06 * km)[0]
    assert not hull_mask(lon, lat, *point, buffer_km=0.04 * km)[0]


def test_samples_on_one_line_have_no_hull():
    lon = np.array([0.0, 1.0, 2.0])
    inside = hull_mask(lon, lon, np.array([1.0]), np.array([1.0]))
    assert not inside[0]


def test_the_esri_ascii_grid_round_trips(tmp_path):
    g = make_grid(-99.0, -98.0, 19.0, 19.5, cells_across=4)
    values = np.arange(g.nrows * g.ncols, dtype=float).reshape(
        g.nrows, g.ncols) * 1.25
    values[0, 0] = np.nan
    path = write_esri_ascii(tmp_path / "cu.asc", g, values)
    g2, back = read_esri_ascii(path)
    assert (g2.ncols, g2.nrows) == (g.ncols, g.nrows)
    assert g2.cell_deg == pytest.approx(g.cell_deg)
    assert (g2.west, g2.south) == pytest.approx((g.west, g.south))
    assert np.isnan(back[0, 0])
    assert back[1:] == pytest.approx(values[1:])


def test_the_esri_ascii_grid_is_written_north_first(tmp_path):
    """The format's order, which a GIS reads as given."""
    g = make_grid(0.0, 2.0, 0.0, 1.0, cells_across=2)      # 2 cols, 1 row
    g = type(g)(g.west, g.south, g.cell_deg, 2, 2)
    values = np.array([[1.0, 2.0],      # south row
                       [3.0, 4.0]])     # north row
    path = write_esri_ascii(tmp_path / "g.asc", g, values)
    lines = path.read_text().splitlines()
    assert lines[0].split() == ["ncols", "2"]
    assert lines[5].split()[0] == "NODATA_value"
    assert [float(v) for v in lines[6].split()] == [3.0, 4.0]
    assert [float(v) for v in lines[7].split()] == [1.0, 2.0]


def test_the_projection_file_declares_wgs84(tmp_path):
    g = make_grid(0.0, 1.0, 0.0, 1.0, cells_across=2)
    path = write_esri_ascii(tmp_path / "g.asc", g, np.zeros((2, 2)))
    prj = path.with_suffix(".prj").read_text()
    assert prj == WGS84_PRJ
    assert "6378137.0,298.257223563" in prj


def test_a_grid_of_the_wrong_shape_is_refused(tmp_path):
    g = make_grid(0.0, 1.0, 0.0, 1.0, cells_across=2)
    with pytest.raises(ValueError):
        write_esri_ascii(tmp_path / "g.asc", g, np.zeros((3, 3)))


def test_merge_coincident_leaves_distinct_samples_alone():
    lon = np.array([-99.0, -99.1, -99.2])
    lat = np.array([19.0, 19.1, 19.2])
    out = merge_coincident(lon, lat, np.array([1.0, 2.0, 3.0]))
    assert out[3] == 0
    assert out[2] == pytest.approx([1.0, 2.0, 3.0])
