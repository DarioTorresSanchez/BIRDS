"""The two Defant & Drummond (1990) adakite discriminants.

Nature 347, 662-665 has exactly three figures: Y or Yb against the age
of the subducting lithosphere, Sr/Y against Y, and a chondrite
spider.  Two consequences, and both were wrong here.

**Figure 2 draws no adakite field.**  Its adakites are crosses and
nothing encloses them; what it draws is a boninite field, an
island-arc andesite-dacite-rhyolite field, a MORB bar, four model
melting curves and an AFC trend arrow.  The dashed "adakite boundary"
this diagram used to carry, and the "Sr/Y > 40" its citation claimed,
are in neither the figure nor the text.  The frame was wrong too --
(0, 50) by (0, 200) against a published (0, 25) by (0, 500) -- so a
sample sat at less than half its real Y and more than twice its real
Sr/Y relative to anything drawn around it.

**There is no Yb against La/Yb figure in the paper at all.**  Rollinson
& Pease (2021) list one in their table of discrimination diagrams,
under this reference and marked "unevaluated", which is where the
attribution came from.  It cannot be reproduced from a source that
does not contain it, so that diagram now draws only the threshold the
paper does state and lets its axes follow the data.

What the paper gives for adakites is a list of numbers on page 663:
"low Y and HREE relative to island-arc ADRs (for example, Y and Yb
<= 18 and 1.9 p.p.m., respectively), high Sr relative to island-arc
ADR (rarely <400 p.p.m.)".  Those are exact and quotable, and they are
what both diagrams draw.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PolyCollection
from matplotlib.figure import Figure

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import PlotOptions
from birds.diagrams.templates.tectonic_bivariate import (
    DD_ADAKITE_Y_MAX,
    DD_ADAKITE_YB_MAX,
    DD_FIG2_X_RANGE,
    DD_FIG2_Y_RANGE,
    DD_ISLAND_ARC_ADR,
    DD_MORB_FIELD,
)
from birds.plot_style import PlotStyle


# ---------------------------------------------------------------------------
# The thresholds the paper states in words
# ---------------------------------------------------------------------------

def test_the_two_published_thresholds():
    """"Y and Yb <= 18 and 1.9 p.p.m., respectively" -- page 663."""
    assert DD_ADAKITE_Y_MAX == 18.0
    assert DD_ADAKITE_YB_MAX == 1.9


@pytest.mark.parametrize("key, column, other, threshold", [
    ("defant_drummond_YSrY", "Y", "Sr", DD_ADAKITE_Y_MAX),
    ("defant_drummond_YbLaYb", "Yb", "La", DD_ADAKITE_YB_MAX),
])
def test_the_threshold_is_on_the_x_axis(key, column, other, threshold):
    """Both thresholds are on the element, which is x on both diagrams."""
    df = pd.DataFrame({column: [threshold], other: [100.0]})
    x, _y = get_diagram(key)._compute_xy(df)
    assert float(x.iloc[0]) == pytest.approx(threshold)


# ---------------------------------------------------------------------------
# Figure 2's frame
# ---------------------------------------------------------------------------

def test_figure_2_frame():
    d = get_diagram("defant_drummond_YSrY")
    assert tuple(d.x_range) == DD_FIG2_X_RANGE == (0, 25)
    assert tuple(d.y_range) == DD_FIG2_Y_RANGE == (0, 500)
    assert not d.log_x and not d.log_y


def test_the_adakite_threshold_falls_inside_figure_2s_frame():
    """Y = 18 has to be a line one can see, not one off the edge.

    It is also the check that would have caught the old frame: on
    (0, 50) the line would sit at the middle instead of at 72 % of the
    width, and on a y axis stopping at 200 most of Figure 2's own
    adakites would have been off the top.
    """
    lo, hi = DD_FIG2_X_RANGE
    assert lo < DD_ADAKITE_Y_MAX < hi
    assert DD_ADAKITE_Y_MAX / hi == pytest.approx(0.72)


# ---------------------------------------------------------------------------
# The two fields measured off Figure 2
# ---------------------------------------------------------------------------

def test_the_morb_bar_is_where_it_was_measured():
    """Y 20 to the frame edge, Sr/Y 0 to 15.

    This one is exact rather than approximate: the bar is filled, so
    its edges were read as the longest unbroken runs of ink and came
    out at Y 19.97-25.01 and Sr/Y -1.8 to 15.2, the overshoots being
    the axis line's own thickness.
    """
    lo, hi, bot, top = DD_MORB_FIELD
    assert (lo, hi, bot, top) == (20.0, 25.0, 0.0, 15.0)
    assert hi == DD_FIG2_X_RANGE[1]          # it runs off the frame edge
    assert bot == DD_FIG2_Y_RANGE[0]


def test_the_island_arc_field_stays_inside_the_frame():
    for x, y in DD_ISLAND_ARC_ADR:
        assert DD_FIG2_X_RANGE[0] <= x <= DD_FIG2_X_RANGE[1]
        assert DD_FIG2_Y_RANGE[0] <= y <= DD_FIG2_Y_RANGE[1]


def test_the_measured_field_edge_lands_on_the_stated_threshold():
    """The strongest check available here, and it was not designed in.

    The island-arc field's left edge measured at Y = 17.9.  The paper's
    stated adakite limit, written in the text and nowhere drawn on the
    figure, is Y <= 18.  The two come from independent places -- a
    dashed outline on a half-tone scan and a sentence on page 663 --
    and agree to 0.1, which is a third of the measurement's own
    uncertainty and 8 pixels on the calibrated figure.

    So the drawn field begins where the quoted threshold says it
    should.  That is what makes this measurement trustworthy: nothing
    in reading the dashes used the number 18.
    """
    xs = [x for x, _ in DD_ISLAND_ARC_ADR]
    assert min(xs) == pytest.approx(DD_ADAKITE_Y_MAX, abs=0.3)
    assert min(xs) == 17.9

    ys = [y for _, y in DD_ISLAND_ARC_ADR]
    assert max(ys) < 100.0                   # adakites on Fig. 2 pass 400
    assert max(ys) == pytest.approx(59.6)    # the dome, at Y = 20.0


def test_the_island_arc_field_is_a_simple_closed_outline():
    """One dome: Sr/Y rises then falls, with no second hump.

    A measured outline read dash by dash can come back out of order;
    this says it did not.
    """
    ys = [y for _, y in DD_ISLAND_ARC_ADR]
    peak = ys.index(max(ys))
    rising = ys[:peak + 1]
    falling = ys[peak:]
    assert rising == sorted(rising)
    assert falling == sorted(falling, reverse=True)

    xs = [x for x, _ in DD_ISLAND_ARC_ADR]
    assert xs[:-1] == sorted(xs[:-1])        # left to right, then closes


def test_a_measured_field_is_not_claimed_to_be_exact():
    """The vertices carry one decimal, which is the resolution claimed.

    0.1 in Y is 8 px on the calibrated scan and 0.1 in Sr/Y is a third
    of a pixel, so nothing here pretends to more than it measured.
    """
    for x, y in DD_ISLAND_ARC_ADR:
        assert round(x, 1) == x
        assert round(y, 1) == y


# ---------------------------------------------------------------------------
# What is deliberately absent
# ---------------------------------------------------------------------------

def test_the_adakite_side_of_figure_2_is_left_empty():
    """The paper draws nothing there, so neither may we.

    Every boundary on Figure 2 -- the island-arc field, the MORB bar --
    is to the right of the adakite threshold.  The region a user's
    adakites land in carries no drawn line at all, which is precisely
    the thing the invented dashed curve used to put there.

    Measured against 17.5 rather than 18 because the field's own left
    edge measured 17.9; see the threshold test above.
    """
    style = PlotStyle()
    df = pd.DataFrame({"Sr": [900.0], "Y": [9.0], "La": [18.0],
                       "Yb": [0.9]})
    fig = Figure()
    get_diagram("defant_drummond_YSrY").plot(fig, df, style, PlotOptions())
    ax = fig.axes[0]

    background = [ln for ln in ax.lines
                  if ln.get_label().startswith("_")]
    assert background, "no background was drawn at all"
    for line in background:
        xs = np.asarray(line.get_xdata(), float)
        xs = xs[np.isfinite(xs)]
        if xs.size:
            assert xs.min() >= 17.5, line.get_label()

    # The MORB bar is a fill_between, so it arrives as a PolyCollection.
    # The sample scatter is a PathCollection whose paths are the marker
    # outlines in their own unit coordinates, which is not a field and
    # is what an untyped sweep over ax.collections picks up instead.
    for coll in ax.collections:
        if not isinstance(coll, PolyCollection):
            continue
        for path in coll.get_paths():
            xs = np.asarray(path.vertices, float)[:, 0]
            xs = xs[np.isfinite(xs)]
            if xs.size:
                assert xs.min() >= 17.5, "a filled field reaches the "\
                                         "adakite side of the frame"

    fig.clf()


def test_both_diagrams_name_the_threshold_on_the_plot():
    """A user has to be able to see which line that is."""
    style = PlotStyle()
    df = pd.DataFrame({"Sr": [900.0], "Y": [9.0], "La": [18.0],
                       "Yb": [0.9]})
    for key in ("defant_drummond_YSrY", "defant_drummond_YbLaYb"):
        fig = Figure()
        get_diagram(key).plot(fig, df, style, PlotOptions())
        labels = " ".join(t.get_text() for t in fig.axes[0].texts).lower()
        assert "adakite" in labels
        fig.clf()


def test_the_yb_diagram_has_no_frame_of_its_own():
    """There is no published figure to take one from.

    Its limits were (0, 6) by (0, 80), which clipped anything beyond
    and came from nowhere.  The axes now follow the data.
    """
    d = get_diagram("defant_drummond_YbLaYb")
    assert d.x_range is None
    assert d.y_range is None


def test_both_citations_say_what_the_source_actually_contains():
    """The old ones asserted thresholds the paper does not state.

    "Sr/Y > 40" was in the first and "La/Yb > 20" in the second;
    neither appears in Defant & Drummond (1990).  The second now says
    outright that the paper does not publish that diagram, because a
    user who goes looking for it will not find it.
    """
    sry = get_diagram("defant_drummond_YSrY").citation
    laybb = get_diagram("defant_drummond_YbLaYb").citation
    assert "Sr/Y > 40" not in sry and "40" not in sry.split("400")[0][-4:]
    assert "draws no adakite envelope" in sry
    assert "do not publish this diagram" in laybb
    assert "Rollinson" in laybb


# ---------------------------------------------------------------------------
# End to end
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name, sr, y, la, yb, adakite", [
    ("adakite", 900.0, 9.0, 18.0, 0.9, True),
    ("adakite, higher Y", 750.0, 15.0, 20.0, 1.5, True),
    ("island-arc andesite", 400.0, 21.0, 11.0, 2.6, False),
    ("island-arc dacite", 300.0, 23.0, 8.0, 3.4, False),
])
def test_the_two_diagrams_agree_on_a_sample(name, sr, y, la, yb, adakite):
    """Y <= 18 and Yb <= 1.9 are one criterion split over two plots."""
    df = pd.DataFrame({"Sr": [sr], "Y": [y], "La": [la], "Yb": [yb]})
    x1, _ = get_diagram("defant_drummond_YSrY")._compute_xy(df)
    x2, _ = get_diagram("defant_drummond_YbLaYb")._compute_xy(df)
    assert (float(x1.iloc[0]) <= DD_ADAKITE_Y_MAX) == adakite, name
    assert (float(x2.iloc[0]) <= DD_ADAKITE_YB_MAX) == adakite, name


def test_zero_yttrium_does_not_become_an_infinite_ratio():
    df = pd.DataFrame({"Sr": [400.0, 400.0], "Y": [0.0, 20.0],
                       "La": [10.0, 10.0], "Yb": [0.0, 2.0]})
    for key in ("defant_drummond_YSrY", "defant_drummond_YbLaYb"):
        x, ratio = get_diagram(key)._compute_xy(df)
        assert not np.isfinite(float(ratio.iloc[0]))
        assert np.isfinite(float(ratio.iloc[1]))
