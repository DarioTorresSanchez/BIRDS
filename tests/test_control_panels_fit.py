"""No control in a view's panel is out of reach.

The control panels scrolled up and down but never sideways, so a control
wider than its column was cut off at the right edge with no way to reach
it.  On the Mac the Petrography panel was: its list of diagrams sized
itself to the longest name and pushed the panel 35 px past its column.
On Windows, whose fonts run wider, CI found six panels too wide -- the
Classification one by 88 px, the Map one by 228.  The panels now scroll
sideways when, and only when, their controls cannot fit.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QWidget

VIEWS = {"ClassificationView", "BivariateView", "SpiderView", "TectonicView",
         "MapView", "IsotopesView", "NormView", "PetrographyView"}


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
            if scroll.widget() is not None and scroll.widgetResizable():
                yield type(view).__name__, scroll


def _widest(panel, limit):
    """The visible controls that need most of the width, to say which one
    a failure is about (fonts and styles differ between systems)."""
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


def test_a_panel_too_wide_for_its_column_scrolls_sideways(window, qapp):
    panels = list(_panels(window, qapp))
    assert {name for name, _ in panels} >= VIEWS
    out_of_reach = []
    for name, scroll in panels:
        needed = scroll.widget().minimumSizeHint().width()
        room = scroll.viewport().width()
        if (needed > room and scroll.horizontalScrollBarPolicy()
                == Qt.ScrollBarPolicy.ScrollBarAlwaysOff):
            out_of_reach.append(
                f"{name}: needs {needed}, has {room}; widest: "
                + "; ".join(_widest(scroll.widget(), room - 80)))
    assert not out_of_reach, "\n".join(out_of_reach)


def test_no_control_panel_turns_sideways_scrolling_off(window, qapp):
    """Whether the controls fit depends on the system's fonts, so the
    panels must not count on it."""
    for name, scroll in _panels(window, qapp):
        if name in VIEWS:
            assert (scroll.horizontalScrollBarPolicy()
                    == Qt.ScrollBarPolicy.ScrollBarAsNeeded), name


def test_the_petrography_list_takes_the_width_it_is_given(window):
    combo = window.petrography.diagram_combo
    assert (combo.sizeAdjustPolicy() == combo.SizeAdjustPolicy
            .AdjustToMinimumContentsLengthWithIcon)
    labels = [combo.itemText(i) for i in range(combo.count())]
    assert ("Gabbroic rocks — Plagioclase / Pyroxene / Olivine "
            "(Streckeisen 1976)") in labels
