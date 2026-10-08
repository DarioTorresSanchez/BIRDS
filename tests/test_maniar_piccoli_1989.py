"""Maniar & Piccoli (1989) A/CNK–A/NK, pinned to Shand's definitions.

GSA Bulletin **101**, 635-643; the index after Shand (1943).  Registry
key ``maniar_piccolli``, which keeps an old misspelling because saved
sessions store it.

The boundaries are rules, so there is nothing to measure: A/CNK = 1 and
A/NK = 1 *are* the boundaries.  What can go wrong is the arithmetic
under them and what is drawn around them, and both did:

* The ratios are molar.  A pure feldspar is the composition the two
  lines are defined by, so it has to land on them -- albite and
  orthoclase on both, any feldspar mixture on A/CNK = 1.  Computed in
  wt.% instead, albite would sit at A/NK = 1.64.
* A third line is drawn, the diagonal A/NK = A/CNK.  It is not a field
  boundary but the CaO = 0 limit, and it used to be stored under the
  name "Peralkaline", with that label in the quadrant below it, where no
  composition can plot.  Peralkaline rocks sit in the triangle above it.

The wt.% of each feldspar here is built from IUPAC atomic weights, not
from the module's molar masses, so the round trip checks those too.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import PlotOptions
from birds.diagrams.templates.maniar_piccolli import (
    A_CNK_BOUNDARY,
    A_NK_BOUNDARY,
    MOLAR_MASS,
)
from birds.plot_style import PlotStyle

DIAGRAM = "maniar_piccolli"

# IUPAC standard atomic weights (conventional values where an interval
# is given).
_ATOMIC = {"Al": 26.9815385, "Ca": 40.078, "Na": 22.98976928,
           "K": 39.0983, "O": 15.999}

_OXIDE = {
    "Al2O3": 2 * _ATOMIC["Al"] + 3 * _ATOMIC["O"],
    "CaO": _ATOMIC["Ca"] + _ATOMIC["O"],
    "Na2O": 2 * _ATOMIC["Na"] + _ATOMIC["O"],
    "K2O": 2 * _ATOMIC["K"] + _ATOMIC["O"],
}


def _wt(**moles) -> dict:
    """Oxide wt.% (unnormalised; only ratios matter) from oxide moles."""
    return {ox: [moles.get(ox, 0.0) * _OXIDE[ox]] for ox in _OXIDE}


def _xy(**moles) -> tuple[float, float]:
    x, y = get_diagram(DIAGRAM)._compute_xy(pd.DataFrame(_wt(**moles)))
    return float(x.iloc[0]), float(y.iloc[0])


def _field(x: float, y: float) -> str:
    """Shand's three fields, by rule."""
    if x > A_CNK_BOUNDARY:
        return "Peraluminous"
    if y < A_NK_BOUNDARY:
        return "Peralkaline"
    return "Metaluminous"


# ---------------------------------------------------------------------------
# The molar computation
# ---------------------------------------------------------------------------

def test_the_molar_masses_are_the_oxides_of_iupac_atomic_weights():
    """To the two decimals they carry.

    Both routes from wt.% would move together under a wrong shared
    constant, so it is checked against the atomic weights, not itself.
    """
    for oxide, mass in _OXIDE.items():
        assert MOLAR_MASS[oxide] == pytest.approx(mass, abs=0.005), oxide


@pytest.mark.parametrize("name, moles", [
    # Na2O.Al2O3.6SiO2 and K2O.Al2O3.6SiO2; SiO2 does not enter.
    ("albite", {"Na2O": 1.0, "Al2O3": 1.0}),
    ("orthoclase", {"K2O": 1.0, "Al2O3": 1.0}),
    ("Or40Ab60 alkali feldspar", {"K2O": 0.4, "Na2O": 0.6, "Al2O3": 1.0}),
])
def test_an_alkali_feldspar_sits_on_both_boundaries(name, moles):
    x, y = _xy(**moles)
    assert x == pytest.approx(A_CNK_BOUNDARY, rel=1e-4), name
    assert y == pytest.approx(A_NK_BOUNDARY, rel=1e-4), name


def test_every_feldspar_mixture_has_a_cnk_of_one():
    """Plagioclase too: CaO.Al2O3.2SiO2 brings one Al2O3 per CaO.

    For x albite + y orthoclase + z anorthite, in moles of formula
    units on the oxide basis, A/CNK = 1 and A/NK = 1 + z/(x + y).
    """
    for ab, or_, an in [(0.5, 0.0, 0.5), (0.3, 0.2, 0.5), (0.1, 0.1, 0.8)]:
        x, y = _xy(Na2O=ab, K2O=or_, CaO=an, Al2O3=ab + or_ + an)
        assert x == pytest.approx(1.0, rel=1e-4)
        assert y == pytest.approx(1.0 + an / (ab + or_), rel=1e-4)


