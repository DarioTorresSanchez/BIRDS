"""Geostatistics for the Map view: variograms, ordinary kriging and
leave-one-out cross-validation.

Everything here works on plain arrays -- longitude, latitude and one
value per sample -- so it is tested without the interface, and nothing
beyond numpy and scipy is needed: no further licence to review and no
further package to install.

Four choices shape the rest, and each is the conservative one.

**Distances are measured through the Earth, not across a projection.**
Every sample is placed in Earth-centred Cartesian coordinates on the
WGS-84 ellipsoid and kriged there with straight-line distances.  The
chord differs from the distance along the surface by about one part in
10⁵ at 100 km, nothing is distorted anywhere on the globe, and the three
variogram models offered here are valid in three dimensions -- so
restricting them to the ellipsoid's surface keeps them valid, which
measuring along the surface would not guarantee.

**Ordinary kriging, in the variogram form, from every sample at once.**
No search neighbourhood.  Field data sets run to tens or hundreds of
samples, small enough to krige from all of them, and a neighbourhood
would add a choice the user has to make and the map would show.

**The range is the effective range.**  For all three models it is the
distance at which the variogram reaches 95 % of its sill -- exactly the
sill, for the spherical one -- so the word means the same thing
whichever model is chosen.  Other software differ: gstat in R, for one,
parameterises the exponential model by a third of this distance.

**Concentrations are kriged as logarithms by default.**  Trace-element
concentrations are compositional and close to log-normal; kriged raw,
a few high values dominate the surface and the estimate can go
negative.  Back-transformed, the kriged logarithm is the *median*
estimate, and it is reported as such: exp(ŷ), with a 95 % interval
exp(ŷ ± 1.96 σ).  The usual bias correction to the mean is notoriously
sensitive to the sill, and an honest median beats a fragile mean.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional, Union

import numpy as np
from scipy import linalg, optimize
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import ConvexHull, Delaunay, QhullError, cKDTree
from scipy.spatial.distance import cdist, pdist

from .coords import geodetic_to_ecef_km, km_per_degree_lat, km_per_degree_lon

MODELS = ("spherical", "exponential", "gaussian")
TRANSFORMS = ("none", "log")

#: Fewer samples than this and no variogram is attempted at all.
MIN_SAMPLES = 5

#: Webster & Oliver (1992): a variogram computed from fewer than about
#: 50 data is of little value, and about 100 are needed for a reliable
#: one.  Reported to the user rather than enforced.
MARGINAL_N = 50
RELIABLE_N = 100

#: Average pairs per lag class the default binning aims for -- the
#: classical rule of thumb of a few tens per class.
PAIRS_PER_LAG = 30

#: Standard-normal 97.5 % quantile, for 95 % intervals.
Z95 = 1.959963984540054

#: Samples closer than this, in km, are treated as one location.
COINCIDENT_KM = 1e-3


# ---------------------------------------------------------------------------
# Variogram models
# ---------------------------------------------------------------------------
#
# Each structure is a function of r = h / range, rising from 0 to 1.

def _spherical(r):
    r = np.minimum(r, 1.0)
    return 1.5 * r - 0.5 * r ** 3


def _exponential(r):
    return 1.0 - np.exp(-3.0 * r)


def _gaussian(r):
    return 1.0 - np.exp(-3.0 * r ** 2)


_STRUCTURE = {
    "spherical": _spherical,
    "exponential": _exponential,
    "gaussian": _gaussian,
}


@dataclass(frozen=True)
class VariogramModel:
    """A nugget plus one spherical, exponential or Gaussian structure.

    ``sill`` is the *total* sill, nugget included; ``range_km`` is the
    effective range (see the module docstring).  γ(0) is 0: the nugget
    is a jump at the origin, not a value there.
    """

    kind: str
    nugget: float
    sill: float
    range_km: float

    def __post_init__(self):
        if self.kind not in _STRUCTURE:
            raise ValueError(f"unknown variogram model {self.kind!r}; "
                             f"choose one of {', '.join(MODELS)}")
        if not np.isfinite(self.nugget) or self.nugget < 0:
            raise ValueError("the nugget cannot be negative")
        if not np.isfinite(self.sill) or self.sill < self.nugget:
            raise ValueError("the sill cannot be below the nugget")
        if not self.sill > 0:
            # γ ≡ 0 makes every kriging matrix singular.
            raise ValueError("the sill has to be above zero")
        if not np.isfinite(self.range_km) or self.range_km <= 0:
            raise ValueError("the range has to be a positive distance")

    @property
    def partial_sill(self) -> float:
        return self.sill - self.nugget

    def __call__(self, h_km):
        h = np.asarray(h_km, dtype=float)
        g = self.nugget + self.partial_sill * _STRUCTURE[self.kind](
            h / self.range_km)
        return np.where(h > 0, g, 0.0)


# ---------------------------------------------------------------------------
# The experimental variogram
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EmpiricalVariogram:
    """Matheron's estimator in equal-width lag classes.

    ``lag_km`` is the mean separation of the pairs actually in each
    class, not the class centre; empty classes are dropped.
    ``variance`` is the sample variance, the usual reference line for
    the sill.
    """

    lag_km: np.ndarray
    gamma: np.ndarray
    pairs: np.ndarray
    max_lag_km: float
    variance: float


def empirical_variogram(xyz_km, values, *, n_lags: Optional[int] = None,
                        max_lag_km: Optional[float] = None
                        ) -> EmpiricalVariogram:
    """γ(h) = Σ (zᵢ − zⱼ)² / 2N(h) over the pairs in each lag class.

    *max_lag_km* defaults to half the largest separation, the usual
    limit beyond which too few pairs remain to trust.  *n_lags* defaults
    to as many classes as give about ``PAIRS_PER_LAG`` pairs each,
    between 4 and 15.
    """
    xyz = np.asarray(xyz_km, dtype=float)
    z = np.asarray(values, dtype=float)
    if len(z) < 2:
        raise ValueError("a variogram needs at least two samples")
    d = pdist(xyz)
    sq = pdist(z[:, None], "sqeuclidean")
    if max_lag_km is None:
        max_lag_km = float(d.max()) / 2.0
    if not max_lag_km > 0:
        raise ValueError("every sample is at the same location")
    keep = (d > 0) & (d <= max_lag_km)
    if n_lags is None:
        n_lags = int(np.clip(keep.sum() // PAIRS_PER_LAG, 4, 15))
    edges = np.linspace(0.0, max_lag_km, n_lags + 1)
    idx = np.clip(np.digitize(d[keep], edges) - 1, 0, n_lags - 1)
    pairs = np.bincount(idx, minlength=n_lags)
    lag_sum = np.bincount(idx, weights=d[keep], minlength=n_lags)
    sq_sum = np.bincount(idx, weights=sq[keep], minlength=n_lags)
    ok = pairs > 0
    return EmpiricalVariogram(
        lag_km=lag_sum[ok] / pairs[ok],
        gamma=0.5 * sq_sum[ok] / pairs[ok],
        pairs=pairs[ok],
        max_lag_km=float(max_lag_km),
        variance=float(np.var(z, ddof=1)),
    )


# ---------------------------------------------------------------------------
# Fitting a model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VariogramFit:
    model: VariogramModel
    converged: bool
    message: str


def fit_variogram(emp: EmpiricalVariogram, kind: str = "spherical", *,
                  nugget: Optional[float] = None) -> VariogramFit:
    """Weighted least squares, each class weighted by N(h) / h².

    More pairs mean a better estimate, and the short lags are the ones
    that decide the kriging weights, so both count for more.  Pass
    *nugget* to hold it fixed -- 0 for a model that honours the data
    exactly -- and fit only the sill and the range.
    """
    if kind not in _STRUCTURE:
        raise ValueError(f"unknown variogram model {kind!r}")
    h, g, n = emp.lag_km, emp.gamma, emp.pairs
    free = 3 if nugget is None else 2
    if len(h) <= free:
        raise ValueError(
            f"only {len(h)} lag classes hold any pairs; fitting {free} "
            f"parameters needs at least {free + 1}")

    weight = np.sqrt(n / h ** 2)
    top = float(max(g.max(), emp.variance))
    structure = _STRUCTURE[kind]
    range_lo, range_hi = 1e-6 * emp.max_lag_km, 3.0 * emp.max_lag_km

    reached = np.flatnonzero(g >= 0.95 * g.max())
    range0 = float(np.clip(h[reached[0]] if reached.size else emp.max_lag_km,
                           range_lo * 10, range_hi * 0.9))
    if nugget is None:
        slope = (g[1] - g[0]) / (h[1] - h[0]) if h[1] > h[0] else 0.0
        nugget0 = float(np.clip(g[0] - slope * h[0], 0.0, g.min()))
        x0 = [nugget0, max(top - nugget0, 1e-12), range0]
        lower, upper = [0.0, 0.0, range_lo], [np.inf, np.inf, range_hi]

        def curve(p):
            return p[0] + p[1] * structure(h / p[2])
    else:
        if nugget < 0:
            raise ValueError("the nugget cannot be negative")
        x0 = [max(top - nugget, 1e-12), range0]
        lower, upper = [0.0, range_lo], [np.inf, range_hi]

        def curve(p):
            return nugget + p[0] * structure(h / p[1])

    res = optimize.least_squares(lambda p: weight * (curve(p) - g), x0,
                                 bounds=(lower, upper), method="trf")
    p = res.x
    c0, c, a = (p if nugget is None else (nugget, p[0], p[1]))
    model = VariogramModel(kind, float(c0), float(c0 + c), float(a))
    message = res.message
    if a >= range_hi * (1 - 1e-6):
        message = ("the fitted range ran to its upper bound: the variogram "
                   "does not level off within the lags measured")
    return VariogramFit(model, bool(res.success), str(message))


# ---------------------------------------------------------------------------
# Ordinary kriging
# ---------------------------------------------------------------------------

Variogram = Callable[[np.ndarray], np.ndarray]


class OrdinaryKriging:
    """The ordinary-kriging system for one data set and one variogram.

    Variogram form, augmented with the unbiasedness constraint::

        [ Γ  1 ] [ λ ]   [ γ₀ ]
        [ 1ᵀ 0 ] [ μ ] = [ 1  ]

    estimate = λᵀz, variance = λᵀγ₀ + μ.  The matrix is factorised once
    and every target solved against the factors.  *variogram* is any
    callable with γ(0) = 0; a :class:`VariogramModel` is one.
    """

    def __init__(self, xyz_km, values, variogram: Variogram):
        self.xyz = np.asarray(xyz_km, dtype=float)
        self.z = np.asarray(values, dtype=float)
        n = len(self.z)
        if n < 2:
            raise ValueError("kriging needs at least two samples")
        d = cdist(self.xyz, self.xyz)
        np.fill_diagonal(d, np.inf)
        if np.any(d == 0):
            i, j = np.argwhere(d == 0)[0]
            raise ValueError(
                f"samples {i} and {j} share a location; merge coincident "
                f"samples first (merge_coincident)")
        np.fill_diagonal(d, 0.0)
        self.variogram = variogram
        a = np.zeros((n + 1, n + 1))
        a[:n, :n] = variogram(d)
        a[:n, n] = 1.0
        a[n, :n] = 1.0
        self.matrix = a
        #: Large values warn of an ill-posed model -- typically a
        #: Gaussian variogram with no nugget.
        self.condition = float(np.linalg.cond(a))
        self._lu = linalg.lu_factor(a, check_finite=True)

    @property
    def n(self) -> int:
        return len(self.z)

    def _solve(self, targets_xyz):
        b = np.ones((self.n + 1, len(targets_xyz)))
        b[:self.n] = self.variogram(cdist(self.xyz, targets_xyz))
        return b, linalg.lu_solve(self._lu, b)

    def weights(self, target_xyz):
        """(λ, μ) for a single target."""
        _b, sol = self._solve(np.asarray(target_xyz, float).reshape(1, 3))
        return sol[:self.n, 0], float(sol[self.n, 0])

    def predict(self, targets_xyz, *, chunk: int = 2048):
        """Estimate and kriging variance at every target, in chunks."""
        t = np.asarray(targets_xyz, dtype=float).reshape(-1, 3)
        est = np.empty(len(t))
        var = np.empty(len(t))
        for start in range(0, len(t), chunk):
            stop = start + chunk
            b, sol = self._solve(t[start:stop])
            lam = sol[:self.n]
            est[start:stop] = self.z @ lam
            var[start:stop] = (lam * b[:self.n]).sum(axis=0) + sol[self.n]
        # Round-off can leave a hair below zero at a sampled location.
        return est, np.maximum(var, 0.0)


# ---------------------------------------------------------------------------
# Leave-one-out cross-validation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CrossValidation:
    """Each sample predicted from all the others.

    ``rmse_of_mean`` is the same exercise with the mean of the others as
    the predictor, and ``skill`` is 1 − (RMSE / RMSE of the mean)²: the
    share of the error that kriging removes over not kriging at all.
    Near 0, or below it, the spatial model is adding nothing.  The
    standardised errors should average about 0 with a mean square of
    about 1 when the variogram describes the data honestly: well above
    1, the kriging variance is too optimistic about the surface; well
    below 1, too pessimistic.
    """

    observed: np.ndarray
    predicted: np.ndarray
    variance: np.ndarray

    @property
    def errors(self) -> np.ndarray:
        return self.predicted - self.observed

    @property
    def standardized(self) -> np.ndarray:
        with np.errstate(divide="ignore", invalid="ignore"):
            return self.errors / np.sqrt(self.variance)

    @property
    def mean_error(self) -> float:
        return float(np.mean(self.errors))

    @property
    def rmse(self) -> float:
        return float(np.sqrt(np.mean(self.errors ** 2)))

    @property
    def mean_standardized_error(self) -> float:
        return float(np.mean(self.standardized))

    @property
    def mean_squared_standardized_error(self) -> float:
        return float(np.mean(self.standardized ** 2))

    @property
    def rmse_of_mean(self) -> float:
        z = self.observed
        n = len(z)
        loo = n / (n - 1) * (z - z.mean())
        return float(np.sqrt(np.mean(loo ** 2)))

    @property
    def skill(self) -> float:
        base = self.rmse_of_mean
        if base == 0:
            return float("nan")
        return float(1.0 - (self.rmse / base) ** 2)


def cross_validate(system: OrdinaryKriging) -> CrossValidation:
    """Leave-one-out, from one inverse of the full system (Dubrule 1983).

    For any invertible kriging matrix K with inverse Q, dropping sample
    i leaves the weights −Q[−i, i] / Q[i, i] -- the partitioned-inverse
    identity -- so the residual zᵢ − ẑ₍ᵢ₎ is (Q z̃)ᵢ / Qᵢᵢ with z̃ = [z; 0].
    In the variogram form Kᵢᵢ = γ(0) = 0, which makes the left-out
    kriging variance −1 / Qᵢᵢ.  One inverse instead of n refits.
    """
    n = system.n
    q = linalg.lu_solve(system._lu, np.eye(n + 1))
    z_aug = np.append(system.z, 0.0)
    qd = np.diag(q)[:n]
    residual = (q @ z_aug)[:n] / qd
    return CrossValidation(observed=system.z.copy(),
                           predicted=system.z - residual,
                           variance=-1.0 / qd)


# ---------------------------------------------------------------------------
# Preparing the data
# ---------------------------------------------------------------------------

def merge_coincident(lon, lat, values, *, tol_km: float = COINCIDENT_KM):
    """Fold samples within *tol_km* of each other into one, averaged.

    Two analyses of one outcrop give two rows at one place, and with no
    nugget the kriging matrix is then singular.  Returns ``(lon, lat,
    values, n_folded)``, *n_folded* being how many rows disappeared into
    another.
    """
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    values = np.asarray(values, float)
    xyz = geodetic_to_ecef_km(lon, lat)
    pairs = cKDTree(xyz).query_pairs(tol_km, output_type="ndarray")
    n = len(values)
    if len(pairs) == 0:
        return lon, lat, values, 0
    graph = coo_matrix((np.ones(len(pairs)), (pairs[:, 0], pairs[:, 1])),
                       shape=(n, n))
    n_groups, label = connected_components(graph, directed=False)
    count = np.bincount(label, minlength=n_groups)

    def mean_by(v):
        return np.bincount(label, weights=v, minlength=n_groups) / count

    return mean_by(lon), mean_by(lat), mean_by(values), int(n - n_groups)


def forward_transform(values, transform: str):
    if transform == "none":
        return np.asarray(values, float)
    if transform == "log":
        return np.log(np.asarray(values, float))
    raise ValueError(f"unknown transform {transform!r}")


def back_transform(estimate, sd, transform: str):
    """``(centre, lower, upper)`` in the data's own units, 95 %.

    Under "log" the centre is exp(ŷ), the median: a monotone transform
    carries quantiles over exactly and means not at all.
    """
    lo, hi = estimate - Z95 * sd, estimate + Z95 * sd
    if transform == "none":
        return estimate, lo, hi
    if transform == "log":
        return np.exp(estimate), np.exp(lo), np.exp(hi)
    raise ValueError(f"unknown transform {transform!r}")


def reliability(n: int) -> str:
    """Webster & Oliver's (1992) verdict on a variogram from *n* samples."""
    if n < MARGINAL_N:
        return (f"{n} samples: a variogram from fewer than {MARGINAL_N} is "
                f"of little value (Webster & Oliver 1992). Treat the "
                f"surface as a sketch.")
    if n < RELIABLE_N:
        return (f"{n} samples: marginal. About {RELIABLE_N} are needed for "
                f"a reliable variogram (Webster & Oliver 1992).")
    return f"{n} samples: enough for a reliable variogram."


