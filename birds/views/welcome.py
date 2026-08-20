"""Welcome screen shown at startup."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QLabel,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

RESOURCES = Path(__file__).resolve().parents[1] / "resources"


class WelcomeView(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("WelcomeView")

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        logo = QLabel()
        logo_path = RESOURCES / "LOGO-BIRDS.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            pix = pix.scaledToWidth(360, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pix)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo)

        title = QLabel("Welcome to B.I.R.D.S")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("WelcomeTitle")
        layout.addWidget(title)

        subtitle = QLabel("Broad Igneous Rocks — Diagrams & Statistics")
        subtitle_font = QFont()
        subtitle_font.setPointSize(16)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        tip = QLabel(
            "Use <b>Data → Import</b> to load a geochemical dataset, "
            "then explore the menus above."
        )
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tip.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(tip)

        layout.addSpacerItem(
            QSpacerItem(20, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self.setStyleSheet(
            """
            #WelcomeView { background: #f7f8fc; }
            #WelcomeView QLabel { color: #1c2237; }
            #WelcomeTitle { color: #0d1b3d; }
            """
        )
