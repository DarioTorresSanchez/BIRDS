# Spatial analysis in the Map view — method

This note records what the Map view computes when it kriges a variable,
why each choice was made, and how the result has been checked. It is
the counterpart, for the geostatistics, of `DIAGRAM_PROVENANCE.md`. The
code is in `birds/geostats.py` (the arithmetic, no interface),
`birds/views/spatial_plots.py` (drawing and export) and
`birds/views/map_view.py` (the widget). How to use the view is in the
user manual, section 12.

## 1. What is computed

For one numeric column and one set of samples — a group, or every
group pooled — the view:

1. converts the coordinates to WGS-84 longitude and latitude;
2. drops the rows that cannot be used, and folds samples that share a
   location into one;
3. transforms the values (natural logarithm by default);
4. computes the experimental variogram and fits a model to it;
5. solves the ordinary-kriging system on a regular grid of longitude
   and latitude;
6. cross-validates the model by leaving out each sample in turn;
7. back-transforms the estimate, and clips the surface to the samples'
   convex hull.

Nothing beyond NumPy and SciPy is used, and nothing is downloaded.

## 2. Distances

Every sample is placed in Earth-centred Cartesian coordinates on the
WGS-84 ellipsoid (a = 6 378 137 m, f = 1/298.257 223 563), and every
distance is the straight line between two such points. The chord falls
short of the distance along the surface by (d/R)²/24 of it — about one
part in 10⁵ at 100 km, a hundred times less at 10 km. Nothing is projected, so nothing is
distorted, anywhere on the globe; and because the three variogram
models are valid in three dimensions, restricting them to the
ellipsoid's surface keeps them valid — which measuring distances along
the surface would not guarantee.

The map itself is drawn in degrees with the aspect ratio set at the
frame's centre latitude (the equirectangular projection). That affects
the picture only: no distance is ever read off the axes.

## 3. Preparing the data

- A row is left out if it lacks either coordinate or the value, if a
  coordinate is outside ±90° / ±180°, or — under the logarithmic
  transform — if the value is zero or negative. The count is reported.
- Samples closer than 1 m to each other are merged into one, at their
  mean position with their mean value, since two analyses of one
  outcrop make the kriging matrix singular when there is no nugget. The
  count is reported.
- At least five distinct locations are required, and the values must
  not all be equal. A group that fails either is reported as not
  kriged; the others go ahead.

## 4. Transform

Trace-element concentrations are positive and skewed, close to
log-normal; kriged as they are, a few high values dominate the surface
and the estimate can go negative. They are therefore kriged as
y = ln(z) by default. The estimate is reported as exp(ŷ) — the
**median**, since a monotone transform carries quantiles across
exactly — with the 95 % interval exp(ŷ ± 1.96 σ). The usual correction
to the mean, exp(ŷ + σ²/2), is not applied: it is notoriously sensitive
to the sill, and an honest median is preferred to a fragile mean. The
kriging standard deviation stays in log units, where 0.1 means roughly
±10 %. With the transform set to None the values are kriged as they
are, which suits variables that can be negative (εNd, for instance).

## 5. The experimental variogram

γ(h) = Σ (yᵢ − yⱼ)² / 2N(h), over the N(h) pairs whose separation falls
in each distance class. Each class is placed at the mean separation of
its pairs, not at its midpoint.

- **Maximum lag** — half the largest separation between two samples
  unless set by the user: beyond it too few pairs remain to trust.
- **Number of classes** — as many as give about 30 pairs each, between
  4 and 15, unless set by the user.

## 6. Variogram models

A nugget c₀ plus one structure of partial sill c, with total sill
c₀ + c. γ(0) = 0: the nugget is a discontinuity at the origin, not a
value there. Writing r = h/a:

| Model | γ(h) − c₀, for h > 0 |
|---|---|
| Spherical | c (1.5 r − 0.5 r³) for r < 1, c beyond |
| Exponential | c (1 − exp(−3r)) |
| Gaussian | c (1 − exp(−3r²)) |

In all three, **a is the effective range**: the distance at which the
model reaches 95 % of its sill (exactly the sill, for the spherical
model), so "range" means the same thing whichever model is chosen.
Other programs differ: gstat, for one, parameterises the exponential
model by a/3.

## 7. Fitting

Weighted least squares, each class weighted by N(h)/h² — more pairs
mean a better estimate, and the short lags, which decide the kriging
weights, matter most. This is gstat's default criterion (Pebesma 2004,
`fit.method = 7`), justified by practice rather than theory. The
nugget and partial sill are bounded below by zero, and the range
between 10⁻⁶ and 3 times the maximum lag. A range that runs to that
upper bound means the variogram does not level off within the lags
measured, and the summary says so: the usual cause is a regional trend,
which ordinary kriging — assuming a constant mean — describes only
roughly.

A model can instead be set by hand for any group. It is then used
exactly as given, and marked as such in the summary and the exported
metadata. A sill of zero is refused, since it makes the kriging system
singular.

## 8. Ordinary kriging

Every sample is used for every prediction; there is no search
neighbourhood. Field data sets run to tens or hundreds of samples, few
enough to krige from all of them, and a neighbourhood would add a
choice the user has to make and the map would show. The system is
written in the variogram form,

```
[ Γ   1 ] [ λ ]   [ γ₀ ]
[ 1ᵀ  0 ] [ μ ] = [ 1  ]
```

with estimate ŷ = λᵀy and kriging variance σ² = λᵀγ₀ + μ. The matrix
is factorised once (LU) and every grid node solved against the
factors, in chunks. Its condition number is reported when it exceeds
10¹⁰ — typically a Gaussian model without a nugget — because the
weights of such a system are not to be trusted.

## 9. Cross-validation

