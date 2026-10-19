"""Read files without freezing the window.

Google Drive, iCloud Drive, Dropbox and OneDrive can keep a file in the
cloud only, with nothing on disk but a placeholder, until something
opens it.  Opening it then waits inside the read call while the
provider downloads it -- and on the window's own thread that wait froze
B.I.R.D.S whole: no repaint, no click answered, for as long as the
download took.  Measured on the user's Drive: eleven minutes for a
68 kB session that was not on the Mac yet.

:func:`run_in_background` does the reading on a worker thread.  A local
file comes back at once with no dialog; a slow one brings up a dialog
that says what is being waited for, with Cancel, while the window keeps
painting.  The work handed over must not touch Qt -- reading the file
and parsing it into DataFrames, nothing more.
"""

from __future__ import annotations

import os
import stat
import threading
from pathlib import Path
from typing import Callable, TypeVar

from PySide6.QtCore import QEventLoop, Qt, QTimer
from PySide6.QtWidgets import QProgressDialog

T = TypeVar("T")

#: st_flags bit macOS sets on a cloud placeholder ("dataless" file).
SF_DATALESS = getattr(stat, "SF_DATALESS", 0x40000000)

#: How long a read may take before the dialog comes up, in seconds.
QUICK = 0.15


class Cancelled(Exception):
    """The user stopped waiting; the read is abandoned."""


def is_cloud_placeholder(path: str | Path) -> bool:
    """True when *path* is a cloud file not yet downloaded (macOS)."""
    try:
        return bool(os.stat(path).st_flags & SF_DATALESS)
    except (OSError, AttributeError):
        return False


def reading_label(path: str | Path) -> str:
    """What the dialog says while *path* is read."""
    name = Path(path).name
    if is_cloud_placeholder(path):
        return (f"Downloading “{name}” from cloud storage…\n\n"
                "The file is kept online only (Google Drive, iCloud…), "
                "so it has to come down before it can be opened. "
                "Cancel stops waiting; the window stays as it was.")
    return f"Opening “{name}”…"


def run_in_background(parent, title: str, label: str,
                      fn: Callable[..., T], *args, **kwargs) -> T:
    """``fn(*args, **kwargs)`` on a worker thread, the window painting.

    Returns its result or raises its exception; raises
    :class:`Cancelled` if the user cancels -- the worker is then left
    to finish on its own and its result is dropped.
    """
    outcome: dict = {}

    def work() -> None:
        try:
            outcome["value"] = fn(*args, **kwargs)
        except BaseException as exc:                        # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=work, name="birds-read", daemon=True)
    worker.start()
    worker.join(QUICK)
    if worker.is_alive():
        _wait(parent, title, label, worker)
    if worker.is_alive():
        raise Cancelled(label)
    if "error" in outcome:
        raise outcome["error"]
    return outcome["value"]


def _wait(parent, title: str, label: str, worker: threading.Thread) -> None:
    """Spin an event loop under a busy dialog until *worker* ends or the
    user cancels."""
    dialog = QProgressDialog(label, "Cancel", 0, 0, parent)
    dialog.setWindowTitle(title)
    dialog.setWindowModality(Qt.WindowModality.WindowModal)
    dialog.setMinimumDuration(0)
    dialog.setAutoClose(False)
    dialog.setAutoReset(False)
    loop = QEventLoop()
    timer = QTimer()
    timer.setInterval(50)
    # Quit when the read ends, or on any way of cancelling -- the
    # button, Escape, closing the dialog -- which wasCanceled() covers.
    timer.timeout.connect(
        lambda: loop.quit() if (not worker.is_alive()
                                or dialog.wasCanceled()) else None)
    dialog.canceled.connect(loop.quit)
    timer.start()
    dialog.show()
    loop.exec()
    timer.stop()
    dialog.canceled.disconnect(loop.quit)
    dialog.close()
    dialog.deleteLater()
