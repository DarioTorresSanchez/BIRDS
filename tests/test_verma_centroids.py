"""Check the Verma discriminant functions against their papers' own output.

Pinning coefficients digit by digit only proves a transcription was not
changed since it was made; it cannot catch one that was wrong when it
was made.  ``tests/test_verma_coefficients.py`` does that job for
``VV13_MAJOR``, and the other seven sets carried ten wrong values that
such a test would never have found.

These papers publish, for every panel, the **group centroid** in DF1-DF2
space, and separately the group mean log-ratios.  A discriminant
function is linear in the log-ratios, so evaluating it at a group's mean
log-ratios must reproduce that group's published centroid exactly.  That
is an end-to-end check of the coefficients, the intercept, the part
order, the denominator and the unit handling at once.

Two things are deliberately left out:

*Merged groups* (``IA+CA``, ``CR+OI``, ``CRB+OIB``).  Their published
centroid is a mean over samples and the papers do not give the group
sizes, so the best this module could do is an unweighted mean of the two
centroids.  That is off by a few tenths, which would force a tolerance
loose enough to hide a real defect.  Only single groups are asserted.

*``V13A_MACID`` groups involving CR.*  The CR column of that paper's
Supplementary Table 5 disagrees with the concentrations printed beside it
in the same table — ln(Fe2O3/SiO2) is given as -1.693 where 1.10 wt.%
over ~70 wt.% SiO2 requires about -4.2, and MnO, MgO, CaO, Na2O and P2O5
are wrong by as much.  The values line up one row below where they
belong, so the column appears to have slipped during typesetting.  The
CR means are therefore not usable as reference data.  The coefficients
of those panels were checked directly against the printed equations
instead.

``V12_ACID`` publishes no centroids, so it is pinned by value; every
figure there was read off the rendered Table 3, pp. 335-336.
"""

from __future__ import annotations

import pytest

from birds.verma_probability import CENTROIDS, VA11_GROUP_MEANS
from birds.diagrams.templates.verma_coefficients import (
    V12_ACID,
    V13A_MACID,
    V13A_MTACID,
    V13A_TACID,
    VA11,
    VV13_IMINT,
    VV13_MAJOR,
    VV13_TRACE,
)

# ---------------------------------------------------------------------------
# Group mean log-ratios, as published
# ---------------------------------------------------------------------------
# Every value below is a published mean of ln(part/denominator), so it is
# already in the units the equations expect and needs no conversion.

#: Verma & Agrawal (2011) Table 2, via the module that derives that
#: set's centroids from it.
VA11_MEANS = VA11_GROUP_MEANS

#: Verma & Verma (2013) Table S4 — intermediate, majors over SiO2.
VV13_MAJOR_MEANS = {
    "IA":  {"TiO2": -4.237, "Al2O3": -1.168, "Fe2O3": -3.367, "FeO": -2.229,
            "MnO": -5.836, "MgO": -2.620, "CaO": -1.928, "Na2O": -2.901,
            "K2O": -4.15, "P2O5": -5.82},
    "CA":  {"TiO2": -4.227, "Al2O3": -1.135, "Fe2O3": -3.421, "FeO": -2.289,
            "MnO": -5.961, "MgO": -2.696, "CaO": -1.986, "Na2O": -2.790,
            "K2O": -4.04, "P2O5": -5.598},
    "CR":  {"TiO2": -3.75, "Al2O3": -1.256, "Fe2O3": -3.285, "FeO": -2.289,
            "MnO": -5.843, "MgO": -3.06, "CaO": -2.38, "Na2O": -2.635,
            "K2O": -3.21, "P2O5": -5.12},
    "OI":  {"TiO2": -3.85, "Al2O3": -1.181, "Fe2O3": -3.436, "FeO": -2.52,
            "MnO": -5.668, "MgO": -3.55, "CaO": -2.81, "Na2O": -2.415,
            "K2O": -3.14, "P2O5": -5.49},
    "Col": {"TiO2": -4.180, "Al2O3": -1.252, "Fe2O3": -3.588, "FeO": -2.589,
            "MnO": -6.278, "MgO": -2.81, "CaO": -2.183, "Na2O": -2.860,
            "K2O": -3.01, "P2O5": -5.19},
}

