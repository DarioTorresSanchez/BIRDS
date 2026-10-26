"""Opening a double-clicked session, and what the app declares about it.

Double-clicking a ``.birds`` file opens it in B.I.R.D.S once the app is
installed; the system shows it with the session icon.  The opening is
tested here directly; the packaging files -- Info.plist keys, the
Windows installer, the Linux MIME type -- are checked for agreeing with
each other and with the program, since a mismatch fails silently: the
file just keeps the generic icon.
"""

from __future__ import annotations

import plistlib
import re
import subprocess
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
import update_mac_app as updater  # noqa: E402


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
    mime = (PACKAGING / "linux" / "birds-session.xml").read_text(encoding="utf-8")
    desktop = (PACKAGING / "linux" / "birds.desktop").read_text(encoding="utf-8")
    assert f'type="{app_info.SESSION_MIME}"' in mime
    assert f'<glob pattern="*.{app_info.SESSION_EXTENSION}"/>' in mime
    assert f"MimeType={app_info.SESSION_MIME};" in desktop
    assert re.search(r"^Exec=.* %f$", desktop, re.MULTILINE)


def test_the_spec_bundles_the_document_icon_and_the_logo():
    spec = (PACKAGING / "birds.spec").read_text(encoding="utf-8")
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
    spec = (PACKAGING / "birds.spec").read_text(encoding="utf-8")
    assert 'glob("libmgrs*")' in spec and "binaries=binaries" in spec


# ---------------------------------------------------------------------------
# Updating the installed app (packaging/update_mac_app.py)
# ---------------------------------------------------------------------------

def _fake_app(folder, marker, identifier=app_info.BUNDLE_ID):
    app = folder / f"{app_info.APP_NAME}.app"
    (app / "Contents" / "MacOS").mkdir(parents=True)
    with open(app / "Contents" / "Info.plist", "wb") as fh:
        plistlib.dump({"CFBundleIdentifier": identifier}, fh)
    updater.executable(app).write_text(marker)
    return app


def _marker(app):
    return updater.executable(app).read_text(encoding="utf-8")


macos_only = pytest.mark.skipif(sys.platform != "darwin",
                                reason="copies with ditto")


@macos_only
def test_the_new_build_replaces_the_installed_one(tmp_path):
    built = _fake_app(tmp_path / "dist", "new")
    installed = _fake_app(tmp_path / "Applications", "old")
    for leftover in (".BIRDS.app.new", ".BIRDS.app.old"):   # interrupted run
        (installed.parent / leftover).mkdir()
    updater.replace_app(built, installed)
    assert _marker(installed) == "new"
    assert [p.name for p in installed.parent.iterdir()] == ["BIRDS.app"]


@macos_only
def test_a_first_install_needs_no_old_copy(tmp_path):
    built = _fake_app(tmp_path / "dist", "new")
    (tmp_path / "Applications").mkdir()
    installed = tmp_path / "Applications" / built.name
    updater.replace_app(built, installed)
    assert _marker(installed) == "new"


@macos_only
def test_an_install_under_the_previous_identifier_is_still_ours(tmp_path):
    """The identifier moved to the project's GitHub account on
    2026-10-26; the copy already installed carries the old one."""
    assert app_info.BUNDLE_ID == "io.github.dariotorressanchez.birds"
    built = _fake_app(tmp_path / "dist", "new")
    installed = _fake_app(tmp_path / "Applications", "old",
                          identifier=app_info.PREVIOUS_BUNDLE_IDS[0])
    updater.replace_app(built, installed)
    assert _marker(installed) == "new"


def test_another_app_with_the_name_is_left_alone(tmp_path):
    built = _fake_app(tmp_path / "dist", "new")
    other = _fake_app(tmp_path / "Applications", "theirs",
                      identifier="org.example.birdwatching")
    with pytest.raises(updater.Stop, match="org.example.birdwatching"):
        updater.replace_app(built, other)
    assert _marker(other) == "theirs"


def test_a_failed_copy_leaves_the_installed_app(tmp_path, monkeypatch):
    built = _fake_app(tmp_path / "dist", "new")
    installed = _fake_app(tmp_path / "Applications", "old")

    def half_a_copy(cmd, **_kw):
        (installed.parent / ".BIRDS.app.new").mkdir()
        return subprocess.CompletedProcess(cmd, 1, "", "No space left")

    monkeypatch.setattr(updater.subprocess, "run", half_a_copy)
    with pytest.raises(updater.Stop, match="No space left"):
        updater.replace_app(built, installed)
    assert _marker(installed) == "old"
    assert [p.name for p in installed.parent.iterdir()] == ["BIRDS.app"]


