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


def test_every_mention_of_the_version_is_the_programs():
    """A release is filed under one version; the files that name it are
    set by hand and drift apart unnoticed (the About box said
    "0.1.0 (alpha)" long after the alpha)."""
    import birds
    v = birds.__version__

    def read(path):
        return (ROOT / path).read_text(encoding="utf-8")

    assert re.search(r'^version = "([^"]+)"$', read("pyproject.toml"),
                     re.MULTILINE).group(1) == v
    assert re.search(r"^version: (\S+)$", read("CITATION.cff"),
                     re.MULTILINE).group(1) == v
    readme = read("README.md")
    assert re.search(r"badge/version-([^-%]+)", readme).group(1) == v
    assert re.search(r"\*\*Version (\S+) \(", readme).group(1) == v
    assert re.search(r"version = \{([^}]+)\}", readme).group(1) == v
    assert re.search(r"\(Version (\S+)\) \[Computer software\]",
                     readme).group(1) == v
    assert f"The current version, {v}," in readme
    # The About box and the manual read it rather than repeat it.
    assert "Version {__version__}" in read("birds/main_window.py")
    sys.path.insert(0, str(ROOT / "docs"))
    import manual_content
    assert manual_content.VERSION == v
    assert manual_content.SUBTITLE.endswith(f"Version {v}")


@pytest.mark.parametrize("version, numbers", [
    ("0.1.0", "0.1.0"), ("0.1.0b1", "0.1.0"), ("1.2.3rc2", "1.2.3"),
    ("0.2.0a1", "0.2.0"), ("2.0", "2.0"),
])
def test_macos_is_given_the_version_as_numbers_only(monkeypatch, version,
                                                     numbers):
    monkeypatch.setattr(app_info, "version", lambda: version)
    assert app_info.bundle_version() == numbers
    plist = app_info.info_plist()
    assert plist["CFBundleShortVersionString"] == numbers
    assert plist["CFBundleVersion"] == numbers


def test_the_app_declares_the_macos_its_qt_needs():
    assert app_info.info_plist()["LSMinimumSystemVersion"] == "13.0"
    spec = (PACKAGING / "birds.spec").read_text(encoding="utf-8")
    assert "version=app_info.bundle_version()" in spec


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


# ---------------------------------------------------------------------------
# Linux: install.sh, run from the unpacked bundle
# ---------------------------------------------------------------------------

INSTALL_SH = PACKAGING / "linux" / "install.sh"
posix_only = pytest.mark.skipif(sys.platform == "win32",
                                reason="a POSIX shell script")


@pytest.fixture
def linux_bundle(tmp_path):
    """BIRDS-linux/ as the build workflow packs it, with a stand-in
    program, and an empty home to install into."""
    import shutil
    bundle = tmp_path / "BIRDS-linux"
    program = bundle / "BIRDS"
    program.mkdir(parents=True)
    (program / "BIRDS").write_text("#!/bin/sh\necho birds\n")
    (program / "BIRDS").chmod(0o755)
    (program / "_internal").mkdir()
    (program / "_internal" / "lib.so").write_bytes(b"x")
    for item in (PACKAGING / "linux").iterdir():
        shutil.copy(item, bundle)
    for name in ("birds_app_256.png", "birds_document_256.png"):
        shutil.copy(PACKAGING / "icons" / name, bundle)
    home = tmp_path / "home"
    home.mkdir()
    # Only the system's own commands: no desktop tools, which are
    # optional, and none of the user's.
    env = {"HOME": str(home), "PATH": "/usr/bin:/bin"}

    def run(*args):
        return subprocess.run(["sh", str(bundle / "install.sh"), *args],
                              env=env, capture_output=True, text=True)
    return SimpleNamespace(bundle=bundle, home=home, run=run)


def test_install_sh_is_executable_in_the_repository():
    """The bundle is packed from a checkout, and the mode comes from git."""
    out = subprocess.run(["git", "ls-files", "-s", "packaging/linux/install.sh"],
                         cwd=ROOT, capture_output=True, text=True)
    if out.returncode or not out.stdout:
        pytest.skip("not a git checkout")
    assert out.stdout.startswith("100755")


@posix_only
def test_install_sh_installs_for_the_user(linux_bundle):
    result = linux_bundle.run()
    assert result.returncode == 0, result.stderr
    share = linux_bundle.home / ".local" / "share"
    prefix = share / "BIRDS"
    assert (prefix / "BIRDS").stat().st_mode & 0o111
    assert (prefix / "_internal" / "lib.so").exists()
    command = linux_bundle.home / ".local" / "bin" / "BIRDS"
    assert command.is_symlink() and command.resolve() == (prefix / "BIRDS").resolve()
    entry = (share / "applications" / "birds.desktop").read_text()
    assert f'Exec="{prefix}/BIRDS" %f' in entry
    assert "MimeType=application/x-birds-session;" in entry
    assert (share / "mime" / "packages" / "birds-session.xml").exists()
    assert (share / "icons" / "hicolor" / "256x256" / "apps" / "birds.png").exists()
    assert (share / "icons" / "hicolor" / "256x256" / "mimetypes"
            / "application-x-birds-session.png").exists()
    assert "is installed" in result.stdout


@posix_only
def test_install_sh_replaces_an_earlier_copy(linux_bundle):
    assert linux_bundle.run().returncode == 0
    stale = linux_bundle.home / ".local" / "share" / "BIRDS" / "_internal" / "old.so"
    stale.write_bytes(b"old")
    assert linux_bundle.run().returncode == 0
    assert not stale.exists()


