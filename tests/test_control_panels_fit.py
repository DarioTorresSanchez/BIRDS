"""Every view's control panel fits the column it sits in.

The panels scroll vertically and never sideways, so a control wider than
the column is cut off at the right edge with no way to reach it.  The
Petrography panel was: its list of diagrams sized itself to the longest
name and pushed the panel 35 px past its column, clipping the list, the
legend fields and the annotation buttons.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea


@pytest.fixture
def window(qapp):
    from birds.main_window import BirdsMainWindow
    win = BirdsMainWindow()
    win.resize(1440, 900)
    win.show()
    # The spider view builds each mode's controls when it is first opened.
    win._open_spider("multielement")
    win._open_spider("ree")
    qapp.processEvents()
    # Not closed: opening views marks the session changed, and closing
    # would wait on the "discard changes?" question.
    return win


def _panels(window, qapp):
    for i in range(window.stack.count()):
        view = window.stack.widget(i)
        window.stack.setCurrentWidget(view)
        qapp.processEvents()
        for scroll in view.findChildren(QScrollArea):
            if (scroll.widget() is not None
                    and scroll.horizontalScrollBarPolicy()
                    == Qt.ScrollBarPolicy.ScrollBarAlwaysOff):
                yield type(view).__name__, scroll


def _widest(panel, limit):
    """The visible controls that need most of the width, to say which one
    a failure is about (fonts and styles differ between systems)."""
    from PySide6.QtWidgets import QWidget
    rows = []
    for w in panel.findChildren(QWidget):
        if not w.isVisibleTo(panel) or w.minimumSizeHint().width() < limit:
            continue
        text = ""
        for attr in ("text", "currentText", "title"):
            if hasattr(w, attr):
                text = getattr(w, attr)() or text
        rows.append(f"{w.minimumSizeHint().width()} {type(w).__name__} "
                    f"{text[:60]!r}")
    return sorted(rows, key=lambda r: -int(r.split()[0]))[:6]


def test_every_control_panel_fits_its_column(window, qapp):
    panels = list(_panels(window, qapp))
    assert {name for name, _ in panels} >= {
        "ClassificationView", "BivariateView", "SpiderView", "TectonicView",
        "MapView", "IsotopesView", "NormView", "PetrographyView"}
    too_wide = []
    for name, scroll in panels:
        needed = scroll.widget().minimumSizeHint().width()
        room = scroll.viewport().width()
        if needed > room:
            too_wide.append(f"{name}: needs {needed}, has {room}; widest: "
                            + "; ".join(_widest(scroll.widget(), room - 80)))
    assert not too_wide, "\n".join(too_wide)


def test_the_petrography_list_still_offers_the_full_names(window):
    combo = window.petrography.diagram_combo
    labels = [combo.itemText(i) for i in range(combo.count())]
    assert ("Gabbroic rocks — Plagioclase / Pyroxene / Olivine "
            "(Streckeisen 1976)") in labels
