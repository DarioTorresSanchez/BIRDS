"""Export the active plot to .png / .jpg / .pdf / .svg."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


FORMATS: tuple[tuple[str, str], ...] = (
    ("PDF (.pdf) — vector (recommended for journals)", "pdf"),
    ("PNG (.png) — raster", "png"),
    ("JPEG (.jpg) — raster", "jpg"),
    ("SVG (.svg) — vector", "svg"),
    ("EPS (.eps) — vector (PostScript)", "eps"),
)


MM_PER_INCH = 25.4

# Column widths taken from the current author guidelines of the main
# earth-science publishers.  Values are the *printed* text-block widths,
# so a figure exported at exactly this width needs no rescaling by the
# typesetter — which is what keeps your fonts at the size you chose.
# (label, width in mm)  — ``None`` width means "leave the spin boxes alone".
JOURNAL_PRESETS: tuple[tuple[str, float | None], ...] = (
    ("Custom (set width / height below)", None),
    ("Elsevier — single column (90 mm)", 90.0),
    ("Elsevier — 1.5 column (140 mm)", 140.0),
    ("Elsevier — double column (190 mm)", 190.0),
    ("Nature — single column (89 mm)", 89.0),
    ("Nature — double column (183 mm)", 183.0),
    ("Springer — single column (84 mm)", 84.0),
    ("Springer — double column (174 mm)", 174.0),
    ("AGU / Wiley — single column (95 mm)", 95.0),
    ("AGU / Wiley — full width (190 mm)", 190.0),
    ("GSA Bulletin — single column (89 mm)", 89.0),
    ("GSA Bulletin — double column (186 mm)", 186.0),
)

# Height presets expressed as height / width.
ASPECT_PRESETS: tuple[tuple[str, float], ...] = (
    ("4 : 3 (standard)", 3.0 / 4.0),
    ("1 : 1 (square — ternary plots)", 1.0),
    ("3 : 2 (wide)", 2.0 / 3.0),
    ("16 : 9 (very wide)", 9.0 / 16.0),
    ("Golden ratio", 1.0 / 1.618),
)


def scale_figure_fonts(fig, factor: float):
    """Multiply every text element in *fig* by *factor*.

    Returns the list of ``(artist, original_size)`` pairs so the caller
    can restore the on-screen appearance afterwards.  A factor of 1.0
    is a no-op and returns an empty list.
    """
    if abs(factor - 1.0) < 1e-6:
        return []
    saved: list = []
    items: list = list(fig.texts)
    for ax in fig.axes:
        items.append(ax.title)
        items.append(ax.xaxis.label)
        items.append(ax.yaxis.label)
        items.extend(ax.get_xticklabels())
        items.extend(ax.get_yticklabels())
        items.extend(ax.texts)
        legend = ax.get_legend()
        if legend is not None:
            items.extend(legend.get_texts())
            title = legend.get_title()
            if title is not None:
                items.append(title)
    for artist in items:
        try:
            size = artist.get_fontsize()
        except Exception:                                  # noqa: BLE001
            continue
        saved.append((artist, size))
        artist.set_fontsize(size * factor)
    return saved


def restore_figure_fonts(saved) -> None:
    """Undo :func:`scale_figure_fonts`."""
    for artist, size in saved:
        try:
            artist.set_fontsize(size)
        except Exception:                                  # noqa: BLE001
            pass


def reference_font_size(fig, default: float = 10.0) -> float:
    """Best guess at the figure's *base* font size — the size of the
    first axis label.  Used as the denominator of the print-scaling
    factor so "target 8 pt" means "axis labels come out at 8 pt"."""
    for ax in fig.axes:
        try:
            size = ax.xaxis.label.get_fontsize()
            if size:
                return float(size)
        except Exception:                                  # noqa: BLE001
            continue
    return default


class ExportPlotDialog(QDialog):
    """Modal dialog to configure plot export options."""

    def __init__(
        self,
        suggested_name: str = "birds_plot",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Export plot")
        self.resize(560, 460)

        self._suggested_name = suggested_name
        self._path: Optional[Path] = None
        # Guards the preset ↔ spin-box feedback loop.
        self._suspend_size_signal = False

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Export the active diagram. Use a vector format (.pdf / .svg / "
            ".eps) for journal submissions and downstream editing, or a "
            "raster format (.png / .jpg) for presentations and web."
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
        for label, code in FORMATS:
            self.format_combo.addItem(label, code)
        self.format_combo.currentIndexChanged.connect(self._on_format_changed)
        format_row.addWidget(self.format_combo, stretch=1)
        dest_layout.addLayout(format_row)

        layout.addWidget(dest_box)

        # Journal presets -----------------------------------------------------
        journal_box = QGroupBox("Journal figure size")
        journal_form = QFormLayout(journal_box)

        self.journal_combo = QComboBox()
        for label, width_mm in JOURNAL_PRESETS:
            self.journal_combo.addItem(label, width_mm)
        self.journal_combo.setToolTip(
            "Sets the figure width to the journal's printed column width, "
            "so the typesetter doesn't rescale (and shrink) your fonts."
        )
        self.journal_combo.currentIndexChanged.connect(self._on_preset_changed)
        journal_form.addRow("Preset:", self.journal_combo)

        self.aspect_combo = QComboBox()
        for label, ratio in ASPECT_PRESETS:
            self.aspect_combo.addItem(label, ratio)
        self.aspect_combo.currentIndexChanged.connect(self._on_preset_changed)
        journal_form.addRow("Aspect ratio:", self.aspect_combo)

        self.font_scale_chk = QCheckBox(
            "Scale text so axis labels print at the size below"
        )
        self.font_scale_chk.setChecked(True)
        self.font_scale_chk.setToolTip(
            "Font sizes are absolute points, so shrinking a 7-inch figure "
            "to a 3.5-inch column makes the text look twice as big.  Tick "
            "this to rescale every label, tick and legend entry so they "
            "land at the target size in the printed figure."
        )
        self.font_scale_chk.toggled.connect(
            lambda on: self.target_font_spin.setEnabled(on))
        journal_form.addRow("", self.font_scale_chk)

        self.target_font_spin = QDoubleSpinBox()
        self.target_font_spin.setRange(4.0, 24.0)
        self.target_font_spin.setSingleStep(0.5)
        self.target_font_spin.setValue(8.0)
        self.target_font_spin.setSuffix(" pt")
        self.target_font_spin.setToolTip(
            "Most journals ask for 7-9 pt in the final figure; below 6 pt "
            "is usually rejected."
        )
        journal_form.addRow("Target label size:", self.target_font_spin)

        self.size_hint = QLabel("")
        self.size_hint.setStyleSheet("color: #5b6478; font-size: 11px;")
        self.size_hint.setWordWrap(True)
        journal_form.addRow("", self.size_hint)

        layout.addWidget(journal_box)

        # Render options ----------------------------------------------------
        render_box = QGroupBox("Render options")
        render_form = QFormLayout(render_box)

        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(72, 1200)
        self.dpi_spin.setValue(300)
        self.dpi_spin.setSuffix(" dpi")
        self.dpi_spin.valueChanged.connect(self._refresh_size_hint)
        render_form.addRow("Resolution:", self.dpi_spin)

        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(2.0, 30.0)
        self.width_spin.setSingleStep(0.5)
        self.width_spin.setValue(7.0)
        self.width_spin.setSuffix(" in")
        self.width_spin.valueChanged.connect(self._on_size_edited)
        render_form.addRow("Width:", self.width_spin)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(2.0, 30.0)
        self.height_spin.setSingleStep(0.5)
        self.height_spin.setValue(5.0)
        self.height_spin.setSuffix(" in")
        self.height_spin.valueChanged.connect(self._on_size_edited)
        render_form.addRow("Height:", self.height_spin)

        self.transparent_chk = QCheckBox("Transparent background (PNG / SVG only)")
        render_form.addRow("", self.transparent_chk)

        self.tight_chk = QCheckBox("Tight bounding box (trim white margins)")
        self.tight_chk.setChecked(True)
        render_form.addRow("", self.tight_chk)

        layout.addWidget(render_box)
        layout.addStretch()

        # Buttons -----------------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.save_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        self.save_button.setText("Export")
        self.save_button.setEnabled(False)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_size_hint()

    # ------------------------------------------------------------------ API
    @property
    def path(self) -> Optional[Path]:
        return self._path

    @property
    def fmt(self) -> str:
        return self.format_combo.currentData()

    @property
    def render_kwargs(self) -> dict:
        kwargs: dict = {"dpi": self.dpi_spin.value()}
        if self.tight_chk.isChecked():
            kwargs["bbox_inches"] = "tight"
        if self.transparent_chk.isChecked() and self.fmt in {"png", "svg"}:
            kwargs["transparent"] = True
        return kwargs

    @property
    def figure_size(self) -> tuple[float, float]:
        return (self.width_spin.value(), self.height_spin.value())

    @property
    def target_font_pt(self) -> Optional[float]:
        """Requested printed size of the axis labels, or None when the
        user opted out of font rescaling."""
        if not self.font_scale_chk.isChecked():
            return None
        return float(self.target_font_spin.value())

    # ------------------------------------------------------- size presets
    def _on_preset_changed(self, _index: int) -> None:
        """Apply the selected journal width + aspect to the spin boxes."""
        width_mm = self.journal_combo.currentData()
        if width_mm is None:            # "Custom" — leave the user's values
            self._refresh_size_hint()
            return
        ratio = self.aspect_combo.currentData() or 0.75
        width_in = float(width_mm) / MM_PER_INCH
        self._suspend_size_signal = True
        self.width_spin.setValue(width_in)
        self.height_spin.setValue(width_in * float(ratio))
        self._suspend_size_signal = False
        self._refresh_size_hint()

    def _on_size_edited(self, _value: float) -> None:
        """Typing a custom width/height drops the preset back to Custom."""
        if getattr(self, "_suspend_size_signal", False):
            return
        if self.journal_combo.currentIndex() != 0:
            self.journal_combo.blockSignals(True)
            self.journal_combo.setCurrentIndex(0)
            self.journal_combo.blockSignals(False)
        self._refresh_size_hint()

    def _refresh_size_hint(self, *_args) -> None:
        w_in = self.width_spin.value()
        h_in = self.height_spin.value()
        dpi = self.dpi_spin.value()
        self.size_hint.setText(
            f"Output: {w_in * MM_PER_INCH:.0f} × {h_in * MM_PER_INCH:.0f} mm "
            f"({w_in:.2f} × {h_in:.2f} in) — "
            f"{int(round(w_in * dpi))} × {int(round(h_in * dpi))} px at {dpi} dpi"
        )

    # -------------------------------------------------------------- helpers
    def _on_format_changed(self, _index: int) -> None:
        if self._path is None:
            return
        new_ext = "." + self.format_combo.currentData()
        if self._path.suffix.lower() != new_ext:
            self._path = self._path.with_suffix(new_ext)
            self.path_edit.setText(str(self._path))

    def _browse(self) -> None:
        fmt = self.format_combo.currentData()
        label = next((lbl for lbl, code in FORMATS if code == fmt), fmt.upper())
        filt = f"{label} (*.{fmt})"
        suggested = f"{self._suggested_name}.{fmt}"
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export plot", suggested, filt
        )
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix.lower().lstrip(".") != fmt:
            path = path.with_suffix("." + fmt)
        self._path = path
        self.path_edit.setText(str(self._path))
        self.save_button.setEnabled(True)

    def _on_accept(self) -> None:
        if not self._path:
            QMessageBox.warning(self, "Export", "Please choose a destination file.")
            return
        self.accept()
