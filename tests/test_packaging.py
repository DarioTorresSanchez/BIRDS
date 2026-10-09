"""Opening a double-clicked session, and what the app declares about it.

Double-clicking a ``.birds`` file opens it in B.I.R.D.S once the app is
installed; the system shows it with the session icon.  The opening is
tested here directly; the packaging files -- Info.plist keys, the
Windows installer, the Linux MIME type -- are checked for agreeing with
each other and with the program, since a mismatch fails silently: the
file just keeps the generic icon.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from birds.app import BirdsApplication, SessionOpener, session_paths_from_argv
from birds.session import SESSION_EXT

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging"
sys.path.insert(0, str(PACKAGING))

import app_info  # noqa: E402


# ---------------------------------------------------------------------------
# The path handed over
# ---------------------------------------------------------------------------

def test_only_session_files_on_the_command_line_count(tmp_path):
    session = tmp_path / "rocks.birds"
    session.write_bytes(b"x")
    upper = tmp_path / "MORE.BIRDS"
    upper.write_bytes(b"x")
    other = tmp_path / "data.csv"
    other.write_text("a")
    argv = ["BIRDS", "-psn_0_12345", str(other), str(session),
            str(tmp_path / "missing.birds"), str(upper), "--style", ""]
    assert session_paths_from_argv(argv) == [session, upper]
    assert session_paths_from_argv(["BIRDS"]) == []


class _Window:
    def __init__(self):
        self.opened = []

    def open_session_file(self, path):
        self.opened.append(Path(path))


def test_a_session_sent_before_the_window_waits_for_it():
    opener = SessionOpener()
    opener.open(Path("a.birds"))
    opener.open(Path("b.birds"))
    window = _Window()
    opener.attach(window)
    assert window.opened == [Path("b.birds")]       # one window, the last
    opener.open(Path("c.birds"))                     # and now straight in
    assert window.opened == [Path("b.birds"), Path("c.birds")]


def test_nothing_is_opened_when_nothing_was_sent():
    opener = SessionOpener()
    window = _Window()
    opener.attach(window)
    assert window.opened == []


def test_the_macos_file_open_event_reaches_the_opener(qapp):
    from PySide6.QtGui import QFileOpenEvent
    fake = SimpleNamespace(opener=SessionOpener())
    handled = BirdsApplication.event(fake, QFileOpenEvent("/tmp/x.birds"))
    assert handled is True
    assert fake.opener.pending == [Path("/tmp/x.birds")]


# ---------------------------------------------------------------------------
# The window opening it
# ---------------------------------------------------------------------------

@pytest.fixture
def saved_session(qapp, tmp_path):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = pd.DataFrame({"Sample_Name": ["A", "B"],
                              "SiO2": [50.0, 60.0]})
    w.on_dataset_replaced()
    path = tmp_path / f"saved{SESSION_EXT}"
    w._session_path = path
    w.on_save_session()
    return path


def test_the_window_opens_a_handed_over_session(saved_session):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.open_session_file(saved_session)
    assert w._session_path == saved_session
    assert list(w.data.df["SiO2"]) == [50.0, 60.0]


def test_a_session_opened_at_launch_is_not_covered_by_the_recovery_offer(
        saved_session, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    from birds.main_window import BirdsMainWindow
    asked = []
    monkeypatch.setattr(QMessageBox, "question",
                        lambda *a, **k: asked.append(1))
    w = BirdsMainWindow()
    w.open_session_file(saved_session)
    w._maybe_offer_recovery()
    assert not asked


def test_unsaved_work_is_not_thrown_away_silently(saved_session,
                                                  monkeypatch):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = pd.DataFrame({"SiO2": [1.0]})
    w.setWindowModified(True)
    monkeypatch.setattr(w, "_confirm_discard_changes", lambda _a: False)
    w.open_session_file(saved_session)
    assert list(w.data.df["SiO2"]) == [1.0]


# ---------------------------------------------------------------------------
# What the packaged app declares
# ---------------------------------------------------------------------------

def test_the_declared_extension_is_the_programs():
    assert f".{app_info.SESSION_EXTENSION}" == SESSION_EXT


def test_the_version_is_the_programs():
    import birds
    assert app_info.version() == birds.__version__
    iss = (PACKAGING / "windows" / "birds.iss").read_text(encoding="utf-8")
    assert f'#define AppVersion "{birds.__version__}"' in iss


def test_info_plist_ties_the_extension_to_the_document_icon():
    plist = app_info.info_plist()
    exported = plist["UTExportedTypeDeclarations"][0]
    document = plist["CFBundleDocumentTypes"][0]
    assert exported["UTTypeTagSpecification"][
        "public.filename-extension"] == [app_info.SESSION_EXTENSION]
    assert document["LSItemContentTypes"] == [exported["UTTypeIdentifier"]]
    assert document["LSHandlerRank"] == "Owner"
    for icon in (document["CFBundleTypeIconFile"],
                 exported["UTTypeIconFile"]):
        assert (app_info.ICONS / icon).is_file(), icon
    assert plist["CFBundleIdentifier"] == app_info.BUNDLE_ID
    assert exported["UTTypeIdentifier"].startswith(app_info.BUNDLE_ID)


def test_the_plist_survives_being_written():
    import plistlib
    data = plistlib.dumps(app_info.info_plist())
    assert plistlib.loads(data) == app_info.info_plist()


@pytest.mark.parametrize("name", [app_info.APP_ICON, app_info.DOCUMENT_ICON])
def test_every_icon_exists_in_every_format(name):
    from PIL import Image
    for suffix in (".png", "_256.png", ".ico", ".icns"):
        assert (app_info.ICONS / f"{name}{suffix}").is_file(), suffix
    sizes = Image.open(app_info.ICONS / f"{name}.ico").info["sizes"]
    assert {(16, 16), (32, 32), (256, 256)} <= set(sizes)
    assert Image.open(app_info.ICONS / f"{name}.png").size == (1024, 1024)


def test_the_windows_installer_registers_the_session_type():
    iss = (PACKAGING / "windows" / "birds.iss").read_text(encoding="utf-8")
    assert 'Subkey: "Software\\Classes\\.birds"' in iss
    assert f"{app_info.DOCUMENT_ICON}.ico" in iss
    assert f"{app_info.APP_NAME}.exe" in iss
    assert "ChangesAssociations=yes" in iss
    assert '""%1""' in iss                  # the double-clicked file


def test_the_linux_mime_type_matches_the_desktop_entry():
    mime = (PACKAGING / "linux" / "birds-session.xml").read_text()
    desktop = (PACKAGING / "linux" / "birds.desktop").read_text()
    assert f'type="{app_info.SESSION_MIME}"' in mime
    assert f'<glob pattern="*.{app_info.SESSION_EXTENSION}"/>' in mime
    assert f"MimeType={app_info.SESSION_MIME};" in desktop
    assert re.search(r"^Exec=.* %f$", desktop, re.MULTILINE)


def test_the_spec_bundles_the_document_icon_and_the_logo():
    spec = (PACKAGING / "birds.spec").read_text()
    assert "app_info.info_plist()" in spec
    assert "DOCUMENT_ICON" in spec and "birds\" / \"resources\"" in spec


# ---------------------------------------------------------------------------
# The self-test a packaged build runs, and an optional library gone wrong
# ---------------------------------------------------------------------------

def test_the_self_test_passes_here(qapp):
    from birds.selftest import run
    lines = []
    assert run(echo=lines.append) == 0
    assert lines[-1].endswith("checks passed")
    assert not [line for line in lines if line.startswith("FAIL")]


def test_a_failing_check_fails_the_self_test(monkeypatch):
    from birds import selftest

    def broken():
        raise OSError("libmgrs not found")

    monkeypatch.setattr(selftest, "CHECKS", [("mgrs", broken)])
    lines = []
    assert selftest.run(echo=lines.append) == 1
    assert lines[0].startswith("FAIL  mgrs") and "libmgrs" in lines[0]


def test_a_missing_compiled_library_costs_mgrs_not_the_program(monkeypatch):
    """The packaged app once left out libmgrs: importing mgrs raised an
    OSError, which the optional import did not catch, and B.I.R.D.S
    would not start."""
    import importlib
    import importlib.abc

    import birds.coords as coords

    class _Broken(importlib.abc.MetaPathFinder):
        def find_spec(self, name, path=None, target=None):
            if name == "mgrs":
                raise OSError("Failed to load dynlib libmgrs")
            return None

    monkeypatch.delitem(sys.modules, "mgrs", raising=False)
    monkeypatch.setattr(sys, "meta_path", [_Broken(), *sys.meta_path])
    try:
        importlib.reload(coords)
        assert coords._HAS_MGRS is False
    finally:
        monkeypatch.undo()
        importlib.reload(coords)


def test_the_spec_bundles_the_mgrs_library():
    spec = (PACKAGING / "birds.spec").read_text()
    assert 'glob("libmgrs*")' in spec and "binaries=binaries" in spec
