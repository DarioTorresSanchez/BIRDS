"""The sample tally on the triangles says what the triangle shows.

The tally under a diagram reads each sample's position from the
diagram's ``_compute_xy``.  The ternary templates placed their samples
with ``_abc`` inside their own ``plot`` and never exposed that, so the
tally fell back to counting every visible sample as plotted: Wood
(1980) reported every sample of a dataset with no Th, Hf or Ta as
plotted on an empty triangle, and a click identified nothing.
``TernaryDiagram`` derives ``_compute_xy`` from ``_abc`` once, for the
plot and everything that reads the plot.

``test_tally_is_self_consistent`` in test_diagrams.py checks the counts
add up; it cannot see them all being wrong together.  These check them
against the points drawn.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure

from birds.diagrams.registry import _REGISTRY, get_diagram
from birds.diagrams.templates.base import PlotOptions, TernaryDiagram
from birds.plot_style import PlotStyle
from birds.views.sample_counts import _owns_compute_xy, count_for_diagram
from conftest import MAJORS, MODAL, TRACES

TERNARIES = sorted(k for k, d in _REGISTRY.items()
                   if isinstance(d, TernaryDiagram))


def _drawn(key, df):
    """How many samples the rendered triangle actually shows."""
    fig = Figure()
    get_diagram(key).plot(fig, df, PlotStyle(), PlotOptions())
    return sum(int(np.isfinite(np.asarray(c.get_offsets(), float))
                   .all(axis=1).sum())
               for c in fig.axes[0].collections
               if isinstance(c, PathCollection))


def test_every_triangle_is_on_the_shared_mapping():
    assert set(TERNARIES) == {
        "afm", "jensen", "barker_anaborn", "haplogranite",
        "cabanis_lecolle_1989", "harris_1986_HfRbTa", "wood_1980_ThHfTa",
        "vermeesch_EuLuSr", "vermeesch_NaNbSr", "vermeesch_SiTiSr",
        "vermeesch_SmTiV", "vermeesch_VTiSc",
    }


def test_no_other_diagram_is_left_without_a_mapping():
    """A template added later without one would be counted as fully
    plotted whatever it drew.  The exceptions are the multi-panel
    templates, which the tally reads through their panels; Frost's 2×2
    grid; and the Petrography view's modal triangles, a view with no
    tally."""
    lacking = sorted(
        k for k, d in _REGISTRY.items()
        if not (hasattr(d, "panels") or hasattr(d, "_compute_xy_for_panel"))
        and not _owns_compute_xy(type(d)))
    assert lacking == ["frost", "gabbro_pl_px_ol",
                       "streckeisen_qapf_plutonic",
                       "streckeisen_qapf_volcanic",
                       "tuff_crystal_vitric_lithic", "ultramafic_ol_opx_cpx"]


@pytest.fixture(params=["complete", "every third lacks its traces",
                        "majors only", "all blank", "zeros",
                        "negative majors"])
def shaped(request, full_df):
    kind = request.param
    df = full_df
    if kind == "every third lacks its traces":
        df = full_df.copy()
        df.loc[df.index % 3 == 0, TRACES + MODAL] = np.nan
    elif kind == "majors only":
        df = full_df[["Sample_Name", "Group", *MAJORS]]
    elif kind == "all blank":
        df = full_df.assign(**{c: np.nan for c in MAJORS + TRACES + MODAL})
    elif kind == "zeros":
        df = full_df.assign(**{c: 0.0 for c in MAJORS + TRACES + MODAL})
    elif kind == "negative majors":
        df = full_df.assign(**{c: -full_df[c] for c in MAJORS})
    return kind, df


@pytest.mark.parametrize("key", TERNARIES)
def test_the_tally_counts_what_is_drawn(key, shaped):
    kind, df = shaped
    report = count_for_diagram(get_diagram(key), df, df, PlotStyle())
    drawn = _drawn(key, df)
    assert report.plotted == drawn, f"{key} / {kind}"
    assert report.missing == len(df) - drawn, f"{key} / {kind}"


@pytest.mark.parametrize("key", TERNARIES)
def test_the_samples_left_off_are_named(key, full_df):
    df = full_df.copy()
    df.loc[df.index[:2], TRACES + MODAL + ["Al2O3", "MgO", "Na2O"]] = np.nan
    report = count_for_diagram(get_diagram(key), df, df, PlotStyle())
    assert set(df["Sample_Name"].iloc[:2]) <= set(report.names_for("missing"))
    assert not set(df["Sample_Name"].iloc[:2]) & set(
        report.names_for("plotted"))


def test_wood_with_none_of_its_elements_plots_nothing():
    """The case that was reported: every sample called plotted."""
    df = pd.DataFrame({"Sample_Name": ["a", "b"], "SiO2": [50.0, 52.0]})
    report = count_for_diagram(get_diagram("wood_1980_ThHfTa"), df, df,
                               PlotStyle())
    assert (report.plotted, report.missing) == (0, 2)


@pytest.mark.parametrize("key", TERNARIES)
def test_the_plot_and_the_mapping_agree_point_for_point(key, full_df):
    diagram = get_diagram(key)
    x, y = diagram._compute_xy(full_df)
    keep = x.notna() & y.notna()
    fig = Figure()
    diagram.plot(fig, full_df, PlotStyle(), PlotOptions())
    drawn = np.vstack([np.asarray(c.get_offsets(), float)
                       for c in fig.axes[0].collections
                       if isinstance(c, PathCollection)])
    expected = np.column_stack([x[keep], y[keep]])
    np.testing.assert_allclose(drawn[np.lexsort(drawn.T)],
                               expected[np.lexsort(expected.T)])


def test_a_click_on_a_triangle_identifies_the_sample(qapp, full_df):
    """Identify-sample resolves a click through _compute_xy; on a
    triangle it found nothing."""
    from birds.main_window import BirdsMainWindow

    window = BirdsMainWindow()
    window.data.df = full_df
    view = window.classification
    view.rock_type_filter_chk.setChecked(False)
    view._diagram_key = "afm"
    view.update_plot()
    x, y = get_diagram("afm")._compute_xy(full_df)
    i = int(np.flatnonzero(x.notna().to_numpy())[3])
    hit = view._resolve_sample(float(x.iloc[i]), float(y.iloc[i]))
    assert hit is not None and hit[2] == full_df["Sample_Name"].iloc[i]
