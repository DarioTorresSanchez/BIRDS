"""Pearce & Cann's Zr-Ti diagram, with Vermeesch's boundaries computed.

What this diagram used to draw was two straight dotted lines at Ti/Zr =
30 and Ti/Zr = 110, with a comment calling them "approximate refined
boundaries".  They were not Vermeesch's and they were not refined; they
were a guess at the shape of his figure.

Vermeesch (2006a) Figure 38 runs a linear discriminant analysis on
ln(Zr/rest) and ln(Ti/rest) -- the additive log-ratio of the three-part
composition (Zr, Ti, everything else) in ppm -- where the boundaries
come out straight, and maps them back to Zr-Ti, where they curve.

Unlike his ternary LDAs, this one is **two separate segments** rather
than three rays from a triple point, which is why the x column of Table
6 repeats: -13, -7, -13, -7.  Reading those four numbers as a triple
point plus three ray ends, as the ternaries need, would put two of the
"rays" on top of each other and lose a field.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import inverse_logratio
from birds.diagrams.templates.tectonic_bivariate import (
    _PEARCE_CANN_LDA,
    _PPM_CLOSURE,
    _pearce_cann_boundary,
)

#: Reference compositions: Zr in ppm, TiO2 in wt.%.
REFERENCE = pd.DataFrame([
    {"Sample": "N-MORB", "Zr": 74.0, "TiO2": 1.15},
    {"Sample": "OIB", "Zr": 229.0, "TiO2": 2.9},
    {"Sample": "IAB", "Zr": 65.0, "TiO2": 0.9},
])


def _field_of(zr, ti):
    """Which of the three bands a point falls in."""
    upper = _pearce_cann_boundary(_PEARCE_CANN_LDA["upper"][0])
    lower = _pearce_cann_boundary(_PEARCE_CANN_LDA["lower"][0])
    if ti > np.interp(zr, upper[0], upper[1]):
        return "OIB"
    if ti > np.interp(zr, lower[0], lower[1]):
        return "MORB"
    return "IAB"


class TestTheAnchorPoints:
    """Table 6, the two rows headed log(Zr/(10^6-Ti-Zr)) and
    log(Ti/(10^6-Ti-Zr))."""

    def test_the_published_values(self):
        assert _PEARCE_CANN_LDA["upper"][0] == ((-13.0, -4.28),
                                                (-7.0, -4.45))
        assert _PEARCE_CANN_LDA["lower"][0] == ((-13.0, -5.36),
                                                (-7.0, -4.72))

    def test_two_segments_and_three_fields(self):
        assert len(_PEARCE_CANN_LDA) == 2
        named = [f for _seg, pair in _PEARCE_CANN_LDA.values() for f in pair]
        assert set(named) == {"IAB", "MORB", "OIB"}
        assert named.count("MORB") == 2, "MORB is the band between them"

    def test_the_segments_share_their_x_range(self):
        """Both run from -13 to -7, which is the giveaway that these are
        segments with endpoints rather than rays from a common point."""
        for segment, _pair in _PEARCE_CANN_LDA.values():
            assert [point[0] for point in segment] == [-13.0, -7.0]

    @pytest.mark.parametrize("name,expected_ti", [
        ("upper", (13654, 11533)),
        ("lower", (4679, 8828)),
    ])
    def test_the_anchors_land_where_the_figure_puts_them(self, name,
                                                         expected_ti):
        """Figure 38d draws the upper boundary flat near Ti = 1.2e4 and
        the lower one rising from about 4000 to 9000."""
        segment, _pair = _PEARCE_CANN_LDA[name]
        for (x, y), want in zip(segment, expected_ti):
            _rest, _zr, ti = inverse_logratio(np.array([x]), np.array([y]))
            assert float(ti[0]) * _PPM_CLOSURE == pytest.approx(want, rel=1e-3)


class TestTheBoundaries:

    def test_they_span_the_frame(self):
        diagram = get_diagram("pearce_cann_1973_ZrTi")
        low, high = diagram.x_range
        for segment, _pair in _PEARCE_CANN_LDA.values():
            zr, _ti = _pearce_cann_boundary(segment)
            assert zr.min() < low and zr.max() > high, (
                "a boundary stops inside the frame")

    def test_the_upper_one_stays_above_the_lower_one(self):
        """They must not cross, or a field would vanish."""
        upper = _pearce_cann_boundary(_PEARCE_CANN_LDA["upper"][0])
        lower = _pearce_cann_boundary(_PEARCE_CANN_LDA["lower"][0])
        probe = np.geomspace(10.0, 1000.0, 50)
        above = np.interp(probe, upper[0], upper[1])
        below = np.interp(probe, lower[0], lower[1])
        assert (above > below).all()

    def test_they_are_not_the_straight_lines_they_replaced(self):
        """The old background drew Ti = 30 Zr and Ti = 110 Zr.  Nothing
        about these boundaries is a constant Ti/Zr ratio: along the
        upper one Ti falls slightly while Zr rises by two orders of
        magnitude."""
        zr, ti = _pearce_cann_boundary(_PEARCE_CANN_LDA["upper"][0])
        inside = (zr > 10.0) & (zr < 1000.0)
        ratio = ti[inside] / zr[inside]
        assert ratio.max() / ratio.min() > 50


class TestReferenceBasalts:

    @pytest.mark.parametrize("name", ["N-MORB", "OIB", "IAB"])
    def test_each_lands_in_its_own_band(self, name):
        diagram = get_diagram("pearce_cann_1973_ZrTi")
        zr, ti = diagram._compute_xy(REFERENCE)
        index = list(REFERENCE["Sample"]).index(name)
        got = _field_of(float(zr.iloc[index]), float(ti.iloc[index]))
        assert got == name.replace("N-", "")

    def test_titanium_comes_from_the_oxide_when_the_element_is_absent(self):
        """Most analyses report TiO2, and the log-ratio is against a
        ppm closure, so the conversion has to happen."""
        diagram = get_diagram("pearce_cann_1973_ZrTi")
        _zr, ti = diagram._compute_xy(REFERENCE.iloc[[0]])
        assert float(ti.iloc[0]) == pytest.approx(1.15 * 5993.4)


class TestItDraws:

    def test_the_figure_carries_both_curves_and_three_labels(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle

        figure = plt.figure()
        get_diagram("pearce_cann_1973_ZrTi").plot(
            figure, REFERENCE, PlotStyle(), PlotOptions())
        ax = figure.axes[0]
        curves = [line for line in ax.lines if len(line.get_xdata()) > 50]
        assert len(curves) == 2
        assert {"OIB", "MORB", "IAB"} <= {t.get_text() for t in ax.texts}
        plt.close(figure)

    def test_the_labels_sit_in_their_own_bands(self):
        """A label in the wrong band would be worse than none."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle

        figure = plt.figure()
        get_diagram("pearce_cann_1973_ZrTi").plot(
            figure, REFERENCE, PlotStyle(), PlotOptions())
        for text in figure.axes[0].texts:
            name = text.get_text()
            if name not in {"OIB", "MORB", "IAB"}:
                continue
            x, y = text.get_position()
            assert _field_of(x, y) == name, f"{name} label is in another band"
        plt.close(figure)