def test_wt_percent_ratios_would_put_albite_off_the_line():
    """The guard the molar conversion exists for.

    Albite is 19.44 wt.% Al2O3 and 11.82 Na2O; their plain ratio, 1.64,
    is what a wt.% computation would plot.  The molar one is 1.
    """
    w = _wt(Na2O=1.0, Al2O3=1.0)
    total = sum(v[0] for v in w.values()) + 6 * (28.085 + 2 * 15.999)
    al_wt = 100 * w["Al2O3"][0] / total
    na_wt = 100 * w["Na2O"][0] / total
    assert al_wt == pytest.approx(19.44, abs=0.01)
    assert na_wt == pytest.approx(11.82, abs=0.01)
    assert al_wt / na_wt == pytest.approx(1.64, abs=0.01)

    x, y = get_diagram(DIAGRAM)._compute_xy(
        pd.DataFrame({"Al2O3": [al_wt], "CaO": [0.0], "Na2O": [na_wt],
                      "K2O": [0.0]}))
    assert float(y.iloc[0]) == pytest.approx(1.0, rel=1e-3)


def test_the_fields_follow_the_mineralogy():
    """Al left over after feldspar, Ca left over, Na left over."""
    # albite + corundum
    assert _field(*_xy(Na2O=1.0, Al2O3=1.2)) == "Peraluminous"
    # plagioclase + CaO as in diopside: more Ca than Al can make feldspar of
    assert _field(*_xy(Na2O=0.5, CaO=0.8, Al2O3=1.0)) == "Metaluminous"
    # albite + acmite's Na2O: more alkali than Al
    assert _field(*_xy(Na2O=1.2, Al2O3=1.0)) == "Peralkaline"


def test_a_nk_is_never_below_a_cnk_and_equals_it_without_cao():
    """The diagonal: A/NK / A/CNK = (C + N + K)/(N + K) >= 1."""
    rng = np.random.default_rng(1989)
    moles = rng.uniform(0.01, 1.0, size=(200, 4))
    moles[:20, 1] = 0.0                                  # CaO-free rows
    df = pd.DataFrame({ox: moles[:, i] * _OXIDE[ox]
                       for i, ox in enumerate(["Al2O3", "CaO", "Na2O",
                                               "K2O"])})
    x, y = get_diagram(DIAGRAM)._compute_xy(df)
    assert (y >= x).all()
    assert np.allclose(y[:20], x[:20])
    assert (y[20:] > x[20:]).all()


# ---------------------------------------------------------------------------
# What is drawn
# ---------------------------------------------------------------------------

def _rendered_axes():
    fig = Figure()
    get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
    return fig.axes[0]


def test_the_drawn_lines_are_exactly_the_two_boundaries_and_the_diagonal():
    d = get_diagram(DIAGRAM)
    (x0, x1), (y0, y1) = d.x_range, d.y_range
    lines = sorted(
        (tuple(map(float, ln.get_xdata())), tuple(map(float, ln.get_ydata())))
        for ln in _rendered_axes().lines)
    assert lines == sorted([
        ((1.0, 1.0), (y0, y1)),           # A/CNK = 1, the full height
        ((x0, x1), (1.0, 1.0)),           # A/NK = 1, the full width
        ((x0, x1), (x0, x1)),             # A/NK = A/CNK, CaO = 0
    ])
    assert A_CNK_BOUNDARY == 1.0 and A_NK_BOUNDARY == 1.0
    assert d.field_polygons == {}


def test_each_label_sits_inside_the_field_it_names_and_above_the_diagonal():
    """The labels are placed by eye and the fields are rules.

    "Peralkaline" used to sit at (1.25, 0.75): below A/NK = 1, but also
    right of A/CNK = 1 and below the diagonal, where nothing plots.
    """
    d = get_diagram(DIAGRAM)
    texts = {t.get_text(): t.get_position() for t in _rendered_axes().texts}
    assert set(texts) == {"Peraluminous", "Metaluminous", "Peralkaline"}
    for name, (x, y) in texts.items():
        assert _field(x, y) == name
        assert y > x, f"{name} label is below the CaO = 0 line"
        assert d.x_range[0] < x < d.x_range[1]
        assert d.y_range[0] < y < d.y_range[1]


def test_a_peralkaline_rhyolite_lands_beside_its_label():
    """A comendite-like composition, close to the diagonal as they are."""
    x, y = get_diagram(DIAGRAM)._compute_xy(pd.DataFrame(
        {"Al2O3": [9.5], "CaO": [0.3], "Na2O": [5.0], "K2O": [4.5]}))
    x, y = float(x.iloc[0]), float(y.iloc[0])
    assert _field(x, y) == "Peralkaline"
    assert x < y < 1.0
    label_x, label_y = get_diagram(DIAGRAM).field_label_pos["Peralkaline"]
    assert abs(x - label_x) < 0.1 and abs(y - label_y) < 0.2


# ---------------------------------------------------------------------------
# The name
# ---------------------------------------------------------------------------

def test_the_author_is_spelt_right_where_users_read_it():
    """Piccoli, with one l; the key keeps two because sessions store it."""
    d = get_diagram(DIAGRAM)
    assert d.key == "maniar_piccolli"
    for text in (d.title, d.citation):
        assert "Piccoli" in text
        assert "Piccolli" not in text
