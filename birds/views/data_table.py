"""Interactive data-table viewer / editor for the loaded dataset.

Shows the three sheets (Data / Isotopes / Petrography) in an editable
grid so the user can inspect exactly what B.I.R.D.S loaded, fix a typo
in place, and re-render the diagrams — closing the import → inspect →
correct loop without round-tripping through Excel.

Rows and columns can be added and removed here too: adding a *Group*
column to a table that arrived without one is the usual case, and it
is much less work than editing the source file and re-importing.

Every change — cell edits included — goes through an undo stack
(Ctrl+Z / Ctrl+Shift+Z), because a grid that writes straight into the
working dataset without one is a trap.

Below-detection cells (see :mod:`birds.detection_limits`) are tinted
amber and show the substitution in their tooltip.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd
from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QSortFilterProxyModel,
    Qt,
)
from PySide6.QtGui import QBrush, QColor, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

_BDL_BG = QColor("#FFF3D6")          # soft amber for <LD cells
_BDL_FG = QColor("#8a6d1a")

_UNDO_DEPTH = 40                     # snapshots kept per session


def _next_index(df: pd.DataFrame):
    """Index label for a row appended to *df*.

    Integer indices continue the sequence; anything else (sample names
    used as the index, dates, …) gets a distinct string so the new row
    can never collide with an existing label.
    """
    if len(df.index) == 0:
        return 0
    if pd.api.types.is_integer_dtype(df.index):
        return int(df.index.max()) + 1
    base, n = "new", 1
    existing = set(df.index)
    while f"{base}_{n}" in existing:
        n += 1
    return f"{base}_{n}"


@dataclass
class _Snapshot:
    """One undoable state of a single sheet.

    Whole-frame copies rather than deltas: geochemical tables run to a
    few thousand rows at most, and a copy is impossible to get subtly
    wrong — which a delta-based stack very much is.
    """

    sheet: str
    label: str
    df: Optional[pd.DataFrame]
    mask: Optional[pd.DataFrame]
    limits: Optional[pd.DataFrame]


class NewColumnDialog(QDialog):
    """Ask for a column name and whether it holds numbers or text."""

    def __init__(self, existing, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add column")
        self._existing = {str(c) for c in existing}

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g. Rock_type, Nd143_144, Group")
        form.addRow("Name:", self.name_edit)
        self.kind_combo = QComboBox()
        self.kind_combo.addItem("Numeric (blank cells)", "numeric")
        self.kind_combo.addItem("Text (blank cells)", "text")
        form.addRow("Type:", self.kind_combo)
        layout.addLayout(form)

        self.warning = QLabel("")
        self.warning.setStyleSheet("color: #b13a3a;")
        self.warning.setWordWrap(True)
        layout.addWidget(self.warning)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _validate(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            self.warning.setText("Give the column a name.")
            return
        if name in self._existing:
            self.warning.setText(f"'{name}' already exists in this sheet.")
            return
        self.accept()

    @property
    def column_name(self) -> str:
        return self.name_edit.text().strip()

    @property
    def is_numeric(self) -> bool:
        return self.kind_combo.currentData() == "numeric"


class DataFrameModel(QAbstractTableModel):
    """Editable Qt model over a pandas DataFrame.

    Edits write straight back into the *same* DataFrame object held by
    the DataManager, so every view sees the change on its next render.
    Numeric columns reject text that doesn't parse as a number.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._df: Optional[pd.DataFrame] = None
        self._bdl: Optional[pd.DataFrame] = None
        self._dirty_cb = None            # main-window mark_dirty hook
        self._before_change_cb = None    # view's undo-snapshot hook

    # ------------------------------------------------------------- setup
    def set_frame(self, df: Optional[pd.DataFrame],
                  bdl_mask: Optional[pd.DataFrame] = None) -> None:
        self.beginResetModel()
        self._df = df
        self._bdl = bdl_mask
        self.endResetModel()

    def set_dirty_callback(self, cb) -> None:
        self._dirty_cb = cb

    def set_before_change_callback(self, cb) -> None:
        """Called with a short label just before any edit lands."""
        self._before_change_cb = cb

    @property
    def frame(self) -> Optional[pd.DataFrame]:
        return self._df

    # ---------------------------------------------------------- Qt model
    def rowCount(self, parent=QModelIndex()) -> int:            # noqa: N802
        return 0 if (self._df is None or parent.isValid()) else len(self._df)

    def columnCount(self, parent=QModelIndex()) -> int:         # noqa: N802
        return 0 if (self._df is None or parent.isValid()) else len(self._df.columns)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole or self._df is None:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(self._df.index[section])

    def _is_bdl(self, row: int, col: int) -> bool:
        if self._bdl is None:
            return False
        colname = self._df.columns[col]
        if colname not in self._bdl.columns or row >= len(self._bdl):
            return False
        try:
            return bool(self._bdl.iloc[row][colname])
        except Exception:
            return False

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or self._df is None:
            return None
        r, c = index.row(), index.column()
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            v = self._df.iloc[r, c]
            if pd.isna(v):
                return ""
            if isinstance(v, (float, np.floating)):
                # Show floats compactly but fully editable.
                return f"{v:g}"
            return str(v)
        if role == Qt.ItemDataRole.BackgroundRole and self._is_bdl(r, c):
            return QBrush(_BDL_BG)
        if role == Qt.ItemDataRole.ForegroundRole and self._is_bdl(r, c):
            return QBrush(_BDL_FG)
        if role == Qt.ItemDataRole.ToolTipRole and self._is_bdl(r, c):
            return ("Below-detection value substituted at import "
                    "(see the Detection-limits policy in the Import dialog).")
        return None

    def flags(self, index):
        base = super().flags(index)
        return base | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):  # noqa: N802
        if role != Qt.ItemDataRole.EditRole or self._df is None:
            return False
        r, c = index.row(), index.column()
        col = self._df.columns[c]
        text = str(value).strip()
        current = self._df.iloc[r, c]

        if pd.api.types.is_numeric_dtype(self._df[col]):
            if text == "":
                new_val = np.nan
            else:
                try:
                    new_val = float(text.replace(",", "."))
                except ValueError:
                    return False           # reject non-numeric input
        else:
            new_val = text

        if (pd.isna(current) and (new_val is np.nan or new_val == "")):
            return False                   # no-op edit
        if self._before_change_cb is not None:
            self._before_change_cb(f"edit {col}")
        self._df.iloc[r, c] = new_val
        # Editing a BDL cell manually clears its flag — the user has
        # taken ownership of that value.
        if self._bdl is not None and col in self._bdl.columns:
            try:
                self._bdl.iloc[r, self._bdl.columns.get_loc(col)] = False
            except Exception:
                pass
        self.dataChanged.emit(index, index)
        if self._dirty_cb is not None:
            self._dirty_cb()
        return True


