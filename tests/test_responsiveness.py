"""The crash on a redraw, the slow session loads, and the tests that
wrote into the user's own settings.

* Twice the app closed on its own (macOS 26, Qt 6.11): Matplotlib put
  up its wait cursor for a redraw and Qt, building that cursor from a
  bitmap, crashed inside CGImageCreate.  The canvas now asks only for
  native cursors, and never for the wait one.
* Every view redrew whenever anything touched it, hidden or not: a
  session load restored and redrew all of them, Spider 29 times over.
  A page behind another now holds its redraws and is drawn once, when
  shown.
* The suite opened and saved sessions in the user's real settings,
  pushing pytest's temporary files into File → Recent sessions.
"""

from __future__ import annotations

import collections
import os
from pathlib import Path

import numpy as np
import pytest
from matplotlib.backend_tools import Cursors
from PySide6.QtCore import QSettings, Qt

#: What Qt draws natively on macOS -- anything else is built from a
#: bitmap through QImage::toCGImage, where the crashes happened.
_NATIVE = {Qt.CursorShape.ArrowCursor, Qt.CursorShape.PointingHandCursor,
           Qt.CursorShape.CrossCursor, Qt.CursorShape.OpenHandCursor,
           Qt.CursorShape.ClosedHandCursor, Qt.CursorShape.SplitHCursor,
           Qt.CursorShape.SplitVCursor, Qt.CursorShape.IBeamCursor}


# ---------------------------------------------------------------------------
# Cursors
# ---------------------------------------------------------------------------

@pytest.fixture
def canvas(qapp):
    from birds.views.plot_canvas import PlotCanvas
    pc = PlotCanvas()
    shapes = []
    pc.canvas.setCursor = lambda shape: shapes.append(shape)
    return pc, shapes


def test_every_cursor_the_canvas_asks_for_is_native(canvas):
    pc, shapes = canvas
    for cursor in Cursors:
        pc.canvas.set_cursor(cursor)
    assert shapes and set(shapes) <= _NATIVE
    assert Qt.CursorShape.WaitCursor not in shapes


def test_a_redraw_after_a_pause_keeps_a_native_cursor(canvas):
    """Matplotlib sets the wait cursor on any draw a second after the
    last -- the path of both crashes."""
    pc, shapes = canvas
    pc.figure.add_subplot(111).plot([0, 1], [0, 1])
    pc.toolbar._draw_time = -np.inf            # long since the last draw
    pc.canvas.draw()
    assert Qt.CursorShape.WaitCursor not in shapes
    assert set(shapes) <= _NATIVE


def test_main_logs_native_crashes(tmp_path, monkeypatch):
    import faulthandler

    import main
    monkeypatch.setattr(main, "_CRASH_LOG", tmp_path / "crash.log")
    try:
        main._install_faulthandler()
        assert faulthandler.is_enabled()
        assert "SESSION START" in (tmp_path / "crash.log").read_text(encoding="utf-8")
    finally:
        faulthandler.disable()
        if main._FAULT_FILE is not None:
            main._FAULT_FILE.close()
            main._FAULT_FILE = None


# ---------------------------------------------------------------------------
# Hidden pages hold their redraws
# ---------------------------------------------------------------------------

@pytest.fixture
def window(qapp, full_df, plot_style):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = full_df
    w.style.copy_from(plot_style)
    w.on_dataset_replaced()
    return w


def _count_draws(window):
    draws = collections.Counter()
    for name in window._VIEW_ATTRS:
        view = getattr(window, name)
        canvas = getattr(view, "canvas", None)
        if canvas is None or not hasattr(canvas, "draw"):
            continue
        original = canvas.draw

        def draw(*a, _o=original, _n=name, **k):
            draws[_n] += 1
            return _o(*a, **k)
        canvas.draw = draw
    return draws


