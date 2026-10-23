"""Tiny helpers for serialising / restoring Qt widget state.

Each view's ``serialize()`` produces a small ``dict`` describing its
controls; ``restore()`` reverses the process.  Without these helpers
each view would have to repeat the same boilerplate eight times over,
which makes the code hard to keep in sync.

The functions here are intentionally tolerant: missing keys are treated
as "leave the widget at its current value", because users may open a
session saved by an older B.I.R.D.S that didn't yet serialise some
control.
"""

from __future__ import annotations

from typing import Iterable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLineEdit,
    QListWidget,
    QSpinBox,
    QTreeWidget,
)


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def combo_state(c: QComboBox) -> dict:
    """Capture a QComboBox's selection (text + index) and editable text."""
    out = {"text": c.currentText(), "index": c.currentIndex()}
    if c.isEditable():
        out["editable_text"] = c.lineEdit().text()
    return out


def edit_state(e: QLineEdit) -> str:
    return e.text()


def spin_state(s) -> float:
    return float(s.value())


def check_state(b) -> bool:
    return bool(b.isChecked())


def list_selection(lw: QListWidget) -> dict:
    """Return both the selected texts AND any custom (purple) items
    that aren't part of the default column dictionary, so the user's
    "+Add expression" items survive a session round-trip."""
    selected = [lw.item(i).text() for i in range(lw.count())
                if lw.item(i).isSelected()]
    custom = [lw.item(i).text() for i in range(lw.count())
              if lw.item(i).data(Qt.ItemDataRole.UserRole) == "expr"]
    return {"selected": selected, "custom": custom}


def tree_checked(tree: QTreeWidget) -> list[str]:
    """Return the names of every CHECKED leaf (depth=2) in a QTreeWidget.

    Used for the ReservoirGroup widget where the user ticks a subset of
    reservoirs by name.
    """
    names: list[str] = []
    for i in range(tree.topLevelItemCount()):
        parent = tree.topLevelItem(i)
        for j in range(parent.childCount()):
            child = parent.child(j)
            if child.checkState(0) == Qt.CheckState.Checked:
                name = child.data(0, Qt.ItemDataRole.UserRole)
                if name:
                    names.append(str(name))
    return names


# ---------------------------------------------------------------------------
# Restore
# ---------------------------------------------------------------------------

def restore_combo(c: QComboBox, state: Optional[dict]) -> None:
    if not state:
        return
    text = state.get("text") or state.get("editable_text") or ""
    if not text:
        return
    idx = c.findText(text)
    if idx >= 0:
        c.setCurrentIndex(idx)
    elif c.isEditable():
        # Free-text not in the dropdown — paste it into the line edit.
        c.setCurrentText(text)


def restore_edit(e: QLineEdit, state: Optional[str]) -> None:
    if state is not None:
        e.setText(state)


def restore_spin(s, state) -> None:
    if state is None:
        return
    try:
        if isinstance(s, QDoubleSpinBox):
            s.setValue(float(state))
        elif isinstance(s, QSpinBox):
            s.setValue(int(state))
        else:
            s.setValue(state)
    except (TypeError, ValueError):
        pass


def restore_check(b, state: Optional[bool]) -> None:
    if state is None:
        return
    b.setChecked(bool(state))


def restore_list_selection(lw: QListWidget, state: Optional[dict],
                           item_factory=None) -> None:
    """Re-add any custom items and re-select the user's prior selection.

    ``item_factory`` is an optional callable ``(text) -> QListWidgetItem``
    used to style custom expression items (purple foreground); when
    omitted a plain item is used.
    """
    if not state:
        return
    # 1. Re-create custom (expression) items that aren't in the default list
    existing = {lw.item(i).text() for i in range(lw.count())}
    for text in state.get("custom", []):
        if text not in existing:
            if item_factory is not None:
                lw.addItem(item_factory(text))
            else:
                lw.addItem(text)
    # 2. Re-apply selection
    selected = set(state.get("selected", []))
    for i in range(lw.count()):
        lw.item(i).setSelected(lw.item(i).text() in selected)


