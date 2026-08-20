"""Save the statistics-and-anomalies output to .xlsx or .csv."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


# Sections offered by the dialog.  Single source of truth for both the
# checkbox UI and the ``sections`` payload consumed by main_window.
_SECTIONS: Tuple[Tuple[str, str], ...] = (
    ("raw",         "Original dataset (samples × elements)"),
    ("adjusted",    "Pre-processed analyses (100 % adjusted + Fe partitioned)"),
    ("cipw",        "CIPW normative mineralogy (per-sample wt % + classification)"),
    ("descriptive", "Descriptive statistics (count, mean, std, min, percentiles, max)"),
    ("anomalies",   "REE anomalies (Eu/Eu*, Ce/Ce*) per sample"),
    ("ratios",      "Selected trace-element ratios (La/Yb, Zr/Y, Th/Yb, …) per sample"),
    ("tectonic",    "Tectonic-discrimination results (whatever is ticked in the Statistics view)"),
)


class SaveStatisticsDialog(QDialog):
    """Choose destination, file type and which sections to include."""

    def __init__(
        self,
        suggested_name: str = "birds_statistics",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Save file – Statistics & Anomalies")
        self.resize(580, 440)

        self._path: Optional[Path] = None
        self._suggested_name = suggested_name

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Save the statistical analysis output (descriptive statistics, "
            "Eu/Eu* and Ce/Ce* anomalies, selected trace-element ratios) "
            "together with the original samples imported into B.I.R.D.S. "
            "Pre-processed analyses (100 % adjusted, Fe partitioned) and "
            "CIPW normative mineralogy can also be bundled when they have "
            "been computed."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #444;")
        layout.addWidget(intro)

        # Destination -------------------------------------------------------
        dest_box = QGroupBox("Destination")
        dest_layout = QVBoxLayout(dest_box)

        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Click 'Browse' to choose a file…")
        self.path_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        path_row.addWidget(self.path_edit, stretch=1)
        path_row.addWidget(browse_btn)
        dest_layout.addLayout(path_row)

        format_row = QHBoxLayout()
        format_row.addWidget(QLabel("Format:"))
        self.format_combo = QComboBox()
        self.format_combo.addItem(
            "Excel workbook (.xlsx) — one sheet per section", "xlsx"
        )
        self.format_combo.addItem(
            "CSV (.csv) — sections concatenated with headers", "csv"
        )
        format_row.addWidget(self.format_combo, stretch=1)
        dest_layout.addLayout(format_row)

        layout.addWidget(dest_box)

        # Sections ----------------------------------------------------------
        sections_box = QGroupBox("Include")
        sections_layout = QVBoxLayout(sections_box)
        self._checks: Dict[str, QCheckBox] = {}
        for key, label in _SECTIONS:
            cb = QCheckBox(label)
            cb.setChecked(True)
            self._checks[key] = cb
            sections_layout.addWidget(cb)
        layout.addWidget(sections_box)

        layout.addStretch()

        # Buttons -----------------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setEnabled(False)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------ API
    @property
    def path(self) -> Optional[Path]:
        return self._path

    @property
    def fmt(self) -> str:
        return self.format_combo.currentData()

    @property
    def sections(self) -> dict[str, bool]:
        return {k: cb.isChecked() for k, cb in self._checks.items()}

    # -------------------------------------------------------------- helpers
    def _browse(self) -> None:
        fmt = self.format_combo.currentData()
        if fmt == "xlsx":
            filt = "Excel (*.xlsx)"
            ext = ".xlsx"
        else:
            filt = "CSV (*.csv)"
            ext = ".csv"
        suggested = f"{self._suggested_name}{ext}"
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save statistics output", suggested, filt
        )
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix.lower() != ext:
            path = path.with_suffix(ext)
        self._path = path
        self.path_edit.setText(str(self._path))
        self.save_button.setEnabled(True)

    def _on_accept(self) -> None:
        if not self._path:
            QMessageBox.warning(self, "Save", "Please choose a destination file.")
            return
        if not any(self.sections.values()):
            QMessageBox.warning(
                self, "Save", "Select at least one section to include."
            )
            return
        self.accept()
