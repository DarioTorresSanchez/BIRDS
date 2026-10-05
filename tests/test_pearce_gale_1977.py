"""Pearce & Gale (1977) Ti/Y–Zr/Y, and the four ways it was drawn wrong.

Geol. Soc. London Spec. Publ. **7**, 14-24, Figure 3.  Everything about
how this diagram was drawn was wrong, in the same way Saccani's
Figures 8 and 9 were:

* **The axes were swapped.**  Pearce & Gale put Ti/Y across the bottom
  and Zr/Y up the side; this had Zr/Y on x and Ti/Y on y.
* **Both were logarithmic** where the published figure is linear on
  both.
* **The frame was invented**: (1, 30) by (100, 1000), against a figure
  running Ti/Y 0 to about 1118 and Zr/Y 0 to about 7.9.
* **The fields went with the axes.**  Within-plate is to the *right*,
  at high Ti/Y, and this put it above.

The boundary coordinates were never in doubt and were already quoted
in a comment in the file: Rollinson & Pease (2021) print them in the
caption of their Figure 5.2a -- "Boundary coordinates: (513, 0) and
(313, 7.5)" -- as (Ti/Y, Zr/Y).  They were then drawn as if they were
(Zr/Y, Ti/Y), which put a line from (1, 513) to (30, 313) on the plot,
a thing unrelated to either reading.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.tectonic_bivariate import (
    PEARCE_GALE_BOUNDARY,
    PEARCE_GALE_MEASURED,
    PEARCE_GALE_RATES,
    PEARCE_GALE_X_RANGE,
    PEARCE_GALE_Y_RANGE,
    TIO2_WT_TO_TI_PPM,
)

DIAGRAM = "pearce_gale_1977"


def _xy(ti_ppm=None, zr=None, y=None, tio2=None):
    data = {"Zr": [zr], "Y": [y]}
    if ti_ppm is not None:
        data["Ti"] = [ti_ppm]
    if tio2 is not None:
        data["TiO2"] = [tio2]
    x, yy = get_diagram(DIAGRAM)._compute_xy(pd.DataFrame(data))
    return float(x.iloc[0]), float(yy.iloc[0])


# ---------------------------------------------------------------------------
# The printed boundary
# ---------------------------------------------------------------------------

def test_the_printed_boundary_coordinates():
    """Rollinson & Pease (2021) Fig. 5.2a caption, as (Ti/Y, Zr/Y)."""
    assert PEARCE_GALE_BOUNDARY == ((513.0, 0.0), (313.0, 7.5))


def test_the_measurement_of_the_original_agrees_with_the_printed_pair():
    """Two sources, 1.7 % and 3.1 % apart, and the printed one wins.

    Pearce & Gale's own Figure 3 was measured with its axes calibrated
    on their tick labels; the drawn line fits a straight line to an rms
    of 0.3 in Ti/Y over 144 sampled rows and gives (521.6, 0) and
    (303.3, 7.5).  The calibration itself is worth about 4 units in
    Ti/Y, so the gap is real but small.

    What is used is the printed pair, because it is published and
    citable where the measurement is mine, off a 1977 half-tone.  The
    measurement is kept as the check that the two agree.
    """
    (px0, _), (px1, _) = PEARCE_GALE_BOUNDARY
    (mx0, _), (mx1, _) = PEARCE_GALE_MEASURED
    assert mx0 == pytest.approx(px0, rel=0.02)
    assert mx1 == pytest.approx(px1, rel=0.035)
    # and the slopes agree to better than a tenth
    printed = (PEARCE_GALE_BOUNDARY[1][0] - px0) / 7.5
    measured = (PEARCE_GALE_MEASURED[1][0] - mx0) / 7.5
    assert measured == pytest.approx(printed, rel=0.10)


def test_the_boundary_is_not_extrapolated_past_the_published_segment():
    """Rollinson stops it at Zr/Y = 7.5 and Figure 3's frame ends at 7.9.

    Neither says where it goes above that, so neither does this.
    """
    ys = [p[1] for p in PEARCE_GALE_BOUNDARY]
    assert max(ys) == 7.5
    assert max(ys) < PEARCE_GALE_Y_RANGE[1]      # frame is taller


# ---------------------------------------------------------------------------
# The axes
# ---------------------------------------------------------------------------

def test_ti_over_y_is_on_x_and_zr_over_y_is_on_y():
    """The swap, pinned by arithmetic rather than by a label.

    Ti enters x only and Zr enters y only, so changing one must move
    exactly one axis.
    """
    d = get_diagram(DIAGRAM)
    assert d.x_label == "Ti/Y" and d.y_label == "Zr/Y"

    base = _xy(ti_ppm=8000.0, zr=80.0, y=20.0)
    assert base == pytest.approx((400.0, 4.0))

    more_ti = _xy(ti_ppm=16000.0, zr=80.0, y=20.0)
    assert more_ti[0] == pytest.approx(800.0)    # x moved
    assert more_ti[1] == pytest.approx(base[1])  # y did not

    more_zr = _xy(ti_ppm=8000.0, zr=160.0, y=20.0)
    assert more_zr[0] == pytest.approx(base[0])
    assert more_zr[1] == pytest.approx(8.0)


def test_both_axes_are_linear():
    d = get_diagram(DIAGRAM)
    assert not d.log_x
    assert not d.log_y


def test_the_frame_is_the_one_the_boundary_was_published_on():
    d = get_diagram(DIAGRAM)
    assert tuple(d.x_range) == PEARCE_GALE_X_RANGE == (0, 1200)
    assert tuple(d.y_range) == PEARCE_GALE_Y_RANGE == (0, 18)


def test_the_frame_holds_an_ordinary_ocean_island_basalt():
    """Which is why Rollinson's frame is used and not Figure 3's.

    Sun & McDonough's OIB sits at Zr/Y 9.7, off the top of Pearce &
    Gale's own figure, which reaches only about 7.9.  A fixed frame
    clips, so the one that does not clip the rock the diagram is meant
    to identify is the one to draw on.
    """
    x, y = _xy(ti_ppm=17200.0, zr=280.0, y=29.0)
    assert PEARCE_GALE_X_RANGE[0] <= x <= PEARCE_GALE_X_RANGE[1]
    assert PEARCE_GALE_Y_RANGE[0] <= y <= PEARCE_GALE_Y_RANGE[1]
    assert y > 7.9                               # off Figure 3's own frame


def test_titanium_may_arrive_as_the_oxide():
    from_element = _xy(ti_ppm=1.0 * TIO2_WT_TO_TI_PPM, zr=80.0, y=20.0)
    from_oxide = _xy(tio2=1.0, zr=80.0, y=20.0)
    assert from_element == pytest.approx(from_oxide)


# ---------------------------------------------------------------------------
# Which side is which
# ---------------------------------------------------------------------------

def _within_plate(ti_y, zr_y):
    """Right of the boundary, read as a line in (Ti/Y, Zr/Y)."""
    (x0, y0), (x1, y1) = PEARCE_GALE_BOUNDARY
    at = x0 + (x1 - x0) * (zr_y - y0) / (y1 - y0)
    return ti_y > at


@pytest.mark.parametrize("name, ti, zr, y, within_plate", [
    # Sun & McDonough (1989)
    ("N-MORB", 7600.0, 74.0, 28.0, False),
    ("OIB", 17200.0, 280.0, 29.0, True),
    # plainly either side
    ("low-Ti island arc", 4000.0, 40.0, 25.0, False),
    ("continental rift", 14000.0, 200.0, 25.0, True),
])
def test_the_reference_basalts_land_on_their_own_side(name, ti, zr, y,
                                                      within_plate):
    ti_y, zr_y = _xy(ti_ppm=ti, zr=zr, y=y)
    assert _within_plate(ti_y, zr_y) == within_plate, name


def test_within_plate_is_to_the_right_not_above():
    """The fields moved with the axes, and this is the fix.

    At one Zr/Y, raising Ti/Y has to cross into within-plate; at one
    Ti/Y, raising Zr/Y must not.
    """
    assert not _within_plate(300.0, 2.0)
    assert _within_plate(700.0, 2.0)             # higher Ti/Y crosses it
    assert not _within_plate(300.0, 2.0)
    assert not _within_plate(300.0, 7.0)         # higher Zr/Y does not


def test_e_morb_is_the_case_the_diagram_does_not_handle():
    """Verma's rates hold only with E-MORB excluded, so it is quoted.

    Sun & McDonough's E-MORB lands among the plate-margin basalts at
    Ti/Y 273, barely distinguishable from their N-MORB at 271, which
    is the overlap the reassessment had to set aside.
    """
    n_morb = _xy(ti_ppm=7600.0, zr=74.0, y=28.0)
    e_morb = _xy(ti_ppm=6000.0, zr=73.0, y=22.0)
    assert e_morb[0] == pytest.approx(n_morb[0], rel=0.02)
    assert not _within_plate(*e_morb)
    assert "E-MORB" in get_diagram(DIAGRAM).citation


def test_the_citation_carries_vermas_rates():
    rates = PEARCE_GALE_RATES
    assert rates == {"plate margin": 90, "within-plate": 89}
    citation = get_diagram(DIAGRAM).citation
    for value in rates.values():
        assert str(value) in citation
    assert "Verma" in citation


def test_zero_yttrium_does_not_become_an_infinite_ratio():
    df = pd.DataFrame({"Ti": [8000.0, 8000.0], "Zr": [80.0, 80.0],
                       "Y": [0.0, 20.0]})
    x, y = get_diagram(DIAGRAM)._compute_xy(df)
    assert not np.isfinite(float(x.iloc[0]))
    assert not np.isfinite(float(y.iloc[0]))
    assert np.isfinite(float(x.iloc[1]))
    assert np.isfinite(float(y.iloc[1]))
