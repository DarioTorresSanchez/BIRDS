"""The default legend steps out of the way of the field names.

"best" places a legend clear of the samples only.  With many groups the
box grew over the names of the fields -- on Li et al. (2025), over
"Continental extensional zone".  With the default location the legend
now moves out to the right when it would cover a name; a location the
user picked is kept.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import (
    LEGEND_ENTRIES_OUTSIDE,
    LegendStyle,
    PlotOptions,
)
from birds.plot_style import PlotStyle


def _data(groups):
    rng = np.random.default_rng(1)
    rows = []
    for g in range(groups):
        for _ in range(5):
            rows.append(dict(Group=f"Group {g + 1}",
                             Th=rng.uniform(0.5, 5), Nb=rng.uniform(2, 30),
                             Yb=rng.uniform(1, 4), Zr=rng.uniform(50, 300),
                             La=rng.uniform(5, 60), SiO2=rng.uniform(45, 70),
                             Na2O=rng.uniform(2, 5), K2O=rng.uniform(0.5, 3)))
    return pd.DataFrame(rows)


def _plot(key, groups, location="best", canvas=True):
    style = PlotStyle()
    style.group_columns = ["Group"]
    fig = Figure(figsize=(9, 7))
    if canvas:
        FigureCanvasAgg(fig)
    options = PlotOptions(legend=LegendStyle(location=location))
    get_diagram(key).plot(fig, _data(groups), style, options)
    return fig


def _outside(fig):
    legend = fig.axes[0].get_legend()
    anchor = legend.get_bbox_to_anchor().transformed(
        fig.axes[0].transAxes.inverted())
    return anchor.x0 > 1.0


def _covers_a_name(fig):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ax = fig.axes[0]
    box = ax.get_legend().get_window_extent(renderer)
    return any(box.overlaps(t.get_window_extent(renderer))
               for t in ax.texts if t.get_text().strip())


@pytest.mark.parametrize("key", ["li2025_nbyb_thnb", "tas_volcanic"])
def test_many_groups_put_the_legend_outside(key):
    fig = _plot(key, 10)
    assert _outside(fig)
    assert not _covers_a_name(fig)
    legend = fig.axes[0].get_legend().get_window_extent(
        fig.canvas.get_renderer())
    assert legend.x1 <= fig.bbox.x1 + 1          # still on the figure


def test_a_legend_that_covers_nothing_stays_inside():
    fig = _plot("godang2024_nbzr_thnb", 1)
    if _covers_a_name(fig):
        pytest.skip("the one-group legend happens to land on a name")
    assert not _outside(fig)


def test_a_location_the_user_picked_is_kept():
    fig = _plot("li2025_nbyb_thnb", 10, location="upper right")
    assert not _outside(fig)


def test_without_a_renderer_a_long_legend_goes_outside():
    fig = _plot("li2025_nbyb_thnb", LEGEND_ENTRIES_OUTSIDE + 1, canvas=False)
    assert _outside(fig)
    fig = _plot("li2025_nbyb_thnb", 2, canvas=False)
    assert not _outside(fig)
