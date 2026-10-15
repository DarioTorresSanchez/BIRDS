"""Reusable Matplotlib canvas widget."""

from __future__ import annotations

from matplotlib.backend_tools import Cursors
from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

#: The cursors the canvas may put up, every one drawn natively.  On
#: macOS Qt builds its wait and four-way move cursors from bitmaps, and
#: turning such a bitmap into a CGImage has brought the app down
#: (EXC_BREAKPOINT inside CGImageCreate under QImage::toCGImage, macOS
#: 26 with Qt 6.11) -- each time as Matplotlib put up its wait cursor
#: for a redraw, which it does whenever a second has passed since the
#: last one.  The wait cursor is not here: a redraw keeps the cursor
#: there is.
NATIVE_CURSORS = {
    Cursors.POINTER: Qt.CursorShape.ArrowCursor,
    Cursors.HAND: Qt.CursorShape.PointingHandCursor,
    Cursors.SELECT_REGION: Qt.CursorShape.CrossCursor,
    Cursors.MOVE: Qt.CursorShape.OpenHandCursor,
    Cursors.RESIZE_HORIZONTAL: Qt.CursorShape.SplitHCursor,
    Cursors.RESIZE_VERTICAL: Qt.CursorShape.SplitVCursor,
}


class SafeCursorCanvas(FigureCanvasQTAgg):
    """FigureCanvasQTAgg that only ever asks Qt for native cursors."""

    def set_cursor(self, cursor) -> None:
        shape = NATIVE_CURSORS.get(cursor)
        if shape is not None:
            self.setCursor(shape)


class PlotCanvas(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(7, 5), dpi=100)
        self.canvas = SafeCursorCanvas(self.figure)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)

    def clear(self) -> None:
        self.figure.clear()
        self.canvas.draw_idle()

    def draw(self) -> None:
        self.canvas.draw_idle()

    def mpl_connect(self, event_name: str, handler):
        """Delegate to the underlying FigureCanvas so callers can attach
        Matplotlib event handlers (button_press_event, motion_notify_event,
        etc.) without poking at the private canvas attribute."""
        return self.canvas.mpl_connect(event_name, handler)
