"""The Verma coefficient sets against the authors' own Statistica sheet.

``tests/data/verma_statistica_sheet.json`` holds every discriminant
function and group centroid of the eight sets as the worksheet in which
Verma's group computed them defines it -- most to 17 figures, where the
papers print 2 to 10.  A paper prints the sheet's value rounded or cut
short, so each coefficient here must be the sheet's, rounded or
truncated to the digits it carries.

Checking that found eight values copied wrong in Verma & Verma (2013)
Sets 2 and 3 -- among them a P2O5 coefficient of -1.1082014 for
-1.082014, which moved DF1 by up to 0.19 on real samples -- and
confirmed, from the sheet, the sign of Nb in Verma et al. (2013) eq
(16): the paper prints +0.382, the sheet has -0.38213.
"""

from __future__ import annotations

import json
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from pathlib import Path

import pytest

from birds import verma_probability as VP
from birds.diagrams.templates import verma_coefficients as V

SHEET = json.loads((Path(__file__).parent / "data"
                    / "verma_statistica_sheet.json").read_text())
TABLES = list(SHEET["functions"])

#: Values a paper prints that are neither the sheet's value rounded nor
#: truncated -- each read on the rendered page, so it stays as printed.
PAPER_SLIPS = {
    # Verma & Verma (2013) eq (7): sheet 0.11236087.
    ("VV13_MAJOR", "DF1_IA_CROI_COL", "P2O5"),
    # Verma et al. (2013) eqs (1) and (16), rounded the wrong way:
    # sheet -2.11492 and 7.27450.
    ("V13A_MACID", "DF1_IACA_CROI_COL", "const"),
    ("V13A_MTACID", "DF2_IA_CA_COL", "const"),
}


def _values(table, key):
    """(label, ours, sheet's) for every coefficient and the constant."""
    ours = getattr(V, table)[key]
    sheet = SHEET["functions"][table][key]
    rows = [(p, c, sheet["coefs"][p]) for p, c in zip(ours.parts, ours.coefs)]
    return rows + [("const", ours.intercept, sheet["intercept"])]


def _printed_from(sheet_value, ours):
    """Is *ours* the sheet's value rounded or truncated to its digits?"""
    mine = Decimal(repr(float(ours)))
    step = Decimal(1).scaleb(mine.as_tuple().exponent)
    full = Decimal(repr(float(sheet_value)))
    return mine in (full.quantize(step, rounding=ROUND_HALF_UP),
                    full.quantize(step, rounding=ROUND_DOWN))


@pytest.mark.parametrize("table", TABLES)
def test_every_function_has_the_sheets_terms(table):
    for key, coef in getattr(V, table).items():
        sheet = SHEET["functions"][table][key]
        assert set(coef.parts) == set(sheet["coefs"]), key


@pytest.mark.parametrize("table", TABLES)
def test_every_value_is_the_sheets_as_printed(table):
    wrong = []
    for key in getattr(V, table):
        for label, ours, theirs in _values(table, key):
            if (table, key, label) in PAPER_SLIPS:
                assert abs(ours - theirs) < 0.0055, (key, label)
                continue
            if not _printed_from(theirs, ours):
                wrong.append((key, label, ours, theirs))
    assert not wrong, wrong


@pytest.mark.parametrize("table, key, part, value", [
    ("VV13_IMINT", "DF1_IACA_CROI_COL", "const", 1.900726416),
    ("VV13_IMINT", "DF1_IA_CA_COL", "Y", -0.6405805),
    ("VV13_IMINT", "DF1_IA_CA_COL", "const", 8.1087217398),
    ("VV13_IMINT", "DF2_IA_CA_COL", "Ni", -0.1339018),
    ("VV13_IMINT", "DF1_CA_CROI_COL", "MgO", -1.25554),
    ("VV13_IMINT", "DF1_CA_CROI_COL", "P2O5", -1.082014),
    ("VV13_TRACE", "DF2_IA_CA_COL", "Nb", -0.0782899),
    ("VV13_TRACE", "DF1_IA_CROI_COL", "La", 0.720851),
])
def test_the_eight_values_copied_wrong(table, key, part, value):
    """They were 1.90072648, -0.6405806, 8.108721398, -0.1339918,
    -1.255543, -1.1082014, -0.07828951 and 0.7208951; the rendered
    page agrees with the sheet on every one."""
    coef = getattr(V, table)[key]
    got = coef.intercept if part == "const" else dict(
        zip(coef.parts, coef.coefs))[part]
    assert got == value


def test_the_sheet_settles_the_sign_of_nb_in_eq_16():
    """Verma et al. (2013) print +0.382; the sheet they computed with
    has -0.38213, which is what the program uses."""
    sheet = SHEET["functions"]["V13A_MTACID"]["DF2_IA_CA_COL"]["coefs"]["Nb"]
    ours = dict(zip(V.V13A_MTACID["DF2_IA_CA_COL"].parts,
                    V.V13A_MTACID["DF2_IA_CA_COL"].coefs))["Nb"]
    assert sheet == pytest.approx(-0.38213, abs=1e-5)
    assert ours == -0.382


# ---------------------------------------------------------------------------
# Centroids
# ---------------------------------------------------------------------------

def _centroid_gap(table):
    worst = 0.0
    for panel, cents in SHEET["centroids"][table].items():
        ours = VP.CENTROIDS[table][panel]
        for group, (x, y) in zip(VP.PANEL_GROUPS[panel], cents):
            ox, oy = ours[group]
            worst = max(worst, abs(ox - x), abs(oy - y))
    return worst


@pytest.mark.parametrize("table", ["VV13_MAJOR", "VV13_IMINT", "VV13_TRACE"])
def test_verma_verma_centroids_are_the_sheets(table):
    assert _centroid_gap(table) < 1e-8


def test_the_derived_verma_agrawal_centroids_are_within_0_015():
    """Derived from the group means of Table 2, for want of the
    supplement that prints them."""
    assert _centroid_gap("VA11") < 0.015


@pytest.mark.parametrize("table", ["V13A_MACID", "V13A_MTACID",
                                   "V13A_TACID"])
def test_the_printed_acid_centroids_are_the_sheets_rounded(table):
    """The 2013 acid papers print one or two decimals."""
    assert _centroid_gap(table) < 0.055


@pytest.mark.parametrize("table", ["VA11", "V12_ACID"])
def test_the_sheets_centroids_put_the_triple_point_where_printed(table):
    """The point of equal probability is the circumcentre of the three
    centroids; each paper prints it, and the sheet's centroids, used
    nowhere in that, put it there.  Verma et al. (2012) print no
    centroids at all."""
    fields = getattr(V, f"{table}_FIELDS")
    for panel, cents in SHEET["centroids"][table].items():
        tx, ty = fields[panel]["triple"]
        cx, cy = VP.circumcentre(cents)
        assert ((cx - tx) ** 2 + (cy - ty) ** 2) ** 0.5 < 0.004, panel
