"""CIPW norm — the numerical core, so the invariants are checked hard.

Most of these are petrological laws rather than implementation details:
a norm that violates them is wrong no matter how the code is written.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.cipw import OUTPUT_MINERALS, compute_cipw
from conftest import MAJORS

NORM_COLS = [f"norm_{m}" for m in OUTPUT_MINERALS]


def _oxide_total(row: dict) -> float:
    return sum(v for k, v in row.items() if k in MAJORS)


class TestMassBalance:
    def test_total_matches_oxide_sum(self, majors_df):
        """Every oxide wt % must reappear in some normative mineral."""
        result = compute_cipw(majors_df)
        clean = result["silica_deficit"] < 1e-6
        assert clean.any(), "fixture produced no ordinary rocks"
        deviation = (result.loc[clean, "norm_Total"] - 100.0).abs()
        assert deviation.max() < 0.05, (
            f"norm total drifts from 100 wt % by {deviation.max():.4f}")

    def test_manganese_is_not_lost(self):
        """MnO folds into FeO; dropping it leaves the total short."""
        base = dict(zip(MAJORS,
                        [50.0, 1.5, 15.0, 3.0, 7.0, 0.0, 8.0, 11.0,
                         2.5, 0.5, 0.2]))
        with_mn = dict(base, MnO=1.5, MgO=6.5)   # swap MgO for MnO
        r0 = compute_cipw(pd.DataFrame([base]))
        r1 = compute_cipw(pd.DataFrame([with_mn]))
        for row, frame in ((base, r0), (with_mn, r1)):
            total = float(frame["norm_Total"].iloc[0])
            assert abs(total - _oxide_total(row)) < 0.05, (
                f"{total:.3f} vs {_oxide_total(row):.3f} wt %")

    def test_excess_titanium_becomes_rutile(self):
        """TiO2 the FeO cannot pair with must not vanish."""
        row = dict(zip(MAJORS,
                       [45.0, 12.0, 14.0, 1.0, 2.0, 0.1, 6.0, 10.0,
                        3.0, 1.0, 0.2]))
        result = compute_cipw(pd.DataFrame([row]))
        assert float(result["norm_Ru"].iloc[0]) > 0
        total = float(result["norm_Total"].iloc[0])
        assert abs(total - _oxide_total(row)) < 0.05

    def test_scale_invariance(self, majors_df):
        """Doubling every oxide doubles every normative mineral."""
        single = compute_cipw(majors_df)
        doubled = compute_cipw(
            majors_df.assign(**{c: majors_df[c] * 2 for c in MAJORS}))
        ratio = doubled["norm_Total"] / single["norm_Total"]
        assert np.allclose(ratio, 2.0, atol=1e-6)


class TestPetrologicalRules:
    def test_quartz_and_nepheline_never_coexist(self, majors_df):
        result = compute_cipw(majors_df)
        both = (result["norm_Q"] > 0.01) & (result["norm_Ne"] > 0.01)
        assert not both.any()

    def test_no_negative_minerals(self, majors_df):
        result = compute_cipw(majors_df)
        for col in NORM_COLS:
            assert result[col].min() >= -1e-9, f"{col} went negative"

    def test_saturation_label_agrees_with_quartz(self, majors_df):
        result = compute_cipw(majors_df)
        over = result["silica_saturation"] == "oversaturated"
        under = result["silica_saturation"] == "undersaturated"
        assert (result.loc[over, "norm_Q"] > 0).all()
        assert (result.loc[under, "norm_Q"] <= 0.01).all()


class TestSilicaDeficit:
    """Rocks poorer in silica than the implemented cascade can handle."""

    MELILITITE = dict(zip(MAJORS,
                          [37.1, 0.55, 19.27, 4.61, 10.95, 0.18,
                           10.88, 13.33, 2.62, 0.23, 0.29]))

    def test_deficit_is_reported_not_swallowed(self):
        result = compute_cipw(pd.DataFrame([self.MELILITITE]))
        deficit = float(result["silica_deficit"].iloc[0])
        assert deficit > 1.0, "an unresolvable deficit went unreported"

    def test_reported_deficit_explains_the_overstated_total(self):
        """The flag must quantify the error, not merely announce it."""
        result = compute_cipw(pd.DataFrame([self.MELILITITE]))
        overshoot = (float(result["norm_Total"].iloc[0])
                     - _oxide_total(self.MELILITITE))
        deficit = float(result["silica_deficit"].iloc[0])
        assert abs(overshoot - deficit) < 0.6

    def test_ordinary_rocks_are_not_flagged(self, majors_df):
        result = compute_cipw(majors_df)
        ordinary = majors_df["SiO2"] > 45
        assert (result.loc[ordinary, "silica_deficit"] < 1e-6).all()


class TestRobustness:
    def test_deterministic(self, majors_df):
        a = compute_cipw(majors_df).select_dtypes("number")
        b = compute_cipw(majors_df).select_dtypes("number")
        pd.testing.assert_frame_equal(a, b)

    def test_all_nan_row_does_not_raise(self):
        blank = pd.DataFrame([{c: np.nan for c in MAJORS}])
        result = compute_cipw(blank)
        assert np.isnan(result["norm_Total"].iloc[0])
        assert result["silica_saturation"].iloc[0] == "incomplete"

    def test_missing_columns_do_not_raise(self):
        partial = pd.DataFrame([{"SiO2": 50.0, "Al2O3": 15.0}])
        result = compute_cipw(partial)
        assert len(result) == 1

    def test_index_is_preserved(self, majors_df):
        shuffled = majors_df.sample(frac=1, random_state=1)
        result = compute_cipw(shuffled)
        assert result.index.equals(shuffled.index)

    @pytest.mark.parametrize("scale", [1e-12, 1e12])
    def test_extreme_magnitudes(self, majors_df, scale):
        scaled = majors_df.assign(
            **{c: majors_df[c] * scale for c in MAJORS})
        result = compute_cipw(scaled)
        assert np.isfinite(result["norm_Total"]).all()
