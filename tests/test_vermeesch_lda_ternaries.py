"""Vermeesch's three log-ratio LDA ternaries, computed rather than traced.

These diagrams were drawn envelopes: polygons typed in ternary percent,
approximating curves by eye.  They do not need to be.  Vermeesch (2006a)
runs a linear discriminant analysis in log-ratio space, where the
decision boundaries come out straight, and maps them back to the
ternary, where "the transformed decision boundaries are no longer
linear, but curved".  His Table 6 gives four anchor points per diagram
in log-ratio coordinates -- node 3 the triple point, nodes 1, 2 and 4
the three ray ends -- which is everything needed to rebuild them.

Three things this pins that nothing else would catch:

* **The base of the logarithm.** The paper writes "log" throughout and
  never says which.  It is natural: read off Figure 42a, whose training
  clusters sit at roughly x[0, 0.5] y[-1, -0.5] for MORB, x[-1, 0]
  y[0, 0.7] for OIB and x[0.3, 1.3] y[0.5, 1.8] for IAB, natural logs
  put a reference N-MORB at (0.31, -0.45), an OIB at (-0.67, 0.42) and
  an IAB at (0.57, 0.95) -- each in its own cluster -- while base ten
  gives (0.14, -0.20), (-0.29, 0.18) and (0.25, 0.41), all pulled
  toward the origin and two of the three outside their cluster.

  That reasoning stays here rather than becoming an assertion: the
  cluster windows are read by eye and the N-MORB reference sits close
  enough to an edge that the test would have turned on a hundredth.
  What is asserted instead is that base ten misclassifies, which it
  does -- though only taken over all three diagrams at once, since on
  Si-Ti-Sr these particular references keep their sectors either way.
* **Which apex is which.** The previous implementation put Si/1000 at
  the top of the Si-Ti-Sr triangle where Figure 42b has Ti/40, and a
  ternary read with its corners permuted is not the published diagram.
* **That the boundaries curve.** Straight lines between the same anchor
  points would look close enough to pass a glance and be wrong
  everywhere except at the nodes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

import birds.diagrams.templates.tectonic_ternary as ternary
from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import ternary_to_xy

#: label -> (diagram key, spec), for the three rebuilt here.
SETS = {
    "Si-Ti-Sr": ("vermeesch_SiTiSr", ternary._LDA_SI_TI_SR),
    "Eu-Lu-Sr": ("vermeesch_EuLuSr", ternary._LDA_EU_LU_SR),
    "Ti-V-Sc": ("vermeesch_VTiSc", ternary._LDA_TI_V_SC),
}

#: Reference compositions, majors in wt.% and traces in ppm.  Ordinary
#: values for the three settings, not anything tuned to pass.
REFERENCE = pd.DataFrame([
    {"Sample": "N-MORB", "SiO2": 50.5, "TiO2": 1.15, "Sr": 110.0,
     "Eu": 1.2, "Lu": 0.46, "V": 250.0, "Sc": 40.0},
    {"Sample": "OIB", "SiO2": 47.5, "TiO2": 2.9, "Sr": 660.0,
     "Eu": 2.0, "Lu": 0.27, "V": 283.0, "Sc": 32.0},
    {"Sample": "IAB", "SiO2": 51.0, "TiO2": 0.9, "Sr": 350.0,
     "Eu": 1.0, "Lu": 0.30, "V": 290.0, "Sc": 38.0},
])

EXPECTED_FIELD = {"N-MORB": "MORB", "OIB": "OIB", "IAB": "IAB"}


def _field_at(spec, x, y):
    """Which field owns the log-ratio point (x, y)."""
    cx, cy = spec["triple"]

    def angle(point):
        return np.arctan2(point[1] - cy, point[0] - cx)

    edges = [(angle(end), set(pair)) for end, pair in spec["boundaries"]]
    here = angle((x, y))
    for name in sorted({n for _a, pair in edges for n in pair}):
        limits = sorted(a for a, pair in edges if name in pair)
        if len(limits) != 2:
            continue
        low, high = limits
        inside = ((low <= here <= high) if (high - low) <= np.pi
                  else not (low < here < high))
        if inside:
            return name
    return None


def _log_ratios(key, frame, log=np.log):
    top, left, right = get_diagram(key)._abc(frame)
    return log(left / top), log(right / top)


class TestTheAnchorPoints:
    """Transcribed from Table 6; node 3 is the triple point."""

    PUBLISHED = {
        "Si-Ti-Sr": {"triple": (-0.05, 0.39),
                     "nodes": {(-1.26, -2.15), (-0.2, 2.98), (2.0, -0.77)}},
        "Eu-Lu-Sr": {"triple": (0.03, 1.0),
                     "nodes": {(-1.23, -1.0), (0.5, 2.33), (-0.61, -5.0)}},
        "Ti-V-Sc": {"triple": (0.57, -0.39),
                    "nodes": {(-2.0, -0.54), (1.1, 2.0), (2.0, -1.41)}},
    }

    @pytest.mark.parametrize("label", sorted(SETS))
    def test_the_triple_point(self, label):
        _key, spec = SETS[label]
        assert spec["triple"] == self.PUBLISHED[label]["triple"]

    @pytest.mark.parametrize("label", sorted(SETS))
    def test_the_three_ray_ends(self, label):
        _key, spec = SETS[label]
        ends = {tuple(end) for end, _pair in spec["boundaries"]}
        assert ends == self.PUBLISHED[label]["nodes"]

    @pytest.mark.parametrize("label", sorted(SETS))
    def test_three_fields_meet_at_the_triple_point(self, label):
        """Each boundary separates two of the three, and each field is
        bounded by exactly two of them."""
        _key, spec = SETS[label]
        fields = [f for _e, pair in spec["boundaries"] for f in pair]
        assert set(fields) == {"IAB", "MORB", "OIB"}
        for name in set(fields):
            assert fields.count(name) == 2, name


class TestReferenceBasalts:

    @pytest.mark.parametrize("label", sorted(SETS))
    def test_each_lands_in_its_own_field(self, label):
        key, spec = SETS[label]
        xs, ys = _log_ratios(key, REFERENCE)
        for name, x, y in zip(REFERENCE["Sample"], xs, ys):
            got = _field_at(spec, float(x), float(y))
            assert got == EXPECTED_FIELD[name], (
                f"{label}: {name} at ({x:.2f}, {y:.2f}) -> {got}")

    def test_all_nine_assignments_are_right(self):
        """Three references on three diagrams, and nothing may miss."""
        wrong = []
        for label, (key, spec) in SETS.items():
            xs, ys = _log_ratios(key, REFERENCE)
            for name, x, y in zip(REFERENCE["Sample"], xs, ys):
                if _field_at(spec, float(x), float(y)) != EXPECTED_FIELD[name]:
                    wrong.append(f"{label}/{name}")
        assert wrong == []

    def test_base_ten_does_not_work(self):
        """The paper writes "log" throughout and never says which.

        Stated over all three diagrams rather than one at a time,
        because that is as much as the evidence supports: on Si-Ti-Sr
        these three references happen to stay in their sectors under
        base ten as well, since shrinking every coordinate toward the
        triple point does not always cross a boundary.  Collectively it
        does fail, and on the published figures the difference is
        plainer still -- under natural logs the references sit inside
        their own clouds, under base ten they huddle near the origin
        outside them.
        """
        wrong = []
        for label, (key, spec) in SETS.items():
            xs, ys = _log_ratios(key, REFERENCE, log=np.log10)
            for name, x, y in zip(REFERENCE["Sample"], xs, ys):
                if _field_at(spec, float(x), float(y)) != EXPECTED_FIELD[name]:
                    wrong.append(f"{label}/{name}")
        assert wrong, "base ten classifies all nine just as well"


class TestTheApices:
    """Figures 42b, 43b and 44b, which corner carries which quantity.

    The frame helper puts the first apex at the top.
    """

    EXPECTED = {
        "vermeesch_SiTiSr": ("Ti/40", "Si/1000", "Sr"),
        "vermeesch_EuLuSr": ("500 Lu", "100 Eu", "Sr"),
        "vermeesch_VTiSc": ("Ti/50", "V", "5 Sc"),
    }

    @pytest.mark.parametrize("key", sorted(EXPECTED))
    def test_the_published_corner_order(self, key):
        assert get_diagram(key).apices == self.EXPECTED[key]

    def test_the_top_apex_is_the_log_ratio_denominator(self):
        """Both axes of Table 6 divide by the top apex, which is what
        makes the pair an ordinary additive log-ratio."""
        frame = REFERENCE.iloc[[0]]
        top, left, right = get_diagram("vermeesch_VTiSc")._abc(frame)
        # Table 6 writes these as ln(50 V / Ti) and ln(250 Sc / Ti).
        ti = frame["TiO2"].iloc[0] * ternary._TI_WT_TO_PPM
        assert float(left.iloc[0] / top.iloc[0]) == pytest.approx(
            50.0 * frame["V"].iloc[0] / ti)
        assert float(right.iloc[0] / top.iloc[0]) == pytest.approx(
            250.0 * frame["Sc"].iloc[0] / ti)


class TestTheInverseTransform:

    def test_it_returns_a_composition(self):
        rng = np.random.default_rng(20261002)
        x = rng.uniform(-8, 8, 500)
        y = rng.uniform(-8, 8, 500)
        a, b, c = ternary._inverse_logratio(x, y)
        assert np.allclose(a + b + c, 1.0)
        assert (a > 0).all() and (b > 0).all() and (c > 0).all()

    def test_it_undoes_the_log_ratio(self):
        x = np.array([-3.0, 0.0, 0.5, 4.0])
        y = np.array([2.0, 0.0, -1.5, -6.0])
        a, b, c = ternary._inverse_logratio(x, y)
        assert np.allclose(np.log(b / a), x)
        assert np.allclose(np.log(c / a), y)

    def test_a_far_point_does_not_overflow(self):
        """Boundaries are walked 40 log-ratio units out, where a naive
        exp() would have overflowed long before."""
        a, b, c = ternary._inverse_logratio(
            np.array([700.0]), np.array([-700.0]))
        assert np.isfinite([a, b, c]).all()
        assert np.isclose(a + b + c, 1.0)


class TestTheBoundaries:

    @pytest.mark.parametrize("label", sorted(SETS))
    def test_they_start_at_the_triple_point(self, label):
        _key, spec = SETS[label]
        a, b, c = ternary._inverse_logratio(*(np.array([v]) for v in
                                              spec["triple"]))
        want_x, want_y = ternary_to_xy(pd.Series(a), pd.Series(b),
                                       pd.Series(c))
        for end, _pair in spec["boundaries"]:
            xs, ys = ternary._lda_boundary_xy(spec["triple"], end)
            assert float(xs.iloc[0]) == pytest.approx(float(want_x.iloc[0]))
            assert float(ys.iloc[0]) == pytest.approx(float(want_y.iloc[0]))

    @pytest.mark.parametrize("label", sorted(SETS))
    def test_they_stay_inside_the_triangle(self, label):
        _key, spec = SETS[label]
        for end, _pair in spec["boundaries"]:
            xs, ys = ternary._lda_boundary_xy(spec["triple"], end)
            assert (ys >= -1e-9).all()
            # The two slanted sides, as y <= sqrt(3) x and
            # y <= sqrt(3) (1 - x).
            assert (ys <= np.sqrt(3) * xs + 1e-9).all()
            assert (ys <= np.sqrt(3) * (1.0 - xs) + 1e-9).all()

    @pytest.mark.parametrize("label", sorted(SETS))
    def test_they_curve(self, label):
        """Straight in log-ratio space, curved here -- the reason the
        hand-drawn polygons they replace could never have been right.

        Measured as the gap between the path and the straight chord
        joining its ends, relative to the chord.
        """
        _key, spec = SETS[label]
        bends = []
        for end, _pair in spec["boundaries"]:
            xs, ys = ternary._lda_boundary_xy(spec["triple"], end)
            x0, y0 = float(xs.iloc[0]), float(ys.iloc[0])
            x1, y1 = float(xs.iloc[-1]), float(ys.iloc[-1])
            chord = np.hypot(x1 - x0, y1 - y0)
            if chord < 1e-9:
                continue
            away = np.abs((x1 - x0) * (y0 - ys) - (x0 - xs) * (y1 - y0))
            bends.append(float(np.max(away) / chord))
        assert max(bends) > 0.02, (
            f"{label}: the widest boundary departs from its chord by "
            f"{max(bends):.4f} of its length, which is a straight line")


class TestTheDiagramsStillDraw:

    @pytest.mark.parametrize("label", sorted(SETS))
    def test_a_figure_comes_out_with_boundaries_and_labels(self, label):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle

        key, _spec = SETS[label]
        figure = plt.figure()
        get_diagram(key).plot(figure, REFERENCE, PlotStyle(), PlotOptions())
        ax = figure.axes[0]
        labelled = {t.get_text() for t in ax.texts}
        assert {"IAB", "MORB", "OIB"} <= labelled
        assert any(len(line.get_xdata()) > 50 for line in ax.lines), (
            "no sampled boundary curve on the canvas")
        plt.close(figure)

    def test_a_dataset_without_the_elements_draws_nothing(self):
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle

        figure = plt.figure()
        get_diagram("vermeesch_EuLuSr").plot(
            figure, pd.DataFrame({"SiO2": [50.0]}), PlotStyle(),
            PlotOptions())
        points = [c for c in figure.axes[0].collections
                  if len(c.get_offsets())]
        assert not points
        plt.close(figure)


class TestWood:
    """Th-Hf/3-Ta, with Vermeesch's LDA in place of Wood's eye-drawn
    fields -- and one anchor point used against what Table 6 prints.

    The table gives node 2 as (1.43, -1.5).  That puts it diagonally
    opposite where Figure 41b draws it, and sends a reference N-MORB
    into the OIB field.  Measuring the figure settles it: the four
    numbered discs were detected in a render of panel (b) and the axes
    calibrated on nodes 1, 3 and 4, which do agree with the table.  That
    calibration reproduces node 3 as (-0.076, -0.864) against a
    published (-0.07, -0.86), and puts node 2 at (-1.44, +1.50) -- the
    printed magnitudes to a hundredth, with both signs reversed.
    """

    SPEC = ternary._LDA_TH_TA_HF

    REFERENCE = pd.DataFrame([
        {"Sample": "N-MORB", "Th": 0.12, "Ta": 0.132, "Hf": 2.05},
        {"Sample": "OIB", "Th": 4.00, "Ta": 2.70, "Hf": 7.80},
        {"Sample": "IAB", "Th": 2.00, "Ta": 0.18, "Hf": 1.80},
    ])

    def test_the_three_anchors_that_agree_with_the_table(self):
        assert self.SPEC["triple"] == (-0.07, -0.86)
        ends = {tuple(end) for end, _pair in self.SPEC["boundaries"]}
        assert (-1.49, -2.48) in ends
        assert (2.81, 1.0) in ends

    def test_node_two_is_used_with_its_signs_reversed(self):
        ends = {tuple(end) for end, _pair in self.SPEC["boundaries"]}
        assert (-1.43, 1.5) in ends, "the measured position"
        assert (1.43, -1.5) not in ends, "the printed position"

    @pytest.mark.parametrize("name", ["N-MORB", "OIB", "IAB"])
    def test_reference_basalts_land_in_their_own_field(self, name):
        xs, ys = _log_ratios("wood_1980_ThHfTa", self.REFERENCE)
        index = list(self.REFERENCE["Sample"]).index(name)
        got = _field_at(self.SPEC, float(xs.iloc[index]),
                        float(ys.iloc[index]))
        assert got == name.replace("N-", "")

    def test_the_printed_node_would_misclassify(self):
        """Guards the correction: it has to still matter.

        With node 2 as printed, the ray that should separate MORB from
        OIB points the other way and N-MORB is swept into OIB.
        """
        as_printed = {
            "triple": self.SPEC["triple"],
            "boundaries": tuple(
                (((1.43, -1.5) if tuple(end) == (-1.43, 1.5) else end), pair)
                for end, pair in self.SPEC["boundaries"]),
        }
        xs, ys = _log_ratios("wood_1980_ThHfTa", self.REFERENCE)
        index = list(self.REFERENCE["Sample"]).index("N-MORB")
        assert _field_at(as_printed, float(xs.iloc[index]),
                         float(ys.iloc[index])) != "MORB"

    def test_the_apices_match_the_figure(self):
        """Figure 41a and 41d put Hf/3 at the top, Th bottom-left and Ta
        bottom-right."""
        assert get_diagram("wood_1980_ThHfTa").apices == ("Hf/3", "Th", "Ta")

    def test_the_axes_divide_by_the_top_apex(self):
        frame = self.REFERENCE.iloc[[1]]
        top, left, right = get_diagram("wood_1980_ThHfTa")._abc(frame)
        assert float(left.iloc[0] / top.iloc[0]) == pytest.approx(
            3.0 * frame["Th"].iloc[0] / frame["Hf"].iloc[0])
        assert float(right.iloc[0] / top.iloc[0]) == pytest.approx(
            3.0 * frame["Ta"].iloc[0] / frame["Hf"].iloc[0])
