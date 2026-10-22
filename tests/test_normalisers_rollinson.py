"""Spider-diagram normalisers against Rollinson & Pease (2021).

``birds/normalizations.py`` credits its REE chondrites, shale composites
and multi-element normalisers to the book's Tables 4.7, 4.8 and 4.9.
``tests/data/rollinson_pease_2021_tables.json`` holds those columns as
the book prints them, and every value of ours that they contain must be
theirs.  Checking found six that were not (pinned below), a NASC that
carried the upper crust's Pb and Y where the book has "nd", and the
Arevalo & McDonough global mean filed as an N-MORB.

What this copy of the book cannot confirm is listed, so that a new or
changed value outside the tables is noticed rather than assumed checked.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from birds import normalizations as N

BOOK = json.loads((Path(__file__).parent / "data"
                   / "rollinson_pease_2021_tables.json").read_text())["tables"]

#: (group, name) -> (table, column) where the book prints it.
CHECKED = {
    ("REE_CHONDRITES", "Sun & McDonough (1989) – CI"): ("4.7", "1"),
    ("REE_CHONDRITES", "McDonough & Sun (1995) – CI"): ("4.7", "2"),
    ("REE_CHONDRITES", "Anders & Grevesse (1989) – CI avg"): ("4.7", "3"),
    ("REE_CHONDRITES", "Pourmand et al. (2012)"): ("4.7", "6"),
    ("REE_CHONDRITES", "Barrat et al. (2012) – Orgueil"): ("4.7", "7"),
    ("REE_CHONDRITES", "Wakita et al. (1971) – ordinary chondrites"): ("4.7", "9"),
    ("REE_SHALES", "NASC (McLennan 1989)"): ("4.8", "1"),
    ("REE_SHALES", "MUQ (Kamber et al. 2005)"): ("4.8", "2"),
    ("REE_SHALES", "PAAS (Pourmand et al. 2012)"): ("4.8", "3"),
    ("REE_SHALES", "European Shale (Bau et al. 2018)"): ("4.8", "4"),
    ("REE_SHALES", "World Shale Average (Bau et al. 2018)"): ("4.8", "5"),
    ("REE_SHALES", "Upper Continental Crust (Rudnick & Gao 2014)"): ("4.8", "6"),
    ("MULTIELEMENT_NORMS", "CI Chondrite (McDonough & Sun 1995)"): ("4.9", "1"),
    ("MULTIELEMENT_NORMS", "Primitive Mantle (McDonough & Sun 1995)"): ("4.9", "3"),
    ("MULTIELEMENT_NORMS", "Primitive Mantle (Palme & O'Neill 2014)"): ("4.9", "4"),
    ("MULTIELEMENT_NORMS",
     "Global MORB, log-normal mean (Arevalo & McDonough 2010)"): ("4.9", "6"),
    ("MULTIELEMENT_NORMS", "N-MORB (Sun & McDonough 1989)"): ("4.9", "8"),
    ("MULTIELEMENT_NORMS", "NASC (Gromet et al. 1984)"): ("4.9", "9"),
    ("MULTIELEMENT_NORMS",
     "Upper Continental Crust (Rudnick & Gao 2014)"): ("4.9", "10"),
}

#: Whole references this copy cannot confirm.  Table 4.7 is cut off at
#: its tenth column (Taylor & McLennan is its 12th, Boynton its 14th),
#: Table 4.9 at its eleventh (bulk crust), and Table 4.9 has no E-MORB.
#: All but the bulk crust were then read in their own papers:
#: ``test_normalisers_primary_sources.py``.
NOT_IN_THE_BOOKS_COPY = {
    ("REE_CHONDRITES", "Boynton (1984)"),
    ("REE_CHONDRITES", "Taylor & McLennan (1985) – CI calc. volatile-free"),
    ("MULTIELEMENT_NORMS", "E-MORB (Sun & McDonough 1989)"),
    ("MULTIELEMENT_NORMS", "Bulk Continental Crust (Rudnick & Gao 2014)"),
}

#: Single values a checked reference carries that its column does not:
#: Table 4.9 lists no P.
ELEMENTS_NOT_IN_THE_TABLE = {
    ("MULTIELEMENT_NORMS", "CI Chondrite (McDonough & Sun 1995)"): {"P"},
    ("MULTIELEMENT_NORMS", "Primitive Mantle (McDonough & Sun 1995)"): {"P"},
    ("MULTIELEMENT_NORMS", "N-MORB (Sun & McDonough 1989)"): {"P"},
    ("MULTIELEMENT_NORMS",
     "Upper Continental Crust (Rudnick & Gao 2014)"): {"P"},
}


def _ours(group, name):
    return getattr(N, group)[name]


def _column(table, col):
    return BOOK[table][col]


@pytest.mark.parametrize("group, name", list(CHECKED))
def test_every_value_is_the_books(group, name):
    ours, book = _ours(group, name), _column(*CHECKED[(group, name)])
    wrong = {el: (v, book[el]) for el, v in ours.items()
             if el in book and v != pytest.approx(book[el], rel=1e-12)}
    assert not wrong, wrong


@pytest.mark.parametrize("group, name", list(CHECKED))
def test_nothing_is_carried_that_the_column_leaves_out(group, name):
    """The NASC carried Pb 17 and Y 21 where Gromet et al. have "nd" --
    the upper crust's values, one column over."""
    ours, book = _ours(group, name), _column(*CHECKED[(group, name)])
    extra = set(ours) - set(book)
    assert extra == ELEMENTS_NOT_IN_THE_TABLE.get((group, name), set()), extra