#: Verma & Verma (2013) Table S6 — intermediate, immobile majors + traces.
VV13_IMINT_MEANS = {
    "IA":  {"MgO": 1.65, "P2O5": -1.598, "Nb": -7.89, "Ni": -6.12,
            "V": -3.713, "Y": -5.894, "Zr": -4.541},
    "CA":  {"MgO": 1.703, "P2O5": -1.341, "Nb": -7.66, "Ni": -5.81,
            "V": -3.822, "Y": -6.078, "Zr": -4.538},
    "CR":  {"MgO": 1.08, "P2O5": -1.39, "Nb": -6.71, "Ni": -5.84,
            "V": -4.62, "Y": -6.319, "Zr": -4.38},
    "OI":  {"MgO": 1.00, "P2O5": -1.86, "Nb": -7.25, "Ni": -5.67,
            "V": -4.651, "Y": -6.715, "Zr": -4.71},
    "Col": {"MgO": 1.368, "P2O5": -1.045, "Nb": -6.410, "Ni": -5.67,
            "V": -4.208, "Y": -5.967, "Zr": -3.770},
}

#: Verma & Verma (2013) Table S8 — intermediate, immobile traces over Yb.
VV13_TRACE_MEANS = {
    "IA":  {"La": 1.27, "Ce": 2.10, "Sm": 0.332, "Nb": 0.09, "Th": -0.45,
            "Y": 2.291, "Zr": 3.568},
    "CA":  {"La": 1.787, "Ce": 2.571, "Sm": 0.613, "Nb": 0.66, "Th": -0.25,
            "Y": 2.333, "Zr": 3.767},
    "CR":  {"La": 2.51, "Ce": 3.18, "Sm": 0.897, "Nb": 2.30, "Th": 0.77,
            "Y": 2.476, "Zr": 4.38},
    "OI":  {"La": 2.76, "Ce": 3.48, "Sm": 1.030, "Nb": 3.02, "Th": 0.42,
            "Y": 2.480, "Zr": 5.02},
    "Col": {"La": 2.97, "Ce": 3.63, "Sm": 1.113, "Nb": 1.89, "Th": 1.76,
            "Y": 2.451, "Zr": 4.50},
}

#: Verma et al. (2013) Supplementary Table 5 — acid, majors over SiO2.
#: The CR column is unusable (see the module docstring) and is omitted.
V13A_MACID_MEANS = {
    "IA":  {"TiO2": -4.878, "Al2O3": -1.528, "Fe2O3": -3.935, "FeO": -3.09,
            "MnO": -6.229, "MgO": -4.12, "CaO": -2.900, "Na2O": -2.820,
            "K2O": -4.007, "P2O5": -6.30},
    "CA":  {"TiO2": -4.754, "Al2O3": -1.422, "Fe2O3": -3.978, "FeO": -3.121,
            "MnO": -6.609, "MgO": -3.84, "CaO": -2.847, "Na2O": -2.754,
            "K2O": -3.420, "P2O5": -6.059},
    "Col": {"TiO2": -5.73, "Al2O3": -1.529, "Fe2O3": -4.79, "FeO": -4.06,
            "MnO": -7.56, "MgO": -5.06, "CaO": -3.91, "Na2O": -2.969,
            "K2O": -2.876, "P2O5": -6.23},
}

#: Verma et al. (2013) Supplementary Table 9 — acid, immobile majors+traces.
V13A_MTACID_MEANS = {
    "IA":  {"MgO": 0.67, "P2O5": -1.382, "Nb": -7.81, "Y": -5.10, "Zr": -3.77},
    "CA":  {"MgO": 0.98, "P2O5": -1.294, "Nb": -6.84, "Y": -5.81, "Zr": -3.793},
    "CR":  {"MgO": 0.06, "P2O5": -2.00, "Nb": -4.95, "Y": -4.50, "Zr": -2.48},
    "OI":  {"MgO": -0.18, "P2O5": -2.34, "Nb": -3.67, "Y": -4.30, "Zr": -1.96},
    "Col": {"MgO": 0.81, "P2O5": -0.59, "Nb": -5.62, "Y": -5.40, "Zr": -3.29},
}

