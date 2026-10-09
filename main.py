"""B.I.R.D.S launcher."""

from __future__ import annotations

import datetime as _dt
import sys
import traceback
from pathlib import Path

from PySide6.QtCore import qInstallMessageHandler, QtMsgType

from birds.app import BirdsApplication
from birds.main_window import BirdsMainWindow


# ---------------------------------------------------------------------------
# Crash logging
# ---------------------------------------------------------------------------
# When the app closes "instantly" (Qt segfault, C++ assertion, uncaught
# Python exception in a slot, …) the macOS terminal usually shows nothing
# because the GUI process detaches from stdout.  We mirror every uncaught
# Python exception AND every Qt warning/critical message into a rolling
# log at ``~/.birds/crash.log`` so we have something to look at next
# time the window vanishes.

_CRASH_LOG = Path.home() / ".birds" / "crash.log"


def _ensure_crash_dir() -> None:
    try:
        _CRASH_LOG.parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def _log_crash(prefix: str, msg: str) -> None:
    _ensure_crash_dir()
    try:
        with _CRASH_LOG.open("a", encoding="utf-8") as f:
            ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{ts}] {prefix}\n{msg}\n")
    except OSError:
        pass


def _install_excepthook() -> None:
    """Replace ``sys.excepthook`` with one that appends the traceback to
    ``crash.log`` before delegating to the default handler.  Without
    this, exceptions raised inside Qt slots / mpl callbacks vanish."""
    prev_hook = sys.excepthook

    def _hook(exc_type, exc_value, exc_tb):
        try:
            tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            _log_crash("PYTHON EXCEPTION", tb)
        finally:
            prev_hook(exc_type, exc_value, exc_tb)

    sys.excepthook = _hook


def _install_qt_message_handler() -> None:
    """Route ``qWarning`` / ``qCritical`` / ``qFatal`` into the same
    crash.log.  These are the messages Qt prints to stderr when, e.g.,
    a signal disconnect fails or the C++ side of a widget gets
    deallocated under our feet."""
    severities = {
        QtMsgType.QtDebugMsg:    "DEBUG",
        QtMsgType.QtInfoMsg:     "INFO",
        QtMsgType.QtWarningMsg:  "WARN",
        QtMsgType.QtCriticalMsg: "CRIT",
        QtMsgType.QtFatalMsg:    "FATAL",
    }

    def _handler(mode, context, message):
        # Only log warn-and-above; debug/info would flood the file.
        if mode in (QtMsgType.QtDebugMsg, QtMsgType.QtInfoMsg):
            return
        label = severities.get(mode, str(mode))
        _log_crash(f"QT {label}", message)

    qInstallMessageHandler(_handler)


def main() -> int:
    # A packaged app checks itself with: BIRDS --self-test
    if "--self-test" in sys.argv:
        import os
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        from birds.selftest import run
        return run()

    _install_excepthook()
    _install_qt_message_handler()

    # BirdsApplication opens the .birds files the system hands over: a
    # double-clicked session, or one named on the command line.
    app = BirdsApplication(sys.argv)
    app.setApplicationName("B.I.R.D.S")
    app.setOrganizationName("B.I.R.D.S")
    app.setApplicationDisplayName("B.I.R.D.S")

    window = BirdsMainWindow()
    window.show()
    app.attach(window)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
