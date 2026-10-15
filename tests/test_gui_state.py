"""Shared-state regressions.

Every test here corresponds to a bug that actually shipped: state that
outlived the dataset it described, or a tally that reported a figure the
canvas was not showing.
"""

from __future__ import annotations

import re

import numpy as np
import pandas as pd
import pytest

from birds.detection_limits import scan_and_convert
from birds.plot_style import GroupStyle
from conftest import MAJORS


def strip_html(text: str) -> str:
    return re.sub("<[^>]+>", "", text or "")


@pytest.fixture
def window(qapp):
    from birds.main_window import BirdsMainWindow
    return BirdsMainWindow()


@pytest.fixture
def censored_df():
    return pd.DataFrame({
        "Sample_Name": ["A", "B", "C"],
        "SiO2": ["50.0", "55.0", "60.0"],
        "Nb": ["<0.5", "3.2", "b.d.l."],
        "Group": ["x", "x", "y"],
    })


class TestDatasetReplacement:
    def test_data_table_follows_a_new_import(self, window, censored_df):
        """The table used to keep rendering the previous dataset."""
        window.data.df = censored_df
        window.on_dataset_replaced()
        assert window.data_table.model.rowCount() == 3

        bigger = pd.DataFrame({"Sample_Name": [f"S{i}" for i in range(8)],
                               "SiO2": np.linspace(45, 75, 8)})
        window.data.df = bigger
        window.on_dataset_replaced()
        assert window.data_table.model.rowCount() == 8

    def test_selection_is_cleared(self, window, censored_df):
        """Stale sample names would light up rows in the new dataset."""
        window.data.df = censored_df
        window.on_dataset_replaced()
        window.selection.toggle("A")
        assert len(window.selection) == 1
        window.data.df = censored_df.copy()
        window.on_dataset_replaced()
        assert len(window.selection) == 0

    def test_variable_pickers_follow(self, window, censored_df):
        window.data.df = censored_df
        window.on_dataset_replaced()
        combo = window.bivariate._individual.x_combo
        before = {combo.itemText(i) for i in range(combo.count())}
        window.data.df = censored_df.assign(Zr=[100.0, 120.0, 140.0])
        window.on_dataset_replaced()
        after = {combo.itemText(i) for i in range(combo.count())}
        assert "Zr" in after - before


class TestBdlMaskAlignment:
    def test_mask_stays_a_subset_after_preprocess(self, window):
        from birds.preprocess import pre_process
        raw = pd.DataFrame([dict(zip(MAJORS,
                                     ["50.0", 1.5, 15.0, 3.0, 7.0, 0.17,
                                      8.0, 11.0, 2.5, "<0.1", 0.2]),
                                 Sample_Name="A")])
        conv, mask, report = scan_and_convert(raw, "half")
        window.data.df = conv
        window.data.bdl_masks = {"main": mask}
        window.data.bdl_limits = {"main": report.limits}
        window.data.df = pre_process(window.data.df)
        window.data.realign_bdl_masks()
        aligned = window.data.bdl_masks["main"]
        assert set(aligned.columns) <= set(window.data.df.columns)
        assert len(aligned) == len(window.data.df)
        assert bool(aligned.loc[0, "K2O"]), "the K2O flag was lost"


