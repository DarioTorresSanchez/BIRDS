"""The diagrams drawn from normative minerals, and what a norm needs.

Barker's An-Ab-Or, the haplogranite Ab-Or-Q and Frost's FSSI panel
read normative minerals.  They looked for columns named An, Ab, Or, Q,
while the CIPW norm writes norm_An, norm_Ab, ...: computing the norm
drew nothing, and the sample tally still called every sample plotted.
They now compute the norm themselves from the majors in use, unless the
dataset brings its own.

The norm also counted a blank oxide as zero.  A sample with no Al2O3
came out with no feldspar and its silica as quartz -- on the haplogranite
it sat on the Q apex -- and iron given only as FeOt was left out, which
makes a basalt quartz-normative.  Such a sample now gets no norm, and
the diagram and the Norm view say which and why.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure

from birds.cipw import compute_cipw, norm_gaps
from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import PlotOptions, ternary_to_xy
from birds.plot_style import PlotStyle

GRANITOIDS = pd.DataFrame({
    "Sample_Name": ["G1", "G2", "T1"],
    "SiO2": [72.0, 68.5, 66.0], "TiO2": [0.25, 0.45, 0.5],
    "Al2O3": [14.2, 15.0, 16.5], "Fe2O3": [0.8, 1.2, 1.0],
    "FeO": [1.0, 2.0, 2.2], "MnO": [0.04, 0.06, 0.07],
    "MgO": [0.5, 1.1, 1.4], "CaO": [1.4, 2.8, 3.9],
    "Na2O": [3.5, 3.9, 5.0], "K2O": [4.8, 3.3, 1.2],
    "P2O5": [0.08, 0.14, 0.15]})

TERNARIES = ("barker_anaborn", "haplogranite")


def _render(key, df):
    fig = Figure()
    get_diagram(key).plot(fig, df, PlotStyle(), PlotOptions())
    return fig


def _drawn(ax):
    """The points actually on *ax*: finite offsets only."""
    pts = [np.asarray(c.get_offsets(), float) for c in ax.collections
           if isinstance(c, PathCollection)]
    if not pts:
        return np.empty((0, 2))
    pts = np.vstack(pts)
    return pts[np.isfinite(pts).all(axis=1)]


def _notes(fig):
    return [t.get_text() for ax in fig.axes for t in ax.texts
            if t.get_color() == "#a02020"]


def _with_norm_columns(df):
    """What the Norm view's auto-fill leaves in the dataset."""
    out = df.copy()
    norm = compute_cipw(df)
    out[list(norm.columns)] = norm
    return out


# ---------------------------------------------------------------------------
# What a norm needs
# ---------------------------------------------------------------------------

def test_a_complete_analysis_lacks_nothing():
    assert list(norm_gaps(GRANITOIDS)) == ["", "", ""]


def test_each_missing_essential_is_named():
    df = GRANITOIDS.copy()
    df.loc[0, "Al2O3"] = np.nan
    df.loc[1, ["MgO", "K2O"]] = np.nan
    assert list(norm_gaps(df)) == ["Al2O3", "MgO, K2O", ""]


def test_a_zero_is_a_value_not_a_gap():
    df = GRANITOIDS.assign(K2O=0.0)
    assert list(norm_gaps(df)) == ["", "", ""]


def test_iron_only_as_a_total_is_named_as_such():
    feot = GRANITOIDS.drop(columns=["FeO", "Fe2O3"])
    assert set(norm_gaps(feot.assign(FeOt=2.0))) == {
        "FeO/Fe2O3 (iron given only as a total)"}
    assert set(norm_gaps(feot.assign(Fe2O3t=2.2))) == {
        "FeO/Fe2O3 (iron given only as a total)"}
    assert set(norm_gaps(feot)) == {"iron"}
    assert set(norm_gaps(GRANITOIDS.drop(columns="FeO"))) == {""}


def test_gaps_survive_a_repeated_index():
    df = pd.concat([GRANITOIDS, GRANITOIDS.assign(Al2O3=np.nan)])
    assert list(norm_gaps(df)) == ["", "", "", "Al2O3", "Al2O3", "Al2O3"]


def test_an_incomplete_row_gets_no_norm_and_others_are_unchanged():
    df = GRANITOIDS.copy()
    df.loc[1, "Al2O3"] = np.nan
    result = compute_cipw(df)
    assert result.loc[1, ["norm_Q", "norm_Ab", "norm_Total"]].isna().all()
    assert result.loc[1, "silica_saturation"] == "incomplete"
    alone = compute_cipw(GRANITOIDS.loc[[0, 2]])
    pd.testing.assert_frame_equal(result.loc[[0, 2]], alone)


def test_without_al2o3_the_old_norm_was_quartz_on_its_own():
    """Why the gap matters: blanks read as zeros put a granite on the
    haplogranite's Q apex."""
    row = GRANITOIDS.loc[[0]].copy()
    row["Al2O3"] = 0.0                              # what a blank used to be
    norm = compute_cipw(row).iloc[0]
    assert norm["norm_Ab"] == norm["norm_Or"] == 0.0 and norm["norm_Q"] > 60


# ---------------------------------------------------------------------------
# The diagrams find the norm
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", TERNARIES)
def test_the_norm_view_columns_no_longer_leave_the_diagram_empty(key):
    fig = _render(key, _with_norm_columns(GRANITOIDS))
    assert len(_drawn(fig.axes[0])) == 3
    assert not _notes(fig)


