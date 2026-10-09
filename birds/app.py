"""The Qt application object, and the sessions the system hands it.

Double-clicking a ``.birds`` file opens it in B.I.R.D.S once the app is
installed (see ``packaging/``).  The file arrives in one of two ways:

* on macOS, as a ``FileOpen`` event -- both when the double-click
  launches the app and when the app is already running;
* on Windows and Linux, as a path on the command line.

Either way it may come before the main window exists, so paths are held
until the window is attached.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from PySide6.QtCore import QEvent
from PySide6.QtWidgets import QApplication

from .session import SESSION_EXT


def session_paths_from_argv(argv: Iterable[str]) -> List[Path]:
    """The session files named on a command line, program name excluded.

    Anything else -- Qt's own options, macOS's old ``-psn_…`` process
    serial number, a file of another type -- is ignored.
    """
    out = []
    for arg in list(argv)[1:]:
        if not arg or arg.startswith("-"):
            continue
        path = Path(arg)
        if path.suffix.lower() == SESSION_EXT and path.is_file():
            out.append(path)
    return out


class SessionOpener:
    """Holds the sessions handed over until there is a window to open
    them in.  Kept apart from Qt so it can be tested on its own."""

    def __init__(self, paths: Iterable[Path] = ()) -> None:
        self.window = None
        self.pending: List[Path] = [Path(p) for p in paths]

    def open(self, path: Path) -> None:
        """Open *path* now, or as soon as a window is attached."""
        if self.window is None:
            self.pending.append(Path(path))
        else:
            self.window.open_session_file(Path(path))

    def attach(self, window) -> None:
        """Give it the main window and open what was held -- only the
        last, since one window shows one session."""
        self.window = window
        last = self.pending[-1] if self.pending else None
        self.pending.clear()
        if last is not None:
            window.open_session_file(last)


class BirdsApplication(QApplication):
    """QApplication that opens the sessions the operating system sends."""

    def __init__(self, argv) -> None:
        super().__init__(argv)
        self.opener = SessionOpener(session_paths_from_argv(argv))

    def event(self, event) -> bool:
        if event.type() == QEvent.Type.FileOpen:
            if event.file():
                self.opener.open(Path(event.file()))
            return True
        return super().event(event)

    def attach(self, window) -> None:
        self.opener.attach(window)
