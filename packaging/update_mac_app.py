"""Rebuild the macOS app from the source and replace the installed copy.

    python3 packaging/update_mac_app.py                build, check, install
    python3 packaging/update_mac_app.py --tests        run the test suite first
    python3 packaging/update_mac_app.py --build-only   build and check only

Changes are made to the source; ``BIRDS.app`` is a snapshot of it, and
this brings the installed copy up to date in one step.  The installed
copy is replaced only when the new build passes ``--self-test``, and
only if what sits there is B.I.R.D.S itself.  Run it with the Python
that runs B.I.R.D.S; it needs PyInstaller.
"""

from __future__ import annotations

import argparse
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import app_info  # noqa: E402

SPEC = HERE / "birds.spec"
BUILT = ROOT / "dist" / f"{app_info.APP_NAME}.app"
LOG = ROOT / "build" / "update_mac_app.log"
APPLICATIONS = Path("/Applications")
LSREGISTER = Path("/System/Library/Frameworks/CoreServices.framework"
                  "/Frameworks/LaunchServices.framework/Support/lsregister")
MACOS = sys.platform == "darwin"


class Stop(Exception):
    """A reason not to go on.  Raised before the installed app is touched."""


def executable(app: Path) -> Path:
    return app / "Contents" / "MacOS" / app_info.APP_NAME


def bundle_id(app: Path) -> str | None:
    try:
        with open(app / "Contents" / "Info.plist", "rb") as fh:
            return plistlib.load(fh).get("CFBundleIdentifier")
    except (OSError, plistlib.InvalidFileException):
        return None


def is_running(app: Path) -> bool:
    found = subprocess.run(["pgrep", "-f", str(executable(app))],
                           capture_output=True)
    return found.returncode == 0


def has_pyinstaller() -> bool:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        return False
    return True


def run_tests() -> bool:
    return subprocess.run([sys.executable, "-m", "pytest", "-q"],
                          cwd=ROOT).returncode == 0


def build() -> bool:
    """Run PyInstaller, its chatter going to the log."""
    LOG.parent.mkdir(exist_ok=True)
    with open(LOG, "w") as log:
        done = subprocess.run(
            [sys.executable, "-m", "PyInstaller", str(SPEC), "--noconfirm"],
            cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    return done.returncode == 0


def self_test(app: Path) -> bool:
    return subprocess.run([str(executable(app)), "--self-test"]).returncode == 0


def replace_app(built: Path, installed: Path) -> None:
    """Put a copy of ``built`` at ``installed``, replacing only B.I.R.D.S.

    The copy is made beside the old app and swapped in by renaming, so
    whatever fails, a working app is left at ``installed``.
    """
    if installed.exists() and bundle_id(installed) != app_info.BUNDLE_ID:
        raise Stop(f"{installed} is not B.I.R.D.S "
                   f"(it is {bundle_id(installed) or 'unidentified'}); "
                   f"left alone.")
    staging = installed.with_name(f".{installed.name}.new")
    old = installed.with_name(f".{installed.name}.old")
    for leftover in (staging, old):            # from an interrupted run
        shutil.rmtree(leftover, ignore_errors=True)
    # ditto keeps the bundle's symlinks, permissions and signatures.
    copied = subprocess.run(["ditto", str(built), str(staging)],
                            capture_output=True, text=True)
    if copied.returncode != 0:
        shutil.rmtree(staging, ignore_errors=True)
        raise Stop(f"copying the new build failed ({copied.stderr.strip()}); "
                   f"{installed} was not touched.")
    if installed.exists():
        installed.rename(old)
    staging.rename(installed)
    shutil.rmtree(old, ignore_errors=True)


def register(installed: Path, built: Path) -> None:
    """Tell macOS about the new copy, and forget the one in dist/, so a
    double-clicked session opens in the installed app."""
    subprocess.run([str(LSREGISTER), "-f", str(installed)], check=False)
    subprocess.run([str(LSREGISTER), "-u", str(built)], check=False)


def source_state() -> str:
    """The commit built, and whether there was work not yet committed."""
    def git(*args: str) -> str:
        done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                              text=True)
        return done.stdout.strip() if done.returncode == 0 else ""

    commit = git("rev-parse", "--short", "HEAD") or "unknown commit"
    if git("status", "--porcelain", "--untracked-files=no"):
        return f"{commit} plus uncommitted changes"
    return commit


def step(text: str) -> None:
    print(f"\n==> {text}", flush=True)


def update(dest: Path, tests: bool = False, build_only: bool = False) -> str:
    """Every step in order; returns what was done, raises Stop if not."""
    if not MACOS:
        raise Stop("this builds the macOS app; for Windows and Linux see "
                   "packaging/README.md.")
    if not has_pyinstaller():
        raise Stop(f"PyInstaller is not installed for {sys.executable}: "
                   f"{sys.executable} -m pip install pyinstaller")
    installed = dest / BUILT.name
    quit_first = (f"B.I.R.D.S is open from {installed}; quit it and run "
                  f"this again.")
    if not build_only and is_running(installed):
        raise Stop(quit_first)
    state = source_state()

    if tests:
        step("Running the test suite")
        if not run_tests():
            raise Stop("tests failed; nothing was built.")

    step(f"Building {BUILT.name} from {state} (a few minutes)")
    if not build():
        raise Stop(f"PyInstaller failed; its output is in {LOG}.")

    step("Self-test of the new build")
    if not self_test(BUILT):
        raise Stop(f"the new build failed its self-test; {installed} was "
                   f"not touched.")
    if build_only:
        return f"Built and checked {BUILT} ({state})."

    if is_running(installed):              # opened while it was building
        raise Stop(quit_first)
    step(f"Installing in {dest}")
    replace_app(BUILT, installed)
    register(installed, BUILT)
    return (f"Installed B.I.R.D.S {app_info.version()} ({state}) "
            f"in {dest}.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Rebuild BIRDS.app from the source and replace the "
                    "installed copy.")
    parser.add_argument("--tests", action="store_true",
                        help="run the test suite before building")
    parser.add_argument("--build-only", action="store_true",
                        help="build and self-test, leave the installed "
                             "copy alone")
    parser.add_argument("--dest", type=Path, default=APPLICATIONS,
                        help="folder the app is installed in "
                             "(default: /Applications)")
    args = parser.parse_args(argv)
    try:
        print(f"\n{update(args.dest, args.tests, args.build_only)}")
    except Stop as reason:
        print(f"\nStopped: {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
