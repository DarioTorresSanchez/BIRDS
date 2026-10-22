"""Martin (1986) Figure 1: (La/Yb)_N vs Yb_N, Archean TTG and after.

Both fields were measured on the scan of Figure 1, each edge fitted to
the ink along it.  Two checks lie outside that measurement: the
caption's own bounds for each group, and Figure 4, which draws the same
two fields again, separately.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates import martin1986 as M


def test_the_fields_keep_to_the_captions_bounds():
    """"0.3 < YbN < 8.5" and "from 5 to more than 150" for the TTG;
    "4.5 < YbN < 20" for the post-Archean rocks."""
    x, y = np.array(M.TTG_FIELD).T
    assert x.min() == pytest.approx(0.3, abs=0.05)
    assert x.max() == pytest.approx(8.5, abs=0.05)
    assert y.max() == 150.0
    assert y.min() == pytest.approx(5, abs=1)
    x, y = np.array(M.POST_ARCHEAN_FIELD).T
    assert x.min() == pytest.approx(4.5, abs=0.05)
    assert x.max() == 20.0


#: The same fields as Figure 4 draws them, measured the same way.
FIGURE_4A_POST_ARCHEAN = ((4.466, 30.74), (20.010, 9.78), (20.008, 4.27),
                          (4.488, 4.23))
FIGURE_4B_TTG = ((0.173, 148.02), (1.421, 148.02), (2.399, 69.10),
                 (4.888, 39.97), (8.360, 24.51), (8.360, 3.79),
                 (3.060, 3.89), (1.104, 14.67), (0.293, 34.17))


def test_figure_4a_draws_the_same_post_archean_field():
    gap = np.abs(np.array(M.POST_ARCHEAN_FIELD) - FIGURE_4A_POST_ARCHEAN)
    assert gap[:, 0].max() < 0.05 and gap[:, 1].max() < 0.6


def test_figure_4b_draws_the_ttg_field_a_little_narrower():
    """Its top at 148 for 150 and its steep edge up to a third of a unit
    to the left: two drawings, not two definitions."""
    gap = np.abs(np.array(M.TTG_FIELD) - FIGURE_4B_TTG)
    assert gap[:, 0].max() < 0.35 and gap[:, 1].max() < 2.1


@pytest.mark.parametrize("yb_n, la_yb_n, field", [
    (2.0, 100.0, M.TTG),
    (15.0, 8.0, M.POST_ARCHEAN),
    (6.0, 10.0, M.OVERLAP),
    (15.0, 100.0, ""),
    (np.nan, 10.0, ""),
])
def test_classify(yb_n, la_yb_n, field):
    assert M.classify([yb_n], [la_yb_n])[0] == field


def test_normalised_to_boynton():
    df = pd.DataFrame({"La": [31.0], "Yb": [2.09]})
    yb_n, la_yb_n = M.normalised(df)
    assert yb_n.iloc[0] == pytest.approx(10.0)
    assert la_yb_n.iloc[0] == pytest.approx(100.0 / 10.0)
    assert M.CHONDRITE == "Boynton (1984)"
    assert "Boynton (1984)" in get_diagram("martin_1986_LaYbN").citation


def test_classify_frame_and_plot(full_df, plot_style):
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    diagram = get_diagram("martin_1986_LaYbN")
    got = diagram.classify_frame(full_df)
    assert set(got) <= {M.TTG, M.POST_ARCHEAN, M.OVERLAP, ""}
    fig = Figure()
    diagram.plot(fig, full_df, plot_style, PlotOptions())
    ax = fig.axes[0]
    assert ax.get_xlim() == M.X_RANGE and ax.get_ylim() == M.Y_RANGE
    assert {"Archean TTG"} <= {t.get_text() for t in ax.texts}


def test_it_is_offered_for_intermediate_and_acid_rocks():
    from birds.diagrams.catalog import TECTONIC_PLUTONIC, TECTONIC_VOLCANIC
    for menu in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC):
        for composition in ("Intermediate", "Acid"):
            assert "martin_1986_LaYbN" in [k for _l, k in menu[composition]]
