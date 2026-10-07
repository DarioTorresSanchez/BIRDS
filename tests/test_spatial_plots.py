"""Drawing, summarising and exporting the Map view's kriging.

Everything here runs on a bare matplotlib ``Figure`` and a temporary
folder, without Qt: the surfaces, the variogram and cross-validation
plots, the summary under them, and the grid files a GIS reads.
"""

from __future__ import annotations

import numpy as np
import pytest
from matplotlib.collections import QuadMesh
from matplotlib.colors import LogNorm, Normalize
from matplotlib.contour import ContourSet
from matplotlib.figure import Figure

from birds.coords import km_per_degree_lat, km_per_degree_lon
from birds.geostats import (
    POOLED_LABEL,
    GroupAnalysis,
    VariogramModel,
    analyse_groups,
    make_grid,
    read_esri_ascii,
)
from birds.views.spatial_plots import (
    ESTIMATE_CMAP,
    UNCERTAINTY_CMAP,
    attach_colorbar,
    draw_cross_validation,
    draw_surface,
    draw_variogram,
    kriged_name,
    plain_log_ticks,
    safe_file_name,
    summary_html,
    surface_label,
    surface_layers,
    surface_norm,
    write_kriged_grids,
)


def _unit(n, seed, lon0, level, lat0=19.2, side_km=30.0):
    rng = np.random.default_rng(seed)
    xk = rng.uniform(0, side_km, n)
    yk = rng.uniform(0, side_km, n)
    lon = lon0 + xk / km_per_degree_lon(lat0)
    lat = lat0 + yk / km_per_degree_lat(lat0)
    return lon, lat, np.exp(level + xk / 20.0 + 0.3 * np.sin(yk / 6.0))


def _groups(*, apart=True):
    """Two units: side by side, or (``apart=False``) on top of each other."""
    a = _unit(40, 1, -99.0, 1.0)
    b = _unit(35, 2, -98.5 if apart else -98.95, 3.0)
    return [("Pluton", *a), ("Host", *b)]


@pytest.fixture(scope="module")
def results():
    return analyse_groups(_groups())


@pytest.fixture(scope="module")
def grid():
    return make_grid(-99.05, -98.15, 19.15, 19.5, cells_across=60)


def _ax():
    return Figure(figsize=(6, 5)).add_subplot(111)


class _Style:
    def __init__(self, color):
        self.color = color


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------

def test_a_clipped_surface_is_blank_outside_each_groups_hull(results, grid):
    layers, overlaps = surface_layers(results, grid, clip=True)
    assert [layer.label for layer in layers] == ["Pluton", "Host"]
    glon, _glat = grid.mesh()
    for layer, r in zip(layers, results):
        blank = ~np.isfinite(layer.estimate)
        # Blank wherever the grid is clear of the group's samples ...
        assert blank[(glon < r.analysis.lon.min())
                     | (glon > r.analysis.lon.max())].all()
        # ... and filled somewhere inside them.
        assert np.isfinite(layer.estimate).any()
        assert (np.isfinite(layer.sd) == ~blank).all()
    assert overlaps == []


def test_an_unclipped_surface_covers_the_whole_grid(results, grid):
    layers, _ = surface_layers(results, grid, clip=False)
    for layer in layers:
        assert np.isfinite(layer.estimate).all()
        assert (layer.lower <= layer.estimate).all()
        assert (layer.estimate <= layer.upper).all()


def test_overlapping_groups_are_reported(grid):
    results = analyse_groups(_groups(apart=False))
    _layers, overlaps = surface_layers(results, grid, clip=True)
    assert overlaps == [("Pluton", "Host")]


def test_a_buffer_widens_the_clipped_surface(results, grid):
    tight, _ = surface_layers(results, grid, clip=True)
    loose, _ = surface_layers(results, grid, clip=True, buffer_km=3.0)
    for t, lo in zip(tight, loose):
        assert np.isfinite(lo.estimate).sum() > np.isfinite(t.estimate).sum()


def test_a_group_that_was_not_kriged_has_no_layer(results, grid):
    failed = GroupAnalysis("Dyke", 3, error="3 usable sample locations")
    layers, _ = surface_layers([*results, failed], grid)
    assert [layer.label for layer in layers] == ["Pluton", "Host"]