# ---------------------------------------------------------------------------
# The whole analysis for one set of samples
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Prediction:
    """Kriged surface values.

    ``estimate``, ``lower`` and ``upper`` are in the data's own units --
    under "log", the median and its 95 % interval.  ``sd`` is the kriging
    standard deviation in the units that were kriged, logarithmic under
    "log".
    """

    estimate: np.ndarray
    sd: np.ndarray
    lower: np.ndarray
    upper: np.ndarray


@dataclass(frozen=True)
class SpatialAnalysis:
    """Variogram, fitted model, kriging system and cross-validation.

    ``lon``, ``lat`` and ``values`` are what was kriged, after dropping
    unusable rows and folding coincident ones, with values in the data's
    own units.  Nothing is dropped silently: ``n_excluded`` and
    ``n_folded`` say how many went and why.
    """

    lon: np.ndarray
    lat: np.ndarray
    values: np.ndarray
    transform: str
    n_input: int
    n_excluded: int
    n_folded: int
    variogram: EmpiricalVariogram
    fit: VariogramFit
    kriging: OrdinaryKriging
    cross_validation: CrossValidation

    @property
    def model(self) -> VariogramModel:
        return self.fit.model

    @property
    def n(self) -> int:
        return len(self.values)

    @property
    def reliability(self) -> str:
        return reliability(self.n)

    def predict(self, lon, lat) -> Prediction:
        lon = np.asarray(lon, float)
        lat = np.asarray(lat, float)
        shape = lon.shape
        est, var = self.kriging.predict(geodetic_to_ecef_km(lon, lat))
        sd = np.sqrt(var)
        centre, lo, hi = back_transform(est, sd, self.transform)
        return Prediction(*(a.reshape(shape) for a in (centre, sd, lo, hi)))


