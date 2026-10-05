"""Samples outside a diagram's frame are reported, not counted as plotted.

Twenty-four of the 52 templates fix their limits to the frame their
source figure is drawn on -- the TAS is 35-78 wt.% SiO2 by 0-16 wt.%
alkalis, the Verma panels run -8 to +8 -- and eight more carry those
limits on their panels.  A sample beyond the frame is drawn and then
clipped away by matplotlib, so it is absent from the figure however
good its analysis was.

It used to be counted as plotted, which is the worst of both: invisible
on the canvas and accounted for as though it were there.  Someone
checking "n = 12 plotted" against twelve points would have counted
eleven and had no way to find the twelfth.

The frame itself is left alone.  Widening it to fit the data would move
boundaries that are only defined inside it -- there is no TAS field at
90 wt.% SiO2 to put a sample in.
"""

from __future__ import annotations

import pandas as pd
import pytest

from birds.diagrams.registry import _REGISTRY, get_diagram
from birds.plot_style import PlotStyle
from birds.views.sample_counts import (
    _within,
    count_for_diagram,
    count_samples,
)


@pytest.fixture
def style():
    return PlotStyle()


class TestTheTas:
    """Frame: 35-78 wt.% SiO2 by 0-16 wt.% total alkalis."""

    SAMPLES = pd.DataFrame([
        {"Sample": "inside", "SiO2": 50.0, "Na2O": 2.0, "K2O": 1.0},
        {"Sample": "past the silica edge", "SiO2": 90.0, "Na2O": 2.0,
         "K2O": 1.0},
        {"Sample": "past the alkali edge", "SiO2": 50.0, "Na2O": 12.0,
         "K2O": 8.0},
        {"Sample": "no silica at all", "SiO2": None, "Na2O": 2.0,
         "K2O": 1.0},
    ])

    @pytest.fixture
    def report(self, style):
        return count_for_diagram(get_diagram("tas_volcanic"),
                                 self.SAMPLES, self.SAMPLES, style)

    def test_only_the_one_inside_counts_as_plotted(self, report):
        assert report.plotted == 1
        assert report.names_for("plotted") == ["inside"]

    def test_both_edges_are_caught(self, report):
        assert report.offframe == 2
        assert set(report.names_for("offframe")) == {
            "past the silica edge", "past the alkali edge"}

    def test_off_the_frame_is_not_missing_data(self, report):
        """A different question with a different answer: one has no
        analysis, the others have a perfectly good one that the diagram
        simply does not reach."""
        assert report.missing == 1
        assert report.names_for("missing") == ["no silica at all"]

    def test_every_sample_is_accounted_for(self, report):
        assert report.plotted + report.dropped == report.total == 4

    def test_the_tally_says_so(self, report):
        assert "off the frame" in report.html()


class TestAReversedAxis:
    """Hastie's Th-Co diagram runs its x axis from 70 down to 0.

    A literal ``low <= value <= high`` against the limits as written
    would exclude every sample on that diagram.
    """

    def test_the_limits_are_read_in_either_order(self):
        values = pd.Series([10.0, 50.0, 90.0])
        forwards = _within(values, (0.0, 70.0))
        backwards = _within(values, (70.0, 0.0))
        assert list(forwards) == list(backwards) == [True, True, False]

    def test_a_sample_inside_a_reversed_frame_still_plots(self, style):
        samples = pd.DataFrame([
            {"Sample": "inside", "Co": 30.0, "Th": 1.0},
            {"Sample": "past the cobalt edge", "Co": 90.0, "Th": 1.0},
        ])
        report = count_for_diagram(get_diagram("hastie_2007_thco"),
                                   samples, samples, style)
        assert report.plotted == 1
        assert report.names_for("offframe") == ["past the cobalt edge"]