class TestSampleTally:
    @pytest.fixture(autouse=True)
    def _on_screen(self, window):
        """The tally belongs to the page on screen; a page behind
        another holds its redraws until it is shown."""
        window.stack.setCurrentWidget(window.classification)

    def test_all_groups_hidden_reports_zero(self, window, full_df,
                                            plot_style):
        """get_groups drops hidden groups, which used to read as 'no grouping'."""
        window.data.df = full_df
        window.style.group_columns = ["Group"]
        window.style.groups = [GroupStyle(name="A", visible=False),
                               GroupStyle(name="B", visible=False)]
        window.classification.show_diagram("tas_volcanic", "volcanic")
        text = strip_html(window.classification.count_label.text())
        assert "0 plotted" in text and "hidden" in text

    def test_missing_columns_are_not_counted_as_plotted(self, window):
        """A TAS without Na2O/K2O plots nothing; it must say so."""
        window.data.df = pd.DataFrame({
            "Sample_Name": [f"S{i}" for i in range(4)],
            "SiO2": [45.0, 55.0, 65.0, 70.0]})
        window.classification.show_diagram("tas_volcanic", "volcanic")
        text = strip_html(window.classification.count_label.text())
        assert "missing data" in text and "0 plotted" in text

    def test_names_behind_each_number(self, window):
        window.data.df = pd.DataFrame({
            "Sample_Name": ["good", "blank"],
            "SiO2": [50.0, np.nan], "Na2O": [3.0, 3.0], "K2O": [1.0, 1.0]})
        window.classification.show_diagram("tas_volcanic", "volcanic")
        report = window.classification.count_label._report
        assert report.names_for("plotted") == ["good"]
        assert report.names_for("missing") == ["blank"]

    def test_label_clears_when_the_canvas_empties(self, window, full_df):
        window.data.df = full_df
        window.classification.show_diagram("tas_volcanic", "volcanic")
        assert window.classification.count_label.text()
        window.classification._diagram_key = ""
        window.classification.update_plot()
        assert window.classification.count_label.text() == ""


class TestNormIntegration:
    def test_norm_columns_become_plottable(self, window, majors_df):
        """Auto-fill is pointless if the pickers never re-read the columns."""
        window.data.df = majors_df
        window.on_dataset_replaced()
        window.norm.show_view()
        window.norm.compute()
        combo = window.bivariate._individual.x_combo
        options = {combo.itemText(i) for i in range(combo.count())}
        assert "norm_Q" in options and "norm_An" in options


class TestDataTableEditing:
    def test_undo_restores_a_deleted_column(self, window, majors_df):
        window.data.df = majors_df
        window.on_dataset_replaced()
        table = window.data_table
        table._snapshot("drop TiO2")
        window.data.df = window.data.df.drop(columns=["TiO2"])
        table.refresh_from_data()
        assert "TiO2" not in window.data.df.columns
        table.undo()
        assert "TiO2" in window.data.df.columns

    def test_editing_a_flagged_cell_clears_the_flag(self, window,
                                                    censored_df):
        conv, mask, report = scan_and_convert(censored_df, "half")
        window.data.df = conv
        window.data.bdl_masks = {"main": mask}
        window.data.bdl_limits = {"main": report.limits}
        window.on_dataset_replaced()
        table = window.data_table
        col = list(window.data.df.columns).index("Nb")
        assert bool(window.data.bdl_masks["main"].iloc[0]["Nb"])
        table.model.setData(table.model.index(0, col), "0.44")
        assert not bool(window.data.bdl_masks["main"].iloc[0]["Nb"])
        table.undo()
        assert bool(window.data.bdl_masks["main"].iloc[0]["Nb"])

    def test_grid_opens_in_file_order(self, window):
        """setSortingEnabled used to show the table upside-down."""
        window.data.df = pd.DataFrame({"Sample_Name": ["A", "B", "C", "D"],
                                       "SiO2": [50.0, 55.0, 60.0, 65.0]})
        window.on_dataset_replaced()
        proxy = window.data_table.proxy
        shown = [proxy.data(proxy.index(r, 0)) for r in range(proxy.rowCount())]
        assert shown == ["A", "B", "C", "D"]


class TestShortcuts:
    def test_no_ambiguous_shortcuts(self, window):
        """Two actions sharing a sequence makes Qt fire neither."""
        from PySide6.QtGui import QAction
        seen: dict[str, list[str]] = {}
        for action in window.findChildren(QAction):
            key = action.shortcut().toString()
            if key:
                seen.setdefault(key, []).append(action.text())
        clashes = {k: v for k, v in seen.items() if len(v) > 1}
        assert not clashes, f"ambiguous shortcuts: {clashes}"
