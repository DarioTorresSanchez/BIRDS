"""Reusable control-panel widgets shared across diagram views."""

from __future__ import annotations

from PySide6.QtCore import SIGNAL, Qt, QTimer, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QAbstractSpinBox,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..diagrams.templates.base import AxisStyle, LegendStyle
from ..reservoirs import RESERVOIR_CATEGORIES


# Annotation tool keys exchanged with the bivariate view.
ANN_MODE_NONE   = ""
ANN_MODE_LINE   = "line"
ANN_MODE_ARROW  = "arrow"
ANN_MODE_TEXT   = "text"
ANN_MODE_SAMPLE = "sample"


#: The change signal of each kind of control :func:`make_live` follows.
_LIVE_SIGNALS = (
    (QCheckBox, "toggled", "toggled(bool)"),
    (QComboBox, "currentIndexChanged", "currentIndexChanged(int)"),
    (QSpinBox, "valueChanged", "valueChanged(int)"),
    (QDoubleSpinBox, "valueChanged", "valueChanged(double)"),
    (QLineEdit, "editingFinished", "editingFinished()"),
    (QGroupBox, "toggled", "toggled(bool)"),
)

#: How long a burst of changes -- a spin box held down, a radio pair
#: swapping -- is gathered into one redraw.
LIVE_DELAY_MS = 150


def make_live(container, redraw, *, delay_ms: int = LIVE_DELAY_MS) -> int:
    """Redraw as soon as a control under *container* changes.

    Most panel controls -- log scale, legend, fonts, axis titles, the
    regression line, the isotope reservoirs, the map's options -- used to
    take effect only on *Update plot*, while the diagram and normaliser
    pickers redrew at once; the difference read as controls that did not
    respond.  Every control not already wired to something gets a
    connection to one debounced *redraw*.  Call it before the main
    window wires its "modified" tracking, so a connection there is not
    mistaken for a live one; mark a control that must not redraw with
    ``setProperty("liveExempt", True)``.  Returns how many were wired.
    """
    timer = QTimer(container)
    timer.setSingleShot(True)
    timer.setInterval(delay_ms)
    timer.timeout.connect(redraw)

    def kick(*_args) -> None:
        timer.start()

    wired = 0
    for kind, name, signature in _LIVE_SIGNALS:
        for widget in container.findChildren(kind):
            if widget.property("liveExempt") or getattr(widget, "_live", False):
                continue
            if kind is QGroupBox and not widget.isCheckable():
                continue
            if kind is QLineEdit and isinstance(
                    widget.parentWidget(), (QAbstractSpinBox, QComboBox)):
                continue                  # a spin box's or combo's own edit
            if widget.receivers(SIGNAL(signature)) > 0:
                continue                  # already redraws, or does its job
            getattr(widget, name).connect(kick)
            widget._live = True
            wired += 1
    return wired


FONT_CHOICES = (
    "DejaVu Sans", "Arial", "Helvetica", "Times New Roman", "Courier New",
)
LEGEND_LOCATIONS = (
    "best", "upper right", "upper left", "lower left", "lower right",
    "center", "outside",
)


class AxisGroup(QGroupBox):
    """Axis labels + font + log-scale controls."""

    def __init__(self, title: str = "Axes (labels and font)") -> None:
        super().__init__(title)
        form = QFormLayout(self)
        self.x_label_edit = QLineEdit()
        form.addRow("X label override:", self.x_label_edit)
        self.y_label_edit = QLineEdit()
        form.addRow("Y label override:", self.y_label_edit)
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 32)
        self.font_size.setValue(12)
        form.addRow("Font size:", self.font_size)
        self.font_family = QComboBox()
        self.font_family.addItems(FONT_CHOICES)
        form.addRow("Font family:", self.font_family)
        style_row = QHBoxLayout()
        self.bold = QCheckBox("Bold")
        self.italic = QCheckBox("Italic")
        style_row.addWidget(self.bold)
        style_row.addWidget(self.italic)
        style_row.addStretch()
        form.addRow("Style:", style_row)
        self.log_x = QCheckBox("Log scale on X")
        self.log_y = QCheckBox("Log scale on Y")
        form.addRow("", self.log_x)
        form.addRow("", self.log_y)

    def axis_style(self, label: str | None = None) -> AxisStyle:
        return AxisStyle(
            label=label,
            font_size=self.font_size.value(),
            font_family=self.font_family.currentText(),
            font_weight="bold" if self.bold.isChecked() else "normal",
            font_style="italic" if self.italic.isChecked() else "normal",
        )


