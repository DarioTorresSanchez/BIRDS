"""Frost et al. (2001) / Frost & Frost (2008): the ASI is Shand's index.

ASI = molecular Al/(Ca - 1.67P + Na + K), and Rollinson & Pease (2021)
p. 127 say what the line at 1 means: peraluminous rocks "have more Al
than is needed to make feldspars", metaluminous ones lack it.  So every
feldspar has to sit on ASI = 1, anorthite included, and with no P2O5
the index has to equal Maniar & Piccoli's A/CNK.

It did neither.  Al, Na and K were doubled to cations and Ca was not,
which made the index 2A/(C + 2N + 2K): anorthite came out at 2, and a
granite at A/CNK 1.03 at 1.23, peraluminous on this panel whatever it
was on the other.

The wt.% of each mineral here is built from IUPAC atomic weights, not
from the module's molar masses, so the round trip checks those too.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.frost import APATITE_CA_PER_P, MOLAR_MASS

DIAGRAM = "frost"

# IUPAC standard atomic weights (conventional values where an interval
# is given).
_ATOMIC = {"Al": 26.9815385, "Ca": 40.078, "Na": 22.98976928,
           "K": 39.0983, "P": 30.973761998, "O": 15.999}

_OXIDE = {
    "Al2O3": 2 * _ATOMIC["Al"] + 3 * _ATOMIC["O"],
    "CaO": _ATOMIC["Ca"] + _ATOMIC["O"],
    "Na2O": 2 * _ATOMIC["Na"] + _ATOMIC["O"],
    "K2O": 2 * _ATOMIC["K"] + _ATOMIC["O"],
    "P2O5": 2 * _ATOMIC["P"] + 5 * _ATOMIC["O"],
}


def _wt(**moles) -> pd.DataFrame:
    """Oxide wt.% (unnormalised; only ratios matter) from oxide moles."""
    row = {ox: moles.get(ox, 0.0) * _OXIDE[ox] for ox in _OXIDE}
    row["SiO2"] = 60.0                    # needed by the panel, not read
    return pd.DataFrame([row])


def _asi(**moles) -> float:
    _si, asi = get_diagram(DIAGRAM)._asi(_wt(**moles))
    return float(asi.iloc[0])


def test_the_molar_masses_are_the_oxides_of_iupac_atomic_weights():
    """To the two decimals they carry; P2O5 used to be 141.95."""
    for oxide, mass in _OXIDE.items():
        assert MOLAR_MASS[oxide] == pytest.approx(mass, abs=0.005), oxide


@pytest.mark.parametrize("name, moles", [
    # Oxide-basis formula units; SiO2 does not enter.
    ("albite", {"Na2O": 1.0, "Al2O3": 1.0}),
    ("orthoclase", {"K2O": 1.0, "Al2O3": 1.0}),
    ("anorthite", {"CaO": 1.0, "Al2O3": 1.0}),
    ("An50 plagioclase", {"Na2O": 0.5, "CaO": 0.5, "Al2O3": 1.0}),
    ("ternary feldspar", {"Na2O": 0.3, "K2O": 0.2, "CaO": 0.5,
                          "Al2O3": 1.0}),
])
def test_every_feldspar_sits_on_asi_one(name, moles):
    """Anorthite was 2 and An50 1.33."""
    assert _asi(**moles) == pytest.approx(1.0, rel=1e-4), name


def test_without_phosphorus_it_is_maniar_and_piccolis_a_cnk():
    """The same index reaches the user twice; the two must agree.

    The two modules keep their own molar masses, so this is a real
    cross-check of the arithmetic, not a restatement of it.
    """
    rng = np.random.default_rng(2001)
    moles = rng.uniform(0.01, 1.0, size=(200, 4))
    parts = ["Al2O3", "CaO", "Na2O", "K2O"]
    df = pd.DataFrame({ox: moles[:, i] * _OXIDE[ox]
                       for i, ox in enumerate(parts)})
    df["SiO2"] = 60.0
    _si, asi = get_diagram(DIAGRAM)._asi(df)
    a_cnk, _a_nk = get_diagram("maniar_piccolli")._compute_xy(df)
    assert np.allclose(asi, a_cnk, rtol=1e-12)


def test_the_apatite_correction_takes_out_apatites_calcium():
    """Adding apatite to a feldspar leaves it on ASI = 1.

    Apatite is 10/3 CaO per P2O5.  The index removes 1.67 Ca per P
    atom, two atoms per P2O5, which is 3.34 against 3.333; the
    difference is the printed rounding of 5/3 and shows only at the
    fourth decimal even with 7 wt.% P2O5.
    """
    assert APATITE_CA_PER_P == 1.67
    for p2o5 in (0.002, 0.01, 0.05):
        with_ap = _asi(Na2O=0.6, CaO=0.4 + 10.0 / 3.0 * p2o5,
                       Al2O3=1.0, P2O5=p2o5)
        assert with_ap == pytest.approx(1.0, abs=5e-4)
        # without the correction the same rock reads metaluminous
        no_p = _asi(Na2O=0.6, CaO=0.4 + 10.0 / 3.0 * p2o5, Al2O3=1.0)
        assert no_p < 1.0


def test_a_missing_phosphorus_column_means_no_correction():
    df = _wt(Na2O=1.0, Al2O3=1.0).drop(columns=["P2O5"])
    _si, asi = get_diagram(DIAGRAM)._asi(df)
    assert float(asi.iloc[0]) == pytest.approx(1.0, rel=1e-4)


def test_the_sides_follow_the_mineralogy():
    """Al left over after feldspar is peraluminous; Ca left over is not."""
    assert _asi(Na2O=0.5, CaO=0.5, Al2O3=1.2) > 1.0      # + corundum
    assert _asi(Na2O=0.5, CaO=0.8, Al2O3=1.0) < 1.0      # + diopside's CaO


def test_a_granite_reads_the_same_on_both_diagrams():
    """The case that disagreed: A/CNK 1.03 came out at ASI 1.23."""
    df = pd.DataFrame([{"SiO2": 72.0, "Al2O3": 14.5, "CaO": 2.5,
                        "Na2O": 3.5, "K2O": 3.5}])
    _si, asi = get_diagram(DIAGRAM)._asi(df)
    a_cnk, _ = get_diagram("maniar_piccolli")._compute_xy(df)
    assert float(asi.iloc[0]) == pytest.approx(float(a_cnk.iloc[0]))
    assert float(asi.iloc[0]) == pytest.approx(1.029, abs=0.001)


# ---------------------------------------------------------------------------
# Panel (d): AI against FSSI
# ---------------------------------------------------------------------------

def _ai_fssi(**row) -> tuple[float, float]:
    ai, fssi = get_diagram(DIAGRAM)._ai_fssi(pd.DataFrame([row]))
    return float(ai.iloc[0]), float(fssi.iloc[0])


def test_the_signs_of_ai_and_fssi():
    """AI < 0 is Al-deficient; FSSI < 0 is silica-undersaturated."""
    mm = MOLAR_MASS
    feldspar = {"Al2O3": mm["Al2O3"], "Na2O": mm["Na2O"], "K2O": 0.0}
    ai, fssi = _ai_fssi(**feldspar, Q=20.0, Ne=0.0)
    assert ai == pytest.approx(0.0, abs=1e-12)
    assert fssi > 0
    ai, fssi = _ai_fssi(**{**feldspar, "Na2O": 1.2 * mm["Na2O"]},
                        Q=0.0, Ne=15.0)
    assert ai < 0
    assert fssi < 0


def test_each_quadrant_label_names_its_own_quadrant():
    """As Rollinson & Pease (2021) Figure 3.9d names them.

    The panel carried two labels, both wrong: "metaluminous,
    silica-saturated" sat at FSSI < 0, which is undersaturated, and
    "peralkaline, silica-saturated" at AI > 0, which is not peralkaline.
    The lower half had none.
    """
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    from birds.plot_style import PlotStyle

    fig = Figure()
    get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
    ax = fig.axes[3]
    assert ax.get_title() == "(d) AI vs FSSI"
    quadrants = set()
    for t in ax.texts:
        x, y = t.get_position()
        words = " ".join(t.get_text().split())
        assert ("undersaturated" in words) == (x < 0), words
        assert ("deficient" in words) == (y < 0), words
        assert ("excessive" in words) == (y > 0), words
        assert "metaluminous" not in words and "peralkaline" not in words
        quadrants.add((x > 0, y > 0))
    assert len(ax.texts) == 4 and len(quadrants) == 4