Each sample is predicted from all the others. Refitting the system n
times is not needed: with Q the inverse of the full kriging matrix,
dropping sample i leaves the residual yᵢ − ŷ₍ᵢ₎ = (Q ỹ)ᵢ / Qᵢᵢ, with
ỹ = [y; 0], and — because Γᵢᵢ = γ(0) = 0 in the variogram form — the
left-out kriging variance −1/Qᵢᵢ (Dubrule 1983). The statistics, in the
units kriged:

- **RMSE** — root mean square of the prediction errors.
- **Skill** — 1 − (RMSE / RMSE₀)², where RMSE₀ is the same exercise
  with the mean of the other samples as the predictor. It is the share
  of the squared error of not kriging at all that kriging removes; near
  zero or below, the spatial model adds nothing.
- **MSSE** — mean of the squared errors divided by their kriging
  variances. About 1 when the kriging variance is honest; well above 1
  it is too optimistic, well below 1 too cautious.

## 10. How many samples

Webster & Oliver (1992) found that a variogram computed from fewer than
50 data is of little value and that about 100 are needed for a reliable
one. The summary quotes that verdict for every group below 100.

## 11. Groups

Each group is kriged on its own by default. Samples from two units — a
pluton and its host, two lava sequences — are not one random field, and
kriging across the contact would draw a smooth gradient that is not
there. Pooling every sample into one analysis is available as an
option. When groups are kriged separately, all surfaces share one
colour scale so that colours compare between them; where two clipped
surfaces overlap, the one drawn last covers the other and the summary
names both.

## 12. Grid and clipping

The grid covers the map frame in square cells of longitude and latitude
— the single cell size an ESRI ASCII grid requires — with the chosen
number of cells along the longer side. On the ground the cells are a
little taller than wide away from the equator.

Beyond the outermost samples kriging can only extrapolate, drifting
back to the mean while painting a plausible colour. By default each
group's surface is therefore clipped to the convex hull of its own
samples, worked out in a local plane at the samples' centre (which
distorts the hull by a fraction of a percent over a field area), with
an optional buffer in kilometres.

## 13. Export

Each kriged group is written as two ESRI ASCII grids — the estimate in
the data's units and the kriging standard deviation of what was kriged
— in WGS-84 longitude and latitude, rows from north to south as the
format requires, with −9999 for cells outside the clipped hull. Each
grid has a `.prj` declaring WGS-84 geographic coordinates
(EPSG:4326) in ESRI WKT, so QGIS and ArcGIS place it without being
told. A text file beside them records the variable, the transform, the
grid, and every group's samples, model and cross-validation figures.
No GDAL is needed to write them.

## 14. How it has been checked

Kriging has, for testing, the advantage of several exact answers, and
the engine is checked against them rather than against another program,
which might share a mistake (`tests/test_geostats.py`):

- kriging honours the data exactly, and its weights sum to one;
- with no spatial structure (a pure nugget) it returns the mean, with
  variance c₀(1 + 1/n);
- with a linear variogram in one dimension it reproduces the Brownian
  bridge — linear interpolation between the two neighbours, with
  variance 2s·ab/(a + b) — to machine precision, and beyond the last
  sample it carries that sample forward;
- the one-inverse cross-validation equals refitting n times to 10⁻¹⁵;
- on a smooth synthetic field kriging removes nearly all the error of
  guessing the mean (skill above 0.9); on pure noise it removes none
  (|skill| below 0.1) and its variance says so (MSSE between 0.7 and
  1.5);
- distances through the Earth match the WGS-84 lengths of a degree, and
  the grid files round-trip cell for cell.

The drawing and export are tested without the interface
(`tests/test_spatial_plots.py`) and the wiring through it
(`tests/test_map_kriging.py`): one surface per group or one pooled,
blank outside each hull unless asked, a hand-set variogram reaching its
own group only, and every setting surviving a saved session. The suites
were themselves checked by putting deliberate faults into the code — 22
across the engine and the view — and confirming that each one makes a
test fail.

## 15. Limits

- **Stationarity.** Ordinary kriging assumes a constant, unknown mean.
  A strong regional trend shows up as a range that never levels off;
  universal kriging, which would model the trend, is not offered.
- **Isotropy.** The variogram depends on distance only, not on
  direction. Anisotropy along a structure is not modelled.
- **One variable at a time.** No co-kriging; correlated elements are
  not used to inform each other.
- **Log-normality.** The default transform suits concentrations; it is
  wrong for variables that are not positive and skewed, which is why it
  can be switched off.
- **Size.** Kriging from every sample costs O(n³) once and O(n²) per
  grid node. On a laptop, 300 samples krige onto a 100 × 100 grid in
  about 0.1 s and 2000 in about 2 s; tens of thousands would call for a
  search neighbourhood, which is not offered.

## References

- Dubrule, O. (1983). Cross validation of kriging in a unique
  neighborhood. *Mathematical Geology*, 15, 687–699.
  https://doi.org/10.1007/BF01033232
- Matheron, G. (1963). Principles of geostatistics. *Economic Geology*,
  58, 1246–1266. https://doi.org/10.2113/gsecongeo.58.8.1246
- National Geospatial-Intelligence Agency (2014). *World Geodetic
  System 1984 (WGS-84): Its definition and relationships with local
  geodetic systems* (NGA.STND.0036_1.0.0_WGS84).
- Pebesma, E. J. (2004). Multivariable geostatistics in S: the gstat
  package. *Computers & Geosciences*, 30, 683–691.
  https://doi.org/10.1016/j.cageo.2004.03.012
- Webster, R., & Oliver, M. A. (1992). Sample adequately to estimate
  variograms of soil properties. *Journal of Soil Science*, 43,
  177–192.
