"""Verma & Verma (2013) major-element discriminant functions, pinned.

Equations (1)–(10) of *First 15 probability-based multidimensional
tectonic discrimination diagrams for intermediate magmas*, Turkish
J. Earth Sci. 22(6), 931–995, doi:10.3906/yer-1204-6, journal pages
933–935.

The equations are set as embedded objects in the PDF and never reach
its text layer, so they were read off the rendered pages.  Every value
below is a transcription of the printed equation; nothing is rounded
and nothing is derived from the code being tested.

A discriminant function has no separate boundary to fall back on — the
coefficients *are* the boundary — so this file exists to stop one being
"tidied" into a different diagram.
"""

from __future__ import annotations

import numpy as np
import pytest

from birds.diagrams.templates.verma_coefficients import (
    VV13_MAJOR,
    _VV13_PARTS_MAJ,
)

#: Order of the ten oxides in every equation of this set.
OXIDES = ("TiO2", "Al2O3", "Fe2O3", "FeO", "MnO",
          "MgO", "CaO", "Na2O", "K2O", "P2O5")

#: name -> (ten coefficients in OXIDES order, additive constant)
PUBLISHED = {
    # Eq. (1) — DF1(IA+CA-CR+OI-Col)mint
    "DF1_IACA_CROI_COL": (
        (-2.45605, 1.11985, -2.22475, 2.48861, -0.212024,
         -0.06661, 1.29066, -0.28377, -0.40211, 0.030635), -11.43097347),
    # Eq. (2) — DF2(IA+CA-CR+OI-Col)mint
    "DF2_IACA_CROI_COL": (
        (-0.57759, -0.01121, 0.69125, -1.99798, -1.72014,
         0.305275, 0.816018, -1.791727, 0.871298, 0.335479), -12.20158596),
    # Eq. (3) — DF1(IA-CA-CR+OI)mint
    "DF1_IA_CA_CROI": (
        (-2.51880, 0.54210, -3.790190, 3.846277, -0.362718,
         -0.176632, 1.426496, 0.111801, -0.219223, -0.07248), -14.3151255),
    # Eq. (4) — DF2(IA-CA-CR+OI)mint
    "DF2_IA_CA_CROI": (
        (-1.04907, 3.440438, -3.43323, 4.807165, -3.499257,
         0.373928, -2.147775, 3.00229, -0.773719, 1.061808), -13.4885545),
    # Eq. (5) — DF1(IA-CA-Col)mint
    "DF1_IA_CA_COL": (
        (-0.88680, -0.781835, -2.43157, 4.10644, 2.050295,
         -0.386860, -0.74023, 1.35997, -0.816315, -0.468418), 4.31214432),
    # Eq. (6) — DF2(IA-CA-Col)mint
    "DF2_IA_CA_COL": (
        (1.76033, -4.32894, 2.60111, -4.96088, 2.89683,
         -0.362075, 2.23018, -2.96677, 0.790236, -1.326438), 7.586117348),
    # Eq. (7) — DF1(IA-CR+OI-Col)mint
    "DF1_IA_CROI_COL": (
        (-2.43565, 1.53913, -1.51665, 1.45582, 0.4961937,
         -0.050128, 1.258138, -0.8274299, -0.4884699, 0.1123605),
        -7.894955173),
    # Eq. (8) — DF2(IA-CR+OI-Col)mint
    "DF2_IA_CROI_COL": (
        (-0.736658, -0.0788099, 0.065533, -1.130176, -2.130889,
         0.245709, 0.6816946, -1.3284307, 0.7709408, 0.295664),
        -15.24062267),
    # Eq. (9) — DF1(CA-CR+OI-Col)mint
    "DF1_CA_CROI_COL": (
        (-2.32173, 1.97128, -0.537435, 0.431388, -1.139286,
         0.527984, 0.9884038, -0.894467, 0.16138688, 0.0778358),
        -12.34961873),
    # Eq. (10) — DF2(CA-CR+OI-Col)mint
    "DF2_CA_CROI_COL": (
        (-0.40691, 2.60576, 0.1610669, 1.345967, 0.4457959,
         -0.260127, -0.464534, 0.9211739, -1.2769499, -0.142884),
        3.501318155),
}


