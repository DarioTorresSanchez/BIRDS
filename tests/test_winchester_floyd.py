"""Winchester & Floyd (1977) — boundaries measured from the figure.

The control points below are independent readings of the published
figure, taken away from the vertices the module stores, so a refactor
that shifts a boundary fails here rather than quietly renaming rocks.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.winchester_floyd import (
    _DASHED,
    _LABELS,
    _SOLID,
    SUBALKALINE_LIMIT,
)

DIAGRAM = "winchester_floyd_1977"


def interp(polyline, x: float) -> float:
    """Value of *polyline* at *x* — straight in log-log space."""
    pts = sorted(polyline)
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        if x0 <= x <= x1:
            f = (np.log10(x) - np.log10(x0)) / (np.log10(x1) - np.log10(x0))
            return float(10 ** (np.log10(y0)
                                + f * (np.log10(y1) - np.log10(y0))))
    raise AssertionError(f"x={x} outside {pts[0][0]}..{pts[-1][0]}")


def named(collection, x: float, y: float):
    """The polyline whose first vertex matches — keeps tests readable."""
    for polyline in collection:
        if (abs(polyline[0][0] - x) < 1e-6
                and abs(polyline[0][1] - y) < 1e-6):
            return polyline
    raise AssertionError(f"no polyline starting at ({x}, {y})")


class TestAxes:
    def test_limits_match_the_published_figure(self):
        diagram = get_diagram(DIAGRAM)
        assert diagram.x_range == (0.01, 10.0)
        assert diagram.y_range == (0.001, 5.0)
        assert diagram.log_x and diagram.log_y

    def test_ratio_uses_titanium_in_ppm(self):
        """Zr/TiO2 × 0.0001 means Zr(ppm) / TiO2(ppm)."""
        diagram = get_diagram(DIAGRAM)
        df = pd.DataFrame({"Nb": [6.0], "Y": [20.0],
                           "Zr": [100.0], "TiO2": [1.0]})
        xs, ys = diagram._compute_xy(df)
        assert float(xs.iloc[0]) == pytest.approx(0.3)
        assert float(ys.iloc[0]) == pytest.approx(0.01)

    def test_non_positive_denominators_do_not_blow_up_the_log_axes(self):
        diagram = get_diagram(DIAGRAM)
        df = pd.DataFrame({"Nb": [6.0, 6.0], "Y": [0.0, 20.0],
                           "Zr": [100.0, 100.0], "TiO2": [1.0, 0.0]})
        xs, ys = diagram._compute_xy(df)
        assert pd.isna(xs.iloc[0]) and pd.isna(ys.iloc[1])

    def test_missing_columns_are_reported_not_guessed(self):
        diagram = get_diagram(DIAGRAM)
        xs, ys = diagram._compute_xy(pd.DataFrame({"Nb": [1.0],
                                                   "Y": [1.0]}))
        assert xs is None and ys is None


class TestSubAlkalineDivide:
    """The diagram's backbone, and the one value everyone quotes."""

    def test_sits_where_the_literature_puts_it(self):
        assert 0.60 <= SUBALKALINE_LIMIT <= 0.70

    @staticmethod
    def _divide():
        """The one solid polyline whose x never varies."""
        verticals = [p for p in _SOLID
                     if len({round(x, 6) for x, _y in p}) == 1]
        assert len(verticals) == 2, "expected two vertical boundaries"
        return next(p for p in verticals
                    if abs(p[0][0] - SUBALKALINE_LIMIT) < 1e-6)

    def test_the_vertical_boundary_uses_it(self):
        divide = self._divide()
        assert all(x == SUBALKALINE_LIMIT for x, _y in divide)

    def test_it_spans_the_useful_height(self):
        divide = self._divide()
        assert max(y for _x, y in divide) > 0.08
        assert min(y for _x, y in divide) < 0.002

    def test_it_stops_short_of_the_bottom_axis(self):
        """The figure does not run it into the frame; nor do we."""
        divide = self._divide()
        assert min(y for _x, y in divide) > get_diagram(DIAGRAM).y_range[0]


