"""Vermeesch (2006a) Na-Nb-Sr and Ti-V-Sm: the two QDA ternaries.

They were the last two diagrams "drawn by eye, blocked": a QDA's
boundaries are conics that need the class covariances to compute, and
the paper prints none.  The paper does draw them, as vector curves, and
those curves are what the templates now carry.  Three checks tie them to
the paper, each independent of the drawing they came from:

* Figures 45a and 46a draw the same boundaries in log-ratio space;
  mapped back with ln they lie on the triangle's curves;
* Figures 45b and 46b plot the test samples, and the paper's test table
  says how each was classified: these fields classify them the same;
* the triangle is the paper's way up.

``tests/data/vermeesch2006_qda_figures.json`` holds the test samples'
positions and the log-ratio curves, read from the PDF's vector paths.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates import tectonic_ternary as tt

DATA = json.loads((Path(__file__).parent / "data"
                   / "vermeesch2006_qda_figures.json").read_text(encoding="utf-8"))
SPECS = {"NaNbSr": tt._QDA_NA_NB_SR, "SmTiV": tt._QDA_TI_V_SM}
CLASSES = ("IAB", "MORB", "OIB")


def _bezier(segments, n=200):
    t = np.linspace(0, 1, n)[:, None]
    out = []
    for seg in segments:
        p0, p1, p2, p3 = (np.asarray(p, float) for p in seg)
        out.append(((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1
                   + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
    return np.vstack(out)


def _xy(fractions):
    """Plot coordinates, in units of the triangle's side."""
    from birds.diagrams.templates.base import ternary_to_xy
    f = np.atleast_2d(fractions)
    x, y = ternary_to_xy(pd.Series(f[:, 0]), pd.Series(f[:, 1]),
                         pd.Series(f[:, 2]))
    return np.column_stack([x.to_numpy(), y.to_numpy()])


def _distance_to_boundary(spec, fractions):
    """Distance from each point to the drawn line, as a fraction of the
    triangle's side."""
    line = _xy(np.vstack(list(tt.qda_fields(spec).values())))
    p = _xy(fractions)
    return np.sqrt(((p[:, None, :] - line[None, :, :]) ** 2).sum(-1)).min(1)


# ---------------------------------------------------------------------------
# The drawing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key, top, left, right", [
    ("vermeesch_NaNbSr", "25 Nb", "Na/100", "Sr"),
    ("vermeesch_SmTiV", "Ti/50", "50 Sm", "V"),
])
def test_the_triangle_is_the_papers_way_up(key, top, left, right):
    """Both used to put Na/100 and 50 Sm at the top."""
    diagram = get_diagram(key)
    assert diagram.spec["apices"] == (top, left, right)
    df = pd.DataFrame({"Na2O": [3.0], "Nb": [10.0], "Sr": [300.0],
                       "TiO2": [1.5], "Sm": [4.0], "V": [250.0]})
    a, b, c = diagram._abc(df)
    if key == "vermeesch_NaNbSr":
        assert (a.iloc[0], c.iloc[0]) == (250.0, 300.0)
        assert b.iloc[0] == pytest.approx(3.0 * 0.7419 * 1e4 / 100)
    else:
        assert a.iloc[0] == pytest.approx(1.5 * 5993.4 / 50)
        assert (b.iloc[0], c.iloc[0]) == (200.0, 250.0)


def test_the_fields_are_closed_and_meet_where_drawn():
    for spec in SPECS.values():
        fields = tt.qda_fields(spec)
        for name in ("MORB", "OIB"):
            outline = fields[name]
            assert np.allclose(outline.sum(1), 1.0, atol=2e-4), name
            gap = np.linalg.norm(outline[0] - outline[-1])
            assert gap < 0.01, (name, gap)
    # The Na-Nb-Sr OIB lobe leaves and rejoins the MORB loop.
    morb = tt.qda_fields(tt._QDA_NA_NB_SR)["MORB"]
    lobe = tt._bezier_fractions(tt._QDA_NA_NB_SR["oib_lobe"])
    for end in (lobe[0], lobe[-1]):
        assert np.sqrt(((morb - end) ** 2).sum(1)).min() < 0.01
    # The Ti-V-Sm dome starts and ends on the 50 Sm - Ti/50 edge (V = 0).
    dome = tt._bezier_fractions(tt._QDA_TI_V_SM["oib"])
    assert dome[0][2] < 0.005 and dome[-1][2] < 0.005


def test_field_labels_sit_in_their_fields():
    for spec in SPECS.values():
        for name, abc in spec["labels"]:
            got = tt.qda_field(spec, [abc[0]], [abc[1]], [abc[2]]).iloc[0]
            assert got == name, (name, abc)


# ---------------------------------------------------------------------------
# Check 1: the log-ratio figures, mapped back with ln
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["NaNbSr", "SmTiV"])
def test_the_log_ratio_figure_maps_onto_the_triangle(name):
    xy = _bezier(DATA[name]["logratio_curves"])

    def mapped(base):
        left, right = base ** xy[:, 0], base ** xy[:, 1]
        total = 1.0 + left + right
        return np.column_stack([1.0 / total, left / total, right / total])

    with_ln = _distance_to_boundary(SPECS[name], mapped(np.e))
    with_log10 = _distance_to_boundary(SPECS[name], mapped(10.0))
    assert np.median(with_ln) < 0.005          # measured 0.34 % / 0.23 %
    assert np.percentile(with_ln, 90) < 0.01   # of the triangle's side
    assert np.median(with_log10) > 0.04        # measured 4.6 % / 6.1 %