def analyse(lon, lat, values, *,
            model: Union[str, VariogramModel] = "spherical",
            transform: str = "log", n_lags: Optional[int] = None,
            max_lag_km: Optional[float] = None,
            nugget: Optional[float] = None) -> SpatialAnalysis:
    """Everything kriging needs for one variable over one set of samples.

    Rows missing a coordinate or the value are dropped, and so, under
    "log", are values at or below zero; coincident samples are folded
    together.  *model* is a model name to fit, or a
    :class:`VariogramModel` to use exactly as given -- which is how a
    model adjusted by hand gets used.
    """
    if transform not in TRANSFORMS:
        raise ValueError(f"unknown transform {transform!r}")
    lon = np.asarray(lon, float).ravel()
    lat = np.asarray(lat, float).ravel()
    values = np.asarray(values, float).ravel()
    n_input = len(values)
    usable = (np.isfinite(lon) & np.isfinite(lat) & np.isfinite(values)
              & (np.abs(lat) <= 90) & (np.abs(lon) <= 180))
    if transform == "log":
        usable &= values > 0
    lon, lat, values = lon[usable], lat[usable], values[usable]
    n_excluded = int(n_input - usable.sum())

    lon, lat, values, n_folded = merge_coincident(lon, lat, values)
    if len(values) < MIN_SAMPLES:
        raise ValueError(
            f"{len(values)} usable sample locations; kriging needs at "
            f"least {MIN_SAMPLES}")
    kriged = forward_transform(values, transform)
    if np.ptp(kriged) == 0:
        raise ValueError("every value is the same; there is nothing to "
                         "interpolate")

    xyz = geodetic_to_ecef_km(lon, lat)
    emp = empirical_variogram(xyz, kriged, n_lags=n_lags,
                              max_lag_km=max_lag_km)
    if isinstance(model, VariogramModel):
        fit = VariogramFit(model, True, "set by hand")
    else:
        fit = fit_variogram(emp, model, nugget=nugget)
    system = OrdinaryKriging(xyz, kriged, fit.model)
    return SpatialAnalysis(
        lon=lon, lat=lat, values=values, transform=transform,
        n_input=n_input, n_excluded=n_excluded, n_folded=n_folded,
        variogram=emp, fit=fit, kriging=system,
        cross_validation=cross_validate(system),
    )


