"""Censored-value parsing — where silent data loss used to happen."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from birds.detection_limits import (
    POLICIES,
    reapply_policy,
    scan_and_convert,
)


def _frame(values: list) -> pd.DataFrame:
    return pd.DataFrame({
        "Sample_Name": [f"S{i}" for i in range(len(values))],
        "X": values,
    })


class TestParsing:
    @pytest.mark.parametrize("marker,limit", [
        ("<0.5", 0.5), ("< 0.5", 0.5), ("≤0.5", 0.5), ("<=0.5", 0.5),
        ("<1e-3", 1e-3),
    ])
    def test_censored_forms_recognised(self, marker, limit):
        out, mask, report = scan_and_convert(_frame([marker, "1.0"]), "half")
        assert bool(mask["X"].iloc[0])
        assert out["X"].iloc[0] == pytest.approx(limit / 2)
        assert report.limits["X"].iloc[0] == pytest.approx(limit)

    @pytest.mark.parametrize("marker", ["b.d.l.", "bdl", "n.d.", "nd", "-"])
    def test_textual_markers_become_blank_but_flagged(self, marker):
        out, mask, _ = scan_and_convert(_frame([marker, "1.0"]), "half")
        assert bool(mask["X"].iloc[0])
        assert math.isnan(out["X"].iloc[0])

    def test_fully_censored_column_is_converted(self):
        """An analyte never above detection is still an analyte."""
        out, mask, _ = scan_and_convert(_frame(["b.d.l.", "n.d."]), "half")
        assert out["X"].dtype.kind == "f"
        assert int(mask["X"].sum()) == 2

    def test_descriptive_text_column_is_left_alone(self):
        """A rock-name column using '-' as a placeholder is not data."""
        out, mask, _ = scan_and_convert(
            _frame(["basalt", "andesite", "-"]), "half")
        assert out["X"].tolist() == ["basalt", "andesite", "-"]
        assert mask is None or not mask["X"].any()

    def test_plain_numeric_column_untouched(self):
        out, mask, report = scan_and_convert(_frame([1.0, 2.0, 3.0]), "half")
        assert mask is None
        assert report.total == 0


class TestPolicies:
    @pytest.mark.parametrize("policy,expected", [
        ("half", 0.25), ("sqrt2", 0.5 / math.sqrt(2)), ("nan", float("nan")),
    ])
    def test_each_policy_substitutes_correctly(self, policy, expected):
        out, _, _ = scan_and_convert(_frame(["<0.5", "1.0"]), policy)
        value = out["X"].iloc[0]
        if math.isnan(expected):
            assert math.isnan(value)
        else:
            assert value == pytest.approx(expected)

    def test_unknown_policy_raises(self):
        """Falling back silently would discard every censored value."""
        with pytest.raises(ValueError):
            scan_and_convert(_frame(["<0.5", "1.0"]), "nonsense")

    def test_reapply_round_trip_is_lossless(self):
        df = _frame(["<0.5", "3.2", "b.d.l."])
        conv, mask, report = scan_and_convert(df, "half")
        original = conv["X"].tolist()
        for policy in POLICIES:
            conv, _ = reapply_policy(conv, mask, report.limits, policy)
        back, _ = reapply_policy(conv, mask, report.limits, "half")
        assert back["X"].iloc[0] == pytest.approx(original[0])
        assert back["X"].iloc[1] == pytest.approx(3.2)

    def test_reapply_leaves_uncensored_values_alone(self):
        conv, mask, report = scan_and_convert(
            _frame(["<0.5", "3.2", "7.9"]), "half")
        out, _ = reapply_policy(conv, mask, report.limits, "nan")
        assert out["X"].iloc[1] == pytest.approx(3.2)
        assert out["X"].iloc[2] == pytest.approx(7.9)

    def test_reapply_without_limits_is_a_no_op(self):
        df = _frame([1.0, 2.0])
        out, changed = reapply_policy(df, None, None, "half")
        assert changed == 0
        pd.testing.assert_frame_equal(out, df)


class TestShape:
    def test_mask_matches_frame_shape(self):
        df = pd.DataFrame({"Sample_Name": ["A", "B"],
                           "X": ["<1", "2"], "Y": ["3", "b.d.l."]})
        out, mask, _ = scan_and_convert(df, "half")
        assert mask.shape == df.shape
        assert out.shape == df.shape

    def test_empty_frame(self):
        out, mask, report = scan_and_convert(pd.DataFrame(), "half")
        assert mask is None and report.total == 0

    def test_none_frame(self):
        out, mask, report = scan_and_convert(None, "half")
        assert out is None and mask is None
