"""Spider diagrams view — REE (chondrite / shale) and multi-element."""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
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
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..diagrams.templates.base import get_groups, resolve_column
from ..normalizations import (
    MULTIELEMENT_NORMS,
    MULTIELEMENT_ORDER,
    OXIDE_TO_ELEMENT_PPM,
    REE_CHONDRITES,
    REE_ORDER,
    REE_ORDER_WITH_Y,
    REE_SHALES,
    get_normaliser,
)
from ..reservoirs import get_reservoir_value
from .annotation_controller import AnnotationController
from .plot_canvas import PlotCanvas
from .widgets import AxisGroup, GroupingGroup, LegendGroup, ReservoirGroup


# ---------------------------------------------------------------------------
# Element value lookup (auto oxide→ppm conversion for K / Ti / P / …)
# ---------------------------------------------------------------------------

def _element_series(df: pd.DataFrame, element: str) -> Optional[pd.Series]:
    """Return a numeric Series of *element* values in ppm.

    Tries direct column first, falls back to the corresponding oxide
    (auto-converted to ppm) for major elements.
    """
    col = resolve_column(df, [element])
    if col is not None:
        return pd.to_numeric(df[col], errors="coerce")
    if element in OXIDE_TO_ELEMENT_PPM:
        oxide, factor = OXIDE_TO_ELEMENT_PPM[element]
        oxide_col = resolve_column(df, [oxide])
        if oxide_col is not None:
            return pd.to_numeric(df[oxide_col], errors="coerce") * factor
    return None


# ---------------------------------------------------------------------------
# Controls (shared between REE and Multi-element modes)
# ---------------------------------------------------------------------------

