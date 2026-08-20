"""Petrography view — IUGS modal-mineralogy classifications.

Five ternary diagrams that classify igneous rocks by their thin-section
modal proportions rather than their bulk chemistry:

* **Streckeisen QAPF plutonic** — Q-A-P (top) / A-P-F (bottom) double
  triangle for coarse-grained rocks.
* **Streckeisen QAPF volcanic** — same scheme with the IUGS volcanic
  field names (rhyolite, dacite, trachyte, phonolite …).
* **Gabbro Pl-Px-Ol** — Le Maitre (2002) classification of mafic rocks
  with > 90 % mafic + plagioclase.
* **Ultramafic Ol-Opx-Cpx** — Streckeisen (1976) peridotite /
  pyroxenite ternary.
* **Tuff Crystal-Vitric-Lithic** — Schmid (1981) pyroclastic
  classification.

The view reads the modal-percentage columns from the *Petrography*
sheet that the Import dialog merges onto the bulk-chemistry table
through ``Sample_Name``.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
    QVBoxLayout,
    QWidget,
)

from ..diagrams.registry import get_diagram
from ..diagrams.templates.base import AxisStyle, PlotOptions
from .annotation_controller import AnnotationController
from .plot_canvas import PlotCanvas
from .widgets import AxisGroup, GroupingGroup, LegendGroup


# Catalogue of petrographic diagrams shown in the selector.
_PETROGRAPHY_CATALOG: tuple[tuple[str, str], ...] = (
    ("Streckeisen QAPF — Plutonic (Streckeisen 1976, IUGS 1989)",
     "streckeisen_qapf_plutonic"),
    ("Streckeisen QAPF — Volcanic (Le Maitre 2002, IUGS)",
     "streckeisen_qapf_volcanic"),
    ("Gabbroic rocks — Plagioclase / Pyroxene / Olivine (Le Maitre 2002)",
     "gabbro_pl_px_ol"),
    ("Ultramafic rocks — Olivine / Opx / Cpx (Streckeisen 1976)",
     "ultramafic_ol_opx_cpx"),
    ("Pyroclastic tuffs — Crystal / Vitric / Lithic (Schmid 1981)",
     "tuff_crystal_vitric_lithic"),
)


class PetrographyView(QWidget):
    """Splitter UI for the petrographic ternaries."""

    def __init__(self, data_manager, plot_style,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style
        self._diagram_key: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ----- Left: controls panel ---------------------------------------
        controls = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._build_controls(controls)

        # Sticky action bar (always visible at the bottom)
        self.update_btn = QPushButton("Update plot")
        self.update_btn.setMinimumHeight(34)
        self.update_btn.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 6px 12px; }"
        )
        self.update_btn.clicked.connect(self.update_plot)

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
        btn_pad_l.addWidget(self.update_btn)
        left_layout.addWidget(btn_pad)
        left_panel.setMinimumWidth(380)
        left_panel.setMaximumWidth(540)
        splitter.addWidget(left_panel)

        # ----- Right: canvas ----------------------------------------------
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(6)
        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        self.title_label.setWordWrap(True)
        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("color: #5b6478;")
        self.subtitle_label.setWordWrap(True)
        right_layout.addWidget(self.title_label)
        right_layout.addWidget(self.subtitle_label)
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        right_layout.addWidget(sep)
        self.canvas = PlotCanvas()
        right_layout.addWidget(self.canvas, stretch=1)
        splitter.addWidget(right)
        splitter.setSizes([460, 820])
        self.annotation_ctl.bind_canvas(self.canvas)

        # Start on the first entry
        if self.diagram_combo.count():
            self._on_diagram_changed(0)

    # ------------------------------------------------------------------ UI
    def _build_controls(self, parent: QWidget) -> None:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Rich help shown on hover instead of stealing vertical space.
        sel_tooltip = (
            "<b>Petrographic ternaries</b> read modal-percentage columns "
            "(Q_mode, A_mode, Pl_mode, Px_mode, Ol_mode, Crystal_pct …) "
            "from the <b>Petrography</b> sheet, joined to the bulk "
            "dataset through <code>Sample_Name</code> at import time."
        )

        sel_box = QGroupBox("Diagram selection")
        sel_box.setToolTip(sel_tooltip)
        sel_layout = QVBoxLayout(sel_box)
        sel_layout.setContentsMargins(8, 12, 8, 8)
        sel_layout.setSpacing(4)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(4)
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )
        self.diagram_combo = QComboBox()
        for label, key in _PETROGRAPHY_CATALOG:
            self.diagram_combo.addItem(label, key)
        self.diagram_combo.currentIndexChanged.connect(self._on_diagram_changed)
        self.diagram_combo.setToolTip(sel_tooltip)
        form.addRow("Diagram:", self.diagram_combo)
        sel_layout.addLayout(form)

        intro = QLabel(
            "<i>Modal-percent ternaries from the Petrography sheet — "
            "hover ⓘ for column names.</i>"
        )
        intro.setWordWrap(True)
        intro.setTextFormat(Qt.TextFormat.RichText)
        intro.setToolTip(sel_tooltip)
        intro.setStyleSheet("color: #6c7388; font-size: 11px;")
        sel_layout.addWidget(intro)
        layout.addWidget(sel_box)

        self.axis_grp = AxisGroup("Apex labels (font)")
        # Modal ternaries don't have X/Y/log axes in the usual sense
        self.axis_grp.log_x.setVisible(False)
        self.axis_grp.log_y.setVisible(False)
        self.axis_grp.x_label_edit.setVisible(False)
        self.axis_grp.y_label_edit.setVisible(False)
        layout.addWidget(self.axis_grp)

        self.legend_grp = LegendGroup()
        layout.addWidget(self.legend_grp)

        self.grouping_grp = GroupingGroup()
        # Faceting doesn't make sense on a fixed ternary frame
        self.grouping_grp.facet_chk.setVisible(False)
        layout.addWidget(self.grouping_grp)

        # Annotation toolkit — ternary diagrams use barycentric clicks
        # so identify-sample is awkward; keep it disabled here.
        self.annotation_ctl = AnnotationController(self, sample_resolver=None)
        layout.addWidget(self.annotation_ctl.group)

        layout.addStretch(1)

    # ------------------------------------------------------------------ API
    def show_diagram(self, key: str) -> None:
        """Switch to *key* and re-render."""
        i = self.diagram_combo.findData(key)
        if i >= 0:
            self.diagram_combo.setCurrentIndex(i)

    def _active_df(self):
        """Prefer the standalone Petrography sheet, fall back to the main
        Data sheet for legacy single-sheet imports."""
        df = getattr(self.data, "petrography_df", None)
        if df is not None and not df.empty:
            return df
        return self.data.df

    def update_plot(self) -> None:
        if not self._diagram_key:
            return
        diagram = get_diagram(self._diagram_key)
        if diagram is None:
            self._empty_canvas(
                f"Diagram template '{self._diagram_key}' not yet implemented.")
            return
        axis_style = AxisStyle(
            font_size=self.axis_grp.font_size.value(),
            font_family=self.axis_grp.font_family.currentText(),
            font_weight="bold" if self.axis_grp.bold.isChecked() else "normal",
            font_style="italic" if self.axis_grp.italic.isChecked() else "normal",
        )
        options = PlotOptions(
            x_axis=axis_style, y_axis=axis_style,
            legend=self.legend_grp.legend_style(),
        )
        try:
            diagram.plot(self.canvas.figure, self._active_df(),
                          self.plot_style, options)
        except Exception as exc:                           # noqa: BLE001
            self._empty_canvas(f"Plot error:\n{exc}")
            return
        if self.canvas.figure.axes:
            self.annotation_ctl.draw(self.canvas.figure.axes[0])
        self.canvas.draw()

    # ------------------------------------------------------------------ impl
    def _on_diagram_changed(self, _index: int) -> None:
        if self.diagram_combo.count() == 0:
            return
        self._diagram_key = self.diagram_combo.currentData()
        diagram = get_diagram(self._diagram_key)
        if diagram is None:
            self.title_label.setText(self._diagram_key)
            self.subtitle_label.setText("(template not implemented yet)")
        else:
            self.title_label.setText(diagram.title)
            self.subtitle_label.setText(diagram.citation)
        self.update_plot()

    def _empty_canvas(self, message: str) -> None:
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center",
                color="#6c7388", fontsize=12, wrap=True)
        ax.axis("off")
        self.canvas.draw()

    # ----------------------------------------------------- compatibility
    def export_plot(self) -> None:
        from ._export_helpers import ask_export_path, save_figure
        path = ask_export_path(self)
        if path is None:
            return
        save_figure(self, self.canvas.figure, path)

    def edit_plot(self) -> None:
        QMessageBox.information(
            self, "Edit plot",
            "Per-group styling lives in Data → Edit plot."
        )

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        from .. import widget_state as ws
        return {
            "diagram_key": self._diagram_key or "",
            "axis": ws.axis_group_state(self.axis_grp),
            "legend": ws.legend_group_state(self.legend_grp),
            "grouping": ws.grouping_group_state(self.grouping_grp),
            "annotations": self.annotation_ctl.serialize(),
        }

    def restore(self, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
        key = state.get("diagram_key", "")
        if key:
            self.show_diagram(key)
        ws.restore_axis_group(self.axis_grp, state.get("axis"))
        ws.restore_legend_group(self.legend_grp, state.get("legend"))
        ws.restore_grouping_group(self.grouping_grp, state.get("grouping"))
        self.annotation_ctl.restore(state.get("annotations"))
