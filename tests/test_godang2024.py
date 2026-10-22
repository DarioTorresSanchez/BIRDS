"""Godang, Saputro & Li (2024) Nb/Zr vs Th/Nb, against Li et al. (2025)
Figure 5 and against the paper's own Figure 7.

The ratios printed on the figure are pinned as printed; the diagonal
and the PM dot, which were measured, are tied to the McDonough & Sun
(1995) primitive mantle and the frame corner they run between.  The
classification is tested on the case studies Li et al. plot on it.

The template was measured on Li et al.'s reproduction; the original,
Figure 7 of Godang et al. (2024), was measured afterwards and on its
own, and agrees.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from birds.diagrams.catalog import TECTONIC_PLUTONIC, TECTONIC_VOLCANIC
from birds.diagrams.registry import get_diagram
from birds.diagrams.templates import godang2024 as godang
from birds.diagrams.templates.base import PlotOptions
from birds.plot_style import PlotStyle

KEY = "godang2024_nbzr_thnb"


def test_the_printed_boundaries():
    assert godang.TH_NB_ARRAY == (0.04, 0.11)
    assert godang.TH_NB_LITHOSPHERIC == 0.67
    assert (godang.NB_ZR_DEPLETED, godang.NB_ZR_PLUME) == (0.04, 0.15)
    assert round(godang.NB_ZR_PM, 4) == 0.0627          # "0.0627 (PM)"
    assert godang.LA_YB_RIFT == 20.0
    assert (godang.X_RANGE, godang.Y_RANGE) == ((0.015, 5.0), (0.01, 1.0))


def test_the_pm_dot_is_mcdonough_and_sun():
    # measured at (0.1206, 0.0630)
    assert godang.PM_POINT == pytest.approx((0.0795 / 0.658, 0.658 / 10.5))
    assert godang.PM_POINT == pytest.approx((0.1206, 0.0630), rel=0.006)


def test_the_diagonal_runs_from_pm_to_the_corner():
    (x0, y0), (x1, y1) = godang.DIAGONAL
    assert (x0, y0) == godang.PM_POINT and (x1, y1) == (5.0, 0.01)
    slope = np.log10(y1 / y0) / np.log10(x1 / x0)
    assert slope == pytest.approx(-0.4936, abs=0.001)    # fitted on Fig. 5
    assert godang.diagonal_nb_zr(x0) == pytest.approx(y0)
    assert godang.diagonal_nb_zr(5.0) == pytest.approx(0.01)
    # It crosses Nb/Zr 0.04 where Figure 5 does: measured Th/Nb 0.301.
    assert godang.diagonal_nb_zr(0.301) == pytest.approx(0.04, rel=0.01)


#: Godang et al. (2024) Figure 7 (1895 x 1384 raster), calibrated on its
#: lines Th/Nb 0.04, 0.11 and 0.67 (650.3 px per decade) and its frame,
#: which then lands on Th/Nb 0.0150 and 5.01.
FIGURE_7 = {
    "Nb/Zr 0.0627 line at": 0.0625,
    "Nb/Zr 0.04 line at": 0.0397,
    "PM dot": (0.1210, 0.0641),       # centre of its purple, label included
    "diagonal slope": -0.4940,
    "diagonal at Th/Nb 5": 0.0100,
}


def test_the_original_figure_7_agrees():
    """Each line spans what the template draws: Nb/Zr 0.15 only across
    the array, 0.0627 and 0.04 from Th/Nb 0.04 to the right edge, 0.67
    from Nb/Zr 0.0627 up -- each inked over that span and not past it."""
    assert FIGURE_7["Nb/Zr 0.0627 line at"] == pytest.approx(
        godang.NB_ZR_PM, rel=0.005)
    assert FIGURE_7["Nb/Zr 0.04 line at"] == pytest.approx(
        godang.NB_ZR_DEPLETED, rel=0.01)
    assert FIGURE_7["PM dot"] == pytest.approx(godang.PM_POINT, rel=0.03)
    (x0, y0), (x1, y1) = godang.DIAGONAL
    slope = np.log10(y1 / y0) / np.log10(x1 / x0)
    assert FIGURE_7["diagonal slope"] == pytest.approx(slope, abs=0.002)
    assert FIGURE_7["diagonal at Th/Nb 5"] == pytest.approx(y1, rel=0.01)


@pytest.mark.parametrize("th_nb, nb_zr, extra, setting", [
    (0.02, 0.5, {}, "source modification or contamination"),
    # N-MORB, Indian Ocean; OIB Mauna Kea (4.1)
    (0.055, 0.02, {}, "N-MORB"),
    (0.06, 0.09, {}, "OIB and E-MORB"),
    (0.06, 0.05, {}, godang.TRANSITION),
    # Aitutaki: rift, Nb/Zr > 0.15, La/Yb > 20 (4.2)
    (0.2, 0.4, {}, "intracontinental rift"),
    (0.2, 0.4, {"la_yb": 25}, "intracontinental rift (alkali basalt)"),
    (0.2, 0.4, {"la_yb": 12}, "intracontinental rift (enriched tholeiitic)"),
    (0.07, 0.3, {}, "mantle plume basalts"),
    (1.5, 0.3, {}, "continental extensional zone / initial rift basalts "
                   "or alkaline arc"),
    # Candlemass: Th/Nb > 0.11, Nb/Zr 0.0132 and 0.0096 -> island arc (3.3)
    (0.4, 0.0132, {}, "island arc (IA), depleted mantle source"),
    (0.4, 0.0096, {}, "island arc (IA), depleted mantle source"),
    # Fossa delle Felci: calc-alkaline continental arc (4.3.3)
    (0.9, 0.03, {}, "continental arc (ACM), depleted mantle source"),
    (0.9, 0.057, {}, "continental arc (ACM), slightly enriched mantle "
                     "source"),
    # Left of the PM dot, below 0.0627: under the diagonal's extension
    (0.115, 0.05, {}, "island arc (IA), slightly enriched mantle source"),
])
def test_settings_as_figure_5_names_them(th_nb, nb_zr, extra, setting):
    # Candlemass's 0.0096 is under the frame's 0.01: it is still named,
    # and the plot flags it at the edge like any sample off the frame.
    assert godang.classify(th_nb, nb_zr, **extra) == setting


def test_the_mantle_source_brackets():
    assert godang.mantle_source(0.1) == "enriched mantle source"
    assert godang.mantle_source(0.05) == "slightly enriched mantle source"
    assert godang.mantle_source(0.02) == "depleted mantle source"
    assert godang.mantle_source(np.nan) == ""


def test_classify_frame_reads_la_and_yb():
    df = pd.DataFrame({"Th": [2.0, 5.0], "Nb": [10.0, 10.0],
                       "Zr": [25.0, 500.0], "La": [30.0, 5.0],
                       "Yb": [1.0, 1.0]})
    assert list(get_diagram(KEY).classify_frame(df)) == [
        "intracontinental rift (alkali basalt)",
        "island arc (IA), depleted mantle source"]


def test_samples_plot_at_th_nb_and_nb_zr():
    df = pd.DataFrame({"Th": [3.0], "Nb": [10.0], "Zr": [200.0]})
    x, y = get_diagram(KEY)._compute_xy(df)
    assert (x.iloc[0], y.iloc[0]) == pytest.approx((0.3, 0.05))
    fig = Figure()
    get_diagram(KEY).plot(fig, df, PlotStyle(), PlotOptions())
    ax = fig.axes[0]
    assert ax.get_xscale() == ax.get_yscale() == "log"
    assert ax.get_xlim() == pytest.approx(godang.X_RANGE)
    assert ax.get_ylim() == pytest.approx(godang.Y_RANGE)
    assert ax.get_xlabel() == "Th/Nb" and ax.get_ylabel() == "Nb/Zr"


def test_the_diagram_is_offered_for_every_composition():
    """Li et al. (2025, Section 4) use it on basaltic and rhyolitic
    rocks alike."""
    for catalogue in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC):
        for family in ("Mafic", "Intermediate", "Acid"):
            assert KEY in [k for _l, k in catalogue[family]], family
    assert "mafic to felsic" in get_diagram(KEY).citation
    assert getattr(get_diagram(KEY), "composition_filter", None) is None
