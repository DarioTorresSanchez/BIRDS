"""Tectonic discrimination diagrams view."""

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
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..composition import filter_by_composition, filter_by_rock_type
from ..diagrams.catalog import TECTONIC_PLUTONIC, TECTONIC_VOLCANIC
from ..diagrams.registry import get_diagram, has_diagram
from ..diagrams.templates.base import AxisStyle, PlotOptions
from .annotation_controller import AnnotationController, nearest_sample
from .plot_canvas import PlotCanvas
from .widgets import AxisGroup, GroupingGroup, LegendGroup


class TectonicView(QWidget):
    """Splitter UI for tectonic discrimination diagrams."""

    def __init__(self, data_manager, plot_style, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style
        self._family = "volcanic"
        self._composition = "Mafic"
        self._diagram_key: Optional[str] = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left controls --------------------------------------------------------
        controls = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._build_controls(controls)

        # Sticky Update button outside the scroll area
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

        # Right canvas --------------------------------------------------------
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

        self.annotation_ctl.bind_canvas(self.canvas)

        self.set_family_composition("volcanic", "Mafic")

    # ------------------------------------------------------------------ UI
    def _build_controls(self, parent: QWidget) -> None:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        sel_box = QGroupBox("Selection")
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
        self.family_label = QLabel("Volcanic")
        form.addRow("Rock family:", self.family_label)
        self.composition_combo = QComboBox()
        self.composition_combo.addItems(("Mafic", "Intermediate", "Acid"))
        self.composition_combo.currentIndexChanged.connect(
            self._on_composition_changed
        )
        form.addRow("Composition:", self.composition_combo)
        self.diagram_combo = QComboBox()
        self.diagram_combo.currentIndexChanged.connect(self._on_diagram_changed)
        form.addRow("Diagram:", self.diagram_combo)
        sel_layout.addLayout(form)
        layout.addWidget(sel_box)

        self.axis_grp = AxisGroup("Axes (labels and font)")
        self.axis_grp.log_x.setVisible(False)
        self.axis_grp.log_y.setVisible(False)
        layout.addWidget(self.axis_grp)
        self.legend_grp = LegendGroup()
        layout.addWidget(self.legend_grp)
        self.grouping_grp = GroupingGroup()
        # Faceting is less useful here; hide for simplicity
        self.grouping_grp.facet_chk.setVisible(False)
        layout.addWidget(self.grouping_grp)

        # ---- Composition filter ------------------------------------------
        # Verma multidim diagrams are each calibrated on a specific SiO2
        # range.  When the user opens one, we auto-filter the dataset to
        # the matching range so samples that don't belong don't pollute
        # the plot.  Toggleable; status label shows kept/dropped counts.
        self.composition_grp = QGroupBox("Composition filter")
        cg_layout = QVBoxLayout(self.composition_grp)
        cg_layout.setContentsMargins(8, 12, 8, 8)
        cg_layout.setSpacing(4)
        self.composition_filter_chk = QCheckBox(
            "Auto-filter samples by SiO₂ range"
        )
        self.composition_filter_chk.setChecked(True)
        self.composition_filter_chk.setStatusTip(
            "Each Verma multidim diagram is calibrated on a specific SiO₂ "
            "range (ultrabasic, basic, intermediate or acid).  When this "
            "is on, samples outside that range are hidden so they don't "
            "fall in arbitrary discriminant fields."
        )
        cg_layout.addWidget(self.composition_filter_chk)
        self.composition_status = QLabel(
            "Not active — current diagram has no SiO₂ filter."
        )
        self.composition_status.setStyleSheet(
            "color: #5b6478; font-size: 11px;"
        )
        self.composition_status.setWordWrap(True)
        cg_layout.addWidget(self.composition_status)
        self.composition_filter_chk.toggled.connect(self.update_plot)
        # Rock-type filter — when the user picked the Volcanic submenu we
        # also drop plutonic rows (and vice versa) so the plot matches
        # the menu context.
        self.rock_type_filter_chk = QCheckBox(
            "Auto-filter by Rock_Type (Volcanic / Plutonic)"
        )
        self.rock_type_filter_chk.setChecked(True)
        self.rock_type_filter_chk.setStatusTip(
            "When you open the Volcanic submenu, samples with "
            "Rock_Type = Plutonic are hidden, and vice versa. "
            "Samples with an empty Rock_Type are kept on both sides."
        )
        cg_layout.addWidget(self.rock_type_filter_chk)
        self.rock_type_status = QLabel("")
        self.rock_type_status.setStyleSheet(
            "color: #5b6478; font-size: 11px;"
        )
        self.rock_type_status.setWordWrap(True)
        cg_layout.addWidget(self.rock_type_status)
        self.rock_type_filter_chk.toggled.connect(self.update_plot)
        layout.addWidget(self.composition_grp)

        # Annotation toolkit
        self.annotation_ctl = AnnotationController(
            self, sample_resolver=self._resolve_sample)
        layout.addWidget(self.annotation_ctl.group)

        layout.addStretch(1)

    # ------------------------------------------------------------------ API
    def set_family_composition(self, family: str, composition: str) -> None:
        self._family = family
        self._composition = composition
        self.family_label.setText(family.capitalize())

        idx = self.composition_combo.findText(composition)
        self.composition_combo.blockSignals(True)
        self.composition_combo.setCurrentIndex(max(idx, 0))
        self.composition_combo.blockSignals(False)
        self._populate_diagrams()

    # Compat with the old API used by the menu
    def show_diagram(self, key: str, family: str, composition: str) -> None:
        self.set_family_composition(family, composition)
        i = self.diagram_combo.findData(key)
        if i >= 0:
            self.diagram_combo.setCurrentIndex(i)

    def update_plot(self) -> None:
        if not self._diagram_key:
            return
        diagram = get_diagram(self._diagram_key)
        if diagram is None:
            self._empty_canvas(
                f"Diagram template '{self._diagram_key}' not yet implemented."
            )
            return
        x_label = self.axis_grp.x_label_edit.text().strip() or None
        y_label = self.axis_grp.y_label_edit.text().strip() or None
        common = AxisStyle(
            font_size=self.axis_grp.font_size.value(),
            font_family=self.axis_grp.font_family.currentText(),
            font_weight="bold" if self.axis_grp.bold.isChecked() else "normal",
            font_style="italic" if self.axis_grp.italic.isChecked() else "normal",
        )
        options = PlotOptions(
            x_axis=AxisStyle(label=x_label, **{k: getattr(common, k)
                                                for k in ("font_size", "font_family",
                                                          "font_weight", "font_style")}),
            y_axis=AxisStyle(label=y_label, **{k: getattr(common, k)
                                                for k in ("font_size", "font_family",
                                                          "font_weight", "font_style")}),
            legend=self.legend_grp.legend_style(),
        )
        # Compositional pre-filter — only Verma multidim diagrams advertise
        # a composition_filter; everything else passes the dataframe
        # through untouched.
        df_to_plot = self._composition_filtered_df(diagram)
        try:
            diagram.plot(self.canvas.figure, df_to_plot, self.plot_style, options)
        except Exception as exc:  # noqa: BLE001
            self._empty_canvas(f"Plot error:\n{exc}")
            return
        # Replay annotations on the primary axis if any was created.
        if self.canvas.figure.axes:
            self.annotation_ctl.draw(self.canvas.figure.axes[0])
        from .brushing import draw_selection_overlay
        draw_selection_overlay(self)
        self._update_count_label(diagram, df_to_plot)
        self.canvas.draw()

    def _update_count_label(self, diagram, filtered_df) -> None:
        """Tally samples reaching the canvas.  Multi-panel Verma
        templates have no single (x, y) mapping, so for those the tally
        reports filter / visibility only."""
        from .sample_counts import count_for_diagram
        self.count_label.show_report(count_for_diagram(
            diagram, self.data.df, filtered_df, self.plot_style))

    def _selection_points(self, names):
        """Coordinates of the selected samples on the active single-axis
        diagram (multi-panel Verma templates are skipped)."""
        from .brushing import names_series
        diagram = get_diagram(self._diagram_key) if self._diagram_key else None
        if diagram is None:
            return []
        compute = getattr(diagram, "_compute_xy", None)
        if compute is None:
            return []
        df = self._composition_filtered_df(diagram)
        axes = self.canvas.figure.axes
        if df is None or df.empty or not axes:
            return []
        try:
            xs, ys = compute(df)
        except Exception:                                  # noqa: BLE001
            return []
        if xs is None or ys is None:
            return []
        nm = names_series(df)
        m = nm.isin(names) & xs.notna() & ys.notna()
        return [(axes[0], list(zip(xs[m], ys[m])))]

    def _resolve_sample(self, x: float, y: float):
        """Sample resolver — uses the active diagram's _compute_xy
        mapping.  Only works on single-panel diagrams; multi-panel
        diagrams (Verma multidim) silently return None."""
        df = self._composition_filtered_df(get_diagram(self._diagram_key)) \
            if self._diagram_key else self.data.df
        if df is None or df.empty:
            return None
        diagram = get_diagram(self._diagram_key) if self._diagram_key else None
        if diagram is None:
            return None
        compute = getattr(diagram, "_compute_xy", None)
        if compute is None:
            return None
        try:
            xs, ys = compute(df)
        except Exception:                                  # noqa: BLE001
            return None
        if xs is None or ys is None:
            return None
        axes = self.canvas.figure.axes
        if not axes:
            return None
        return nearest_sample(df, xs, ys, x, y,
                              axes[0].get_xlim(), axes[0].get_ylim())

    # ------------------------------------------------------------------ impl
    def _populate_diagrams(self) -> None:
        catalog = (TECTONIC_VOLCANIC if self._family == "volcanic"
                   else TECTONIC_PLUTONIC)
        entries = catalog.get(self._composition, [])

        self.diagram_combo.blockSignals(True)
        self.diagram_combo.clear()
        for label, key in entries:
            suffix = "" if has_diagram(key) else "  (coming soon)"
            self.diagram_combo.addItem(label + suffix, key)
        self.diagram_combo.blockSignals(False)
        if self.diagram_combo.count():
            self._on_diagram_changed(0)

    def _on_composition_changed(self, _index: int) -> None:
        self._composition = self.composition_combo.currentText()
        self._populate_diagrams()

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
            self.axis_grp.x_label_edit.setPlaceholderText(self._plain(diagram.x_label))
            self.axis_grp.y_label_edit.setPlaceholderText(self._plain(diagram.y_label))
        self.axis_grp.x_label_edit.setText("")
        self.axis_grp.y_label_edit.setText("")
        self.update_plot()

    @staticmethod
    def _plain(label: str) -> str:
        return (label
                .replace("$_2$", "2").replace("$_3$", "3")
                .replace("$_4$", "4").replace("$_T$", "T")
                .replace("$_{N-MORB}$", " (N-MORB)")
                .replace("$_", "").replace("$", ""))

    def _empty_canvas(self, message: str) -> None:
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center",
                color="#6c7388", fontsize=12, wrap=True)
        ax.axis("off")
        self.canvas.draw()
        # No points on the canvas — the previous tally no longer applies.
        self.count_label.clear_report()

    # ------------------------------------------------------------------
    # Composition pre-filter
    # ------------------------------------------------------------------
    def _composition_filtered_df(self, diagram):
        """Apply the diagram's compositional pre-filter (if any) and
        return the dataframe to plot.  Also updates the status label
        with kept/dropped counts and a hint about the SiO2 source."""
        df = self.data.df
        # First pass — rock-type filter (Volcanic / Plutonic).  Runs
        # before the SiO2 filter so the SiO2 counts reflect what was
        # already eligible.
        df = self._apply_rock_type_filter(df)
        target = getattr(diagram, "composition_filter", None)

        # No filter on this diagram → universal (UBIA, classification, …)
        if target is None:
            self.composition_status.setText(
                f"Not active — '{diagram.__class__.__name__}' has no "
                "SiO₂ filter."
            )
            return df

        # User turned it off → pass everything but tell them.
        if not self.composition_filter_chk.isChecked():
            self.composition_status.setText(
                f"<b>Filter disabled.</b> Target was: {target}.  "
                "Untick 'Auto-filter' above to ignore SiO₂ range."
            )
            self.composition_status.setTextFormat(Qt.TextFormat.RichText)
            return df

        if df is None or df.empty:
            self.composition_status.setText(
                "No dataset loaded.  Import via Data → Import."
            )
            return df

        filtered, info = filter_by_composition(df, target)
        src = info.get("sio2_source", "n/a")
        rng = info.get("range", "")
        if src == "missing":
            self.composition_status.setText(
                f"<b>Warning:</b> No SiO₂ column found "
                "(expected one of SiO2 / SiO2_adj).  Showing all samples."
            )
            self.composition_status.setTextFormat(Qt.TextFormat.RichText)
            return df
        src_label = ("SiO₂ (adjusted)" if src == "adj"
                     else "SiO₂ (raw — run Pre-process for better fit)")
        kept, dropped = info["kept"], info["dropped"]
        target_lbl = target.replace("+", " + ")
        # The SiO₂ range string contains literal '<' which Qt rich-text
        # would treat as a tag opener — escape it before injecting.
        rng_html = rng.replace("<", "&lt;").replace(">", "&gt;")
        self.composition_status.setText(
            f"<b>Filter:</b> {target_lbl} ({rng_html}) — "
            f"<b>{kept}</b> kept, <b>{dropped}</b> dropped.  "
            f"Using {src_label}."
        )
        self.composition_status.setTextFormat(Qt.TextFormat.RichText)
        return filtered

    def _apply_rock_type_filter(self, df):
        """Filter samples to the current submenu's family (volcanic /
        plutonic).  Updates the rock_type_status label."""
        if not self.rock_type_filter_chk.isChecked():
            self.rock_type_status.setText(
                "<b>Rock_Type filter disabled.</b> Showing all samples "
                "regardless of family."
            )
            self.rock_type_status.setTextFormat(Qt.TextFormat.RichText)
            return df
        if df is None or df.empty:
            self.rock_type_status.setText("")
            return df
        filtered, info = filter_by_rock_type(df, self._family)
        if info["source"] is None:
            self.rock_type_status.setText(
                f"<b>Rock_Type:</b> column not found — all samples shown."
            )
            self.rock_type_status.setTextFormat(Qt.TextFormat.RichText)
            return df
        kept, dropped, blank = info["kept"], info["dropped"], info["blank"]
        blank_note = (f" ({blank} blank kept)" if blank else "")
        self.rock_type_status.setText(
            f"<b>Rock_Type:</b> {self._family.capitalize()} — "
            f"<b>{kept}</b> kept, <b>{dropped}</b> dropped"
            f"{blank_note}.  Column: {info['source']}."
        )
        self.rock_type_status.setTextFormat(Qt.TextFormat.RichText)
        return filtered

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
            "family": self._family,
            "composition": self._composition,
            "diagram_key": self._diagram_key or "",
            "axis": ws.axis_group_state(self.axis_grp),
            "legend": ws.legend_group_state(self.legend_grp),
            "grouping": ws.grouping_group_state(self.grouping_grp),
            "comp_filter": ws.check_state(self.composition_filter_chk),
            "rock_filter": ws.check_state(self.rock_type_filter_chk),
            "annotations": self.annotation_ctl.serialize(),
        }

    def restore(self, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
        family = state.get("family", "volcanic")
        comp = state.get("composition", "Mafic")
        key = state.get("diagram_key", "")
        if family and key:
            self.show_diagram(key, family, comp)
        else:
            self.set_family_composition(family, comp)
        ws.restore_axis_group(self.axis_grp, state.get("axis"))
        ws.restore_legend_group(self.legend_grp, state.get("legend"))
        ws.restore_grouping_group(self.grouping_grp, state.get("grouping"))
        ws.restore_check(self.composition_filter_chk, state.get("comp_filter"))
        ws.restore_check(self.rock_type_filter_chk, state.get("rock_filter"))
        self.annotation_ctl.restore(state.get("annotations"))
