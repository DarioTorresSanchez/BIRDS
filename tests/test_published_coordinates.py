"""Diagrams whose boundaries are published as coordinate lists.

Rollinson & Pease (2021) print the plotting coordinates for several of
these diagrams in the figure captions themselves, and Table 3.10 gives
the haplogranite minima and eutectics outright.  None of this needs
measuring: the numbers below are transcribed from those captions and
that table, and each test asserts the module carries them exactly.

Where the source stops, so do we.  A boundary carried past its
published range is an extrapolation, and is marked as one rather than
quietly extended.
"""

from __future__ import annotations

import pytest

from birds.diagrams.templates.afm import _AFM_BOUNDARY
from birds.diagrams.templates.haplogranite import _MIN_EUT
from birds.diagrams.templates.ib1971 import (
    _IRVINE_BARAGAR_1971,
    _KUNO_1966,
    _MACDONALD_1968,
)
from birds.diagrams.templates.jensen import _TH_CA_BOUNDARY
from birds.diagrams.templates.k2o_sio2 import (
    LM89_LINES,
    LM89_SIO2_MIN,
    RICKWOOD_BANDS,
)
from birds.diagrams.templates.tas import _IB1971_BOUNDARY


def pairs(seq):
    return [tuple(float(v) for v in p) for p in seq]


class TestAlkalicBoundaries:
    """Rollinson & Pease (2021) Figure 3.3 caption."""

    IRVINE_BARAGAR = [
        (39.2, 0.0), (40.0, 0.4), (43.2, 2.0), (45.0, 2.8), (48.0, 4.0),
        (50.0, 4.75), (53.7, 6.0), (55.0, 6.4), (60.0, 8.0), (65.0, 9.6),
        (66.4, 10.0)]
    KUNO = [
        (45.85, 2.75), (46.85, 3.0), (50.0, 3.9), (50.3, 4.0), (53.1, 5.0),
        (55.0, 5.8), (55.6, 6.0), (60.0, 6.8), (61.5, 7.0), (65.0, 7.35),
        (70.0, 7.85), (71.6, 8.0), (75.0, 8.3), (76.4, 8.4)]
    MACDONALD = [(39.8, 0.35), (65.5, 9.7)]

    def test_irvine_and_baragar(self):
        assert pairs(_IRVINE_BARAGAR_1971) == self.IRVINE_BARAGAR

    def test_kuno(self):
        assert pairs(_KUNO_1966) == self.KUNO

    def test_macdonald_is_a_straight_line(self):
        assert pairs(_MACDONALD_1968) == self.MACDONALD

    def test_the_tas_panel_draws_the_same_curve(self):
        """It used to keep a second copy that had drifted to (65, 8.8)
        and (77.4, 10) — an error of 1 wt.% alkalis near SiO2 66, which
        is enough to call an alkaline trachyte sub-alkaline."""
        assert _IB1971_BOUNDARY is _IRVINE_BARAGAR_1971

    def test_the_curves_rise_monotonically(self):
        for curve in (_IRVINE_BARAGAR_1971, _KUNO_1966):
            xs = [p[0] for p in curve]
            ys = [p[1] for p in curve]
            assert xs == sorted(xs)
            assert ys == sorted(ys)

    def test_kuno_lies_below_irvine_and_baragar_where_they_overlap(self):
        """Kuno's boundary encloses a smaller tholeiitic field."""
        import numpy as np
        for x in np.linspace(48.0, 65.0, 18):
            k = np.interp(x, [p[0] for p in _KUNO_1966],
                          [p[1] for p in _KUNO_1966])
            ib = np.interp(x, [p[0] for p in _IRVINE_BARAGAR_1971],
                           [p[1] for p in _IRVINE_BARAGAR_1971])
            assert k < ib, x


class TestJensen:
    """Figure 3.8b caption — the tholeiitic / calc-alkalic boundary."""

    BOUNDARY = [
        (90, 10, 0), (53.5, 28.5, 18), (52.5, 29, 18.5), (51.5, 29, 19.5),
        (50.5, 27.5, 22), (50.3, 25, 24.7), (50.8, 20, 29.2),
        (51.5, 12.5, 36)]

    def test_matches_the_published_coordinates(self):
        assert pairs(_TH_CA_BOUNDARY) == pairs(self.BOUNDARY)

    def test_every_vertex_sums_to_a_hundred(self):
        for v in _TH_CA_BOUNDARY:
            assert sum(v) == pytest.approx(100.0, abs=0.05), v

    def test_it_is_the_only_boundary_the_caption_gives(self):
        """The caption prints this one curve; the remaining Jensen
        subdivisions are not tabulated and are not invented here."""
        assert len(_TH_CA_BOUNDARY) == 8


