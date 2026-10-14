"""Li, Godang & Saputro (2025) Nb/Yb vs Th/Nb, against the paper.

The ratios the text states are pinned as stated; what was measured on
Figure 1 is pinned with the measurement and the check that ties it to
something independent (the primitive mantle, Th/Yb = 0.65).  The
classification is tested on the case studies of Section 3, whose ratios
the paper prints.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from birds.diagrams.catalog import TECTONIC_PLUTONIC, TECTONIC_VOLCANIC
from birds.diagrams.registry import get_diagram
from birds.diagrams.templates import li2025
from birds.diagrams.templates.base import PlotOptions
from birds.plot_style import PlotStyle

KEY = "li2025_nbyb_thnb"


def test_the_stated_boundaries():
    assert li2025.TH_NB_ARRAY == (0.04, 0.11)
    assert li2025.TH_NB_LITHOSPHERIC == 0.67
    assert (li2025.NB_YB_ALKALINE, li2025.NB_YB_SLAB) == (6.0, 4.0)
    assert li2025.TH_YB_ARC == (0.35, 0.65)
    assert li2025.LA_YB_RIFT == 20.0
    assert li2025.TIO2_AL2O3 == (-1.1610, 0.1935)


def test_the_measured_boundaries_meet_what_ties_them_down():
    # The lower horizontal is the McDonough & Sun (1995) primitive
    # mantle, measured at 1.489.
    assert li2025.NB_YB_PM == pytest.approx(0.658 / 0.441)
    assert li2025.NB_YB_PM == pytest.approx(1.489, rel=0.005)
    # Field {7}'s side meets Th/Yb = 0.65 at the Nb/Yb measured, 2.689.
    assert li2025.TH_YB_ARC[1] / li2025.TH_NB_FIELD7 == pytest.approx(
        2.689, rel=0.01)
    # ... and the 1.49 horizontal ends on Th/Yb = 0.35, measured 0.237
    # to the last dark pixel, half a 4-px stroke (0.6 %) past its end.
    assert li2025.TH_YB_ARC[0] / li2025.NB_YB_PM == pytest.approx(
        0.237, rel=0.015)


def test_the_interaction_line_runs_from_asthenosphere_to_lithosphere():
    pts = np.array(li2025.INTERACTION_LINE)
    assert len(pts) == 11                                  # 0-100 % by 10
    assert np.all(np.diff(pts[:, 0]) > 0) and np.all(np.diff(pts[:, 1]) < 0)
    # 50 % sits where the figure draws it, on Nb/Yb = 6.
    assert pts[5, 1] == pytest.approx(6.0, rel=0.03)


def test_the_reference_stars_are_sun_and_mcdonough():
    ref = li2025.reference_points()
    assert ref["N-MORB"] == pytest.approx((0.12 / 2.33, 2.33 / 3.05))
    assert ref["E-MORB"] == pytest.approx((0.6 / 8.3, 8.3 / 2.37))
    assert ref["OIB"] == pytest.approx((4.0 / 48.0, 48.0 / 2.16))
    assert ref["PM"] == pytest.approx((0.0795 / 0.658, 0.658 / 0.441))


@pytest.mark.parametrize("th_nb, nb_yb, extra, setting", [
    (0.052, 0.76, {}, "N-MORB"),                        # Sun & McDonough
    (0.072, 3.5, {}, "E-MORB"),
    (0.083, 22.2, {}, "OIB / mantle plume"),
    # Aitutaki: 0.11 < Th/Nb < 0.67, Nb/Yb > 6, La/Yb > 20 (3.2, 4.2)
    (0.30, 10.0, {}, "intracontinental rift"),
    (0.30, 10.0, {"la_yb": 25}, "intracontinental rift (alkali basalt)"),
    # Guangxi: rift, La/Yb 8.9-14.1 -> enriched tholeiitic (4.4)
    (0.15, 9.0, {"la_yb": 12}, "intracontinental rift (enriched tholeiitic)"),
    # Candlemass: Th/Nb > 0.11, Th/Yb < 0.35, Nb/Yb < 0.3 (3.3)
    (0.6, 0.25, {}, "island arc (tholeiitic)"),
    # Pagan: Th/Yb 0.35-0.65, Nb/Yb < 1 (3.3)
    (0.6, 0.8, {}, "island arc to continental arc (transitional)"),
    # Kebasen: Th/Yb > 0.65, Nb/Yb < 1 (3.3)
    (0.9, 0.9, {}, "continental arc / ACM (calc-alkaline)"),
    # Franz Josef Land: Th/Nb 0.078-0.148, Nb/Yb 2.6-4.6 (3.5)
    (0.13, 3.0, {}, "sub-alkaline enriched tholeiitic"),
    (0.09, 3.0, {}, "E-MORB"),
    # Adang: Th/Nb > 0.67, Nb/Yb > 6, high TiO2 for its Al2O3 (3.6)
    (1.0, 10.0, {"tio2": 2.0, "al2o3": 15.0},
     "continental extensional setting"),
    (1.0, 10.0, {"tio2": 1.0, "al2o3": 18.0}, "alkaline arc"),
    (1.0, 10.0, {}, "continental extensional setting / alkaline arc"),
    # Sumbing-Slamet: past Nb/Yb = 4 (4.4)
    (0.45, 5.0, {}, "continental arc / ACM (calc-alkaline), slab failure "
                    "or alkaline assimilation"),
    (0.02, 5.0, {}, ""),                                # left of the array
])
def test_settings_as_the_paper_names_them(th_nb, nb_yb, extra, setting):
    assert li2025.classify(th_nb, nb_yb, **extra) == setting


def test_classify_frame_reads_la_tio2_and_al2o3():
    df = pd.DataFrame({"Th": [3.0, 10.0], "Nb": [10.0, 10.0],
                       "Yb": [1.0, 1.0], "La": [30.0, 5.0],
                       "TiO2": [np.nan, 2.0], "Al2O3": [np.nan, 15.0]})
    assert list(get_diagram(KEY).classify_frame(df)) == [
        "intracontinental rift (alkali basalt)",
        "continental extensional setting"]


def test_samples_plot_at_th_nb_and_nb_yb():
    df = pd.DataFrame({"Th": [3.0], "Nb": [10.0], "Yb": [2.0]})
    x, y = get_diagram(KEY)._compute_xy(df)
    assert (x.iloc[0], y.iloc[0]) == pytest.approx((0.3, 5.0))
    fig = Figure()
    get_diagram(KEY).plot(fig, df, PlotStyle(), PlotOptions())
    ax = fig.axes[0]
    assert ax.get_xscale() == ax.get_yscale() == "log"
    assert ax.get_xlim() == pytest.approx(li2025.X_RANGE)
    assert ax.get_ylim() == pytest.approx(li2025.Y_RANGE)
    assert ax.get_xlabel() == "Th/Nb" and ax.get_ylabel() == "Nb/Yb"


def test_the_diagram_is_offered_for_every_composition():
    """Mafic to felsic, volcanic and plutonic (Section 2.1)."""
    for catalogue in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC):
        for family in ("Mafic", "Intermediate", "Acid"):
            assert KEY in [k for _l, k in catalogue[family]], family
    assert "mafic to felsic" in get_diagram(KEY).citation
    assert getattr(get_diagram(KEY), "composition_filter", None) is None
