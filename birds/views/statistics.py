"""Statistics and Anomalies dashboard — 5 tabs + heatmap."""

from __future__ import annotations

from typing import List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..stats_engine import (
    available_normalisers,
    compute_anomalies_extended,
    compute_correlation_matrix,
    compute_descriptive_by_group,
    compute_descriptive_full,
    compute_paper_table,
    compute_ratios,
    paper_table_to_latex,
    paper_table_to_markdown,
)
from ..tectonic_results import (
    compute_results as compute_tectonic_results,
    discriminator_catalog,
)
from .plot_canvas import PlotCanvas


# ---------------------------------------------------------------------------
# Colour codes used by the anomalies table (kept as module-level constants
# so the legend swatch below the table can stay in sync with the code that
# paints the cells).
# ---------------------------------------------------------------------------

POSITIVE_COLOR = QColor(244, 191, 191)   # soft red
NEGATIVE_COLOR = QColor(191, 215, 244)   # soft blue


def _hex(c: QColor) -> str:
    return c.name()


def _anomaly_color(name: str, value: float) -> Optional[QColor]:
    """Soft red for positive anomalies, soft blue for negative.

    Thresholds:
      * REE / Nb / Ta / Ti anomalies (``X/X*``): >1.05 positive, <0.95 negative
      * Y/Ho ratio (chondritic ≈ 28): >32 positive, <24 negative
    """
    if pd.isna(value):
        return None
    if name.endswith("*"):
        if value > 1.05:
            return POSITIVE_COLOR
        if value < 0.95:
            return NEGATIVE_COLOR
    elif name == "Y/Ho":
        if value > 32:
            return POSITIVE_COLOR
        if value < 24:
            return NEGATIVE_COLOR
    return None


# ---------------------------------------------------------------------------
# Element categorisation used by the correlation-matrix selector
# ---------------------------------------------------------------------------

MAJOR_OXIDES_SET = frozenset({
    "SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO", "FeOt", "MnO", "MgO",
    "CaO", "Na2O", "K2O", "P2O5", "Cr2O3", "NiO",
})

REE_SET = frozenset({
    "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb",
    "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Y",
})

TRACE_SET = frozenset({
    "Li", "Be", "Sc", "V", "Cr", "Co", "Ni", "Cu", "Zn", "Ga",
    "Rb", "Sr", "Zr", "Nb", "Mo", "Sn", "Sb", "Cs", "Ba", "Hf",
    "Ta", "W", "Tl", "Pb", "Bi", "Th", "U",
})


def _categorise(column: str) -> str:
    """Return the category bucket a column name belongs to."""
    if column in MAJOR_OXIDES_SET:
        return "Major oxides"
    if column in REE_SET:
        return "Rare-earth elements"
    if column in TRACE_SET:
        return "Trace elements"
    return "Other numeric columns"


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------

