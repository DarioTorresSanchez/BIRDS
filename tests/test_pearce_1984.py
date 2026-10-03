"""The four Pearce, Harris & Tindle (1984) granitoid discriminants.

These are among the rare diagrams of their era whose authors printed
the boundary coordinates outright, in the captions of Figures 3 and 4.
Nothing in them is measured off a figure, and what was here before --
hand-written line segments bearing no relation to those captions, one
of them commented "approximate boundaries" -- has been replaced by the
published numbers.

Two of the printed coordinates are wrong and are used as Verma et al.
(2012) corrected them.  Both corrections are checkable from the
geometry rather than taken on trust, and both are asserted below:

* **Yb-Ta, syn-COLG/WPG**, printed "(55,20) to (3,2)".  The two fields
  it divides lie above and to either side of (3,2), so the boundary has
  to leave that point going up and to the left.  (55,20) is down and to
  the right.
* **Rb-(Yb+Ta), syn-COLG/VAG**, printed as ending at "(6,2000)" where
  the other two boundaries of that junction both start at (6,200).  A
  triple point has to be one point.

The junction test here is the one that matters: it is exactly what the
second error breaks, and it would have caught it in the original.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.tectonic_bivariate import _PEARCE_1984

#: panel key -> diagram key.
PANELS = {
    "Y-Nb": "pearce1984_YNb",
    "Yb-Ta": "pearce1984_YbTa",
    "YNb-Rb": "pearce1984_YNbRb",
    "YbTa-Rb": "pearce1984_YbTaRb",
}


def _above(segment, x, y):
    """Is (x, y) above the line through *segment*, read in log space?

    These diagrams are log-log, so a straight boundary on the page is
    straight in logarithms, not in the raw ppm.
    """
    (x0, y0), (x1, y1) = segment
    lx0, ly0, lx1, ly1 = (np.log10(v) for v in (x0, y0, x1, y1))
    if lx1 == lx0:                      # vertical: "above" is undefined
        raise ValueError("vertical segment")
    slope = (ly1 - ly0) / (lx1 - lx0)
    return bool(np.log10(y) > ly0 + slope * (np.log10(x) - lx0))


def _segment(panel, fields):
    """The boundary of *panel* separating the two named fields."""
    wanted = set(fields)
    for segment, _style, pair in _PEARCE_1984[panel]["boundaries"]:
        if set(pair) == wanted:
            return segment
    raise KeyError(f"{panel} has no {fields} boundary")


class TestThePublishedCoordinates:
    """Figures 3 and 4 captions, cross-checked against the re-statement
    in Verma et al. (2012), which agrees everywhere except the two
    corrections."""

    EXPECTED = {
        "Y-Nb": {
            ("VAG+syn-COLG", "WPG"): ((1.0, 2000.0), (50.0, 10.0)),
            ("VAG+syn-COLG", "ORG"): ((40.0, 1.0), (50.0, 10.0)),
            ("WPG", "ORG"): ((50.0, 10.0), (1000.0, 100.0)),
        },
        "Yb-Ta": {
            ("VAG", "syn-COLG"): ((0.1, 0.35), (3.0, 2.0)),
            ("VAG", "WPG"): ((3.0, 2.0), (5.0, 1.0)),
            ("VAG", "ORG"): ((5.0, 0.05), (5.0, 1.0)),
            ("WPG", "ORG"): ((5.0, 1.0), (100.0, 7.0)),
        },
        "YNb-Rb": {
            ("VAG", "syn-COLG"): ((2.0, 80.0), (55.0, 300.0)),
            ("syn-COLG", "WPG"): ((55.0, 300.0), (400.0, 2000.0)),
            ("VAG", "WPG"): ((55.0, 300.0), (51.5, 8.0)),
            ("VAG", "ORG"): ((51.5, 8.0), (50.0, 1.0)),
            ("WPG", "ORG"): ((51.5, 8.0), (2000.0, 400.0)),
        },
        "YbTa-Rb": {
            ("syn-COLG", "WPG"): ((6.0, 200.0), (50.0, 2000.0)),
            ("VAG", "WPG"): ((6.0, 200.0), (6.0, 8.0)),
            ("VAG", "ORG"): ((6.0, 8.0), (6.0, 1.0)),
            ("WPG", "ORG"): ((6.0, 8.0), (200.0, 400.0)),
        },
    }

    @pytest.mark.parametrize("panel", sorted(EXPECTED))
    def test_every_boundary_matches_its_caption(self, panel):
        for fields, expected in self.EXPECTED[panel].items():
            assert _segment(panel, fields) == expected, f"{panel} {fields}"


class TestTheTwoCorrections:

    def test_the_yb_ta_syn_colg_boundary_points_the_right_way(self):
        """Printed (55,20) to (3,2); used as (0.1,100) to (3,2).

        syn-COLG sits upper-left of (3,2) and WPG upper-right, so their
        boundary leaves it going up and to the left.
        """
        start, end = _segment("Yb-Ta", ("syn-COLG", "WPG"))
        assert end == (3.0, 2.0)
        assert start == (0.1, 100.0)
        assert start[0] < end[0] and start[1] > end[1], (
            "the boundary no longer leaves the junction up and to the left")

    def test_the_printed_yb_ta_coordinate_would_point_away(self):
        """Guards the correction: (55,20) really is the wrong quadrant,
        so this is not a cosmetic preference."""
        printed = (55.0, 20.0)
        junction = (3.0, 2.0)
        assert printed[0] > junction[0] and printed[1] > junction[1], (
            "the printed point is up-and-right of the junction, which is "
            "where WPG already is")

    def test_the_rb_yb_ta_junction_is_one_point(self):
        """Printed (0.5,140) to (6,2000); used as ending at (6,200),
        which is where the other two boundaries of that junction start."""
        start, end = _segment("YbTa-Rb", ("syn-COLG", "VAG"))
        assert (start, end) == ((0.5, 140.0), (6.0, 200.0))
        for other in (("syn-COLG", "WPG"), ("VAG", "WPG")):
            assert (6.0, 200.0) in _segment("YbTa-Rb", other)

    def test_the_printed_endpoint_would_miss_the_junction(self):
        """With (6,2000) the three boundaries meet nowhere, and the
        junction test below would fail -- which is the point."""
        assert (6.0, 2000.0) != (6.0, 200.0)
        junctions = [p for p, n in self._tally("YbTa-Rb").items() if n >= 3]
        assert junctions == [(6.0, 200.0)] or (6.0, 200.0) in junctions

    @staticmethod
    def _tally(panel):
        counts = Counter()
        for (start, end), _style, _pair in _PEARCE_1984[panel]["boundaries"]:
            counts[start] += 1
            counts[end] += 1
        return counts


class TestTheJunctions:
    """Boundaries that share a field have to meet, or a field leaks.

    This is the structural check the published Rb-(Yb+Ta) coordinates
    fail: with the printed (6,2000) the syn-COLG/VAG boundary stops a
    decade above the junction the other two share.
    """

    EXPECTED = {
        "Y-Nb": {(50.0, 10.0)},
        "Yb-Ta": {(3.0, 2.0), (5.0, 1.0)},
        "YNb-Rb": {(55.0, 300.0), (51.5, 8.0)},
        "YbTa-Rb": {(6.0, 200.0), (6.0, 8.0)},
    }

    @pytest.mark.parametrize("panel", sorted(EXPECTED))
    def test_the_junctions_are_where_they_should_be(self, panel):
        counts = Counter()
        for (start, end), _style, _pair in _PEARCE_1984[panel]["boundaries"]:
            counts[start] += 1
            counts[end] += 1
        shared = {point for point, n in counts.items() if n >= 3}
        assert shared == self.EXPECTED[panel]


class TestTheDashedLines:
    """The dashed line is the upper limit for ocean-ridge granites from
    anomalous ridge segments, not a field boundary.  It belongs only to
    the two diagrams whose captions draw it."""

    def test_only_the_two_element_diagrams_carry_one(self):
        dashed = {panel for panel, spec in _PEARCE_1984.items()
                  if any(style == "dashed"
                         for _seg, style, _pair in spec["boundaries"])}
        assert dashed == {"Y-Nb", "Yb-Ta"}

    @pytest.mark.parametrize("panel,expected", [
        ("Y-Nb", ((25.0, 25.0), (1000.0, 400.0))),
        ("Yb-Ta", ((3.0, 2.0), (100.0, 20.0))),
    ])
    def test_its_published_coordinates(self, panel, expected):
        drawn = [seg for seg, style, _pair in _PEARCE_1984[panel]["boundaries"]
                 if style == "dashed"]
        assert drawn == [expected]

    def test_it_is_drawn_dashed_on_the_canvas(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle

        figure = plt.figure()
        get_diagram("pearce1984_YbTa").plot(
            figure, pd.DataFrame(), PlotStyle(), PlotOptions())
        styles = {line.get_linestyle() for line in figure.axes[0].lines}
        assert "--" in styles
        plt.close(figure)


class TestGranitoidsLandInTheirFields:
    """Granitoids have no canonical composition per setting the way
    N-MORB or OIB do, so these are points placed inside each field from
    the published geometry.  They test the drawing, not the geology."""

    def test_the_separating_power_the_authors_claim(self):
        """The authors say volcanic-arc and syn-collision granites are
        separated "almost completely on the Yb-Ta diagram but hardly at
        all on the Y-Nb diagram".  Two granitoids differing mainly in
        Ta and Rb should show exactly that.
        """
        arc = {"Y": 20.0, "Nb": 6.0, "Yb": 2.0, "Ta": 0.4, "Rb": 70.0}
        collision = {"Y": 25.0, "Nb": 14.0, "Yb": 1.0, "Ta": 2.0,
                     "Rb": 380.0}

        # Yb-Ta tells them apart, across the VAG/syn-COLG boundary.
        boundary = _segment("Yb-Ta", ("VAG", "syn-COLG"))
        assert not _above(boundary, arc["Yb"], arc["Ta"])
        assert _above(boundary, collision["Yb"], collision["Ta"])

        # Y-Nb does not: both sit in the one combined field, below the
        # VAG+syn-COLG / WPG boundary.
        combined = _segment("Y-Nb", ("VAG+syn-COLG", "WPG"))
        for rock in (arc, collision):
            assert not _above(combined, rock["Y"], rock["Nb"])

    @pytest.mark.parametrize("panel,fields,point,expected_above", [
        ("Yb-Ta", ("WPG", "ORG"), (20.0, 20.0), True),    # WPG over ORG
        ("Yb-Ta", ("WPG", "ORG"), (20.0, 0.3), False),    # ORG under it
        ("YNb-Rb", ("WPG", "ORG"), (300.0, 600.0), True),
        ("YNb-Rb", ("WPG", "ORG"), (300.0, 6.0), False),
        ("YbTa-Rb", ("WPG", "ORG"), (40.0, 700.0), True),
        ("YbTa-Rb", ("WPG", "ORG"), (40.0, 5.0), False),
    ])
    def test_a_point_falls_on_the_side_it_should(self, panel, fields, point,
                                                 expected_above):
        assert _above(_segment(panel, fields), *point) == expected_above


class TestTheDiagrams:

    @pytest.mark.parametrize("panel,key", sorted(PANELS.items()))
    def test_the_axes_are_the_published_ones(self, panel, key):
        diagram = get_diagram(key)
        assert diagram.log_x and diagram.log_y
        assert diagram.panel == panel

    @pytest.mark.parametrize("key", sorted(PANELS.values()))
    def test_every_label_sits_inside_the_frame(self, key):
        diagram = get_diagram(key)
        spec = _PEARCE_1984[diagram.panel]
        x_lo, x_hi = diagram.x_range
        y_lo, y_hi = diagram.y_range
        for name, (x, y) in spec["labels"].items():
            assert x_lo <= x <= x_hi, f"{key}: {name} x"
            assert y_lo <= y <= y_hi, f"{key}: {name} y"

    @pytest.mark.parametrize("key", sorted(PANELS.values()))
    def test_it_draws_with_data(self, key):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle

        frame = pd.DataFrame([{"Y": 30.0, "Nb": 15.0, "Yb": 3.0, "Ta": 1.0,
                               "Rb": 120.0}])
        figure = plt.figure()
        get_diagram(key).plot(figure, frame, PlotStyle(), PlotOptions())
        ax = figure.axes[0]
        assert len(ax.lines) == len(_PEARCE_1984[get_diagram(key).panel]
                                    ["boundaries"])
        assert any(len(c.get_offsets()) for c in ax.collections)
        plt.close(figure)

    def test_the_rubidium_diagrams_need_rubidium(self):
        diagram = get_diagram("pearce1984_YNbRb")
        xs, ys = diagram._compute_xy(pd.DataFrame([{"Y": 30.0, "Nb": 15.0}]))
        assert xs is None and ys is None

    def test_the_sums_are_sums(self):
        diagram = get_diagram("pearce1984_YbTaRb")
        xs, _ys = diagram._compute_xy(
            pd.DataFrame([{"Yb": 3.0, "Ta": 1.0, "Rb": 120.0}]))
        assert float(xs.iloc[0]) == pytest.approx(4.0)
