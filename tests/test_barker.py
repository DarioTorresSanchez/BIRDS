"""Barker (1979) An–Ab–Or granitoid ternary, measured from the figure.

The two principal boundaries are lines of constant Or.  The figure
states their values twice — as drawn lines and as tick labels on the
An–Or edge — and the measurements below come from the drawing itself,
independently of the vertices the module stores.
"""

from __future__ import annotations

import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.barker import (
    _BOUNDARIES,
    _J1,
    _J2,
    _LABELS,
    BarkerAnAbOr,
    GRANITE_OR,
    GRANODIORITE_OR,
)

DIAGRAM = "barker_anaborn"


def named_boundary(first_vertex):
    for polyline in _BOUNDARIES:
        if polyline[0] == first_vertex or polyline[-1] == first_vertex:
            return polyline
    raise AssertionError(f"no boundary touching {first_vertex}")


class TestPrincipalLimits:
    """Measured Or = 20.20 ± 0.07 and 34.84 ± 0.07 along their length."""

    def test_granodiorite_lower_limit(self):
        assert GRANODIORITE_OR == 20.0

    def test_granite_lower_limit(self):
        assert GRANITE_OR == 35.0

    def test_measured_values_round_to_them(self):
        assert GRANODIORITE_OR == pytest.approx(20.20, abs=0.25)
        assert GRANITE_OR == pytest.approx(34.84, abs=0.25)

    def test_tonalite_granodiorite_line_is_constant_in_or(self):
        line = named_boundary((49.4, 30.6, GRANODIORITE_OR))
        assert all(v[2] == pytest.approx(GRANODIORITE_OR) for v in line)

    def test_granodiorite_granite_line_is_constant_in_or(self):
        line = _BOUNDARIES[-1]
        assert all(v[2] == pytest.approx(GRANITE_OR) for v in line[1:])

    def test_granodiorite_is_a_band_between_them(self):
        assert GRANODIORITE_OR < GRANITE_OR


class TestGeometry:
    def test_every_vertex_sums_to_a_hundred(self):
        for polyline in _BOUNDARIES:
            for vertex in polyline:
                assert sum(vertex) == pytest.approx(100.0, abs=0.15), vertex

    def test_no_negative_components(self):
        for polyline in _BOUNDARIES:
            for vertex in polyline:
                assert min(vertex) >= 0.0, vertex

    def test_the_two_junctions_are_shared(self):
        """Both must appear in more than one boundary or the net is open."""
        for junction in (_J1, _J2):
            touching = [p for p in _BOUNDARIES
                        if junction in (p[0], p[-1])]
            assert len(touching) >= 2, junction

    def test_trondhjemite_corner_contacts_sit_at_albite_seventy(self):
        """Both edge contacts land on the labelled Ab = 70 tick."""
        on_edge = [v for p in _BOUNDARIES for v in p
                   if min(v) == 0.0]
        assert on_edge, "no boundary reaches a triangle side"
        for vertex in on_edge:
            assert vertex[1] == pytest.approx(70.0, abs=0.5), vertex

    def test_trondhjemite_granite_line_reaches_or_thirty(self):
        """The base label the figure marks for it."""
        base = [v for p in _BOUNDARIES for v in p if v[0] == 0.0]
        assert base and base[0][2] == pytest.approx(30.0, abs=0.5)

    def test_boundaries_are_open_segments_not_polygons(self):
        """The figure leaves the fields open at the top; so do we."""
        for polyline in _BOUNDARIES:
            assert polyline[0] != polyline[-1]


class TestLabels:
    def test_all_four_fields_are_named(self):
        assert len(_LABELS) == 4
        assert {n for n, *_ in _LABELS} == {
            "Tonalite", "Granodiorite", "Granite", "Trondhjemite"}

    def test_positions_are_valid_ternary_points(self):
        for name, an, ab, orx in _LABELS:
            assert sum((an, ab, orx)) == pytest.approx(100.0, abs=0.2), name
            assert min(an, ab, orx) >= 0.0, name

    @pytest.mark.parametrize("name", ["Tonalite", "Granodiorite",
                                      "Granite", "Trondhjemite"])
    def test_each_label_sits_in_the_field_it_names(self, name):
        an, ab, orx = next((a, b, c) for n, a, b, c in _LABELS if n == name)
        assert BarkerAnAbOr.classify(an, ab, orx) == name


