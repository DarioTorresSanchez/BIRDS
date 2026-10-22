"""Posterior probabilities for the Verma DF panels.

The model is checked against three things the papers state independently
of it: where the triple point lies, what the probability is there, and
what a field boundary means.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.templates import verma_coefficients as VC
from birds.tectonic_results import DISCRIMINATORS
from birds.verma_probability import (
    BY_CHANCE_PERCENT,
    CENTROIDS,
    PANEL_GROUPS,
    TABLES,
    circumcentre,
    equal_probability_radius,
    panel_probabilities,
    posterior_percent,
)

#: Field geometry per set, for the published triple points.
FIELDS = {
    "VA11": VC.VA11_FIELDS,
    "V12_ACID": VC.V12_ACID_FIELDS,
    "VV13_MAJOR": VC.VV13_MAJOR_FIELDS,
    "VV13_IMINT": VC.VV13_IMINT_FIELDS,
    "VV13_TRACE": VC.VV13_TRACE_FIELDS,
    "V13A_MACID": VC.V13A_MACID_FIELDS,
    "V13A_MTACID": VC.V13A_MTACID_FIELDS,
    "V13A_TACID": VC.V13A_TACID_FIELDS,
}

#: How far the circumcentre may sit from the published triple point.
#: Verma & Verma (2013) prints its centroids to ten significant figures,
#: Verma & Agrawal (2011) and Verma et al. (2012) have theirs from the
#: authors' sheet, and the 2013 acid papers print one or two decimals.
TRIPLE_TOLERANCE = {
    "VA11": 0.005, "V12_ACID": 0.005, "VV13_MAJOR": 0.02, "VV13_IMINT": 0.02,
    "VV13_TRACE": 0.02, "V13A_MACID": 0.10, "V13A_MTACID": 0.06,
    "V13A_TACID": 0.15,
}


def _panels():
    return [(key, panel) for key, panels in CENTROIDS.items()
            for panel in panels]


class TestAgainstThePublishedFigures:
    """Checks that use numbers the probability model never saw."""

    @pytest.mark.parametrize("key,panel", _panels())
    def test_the_triple_point_is_the_circumcentre(self, key, panel):
        """Equal probability for three groups means equal distance.

        The triple point comes from the figure caption and the centroids
        from elsewhere in the same paper, so agreement here is a real
        check on both -- and on the choice of model.
        """
        triple = FIELDS[key][panel]["triple"]
        centre = circumcentre([CENTROIDS[key][panel][g]
                               for g in PANEL_GROUPS[panel]])
        assert centre is not None, f"{key} {panel}: centroids are collinear"
        assert np.hypot(centre[0] - triple[0],
                        centre[1] - triple[1]) < TRIPLE_TOLERANCE[key]

    @pytest.mark.parametrize("key,panel", _panels())
    def test_every_group_is_equally_likely_at_the_triple_point(self, key,
                                                               panel):
        """"the probability reaches to about 33.3% for any given field"."""
        triple = FIELDS[key][panel]["triple"]
        got = posterior_percent([triple[0]], [triple[1]],
                                CENTROIDS[key][panel])
        for group, series in got.items():
            assert series.iloc[0] == pytest.approx(BY_CHANCE_PERCENT, abs=6.0), (
                f"{key} {panel} {group}")

    @pytest.mark.parametrize("key,panel", _panels())
    def test_a_group_is_most_likely_at_its_own_centroid(self, key, panel):
        centroids = CENTROIDS[key][panel]
        for group, (x, y) in centroids.items():
            got = posterior_percent([x], [y], centroids)
            best = max(got, key=lambda g: got[g].iloc[0])
            assert best == group, f"{key} {panel}: at {group} the model says {best}"

    @pytest.mark.parametrize("key,panel", _panels())
    def test_two_groups_are_even_halfway_between_them(self, key, panel):
        """A boundary "represent[s] about 50% (0.50) probability".

        Midway between two centroids the two are equidistant, so they
        must come out equal -- whatever the third group contributes.
        """
        centroids = CENTROIDS[key][panel]
        groups = PANEL_GROUPS[panel]
        for i, a in enumerate(groups):
            for b in groups[i + 1:]:
                (ax, ay), (bx, by) = centroids[a], centroids[b]
                got = posterior_percent([(ax + bx) / 2], [(ay + by) / 2],
                                        centroids)
                assert got[a].iloc[0] == pytest.approx(got[b].iloc[0],
                                                       abs=1e-9), (
                    f"{key} {panel}: {a} vs {b}")


class TestTheArithmetic:

    @pytest.mark.parametrize("key,panel", _panels())
    def test_the_three_probabilities_total_one_hundred(self, key, panel):
        rng = np.random.default_rng(20260926)
        xs = rng.uniform(-8, 8, 200)
        ys = rng.uniform(-8, 8, 200)
        got = posterior_percent(xs, ys, CENTROIDS[key][panel])
        total = sum(got.values())
        assert np.allclose(total, 100.0)

    def test_a_far_away_sample_still_gets_real_numbers(self):
        """Guards the shift by the smallest squared distance.

        exp(-d^2/2) underflows to zero past d ~ 40, so a naive
        implementation would divide 0 by 0 and return NaN for exactly
        the samples worth flagging.  Here the nearest group should
        simply take essentially all of the probability.
        """
        centroids = CENTROIDS["VA11"]["IAB_CRB_OIB"]
        got = posterior_percent([500.0], [-500.0], centroids)
        total = sum(s.iloc[0] for s in got.values())
        assert total == pytest.approx(100.0)
        assert all(np.isfinite(s.iloc[0]) for s in got.values())
        assert max(s.iloc[0] for s in got.values()) > 99.0

    def test_a_missing_score_gives_no_probability(self):
        centroids = CENTROIDS["VA11"]["IAB_CRB_OIB"]
        got = posterior_percent([1.0, np.nan], [1.0, 2.0], centroids)
        for series in got.values():
            assert np.isfinite(series.iloc[0])
            assert np.isnan(series.iloc[1])

    def test_the_fifty_percent_radius_is_the_published_one(self):
        """Two groups at equal distance each take 50 %; the helper
        inverts the exponential for a single competing group."""
        assert equal_probability_radius(50.0) == pytest.approx(
            np.sqrt(2.0 * np.log(2.0)))
        with pytest.raises(ValueError):
            equal_probability_radius(0.0)


class TestFromASampleTable:

    #: Reference compositions, majors in wt.% and traces in ppm.
    SAMPLES = pd.DataFrame([
        {"name": "N-MORB", "SiO2": 50.5, "TiO2": 1.15, "Al2O3": 15.3,
         "Fe2O3": 2.0, "FeO": 6.0, "MnO": 0.17, "MgO": 7.6, "CaO": 11.3,
         "Na2O": 2.7, "K2O": 0.1, "P2O5": 0.1, "Nb": 2.33, "V": 250.0,
         "Y": 28.0, "Zr": 74.0},
        {"name": "continental rift", "SiO2": 47.0, "TiO2": 2.40,
         "Al2O3": 15.0, "Fe2O3": 3.5, "FeO": 7.5, "MnO": 0.17, "MgO": 7.0,
         "CaO": 9.5, "Na2O": 3.6, "K2O": 1.6, "P2O5": 0.6, "Nb": 48.0,
         "V": 220.0, "Y": 29.0, "Zr": 216.0},
        {"name": "island arc", "SiO2": 51.0, "TiO2": 0.90, "Al2O3": 18.0,
         "Fe2O3": 3.0, "FeO": 6.0, "MnO": 0.18, "MgO": 5.5, "CaO": 11.0,
         "Na2O": 2.6, "K2O": 0.5, "P2O5": 0.12, "Nb": 2.6, "V": 290.0,
         "Y": 21.0, "Zr": 65.0},
    ])

    #: Only panels that actually contain the sample's own setting are
    #: listed.  The papers call a panel missing the true setting
    #: "inapplicable", and their own Turkey case study shows a sample
    #: landing in the wrong field in exactly that situation.
    EXPECTED = {
        "IAB_CRBOIB_MORB": {"N-MORB": "MORB", "continental rift": "CRB+OIB",
                            "island arc": "IAB"},
        "IAB_CRB_MORB": {"N-MORB": "MORB", "continental rift": "CRB",
                         "island arc": "IAB"},
        "IAB_CRB_OIB": {"continental rift": "CRB", "island arc": "IAB"},
        "IAB_OIB_MORB": {"N-MORB": "MORB", "island arc": "IAB"},
        "CRB_OIB_MORB": {"N-MORB": "MORB", "continental rift": "CRB"},
    }

    @pytest.mark.parametrize("panel", sorted(EXPECTED))
    def test_reference_basalts_land_in_their_own_setting(self, panel):
        got = panel_probabilities(self.SAMPLES, "VA11", panel)
        assert got is not None
        for i, name in enumerate(self.SAMPLES["name"]):
            if name not in self.EXPECTED[panel]:
                continue
            scores = {g: got[g].iloc[i] for g in PANEL_GROUPS[panel]}
            best = max(scores, key=scores.__getitem__)
            assert best == self.EXPECTED[panel][name], (
                f"{panel}: {name} -> {best} ({scores[best]:.1f} %)")
            assert scores[best] > BY_CHANCE_PERCENT

    def test_a_table_without_the_needed_columns_returns_nothing(self):
        assert panel_probabilities(pd.DataFrame({"SiO2": [50.0]}),
                                   "VA11", "IAB_CRB_OIB") is None

    def test_every_set_with_centroids_covers_all_its_panels(self):
        for key, panels in CENTROIDS.items():
            table = TABLES[key]
            for panel in panels:
                assert f"DF1_{panel}" in table, f"{key} {panel}"
                assert set(CENTROIDS[key][panel]) == set(PANEL_GROUPS[panel])


class TestTheStatisticsTable:

    def test_probabilities_are_offered_for_every_eligible_set(self):
        keys = {d.key for d in DISCRIMINATORS}
        for key, panels in CENTROIDS.items():
            prefix = {"VA11": "va11", "V12_ACID": "v12_acid",
                      "VV13_MAJOR": "vv13_maj",
                      "VV13_IMINT": "vv13_imint", "VV13_TRACE": "vv13_tr",
                      "V13A_MACID": "v13a_macid",
                      "V13A_MTACID": "v13a_mtacid",
                      "V13A_TACID": "v13a_tacid"}[key]
            for panel, groups in ((p, PANEL_GROUPS[p]) for p in panels):
                for group in groups:
                    want = f"{prefix}.p.{panel.lower()}.{group.lower()}"
                    assert want in keys, want

    def test_verma_2012_acid_offers_probabilities_from_the_sheet(self):
        """The paper prints no centroids; the authors' sheet has them."""
        assert len([d for d in DISCRIMINATORS
                    if d.key.startswith("v12_acid.p.")]) == 15

    def test_the_basic_sets_of_2004_to_2008_offer_scores_only(self):
        """None of the three papers has centroids anywhere."""
        for prefix in ("a04", "v06", "a08"):
            mine = [d for d in DISCRIMINATORS
                    if d.key.startswith(f"{prefix}.")]
            assert len(mine) == 10
            assert not [d for d in mine if ".p." in d.key]

    def test_each_panel_column_reports_its_own_group(self):
        """Guards a late-binding slip.

        The three columns of a panel are built in a loop, and closing
        over the loop variable rather than binding it would make every
        column report the last group of the last panel.
        """
        by_key = {d.key: d for d in DISCRIMINATORS}
        samples = TestFromASampleTable.SAMPLES
        for panel in CENTROIDS["VA11"]:
            groups = PANEL_GROUPS[panel]
            direct = panel_probabilities(samples, "VA11", panel)
            for group in groups:
                key = f"va11.p.{panel.lower()}.{group.lower()}"
                got = by_key[key].compute(samples)
                assert np.allclose(got.to_numpy(),
                                   direct[group].to_numpy()), key