def test_every_group_shares_one_colour_scale(results, grid):
    layers, _ = surface_layers(results, grid)
    ax = _ax()
    draw_surface(ax, layers, grid, which="estimate", transform="log")
    meshes = [c for c in ax.collections if isinstance(c, QuadMesh)]
    assert len(meshes) == 2
    assert meshes[0].norm is meshes[1].norm
    allv = np.concatenate([layer.estimate[np.isfinite(layer.estimate)]
                           for layer in layers])
    assert meshes[0].norm.vmin == pytest.approx(allv.min())
    assert meshes[0].norm.vmax == pytest.approx(allv.max())


def test_a_log_estimate_gets_a_log_scale_and_its_spread_a_linear_one(
        results, grid):
    layers, _ = surface_layers(results, grid)
    assert isinstance(surface_norm(layers, which="estimate",
                                   transform="log"), LogNorm)
    sd = surface_norm(layers, which="sd", transform="log")
    assert isinstance(sd, Normalize) and not isinstance(sd, LogNorm)
    assert not isinstance(surface_norm(layers, which="estimate",
                                       transform="none"), LogNorm)


def test_nothing_finite_draws_nothing(grid):
    assert surface_norm([], which="estimate", transform="log") is None
    assert draw_surface(_ax(), [], grid) is None


def test_the_two_surfaces_use_their_own_colours(results, grid):
    layers, _ = surface_layers(results, grid)
    ax = _ax()
    est = draw_surface(ax, layers, grid, which="estimate")
    sd = draw_surface(ax, layers, grid, which="sd")
    assert est.get_cmap().name == ESTIMATE_CMAP
    assert sd.get_cmap().name == UNCERTAINTY_CMAP


def test_the_cells_sit_where_the_grid_says(results, grid):
    layers, _ = surface_layers(results, grid)
    ax = _ax()
    mesh = draw_surface(ax, layers, grid)
    (x0, y0), (x1, y1) = mesh.get_datalim(ax.transData).get_points()
    assert (x0, y0) == pytest.approx((grid.west, grid.south))
    assert x1 == pytest.approx(grid.west + grid.ncols * grid.cell_deg)
    assert y1 == pytest.approx(grid.south + grid.nrows * grid.cell_deg)


def test_contours_go_on_the_estimate_only(results, grid):
    layers, _ = surface_layers(results, grid)
    ax = _ax()
    draw_surface(ax, layers, grid, which="estimate", contours=True)
    assert any(isinstance(c, ContourSet) for c in ax.collections)
    ax = _ax()
    draw_surface(ax, layers, grid, which="sd", contours=True)
    assert not any(isinstance(c, ContourSet) for c in ax.collections)


def test_the_colorbar_is_as_tall_as_the_map(results, grid):
    layers, _ = surface_layers(results, grid)
    ax = _ax()
    mesh = draw_surface(ax, layers, grid)
    ax.set_xlim(grid.west, grid.west + grid.ncols * grid.cell_deg)
    ax.set_ylim(grid.south, grid.south + grid.nrows * grid.cell_deg)
    ax.set_aspect(1.06)                  # a map's: the box will not fill
    cbar = attach_colorbar(ax, mesh, "Cu")
    ax.figure.canvas.draw()
    map_box = ax.get_window_extent()
    bar_box = cbar.ax.get_window_extent()
    assert bar_box.height == pytest.approx(map_box.height, rel=1e-3)
    assert bar_box.y0 == pytest.approx(map_box.y0, abs=0.5)
    assert bar_box.x0 > map_box.x1


@pytest.mark.parametrize("lo, hi, expect", [
    (3.0, 80.0, [5, 10, 20, 50]),      # two decades: 1, 2, 5 of each
    (0.01, 1e4, [0.01, 0.1, 1, 10, 100, 1000, 10000]),   # six: decades
])
def test_log_ticks_read_as_plain_numbers(lo, hi, expect):
    ax = _ax()
    ax.set_yscale("log")
    ax.set_ylim(lo, hi)
    plain_log_ticks(ax.yaxis)
    ticks = [t for t in ax.yaxis.get_major_locator()() if lo <= t <= hi]
    assert ticks == pytest.approx(expect)
    fmt = ax.yaxis.get_major_formatter()
    assert fmt(20.0, 0) == "20" and fmt(0.5, 0) == "0.5"


def test_the_colour_labels_say_what_is_shown():
    assert "median" in surface_label("Cu", which="estimate", transform="log")
    assert "ln(Cu)" in surface_label("Cu", which="sd", transform="log")
    assert "ln" not in surface_label("Cu", which="sd", transform="none")
    assert kriged_name("Cu", "log") == "ln(Cu)"
    assert kriged_name("εNd", "none") == "εNd"


# ---------------------------------------------------------------------------
# Variogram and cross-validation
# ---------------------------------------------------------------------------

