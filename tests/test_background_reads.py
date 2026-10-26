"""Reading sessions and datasets without freezing the window.

A file kept online only in Google Drive or iCloud downloads inside the
read call; on the window's thread that froze B.I.R.D.S for as long as
the download took (eleven minutes once, for a 68 kB session).  Reads now
run on a worker thread: the window keeps processing events, a dialog
says what is awaited, and Cancel stops waiting.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QProgressDialog

from birds.views import background
from birds.views.background import Cancelled, run_in_background


#: A frozen window ticks zero times while the read runs; Qt's timers are
#: coarse on a busy machine, so a running one is only promised a few.
FROZEN_IS_ZERO = 3


def _ticking():
    """A timer that counts while the main thread runs its event loop --
    zero ticks means the window was frozen.  Work earlier tests left
    queued (their windows' redraws, their start-up timers) is run off
    first, or it eats into the count."""
    from PySide6.QtCore import QEventLoop
    settle = QEventLoop()
    QTimer.singleShot(400, settle.quit)
    settle.exec()
    ticks = []
    timer = QTimer()
    timer.setInterval(20)
    timer.timeout.connect(lambda: ticks.append(1))
    timer.start()
    return timer, ticks


def _cancel_soon(ms=150):
    def cancel():
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget, QProgressDialog) and widget.isVisible():
                widget.cancel()
    QTimer.singleShot(ms, cancel)


def test_a_quick_read_returns_at_once_without_a_dialog(qapp, monkeypatch):
    shown = []
    monkeypatch.setattr(background, "_wait", lambda *a: shown.append(a))
    assert run_in_background(None, "t", "l", lambda x: x * 2, 21) == 42
    assert shown == []


def test_a_slow_read_keeps_the_window_running(qapp):
    timer, ticks = _ticking()
    value = run_in_background(None, "t", "l",
                              lambda: (time.sleep(0.6), "done")[1])
    timer.stop()
    assert value == "done"
    assert len(ticks) >= FROZEN_IS_ZERO


def test_the_reads_error_reaches_the_caller(qapp):
    def fail():
        time.sleep(0.3)
        raise ValueError("bad zip")
    with pytest.raises(ValueError, match="bad zip"):
        run_in_background(None, "t", "l", fail)


def test_cancel_stops_waiting(qapp):
    release = threading.Event()
    _cancel_soon()
    start = time.perf_counter()
    with pytest.raises(Cancelled):
        run_in_background(None, "t", "l", release.wait, 30)
    assert time.perf_counter() - start < 5
    release.set()


def test_a_cloud_placeholder_is_named_in_the_dialog(monkeypatch, tmp_path):
    path = tmp_path / "SOB_1.birds"
    path.write_bytes(b"x")
    assert not background.is_cloud_placeholder(path)
    assert background.reading_label(path) == "Opening “SOB_1.birds”…"
    monkeypatch.setattr(background.os, "stat", lambda p: SimpleNamespace(
        st_flags=background.SF_DATALESS))
    assert background.is_cloud_placeholder(path)
    assert "from cloud storage" in background.reading_label(path)


# ---------------------------------------------------------------------------
# Through the window
# ---------------------------------------------------------------------------

@pytest.fixture
def saved(qapp, tmp_path, majors_df):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = majors_df
    w.on_dataset_replaced()
    path = tmp_path / "s.birds"
    w._session_path = path
    w.on_save_session()
    return path


def _slow(fn, seconds, gate=None):
    def wrapper(*a, **k):
        if gate is not None:
            gate.wait(30)
        else:
            time.sleep(seconds)
        return fn(*a, **k)
    return wrapper


def test_opening_a_slow_session_keeps_the_window_running(saved, monkeypatch):
    import birds.main_window as mw
    from birds.main_window import BirdsMainWindow
    monkeypatch.setattr(mw, "load_session", _slow(mw.load_session, 0.6))
    window = BirdsMainWindow()
    timer, ticks = _ticking()
    window._load_session_path(saved)
    timer.stop()
    assert len(ticks) >= FROZEN_IS_ZERO
    assert window._session_path == saved
    assert len(window.data.df) == 12


def test_cancelling_a_session_leaves_the_window_as_it_was(saved,
                                                          monkeypatch):
    import birds.main_window as mw
    from birds.main_window import BirdsMainWindow
    gate = threading.Event()
    monkeypatch.setattr(mw, "load_session", _slow(mw.load_session, 0, gate))
    window = BirdsMainWindow()
    window.data.df = pd.DataFrame({"SiO2": [1.0]})
    _cancel_soon()
    window._load_session_path(saved)
    gate.set()
    assert window._session_path is None
    assert list(window.data.df["SiO2"]) == [1.0]
    assert "Stopped waiting" in window.statusBar().currentMessage()


def test_importing_a_slow_file_keeps_the_window_running(qapp, tmp_path,
                                                        monkeypatch):
    import birds.dialogs.import_dialog as imp
    csv = tmp_path / "data.csv"
    pd.DataFrame({"Sample_Name": ["A", "B"], "SiO2": [50.0, 60.0]}).to_csv(
        csv, index=False)
    monkeypatch.setattr(imp, "read_tabular", _slow(imp.read_tabular, 0.6))
    monkeypatch.setattr(imp.QFileDialog, "getOpenFileName",
                        lambda *a, **k: (str(csv), ""))
    dialog = imp.ImportDialog()
    timer, ticks = _ticking()
    dialog._browse()
    timer.stop()
    assert len(ticks) >= FROZEN_IS_ZERO
    assert dialog.ok_button.isEnabled()


def test_cancelling_an_import_forgets_the_file(qapp, tmp_path, monkeypatch):
    import birds.dialogs.import_dialog as imp
    csv = tmp_path / "data.csv"
    csv.write_text("Sample_Name,SiO2\nA,50\n")
    gate = threading.Event()
    monkeypatch.setattr(imp, "read_tabular", _slow(imp.read_tabular, 0, gate))
    monkeypatch.setattr(imp.QFileDialog, "getOpenFileName",
                        lambda *a, **k: (str(csv), ""))
    monkeypatch.setattr(imp.QMessageBox, "critical",
                        lambda *a, **k: pytest.fail("cancel is not an error"))
    dialog = imp.ImportDialog()
    _cancel_soon()
    dialog._browse()
    gate.set()
    assert dialog._path is None and dialog.path_edit.text() == ""
    assert not dialog.ok_button.isEnabled()


def test_every_file_read_of_the_window_goes_through_the_worker():
    """A new read added on the window's thread would bring the freeze
    back; each one named here must stay off it."""
    root = Path(__file__).resolve().parent.parent / "birds"
    window = (root / "main_window.py").read_text(encoding="utf-8")
    for call in ("load_session, path", "load_preset, path_str"):
        assert "run_in_background" in window and call in window, call
    dialog = (root / "dialogs" / "import_dialog.py").read_text(encoding="utf-8")
    assert "self._read(list_excel_sheets" in dialog
    assert dialog.count("self._read(read_tabular") == 2
