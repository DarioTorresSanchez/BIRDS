"""The Data sheet's calculated columns: Mg#, ratios, anomalies per sample.

The values must be the Statistics view's -- a number in the table and
in Statistics is the same number -- worked out from the data as they
stand, never written into them.  Alongside: Ti now comes from TiO2 when
there is no Ti column, as every diagram takes it, and the table sorts
numbers as numbers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from PySide6.QtCore import Qt

from birds.normalizations import TIO2_WT_TO_TI_PPM

N = 6


@pytest.fixture
def window(qapp, full_df, plot_style):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    df = full_df.iloc[:N].copy()
    assert "Ti" not in df.columns          # TiO2 only, as most datasets
    w.data.df = df
    w.style.copy_from(plot_style)
    w.on_dataset_replaced()
    w.on_view_table()
    return w


def _calc(window):
    return window.data_table.model.calculated


def _col(window, name):
    """Source-model column of *name*, calculated or not."""
    model = window.data_table.model
    for c in range(model.columnCount()):
        if model.headerData(c, Qt.Orientation.Horizontal) == name:
            return c
    raise KeyError(name)


# ---------------------------------------------------------------------------
# What is shown
# ---------------------------------------------------------------------------

def test_the_data_sheet_ends_with_mg_ratios_and_anomalies(window):
    calc = _calc(window)
    assert calc is not None
    for name in ("Mg#", "Mg#_FeOt", "La/Yb", "Th/Nb", "Ti/Y", "CIA",
                 "Eu/Eu*", "Nb/Nb*", "Ti/Ti*", "(La/Yb)N"):
        assert name in calc.columns, name
    model = window.data_table.model
    assert model.source_column_count() == len(window.data.df.columns)
    assert model.columnCount() == len(window.data.df.columns) + len(
        calc.columns)
    assert "calculated (green)" in window.data_table.status_label.text()


def test_every_value_is_the_statistics_views(window):
    window._open_statistics()
    stats = window.statistics
    calc = _calc(window)
    shared = 0
    for frame in (stats.ratios_frame, stats.anomalies_frame):
        for name in frame.columns:
            if name in calc.columns:
                np.testing.assert_allclose(calc[name], frame[name],
                                           equal_nan=True, err_msg=name)
                shared += 1
    assert shared >= 35


def test_mg_number_is_the_bivariate_axis(window):
    from birds.derived import derived_series
    for name in ("Mg#", "Mg#_FeOt"):
        np.testing.assert_allclose(
            _calc(window)[name], derived_series(window.data.df, name))


def test_nothing_is_written_into_the_data(window):
    before = list(window.data.df.columns)
    window.data_table.refresh_from_data()
    assert list(window.data.df.columns) == before
    assert "Eu/Eu*" not in window.data.df.columns


def test_a_column_of_the_users_own_is_theirs(window):
    window.data.df["Mg#"] = 99.0
    window.data_table.refresh_from_data()
    assert "Mg#" not in _calc(window).columns
    model = window.data_table.model
    names = [model.headerData(c, Qt.Orientation.Horizontal)
             for c in range(model.columnCount())]
    assert names.count("Mg#") == 1


def test_the_switch_hides_them_and_other_sheets_have_none(window):
    table = window.data_table
    table.calc_chk.setChecked(False)
    assert table.model.calculated is None
    table.calc_chk.setChecked(True)
    window.data.isotopes_df = pd.DataFrame({"Sample_Name": ["S0"],
                                            "87Sr/86Sr": [0.704]})
    table.sheet_combo.setCurrentIndex(table.sheet_combo.findData("isotopes"))
    assert table.model.calculated is None
    assert not table.anomaly_combo.isEnabled()


def test_each_row_is_headed_by_its_sample(window):
    model = window.data_table.model
    assert model.headerData(2, Qt.Orientation.Vertical) == \
        window.data.df["Sample_Name"].iloc[2]


# ---------------------------------------------------------------------------
# Read-only, and always current
# ---------------------------------------------------------------------------

def test_calculated_cells_are_read_only(window):
    model = window.data_table.model
    index = model.index(0, _col(window, "La/Yb"))
    assert not model.flags(index) & Qt.ItemFlag.ItemIsEditable
    assert not model.setData(index, "5")
    raw = model.index(0, _col(window, "La"))
    assert model.flags(raw) & Qt.ItemFlag.ItemIsEditable


def test_editing_a_value_updates_its_ratios(window):
    model = window.data_table.model
    yb = window.data.df["Yb"].iloc[0]
    assert model.setData(model.index(0, _col(window, "La")), "100")
    shown = model.data(model.index(0, _col(window, "La/Yb")), Qt.ItemDataRole.DisplayRole)
    assert float(shown) == pytest.approx(round(100 / yb, 4))


def test_calculated_columns_cannot_be_deleted(window, monkeypatch):
    table = window.data_table
    monkeypatch.setattr(table, "_selected_source_columns",
                        lambda: [_col(window, "Eu/Eu*")])
    shown = []
    monkeypatch.setattr("birds.views.data_table.QMessageBox.information",
                        lambda *a, **k: shown.append(a[2]))
    before = list(window.data.df.columns)
    table.delete_selected_columns()
    assert list(window.data.df.columns) == before
    assert "cannot be deleted" in shown[0]


# ---------------------------------------------------------------------------
# Ti from TiO2
# ---------------------------------------------------------------------------

def test_ti_comes_from_tio2_when_there_is_no_ti_column(window):
    df = window.data.df
    expected = (df["TiO2"] * TIO2_WT_TO_TI_PPM / df["Y"]).round(4)
    np.testing.assert_allclose(_calc(window)["Ti/Y"], expected)


def test_a_ti_column_wins_over_tio2():
    from birds.stats_engine import compute_ratios
    df = pd.DataFrame({"TiO2": [1.0], "Ti": [1000.0], "Y": [10.0],
                       "V": [100.0]})
    assert compute_ratios(df)["Ti/Y"].iloc[0] == pytest.approx(100.0)


def test_ti_anomaly_follows_the_adjusted_majors(window):
    from birds.preprocess import attach_adjusted
    window.data.df = attach_adjusted(window.data.df)
    window.data.use_adjusted = True
    adjusted = window.statistics.anomaly_frame()["Ti/Ti*"]
    window.data.use_adjusted = False
    analysed = window.statistics.anomaly_frame()["Ti/Ti*"]
    ratio = (window.data.df["TiO2_adj"] / window.data.df["TiO2"])
    # Both are rounded to four decimals, hence the tolerance.
    np.testing.assert_allclose(adjusted, analysed * ratio, atol=2e-4)
    assert not np.allclose(adjusted, analysed)


# ---------------------------------------------------------------------------
# Sorting, export, one anomaly reference
# ---------------------------------------------------------------------------

def test_numbers_sort_as_numbers(qapp):
    from birds.data_manager import DataManager
    from birds.views.data_table import DataTableView
    data = DataManager()
    data.df = pd.DataFrame({"Sample_Name": list("ABCD"),
                            "SiO2": [9.0, 10.0, 100.0, np.nan]})
    view = DataTableView(data)
    view.refresh_from_data()
    view.table.sortByColumn(1, Qt.SortOrder.AscendingOrder)
    shown = [view.proxy.index(r, 1).data() for r in range(4)]
    assert shown == ["9", "10", "100", ""]           # was 10, 100, 9


def test_a_calculated_column_sorts_numerically(window):
    table = window.data_table
    col = _col(window, "La/Yb")
    table.table.sortByColumn(col, Qt.SortOrder.AscendingOrder)
    values = [float(table.proxy.index(r, col).data())
              for r in range(table.proxy.rowCount())]
    assert values == sorted(values)


@pytest.mark.parametrize("suffix", [".xlsx", ".csv"])
def test_export_writes_the_calculated_columns(window, tmp_path, monkeypatch,
                                              suffix):
    path = tmp_path / f"table{suffix}"
    monkeypatch.setattr(
        "birds.views.data_table.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(path), ""))
    window.data_table.export_table()
    back = (pd.read_excel(path) if suffix == ".xlsx" else pd.read_csv(path))
    assert len(back) == N
    assert list(back.columns[:len(window.data.df.columns)]) == list(
        window.data.df.columns)
    np.testing.assert_allclose(back["Eu/Eu*"], _calc(window)["Eu/Eu*"])
    assert "calculated" in window.data_table.status_label.text()


def test_one_anomaly_reference_for_table_and_statistics(window):
    table, stats = window.data_table.anomaly_combo, window.statistics.norm_combo
    table.setCurrentIndex(table.findData("Boynton (1984)"))
    assert stats.currentData() == "Boynton (1984)"
    # Statistics, opened, recomputes with the table's pick.
    window._open_statistics()
    np.testing.assert_allclose(
        window.statistics.anomalies_frame["Eu/Eu*"],
        window.statistics.anomaly_frame("Boynton (1984)")["Eu/Eu*"])
    stats.setCurrentIndex(stats.findData("Pourmand et al. (2012)"))
    assert table.currentData() == "Pourmand et al. (2012)"
    window.data_table.refresh_from_data()
    from birds.stats_engine import compute_anomalies_extended
    np.testing.assert_allclose(
        _calc(window)["Eu/Eu*"],
        compute_anomalies_extended(window.data.majors_df(),
                                   "Pourmand et al. (2012)")["Eu/Eu*"])


def test_anomaly_shading_is_the_statistics_key():
    from birds.per_sample import anomaly_sign
    from birds.views.statistics import (
        NEGATIVE_COLOR,
        POSITIVE_COLOR,
        _anomaly_color,
    )
    assert anomaly_sign("Eu/Eu*", 0.80) == -1 and anomaly_sign("Eu/Eu*", 1.2) == 1
    assert anomaly_sign("Eu/Eu*", 1.0) == 0 and anomaly_sign("La/Yb", 50) == 0
    assert anomaly_sign("Y/Ho", 35) == 1 and anomaly_sign("Y/Ho", 20) == -1
    assert _anomaly_color("Eu/Eu*", 0.8) == NEGATIVE_COLOR
    assert _anomaly_color("Ce/Ce*", 1.2) == POSITIVE_COLOR