class TestAfm:
    """Figure 3.18b caption — the boundary the book recommends."""

    CURVE = [(11, 39, 50), (14, 50, 36), (18, 56, 26),
             (28, 52, 20), (40, 45, 15), (70, 26, 4)]

    def test_matches_the_published_coordinates(self):
        assert pairs(_AFM_BOUNDARY) == pairs(self.CURVE)

    def test_every_vertex_sums_to_a_hundred(self):
        for v in _AFM_BOUNDARY:
            assert sum(v) == pytest.approx(100.0, abs=0.05), v

    def test_it_runs_from_the_magnesian_to_the_alkali_corner(self):
        assert _AFM_BOUNDARY[0][2] > _AFM_BOUNDARY[-1][2]
        assert _AFM_BOUNDARY[0][0] < _AFM_BOUNDARY[-1][0]


class TestK2OSiO2:
    """Figure 3.4 caption prints every plotting parameter."""

    def test_le_maitre_lines(self):
        assert LM89_LINES["medium-K / high-K"] == ((48.0, 1.2), (68.0, 3.1))
        assert LM89_LINES["low-K / medium-K"] == ((48.0, 0.3), (68.0, 1.2))

    def test_le_maitre_vertical(self):
        assert LM89_SIO2_MIN == 48.0

    def test_all_three_rickwood_bands_are_present(self):
        """The module used to carry one of the three, as a single line."""
        assert set(RICKWOOD_BANDS) == {
            "shoshonitic / high-K", "high-K / calc-alkalic",
            "calc-alkalic / low-K"}

    @pytest.mark.parametrize("name,upper,lower", [
        ("shoshonitic / high-K",
         [(45.0, 1.38), (48.0, 1.7), (56.0, 3.3), (63.0, 4.2), (70.0, 5.1)],
         [(45.0, 1.37), (48.0, 1.6), (56.0, 2.98), (63.0, 3.87),
          (70.0, 4.61)]),
        ("high-K / calc-alkalic",
         [(45.0, 0.98), (49.0, 1.28), (52.0, 1.5), (63.0, 2.48),
          (70.0, 3.1), (75.0, 3.43)],
         [(45.0, 0.92), (49.0, 1.1), (52.0, 1.35), (63.0, 2.32),
          (70.0, 2.86), (75.0, 3.25)]),
        ("calc-alkalic / low-K",
         [(45.0, 0.2), (48.0, 0.41), (61.0, 0.97), (70.0, 1.38),
          (75.0, 1.51)],
         [(45.0, 0.15), (48.0, 0.3), (61.0, 0.8), (70.0, 1.23),
          (75.0, 1.44)]),
    ])
    def test_band_bounds(self, name, upper, lower):
        got_upper, got_lower = RICKWOOD_BANDS[name]
        assert pairs(got_upper) == pairs(upper)
        assert pairs(got_lower) == pairs(lower)

    def test_the_first_shoshonite_point_is_not_rounded(self):
        """It was carried as 1.4; the caption prints 1.38."""
        assert RICKWOOD_BANDS["shoshonitic / high-K"][0][0] == (45.0, 1.38)

    def test_each_band_is_sampled_at_the_same_silica_values(self):
        """Otherwise the shaded band between them is meaningless."""
        for name, (upper, lower) in RICKWOOD_BANDS.items():
            assert [p[0] for p in upper] == [p[0] for p in lower], name

    def test_the_upper_bound_is_above_the_lower_one(self):
        for name, (upper, lower) in RICKWOOD_BANDS.items():
            for u, low in zip(upper, lower):
                assert u[1] >= low[1], (name, u)

    def test_the_bands_never_cross(self):
        import numpy as np
        order = ["calc-alkalic / low-K", "high-K / calc-alkalic",
                 "shoshonitic / high-K"]
        for x in np.linspace(49.0, 70.0, 22):
            tops = [np.interp(x, [p[0] for p in RICKWOOD_BANDS[n][0]],
                              [p[1] for p in RICKWOOD_BANDS[n][0]])
                    for n in order]
            assert tops == sorted(tops), x


