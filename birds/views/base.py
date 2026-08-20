"""Base widget that diagram views inherit from."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from ._export_helpers import ask_export_path, save_figure
from .plot_canvas import PlotCanvas


class DiagramView(QWidget):
    """Header (title + subtitle) + Matplotlib canvas + helpers."""

    def __init__(self, data_manager, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        self.title_label = QLabel("")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.title_label.setWordWrap(True)
        outer.addWidget(self.title_label)

        self.subtitle_label = QLabel("")
        self.subtitle_label.setStyleSheet("color: #5b6478;")
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setTextFormat(Qt.TextFormat.RichText)
        outer.addWidget(self.subtitle_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #d4d8e1;")
        outer.addWidget(separator)

        self.canvas = PlotCanvas()
        outer.addWidget(self.canvas, stretch=1)

        self._show_empty_state()

    # ------------------------------------------------------------------ utils
    def _show_empty_state(
        self, message: str = "Select a diagram from the menu to begin."
    ) -> None:
        self.canvas.figure.clear()
        ax = self.canvas.figure.add_subplot(111)
        ax.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            fontsize=12,
            color="#6c7388",
            wrap=True,
        )
        ax.axis("off")
        self.canvas.draw()

    def export_plot(self) -> None:
        path = ask_export_path(self)
        if path is None:
            return
        save_figure(self, self.canvas.figure, path)

    def edit_plot(self) -> None:
        QMessageBox.information(
            self,
            "Edit plot",
            "Live plot editor will be added in a future release.",
        )
