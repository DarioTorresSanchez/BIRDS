"""Configure marker size, transparency, sample groups and styling."""

from __future__ import annotations

from typing import Optional

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..plot_style import DEFAULT_COLORS, DEFAULT_MARKERS, GroupStyle, PlotStyle


MAX_GROUPS = 10
MAX_GROUPING_COLUMNS = 3


MARKER_CHOICES: tuple[tuple[str, str], ...] = (
    ("Circle",        "o"),
    ("Square",        "s"),
    ("Triangle up",   "^"),
    ("Triangle down", "v"),
    ("Diamond",       "D"),
    ("Star",          "*"),
    ("Plus",          "P"),
    ("Cross",         "X"),
    ("Pentagon",      "p"),
    ("Hexagon",       "h"),
)


# ---------------------------------------------------------------------------
# Small reusable widgets
# ---------------------------------------------------------------------------

class ColorButton(QPushButton):
    """A button whose face displays the currently-selected color."""

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


class GroupRow(QWidget):
    """One row in the groups table.

    Layout: ↑↓ reorder buttons + visible toggle + name + colour + marker
    style + per-group "show markers" toggle + per-group "shade hull"
    toggle. Markers and hull can be turned on/off independently, so the
    user gets:

    * markers only (the default)
    * markers + hull
    * hull only (for a clean field outline)

    The row's position in the parent dialog dictates the **draw order**:
    earlier rows are drawn first (i.e. behind), later rows on top. The
    legend follows the same order.
    """

    def __init__(
        self,
        index: int,
        name: str,
        color: str,
        marker: str,
        *,
        visible: bool = True,
        show_markers: bool = True,
        shaded: bool = False,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.tag = QLabel(f"#{index + 1}")
        self.tag.setFixedWidth(28)
        self.tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tag.setStyleSheet("color: #5b6478;")
        layout.addWidget(self.tag)

        # ↑ / ↓ reorder buttons. The dialog wires their click handlers
        # because moving a row needs access to the whole row list.
        self.up_btn = QPushButton("↑")
        self.up_btn.setFixedSize(24, 24)
        self.up_btn.setToolTip(
            "Move this group up (drawn earlier — behind the others)."
        )
        layout.addWidget(self.up_btn)
        self.down_btn = QPushButton("↓")
        self.down_btn.setFixedSize(24, 24)
        self.down_btn.setToolTip(
            "Move this group down (drawn later — on top of the others)."
        )
        layout.addWidget(self.down_btn)

        # Master visibility toggle: when unticked, the group is dropped
        # entirely (no markers, no hull, no legend entry).
        self.visible_chk = QCheckBox()
        self.visible_chk.setChecked(visible)
        self.visible_chk.setToolTip(
            "Untick to hide this group from every plot and from the legend."
        )
        self.visible_chk.setFixedWidth(28)
        layout.addWidget(self.visible_chk)

        self.name_edit = QLineEdit(name)
        self.name_edit.setPlaceholderText(f"Group {index + 1} name")
        layout.addWidget(self.name_edit, stretch=2)

        self.color_btn = ColorButton(color)
        layout.addWidget(self.color_btn)

        self.marker_combo = QComboBox()
        for label, code in MARKER_CHOICES:
            self.marker_combo.addItem(label, code)
        for i in range(self.marker_combo.count()):
            if self.marker_combo.itemData(i) == marker:
                self.marker_combo.setCurrentIndex(i)
                break
        layout.addWidget(self.marker_combo, stretch=1)

        # Independent toggle for the symbol scatter
        self.show_markers_chk = QCheckBox()
        self.show_markers_chk.setChecked(show_markers)
        self.show_markers_chk.setToolTip(
            "Tick to scatter the individual sample points with the marker "
            "above. Untick to hide the points (e.g. when you only want "
            "the convex-hull envelope to act as a coloured field)."
        )
        self.show_markers_chk.setFixedWidth(28)
        layout.addWidget(self.show_markers_chk)

        # Shade toggle: when ticked, a translucent convex hull is drawn
        # around the group's points wherever per-group shading is supported.
        self.shaded_chk = QCheckBox()
        self.shaded_chk.setChecked(shaded)
        self.shaded_chk.setToolTip(
            "Tick to draw a translucent convex hull around this group. "
            "Combine with 'symbol off' to show the field only, or with "
            "'symbol on' to overlay both."
        )
        self.shaded_chk.setFixedWidth(28)
        layout.addWidget(self.shaded_chk)

    def set_position(self, index: int, n_rows: int) -> None:
        """Refresh the row's position-dependent state after a reorder.

        Updates the leading ``#N`` label, disables ↑ on the top row and
        ↓ on the bottom row.
        """
        self.tag.setText(f"#{index + 1}")
        self.up_btn.setEnabled(index > 0)
        self.down_btn.setEnabled(index < n_rows - 1)

    def to_style(self, fallback_index: int) -> GroupStyle:
        name = self.name_edit.text().strip() or f"Group {fallback_index + 1}"
        return GroupStyle(
            name=name,
            color=self.color_btn.color,
            marker=self.marker_combo.currentData(),
            visible=self.visible_chk.isChecked(),
            show_markers=self.show_markers_chk.isChecked(),
            shaded=self.shaded_chk.isChecked(),
        )


# ---------------------------------------------------------------------------
# Main dialog
# ---------------------------------------------------------------------------

class EditPlotDialog(QDialog):
    """Edit ``PlotStyle`` interactively. Use :meth:`updated_style` on accept."""

    def __init__(
        self,
        style: PlotStyle,
        dataframe: Optional[pd.DataFrame] = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit plot style")
        self.resize(720, 660)

        self._df = dataframe if isinstance(dataframe, pd.DataFrame) else None
        column_names: list[str] = (
            [str(c) for c in self._df.columns] if self._df is not None else []
        )
        self._initial_groups = list(style.groups)
        self._initial_columns = list(style.group_columns)
        self._programmatic = False  # guard against re-entrant auto-fill

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Configure marker style, colours and grouping used by every "
            "plot in B.I.R.D.S. Pick up to three columns to group your "
            "samples — names auto-fill from the data, you can still edit them."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #444;")
        layout.addWidget(intro)

        # ---- Marker style ------------------------------------------------
        marker_box = QGroupBox("Marker style")
        marker_form = QFormLayout(marker_box)

        self.size_spin = QDoubleSpinBox()
        self.size_spin.setRange(1.0, 30.0)
        self.size_spin.setSingleStep(0.5)
        self.size_spin.setValue(style.point_size)
        marker_form.addRow("Point size:", self.size_spin)

        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.05, 1.0)
        self.alpha_spin.setSingleStep(0.05)
        self.alpha_spin.setDecimals(2)
        self.alpha_spin.setValue(style.alpha)
        marker_form.addRow("Transparency (alpha):", self.alpha_spin)

        layout.addWidget(marker_box)

        # ---- Grouping ----------------------------------------------------
        groups_box = QGroupBox("Sample grouping")
        groups_layout = QVBoxLayout(groups_box)

        # Three grouping-column combo boxes
        self._col_combos: list[QComboBox] = []
        for i in range(MAX_GROUPING_COLUMNS):
            row = QHBoxLayout()
            label_text = (
                "Grouping column 1 (primary):" if i == 0
                else f"Grouping column {i + 1} (optional):"
            )
            lbl = QLabel(label_text)
            lbl.setFixedWidth(190)
            row.addWidget(lbl)
            combo = QComboBox()
            combo.addItem("(none)", "")
            for c in column_names:
                combo.addItem(c, c)
            # preselect from style
            if i < len(self._initial_columns):
                preset = self._initial_columns[i]
                idx = combo.findData(preset)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
            combo.currentIndexChanged.connect(self._on_columns_changed)
            row.addWidget(combo, stretch=1)
            groups_layout.addLayout(row)
            self._col_combos.append(combo)

        # Number of groups
        n_row = QHBoxLayout()
        n_row.addWidget(QLabel(f"Number of groups (2–{MAX_GROUPS}):"))
        self.n_groups_spin = QSpinBox()
        self.n_groups_spin.setRange(2, MAX_GROUPS)
        self.n_groups_spin.setValue(max(2, min(MAX_GROUPS, len(style.groups))))
        self.n_groups_spin.valueChanged.connect(self._on_n_groups_changed)
        n_row.addWidget(self.n_groups_spin)
        n_row.addStretch()

        self.auto_info = QLabel("")
        self.auto_info.setStyleSheet("color: #5b6478; font-size: 11px;")
        n_row.addWidget(self.auto_info)
        groups_layout.addLayout(n_row)

        # Header — column widths must match GroupRow's layout above.
        header = QHBoxLayout()
        header.setContentsMargins(0, 4, 0, 0)
        header.setSpacing(6)
        h_idx = QLabel("#")
        h_idx.setFixedWidth(28)
        h_idx.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_order = QLabel("Order")
        h_order.setFixedWidth(54)        # two 24 px buttons + 6 px gap
        h_order.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_order.setToolTip(
            "Use the ↑ / ↓ buttons to set the draw and legend order. "
            "Top of the list is drawn first (behind), bottom of the "
            "list is drawn last (on top)."
        )
        h_visible = QLabel("On")
        h_visible.setFixedWidth(28)
        h_visible.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_visible.setToolTip("Show this group on every plot")
        h_name = QLabel("Group name")
        h_color = QLabel("Colour")
        h_color.setFixedWidth(56)
        h_color.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_marker = QLabel("Symbol")
        h_show_sym = QLabel("Sym")
        h_show_sym.setFixedWidth(28)
        h_show_sym.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_show_sym.setToolTip("Scatter the individual sample points")
        h_shaded = QLabel("Hull")
        h_shaded.setFixedWidth(28)
        h_shaded.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_shaded.setToolTip("Shade this group with a translucent convex hull")
        for w in (h_idx, h_order, h_visible, h_name, h_color, h_marker,
                  h_show_sym, h_shaded):
            w.setStyleSheet("color: #5b6478; font-weight: 600;")
        header.addWidget(h_idx)
        header.addWidget(h_order)
        header.addWidget(h_visible)
        header.addWidget(h_name, stretch=2)
        header.addWidget(h_color)
        header.addWidget(h_marker, stretch=1)
        header.addWidget(h_show_sym)
        header.addWidget(h_shaded)
        groups_layout.addLayout(header)

        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(6)
        groups_layout.addLayout(self.rows_container)

        self._group_rows: list[GroupRow] = []
        # Initial population:
        #   * If the existing style already has groups whose names match
        #     the data labels (the common case after a previous Edit-plot
        #     session), preserve them — the user may have reordered,
        #     renamed or toggled them and we must not clobber that.
        #   * Otherwise (first open, or the data labels changed entirely
        #     since the last session) seed the rows from the data.
        if self._should_auto_populate_on_open():
            self._populate_from_data()
        else:
            self._rebuild_group_rows(self.n_groups_spin.value())

        layout.addWidget(groups_box, stretch=1)

        # ---- Buttons -----------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # -------------------------------------------------------------- helpers
    def _selected_columns(self) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for combo in self._col_combos:
            c = combo.currentData() or ""
            if c and c not in seen:
                out.append(c)
                seen.add(c)
        return out

    def _any_column_selected(self) -> bool:
        return bool(self._selected_columns())

    def _should_auto_populate_on_open(self) -> bool:
        """Decide whether to seed the rows from data on dialog open.

        Auto-population is *destructive* (it rewrites row names and
        resets order to data-appearance), so it should only run when
        the existing style has nothing in common with the data — for
        instance:

        * first time the dialog is opened (default styles "Group 1" /
          "Group 2" don't match any data label);
        * the dataset has been replaced and the previous group names
          no longer match any value of the grouping column.

        When at least one existing group's name matches a data label,
        we trust the user's previous configuration (including manual
        reorder, renames and per-group toggles) and only refill on
        explicit column-selector changes.
        """
        if not self._any_column_selected():
            return False
        data_labels = set(self._unique_labels(self._selected_columns()))
        if not data_labels:
            return False
        existing_names = {gs.name.strip() for gs in self._initial_groups
                          if gs.name.strip()}
        # Auto-populate only when no existing name matches any data label
        return existing_names.isdisjoint(data_labels)

    def _on_columns_changed(self, _index: int = 0) -> None:
        if self._programmatic:
            return
        if self._any_column_selected():
            self._populate_from_data()
        else:
            self.auto_info.setText("")

    def _on_n_groups_changed(self, _value: int) -> None:
        if self._programmatic:
            return
        self._rebuild_group_rows(self.n_groups_spin.value())

    def _unique_labels(self, cols: list[str]) -> list[str]:
        if self._df is None or self._df.empty or not cols:
            return []
        sub = self._df[cols]
        if len(cols) == 1:
            series = sub[cols[0]].astype("string")
            labels = series.dropna().drop_duplicates().tolist()
        else:
            joined = sub.astype("string").fillna("NA").agg(" | ".join, axis=1)
            labels = joined.dropna().drop_duplicates().tolist()
        return [str(x).strip() for x in labels if str(x).strip()]

    def _populate_from_data(self) -> None:
        cols = self._selected_columns()
        labels = self._unique_labels(cols)
        if not labels:
            self.auto_info.setText("No values found in the selected column(s).")
            return
        total = len(labels)
        if total > MAX_GROUPS:
            self.auto_info.setText(
                f"Found {total} unique combinations — showing the first {MAX_GROUPS}."
            )
        else:
            self.auto_info.setText(
                f"Auto-filled {total} group{'s' if total != 1 else ''} from "
                + " + ".join(cols)
            )
        labels = labels[:MAX_GROUPS]
        count = max(2, min(MAX_GROUPS, len(labels)))
        # Update spinner without re-triggering rebuild
        self._programmatic = True
        self.n_groups_spin.setValue(count)
        self._programmatic = False
        self._rebuild_group_rows(count, names=labels)

    def _rebuild_group_rows(
        self,
        count: int,
        names: Optional[list[str]] = None,
    ) -> None:
        # Capture existing row data (name, color, marker, visible,
        # show_markers, shaded).  The tuple lets us survive a spin-box
        # bump without losing checkbox state.
        current = [
            (row.name_edit.text(), row.color_btn.color,
             row.marker_combo.currentData(),
             row.visible_chk.isChecked(),
             row.show_markers_chk.isChecked(),
             row.shaded_chk.isChecked())
            for row in self._group_rows
        ]
        while self.rows_container.count():
            item = self.rows_container.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._group_rows = []

        for i in range(count):
            # Decide name / color / marker / flags for this row
            if names is not None and i < len(names):
                name = names[i]
            elif i < len(current):
                name = current[i][0]
            elif i < len(self._initial_groups):
                name = self._initial_groups[i].name
            else:
                name = f"Group {i + 1}"

            if i < len(current):
                color, marker = current[i][1], current[i][2]
                visible, show_markers, shaded = current[i][3:6]
            elif i < len(self._initial_groups):
                gs = self._initial_groups[i]
                color, marker = gs.color, gs.marker
                visible = gs.visible
                show_markers = getattr(gs, "show_markers", True)
                shaded = gs.shaded
            else:
                color = DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
                marker = DEFAULT_MARKERS[i % len(DEFAULT_MARKERS)]
                visible, show_markers, shaded = True, True, False

            row = GroupRow(i, name, color, marker, visible=visible,
                            show_markers=show_markers, shaded=shaded)
            # Bind the ↑/↓ buttons to dialog-level reorder; ``row=row`` in
            # the lambda captures the actual GroupRow instance instead of
            # the loop variable.
            row.up_btn.clicked.connect(lambda _=False, r=row: self._move_row(r, -1))
            row.down_btn.clicked.connect(lambda _=False, r=row: self._move_row(r, +1))
            self.rows_container.addWidget(row)
            self._group_rows.append(row)
        self._refresh_row_positions()

    # --------------------------------------------------- ordering helpers
    def _move_row(self, row: GroupRow, delta: int) -> None:
        """Swap *row* with its neighbour at offset *delta* (±1)."""
        try:
            idx = self._group_rows.index(row)
        except ValueError:
            return
        new_idx = idx + delta
        if not (0 <= new_idx < len(self._group_rows)):
            return
        # Reorder the python-side list and the Qt layout in lockstep.
        other = self._group_rows[new_idx]
        self._group_rows[idx], self._group_rows[new_idx] = other, row
        # Detach both widgets from the layout, re-insert in the new order.
        # ``QVBoxLayout.removeWidget`` is enough — the widgets stay alive.
        self.rows_container.removeWidget(row)
        self.rows_container.removeWidget(other)
        # Re-insert: rebuilding from the canonical list keeps things simple.
        # Note: rebuilding the layout is O(N) but N ≤ 10 so it's free.
        for r in self._group_rows[min(idx, new_idx):]:
            self.rows_container.removeWidget(r)
        for r in self._group_rows:
            self.rows_container.addWidget(r)
        self._refresh_row_positions()

    def _refresh_row_positions(self) -> None:
        """Update the per-row position label and arrow-button enabled state."""
        n = len(self._group_rows)
        for i, row in enumerate(self._group_rows):
            row.set_position(i, n)

    # ------------------------------------------------------------------ API
    def updated_style(self) -> PlotStyle:
        return PlotStyle(
            point_size=self.size_spin.value(),
            alpha=self.alpha_spin.value(),
            group_columns=self._selected_columns(),
            groups=[row.to_style(i) for i, row in enumerate(self._group_rows)],
        )