#: Verma et al. (2013) Supplementary Table 13 — acid, immobile traces over Yb.
V13A_TACID_MEANS = {
    "IA":  {"La": 0.96, "Ce": 1.82, "Sm": 0.127, "Nb": -0.42, "Th": -0.79,
            "Y": 2.248, "Zr": 3.597},
    "CA":  {"La": 2.62, "Ce": 3.32, "Sm": 1.00, "Nb": 1.50, "Th": 1.41,
            "Y": 2.402, "Zr": 4.51},
    "CR":  {"La": 2.260, "Ce": 3.072, "Sm": 0.420, "Nb": 1.595, "Th": 1.56,
            "Y": 2.280, "Zr": 4.164},
    "OI":  {"La": 2.543, "Ce": 3.146, "Sm": 0.460, "Nb": 2.909, "Th": 0.4842,
            "Y": 2.3420, "Zr": 4.41},
    "Col": {"La": 3.10, "Ce": 3.77, "Sm": 1.23, "Nb": 2.24, "Th": 2.39,
            "Y": 2.423, "Zr": 4.55},
}

# ---------------------------------------------------------------------------
# Published group centroids
# ---------------------------------------------------------------------------
# The centroids themselves live in birds.verma_probability, which needs
# them at runtime to work out posterior probabilities.  Keeping a second
# copy here would let the two drift apart, so this module filters that
# one instead of restating it.
#
# Merged groups are dropped, for the reason in the module docstring: their
# published centroid is a mean over samples and the papers give no group
# sizes, so the closest this module could get is an unweighted mean of two
# centroids -- off by a few tenths, which would force a tolerance loose
# enough to hide a real defect.

#: Verma & Agrawal (2011) prints boundary coordinates, not centroids, so
#: there is nothing to filter for VA11 -- only its panel names, which the
#: field-membership test below iterates over.
VA11_PANELS = ("IAB_CRBOIB_MORB", "IAB_CRB_OIB", "IAB_CRB_MORB",
               "IAB_OIB_MORB", "CRB_OIB_MORB")


def _single_groups(centroid_key):
    """That set's published centroids, merged groups left out."""
    return {
        panel: {group: xy for group, xy in groups.items() if "+" not in group}
        for panel, groups in CENTROIDS[centroid_key].items()
    }


VV13_MAJOR_CENTROIDS = _single_groups("VV13_MAJOR")
VV13_IMINT_CENTROIDS = _single_groups("VV13_IMINT")
VV13_TRACE_CENTROIDS = _single_groups("VV13_TRACE")
V13A_MACID_CENTROIDS = _single_groups("V13A_MACID")
V13A_MTACID_CENTROIDS = _single_groups("V13A_MTACID")
V13A_TACID_CENTROIDS = _single_groups("V13A_TACID")

#: ``(label, table, means, centroids, base, per_coef)``.  A centroid is
#: accepted within ``base + per_coef * sum(abs(coefficients))``.
#:
#: Two sources of slack, and only two.  ``base`` covers the rounding of
#: the published centroid itself: the intermediate paper prints ten
#: significant figures, so it contributes nothing there, while the acid
#: papers print one decimal in places.  ``per_coef`` covers the rounding
#: of the published group means, which the DF multiplies term by term --
#: so a function whose coefficients sum to 21 inherits five times the
#: slack of one whose coefficients sum to 4.  The papers state their
#: values are "rounded values obtained from the flexible rules
#: summarised by Verma (2005)" rather than to a fixed decimal, so both
#: figures carry a little more slack than half of the last place
#: printed.  One acid centroid (V13A_MTACID, IA-CR+OI-Col, Col) sits
#: 0.013 outside a strict half-a-place budget; its equation, eq (17),
#: was read back off the rendered page and is right to the digit, so
#: the budget is what is loose, not the coefficient.
#:
#: A flat tolerance cannot do this job.  Within V13A_TACID alone the
#: coefficient sums run from 4.4 to 21.5; a tolerance loose enough for
#: the second would have let the Sm coefficient of eq (21), wrong by
#: 0.10 and worth 0.12 at the centroid, pass unnoticed.
SETS = [
    ("VV13_MAJOR", VV13_MAJOR, VV13_MAJOR_MEANS, VV13_MAJOR_CENTROIDS, 0.02, 0.0),
    ("VV13_IMINT", VV13_IMINT, VV13_IMINT_MEANS, VV13_IMINT_CENTROIDS, 0.05, 0.0),
    ("VV13_TRACE", VV13_TRACE, VV13_TRACE_MEANS, VV13_TRACE_CENTROIDS, 0.02, 0.0),
    ("V13A_MACID", V13A_MACID, V13A_MACID_MEANS, V13A_MACID_CENTROIDS, 0.08, 0.006),
    ("V13A_MTACID", V13A_MTACID, V13A_MTACID_MEANS, V13A_MTACID_CENTROIDS, 0.08, 0.006),
    ("V13A_TACID", V13A_TACID, V13A_TACID_MEANS, V13A_TACID_CENTROIDS, 0.08, 0.006),
]