#: The window each log-ratio figure draws, (x_min, x_max, y_min, y_max).
LOGRATIO_FRAMES = {"NaNbSr": (-2.24, 3.55, -2.84, 4.47),
                   "SmTiV": (-0.69, 2.06, -2.02, 2.39)}


@pytest.mark.parametrize("name", ["NaNbSr", "SmTiV"])
def test_every_drawn_boundary_in_the_window_is_on_the_log_ratio_curve(name):
    """The reverse check, point by point: wherever the log-ratio figure
    can see our boundary, the boundary lies on its curve -- a local
    error a median would hide is caught here."""
    xy = _bezier(DATA[name]["logratio_curves"], 400)
    left, right = np.exp(xy[:, 0]), np.exp(xy[:, 1])
    total = 1.0 + left + right
    curve = _xy(np.column_stack([1.0 / total, left / total, right / total]))
    ours = np.vstack(list(tt.qda_fields(SPECS[name]).values()))
    with np.errstate(divide="ignore", invalid="ignore"):
        lx = np.log(ours[:, 1] / ours[:, 0])
        ly = np.log(ours[:, 2] / ours[:, 0])
    # A margin off the window's edges: near the Ti/50 apex the dome's top
    # arc grazes Figure 46a's corner, where a hair's move in the triangle
    # is a large one in log-ratio units.
    x0, x1, y0, y1 = LOGRATIO_FRAMES[name]
    m = 0.25
    seen = (lx > x0 + m) & (lx < x1 - m) & (ly > y0 + m) & (ly < y1 - m)
    assert seen.sum() > 100
    p = _xy(ours[seen])
    d = np.sqrt(((p[:, None, :] - curve[None, :, :]) ** 2).sum(-1)).min(1)
    assert d.max() < 0.02, d.max()


def test_each_segment_starts_where_the_last_ended():
    runs = (tt._QDA_NA_NB_SR["oib_lobe"], tt._QDA_NA_NB_SR["morb"],
            tt._QDA_TI_V_SM["oib"], tt._QDA_TI_V_SM["morb_lower"])
    for run in runs:
        for before, after in zip(run, run[1:]):
            assert np.allclose(before[3], after[0], atol=1e-4)


# ---------------------------------------------------------------------------
# Check 2: the paper's test samples, classified
# ---------------------------------------------------------------------------

def _confusion(name):
    spec = SPECS[name]
    table = {}
    for true in CLASSES:
        pts = np.array(DATA[name]["test_markers"][true])
        got = tt.qda_field(spec, pts[:, 0], pts[:, 1], pts[:, 2])
        table[true] = [int((got == c).sum()) for c in CLASSES]
    return table


def test_na_nb_sr_classifies_every_test_sample_as_published():
    """All 61: 21 IAB right; 7 of 12 MORB right, 5 taken for IAB; all
    28 OIB right."""
    assert _confusion("NaNbSr") == DATA["published_test_table"]["NaNbSr"]


def test_ti_v_sm_differs_only_on_the_line():
    """82 of 85 as published.  The other three -- one in each row --
    lie on the drawn line, 0.05-0.31 % of the triangle's side from it,
    about the width of the stroke; every true misclassification lies
    clear of it."""
    spec = SPECS["SmTiV"]
    ours = _confusion("SmTiV")
    published = DATA["published_test_table"]["SmTiV"]
    moved = sum(abs(a - b) for t in CLASSES
                for a, b in zip(ours[t], published[t])) // 2
    assert moved == 3
    for true in CLASSES:
        off = sum(abs(a - b) for a, b in zip(ours[true], published[true])) // 2
        pts = np.array(DATA["SmTiV"]["test_markers"][true])
        on_line = (_distance_to_boundary(spec, pts) < 0.0035).sum()
        assert on_line >= off, true      # each difference has a sample on the line


# ---------------------------------------------------------------------------
# Through the template
# ---------------------------------------------------------------------------

def test_classify_frame_names_each_sample():
    df = pd.DataFrame({"TiO2": [np.nan, 1.6], "Sm": [3.0, 3.5],
                       "V": [250.0, 260.0]})
    got = get_diagram("vermeesch_SmTiV").classify_frame(df)
    assert got.iloc[0] == "" and got.iloc[1] in CLASSES


def test_the_plot_draws_the_fields_and_the_samples(full_df, plot_style):
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    for key in ("vermeesch_NaNbSr", "vermeesch_SmTiV"):
        fig = Figure()
        get_diagram(key).plot(fig, full_df, plot_style, PlotOptions())
        ax = fig.axes[0]
        texts = {t.get_text() for t in ax.texts}
        assert {"IAB", "MORB", "OIB"} <= texts, key
        assert len(ax.lines) >= 2