class _SpiderControls(QWidget):
    """Left-panel controls for the spider view."""

    def __init__(self, mode: str) -> None:
        super().__init__()
        self.mode = mode

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── Normalisation ───────────────────────────────────────────────
        norm_tooltip = (
            "Pick a published reference composition. Sample values are "
            "divided by the corresponding element value in the reference."
        )
        norm_box = QGroupBox("Normalisation reference")
        norm_box.setToolTip(norm_tooltip)
        norm_layout = QVBoxLayout(norm_box)
        norm_layout.setContentsMargins(8, 12, 8, 8)
        norm_layout.setSpacing(4)
        self.norm_combo = QComboBox()
        self.norm_combo.setToolTip(norm_tooltip)
        norm_layout.addWidget(self.norm_combo)

        # REE-only options
        if mode == "ree":
            self.include_y_chk = QCheckBox(
                "Include Y in the pattern (between Dy and Ho)"
            )
            norm_layout.addWidget(self.include_y_chk)
        else:
            self.include_y_chk = None

        layout.addWidget(norm_box)

        # ── Elements (multi-element mode only) ─────────────────────────
        # Lets the user pick which trace elements appear on the x-axis,
        # like the R Shiny version did.  Built lazily — the items are
        # populated from MULTIELEMENT_ORDER on first show, and items
        # whose values are missing from the loaded dataset are greyed
        # out by ``SpiderView._refresh_elements_list``.
        if mode != "ree":
            # Multi-element (a.k.a. "multielement") mode.
            from ..normalizations import MULTIELEMENT_ORDER
            elem_tooltip = (
                "Tick the trace elements to include on the spider diagram. "
                "Greyed-out elements are absent from the current dataset "
                "or from the chosen normaliser."
            )
            elem_box = QGroupBox("Elements to plot")
            elem_box.setToolTip(elem_tooltip)
            elem_v = QVBoxLayout(elem_box)
            elem_v.setContentsMargins(8, 12, 8, 8)
            elem_v.setSpacing(4)
            # All / None shortcut row
            row = QHBoxLayout()
            row.setSpacing(6)
            self.elem_all_btn = QPushButton("All")
            self.elem_all_btn.setMaximumWidth(50)
            self.elem_none_btn = QPushButton("None")
            self.elem_none_btn.setMaximumWidth(50)
            row.addWidget(self.elem_all_btn)
            row.addWidget(self.elem_none_btn)
            row.addStretch(1)
            elem_v.addLayout(row)
            # The list itself — small icon-less items in the canonical
            # Sun & McDonough (1989) order.  All ticked by default.
            self.elements_list = QListWidget()
            self.elements_list.setMaximumHeight(180)
            self.elements_list.setToolTip(elem_tooltip)
            for el in MULTIELEMENT_ORDER:
                item = QListWidgetItem(el)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                self.elements_list.addItem(item)
            elem_v.addWidget(self.elements_list)
            layout.addWidget(elem_box)

            # Wire shortcut buttons
            self.elem_all_btn.clicked.connect(
                lambda: self._set_all_elements(True))
            self.elem_none_btn.clicked.connect(
                lambda: self._set_all_elements(False))
        else:
            self.elements_list = None
            self.elem_all_btn = None
            self.elem_none_btn = None

        # ── Plot mode ──────────────────────────────────────────────────
        plot_box = QGroupBox("Plot mode")
        plot_layout = QVBoxLayout(plot_box)
        plot_layout.setContentsMargins(8, 12, 8, 8)
        plot_layout.setSpacing(4)
        self.mode_individual = QRadioButton("Individual sample lines")
        self.mode_individual.setChecked(True)
        self.mode_summary = QRadioButton(
            "Group summary (median + min–max envelope)"
        )
        plot_layout.addWidget(self.mode_individual)
        plot_layout.addWidget(self.mode_summary)
        # When a sample is missing one of the pattern elements the
        # default matplotlib behaviour is to leave a gap in the polyline.
        # Tick this to skip the missing element and draw a single
        # continuous line through whatever data the sample does carry.
        self.connect_chk = QCheckBox(
            "Connect across missing elements (no breaks)"
        )
        self.connect_chk.setToolTip(
            "Untick to keep the visible gap at every element a sample "
            "doesn't have a value for; tick to bridge over them so the "
            "polyline reads as a single connected pattern."
        )
        plot_layout.addWidget(self.connect_chk)

        # Envelope statistic — applies to every group whose 'shaded'
        # flag is on (Data → Edit plot).  Min–max shows the full spread;
        # the percentile bands trim outliers for publication figures.
        env_row = QHBoxLayout()
        env_row.setSpacing(6)
        env_row.addWidget(QLabel("Envelope band:"))
        self.envelope_combo = QComboBox()
        self.envelope_combo.addItem("Min – Max", "minmax")
        self.envelope_combo.addItem("P10 – P90", "p10p90")
        self.envelope_combo.addItem("P25 – P75", "p25p75")
        self.envelope_combo.setToolTip(
            "Statistic for the shaded group envelope (enable per group "
            "with the 'shaded' flag in Data → Edit plot)."
        )
        env_row.addWidget(self.envelope_combo, stretch=1)
        plot_layout.addLayout(env_row)
        layout.addWidget(plot_box)

        # ── Axes / fonts ───────────────────────────────────────────────
        self.axis_grp = AxisGroup("Axes (labels and font)")
        # Spider plots are linear in X (element index) but typically log in Y
        self.axis_grp.log_y.setChecked(True)
        # Hide log-X (it would not be meaningful for a categorical x-axis)
        self.axis_grp.log_x.setVisible(False)
        layout.addWidget(self.axis_grp)

        # ── Legend ─────────────────────────────────────────────────────
        self.legend_grp = LegendGroup()
        layout.addWidget(self.legend_grp)

        # ── Grouping ───────────────────────────────────────────────────
        self.grouping_grp = GroupingGroup()
        # Faceting is not used for spider; hide that checkbox
        self.grouping_grp.facet_chk.setVisible(False)
        layout.addWidget(self.grouping_grp)

        # ── Reservoir overlays ─────────────────────────────────────────
        self.reservoirs_grp = ReservoirGroup(
            "Reservoir patterns (overlay reference lines)"
        )
        # Cap the tree so the outer panel does not need a second scroll.
        self.reservoirs_grp.tree.setMaximumHeight(220)
        layout.addWidget(self.reservoirs_grp)

        layout.addStretch(1)

    # ------------------------------------------------------------------
    # Helpers for the multi-element element selector
    # ------------------------------------------------------------------
    def _set_all_elements(self, on: bool) -> None:
        """Bulk-toggle every element in the multi-element list."""
        if self.elements_list is None:
            return
        state = Qt.CheckState.Checked if on else Qt.CheckState.Unchecked
        for i in range(self.elements_list.count()):
            self.elements_list.item(i).setCheckState(state)

    def selected_elements(self) -> Optional[list[str]]:
        """Return the names of TICKED items in the multi-element list,
        or ``None`` for the REE mode (which has no list)."""
        if self.elements_list is None:
            return None
        return [
            self.elements_list.item(i).text()
            for i in range(self.elements_list.count())
            if self.elements_list.item(i).checkState() == Qt.CheckState.Checked
        ]


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------

