"""Splitting the Statistics dashboard by the user's own grouping.

The per-sample tables are computed positionally, so without these the
rows come back labelled 0..n and a reader cannot tell which row is which
rock.  The plots and the correlation matrix gain the same split, using
the grouping already set in Edit plot so the colours agree with the
diagrams.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.plot_style import GroupStyle
from birds.views.statistics import (
    GROUP_COLUMN,
    group_labels,
    sample_labels,
    with_identity,
)

RARE_EARTHS = ("La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy",
               "Ho", "Er", "Tm", "Yb", "Lu", "Y")


@pytest.fixture
def grouped_df() -> pd.DataFrame:
    rng = np.random.default_rng(11)
    n = 12
    return pd.DataFrame({
        "Sample_Name": [f"S{i}" for i in range(n)],
        "Sample_Label": [f"R-{i:02d}" for i in range(n)],
        "Group": ["mafic"] * 4 + ["interm"] * 4 + ["felsic"] * 4,
        **{el: np.abs(rng.normal(20, 5, n)) + 1
           for el in RARE_EARTHS + ("SiO2", "TiO2", "MgO", "Nb", "Ta",
                                    "Th", "Zr", "Hf", "Ti")},
    })


@pytest.fixture
def window(qapp, grouped_df):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = grouped_df
    w.style.group_columns = ["Group"]
    w.style.groups = [GroupStyle(name=n)
                      for n in ("mafic", "interm", "felsic")]
    w.statistics.refresh()
    return w


def headers(table) -> list:
    return [table.horizontalHeaderItem(c).text()
            for c in range(table.columnCount())]


def column(table, index: int) -> list:
    return [table.item(r, index).text() for r in range(table.rowCount())]


class TestIdentityHelpers:
    def test_sample_label_wins_over_sample_name(self, grouped_df):
        assert sample_labels(grouped_df).iloc[0] == "R-00"

    def test_falls_back_to_sample_name(self, grouped_df):
        labels = sample_labels(grouped_df.drop(columns=["Sample_Label"]))
        assert labels.iloc[0] == "S0"

    def test_blank_labels_fall_back_to_the_index(self, grouped_df):
        df = grouped_df.copy()
        df.loc[0, "Sample_Label"] = "   "
        assert sample_labels(df).iloc[0] == "0"

    def test_no_identifying_column_at_all(self):
        df = pd.DataFrame({"SiO2": [50.0, 60.0]})
        assert list(sample_labels(df)) == ["0", "1"]

    def test_group_labels_need_a_configured_grouping(self, grouped_df,
                                                     plot_style):
        empty = type(plot_style)()
        assert group_labels(grouped_df, empty) is None

    def test_group_labels_combine_multiple_columns(self, grouped_df):
        from birds.plot_style import PlotStyle
        df = grouped_df.assign(Suite=["A"] * 6 + ["B"] * 6)
        style = PlotStyle()
        style.group_columns = ["Group", "Suite"]
        assert group_labels(df, style).iloc[0] == "mafic | A"


class TestWithIdentity:
    def test_label_column_is_prepended(self, grouped_df):
        frame = pd.DataFrame({"Eu/Eu*": np.ones(len(grouped_df))},
                             index=grouped_df.index)
        out = with_identity(frame, grouped_df)
        assert list(out.columns)[0] == "Sample_Label"
        assert out["Sample_Label"].iloc[0] == "R-00"

    def test_split_sorts_rows_into_group_blocks(self, grouped_df,
                                                 plot_style):
        from birds.plot_style import PlotStyle
        style = PlotStyle()
        style.group_columns = ["Group"]
        frame = pd.DataFrame({"Eu/Eu*": np.arange(len(grouped_df))},
                             index=grouped_df.index)
        out = with_identity(frame, grouped_df, style, split_by_group=True)
        assert list(out.columns)[:2] == [GROUP_COLUMN, "Sample_Label"]
        groups = out[GROUP_COLUMN].tolist()
        assert groups == sorted(groups), "rows are not grouped together"

    def test_values_travel_with_their_row(self, grouped_df):
        """Sorting must not shear the data away from its label."""
        from birds.plot_style import PlotStyle
        style = PlotStyle()
        style.group_columns = ["Group"]
        frame = pd.DataFrame({"v": np.arange(len(grouped_df))},
                             index=grouped_df.index)
        out = with_identity(frame, grouped_df, style, split_by_group=True)
        for label, value in zip(out["Sample_Label"], out["v"]):
            assert label == f"R-{int(value):02d}"

    def test_empty_frame_is_returned_untouched(self, grouped_df):
        empty = pd.DataFrame()
        assert with_identity(empty, grouped_df).empty


class TestAnomaliesTable:
    def test_sample_label_shown_by_default(self, window):
        table = window.statistics.anomalies_table
        assert headers(table)[0] == "Sample_Label"
        assert column(table, 0)[0] == "R-00"

    def test_split_adds_the_group_column(self, window):
        window.statistics.anomalies_split_chk.setChecked(True)
        table = window.statistics.anomalies_table
        assert headers(table)[:2] == [GROUP_COLUMN, "Sample_Label"]
        groups = column(table, 0)
        assert groups == sorted(groups)

    def test_ratios_table_follows_the_same_switch(self, window):
        window.statistics.anomalies_split_chk.setChecked(True)
        assert headers(window.statistics.ratios_table)[:2] == \
            [GROUP_COLUMN, "Sample_Label"]

    def test_text_columns_do_not_break_the_anomaly_colouring(self, window):
        """float() on a sample label used to raise here."""
        window.statistics.anomalies_split_chk.setChecked(True)
        window.statistics.anomalies_split_chk.setChecked(False)
        assert window.statistics.anomalies_table.rowCount() > 0

    def test_split_disabled_without_a_grouping(self, qapp, grouped_df):
        from birds.main_window import BirdsMainWindow
        w = BirdsMainWindow()
        w.data.df = grouped_df
        w.style.group_columns = []
        w.statistics.refresh()
        assert not w.statistics.anomalies_split_chk.isEnabled()


class TestTectonicTable:
    def test_labels_and_split(self, window):
        stats = window.statistics
        stats._set_tect_tree_state(True)
        stats._update_tectonic()
        if stats._tectonic.empty:
            pytest.skip("no discriminator could be computed on this fixture")
        assert headers(stats.tectonic_table)[0] == "Sample_Label"
        stats.tect_split_chk.setChecked(True)
        assert headers(stats.tectonic_table)[:2] == \
            [GROUP_COLUMN, "Sample_Label"]

    def test_caption_lands_on_its_own_tab(self, window):
        """This used to retitle the correlation tab instead."""
        stats = window.statistics
        stats._set_tect_tree_state(True)
        stats._update_tectonic()
        titles = [stats.tabs.tabText(i) for i in range(stats.tabs.count())]
        tectonic = stats.tabs.indexOf(stats._tab_pages["tectonic"])
        correlation = stats.tabs.indexOf(stats._tab_pages["correlation"])
        assert titles[tectonic].startswith("Tectonic discrimination")
        assert titles[correlation].startswith("Correlation")


class TestCorrelationSplit:
    def test_selector_lists_pooled_facet_and_each_group(self, window):
        combo = window.statistics.corr_group_combo
        entries = [combo.itemData(i) for i in range(combo.count())]
        assert entries[0] == window.statistics._CORR_ALL
        assert window.statistics._CORR_FACET in entries
        for name in ("mafic", "interm", "felsic"):
            assert name in entries

    def test_facet_draws_one_panel_per_group(self, window):
        stats = window.statistics
        combo = stats.corr_group_combo
        combo.setCurrentIndex(combo.findData(stats._CORR_FACET))
        assert len(stats._correlations) == 3

    def test_single_group_uses_only_those_rows(self, window, grouped_df):
        stats = window.statistics
        combo = stats.corr_group_combo
        combo.setCurrentIndex(combo.findData("mafic"))
        assert len(stats._correlations) == 1
        # A 4-sample subset still produces a matrix over the same columns.
        assert not stats._correlations[0][1].empty

    def test_selector_holds_only_the_pooled_entry_without_grouping(
            self, qapp, grouped_df):
        from birds.main_window import BirdsMainWindow
        w = BirdsMainWindow()
        w.data.df = grouped_df
        w.style.group_columns = []
        w.statistics.refresh()
        assert w.statistics.corr_group_combo.count() == 1


class TestCorrelationLabels:
    """A matrix without element names cannot be read, so they always show."""

    @pytest.fixture
    def wide_window(self, qapp):
        """A realistic dataset: 34 numeric columns, as a full analysis."""
        from birds.main_window import BirdsMainWindow
        rng = np.random.default_rng(3)
        n = 15
        columns = [
            "SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO", "MnO", "MgO", "CaO",
            "Na2O", "K2O", "P2O5", "La", "Ce", "Pr", "Nd", "Sm", "Eu",
            "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Rb", "Ba",
            "Th", "U", "Nb", "Ta", "Sr", "Zr", "Hf",
        ]
        w = BirdsMainWindow()
        w.data.df = pd.DataFrame({
            "Sample_Name": [f"S{i}" for i in range(n)],
            "Group": ["A"] * 5 + ["B"] * 5 + ["C"] * 5,
            **{c: np.abs(rng.normal(20, 5, n)) + 1 for c in columns},
        })
        w.style.group_columns = ["Group"]
        w.style.groups = [GroupStyle(name=g) for g in ("A", "B", "C")]
        w.statistics.refresh()
        return w

    def test_labels_present_on_a_wide_matrix(self, wide_window):
        ax = wide_window.statistics.correlation_canvas.figure.axes[0]
        names = [t.get_text() for t in ax.get_xticklabels()]
        assert len(names) == len(wide_window.statistics._correlation.columns)
        assert "SiO2" in names and "Yb" in names

    def test_both_axes_are_labelled(self, wide_window):
        ax = wide_window.statistics.correlation_canvas.figure.axes[0]
        assert [t.get_text() for t in ax.get_xticklabels()] == \
            [t.get_text() for t in ax.get_yticklabels()]

    def test_labels_fit_inside_the_canvas(self, wide_window):
        fig = wide_window.statistics.correlation_canvas.figure
        fig.canvas.draw()
        renderer = fig.canvas.get_renderer()
        ax = fig.axes[0]
        bottom = min(t.get_window_extent(renderer).y0
                     for t in ax.get_xticklabels())
        left = min(t.get_window_extent(renderer).x0
                   for t in ax.get_yticklabels())
        assert bottom >= 0, "x labels are clipped off the figure"
        assert left >= 0, "y labels are clipped off the figure"

    def test_labels_survive_the_facet_view(self, wide_window):
        stats = wide_window.statistics
        combo = stats.corr_group_combo
        combo.setCurrentIndex(combo.findData(stats._CORR_FACET))
        for ax in stats.correlation_canvas.figure.axes:
            if ax.get_label() == "<colorbar>":
                continue
            if ax.images:
                assert len(ax.get_xticklabels()) > 0

    @pytest.mark.parametrize("n_elements,n_panels", [
        (5, 1), (12, 1), (34, 1), (60, 1), (34, 3), (60, 4),
    ])
    def test_font_size_stays_within_legible_bounds(self, n_elements,
                                                    n_panels):
        from birds.views.statistics import _tick_font_size
        size = _tick_font_size(n_elements, n_panels)
        assert 3.5 <= size <= 9.0

    def test_font_shrinks_as_the_matrix_grows(self):
        from birds.views.statistics import _tick_font_size
        assert _tick_font_size(12) > _tick_font_size(34) >= _tick_font_size(60)


class TestPlotsSplit:
    @pytest.mark.parametrize("kind", ["histogram", "ecdf", "qq"])
    def test_facet_draws_one_panel_per_group(self, window, kind):
        stats = window.statistics
        stats._plot_type_combo.setCurrentIndex(
            stats._plot_type_combo.findData(kind))
        combo = stats._plots_split_combo
        combo.setCurrentIndex(combo.findData("facet"))
        titles = [ax.get_title() for ax in stats._plots_canvas.figure.axes
                  if ax.get_title()]
        assert len(titles) == 3
        for name in ("mafic", "interm", "felsic"):
            assert any(name in t for t in titles)

    @pytest.mark.parametrize("kind", ["histogram", "ecdf", "qq"])
    def test_overlay_uses_a_single_axis(self, window, kind):
        stats = window.statistics
        stats._plot_type_combo.setCurrentIndex(
            stats._plot_type_combo.findData(kind))
        combo = stats._plots_split_combo
        combo.setCurrentIndex(combo.findData("overlay"))
        primary = [ax for ax in stats._plots_canvas.figure.axes
                   if ax.get_ylabel() != "Density (KDE)"]
        assert len(primary) == 1

    @pytest.mark.parametrize("kind", ["box", "violin", "bar", "pie"])
    def test_control_hidden_where_a_category_axis_already_exists(
            self, window, kind):
        stats = window.statistics
        stats._plot_type_combo.setCurrentIndex(
            stats._plot_type_combo.findData(kind))
        assert not stats._plots_split_lbl.isVisible()

    def test_no_split_matches_the_previous_behaviour(self, window):
        stats = window.statistics
        stats._plot_type_combo.setCurrentIndex(
            stats._plot_type_combo.findData("ecdf"))
        combo = stats._plots_split_combo
        combo.setCurrentIndex(combo.findData("none"))
        axes = stats._plots_canvas.figure.axes
        assert len(axes) == 1
        assert axes[0].get_title().startswith("ECDF")


class TestSessionPersistence:
    def test_split_choices_survive_serialisation(self, window):
        stats = window.statistics
        stats.anomalies_split_chk.setChecked(True)
        combo = stats._plots_split_combo
        combo.setCurrentIndex(combo.findData("facet"))
        state = stats.serialize()
        assert state["anomalies_split"] is True
        assert state["plots_split"] == "facet"

        stats.anomalies_split_chk.setChecked(False)
        combo.setCurrentIndex(combo.findData("none"))
        stats.restore(state)
        assert stats.anomalies_split_chk.isChecked()
        assert stats._split_mode() == "facet"
