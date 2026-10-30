"""The anomalies are axes of the Bivariate view, Individual and Paired.

Eu/Eu*, Ce/Ce*, Nb/Nb*, (La/Yb)N… were in Statistics and the data table
but could not be plotted.  They are offered now beside the chemistry,
with the values those views show -- the same function, the same majors,
the same chondrite -- and nothing is written into the dataset.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection

from birds.expression import evaluate
from birds.per_sample import calculated_columns
from birds.stats_engine import ANOMALY_DESCRIPTIONS

ANOMALIES = ("Eu/Eu*", "Ce/Ce*", "Nb/Nb*", "(La/Yb)N", "Ti/Ti*")


@pytest.fixture
def window(qapp, full_df):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = full_df.copy()
    w.style.group_columns = ["Group"]
    w.on_dataset_replaced()
    w._open_bivariate("individual")
    return w


def _points(fig):
    return sum(len(c.get_offsets()) for ax in fig.axes
               for c in ax.collections if isinstance(c, PathCollection)
               and not c.get_label().startswith("_"))


def test_the_anomalies_are_offered_after_the_chemistry(window):
    window.data.df["Latitude"] = 19.0
    window.on_dataset_replaced()
    cols = window.bivariate._numeric_columns()
    for name in ANOMALIES:
        assert name in cols, name
    assert cols.index("Lu") < cols.index("Eu/Eu*") < cols.index("Latitude")


def test_they_are_the_values_statistics_shows(window):
    view = window.bivariate
    frame = view._frame()
    reference = window.statistics.norm_combo.currentData()
    table = calculated_columns(window.data, reference)
    for name in ANOMALIES:
        np.testing.assert_allclose(evaluate(frame, name), table[name],
                                   equal_nan=True, err_msg=name)


def test_nothing_is_written_into_the_dataset(window):
    window.bivariate.update_plot()
    assert not set(ANOMALY_DESCRIPTIONS) & set(window.data.df.columns)


def test_an_anomaly_on_an_individual_axis(window, qapp):
    view = window.bivariate
    view._individual.x_combo.setCurrentText("SiO2")
    view._individual.y_combo.setCurrentText("Eu/Eu*")
    view.update_plot()
    qapp.processEvents()
    expected = int(view._frame()["Eu/Eu*"].notna().sum())
    assert expected > 0
    assert _points(view.canvas.figure) == expected
    _df, xs, ys = view._current_plot_xy()
    assert ys.notna().sum() == expected


def test_anomalies_in_a_paired_grid(window, qapp):
    view = window.bivariate
    window._open_bivariate("paired")
    ctrl = view._paired
    for lst, wanted in ((ctrl.x_list, {"SiO2"}),
                        (ctrl.y_list, {"Eu/Eu*", "Nb/Nb*"})):
        lst.clearSelection()
        for i in range(lst.count()):
            if lst.item(i).text() in wanted:
                lst.item(i).setSelected(True)
    view.update_plot()
    qapp.processEvents()
    axes = view.canvas.figure.axes
    assert len(axes) >= 2
    assert {view._paired_axes[ax][1] for ax in axes
            if ax in view._paired_axes} == {"Eu/Eu*", "Nb/Nb*"}
    assert _points(view.canvas.figure) > 0


def test_the_chondrite_is_the_one_statistics_uses(window):
    view = window.bivariate
    combo = window.statistics.norm_combo
    assert combo.count() > 1
    before = evaluate(view._frame(), "Eu/Eu*")
    # A chondrite giving other values than the first
    for i in range(1, combo.count()):
        combo.setCurrentIndex(i)
        assert view.anomaly_reference() == combo.currentData()
        after = evaluate(view._frame(), "Eu/Eu*")
        if not np.allclose(before, after, equal_nan=True):
            break
    else:
        pytest.fail("no chondrite changed Eu/Eu*")


def test_an_anomaly_is_marked_and_explained(window):
    colour, tip = window.bivariate._variable_hint("Eu/Eu*")
    assert "Eu" in tip and "chondrite" in tip.lower()


def test_a_column_of_the_users_own_wins(window):
    df = window.data.df
    df["Eu/Eu*"] = 7.0
    window.on_dataset_replaced()
    frame = window.bivariate._frame()
    assert (evaluate(frame, "Eu/Eu*") == 7.0).all()
    assert list(frame.columns).count("Eu/Eu*") == 1


def test_no_trace_elements_no_anomalies(qapp, majors_df):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = majors_df.copy()
    w.on_dataset_replaced()
    cols = w.bivariate._numeric_columns()
    assert not set(ANOMALY_DESCRIPTIONS) & set(cols)
    assert isinstance(w.bivariate._frame(), pd.DataFrame)