class TestMeasuredBoundaries:
    """Control points read off the figure between the stored vertices."""

    @pytest.mark.parametrize("nb_y,expected", [
        (0.05, 0.04603), (0.08, 0.03977), (0.10, 0.03684),
        (0.15, 0.03224), (0.20, 0.02930), (0.25, 0.02715),
    ])
    def test_andesite_rhyodacite(self, nb_y, expected):
        line = named(_DASHED, 0.0229, 0.0597)
        assert interp(line, nb_y) == pytest.approx(expected, rel=0.06)

    @pytest.mark.parametrize("nb_y,expected", [
        (0.25, 0.11144), (0.30, 0.10391), (0.35, 0.10066),
        (0.45, 0.09326), (0.50, 0.09092),
    ])
    def test_rhyodacite_rhyolite(self, nb_y, expected):
        line = named(_DASHED, 0.1948, 0.1186)
        assert interp(line, nb_y) == pytest.approx(expected, rel=0.06)

    @pytest.mark.parametrize("nb_y,expected", [
        (0.10, 0.01242), (0.15, 0.01274), (0.20, 0.01298),
        (0.30, 0.01340), (0.40, 0.01349),
    ])
    def test_andesite_basalt_andesite(self, nb_y, expected):
        line = named(_DASHED, 0.0735, 0.0122)
        assert interp(line, nb_y) == pytest.approx(expected, rel=0.06)

    @pytest.mark.parametrize("nb_y,expected", [
        (0.331, 0.00915), (0.05, 0.00492),
    ])
    def test_sub_alkaline_basalt_andesite_basalt(self, nb_y, expected):
        line = named(_DASHED, 0.0277, 0.0047)
        assert interp(line, nb_y) == pytest.approx(expected, rel=0.08)

    @pytest.mark.parametrize("nb_y,expected", [
        (3.5, 0.29491), (5.0, 0.22010), (6.5, 0.17394), (8.0, 0.15711),
    ])
    def test_phonolite_trachyte(self, nb_y, expected):
        line = named(_DASHED, 1.9093, 1.1504)
        assert interp(line, nb_y) == pytest.approx(expected, rel=0.06)

    @pytest.mark.parametrize("nb_y,expected", [
        (2.0, 0.07005), (3.0, 0.05536),
    ])
    def test_trachyte_trachyandesite(self, nb_y, expected):
        line = named(_SOLID, 1.1800, 0.0951)
        assert interp(line, nb_y) == pytest.approx(expected, rel=0.06)


class TestTopology:
    def test_every_vertex_is_inside_the_axes(self):
        diagram = get_diagram(DIAGRAM)
        x_lo, x_hi = diagram.x_range
        y_lo, y_hi = diagram.y_range
        for polyline in _SOLID + _DASHED:
            for x, y in polyline:
                assert x_lo <= x <= x_hi, f"{x} outside the Nb/Y axis"
                assert y_lo <= y <= y_hi, f"{y} outside the Zr/TiO2 axis"

    def test_every_label_is_inside_the_axes(self):
        diagram = get_diagram(DIAGRAM)
        x_lo, x_hi = diagram.x_range
        y_lo, y_hi = diagram.y_range
        for name, x, y in _LABELS:
            assert x_lo <= x <= x_hi and y_lo <= y <= y_hi, name

    def test_all_eleven_fields_are_named(self):
        assert len(_LABELS) == 11
        assert len({n for n, _x, _y in _LABELS}) == 11

    def test_sub_alkaline_labels_sit_left_of_the_divide(self):
        for name in ("Sub-alkaline\nbasalt", "Andesite /\nbasalt",
                     "Andesite", "Rhyodacite /\ndacite", "Rhyolite"):
            x = next(x for n, x, _y in _LABELS if n == name)
            assert x < SUBALKALINE_LIMIT, name

    def test_alkaline_labels_sit_right_of_the_divide(self):
        for name in ("Trachy-\nandesite", "Alkali\nbasalt", "Trachyte",
                     "Phonolite", "Basanite /\nnephelinite"):
            x = next(x for n, x, _y in _LABELS if n == name)
            assert x > SUBALKALINE_LIMIT, name

    def test_polylines_are_ordered_and_non_degenerate(self):
        for polyline in _SOLID + _DASHED:
            assert len(polyline) >= 2
            assert len(set(polyline)) == len(polyline)

    def test_dashed_boundaries_are_kept_distinct_from_solid(self):
        """The authors drew the uncertain ones dashed; so do we."""
        assert len(_SOLID) >= 10 and len(_DASHED) >= 6
        solid_starts = {p[0] for p in _SOLID}
        assert not solid_starts & {p[0] for p in _DASHED}


class TestRendering:
    def test_draws_every_boundary(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import GroupStyle, PlotStyle
        style = PlotStyle()
        style.group_columns = ["Group"]
        style.groups = [GroupStyle(name="alt")]
        df = pd.DataFrame({"Sample_Name": ["a", "b"],
                           "Nb": [6.0, 20.0], "Y": [20.0, 10.0],
                           "Zr": [100.0, 400.0], "TiO2": [1.0, 0.4],
                           "Group": ["alt", "alt"]})
        fig = Figure(figsize=(7, 6))
        get_diagram(DIAGRAM).plot(fig, df, style, PlotOptions())
        ax = fig.axes[0]
        drawn = [ln for ln in ax.lines if len(ln.get_xdata()) >= 2]
        assert len(drawn) >= len(_SOLID) + len(_DASHED)
        texts = {t.get_text() for t in ax.texts}
        for name, _x, _y in _LABELS:
            assert name in texts
        fig.clf()

    def test_dashed_lines_really_are_dashed(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle
        fig = Figure(figsize=(7, 6))
        get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
        styles = {ln.get_linestyle() for ln in fig.axes[0].lines}
        assert len(styles) >= 2, "solid and dashed collapsed into one style"
        fig.clf()
