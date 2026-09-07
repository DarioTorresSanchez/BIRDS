"""Shared fixtures.

Qt needs a display; the offscreen platform plugin gives us one without a
window server, which is what lets the GUI tests run in CI.  It has to be
set before PySide6 is imported anywhere, hence the module-level
assignment rather than a fixture.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

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
]


@pytest.fixture(scope="session")
def qapp():
    """One QApplication for the whole session — Qt allows only one."""
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    return app


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
