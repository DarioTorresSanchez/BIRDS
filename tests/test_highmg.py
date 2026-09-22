"""Le Maitre (2002) high-Mg subdivision — the IUGS rule, as stated.

This diagram is a picture of a definition rather than a set of drawn
curves, so the tests check the definition itself: the limits, the axes
they are drawn against, and that a sample on either side of each one
gets the name the rule gives it.
"""

from __future__ import annotations

import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.highmg_tas import (
    HighMgTAS,
    KOMATIITE_ALKALIS,
    KOMATIITE_MGO,
    MEIMECHITE_TIO2,
    PICRITE_ALKALIS,
    PICRITE_MGO,
)

DIAGRAM = "highmg_tas"


class TestLimits:
    """Values measured off the figure round to exactly these."""

    def test_picrite_magnesia(self):
        assert PICRITE_MGO == 12.0

    def test_picrite_alkalis(self):
        assert PICRITE_ALKALIS == 3.0

    def test_komatiite_magnesia(self):
        assert KOMATIITE_MGO == 18.0

    def test_komatiite_alkalis(self):
        assert KOMATIITE_ALKALIS == 2.0

    def test_meimechite_titania(self):
        assert MEIMECHITE_TIO2 == 1.0

    def test_the_inner_field_is_the_stricter_one(self):
        """Komatiite sits inside the picrite envelope, not beside it."""
        assert KOMATIITE_MGO > PICRITE_MGO
        assert KOMATIITE_ALKALIS < PICRITE_ALKALIS


class TestAxes:
    def test_plots_alkalis_not_titania(self):
        """The old version used TiO2 on y, which is a different plane."""
        diagram = get_diagram(DIAGRAM)
        assert "Na" in diagram.y_label and "K" in diagram.y_label
        assert "MgO" in diagram.x_label

    def test_coordinates_are_magnesia_and_total_alkalis(self):
        diagram = get_diagram(DIAGRAM)
        df = pd.DataFrame({"MgO": [20.0], "Na2O": [1.2], "K2O": [0.3],
                           "TiO2": [0.5]})
        xs, ys = diagram._compute_xy(df)
        assert float(xs.iloc[0]) == pytest.approx(20.0)
        assert float(ys.iloc[0]) == pytest.approx(1.5)

    def test_missing_columns_are_reported_not_guessed(self):
        diagram = get_diagram(DIAGRAM)
        xs, ys = diagram._compute_xy(pd.DataFrame({"MgO": [20.0]}))
        assert xs is None and ys is None

    def test_range_covers_the_published_envelope(self):
        """The figure is cropped to MgO 12-30, alkalis 0-3."""
        diagram = get_diagram(DIAGRAM)
        assert diagram.x_range[0] < PICRITE_MGO
        assert diagram.x_range[1] > 30.0
        assert diagram.y_range[1] > PICRITE_ALKALIS

    def test_samples_that_fail_the_rule_stay_on_screen(self):
        """A clipped point would be counted as plotted but be invisible."""
        diagram = get_diagram(DIAGRAM)
        assert diagram.x_range[0] <= 9.0
        assert diagram.y_range[1] >= 4.0


class TestClassification:
    @pytest.mark.parametrize("mgo,alkalis,tio2,expected", [
        # Inside the komatiite / meimechite box, split by titania.
        (25.0, 1.0, 0.5, "Komatiite"),
        (25.0, 1.0, 1.8, "Meimechite"),
        (19.0, 1.9, 0.9, "Komatiite"),
        # Magnesian enough, but too alkaline for the inner box.
        (25.0, 2.5, 0.5, "Picrite"),
        # Picrite proper.
        (14.0, 1.9, 0.8, "Picrite"),
        (12.5, 2.9, 2.0, "Picrite"),
        # Fails a limit: not one of these rocks.
        (11.0, 1.0, 0.5, ""),
        (14.0, 3.5, 0.5, ""),
        (25.0, 3.5, 0.5, ""),
    ])
    def test_names(self, mgo, alkalis, tio2, expected):
        assert HighMgTAS.classify(mgo, alkalis, tio2) == expected

    def test_titania_is_needed_to_separate_the_inner_pair(self):
        """Guessing one of the two would be worse than saying so."""
        assert HighMgTAS.classify(25.0, 1.0) == "Komatiite / meimechite"
        assert HighMgTAS.classify(25.0, 1.0, float("nan")) == \
            "Komatiite / meimechite"

    def test_titania_is_irrelevant_outside_the_inner_box(self):
        assert HighMgTAS.classify(14.0, 1.0, 5.0) == "Picrite"

    def test_limits_are_exclusive_as_the_rule_states_them(self):
        """'> 12' and '< 3', so a sample exactly on a limit is outside."""
        assert HighMgTAS.classify(PICRITE_MGO, 1.0, 0.5) == ""
        assert HighMgTAS.classify(14.0, PICRITE_ALKALIS, 0.5) == ""
        assert HighMgTAS.classify(KOMATIITE_MGO, 1.0, 0.5) == "Picrite"

    def test_blank_input_gives_no_name(self):
        assert HighMgTAS.classify(float("nan"), 1.0, 0.5) == ""
        assert HighMgTAS.classify(25.0, float("nan"), 0.5) == ""


class TestRendering:
    def test_draws_the_two_nested_fields(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle
        fig = Figure(figsize=(7, 5))
        get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
        ax = fig.axes[0]
        assert len([ln for ln in ax.lines if len(ln.get_xdata()) == 2]) >= 4
        blob = " ".join(t.get_text() for t in ax.texts)
        assert "Picrite" in blob
        assert "Meimechite" in blob and "Komatiite" in blob
        fig.clf()

    def test_the_picrite_ceiling_is_dashed_as_published(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle
        fig = Figure(figsize=(7, 5))
        get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
        dashed = [ln for ln in fig.axes[0].lines
                  if ln.get_linestyle() not in ("-", "solid")
                  and len(ln.get_xdata()) == 2]
        assert dashed, "the alkali ceiling of the picrite field is dashed"
        assert max(dashed[0].get_ydata()) == pytest.approx(PICRITE_ALKALIS)
        fig.clf()

    def test_titania_criterion_is_stated_on_the_plot(self, qapp):
        """TiO2 is not an axis, so the label has to carry it."""
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle
        fig = Figure(figsize=(7, 5))
        get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
        blob = " ".join(t.get_text() for t in fig.axes[0].texts)
        assert "TiO" in blob and "1 wt.%" in blob
        fig.clf()
