"""Up to 25 sample groups, each looking like no other.

The limit was 10, with 10 colours and 10 markers cycled together, so an
eleventh group would have been the first one again.  The limit is now
``MAX_GROUPS`` = 25 everywhere -- the Edit plot dialog, its auto-fill
from the data, the plots and their legends, and saved sessions.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection
from matplotlib.colors import to_rgb
from matplotlib.figure import Figure
from matplotlib.markers import MarkerStyle

from birds.plot_style import (
    DEFAULT_COLORS,
    DEFAULT_MARKERS,
    MAX_GROUPS,
    GroupStyle,
    PlotStyle,
    legend_columns,
)


def _lab(colour):
    rgb = np.array(to_rgb(colour))
    rgb = np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722],
                  [0.0193, 0.1192, 0.9505]])
    xyz = m @ rgb / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]),
                     200 * (f[1] - f[2])])


def _styles(n):
    return [GroupStyle(name=f"G{i + 1}", color=DEFAULT_COLORS[i % len(
        DEFAULT_COLORS)], marker=DEFAULT_MARKERS[i % len(DEFAULT_MARKERS)])
        for i in range(n)]


def _data(n_groups, per_group=3):
    rng = np.random.default_rng(3)
    rows = n_groups * per_group
    return pd.DataFrame({
        "Sample_Name": [f"S{i}" for i in range(rows)],
        "Unit": [f"G{i // per_group + 1}" for i in range(rows)],
        "SiO2": rng.uniform(45, 75, rows),
        "Na2O": rng.uniform(2, 5, rows), "K2O": rng.uniform(0.5, 5, rows)})


# ---------------------------------------------------------------------------
# The palette
# ---------------------------------------------------------------------------

def test_the_limit_is_25():
    assert MAX_GROUPS == 25


def test_every_group_has_its_own_colour_and_they_stay_apart():
    colours = DEFAULT_COLORS[:MAX_GROUPS]
    assert len(set(colours)) == MAX_GROUPS == len(DEFAULT_COLORS)
    gaps = [np.linalg.norm(_lab(a) - _lab(b))
            for a, b in itertools.combinations(colours, 2)]
    assert min(gaps) > 18                      # CIELAB Delta E
    assert all(_lab(c)[0] < 85 for c in colours)   # readable on white


def test_the_first_ten_colours_are_unchanged():
    """Sessions and figures made before keep their look."""
    assert DEFAULT_COLORS[:10] == (
        "#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b",
        "#e377c2", "#17becf", "#bcbd22", "#7f7f7f")


def test_markers_are_filled_and_no_two_groups_share_colour_and_shape():
    assert all(MarkerStyle(m).is_filled() for m in DEFAULT_MARKERS)
    pairs = {(s.color, s.marker) for s in _styles(MAX_GROUPS)}
    assert len(pairs) == MAX_GROUPS


def test_a_long_legend_wraps_into_columns():
    assert [legend_columns(n) for n in (1, 12, 13, 24, 25)] == [1, 1, 2, 2,
                                                                  3]


# ---------------------------------------------------------------------------
# The Edit plot dialog
# ---------------------------------------------------------------------------

@pytest.fixture
def dialog_for(qapp):
    from birds.dialogs.edit_plot_dialog import EditPlotDialog

    def make(df, style=None):
        return EditPlotDialog(style or PlotStyle(), df)
    return make


def test_the_dialog_offers_25_groups(dialog_for):
    dialog = dialog_for(_data(2))
    assert dialog.n_groups_spin.maximum() == 25
    dialog.n_groups_spin.setValue(25)
    style = dialog.updated_style()
    assert len(style.groups) == 25
    assert len({g.color for g in style.groups}) == 25


def test_auto_fill_takes_25_groups_from_the_data(dialog_for):
    dialog = dialog_for(_data(25))
    combo = dialog._col_combos[0]
    combo.setCurrentIndex(combo.findData("Unit"))
    style = dialog.updated_style()
    assert [g.name for g in style.groups] == [f"G{i}" for i in range(1, 26)]
    assert len({(g.color, g.marker) for g in style.groups}) == 25


def test_more_than_25_values_are_cut_at_25_and_said(dialog_for):
    dialog = dialog_for(_data(30))
    combo = dialog._col_combos[0]
    combo.setCurrentIndex(combo.findData("Unit"))
    assert len(dialog.updated_style().groups) == 25
    assert "30 unique" in dialog.auto_info.text()


def test_every_default_marker_can_be_chosen_and_is_shown(dialog_for):
    """A marker missing from the list would show, and save, as a circle."""
    from birds.dialogs.edit_plot_dialog import MARKER_CHOICES

    assert set(DEFAULT_MARKERS) <= {code for _label, code in MARKER_CHOICES}
    dialog = dialog_for(_data(2))
    dialog.n_groups_spin.setValue(25)
    shown = [row.marker_combo.currentData() for row in dialog._group_rows]
    assert shown == [DEFAULT_MARKERS[i % len(DEFAULT_MARKERS)]
                     for i in range(25)]


def test_the_group_rows_scroll(dialog_for):
    dialog = dialog_for(_data(2))
    dialog.n_groups_spin.setValue(25)
    assert dialog.rows_scroll.widget().layout() is dialog.rows_container
    assert dialog.rows_container.count() == 25


# ---------------------------------------------------------------------------
# Plots, legends and sessions
# ---------------------------------------------------------------------------

def test_a_diagram_draws_25_groups_with_a_legend_in_columns():
    from birds.diagrams.registry import get_diagram
    from birds.diagrams.templates.base import PlotOptions

    style = PlotStyle(group_columns=["Unit"], groups=_styles(25))
    fig = Figure(figsize=(9, 7))
    get_diagram("tas_volcanic").plot(fig, _data(25), style, PlotOptions())
    ax = fig.axes[0]
    drawn = [c for c in ax.collections if isinstance(c, PathCollection)
             and not c.get_label().startswith("_")]
    assert len(drawn) == 25
    assert len({tuple(np.round(c.get_facecolor()[0], 3)) for c in drawn}) == 25
    legend = ax.get_legend()
    texts = [t.get_text() for t in legend.get_texts()]
    assert {f"G{i}" for i in range(1, 26)} <= set(texts)
    # 25 groups and the Irvine & Baragar curve: three columns of twelve.
    assert legend._ncols == legend_columns(len(texts)) == 3


def test_25_groups_survive_a_session(tmp_path):
    from birds.session import SessionState, load_session, save_session

    style = PlotStyle(group_columns=["Unit"], groups=_styles(25))
    path = tmp_path / "groups.birds"
    save_session(path, SessionState(data={"main": _data(25)},
                                    plot_style=style.to_dict()))
    back = PlotStyle.from_dict(load_session(path).plot_style)
    assert [(g.name, g.color, g.marker) for g in back.groups] == \
        [(g.name, g.color, g.marker) for g in style.groups]
