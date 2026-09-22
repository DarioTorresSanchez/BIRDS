"""Hastie et al. (2007) Th–Co — boundaries measured from the figure.

These lock the calibration in place.  The anchors were obtained by
extracting the line pixels from the published figure and fitting them;
the control points below are independent readings taken at other Co and
Th values, so a refactor that shifts a boundary fails here rather than
silently misclassifying arc rocks.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.hastie import (
    _B_BAA,
    _BAA_DR,
    _CA_HK,
    _IAT_CA,
)


def th_on(anchors, co: float) -> float:
    """Th of a series boundary at *co* — straight in (Co, log10 Th)."""
    (c0, t0), (c1, t1) = anchors
    f = (co - c0) / (c1 - c0)
    return float(10 ** (np.log10(t0) + f * (np.log10(t1) - np.log10(t0))))


def co_on(anchors, th: float) -> float:
    """Co of a composition divider at *th*."""
    (t0, c0), (t1, c1) = anchors
    f = (np.log10(th) - np.log10(t0)) / (np.log10(t1) - np.log10(t0))
    return float(c0 + f * (c1 - c0))


class TestSeriesBoundaries:
    """Read off the published figure at Co values away from the anchors."""

    # Every expected value below was read off the published figure at
    # that Co, independently of the two anchors the module stores.
    # The tolerance is the figure's own line width, not a fudge factor.
    @pytest.mark.parametrize("co,expected", [
        (60.0, 0.3120), (50.0, 0.3990), (45.0, 0.4535), (40.0, 0.5047),
        (35.0, 0.5737), (30.0, 0.6453), (25.0, 0.7258), (20.0, 0.8250),
        (10.0, 1.0549), (5.0, 1.1864),
    ])
    def test_tholeiite_calc_alkaline(self, co, expected):
        assert th_on(_IAT_CA, co) == pytest.approx(expected, rel=0.02)

    @pytest.mark.parametrize("co,expected", [
        (65.0, 2.4275), (60.0, 2.6725), (55.0, 2.9738), (50.0, 3.3092),
        (45.0, 3.6432), (40.0, 3.9683), (35.0, 4.4633), (30.0, 4.9666),
        (25.0, 5.4098), (20.0, 5.9558), (15.0, 6.6274), (10.0, 7.3748),
        (5.0, 8.0329),
    ])
    def test_calc_alkaline_high_k(self, co, expected):
        assert th_on(_CA_HK, co) == pytest.approx(expected, rel=0.02)

    def test_bands_never_cross(self):
        """A crossing would put the calc-alkaline field on the wrong side."""
        for co in np.linspace(0, 70, 71):
            assert th_on(_IAT_CA, co) < th_on(_CA_HK, co)

    def test_boundaries_rise_towards_low_co(self):
        """Both series lines climb as the silica proxy increases."""
        for anchors in (_IAT_CA, _CA_HK):
            assert th_on(anchors, 70.0) < th_on(anchors, 0.0)

    def test_boundaries_stay_inside_the_axes(self):
        diagram = get_diagram("hastie_2007_thco")
        low, high = diagram.y_range
        for anchors in (_IAT_CA, _CA_HK):
            for co in (0.0, 35.0, 70.0):
                assert low < th_on(anchors, co) < high


class TestCompositionDividers:
    """The figure draws these sloping, not vertical."""

    # Read off the published figure at each Th, independently of the
    # anchors the module stores.
    @pytest.mark.parametrize("th,expected", [
        (0.05, 35.83), (0.2, 33.69), (0.5, 32.16), (2.0, 30.09),
        (20.0, 26.49), (50.0, 25.11),
    ])
    def test_basalt_basaltic_andesite(self, th, expected):
        assert co_on(_B_BAA, th) == pytest.approx(expected, abs=0.3)

    @pytest.mark.parametrize("th,expected", [
        (0.05, 20.27), (0.2, 17.71), (0.5, 16.25), (2.0, 13.76),
        (20.0, 9.68), (50.0, 8.16),
    ])
    def test_andesite_dacite_rhyolite(self, th, expected):
        assert co_on(_BAA_DR, th) == pytest.approx(expected, abs=0.3)

    def test_dividers_are_not_vertical(self):
        """They used to be drawn as axvlines, which the figure is not."""
        for anchors in (_B_BAA, _BAA_DR):
            assert abs(co_on(anchors, 0.01) - co_on(anchors, 100.0)) > 10

    def test_dividers_lean_towards_lower_co_as_th_rises(self):
        for anchors in (_B_BAA, _BAA_DR):
            assert co_on(anchors, 100.0) < co_on(anchors, 0.01)

    def test_dividers_never_cross(self):
        for th in (0.01, 0.1, 1.0, 10.0, 100.0):
            assert co_on(_BAA_DR, th) < co_on(_B_BAA, th)

    def test_dividers_stay_inside_the_axes(self):
        for anchors in (_B_BAA, _BAA_DR):
            for th in (0.01, 1.0, 100.0):
                assert 0.0 < co_on(anchors, th) < 70.0


class TestDiagram:
    def test_axes_match_the_published_figure(self):
        diagram = get_diagram("hastie_2007_thco")
        assert diagram.x_range == (70.0, 0.0), "Co axis must be reversed"
        assert diagram.y_range == (0.01, 100.0)
        assert diagram.log_y is True

    def test_coordinates_come_from_th_and_co(self):
        diagram = get_diagram("hastie_2007_thco")
        df = pd.DataFrame({"Co": [40.0, 10.0], "Th": [1.0, 12.0]})
        xs, ys = diagram._compute_xy(df)
        assert list(xs) == [40.0, 10.0]
        assert list(ys) == [1.0, 12.0]

    def test_missing_columns_are_reported_not_guessed(self):
        diagram = get_diagram("hastie_2007_thco")
        xs, ys = diagram._compute_xy(pd.DataFrame({"Co": [40.0]}))
        assert xs is None and ys is None

    def test_renders_with_the_four_boundaries(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import GroupStyle, PlotStyle
        style = PlotStyle()
        style.group_columns = ["Group"]
        style.groups = [GroupStyle(name="arc")]
        df = pd.DataFrame({"Sample_Name": ["a", "b"], "Co": [55.0, 12.0],
                           "Th": [0.5, 15.0], "Group": ["arc", "arc"]})
        fig = Figure(figsize=(6, 5))
        get_diagram("hastie_2007_thco").plot(fig, df, style, PlotOptions())
        ax = fig.axes[0]
        # Four boundary polylines, each densified for the log axis.
        boundaries = [ln for ln in ax.lines if len(ln.get_xdata()) > 8]
        assert len(boundaries) == 4
        fig.clf()