@pytest.fixture
def pipeline(monkeypatch):
    """Every step of update() recorded instead of run."""
    calls = []
    monkeypatch.setattr(updater, "MACOS", True)
    monkeypatch.setattr(updater, "has_pyinstaller", lambda: True)
    monkeypatch.setattr(updater, "source_state", lambda: "abc1234")
    monkeypatch.setattr(updater, "step", lambda _text: None)
    pipe = SimpleNamespace(calls=calls, tests=True, build=True,
                           self_test=True, running=[])

    def record(name, result=None):
        def run(*_a):
            calls.append(name)
            return getattr(pipe, name) if result is None else result
        return run

    monkeypatch.setattr(updater, "run_tests", record("tests"))
    monkeypatch.setattr(updater, "build", record("build"))
    monkeypatch.setattr(updater, "self_test", record("self_test"))
    monkeypatch.setattr(updater, "replace_app", record("replace", False))
    monkeypatch.setattr(updater, "register", record("register", False))
    monkeypatch.setattr(updater, "is_running",
                        lambda _app: pipe.running.pop(0)
                        if pipe.running else False)
    return pipe


def test_an_update_builds_checks_then_installs(pipeline, tmp_path):
    done = updater.update(tmp_path)
    assert pipeline.calls == ["build", "self_test", "replace", "register"]
    assert "Installed" in done and "abc1234" in done


def test_a_build_failing_its_self_test_is_not_installed(pipeline, tmp_path):
    pipeline.self_test = False
    with pytest.raises(updater.Stop, match="was not touched"):
        updater.update(tmp_path)
    assert pipeline.calls == ["build", "self_test"]


def test_a_failed_build_goes_no_further(pipeline, tmp_path):
    pipeline.build = False
    with pytest.raises(updater.Stop, match="PyInstaller failed"):
        updater.update(tmp_path)
    assert pipeline.calls == ["build"]


def test_failing_tests_stop_the_build(pipeline, tmp_path):
    pipeline.tests = False
    with pytest.raises(updater.Stop, match="tests failed"):
        updater.update(tmp_path, tests=True)
    assert pipeline.calls == ["tests"]


def test_build_only_leaves_the_installed_copy(pipeline, tmp_path):
    done = updater.update(tmp_path, build_only=True)
    assert pipeline.calls == ["build", "self_test"]
    assert "Built and checked" in done


def test_an_open_app_is_not_replaced(pipeline, tmp_path):
    pipeline.running = [True]                       # open from the start
    with pytest.raises(updater.Stop, match="quit it"):
        updater.update(tmp_path)
    assert pipeline.calls == []
    pipeline.running = [False, True]                # opened while building
    with pytest.raises(updater.Stop, match="quit it"):
        updater.update(tmp_path)
    assert "replace" not in pipeline.calls


def test_the_updater_refuses_other_systems(pipeline, tmp_path, monkeypatch):
    monkeypatch.setattr(updater, "MACOS", False)
    with pytest.raises(updater.Stop, match="macOS"):
        updater.update(tmp_path)
    assert pipeline.calls == []


def test_a_stop_is_reported_not_raised(pipeline, tmp_path, capsys):
    pipeline.self_test = False
    assert updater.main(["--dest", str(tmp_path)]) == 1
    assert "Stopped:" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# The build workflow (.github/workflows/build.yml)
# ---------------------------------------------------------------------------

BUILD_FLOW = ROOT / ".github" / "workflows" / "build.yml"


def test_the_build_workflow_runs_only_when_asked():
    """Building installers takes a quarter of an hour on two systems:
    by hand, or for a version tag -- never on every push."""
    text = BUILD_FLOW.read_text(encoding="utf-8")
    on = text.split("\non:\n", 1)[1].split("\njobs:", 1)[0]
    assert "workflow_dispatch:" in on
    assert 'tags: ["v*"]' in on
    assert "branches" not in on and "pull_request" not in on
    jobs = re.findall(r"^  (\w+):\n    runs-on:", text, re.MULTILINE)
    assert jobs == ["windows", "linux"]


@pytest.mark.parametrize("path", [
    "packaging/birds.spec", "packaging/windows/birds.iss",
    "packaging/icons/birds_app_256.png",
    "packaging/icons/birds_document_256.png",
])
def test_what_the_build_workflow_uses_is_in_the_repository(path):
    text = BUILD_FLOW.read_text(encoding="utf-8")
    assert (ROOT / path).exists()
    assert path.replace("/", "\\") in text or path in text
