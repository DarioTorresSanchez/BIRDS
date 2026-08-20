"""CIPW normative-mineralogy view.

Two complementary representations of the same result:

* **Tab 1 — Table**: one row per sample, one column per mineral
  (wt %), plus a silica-saturation column colour-coded by category
  (oversaturated / saturated / undersaturated) and, for the SINCLAS
  variant, a TAS-derived rock name.

* **Tab 2 — Bar plot**: stacked 100 %-bar chart by sample (or by
  group), with a fixed palette that maps each normative mineral to a
  petrologically-meaningful colour.

A multi-sheet XLSX export bundles: input oxides → preprocessed oxides →
iron-partitioned analysis → CIPW table → classification, so the file is
fully self-contained for thesis appendices.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from matplotlib.patches import Patch
from PySide6.QtCore import Qt
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..cipw import OUTPUT_MINERALS, compute_cipw
from ..diagrams.templates.base import get_groups
from ..preprocess import pre_process
from .plot_canvas import PlotCanvas


# ---------------------------------------------------------------------------
# Colour palette for the stacked bar plot
# ---------------------------------------------------------------------------

MINERAL_COLOURS: Dict[str, str] = {
    # Felsic (warm-light)
    "Q":  "#f6e3b4",   # quartz             pale yellow
    "Or": "#f4b183",   # orthoclase         peach
    "Ab": "#f9d2e2",   # albite             pink
    "An": "#c2a4dc",   # anorthite          lavender
    "Ne": "#94c3e1",   # nepheline          light blue
    "Lc": "#5a9fd4",   # leucite            blue
    "Kp": "#3c7fb1",   # kaliophilite       darker blue
    "C":  "#e0e0e0",   # corundum           light grey
    # Mafic (cool / earth)
    "Di": "#9bcd84",   # diopside           green
    "Wo": "#bee2a4",   # wollastonite       light green
    "Hy": "#6a9c40",   # hypersthene        olive
    "Ol": "#3f7026",   # olivine            dark green
    # Accessories
    "Mt": "#5d5d5d",   # magnetite          dark grey
    "Hm": "#b13a3a",   # hematite           red brown
    "Il": "#7a5a4a",   # ilmenite           brown
    "Ru": "#a36b46",   # rutile             tan
    "Tn": "#d4a017",   # titanite           ochre
    "Cm": "#3a2e2e",   # chromite           near-black
    "Ap": "#bfd8d2",   # apatite            mint
    "Pf": "#f3e6c3",   # perovskite         cream
    "Z":  "#c97f7f",   # zircon             dusty rose
    "Ac": "#2e7d32",   # acmite             forest
    "Ns": "#8e44ad",   # Na metasilicate    purple
    # Hutchison extras
    "Py": "#fee08b",   # pyrite             gold
    "Cc": "#dfdfdf",   # calcite            pale grey
    "Hl": "#ffffff",   # halite             white
    "Fl": "#ebd6f1",   # fluorite           lilac
}

# Foreground for the saturation column in the table
SAT_FILL: Dict[str, QColor] = {
    "oversaturated":   QColor(248, 215, 188),   # warm peach
    "saturated":       QColor(218, 235, 199),   # mint
    "undersaturated":  QColor(196, 212, 240),   # cool blue
}


VARIANTS = (
    ("SINCLAS (Verma 2002) — recommended", "sinclas"),
    ("Verma & Rivera-Gómez (2013) — SINCLAS + titanite / perovskite chain",
     "verma_rg_2013"),
    ("Classical (Cross-Iddings-Pirsson-Washington 1903)", "classical"),
    ("Extended (Hutchison 1974 + Verma 2003 — Py, Cc, Hl, Fl)", "hutchison"),
)


# ---------------------------------------------------------------------------
# NormView
# ---------------------------------------------------------------------------

class NormView(QWidget):
    """CIPW normative dashboard."""

    def __init__(self, data_manager, plot_style,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style

        # Last computed result, kept around for export and bar plot
        self._result: Optional[pd.DataFrame] = None
        self._preprocessed: Optional[pd.DataFrame] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ----- left: controls panel ----------------------------------------
        ctrl = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(ctrl)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._build_controls(ctrl)

        # Sticky action bar — both buttons visible without scrolling
        self.run_btn = QPushButton("Compute CIPW norm")
        self.run_btn.setMinimumHeight(34)
        self.run_btn.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 6px 12px; }"
        )
        self.run_btn.clicked.connect(self.compute)
        self.export_btn = QPushButton("Export XLSX report…")
        self.export_btn.setMinimumHeight(30)
        self.export_btn.clicked.connect(self.export_xlsx)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(scroll, stretch=1)
        sep_left = QFrame()
        sep_left.setFrameShape(QFrame.Shape.HLine)
        sep_left.setStyleSheet("color: #ccc;")
        left_layout.addWidget(sep_left)
        btn_pad = QWidget()
        btn_pad_l = QVBoxLayout(btn_pad)
        btn_pad_l.setContentsMargins(8, 6, 8, 8)
        btn_pad_l.setSpacing(4)
        btn_pad_l.addWidget(self.run_btn)
        btn_pad_l.addWidget(self.export_btn)
        left_layout.addWidget(btn_pad)
        left_panel.setMinimumWidth(380)
        left_panel.setMaximumWidth(540)
        splitter.addWidget(left_panel)

        # ----- right: header + tabs ----------------------------------------
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(6)
        self.title_label = QLabel("Normative mineralogy (CIPW)")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.subtitle_label = QLabel(
            "Compute the CIPW norm of every sample with one of three "
            "published algorithms. Results can be auto-filled into the "
            "dataset (so diagrams like Barker An-Ab-Or, Haplogranite Q-"
            "Ab-Or and the Irvine-Baragar boundary pick them up) and "
            "exported as a multi-sheet XLSX report."
        )
        self.subtitle_label.setStyleSheet("color: #5b6478;")
        self.subtitle_label.setWordWrap(True)
        rl.addWidget(self.title_label)
        rl.addWidget(self.subtitle_label)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); rl.addWidget(sep)

        self.tabs = QTabWidget()
        rl.addWidget(self.tabs, stretch=1)

        # Tab 1 — table
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.tabs.addTab(self.table, "Mineral table")

        # Tab 2 — stacked bar plot
        self.canvas = PlotCanvas()
        self.tabs.addTab(self.canvas, "Stacked bar")

        # Tab 3 — summary
        self.summary_label = QLabel("Run the computation to see a summary.")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet(
            "color: #1c2237; font-family: 'Menlo', 'Monaco', 'Consolas', 'Courier New', monospace; "
            "padding: 12px;")
        sumw = QWidget()
        sl = QVBoxLayout(sumw)
        sl.addWidget(self.summary_label)
        sl.addStretch()
        self.tabs.addTab(sumw, "Summary")

        splitter.addWidget(right)
        splitter.setSizes([460, 820])

    # ------------------------------------------------------------------ UI
    def _build_controls(self, parent: QWidget) -> None:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Helper to set up a tightly-packed QFormLayout
        def _compact_form() -> QFormLayout:
            f = QFormLayout()
            f.setContentsMargins(0, 0, 0, 0)
            f.setHorizontalSpacing(8)
            f.setVerticalSpacing(4)
            f.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
            )
            return f

        # Algorithm -------------------------------------------------------
        algo_box = QGroupBox("Algorithm")
        algo_box.setToolTip(
            "Choose the CIPW algorithm. SINCLAS is the recommended "
            "modern variant; Verma & Rivera-Gómez 2013 adds the titanite "
            "/ perovskite chain for silica-undersaturated rocks."
        )
        algo_layout = QVBoxLayout(algo_box)
        algo_layout.setContentsMargins(8, 12, 8, 8)
        algo_layout.setSpacing(4)
        f = _compact_form()
        self.variant_combo = QComboBox()
        for label, key in VARIANTS:
            self.variant_combo.addItem(label, key)
        f.addRow("Variant:", self.variant_combo)
        algo_layout.addLayout(f)
        layout.addWidget(algo_box)

        # Bar plot options -----------------------------------------------
        bar_box = QGroupBox("Bar plot")
        bar_layout = QVBoxLayout(bar_box)
        bar_layout.setContentsMargins(8, 12, 8, 8)
        bar_layout.setSpacing(4)
        bf = _compact_form()
        self.aggregate_combo = QComboBox()
        self.aggregate_combo.addItem("One bar per sample", "sample")
        self.aggregate_combo.addItem("One bar per group (mean)", "group")
        bf.addRow("Aggregation:", self.aggregate_combo)
        self.show_legend_chk = QCheckBox("Show legend")
        self.show_legend_chk.setChecked(True)
        bf.addRow("", self.show_legend_chk)
        self.min_pct_threshold = QComboBox()
        for v in ("0.1 %", "0.5 %", "1 %", "2 %"):
            self.min_pct_threshold.addItem(v, float(v.replace(" %", "")))
        self.min_pct_threshold.setCurrentIndex(0)
        bf.addRow("Hide minerals below:", self.min_pct_threshold)
        bar_layout.addLayout(bf)
        layout.addWidget(bar_box)

        # Auto-fill -------------------------------------------------------
        attach_tooltip = (
            "When ON, B.I.R.D.S adds the <code>norm_*</code> columns to "
            "the loaded dataset so the Barker An-Ab-Or, Haplogranite "
            "Ab-Or-Q and Irvine-Baragar 1971 diagrams pick up the "
            "computed normative values automatically."
        )
        fill_box = QGroupBox("Integration with other views")
        fill_box.setToolTip(attach_tooltip)
        fill_layout = QVBoxLayout(fill_box)
        fill_layout.setContentsMargins(8, 12, 8, 8)
        fill_layout.setSpacing(4)
        self.attach_chk = QCheckBox(
            "Auto-fill normative columns into the dataset")
        self.attach_chk.setChecked(True)
        self.attach_chk.setToolTip(attach_tooltip)
        fill_layout.addWidget(self.attach_chk)
        ff_note = QLabel(
            "<i>Hover ⓘ for what this changes downstream.</i>"
        )
        ff_note.setStyleSheet("color: #6c7388; font-size: 11px;")
        ff_note.setTextFormat(Qt.TextFormat.RichText)
        ff_note.setWordWrap(True)
        ff_note.setToolTip(attach_tooltip)
        fill_layout.addWidget(ff_note)
        layout.addWidget(fill_box)

        # The Compute / Export buttons live OUTSIDE the scroll area
        # so they are always visible — they are created in __init__.
        layout.addStretch(1)

    # ------------------------------------------------------------------ API
    def show_view(self) -> None:
        """Called when the user navigates into the Norm view."""
        if self.data.df is None or self.data.df.empty:
            self._empty("Load a dataset (Data → Import) before computing CIPW.")
            return
        # Don't auto-compute — the user might want to pick a variant first
        self.summary_label.setText(
            "Pick a variant on the left and click 'Compute CIPW norm'.")

    def compute(self) -> None:
        df = self.data.df
        if df is None or df.empty:
            QMessageBox.information(self, "No data",
                                    "Load a dataset before computing.")
            return

        variant = self.variant_combo.currentData()
        try:
            result = compute_cipw(df, variant=variant)
        except Exception as exc:                           # noqa: BLE001
            QMessageBox.critical(self, "CIPW error", str(exc))
            return

        self._result = result
        self._preprocessed = df.copy()

        # Optionally write back
        if self.attach_chk.isChecked():
            for col in result.columns:
                df[col] = result[col]

        # Update tabs
        self._fill_table(result)
        self._draw_bar_plot(result)
        self._update_summary(result, variant)

    # ------------------------------------------------------------ table tab
    def _fill_table(self, result: pd.DataFrame) -> None:
        """Render the per-sample mineral table with saturation colour codes."""
        cols = ["norm_Total"] + [f"norm_{m}" for m in OUTPUT_MINERALS]
        # Drop minerals that are 0 across all samples to keep the table tidy
        nonzero_cols = [c for c in cols
                        if c == "norm_Total"
                        or (pd.to_numeric(result[c], errors="coerce") > 0.01).any()]
        sat_col = "silica_saturation"
        tas_col = "tas_field" if "tas_field" in result.columns else None
        headers = (["Sample", sat_col]
                   + ([tas_col] if tas_col else [])
                   + [c.replace("norm_", "") for c in nonzero_cols])
        self.table.clear()
        self.table.setRowCount(len(result))
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Sample-label resolution
        df = self.data.df
        name_col = None
        for cand in ("Sample_Name", "Sample", "Name", "No."):
            if cand in df.columns:
                name_col = cand
                break

        for i, idx in enumerate(result.index):
            sample = str(df.at[idx, name_col]) if name_col else str(idx)
            self.table.setItem(i, 0, QTableWidgetItem(sample))
            sat = str(result.at[idx, sat_col])
            item_sat = QTableWidgetItem(sat)
            item_sat.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if sat in SAT_FILL:
                item_sat.setBackground(QBrush(SAT_FILL[sat]))
            self.table.setItem(i, 1, item_sat)
            col_offset = 2
            if tas_col:
                self.table.setItem(i, 2, QTableWidgetItem(
                    str(result.at[idx, tas_col])))
                col_offset = 3
            for j, c in enumerate(nonzero_cols):
                v = pd.to_numeric(result.at[idx, c], errors="coerce")
                text = "" if pd.isna(v) else f"{v:.2f}"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight
                                      | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(i, col_offset + j, item)
        self.table.resizeColumnsToContents()

    # --------------------------------------------------------- bar plot tab
    def _draw_bar_plot(self, result: pd.DataFrame) -> None:
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        df_data = self.data.df
        agg = self.aggregate_combo.currentData()
        threshold = float(self.min_pct_threshold.currentData())

        # Build the matrix: rows = bars, cols = minerals
        norm_cols = [f"norm_{m}" for m in OUTPUT_MINERALS
                     if (pd.to_numeric(result[f"norm_{m}"], errors="coerce")
                         > threshold).any()]
        if not norm_cols:
            ax.text(0.5, 0.5, "All normative minerals fall below the threshold.",
                    ha="center", va="center", color="#6c7388",
                    transform=ax.transAxes)
            ax.axis("off")
            self.canvas.draw()
            return

        if agg == "group":
            # One bar per group (mean of normative wt%)
            groups = list(get_groups(df_data, self.plot_style))
            if not groups:
                ax.text(0.5, 0.5, "No groups defined.", ha="center",
                        va="center", transform=ax.transAxes,
                        color="#6c7388")
                ax.axis("off")
                self.canvas.draw()
                return
            labels = [g[0] for g in groups]
            matrix = np.array([
                [result.loc[g[1].index, c].mean() for c in norm_cols]
                for g in groups
            ])
        else:
            # One bar per sample
            df = df_data
            name_col = next((c for c in ("Sample_Name", "Sample", "Name", "No.")
                             if c in df.columns), None)
            labels = ([str(df.at[i, name_col]) for i in result.index]
                      if name_col else [str(i) for i in result.index])
            matrix = result[norm_cols].to_numpy(dtype=float)

        # Normalise each row to 100 % so all bars are visually comparable
        row_sums = matrix.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = np.nan
        norm_matrix = matrix / row_sums * 100.0

        x = np.arange(len(labels))
        bottom = np.zeros(len(labels))
        legend_handles: List[Patch] = []
        for j, col in enumerate(norm_cols):
            mineral = col.replace("norm_", "")
            colour = MINERAL_COLOURS.get(mineral, "#888888")
            ax.bar(x, norm_matrix[:, j], bottom=bottom, color=colour,
                   edgecolor="white", linewidth=0.4, label=mineral)
            legend_handles.append(Patch(facecolor=colour, edgecolor="white",
                                         label=mineral))
            bottom = bottom + np.nan_to_num(norm_matrix[:, j], nan=0)

        ax.set_xticks(x)
        ax.set_xticklabels(labels,
                           rotation=45 if len(labels) > 6 else 0,
                           ha="right" if len(labels) > 6 else "center",
                           fontsize=9)
        ax.set_ylabel("Normative mineralogy (wt %, rescaled to 100 %)")
        ax.set_ylim(0, 100)
        ax.grid(True, axis="y", linestyle=":", linewidth=0.5,
                color="#aaa", alpha=0.7)
        ax.set_axisbelow(True)
        if self.show_legend_chk.isChecked() and legend_handles:
            ax.legend(handles=legend_handles, loc="upper left",
                      bbox_to_anchor=(1.01, 1.0),
                      fontsize=8, frameon=False, ncol=1)
        fig.tight_layout()
        self.canvas.draw()

    # ------------------------------------------------------------- summary
    def _update_summary(self, result: pd.DataFrame, variant: str) -> None:
        n = len(result)
        sat_counts = result["silica_saturation"].value_counts()
        parts = [
            f"Variant   : {variant.upper()}",
            f"Samples   : {n}",
            f"Norm Σ ±  : "
            + f"{result['norm_Total'].mean():.2f} ± "
            + f"{result['norm_Total'].std(ddof=0):.2f}  wt%",
            "",
            "Silica saturation distribution:",
        ]
        for label in ("oversaturated", "saturated", "undersaturated"):
            count = int(sat_counts.get(label, 0))
            parts.append(f"  {label:18s}{count:5d}   "
                         f"({(count/n*100 if n else 0):.1f} %)")
        if "tas_field" in result.columns:
            tas_counts = result["tas_field"].value_counts()
            parts.append("")
            parts.append("TAS rock distribution (SINCLAS):")
            for name, count in tas_counts.items():
                parts.append(f"  {name:25s}{int(count):5d}")
        # Mean of each non-zero mineral
        parts.append("")
        parts.append("Mean wt% per normative mineral (≥ 0.1 %):")
        for col in [f"norm_{m}" for m in OUTPUT_MINERALS]:
            v = pd.to_numeric(result[col], errors="coerce").mean()
            if v > 0.1:
                parts.append(f"  {col.replace('norm_',''):6s}{v:7.2f}")
        self.summary_label.setText("\n".join(parts))

    # ------------------------------------------------------------- export
    def export_xlsx(self) -> None:
        if self._result is None or self.data.df is None:
            QMessageBox.information(
                self, "Nothing to export",
                "Compute the CIPW norm first (button on the left)."
            )
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CIPW report", "BIRDS_CIPW_report.xlsx",
            "Excel workbook (*.xlsx)",
        )
        if not path:
            return
        try:
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                # 1. Input — as currently loaded (after any preprocess)
                self.data.df.to_excel(writer, sheet_name="Input",
                                       index=True)
                # 2. CIPW table
                self._result.to_excel(writer, sheet_name="CIPW", index=True)
                # 3. Classification only
                class_cols = ["silica_saturation"]
                if "tas_field" in self._result.columns:
                    class_cols.append("tas_field")
                self._result[class_cols].to_excel(
                    writer, sheet_name="Classification", index=True)
                # 4. Total per sample
                self._result[["norm_Total"]].to_excel(
                    writer, sheet_name="Totals", index=True)
                # 5. Variant info
                pd.DataFrame({
                    "Field": [
                        "Algorithm variant", "Number of samples",
                        "Mean norm total (wt%)",
                    ],
                    "Value": [
                        self.variant_combo.currentText(),
                        len(self._result),
                        f"{self._result['norm_Total'].mean():.3f}",
                    ],
                }).to_excel(writer, sheet_name="Metadata", index=False)
        except Exception as exc:                           # noqa: BLE001
            QMessageBox.critical(self, "Export error", str(exc))
            return
        QMessageBox.information(
            self, "Export complete",
            f"CIPW report written to:\n{path}"
        )

    # ------------------------------------------------------------ utilities
    def _empty(self, message: str) -> None:
        self.summary_label.setText(message)
        self.table.clear()
        self.table.setRowCount(0)
        self.canvas.figure.clear()
        self.canvas.draw()

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        from .. import widget_state as ws
        return {
            "variant": self.variant_combo.currentData() or "sinclas",
            "aggregation": self.aggregate_combo.currentData() or "sample",
            "show_legend": ws.check_state(self.show_legend_chk),
            "min_pct_index": self.min_pct_threshold.currentIndex(),
            "attach": ws.check_state(self.attach_chk),
            "has_result": self._result is not None,
        }

    def restore(self, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
        for code, combo in [
            (state.get("variant"), self.variant_combo),
            (state.get("aggregation"), self.aggregate_combo),
        ]:
            if code:
                idx = combo.findData(code)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
        ws.restore_check(self.show_legend_chk, state.get("show_legend"))
        idx = state.get("min_pct_index")
        if idx is not None and 0 <= idx < self.min_pct_threshold.count():
            self.min_pct_threshold.setCurrentIndex(int(idx))
        ws.restore_check(self.attach_chk, state.get("attach"))

    def restore_result(self, result_df: pd.DataFrame) -> None:
        """Re-populate the table / bar plot / summary from a cached CIPW
        result DataFrame loaded out of a ``.birds`` session, without
        recomputing the norm from scratch."""
        if result_df is None or result_df.empty:
            return
        self._result = result_df
        variant = self.variant_combo.currentData() or "sinclas"
        self._fill_table(result_df)
        self._draw_bar_plot(result_df)
        self._update_summary(result_df, variant)
