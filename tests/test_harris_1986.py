"""Harris, Pearce & Tindle (1986) Rb/30 – Hf – Ta×3.

Geol. Soc. London Spec. Publ. **19**, 67–81, Figure 6.  Two errors, and
the first is the one that mattered.

**The apexes were wrong.**  Hf sat at the top with Rb bottom left;
Figure 6 puts **Rb/30 at the apex**, Hf bottom left and Ta×3 bottom
right.  **And the divisor was wrong**: Rb/10 where the figure, its
caption and Figure 7 all say Rb/30.  Between them every sample was
placed by the wrong pair of coordinates and with one of them three
times too large.  The four fields drawn under it were quadrilaterals
typed in ternary percent.

The boundaries are now measured off Figure 6.  Its triangle is
equilateral to 0.04 %, which is what fixes the calibration, and the
dotted boundaries separate from the data cleanly because the two
populations do not overlap in size — 241 components of 32–64 px for
the dots, 133 of 256–4096 px for the triangles and squares.  RANSAC
over the dots recovers five segments carrying 245 of 260, each
straight to 0.5–4.3 px rms against a triangle 2008 px wide.
"""

from __future__ import annotations

import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.tectonic_ternary import (
    HARRIS_BOUNDARIES,
    HARRIS_FIELD_LABELS,
    _HARRIS_BEND,
    _HARRIS_GREEN_START,
    _HARRIS_III_WP_BRANCH,
    _HARRIS_VA_WP_BRANCH,
)

DIAGRAM = "harris_1986_HfRbTa"


def _abc(rb, hf, ta):
    """(apex, left, right) as the diagram computes them, in percent."""
    df = pd.DataFrame({"Rb": [rb], "Hf": [hf], "Ta": [ta]})
    a, b, c = get_diagram(DIAGRAM)._abc(df)
    total = float(a.iloc[0]) + float(b.iloc[0]) + float(c.iloc[0])
    return tuple(100 * float(v.iloc[0]) / total for v in (a, b, c))


# ---------------------------------------------------------------------------
# The apexes and the divisor
# ---------------------------------------------------------------------------

def test_rb_is_at_the_apex_and_hf_on_the_left():
    """Rb/30 = Hf = 3Ta = 10 here, so the point is the centroid.

    Any mix-up of the three shows as a lopsided triple, and the Rb
    value needed to make it balance is itself the divisor test: 300,
    not 100.
    """
    assert _abc(rb=300.0, hf=10.0, ta=10.0 / 3.0) == pytest.approx(
        (100 / 3, 100 / 3, 100 / 3))


def test_the_divisor_is_thirty_not_ten():
    """Figure 6, its caption and Figure 7 all print Rb/30.

    Under Rb/10 the same rock sits three times further toward the
    apex, which is most of the way across the triangle.
    """
    with_30 = _abc(rb=300.0, hf=10.0, ta=10.0 / 3.0)[0]
    # what the old code would have produced for the same rock
    rb_10, hf, ta3 = 300.0 / 10.0, 10.0, 10.0
    with_10 = 100 * rb_10 / (rb_10 + hf + ta3)
    assert with_30 == pytest.approx(100 / 3)
    assert with_10 == pytest.approx(60.0)
    assert with_10 > 1.7 * with_30


@pytest.mark.parametrize("element, index", [("Rb", 0), ("Hf", 1), ("Ta", 2)])
def test_each_element_moves_only_its_own_coordinate(element, index):
    base = dict(rb=300.0, hf=10.0, ta=10.0 / 3.0)
    before = _abc(**base)
    base[{"Rb": "rb", "Hf": "hf", "Ta": "ta"}[element]] *= 2.0
    after = _abc(**base)
    assert after[index] > before[index]
    for other in range(3):
        if other != index:
            assert after[other] < before[other]


def test_the_apex_labels_match_the_coordinates():
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    from birds.plot_style import PlotStyle

    fig = Figure()
    df = pd.DataFrame({"Rb": [60.0], "Hf": [3.5], "Ta": [0.4]})
    get_diagram(DIAGRAM).plot(fig, df, PlotStyle(), PlotOptions())
    pos = {t.get_text(): t.get_position()
           for t in fig.axes[0].texts
           if t.get_text() in ("Rb / 30", "Hf", "3 Ta")}
    assert set(pos) == {"Rb / 30", "Hf", "3 Ta"}
    assert pos["Rb / 30"][1] > pos["Hf"][1]
    assert pos["Rb / 30"][1] > pos["3 Ta"][1]
    assert pos["Hf"][0] < pos["3 Ta"][0]
    fig.clf()


# ---------------------------------------------------------------------------
# The measured boundary network
# ---------------------------------------------------------------------------

def test_there_are_five_segments():
    assert len(HARRIS_BOUNDARIES) == 5


@pytest.mark.parametrize("name", sorted(HARRIS_BOUNDARIES))
def test_every_vertex_is_a_proper_ternary_point(name):
    for vertex in HARRIS_BOUNDARIES[name]:
        assert len(vertex) == 3
        assert sum(vertex) == pytest.approx(100.0, abs=0.3)
        assert all(v >= 0.0 for v in vertex)


def test_the_network_is_connected_through_its_shared_vertices():
    """Each branch has to start on the boundary it leaves, or the
    fields do not close and a sample can fall through a gap."""
    va = HARRIS_BOUNDARIES["VA | Group II–III"]
    assert va[0] == _HARRIS_BEND
    assert va[1] == _HARRIS_VA_WP_BRANCH
    assert va[2] == _HARRIS_III_WP_BRANCH

    assert HARRIS_BOUNDARIES["top of Group II"][0] == _HARRIS_BEND
    assert HARRIS_BOUNDARIES["VA | WP"][0] == _HARRIS_VA_WP_BRANCH
    assert HARRIS_BOUNDARIES["Group III | WP"][0] == _HARRIS_III_WP_BRANCH


