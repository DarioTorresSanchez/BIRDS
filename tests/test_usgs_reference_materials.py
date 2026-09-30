"""End-to-end validation against three USGS geochemical reference materials.

Every other test in this suite checks one component against one paper.
This one takes three rocks whose composition and geological setting are
both independently known, and runs them through the chain a user
actually follows: pre-process, classify, norm, normalise, discriminate.

The compositions are transcribed from the USGS Reference Material
Information Sheets, revised June 2022, which take their Table 1 (major
oxides) from Table 3 and their Table 2 (trace elements) from Table 4 of

    Jochum K.P., Weis U., Schwager B., Stoll B., Wilson S.A., Haug G.H.,
    Meinrat A.O. & Enzweiler J. (2016) "Reference values following ISO
    guidelines for frequently requested rock reference materials",
    Geostandards and Geoanalytical Research 40, 333-350,
    doi:10.1111/j.1751-908X.2015.00392.x

The sheets are explicit that "the USGS has not published a
metrologically traceable characterization of the elemental content of
this material", so these are community consensus values, not
certificates.  That is the right standard for this test, which asks
whether BIRDS reproduces what the literature says about these rocks.

The three cover a useful spread:

* **BHVO-2**, Kilauea, Hawaii -- 1919 Halemaumau pahoehoe.  An ocean
  island tholeiite, and the least ambiguous tectonic setting available
  in a reference material.
* **BCR-2**, Bridal Veil Flow Quarry, Oregon -- Columbia River flood
  basalt.  Continental, and well known to be crustally contaminated.
* **AGV-2**, Guano Valley, Oregon.  Included for the classification and
  norm, not for discrimination: Guano Valley sits in the extensional
  northern Basin and Range while AGV-2's trace signature is arc-like,
  so its "correct" tectonic answer is itself contested.  Nothing here
  asserts one.

All three report total iron as Fe2O3T with no LOI, so they exercise the
pre-process step -- anhydrous rescale then Middlemost Fe partition,
which is what SINCLAS does and what the Verma papers require.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.cipw import compute_cipw
from birds.diagrams.templates.tas import TASVolcanic
from birds.normalizations import REE_CHONDRITES
from birds.preprocess import pre_process
from birds.tectonic_results import DISCRIMINATORS
from birds.verma_probability import PANEL_GROUPS, panel_probabilities

#: Major oxides in g/100 g, trace elements in mg/kg, as printed.
REFERENCE_MATERIALS = pd.DataFrame([
    {
        "Sample": "BHVO-2", "SiO2": 49.60, "TiO2": 2.731, "Al2O3": 13.44,
        "Fe2O3t": 12.39, "MnO": 0.1690, "MgO": 7.257, "CaO": 11.40,
        "Na2O": 2.219, "K2O": 0.5130, "P2O5": 0.2685,
        "Ba": 130.9, "Ce": 37.53, "Co": 44.89, "Cr": 287.2, "Cs": 0.0996,
        "Cu": 129.3, "Dy": 5.280, "Er": 2.511, "Eu": 2.043, "Ga": 21.37,
        "Gd": 6.207, "Hf": 4.470, "Ho": 0.9887, "La": 15.20, "Lu": 0.2754,
        "Nb": 18.10, "Nd": 24.27, "Ni": 119.8, "Pb": 1.653, "Pr": 5.339,
        "Rb": 9.261, "Sc": 31.83, "Sm": 6.023, "Sr": 394.1, "Ta": 1.154,
        "Tb": 0.9392, "Th": 1.224, "Tm": 0.3349, "U": 0.412, "V": 318.2,
        "Y": 25.91, "Yb": 1.994, "Zn": 103.9, "Zr": 171.2,
    },
    {
        "Sample": "BCR-2", "SiO2": 54.00, "TiO2": 2.265, "Al2O3": 13.48,
        "Fe2O3t": 13.77, "MnO": 0.1966, "MgO": 3.599, "CaO": 7.114,
        "Na2O": 3.120, "K2O": 1.774, "P2O5": 0.3593,
        "Ba": 683.9, "Ce": 53.12, "Co": 37.33, "Cr": 15.85, "Cs": 1.160,
        "Cu": 19.66, "Dy": 6.424, "Er": 3.670, "Eu": 1.989, "Ga": 22.07,
        "Gd": 6.811, "Hf": 4.972, "Ho": 1.313, "La": 25.08, "Lu": 0.5049,
        "Nb": 12.44, "Nd": 28.26, "Ni": 12.57, "Pb": 10.59, "Pr": 6.827,
        "Rb": 46.02, "Sc": 33.53, "Sm": 6.547, "Sr": 337.4, "Ta": 0.785,
        "Tb": 1.077, "Th": 5.828, "Tm": 0.5341, "U": 1.683, "V": 417.6,
        "Y": 36.07, "Yb": 3.392, "Zn": 129.5, "Zr": 186.5,
    },
    {
        "Sample": "AGV-2", "SiO2": 59.14, "TiO2": 1.051, "Al2O3": 17.03,
        "Fe2O3t": 6.78, "MnO": 0.1004, "MgO": 1.80, "CaO": 5.15,
        "Na2O": 4.204, "K2O": 2.898, "P2O5": 0.483,
        "Ba": 1134.0, "Ce": 69.43, "Co": 15.46, "Cr": 16.22, "Cs": 1.173,
        "Cu": 51.51, "Dy": 3.549, "Er": 1.825, "Eu": 1.553, "Ga": 20.42,
        "Gd": 4.678, "Hf": 5.137, "Ho": 0.6818, "La": 38.21, "Lu": 0.2507,
        "Nb": 14.12, "Nd": 30.49, "Ni": 18.87, "Pb": 13.14, "Pr": 8.165,
        "Rb": 67.79, "Sc": 13.11, "Sm": 5.509, "Sr": 659.5, "Ta": 0.865,
        "Tb": 0.6510, "Th": 6.174, "Tm": 0.2623, "U": 1.885, "V": 118.5,
        "Y": 19.14, "Yb": 1.653, "Zn": 86.7, "Zr": 232.0,
    },
])

MAJORS = ("SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO", "MnO", "MgO", "CaO",
          "Na2O", "K2O", "P2O5")


@pytest.fixture(scope="module")
def adjusted() -> pd.DataFrame:
    """The analyses as the app prepares them, indexed by sample name."""
    out = pre_process(REFERENCE_MATERIALS, "anhydrous", "middlemost")
    for column in REFERENCE_MATERIALS.columns:
        if column not in out.columns:
            out[column] = REFERENCE_MATERIALS[column].to_numpy()
    return out.set_index(REFERENCE_MATERIALS["Sample"].to_numpy())


class TestPreProcessing:

    def test_the_published_totals_are_close_to_a_hundred(self):
        """A sanity check on the transcription before anything uses it."""
        oxides = ("SiO2", "TiO2", "Al2O3", "Fe2O3t", "MnO", "MgO", "CaO",
                  "Na2O", "K2O", "P2O5")
        for _, row in REFERENCE_MATERIALS.iterrows():
            total = sum(row[o] for o in oxides)
            assert 98.0 <= total <= 100.5, f"{row['Sample']}: {total}"

    def test_the_adjusted_analysis_closes_at_a_hundred(self, adjusted):
        for name, row in adjusted.iterrows():
            assert sum(row[o] for o in MAJORS) == pytest.approx(100.0,
                                                                abs=1e-6), name

    def test_total_iron_is_split_into_two_oxides(self, adjusted):
        """The sheets give Fe2O3T only; Verma's major-element sets need
        Fe2O3 and FeO separately, and so does the CIPW norm."""
        for name, row in adjusted.iterrows():
            assert row["Fe2O3"] > 0 and row["FeO"] > 0, name
            # Middlemost gives a basalt roughly 0.1-0.3 by mass.
            assert 0.05 < row["Fe2O3"] / row["FeO"] < 0.35, name


class TestClassification:

    #: What the IUGS scheme calls each of these rocks.
    EXPECTED = {"BHVO-2": "Basalt", "BCR-2": "Basaltic andesite",
                "AGV-2": "Trachyandesite"}

    @pytest.mark.parametrize("name", sorted(EXPECTED))
    def test_the_tas_name_is_the_published_one(self, adjusted, name):
        row = adjusted.loc[name]
        norm = compute_cipw(adjusted.loc[[name]])
        got = TASVolcanic.classify(
            row["SiO2"], row["Na2O"] + row["K2O"],
            normative_ol=float(norm["norm_Ol"].iloc[0]),
            normative_q=float(norm["norm_Q"].iloc[0]))
        assert got == self.EXPECTED[name]


class TestCipwNorm:

    def test_every_norm_closes_at_a_hundred(self, adjusted):
        """Within 0.05 wt.%, the tolerance tests/test_cipw.py already
        uses: recombining oxides into mineral molecules does not
        conserve mass exactly, and these three land about 0.003 over."""
        norm = compute_cipw(adjusted)
        assert np.allclose(norm["norm_Total"].to_numpy(), 100.0, atol=0.05)

    def test_all_three_are_silica_oversaturated(self, adjusted):
        norm = compute_cipw(adjusted)
        assert set(norm["silica_saturation"]) == {"oversaturated"}

    def test_bhvo_2_is_a_quartz_normative_tholeiite(self, adjusted):
        """Kilauea's 1919 lava is a tholeiite, so it should carry
        normative quartz and hypersthene and no nepheline."""
        norm = compute_cipw(adjusted).set_index(adjusted.index)
        row = norm.loc["BHVO-2"]
        assert row["norm_Q"] > 0.0
        assert row["norm_Hy"] > 10.0
        assert row.get("norm_Ne", 0.0) == pytest.approx(0.0, abs=1e-9)


class TestRareEarths:

    #: Chondrite-normalised ratios reported for these materials.
    #: BHVO-2 and BCR-2 are moderately light-REE enriched; AGV-2 is
    #: strongly so.  Only BCR-2 and AGV-2 carry a europium anomaly, and
    #: a small one.
    EXPECTED_LA_YB_N = {"BHVO-2": (4.5, 6.5), "BCR-2": (4.5, 6.5),
                        "AGV-2": (14.0, 19.0)}
    EXPECTED_EU_ANOMALY = {"BHVO-2": (0.95, 1.10), "BCR-2": (0.85, 1.00),
                           "AGV-2": (0.85, 1.00)}

    @pytest.mark.parametrize("name", sorted(EXPECTED_LA_YB_N))
    def test_the_chondrite_normalised_pattern(self, name):
        chondrite = REE_CHONDRITES["Sun & McDonough (1989) – CI"]
        row = REFERENCE_MATERIALS.set_index("Sample").loc[name]
        n = {e: row[e] / chondrite[e] for e in ("La", "Sm", "Eu", "Gd", "Yb")}

        low, high = self.EXPECTED_LA_YB_N[name]
        assert low <= n["La"] / n["Yb"] <= high, f"{name} (La/Yb)N"

        anomaly = n["Eu"] / np.sqrt(n["Sm"] * n["Gd"])
        low, high = self.EXPECTED_EU_ANOMALY[name]
        assert low <= anomaly <= high, f"{name} Eu/Eu*"


class TestTectonicDiscrimination:
    """Only the two rocks whose setting is not in dispute."""

    def _ratio(self, adjusted, key, name):
        lookup = {d.key: d for d in DISCRIMINATORS}
        return lookup[key].compute(adjusted).loc[name]

    def test_bhvo_2_sits_in_the_mantle_array(self, adjusted):
        """Pearce (2008): an ocean island basalt with no subduction or
        crustal input stays inside the MORB-OIB array, whose measured
        Th/Nb range is 0.043 to 0.096."""
        th_yb = self._ratio(adjusted, "pearce2008.th_yb", "BHVO-2")
        nb_yb = self._ratio(adjusted, "pearce2008.nb_yb", "BHVO-2")
        assert 0.043 <= th_yb / nb_yb <= 0.096
        # And at the ocean-island end of it, not the depleted end.
        assert nb_yb > 5.0

    @pytest.mark.parametrize("name", ["BCR-2", "AGV-2"])
    def test_the_continental_rocks_sit_above_the_array(self, adjusted, name):
        """Both carry a crustal component, which Pearce's Th/Nb > 0.2
        filter is there to catch."""
        th_yb = self._ratio(adjusted, "pearce2008.th_yb", name)
        nb_yb = self._ratio(adjusted, "pearce2008.nb_yb", name)
        assert th_yb / nb_yb > 0.2

    def test_bhvo_2_is_discriminated_as_an_ocean_island_basalt(self,
                                                               adjusted):
        """Verma & Agrawal (2011), the set for basic magmas.

        Panel (c) has no OIB field, so it is inapplicable and is left
        out -- the papers say as much, and their own Turkey case study
        shows a sample landing in the wrong field in that situation.
        """
        for panel, expected in (("IAB_CRBOIB_MORB", "CRB+OIB"),
                                ("IAB_CRB_OIB", "OIB"),
                                ("IAB_OIB_MORB", "OIB"),
                                ("CRB_OIB_MORB", "OIB")):
            probabilities = panel_probabilities(adjusted, "VA11", panel)
            assert probabilities is not None, panel
            scores = {g: probabilities[g].loc["BHVO-2"]
                      for g in PANEL_GROUPS[panel]}
            best = max(scores, key=scores.__getitem__)
            assert best == expected, f"{panel}: {best} at {scores[best]:.0f} %"
            assert scores[best] > 50.0, panel

    def test_bcr_2_is_discriminated_as_continental(self, adjusted):
        """Verma & Verma (2013) Set 2.

        BCR-2 adjusts to about 55 wt.% SiO2, so it is intermediate
        rather than basic and belongs to this set, not to the mafic
        one.  Panel (c) has no CR+OI field and is left out.
        """
        for panel in ("IACA_CROI_COL", "IA_CA_CROI", "IA_CROI_COL",
                      "CA_CROI_COL"):
            probabilities = panel_probabilities(adjusted, "VV13_IMINT", panel)
            assert probabilities is not None, panel
            scores = {g: probabilities[g].loc["BCR-2"]
                      for g in PANEL_GROUPS[panel]}
            best = max(scores, key=scores.__getitem__)
            assert best == "CR+OI", f"{panel}: {best} at {scores[best]:.0f} %"


class TestRockTypeApplicability:
    """A Verma set applied outside its own rock type gives a confident
    wrong answer, and nothing in the app currently says so.

    Documented here rather than asserted as correct behaviour: the
    papers require the rock type to be fixed first, by SINCLAS or
    IgRoCS, and BIRDS does not yet gate the diagrams on it.
    """

    def test_a_basalt_through_the_intermediate_majors_set_misleads(self,
                                                                   adjusted):
        """BHVO-2 is a basalt, so Verma & Verma (2013) Set 1 -- which is
        for intermediate magmas -- does not apply to it.  Fed anyway, it
        answers arc, with no hint that the question was invalid."""
        probabilities = panel_probabilities(adjusted, "VV13_MAJOR",
                                            "IA_CA_COL")
        scores = {g: probabilities[g].loc["BHVO-2"]
                  for g in PANEL_GROUPS["IA_CA_COL"]}
        best = max(scores, key=scores.__getitem__)
        assert best in {"IA", "CA"}
        assert scores[best] > 50.0
        # The mafic set, which does apply, says ocean island instead.
        mafic = panel_probabilities(adjusted, "VA11", "IAB_CRB_OIB")
        mafic_scores = {g: mafic[g].loc["BHVO-2"]
                        for g in PANEL_GROUPS["IAB_CRB_OIB"]}
        assert max(mafic_scores, key=mafic_scores.__getitem__) == "OIB"
