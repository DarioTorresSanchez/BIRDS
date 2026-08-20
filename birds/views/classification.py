"""Classification diagrams view with left controls and right plot canvas."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..composition import filter_by_rock_type
from ..diagrams.catalog import CLASSIFICATION_PLUTONIC, CLASSIFICATION_VOLCANIC
from ..diagrams.registry import get_diagram
from ..diagrams.templates.base import AxisStyle, LegendStyle, PlotOptions
from .annotation_controller import AnnotationController, nearest_sample
from .plot_canvas import PlotCanvas


_FONT_CHOICES = ["DejaVu Sans", "Arial", "Helvetica", "Times New Roman",
                 "Courier New"]
_LEGEND_LOCATIONS = ["best", "upper right", "upper left", "lower left",
                     "lower right", "center", "outside"]


class ClassificationView(QWidget):
    """Splitter UI: controls on the left, plot on the right."""

    def __init__(self, data_manager, plot_style, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style
        self._family = "volcanic"
        self._diagram_key: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ---- Left panel ----------------------------------------------------
        self._controls = QWidget()
        controls_scroll = QScrollArea()
        controls_scroll.setWidgetResizable(True)
        controls_scroll.setWidget(self._controls)
        controls_scroll.setFrameShape(QFrame.Shape.NoFrame)
        controls_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._build_controls()

        # Sticky Update button below the scroll
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
        left_layout.addWidget(controls_scroll, stretch=1)
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

        # ---- Right panel ---------------------------------------------------
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
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        right_layout.addWidget(sep)
        self.canvas = PlotCanvas()
        right_layout.addWidget(self.canvas, stretch=1)
        from .sample_counts import CountLabel
        self.count_label = CountLabel()
        right_layout.addWidget(self.count_label)
        splitter.addWidget(right)

        splitter.setSizes([460, 820])

        # Wire the annotation toolkit's click handler now that both the
        # AnnotationController and the canvas exist.
        self.annotation_ctl.bind_canvas(self.canvas)

        # Initialise with the volcanic catalogue
        self.set_family("volcanic")

    # ------------------------------------------------------------------ UI
    def _build_controls(self) -> None:
        layout = QVBoxLayout(self._controls)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        def _compact_form() -> QFormLayout:
            f = QFormLayout()
            f.setContentsMargins(0, 0, 0, 0)
            f.setHorizontalSpacing(8)
            f.setVerticalSpacing(4)
            f.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
            )
            return f

        # Diagram selector ---------------------------------------------------
        diag_box = QGroupBox("Diagram")
        diag_layout = QVBoxLayout(diag_box)
        diag_layout.setContentsMargins(8, 12, 8, 8)
        diag_layout.setSpacing(4)
        self.diagram_combo = QComboBox()
        self.diagram_combo.currentIndexChanged.connect(self._on_diagram_changed)
        diag_layout.addWidget(self.diagram_combo)
        layout.addWidget(diag_box)

        # Axes / fonts -------------------------------------------------------
        axes_box = QGroupBox("Axes (titles and font)")
        axes_layout = QVBoxLayout(axes_box)
        axes_layout.setContentsMargins(8, 12, 8, 8)
        axes_layout.setSpacing(4)
        axes_form = _compact_form()
        self.x_label_edit = QLineEdit()
        axes_form.addRow("X label:", self.x_label_edit)
        self.y_label_edit = QLineEdit()
        axes_form.addRow("Y label:", self.y_label_edit)
        self.axis_font_size = QSpinBox()
        self.axis_font_size.setRange(6, 32)
        self.axis_font_size.setValue(12)
        axes_form.addRow("Font size:", self.axis_font_size)
        self.axis_font_family = QComboBox()
        self.axis_font_family.addItems(_FONT_CHOICES)
        axes_form.addRow("Font family:", self.axis_font_family)
        style_row = QHBoxLayout()
        style_row.setSpacing(8)
        self.axis_bold = QCheckBox("Bold")
        self.axis_italic = QCheckBox("Italic")
        style_row.addWidget(self.axis_bold)
        style_row.addWidget(self.axis_italic)
        style_row.addStretch()
        axes_form.addRow("Style:", style_row)
        axes_layout.addLayout(axes_form)
        layout.addWidget(axes_box)

        # Legend -------------------------------------------------------------
        legend_box = QGroupBox("Legend")
        legend_layout = QVBoxLayout(legend_box)
        legend_layout.setContentsMargins(8, 12, 8, 8)
        legend_layout.setSpacing(4)
        legend_form = _compact_form()
        self.legend_visible = QCheckBox("Show legend")
        self.legend_visible.setChecked(True)
        legend_form.addRow("", self.legend_visible)
        self.legend_title_edit = QLineEdit()
        legend_form.addRow("Title:", self.legend_title_edit)
        self.legend_location = QComboBox()
        self.legend_location.addItems(_LEGEND_LOCATIONS)
        legend_form.addRow("Location:", self.legend_location)
        self.legend_font_size = QSpinBox()
        self.legend_font_size.setRange(6, 24)
        self.legend_font_size.setValue(10)
        legend_form.addRow("Font size:", self.legend_font_size)
        legend_layout.addLayout(legend_form)
        layout.addWidget(legend_box)

        # Grouping options — use the shared GroupingGroup widget so the
        # user gets per-group visibility checkboxes (+ facet) just like
        # in the Bivariate / Spider / Tectonic / Petrography views.
        from .widgets import GroupingGroup
        self.grouping_grp = GroupingGroup()
        # Backwards-compatibility alias — the rest of this view still
        # reads ``self.facet_chk`` directly.
        self.facet_chk = self.grouping_grp.facet_chk
        layout.addWidget(self.grouping_grp)

        # Rock-type filter — match the menu family (Volcanic / Plutonic)
        # against the Rock_Type column in the dataset.
        rock_box = QGroupBox("Rock-type filter")
        rl = QVBoxLayout(rock_box)
        rl.setContentsMargins(8, 12, 8, 8)
        rl.setSpacing(4)
        self.rock_type_filter_chk = QCheckBox(
            "Auto-filter by Rock_Type (Volcanic / Plutonic)"
        )
        self.rock_type_filter_chk.setChecked(True)
        self.rock_type_filter_chk.setStatusTip(
            "Hide samples whose Rock_Type doesn't match the current "
            "submenu (Volcanic ↔ Plutonic).  Empty Rock_Type is kept."
        )
        rl.addWidget(self.rock_type_filter_chk)
        self.rock_type_status = QLabel("")
        self.rock_type_status.setStyleSheet(
            "color: #5b6478; font-size: 11px;"
        )
        self.rock_type_status.setWordWrap(True)
        rl.addWidget(self.rock_type_status)
        self.rock_type_filter_chk.toggled.connect(self.update_plot)
        layout.addWidget(rock_box)

        # Annotation toolkit — applies to single-axis diagrams (TAS,
        # K2O-SiO2, AFM, Jensen, Frost, Hanski, …).  For ternary
        # classifications (Barker, Haplogranite) the click coordinates
        # are still data-space so lines / arrows work; sample identifier
        # uses the diagram's own _compute_xy mapping.
        self.annotation_ctl = AnnotationController(
            self, sample_resolver=self._resolve_sample)
        layout.addWidget(self.annotation_ctl.group)

        layout.addStretch(1)

    # ------------------------------------------------------------------ API
    def set_family(self, family: str) -> None:
        self._family = family
        entries = (
            CLASSIFICATION_VOLCANIC if family == "volcanic"
            else CLASSIFICATION_PLUTONIC
        )
        self.diagram_combo.blockSignals(True)
        self.diagram_combo.clear()
        for label, key in entries:
            self.diagram_combo.addItem(label, key)
        self.diagram_combo.blockSignals(False)
        if self.diagram_combo.count():
            self._on_diagram_changed(0)

    # Compat with old API: select a specific diagram key
    def show_diagram(self, key: str, family: str) -> None:
        self.set_family(family)
        idx = self.diagram_combo.findData(key)
        if idx >= 0:
            self.diagram_combo.setCurrentIndex(idx)

    def update_plot(self) -> None:
        # Every path that leaves the canvas without points must also drop
        # the tally, otherwise it keeps advertising the previous render.
        if not self._diagram_key:
            self.count_label.clear_report()
            return
        diagram = get_diagram(self._diagram_key)
        if diagram is None:
            self.canvas.figure.clear()
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5,
                    f"Template not yet implemented: {self._diagram_key}",
                    ha="center", va="center", color="#6c7388")
            ax.axis("off")
            self.canvas.draw()
            self.count_label.clear_report()
            return
        df = self._rock_type_filtered_df()
        try:
            diagram.plot(self.canvas.figure, df, self.plot_style,
                         self._gather_options())
        except Exception as exc:  # noqa: BLE001
            self.canvas.figure.clear()
            ax = self.canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, f"Plot error:\n{exc}", ha="center", va="center",
                    color="#b13a3a", fontsize=10, wrap=True)
            ax.axis("off")
        # Replay user annotations on the primary axis.
        if self.canvas.figure.axes:
            self.annotation_ctl.draw(self.canvas.figure.axes[0])
        from .brushing import draw_selection_overlay
        draw_selection_overlay(self)
        self._update_count_label(diagram, df)
        self.canvas.draw()

    def _update_count_label(self, diagram, filtered_df) -> None:
        """Tally how many samples actually reached the canvas.  Handles
        the multi-panel templates (Frost's 2×2 grid) transparently."""
        from .sample_counts import count_for_diagram
        self.count_label.show_report(count_for_diagram(
            diagram, self.data.df, filtered_df, self.plot_style))

    def _selection_points(self, names):
        """Plotted coordinates of the given sample names, for the
        cross-view selection overlay.  Single-axis diagrams only —
        multi-panel templates are silently skipped."""
        from .brushing import names_series
        diagram = get_diagram(self._diagram_key)
        if diagram is None or not hasattr(diagram, "_compute_xy"):
            return []
        df = self._rock_type_filtered_df()
        axes = self.canvas.figure.axes
        if df is None or df.empty or not axes:
            return []
        xs, ys = diagram._compute_xy(df)
        if xs is None or ys is None:
            return []
        nm = names_series(df)
        m = nm.isin(names) & xs.notna() & ys.notna()
        return [(axes[0], list(zip(xs[m], ys[m])))]

    def _resolve_sample(self, x: float, y: float):
        """Sample resolver for Identify-sample mode — uses the active
        diagram's own _compute_xy mapping so the click works on TAS,
        K2O-SiO2, AFM, Jensen, etc. without per-diagram code."""
        df = self.data.df
        if df is None or df.empty:
            return None
        diagram = get_diagram(self._diagram_key)
        if diagram is None:
            return None
        # Apply the same rock-type filter the plot uses so the user
        # doesn't accidentally label a sample that's hidden.
        filtered = self._rock_type_filtered_df()
        xs, ys = diagram._compute_xy(filtered)
        if xs is None or ys is None:
            return None
        axes = self.canvas.figure.axes
        if not axes:
            return None
        return nearest_sample(filtered, xs, ys, x, y,
                              axes[0].get_xlim(), axes[0].get_ylim())

    def _rock_type_filtered_df(self):
        """Drop samples that don't belong to the current family
        (volcanic / plutonic).  Toggleable via the checkbox."""
        df = self.data.df
        if not self.rock_type_filter_chk.isChecked():
            self.rock_type_status.setText(
                "<b>Filter disabled.</b> Showing all samples."
            )
            self.rock_type_status.setTextFormat(Qt.TextFormat.RichText)
            return df
        if df is None or df.empty:
            self.rock_type_status.setText("")
            return df
        filtered, info = filter_by_rock_type(df, self._family)
        if info["source"] is None:
            self.rock_type_status.setText(
                "<b>Rock_Type column not found</b> — showing all samples."
            )
            self.rock_type_status.setTextFormat(Qt.TextFormat.RichText)
            return df
        kept, dropped, blank = info["kept"], info["dropped"], info["blank"]
        blank_note = (f" ({blank} blank kept)" if blank else "")
        self.rock_type_status.setText(
            f"<b>{self._family.capitalize()}</b> samples — "
            f"<b>{kept}</b> kept, <b>{dropped}</b> dropped"
            f"{blank_note}.  Column: {info['source']}."
        )
        self.rock_type_status.setTextFormat(Qt.TextFormat.RichText)
        return filtered

    # ----------------------------------------------------------------- impl
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
            self.x_label_edit.setPlaceholderText(self._plain(diagram.x_label))
            self.y_label_edit.setPlaceholderText(self._plain(diagram.y_label))
        self.x_label_edit.setText("")
        self.y_label_edit.setText("")
        self.update_plot()

    @staticmethod
    def _plain(label: str) -> str:
        return (label
                .replace("$_2$", "2").replace("$_3$", "3").replace("$_4$", "4")
                .replace("$_T$", "T").replace("$_", "").replace("$", ""))

    def _gather_options(self) -> PlotOptions:
        weight = "bold" if self.axis_bold.isChecked() else "normal"
        style = "italic" if self.axis_italic.isChecked() else "normal"
        # If the user typed nothing we let the template fall back to its own
        # x_label/y_label rather than the prettified placeholder.
        x_label = self.x_label_edit.text().strip() or None
        y_label = self.y_label_edit.text().strip() or None

        axis_style = AxisStyle(
            font_size=self.axis_font_size.value(),
            font_family=self.axis_font_family.currentText(),
            font_weight=weight,
            font_style=style,
        )
        legend_style = LegendStyle(
            visible=self.legend_visible.isChecked(),
            location=self.legend_location.currentText(),
            font_size=self.legend_font_size.value(),
            title=self.legend_title_edit.text().strip() or None,
        )
        return PlotOptions(
            x_axis=AxisStyle(label=x_label, **{k: getattr(axis_style, k)
                                                for k in ("font_size", "font_family",
                                                          "font_weight", "font_style")}),
            y_axis=AxisStyle(label=y_label, **{k: getattr(axis_style, k)
                                                for k in ("font_size", "font_family",
                                                          "font_weight", "font_style")}),
            legend=legend_style,
            facet_by_group=self.facet_chk.isChecked(),
        )

    # The diagram view exposes export_plot/edit_plot via duck-typing on the
    # central widget. They are not necessary here because main_window uses the
    # canvas directly, but we keep them for backwards-compat.
    def export_plot(self) -> None:
        from ._export_helpers import ask_export_path, save_figure
        path = ask_export_path(self)
        if path is None:
            return
        save_figure(self, self.canvas.figure, path)

    def edit_plot(self) -> None:
        QMessageBox.information(
            self, "Edit plot",
            "Use the controls on the left to modify axis labels, legend and "
            "grouping. The global style is managed from Data → Edit plot."
        )

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        from .. import widget_state as ws
        return {
            "family": self._family,
            "diagram_key": self._diagram_key or "",
            "x_label": ws.edit_state(self.x_label_edit),
            "y_label": ws.edit_state(self.y_label_edit),
            "font_size": ws.spin_state(self.axis_font_size),
            "font_family": self.axis_font_family.currentText(),
            "bold": ws.check_state(self.axis_bold),
            "italic": ws.check_state(self.axis_italic),
            "legend_visible": ws.check_state(self.legend_visible),
            "legend_title": ws.edit_state(self.legend_title_edit),
            "legend_location": self.legend_location.currentText(),
            "legend_font_size": ws.spin_state(self.legend_font_size),
            "facet": ws.check_state(self.facet_chk),
            "rock_filter": ws.check_state(self.rock_type_filter_chk),
            "annotations": self.annotation_ctl.serialize(),
        }

    def restore(self, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
        family = state.get("family", "volcanic")
        key = state.get("diagram_key", "")
        if family and key:
            self.show_diagram(key, family)
        elif family:
            self.set_family(family)
        ws.restore_edit(self.x_label_edit, state.get("x_label"))
        ws.restore_edit(self.y_label_edit, state.get("y_label"))
        ws.restore_spin(self.axis_font_size, state.get("font_size"))
        ws.restore_combo(self.axis_font_family,
                         {"text": state.get("font_family", "")})
        ws.restore_check(self.axis_bold, state.get("bold"))
        ws.restore_check(self.axis_italic, state.get("italic"))
        ws.restore_check(self.legend_visible, state.get("legend_visible"))
        ws.restore_edit(self.legend_title_edit, state.get("legend_title"))
        ws.restore_combo(self.legend_location,
                         {"text": state.get("legend_location", "")})
        ws.restore_spin(self.legend_font_size, state.get("legend_font_size"))
        ws.restore_check(self.facet_chk, state.get("facet"))
        ws.restore_check(self.rock_type_filter_chk, state.get("rock_filter"))
        self.annotation_ctl.restore(state.get("annotations"))