class SpiderView(QWidget):
    """Spider diagrams view — REE and multi-element sub-modes."""

    def __init__(self, data_manager, plot_style, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style
        self._mode = "ree"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter)

        # Left panel (built lazily per mode)
        self._controls: dict[str, _SpiderControls] = {}
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Sticky Update button shared across both modes
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
        left_layout.addWidget(self._scroll, stretch=1)
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

        # Right panel
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(6)
        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-size: 16px; font-weight: 600;")
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

        # One AnnotationController per mode — REE and multi-element have
        # different x-axes (14 vs 29 elements), so annotations placed in
        # one mode would land on the wrong element in the other.
        self._annotation_ctls: dict[str, AnnotationController] = {}
        # Cache the current run's (sample, value) lookup table so the
        # sample identifier resolver knows what's on the plot.
        self._plot_index: list = []
        # Bind the canvas once; dispatch routes the click to the active
        # mode's controller.
        self.canvas.mpl_connect("button_press_event", self._dispatch_click)

        # Initialise mode
        self.set_mode("ree")

    # ------------------------------------------------------------------ API
    def set_mode(self, mode: str) -> None:
        self._mode = mode
        if mode not in self._controls:
            ctrl = _SpiderControls(mode)
            # Update button now lives outside the scroll area and is
            # wired in __init__; per-control widgets still trigger
            # auto-refresh on change.
            ctrl.norm_combo.currentIndexChanged.connect(self.update_plot)
            ctrl.mode_individual.toggled.connect(self.update_plot)
            ctrl.mode_summary.toggled.connect(self.update_plot)
            ctrl.connect_chk.toggled.connect(self.update_plot)
            ctrl.envelope_combo.currentIndexChanged.connect(self.update_plot)
            if ctrl.include_y_chk is not None:
                ctrl.include_y_chk.toggled.connect(self.update_plot)
            # Multi-element mode: toggling an element re-renders.
            if ctrl.elements_list is not None:
                ctrl.elements_list.itemChanged.connect(
                    lambda _item: self.update_plot()
                )
            # Per-group visibility toggles must trigger update_plot too.
            # MainWindow._wire_grouping_groups only runs at startup, so a
            # mode-switch-time control would otherwise have a dead
            # GroupingGroup until the next Edit plot.  Wire it here.
            ctrl.grouping_grp.set_groups(self.plot_style)
            ctrl.grouping_grp.visibility_changed.connect(self.update_plot)
            # Reservoir style editor — fires when the user changes any
            # colour / linestyle / linewidth / marker on a checked
            # reservoir's inline row.
            ctrl.reservoirs_grp.styles_changed.connect(self.update_plot)
            # Annotation toolkit — own controller per mode.  We don't
            # call .bind_canvas here; dispatch_click does the routing
            # so canvas-level events are exclusive to the active mode.
            ann_ctl = AnnotationController(
                self, sample_resolver=self._resolve_sample,
                redraw_method="update_plot",
            )
            self._annotation_ctls[mode] = ann_ctl
            ctrl_layout = ctrl.layout()
            if ctrl_layout is not None:
                # Insert the annotation widget just before the trailing
                # stretch (the controls panel ends with addStretch(1)).
                ctrl_layout.insertWidget(ctrl_layout.count() - 1,
                                          ann_ctl.group)
            self._populate_norm_combo(ctrl, mode)
            self._controls[mode] = ctrl

        # Release the current scroll-area widget before swapping it.
        # ``QScrollArea.setWidget`` would otherwise *delete* the previous
        # widget on the C++ side, leaving the Python references in
        # ``self._controls`` pointing at zombies and raising
        # ``RuntimeError: Internal C++ object already deleted`` the next
        # time the user comes back to that mode.
        previous = self._scroll.takeWidget()
        if previous is not None:
            previous.setParent(None)
        # Re-sync the grouping checkboxes from the shared PlotStyle so any
        # visibility toggle the user made in the OTHER mode is reflected
        # here when they return.  Cheap — set_groups rebuilds the list
        # from scratch.
        self._controls[mode].grouping_grp.set_groups(self.plot_style)
        self._scroll.setWidget(self._controls[mode])
        if mode == "ree":
            self.title_label.setText("REE spider diagram — chondrite / shale normalised")
            self.subtitle_label.setText(
                "Lanthanides La → Lu plotted in atomic-number order. "
                "Pick a chondrite (igneous) or shale composite (sedimentary) "
                "reference on the left."
            )
        else:
            self.title_label.setText("Multi-element diagram")
            self.subtitle_label.setText(
                "Incompatible elements ordered after Sun & McDonough (1989) "
                "/ Rollinson & Pease (2021) Table 4.9. Major elements K, Ti "
                "and P are auto-converted from wt.% oxide to ppm element."
            )
        self.update_plot()

    # ---------------------------------------------------------------- impl
    @staticmethod
    def _populate_norm_combo(ctrl: _SpiderControls, mode: str) -> None:
        ctrl.norm_combo.blockSignals(True)
        ctrl.norm_combo.clear()
        from ..normalizations import CHALCOPHILE_NORMS

        def _header(text: str) -> None:
            ctrl.norm_combo.addItem(text, None)
            ctrl.norm_combo.model().item(
                ctrl.norm_combo.count() - 1).setEnabled(False)

        if mode == "ree":
            _header("— REE chondrite —")
            for name in REE_CHONDRITES:
                ctrl.norm_combo.addItem(name, name)
            _header("— REE shale / crustal composite —")
            for name in REE_SHALES:
                ctrl.norm_combo.addItem(name, name)
            # Ni-Cu-PGE references are offered in both modes: a sulphide
            # study normally wants the metal plot next to the REE one,
            # and hunting for it in another tab helps nobody.
            _header("— Ni-Cu-PGE metals —")
            for name in CHALCOPHILE_NORMS:
                ctrl.norm_combo.addItem(name, name)
            # Default: Sun & McDonough 1989
            ctrl.norm_combo.setCurrentIndex(1)
        else:
            _header("— Multi-element —")
            for name in MULTIELEMENT_NORMS:
                ctrl.norm_combo.addItem(name, name)
            _header("— Ni-Cu-PGE metals —")
            for name in CHALCOPHILE_NORMS:
                ctrl.norm_combo.addItem(name, name)
            ctrl.norm_combo.setCurrentIndex(1)
        ctrl.norm_combo.blockSignals(False)

    def _empty_canvas(self, message: str) -> None:
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center",
                color="#6c7388", fontsize=12, wrap=True)
        ax.axis("off")
        self.canvas.draw()
        # No spidergram drawn — drop the tally from the previous render.
        self.count_label.clear_report()

    def update_plot(self) -> None:
        if self.data.df is None or self.data.df.empty:
            self._empty_canvas(
                "Load a dataset via Data → Import to start plotting."
            )
            return
        ctrl = self._controls.get(self._mode)
        if ctrl is None:
            return

        norm_name = ctrl.norm_combo.currentData()
        if not norm_name:
            self._empty_canvas("Pick a normalisation reference on the left.")
            return
        norm_values = get_normaliser(norm_name)
        if norm_values is None:
            self._empty_canvas(f"Reference '{norm_name}' not found.")
            return

        # Element order.  A Ni-Cu-PGE reference brings its own x-axis —
        # metals ordered by compatibility with sulphide liquid — which
        # overrides both the REE and the incompatibility orders.
        from ..normalizations import chalcophile_order, is_chalcophile_normaliser
        if is_chalcophile_normaliser(norm_name):
            order = chalcophile_order(norm_name)
        elif self._mode == "ree":
            include_y = bool(ctrl.include_y_chk and ctrl.include_y_chk.isChecked())
            order = REE_ORDER_WITH_Y if include_y else REE_ORDER
        else:
            # Multi-element: respect the user's per-element checkboxes
            # while keeping the canonical Sun & McDonough ordering.
            user_selection = ctrl.selected_elements()
            if user_selection is None:
                order = MULTIELEMENT_ORDER
            else:
                selected = set(user_selection)
                order = [el for el in MULTIELEMENT_ORDER if el in selected]
                if not order:
                    self._empty_canvas(
                        "All elements have been unticked. Tick at least "
                        "one in 'Elements to plot' on the left."
                    )
                    return

        # Resolve which elements are actually present (data + normaliser)
        df = self.data.df
        available: list[tuple[str, pd.Series]] = []
        for el in order:
            if el not in norm_values:
                continue
            series = _element_series(df, el)
            if series is None or series.dropna().empty:
                continue
            available.append((el, series))

        if not available:
            self._empty_canvas(
                "None of the reference elements were found in the dataset. "
                "Check that column names match standard element symbols "
                "(La, Ce, Nd, … or SiO2/K2O for major elements)."
            )
            return

        elements = [el for el, _ in available]
        x_pos = np.arange(len(elements))

        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)

        # Reset the (sample, element) lookup table used by the sample-
        # identifier annotation tool.  Populated as samples are drawn.
        self._plot_index = []

        summary = ctrl.mode_summary.isChecked()
        # When ``connect_chk`` is on, NaN values are dropped from each
        # polyline so matplotlib draws a single continuous line through
        # the available elements. Off (default) keeps the gap so missing
        # values stay visually obvious.
        connect_breaks = ctrl.connect_chk.isChecked()
        groups_data = get_groups(df, self.plot_style)
        legend_style = ctrl.legend_grp.legend_style()

        for label, sub, gs in groups_data:
            # Master visibility switch — Grouping checkbox in the side
            # panel flips this.  When off, the group is dropped entirely.
            if gs is not None and not getattr(gs, "visible", True):
                continue
            color = gs.color if gs else "#1f77b4"
            marker = gs.marker if gs else "o"
            # Per-group flags — see GroupStyle docstring for the 4 modes.
            show_markers = getattr(gs, "show_markers", True) if gs else True
            shaded = getattr(gs, "shaded", False) if gs else False
            if not show_markers and not shaded:
                # No symbols and no envelope ⇒ this group is invisible.
                continue

            # Build n_samples × n_elements matrix of normalised values
            rows: list[list[float]] = []
            sample_labels: list[str] = []  # parallel to rows
            for _, sample in sub.iterrows():
                vals: list[float] = []
                for el, series in available:
                    v = series.loc[sample.name] if sample.name in series.index else np.nan
                    if pd.isna(v):
                        vals.append(np.nan)
                    else:
                        vals.append(float(v) / norm_values[el])
                rows.append(vals)
                # Resolve a human-readable sample name for the identifier
                # tool — prefer Sample_Name, then Sample_Label, then index.
                lbl = None
                for col in ("Sample_Name", "Sample_Label", "Sample", "No.", "id"):
                    if col in df.columns:
                        v = df.at[sample.name, col] if sample.name in df.index else None
                        if v is not None and pd.notna(v):
                            lbl = str(v)
                            break
                sample_labels.append(lbl or str(sample.name))
            if not rows:
                continue
            matrix = np.array(rows, dtype=float)
            # Feed the sample-identifier lookup: every finite point on
            # the canvas becomes a (x_pos, y_val, label) entry.
            for r, lbl in zip(matrix, sample_labels):
                for col_i, val in enumerate(r):
                    if np.isfinite(val) and col_i < len(x_pos):
                        self._plot_index.append(
                            (float(x_pos[col_i]), float(val), lbl))

            # The group envelope band across samples — statistic chosen
            # in the 'Envelope band' combo: full min-max spread or a
            # percentile band that trims outliers.  When markers are off
            # the envelope inherits the legend label so the group still
            # shows up in the legend.
            env_mode = ctrl.envelope_combo.currentData() or "minmax"
            with np.errstate(all="ignore"):
                if env_mode == "p10p90":
                    lo = np.nanpercentile(matrix, 10, axis=0)
                    hi = np.nanpercentile(matrix, 90, axis=0)
                elif env_mode == "p25p75":
                    lo = np.nanpercentile(matrix, 25, axis=0)
                    hi = np.nanpercentile(matrix, 75, axis=0)
                else:
                    lo = np.nanmin(matrix, axis=0)
                    hi = np.nanmax(matrix, axis=0)
            envelope_valid = ~np.isnan(lo) & ~np.isnan(hi)
            fill_label = label if (shaded and not show_markers) else None
            envelope_alpha = 0.20 if not show_markers else 0.15

            if shaded and envelope_valid.any():
                ax.fill_between(x_pos[envelope_valid],
                                lo[envelope_valid], hi[envelope_valid],
                                color=color, alpha=envelope_alpha,
                                label=fill_label, zorder=2)

            if not show_markers:
                # No per-sample / median line — the envelope (if any)
                # already carries the visual for this group.
                continue

            if summary:
                median = np.nanmedian(matrix, axis=0)
                if connect_breaks:
                    valid = ~np.isnan(median)
                    xs, ys = x_pos[valid], median[valid]
                else:
                    xs, ys = x_pos, median
                ax.plot(xs, ys, color=color, marker=marker,
                        linewidth=2.0, markersize=self.plot_style.point_size,
                        alpha=min(self.plot_style.alpha + 0.1, 1.0),
                        label=label, zorder=4)
            else:
                first = True
                for sample_vals in matrix:
                    if np.all(np.isnan(sample_vals)):
                        continue
                    if connect_breaks:
                        valid = ~np.isnan(sample_vals)
                        xs, ys = x_pos[valid], sample_vals[valid]
                    else:
                        xs, ys = x_pos, sample_vals
                    ax.plot(xs, ys, color=color, marker=marker,
                            linewidth=1.0,
                            markersize=self.plot_style.point_size,
                            alpha=self.plot_style.alpha,
                            label=label if first else None,
                            zorder=3)
                    first = False

        # Reservoir overlays (reference patterns) — per-reservoir styling
        # comes from the inline editor in ReservoirGroup; user can change
        # colour, line style, width and marker on the fly.
        reservoir_names = ctrl.reservoirs_grp.selected_reservoirs()
        for i, res_name in enumerate(reservoir_names):
            res_vals = []
            for el in elements:
                v = get_reservoir_value(res_name, el)
                if v is None or el not in norm_values:
                    res_vals.append(np.nan)
                else:
                    res_vals.append(float(v) / norm_values[el])
            if all(np.isnan(v) for v in res_vals):
                continue
            short = res_name.split(" (")[0]
            style = ctrl.reservoirs_grp.style_for(res_name, index=i)
            marker = style.get("marker") or None  # "" → None
            ax.plot(x_pos, res_vals,
                    color=style["color"],
                    linestyle=style["linestyle"],
                    linewidth=style["linewidth"],
                    marker=marker,
                    markersize=6.5 if marker else 0,
                    label=short, zorder=5)

        # Axes decoration
        ax.set_xticks(x_pos)
        ax.set_xticklabels(elements,
                           fontsize=ctrl.axis_grp.font_size.value(),
                           rotation=45 if len(elements) > 18 else 0,
                           ha="right" if len(elements) > 18 else "center")
        y_label = ctrl.axis_grp.y_label_edit.text().strip()
        if not y_label:
            y_label = f"Sample / {norm_name}"
        x_label = ctrl.axis_grp.x_label_edit.text().strip()
        if x_label:
            ax.set_xlabel(x_label, **ctrl.axis_grp.axis_style(x_label).label_kwargs())
        ax.set_ylabel(y_label, **ctrl.axis_grp.axis_style(y_label).label_kwargs())
        if ctrl.axis_grp.log_y.isChecked():
            ax.set_yscale("log")
        ax.grid(True, axis="both", which="major", linewidth=0.5,
                color="#d4d8e1", alpha=0.7, zorder=0)
        ax.grid(True, axis="y", which="minor", linewidth=0.4,
                color="#e6e9f0", alpha=0.6, zorder=0)

        # Legend
        if legend_style.visible:
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                kwargs = {"fontsize": legend_style.font_size}
                if legend_style.title:
                    kwargs["title"] = legend_style.title
                if legend_style.location == "outside":
                    kwargs.update(loc="upper left",
                                  bbox_to_anchor=(1.02, 1.0))
                else:
                    kwargs["loc"] = legend_style.location
                ax.legend(**kwargs)

        fig.tight_layout()
        # Replay user annotations on the primary axis if one exists.
        ann_ctl = self._annotation_ctls.get(self._mode)
        if ann_ctl is not None and fig.axes:
            ann_ctl.draw(fig.axes[0])
        from .brushing import draw_selection_overlay
        draw_selection_overlay(self)
        self._update_count_label(df, elements, available)
        self.canvas.draw()

    def _update_count_label(self, df, elements, available) -> None:
        """Tally samples on the spider.  A sample counts as plotted when
        it has at least ONE finite normalised value — a pattern with
        gaps is still a pattern — and as missing-data when it has none
        of the plotted elements."""
        from .sample_counts import CountReport
        rep = CountReport(total=len(df) if df is not None else 0)
        if df is None or df.empty or not available:
            self.count_label.show_report(rep)
            return
        # Which rows belong to a visible group?
        visible = set()
        for _label, sub, gs in get_groups(df, self.plot_style):
            if gs is None or getattr(gs, "visible", True):
                visible.update(sub.index)
        rep.hidden = rep.total - len(visible)
        plotted = 0
        for idx in visible:
            for _el, series in available:
                if idx in series.index and pd.notna(series.loc[idx]):
                    plotted += 1
                    break
        rep.plotted = plotted
        rep.missing = len(visible) - plotted
        self.count_label.show_report(rep)

    def _selection_points(self, names):
        """Every (sample, element) point of the selected samples —
        rings the full pattern of a selected sample, straight from the
        ``_plot_index`` cache that update_plot just filled."""
        fig = self.canvas.figure
        if not self._plot_index or not fig.axes:
            return []
        pts = [(px, py) for px, py, label in self._plot_index
               if label in names]
        return [(fig.axes[0], pts)]

    # ------------------------------------------------------------------
    # Annotation routing — one controller per mode (REE / multi-element)
    # ------------------------------------------------------------------
    def _dispatch_click(self, event) -> None:
        """Route the canvas click to whichever mode's controller is
        currently active.  REE and multi-element share the canvas but
        keep separate annotation lists."""
        ctl = self._annotation_ctls.get(self._mode)
        if ctl is not None:
            ctl._on_click(event)

    def _resolve_sample(self, x: float, y: float):
        """Sample identifier — finds the (sample, element) point closest
        to the click using the cached ``self._plot_index`` populated by
        update_plot.  The label is the sample's name (from Sample_Name
        or Sample_Label)."""
        index = self._plot_index
        if not index:
            return None
        # Spider plots are linear-x / log-y.  Compute distances in the
        # axes' display units so a click near a low-Y sample isn't
        # swallowed by the log span of higher-Y samples.
        fig = self.canvas.figure
        if not fig.axes:
            return None
        ax = fig.axes[0]
        xlim = ax.get_xlim()
        log_y = ax.get_yscale() == "log"
        ylim = ax.get_ylim()
        if log_y and ylim[0] > 0:
            sy = max(abs(np.log10(ylim[1]) - np.log10(ylim[0])), 1e-9)
            ref_y = np.log10(y) if y > 0 else float("nan")
        else:
            sy = max(abs(ylim[1] - ylim[0]), 1e-9)
            ref_y = y
        sx = max(abs(xlim[1] - xlim[0]), 1e-9)

        best = None
        best_d = float("inf")
        for px, py, label in index:
            if log_y and py > 0:
                dy = (np.log10(py) - ref_y) / sy
            else:
                dy = (py - ref_y) / sy
            dx = (px - x) / sx
            d = float(np.hypot(dx, dy))
            if d < best_d:
                best_d = d
                best = (px, py, label)
        return best

    # ---------------------------------------------------------- compatibility
    def export_plot(self) -> None:
        from ._export_helpers import ask_export_path, save_figure
        path = ask_export_path(self)
        if path is None:
            return
        save_figure(self, self.canvas.figure, path)

    def edit_plot(self) -> None:
        QMessageBox.information(
            self, "Edit plot",
            "Per-group styling lives in Data → Edit plot. Use the panel on "
            "the left to change normalisation, fonts, legend and reservoirs."
        )

    # ------------------------------------------------------------------
    # Session persistence — serialise BOTH modes (ree + multi) plus the
    # currently active one.  Each mode's _SpiderControls is built lazily,
    # so we instantiate any that are missing before reading their state.
    # ------------------------------------------------------------------
    def _serialise_controls(self, ctrl) -> dict:
        from .. import widget_state as ws
        out = {
            "normaliser": ctrl.norm_combo.currentText(),
            "mode_individual": ws.check_state(ctrl.mode_individual),
            "mode_summary": ws.check_state(ctrl.mode_summary),
            "connect": ws.check_state(ctrl.connect_chk),
            "envelope": ctrl.envelope_combo.currentData(),
            "axis": ws.axis_group_state(ctrl.axis_grp),
            "legend": ws.legend_group_state(ctrl.legend_grp),
            "grouping": ws.grouping_group_state(ctrl.grouping_grp),
            "reservoirs": ws.reservoirs_state(ctrl.reservoirs_grp),
            # Per-reservoir style overrides (colour, linestyle, linewidth,
            # marker) so the user's customised look survives a session
            # save / restore.
            "reservoir_styles": ctrl.reservoirs_grp.all_styles(),
        }
        # Annotation state for this mode (REE and multi-element keep
        # separate lists since the x-axis differs).
        mode = next((m for m, c in self._controls.items() if c is ctrl), None)
        ann_ctl = self._annotation_ctls.get(mode) if mode else None
        if ann_ctl is not None:
            out["annotations"] = ann_ctl.serialize()
        if ctrl.include_y_chk is not None:
            out["include_y"] = ws.check_state(ctrl.include_y_chk)
        # Multi-element selection — preserve which elements the user
        # ticked on the "Elements to plot" list.
        if ctrl.elements_list is not None:
            out["selected_elements"] = ctrl.selected_elements()
        return out

    def _restore_controls(self, ctrl, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
        ws.restore_combo(ctrl.norm_combo,
                         {"text": state.get("normaliser", "")})
        if state.get("mode_summary"):
            ctrl.mode_summary.setChecked(True)
        elif state.get("mode_individual"):
            ctrl.mode_individual.setChecked(True)
        ws.restore_check(ctrl.connect_chk, state.get("connect"))
        env = state.get("envelope")
        if env:
            idx = ctrl.envelope_combo.findData(env)
            if idx >= 0:
                ctrl.envelope_combo.setCurrentIndex(idx)
        ws.restore_axis_group(ctrl.axis_grp, state.get("axis"))
        ws.restore_legend_group(ctrl.legend_grp, state.get("legend"))
        ws.restore_grouping_group(ctrl.grouping_grp, state.get("grouping"))
        ws.restore_reservoirs(ctrl.reservoirs_grp, state.get("reservoirs"))
        ctrl.reservoirs_grp.restore_styles(state.get("reservoir_styles"))
        # Annotations per-mode.
        mode = next((m for m, c in self._controls.items() if c is ctrl), None)
        ann_ctl = self._annotation_ctls.get(mode) if mode else None
        if ann_ctl is not None:
            ann_ctl.restore(state.get("annotations"))
        if ctrl.include_y_chk is not None and "include_y" in state:
            ws.restore_check(ctrl.include_y_chk, state["include_y"])
        # Multi-element selection restore
        if ctrl.elements_list is not None and "selected_elements" in state:
            wanted = set(state["selected_elements"])
            for i in range(ctrl.elements_list.count()):
                item = ctrl.elements_list.item(i)
                item.setCheckState(
                    Qt.CheckState.Checked if item.text() in wanted
                    else Qt.CheckState.Unchecked
                )

    # Canonical mode keys used by ``set_mode`` and as dict keys here.
    _MODES = ("ree", "multielement")

    def serialize(self) -> dict:
        out: dict = {"mode": self._mode}
        for mode in self._MODES:
            out[mode] = (
                self._serialise_controls(self._controls[mode])
                if mode in self._controls else {}
            )
        return out

    def restore(self, state: dict) -> None:
        if not state:
            return
        # Make sure the controls for both modes exist so we can populate
        # them, then end on the saved active mode.  Older sessions may
        # still carry the legacy "multi" key — fall through to that
        # when "multielement" isn't present.
        for mode in self._MODES:
            self.set_mode(mode)
            sub = state.get(mode) or state.get("multi" if mode == "multielement"
                                               else mode, {})
            self._restore_controls(self._controls[mode], sub)
        active = state.get("mode", "ree")
        # Map legacy "multi" → canonical "multielement".
        if active == "multi":
            active = "multielement"
        self.set_mode(active)