class TestHaplogranite:
    """Table 3.10, water-saturated entries (X H2O = 1.00)."""

    #: (pressure kb, Ab, Or, Q, kind) as the table prints them.
    TABLE = {
        (0.5, 30, 30, 40, "min"), (1.0, 33, 29, 38, "min"),
        (2.0, 39, 26, 35, "min"), (3.0, 42, 25, 33, "min"),
        (5.0, 47, 22, 31, "eut"), (10.0, 56, 21, 23, "eut"),
        (20.0, 63, 19, 18, "eut"), (30.0, 67, 18, 15, "eut"),
    }

    def test_every_point_is_in_the_published_table(self):
        got = {(float(p), ab, orx, q, kind)
               for ab, orx, q, p, kind in _MIN_EUT}
        assert got == self.TABLE

    def test_every_point_sums_to_a_hundred(self):
        for ab, orx, q, _p, _k in _MIN_EUT:
            assert ab + orx + q == 100

    def test_pressures_are_in_order(self):
        ps = [p for _a, _o, _q, p, _k in _MIN_EUT]
        assert ps == sorted(ps)

    def test_albite_rises_with_pressure(self):
        """The minimum migrates towards albite as pressure climbs — the
        trend the diagram exists to show."""
        ab = [a for a, _o, _q, _p, _k in _MIN_EUT]
        assert ab == sorted(ab)

    def test_minima_give_way_to_eutectics(self):
        kinds = [k for _a, _o, _q, _p, k in _MIN_EUT]
        assert kinds == sorted(kinds, key=lambda k: k != "min")


# ==========================================================================
# Published equations
# ==========================================================================

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from birds.diagrams.registry import get_diagram  # noqa: E402
from birds.diagrams.templates.frost import (  # noqa: E402
    FE_INDEX_INTERCEPT,
    FE_INDEX_SLOPE,
    MALI_BOUNDARIES,
    MALI_LABELS,
)
from birds.diagrams.templates.major_df import (  # noqa: E402
    BUTLER_WORONOW_DENOMINATOR,
    BUTLER_WORONOW_DF1,
    BUTLER_WORONOW_DF2,
    BUTLER_WORONOW_PARTS,
    PEARCE_1976_DENOMINATOR,
    PEARCE_1976_DF1,
    PEARCE_1976_DF2,
    PEARCE_1976_FIELDS,
    PEARCE_1976_PARTS,
    TIO2_WT_TO_TI_PPM,
)
from birds.diagrams.templates.tectonic_bivariate import (  # noqa: E402
    TIO2_WT_TO_TI_PPM as TIV_CONVERSION,
)

#: Reference basalts, ppm for traces and wt.% for oxides.
REFERENCE_BASALTS = {
    "N-MORB": dict(Zr=74, Y=28, Sr=90, TiO2=1.15, SiO2=50.5, Al2O3=15.3,
                   CaO=11.3, MgO=7.6, MnO=0.17, K2O=0.10, Na2O=2.7),
    "OIB": dict(Zr=280, Y=29, Sr=660, TiO2=2.87, SiO2=47.0, Al2O3=15.8,
                CaO=10.0, MgO=6.5, MnO=0.17, K2O=1.20, Na2O=3.5),
    "IAB": dict(Zr=60, Y=22, Sr=400, TiO2=0.90, SiO2=51.0, Al2O3=17.5,
                CaO=10.5, MgO=5.5, MnO=0.16, K2O=0.60, Na2O=2.8),
}


class TestTitaniumConversion:
    def test_one_per_cent_titania_in_parts_per_million(self):
        """47.867 / 79.866 by mass.  Both modules must agree."""
        assert TIO2_WT_TO_TI_PPM == pytest.approx(5993.4, abs=0.1)
        assert TIV_CONVERSION == TIO2_WT_TO_TI_PPM

    def test_it_is_the_mass_ratio(self):
        assert TIO2_WT_TO_TI_PPM == pytest.approx(
            47.867 / 79.866 * 10000, abs=0.5)


