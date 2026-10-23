"""Drummond & Defant (1990) Figure 10: (La/Yb)N against YbN.

J. Geophys. Res. 95(B13), 21503-21521.  The figure the key
``defant_drummond_YbLaYb`` was attributed to all along: Defant &
Drummond's Nature paper of the same year has no Yb-La/Yb figure, and
for a while the key drew nothing but a threshold.  Figure 10 draws three
fields -- Archean TTG, post-Archean granitic rocks and the range of
MORB -- normalised to the chondrite the paper names, Wakita et al.
(1971).

The fields were measured on the figure.  What makes the measurement
trustworthy is that two things outside the figure land where they
should: the MORB sources of the caption's melting models fall in the
measured MORB bar, and the TTG field reproduces Martin's (1986), which
the caption says it is drawn after.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates import drummond_defant1990 as dd
from birds.diagrams.templates import martin1986
from birds.diagrams.templates.base import PlotOptions
from birds.normalizations import REE_CHONDRITES
from birds.plot_style import PlotStyle
from birds.reservoirs import RESERVOIRS

KEY = "defant_drummond_YbLaYb"


def test_the_key_saved_sessions_store_draws_figure_10():
    d = get_diagram(KEY)
    assert isinstance(d, dd.DrummondDefant1990LaYbN)
    assert "Drummond & Defant (1990)" in d.title
    assert (d.x_label, d.y_label) == ("YbN", "(La/Yb)N")


def test_the_frame_is_the_figures():
    """Ticked to 25 and 150, both axes drawn on beyond: to 27 and 170."""
    d = get_diagram(KEY)
    assert tuple(d.x_range) == dd.X_RANGE == (0.0, 27.0)
    assert tuple(d.y_range) == dd.Y_RANGE == (0.0, 170.0)
    assert not d.log_x and not d.log_y


def test_the_chondrite_is_the_one_the_paper_names():
    """Figure 1's caption: "Chondrite-normalized [Wakita et al., 1971]"."""
    assert dd.CHONDRITE.startswith("Wakita et al. (1971)")
    ch = REE_CHONDRITES[dd.CHONDRITE]
    assert (ch["La"], ch["Yb"]) == (0.340, 0.220)
    df = pd.DataFrame({"La": [3.4], "Yb": [0.22]})
    x, y = get_diagram(KEY)._compute_xy(df)
    assert float(x.iloc[0]) == pytest.approx(1.0)
    assert float(y.iloc[0]) == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# The measured fields
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field", [dd.TTG_FIELD, dd.POST_ARCHEAN_FIELD])
def test_the_fields_stay_inside_the_frame(field):
    for x, y in field:
        assert dd.X_RANGE[0] <= x <= dd.X_RANGE[1]
        assert dd.Y_RANGE[0] <= y <= dd.Y_RANGE[1]


@pytest.mark.parametrize("field", [dd.TTG_FIELD, dd.POST_ARCHEAN_FIELD])
def test_a_measured_vertex_claims_no_more_than_was_measured(field):
    """Two decimals in YbN, one in (La/Yb)N: a pixel is 0.04 and 0.4."""
    for x, y in field:
        assert round(x, 2) == x
        assert round(y, 1) == y


def test_the_vertical_edges_are_vertical():
    """The TTG field's right edge and the post-Archean field's left edge
    are drawn vertical; fitted independently, their ends agree."""
    right = [p for p in dd.TTG_FIELD if p[0] > 8]
    assert len(right) == 2 and right[0][0] == right[1][0] == 8.35
    left = [p for p in dd.POST_ARCHEAN_FIELD if p[0] < 5]
    assert len(left) == 2 and left[0][0] == left[1][0] == 4.62


def test_the_morb_bar():
    """Yb_N 7.91-15.99 on the scan, from the axis to (La/Yb)_N 5.2."""
    assert dd.MORB_RANGE == (7.9, 16.0, 0.0, 5.2)


@pytest.mark.parametrize("yb_n", [10.0, 12.0])
def test_the_captions_morb_sources_lie_in_the_measured_bar(yb_n):
    """The caption's melting models start from "a MORB source having
    YbN = 10 and (La/Yb)N = 1" and from one with YbN = 12.  Nothing in
    measuring the bar used either number."""
    out = dd.classify(np.array([yb_n]), np.array([1.0]))
    assert out[0] == dd.MORB