@posix_only
def test_install_sh_uninstalls_what_it_installed(linux_bundle):
    assert linux_bundle.run().returncode == 0
    result = linux_bundle.run("--uninstall")
    assert result.returncode == 0, result.stderr
    share = linux_bundle.home / ".local" / "share"
    assert not (share / "BIRDS").exists()
    assert not (share / "applications" / "birds.desktop").exists()
    assert not (share / "mime" / "packages" / "birds-session.xml").exists()
    assert not list((share / "icons").rglob("*.png"))
    assert not (linux_bundle.home / ".local" / "bin" / "BIRDS").exists()


@posix_only
def test_install_sh_leaves_a_birds_command_it_did_not_make(linux_bundle):
    bin_dir = linux_bundle.home / ".local" / "bin"
    bin_dir.mkdir(parents=True)
    (bin_dir / "BIRDS").write_text("someone else's\n")
    assert linux_bundle.run("--uninstall").returncode == 0
    assert (bin_dir / "BIRDS").read_text() == "someone else's\n"


@posix_only
def test_install_sh_refuses_to_run_outside_the_bundle(linux_bundle):
    import shutil
    shutil.rmtree(linux_bundle.bundle / "BIRDS")
    result = linux_bundle.run()
    assert result.returncode == 1
    assert "unpacked bundle" in result.stderr
    assert not (linux_bundle.home / ".local" / "share" / "BIRDS").exists()


def test_the_spec_bundles_the_document_icon_and_the_logo():
    spec = (PACKAGING / "birds.spec").read_text(encoding="utf-8")
    assert "app_info.info_plist()" in spec
    assert "DOCUMENT_ICON" in spec and "birds\" / \"resources\"" in spec


def _offered_formats():
    from birds.dialogs.export_plot_dialog import FORMATS
    from birds.views._export_helpers import _FILTER_TO_EXT
    return ({fmt for _label, fmt in FORMATS}
            | {ext.lstrip(".") for ext in _FILTER_TO_EXT.values()})


def test_every_export_format_has_its_backend_declared():
    """matplotlib imports the writer of a format only when a file is
    saved, so PyInstaller does not see it: the first betas exported PNG
    and JPEG and failed on the rest with "No module named
    'matplotlib.backends.backend_svg'"."""
    import importlib
    offered = _offered_formats()
    assert offered == set(app_info.EXPORT_BACKENDS)
    for fmt in offered:
        module = importlib.import_module(app_info.EXPORT_BACKENDS[fmt])
        assert hasattr(module, "FigureCanvas"), fmt


def test_the_spec_hands_the_export_backends_to_pyinstaller():
    spec = (PACKAGING / "birds.spec").read_text(encoding="utf-8")
    assert "app_info.EXPORT_BACKENDS.values()" in spec
    assert 'collect_submodules("fontTools.ttLib.tables")' in spec


def test_the_self_test_writes_every_format(qapp):
    from birds import selftest
    names = [name for name, _check in selftest.CHECKS]
    assert "plot export" in names
    written = selftest._plot_export().split()
    assert set(written) == _offered_formats()


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
    jobs = re.findall(r"^  (\w+):\n", text.split("\njobs:\n", 1)[1],
                      re.MULTILINE)
    assert jobs == ["windows", "linux", "release"]


def _job(name: str) -> str:
    text = BUILD_FLOW.read_text(encoding="utf-8")
    return re.search(rf"^  {name}:\n(.*?)(?=^  \w+:\n|\Z)", text,
                     re.MULTILINE | re.DOTALL).group(1)


def test_a_version_tag_files_the_builds_as_a_draft_release():
    """Only a tag reaches the Releases page, only once both builds pass,
    and only as a draft: publishing stays a decision taken by hand."""
    job = _job("release")
    assert "if: startsWith(github.ref, 'refs/tags/v')" in job
    assert "needs: [windows, linux]" in job
    assert "contents: write" in job
    assert "gh release create" in job and "--draft" in job


def test_the_release_refuses_a_tag_that_is_not_the_version():
    """The installers are named after birds/__init__.py, so the check
    reads the version the same way."""
    job = _job("release")
    assert "app_info.version()" in job
    assert '"${GITHUB_REF_NAME#v}" != "$version"' in job
    assert job.index("Check the tag") < job.index("gh release create")


@pytest.mark.parametrize("tag, pre", [
    ("v0.1.0b1", True), ("v0.2.0rc1", True), ("v0.2.0a3", True),
    ("v0.1.0", False), ("v1.0.0", False),
])
def test_a_beta_is_filed_as_a_pre_release(tag, pre):
    job = _job("release")
    pattern = re.search(r'=~ (\S+) \]\]', job).group(1)
    assert "--prerelease" in job
    assert bool(re.search(pattern, tag)) is pre


def test_the_linux_bundle_is_built_on_a_settled_ubuntu():
    """The bundle needs a C library at least as new as the build's."""
    assert "runs-on: ubuntu-24.04" in _job("linux")


@pytest.mark.parametrize("path", [
    "packaging/birds.spec", "packaging/windows/birds.iss",
    "packaging/icons/birds_app_256.png",
    "packaging/icons/birds_document_256.png",
])
def test_what_the_build_workflow_uses_is_in_the_repository(path):
    text = BUILD_FLOW.read_text(encoding="utf-8")
    assert (ROOT / path).exists()
    assert path.replace("/", "\\") in text or path in text