@pytest.mark.parametrize("group, name", list(CHECKED))
def test_nothing_the_column_gives_is_left_out(group, name):
    """The NASC lacked Gromet et al.'s Ta."""
    ours, book = _ours(group, name), _column(*CHECKED[(group, name)])
    assert set(book) <= set(ours), set(book) - set(ours)


def test_every_reference_is_checked_or_listed_as_not():
    every = {(g, n) for g in ("REE_CHONDRITES", "REE_SHALES",
                              "MULTIELEMENT_NORMS")
             for n in getattr(N, g)}
    assert every == set(CHECKED) | NOT_IN_THE_BOOKS_COPY


def test_the_count():
    checked = sum(len(set(_ours(g, n)) & set(_column(*CHECKED[(g, n)])))
                  for g, n in CHECKED)
    assert checked == 366


@pytest.mark.parametrize("group, name, element, book_value", [
    ("REE_SHALES", "PAAS (Pourmand et al. 2012)", "Tm", 0.451),
    ("MULTIELEMENT_NORMS", "Primitive Mantle (Palme & O'Neill 2014)", "Cs", 0.018),
    ("MULTIELEMENT_NORMS", "NASC (Gromet et al. 1984)", "Ti", 4705),
    ("MULTIELEMENT_NORMS", "NASC (Gromet et al. 1984)", "Ta", 1.12),
    ("MULTIELEMENT_NORMS", "Upper Continental Crust (Rudnick & Gao 2014)", "Rb", 84),
    ("MULTIELEMENT_NORMS", "Upper Continental Crust (Rudnick & Gao 2014)", "K", 23244),
    ("MULTIELEMENT_NORMS", "Upper Continental Crust (Rudnick & Gao 2014)", "Ti", 3836),
])
def test_what_checking_corrected(group, name, element, book_value):
    """They were 0.4516, 0.0188, 4707, absent, 82, 23200 and 3840."""
    assert _ours(group, name)[element] == book_value


def test_the_nasc_has_no_lead_or_yttrium():
    nasc = N.MULTIELEMENT_NORMS["NASC (Gromet et al. 1984)"]
    assert "Pb" not in nasc and "Y" not in nasc


# ---------------------------------------------------------------------------
# The book read twice
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ree_column, multi_column", [
    (("4.7", "2"), ("4.9", "1")),       # CI, McDonough & Sun (1995)
    (("4.8", "6"), ("4.9", "10")),      # upper crust, Rudnick & Gao (2014)
])
def test_the_tables_agree_where_they_print_the_same_reference(ree_column,
                                                              multi_column):
    """Two pages of the book, read separately, give the same numbers --
    a check on the reading as much as on the book."""
    a, b = _column(*ree_column), _column(*multi_column)
    shared = set(a) & set(b)
    assert len(shared) >= 14
    assert all(a[el] == b[el] for el in shared)


# ---------------------------------------------------------------------------
# The renamed MORB mean
# ---------------------------------------------------------------------------

def test_a_session_saved_under_the_n_morb_name_finds_the_global_mean(qapp):
    from birds.data_manager import DataManager
    from birds.plot_style import PlotStyle
    from birds.views.spider import SpiderView

    old = "N-MORB mean (Arevalo & McDonough 2010)"
    new = "Global MORB, log-normal mean (Arevalo & McDonough 2010)"
    assert N.current_name(old) == new and old not in N.MULTIELEMENT_NORMS
    view = SpiderView(DataManager(), PlotStyle())
    view.restore({"mode": "multielement",
                  "multielement": {"normaliser": old}})
    assert view._controls["multielement"].norm_combo.currentText() == new
