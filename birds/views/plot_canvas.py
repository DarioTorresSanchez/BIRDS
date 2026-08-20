"""Reusable Matplotlib canvas widget."""

from __future__ import annotations

from matplotlib.backends.backend_qtagg import (
    FigureCanvasQTAgg,
    NavigationToolbar2QT,
)
from matplotlib.figure import Figure
from PySide6.QtWidgets import QVBoxLayout, QWidget


class PlotCanvas(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(7, 5), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.figure)
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