class DataTableView(QWidget):
    """Sheet selector + live filter + editable grid over the DataManager."""

    _SHEETS = (
        ("Data (bulk)", "main"),
        ("Isotopes", "isotopes"),
        ("Petrography", "petrography"),
    )

    def __init__(self, data_manager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        title = QLabel("Data table")
        title.setStyleSheet("font-size: 18px; font-weight: 600;")
        outer.addWidget(title)

        subtitle = QLabel(
            "Inspect and edit the loaded sheets in place.  Edits are "
            "applied to the working dataset immediately — re-render any "
            "diagram (Ctrl+R) to see them.  Amber cells were below the "
            "detection limit at import."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #5b6478;")
        outer.addWidget(subtitle)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("Sheet:"))
        self.sheet_combo = QComboBox()
        for label, key in self._SHEETS:
            self.sheet_combo.addItem(label, key)
        self.sheet_combo.currentIndexChanged.connect(self._on_sheet_changed)
        bar.addWidget(self.sheet_combo)

        bar.addSpacing(16)
        bar.addWidget(QLabel("Filter:"))
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(
            "Type to filter rows (matches any column)…")
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        bar.addWidget(self.filter_edit, stretch=1)

        self.refresh_btn = QPushButton("Reload from dataset")
        self.refresh_btn.setToolTip(
            "Re-read the sheet from the data manager (e.g. after a new "
            "import or pre-processing run).")
        self.refresh_btn.clicked.connect(self.refresh_from_data)
        bar.addWidget(self.refresh_btn)
        outer.addLayout(bar)

        # ---- structural edits + undo -------------------------------
        self._undo: list[_Snapshot] = []
        self._redo: list[_Snapshot] = []

        edit_bar = QHBoxLayout()
        self.add_row_btn = QPushButton("+ Row")
        self.add_row_btn.setToolTip("Append an empty sample row.")
        self.add_row_btn.clicked.connect(self.add_row)
        edit_bar.addWidget(self.add_row_btn)

        self.del_row_btn = QPushButton("− Rows")
        self.del_row_btn.setToolTip(
            "Delete every row touched by the current selection.")
        self.del_row_btn.clicked.connect(self.delete_selected_rows)
        edit_bar.addWidget(self.del_row_btn)

        edit_bar.addSpacing(12)
        self.add_col_btn = QPushButton("+ Column")
        self.add_col_btn.setToolTip(
            "Add a column — handy for a Group or Rock_type the source "
            "file did not carry.")
        self.add_col_btn.clicked.connect(self.add_column)
        edit_bar.addWidget(self.add_col_btn)

        self.del_col_btn = QPushButton("− Columns")
        self.del_col_btn.setToolTip(
            "Delete every column touched by the current selection.")
        self.del_col_btn.clicked.connect(self.delete_selected_columns)
        edit_bar.addWidget(self.del_col_btn)

        edit_bar.addSpacing(16)
        self.undo_btn = QPushButton("↶ Undo")
        self.undo_btn.clicked.connect(self.undo)
        edit_bar.addWidget(self.undo_btn)
        self.redo_btn = QPushButton("↷ Redo")
        self.redo_btn.clicked.connect(self.redo)
        edit_bar.addWidget(self.redo_btn)
        edit_bar.addStretch(1)
        outer.addLayout(edit_bar)

        QShortcut(QKeySequence.StandardKey.Undo, self, self.undo)
        QShortcut(QKeySequence.StandardKey.Redo, self, self.redo)

        self.model = DataFrameModel(self)
        self.proxy = QSortFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)          # match ANY column

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        # setSortingEnabled leaves the header sorting descending on
        # column 0, which silently shows the file upside-down.  Clear the
        # indicator and the proxy sort so the grid opens in file order —
        # clicking a header still sorts as usual.
        self.table.horizontalHeader().setSortIndicator(
            -1, Qt.SortOrder.AscendingOrder)
        self.proxy.sort(-1)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setDefaultSectionSize(92)
        outer.addWidget(self.table, stretch=1)

        self.status_label = QLabel("No dataset loaded.")
        self.status_label.setStyleSheet("color: #666;")
        outer.addWidget(self.status_label)

        self._dirty_cb = None
        self.model.set_before_change_callback(self._snapshot)
        self._update_undo_buttons()

    # ------------------------------------------------------------------ API
    def set_dirty_callback(self, cb) -> None:
        self._dirty_cb = cb
        self.model.set_dirty_callback(cb)
        self.model.set_before_change_callback(self._snapshot)

    def refresh_from_data(self) -> None:
        """Re-bind the current sheet from the DataManager."""
        key = self.sheet_combo.currentData() or "main"
        df, mask = self._frame_for(key)
        self.model.set_frame(df, mask)
        self._update_status()

    # ---------------------------------------------------------------- undo
    _SHEET_ATTR = {
        "main": "df",
        "isotopes": "isotopes_df",
        "petrography": "petrography_df",
    }

    def _sheet_key(self) -> str:
        return self.sheet_combo.currentData() or "main"

    def _snapshot(self, label: str) -> None:
        """Record the current sheet so the next change can be undone."""
        key = self._sheet_key()
        df, mask = self._frame_for(key)
        limits = getattr(self.data, "bdl_limits", {}).get(key)
        self._undo.append(_Snapshot(
            sheet=key, label=label,
            df=None if df is None else df.copy(),
            mask=None if mask is None else mask.copy(),
            limits=None if limits is None else limits.copy(),
        ))
        del self._undo[:-_UNDO_DEPTH]
        self._redo.clear()
        self._update_undo_buttons()

    def _capture(self, label: str) -> _Snapshot:
        """Current state of the sheet, for the *redo* side of the stack."""
        key = self._sheet_key()
        df, mask = self._frame_for(key)
        limits = getattr(self.data, "bdl_limits", {}).get(key)
        return _Snapshot(
            sheet=key, label=label,
            df=None if df is None else df.copy(),
            mask=None if mask is None else mask.copy(),
            limits=None if limits is None else limits.copy(),
        )

    def _restore(self, snap: _Snapshot) -> None:
        """Write a snapshot back into the DataManager and re-bind."""
        attr = self._SHEET_ATTR.get(snap.sheet, "df")
        setattr(self.data, attr, snap.df)
        for store, frame in (("bdl_masks", snap.mask),
                             ("bdl_limits", snap.limits)):
            registry = getattr(self.data, store, None)
            if registry is None:
                continue
            if frame is None:
                registry.pop(snap.sheet, None)
            else:
                registry[snap.sheet] = frame
        idx = self.sheet_combo.findData(snap.sheet)
        if idx >= 0 and idx != self.sheet_combo.currentIndex():
            self.sheet_combo.setCurrentIndex(idx)   # also refreshes
        else:
            self.refresh_from_data()
        self._mark_dirty()
        self._update_undo_buttons()

    def undo(self) -> None:
        if not self._undo:
            return
        snap = self._undo.pop()
        self._redo.append(self._capture(snap.label))
        self._restore(snap)
        self.status_label.setText(f"Undid: {snap.label}")

    def redo(self) -> None:
        if not self._redo:
            return
        snap = self._redo.pop()
        self._undo.append(self._capture(snap.label))
        self._restore(snap)
        self.status_label.setText(f"Redid: {snap.label}")

    def _update_undo_buttons(self) -> None:
        self.undo_btn.setEnabled(bool(self._undo))
        self.redo_btn.setEnabled(bool(self._redo))
        self.undo_btn.setToolTip(
            f"Undo: {self._undo[-1].label}" if self._undo
            else "Nothing to undo.")
        self.redo_btn.setToolTip(
            f"Redo: {self._redo[-1].label}" if self._redo
            else "Nothing to redo.")

    def _mark_dirty(self) -> None:
        cb = getattr(self, "_dirty_cb", None)
        if cb is not None:
            cb()

    # -------------------------------------------------------- structure
    def add_row(self) -> None:
        """Append an all-blank sample row to the active sheet."""
        key = self._sheet_key()
        df, _ = self._frame_for(key)
        if df is None:
            QMessageBox.information(
                self, "Add row",
                "This sheet is empty — import a dataset first.")
            return
        self._snapshot("add row")
        new_df = df.copy()
        new_df.loc[_next_index(new_df)] = [pd.NA] * len(new_df.columns)
        setattr(self.data, self._SHEET_ATTR[key], new_df)
        self.data.realign_bdl_masks()
        self.refresh_from_data()
        self._mark_dirty()
        self.table.scrollToBottom()
        self.status_label.setText(
            f"Row added — {len(new_df)} rows. Fill it in and re-render "
            "(Ctrl+R).")

    def delete_selected_rows(self) -> None:
        key = self._sheet_key()
        df, _ = self._frame_for(key)
        if df is None or df.empty:
            return
        rows = self._selected_source_rows()
        if not rows:
            QMessageBox.information(
                self, "Delete rows",
                "Select at least one cell in the rows you want to delete.")
            return
        labels = [df.index[r] for r in rows if r < len(df)]
        if not labels:
            return
        if not self._confirm(
                "Delete rows",
                f"Delete {len(labels)} row"
                f"{'s' if len(labels) != 1 else ''} from this sheet?"):
            return
        self._snapshot(f"delete {len(labels)} row"
                       f"{'s' if len(labels) != 1 else ''}")
        setattr(self.data, self._SHEET_ATTR[key], df.drop(index=labels))
        self.data.realign_bdl_masks()
        self.refresh_from_data()
        self._mark_dirty()

    def add_column(self) -> None:
        key = self._sheet_key()
        df, _ = self._frame_for(key)
        if df is None:
            QMessageBox.information(
                self, "Add column",
                "This sheet is empty — import a dataset first.")
            return
        dlg = NewColumnDialog(df.columns, self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        name = dlg.column_name
        self._snapshot(f"add column {name}")
        new_df = df.copy()
        new_df[name] = (pd.Series(np.nan, index=new_df.index, dtype=float)
                        if dlg.is_numeric
                        else pd.Series("", index=new_df.index, dtype=object))
        setattr(self.data, self._SHEET_ATTR[key], new_df)
        self.data.realign_bdl_masks()
        self.refresh_from_data()
        self._mark_dirty()
        self.status_label.setText(
            f"Column '{name}' added. Grouping columns are picked up by "
            "Data → Edit plot.")

    def delete_selected_columns(self) -> None:
        key = self._sheet_key()
        df, _ = self._frame_for(key)
        if df is None or df.empty:
            return
        cols = [df.columns[c] for c in self._selected_source_columns()
                if c < len(df.columns)]
        if not cols:
            QMessageBox.information(
                self, "Delete columns",
                "Select at least one cell in the columns you want to "
                "delete.")
            return
        if not self._confirm(
                "Delete columns",
                f"Delete {len(cols)} column"
                f"{'s' if len(cols) != 1 else ''} — "
                f"{', '.join(str(c) for c in cols[:6])}"
                f"{'…' if len(cols) > 6 else ''}?\n\n"
                "Diagrams that need them will report the samples as "
                "missing data."):
            return
        self._snapshot(f"delete {len(cols)} column"
                       f"{'s' if len(cols) != 1 else ''}")
        setattr(self.data, self._SHEET_ATTR[key], df.drop(columns=cols))
        self.data.realign_bdl_masks()
        self.refresh_from_data()
        self._mark_dirty()

    # -------------------------------------------------------------- helpers
    def _confirm(self, title: str, text: str) -> bool:
        return QMessageBox.question(
            self, title, text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        ) == QMessageBox.StandardButton.Yes

    def _selected_source_rows(self) -> list:
        """Source-model row numbers behind the selection (sorted, unique).

        The view sits behind a sort/filter proxy, so a selected visual
        row is rarely the same row of the dataframe.
        """
        rows = {self.proxy.mapToSource(i).row()
                for i in self.table.selectionModel().selectedIndexes()}
        return sorted(r for r in rows if r >= 0)

    def _selected_source_columns(self) -> list:
        cols = {self.proxy.mapToSource(i).column()
                for i in self.table.selectionModel().selectedIndexes()}
        return sorted(c for c in cols if c >= 0)

    def _frame_for(self, key: str):
        if key == "isotopes":
            return self.data.isotopes_df, self.data.bdl_masks.get("isotopes")
        if key == "petrography":
            return self.data.petrography_df, self.data.bdl_masks.get("petrography")
        return self.data.df, self.data.bdl_masks.get("main")

    def _on_sheet_changed(self, _idx: int) -> None:
        self.refresh_from_data()

    def _on_filter_changed(self, text: str) -> None:
        self.proxy.setFilterFixedString(text)
        self._update_status()

    def _update_status(self) -> None:
        df = self.model.frame
        if df is None or df.empty:
            self.status_label.setText(
                "This sheet is empty — import a dataset first "
                "(Data → Import).")
            return
        shown = self.proxy.rowCount()
        total = len(df)
        n_bdl = 0
        key = self.sheet_combo.currentData() or "main"
        mask = self.data.bdl_masks.get(key)
        if mask is not None:
            n_bdl = int(mask.to_numpy().sum())
        parts = [f"{shown} of {total} rows shown",
                 f"{len(df.columns)} columns"]
        if n_bdl:
            parts.append(f"{n_bdl} below-detection cells (amber)")
        self.status_label.setText("  ·  ".join(parts))