def _centroid(coef, means):
    """DF evaluated at a group's mean log-ratios."""
    return coef.intercept + sum(c * means[p]
                                for p, c in zip(coef.parts, coef.coefs))


def _tolerance(coef, base, per_coef):
    return base + per_coef * sum(abs(c) for c in coef.coefs)


def _cases():
    out = []
    for label, table, means, centroids, base, per_coef in SETS:
        for panel, groups in centroids.items():
            for group, xy in groups.items():
                out.append(pytest.param(label, table, means[group], panel,
                                        group, xy, base, per_coef,
                                        id=f"{label}-{panel}-{group}"))
    return out


@pytest.mark.parametrize(
    "label,table,means,panel,group,published,base,per_coef", _cases())
def test_group_centroid_matches_the_published_one(label, table, means, panel,
                                                  group, published, base,
                                                  per_coef):
    """The DF at a group's mean log-ratios is that group's centroid.

    A wrong coefficient moves the centroid by (error x log-ratio), and
    these log-ratios run to -8, so even a third-decimal slip shows up.
    """
    df1 = table[f"DF1_{panel}"]
    df2 = table[f"DF2_{panel}"]
    got = (_centroid(df1, means), _centroid(df2, means))
    assert got[0] == pytest.approx(
        published[0], abs=_tolerance(df1, base, per_coef)), (
        f"{label} {panel} {group} DF1")
    assert got[1] == pytest.approx(
        published[1], abs=_tolerance(df2, base, per_coef)), (
        f"{label} {panel} {group} DF2")


def test_no_set_drifts_as_a_whole():
    """Every centroid sitting just inside its own bound would still be wrong.

    The per-centroid bounds are worst-case, so a systematic error -- a
    wrong intercept, say -- could hide under them.  In practice the
    residuals are far smaller than the bounds, and this pins that.
    """
    import math

    for label, table, means, centroids, _base, _per in SETS:
        residuals = []
        for panel, groups in centroids.items():
            for group, (px, py) in groups.items():
                m = means[group]
                residuals.append(_centroid(table[f"DF1_{panel}"], m) - px)
                residuals.append(_centroid(table[f"DF2_{panel}"], m) - py)
        rms = math.sqrt(sum(r * r for r in residuals) / len(residuals))
        assert rms < 0.06, f"{label}: RMS residual {rms:.3f}"


class TestVermaAgrawal2011:
    """The basic/ultrabasic set, checked by where its groups land.

    Verma & Agrawal (2011) prints boundary coordinates rather than
    centroids, so the assertion here is the one the diagram is for: each
    group's mean composition falls in that group's own field.
    """

    @pytest.mark.parametrize("panel", VA11_PANELS)
    def test_every_group_lands_in_its_own_field(self, panel):
        from birds.diagrams.templates.verma_coefficients import VA11_FIELDS
        import numpy as np

        geom = VA11_FIELDS[panel]
        tx, ty = geom["triple"]

        def sector(x, y):
            def ang(p):
                return np.arctan2(p[1] - ty, p[0] - tx)
            edges = [(ang(e), set(pair)) for e, pair in geom["boundaries"]]
            a = ang((x, y))
            for name in sorted({n for _, p in edges for n in p}):
                lims = sorted(t for t, p in edges if name in p)
                if len(lims) != 2:
                    continue
                lo, hi = lims
                inside = ((lo <= a <= hi) if (hi - lo) <= np.pi
                          else not (lo < a < hi))
                if inside:
                    return name
            return None

        df1 = VA11[f"DF1_{panel}"]
        df2 = VA11[f"DF2_{panel}"]
        tokens = panel.split("_")
        for group, means in VA11_MEANS.items():
            if group in tokens:
                expected = group
            elif group in ("CRB", "OIB") and "CRBOIB" in tokens:
                expected = "CRB+OIB"
            else:
                continue
            x, y = _centroid(df1, means), _centroid(df2, means)
            assert sector(x, y) == expected, (
                f"{panel}: the {group} mean plots at ({x:.2f}, {y:.2f}), "
                f"in the {sector(x, y)} field")

    @pytest.mark.parametrize("panel", VA11_PANELS)
    def test_every_group_stays_inside_the_published_frame(self, panel):
        """Figure 1 is drawn on (-8, +8).

        Feeding the trace elements in ppm over TiO2 in wt.% would add
        about +40 here, so this also guards the unit handling.
        """
        for axis in ("DF1", "DF2"):
            coef = VA11[f"{axis}_{panel}"]
            for group, means in VA11_MEANS.items():
                value = _centroid(coef, means)
                assert -8.0 <= value <= 8.0, (
                    f"{axis}_{panel} puts the {group} mean at {value:.2f}")


