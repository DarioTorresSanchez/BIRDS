"""Shared helpers for plot export across every diagram view.

Centralising the file-dialog filter and the extension-injection logic
keeps every view in sync (so PDF / EPS / SVG never go missing from one
panel) and guarantees that whatever extension the user picks in the
``QFileDialog`` filter is appended to the filename if missing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


# Pipe-separated filter passed to QFileDialog.  PDF first so it shows up
# at the top of the dropdown for journal-quality vector exports.
EXPORT_FILTER = (
    "PDF (*.pdf);;"
    "PNG (*.png);;"
    "JPEG (*.jpg);;"
    "SVG (*.svg);;"
    "EPS (*.eps)"
)


# Map each filter label back to its extension so we can repair filenames
# missing one.  Keys must match the exact strings used in EXPORT_FILTER.
_FILTER_TO_EXT = {
    "PDF (*.pdf)": ".pdf",
    "PNG (*.png)": ".png",
    "JPEG (*.jpg)": ".jpg",
    "SVG (*.svg)": ".svg",
    "EPS (*.eps)": ".eps",
}


def ask_export_path(
    parent: QWidget,
    suggested_name: str = "",
    title: str = "Export plot",
) -> Optional[Path]:
    """Show a save-file dialog with every supported plot format.

    Returns the chosen ``Path`` with a sane extension, or ``None`` if
    the user cancelled.  When the filename has no extension the one
    matching the active filter is appended; when the extension does
    not match any known format, the filter-selected extension wins.
    """
    path_str, selected_filter = QFileDialog.getSaveFileName(
        parent, title, suggested_name, EXPORT_FILTER
    )
    if not path_str:
        return None
    path = Path(path_str)
    expected = _FILTER_TO_EXT.get(selected_filter)
    if expected is None:
        return path
    if path.suffix.lower() not in _FILTER_TO_EXT.values():
        path = path.with_suffix(expected)
    return path


def save_figure(parent: QWidget, figure, path: Path, *, dpi: int = 300) -> bool:
    """``figure.savefig`` with a friendly error dialog on failure."""
    try:
        figure.savefig(str(path), dpi=dpi, bbox_inches="tight")
        return True
    except Exception as exc:  # noqa: BLE001
        QMessageBox.critical(parent, "Export error", str(exc))
        return False
