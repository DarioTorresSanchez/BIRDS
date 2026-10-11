"""Frost's 2×2 grid: what each panel draws, and the tally across them.

Panel (d) drew AI across and FSSI up under axes labelled FSSI across
and AI up, so a sample whose two signs differ landed in the opposite
quadrant.  And the sample tally had no mapping for the grid at all: it
called every visible sample plotted, whatever the four panels showed.
Both now read ``frost.PANELS`` through ``_panels_xy``.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import PlotOptions
from birds.diagrams.templates.frost import PANELS
from birds.plot_style import PlotStyle
from birds.views.sample_counts import count_for_diagram

ROCKS = pd.DataFrame({
    "Sample_Name": ["granite", "Ne-syenite", "peralkaline", "picrite"],
    "SiO2": [72.0, 56.0, 74.0, 42.0], "TiO2": [0.25, 0.6, 0.2, 1.2],
    "Al2O3": [14.2, 21.5, 10.0, 8.0], "Fe2O3": [0.8, 2.0, 2.5, 2.0],
    "FeO": [1.0, 2.0, 1.5, 10.0], "MnO": [0.04, 0.15, 0.06, 0.18],
    "MgO": [0.5, 0.6, 0.1, 25.0], "CaO": [1.4, 2.0, 0.3, 7.0],
    "Na2O": [3.5, 8.5, 5.2, 1.0], "K2O": [4.8, 5.5, 4.6, 0.3],
    "P2O5": [0.08, 0.1, 0.02, 0.1]})


def _render(df):
    fig = Figure()
    get_diagram("frost").plot(fig, df, PlotStyle(), PlotOptions())
    return fig


def _points(ax):
    pts = [np.asarray(c.get_offsets(), float) for c in ax.collections
           if isinstance(c, PathCollection)]
    return np.vstack(pts) if pts else np.empty((0, 2))


def _tally(df):
    return count_for_diagram(get_diagram("frost"), df, df, PlotStyle())


# ---------------------------------------------------------------------------
# Panel (d)
# ---------------------------------------------------------------------------

def test_panel_d_draws_fssi_across_and_ai_up():
    ai, fssi = get_diagram("frost")._ai_fssi(ROCKS)
    ax = _render(ROCKS).axes[3]
    assert ax.get_xlabel() == "FSSI" and ax.get_ylabel().startswith("AI")
    np.testing.assert_allclose(_points(ax), np.column_stack([fssi, ai]))


@pytest.mark.parametrize("rock, saturated, al_deficient", [
    ("granite", True, False),
    ("Ne-syenite", False, False),     # was drawn saturated, Al-deficient
    ("peralkaline", True, True),      # was drawn undersaturated, Al to spare
])
def test_each_rock_lands_in_its_own_quadrant(rock, saturated, al_deficient):
    i = list(ROCKS["Sample_Name"]).index(rock)
    x, y = _points(_render(ROCKS).axes[3])[i]
    assert (x > 0) == saturated and (y < 0) == al_deficient


# ---------------------------------------------------------------------------
# One mapping for the plot and the tally
# ---------------------------------------------------------------------------

def test_every_panel_draws_what_the_mapping_gives():
    fig = _render(ROCKS)
    panels = get_diagram("frost")._panels_xy(ROCKS)
    assert len(panels) == len(PANELS) == len(fig.axes)
    for ax, (x, y, x_frame, y_frame) in zip(fig.axes, panels):
        keep = x.notna() & y.notna()
        np.testing.assert_allclose(_points(ax),
                                   np.column_stack([x[keep], y[keep]]))
        assert ax.get_xlim() == x_frame and ax.get_ylim() == y_frame


def test_a_complete_dataset_is_plotted_everywhere():
    rocks = ROCKS[ROCKS["Sample_Name"] != "picrite"]
    report = _tally(rocks)
    assert (report.plotted, report.partial, report.missing,
            report.offframe) == (3, 0, 0, 0)


def test_off_one_frame_is_on_some_panels_only_and_flagged_there():
    report = _tally(ROCKS)
    assert (report.plotted, report.partial) == (4, 1)
    assert report.names_for("partial") == ["picrite"]
    fig = _render(ROCKS)
    flags = [sum(1 for line in ax.lines if line.get_label() == "_offframe")
             for ax in fig.axes]
    assert flags == [1, 1, 1, 0]          # SiO2 42 is off (a) to (c)


def test_no_norm_is_not_nothing_to_show():
    """Iron only as FeOt: no norm, so panel (d) is empty while the other
    three are full.  Requiring every panel would have read "nothing to
    show"."""
    feot = ROCKS.drop(columns=["FeO", "Fe2O3"]).assign(
        FeOt=[1.72, 3.8, 3.75, 11.8])
    report = _tally(feot)
    # The picrite, off (a) to (c) and with no norm for (d), is on none.
    assert (report.plotted, report.partial, report.missing,
            report.offframe) == (3, 3, 0, 1)
    assert "nothing to show" not in report.html()
    assert "3 on some panels only" in report.html()


def test_a_sample_on_no_panel_is_missing():
    blank = ROCKS.copy()
    blank.loc[1, ["SiO2", "Al2O3", "Na2O", "K2O"]] = np.nan
    report = _tally(blank)
    assert report.names_for("missing") == ["Ne-syenite"]
    assert report.plotted + report.dropped == report.total


def test_a_sample_off_every_frame_is_off_the_frame():
    far = ROCKS.iloc[[0]].assign(SiO2=95.0, Al2O3=np.nan)  # no ASI, no norm
    report = _tally(far)
    assert (report.plotted, report.offframe, report.missing) == (0, 1, 0)