# ---------------------------------------------------------------------------
# One analysis per group, or one for all of them
# ---------------------------------------------------------------------------

#: The label a pooled analysis goes under.
POOLED_LABEL = "All groups pooled"


@dataclass(frozen=True)
class GroupAnalysis:
    """The outcome for one group: an analysis, or the reason there is none."""

    label: str
    n_input: int
    analysis: Optional[SpatialAnalysis] = None
    error: Optional[str] = None


def analyse_groups(groups, *, pooled: bool = False,
                   model: str = "spherical", transform: str = "log",
                   overrides: Optional[dict] = None,
                   n_lags: Optional[int] = None,
                   max_lag_km: Optional[float] = None) -> list:
    """Run :func:`analyse` over each group, or once over all of them.

    *groups* is a sequence of ``(label, lon, lat, values)``.  Kriging
    each group on its own is the default, because samples from two
    units -- a pluton and its host, two lava sequences -- are not one
    random field, and kriging across the contact draws a smooth
    gradient that is not there.  *pooled* puts every sample into one
    analysis under :data:`POOLED_LABEL`.

    *overrides* maps a label to a :class:`VariogramModel` used exactly
    as given.  A group that cannot be analysed -- too few samples, a
    constant value -- comes back with its reason in ``error`` rather
    than stopping the others.
    """
    overrides = overrides or {}
    items = [(label, np.asarray(lon, float).ravel(),
              np.asarray(lat, float).ravel(),
              np.asarray(values, float).ravel())
             for label, lon, lat, values in groups]
    if pooled:
        if items:
            items = [(POOLED_LABEL,
                      np.concatenate([i[1] for i in items]),
                      np.concatenate([i[2] for i in items]),
                      np.concatenate([i[3] for i in items]))]
        else:
            items = [(POOLED_LABEL, np.empty(0), np.empty(0), np.empty(0))]
    out = []
    for label, lon, lat, values in items:
        try:
            result = analyse(lon, lat, values,
                             model=overrides.get(label, model),
                             transform=transform, n_lags=n_lags,
                             max_lag_km=max_lag_km)
        except ValueError as exc:
            out.append(GroupAnalysis(label, len(values), error=str(exc)))
        else:
            out.append(GroupAnalysis(label, len(values), analysis=result))
    return out