class TestUnits:
    """Where a part and its denominator are reported in different units."""

    #: The three sets that divide ppm trace elements by a wt.% oxide, and
    #: exactly which parts those are.  The other five sets are internally
    #: consistent -- majors over SiO2, or traces over Yb.
    MIXED = {
        "VA11": (VA11, {"Nb", "V", "Y", "Zr"}),
        "VV13_IMINT": (VV13_IMINT, {"Nb", "Ni", "V", "Y", "Zr"}),
        "V13A_MTACID": (V13A_MTACID, {"Nb", "Y", "Zr"}),
    }

    CONSISTENT = {"VV13_MAJOR": VV13_MAJOR, "VV13_TRACE": VV13_TRACE,
                  "V12_ACID": V12_ACID, "V13A_MACID": V13A_MACID,
                  "V13A_TACID": V13A_TACID}

    @pytest.mark.parametrize("label", sorted(MIXED))
    def test_the_ppm_parts_are_declared(self, label):
        table, traces = self.MIXED[label]
        for name, coef in table.items():
            want = tuple(p for p in coef.parts if p in traces)
            assert coef.ppm_parts == want, f"{label} {name}"

    @pytest.mark.parametrize("label", sorted(CONSISTENT))
    def test_a_consistent_set_declares_no_conversion(self, label):
        for name, coef in self.CONSISTENT[label].items():
            assert coef.ppm_parts == (), f"{label} {name}"

    def test_the_diagram_and_the_statistics_table_agree(self):
        """Both read the conversion off the coefficient set.

        It used to live on the diagram classes, so the statistics tables
        -- which reach the same functions by another route -- reported
        values tens of units out.
        """
        import pandas as pd
        from birds.diagrams.templates.verma_multidim import (
            _apply_df, _logratios_for_coef)
        from birds.tectonic_results import DISCRIMINATORS

        sample = pd.DataFrame([{
            "SiO2": 50.5, "TiO2": 1.15, "Al2O3": 15.3, "Fe2O3": 2.0,
            "FeO": 6.0, "MnO": 0.17, "MgO": 7.6, "CaO": 11.3, "Na2O": 2.7,
            "K2O": 0.1, "P2O5": 0.1, "Nb": 2.33, "Ni": 100.0, "V": 250.0,
            "Y": 28.0, "Zr": 74.0, "Yb": 3.05,
        }])
        by_key = {d.key: d for d in DISCRIMINATORS if hasattr(d, "key")}
        checked = 0
        for name, coef in VA11.items():
            key = f"va11.{name.lower()}"
            if key not in by_key:
                continue
            direct = _apply_df(_logratios_for_coef(sample, coef), coef).iloc[0]
            listed = by_key[key].compute(sample).iloc[0]
            assert listed == pytest.approx(direct, abs=1e-9), name
            assert -8.0 <= listed <= 8.0, f"{name} is off the panel: {listed}"
            checked += 1
        assert checked == len(VA11), "not every VA11 function was reached"