def test_the_variogram_shows_points_and_model_for_each_group(results):
    ax = _ax()
    styles = {"Pluton": _Style("#123456"), "Host": _Style("#abcdef")}
    draw_variogram(ax, results, styles, variable="Cu", transform="log")
    assert len(ax.collections) == 2                  # one scatter each
    assert len(ax.get_lines()) == 2                  # one model curve each
    assert ax.get_lines()[0].get_color() == "#123456"
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["Pluton  (spherical)", "Host  (spherical)"]
    assert ax.get_ylabel() == "Semivariance of ln(Cu)"
    assert ax.get_xlabel() == "Distance (km)"


def test_one_variogram_alone_carries_its_variance_range_and_pairs(results):
    ax = _ax()
    draw_variogram(ax, results[:1], {}, variable="Cu", transform="log")
    emp = results[0].analysis.variogram
    variance = [ln for ln in ax.get_lines()
                if list(ln.get_ydata()) == [emp.variance, emp.variance]]
    assert variance
    pair_labels = [t.get_text() for t in ax.texts]
    assert [str(int(n)) for n in emp.pairs] == [
        t for t in pair_labels if t.isdigit()]


def test_cross_validation_reads_in_the_datas_units(results):
    ax = _ax()
    draw_cross_validation(ax, results, {}, variable="Cu", transform="log")
    assert ax.get_xscale() == ax.get_yscale() == "log"
    pts = np.asarray(ax.collections[0].get_offsets())
    cv = results[0].analysis.cross_validation
    assert pts[:, 0] == pytest.approx(np.exp(cv.observed))
    assert pts[:, 1] == pytest.approx(np.exp(cv.predicted))
    one_to_one = ax.get_lines()[-1]
    assert list(one_to_one.get_xdata()) == list(one_to_one.get_ydata())
    assert ax.get_xlim() == ax.get_ylim()
    assert "skill" in ax.get_legend().get_texts()[0].get_text()


def test_cross_validation_without_logs_stays_linear():
    results = analyse_groups(_groups()[:1], transform="none")
    ax = _ax()
    draw_cross_validation(ax, results, {}, variable="Cu", transform="none")
    assert ax.get_xscale() == "linear"


def test_nothing_analysed_draws_an_empty_graph():
    failed = [GroupAnalysis("Dyke", 3, error="too few")]
    ax = _ax()
    draw_variogram(ax, failed, {}, variable="Cu", transform="log")
    draw_cross_validation(ax, failed, {}, variable="Cu", transform="log")
    assert not ax.collections


# ---------------------------------------------------------------------------
# The summary
# ---------------------------------------------------------------------------

def test_the_summary_has_a_row_per_group_with_its_numbers(results):
    text = summary_html(results, variable="Cu", transform="log")
    for r in results:
        a = r.analysis
        assert f"<b>{r.label}</b>" in text
        assert f"{a.n} of {r.n_input}" in text
        assert f"{a.cross_validation.skill:.2f}" in text
    assert "Kriged: ln(Cu)" in text


def test_the_summary_says_why_a_group_was_not_kriged(results):
    failed = GroupAnalysis("Dyke", 3, error="3 usable sample locations; "
                                            "kriging needs at least 5")
    text = summary_html([*results, failed], variable="Cu", transform="log")
    assert "not kriged" in text and "needs at least 5" in text


def test_the_summary_warns_of_small_samples_overlaps_and_hand_set_models():
    mine = VariogramModel("spherical", 0.0, 0.5, 10.0)
    results = analyse_groups(_groups(), overrides={"Host": mine})
    text = summary_html(results, variable="Cu", transform="log",
                        overlaps=[("Pluton", "Host")],
                        manual_labels=("Host",))
    assert "spherical (by hand)" in text
    assert text.count("(by hand)") == 1
    assert "Webster" in text                         # 40 and 35 samples
    assert "Host is drawn on top" in text


def test_the_summary_counts_what_was_left_out():
    lon, lat, values = _unit(30, 4, -99.0, 1.0)
    values[:2] = [-1.0, 0.0]                           # cannot be logged
    lon = np.append(lon, lon[5])                       # same outcrop twice
    lat = np.append(lat, lat[5])
    values = np.append(values, values[5])
    results = analyse_groups([("Pluton", lon, lat, values)])
    text = summary_html(results, variable="Cu", transform="log")
    assert "2 sample(s) left out" in text and "not loggable" in text
    assert "1 sample(s) shared a location" in text