class LegendGroup(QGroupBox):
    def __init__(self, title: str = "Legend") -> None:
        super().__init__(title)
        form = QFormLayout(self)
        self.visible = QCheckBox("Show legend")
        self.visible.setChecked(True)
        form.addRow("", self.visible)
        self.title_edit = QLineEdit()
        form.addRow("Title:", self.title_edit)
        self.location = QComboBox()
        self.location.addItems(LEGEND_LOCATIONS)
        form.addRow("Location:", self.location)
        self.font_size = QSpinBox()
        self.font_size.setRange(6, 24)
        self.font_size.setValue(10)
        form.addRow("Font size:", self.font_size)

    def legend_style(self) -> LegendStyle:
        return LegendStyle(
            visible=self.visible.isChecked(),
            location=self.location.currentText(),
            font_size=self.font_size.value(),
            title=self.title_edit.text().strip() or None,
        )


class AdjustedMajorsBox(QGroupBox):
    """Which major-element values a view plots: adjusted, or as analysed.

    One per view that reads majors, all showing the same switch -- the
    state lives in the DataManager, so ticking it in one view changes
    every view, and the statistics, the diagrams and the norm cannot
    disagree.  The owning view connects :attr:`toggled`, and calls
    :meth:`sync` before it draws so the box shows the shared state.
    """

    toggled = Signal(bool)

    def __init__(self, title: str = "Major elements") -> None:
        super().__init__(title)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(4)
        self.check = QCheckBox("Use majors adjusted to 100 %")
        self.check.setToolTip(
            "Plot SiO2_adj, TiO2_adj, … — the values Data → Pre-process "
            "majors… adjusted — in place of the analysed ones. The same "
            "switch appears in every view that reads major elements.")
        self.check.toggled.connect(self.toggled.emit)
        layout.addWidget(self.check)
        self.status = QLabel()
        self.status.setWordWrap(True)
        self.status.setTextFormat(Qt.TextFormat.RichText)
        self.status.setStyleSheet("font-size: 11px;")
        layout.addWidget(self.status)

    def sync(self, data) -> None:
        """Show the DataManager's state without firing :attr:`toggled`."""
        from ..preprocess import describe_adjustment, has_adjusted

        available = has_adjusted(data.df)
        on = available and data.use_adjusted
        self.check.blockSignals(True)
        self.check.setEnabled(available)
        self.check.setChecked(on)
        self.check.blockSignals(False)
        if on:
            how = describe_adjustment(data.adjust_settings)
            text = (f"<span style='color:#1f4e99'><b>● Adjusted</b></span> "
                    f"— {how}. The analysed values are kept.")
        elif available:
            text = ("<span style='color:#5b6478'><b>● As analysed.</b></span> "
                    "Adjusted copies exist; tick to plot them.")
        else:
            text = ("<span style='color:#5b6478'><b>● As analysed.</b></span> "
                    "<i>Data → Pre-process majors…</i> adds adjusted copies "
                    "(SiO2_adj, …) and keeps these.")
        self.status.setText(text)