# ---------------------------------------------------------------------------
# The prediction grid and where it may be trusted
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Grid:
    """Square cells in degrees, laid out the way an ESRI ASCII grid is.

    ``west`` and ``south`` are the outer edges of the lower-left cell;
    row 0 is the southernmost.
    """

    west: float
    south: float
    cell_deg: float
    ncols: int
    nrows: int

    @property
    def lon_centres(self) -> np.ndarray:
        return self.west + (np.arange(self.ncols) + 0.5) * self.cell_deg

    @property
    def lat_centres(self) -> np.ndarray:
        return self.south + (np.arange(self.nrows) + 0.5) * self.cell_deg

    def mesh(self):
        """``(lon, lat)`` of every cell centre, shape ``(nrows, ncols)``."""
        return np.meshgrid(self.lon_centres, self.lat_centres)


def make_grid(lon_min: float, lon_max: float, lat_min: float,
              lat_max: float, *, cells_across: int = 100) -> Grid:
    """A grid covering the frame, *cells_across* cells along its longer side.

    Cells are square in degrees, which a single-cellsize ESRI ASCII grid
    requires; on the ground they are a little taller than wide away from
    the equator.
    """
    if not (lon_max > lon_min and lat_max > lat_min):
        raise ValueError("the frame has no extent")
    cell = max(lon_max - lon_min, lat_max - lat_min) / cells_across
    return Grid(west=float(lon_min), south=float(lat_min),
                cell_deg=float(cell),
                ncols=int(np.ceil((lon_max - lon_min) / cell - 1e-9)),
                nrows=int(np.ceil((lat_max - lat_min) / cell - 1e-9)))


