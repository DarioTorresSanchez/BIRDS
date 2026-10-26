"""Shared fixtures.

Qt needs a display; the offscreen platform plugin gives us one without a
window server, which is what lets the GUI tests run in CI.  It has to be
set before PySide6 is imported anywhere, hence the module-level
assignment rather than a fixture.
"""

from __future__ import annotations

import atexit
import os
import shutil
import tempfile

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# The suite must leave the user's own B.I.R.D.S alone.  The tests open
# and save sessions, and the app keeps its recent-sessions list in
# QSettings and its auto-saves, crash log and style presets under
# ~/.birds -- so a run used to push pytest's temporary sessions into the
# user's File → Recent sessions, evicting real ones, and write to the
# real crash log.  Both now point at a throwaway directory.  Matplotlib
# reads its config and font cache from the real home first, so the font
# cache is not rebuilt on every run.
import matplotlib  # noqa: E402

matplotlib.get_configdir()
matplotlib.get_cachedir()
_SANDBOX = tempfile.mkdtemp(prefix="birds-tests-")
os.environ["HOME"] = _SANDBOX
# Windows takes the home folder from USERPROFILE and ignores HOME.
os.environ["USERPROFILE"] = _SANDBOX
atexit.register(shutil.rmtree, _SANDBOX, ignore_errors=True)

from PySide6.QtCore import QSettings  # noqa: E402

QSettings.setDefaultFormat(QSettings.Format.IniFormat)
QSettings.setPath(QSettings.Format.IniFormat, QSettings.Scope.UserScope,
                  _SANDBOX)

import numpy as np
import pandas as pd
import pytest

MAJORS = [
    "SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO", "MnO",
    "MgO", "CaO", "Na2O", "K2O", "P2O5",
]

TRACES = [
    "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er",
    "Tm", "Yb", "Lu", "Rb", "Ba", "Th", "U", "Nb", "Ta", "Sr", "Zr",
    "Hf", "Y", "V", "Sc", "Co", "Ni", "Cr", "Pb", "Cs",
]

MODAL = [
    "Q", "A", "P", "F", "Ol", "Opx", "Cpx", "Pl", "Hbl", "Px",
    "An", "Ab", "Or", "Lithic", "Crystal", "Vitric",
    "Blocks", "Lapilli", "Ash",
]


@pytest.fixture(scope="session")
def qapp():
    """One QApplication for the whole session — Qt allows only one."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    return app


# ---------------------------------------------------------------------------
# Leaving
# ---------------------------------------------------------------------------
# The tests leave hundreds of windows alive.  On Python 3.12 the
# interpreter then destroys them, and the QApplication, in an order Qt
# does not survive: in CI every test passed and was reported -- "4000
# passed" -- and the process still died with "Fatal Python error:
# Aborted" and no Python frame, failing the run.  By the time pytest
# unconfigures, every result has been written; leave with pytest's own
# status and skip the teardown.  The application quits through its event
# loop and is not affected.

_EXIT_STATUS = 0


def pytest_sessionfinish(session, exitstatus):
    global _EXIT_STATUS
    _EXIT_STATUS = int(exitstatus)


@pytest.hookimpl(trylast=True)
def pytest_unconfigure(config):
    if os.environ.get("BIRDS_TESTS_FULL_TEARDOWN"):
        return                      # to debug the teardown itself
    import sys
    sys.stdout.flush()
    sys.stderr.flush()
    shutil.rmtree(_SANDBOX, ignore_errors=True)
    if sys.platform == "win32":
        # os._exit still unloads the DLLs on Windows, and Qt's own
        # clean-up then fails the same way ("access violation");
        # TerminateProcess ends the process without running it.
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.TerminateProcess(kernel32.GetCurrentProcess(),
                                  _EXIT_STATUS)
    os._exit(_EXIT_STATUS)


@pytest.fixture
def majors_df() -> pd.DataFrame:
    """Twelve realistic major-element analyses, closed to 100 wt %."""
    rng = np.random.default_rng(20260101)
    centre = [52, 1.2, 16, 2.5, 6, 0.15, 6, 9, 3, 1.5, 0.25]
    spread = [8, 0.6, 2, 1, 2, 0.05, 4, 3, 1, 1, 0.1]
    rows = []
    for _ in range(12):
        v = np.abs(rng.normal(centre, spread))
        rows.append(v / v.sum() * 100)
    df = pd.DataFrame(rows, columns=MAJORS)
    df.insert(0, "Sample_Name", [f"S{i}" for i in range(len(df))])
    df["Group"] = ["A"] * 6 + ["B"] * 6
    return df


@pytest.fixture
def full_df(majors_df: pd.DataFrame) -> pd.DataFrame:
    """Majors + traces + modal counts — enough for every diagram."""
    rng = np.random.default_rng(7)
    n = len(majors_df)
    extra = {c: np.abs(rng.normal(20, 8, n)) + 0.5 for c in TRACES + MODAL}
    df = majors_df.assign(**extra)
    df["SiO2"] = np.linspace(42, 76, n)
    return df


@pytest.fixture
def plot_style():
    from birds.plot_style import GroupStyle, PlotStyle
    style = PlotStyle()
    style.group_columns = ["Group"]
    style.groups = [GroupStyle(name="A"), GroupStyle(name="B")]
    return style