class GroupingGroup(QGroupBox):
    """Per-group visibility toggles + facet (separate-plot) checkbox.

    Each ``PlotStyle.groups[i]`` is mapped to a checkbox here, so the
    user can hide / show specific groups in the current view *without*
    going through the Edit plot dialog.  Toggling a checkbox flips
    ``GroupStyle.visible`` on the shared style object and emits
    :py:attr:`visibility_changed` so the view can redraw.

    Call :meth:`set_groups` whenever the underlying ``PlotStyle.groups``
    list changes (e.g. after Edit plot or after loading a session).
    """

    # Re-emitted on any per-group toggle.  No argument — handlers just
    # call ``update_plot``.
    visibility_changed = Signal()

    def __init__(self, title: str = "Grouping") -> None:
        super().__init__(title)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 12, 8, 8)
        self._layout.setSpacing(4)

        self.facet_chk = QCheckBox("Separate plot by group (facet)")
        self._layout.addWidget(self.facet_chk)

        # Header for the per-group section.  Hidden when no groups exist.
        self._groups_header = QLabel("<b>Show groups:</b>")
        self._groups_header.setTextFormat(Qt.TextFormat.RichText)
        self._groups_header.setStyleSheet(
            "color: #1c2237; font-size: 11px; margin-top: 4px;"
        )
        self._layout.addWidget(self._groups_header)

        # Container that holds the dynamic per-group checkboxes.  We
        # rebuild it from scratch in ``set_groups`` because the group
        # list can grow / shrink / be renamed between calls.
        self._groups_container = QWidget()
        self._groups_layout = QVBoxLayout(self._groups_container)
        self._groups_layout.setContentsMargins(0, 0, 0, 0)
        self._groups_layout.setSpacing(2)
        self._layout.addWidget(self._groups_container)

        self._select_row = QWidget()
        select_row_l = QHBoxLayout(self._select_row)
        select_row_l.setContentsMargins(0, 0, 0, 0)
        select_row_l.setSpacing(6)
        self._all_btn = QPushButton("All")
        self._all_btn.setMaximumWidth(50)
        self._none_btn = QPushButton("None")
        self._none_btn.setMaximumWidth(50)
        select_row_l.addWidget(self._all_btn)
        select_row_l.addWidget(self._none_btn)
        select_row_l.addStretch(1)
        self._layout.addWidget(self._select_row)
        self._all_btn.clicked.connect(lambda: self._set_all(True))
        self._none_btn.clicked.connect(lambda: self._set_all(False))

        self._group_checks: list[QCheckBox] = []
        self._plot_style = None  # set via set_groups()

        # Initial state: hide the per-group section until set_groups
        # is called.
        self._set_groups_visible(False)

    # ------------------------------------------------------------------
    def set_groups(self, plot_style) -> None:
        """Rebuild the per-group checkbox list from ``plot_style.groups``.

        Must be called once after the GroupingGroup is created and again
        whenever the group list changes (typically after Edit plot or
        after loading a session).
        """
        self._plot_style = plot_style

        # Tear down previous checkboxes.
        while self._groups_layout.count():
            item = self._groups_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()
        self._group_checks = []

        groups = getattr(plot_style, "groups", []) if plot_style else []
        if not groups:
            self._set_groups_visible(False)
            return

        for i, g in enumerate(groups):
            cb = QCheckBox(g.name)
            # Small colour swatch so the user can read the symbol legend
            # straight from this widget.
            cb.setStyleSheet(
                f"QCheckBox::indicator:checked {{ background-color: {g.color}; }}"
                "QCheckBox { padding: 2px 0; }"
            )
            cb.setChecked(bool(g.visible))
            # Capture the index of THIS checkbox so the lambda doesn't
            # close over the loop variable.
            cb.toggled.connect(
                lambda checked, idx=i: self._on_group_toggled(idx, checked)
            )
            self._groups_layout.addWidget(cb)
            self._group_checks.append(cb)

        self._set_groups_visible(True)

    # ------------------------------------------------------------------
    def visible_group_names(self) -> list[str]:
        """Return the names of groups that are currently ticked."""
        if not self._plot_style:
            return []
        return [
            g.name for i, g in enumerate(self._plot_style.groups)
            if i < len(self._group_checks) and self._group_checks[i].isChecked()
        ]

    # ------------------------------------------------------------------
    def _on_group_toggled(self, idx: int, checked: bool) -> None:
        """Mirror the checkbox state into ``PlotStyle.groups[idx].visible``."""
        if (self._plot_style is not None
                and 0 <= idx < len(self._plot_style.groups)):
            self._plot_style.groups[idx].visible = bool(checked)
        self.visibility_changed.emit()

    def _set_all(self, value: bool) -> None:
        """Tick / untick every checkbox at once."""
        for cb in self._group_checks:
            # blockSignals prevents N redraws — we emit once at the end.
            cb.blockSignals(True)
            cb.setChecked(value)
            cb.blockSignals(False)
        if self._plot_style:
            for g in self._plot_style.groups:
                g.visible = value
        self.visibility_changed.emit()

    def _set_groups_visible(self, on: bool) -> None:
        """Show / hide the per-group section as a block."""
        self._groups_header.setVisible(on)
        self._groups_container.setVisible(on)
        self._select_row.setVisible(on)


