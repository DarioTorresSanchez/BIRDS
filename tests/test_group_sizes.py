"""Each group can have its own symbol size, to make it stand out.

Edit plot had one Point size for every group.  A group's Size column
now sets its own; "Auto" follows the Point size.  Sessions and style
presets keep it, a session saved before groups had sizes opens with
every group on Auto, and every view draws it: the diagrams and the
Bivariate view through ``draw_group``, the Isotopes view, the spider
patterns, and the map in proportion to its own Size.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from birds.diagrams.registry import _REGISTRY
from birds.diagrams.templates.base import PlotOptions, get_groups
from birds.plot_style import GroupStyle, PlotStyle


# ---------------------------------------------------------------------------
# The style
# ---------------------------------------------------------------------------

def test_a_group_size_overrides_the_point_size():
    style = PlotStyle(point_size=8.0,
                      groups=[GroupStyle("A", size=14.0), GroupStyle("B")])
    assert style.size_of(style.groups[0]) == 14.0
    assert style.size_of(style.groups[1]) == 8.0          # Auto
    assert style.size_of(None) == 8.0
    assert style.size_scale(style.groups[0]) == pytest.approx(1.75)
    assert style.size_scale(style.groups[1]) == 1.0


def test_sizes_survive_a_session_and_a_copy():
    style = PlotStyle(groups=[GroupStyle("A", size=14.0), GroupStyle("B")])
    back = PlotStyle.from_dict(style.to_dict())
    assert [g.size for g in back.groups] == [14.0, None]
    other = PlotStyle()
    other.copy_from(style)
    assert [g.size for g in other.groups] == [14.0, None]


@pytest.mark.parametrize("saved", [{}, {"size": None}, {"size": 0},
                                   {"size": "big"}, {"size": -3}])
def test_a_style_saved_without_a_size_follows_the_point_size(saved):
    style = PlotStyle.from_dict({"groups": [{"name": "A", **saved}]})
    assert style.groups[0].size is None


# ---------------------------------------------------------------------------
# Every diagram
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", sorted(_REGISTRY))
def test_every_diagram_draws_each_group_at_its_size(key, full_df,
                                                    plot_style):
    plot_style.point_size = 8.0
    plot_style.groups[0].size = 20.0
    fig = Figure(figsize=(7, 5.5))
    _REGISTRY[key].plot(fig, full_df, plot_style, PlotOptions())
    wanted = {"A": 20.0 ** 2, "B": 8.0 ** 2}
    for ax in fig.axes:
        for c in ax.collections:
            if isinstance(c, PathCollection) and c.get_label() in wanted:
                assert np.allclose(c.get_sizes(), wanted[c.get_label()]), \
                    (key, c.get_label())


# ---------------------------------------------------------------------------
# The views with symbols of their own
# ---------------------------------------------------------------------------

@pytest.fixture
def window(qapp, full_df):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = full_df.copy()
    w.style.group_columns = ["Group"]
    w.style.groups = [GroupStyle("A", color="#1f77b4", size=18.0),
                      GroupStyle("B", color="#d62728", marker="s")]
    w.style.point_size = 6.0
    w.on_dataset_replaced()
    return w


def test_the_spider_patterns_use_the_group_size(window, qapp):
    window._open_spider("ree")
    window.spider.update_plot()
    qapp.processEvents()
    sizes = {line.get_label(): line.get_markersize()
             for ax in window.spider.canvas.figure.axes
             for line in ax.get_lines() if isinstance(line, Line2D)}
    assert sizes.get("A") == 18.0 and sizes.get("B") == 6.0


def test_the_map_scales_its_own_size_by_the_group(window):
    view = window.map
    view.marker_size.setValue(10)
    ax = Figure().add_subplot(111)
    samples = [(label, sub, gs,
                pd.Series(np.linspace(-99, -98, len(sub)), index=sub.index),
                pd.Series(np.linspace(19, 20, len(sub)), index=sub.index))
               for label, sub, gs in get_groups(window.data.df, window.style)]
    view._draw_samples(ax, samples)
    sizes = {c.get_label(): c.get_sizes()[0] for c in ax.collections}
    assert sizes["A"] == pytest.approx((10 * 18.0 / 6.0) ** 2)
    assert sizes["B"] == pytest.approx(10 ** 2)


def test_the_isotope_plots_use_the_group_size(window, qapp):
    df = window.data.df
    df["87Sr/86Sr"] = np.linspace(0.703, 0.709, len(df))
    df["143Nd/144Nd"] = np.linspace(0.5131, 0.5124, len(df))
    window.on_dataset_replaced()
    window._open_isotopes("sr_nd")
    qapp.processEvents()
    sizes = {c.get_label(): c.get_sizes()[0]
             for ax in window.isotopes.canvas.figure.axes
             for c in ax.collections if isinstance(c, PathCollection)}
    assert sizes.get("A") == pytest.approx(18.0 ** 2)
    assert sizes.get("B") == pytest.approx(6.0 ** 2)


# ---------------------------------------------------------------------------
# Edit plot
# ---------------------------------------------------------------------------

def test_edit_plot_offers_a_size_per_group(qapp, full_df):
    from birds.dialogs.edit_plot_dialog import EditPlotDialog
    style = PlotStyle(group_columns=["Group"],
                      groups=[GroupStyle("A", size=12.0), GroupStyle("B")])
    dialog = EditPlotDialog(style, full_df)
    rows = dialog._group_rows
    assert rows[0].size_spin.value() == 12.0
    assert rows[1].size_spin.value() == 0.0
    assert rows[1].size_spin.text() == "Auto"
    rows[1].size_spin.setValue(9.5)
    out = dialog.updated_style()
    assert [g.size for g in out.groups] == [12.0, 9.5]


def test_adding_and_removing_groups_keeps_the_sizes(qapp, full_df):
    from birds.dialogs.edit_plot_dialog import EditPlotDialog
    style = PlotStyle(groups=[GroupStyle("A", size=12.0), GroupStyle("B")])
    dialog = EditPlotDialog(style, full_df)
    dialog.n_groups_spin.setValue(3)
    dialog.n_groups_spin.setValue(2)
    assert dialog._group_rows[0].size_spin.value() == 12.0