@pytest.mark.parametrize("name", ["N-MORB (Sun & McDonough 1989)",
                                  "E-MORB (Sun & McDonough 1989)"])
def test_sun_and_mcdonough_morb_fall_in_the_morb_bar(name):
    r = RESERVOIRS[name]
    x, y = dd.normalised(pd.DataFrame({"La": [r["La"]], "Yb": [r["Yb"]]}))
    assert dd.classify(x.to_numpy(), y.to_numpy())[0] == dd.MORB


def test_the_ttg_field_is_martins_redrawn():
    """"Modified after Jahn et al. [1981] and Martin [1986]".

    Vertex by vertex within 1.7 in (La/Yb)N and 0.12 in YbN of Martin's
    Figure 1, measured separately on a different scan.  These agree as
    drawings; BIRDS normalises Martin to Boynton, not Wakita, so the
    same rock does not land on the same spot of the two diagrams.
    """
    assert len(dd.TTG_FIELD) == len(martin1986.TTG_FIELD)
    for (x1, y1), (x2, y2) in zip(dd.TTG_FIELD, martin1986.TTG_FIELD):
        assert abs(x1 - x2) <= 0.12 + 1e-9
        assert abs(y1 - y2) <= 1.7 + 1e-9


def test_the_adakite_line_falls_just_right_of_the_ttg_field():
    """Yb <= 1.9 ppm is from the Nature paper, not this figure; on
    Wakita's chondrite it is Yb_N 8.64, against the TTG field's right
    edge at 8.35 -- 1.84 ppm.  Two papers, the same limit to 0.06 ppm."""
    assert dd.ADAKITE_YB_N_MAX == pytest.approx(1.9 / 0.220)
    right = max(x for x, _ in dd.TTG_FIELD)
    assert 0 < dd.ADAKITE_YB_N_MAX - right < 0.3
    assert right * 0.220 == pytest.approx(1.84, abs=0.005)


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("la, yb, expected", [
    (18.0, 0.9, dd.TTG),                               # adakite
    (25.0, 3.0, dd.POST_ARCHEAN),
    (2.5, 3.05, dd.MORB),                              # N-MORB
    (20.0, 1.5, f"{dd.TTG} or {dd.POST_ARCHEAN}"),     # the overlap
    (50.0, 5.0, ""),                                   # above them all
])
def test_classify(la, yb, expected):
    df = pd.DataFrame({"La": [la], "Yb": [yb]})
    assert get_diagram(KEY).classify_frame(df).iloc[0] == expected


def test_missing_or_zero_ytterbium_is_unclassified():
    df = pd.DataFrame({"La": [10.0, 10.0, np.nan], "Yb": [0.0, np.nan, 1.0]})
    assert get_diagram(KEY).classify_frame(df).tolist() == ["", "", ""]


def test_without_la_nothing_is_classified():
    df = pd.DataFrame({"Yb": [1.0]})
    assert get_diagram(KEY).classify_frame(df).tolist() == [""]


# ---------------------------------------------------------------------------
# Drawn
# ---------------------------------------------------------------------------

def test_the_three_fields_and_the_line_are_drawn():
    fig = Figure()
    df = pd.DataFrame({"La": [18.0], "Yb": [0.9]})
    get_diagram(KEY).plot(fig, df, PlotStyle(), PlotOptions())
    ax = fig.axes[0]
    patches = [p for p in ax.patches if isinstance(p, Polygon)]
    assert len(patches) == 3
    assert sum(bool(p.get_hatch()) for p in patches) == 1   # MORB, shaded
    texts = " ".join(t.get_text() for t in ax.texts)
    for word in ("Archean TTG", "Post-Archean", "MORB", "adakite",
                 "Nature 1990"):
        assert word in texts
    dotted = [ln for ln in ax.lines if ln.get_linestyle() == ":"]
    assert any(np.allclose(ln.get_xdata(), dd.ADAKITE_YB_N_MAX)
               for ln in dotted)
    fig.clf()
