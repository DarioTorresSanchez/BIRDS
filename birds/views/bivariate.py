"""Bivariate diagrams view: Individual and Paired modes."""

from __future__ import annotations


import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..plot_style import legend_columns
from .. import annotations as _ann
from ..diagrams.templates.base import (
    get_groups,
)
from ..derived import DESCRIPTIONS as _DERIVED_DESCRIPTIONS
from ..derived import available as _derived_available
from ..expression import ExpressionError, evaluate, evaluate_scalar
from ..preprocess import ADJ_SUFFIX, adjusted_name, interleave_twins
from ..reservoirs import RESERVOIRS
from .plot_canvas import PlotCanvas
from .widgets import (
    ANN_MODE_ARROW,
    ANN_MODE_LINE,
    ANN_MODE_NONE,
    ANN_MODE_SAMPLE,
    ANN_MODE_TEXT,
    AnnotationGroup as _AnnotationGroup,
    AxisGroup as _AxisGroup,
    GroupingGroup as _GroupingGroup,
    LegendGroup as _LegendGroup,
    RegressionGroup as _RegressionGroup,
    ReservoirGroup as _ReservoirGroup,
)
from .deferral import defer_while_hidden


# ---------------------------------------------------------------------------
# Individual mode
# ---------------------------------------------------------------------------