class RegressionGroup(QGroupBox):
    """Linear-regression overlay controls (used by bivariate)."""

    def __init__(self) -> None:
        super().__init__("Linear regression")
        form = QFormLayout(self)
        self.show = QCheckBox("Add linear regression line")
        form.addRow("", self.show)
        self.per_group = QCheckBox("Fit per group (else: overall)")
        form.addRow("", self.per_group)
        self.show_label = QCheckBox("Show equation + R² in legend")
        self.show_label.setChecked(True)
        form.addRow("", self.show_label)
        self.ci_chk = QCheckBox("Shade 95 % confidence interval")
        form.addRow("", self.ci_chk)


# Default line styles cycled through new reservoirs.  Matplotlib short
# names so they're directly usable in ax.plot().
_DEFAULT_LINESTYLES = ("--", ":", "-.", "-")
_DEFAULT_COLORS = ("#222222", "#1f3a93", "#117a37", "#b13a3a",
                   "#d4a017", "#6d28d9", "#0891b2")
_LINESTYLE_LABELS = (
    ("solid",      "-"),
    ("dashed",     "--"),
    ("dotted",     ":"),
    ("dash-dot",   "-.")
)
_MARKER_LABELS = (
    ("none",        ""),
    ("circle",      "o"),
    ("square",      "s"),
    ("triangle",    "^"),
    ("diamond",     "D"),
    ("star",        "*"),
    ("plus",        "+"),
    ("x",           "x"),
)