class TestVerma2012Acid:
    """V12_ACID publishes no centroids, so it is pinned by value.

    Read off the rendered Table 3 of Verma S.K., Pandarinath K. & Verma
    S.P. (2012) Int. Geol. Rev. 54(3), pp. 335-336.  Seven of these 110
    values were wrong before this test existed, including an Al2O3
    coefficient stored as +1.361050 where the paper prints -0.954629.
    """

    OXIDES = ("TiO2", "Al2O3", "Fe2O3", "FeO", "MnO", "MgO", "CaO",
              "Na2O", "K2O", "P2O5")

    PUBLISHED = {
        "DF1_IACA_CR_COL": ((0.36077, 0.95693, -2.09239, 0.93391, 0.42703,
                             0.18732, 0.45615, 0.56098, -1.65167, -0.15580),
                            -1.58259),
        "DF2_IACA_CR_COL": ((0.472353, -0.954629, 0.109516, 0.699238,
                             0.739533, -0.027717, -0.244687, 0.231677,
                             0.173552, -0.353797), 6.691035),
        "DF1_IA_CA_CR": ((-0.4786, -0.0871, 2.7433, -1.0663, -0.1389,
                          -0.1907, -0.8516, -0.7139, 1.7166, 0.3386), 6.2573),
        "DF2_IA_CA_CR": ((-0.3204, -1.7585, -3.2046, 1.1210, 0.2170,
                          -0.0745, 1.2505, 1.3142, 1.6616, 0.0186), 0.9984),
        "DF1_IA_CA_COL": ((-0.3620, -0.0342, 0.5198, -0.4980, -0.7223,
                           -0.1229, -0.1388, -0.8174, 1.5074, 0.2684),
                          -3.0829),
        "DF2_IA_CA_COL": ((-0.142, 1.984, 1.747, -0.735, -1.226, 0.062,
                           -1.152, -3.189, -2.339, 0.495), -18.190),
        "DF1_IA_CR_COL": ((0.0226, 1.2877, -2.6406, 2.9494, 0.1970, 0.0673,
                           0.0620, 0.6219, -2.0579, -0.0751), -2.1790),
        "DF2_IA_CR_COL": ((0.2786, -1.0544, 0.8267, 0.3032, 0.4084, -0.0905,
                           -0.3260, 0.1518, 0.6698, -0.2261), 6.5170),
        "DF1_CA_CR_COL": ((0.0645, -1.7943, 0.5264, 0.6385, 0.3407, -0.0720,
                           -0.3265, 0.1063, 1.8098, -0.0338), 8.2616),
        "DF2_CA_CR_COL": ((0.8760, 0.8018, 0.2472, -0.8796, 0.7540, -0.0006,
                           -0.0624, -0.2052, -3.3091, -0.3526), -3.8959),
    }

    def test_the_ten_published_functions_are_all_present(self):
        assert set(V12_ACID) == set(self.PUBLISHED)

    @pytest.mark.parametrize("name", sorted(PUBLISHED))
    def test_matches_the_published_equation(self, name):
        coefs, intercept = self.PUBLISHED[name]
        got = V12_ACID[name]
        assert got.parts == self.OXIDES
        assert got.denominator == "SiO2"
        assert got.intercept == intercept
        for oxide, want, have in zip(self.OXIDES, coefs, got.coefs):
            assert have == want, f"{name}: {oxide}"


class TestVerma2013AcidNbSignCorrection:
    """Eq (16) of the acid paper is used with its Nb sign corrected.

    The printed +0.382 puts all three Fig. 3c centroids about five units
    below where the same paper's caption puts them, and the triple point
    five units from the circumcentre of those centroids.  Negating it
    fixes both.  The reasoning is set out at the coefficient itself.
    """

    def test_the_nb_coefficient_is_negative(self):
        coef = V13A_MTACID["DF2_IA_CA_COL"]
        nb = dict(zip(coef.parts, coef.coefs))["Nb"]
        assert nb == -0.382

    def test_the_printed_sign_would_not_reproduce_the_caption(self):
        """Guards the correction: it must still matter."""
        coef = V13A_MTACID["DF2_IA_CA_COL"]
        as_printed = tuple(-c if p == "Nb" else c
                           for p, c in zip(coef.parts, coef.coefs))
        printed = coef.intercept + sum(
            c * V13A_MTACID_MEANS["IA"][p]
            for p, c in zip(coef.parts, as_printed))
        assert abs(printed - 0.39) > 4.0
