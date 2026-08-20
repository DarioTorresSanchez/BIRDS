"""Shared sample-selection bus for cross-view brushing.

One :class:`SelectionBus` instance lives on the main window.  Views
toggle sample names into it (Alt/Cmd+click) and every subscribed view
re-renders with the selected samples highlighted — so picking a point
on the TAS instantly rings the same sample on the Spider, the Map and
any other open diagram.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class SelectionBus(QObject):
    """Holds the set of currently selected sample names.

    Names are the user-facing identifiers produced by
    :func:`birds.views.annotation_controller.nearest_sample` — i.e. the
    first non-empty of ``Sample_Name`` / ``Sample_Label`` / … for the
    row, so the same string matches across sheets and views.
    """

    changed = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._names: set[str] = set()

    # ------------------------------------------------------------------ API
    @property
    def names(self) -> set[str]:
        return set(self._names)

    def toggle(self, name: str) -> None:
        """Add *name* if absent, remove it if present."""
        if not name:
            return
        if name in self._names:
            self._names.discard(name)
        else:
            self._names.add(name)
        self.changed.emit()

    def set_names(self, names) -> None:
        new = {str(n) for n in names if n}
        if new != self._names:
            self._names = new
            self.changed.emit()

    def clear(self) -> None:
        if self._names:
            self._names.clear()
            self.changed.emit()

    def __contains__(self, name: str) -> bool:
        return name in self._names

    def __len__(self) -> int:
        return len(self._names)
