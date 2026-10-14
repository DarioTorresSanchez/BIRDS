"""The Isotopes view's isotope-ratio-against-SiO2 diagram.

SiO2 comes from the Isotopes sheet, and where that is blank or missing
from the Data sheet for the same Sample_Name; the vertical axis is any
isotope ratio or delta / epsilon column, or εNd / εSr and the initial
ratios computed exactly as the Sr-Nd diagram computes them.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection

from birds.data_manager import DataManager
from birds.plot_style import PlotStyle

N = 6


@pytest.fixture
def view(qapp):
    from birds.views.isotopes import IsotopesView

    data = DataManager()
    names = [f"S{i}" for i in range(N)]
    data.df = pd.DataFrame({"Sample_Name": names,
                            "SiO2": np.linspace(48, 68, N),
                            "Rb": 40.0, "Sr": 400.0, "Sm": 5.0, "Nd": 25.0})
    data.isotopes_df = pd.DataFrame({
        "Sample_Name": names,
        "SiO2": [50.5, np.nan, np.nan, np.nan, np.nan, np.nan],
        "87Sr/86Sr": np.linspace(0.7040, 0.7080, N),
        "87Sr/86Sr_2σ": 1e-5,
        "143Nd/144Nd": np.linspace(0.51290, 0.51250, N),
        "δ18O": np.linspace(5.6, 7.9, N),
        "Rb": 40.0, "Sr": 400.0, "Sm": 5.0, "Nd": 25.0,
        "Age": 2.0, "Age_Unit": "Ma"})
    v = IsotopesView(data, PlotStyle())
    v.show_diagram()
    v.diagram_combo.setCurrentIndex(v.diagram_combo.findData("vs_sio2"))
    return v


def _drawn(v):
    ax = v.canvas.figure.axes[0]
    return np.vstack([np.asarray(c.get_offsets(), float)
                      for c in ax.collections if isinstance(c, PathCollection)])


def _choose(v, key):
    v.sio2_y_combo.setCurrentIndex(v.sio2_y_combo.findData(key))
    v.update_plot()


def test_the_choices_are_the_isotope_columns_and_the_derived_values(view):
    items = [view.sio2_y_combo.itemData(i)
             for i in range(view.sio2_y_combo.count())]
    assert {"87Sr/86Sr", "143Nd/144Nd", "δ18O"} <= set(items)
    assert "87Sr/86Sr_2σ" not in items and "Age" not in items
    assert {"derived:eps_nd", "derived:eps_sr", "derived:sr_i",
            "derived:nd_i"} <= set(items)
    assert view.sio2_y_combo.currentData() == "87Sr/86Sr"     # by default


def test_silica_comes_from_the_sheet_then_from_data(view):
    sio2 = view._silica(view.data.isotopes_df)
    assert sio2.iloc[0] == 50.5                      # the Isotopes value
    np.testing.assert_allclose(sio2.iloc[1:], np.linspace(48, 68, N)[1:])


def test_the_plot_draws_silica_against_the_ratio(view):
    _choose(view, "87Sr/86Sr")
    sio2 = view._silica(view.data.isotopes_df)
    expected = np.column_stack([sio2, np.linspace(0.7040, 0.7080, N)])
    np.testing.assert_allclose(_drawn(view), expected)
    ax = view.canvas.figure.axes[0]
    assert ax.get_xlabel() == "SiO₂ (wt.%)" and ax.get_ylabel() == "87Sr/86Sr"
    assert any(line.get_ydata()[0] == pytest.approx(0.7051)
               for line in ax.lines)                 # BSE, as on Sr-Nd


def test_epsilon_nd_is_the_sr_nd_diagrams_epsilon(view):
    from birds.views.isotopes import epsilon_nd

    _choose(view, "derived:eps_nd")
    nd = view.data.isotopes_df["143Nd/144Nd"]
    np.testing.assert_allclose(_drawn(view)[:, 1], epsilon_nd(nd))
    assert view.canvas.figure.axes[0].get_ylabel() == "εNd"


def test_with_the_age_correction_epsilon_is_at_the_age(view):
    view.age_box.setChecked(True)
    view.age_source.setCurrentIndex(view.age_source.findData("column"))
    view.age_column.setCurrentIndex(view.age_column.findData("Age"))
    _choose(view, "derived:eps_nd")
    expected = view._initials_and_eps(view.data.isotopes_df)["eps_nd_i"]
    np.testing.assert_allclose(_drawn(view)[:, 1], expected)
    assert view.canvas.figure.axes[0].get_ylabel() == "εNd(t)"


def test_without_silica_it_says_so(view):
    view.data.df = view.data.df.drop(columns="SiO2")
    view.data.isotopes_df = view.data.isotopes_df.drop(columns="SiO2")
    view.update_plot()
    texts = " ".join(t.get_text() for ax in view.canvas.figure.axes
                     for t in ax.texts)
    assert "No SiO₂ found" in texts


def test_the_choice_survives_a_session(view, qapp):
    from birds.views.isotopes import IsotopesView

    _choose(view, "δ18O")
    view.sio2_ref_chk.setChecked(False)
    state = view.serialize()
    other = IsotopesView(view.data, PlotStyle())
    other.show_diagram()
    other.restore(state)
    assert other.diagram_combo.currentData() == "vs_sio2"
    assert other.sio2_y_combo.currentData() == "δ18O"
    assert not other.sio2_ref_chk.isChecked()


def test_identify_reads_the_same_points(view):
    _choose(view, "δ18O")
    xs, ys = view._current_plot_xy(view.data.isotopes_df)
    np.testing.assert_allclose(np.column_stack([xs, ys]), _drawn(view))


def test_without_parents_the_label_says_present_day(view):
    """No Sm/Nd to correct with: εNd stays present-day, and says so."""
    view.data.isotopes_df = view.data.isotopes_df.drop(columns=["Sm", "Nd"])
    view.age_box.setChecked(True)
    _choose(view, "derived:eps_nd")
    assert view.canvas.figure.axes[0].get_ylabel() == "εNd"


def test_parents_come_from_the_ratio_then_the_aliquot_then_the_bulk():
    """The template's Sm_iso / Nd_iso were never read: with no
    147Sm/144Nd and no Sm, Nd columns there was no initial ratio."""
    from birds.views.isotopes import (
        SM_ND_TO_147_144,
        _resolve_parent_rb_sr,
        _resolve_parent_sm_nd,
    )

    df = pd.DataFrame({"147Sm/144Nd": [0.15, np.nan, np.nan],
                       "Sm_iso": [9.0, 4.0, np.nan],
                       "Nd_iso": [9.0, 20.0, np.nan],
                       "Sm": [1.0, 1.0, 6.0], "Nd": [1.0, 1.0, 30.0]})
    np.testing.assert_allclose(_resolve_parent_sm_nd(df),
                               [0.15, SM_ND_TO_147_144 * 0.2,
                                SM_ND_TO_147_144 * 0.2])
    only_iso = pd.DataFrame({"Rb_iso": [40.0], "Sr_iso": [400.0]})
    assert _resolve_parent_rb_sr(only_iso).iloc[0] > 0
    assert _resolve_parent_sm_nd(pd.DataFrame({"Sm": [1.0]})) is None
