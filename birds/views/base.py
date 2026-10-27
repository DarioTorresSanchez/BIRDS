"""Base widget that diagram views inherit from."""

from __future__ import annotations

import html
import re

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


_MATHTEXT = re.compile(r"\$([^$]*)\$")
_SUB_SUP = re.compile(r"([_^])(?:\{([^}]*)\}|(\w))")


def header_html(text: str) -> str:
    """A diagram's title or citation, written for matplotlib, as rich
    text for the header above the plot: "Yb$_N$" becomes Yb<sub>N</sub>.

    The figure renders the mathtext itself, but a QLabel showed it as
    typed -- "Yb$_N$ vs Dy$_N$".  Everything else is escaped, so an "&"
    or a "Ti/V < 20" stays text.
    """
    # split() alternates plain text and the inside of $...$
    parts = _MATHTEXT.split(text or "")
    return "".join(_math_html(p) if i % 2 else html.escape(p)
                   for i, p in enumerate(parts))


def _math_html(math: str) -> str:
    def script(m: re.Match) -> str:
        tag = "sub" if m.group(1) == "_" else "sup"
        return f"<{tag}>{m.group(2) or m.group(3)}</{tag}>"
    return _SUB_SUP.sub(script, html.escape(math))


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
