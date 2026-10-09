"""Pre-process dialog: rescale majors to 100 % and partition iron.

Exposed in the main window as ``Data → Pre-process majors…``.  Applying
adds the adjusted values beside the analysed ones -- ``SiO2_adj``,
``TiO2_adj``, … -- and leaves the analysed columns as they were; the
"Major elements" switch in each view says which the diagrams read.  A
before / after preview shows what the adjustment does.
"""

from __future__ import annotations


import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..preprocess import (
    AdjustOptions,
    IronOptions,
    MAJOR_OXIDES,
    attach_adjusted,
    pre_process,
)


_ADJUST_LABELS = (
    ("anhydrous", "Anhydrous (volatile-free → 100 wt %)"),
    ("simple",    "Simple proportional → 100 wt %"),
    ("none",      "No 100 % adjustment"),
)

_IRON_LABELS = (
    ("middlemost", "Middlemost (1989) — auto by TAS sector"),
    ("le_maitre",  "Le Maitre (1976) — auto, coarser bins"),
    ("fixed",      "Fixed Fe₂O₃ / (Fe₂O₃+FeO) ratio"),
    ("none",       "Leave Fe₂O₃ / FeO unchanged"),
)


class PreprocessDialog(QDialog):
    """Modal dialog for the pre-processing pipeline."""

    def __init__(self, data_manager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Pre-process major elements")
        self.resize(900, 560)
        self.data = data_manager

        outer = QVBoxLayout(self)

        intro = QLabel(
            "Re-scale the major oxides so each sample sums to 100 wt % "
            "and partition total iron between Fe₂O₃ and FeO using a "
            "published rule. Applying adds the adjusted values as new "
            "columns — SiO2_adj, TiO2_adj, … — and keeps the analysed "
            "ones. The <b>Major elements</b> switch in each view chooses "
            "which the diagrams use; it turns to adjusted when you apply."
        )
        intro.setTextFormat(Qt.TextFormat.RichText)
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #5b6478;")
        outer.addWidget(intro)

        # ---- options row ----------------------------------------------------
        row = QHBoxLayout()

        adj_box = QGroupBox("100 % adjustment")
        af = QFormLayout(adj_box)
        self.adjust_combo = QComboBox()
        for key, label in _ADJUST_LABELS:
            self.adjust_combo.addItem(label, key)
        self.adjust_combo.currentIndexChanged.connect(self._refresh_preview)
        af.addRow("Mode:", self.adjust_combo)
        adj_note = QLabel(
            "Anhydrous zeros LOI / H₂O / CO₂ before rescaling. "
            "Simple keeps volatiles in the row sum."
        )
        adj_note.setStyleSheet("color: #6c7388; font-size: 10px;")
        adj_note.setWordWrap(True)
        af.addRow(adj_note)
        row.addWidget(adj_box, stretch=1)

        iron_box = QGroupBox("Iron partition")
        f2 = QFormLayout(iron_box)
        self.iron_combo = QComboBox()
        for key, label in _IRON_LABELS:
            self.iron_combo.addItem(label, key)
        self.iron_combo.currentIndexChanged.connect(self._on_iron_changed)
        f2.addRow("Rule:", self.iron_combo)
        self.ratio_spin = QDoubleSpinBox()
        self.ratio_spin.setRange(0.0, 1.0)
        self.ratio_spin.setSingleStep(0.05)
        self.ratio_spin.setValue(0.15)
        self.ratio_spin.setDecimals(3)
        self.ratio_spin.setEnabled(False)
        self.ratio_spin.valueChanged.connect(self._refresh_preview)
        f2.addRow("Fixed ratio (if used):", self.ratio_spin)
        iron_note = QLabel(
            "Fe₂O₃/(Fe₂O₃+FeO). Middlemost & Le Maitre derive the ratio "
            "automatically from SiO₂ + alkalis. FeOt is conserved by all "
            "rules."
        )
        iron_note.setStyleSheet("color: #6c7388; font-size: 10px;")
        iron_note.setWordWrap(True)
        f2.addRow(iron_note)
        row.addWidget(iron_box, stretch=1)

        outer.addLayout(row)

        # ---- preview --------------------------------------------------------
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine); outer.addWidget(sep)
        self.preview_label = QLabel("Preview (first 5 samples, major oxides only):")
        self.preview_label.setStyleSheet("font-weight: 600;")
        outer.addWidget(self.preview_label)

        self.preview_table = QTableWidget()
        self.preview_table.setAlternatingRowColors(True)
        self.preview_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.preview_table.setSizePolicy(QSizePolicy.Policy.Expanding,
                                         QSizePolicy.Policy.Expanding)
        outer.addWidget(self.preview_table, stretch=1)

        # ---- footer ---------------------------------------------------------
        self.status = QLabel("")
        self.status.setStyleSheet("color: #5b6478;")
        outer.addWidget(self.status)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Apply
            | QDialogButtonBox.StandardButton.Cancel
        )
        btns.button(QDialogButtonBox.StandardButton.Apply).setText("Apply")
        btns.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply)
        btns.rejected.connect(self.reject)
        outer.addWidget(btns)

        self._refresh_preview()

    # ------------------------------------------------------------------ logic
    def _current_adjust(self) -> AdjustOptions:
        return AdjustOptions(mode=self.adjust_combo.currentData())

    def _current_iron(self) -> IronOptions:
        return IronOptions(rule=self.iron_combo.currentData(),
                           fixed_ratio=self.ratio_spin.value())

    def _on_iron_changed(self, _idx: int) -> None:
        self.ratio_spin.setEnabled(self.iron_combo.currentData() == "fixed")
        self._refresh_preview()

    def _refresh_preview(self) -> None:
        df = self.data.df
        if df is None or df.empty:
            self.status.setText("⚠  No dataset loaded — import data first.")
            self.preview_table.clear()
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return
        try:
            processed = pre_process(df, self._current_adjust(), self._current_iron())
        except Exception as exc:                           # noqa: BLE001
            self.status.setText(f"Pre-process failed: {exc}")
            return

        # Pick the major-oxide columns that exist in the data
        cols = [c for c in MAJOR_OXIDES if c in df.columns]
        if not cols:
            self.status.setText(
                "⚠  No major-oxide columns recognised "
                "(expected SiO2, TiO2, Al2O3, …)."
            )
            self.preview_table.clear()
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            return

        # Show first N rows
        n = min(5, len(df))
        # Column layout: name (or index), then 2 columns per oxide (before/after)
        headers = ["Sample"]
        for c in cols:
            headers.append(f"{c} (before)")
            headers.append(f"{c} (after)")
        headers.append("Σ (before)")
        headers.append("Σ (after)")

        self.preview_table.setRowCount(n)
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)

        name_col = None
        for cand in ("Sample_Name", "Sample", "Name", "No."):
            if cand in df.columns:
                name_col = cand
                break

        for i in range(n):
            idx = df.index[i]
            label = (str(df.at[idx, name_col]) if name_col
                     else str(idx))
            self.preview_table.setItem(i, 0, QTableWidgetItem(label))
            for j, c in enumerate(cols):
                v_before = pd.to_numeric(df.at[idx, c], errors="coerce")
                v_after = pd.to_numeric(processed.at[idx, c], errors="coerce")
                self.preview_table.setItem(i, 1 + 2 * j,
                                            self._make_item(v_before))
                item_after = self._make_item(v_after, highlight=True)
                self.preview_table.setItem(i, 1 + 2 * j + 1, item_after)
            # row sums
            sum_before = (pd.to_numeric(df.loc[idx, cols], errors="coerce")
                          .fillna(0).sum())
            sum_after  = (pd.to_numeric(processed.loc[idx, cols], errors="coerce")
                          .fillna(0).sum())
            self.preview_table.setItem(i, len(headers) - 2,
                                        self._make_item(sum_before))
            self.preview_table.setItem(i, len(headers) - 1,
                                        self._make_item(sum_after,
                                                        highlight=True))

        self.preview_table.resizeColumnsToContents()
        self.status.setText(
            f"Previewing {n} of {len(df)} samples. Apply adds the adjusted "
            f"values as *_adj columns; the analysed values are kept."
        )
        self._preview_processed = processed

    @staticmethod
    def _make_item(value, *, highlight: bool = False) -> QTableWidgetItem:
        text = "" if pd.isna(value) else f"{value:.3f}"
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight |
                              Qt.AlignmentFlag.AlignVCenter)
        if highlight:
            item.setForeground(Qt.GlobalColor.darkBlue)
        return item

    # ------------------------------------------------------------------ apply
    def _apply(self) -> None:
        if self.data.df is None or self.data.df.empty:
            self.reject()
            return
        adjust, iron = self._current_adjust(), self._current_iron()
        try:
            self.data.df = attach_adjusted(self.data.df, adjust, iron)
        except Exception as exc:                           # noqa: BLE001
            self.status.setText(f"Pre-process failed: {exc}")
            return
        self.data.adjust_settings = {"mode": adjust.mode, "iron": iron.rule,
                                     "ratio": iron.fixed_ratio}
        self.data.use_adjusted = True
        self.accept()