def test_the_green_boundary_starts_on_the_vertical_one():
    """It was fitted independently and lands on it within a unit.

    The II|III line was found by RANSAC without reference to the
    VA boundary; interpolating the VA boundary to the same Rb/30 gives
    Hf within 0.8, which is what says the two really do meet.
    """
    start = _HARRIS_GREEN_START
    assert HARRIS_BOUNDARIES["Group II | Group III"][0] == start
    top, bottom = _HARRIS_BEND, _HARRIS_VA_WP_BRANCH
    t = (start[0] - top[0]) / (bottom[0] - top[0])
    hf_on_va = top[1] + t * (bottom[1] - top[1])
    assert start[1] == pytest.approx(hf_on_va, abs=1.0)


def test_there_is_no_single_triple_point():
    """Two branches leave the vertical about four units apart.

    Fitting the three as concurrent lines put their pairwise
    intersections up to eleven units apart, which is how the stem
    between them was noticed; the figure draws it plainly once
    enlarged.  Nothing here should collapse them into one vertex.
    """
    assert _HARRIS_VA_WP_BRANCH != _HARRIS_III_WP_BRANCH
    gap = abs(_HARRIS_VA_WP_BRANCH[0] - _HARRIS_III_WP_BRANCH[0])
    assert 2.0 < gap < 6.0
    # the VA|WP branch is the higher of the two, as the figure shows
    assert _HARRIS_VA_WP_BRANCH[0] > _HARRIS_III_WP_BRANCH[0]


@pytest.mark.parametrize("name", [
    "top of Group II", "Group II | Group III", "Group III | WP",
])
def test_the_boundaries_that_run_off_to_the_right_edge_reach_it(name):
    """Hf = 0 is the Rb–Ta edge; a segment stopping short leaves a gap."""
    assert HARRIS_BOUNDARIES[name][-1][1] == pytest.approx(0.0, abs=0.1)


def test_the_va_wp_boundary_reaches_the_base():
    """Rb/30 = 0 is the Hf–Ta edge."""
    assert HARRIS_BOUNDARIES["VA | WP"][-1][0] == pytest.approx(0.0, abs=0.1)


# ---------------------------------------------------------------------------
# The four fields
# ---------------------------------------------------------------------------

def test_the_four_fields_are_named_as_the_paper_names_them():
    names = [n for n, *_ in HARRIS_FIELD_LABELS]
    assert names[0] == "VA"
    assert names[-1] == "WP"
    assert "Group II" in names[1] and "syn-collision" in names[1]
    assert "Group III" in names[2] and "post-collision" in names[2]


@pytest.mark.parametrize("name, a, b, c", HARRIS_FIELD_LABELS)
def test_every_label_sits_inside_the_triangle(name, a, b, c):
    assert sum((a, b, c)) == pytest.approx(100.0, abs=0.3)
    assert all(v > 0.0 for v in (a, b, c))


def test_group_ii_is_the_rubidium_rich_corner():
    """Syn-collision leucogranites are what this diagram is for.

    The paper's whole point about Group II is high Rb/Zr and Ta/Nb, so
    its field has to sit nearer the Rb apex than any other.
    """
    by_name = {n.split("\n")[0]: (a, b, c) for n, a, b, c in
               HARRIS_FIELD_LABELS}
    assert by_name["Group II"][0] == max(v[0] for v in by_name.values())
    assert by_name["WP"][0] == min(v[0] for v in by_name.values())


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------

def test_a_syn_collision_leucogranite_lands_above_the_group_ii_boundary():
    """High Rb, low Hf, high Ta -- the Himalayan leucogranite signature.

    It has to end up on the Group-II side of the II|III line, which is
    the one distinction this diagram was built to make.
    """
    apex, left, right = _abc(rb=400.0, hf=2.5, ta=3.0)
    start, end = HARRIS_BOUNDARIES["Group II | Group III"]
    t = (left - start[1]) / (end[1] - start[1])
    rb_on_line = start[0] + t * (end[0] - start[0])
    assert apex > rb_on_line


def test_a_volcanic_arc_granite_lands_left_of_the_va_boundary():
    apex, left, right = _abc(rb=60.0, hf=3.5, ta=0.4)
    top, bottom = _HARRIS_BEND, _HARRIS_VA_WP_BRANCH
    t = (apex - top[0]) / (bottom[0] - top[0])
    hf_on_boundary = top[1] + t * (bottom[1] - top[1])
    assert left > hf_on_boundary          # more Hf = further left


def test_a_sample_missing_an_element_is_declined_rather_than_guessed():
    df = pd.DataFrame({"Rb": [100.0], "Hf": [4.0]})
    assert get_diagram(DIAGRAM)._abc(df) is None


def test_the_catalogue_entry_names_the_right_apexes():
    """The menu text said Rb/10 too, in both the volcanic and the
    plutonic tree, so a user reading it would have divided by ten."""
    from birds.diagrams.catalog import TECTONIC_PLUTONIC, TECTONIC_VOLCANIC

    entries = [label
               for catalogue in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC)
               for section in catalogue.values()
               for label, key in section
               if key == DIAGRAM]
    assert len(entries) == 2, "the diagram dropped out of a catalogue"
    for label in entries:
        assert "Rb/30" in label
        assert "Rb/10" not in label