def hull_mask(lon, lat, grid_lon, grid_lat, *,
              buffer_km: float = 0.0) -> np.ndarray:
    """True where a grid node lies in the samples' convex hull.

    Beyond the hull kriging extrapolates, drifting back toward the mean
    and painting a plausible colour where there is no information.
    *buffer_km* lets the surface run that far past the hull.  Worked in
    a local plane at the samples' centre, which over a field area
    distorts the hull by a fraction of a percent.
    """
    lon = np.asarray(lon, float)
    lat = np.asarray(lat, float)
    g_lon = np.asarray(grid_lon, float)
    g_lat = np.asarray(grid_lat, float)
    lon0, lat0 = float(np.mean(lon)), float(np.mean(lat))
    kx, ky = float(km_per_degree_lon(lat0)), float(km_per_degree_lat(lat0))
    pts = np.column_stack([(lon - lon0) * kx, (lat - lat0) * ky])
    q = np.column_stack([(g_lon.ravel() - lon0) * kx,
                         (g_lat.ravel() - lat0) * ky])
    try:
        inside = Delaunay(pts).find_simplex(q) >= 0
        hull = ConvexHull(pts)
    except (QhullError, ValueError):
        # Fewer than three samples off one line: no hull to speak of.
        inside = np.zeros(len(q), dtype=bool)
        hull = None
    if buffer_km > 0:
        if hull is None:
            near = cKDTree(pts).query(q)[0] <= buffer_km
        else:
            v = pts[hull.vertices]
            a, b = v, np.roll(v, -1, axis=0)
            ab = b - a
            t = np.clip(((q[:, None, :] - a) * ab).sum(-1)
                        / (ab ** 2).sum(-1), 0.0, 1.0)
            closest = a + t[..., None] * ab
            near = np.linalg.norm(q[:, None, :] - closest, axis=-1).min(
                axis=1) <= buffer_km
        inside |= near
    return inside.reshape(g_lon.shape)