class TestClassification:
    @pytest.mark.parametrize("an,ab,orx,expected", [
        (10.0, 35.0, 55.0, "Granite"),
        (5.0, 20.0, 75.0, "Granite"),
        (30.0, 42.0, 28.0, "Granodiorite"),
        (20.0, 55.0, 25.0, "Granodiorite"),
        (45.0, 45.0, 10.0, "Tonalite"),
        (60.0, 35.0, 5.0, "Tonalite"),
        (8.0, 78.0, 14.0, "Trondhjemite"),
        (5.0, 85.0, 10.0, "Trondhjemite"),
    ])
    def test_names(self, an, ab, orx, expected):
        assert BarkerAnAbOr.classify(an, ab, orx) == expected

    def test_renormalises_an_unclosed_norm(self):
        """A CIPW norm rarely sums to exactly 100."""
        assert BarkerAnAbOr.classify(15.0, 21.0, 27.5) == \
            BarkerAnAbOr.classify(24.2, 33.9, 44.4)

    def test_the_or_boundaries_are_where_the_names_change(self):
        assert BarkerAnAbOr.classify(40.0, 40.0 - 0.5, GRANODIORITE_OR
                                     + 0.5) == "Granodiorite"
        assert BarkerAnAbOr.classify(40.0, 25.5, GRANITE_OR - 0.5) == \
            "Granodiorite"
        assert BarkerAnAbOr.classify(40.0, 24.5, GRANITE_OR + 0.5) == \
            "Granite"

    def test_the_trondhjemite_split_follows_the_measured_line(self):
        """At Or = 10 the line sits midway between its two endpoints."""
        limit = 25.0          # An midway from 30 at Or 0 to 20 at Or 20
        assert BarkerAnAbOr.classify(limit + 2, 100 - 10 - limit - 2,
                                     10.0) == "Tonalite"
        assert BarkerAnAbOr.classify(limit - 2, 100 - 10 - limit + 2,
                                     10.0) == "Trondhjemite"

    def test_blank_or_empty_input_gives_no_name(self):
        assert BarkerAnAbOr.classify(float("nan"), 50.0, 20.0) == ""
        assert BarkerAnAbOr.classify(0.0, 0.0, 0.0) == ""


class TestRendering:
    def test_draws_every_boundary_and_label(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle
        fig = Figure(figsize=(7, 6))
        get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
        ax = fig.axes[0]
        texts = {t.get_text() for t in ax.texts}
        for name, *_ in _LABELS:
            assert name in texts
        assert len(ax.lines) >= len(_BOUNDARIES)
        fig.clf()

    def test_plots_samples_from_normative_feldspar(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import GroupStyle, PlotStyle
        style = PlotStyle()
        style.group_columns = ["Group"]
        style.groups = [GroupStyle(name="g")]
        df = pd.DataFrame({"Sample_Name": ["a", "b"],
                           "An": [45.0, 10.0], "Ab": [45.0, 35.0],
                           "Or": [10.0, 55.0], "Group": ["g", "g"]})
        fig = Figure(figsize=(7, 6))
        get_diagram(DIAGRAM).plot(fig, df, style, PlotOptions())
        assert fig.axes[0].collections, "no samples drawn"
        fig.clf()

    def test_missing_normative_columns_are_reported_not_guessed(self):
        from birds.diagrams.templates.base import normative_note
        only_an = pd.DataFrame({"An": [40.0]})        # and no majors
        assert get_diagram(DIAGRAM)._compute_xy(only_an) == (None, None)
        assert "No normative minerals" in normative_note(
            only_an, ("An", "Ab", "Or"))
