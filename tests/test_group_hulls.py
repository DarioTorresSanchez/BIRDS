"""A group's shaded hull is drawn wherever its samples are.

The Hull option of Edit plot shades the convex hull of each group.  It
was drawn by four copies of the same code and missing from Frost, every
ternary (Barker, the haplogranite system, AFM, Jensen, the tectonic
ternaries) and the Petrography diagrams; where it was drawn it was so
faint the user found it did not work.  All of them now draw their
samples through ``draw_group``.
"""

from __future__ import annotations

import numpy as np
import pytest
from matplotlib.collections import PathCollection
from matplotlib.colors import to_rgba
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

from birds.diagrams.registry import _REGISTRY
from birds.diagrams.templates.base import (
    HULL_ALPHA,
    HULL_ALPHA_ALONE,
    PlotOptions,
    hull_vertices,
)


def _render(key, df, style):
    fig = Figure(figsize=(7, 5.5))
    _REGISTRY[key].plot(fig, df, style, PlotOptions())
    return fig


def _hulls(ax, colour):
    """Filled polygons in the group's colour.  A field outline drawn
    unfilled keeps a facecolor too -- matplotlib's blue, at alpha 0 -- so
    only a visible fill counts."""
    want = to_rgba(colour)[:3]
    return [p for p in ax.patches if isinstance(p, Polygon)
            and p.get_facecolor()[3] > 0
            and tuple(np.round(p.get_facecolor()[:3], 3))
            == tuple(np.round(want, 3))]


def _group_scatters(ax, name):
    return [c for c in ax.collections
            if isinstance(c, PathCollection) and c.get_label() == name
            and len(c.get_offsets()) >= 3]


@pytest.mark.parametrize("key", sorted(_REGISTRY))
def test_every_diagram_shades_the_groups_it_plots(key, full_df, plot_style):
    for gs in plot_style.groups:
        gs.shaded = True
    fig = _render(key, full_df, plot_style)
    for ax in fig.axes:
        for gs in plot_style.groups:
            scatters = _group_scatters(ax, gs.name)
            if not scatters:
                continue
            points = np.unique(np.vstack([s.get_offsets() for s in scatters]),
                               axis=0)
            if hull_vertices(points[:, 0], points[:, 1],
                             log_x=ax.get_xscale() == "log",
                             log_y=ax.get_yscale() == "log") is None:
                continue                    # no area to shade
            assert _hulls(ax, gs.color), (key, ax.get_title(), gs.name)


def test_a_hull_is_visible_under_the_symbols(full_df, plot_style):
    plot_style.groups[0].shaded = True
    ax = _render("tas_plutonic", full_df, plot_style).axes[0]
    (hull,) = _hulls(ax, plot_style.groups[0].color)
    assert hull.get_facecolor()[3] == pytest.approx(HULL_ALPHA)
    assert hull.get_edgecolor()[3] > hull.get_facecolor()[3]
    # the symbols carry the legend, once
    _handles, labels = ax.get_legend_handles_labels()
    assert labels.count(plot_style.groups[0].name) == 1


def test_without_symbols_the_hull_carries_the_legend(full_df, plot_style):
    gs = plot_style.groups[0]
    gs.shaded, gs.show_markers = True, False
    for key in ("tas_plutonic", "barker_anaborn", "frost"):
        fig = _render(key, full_df, plot_style)
        ax = fig.axes[0]
        assert not _group_scatters(ax, gs.name), key
        (hull,) = _hulls(ax, gs.color)
        assert hull.get_label() == gs.name, key
        assert hull.get_facecolor()[3] == pytest.approx(HULL_ALPHA_ALONE)


def test_hiding_the_symbols_works_on_a_ternary(full_df, plot_style):
    """Before, the ternaries drew every group's symbols regardless."""
    plot_style.groups[0].show_markers = False
    ax = _render("barker_anaborn", full_df, plot_style).axes[0]
    assert not _group_scatters(ax, plot_style.groups[0].name)
    assert _group_scatters(ax, plot_style.groups[1].name)


def test_on_log_axes_the_hull_is_taken_on_the_logarithms():
    """(20, 20) lies inside the hull of the three corners in value space
    but outside it in log space, which is the space the reader sees."""
    x = np.array([1.0, 100.0, 1.0, 20.0])
    y = np.array([1.0, 1.0, 100.0, 20.0])
    linear = {tuple(v) for v in hull_vertices(x, y)}
    logged = {tuple(np.round(v, 9)) for v in
              hull_vertices(x, y, log_x=True, log_y=True)}
    assert (20.0, 20.0) not in linear
    assert (20.0, 20.0) in logged


def test_no_area_no_hull():
    assert hull_vertices([1, 2], [1, 2]) is None
    assert hull_vertices([1, 2, 3, 4], [2, 4, 6, 8]) is None      # a line
    assert hull_vertices([1, 1, 1, 2], [1, 1, 1, 2]) is None      # duplicates
    assert hull_vertices([0, 1, 2], [1, 5, 3], log_x=True) is None  # log(0)
