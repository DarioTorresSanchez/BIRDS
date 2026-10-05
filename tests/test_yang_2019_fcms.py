"""The FCMS plane of Yang et al. (2019), Figure 1a.

FCMS was computed and reported in the statistics table and had no
diagram, so there was nothing to read the number against.  The sweep in
``test_statistics_match_diagrams.py`` found it by having no partner to
pair with.

What it did **not** have, and still does not, is a discrimination
diagram with fields.  Yang et al. give boundary coordinates in exactly
one place — the caption of Figure 7 — and those are for FCKANTMS.
Their conclusions say why: FCKANTMS is "a more powerful parameter"
because incorporating ln(K2O/Al2O3), ln(TiO2/Na2O) and ln(Na2O/K2O)
removes the temperature and pressure effects that make lherzolite
melts scatter in the FCMS plane.  So no fields are invented here.

What is published is the plane itself and the trend through it.
Figure 1a plots ln(FeO/CaO) against ln(MgO/SiO2) and prints the cubic
beside the curve: y = 0.058x³ + 0.636x² + 1.850x + 1.170, R² = 0.944.
FCMS *is* the vertical distance from that curve, which is what makes
the diagram worth drawing: a sample's FCMS can be read straight off
it, and a lherzolite melt sits near the line.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import _REGISTRY, get_diagram
from birds.diagrams.templates.tectonic_bivariate import (
    YANG_FIG1A_X_RANGE,
    YANG_FIG1A_Y_RANGE,
    YANG_LHERZOLITE_TREND,
    _cubic,
)
from birds.tectonic_results import DISCRIMINATORS

DIAGRAM = "yang_2019_fcms"

#: Two melts far enough apart to sit either side of the trend.
MELTS = pd.DataFrame({
    "SiO2": [46.0, 49.0, 52.0],
    "MgO": [12.0, 8.0, 5.5],
    "FeO": [9.5, 11.5, 10.0],
    "CaO": [11.0, 8.5, 9.0],
    "TiO2": [1.0, 2.0, 1.6],
    "Na2O": [2.0, 3.0, 3.2],
    "K2O": [0.4, 0.9, 1.1],
    "Al2O3": [15.0, 15.5, 16.0],
})


def _fcms_row():
    found = [d for d in DISCRIMINATORS if d.key == "yang.fcms"]
    assert len(found) == 1
    return found[0]


# ---------------------------------------------------------------------------
# The published trend
# ---------------------------------------------------------------------------

def test_the_cubic_is_the_one_printed_on_figure_1a():
    """0.058, 0.636, 1.850, 1.170 — on the figure, in Table 1, and
    again in the conclusions, so there is no room for doubt."""
    assert YANG_LHERZOLITE_TREND == (0.058, 0.636, 1.850, 1.170)


def test_the_frame_is_figure_1as_own():
    d = get_diagram(DIAGRAM)
    assert tuple(d.x_range) == YANG_FIG1A_X_RANGE == (-3.5, 1.0)
    assert tuple(d.y_range) == YANG_FIG1A_Y_RANGE == (-1.4, 1.4)
    assert not d.log_x and not d.log_y


def test_the_trend_has_a_minimum_inside_the_frame():
    """Figure 1a shows it dipping to about -0.45 near x = -2 and
    climbing steeply to the right; a sign error in any coefficient
    would lose that shape."""
    xs = np.linspace(*YANG_FIG1A_X_RANGE, 2001)
    ys = _cubic(YANG_LHERZOLITE_TREND, xs)
    i = int(np.argmin(ys))
    assert YANG_FIG1A_X_RANGE[0] < xs[i] < YANG_FIG1A_X_RANGE[1]
    assert xs[i] == pytest.approx(-2.0, abs=0.15)
    assert ys[i] == pytest.approx(-0.45, abs=0.05)
    assert ys[-1] > ys[i] + 1.0           # climbs steeply to the right


# ---------------------------------------------------------------------------
# The axes
# ---------------------------------------------------------------------------

def test_the_axes_are_the_two_logratios():
    d = get_diagram(DIAGRAM)
    assert "MgO" in d.x_label and "SiO" in d.x_label
    assert "FeO" in d.y_label and "CaO" in d.y_label

    df = pd.DataFrame({"SiO2": [50.0], "MgO": [50.0],
                       "FeO": [10.0], "CaO": [10.0]})
    x, y = d._compute_xy(df)
    assert float(x.iloc[0]) == pytest.approx(0.0)
    assert float(y.iloc[0]) == pytest.approx(0.0)


def test_all_iron_is_counted_as_feo():
    """The parameters were calibrated on experimental melts, where
    iron is reported as FeO; a sample giving Fe2O3 must be converted
    rather than having its ferric iron dropped."""
    d = get_diagram(DIAGRAM)
    as_feo = pd.DataFrame({"SiO2": [50.0], "MgO": [10.0],
                           "FeO": [9.0], "CaO": [10.0]})
    split = pd.DataFrame({"SiO2": [50.0], "MgO": [10.0],
                          "FeO": [5.0], "Fe2O3": [4.4463], "CaO": [10.0]})
    _x1, y1 = d._compute_xy(as_feo)
    _x2, y2 = d._compute_xy(split)
    assert float(y2.iloc[0]) == pytest.approx(float(y1.iloc[0]), abs=0.01)


def test_a_sample_missing_an_oxide_is_declined():
    d = get_diagram(DIAGRAM)
    x, y = d._compute_xy(pd.DataFrame({"SiO2": [50.0], "MgO": [10.0]}))
    assert x is None or y is None


# ---------------------------------------------------------------------------
# The point of the diagram: FCMS is the distance from the curve
# ---------------------------------------------------------------------------

def test_fcms_is_the_vertical_distance_from_the_trend():
    """The claim the citation makes, checked against the other route.

    The statistics row and the diagram reach this by different code --
    the row evaluates equation (2), the diagram plots the two
    logratios -- so their agreeing is a real cross-check rather than a
    restatement.
    """
    x, y = get_diagram(DIAGRAM)._compute_xy(MELTS)
    expected = np.asarray(y, float) - _cubic(YANG_LHERZOLITE_TREND,
                                             np.asarray(x, float))
    got = np.asarray(_fcms_row().compute(MELTS), float)
    np.testing.assert_allclose(got, expected, rtol=1e-12)


def test_a_sample_on_the_curve_has_fcms_zero():
    """Which is what makes the line worth drawing at all."""
    x = -1.5
    on_curve = float(_cubic(YANG_LHERZOLITE_TREND, np.array([x]))[0])
    # pick oxides that land exactly there: MgO/SiO2 = e^x, FeO/CaO = e^y
    sio2 = 50.0
    cao = 10.0
    df = pd.DataFrame({"SiO2": [sio2], "MgO": [sio2 * np.exp(x)],
                       "CaO": [cao], "FeO": [cao * np.exp(on_curve)]})
    assert float(_fcms_row().compute(df).iloc[0]) == pytest.approx(0.0,
                                                                   abs=1e-9)


def test_the_sign_of_fcms_matches_the_side_of_the_curve():
    x, y = get_diagram(DIAGRAM)._compute_xy(MELTS)
    curve = _cubic(YANG_LHERZOLITE_TREND, np.asarray(x, float))
    fcms = np.asarray(_fcms_row().compute(MELTS), float)
    above = np.asarray(y, float) > curve
    assert np.all(above == (fcms > 0))


# ---------------------------------------------------------------------------
# What is deliberately absent
# ---------------------------------------------------------------------------

def test_no_field_boundaries_are_drawn():
    """Yang et al. publish none for this plane.

    Only Figure 7's caption gives boundary coordinates, and those are
    FCKANTMS against ln(SiO2/(CaO+Na2O+TiO2)).  The one line here is
    the published trend, not a discriminant.
    """
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    from birds.plot_style import PlotStyle

    fig = Figure()
    get_diagram(DIAGRAM).plot(fig, MELTS, PlotStyle(), PlotOptions())
    ax = fig.axes[0]
    background = [ln for ln in ax.lines if ln.get_label().startswith("_")]
    assert len(background) == 1, "only the lherzolite trend belongs here"

    drawn = background[0]
    xs = np.asarray(drawn.get_xdata(), float)
    np.testing.assert_allclose(np.asarray(drawn.get_ydata(), float),
                               _cubic(YANG_LHERZOLITE_TREND, xs),
                               rtol=1e-12)
    fig.clf()


def test_the_citation_says_the_paper_prefers_fckantms():
    """A user reaching for FCMS should know the paper moved on from it."""
    citation = get_diagram(DIAGRAM).citation
    assert "FCKANTMS" in citation
    assert "no field boundaries" in citation
    assert "0.944" in citation          # the published R^2 of the trend


def test_both_yang_parameters_now_have_a_diagram():
    """The gap the sweep found, closed.

    Both are registered and both are reachable; FCMS plots the plane
    its parameter is defined in, FCKANTMS plots Figure 7b.
    """
    assert DIAGRAM in _REGISTRY
    assert "yang_2019_fckantms" in _REGISTRY
    keys = {d.key for d in DISCRIMINATORS if d.key.startswith("yang.")}
    assert keys == {"yang.fcms", "yang.fckantms"}


def test_the_catalogue_lists_them_separately():
    """They used to share one entry reading "FCMS / FCKANTMS", which
    pointed at the FCKANTMS diagram only."""
    from birds.diagrams.catalog import TECTONIC_VOLCANIC

    labels = {key: label
              for section in TECTONIC_VOLCANIC.values()
              for label, key in section}
    assert "FCMS" in labels[DIAGRAM]
    assert "FCMS /" not in labels["yang_2019_fckantms"]