class TestShervaisRatioLines:
    """Ti/V rays are arithmetic, not a measurement — x is Ti/1000."""

    @pytest.mark.parametrize("tio2,ratio", [
        (1.5, 30.0), (1.0, 10.0), (2.0, 50.0), (0.8, 20.0), (3.0, 100.0),
    ])
    def test_the_axes_give_the_intended_ratio(self, tio2, ratio):
        """V is chosen to give the target Ti/V exactly, so this checks
        the module's own conversion rather than a typed-in number."""
        v = tio2 * TIV_CONVERSION / ratio
        d = get_diagram("shervais_1982_TiV")
        x, y = d._compute_xy(pd.DataFrame([{"TiO2": tio2, "V": v}]))
        assert float(x.iloc[0]) * 1000 / float(y.iloc[0]) == pytest.approx(
            ratio, rel=1e-9)

    def test_titanium_reported_as_an_element_is_used_directly(self):
        d = get_diagram("shervais_1982_TiV")
        x, _y = d._compute_xy(pd.DataFrame([{"Ti": 9000.0, "V": 300.0}]))
        assert float(x.iloc[0]) == pytest.approx(9.0)


class TestFrostIndices:
    def test_the_fe_index_boundary_is_the_published_equation(self):
        """Frost & Frost (2008): Fe-index = 0.46 + 0.005 SiO2."""
        assert FE_INDEX_INTERCEPT == 0.46
        assert FE_INDEX_SLOPE == 0.005

    def test_the_fe_index_boundary_spans_a_plausible_range(self):
        for sio2, want in ((50, 0.71), (70, 0.81)):
            assert FE_INDEX_INTERCEPT + FE_INDEX_SLOPE * sio2 == \
                pytest.approx(want, abs=0.005)

    def test_all_three_mali_boundaries_are_present(self):
        assert set(MALI_BOUNDARIES) == {
            "alkalic / alkali-calcic", "alkali-calcic / calc-alkalic",
            "calc-alkalic / calcic"}

    def test_the_mali_boundaries_are_curved_not_straight(self):
        """They were three straight lines between invented endpoints."""
        for name, poly in MALI_BOUNDARIES.items():
            xs = np.array([p[0] for p in poly])
            ys = np.array([p[1] for p in poly])
            straight = np.interp(xs, [xs[0], xs[-1]], [ys[0], ys[-1]])
            assert np.abs(ys - straight).max() > 0.2, name

    def test_the_mali_boundaries_never_cross(self):
        order = ["calc-alkalic / calcic", "alkali-calcic / calc-alkalic",
                 "alkalic / alkali-calcic"]
        for x in np.linspace(52.0, 74.0, 23):
            vals = [np.interp(x, [p[0] for p in MALI_BOUNDARIES[n]],
                              [p[1] for p in MALI_BOUNDARIES[n]])
                    for n in order]
            assert vals == sorted(vals), x

    def test_the_mali_boundaries_all_rise_with_silica(self):
        for name, poly in MALI_BOUNDARIES.items():
            ys = [p[1] for p in poly]
            assert ys == sorted(ys), name

    def test_every_mali_field_is_named(self):
        assert set(MALI_LABELS) == {"alkalic", "alkali-calcic",
                                    "calc-alkalic", "calcic"}