class TestStructure:
    def test_the_ten_published_functions_are_all_present(self):
        assert set(VV13_MAJOR) == set(PUBLISHED)

    def test_the_oxide_order_is_the_published_one(self):
        assert _VV13_PARTS_MAJ == OXIDES

    def test_iron_enters_as_two_oxides_not_as_a_total(self):
        """The set is calibrated on Fe2O3 and FeO separately; feeding it
        FeOt would be a different function."""
        assert "Fe2O3" in OXIDES and "FeO" in OXIDES
        assert not {"FeOt", "FeOT", "Fe2O3t", "Fe2O3T"} & set(OXIDES)

    def test_every_function_divides_by_silica(self):
        for name, cs in VV13_MAJOR.items():
            assert cs.denominator == "SiO2", name

    def test_every_function_carries_ten_coefficients(self):
        for name, cs in VV13_MAJOR.items():
            assert len(cs.coefs) == len(OXIDES), name


class TestCoefficients:
    @pytest.mark.parametrize("name", sorted(PUBLISHED))
    def test_matches_the_published_equation(self, name):
        want, intercept = PUBLISHED[name]
        got = VV13_MAJOR[name]
        for oxide, w, g in zip(OXIDES, want, got.coefs):
            assert g == pytest.approx(w, abs=0, rel=0), f"{name} {oxide}"
        assert got.intercept == pytest.approx(intercept, abs=0, rel=0), name

    def test_all_hundred_and_ten_values_are_exact(self):
        """Counted, so a function quietly dropped would show up here."""
        checked = 0
        for name, (want, intercept) in PUBLISHED.items():
            cs = VV13_MAJOR[name]
            for w, g in zip(want, cs.coefs):
                assert g == w, name
                checked += 1
            assert cs.intercept == intercept, name
            checked += 1
        assert checked == 110

    def test_no_coefficient_is_a_rounded_stand_in(self):
        """Eight of these were once truncated to five or six figures.
        The full precision is what the paper prints."""
        for name, (want, _c) in PUBLISHED.items():
            for oxide, w, g in zip(OXIDES, want, VV13_MAJOR[name].coefs):
                assert repr(g) == repr(w), f"{name} {oxide}"


class TestBehaviour:
    ANDESITE = dict(SiO2=59.0, TiO2=0.75, Al2O3=17.2, Fe2O3=2.4, FeO=3.6,
                    MnO=0.12, MgO=3.1, CaO=6.4, Na2O=3.6, K2O=1.5,
                    P2O5=0.18)

    def score(self, name, comp):
        cs = VV13_MAJOR[name]
        return cs.intercept + sum(
            c * np.log(comp[o] / comp["SiO2"])
            for c, o in zip(cs.coefs, OXIDES))

    @pytest.mark.parametrize("name", sorted(PUBLISHED))
    def test_a_real_andesite_lands_inside_the_published_frame(self, name):
        """Every panel is drawn on (-8, +8); a score outside it would
        mean the function or its inputs are wrong."""
        assert -8.0 < self.score(name, self.ANDESITE) < 8.0

    def test_the_function_is_sensitive_to_its_coefficients(self):
        """Rounding one is not harmless — the claim this module used to
        make.  A 1 % nudge moves the score by a visible amount."""
        cs = VV13_MAJOR["DF1_IACA_CROI_COL"]
        base = self.score("DF1_IACA_CROI_COL", self.ANDESITE)
        lr = np.log(self.ANDESITE["Al2O3"] / self.ANDESITE["SiO2"])
        nudged = base + 0.01 * cs.coefs[1] * lr
        assert abs(nudged - base) > 1e-3

    def test_the_two_axes_of_a_panel_are_different_functions(self):
        for a, b in (("DF1_IACA_CROI_COL", "DF2_IACA_CROI_COL"),
                     ("DF1_IA_CA_CROI", "DF2_IA_CA_CROI"),
                     ("DF1_IA_CA_COL", "DF2_IA_CA_COL"),
                     ("DF1_IA_CROI_COL", "DF2_IA_CROI_COL"),
                     ("DF1_CA_CROI_COL", "DF2_CA_CROI_COL")):
            assert VV13_MAJOR[a].coefs != VV13_MAJOR[b].coefs