class TestAMultiPanelSet:
    """Verma's panels carry the +-8 frame themselves, not the template."""

    BASALT = dict(SiO2=50.5, TiO2=1.15, Al2O3=15.3, Fe2O3=2.0, FeO=6.0,
                  MnO=0.17, MgO=7.6, CaO=11.3, Na2O=2.7, K2O=0.1,
                  P2O5=0.1, V=250.0, Y=28.0, Zr=74.0)

    def test_the_panel_frame_is_what_counts(self, style):
        samples = pd.DataFrame([
            {"Sample": "an ordinary N-MORB", "Nb": 2.33, **self.BASALT},
            {"Sample": "niobium off the scale", "Nb": 1e-4, **self.BASALT},
        ])
        report = count_for_diagram(get_diagram("verma_agrawal_2011"),
                                   samples, samples, style)
        assert report.plotted == 1
        assert report.names_for("offframe") == ["niobium off the scale"]

    def test_the_first_panel_really_is_bounded(self):
        """Guards the assumption above: if the panels ever stopped
        carrying limits this check would quietly do nothing."""
        panels = get_diagram("verma_agrawal_2011").panels
        assert panels[0].x_range == (-8, 8)
        assert panels[0].y_range == (-8, 8)


class TestDiagramsWithoutAFrame:

    def test_an_unbounded_diagram_reports_nothing_off_frame(self, style):
        """Most bivariate plots scale to their data, so every finite
        sample is on the canvas by construction."""
        samples = pd.DataFrame([
            {"Sample": "a", "SiO2": 50.0, "MgO": 8.0},
            {"Sample": "b", "SiO2": 1e6, "MgO": 1e6},
        ])
        report = count_samples(samples, samples,
                               samples["SiO2"], samples["MgO"], style,
                               None, None)
        assert report.offframe == 0
        assert report.plotted == 2

    def test_unbounded_limits_let_everything_through(self):
        values = pd.Series([-1e9, 0.0, 1e9])
        assert list(_within(values, None)) == [True, True, True]


class TestCoverage:

    def test_the_bounded_templates_are_still_bounded(self):
        """If this count moves, the frames moved with it -- worth a
        look rather than a silent change in what gets checked.

        It has moved once, from 24 to 23: `defant_drummond_YbLaYb` gave
        its frame up.  Defant & Drummond do not publish that diagram,
        so there was no figure to take a frame from and the one it had
        was invented.  A template may only fix its limits when a
        published figure fixes them.
        """
        own = [k for k, d in _REGISTRY.items()
               if getattr(d, "x_range", None) or getattr(d, "y_range", None)]
        panelled = [k for k, d in _REGISTRY.items()
                    if getattr(d, "panels", None)
                    and getattr(d.panels[0], "x_range", None)]
        assert len(own) == 23, f"{len(own)} templates carry their own frame"
        assert len(panelled) == 8, f"{len(panelled)} carry it on panels"
        assert "defant_drummond_YbLaYb" not in own

    def test_a_hidden_sample_is_not_also_off_the_frame(self):
        """The categories have to stay disjoint or the total stops
        adding up.  A sample that is both outside the frame and in a
        switched-off group must land in exactly one of them."""
        samples = pd.DataFrame([
            {"Sample": "outside and hidden", "SiO2": 90.0, "Na2O": 2.0,
             "K2O": 1.0, "Group": "Group 2"},
            {"Sample": "inside and shown", "SiO2": 50.0, "Na2O": 2.0,
             "K2O": 1.0, "Group": "Group 1"},
        ])
        style = PlotStyle()
        style.group_columns = ["Group"]
        for group in style.groups:
            group.visible = group.name == "Group 1"

        report = count_for_diagram(get_diagram("tas_volcanic"),
                                   samples, samples, style)
        assert report.hidden == 1
        assert report.offframe == 0, (
            "a hidden sample was counted off the frame as well")
        assert report.plotted + report.dropped == report.total