def test_a_hidden_page_waits_and_is_drawn_once_when_shown(window):
    from birds.views.deferral import PENDING
    draws = _count_draws(window)
    view = window.classification
    assert window.stack.currentWidget() is not view
    for _ in range(5):
        view.update_plot()
    assert draws["classification"] == 0 and getattr(view, PENDING)
    window.stack.setCurrentWidget(view)
    assert draws["classification"] == 1 and not getattr(view, PENDING)
    window.stack.setCurrentWidget(window.welcome)
    window.stack.setCurrentWidget(view)        # nothing new to draw
    assert draws["classification"] == 1


def test_the_menu_still_draws_the_page_it_opens(window):
    draws = _count_draws(window)
    window._open_tectonic("pearce2008_thyb_nbyb", "volcanic", "Mafic")
    assert window.stack.currentWidget() is window.tectonic
    assert draws["tectonic"] >= 1
    assert window.tectonic.canvas.figure.axes


def test_a_selection_redraws_only_the_page_on_screen(window):
    window._open_classification_family("volcanic")
    draws = _count_draws(window)
    window.selection.toggle("S3")
    assert draws["classification"] == 1
    assert sum(n for v, n in draws.items() if v != "classification") == 0


def test_a_session_is_drawn_once_on_the_page_it_was_saved_on(
        window, tmp_path, qapp):
    from birds.main_window import BirdsMainWindow
    window._open_spider("multielement")
    window.spider.update_plot()
    window._session_path = tmp_path / "s.birds"
    window.on_save_session()

    other = BirdsMainWindow()
    other._open_bivariate("individual")         # whatever was showing
    draws = _count_draws(other)
    other._load_session_path(tmp_path / "s.birds")
    assert other.stack.currentWidget() is other.spider
    assert draws["spider"] == 1
    assert sum(n for v, n in draws.items() if v != "spider") == 0
    assert other.spider.canvas.figure.axes


def test_restoring_spider_elements_redraws_once(qapp, full_df):
    from birds.data_manager import DataManager
    from birds.views.spider import SpiderView

    data = DataManager()
    data.df = full_df
    view = SpiderView(data, _style())
    view.set_mode("multielement")
    state = view.serialize()
    ctrl = view._controls["multielement"]
    first = ctrl.elements_list.item(0).text()
    state["multielement"]["selected_elements"] = [first]
    calls = []
    original = view.canvas.draw
    view.canvas.draw = lambda: (calls.append(1), original())
    view.restore(state)
    # restore() shows each mode, then the saved one: three draws, where
    # unticking the elements one by one added one per element.
    assert len(calls) == 3
    checked = [ctrl.elements_list.item(i).text()
               for i in range(ctrl.elements_list.count())
               if ctrl.elements_list.item(i).checkState()
               == Qt.CheckState.Checked]
    assert checked == [first]


def _style():
    from birds.plot_style import PlotStyle
    return PlotStyle()


# ---------------------------------------------------------------------------
# The suite stays out of the user's settings
# ---------------------------------------------------------------------------

def test_the_suite_writes_to_a_sandbox_not_the_users_home(qapp):
    """Changing HOME is not enough on macOS: native settings go through
    CFPreferences to the real ~/Library/Preferences whatever HOME says,
    so the window must use the default format, which the suite sets to
    an INI file in the sandbox."""
    from birds.main_window import BirdsMainWindow
    from birds.session import autosave_dir

    home = Path(os.environ["HOME"])
    assert home.name.startswith("birds-tests-")
    assert Path.home() == home
    assert autosave_dir().is_relative_to(home)
    window = BirdsMainWindow()
    assert window._qs.format() == QSettings.Format.IniFormat
    assert Path(window._qs.fileName()).is_relative_to(home)


def test_outside_the_suite_the_settings_stay_native(qapp):
    """Users keep their recent-sessions list: with the platform's own
    format as the default -- as everywhere but this suite -- the window
    reads the same native settings as always.  (Only read here.)"""
    from birds.main_window import BirdsMainWindow

    QSettings.setDefaultFormat(QSettings.Format.NativeFormat)
    try:
        window = BirdsMainWindow()
        assert window._qs.format() == QSettings.Format.NativeFormat
        assert window._qs.organizationName() == "BIRDS"
        assert window._qs.applicationName() == "BIRDS"
    finally:
        QSettings.setDefaultFormat(QSettings.Format.IniFormat)