def restore_tree_checked(tree: QTreeWidget,
                         names: Optional[Iterable[str]]) -> None:
    if not names:
        return
    wanted = set(names)
    for i in range(tree.topLevelItemCount()):
        parent = tree.topLevelItem(i)
        for j in range(parent.childCount()):
            child = parent.child(j)
            name = child.data(0, Qt.ItemDataRole.UserRole)
            if name in wanted:
                child.setCheckState(0, Qt.CheckState.Checked)


# ---------------------------------------------------------------------------
# Convenience for the AxisGroup / LegendGroup / GroupingGroup widgets
# ---------------------------------------------------------------------------

def axis_group_state(ag) -> dict:
    return {
        "x_label": edit_state(ag.x_label_edit),
        "y_label": edit_state(ag.y_label_edit),
        "font_size": spin_state(ag.font_size),
        "font_family": ag.font_family.currentText(),
        "bold": check_state(ag.bold),
        "italic": check_state(ag.italic),
        "log_x": check_state(ag.log_x) if ag.log_x.isVisible() else False,
        "log_y": check_state(ag.log_y) if ag.log_y.isVisible() else False,
    }


def restore_axis_group(ag, state: Optional[dict]) -> None:
    if not state:
        return
    restore_edit(ag.x_label_edit, state.get("x_label"))
    restore_edit(ag.y_label_edit, state.get("y_label"))
    restore_spin(ag.font_size, state.get("font_size"))
    restore_combo(ag.font_family, {"text": state.get("font_family", "")})
    restore_check(ag.bold, state.get("bold"))
    restore_check(ag.italic, state.get("italic"))
    restore_check(ag.log_x, state.get("log_x"))
    restore_check(ag.log_y, state.get("log_y"))


def legend_group_state(lg) -> dict:
    return {
        "visible": check_state(lg.visible),
        "title": edit_state(lg.title_edit),
        "location": lg.location.currentText(),
        "font_size": spin_state(lg.font_size),
    }


def restore_legend_group(lg, state: Optional[dict]) -> None:
    if not state:
        return
    restore_check(lg.visible, state.get("visible"))
    restore_edit(lg.title_edit, state.get("title"))
    restore_combo(lg.location, {"text": state.get("location", "")})
    restore_spin(lg.font_size, state.get("font_size"))


def grouping_group_state(gg) -> dict:
    return {"facet": check_state(gg.facet_chk)}


def restore_grouping_group(gg, state: Optional[dict]) -> None:
    if state is None:
        return
    restore_check(gg.facet_chk, state.get("facet"))


def regression_group_state(rg) -> dict:
    return {
        "show": check_state(rg.show),
        "per_group": check_state(rg.per_group),
        "show_label": check_state(rg.show_label),
        "ci": check_state(rg.ci_chk),
    }


def restore_regression_group(rg, state: Optional[dict]) -> None:
    if not state:
        return
    restore_check(rg.show, state.get("show"))
    restore_check(rg.per_group, state.get("per_group"))
    restore_check(rg.show_label, state.get("show_label"))
    restore_check(rg.ci_chk, state.get("ci"))


def reservoirs_state(rg) -> list[str]:
    """ReservoirGroup → list of ticked names."""
    return tree_checked(rg.tree)


def restore_reservoirs(rg, names: Optional[Iterable[str]]) -> None:
    """A name since removed from the catalogue is restored as the entry
    that replaced it (``RENAMED_RESERVOIRS``)."""
    from .reservoirs import RENAMED_RESERVOIRS
    if names is not None:
        names = list(dict.fromkeys(RENAMED_RESERVOIRS.get(n, n)
                                   for n in names))
    restore_tree_checked(rg.tree, names)
