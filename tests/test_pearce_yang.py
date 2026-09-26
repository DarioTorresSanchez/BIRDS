"""Pearce (2008) and Yang et al. (2019), against their own papers.

Both sources are on disk.  Pearce's two panels have no published
equations — the arrays are drawn — so they were measured from Fig. 2,
with the three Sun & McDonough (1989) reference markers located to
check the calibration.  Yang's parameters *are* published, as Table 1,
and are transcribed here digit for digit.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.tectonic_bivariate import (
    CRUSTAL_CONTAMINATION_TH_NB,
    MORB_ARRAY_TIO2_YB,
    MORB_OIB_ARRAY_TH_NB,
    N_E_MORB_NB_YB,
    OIB_ARRAY_TIO2_YB,
    OIB_THOLEIITIC_ALKALIC,
    SUN_MCDONOUGH_1989,
    TIO2_WT_TO_TI_PPM,
    YANG_FCKANT_TREND,
    YANG_FCKANTMS_CONSTANT,
    YANG_K_AL,
    YANG_LHERZOLITE_TREND,
    YANG_NA_K_TI,
    YANG_PERIDOTITE_EVOLVED,
    YANG_PERIDOTITE_PRIMARY,
    YANG_TI_NA,
    YANG_TRANSITIONAL_UPPER,
    _yang_fckantms,
    _yang_fcms,
    _yang_silica_index,
)


def power(coefs, x):
    a, b = coefs
    return a * x ** b


class TestSunMcDonoughReservoirs:
    """The markers Pearce plots; locating them in Fig. 2 is what fixes
    the calibration of both panels."""

    def test_the_three_reservoirs_are_present(self):
        assert set(SUN_MCDONOUGH_1989) == {"N-MORB", "E-MORB", "OIB"}

    @pytest.mark.parametrize("name,nb_yb,th_yb,tio2_yb", [
        ("N-MORB", 0.764, 0.0393, 0.416),
        ("E-MORB", 3.502, 0.2532, 0.422),
        ("OIB", 22.222, 1.8519, 1.329),
    ])
    def test_ratios(self, name, nb_yb, th_yb, tio2_yb):
        r = SUN_MCDONOUGH_1989[name]
        assert r["Nb"] / r["Yb"] == pytest.approx(nb_yb, abs=0.01)
        assert r["Th"] / r["Yb"] == pytest.approx(th_yb, abs=0.001)
        assert (r["Ti"] / TIO2_WT_TO_TI_PPM) / r["Yb"] == pytest.approx(
            tio2_yb, abs=0.01)

    def test_they_are_ordered_by_enrichment(self):
        order = [SUN_MCDONOUGH_1989[n]["Nb"] / SUN_MCDONOUGH_1989[n]["Yb"]
                 for n in ("N-MORB", "E-MORB", "OIB")]
        assert order == sorted(order)


class TestPearceThYbNbYb:
    """Fig. 2a — the MORB-OIB array as a band of constant Th/Nb."""

    def test_the_measured_bounds(self):
        assert MORB_OIB_ARRAY_TH_NB == (0.043, 0.096)

    def test_the_band_is_not_the_old_guess(self):
        """It carried 0.07 to 0.32, which puts N-MORB below the array."""
        low, _high = MORB_OIB_ARRAY_TH_NB
        r = SUN_MCDONOUGH_1989["N-MORB"]
        assert r["Th"] / r["Nb"] > low
        assert r["Th"] / r["Nb"] < 0.07          # the old lower bound

    @pytest.mark.parametrize("name", ["N-MORB", "E-MORB", "OIB"])
    def test_every_reference_reservoir_sits_inside_the_array(self, name):
        low, high = MORB_OIB_ARRAY_TH_NB
        r = SUN_MCDONOUGH_1989[name]
        assert low < r["Th"] / r["Nb"] < high

    def test_the_contamination_filter_is_the_published_one(self):
        """Pearce excludes samples with Th/Nb > 0.2 (pp. 30, 41)."""
        assert CRUSTAL_CONTAMINATION_TH_NB == 0.2

    def test_the_filter_sits_above_the_array(self):
        assert CRUSTAL_CONTAMINATION_TH_NB > MORB_OIB_ARRAY_TH_NB[1]

    def test_the_axes_are_logarithmic(self):
        d = get_diagram("pearce2008_thyb_nbyb")
        assert d.log_x and d.log_y

    def test_it_computes_the_two_ratios(self):
        d = get_diagram("pearce2008_thyb_nbyb")
        df = pd.DataFrame([{"Nb": 8.0, "Yb": 2.0, "Th": 0.5}])
        xs, ys = d._compute_xy(df)
        assert float(xs.iloc[0]) == pytest.approx(4.0)
        assert float(ys.iloc[0]) == pytest.approx(0.25)

    def test_missing_columns_are_reported_not_guessed(self):
        d = get_diagram("pearce2008_thyb_nbyb")
        xs, ys = d._compute_xy(pd.DataFrame({"Nb": [8.0]}))
        assert xs is None and ys is None


class TestPearceTiO2YbNbYb:
    """Fig. 2b — TiO2 in wt.% over Yb in ppm, not Ti in ppm."""

    def test_the_axis_is_titania_not_titanium(self):
        d = get_diagram("pearce2008_tiyb_nbyb")
        assert "TiO" in d.y_label
        assert "wt.%" in d.y_label

    def test_the_window_matches_the_published_frame(self):
        d = get_diagram("pearce2008_tiyb_nbyb")
        assert d.y_range == (0.1, 10.0)
        assert d.x_range == (0.1, 100.0)

    def test_titania_in_weight_per_cent_is_used_directly(self):
        d = get_diagram("pearce2008_tiyb_nbyb")
        df = pd.DataFrame([{"Nb": 2.33, "Yb": 3.05, "TiO2": 1.268}])
        _xs, ys = d._compute_xy(df)
        assert float(ys.iloc[0]) == pytest.approx(1.268 / 3.05, rel=1e-6)

    def test_titanium_in_ppm_is_converted_to_titania(self):
        d = get_diagram("pearce2008_tiyb_nbyb")
        a = d._compute_xy(pd.DataFrame([
            {"Nb": 2.33, "Yb": 3.05, "TiO2": 1.268}]))
        b = d._compute_xy(pd.DataFrame([
            {"Nb": 2.33, "Yb": 3.05, "Ti": 1.268 * TIO2_WT_TO_TI_PPM}]))
        assert float(a[1].iloc[0]) == pytest.approx(float(b[1].iloc[0]))

    def test_the_three_bounds_are_near_parallel(self):
        """Fitted exponents agree to within 0.006, so the arrays are
        parallel bands in log-log."""
        exps = [MORB_ARRAY_TIO2_YB[0][1], MORB_ARRAY_TIO2_YB[1][1],
                OIB_ARRAY_TIO2_YB[1][1]]
        assert max(exps) - min(exps) < 0.01

    def test_the_arrays_share_their_dividing_line(self):
        assert MORB_ARRAY_TIO2_YB[1] == OIB_ARRAY_TIO2_YB[0]

    def test_the_bounds_never_cross(self):
        for x in np.logspace(-1, 2, 25):
            lo = power(MORB_ARRAY_TIO2_YB[0], x)
            mid = power(MORB_ARRAY_TIO2_YB[1], x)
            hi = power(OIB_ARRAY_TIO2_YB[1], x)
            assert lo < mid < hi, x

    @pytest.mark.parametrize("name,array", [
        ("N-MORB", "MORB"), ("E-MORB", "MORB"), ("OIB", "OIB")])
    def test_reference_reservoirs_land_in_their_array(self, name, array):
        r = SUN_MCDONOUGH_1989[name]
        x = r["Nb"] / r["Yb"]
        y = (r["Ti"] / TIO2_WT_TO_TI_PPM) / r["Yb"]
        lo = power(MORB_ARRAY_TIO2_YB[0], x)
        mid = power(MORB_ARRAY_TIO2_YB[1], x)
        hi = power(OIB_ARRAY_TIO2_YB[1], x)
        if array == "MORB":
            assert lo < y < mid, name
        else:
            assert mid < y < hi, name

    def test_the_n_e_morb_divide_is_the_chondrite_value(self):
        """"Nb/Yb < 1.45, the C1 chondrite value" — Fig. 2 caption."""
        assert N_E_MORB_NB_YB == 1.45

    def test_the_divide_separates_the_two_morb_markers(self):
        n = SUN_MCDONOUGH_1989["N-MORB"]
        e = SUN_MCDONOUGH_1989["E-MORB"]
        assert n["Nb"] / n["Yb"] < N_E_MORB_NB_YB < e["Nb"] / e["Yb"]

    def test_the_tholeiitic_alkalic_divide_descends(self):
        """It cuts across the OIB array from upper left to lower right."""
        assert OIB_THOLEIITIC_ALKALIC[1] < 0

    def test_the_divide_spans_the_oib_array(self):
        """It should meet both bounds inside the plotted range."""
        a, b = OIB_THOLEIITIC_ALKALIC
        top = 10 ** ((np.log10(OIB_ARRAY_TIO2_YB[1][0]) - np.log10(a))
                     / (b - OIB_ARRAY_TIO2_YB[1][1]))
        bottom = 10 ** ((np.log10(MORB_ARRAY_TIO2_YB[1][0]) - np.log10(a))
                        / (b - MORB_ARRAY_TIO2_YB[1][1]))
        assert 0.1 < top < bottom < 100.0
        assert top == pytest.approx(8.5, abs=0.5)
        assert bottom == pytest.approx(18.2, abs=0.8)


class TestYangEquations:
    """Table 1 of Yang et al. (2019).  All oxides in wt.%."""

    def test_the_lherzolite_trend_is_equation_one(self):
        assert YANG_LHERZOLITE_TREND == (0.058, 0.636, 1.850, 1.170)

    def test_the_fckant_trend_is_equation_seven(self):
        assert YANG_FCKANT_TREND == (0.062, 0.641, 1.871, 1.201)

    def test_the_logratio_corrections(self):
        assert (YANG_K_AL, YANG_TI_NA, YANG_NA_K_TI) == (0.08, 0.052, 0.036)

    def test_equation_eight_is_equation_six_minus_equation_seven(self):
        """An internal check the paper allows: FCKANTMS = FCKANT - trend,
        so its constant must be 0.271 + 1.201."""
        assert YANG_FCKANTMS_CONSTANT == pytest.approx(
            0.271 + YANG_FCKANT_TREND[3], abs=0.0011)

    def test_fcms_is_a_logratio_residual_not_an_oxide_sum(self):
        """It used to be 'SiO2 + 0.99 K2O - 1.32 Al2O3 - 0.78 MgO',
        which is neither a log-ratio nor in the paper."""
        melt = dict(SiO2=47.0, TiO2=1.0, Al2O3=15.0, FeO=9.5, MgO=13.0,
                    CaO=11.0, Na2O=1.8, K2O=0.15)
        got = float(_yang_fcms(pd.DataFrame([melt])).iloc[0])
        ms = np.log(melt["MgO"] / melt["SiO2"])
        a, b, c, d = YANG_LHERZOLITE_TREND
        want = (np.log(melt["FeO"] / melt["CaO"])
                - a * ms ** 3 - b * ms ** 2 - c * ms - d)
        assert got == pytest.approx(want)
        assert abs(got) < 2.0            # order 0.1, not order 10

    def test_fckantms_matches_equation_eight_by_hand(self):
        melt = dict(SiO2=47.0, TiO2=1.0, Al2O3=15.0, FeO=9.5, MgO=13.0,
                    CaO=11.0, Na2O=1.8, K2O=0.15)
        got = float(_yang_fckantms(pd.DataFrame([melt])).iloc[0])
        ln = np.log
        ms = ln(melt["MgO"] / melt["SiO2"])
        a, b, c, _d = YANG_FCKANT_TREND
        want = (ln(melt["FeO"] / melt["CaO"])
                - YANG_K_AL * ln(melt["K2O"] / melt["Al2O3"])
                - YANG_TI_NA * ln(melt["TiO2"] / melt["Na2O"])
                - YANG_NA_K_TI * ln(melt["Na2O"] / melt["K2O"])
                * ln(melt["Na2O"] / melt["TiO2"])
                - a * ms ** 3 - b * ms ** 2 - c * ms
                - YANG_FCKANTMS_CONSTANT)
        assert got == pytest.approx(want)

    def test_a_mafic_source_melt_scores_higher_than_a_peridotite_one(self):
        """The whole point of the parameter."""
        lherz = dict(SiO2=47.0, TiO2=1.0, Al2O3=15.0, FeO=9.5, MgO=13.0,
                     CaO=11.0, Na2O=1.8, K2O=0.15)
        pyrox = dict(SiO2=49.0, TiO2=1.6, Al2O3=14.5, FeO=10.5, MgO=10.0,
                     CaO=8.5, Na2O=2.6, K2O=0.35)
        vals = _yang_fckantms(pd.DataFrame([lherz, pyrox]))
        assert float(vals.iloc[1]) > float(vals.iloc[0])

    def test_all_iron_is_taken_as_ferrous(self):
        split = dict(SiO2=47.0, TiO2=1.0, Al2O3=15.0, MgO=13.0, CaO=11.0,
                     Na2O=1.8, K2O=0.15, FeO=6.0, Fe2O3=3.8908)
        total = dict(split); del total["Fe2O3"]
        total["FeO"] = 6.0 + 0.89981 * 3.8908
        a = float(_yang_fcms(pd.DataFrame([split])).iloc[0])
        b = float(_yang_fcms(pd.DataFrame([total])).iloc[0])
        assert a == pytest.approx(b, rel=1e-6)

    def test_non_positive_oxides_give_no_value(self):
        melt = dict(SiO2=47.0, TiO2=1.0, Al2O3=15.0, FeO=9.5, MgO=13.0,
                    CaO=0.0, Na2O=1.8, K2O=0.15)
        assert np.isnan(float(_yang_fcms(pd.DataFrame([melt])).iloc[0]))

    def test_missing_oxides_are_reported_not_guessed(self):
        assert _yang_fckantms(pd.DataFrame({"SiO2": [47.0]})) is None


class TestYangBoundaries:
    """Coordinates printed in the Figure 7 caption."""

    def test_transitional_upper(self):
        assert YANG_TRANSITIONAL_UPPER == ((-0.5, -0.2), (1.0, 0.37),
                                           (1.5, 0.37))

    def test_peridotite_evolved(self):
        assert YANG_PERIDOTITE_EVOLVED == ((-0.4, -0.75), (1.05, 0.15),
                                           (1.3, 0.35), (2.8, 1.75))

    def test_peridotite_primary(self):
        assert YANG_PERIDOTITE_PRIMARY == ((-0.4, -1.45), (1.05, 0.05),
                                           (1.3, 0.15), (2.9, 1.7))

    def test_the_primary_boundary_lies_below_the_evolved_one(self):
        """Mg# = 0.7 is the stricter limit."""
        for x in np.linspace(-0.3, 2.7, 20):
            lo = np.interp(x, [p[0] for p in YANG_PERIDOTITE_PRIMARY],
                           [p[1] for p in YANG_PERIDOTITE_PRIMARY])
            hi = np.interp(x, [p[0] for p in YANG_PERIDOTITE_EVOLVED],
                           [p[1] for p in YANG_PERIDOTITE_EVOLVED])
            assert lo <= hi, x

    def test_all_boundaries_rise(self):
        for poly in (YANG_TRANSITIONAL_UPPER, YANG_PERIDOTITE_EVOLVED,
                     YANG_PERIDOTITE_PRIMARY):
            ys = [p[1] for p in poly]
            assert ys == sorted(ys)

    def test_the_axes_are_the_ones_the_paper_recommends(self):
        d = get_diagram("yang_2019_fckantms")
        assert "FCKANTMS" in d.y_label
        assert "SiO" in d.x_label and "CaO" in d.x_label
        assert "FCMS" not in d.y_label and "FCMS" not in d.x_label

    def test_the_silica_index_is_a_single_log_ratio(self):
        melt = dict(SiO2=50.0, CaO=10.0, Na2O=2.0, TiO2=1.0)
        got = float(_yang_silica_index(pd.DataFrame([melt])).iloc[0])
        assert got == pytest.approx(np.log(50.0 / 13.0))
