"""A quick check that an installed B.I.R.D.S has everything it needs.

``BIRDS --self-test`` (or ``python3 main.py --self-test``) runs one small
job through each part that leans on a compiled or late-loaded library
-- a diagram, its export to every format Export plot offers, the
kriging, a UTM and an MGRS conversion, the CIPW norm, a session round
trip, an Excel file, the main window -- prints a line for each, and
exits with 0 when all pass.

It exists for the packaged application: PyInstaller can leave out a
library a package loads in an unusual way, and the program then fails
only when that part is first used.  This finds it at build time.  Run
it after every ``pyinstaller packaging/birds.spec``, on each platform.
"""

from __future__ import annotations

import tempfile
import traceback
from pathlib import Path
from typing import Callable, List, Tuple

import numpy as np
import pandas as pd


def _diagram() -> str:
    from matplotlib.figure import Figure

    from .diagrams.registry import get_diagram
    from .diagrams.templates.base import PlotOptions
    from .plot_style import PlotStyle

    df = pd.DataFrame({"SiO2": [49.0, 58.0, 71.0], "Na2O": [2.8, 3.9, 4.1],
                       "K2O": [0.6, 1.8, 4.3]})
    fig = Figure()
    get_diagram("tas_volcanic").plot(fig, df, PlotStyle(), PlotOptions())
    fig.canvas.draw()
    return "TAS drawn"


#: How each exported format begins, to tell a real file from an empty
#: or mislabelled one.
_SIGNATURES = {"pdf": b"%PDF", "png": b"\x89PNG", "jpg": b"\xff\xd8",
               "svg": b"<?xml", "eps": b"%!PS"}


def _plot_export() -> str:
    """Every format Export plot offers.  matplotlib imports the writer
    for each only when a file is saved, and the first packaged app had
    none but PNG's and JPEG's."""
    from matplotlib.figure import Figure

    from .diagrams.registry import get_diagram
    from .diagrams.templates.base import PlotOptions
    from .dialogs.export_plot_dialog import FORMATS
    from .plot_style import PlotStyle

    df = pd.DataFrame({"SiO2": [49.0, 58.0, 71.0], "Na2O": [2.8, 3.9, 4.1],
                       "K2O": [0.6, 1.8, 4.3]})
    fig = Figure()
    get_diagram("tas_volcanic").plot(fig, df, PlotStyle(), PlotOptions())
    written = []
    with tempfile.TemporaryDirectory() as tmp:
        for _label, fmt in FORMATS:
            path = Path(tmp) / f"check.{fmt}"
            fig.savefig(path, dpi=72, bbox_inches="tight")
            if not path.read_bytes().startswith(_SIGNATURES[fmt]):
                raise ValueError(f"{fmt}: not a {fmt.upper()} file")
            written.append(fmt)
    return " ".join(written)


def _kriging() -> str:
    from .geostats import analyse

    rng = np.random.default_rng(0)
    lon = -99 + rng.uniform(0, 0.3, 40)
    lat = 19 + rng.uniform(0, 0.3, 40)
    result = analyse(lon, lat, np.exp(1 + 5 * (lon + 99)))
    return f"skill {result.cross_validation.skill:.2f}"


def _utm() -> str:
    from . import coords

    df = pd.DataFrame({"E": [500000.0], "N": [2100000.0]})
    lat, lon = coords.from_utm(df, "E", "N", fixed_zone=14,
                               fixed_hemisphere="N")
    if not (18.9 < lat.iloc[0] < 19.1 and -99.1 < lon.iloc[0] < -98.9):
        raise ValueError(f"UTM 14N 500000/2100000 gave {lat.iloc[0]}, "
                         f"{lon.iloc[0]}")
    return "pyproj" if coords._HAS_PYPROJ else "built-in fallback"


def _mgrs() -> str:
    from . import coords

    if not coords._HAS_MGRS:
        return "mgrs not installed (MGRS option off)"
    df = pd.DataFrame({"G": ["14QMG0000000000"]})
    lat, _lon = coords.from_mgrs(df, "G")
    if not np.isfinite(lat.iloc[0]):
        raise ValueError("MGRS gave no position")
    return "parsed"


def _cipw() -> str:
    from .cipw import compute_cipw

    rock = pd.DataFrame({"SiO2": [49.9], "TiO2": [2.73], "Al2O3": [13.5],
                         "Fe2O3": [1.6], "FeO": [9.5], "MnO": [0.17],
                         "MgO": [7.23], "CaO": [11.4], "Na2O": [2.22],
                         "K2O": [0.52], "P2O5": [0.27]})
    total = float(compute_cipw(rock)["norm_Total"].iloc[0])
    if not 95 < total < 105:
        raise ValueError(f"norm total {total:.2f}")
    return f"norm total {total:.1f}"


def _session_and_excel() -> str:
    from .session import SessionState, load_session, save_session

    df = pd.DataFrame({"Sample_Name": ["A"], "SiO2": [50.0]})
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "check.birds"
        save_session(path, SessionState(data={"main": df}))
        back = load_session(path).data["main"]
        if float(back["SiO2"].iloc[0]) != 50.0:
            raise ValueError("session did not round-trip")
        xlsx = Path(tmp) / "check.xlsx"
        df.to_excel(xlsx, index=False)
        pd.read_excel(xlsx)
    return "saved and read back"


def _window() -> str:
    from PySide6.QtWidgets import QApplication

    from .main_window import BirdsMainWindow

    QApplication.instance() or QApplication([])
    window = BirdsMainWindow()
    window.close()
    return "built"


CHECKS: List[Tuple[str, Callable[[], str]]] = [
    ("diagram", _diagram),
    ("plot export", _plot_export),
    ("kriging", _kriging),
    ("utm", _utm),
    ("mgrs", _mgrs),
    ("cipw", _cipw),
    ("session + excel", _session_and_excel),
    ("main window", _window),
]


def run(echo: Callable[[str], None] = print) -> int:
    """Run every check; 0 if all passed, 1 otherwise."""
    failed = 0
    for name, check in CHECKS:
        try:
            echo(f"ok    {name}: {check()}")
        except Exception as exc:                          # noqa: BLE001
            failed += 1
            echo(f"FAIL  {name}: {exc!r}")
            echo(traceback.format_exc())
    echo(f"{len(CHECKS) - failed} of {len(CHECKS)} checks passed")
    return 1 if failed else 0