class StatisticsView(QWidget):
    """Five-tab dashboard: Descriptive / By group / Anomalies / Ratios /
    Correlation."""

    def __init__(self, data_manager, plot_style, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style

        self._descriptive = pd.DataFrame()
        self._by_group = pd.DataFrame()
        self._anomalies = pd.DataFrame()
        self._ratios = pd.DataFrame()
        self._correlation = pd.DataFrame()
        self._tectonic = pd.DataFrame()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        title = QLabel("Statistics and Anomalies")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        layout.addWidget(title)
        # Long description condensed to one paragraph; details appear on
        # hover so the header doesn't push the tabs down.
        subtitle_tooltip = (
            "Descriptive statistics, REE anomalies (Eu/Eu*, Ce/Ce*, "
            "Pr/Pr*, Gd/Gd*, Dy/Dy*, Y/Y*, Y/Ho), HFSE anomalies "
            "(Nb/Nb*, Ta/Ta*, Ti/Ti* — Pearce 2008; Nb/Nb*_V, Ta/Ta*_V "
            "— Verma 2015), normalised REE ratios, trace ratios "
            "(Zr/Hf, Nb/Ta, Dy/Yb, …), per-group summaries and the "
            "correlation matrix of every numeric column."
        )
        subtitle = QLabel(
            "Descriptive stats, REE/HFSE anomalies, trace ratios, "
            "per-group summaries and correlation matrix — "
            "<i>hover ⓘ for the full list of indices.</i>"
        )
        subtitle.setTextFormat(Qt.TextFormat.RichText)
        subtitle.setStyleSheet("color: #5b6478;")
        subtitle.setWordWrap(True)
        subtitle.setToolTip(subtitle_tooltip)
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Toolbar: normalisation selector + refresh button
        toolbar = QHBoxLayout()
        toolbar.setSpacing(6)
        norm_lbl = QLabel("Anomaly reference (chondrite):")
        norm_lbl.setStyleSheet("font-weight: 600;")
        toolbar.addWidget(norm_lbl)
        self.norm_combo = QComboBox()
        for name in available_normalisers():
            self.norm_combo.addItem(name, name)
        self.norm_combo.setCurrentIndex(0)
        self.norm_combo.currentIndexChanged.connect(self.refresh)
        toolbar.addWidget(self.norm_combo, stretch=2)
        toolbar.addStretch(1)
        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.setMinimumHeight(28)
        self.refresh_btn.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 4px 12px; }"
        )
        self.refresh_btn.clicked.connect(self.refresh)
        toolbar.addWidget(self.refresh_btn)
        layout.addLayout(toolbar)

        self.placeholder = QLabel(
            "Load a dataset (Data → Import) and reopen this view to "
            "compute statistics."
        )
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.placeholder.setStyleSheet("color: #6c7388;")
        layout.addWidget(self.placeholder)

        self.tabs = QTabWidget()
        self.tabs.setVisible(False)
        # Tab 1: descriptive
        self.descriptive_table = self._make_table()
        self.tabs.addTab(self.descriptive_table, "Descriptive")
        # Tab 2: by group
        self.by_group_table = self._make_table()
        self.tabs.addTab(self.by_group_table, "By group")
        # Tab 2b: publication-ready mean ± 1σ (n) summary
        self.tabs.addTab(self._build_paper_tab(), "Paper table")
        # Tab 3: anomalies — table + colour legend
        self.tabs.addTab(self._build_anomalies_tab(), "Anomalies & ratios")
        # Tab 4: trace ratios
        self.ratios_table = self._make_table()
        self.tabs.addTab(self.ratios_table, "Trace-element ratios")
        # Tab 5: correlation heatmap — split between element selector and canvas
        self.tabs.addTab(self._build_correlation_tab(), "Correlation matrix")
        # Tab 6: tectonic discrimination — selectable per-sample DFs / ratios
        self.tabs.addTab(self._build_tectonic_tab(), "Tectonic discrimination")
        # Tab 7: statistical plots — histogram, pie, box, violin, bar,
        # ECDF, Q-Q.  Variable selector + group selector on the left,
        # PlotCanvas on the right.
        self.tabs.addTab(self._build_plots_tab(), "Plots")
        layout.addWidget(self.tabs, stretch=1)

    # ----------------------------------------------------------- tab builders
    def _build_paper_tab(self) -> QWidget:
        """Publication-ready ``mean ± 1σ (n)`` table.

        Variable picker on the left, formatted table on the right, plus
        Copy / Save buttons that emit the table as tab-separated text
        (Word / Excel), Markdown or LaTeX booktabs.
        """
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(6)

        hint = QLabel(
            "Group means with 1σ, rounded so the uncertainty carries two "
            "significant figures — the convention journals expect.  "
            "Columns follow your group order from <b>Data → Edit plot</b>; "
            "cells read <i>n.d.</i> when nothing was measured, and carry "
            "an explicit <i>(n=…)</i> when that variable has fewer "
            "analyses than the group."
        )
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #5b6478;")
        wl.addWidget(hint)

        split = QSplitter(Qt.Orientation.Horizontal)

        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 6, 0)
        ll.setSpacing(4)
        ll.addWidget(QLabel("<b>Variables to include</b>"))
        self.paper_tree = QTreeWidget()
        self.paper_tree.setHeaderHidden(True)
        self.paper_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection)
        self.paper_tree.itemChanged.connect(self._update_paper_table)
        ll.addWidget(self.paper_tree, stretch=1)
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        all_btn = QPushButton("All")
        all_btn.clicked.connect(lambda: self._set_paper_checks(True))
        none_btn = QPushButton("None")
        none_btn.clicked.connect(lambda: self._set_paper_checks(False))
        majors_btn = QPushButton("Majors")
        majors_btn.setToolTip("Tick only the major-element oxides.")
        majors_btn.clicked.connect(self._check_paper_majors)
        for b in (all_btn, none_btn, majors_btn):
            b.setMaximumHeight(24)
            btn_row.addWidget(b)
        ll.addLayout(btn_row)
        split.addWidget(left)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 0, 0, 0)
        rl.setSpacing(4)
        self.paper_table = self._make_table()
        rl.addWidget(self.paper_table, stretch=1)

        export_row = QHBoxLayout()
        export_row.setSpacing(6)
        export_row.addWidget(QLabel("Copy / save as:"))
        self.paper_fmt_combo = QComboBox()
        self.paper_fmt_combo.addItem("Tab-separated (Word / Excel)", "tsv")
        self.paper_fmt_combo.addItem("Markdown", "md")
        self.paper_fmt_combo.addItem("LaTeX (booktabs)", "tex")
        export_row.addWidget(self.paper_fmt_combo, stretch=1)
        copy_btn = QPushButton("⧉ Copy to clipboard")
        copy_btn.clicked.connect(self._copy_paper_table)
        export_row.addWidget(copy_btn)
        save_btn = QPushButton("Save as file…")
        save_btn.clicked.connect(self._save_paper_table)
        export_row.addWidget(save_btn)
        rl.addLayout(export_row)
        split.addWidget(right)

        split.setSizes([220, 780])
        wl.addWidget(split, stretch=1)
        return wrap

    # ------------------------------------------------- paper-table helpers
    _MAJOR_OXIDES = ("SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO", "FeOt",
                     "MnO", "MgO", "CaO", "Na2O", "K2O", "P2O5", "LOI")

    def _populate_paper_tree(self, df: pd.DataFrame) -> None:
        """Fill the variable picker, preserving previous ticks."""
        previous = self._paper_checked_variables()
        first_run = self.paper_tree.topLevelItemCount() == 0
        self.paper_tree.blockSignals(True)
        self.paper_tree.clear()
        numeric = list(df.select_dtypes(include="number").columns)
        majors = [c for c in numeric if c in self._MAJOR_OXIDES]
        traces = [c for c in numeric if c not in self._MAJOR_OXIDES]
        for header, names in (("Major elements", majors),
                              ("Trace elements & others", traces)):
            if not names:
                continue
            parent = QTreeWidgetItem(self.paper_tree, [header])
            parent.setFlags(Qt.ItemFlag.ItemIsEnabled)
            font = parent.font(0)
            font.setBold(True)
            parent.setFont(0, font)
            for name in names:
                item = QTreeWidgetItem(parent, [str(name)])
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable
                              | Qt.ItemFlag.ItemIsEnabled)
                # First open: tick majors only — a full 60-column table
                # is unreadable and nobody publishes one.
                want = (str(name) in previous if not first_run
                        else name in majors)
                item.setCheckState(0, Qt.CheckState.Checked if want
                                   else Qt.CheckState.Unchecked)
            parent.setExpanded(True)
        self.paper_tree.blockSignals(False)

    def _iter_paper_items(self):
        for i in range(self.paper_tree.topLevelItemCount()):
            parent = self.paper_tree.topLevelItem(i)
            for j in range(parent.childCount()):
                yield parent.child(j)

    def _paper_checked_variables(self) -> List[str]:
        return [it.text(0) for it in self._iter_paper_items()
                if it.checkState(0) == Qt.CheckState.Checked]

    def _set_paper_checks(self, checked: bool) -> None:
        self.paper_tree.blockSignals(True)
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for it in self._iter_paper_items():
            it.setCheckState(0, state)
        self.paper_tree.blockSignals(False)
        self._update_paper_table()

    def _check_paper_majors(self) -> None:
        self.paper_tree.blockSignals(True)
        for it in self._iter_paper_items():
            want = it.text(0) in self._MAJOR_OXIDES
            it.setCheckState(0, Qt.CheckState.Checked if want
                             else Qt.CheckState.Unchecked)
        self.paper_tree.blockSignals(False)
        self._update_paper_table()

    def _update_paper_table(self, *_args) -> None:
        df = self.data.df
        if df is None or df.empty:
            self._paper = pd.DataFrame()
            self._fill_table(self.paper_table, self._paper)
            return
        group_cols = getattr(self.plot_style, "group_columns", []) or []
        order = [g.name for g in getattr(self.plot_style, "groups", [])
                 if getattr(g, "name", None)]
        self._paper = compute_paper_table(
            df,
            group_columns=group_cols,
            variables=self._paper_checked_variables() or None,
            group_order=order or None,
        )
        self._fill_table(self.paper_table, self._paper)

    def _paper_text(self) -> str:
        table = getattr(self, "_paper", None)
        if table is None or table.empty:
            return ""
        fmt = self.paper_fmt_combo.currentData()
        if fmt == "md":
            return paper_table_to_markdown(table)
        if fmt == "tex":
            return paper_table_to_latex(table)
        return table.to_csv(sep="\t")

    def _copy_paper_table(self) -> None:
        from PySide6.QtWidgets import QApplication, QMessageBox
        text = self._paper_text()
        if not text:
            QMessageBox.information(
                self, "Paper table",
                "Nothing to copy — tick at least one variable.")
            return
        QApplication.clipboard().setText(text)
        label = self.paper_fmt_combo.currentText()
        QMessageBox.information(
            self, "Paper table",
            f"Table copied to the clipboard as {label}.")

    def _save_paper_table(self) -> None:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        text = self._paper_text()
        if not text:
            QMessageBox.information(
                self, "Paper table",
                "Nothing to save — tick at least one variable.")
            return
        fmt = self.paper_fmt_combo.currentData()
        ext, filt = {
            "md":  (".md",  "Markdown (*.md)"),
            "tex": (".tex", "LaTeX (*.tex)"),
        }.get(fmt, (".txt", "Tab-separated text (*.txt *.tsv)"))
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save paper table", f"geochem_table{ext}", filt)
        if not path_str:
            return
        from pathlib import Path
        path = Path(path_str)
        if not path.suffix:
            path = path.with_suffix(ext)
        try:
            path.write_text(text, encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Save paper table", str(exc))
            return
        QMessageBox.information(self, "Paper table",
                                f"Saved to {path.name}.")

    def _build_anomalies_tab(self) -> QWidget:
        """Anomalies table + a colour legend explaining the cell shading."""
        wrap = QWidget()
        wl = QVBoxLayout(wrap)
        wl.setContentsMargins(0, 0, 0, 0)
        wl.setSpacing(4)

        self.anomalies_table = self._make_table()
        wl.addWidget(self.anomalies_table, stretch=1)

        # Colour legend — kept in sync with `_anomaly_color()` thresholds.
        legend = QFrame()
        legend.setFrameShape(QFrame.Shape.StyledPanel)
        legend.setStyleSheet(
            "QFrame { background: #f4f6fa; border: 1px solid #d4d8e1; "
            "border-radius: 4px; padding: 6px; }"
        )
        ll = QHBoxLayout(legend)
        ll.setContentsMargins(6, 4, 6, 4)
        ll.setSpacing(14)
        title = QLabel("<b>Colour key:</b>")
        title.setStyleSheet("background: transparent; border: none;")
        ll.addWidget(title)
        ll.addWidget(self._swatch_row(
            POSITIVE_COLOR,
            "Positive anomaly — value > 1.05 (X/X*) or > 32 (Y/Ho)"))
        ll.addWidget(self._swatch_row(
            NEGATIVE_COLOR,
            "Negative anomaly — value < 0.95 (X/X*) or < 24 (Y/Ho)"))
        ll.addWidget(self._swatch_row(
            QColor(255, 255, 255),
            "No significant anomaly (≈ chondritic / PM)",
            border="#bcc1cc"))
        ll.addStretch(1)
        wl.addWidget(legend)
        return wrap

    def _build_correlation_tab(self) -> QWidget:
        """Correlation matrix tab: element-selector + heatmap canvas + toolbar."""
        wrap = QSplitter(Qt.Orientation.Horizontal)

        # Left side — element-selector tree
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(6, 6, 6, 6)
        ll.setSpacing(6)
        intro = QLabel(
            "Tick the elements / columns to include in the matrix. "
            "Use the category checkboxes to toggle groups at once."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #6c7388; font-size: 11px;")
        ll.addWidget(intro)

        self.corr_tree = QTreeWidget()
        self.corr_tree.setHeaderHidden(True)
        self.corr_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection)
        ll.addWidget(self.corr_tree, stretch=1)

        btn_row = QHBoxLayout()
        select_all = QPushButton("Select all")
        select_all.clicked.connect(lambda: self._set_corr_tree_state(True))
        btn_row.addWidget(select_all)
        select_none = QPushButton("Clear")
        select_none.clicked.connect(lambda: self._set_corr_tree_state(False))
        btn_row.addWidget(select_none)
        ll.addLayout(btn_row)

        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Method:"))
        self.corr_method_combo = QComboBox()
        for label, key in (("Pearson (linear)", "pearson"),
                           ("Spearman (rank)", "spearman"),
                           ("Kendall (rank)", "kendall")):
            self.corr_method_combo.addItem(label, key)
        method_row.addWidget(self.corr_method_combo, stretch=1)
        ll.addLayout(method_row)

        update_corr = QPushButton("Update matrix")
        update_corr.clicked.connect(self._update_correlation)
        ll.addWidget(update_corr)

        wrap.addWidget(left)

        # Right side — heatmap canvas
        self.correlation_canvas = PlotCanvas()
        wrap.addWidget(self.correlation_canvas)
        wrap.setSizes([280, 720])
        return wrap

    @staticmethod
    def _swatch_row(color: QColor, text: str,
                    border: str = "#888") -> QWidget:
        """A coloured square + a short description, used by the legend."""
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        swatch = QLabel()
        swatch.setFixedSize(18, 14)
        swatch.setStyleSheet(
            f"background: {_hex(color)}; border: 1px solid {border};"
            " border-radius: 2px;"
        )
        row_layout.addWidget(swatch)
        label = QLabel(text)
        label.setStyleSheet("background: transparent; border: none;"
                            " color: #1c2237;")
        row_layout.addWidget(label)
        return row

    # ------------------------------------------------------------ tectonic
    def _build_tectonic_tab(self) -> QWidget:
        """Tectonic-discrimination tab: selector tree on the left,
        results table on the right.

        The user ticks which ratios / DFs to evaluate (grouped by
        published family) and clicks *Compute*. The resulting table
        carries one column per selected discriminator and rides along
        with the Save File export.
        """
        wrap = QSplitter(Qt.Orientation.Horizontal)

        # Left — selector tree + buttons
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(6, 6, 6, 6)
        ll.setSpacing(6)
        intro = QLabel(
            "Tick the bivariate ratios and discriminant functions to "
            "compute. Click <b>Compute</b> to populate the table — the "
            "results are bundled into the Save File report alongside the "
            "descriptive statistics."
        )
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.TextFormat.RichText)
        intro.setStyleSheet("color: #6c7388; font-size: 11px;")
        ll.addWidget(intro)

        self.tect_tree = QTreeWidget()
        self.tect_tree.setHeaderHidden(True)
        self.tect_tree.setSelectionMode(
            QAbstractItemView.SelectionMode.NoSelection)
        self._populate_tectonic_tree()
        ll.addWidget(self.tect_tree, stretch=1)

        btn_row = QHBoxLayout()
        all_btn = QPushButton("Select all")
        all_btn.clicked.connect(lambda: self._set_tect_tree_state(True))
        btn_row.addWidget(all_btn)
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(lambda: self._set_tect_tree_state(False))
        btn_row.addWidget(clear_btn)
        ll.addLayout(btn_row)

        compute_btn = QPushButton("Compute selected")
        compute_btn.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 6px; }")
        compute_btn.clicked.connect(self._update_tectonic)
        ll.addWidget(compute_btn)
        wrap.addWidget(left)

        # Right — results table
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(6, 6, 6, 6)
        rl.setSpacing(6)
        self.tect_summary = QLabel(
            "No discriminator computed yet. Tick entries on the left and "
            "click 'Compute selected'."
        )
        self.tect_summary.setStyleSheet("color: #5b6478;")
        self.tect_summary.setWordWrap(True)
        rl.addWidget(self.tect_summary)
        self.tectonic_table = self._make_table()
        rl.addWidget(self.tectonic_table, stretch=1)
        wrap.addWidget(right)
        wrap.setSizes([320, 700])
        return wrap

    def _populate_tectonic_tree(self) -> None:
        """Fill the discriminator selector tree (categories → entries)."""
        self.tect_tree.clear()
        for category, items in discriminator_catalog().items():
            parent = QTreeWidgetItem(self.tect_tree,
                                      [f"{category}  ({len(items)})"])
            parent.setFlags(parent.flags()
                            | Qt.ItemFlag.ItemIsAutoTristate
                            | Qt.ItemFlag.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.CheckState.Unchecked)
            font = parent.font(0)
            font.setBold(True)
            parent.setFont(0, font)
            for disc in items:
                child = QTreeWidgetItem(parent, [disc.label])
                child.setFlags(child.flags()
                               | Qt.ItemFlag.ItemIsUserCheckable)
                child.setData(0, Qt.ItemDataRole.UserRole, disc.key)
                child.setCheckState(0, Qt.CheckState.Unchecked)
        self.tect_tree.expandToDepth(0)

    def _selected_tect_keys(self) -> List[str]:
        out: List[str] = []
        for cat_i in range(self.tect_tree.topLevelItemCount()):
            cat = self.tect_tree.topLevelItem(cat_i)
            for c_i in range(cat.childCount()):
                child = cat.child(c_i)
                if child.checkState(0) == Qt.CheckState.Checked:
                    key = child.data(0, Qt.ItemDataRole.UserRole)
                    if key:
                        out.append(str(key))
        return out

    def _set_tect_tree_state(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for cat_i in range(self.tect_tree.topLevelItemCount()):
            self.tect_tree.topLevelItem(cat_i).setCheckState(0, state)

    def _update_tectonic(self) -> None:
        df = self.data.df
        if df is None or df.empty:
            self.tect_summary.setText(
                "Load a dataset (Data → Import) before computing.")
            self._tectonic = pd.DataFrame()
            self._fill_table(self.tectonic_table, self._tectonic)
            return
        keys = self._selected_tect_keys()
        if not keys:
            self.tect_summary.setText(
                "Nothing selected. Tick at least one discriminator first.")
            self._tectonic = pd.DataFrame()
            self._fill_table(self.tectonic_table, self._tectonic)
            return
        self._tectonic = compute_tectonic_results(df, keys)
        self._fill_table(self.tectonic_table, self._tectonic)
        n = self._tectonic.shape[1]
        skipped = len(keys) - n
        msg = (f"{n} discriminator{'s' if n != 1 else ''} computed for "
               f"{len(df)} sample{'s' if len(df) != 1 else ''}.")
        if skipped:
            msg += f"  •  {skipped} skipped (missing input columns)."
        self.tect_summary.setText(msg)
        # Tab caption reflects the actual matrix size
        self.tabs.setTabText(5,
            f"Tectonic discrimination ({n})")

    # ------------------------------------------------------------------ API
    @property
    def descriptive_frame(self) -> pd.DataFrame:
        return self._descriptive

    @property
    def by_group_frame(self) -> pd.DataFrame:
        return self._by_group

    @property
    def anomalies_frame(self) -> pd.DataFrame:
        return self._anomalies

    @property
    def ratios_frame(self) -> pd.DataFrame:
        return self._ratios

    @property
    def correlation_frame(self) -> pd.DataFrame:
        return self._correlation

    # ------------------------------------------------------------------
    # Plots tab — histogram / pie / box / violin / bar / ECDF / Q-Q
    # ------------------------------------------------------------------
    _PLOT_TYPES = (
        ("histogram", "Histogram (+ KDE)"),
        ("pie",       "Pie chart"),
        ("box",       "Box plot by group"),
        ("violin",    "Violin plot by group"),
        ("bar",       "Bar chart (counts)"),
        ("ecdf",      "Empirical CDF"),
        ("qq",        "Q-Q plot (normality)"),
    )

    def _build_plots_tab(self) -> QWidget:
        wrap = QSplitter(Qt.Orientation.Horizontal)

        # ---- Left controls -------------------------------------------------
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(8, 8, 8, 8)
        ll.setSpacing(6)

        ll.addWidget(QLabel("<b>Plot type</b>"))
        self._plot_type_combo = QComboBox()
        for key, label in self._PLOT_TYPES:
            self._plot_type_combo.addItem(label, key)
        self._plot_type_combo.currentIndexChanged.connect(
            self._on_plot_type_changed)
        ll.addWidget(self._plot_type_combo)

        # Numeric variable (histogram, box, violin, ECDF, Q-Q)
        self._plots_var_lbl = QLabel("<b>Variable</b>")
        ll.addWidget(self._plots_var_lbl)
        self._plots_var_combo = QComboBox()
        self._plots_var_combo.currentIndexChanged.connect(self._render_stat_plot)
        ll.addWidget(self._plots_var_combo)

        # Categorical column (pie, bar, box, violin)
        self._plots_cat_lbl = QLabel("<b>Group by</b>")
        ll.addWidget(self._plots_cat_lbl)
        self._plots_cat_combo = QComboBox()
        self._plots_cat_combo.currentIndexChanged.connect(self._render_stat_plot)
        ll.addWidget(self._plots_cat_combo)

        # Histogram-specific options
        from PySide6.QtWidgets import QCheckBox, QSpinBox
        self._hist_bins_lbl = QLabel("<b>Bins</b>")
        ll.addWidget(self._hist_bins_lbl)
        self._hist_bins = QSpinBox()
        self._hist_bins.setRange(3, 200)
        self._hist_bins.setValue(20)
        self._hist_bins.valueChanged.connect(self._render_stat_plot)
        ll.addWidget(self._hist_bins)
        self._hist_kde = QCheckBox("Overlay KDE curve")
        self._hist_kde.setChecked(True)
        self._hist_kde.toggled.connect(self._render_stat_plot)
        ll.addWidget(self._hist_kde)
        self._hist_log = QCheckBox("Log-transform values (ln)")
        self._hist_log.setChecked(False)
        self._hist_log.setToolTip(
            "Apply natural log before binning.  Useful for trace elements "
            "with a wide dynamic range (Cr, Ni, Pb, U…)."
        )
        self._hist_log.toggled.connect(self._render_stat_plot)
        ll.addWidget(self._hist_log)

        ll.addStretch(1)
        wrap.addWidget(left)

        # ---- Right canvas --------------------------------------------------
        self._plots_canvas = PlotCanvas()
        wrap.addWidget(self._plots_canvas)
        wrap.setSizes([260, 740])

        # Initial state: refresh selectors + hide irrelevant controls.
        self._refresh_plots_selectors()
        self._on_plot_type_changed(0)
        return wrap

    def _refresh_plots_selectors(self) -> None:
        """Refill the variable / group combos from the current df."""
        df = self.data.df
        # Numeric columns for the variable selector
        self._plots_var_combo.blockSignals(True)
        self._plots_cat_combo.blockSignals(True)
        self._plots_var_combo.clear()
        self._plots_cat_combo.clear()
        if df is None or df.empty:
            self._plots_var_combo.blockSignals(False)
            self._plots_cat_combo.blockSignals(False)
            return
        numeric_cols = []
        cat_cols = []
        for col in df.columns:
            series = df[col]
            # Heuristic: try-to-numeric; if it gives at least 4 finite
            # values, treat as numeric — else treat as categorical.
            num = pd.to_numeric(series, errors="coerce")
            if num.notna().sum() >= 4:
                numeric_cols.append(str(col))
            else:
                cat_cols.append(str(col))
        # Strings that look numeric still belong as categories if they
        # have few unique values.  Add columns with <= 30 unique values
        # to the cat list too (useful for Rock_Type, Magmatic_Series…).
        for col in df.columns:
            s = df[col].dropna()
            if str(col) in cat_cols:
                continue
            if s.nunique() <= 30 and str(col) not in cat_cols:
                cat_cols.append(str(col))
        for c in numeric_cols:
            self._plots_var_combo.addItem(c, c)
        for c in cat_cols:
            self._plots_cat_combo.addItem(c, c)
        self._plots_var_combo.blockSignals(False)
        self._plots_cat_combo.blockSignals(False)

    def _on_plot_type_changed(self, _index: int) -> None:
        """Show / hide the controls that only apply to certain plot types."""
        kind = self._plot_type_combo.currentData()
        wants_var = kind in ("histogram", "box", "violin", "ecdf", "qq")
        wants_cat = kind in ("pie", "bar", "box", "violin")
        wants_hist = kind == "histogram"
        self._plots_var_lbl.setVisible(wants_var)
        self._plots_var_combo.setVisible(wants_var)
        self._plots_cat_lbl.setVisible(wants_cat)
        self._plots_cat_combo.setVisible(wants_cat)
        for w in (self._hist_bins_lbl, self._hist_bins,
                  self._hist_kde, self._hist_log):
            w.setVisible(wants_hist)
        self._render_stat_plot()

    def _render_stat_plot(self) -> None:
        """Re-draw the active plot based on the current selections."""
        canvas = getattr(self, "_plots_canvas", None)
        if canvas is None:
            return
        fig = canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        df = self.data.df
        if df is None or df.empty:
            ax.text(0.5, 0.5,
                    "Load a dataset first (Data → Import).",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            canvas.draw()
            return
        kind = self._plot_type_combo.currentData()
        try:
            if kind == "histogram":
                self._draw_histogram(ax)
            elif kind == "pie":
                self._draw_pie(ax)
            elif kind == "box":
                self._draw_box_or_violin(ax, violin=False)
            elif kind == "violin":
                self._draw_box_or_violin(ax, violin=True)
            elif kind == "bar":
                self._draw_bar(ax)
            elif kind == "ecdf":
                self._draw_ecdf(ax)
            elif kind == "qq":
                self._draw_qq(ax)
        except Exception as exc:  # noqa: BLE001
            ax.text(0.5, 0.5, f"Plot error:\n{exc}",
                    ha="center", va="center", color="#b13a3a",
                    fontsize=10, wrap=True)
            ax.axis("off")
        fig.tight_layout()
        canvas.draw()

    # ------------------------------------------------------------------
    # Stat-plot renderers
    # ------------------------------------------------------------------
    def _numeric_series(self, col: str) -> pd.Series:
        return pd.to_numeric(self.data.df[col], errors="coerce").dropna()

    def _draw_histogram(self, ax) -> None:
        col = self._plots_var_combo.currentData()
        if not col:
            return
        values = self._numeric_series(col)
        if values.empty:
            ax.text(0.5, 0.5, f"No numeric data in '{col}'.",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            return
        if self._hist_log.isChecked():
            values = values[values > 0]
            values = np.log(values)
            x_label = f"ln({col})"
        else:
            x_label = col
        bins = self._hist_bins.value()
        ax.hist(values, bins=bins, color="#0e6cb6", alpha=0.7,
                edgecolor="white", linewidth=0.5, label="Histogram")
        ax.set_xlabel(x_label)
        ax.set_ylabel("Frequency")
        if self._hist_kde.isChecked() and len(values) >= 3:
            try:
                from scipy.stats import gaussian_kde
                kde = gaussian_kde(values)
                xs = np.linspace(values.min(), values.max(), 200)
                density = kde(xs)
                # The KDE goes on its own twin axis, so it carries its
                # own density scale and needs no rescaling to counts.
                ax2 = ax.twinx()
                ax2.plot(xs, density, color="#b13a3a", linewidth=1.6,
                         label="KDE")
                ax2.set_ylabel("Density (KDE)", color="#b13a3a")
                ax2.tick_params(axis="y", colors="#b13a3a")
            except ImportError:
                pass
        n = len(values)
        ax.set_title(f"{col} — n={n}, μ={values.mean():.3g}, "
                     f"σ={values.std(ddof=1):.3g}")
        ax.grid(True, axis="y", alpha=0.3)

    def _draw_pie(self, ax) -> None:
        col = self._plots_cat_combo.currentData()
        if not col:
            return
        series = self.data.df[col].dropna().astype(str)
        counts = series.value_counts()
        if counts.empty:
            ax.text(0.5, 0.5, f"No values in '{col}'.",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            return
        # Lump small slices into "Other" so the pie stays readable.
        if len(counts) > 8:
            top = counts.iloc[:7]
            other = pd.Series({"Other": int(counts.iloc[7:].sum())})
            counts = pd.concat([top, other])
        colors = plt.get_cmap("tab10").colors
        wedges, texts, autotexts = ax.pie(
            counts.values,
            labels=counts.index,
            autopct="%1.1f%%",
            colors=[colors[i % len(colors)] for i in range(len(counts))],
            startangle=90,
            wedgeprops=dict(edgecolor="white", linewidth=1.2),
            textprops=dict(fontsize=10),
        )
        ax.set_title(f"{col} (n={int(counts.sum())})")

    def _draw_box_or_violin(self, ax, *, violin: bool) -> None:
        var = self._plots_var_combo.currentData()
        cat = self._plots_cat_combo.currentData()
        if not var:
            return
        df = self.data.df
        values = pd.to_numeric(df[var], errors="coerce")
        if cat and cat in df.columns:
            groups = df[cat].astype(str)
            data = [values[groups == g].dropna().values
                    for g in groups.dropna().unique()]
            labels = list(groups.dropna().unique())
        else:
            data = [values.dropna().values]
            labels = [var]
        # Drop empty groups so matplotlib doesn't choke.
        keep = [(d, lab) for d, lab in zip(data, labels) if len(d) > 0]
        if not keep:
            ax.text(0.5, 0.5, "No data for the selected variable.",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            return
        data, labels = zip(*keep)
        if violin:
            parts = ax.violinplot(data, showmeans=True, showmedians=True)
            for pc in parts["bodies"]:
                pc.set_facecolor("#0e6cb6"); pc.set_alpha(0.55)
        else:
            ax.boxplot(data, labels=labels, patch_artist=True,
                       boxprops=dict(facecolor="#dceaf6",
                                     edgecolor="#0e6cb6"),
                       medianprops=dict(color="#b13a3a", linewidth=1.4),
                       whiskerprops=dict(color="#0e6cb6"),
                       flierprops=dict(marker="o", markersize=4,
                                       markerfacecolor="#b13a3a",
                                       markeredgecolor="none", alpha=0.7))
        if violin:
            ax.set_xticks(range(1, len(labels) + 1))
            ax.set_xticklabels(labels, rotation=30, ha="right")
        ax.set_ylabel(var)
        ax.set_title(f"{var}" + (f"  by  {cat}" if cat else ""))
        ax.grid(True, axis="y", alpha=0.3)

    def _draw_bar(self, ax) -> None:
        col = self._plots_cat_combo.currentData()
        if not col:
            return
        series = self.data.df[col].dropna().astype(str)
        counts = series.value_counts()
        if counts.empty:
            ax.text(0.5, 0.5, f"No values in '{col}'.",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            return
        colors = plt.get_cmap("tab10").colors
        bars = ax.bar(counts.index, counts.values,
                       color=[colors[i % len(colors)]
                              for i in range(len(counts))],
                       edgecolor="white", linewidth=0.8)
        ax.set_ylabel("Count")
        ax.set_title(f"{col} (n={int(counts.sum())})")
        for bar, v in zip(bars, counts.values):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height(), str(v),
                    ha="center", va="bottom", fontsize=9, color="#1c2237")
        ax.tick_params(axis="x", rotation=30)
        for lbl in ax.get_xticklabels():
            lbl.set_horizontalalignment("right")
        ax.grid(True, axis="y", alpha=0.3)

    def _draw_ecdf(self, ax) -> None:
        col = self._plots_var_combo.currentData()
        if not col:
            return
        values = self._numeric_series(col).sort_values()
        if values.empty:
            ax.text(0.5, 0.5, f"No numeric data in '{col}'.",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            return
        n = len(values)
        y = np.arange(1, n + 1) / n
        ax.step(values, y, where="post", color="#0e6cb6", linewidth=1.6)
        ax.set_xlabel(col)
        ax.set_ylabel("Cumulative fraction")
        ax.set_title(f"ECDF — {col} (n={n})")
        ax.grid(True, alpha=0.3)
        ax.set_ylim(0, 1.02)

    def _draw_qq(self, ax) -> None:
        col = self._plots_var_combo.currentData()
        if not col:
            return
        values = self._numeric_series(col)
        if len(values) < 3:
            ax.text(0.5, 0.5, "Q-Q plot needs at least 3 finite values.",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            return
        try:
            from scipy.stats import probplot
            probplot(values, dist="norm", plot=ax)
            # probplot draws its own labels; tidy them.
            ax.set_title(f"Q-Q plot — {col} (n={len(values)})")
        except ImportError:
            # Manual fallback if scipy is missing.
            sorted_values = np.sort(values.values)
            n = len(sorted_values)
            quantiles = (np.arange(1, n + 1) - 0.5) / n
            try:
                from statistics import NormalDist
                theoretical = [NormalDist().inv_cdf(q) for q in quantiles]
            except Exception:
                # No normal-quantile available → bail with a message
                ax.text(0.5, 0.5, "Need scipy or statistics.NormalDist "
                                  "for Q-Q plot.",
                        ha="center", va="center", color="#6c7388")
                ax.axis("off")
                return
            ax.scatter(theoretical, sorted_values, s=14, color="#0e6cb6",
                       edgecolor="white", linewidth=0.4)
            lo, hi = min(theoretical[0], sorted_values[0]), max(
                theoretical[-1], sorted_values[-1])
            ax.plot([lo, hi], [lo, hi], color="#b13a3a", linewidth=1.0)
            ax.set_xlabel("Theoretical normal quantile")
            ax.set_ylabel("Sample value")
            ax.set_title(f"Q-Q plot — {col} (n={n})")
            ax.grid(True, alpha=0.3)

    @property
    def tectonic_frame(self) -> pd.DataFrame:
        return self._tectonic

    def refresh(self) -> None:
        df = self.data.df
        if df is None or df.empty:
            self.placeholder.setText(
                "Load a dataset (Data → Import) and reopen this view to "
                "compute statistics."
            )
            self.placeholder.setVisible(True)
            self.tabs.setVisible(False)
            return

        norm_name = self.norm_combo.currentData()
        self._descriptive = compute_descriptive_full(df)
        self._by_group = compute_descriptive_by_group(
            df, getattr(self.plot_style, "group_columns", []) or []
        )
        self._anomalies = compute_anomalies_extended(df, norm_name)
        self._ratios = compute_ratios(df)

        self._fill_table(self.descriptive_table, self._descriptive)
        self._fill_table(self.by_group_table, self._by_group)
        self._fill_table(
            self.anomalies_table, self._anomalies, colour_anomalies=True
        )
        self._fill_table(self.ratios_table, self._ratios)

        # Publication-ready table — variable picker then the table itself.
        self._populate_paper_tree(df)
        self._update_paper_table()

        # Repopulate the correlation-tree selector. Default: tick all
        # available numeric columns so the matrix is non-empty on first
        # open. The user can then narrow down via the tree.
        self._populate_corr_tree(df)
        self._update_correlation()

        cols = (
            getattr(self.plot_style, "group_columns", []) or []
        )
        self.tabs.setTabText(0,
            f"Descriptive ({len(self._descriptive)} elements)")
        self.tabs.setTabText(1,
            f"By group ({len(self._by_group)} groups)"
            + (f" – {', '.join(cols)}" if cols else " – set in Edit plot")
        )
        n_paper = max(len(getattr(self, "_paper", pd.DataFrame())) - 1, 0)
        self.tabs.setTabText(2,
            f"Paper table ({n_paper} variables)")
        self.tabs.setTabText(3,
            f"Anomalies & ratios ({len(self._anomalies.columns)} indices)")
        self.tabs.setTabText(4,
            f"Trace ratios ({len(self._ratios.columns)} ratios)")
        self.tabs.setTabText(5,
            f"Correlation ({len(self._correlation.columns)}×{len(self._correlation.columns)})")

        self.placeholder.setVisible(False)
        self.tabs.setVisible(True)
        # Refresh the variable / group lists on the Plots tab so the
        # selectors reflect the current dataset.  Render the active
        # plot too so it doesn't show stale axes after a re-import.
        if hasattr(self, "_plots_var_combo"):
            self._refresh_plots_selectors()
            self._render_stat_plot()

    # -------------------------------------------------------------- helpers
    @staticmethod
    def _make_table() -> QTableWidget:
        t = QTableWidget(0, 0)
        t.setAlternatingRowColors(True)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        return t

    @staticmethod
    def _fill_table(table: QTableWidget, frame: pd.DataFrame,
                    colour_anomalies: bool = False) -> None:
        table.clear()
        if frame is None or frame.empty:
            table.setRowCount(0)
            table.setColumnCount(0)
            return
        # Flatten MultiIndex columns for display
        if isinstance(frame.columns, pd.MultiIndex):
            cols = [" · ".join(str(s) for s in c if str(s) != "") for c in frame.columns]
        else:
            cols = [str(c) for c in frame.columns]
        table.setColumnCount(len(cols))
        table.setRowCount(len(frame.index))
        table.setHorizontalHeaderLabels(cols)
        table.setVerticalHeaderLabels([str(i) for i in frame.index])
        for r in range(len(frame.index)):
            for c in range(len(frame.columns)):
                value = frame.iloc[r, c]
                text = "" if pd.isna(value) else f"{value}"
                item = QTableWidgetItem(text)
                item.setTextAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                if colour_anomalies and not pd.isna(value):
                    colour = _anomaly_color(cols[c], float(value))
                    if colour is not None:
                        item.setBackground(QBrush(colour))
                table.setItem(r, c, item)
        table.resizeColumnsToContents()

    # ----------------------------------------------------------- correlation
    def _populate_corr_tree(self, df: pd.DataFrame) -> None:
        """Repopulate the element-selector tree from the dataset."""
        # Remember the user's previous selection so we don't clobber it on
        # every refresh — only newly-appeared columns default to ticked.
        prev_checked: set[str] = set()
        for cat_i in range(self.corr_tree.topLevelItemCount()):
            cat = self.corr_tree.topLevelItem(cat_i)
            for c_i in range(cat.childCount()):
                child = cat.child(c_i)
                if child.checkState(0) == Qt.CheckState.Checked:
                    prev_checked.add(
                        str(child.data(0, Qt.ItemDataRole.UserRole)))
        first_open = self.corr_tree.topLevelItemCount() == 0

        self.corr_tree.clear()
        numeric = df.select_dtypes(include="number")
        if numeric.empty:
            return

        # Build category buckets in a stable order
        buckets: dict[str, list[str]] = {
            "Major oxides": [],
            "Trace elements": [],
            "Rare-earth elements": [],
            "Other numeric columns": [],
        }
        for col in numeric.columns:
            buckets[_categorise(str(col))].append(str(col))

        for category, names in buckets.items():
            if not names:
                continue
            parent = QTreeWidgetItem(self.corr_tree, [
                f"{category}  ({len(names)})"])
            parent.setFlags(parent.flags()
                            | Qt.ItemFlag.ItemIsAutoTristate
                            | Qt.ItemFlag.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.CheckState.Unchecked)
            font = parent.font(0)
            font.setBold(True)
            parent.setFont(0, font)
            for name in names:
                child = QTreeWidgetItem(parent, [name])
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setData(0, Qt.ItemDataRole.UserRole, name)
                # Tick by default the first time around; on subsequent
                # refreshes preserve the user's previous selection.
                if first_open or name in prev_checked:
                    child.setCheckState(0, Qt.CheckState.Checked)
                else:
                    child.setCheckState(0, Qt.CheckState.Unchecked)
        self.corr_tree.expandAll()

    def _selected_corr_columns(self) -> List[str]:
        out: List[str] = []
        for cat_i in range(self.corr_tree.topLevelItemCount()):
            cat = self.corr_tree.topLevelItem(cat_i)
            for c_i in range(cat.childCount()):
                child = cat.child(c_i)
                if child.checkState(0) == Qt.CheckState.Checked:
                    out.append(str(child.data(0, Qt.ItemDataRole.UserRole)))
        return out

    def _set_corr_tree_state(self, checked: bool) -> None:
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for cat_i in range(self.corr_tree.topLevelItemCount()):
            self.corr_tree.topLevelItem(cat_i).setCheckState(0, state)

    def _update_correlation(self) -> None:
        df = self.data.df
        if df is None or df.empty:
            return
        cols = self._selected_corr_columns()
        method = self.corr_method_combo.currentData() or "pearson"
        self._correlation = compute_correlation_matrix(
            df, columns=cols if cols else None, method=method)
        self._draw_correlation_heatmap()
        # Refresh the tab caption to reflect the actual matrix size
        n = len(self._correlation.columns)
        self.tabs.setTabText(4, f"Correlation ({n}×{n})")

    def _draw_correlation_heatmap(self) -> None:
        fig = self.correlation_canvas.figure
        fig.clear()
        if self._correlation.empty:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5,
                    "Not enough numeric columns to compute correlations.",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            self.correlation_canvas.draw()
            return

        ax = fig.add_subplot(111)
        cols = list(self._correlation.columns)
        n = len(cols)
        im = ax.imshow(self._correlation.values, cmap="RdBu_r",
                       vmin=-1, vmax=1, aspect="auto")
        ax.set_xticks(range(n))
        ax.set_xticklabels(cols, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(n))
        ax.set_yticklabels(cols, fontsize=8)
        # Annotate cells when the matrix is small enough
        if n <= 18:
            for i in range(n):
                for j in range(n):
                    v = self._correlation.iloc[i, j]
                    if pd.isna(v):
                        continue
                    txt_color = "white" if abs(v) > 0.6 else "black"
                    ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                            fontsize=7, color=txt_color)
        cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Pearson r", fontsize=9)
        ax.set_title(f"Correlation matrix ({n} elements)",
                     fontsize=11, pad=8)
        fig.tight_layout()
        self.correlation_canvas.draw()

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        out: dict = {
            "normaliser": self.norm_combo.currentText(),
            "active_tab": self.tabs.currentIndex(),
        }
        # Tectonic discriminators if the user has ticked some
        try:
            keys = self._selected_tect_keys()
        except AttributeError:
            keys = []
        if keys:
            out["selected_tectonic"] = list(keys)
        return out

    def restore(self, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
        ws.restore_combo(self.norm_combo,
                         {"text": state.get("normaliser", "")})
        idx = state.get("active_tab")
        if idx is not None and 0 <= idx < self.tabs.count():
            self.tabs.setCurrentIndex(int(idx))
        # Restore tectonic selection if possible
        keys = state.get("selected_tectonic")
        if keys and hasattr(self, "_set_tect_tree_state"):
            try:
                self._set_tect_tree_state(set(keys))
            except Exception:
                pass