def test_a_nugget_of_round_off_reads_as_zero():
    from birds.views.spatial_plots import _fmt_nugget
    assert _fmt_nugget(VariogramModel("spherical", 1e-22, 1.2, 9.0)) == "0"
    assert _fmt_nugget(VariogramModel("spherical", 0.1, 1.2, 9.0)) == "0.1"


def test_the_summary_escapes_what_it_did_not_write():
    lon, lat, values = _unit(30, 5, -99.0, 1.0)
    results = analyse_groups([("<i>Unit</i> & co", lon, lat, values)])
    text = summary_html(results, variable="<b>Cu</b>", transform="log")
    assert "&lt;i&gt;Unit&lt;/i&gt; &amp; co" in text
    assert "<i>Unit</i>" not in text
    assert "<b>Cu</b>" not in text


# ---------------------------------------------------------------------------
# Grids for a GIS
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text, safe", [
    ("Pluton", "Pluton"),
    ("Pluton (A)/1", "Pluton_A_1"),
    ("  ", "grid"),
    ("Toba–Tuff", "Toba_Tuff"),
])
def test_a_label_becomes_a_safe_file_name(text, safe):
    assert safe_file_name(text) == safe


def test_each_group_is_written_as_estimate_and_sd_grids(results, grid,
                                                        tmp_path):
    written = write_kriged_grids(tmp_path / "cu.asc", results, grid,
                                 variable="Cu", transform="log")
    names = sorted(p.name for p in written)
    assert names == sorted([
        "cu_Pluton.asc", "cu_Pluton.prj", "cu_Pluton_sd.asc",
        "cu_Pluton_sd.prj", "cu_Host.asc", "cu_Host.prj", "cu_Host_sd.asc",
        "cu_Host_sd.prj", "cu.txt"])
    assert all(p.exists() for p in written)
    layers, _ = surface_layers(results, grid, clip=True)
    for layer in layers:
        g, est = read_esri_ascii(tmp_path / f"cu_{layer.label}.asc")
        _g, sd = read_esri_ascii(tmp_path / f"cu_{layer.label}_sd.asc")
        assert (g.ncols, g.nrows) == (grid.ncols, grid.nrows)
        assert (g.west, g.south, g.cell_deg) == pytest.approx(
            (grid.west, grid.south, grid.cell_deg), abs=1e-10)
        assert est == pytest.approx(layer.estimate, rel=1e-7, nan_ok=True)
        assert sd == pytest.approx(layer.sd, rel=1e-7, nan_ok=True)


def test_the_text_file_says_what_the_grids_hold(results, grid, tmp_path):
    failed = GroupAnalysis("Dyke", 3, error="too few samples")
    write_kriged_grids(tmp_path / "cu.asc", [*results, failed], grid,
                       variable="Cu", transform="log", buffer_km=2.0,
                       manual_labels=("Host",))
    text = (tmp_path / "cu.txt").read_text(encoding="utf-8")
    assert "Variable:   Cu" in text
    assert "ln(Cu), by ordinary kriging" in text
    assert "the median" in text
    assert "EPSG:4326" in text
    assert "-9999, outside the group's sample hull plus 2 km" in text
    assert "Pluton: cu_Pluton.asc, cu_Pluton_sd.asc" in text
    assert "spherical model (set by hand)" in text
    assert text.count("(set by hand)") == 1
    assert "Not kriged\n  Dyke: too few samples" in text


def test_a_single_surface_keeps_the_name_it_was_given(grid, tmp_path):
    results = analyse_groups(_groups(), pooled=True)
    written = write_kriged_grids(tmp_path / "pooled", results, grid,
                                 variable="Cu", transform="none", clip=False)
    names = {p.name for p in written}
    assert {"pooled.asc", "pooled_sd.asc", "pooled.txt"} <= names
    _g, est = read_esri_ascii(tmp_path / "pooled.asc")
    assert np.isfinite(est).all()              # unclipped: no blanks
    text = (tmp_path / "pooled.txt").read_text(encoding="utf-8")
    assert POOLED_LABEL in text
    assert "-9999, not predicted" in text
    assert "the kriged Cu, in its units" in text


def test_labels_that_clean_up_alike_still_get_their_own_files(grid,
                                                             tmp_path):
    a, b = _groups()
    results = analyse_groups([("Unit A", *a[1:]), ("Unit/A", *b[1:])])
    written = write_kriged_grids(tmp_path / "g.asc", results, grid,
                                 variable="Cu", transform="log")
    names = {p.name for p in written}
    assert {"g_Unit_A.asc", "g_Unit_A_2.asc", "g_Unit_A_2_sd.asc"} <= names