@pytest.mark.parametrize("key", TERNARIES)
def test_no_visit_to_the_norm_view_is_needed(key):
    assert len(_drawn(_render(key, GRANITOIDS).axes[0])) == 3


@pytest.mark.parametrize("key, top, left, right", [
    ("barker_anaborn", "An", "Ab", "Or"),
    ("haplogranite", "Q", "Ab", "Or"),
])
def test_each_sample_sits_where_its_norm_puts_it(key, top, left, right):
    norm = compute_cipw(GRANITOIDS)
    x, y = ternary_to_xy(norm[f"norm_{top}"], norm[f"norm_{left}"],
                         norm[f"norm_{right}"])
    drawn = _drawn(_render(key, GRANITOIDS).axes[0])
    np.testing.assert_allclose(drawn, np.column_stack([x, y]))


def test_stale_norm_columns_are_not_read():
    """The norm_* columns keep the majors in use when the Norm view ran;
    the diagram computes from the majors it is given now."""
    stale = _with_norm_columns(GRANITOIDS)
    stale["norm_Q"] = 99.0
    np.testing.assert_allclose(_drawn(_render("haplogranite", stale).axes[0]),
                               _drawn(_render("haplogranite",
                                              GRANITOIDS).axes[0]))


def test_a_norm_the_dataset_brings_is_used_as_it_stands():
    own = pd.DataFrame({"An": [20.0], "Ab": [50.0], "Or": [30.0]})
    x, y = ternary_to_xy(own["An"], own["Ab"], own["Or"])
    fig = _render("barker_anaborn", own)
    np.testing.assert_allclose(_drawn(fig.axes[0]), [[x[0], y[0]]])
    assert not _notes(fig)


@pytest.mark.parametrize("key", TERNARIES)
def test_a_sample_without_a_norm_is_left_off_and_named(key):
    df = GRANITOIDS.copy()
    df.loc[1, "Al2O3"] = np.nan
    fig = _render(key, df)
    assert len(_drawn(fig.axes[0])) == 2
    assert _notes(fig) == ["1 of 3 samples has no CIPW norm: missing Al2O3."]


def test_iron_as_a_total_points_to_the_adjustment():
    fig = _render("barker_anaborn",
                  GRANITOIDS.drop(columns=["FeO", "Fe2O3"]).assign(FeOt=2.5))
    assert len(_drawn(fig.axes[0])) == 0
    (note,) = _notes(fig)
    assert note.startswith("None of the 3 samples has a CIPW norm")
    assert "Data → Pre-process majors…" in note


def test_the_diagram_follows_the_adjusted_majors_switch():
    """Iron as FeOt only: no norm from the analysed majors; once
    adjusted, the iron is split and every sample is drawn."""
    from birds.data_manager import DataManager
    from birds.preprocess import attach_adjusted

    feot = GRANITOIDS.drop(columns=["FeO", "Fe2O3"]).assign(
        FeOt=[1.72, 3.08, 3.1])
    data = DataManager()
    data.df = attach_adjusted(feot, "anhydrous", "middlemost")
    counts = {}
    for on in (False, True):
        data.use_adjusted = on
        counts[on] = len(_drawn(_render("haplogranite",
                                        data.majors_df()).axes[0]))
    assert counts == {False: 0, True: 3}


def test_frost_fssi_comes_from_the_norm():
    frost = get_diagram("frost")
    _ai, fssi = frost._ai_fssi(GRANITOIDS)
    norm = compute_cipw(GRANITOIDS)
    expected = (norm["norm_Q"] - (norm["norm_Lc"] + 2.0 * (
        norm["norm_Ne"] + norm["norm_Kp"]))) / 100.0
    pd.testing.assert_series_equal(fssi, expected, check_names=False)
    df = GRANITOIDS.copy()
    df.loc[1, "Al2O3"] = np.nan
    fig = _render("frost", df)
    assert len(_drawn(fig.axes[3])) == 2               # panel (d)
    assert len(_drawn(fig.axes[0])) == 3               # Fe-index: no norm
    assert _notes(fig) == ["1 of 3 samples has no CIPW norm: missing Al2O3."]


# ---------------------------------------------------------------------------
# What the tally and the Norm view report
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", TERNARIES)
def test_the_tally_counts_what_is_drawn(key):
    """It once called every sample plotted on an empty triangle."""
    from birds.views.sample_counts import count_for_diagram

    df = GRANITOIDS.copy()
    df.loc[1, "Al2O3"] = np.nan
    report = count_for_diagram(get_diagram(key), df, df, PlotStyle())
    assert (report.plotted, report.missing) == (2, 1)
    assert report.names_for("missing") == ["G2"]


def test_the_norm_view_names_the_samples_without_a_norm(qapp):
    from birds.data_manager import DataManager
    from birds.views.norm import NormView

    data = DataManager()
    df = GRANITOIDS.copy()
    df.loc[1, "Al2O3"] = np.nan
    df.loc[2, ["FeO", "Fe2O3"]] = np.nan
    df["FeOt"] = [np.nan, np.nan, 3.1]
    data.df = df
    view = NormView(data, PlotStyle())
    view.compute()
    summary = view.summary_label.text()
    assert "incomplete" in summary
    assert "2 samples got no norm" in summary
    assert "missing Al2O3" in summary
    assert "iron given only as a total" in summary
    assert "Pre-process majors" in summary
    assert view.table.item(1, 1).text() == "incomplete"
    assert view.table.item(1, 2).text() == ""          # its norm total
