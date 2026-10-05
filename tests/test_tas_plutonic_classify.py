"""Naming a plutonic rock from the TAS, after Middlemost (1994).

`TASVolcanic` has had `classify()` for a while; the plutonic one did
not, and the reason recorded was that its outlines do not tile.  They
do not, as stored: two of the sixteen are kept as the single boundary
segment each contributes to the drawing, because the rest of their
edges belong to their neighbours and drawing them twice would show.
Closing those two is the whole of the fix, and with them closed the
sixteen tile exactly.

What says they may be closed that way is Middlemost's own text, which
sets the plutonic scheme out as the volcanic one renamed — gabbro for
basalt, diorite for andesite, granodiorite for dacite, syenite for
trachyte, granite for rhyolite, foid gabbro for tephrite, and so on.
The two fields here are the volcanic phonotephrite and tephriphonolite
under plutonic names, and take their vertices.  Both closures were
then checked against Figure 4 and land on its drawn outlines.

Unlike the volcanic scheme this takes no normative arguments.  It
needs none: Middlemost gives foid gabbro one name where the volcanic
plane splits tephrite from basanite, and he draws the quartz monzonite
field rather than splitting a trachyte field at 20 % normative quartz.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.templates.tas import (
    CLASSIFY_ALKALI_MAX,
    TASPlutonic,
    TASVolcanic,
    _PLUTONIC_CLOSURES,
    _PLUTONIC_FIELDS,
    _PLUTONIC_NAMES,
    _PLUTONIC_PATHS,
)

#: A point well inside each field, and the name it must come back as.
INSIDE = [
    ("Peridotgabbro", 43.0, 1.5),
    ("Gabbro", 48.0, 3.0),
    ("Gabbroic diorite", 55.0, 3.0),
    ("Diorite", 60.0, 4.0),
    ("Granodiorite", 68.0, 4.0),
    ("Granite", 75.0, 6.0),
    ("Quartz monzonite", 66.0, 9.0),
    ("Syenite", 62.0, 12.0),
    ("Monzonite", 59.0, 8.0),
    ("Monzodiorite", 54.0, 7.0),
    ("Monzogabbro", 49.0, 6.0),
    ("Foid gabbro", 44.0, 6.0),
    ("Foidolite", 40.0, 10.0),
    ("Foid monzodiorite", 48.0, 9.0),
    ("Foid monzosyenite", 52.0, 11.0),
    ("Foid syenite", 57.0, 15.0),
]


# ---------------------------------------------------------------------------
# The two closures
# ---------------------------------------------------------------------------

def test_only_two_outlines_needed_closing():
    assert set(_PLUTONIC_CLOSURES) == {"Foid\nMonzodiorite",
                                       "Foid\nMonzosyenite"}
    for name in _PLUTONIC_CLOSURES:
        assert len(_PLUTONIC_FIELDS[name]) == 2, (
            f"{name!r} is no longer stored as a bare segment, so the "
            f"closure here may be describing something else")


@pytest.mark.parametrize("plutonic, volcanic", [
    ("Foid\nMonzodiorite", "Phonotephrite"),
    ("Foid\nMonzosyenite", "Tephriphonolite"),
])
def test_each_closure_is_its_volcanic_twin(plutonic, volcanic):
    """Middlemost's correspondence is what licenses the vertices.

    He names these fields as the volcanic ones renamed, so the closed
    plutonic outline has to be the volcanic polygon itself rather than
    anything drawn by hand to look right.
    """
    from birds.diagrams.templates.tas import _VOLCANIC_FIELDS

    assert (sorted(map(tuple, _PLUTONIC_CLOSURES[plutonic]))
            == sorted(map(tuple, _VOLCANIC_FIELDS[volcanic])))


# ---------------------------------------------------------------------------
# The regions tile
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def grid():
    xs = np.arange(30.05, 90.0, 0.2)
    ys = np.arange(0.05, 19.0, 0.08)
    X, Y = np.meshgrid(xs, ys)
    return xs, ys, np.column_stack([X.ravel(), Y.ravel()])


def test_no_two_fields_claim_the_same_composition(grid):
    _xs, _ys, pts = grid
    count = np.zeros(len(pts), dtype=int)
    for _name, path in _PLUTONIC_PATHS:
        count += path.contains_points(pts)
    overlap = np.flatnonzero(count > 1)
    assert overlap.size == 0, (
        f"{overlap.size} compositions are claimed by more than one field, "
        f"the first at {pts[overlap[0]]}")


def test_there_are_no_holes_inside_the_diagram(grid):
    """A gap would name a real rock nothing, with no way to notice.

    An unclaimed cell counts as interior when claimed cells lie both
    sides of it along its row and both sides along its column.
    """
    xs, ys, pts = grid
    count = np.zeros(len(pts), dtype=int)
    for _name, path in _PLUTONIC_PATHS:
        count += path.contains_points(pts)
    claimed = (count > 0).reshape(len(ys), len(xs))

    holes = 0
    for j in range(len(ys)):
        row = claimed[j]
        if not row.any():
            continue
        for i in np.flatnonzero(~row):
            if not (row[:i].any() and row[i + 1:].any()):
                continue
            col = claimed[:, i]
            if col[:j].any() and col[j + 1:].any():
                holes += 1
    assert holes == 0, f"{holes} interior compositions fall through"


# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------

def test_every_field_has_a_name_and_every_name_a_field():
    assert set(_PLUTONIC_NAMES) == set(_PLUTONIC_FIELDS)
    assert len(set(_PLUTONIC_NAMES.values())) == len(_PLUTONIC_NAMES)


@pytest.mark.parametrize("name, sio2, alkalis", INSIDE)
def test_a_composition_inside_a_field_gets_its_name(name, sio2, alkalis):
    assert TASPlutonic.classify(sio2, alkalis) == name


def test_the_names_are_the_rocks_not_the_labels():
    """The outlines carry newlines and hyphens so the labels fit.

    Stripping the newline is not enough: "Monzo\\n-gabbro" has to come
    back as monzogabbro and "Gabbro\\ndiorite" as gabbroic diorite.
    """
    assert _PLUTONIC_NAMES["Monzo\n-gabbro"] == "Monzogabbro"
    assert _PLUTONIC_NAMES["Gabbro\ndiorite"] == "Gabbroic diorite"
    assert _PLUTONIC_NAMES["Peridot\ngabbro"] == "Peridotgabbro"
    for name in _PLUTONIC_NAMES.values():
        assert "\n" not in name
        assert " -" not in name


@pytest.mark.parametrize("sio2, alkalis", [
    (95.0, 2.0),      # beyond the granite field: quartzolite, not drawn
    (45.0, 18.5),     # above foidolite: tawite/urtite/italite, not drawn
    (20.0, 3.0),      # off the left of the diagram
    (float("nan"), 3.0),
])
def test_a_composition_off_the_diagram_is_not_named(sio2, alkalis):
    assert TASPlutonic.classify(sio2, alkalis) == ""


def test_classify_frame_names_every_row():
    df = pd.DataFrame({"SiO2": [48.0, 75.0, 95.0, None],
                       "Na2O": [2.0, 4.0, 1.0, 3.0],
                       "K2O": [1.0, 2.0, 1.0, 1.0]})
    got = TASPlutonic.classify_frame(df)
    assert list(got) == ["Gabbro", "Granite", "", ""]
    assert list(got.index) == list(df.index)


def test_classify_frame_without_the_oxides_returns_blanks():
    df = pd.DataFrame({"SiO2": [48.0], "Na2O": [2.0]})
    assert list(TASPlutonic.classify_frame(df)) == [""]


# ---------------------------------------------------------------------------
# Against the volcanic scheme, which Middlemost says it renames
# ---------------------------------------------------------------------------

#: The pairs he sets out on page 222, plus the foid series and foidite.
MIDDLEMOST_PAIRS = {
    "Picrobasalt": "Peridotgabbro",
    "Basalt": "Gabbro",
    "Basaltic andesite": "Gabbroic diorite",
    "Andesite": "Diorite",
    "Dacite": "Granodiorite",
    "Rhyolite": "Granite",
    "Trachybasalt": "Monzogabbro",
    "Basaltic trachyandesite": "Monzodiorite",
    "Trachyandesite": "Monzonite",
    "Tephrite / Basanite": "Foid gabbro",
    "Phonotephrite": "Foid monzodiorite",
    "Tephriphonolite": "Foid monzosyenite",
    "Phonolite": "Foid syenite",
    "Foidite": "Foidolite",
}


@pytest.mark.parametrize("volcanic, plutonic", sorted(MIDDLEMOST_PAIRS.items()))
def test_the_two_schemes_agree_well_inside_each_field(volcanic, plutonic):
    """The strongest check available, and it was not designed in.

    The two sets of outlines were typed independently.  If Middlemost's
    correspondence holds, a composition well inside a volcanic field
    has to land inside its plutonic twin, and for fourteen pairs it
    does.
    """
    inside = {p: (s, a) for p, s, a in INSIDE}
    sio2, alkalis = inside[plutonic]
    assert TASPlutonic.classify(sio2, alkalis) == plutonic
    assert TASVolcanic.classify(sio2, alkalis) == volcanic


def test_where_the_two_schemes_part_company_and_why():
    """They are not the same diagram, and these are the three places.

    96.6 % of the shared plane agrees.  The rest is Middlemost having
    redrawn rather than traced, and is pinned here so that neither set
    of outlines gets "corrected" to match the other:

    * he closes the **foid syenite** field under a tawite/urtite/italite
      field that Le Bas has no equivalent of, where the volcanic
      phonolite runs open to the top of the plane;
    * he closes **granite** on the right, where volcanic rhyolite runs
      open, so the high-alkali corner above it is his syenite and
      quartz monzonite;
    * his **granodiorite/granite** boundary meets the axis at SiO2 77.3
      where Le Bas puts dacite/rhyolite at 77.0.  Measured off Figure 4
      the boundary extrapolates to 77.31, so the 0.3 is his, not a
      typing slip here.
    """
    # The 77.0-77.3 strip, which is a wedge closing on the axis rather
    # than a band: both boundaries slope up-left from it at much the
    # same angle, so the gap between them is only open very low down.
    assert TASVolcanic.classify(77.1, 0.05) == "Rhyolite"
    assert TASPlutonic.classify(77.1, 0.05) == "Granodiorite"

    # above the granite field, which Middlemost closes and Le Bas does not
    assert TASVolcanic.classify(72.0, 14.0) == "Rhyolite"
    assert TASPlutonic.classify(72.0, 14.0) == ""

    # above the foid syenite field, under his tawite/urtite/italite
    assert TASVolcanic.classify(58.0, 18.0) == "Phonolite"
    assert TASPlutonic.classify(58.0, 18.0) == ""


def test_the_disagreement_stays_small():
    """A sweep, so a change that widens it shows up here.

    If someone edits either set of outlines the agreement moves, and
    this is the number to look at before deciding which one is right.
    """
    xs = np.arange(35.1, 78.0, 0.4)
    ys = np.arange(0.1, 16.0, 0.2)
    agree = disagree = 0
    for sio2 in xs:
        for alk in ys:
            v = TASVolcanic.classify(float(sio2), float(alk))
            p = TASPlutonic.classify(float(sio2), float(alk))
            if not v or not p:
                continue
            want = MIDDLEMOST_PAIRS.get(v)
            if want is None:          # trachyte/trachydacite has no twin
                continue
            if want == p:
                agree += 1
            else:
                disagree += 1
    total = agree + disagree
    assert total > 5000
    assert agree / total > 0.95, f"only {100 * agree / total:.1f} % agree"


def test_the_plutonic_domain_is_closed_where_the_volcanic_one_is_open():
    """They stop in different places, and that is the sources again.

    The volcanic regions run past the published frame on purpose, so a
    rare ultra-alkaline analysis is named rather than silently dropped;
    Le Bas leaves foidite open at the top and the closure here follows
    it to CLASSIFY_ALKALI_MAX.  Middlemost draws foidolite as a closed
    polygon with the tawite/urtite/italite field above it, so the
    plutonic scheme stops at about 14.8 wt.% alkalis at SiO2 40 and
    says nothing above that rather than inventing a lid.
    """
    assert CLASSIFY_ALKALI_MAX == 20.0
    assert TASVolcanic.classify(40.0, 17.0) == "Foidite"

    assert TASPlutonic.classify(40.0, 14.7) == "Foidolite"
    assert TASPlutonic.classify(40.0, 14.8) == ""
