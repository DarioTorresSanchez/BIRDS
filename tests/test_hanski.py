"""Hanski et al. (2001) high-Mg — boundaries measured from the figure.

Every expected value is an independent reading of the published figure
taken between the endpoints the module stores, so a refactor that
nudges a boundary fails here rather than quietly renaming komatiites.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.hanski import (
    _AL_DIVIDE,
    _BONINITE,
    _BOUNDARIES,
    _LABELS,
    _MEIMECHITE,
    _PICRITE_KOMATIITE,
    _TI_ENRICHED,
)

DIAGRAM = "hanski"


def ti_at(boundary, al: float) -> float:
    """[TiO2] of a sub-horizontal boundary at a given [Al2O3]."""
    (x0, y0), (x1, y1) = boundary
    return float(y0 + (al - x0) * (y1 - y0) / (x1 - x0))


def al_at(boundary, ti: float) -> float:
    """[Al2O3] of the steep divider at a given [TiO2]."""
    (x0, y0), (x1, y1) = boundary
    return float(x0 + (ti - y0) * (x1 - x0) / (y1 - y0))


class TestAxes:
    def test_limits_match_the_published_figure(self):
        diagram = get_diagram(DIAGRAM)
        assert diagram.x_range == (0.0, 0.25)
        assert diagram.y_range == (0.0, 0.13)

    def test_axes_are_linear(self):
        diagram = get_diagram(DIAGRAM)
        assert not getattr(diagram, "log_x", False)
        assert not getattr(diagram, "log_y", False)


class TestSubHorizontalBoundaries:
    @pytest.mark.parametrize("al,expected", [
        (0.02, 0.09022), (0.06, 0.09195), (0.10, 0.09369),
        (0.14, 0.09542), (0.18, 0.09716), (0.22, 0.09889),
    ])
    def test_meimechite(self, al, expected):
        assert ti_at(_MEIMECHITE, al) == pytest.approx(expected, abs=0.0004)

    @pytest.mark.parametrize("al,expected", [
        (0.02, 0.02057), (0.06, 0.02231), (0.10, 0.02379),
        (0.14, 0.02553), (0.18, 0.02702),
    ])
    def test_picrite_komatiite(self, al, expected):
        assert ti_at(_PICRITE_KOMATIITE, al) == pytest.approx(
            expected, abs=0.0004)

    @pytest.mark.parametrize("al,expected", [
        (0.02, 0.01066), (0.06, 0.01214), (0.10, 0.01388),
        (0.14, 0.01537), (0.18, 0.01710),
    ])
    def test_ti_enriched(self, al, expected):
        assert ti_at(_TI_ENRICHED, al) == pytest.approx(expected, abs=0.0004)

    @pytest.mark.parametrize("al,expected", [
        (0.10, 0.00397), (0.14, 0.00545), (0.18, 0.00694), (0.22, 0.00867),
    ])
    def test_boninite(self, al, expected):
        assert ti_at(_BONINITE, al) == pytest.approx(expected, abs=0.0004)

    def test_boninite_passes_through_the_origin(self):
        assert ti_at(_BONINITE, 0.0) == pytest.approx(0.0, abs=0.0005)

    def test_they_never_cross(self):
        """A crossing would swap two fields over part of the diagram."""
        ordered = (_BONINITE, _TI_ENRICHED, _PICRITE_KOMATIITE,
                   _MEIMECHITE)
        for al in np.linspace(0.0, 0.25, 26):
            values = [ti_at(b, al) for b in ordered]
            assert values == sorted(values), f"boundaries cross at {al}"

    def test_they_are_nearly_parallel(self):
        """The figure draws them as a family; slopes agree within 10 %."""
        slopes = [(y1 - y0) / (x1 - x0)
                  for (x0, y0), (x1, y1) in
                  (_BONINITE, _TI_ENRICHED, _PICRITE_KOMATIITE,
                   _MEIMECHITE)]
        assert max(slopes) / min(slopes) < 1.10

    def test_all_rise_towards_higher_alumina(self):
        for boundary in (_BONINITE, _TI_ENRICHED, _PICRITE_KOMATIITE,
                         _MEIMECHITE):
            assert boundary[1][1] > boundary[0][1]


class TestAluminaDivide:
    @pytest.mark.parametrize("ti,expected", [
        (0.01, 0.16646), (0.02, 0.15716), (0.04, 0.13936),
        (0.06, 0.12156), (0.08, 0.10336),
    ])
    def test_position(self, ti, expected):
        assert al_at(_AL_DIVIDE, ti) == pytest.approx(expected, abs=0.0008)

    def test_it_leans_towards_lower_alumina_as_titanium_rises(self):
        assert _AL_DIVIDE[1][0] > _AL_DIVIDE[0][0]
        assert _AL_DIVIDE[1][1] < _AL_DIVIDE[0][1]

    def test_it_meets_the_meimechite_line_at_its_top(self):
        top_al, top_ti = _AL_DIVIDE[0]
        assert ti_at(_MEIMECHITE, top_al) == pytest.approx(top_ti,
                                                           abs=0.0006)

    def test_it_meets_the_boninite_line_at_its_bottom(self):
        low_al, low_ti = _AL_DIVIDE[1]
        assert ti_at(_BONINITE, low_al) == pytest.approx(low_ti, abs=0.0006)

    def test_it_is_not_vertical(self):
        assert abs(_AL_DIVIDE[1][0] - _AL_DIVIDE[0][0]) > 0.05


class TestFields:
    def test_all_eight_fields_are_named(self):
        assert len(_LABELS) == 8
        assert len({n for n, _x, _y in _LABELS}) == 8

    def test_every_label_is_inside_the_axes(self):
        diagram = get_diagram(DIAGRAM)
        for name, x, y in _LABELS:
            assert diagram.x_range[0] <= x <= diagram.x_range[1], name
            assert diagram.y_range[0] <= y <= diagram.y_range[1], name

    @pytest.mark.parametrize("name,side", [
        ("Al-depleted\nPicrite", "left"),
        ("Ti-enriched, Al-depleted komatiite", "left"),
        ("Al-depleted komatiite", "left"),
        ("Picrite", "right"),
        ("Ti-enriched komatiite", "right"),
        ("Al-undepleted\nkomatiite", "right"),
    ])
    def test_labels_sit_on_their_side_of_the_divide(self, name, side):
        x, y = next((x, y) for n, x, y in _LABELS if n == name)
        divide = al_at(_AL_DIVIDE, y)
        assert (x < divide) if side == "left" else (x > divide), name

    def test_meimechite_sits_above_its_boundary(self):
        x, y = next((x, y) for n, x, y in _LABELS if n == "Meimechite")
        assert y > ti_at(_MEIMECHITE, x)

    def test_boninite_sits_below_its_boundary(self):
        x, y = next((x, y) for n, x, y in _LABELS if n == "Boninite")
        assert y < ti_at(_BONINITE, x)


class TestProjectionIsFlaggedAsBroken:
    """The projection is wrong and the module has to say so out loud."""

    KOMATIITE = dict(SiO2=46.0, TiO2=0.35, Al2O3=7.8, FeO=10.5,
                     MgO=28.0, CaO=6.8)

    def test_komatiites_currently_fall_outside_the_diagram(self):
        """Documents the defect, so a fix makes this test fail loudly."""
        diagram = get_diagram(DIAGRAM)
        xs, ys = diagram._compute_xy(pd.DataFrame([self.KOMATIITE]))
        x, y = float(xs.iloc[0]), float(ys.iloc[0])
        inside = (diagram.x_range[0] <= x <= diagram.x_range[1]
                  and diagram.y_range[0] <= y <= diagram.y_range[1])
        assert not inside, (
            "the olivine projection now places a komatiite on the "
            "diagram — verify it against Hanski et al. and update this "
            "test and the module warning")

    def test_the_warning_is_visible_in_the_citation(self):
        """The caveat has to reach the screen, not just the source."""
        citation = get_diagram(DIAGRAM).citation.lower()
        assert "unverified" in citation or "warning" in citation

    def test_missing_columns_are_reported_not_guessed(self):
        diagram = get_diagram(DIAGRAM)
        xs, ys = diagram._compute_xy(pd.DataFrame({"Al2O3": [8.0]}))
        assert xs is None and ys is None


class TestRendering:
    def test_draws_five_boundaries_and_eight_labels(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle
        fig = Figure(figsize=(7, 5))
        get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
        ax = fig.axes[0]
        assert len([ln for ln in ax.lines if len(ln.get_xdata()) == 2]) \
            >= len(_BOUNDARIES)
        texts = {t.get_text() for t in ax.texts}
        for name, _x, _y in _LABELS:
            assert name in texts
        fig.clf()
