"""Cabanis & Lecolle (1989) La/10 – Y/15 – Nb/8.

C. R. Acad. Sci. **309** (II), 2023–2029, as redrawn with Verma's
(2010) reassessment in Rollinson & Pease (2021) Figure 5.4d.

**The apexes were wrong**, and that is the error that mattered: La/10
sat at the top where both sources put Y/15, so every sample was placed
by the wrong pair of coordinates.  The seven fields drawn under it were
quadrilaterals typed in ternary percent, approximating by eye a figure
whose real structure is wedges from the apex.

The two boundaries were measured twice, from two independent figures
by two different pipelines, as La/10 and Nb/8 percent where each meets
the base:

    source                         left (IAB|CRB)   right (CRB|OIB+MORB)
    Rollinson & Pease Fig. 5.4d    61.9 / 38.1      37.9 / 62.1
    the 1989 diagram reproduced    62.0 / 38.0      38.1 / 61.9

They agree to 0.2 %, so 62/38 and 38/62 are used.  Only the **left**
boundary reaches the apex; the right one branches off it part of the
way down, which is the one place the two sources differ.
"""

from __future__ import annotations

import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.tectonic_ternary import (
    CABANIS_BOUNDARIES,
    CABANIS_BRANCH_Y,
    CABANIS_BRANCH_Y_ORIGINAL,
    CABANIS_FIELDS,
)

DIAGRAM = "cabanis_lecolle_1989"

#: Sun & McDonough (1989), as (La, Y, Nb) in ppm.
REFERENCE = {
    "N-MORB": (2.50, 28.0, 2.33),
    "E-MORB": (6.30, 22.0, 8.30),
    "OIB": (37.0, 29.0, 48.0),
}


def _abc(la, y, nb):
    """(apex, left, right) as the diagram computes them, in percent."""
    df = pd.DataFrame({"La": [la], "Y": [y], "Nb": [nb]})
    a, b, c = get_diagram(DIAGRAM)._abc(df)
    total = float(a.iloc[0]) + float(b.iloc[0]) + float(c.iloc[0])
    return (100 * float(a.iloc[0]) / total,
            100 * float(b.iloc[0]) / total,
            100 * float(c.iloc[0]) / total)


def _la_share(la, y, nb):
    """La/(La+Nb) in plotted units, which is what the wedges cut on."""
    _apex, left, right = _abc(la, y, nb)
    return 100 * left / (left + right)


# ---------------------------------------------------------------------------
# The apexes
# ---------------------------------------------------------------------------

def test_y_is_at_the_apex_and_la_on_the_left():
    """The fault this file exists for.

    `ternary_to_xy` takes (apex, left, right), so `_abc` returning
    La first put La at the top.  Both published figures put Y/15 there.
    """
    # Y/15, La/10 and Nb/8 all equal 10 here, so the point is the
    # centroid and any mix-up of the three shows as a lopsided triple.
    apex, left, right = _abc(la=100.0, y=150.0, nb=80.0)
    assert (apex, left, right) == pytest.approx((100 / 3, 100 / 3, 100 / 3))

    # Y alone must move the apex coordinate
    apex2, _l, _r = _abc(la=100.0, y=300.0, nb=80.0)
    assert apex2 > apex
    # La alone must move the left one
    _a, left2, _r = _abc(la=200.0, y=150.0, nb=80.0)
    assert left2 > left


def test_the_apex_labels_match_the_coordinates(tmp_path):
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    from birds.plot_style import PlotStyle

    fig = Figure()
    df = pd.DataFrame({"La": [5.0], "Y": [22.0], "Nb": [1.5]})
    get_diagram(DIAGRAM).plot(fig, df, PlotStyle(), PlotOptions())
    texts = [t.get_text() for t in fig.axes[0].texts]
    assert "Y / 15" in texts
    assert "La / 10" in texts
    assert "Nb / 8" in texts
    # and the apex label is the topmost of the three
    pos = {t.get_text(): t.get_position()[1] for t in fig.axes[0].texts
           if t.get_text() in ("Y / 15", "La / 10", "Nb / 8")}
    assert pos["Y / 15"] > pos["La / 10"]
    assert pos["Y / 15"] > pos["Nb / 8"]
    fig.clf()


# ---------------------------------------------------------------------------
# The measured boundaries
# ---------------------------------------------------------------------------

def test_the_two_boundaries_as_measured():
    assert CABANIS_BOUNDARIES == {
        "IAB|CRB": (62.0, 38.0),
        "CRB|OIB+MORB": (38.0, 62.0),
    }


