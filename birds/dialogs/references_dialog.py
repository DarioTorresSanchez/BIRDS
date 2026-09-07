"""References dialog — scrollable APA bibliography for every diagram and
process implemented in B.I.R.D.S.
"""

from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextBrowser,
    QVBoxLayout,
)

from ..references import all_references, total_count


class ReferencesDialog(QDialog):
    """Modeless dialog showing the full APA bibliography."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("References (APA 7th edition)")
        self.resize(820, 640)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(8)

        # ---- Header --------------------------------------------------------
        title = QLabel("References — APA 7th edition")
        f = QFont(); f.setPointSize(13); f.setBold(True)
        title.setFont(f)
        outer.addWidget(title)

        subtitle = QLabel(
            f"{total_count()} entries, organised by category. "
            "Use Copy or Export to extract them for a manuscript."
        )
        subtitle.setStyleSheet("color: #5b6478;")
        subtitle.setWordWrap(True)
        outer.addWidget(subtitle)

        # ---- Body ---------------------------------------------------------
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setHtml(self._build_html())
        self.browser.setSizePolicy(QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Expanding)
        outer.addWidget(self.browser, stretch=1)

        # ---- Buttons ------------------------------------------------------
        btns = QHBoxLayout()
        btns.setSpacing(6)
        self.copy_btn = QPushButton("Copy all to clipboard")
        self.copy_btn.clicked.connect(self._copy)
        btns.addWidget(self.copy_btn)
        self.export_btn = QPushButton("Export…")
        self.export_btn.clicked.connect(self._export)
        btns.addWidget(self.export_btn)
        btns.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.setDefault(True)
        close_btn.clicked.connect(self.accept)
        btns.addWidget(close_btn)
        outer.addLayout(btns)

    # ------------------------------------------------------------------ HTML
    @staticmethod
    def _md_italics_to_html(text: str) -> str:
        """Convert Markdown ``*italic*`` markers in references.py to HTML
        ``<i>...</i>`` tags.  Qt's rich-text engine renders ``*`` literally
        otherwise — book / journal titles would show the asterisks."""
        import re
        # Non-greedy match between paired asterisks (skip empty pairs).
        return re.sub(r"\*([^*]+?)\*", r"<i>\1</i>", text)

    def _build_html(self) -> str:
        """Render the bibliography as a single column with APA hanging
        indents.  Each citation is one ``<p>`` with left margin + negative
        text-indent.  Avoids the table-column auto-sizing problem.
        """
        blocks = []
        for section, items in all_references():
            # Section header
            blocks.append(
                f"<h3 style='color:#1c2237;margin:18px 0 6px 0;"
                f"border-bottom:1px solid #d0d4dc;padding-bottom:3px;"
                f"font-size:15px;'>{section}</h3>"
            )
            for citation, used_for in items:
                citation_html = self._md_italics_to_html(citation)
                used_for_html = self._md_italics_to_html(used_for)
                # APA hanging indent: margin-left pushes wrapped lines in,
                # negative text-indent pulls the first line back out.  We
                # add explicit left-padding on the wrapper so the negative
                # text-indent never clips the first character.
                blocks.append(
                    f"<p style='margin:0 0 2px 28px;"
                    f"text-indent:-28px;text-align:justify;'>"
                    f"{citation_html}</p>"
                    f"<p style='margin:0 0 12px 28px;color:#5b6478;"
                    f"font-style:italic;font-size:12px;'>"
                    f"<b>Used for:</b> {used_for_html}</p>"
                )
        return (
            "<html><body style='font-family:Georgia, \"Times New Roman\", "
            "serif;font-size:13px;line-height:1.45;"
            "margin-left:6px;margin-right:6px;'>"
            + "".join(blocks)
            + "</body></html>"
        )

    # ------------------------------------------------------------------ ops
    def _plain_text(self) -> str:
        """Markdown / plain-text rendering for clipboard + file export.

        Only paired ``*…*`` markers (book titles, journal names) get
        stripped — lone asterisks in geochemical anomaly notation
        (Eu/Eu*, Nb/Nb*, Dy/Dy*) are preserved.
        """
        import re
        # Strip only paired italic markers, leave lone '*' alone.
        strip_italics = lambda s: re.sub(r"\*([^*]+?)\*", r"\1", s)
        out = ["B.I.R.D.S — References (APA 7th edition)",
               "=" * 60, ""]
        for section, items in all_references():
            out.append(section)
            out.append("-" * len(section))
            for citation, used_for in items:
                out.append(strip_italics(citation))
                out.append(f"    Used for: {strip_italics(used_for)}")
                out.append("")
        return "\n".join(out)

    def _copy(self) -> None:
        QApplication.clipboard().setText(self._plain_text())
        self.copy_btn.setText("✓ Copied")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(
            1500, lambda: self.copy_btn.setText("Copy all to clipboard"))

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export references",
            "birds_references.txt",
            "Text (*.txt);;Markdown (*.md);;HTML (*.html);;All files (*.*)",
        )
        if not path:
            return
        if path.lower().endswith(".html") or path.lower().endswith(".htm"):
            content = self._build_html()
        else:
            content = self._plain_text()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        self.export_btn.setText("✓ Exported")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(
            1500, lambda: self.export_btn.setText("Export…"))