class TestTheEdgeMarker:
    """The tally says how many samples went off the frame; the marker on
    the canvas says which way each one went.

    Drawn as a hollow triangle pointing outward, in the group's colour,
    so it reads as a direction rather than as a datum sitting on the
    boundary -- a filled point there would claim a composition the
    sample does not have.
    """

    @staticmethod
    def _markers(ax):
        return [line for line in ax.lines
                if line.get_label() == "_offframe"]

    @pytest.fixture
    def tas_figure(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions

        samples = pd.DataFrame([
            {"Sample": "inside", "SiO2": 55.0, "Na2O": 3.0, "K2O": 2.0},
            {"Sample": "right", "SiO2": 95.0, "Na2O": 3.0, "K2O": 2.0},
            {"Sample": "left", "SiO2": 20.0, "Na2O": 3.0, "K2O": 2.0},
            {"Sample": "above", "SiO2": 55.0, "Na2O": 14.0, "K2O": 10.0},
        ])
        figure = plt.figure()
        get_diagram("tas_volcanic").plot(figure, samples, PlotStyle(),
                                         PlotOptions())
        yield figure
        plt.close(figure)

    def test_one_marker_for_each_sample_that_left(self, tas_figure):
        assert len(self._markers(tas_figure.axes[0])) == 3

    def test_each_points_the_way_its_sample_went(self, tas_figure):
        markers = {m.get_marker() for m in self._markers(tas_figure.axes[0])}
        assert markers == {">", "<", "^"}

    def test_they_sit_on_the_frame(self, tas_figure):
        ax = tas_figure.axes[0]
        x_lo, x_hi = sorted(ax.get_xlim())
        y_lo, y_hi = sorted(ax.get_ylim())
        for marker in self._markers(ax):
            x = marker.get_xdata()[0]
            y = marker.get_ydata()[0]
            assert x_lo <= x <= x_hi and y_lo <= y <= y_hi
            assert x in (x_lo, x_hi) or y in (y_lo, y_hi)

    def test_they_are_hollow(self, tas_figure):
        """Open, so nobody reads one as a sample plotting on the edge."""
        for marker in self._markers(tas_figure.axes[0]):
            assert marker.get_markerfacecolor() == "none"

    def test_they_stay_out_of_the_legend(self, tas_figure):
        _handles, labels = tas_figure.axes[0].get_legend_handles_labels()
        assert not any(label == "_offframe" for label in labels)

    def test_a_reference_point_is_never_marked(self):
        """Templates label their sample scatter with the group name and
        leave reference compositions unlabelled, which is the whole
        basis for telling them apart.  Marking a reference as a stray
        sample would be a worse lie than the silence this replaces."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions

        figure = plt.figure()
        samples = pd.DataFrame([
            {"Sample": "x", "Th": 1.2, "Nb": 18.0, "Yb": 2.0,
             "TiO2": 1.15, "Y": 26.0},
        ])
        get_diagram("pearce2008_thyb_nbyb").plot(
            figure, samples, PlotStyle(), PlotOptions())
        labelled = [c for c in figure.axes[0].collections
                    if not (c.get_label() or "").startswith("_")]
        unlabelled = [c for c in figure.axes[0].collections
                      if (c.get_label() or "").startswith("_")]
        assert labelled, "no sample scatter to tell apart"
        assert unlabelled, "no reference points on this diagram any more"
        plt.close(figure)

    def test_a_multi_panel_set_marks_each_panel(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions

        basalt = dict(SiO2=50.5, TiO2=1.15, Al2O3=15.3, Fe2O3=2.0, FeO=6.0,
                      MnO=0.17, MgO=7.6, CaO=11.3, Na2O=2.7, K2O=0.1,
                      P2O5=0.1, V=250.0, Y=28.0, Zr=74.0)
        samples = pd.DataFrame([
            {"Sample": "ordinary", "Nb": 2.33, **basalt},
            {"Sample": "absurd", "Nb": 1e-4, **basalt},
        ])
        figure = plt.figure()
        get_diagram("verma_agrawal_2011").plot(
            figure, samples, PlotStyle(), PlotOptions())
        marked = sum(1 for ax in figure.axes if self._markers(ax))
        assert marked >= 3, (
            f"only {marked} of {len(figure.axes)} panels flagged it")
        plt.close(figure)

    def test_an_unbounded_diagram_draws_none(self):
        """Nothing can be outside an axis that was scaled to the data.

        Frost's diagram is one of the 20 templates that scale to what
        they are given, so its canvas should carry no edge markers
        however extreme the samples are.
        """
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions

        diagram = get_diagram("frost")
        assert not diagram.x_range and not diagram.y_range, (
            "this template gained a fixed frame; pick another")
        samples = pd.DataFrame([
            {"Sample": "a", "SiO2": 50.0, "FeO": 8.0, "Fe2O3": 2.0,
             "MgO": 8.0, "CaO": 11.0, "Na2O": 2.5, "K2O": 0.5},
            {"Sample": "b", "SiO2": 78.0, "FeO": 0.5, "Fe2O3": 0.2,
             "MgO": 0.1, "CaO": 0.3, "Na2O": 4.5, "K2O": 5.0},
        ])
        figure = plt.figure()
        diagram.plot(figure, samples, PlotStyle(), PlotOptions())
        assert all(self._markers(ax) == [] for ax in figure.axes)
        plt.close(figure)