# ---------------------------------------------------------------------------
# Export for a GIS
# ---------------------------------------------------------------------------

#: WGS-84 geographic coordinates in the ESRI WKT a .prj file carries,
#: so QGIS and ArcGIS place the grid without being told.
WGS84_PRJ = ('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID['
             '"WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],'
             'UNIT["Degree",0.0174532925199433]]')


def write_esri_ascii(path, grid: Grid, values, *, nodata: float = -9999.0,
                     write_prj: bool = True) -> Path:
    """Write *values* (``(nrows, ncols)``, row 0 south) as an ESRI ASCII grid.

    Plain text, readable by QGIS and ArcGIS, written without GDAL.  NaN
    -- a masked or unpredicted cell -- becomes *nodata*.  Rows go north
    first, as the format requires.  A ``.prj`` beside it declares
    WGS-84 geographic coordinates.
    """
    path = Path(path)
    v = np.asarray(values, dtype=float)
    if v.shape != (grid.nrows, grid.ncols):
        raise ValueError(f"values are {v.shape}; the grid is "
                         f"{(grid.nrows, grid.ncols)}")
    body = np.where(np.isfinite(v), v, nodata)[::-1]
    header = (f"ncols         {grid.ncols}\n"
              f"nrows         {grid.nrows}\n"
              f"xllcorner     {grid.west:.10f}\n"
              f"yllcorner     {grid.south:.10f}\n"
              f"cellsize      {grid.cell_deg:.10f}\n"
              f"NODATA_value  {nodata:g}\n")
    with open(path, "w", encoding="ascii", newline="\n") as fh:
        fh.write(header)
        np.savetxt(fh, body, fmt="%.8g")
    if write_prj:
        path.with_suffix(".prj").write_text(WGS84_PRJ, encoding="ascii")
    return path


def read_esri_ascii(path):
    """``(grid, values)`` from an ESRI ASCII grid, row 0 south, NaN for nodata."""
    path = Path(path)
    header = {}
    with open(path, encoding="ascii") as fh:
        for _ in range(6):
            key, val = fh.readline().split()
            header[key.lower()] = float(val)
        body = np.loadtxt(fh, ndmin=2)
    nodata = header.get("nodata_value", -9999.0)
    values = np.where(body == nodata, np.nan, body)[::-1]
    grid = Grid(west=header["xllcorner"], south=header["yllcorner"],
                cell_deg=header["cellsize"], ncols=int(header["ncols"]),
                nrows=int(header["nrows"]))
    return grid, values
