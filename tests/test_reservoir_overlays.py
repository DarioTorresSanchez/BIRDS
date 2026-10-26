"""Reservoirs as the plots read them.

KLB-1, KR4003 and MIX1G, printed as major oxides only, plotted on
nothing but an axis of their own oxides: not against FeOt -- the
template's total iron, which every entry holds as FeOT, so no reservoir
at all plotted against it -- nor against Ni, Cr, Ti or K, which their
papers give as NiO, Cr2O3 and the other oxides.  In a spider diagram
they have no pattern at all and were listed anyway.

:func:`birds.reservoirs.composition` adds what follows from an entry's
own printed values and nothing else; the printed values stay as they
are.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from PySide6.QtCore import Qt

from birds.reservoirs import (
    FEO_TO_FE2O3,
    RESERVOIRS,
    composition,
    get_reservoir_value,
    has_trace_elements,
)

MAJORS_ONLY = ("Spinel lherzolite (KLB-1)", "Garnet lherzolite (KR4003)",
               "Pyroxenite (MIX1G)")


# ---------------------------------------------------------------------------
# What composition() adds
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", list(RESERVOIRS))
def test_every_entry_with_iron_answers_for_feot(name):
    c = composition(name)
    if "FeOT" in RESERVOIRS[name]:
        assert c["FeOt"] == RESERVOIRS[name]["FeOT"]
        assert c["Fe2O3T"] == pytest.approx(c["FeOT"] * 1.11134, rel=1e-5)


def test_fe2o3_per_feo_is_the_molar_mass_ratio():
    assert FEO_TO_FE2O3 == pytest.approx(159.687 / 143.688)


def test_the_old_iron_alias_is_gone():
    """``Fe2O3t`` used to return the FeOT value, 11 % low, and ``Mg#``
    returned MgO."""
    ucc = "UCC (Rudnick & Gao 2003)"
    assert get_reservoir_value(ucc, "fe2o3t") == pytest.approx(5.04 * 1.11134,
                                                               rel=1e-5)
    assert get_reservoir_value(ucc, "mg#") is None


@pytest.mark.parametrize("name, element, oxide, factor", [
    ("Spinel lherzolite (KLB-1)", "Ni", 0.25, 7858.0),
    ("Spinel lherzolite (KLB-1)", "Cr", 0.31, 6842.0),
    ("Garnet lherzolite (KR4003)", "Ni", 0.24, 7858.0),
    ("Garnet lherzolite (KR4003)", "Cr", 0.41, 6842.0),
    ("Pyroxenite (MIX1G)", "Cr", 0.11, 6842.0),
    ("Bulk CC (Rudnick & Gao 2003)", "K", 1.81, 8302),
    ("Bulk CC (Rudnick & Gao 2003)", "P", 0.13, 4364),
])
def test_ppm_from_the_printed_oxide(name, element, oxide, factor):
    assert get_reservoir_value(name, element) == pytest.approx(oxide * factor)


def test_the_dmm_cr_and_ni_follow_the_same_factors():
    """Its Cr and Ni were worked out from Cr2O3 0.57 and NiO 0.24 with
    these factors; going back gives the printed oxides."""
    c = composition("Depleted MORB mantle (Workman & Hart 2005)")
    assert c["Cr2O3"] == pytest.approx(0.57, abs=0.001)
    assert c["NiO"] == pytest.approx(0.24, abs=0.001)


@pytest.mark.parametrize("name", list(RESERVOIRS))
def test_a_printed_value_is_never_replaced(name):
    c = composition(name)
    for key, value in RESERVOIRS[name].items():
        assert c[key] == value, key


def test_mix1g_prints_no_nio_so_has_no_ni():
    assert get_reservoir_value("Pyroxenite (MIX1G)", "Ni") is None


def test_only_the_three_have_no_pattern():
    assert [n for n in RESERVOIRS if not has_trace_elements(n)] == list(
        MAJORS_ONLY)


# ---------------------------------------------------------------------------
# On the plots
# ---------------------------------------------------------------------------

@pytest.fixture
def bivariate(qapp, full_df):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    df = full_df.copy()
    df["FeOt"] = np.abs(df["FeO"]) + 0.8998 * np.abs(df["Fe2O3"])
    w.data.df = df
    w.on_dataset_replaced()
    # The page on screen draws at once (see views/deferral.py); no event
    # loop is needed, and running one here delivers late events of
    # windows other tests have already let go -- on Windows, into a
    # deleted canvas.
    w.stack.setCurrentWidget(w.bivariate)
    ind = w.bivariate._individual
    tree = ind.reservoirs_grp.tree
    for i in range(tree.topLevelItemCount()):
        top = tree.topLevelItem(i)
        for j in range(top.childCount()):
            if top.child(j).text(0) in MAJORS_ONLY:
                top.child(j).setCheckState(0, Qt.CheckState.Checked)
    return w


def _stars(w, qapp, x, y):
    ind = w.bivariate._individual
    ind.x_combo.setCurrentText(x)
    ind.y_combo.setCurrentText(y)
    assert (ind.x_combo.currentText(), ind.y_combo.currentText()) == (x, y)
    w.bivariate.update_plot()
    ax = w.bivariate.canvas.figure.axes[0]
    return sorted(tuple(c.get_offsets()[0]) for c in ax.collections
                  if len(c.get_offsets()) == 1)


@pytest.mark.parametrize("x, y, n", [
    ("SiO2", "MgO", 3),
    ("SiO2", "FeOt", 3),          # no reservoir plotted here before
    ("MgO", "Ni", 2),             # MIX1G prints no NiO
    ("MgO", "Cr", 3),
])
def test_the_three_plot_in_bivariate(bivariate, qapp, x, y, n):
    stars = _stars(bivariate, qapp, x, y)
    assert len(stars) == n
    if y == "FeOt":
        assert sorted(s[1] for s in stars) == [7.8, 8.02, 8.1]


def test_the_spider_does_not_offer_what_it_cannot_draw(qapp):
    from birds.data_manager import DataManager
    from birds.plot_style import PlotStyle
    from birds.views.spider import SpiderView
    from birds.views.widgets import ReservoirGroup
    view = SpiderView(DataManager(), PlotStyle())
    for group in view.findChildren(ReservoirGroup):
        tree = group.tree
        listed = [tree.topLevelItem(i).child(j).text(0)
                  for i in range(tree.topLevelItemCount())
                  for j in range(tree.topLevelItem(i).childCount())]
        assert not set(listed) & set(MAJORS_ONLY)
        assert len(listed) == len(RESERVOIRS) - len(MAJORS_ONLY)


def test_a_spider_pattern_gains_k_ti_and_p_from_its_oxides():
    """The Rudnick & Gao middle crust prints K2O, TiO2 and P2O5 and no
    K, Ti or P; its multi-element pattern had gaps there."""
    name = "MCC (Rudnick & Gao 2003)"
    for el, oxide, factor in (("K", "K2O", 8302), ("Ti", "TiO2", 5993.4),
                              ("P", "P2O5", 4364)):
        assert el not in RESERVOIRS[name]
        assert get_reservoir_value(name, el) == pytest.approx(
            RESERVOIRS[name][oxide] * factor)


def test_full_df_has_the_columns(full_df):
    assert {"SiO2", "MgO", "Ni", "Cr"} <= set(full_df.columns)
    assert isinstance(full_df, pd.DataFrame)