class _IndividualControls(QWidget):
    """Left panel for the Individual sub-mode."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        vars_box = QGroupBox("Variables")
        vbox = QVBoxLayout(vars_box)
        vbox.setContentsMargins(8, 12, 8, 8)
        vbox.setSpacing(4)

        form = QFormLayout()
        form.setContentsMargins(0, 0, 0, 0)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(4)
        # Make the X/Y combos stretch to the full width of the box.
        form.setFieldGrowthPolicy(
            QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
        )

        # Rich help text shown on hover instead of stealing vertical space.
        expr_tooltip = (
            "<b>Pick a column from the dropdown, or type an expression.</b>"
            "<br><br>"
            "Operators: + &minus; * / **"
            "<br>"
            "Functions: log, log10, ln, exp, sqrt, abs"
            "<br><br>"
            "Examples:<br>"
            "&nbsp;&nbsp;<code>La/Yb</code><br>"
            "&nbsp;&nbsp;<code>Ti/1000</code><br>"
            "&nbsp;&nbsp;<code>(La+Ce)/2</code><br>"
            "&nbsp;&nbsp;<code>log(Sr/Y)</code><br>"
            "&nbsp;&nbsp;<code>sqrt(La*Yb)</code>"
        )

        self.x_combo = QComboBox()
        self.x_combo.setEditable(True)
        self.x_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.x_combo.lineEdit().setPlaceholderText(
            "Column or expression (e.g. La/Yb)"
        )
        self.x_combo.setToolTip(expr_tooltip)

        self.y_combo = QComboBox()
        self.y_combo.setEditable(True)
        self.y_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.y_combo.lineEdit().setPlaceholderText(
            "Column or expression (e.g. Ti/1000)"
        )
        self.y_combo.setToolTip(expr_tooltip)

        form.addRow("X variable:", self.x_combo)
        form.addRow("Y variable:", self.y_combo)
        vbox.addLayout(form)

        hint = QLabel(
            "<i>Type a column or a math expression — hover ⓘ for examples.</i>"
        )
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setToolTip(expr_tooltip)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #5b6478; font-size: 11px;")
        vbox.addWidget(hint)

        layout.addWidget(vars_box)

        self.axis_grp = _AxisGroup()
        layout.addWidget(self.axis_grp)
        self.legend_grp = _LegendGroup()
        layout.addWidget(self.legend_grp)
        self.grouping_grp = _GroupingGroup()
        layout.addWidget(self.grouping_grp)
        self.regression_grp = _RegressionGroup()
        layout.addWidget(self.regression_grp)
        self.reservoirs_grp = _ReservoirGroup()
        # The reservoir catalogue is long: bound it so the outer panel
        # does not need a second vertical scrollbar.  The tree keeps its
        # own scrollbar for browsing.
        self.reservoirs_grp.tree.setMaximumHeight(220)
        layout.addWidget(self.reservoirs_grp)
        # Annotation toolkit (lines / arrows / text / sample-IDs)
        self.annotations_grp = _AnnotationGroup()
        layout.addWidget(self.annotations_grp)
        layout.addStretch(1)


#: Numeric columns that describe the sample rather than its chemistry
#: (the data template's context): offered after the analyses.
_CONTEXT_COLUMNS = ("No.", "Latitude", "Longitude", "Elevation", "Age")


def _default_axes(cols: list) -> tuple:
    """The axes a fresh Individual plot opens on: SiO2 against MgO when
    the data have them -- a Harker plot -- else the first two
    variables.  It used to be the first two numeric columns, which in
    the data template are "No." and an empty "Sample_Label"."""
    if not cols:
        return "", ""
    x = next((c for c in ("SiO2", "SiO2_adj") if c in cols), cols[0])
    y = next((c for c in ("MgO", "MgO_adj", "TiO2", "Al2O3", "FeOt",
                          "Fe2O3", "CaO") if c in cols and c != x), None)
    if y is None:
        y = next((c for c in cols if c != x), x)
    return x, y


# ---------------------------------------------------------------------------
# Paired mode
# ---------------------------------------------------------------------------

class _PairedControls(QWidget):
    """Left panel for the Paired (matrix) sub-mode."""

    def __init__(self) -> None:
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        paired_tooltip = (
            "Pick 1 X + several Y (or vice-versa) for a Harker grid; "
            "Ctrl/Cmd or Shift to multi-select. "
            "Type a math expression and click <b>+ Add</b> to use "
            "derived axes (purple items)."
        )

        vars_box = QGroupBox("Variables (multi-select)")
        vars_box.setToolTip(paired_tooltip)
        v_layout = QVBoxLayout(vars_box)
        v_layout.setContentsMargins(8, 12, 8, 8)
        v_layout.setSpacing(4)

        x_lbl = QLabel("X variables:")
        x_lbl.setStyleSheet("font-weight: 600;")
        v_layout.addWidget(x_lbl)
        self.x_list = QListWidget()
        self.x_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        # Cap each list so a long column dictionary doesn't stretch the
        # whole Variables box past the viewport.  The list scrolls
        # internally when there are more entries than fit.
        self.x_list.setMaximumHeight(140)
        v_layout.addWidget(self.x_list, stretch=1)
        self.x_expr_edit = QLineEdit()
        self.x_expr_edit.setProperty("liveExempt", True)   # added via + Add
        self.x_expr_edit.setPlaceholderText("Custom expression — e.g. La/Yb")
        self.x_expr_add = QPushButton("+ Add")
        self.x_expr_add.setMaximumWidth(70)
        self.x_expr_add.setToolTip(
            "Add this expression to the X list (then click it to select)."
        )
        x_row = QHBoxLayout()
        x_row.setSpacing(4)
        x_row.addWidget(self.x_expr_edit, stretch=1)
        x_row.addWidget(self.x_expr_add)
        v_layout.addLayout(x_row)

        y_lbl = QLabel("Y variables:")
        y_lbl.setStyleSheet("font-weight: 600;")
        v_layout.addWidget(y_lbl)
        self.y_list = QListWidget()
        self.y_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection
        )
        self.y_list.setMaximumHeight(140)
        v_layout.addWidget(self.y_list, stretch=1)
        self.y_expr_edit = QLineEdit()
        self.y_expr_edit.setProperty("liveExempt", True)
        self.y_expr_edit.setPlaceholderText("Custom expression — e.g. (La+Ce)/2")
        self.y_expr_add = QPushButton("+ Add")
        self.y_expr_add.setMaximumWidth(70)
        self.y_expr_add.setToolTip(
            "Add this expression to the Y list (then click it to select)."
        )
        y_row = QHBoxLayout()
        y_row.setSpacing(4)
        y_row.addWidget(self.y_expr_edit, stretch=1)
        y_row.addWidget(self.y_expr_add)
        v_layout.addLayout(y_row)

        layout_row = QHBoxLayout()
        layout_row.setSpacing(4)
        grid_lbl = QLabel("Grid layout:")
        grid_lbl.setStyleSheet("font-weight: 600;")
        layout_row.addWidget(grid_lbl)
        self.grid_layout_combo = QComboBox()
        for label, code in (
            ("Auto (near-square)", "auto"),
            ("1 column", "1"),
            ("2 columns", "2"),
            ("3 columns", "3"),
            ("4 columns", "4"),
            ("Strict X × Y matrix", "matrix"),
        ):
            self.grid_layout_combo.addItem(label, code)
        layout_row.addWidget(self.grid_layout_combo, stretch=1)
        v_layout.addLayout(layout_row)

        layout.addWidget(vars_box, stretch=2)

        self.axis_grp = _AxisGroup("Axes (font applied to every panel)")
        layout.addWidget(self.axis_grp)
        self.legend_grp = _LegendGroup("Legend (shared across panels)")
        layout.addWidget(self.legend_grp)
        self.grouping_grp = _GroupingGroup()
        layout.addWidget(self.grouping_grp)
        self.regression_grp = _RegressionGroup()
        layout.addWidget(self.regression_grp)
        self.reservoirs_grp = _ReservoirGroup()
        self.reservoirs_grp.tree.setMaximumHeight(220)
        layout.addWidget(self.reservoirs_grp)
        # Annotation toolkit; each annotation belongs to the panel it
        # was placed on and is redrawn there.
        self.annotations_grp = _AnnotationGroup()
        self.annotations_grp.setToolTip(
            "Each annotation belongs to the panel you click in, and "
            "stays with that X-Y pair when the grid is rearranged.")
        layout.addWidget(self.annotations_grp)
        layout.addStretch(1)


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------

class BivariateView(QWidget):
    """Splitter UI with mode-specific controls on the left, canvas on right."""

    def __init__(self, data_manager, plot_style, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style
        self._mode = "individual"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        outer.addWidget(splitter)

        # Left panel ---------------------------------------------------------
        self.controls_stack = QStackedWidget()
        self._individual = _IndividualControls()
        self._paired = _PairedControls()
        self.controls_stack.addWidget(self._individual)
        self.controls_stack.addWidget(self._paired)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.controls_stack)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # The content wraps naturally; never show a horizontal scrollbar.
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        # Sticky action bar: the Update button lives OUTSIDE the
        # scrollable area so it is always visible at the bottom, even
        # when the user scrolls through reservoirs / axes / legend.
        self.update_btn = QPushButton("Update plot")
        self.update_btn.setMinimumHeight(34)
        self.update_btn.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 6px 12px; }"
        )

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
        btn_pad_layout = QVBoxLayout(btn_pad)
        btn_pad_layout.setContentsMargins(8, 6, 8, 8)
        btn_pad_layout.addWidget(self.update_btn)
        left_layout.addWidget(btn_pad)
        left_panel.setMinimumWidth(380)
        left_panel.setMaximumWidth(540)
        splitter.addWidget(left_panel)

        # Right panel --------------------------------------------------------
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(6)
        self.title_label = QLabel("Bivariate diagrams")
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

        # Wire up the single sticky Update button
        self.update_btn.clicked.connect(self.update_plot)
        # Dropdown selection — instant refresh
        self._individual.x_combo.currentIndexChanged.connect(self.update_plot)
        self._individual.y_combo.currentIndexChanged.connect(self.update_plot)
        # Free-text expression in the editable combo — refresh on Enter
        self._individual.x_combo.lineEdit().editingFinished.connect(
            self.update_plot
        )
        self._individual.y_combo.lineEdit().editingFinished.connect(
            self.update_plot
        )
        # Add-expression buttons in Paired mode
        self._paired.x_expr_add.clicked.connect(
            lambda: self._add_expression_to_list(
                self._paired.x_list, self._paired.x_expr_edit
            )
        )
        self._paired.y_expr_add.clicked.connect(
            lambda: self._add_expression_to_list(
                self._paired.y_list, self._paired.y_expr_edit
            )
        )
        self._paired.x_expr_edit.returnPressed.connect(
            self._paired.x_expr_add.click
        )
        self._paired.y_expr_edit.returnPressed.connect(
            self._paired.y_expr_add.click
        )

        # Annotation state — initialised BEFORE set_mode() because the
        # renderers read it on first paint.  Individual annotations sit
        # on its single axis; Paired ones are (panel, annotation) pairs,
        # the panel being the (x, y) variables of the axes clicked in.
        self._annotations: list = []
        self._paired_annotations: list = []
        self._paired_axes: dict = {}
        self._ann_mode = ANN_MODE_NONE
        self._ann_pending: tuple | None = None
        self._ann_pending_panel: tuple | None = None
        for ag in (self._individual.annotations_grp,
                   self._paired.annotations_grp):
            ag.mode_requested.connect(self._on_ann_mode_requested)
            ag.clear_requested.connect(self._on_ann_clear)
            ag.delete_index.connect(self._on_ann_delete)
        self.canvas.mpl_connect("button_press_event", self._on_canvas_click)

        self.set_mode("individual")

    # ----------------------------------------------------- expression hook
    def _add_expression_to_list(
        self, list_widget: QListWidget, edit: QLineEdit
    ) -> None:
        """Append the text of *edit* as a new item in *list_widget*.

        The new item is tagged so :meth:`_refresh_variable_lists` can
        preserve it across data reloads, and is rendered in a distinct
        colour so the user can tell custom expressions apart from raw
        columns.  Duplicate expressions are ignored.
        """
        text = edit.text().strip()
        if not text:
            return
        # Skip duplicates
        for i in range(list_widget.count()):
            if list_widget.item(i).text() == text:
                list_widget.item(i).setSelected(True)
                edit.clear()
                return
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, "expr")
        item.setForeground(Qt.GlobalColor.darkMagenta)
        list_widget.addItem(item)
        item.setSelected(True)
        edit.clear()

    # ------------------------------------------------------------------ API
    def set_mode(self, mode: str) -> None:
        self._mode = mode
        # A tool armed in the other mode must not fire in this one.
        for ag in (self._individual.annotations_grp,
                   self._paired.annotations_grp):
            ag.cancel_mode()
        self._ann_mode = ANN_MODE_NONE
        self._ann_pending = self._ann_pending_panel = None
        if mode == "individual":
            self.controls_stack.setCurrentWidget(self._individual)
            self.title_label.setText("Bivariate diagrams – Individual")
            self.subtitle_label.setText(
                "Plot one element/oxide against another. "
                "Optional reservoir overlays at the bottom of the left panel."
            )
        else:
            self.controls_stack.setCurrentWidget(self._paired)
            self.title_label.setText("Bivariate diagrams – Paired")
            self.subtitle_label.setText(
                "Pick a set of X and Y variables to build a panel grid "
                "(ggpairs-style). Editing options apply to every panel."
            )
        self._refresh_variable_lists()
        self.update_plot()

    # ----------------------------------------------------------------- impl
    def _numeric_columns(self) -> list[str]:
        """Every variable an axis can take, in the order offered.

        Each adjusted twin (``SiO2_adj``) sits right after the oxide it
        adjusts, so the analysed and the adjusted value are side by side
        and never confused; the Mg# variants follow MgO.
        """
        df = self.data.df
        if df is None or df.empty:
            return []
        # A column with no value cannot be plotted -- the template's
        # Sample_Label, Elevation… left blank used to head the lists and
        # make the default axes -- and the sample's context goes after
        # its chemistry, so the oxides lead.
        numeric = [c for c in df.select_dtypes(include="number").columns
                   if df[c].notna().any()]
        numeric = ([c for c in numeric if c not in _CONTEXT_COLUMNS]
                   + [c for c in numeric if c in _CONTEXT_COLUMNS])
        out = interleave_twins(numeric)
        derived = _derived_available(df)
        if derived:
            anchor = next((a for a in (adjusted_name("MgO"), "MgO")
                           if a in out), None)
            at = out.index(anchor) + 1 if anchor else len(out)
            out[at:at] = derived
        return out

    @staticmethod
    def _variable_hint(name: str):
        """(colour, tooltip) marking an adjusted or derived variable, or
        None for a plain column."""
        if name in _DERIVED_DESCRIPTIONS:
            return QColor("#2a7a3b"), _DERIVED_DESCRIPTIONS[name]
        if name.endswith(ADJ_SUFFIX):
            return QColor("#1f4e99"), (
                f"{name[:-len(ADJ_SUFFIX)]} adjusted to 100 % "
                "(Data → Pre-process majors…). The analysed value is "
                "the column without _adj.")
        return None

    def _refresh_variable_lists(self) -> None:
        cols = self._numeric_columns()

        # Individual combos: preserve any free-text the user typed before
        # reloading the dataset, so they don't lose "La/Yb" by clicking
        # Import on the same workflow.
        prev_x = self._individual.x_combo.currentText()
        prev_y = self._individual.y_combo.currentText()
        self._individual.x_combo.blockSignals(True)
        self._individual.y_combo.blockSignals(True)
        self._individual.x_combo.clear()
        self._individual.y_combo.clear()
        for c in cols:
            for combo in (self._individual.x_combo, self._individual.y_combo):
                combo.addItem(c)
                hint = self._variable_hint(c)
                if hint is not None:
                    i = combo.count() - 1
                    combo.setItemData(i, hint[0],
                                      Qt.ItemDataRole.ForegroundRole)
                    combo.setItemData(i, hint[1], Qt.ItemDataRole.ToolTipRole)
        default_x, default_y = _default_axes(cols)
        self._individual.x_combo.setCurrentText(prev_x or default_x)
        self._individual.y_combo.setCurrentText(prev_y or default_y)
        self._individual.x_combo.blockSignals(False)
        self._individual.y_combo.blockSignals(False)

        # Paired lists: rebuild but preserve any custom expression items
        # the user added with the "+" button.
        for list_widget in (self._paired.x_list, self._paired.y_list):
            custom = []
            selected = set()
            for i in range(list_widget.count()):
                item = list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == "expr":
                    custom.append(item.text())
                if item.isSelected():
                    selected.add(item.text())
            list_widget.clear()
            for c in cols:
                item = QListWidgetItem(c, list_widget)
                hint = self._variable_hint(c)
                if hint is not None:
                    item.setForeground(hint[0])
                    item.setToolTip(hint[1])
            for expr in custom:
                item = QListWidgetItem(expr, list_widget)
                item.setData(Qt.ItemDataRole.UserRole, "expr")
                item.setForeground(Qt.GlobalColor.darkMagenta)
            # Restore the user's selection where the item still exists
            for i in range(list_widget.count()):
                if list_widget.item(i).text() in selected:
                    list_widget.item(i).setSelected(True)

    def _empty_canvas(self, message: str) -> None:
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center",
                color="#6c7388", fontsize=12, wrap=True)
        ax.axis("off")
        self.canvas.draw()

    # ------------------------------------------------------------------
    # Annotation toolkit handlers
    # ------------------------------------------------------------------
    def _on_ann_mode_requested(self, mode: str) -> None:
        """User pressed one of the annotation tool buttons."""
        self._ann_mode = mode
        self._ann_pending = self._ann_pending_panel = None

    def _ann_group(self):
        """The annotation panel of the active mode."""
        return (self._individual.annotations_grp
                if self._mode == "individual"
                else self._paired.annotations_grp)

    def _refresh_ann_list(self) -> None:
        """Repopulate both annotation lists.  Paired rows say which
        panel each annotation is on."""
        self._individual.annotations_grp.refresh(self._annotations)
        grp = self._paired.annotations_grp
        grp.refresh([ann for _panel, ann in self._paired_annotations])
        for row, ((x_col, y_col), _ann_obj) in enumerate(
                self._paired_annotations):
            item = grp.list.item(row)
            item.setText(f"[{y_col} vs {x_col}]  {item.text()}")

    def _on_ann_clear(self) -> None:
        if self._mode == "individual":
            if not self._annotations:
                return
            self._annotations = []
        else:
            if not self._paired_annotations:
                return
            self._paired_annotations = []
        self._refresh_ann_list()
        self.update_plot()

    def _on_ann_delete(self, index: int) -> None:
        items = (self._annotations if self._mode == "individual"
                 else self._paired_annotations)
        if 0 <= index < len(items):
            del items[index]
            self._refresh_ann_list()
            self.update_plot()

    def _end_ann_tool(self) -> None:
        self._ann_group().cancel_mode()
        self._ann_mode = ANN_MODE_NONE
        self._ann_pending = self._ann_pending_panel = None

    def _on_canvas_click(self, event) -> None:
        """Matplotlib click handler — translates a click into the
        appropriate annotation based on the active tool.  In Paired
        mode the annotation goes to the panel clicked in."""
        # Modifier+left-click belongs to cross-view brushing.
        from .brushing import is_select_click
        if is_select_click(event):
            return
        if event.inaxes is None:
            return
        panel = None
        if self._mode != "individual":
            panel = self._paired_axes.get(event.inaxes)
            if panel is None:
                return          # an empty grid cell, or a stale figure
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        # Right-click: delete the closest annotation regardless of mode
        # (in Paired, the closest on the panel clicked).
        if event.button == 3:
            xlim = event.inaxes.get_xlim()
            ylim = event.inaxes.get_ylim()
            tol = 0.04 * max(abs(xlim[1] - xlim[0]),
                             abs(ylim[1] - ylim[0]))
            if panel is None:
                idx = _ann.closest(self._annotations, x, y, tol)
                if idx is not None:
                    del self._annotations[idx]
            else:
                rows = [i for i, (p, _a) in
                        enumerate(self._paired_annotations) if p == panel]
                hit = _ann.closest([self._paired_annotations[i][1]
                                    for i in rows], x, y, tol)
                idx = None if hit is None else rows[hit]
                if idx is not None:
                    del self._paired_annotations[idx]
            if idx is not None:
                self._refresh_ann_list()
                self.update_plot()
            return
        if self._ann_mode == ANN_MODE_NONE or event.button != 1:
            return

        mode = self._ann_mode
        if mode in (ANN_MODE_LINE, ANN_MODE_ARROW):
            # Both ends on one panel: a second click on another panel
            # starts the line again there.
            if self._ann_pending is None or self._ann_pending_panel != panel:
                self._ann_pending = (x, y)
                self._ann_pending_panel = panel
                return
            x1, y1 = self._ann_pending
            kind = (_ann.LineAnnotation if mode == ANN_MODE_LINE
                    else _ann.ArrowAnnotation)
            self._end_ann_tool()
            self._add_annotation(kind(x1=x1, y1=y1, x2=x, y2=y), panel)
        elif mode == ANN_MODE_TEXT:
            text, ok = self._ask_text("Annotation text", "Text to display:")
            self._end_ann_tool()
            if ok and text:
                self._add_annotation(_ann.TextAnnotation(x=x, y=y, text=text),
                                     panel)
        elif mode == ANN_MODE_SAMPLE:
            self._end_ann_tool()
            self._add_sample_annotation(x, y, event.inaxes, panel)

    def _ask_text(self, title: str, prompt: str) -> tuple[str, bool]:
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, title, prompt)
        return text.strip(), ok

    def _add_annotation(self, ann_obj, panel: tuple | None = None) -> None:
        if panel is None:
            self._annotations.append(ann_obj)
        else:
            self._paired_annotations.append((panel, ann_obj))
        self._refresh_ann_list()
        self.update_plot()

    def _current_plot_xy(self):
        """(df, xs, ys) for the Individual panel's current axes, or
        (None, None, None) when unavailable (paired mode, bad expr…)."""
        if self._mode != "individual":
            return None, None, None
        df = self.data.df
        if df is None or df.empty:
            return None, None, None
        ctrl = self._individual
        x_col = ctrl.x_combo.currentText().strip()
        y_col = ctrl.y_combo.currentText().strip()
        try:
            xs = evaluate(df, x_col)
            ys = evaluate(df, y_col)
        except ExpressionError:
            return None, None, None
        return df, xs, ys

    def _panel_xy(self, x_col: str, y_col: str):
        """(df, xs, ys) of one X-Y pair, NaN wherever the sample is not
        drawn -- its group switched off -- so it cannot be picked."""
        df = self.data.df
        if df is None or df.empty:
            return None, None, None
        try:
            xs = evaluate(df, x_col)
            ys = evaluate(df, y_col)
        except ExpressionError:
            return None, None, None
        shown = pd.Series(False, index=df.index)
        for _label, sub, _gs in get_groups(df, self.plot_style):
            shown[sub.index] = True
        return df, xs.where(shown), ys.where(shown)

    def _axes_panel(self, ax):
        """The (x, y) variables plotted on *ax*, or None."""
        if self._mode == "individual":
            ctrl = self._individual
            return (ctrl.x_combo.currentText().strip(),
                    ctrl.y_combo.currentText().strip())
        return self._paired_axes.get(ax)

    def _resolve_sample_in(self, ax, x: float, y: float):
        """Nearest drawn sample to a click on *ax* -- whichever panel it
        is -- as ``(px, py, label)``.  Used by Identify sample and by
        cross-view brushing."""
        if ax is None:
            return None
        panel = self._axes_panel(ax)
        if panel is None:
            return None
        df, xs, ys = self._panel_xy(*panel)
        if df is None:
            return None
        from .annotation_controller import nearest_sample
        return nearest_sample(df, xs, ys, x, y,
                              ax.get_xlim(), ax.get_ylim())

    def _resolve_sample(self, x: float, y: float):
        """Nearest-sample resolver on the Individual axis (Paired needs
        the axes clicked: see :meth:`_resolve_sample_in`)."""
        fig = self.canvas.figure
        if self._mode != "individual" or not fig.axes:
            return None
        return self._resolve_sample_in(fig.axes[0], x, y)

    def _selection_points(self, names):
        """Coordinates of the selected samples on every panel drawn."""
        from .brushing import names_series
        fig = self.canvas.figure
        if not fig.axes:
            return []
        if self._mode == "individual":
            df, xs, ys = self._current_plot_xy()
            if df is None:
                return []
            nm = names_series(df)
            m = nm.isin(names) & xs.notna() & ys.notna()
            return [(fig.axes[0], list(zip(xs[m], ys[m])))]
        out = []
        for ax, (x_col, y_col) in self._paired_axes.items():
            df, xs, ys = self._panel_xy(x_col, y_col)
            if df is None:
                continue
            nm = names_series(df)
            m = nm.isin(names) & xs.notna() & ys.notna()
            out.append((ax, list(zip(xs[m], ys[m]))))
        return out

    def _add_sample_annotation(self, x: float, y: float, ax=None,
                               panel: tuple | None = None) -> None:
        """Label the drawn sample nearest (x, y) on *ax* -- the
        Individual axis when not given."""
        fig = self.canvas.figure
        if ax is None:
            if not fig.axes:
                return
            ax = fig.axes[0]
        hit = self._resolve_sample_in(ax, x, y)
        if hit is None:
            return
        px, py, name = hit
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()
        # Offset label up-right by ~4 % of the axis range.
        self._add_annotation(_ann.SampleAnnotation(
            px=px, py=py,
            dx=0.04 * (xlim[1] - xlim[0]),
            dy=0.04 * (ylim[1] - ylim[0]),
            label=name,
        ), panel)

    def _paired_panel_done(self, ax, x_col: str, y_col: str) -> None:
        """Record which pair *ax* shows and replay its annotations."""
        self._paired_axes[ax] = (x_col, y_col)
        _ann.draw_all(ax, [a for p, a in self._paired_annotations
                           if p == (x_col, y_col)])

    def update_plot(self) -> None:
        if defer_while_hidden(self):
            return      # drawn when its page is shown
        if self.data.df is None or self.data.df.empty:
            self._empty_canvas(
                "Load a dataset via Data → Import to start plotting."
            )
            return
        if self._mode == "individual":
            self._render_individual()
        else:
            self._render_paired()

    # ---------------------------------------------------------- individual
    def _render_individual(self) -> None:
        ctrl = self._individual
        x_col = ctrl.x_combo.currentText().strip()
        y_col = ctrl.y_combo.currentText().strip()
        if not x_col or not y_col:
            self._empty_canvas("Pick X and Y variables.")
            return

        df = self.data.df
        # Validate both axes once up-front; show a friendly message instead
        # of crashing when the user mistypes ("Nb+Ta" with no Nb column).
        try:
            evaluate(df, x_col)
            evaluate(df, y_col)
        except ExpressionError as exc:
            self._empty_canvas(
                f"Cannot evaluate axis expression:\n\n  {exc}\n\n"
                "Allowed operators: + − * / **\n"
                "Allowed functions: log, log10, ln, exp, sqrt, abs"
            )
            return
        x_label_override = ctrl.axis_grp.x_label_edit.text().strip() or None
        y_label_override = ctrl.axis_grp.y_label_edit.text().strip() or None
        x_style = ctrl.axis_grp.axis_style(x_label_override or x_col)
        y_style = ctrl.axis_grp.axis_style(y_label_override or y_col)
        legend = ctrl.legend_grp.legend_style()

        fig = self.canvas.figure
        fig.clear()

        groups_data = get_groups(df, self.plot_style)
        facet = ctrl.grouping_grp.facet_chk.isChecked() and len(groups_data) > 1

        if facet:
            ncols = min(3, len(groups_data))
            nrows = (len(groups_data) + ncols - 1) // ncols
            axes = fig.subplots(nrows, ncols, squeeze=False, sharex=True, sharey=True)
            for i, (label, sub, gs) in enumerate(groups_data):
                ax = axes[i // ncols][i % ncols]
                self._plot_group(ax, sub, label, gs, x_col, y_col,
                                  shaded=getattr(gs, "shaded", False))
                ax.set_title(label, fontsize=ctrl.axis_grp.font_size.value() - 2)
                # Per-panel regression on the group only
                if ctrl.regression_grp.show.isChecked():
                    self._draw_regression(ax, sub, x_col, y_col, ctrl.regression_grp)
                ax.set_box_aspect(1)  # matrix style
            # Hide empty cells
            for i in range(len(groups_data), nrows * ncols):
                axes[i // ncols][i % ncols].axis("off")
            # Apply labels only to edge axes
            for i, ax in enumerate(axes.flat):
                if i < len(groups_data):
                    if i % ncols == 0:
                        ax.set_ylabel(y_style.label, **y_style.label_kwargs())
                    if i // ncols == nrows - 1:
                        ax.set_xlabel(x_style.label, **x_style.label_kwargs())
                    self._apply_scales(ax, ctrl)
            self._draw_reservoirs(fig.axes, x_col, y_col,
                                  ctrl.reservoirs_grp.selected_reservoirs())
            # Single legend
            handles, labels = fig.axes[0].get_legend_handles_labels()
            if legend.visible and handles:
                fig.legend(handles, labels, loc="upper right",
                           fontsize=legend.font_size, title=legend.title,
                           ncol=legend_columns(len(handles)),
                           bbox_to_anchor=(0.99, 0.99))
        else:
            ax = fig.add_subplot(111)
            for label, sub, gs in groups_data:
                self._plot_group(ax, sub, label, gs, x_col, y_col,
                                  shaded=getattr(gs, "shaded", False))
            if ctrl.regression_grp.show.isChecked():
                self._draw_regression(ax, df, x_col, y_col, ctrl.regression_grp)
            ax.set_xlabel(x_style.label, **x_style.label_kwargs())
            ax.set_ylabel(y_style.label, **y_style.label_kwargs())
            self._apply_scales(ax, ctrl)
            self._draw_reservoirs([ax], x_col, y_col,
                                  ctrl.reservoirs_grp.selected_reservoirs())
            if legend.visible:
                handles, lbls = ax.get_legend_handles_labels()
                if handles:
                    kwargs = {"fontsize": legend.font_size,
                              "ncol": legend_columns(len(handles))}
                    if legend.title:
                        kwargs["title"] = legend.title
                    if legend.location == "outside":
                        kwargs.update(loc="upper left",
                                      bbox_to_anchor=(1.02, 1.0))
                    else:
                        kwargs["loc"] = legend.location
                    ax.legend(**kwargs)
            # Replay user-placed annotations on the single-panel axis.
            # Only meaningful in non-facet mode (facet plots have many
            # axes and click coordinates would be ambiguous).
            if not facet:
                _ann.draw_all(ax, self._annotations)

        fig.tight_layout()
        from .brushing import draw_selection_overlay
        draw_selection_overlay(self)
        self._update_count_label()
        self.canvas.draw()

    def _update_count_label(self) -> None:
        """Tally samples for the Individual panel (Paired has one tally
        per sub-plot, which would be noise rather than signal)."""
        from .sample_counts import count_samples, CountReport
        if self._mode != "individual":
            total = len(self.data.df) if self.data.df is not None else 0
            self.count_label.show_report(CountReport(total=total,
                                                     plotted=total))
            return
        df, xs, ys = self._current_plot_xy()
        if df is None:
            self.count_label.show_report(count_samples(
                self.data.df, self.data.df, None, None, self.plot_style))
            return
        self.count_label.show_report(count_samples(
            self.data.df, df, xs, ys, self.plot_style))

    @staticmethod
    def _apply_scales(ax, ctrl) -> None:
        if ctrl.axis_grp.log_x.isChecked():
            ax.set_xscale("log")
        if ctrl.axis_grp.log_y.isChecked():
            ax.set_yscale("log")

    def _draw_regression(self, ax, df, x_col, y_col, reg_ctrl) -> None:
        """Overlay an OLS linear regression on *ax*."""
        try:
            from scipy.stats import linregress
        except ImportError:
            return

        show_label = reg_ctrl.show_label.isChecked()
        per_group = reg_ctrl.per_group.isChecked()
        show_ci = reg_ctrl.ci_chk.isChecked()

        def fit_and_plot(x, y, color, label_prefix):
            if len(x) < 2:
                return
            try:
                r = linregress(x, y)
            except Exception:
                return
            x_line = np.linspace(float(x.min()), float(x.max()), 100)
            y_line = r.slope * x_line + r.intercept
            line_label = None
            if show_label:
                line_label = (
                    f"{label_prefix}: y = {r.slope:.3g}·x {r.intercept:+.3g}, "
                    f"R² = {r.rvalue**2:.3f}"
                )
            ax.plot(x_line, y_line, color=color, linewidth=1.6,
                    linestyle="--", label=line_label, zorder=4)
            # 95 % confidence band on the mean prediction
            if show_ci and r.stderr is not None and not np.isnan(r.stderr):
                n = len(x)
                if n > 2:
                    x_arr = x.to_numpy() if hasattr(x, "to_numpy") else np.asarray(x)
                    x_mean = float(np.mean(x_arr))
                    sxx = float(np.sum((x_arr - x_mean) ** 2))
                    if sxx > 0:
                        residuals = y - (r.slope * x + r.intercept)
                        s_e = float(np.sqrt(np.sum(residuals ** 2) / max(n - 2, 1)))
                        from scipy.stats import t as student_t
                        tval = student_t.ppf(0.975, n - 2)
                        se_pred = s_e * np.sqrt(1.0 / n + (x_line - x_mean) ** 2 / sxx)
                        margin = tval * se_pred
                        ax.fill_between(x_line, y_line - margin, y_line + margin,
                                        color=color, alpha=0.15, zorder=3)

        if per_group:
            for label, sub, gs in get_groups(df, self.plot_style):
                if gs is not None and not getattr(gs, "visible", True):
                    continue
                try:
                    x = evaluate(sub, x_col)
                    y = evaluate(sub, y_col)
                except ExpressionError:
                    continue
                m = x.notna() & y.notna()
                x, y = x[m], y[m]
                color = gs.color if gs else "#1f77b4"
                fit_and_plot(x, y, color, str(label))
        else:
            try:
                x_all = evaluate(df, x_col)
                y_all = evaluate(df, y_col)
            except ExpressionError:
                return
            m = x_all.notna() & y_all.notna()
            fit_and_plot(x_all[m], y_all[m], "#222222", "OLS")

    def _plot_group(self, ax, sub, label, gs, x_col, y_col,
                    shaded: bool = False) -> None:
        # Master visibility switch — Grouping checkbox in the side panel.
        if gs is not None and not getattr(gs, "visible", True):
            return
        # ``x_col`` / ``y_col`` may be a bare column name (e.g. "La") or a
        # math expression (e.g. "La/Yb"); ``evaluate`` handles both.
        try:
            x = evaluate(sub, x_col)
            y = evaluate(sub, y_col)
        except ExpressionError:
            return
        mask = x.notna() & y.notna()
        x, y = x[mask], y[mask]
        if x.empty:
            return
        color = gs.color if gs else "#1f77b4"
        marker = gs.marker if gs else "o"
        show_markers = getattr(gs, "show_markers", True) if gs else True
        # When markers are hidden, hand the legend label over to the hull
        # patch instead so the group still shows up in the legend.
        scatter_label = label if show_markers else None
        fill_label = label if (shaded and not show_markers) else None
        if show_markers:
            ax.scatter(x, y, s=self.plot_style.point_size ** 2,
                       alpha=self.plot_style.alpha, c=color, marker=marker,
                       label=scatter_label,
                       edgecolors="black", linewidths=0.4, zorder=3)
        if shaded and len(x) >= 3:
            try:
                from scipy.spatial import ConvexHull
                pts = np.column_stack([x.to_numpy(), y.to_numpy()])
                hull = ConvexHull(pts)
                hull_pts = pts[hull.vertices]
                ax.fill(hull_pts[:, 0], hull_pts[:, 1], color=color,
                        alpha=0.18 if not show_markers else 0.12,
                        label=fill_label, zorder=2)
            except Exception:
                pass

    # ----------------------------------------------------------- paired
    @staticmethod
    def _smart_grid(n: int) -> tuple[int, int]:
        """Return ``(nrows, ncols)`` for a near-square layout of *n* panels."""
        if n <= 0:
            return 1, 1
        presets = {
            1: (1, 1), 2: (1, 2), 3: (1, 3),
            4: (2, 2), 5: (2, 3), 6: (2, 3),
            7: (3, 3), 8: (3, 3), 9: (3, 3),
            10: (3, 4), 11: (3, 4), 12: (3, 4),
        }
        if n in presets:
            return presets[n]
        import math
        ncols = math.ceil(math.sqrt(n))
        return math.ceil(n / ncols), ncols

    def _render_paired(self) -> None:
        ctrl = self._paired
        x_vars = [item.text() for item in ctrl.x_list.selectedItems()]
        y_vars = [item.text() for item in ctrl.y_list.selectedItems()]
        if not x_vars or not y_vars:
            self._empty_canvas(
                "Pick at least one X variable and one Y variable on the "
                "left to build the paired grid."
            )
            return

        df = self.data.df
        legend = ctrl.legend_grp.legend_style()
        groups_data = get_groups(df, self.plot_style)
        show_reg = ctrl.regression_grp.show.isChecked()
        reservoir_names = ctrl.reservoirs_grp.selected_reservoirs()
        layout_choice = ctrl.grid_layout_combo.currentData()

        fig = self.canvas.figure
        fig.clear()
        self._paired_axes = {}

        # ── Decide the layout ──────────────────────────────────────────
        force_matrix = layout_choice == "matrix"
        cartesian_full = len(x_vars) > 1 and len(y_vars) > 1

        if force_matrix or (cartesian_full and layout_choice == "auto"):
            return self._render_paired_matrix(
                ctrl, df, x_vars, y_vars, groups_data, show_reg,
                reservoir_names, legend,
            )

        # Build the list of (x, y) panel pairs and the sharing mode
        if len(x_vars) == 1:
            shared = "x"
            pairs = [(x_vars[0], y) for y in y_vars]
        elif len(y_vars) == 1:
            shared = "y"
            pairs = [(x, y_vars[0]) for x in x_vars]
        else:
            # Multiple X and Y but user asked for explicit columns – pair them
            # up by position (extra entries reuse the last variable).
            shared = None
            n = max(len(x_vars), len(y_vars))
            pairs = [
                (x_vars[i] if i < len(x_vars) else x_vars[-1],
                 y_vars[i] if i < len(y_vars) else y_vars[-1])
                for i in range(n)
            ]

        n = len(pairs)
        if layout_choice == "auto":
            nrows, ncols = self._smart_grid(n)
        else:
            ncols = max(1, int(layout_choice))
            import math
            nrows = math.ceil(n / ncols)

        axes = fig.subplots(
            nrows, ncols, squeeze=False,
            sharex=(shared == "x"),
            sharey=(shared == "y"),
        )

        for k, (x_col, y_col) in enumerate(pairs):
            i, j = divmod(k, ncols)
            ax = axes[i][j]
            for label, sub, gs in groups_data:
                self._plot_group(ax, sub, label, gs, x_col, y_col,
                                  shaded=getattr(gs, "shaded", False))
            if show_reg:
                self._draw_regression(ax, df, x_col, y_col,
                                      ctrl.regression_grp)
            self._draw_reservoirs([ax], x_col, y_col, reservoir_names,
                                  annotate=(k == 0))
            if ctrl.axis_grp.log_x.isChecked():
                ax.set_xscale("log")
            if ctrl.axis_grp.log_y.isChecked():
                ax.set_yscale("log")
            # Per-panel labels (always show its own variable name)
            ax.set_ylabel(y_col, **ctrl.axis_grp.axis_style(y_col).label_kwargs())
            ax.set_xlabel(x_col, **ctrl.axis_grp.axis_style(x_col).label_kwargs())
            ax.tick_params(labelsize=max(ctrl.axis_grp.font_size.value() - 4, 6))
            ax.set_box_aspect(1)
            self._paired_panel_done(ax, x_col, y_col)

        # Hide unused cells
        for k in range(n, nrows * ncols):
            i, j = divmod(k, ncols)
            axes[i][j].axis("off")

        # When the X (or Y) axis is shared, suppress the redundant label on
        # every panel except the bottom row (or leftmost column).
        if shared == "x":
            for k in range(n):
                i, j = divmod(k, ncols)
                # Only the last *used* row in each column keeps the x-label
                # — find the lowest k for which (k % ncols == j) using the
                # available range
                cells_in_col = [m for m in range(n) if m % ncols == j]
                if cells_in_col and k != cells_in_col[-1]:
                    axes[i][j].set_xlabel("")
        elif shared == "y":
            for k in range(n):
                i, j = divmod(k, ncols)
                cells_in_row = [m for m in range(n) if m // ncols == i]
                if cells_in_row and k != cells_in_row[0]:
                    axes[i][j].set_ylabel("")

        # Single legend
        if legend.visible:
            handles, labels = axes[0][0].get_legend_handles_labels()
            if handles:
                fig.legend(handles, labels, loc="upper center",
                           ncol=min(len(labels), 6),
                           fontsize=legend.font_size, title=legend.title,
                           bbox_to_anchor=(0.5, 1.0))
                fig.subplots_adjust(top=0.9)

        fig.tight_layout()
        from .brushing import draw_selection_overlay
        draw_selection_overlay(self)
        self.canvas.draw()

    def _render_paired_matrix(self, ctrl, df, x_vars, y_vars, groups_data,
                              show_reg, reservoir_names, legend) -> None:
        """Strict X × Y matrix layout (rows = Y, columns = X)."""
        nrows, ncols = len(y_vars), len(x_vars)
        fig = self.canvas.figure
        axes = fig.subplots(nrows, ncols, squeeze=False,
                            sharex="col", sharey="row")
        for i, y_col in enumerate(y_vars):
            for j, x_col in enumerate(x_vars):
                ax = axes[i][j]
                for label, sub, gs in groups_data:
                    self._plot_group(ax, sub, label, gs, x_col, y_col,
                                      shaded=getattr(gs, "shaded", False))
                if show_reg:
                    self._draw_regression(ax, df, x_col, y_col,
                                          ctrl.regression_grp)
                self._draw_reservoirs([ax], x_col, y_col, reservoir_names,
                                      annotate=(i == 0 and j == ncols - 1))
                if ctrl.axis_grp.log_x.isChecked():
                    ax.set_xscale("log")
                if ctrl.axis_grp.log_y.isChecked():
                    ax.set_yscale("log")
                if i == nrows - 1:
                    ax.set_xlabel(x_col,
                                  **ctrl.axis_grp.axis_style(x_col).label_kwargs())
                if j == 0:
                    ax.set_ylabel(y_col,
                                  **ctrl.axis_grp.axis_style(y_col).label_kwargs())
                ax.tick_params(labelsize=max(ctrl.axis_grp.font_size.value() - 4, 6))
                ax.set_box_aspect(1)
                self._paired_panel_done(ax, x_col, y_col)

        if legend.visible:
            handles, labels = axes[0][0].get_legend_handles_labels()
            if handles:
                fig.legend(handles, labels, loc="upper center",
                           ncol=min(len(labels), 6),
                           fontsize=legend.font_size, title=legend.title,
                           bbox_to_anchor=(0.5, 1.0))
                fig.subplots_adjust(top=0.9)
        fig.tight_layout()
        from .brushing import draw_selection_overlay
        draw_selection_overlay(self)
        self.canvas.draw()

    # ------------------------------------------------------- reservoirs
    @staticmethod
    def _draw_reservoirs(axes, x_col: str, y_col: str,
                         names: list[str], annotate: bool = True) -> None:
        """Overlay reference reservoirs on every ax.

        ``x_col`` / ``y_col`` may be plain element names or arithmetic
        expressions; reservoir compositions are evaluated through
        :func:`evaluate_scalar`, so e.g. *La/Yb* of the Primitive Mantle
        is computed on the fly and a reservoir is silently skipped when
        any referenced element is missing from its composition.
        """
        if not names:
            return
        for ax in axes:
            for name in names:
                composition = RESERVOIRS.get(name)
                if composition is None:
                    continue
                xv = evaluate_scalar(composition, x_col)
                yv = evaluate_scalar(composition, y_col)
                if xv is None or yv is None:
                    continue
                ax.scatter([xv], [yv], marker="*", s=180, c="white",
                           edgecolors="black", linewidths=1.2, zorder=5)
                if annotate:
                    short = name.split(" (")[0]
                    ax.annotate(short, (xv, yv), xytext=(6, 6),
                                textcoords="offset points",
                                fontsize=8, color="#222",
                                bbox=dict(facecolor="white", edgecolor="#888",
                                          alpha=0.85, boxstyle="round,pad=0.2"))

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
            "Use the panel on the left. Per-group styling is in "
            "Data → Edit plot."
        )

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        from .. import widget_state as ws
        ind = self._individual
        paired = self._paired
        return {
            "mode": self._mode,
            "individual": {
                "x": ind.x_combo.currentText(),
                "y": ind.y_combo.currentText(),
                "axis": ws.axis_group_state(ind.axis_grp),
                "legend": ws.legend_group_state(ind.legend_grp),
                "grouping": ws.grouping_group_state(ind.grouping_grp),
                "regression": ws.regression_group_state(ind.regression_grp),
                "reservoirs": ws.reservoirs_state(ind.reservoirs_grp),
                # User-placed annotations (lines, arrows, text, sample
                # identifiers) for the Individual single-panel mode.
                "annotations": _ann.serialize(self._annotations),
            },
            "paired": {
                "x_list": ws.list_selection(paired.x_list),
                "y_list": ws.list_selection(paired.y_list),
                "grid_layout": paired.grid_layout_combo.currentData(),
                "axis": ws.axis_group_state(paired.axis_grp),
                "legend": ws.legend_group_state(paired.legend_grp),
                "grouping": ws.grouping_group_state(paired.grouping_grp),
                "regression": ws.regression_group_state(paired.regression_grp),
                "reservoirs": ws.reservoirs_state(paired.reservoirs_grp),
                # Annotations with the panel (X-Y pair) each is on.
                "annotations": [
                    {"x": x_col, "y": y_col, "annotation": ann.to_dict()}
                    for (x_col, y_col), ann in self._paired_annotations],
            },
        }

    def restore(self, state: dict) -> None:
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QListWidgetItem
        from .. import widget_state as ws
        if not state:
            return

        # Make sure both panels have been populated with the current
        # dataset's column lists before applying restored state.
        self._refresh_variable_lists()

        ind = self._individual
        paired = self._paired

        ind_s = state.get("individual", {})
        if ind_s:
            ws.restore_combo(ind.x_combo, {"text": ind_s.get("x", "")})
            ws.restore_combo(ind.y_combo, {"text": ind_s.get("y", "")})
            ws.restore_axis_group(ind.axis_grp, ind_s.get("axis"))
            ws.restore_legend_group(ind.legend_grp, ind_s.get("legend"))
            ws.restore_grouping_group(ind.grouping_grp, ind_s.get("grouping"))
            ws.restore_regression_group(ind.regression_grp,
                                        ind_s.get("regression"))
            ws.restore_reservoirs(ind.reservoirs_grp,
                                  ind_s.get("reservoirs"))
            # Restore user-placed annotations and refresh the list view.
            self._annotations = _ann.deserialize(ind_s.get("annotations"))
            ind.annotations_grp.refresh(self._annotations)

        paired_s = state.get("paired", {})
        if paired_s:
            # Factory recreates the magenta styling on restored expressions
            def _purple(text: str) -> QListWidgetItem:
                it = QListWidgetItem(text)
                it.setData(Qt.ItemDataRole.UserRole, "expr")
                it.setForeground(Qt.GlobalColor.darkMagenta)
                return it
            ws.restore_list_selection(paired.x_list,
                                      paired_s.get("x_list"),
                                      item_factory=_purple)
            ws.restore_list_selection(paired.y_list,
                                      paired_s.get("y_list"),
                                      item_factory=_purple)
            code = paired_s.get("grid_layout")
            if code:
                idx = paired.grid_layout_combo.findData(code)
                if idx >= 0:
                    paired.grid_layout_combo.setCurrentIndex(idx)
            ws.restore_axis_group(paired.axis_grp, paired_s.get("axis"))
            ws.restore_legend_group(paired.legend_grp, paired_s.get("legend"))
            ws.restore_grouping_group(paired.grouping_grp,
                                      paired_s.get("grouping"))
            ws.restore_regression_group(paired.regression_grp,
                                        paired_s.get("regression"))
            ws.restore_reservoirs(paired.reservoirs_grp,
                                  paired_s.get("reservoirs"))
            self._paired_annotations = []
            for entry in paired_s.get("annotations") or []:
                if not isinstance(entry, dict):
                    continue
                anns = _ann.deserialize([entry.get("annotation")])
                if anns and entry.get("x") and entry.get("y"):
                    self._paired_annotations.append(
                        ((str(entry["x"]), str(entry["y"])), anns[0]))

        self.set_mode(state.get("mode", "individual"))
        self._refresh_ann_list()