class TestOceanicBasaltDiscriminants:
    """Appendix 5.1, Axes for Figure 5.5 (Vermeesch 2006a)."""

    def test_pearce_carries_no_iron_term(self):
        """The diagram is named 'major element oxides (without FeO)'.
        The old implementation had an Fe2O3t term and no MnO."""
        assert "MnO" in PEARCE_1976_PARTS
        assert not [p for p in PEARCE_1976_PARTS if "Fe" in p]

    def test_pearce_parts_and_denominator(self):
        assert PEARCE_1976_PARTS == ("Al2O3", "TiO2", "CaO", "MgO", "MnO",
                                     "K2O", "Na2O")
        assert PEARCE_1976_DENOMINATOR == "SiO2"

    def test_pearce_coefficients(self):
        assert PEARCE_1976_DF1 == (0.555, 3.822, 0.522, 1.293, -0.531,
                                   -0.145, -0.399)
        assert PEARCE_1976_DF2 == (3.796, 0.008, -2.868, 0.313, 0.650,
                                   1.421, -3.017)

    def test_butler_woronow_divides_everything_by_titanium(self):
        """The old implementation used SiO2 and Sr as denominators."""
        assert BUTLER_WORONOW_PARTS == ("Zr", "Y", "Sr")
        assert BUTLER_WORONOW_DENOMINATOR == "Ti"

    def test_butler_woronow_coefficients(self):
        assert BUTLER_WORONOW_DF1 == (0.016, -2.961, 1.500)
        assert BUTLER_WORONOW_DF2 == (1.474, 2.143, 1.840)

    def test_the_published_sr_coefficient_is_not_an_intercept(self):
        """1.840 was carried as an additive constant; it is the Sr
        coefficient of DF2."""
        assert BUTLER_WORONOW_DF2[2] == 1.840

    def test_neither_function_has_a_constant_term(self):
        """The appendix prints none, and reference basalts land in
        their fields without one."""
        d = get_diagram("pearce_1976_DF")
        comp = REFERENCE_BASALTS["N-MORB"]
        xs, _ys = d._compute_xy(pd.DataFrame([comp]))
        by_hand = sum(
            c * np.log(comp[p] / comp["SiO2"])
            for c, p in zip(PEARCE_1976_DF1, PEARCE_1976_PARTS))
        assert float(xs.iloc[0]) == pytest.approx(by_hand)

    @pytest.mark.parametrize("rock,field", [
        ("N-MORB", "MORB"), ("OIB", "OIB"), ("IAB", "IAB")])
    def test_reference_basalts_land_in_their_field(self, rock, field):
        """The strongest check available: equations, boundaries and real
        compositions have to agree at once."""
        d = get_diagram("pearce_1976_DF")
        xs, ys = d._compute_xy(pd.DataFrame([REFERENCE_BASALTS[rock]]))
        x, y = float(xs.iloc[0]), float(ys.iloc[0])
        cx, cy = PEARCE_1976_FIELDS["centre"]
        # The named field's label must be the nearest of the three, as
        # seen in angle around the central point.
        def angle(px, py):
            return np.arctan2(py - cy, px - cx)
        here = angle(x, y)
        gaps = {n: abs(np.angle(np.exp(1j * (angle(*p) - here))))
                for n, p in PEARCE_1976_FIELDS["labels"].items()}
        assert min(gaps, key=gaps.get) == field, gaps

    def test_titanium_units_are_converted_for_butler_woronow(self):
        d = get_diagram("butler_woronow_DF")
        as_oxide = d._compute_xy(pd.DataFrame([
            {"Zr": 74, "Y": 28, "Sr": 90, "TiO2": 1.15}]))
        as_element = d._compute_xy(pd.DataFrame([
            {"Zr": 74, "Y": 28, "Sr": 90, "Ti": 1.15 * TIO2_WT_TO_TI_PPM}]))
        assert float(as_oxide[0].iloc[0]) == pytest.approx(
            float(as_element[0].iloc[0]))

    def test_missing_columns_are_reported_not_guessed(self):
        for key in ("pearce_1976_DF", "butler_woronow_DF"):
            xs, ys = get_diagram(key)._compute_xy(
                pd.DataFrame({"SiO2": [50.0]}))
            assert xs is None and ys is None, key

    def test_non_positive_values_do_not_become_infinities(self):
        d = get_diagram("pearce_1976_DF")
        comp = dict(REFERENCE_BASALTS["N-MORB"], MnO=0.0)
        xs, _ys = d._compute_xy(pd.DataFrame([comp]))
        assert np.isnan(float(xs.iloc[0]))

    def test_the_axes_grow_to_hold_the_data(self, qapp):
        """A fixed window would hide a sample while the counter still
        called it plotted."""
        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import GroupStyle, PlotStyle
        from matplotlib.figure import Figure
        df = pd.DataFrame(REFERENCE_BASALTS).T.reset_index()
        df["Suite"] = "ref"
        style = PlotStyle()
        style.group_columns = ["Suite"]
        style.groups = [GroupStyle(name="ref")]
        fig = Figure(figsize=(6, 5))
        get_diagram("butler_woronow_DF").plot(fig, df, style, PlotOptions())
        ax = fig.axes[0]
        xs, ys = get_diagram("butler_woronow_DF")._compute_xy(df)
        assert ax.get_ylim()[0] <= ys.min()
        assert ax.get_ylim()[1] >= ys.max()
        fig.clf()

    def test_the_known_disagreement_is_stated_on_screen(self):
        """The book's Fig. 5.5b boundaries do not match its own
        equations; a user must not read a field name from it unaware."""
        citation = get_diagram("butler_woronow_DF").citation
        assert "CAUTION" in citation