class ReservoirGroup(QGroupBox):
    """A checkable tree of reservoirs grouped by reference.

    Each checked reservoir gets an inline style editor (colour, line
    style, line width, marker) so the user can tell two overlays apart
    when the default cycle isn't enough.  ``styles_changed`` is emitted
    whenever any of those controls is touched so the parent view can
    refresh the plot.
    """

    # Re-emitted whenever the tree check-state OR any per-reservoir
    # style changes.  Parent view connects this to ``update_plot``.
    styles_changed = Signal()

    def __init__(self, title: str = "Reservoirs (reference compositions)",
                 only=None, note: str = "") -> None:
        """*only*, a predicate on the reservoir name, keeps the entries a
        view can draw; *note* says what was left out."""
        super().__init__(title)
        self._only = only
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setSpacing(4)
        intro = QLabel(
            "Tick reservoirs to overlay them on the plot. Sources are cited "
            "next to each entry. Major elements in wt.%, traces in ppm."
            + (f" {note}" if note else "")
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #6c7388; font-size: 11px;")
        layout.addWidget(intro)
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tree.itemChanged.connect(self._on_tree_changed)
        layout.addWidget(self.tree)

        # Per-reservoir style editor — only the editors for currently
        # ticked reservoirs are shown; the rest is hidden.
        self._styles: dict[str, dict] = {}   # name -> {color, ls, lw, marker}
        self._editors: dict[str, QWidget] = {}  # name -> editor row widget
        self._editor_header = QLabel("<b>Reservoir line styles:</b>")
        self._editor_header.setTextFormat(Qt.TextFormat.RichText)
        self._editor_header.setStyleSheet(
            "color: #1c2237; font-size: 11px; margin-top: 6px;"
        )
        self._editor_header.setVisible(False)
        layout.addWidget(self._editor_header)
        self._editor_container = QWidget()
        self._editor_layout = QVBoxLayout(self._editor_container)
        self._editor_layout.setContentsMargins(0, 0, 0, 0)
        self._editor_layout.setSpacing(2)
        layout.addWidget(self._editor_container)

        self._populate()

    def _populate(self) -> None:
        for category, names in RESERVOIR_CATEGORIES.items():
            if self._only is not None:
                names = [n for n in names if self._only(n)]
            if not names:
                continue
            parent = QTreeWidgetItem(self.tree, [category])
            parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsAutoTristate
                            | Qt.ItemFlag.ItemIsUserCheckable)
            parent.setCheckState(0, Qt.CheckState.Unchecked)
            font = parent.font(0)
            font.setBold(True)
            parent.setFont(0, font)
            for name in names:
                child = QTreeWidgetItem(parent, [name])
                child.setFlags(child.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                child.setCheckState(0, Qt.CheckState.Unchecked)
                child.setData(0, Qt.ItemDataRole.UserRole, name)
        self.tree.expandAll()

    def selected_reservoirs(self) -> list[str]:
        out: list[str] = []
        for i in range(self.tree.topLevelItemCount()):
            parent = self.tree.topLevelItem(i)
            for j in range(parent.childCount()):
                child = parent.child(j)
                if child.checkState(0) == Qt.CheckState.Checked:
                    name = child.data(0, Qt.ItemDataRole.UserRole)
                    if name:
                        out.append(str(name))
        return out

    # ------------------------------------------------------------------
    # Style API — called by the spider view at plot time.
    # ------------------------------------------------------------------
    def style_for(self, name: str, index: int = 0) -> dict:
        """Return ``{color, linestyle, linewidth, marker}`` for the named
        reservoir.  Creates a default if the user hasn't customised it
        yet — ``index`` (position in the checked list) seeds the default
        colour / linestyle cycle so two adjacent reservoirs don't get
        identical styling out of the box.
        """
        if name not in self._styles:
            self._styles[name] = {
                "color": _DEFAULT_COLORS[index % len(_DEFAULT_COLORS)],
                "linestyle": _DEFAULT_LINESTYLES[
                    index % len(_DEFAULT_LINESTYLES)],
                "linewidth": 1.8,
                "marker": "",
            }
        return self._styles[name]

    def all_styles(self) -> dict[str, dict]:
        """Snapshot of every customised style (for session save)."""
        return dict(self._styles)

    def restore_styles(self, data: dict | None) -> None:
        if not data:
            return
        for name, style in data.items():
            if isinstance(style, dict):
                self._styles[name] = dict(style)
        self._rebuild_editors()

    # ------------------------------------------------------------------
    # Editor rows
    # ------------------------------------------------------------------
    def _on_tree_changed(self, _item, _col) -> None:
        self._rebuild_editors()
        self.styles_changed.emit()

    def _rebuild_editors(self) -> None:
        """Show one editor row per checked reservoir.  Reuses existing
        widgets where possible so the user doesn't lose focus mid-edit.
        """
        active = self.selected_reservoirs()
        # Hide editors for reservoirs no longer checked.
        for name, row in list(self._editors.items()):
            if name not in active:
                row.setVisible(False)
        # Create or show editors for the ones now checked.
        for i, name in enumerate(active):
            self.style_for(name, index=i)  # ensure default exists
            if name in self._editors:
                self._editors[name].setVisible(True)
            else:
                self._editors[name] = self._build_editor_row(name)
                self._editor_layout.addWidget(self._editors[name])
        self._editor_header.setVisible(bool(active))

    def _build_editor_row(self, name: str) -> QWidget:
        """One compact horizontal row: [colour] [linestyle] [width] [marker]
        prefixed with the reservoir short name."""
        style = self._styles[name]
        row = QFrame()
        row.setFrameShape(QFrame.Shape.NoFrame)
        rl = QHBoxLayout(row)
        rl.setContentsMargins(2, 2, 2, 2)
        rl.setSpacing(4)
        short = name.split(" (")[0]
        if len(short) > 18:
            short = short[:17] + "…"
        lbl = QLabel(short)
        lbl.setMinimumWidth(140)
        lbl.setStyleSheet("font-size: 11px; color: #1c2237;")
        lbl.setToolTip(name)
        rl.addWidget(lbl)

        color_btn = ColorButton(style["color"])
        color_btn.setFixedSize(38, 22)
        color_btn.setToolTip("Line colour")
        def _on_color(_=None, n=name, btn=color_btn):
            self._styles[n]["color"] = btn.color
            self.styles_changed.emit()
        color_btn.clicked.connect(_on_color)
        rl.addWidget(color_btn)

        ls_combo = QComboBox()
        for label, value in _LINESTYLE_LABELS:
            ls_combo.addItem(label, value)
        idx = next((i for i, (_, v) in enumerate(_LINESTYLE_LABELS)
                    if v == style["linestyle"]), 1)
        ls_combo.setCurrentIndex(idx)
        ls_combo.setMaximumWidth(80)
        ls_combo.setToolTip("Line style")
        def _on_ls(_idx=None, n=name, cb=ls_combo):
            self._styles[n]["linestyle"] = cb.currentData()
            self.styles_changed.emit()
        ls_combo.currentIndexChanged.connect(_on_ls)
        rl.addWidget(ls_combo)

        lw_spin = QDoubleSpinBox()
        lw_spin.setRange(0.2, 6.0)
        lw_spin.setSingleStep(0.2)
        lw_spin.setDecimals(1)
        lw_spin.setValue(style["linewidth"])
        lw_spin.setMaximumWidth(60)
        lw_spin.setToolTip("Line width (pt)")
        def _on_lw(_v=None, n=name, sp=lw_spin):
            self._styles[n]["linewidth"] = float(sp.value())
            self.styles_changed.emit()
        lw_spin.valueChanged.connect(_on_lw)
        rl.addWidget(lw_spin)

        mk_combo = QComboBox()
        for label, value in _MARKER_LABELS:
            mk_combo.addItem(label, value)
        idx = next((i for i, (_, v) in enumerate(_MARKER_LABELS)
                    if v == style.get("marker", "")), 0)
        mk_combo.setCurrentIndex(idx)
        mk_combo.setMaximumWidth(80)
        mk_combo.setToolTip("Marker on each element")
        def _on_mk(_idx=None, n=name, cb=mk_combo):
            self._styles[n]["marker"] = cb.currentData()
            self.styles_changed.emit()
        mk_combo.currentIndexChanged.connect(_on_mk)
        rl.addWidget(mk_combo)

        rl.addStretch(1)
        return row


class ColorButton(QPushButton):
    """A button whose face displays the currently-selected colour."""

    def __init__(self, color: str = "#1f77b4", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = color
        self.setFixedSize(56, 28)
        self.clicked.connect(self._pick)
        self._refresh()

    @property
    def color(self) -> str:
        return self._color

    def set_color(self, color: str) -> None:
        self._color = color
        self._refresh()

    def _pick(self) -> None:
        chosen = QColorDialog.getColor(QColor(self._color), self, "Choose colour")
        if chosen.isValid():
            self._color = chosen.name()
            self._refresh()

    def _refresh(self) -> None:
        self.setStyleSheet(
            f"background-color: {self._color}; border: 1px solid #888;"
            " border-radius: 4px;"
        )


class AnnotationGroup(QGroupBox):
    """Paint-style toolbar for placing user annotations on a bivariate plot.

    Four toggle buttons (line / arrow / text / sample identifier) plus a
    Clear-all button.  Selecting a button arms the view's canvas click
    handler; the view emits ``annotation_added`` to refresh the list.

    Signals
    -------
    * ``mode_requested(str)`` — one of ``ANN_MODE_*``.  Empty string
      cancels the current mode.
    * ``clear_requested()`` — user pressed "Clear all".
    * ``delete_index(int)`` — user double-clicked a list row to delete.
    """

    mode_requested = Signal(str)
    clear_requested = Signal()
    delete_index = Signal(int)

    def __init__(self, title: str = "Annotations") -> None:
        super().__init__(title)
        v = QVBoxLayout(self)
        v.setContentsMargins(8, 12, 8, 8)
        v.setSpacing(4)

        intro = QLabel(
            "Pick a tool, then click on the plot.  Lines / arrows need "
            "two clicks (start + end); text and sample-ID just one."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #6c7388; font-size: 11px;")
        v.addWidget(intro)

        tools = QHBoxLayout()
        tools.setSpacing(4)
        self.btn_line   = self._make_tool("Line",   ANN_MODE_LINE)
        self.btn_arrow  = self._make_tool("Arrow",  ANN_MODE_ARROW)
        self.btn_text   = self._make_tool("Text",   ANN_MODE_TEXT)
        self.btn_sample = self._make_tool("Identify sample", ANN_MODE_SAMPLE)
        for b in (self.btn_line, self.btn_arrow, self.btn_text, self.btn_sample):
            tools.addWidget(b)
        v.addLayout(tools)

        self.status_lbl = QLabel("No tool active.")
        self.status_lbl.setStyleSheet("color: #5b6478; font-size: 10px;")
        self.status_lbl.setWordWrap(True)
        v.addWidget(self.status_lbl)

        # Use QListWidget (already imported by spider, but we re-import
        # locally to avoid touching the existing imports list).
        from PySide6.QtWidgets import QListWidget
        self.list = QListWidget()
        self.list.setMaximumHeight(120)
        self.list.itemDoubleClicked.connect(
            lambda item: self.delete_index.emit(self.list.row(item)))
        v.addWidget(self.list)

        row = QHBoxLayout()
        row.setSpacing(4)
        self.clear_btn = QPushButton("Clear all")
        self.clear_btn.clicked.connect(self.clear_requested.emit)
        row.addWidget(self.clear_btn)
        row.addStretch(1)
        hint = QLabel("Double-click a row to delete it.")
        hint.setStyleSheet("color: #6c7388; font-size: 10px;")
        row.addWidget(hint)
        v.addLayout(row)

        self._buttons = {
            ANN_MODE_LINE: self.btn_line,
            ANN_MODE_ARROW: self.btn_arrow,
            ANN_MODE_TEXT: self.btn_text,
            ANN_MODE_SAMPLE: self.btn_sample,
        }
        self._current_mode = ANN_MODE_NONE

    def _make_tool(self, label: str, mode: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setCheckable(True)
        btn.clicked.connect(lambda checked, m=mode: self._on_tool(m, checked))
        return btn

    def _on_tool(self, mode: str, checked: bool) -> None:
        # Exclusive toggle — un-check siblings.
        for m, b in self._buttons.items():
            if m != mode:
                b.setChecked(False)
        if not checked:
            self._current_mode = ANN_MODE_NONE
            self.status_lbl.setText("No tool active.")
            self.mode_requested.emit(ANN_MODE_NONE)
            return
        self._current_mode = mode
        hints = {
            ANN_MODE_LINE:   "Line — click the start, then the end on the plot.",
            ANN_MODE_ARROW:  "Arrow — click the tail, then the head on the plot.",
            ANN_MODE_TEXT:   "Text — click where the label should sit.",
            ANN_MODE_SAMPLE: "Identify — click near a sample point.",
        }
        self.status_lbl.setText(hints.get(mode, ""))
        self.mode_requested.emit(mode)

    def cancel_mode(self) -> None:
        """Called by the view after an annotation is placed (or the user
        right-clicks) so the toolbar resets to no-tool state."""
        for b in self._buttons.values():
            b.setChecked(False)
        self._current_mode = ANN_MODE_NONE
        self.status_lbl.setText("No tool active.")

    def refresh(self, annotations: list) -> None:
        """Repopulate the list from the current annotation collection."""
        self.list.clear()
        for ann in annotations:
            kind = getattr(ann, "kind", "?")
            if kind == "line":
                desc = f"Line  ({ann.x1:.2f}, {ann.y1:.2f}) → ({ann.x2:.2f}, {ann.y2:.2f})"
            elif kind == "arrow":
                lbl = f" — {ann.label}" if ann.label else ""
                desc = f"Arrow ({ann.x1:.2f}, {ann.y1:.2f}) → ({ann.x2:.2f}, {ann.y2:.2f}){lbl}"
            elif kind == "text":
                snip = ann.text[:24] + ("…" if len(ann.text) > 24 else "")
                desc = f"Text  ({ann.x:.2f}, {ann.y:.2f}) “{snip}”"
            elif kind == "sample":
                desc = f"Sample  ({ann.px:.2f}, {ann.py:.2f}) → {ann.label}"
            else:
                desc = f"{kind}"
            self.list.addItem(desc)