def test_the_boundaries_are_symmetric_about_the_median():
    """Measured independently, and they mirror each other to 0.1 %.

    Not imposed: the two figures gave 61.9/38.1 and 37.9/62.1, and
    62.0/38.0 and 38.1/61.9, before anything was rounded.
    """
    la_l, nb_l = CABANIS_BOUNDARIES["IAB|CRB"]
    la_r, nb_r = CABANIS_BOUNDARIES["CRB|OIB+MORB"]
    assert la_l == pytest.approx(nb_r)
    assert nb_l == pytest.approx(la_r)
    assert la_l + nb_l == pytest.approx(100.0)


def test_each_boundary_sums_to_the_whole_edge():
    for la, nb in CABANIS_BOUNDARIES.values():
        assert la + nb == pytest.approx(100.0)


def test_only_the_left_boundary_reaches_the_apex():
    """The right one branches off it, which both figures show.

    Where it branches is the one thing they disagree about, by eight
    and a half points of height, and it changes nothing below that.
    """
    assert 0.0 < CABANIS_BRANCH_Y < 100.0
    assert CABANIS_BRANCH_Y == pytest.approx(89.4)
    assert CABANIS_BRANCH_Y_ORIGINAL == pytest.approx(80.9)
    assert abs(CABANIS_BRANCH_Y - CABANIS_BRANCH_Y_ORIGINAL) < 10.0


# ---------------------------------------------------------------------------
# The three fields, against the original's own labels
# ---------------------------------------------------------------------------

def test_the_three_fields_tile_the_base():
    spans = [(hi, lo) for _n, hi, lo in CABANIS_FIELDS]
    assert spans[0][0] == 100.0
    assert spans[-1][1] == 0.0
    for (_hi, lo), (hi_next, _lo) in zip(spans, spans[1:]):
        assert lo == hi_next                     # no gap, no overlap
    cuts = {spans[0][1], spans[1][1]}
    assert cuts == {62.0, 38.0}


@pytest.mark.parametrize("label, la_share, wedge", [
    # Where the original figure puts each of its own field labels,
    # converted to ternary coordinates and read as La/(La+Nb).
    ("Calc-alkali", 77.6, "IAB"),
    ("VAT", 76.7, "IAB"),
    ("Cont.", 49.9, "CRB"),
    ("EMORB", 23.7, "OIB + MORB"),
    ("Alkaline", 20.2, "OIB + MORB"),
    ("Intercontinental rifts", 20.0, "OIB + MORB"),
])
def test_the_originals_labels_fall_in_the_wedge_that_absorbs_them(
        label, la_share, wedge):
    """The check that the three-field grouping is the right collapse.

    Cabanis & Lecolle name seven fields; Figure 5.4d shows three.  If
    the collapse is faithful, each of the original's labels has to sit
    inside the wedge that is supposed to contain it -- and all six that
    can be placed do.
    """
    got = next(n.split("\n")[0] for n, hi, lo in CABANIS_FIELDS
               if lo <= la_share <= hi)
    assert got == wedge, label


# ---------------------------------------------------------------------------
# What the diagram is and is not good for
# ---------------------------------------------------------------------------

def test_an_arc_basalt_lands_in_the_arc_field():
    """The one setting Verma found this diagram reliable for."""
    assert _la_share(la=5.0, y=22.0, nb=1.5) > 62.0


def test_the_reference_morb_and_oib_do_not_land_in_their_own_field():
    """Not a fault here: it is the weakness the sources warn about.

    Verma (2010) puts OIB + MORB at 29-62 % correctly classified, so
    most of them land somewhere else, and Sun & McDonough's own
    reference compositions show it.  N-MORB falls in the continental
    rift wedge outright, and OIB sits on the boundary to a tenth of a
    percent.  Both are recorded so that nobody later reads them as a
    transcription error and "fixes" the boundaries to suit them.
    """
    assert _la_share(*REFERENCE["N-MORB"]) == pytest.approx(46.2, abs=0.2)
    assert 38.0 < _la_share(*REFERENCE["N-MORB"]) < 62.0       # CRB wedge

    assert _la_share(*REFERENCE["OIB"]) == pytest.approx(38.1, abs=0.2)
    assert abs(_la_share(*REFERENCE["OIB"]) - 38.0) < 0.3      # on the line

    # E-MORB is the one that lands where it should, and only just
    assert _la_share(*REFERENCE["E-MORB"]) < 38.0


def test_the_citation_says_what_it_is_reliable_for():
    citation = get_diagram(DIAGRAM).citation
    assert "74" in citation                      # IAB, the usable one
    assert "42" in citation                      # CRB
    assert "29" in citation and "62" in citation  # OIB + MORB
    assert "Verma" in citation
    assert "not drawn" in citation               # the finer subdivisions


def test_a_sample_missing_an_element_is_declined_rather_than_guessed():
    df = pd.DataFrame({"La": [5.0], "Y": [22.0]})
    assert get_diagram(DIAGRAM)._abc(df) is None
