"""Published log-ratio discriminant-function coefficients for the
Verma & co-authors multidimensional tectonic / classification diagrams.

Coefficient sets are stored as small immutable dataclasses so they can
be cited verbatim from the original papers (see ``source`` field).
Conventions:

* All discriminant functions are linear in **natural-log** ratios of
  the form ``ln(part_i / denominator)`` (Aitchison ``alr``).
* ``intercept`` is the additive constant; ``coefs`` is the vector of
  coefficients applied to ``parts`` in the same order they are listed.
* The boundary between every pair of fields is the iso-value
  ``DF(field_A) = DF(field_B)`` — which, for the published binary DFs,
  reduces to a single threshold on a single axis. The full multi-panel
  figures plot **DFa vs DFb** for two different pairs at a time so the
  user can read the discrimination visually.

Every coefficient here is the published one, digit for digit, and
``tests/test_verma_coefficients.py`` pins them so they stay that way.

Do not "round" one. A discriminant function has no separate boundary
to fall back on: the coefficients *are* the boundary, so editing one
moves the field it divides. An earlier note in this file said that
small numerical edits leave the topology alone; that is false, and it
is the kind of claim that lets a wrong digit survive a review.

Checking a set against its source means matching it to *that* paper —
the intermediate, basic-ultrabasic and acid equations look alike and
comparing one against another's PDF returns a flat zero, which reads
like a catastrophic mismatch and is nothing of the sort. Nor can the
match be done on the PDF text layer alone: several of these equations
are embedded as objects and never appear in the extracted text, so
absence there is no evidence at all. Render the page and read it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Dict, Tuple


@dataclass(frozen=True)
class DFCoefSet:
    """One discriminant function.

    ``DF = intercept + Σ coefs[i] * ln(parts[i] / denominator)``

    ``ppm_parts`` names the parts reported in ppm while the denominator
    is a wt.% oxide.  Those parts are divided by 10 000 before the
    log-ratio is taken, because the published equations were fitted
    with both terms in the *same* unit: "all trace element data
    (μg.g-1) in these equations were first converted to wt.% before
    calculating the trace to major element log-ratios" (Verma 2012,
    acid magmas), and likewise "trace element data were expressed in
    the same unit (wt.%) as the major element (TiO2)adj" (Verma &
    Verma 2013, intermediate magmas).

    This is not a cosmetic detail.  Feeding ppm over wt.% offsets the
    function by ``Σ coefs * ln(10000)`` — about +40 for the four
    Verma & Agrawal (2011) terms, on axes that span ±8.  Every sample
    then lands far outside the diagram.  The unit belongs to the
    coefficient set, not to whatever code happens to evaluate it: it
    lived on the diagram classes before, so the statistics tables —
    which evaluate the same sets by a different route — silently
    reported those +40 values.
    """
    parts: Tuple[str, ...]
    denominator: str
    intercept: float
    coefs: Tuple[float, ...]
    ppm_parts: Tuple[str, ...] = ()


def _traces_in_ppm(table: Dict[str, DFCoefSet],
                   *names: str) -> Dict[str, DFCoefSet]:
    """Tag *names* as ppm parts throughout *table*.

    Applied to the table as a whole rather than written into each
    entry, so the published coefficients above stay verbatim and the
    unit cannot drift between one function of a set and the next.
    """
    return {
        key: replace(coef,
                     ppm_parts=tuple(n for n in names if n in coef.parts))
        for key, coef in table.items()
    }


# ---------------------------------------------------------------------------
# Verma & Verma (2013) — Intermediate magmas, three sets of multidimensional
# discriminant-function diagrams.  Reference: Verma S.P. & Verma S.K. (2013)
# "First 15 probability-based multidimensional tectonic discrimination
# diagrams for intermediate magmas and their robustness against
# postemplacement compositional changes and petrogenetic processes",
# Turkish J Earth Sci 22(6), 931-995, doi:10.3906/yer-1204-6.
#
# Each set provides 5 panels of 3-way (ternary) discrimination, with the
# canonical (-8, +8) × (-8, +8) DF1-DF2 frame and straight boundaries
# radiating from the joint centroid of the training set.
#
#   Set 1 (mint, majors)    — 10 oxides ÷ SiO2_adj
#   Set 2 (imint, mj+trace) — 3 majors + 5 traces ÷ TiO2_adj
#   Set 3 (itrint, traces)  — 7 traces ÷ Yb
#
# Five panels in every set (same layout across the three sets):
#   (a) IA+CA · CR+OI · Col   — Eqs (1)/(2), (11)/(12), (21)/(22)
#   (b) IA · CA · CR+OI       — Eqs (3)/(4), (13)/(14), (23)/(24)
#   (c) IA · CA · Col         — Eqs (5)/(6), (15)/(16), (25)/(26)
#   (d) IA · CR+OI · Col      — Eqs (7)/(8), (17)/(18), (27)/(28)
#   (e) CA · CR+OI · Col      — Eqs (9)/(10), (19)/(20), (29)/(30)
#
# IA  = Island Arc.  CA = Continental Arc.  CR = Continental Rift.
# OI  = Ocean Island.  Col = Collision setting.
# ---------------------------------------------------------------------------

# Set 1 — major elements (TWO Fe oxides separately, NOT FeOt). Order:
# TiO2, Al2O3, Fe2O3, FeO, MnO, MgO, CaO, Na2O, K2O, P2O5.
_VV13_PARTS_MAJ = ("TiO2", "Al2O3", "Fe2O3", "FeO", "MnO",
                   "MgO", "CaO", "Na2O", "K2O", "P2O5")

# Verma & Verma (2013) Eqs (1)–(10) — Set 1 (majors), denominator SiO2_adj.
# The equations run across journal pages 933-935; they are set as embedded
# objects, so they were read off the rendered pages rather than from the
# PDF text layer, and all 110 values were then diffed against the code.
# Order matches _VV13_PARTS_MAJ above.
VV13_MAJOR: Dict[str, DFCoefSet] = {
    # ----- (a) IA+CA · CR+OI · Col  — Eqs (1), (2) ------------------------
    "DF1_IACA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-11.43097347,
        coefs=(-2.45605,  1.11985, -2.22475,  2.48861, -0.212024,
               -0.06661,  1.29066, -0.28377, -0.40211,  0.030635),
    ),
    "DF2_IACA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-12.20158596,
        coefs=(-0.57759, -0.01121,  0.69125, -1.99798, -1.72014,
                0.305275, 0.816018, -1.791727, 0.871298, 0.335479),
    ),
    # ----- (b) IA · CA · CR+OI  — Eqs (3), (4) ---------------------------
    "DF1_IA_CA_CROI": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-14.3151255,
        coefs=(-2.51880,  0.54210, -3.790190, 3.846277, -0.362718,
               -0.176632, 1.426496, 0.111801, -0.219223, -0.07248),
    ),
    "DF2_IA_CA_CROI": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-13.4885545,
        coefs=(-1.04907,  3.440438, -3.43323,  4.807165, -3.499257,
                0.373928, -2.147775, 3.00229, -0.773719, 1.061808),
    ),
    # ----- (c) IA · CA · Col  — Eqs (5), (6) -----------------------------
    "DF1_IA_CA_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=4.31214432,
        coefs=(-0.88680, -0.781835, -2.43157,  4.10644,  2.050295,
               -0.386860, -0.74023,  1.35997, -0.816315, -0.468418),
    ),
    "DF2_IA_CA_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=7.586117348,
        coefs=( 1.76033, -4.32894,  2.60111, -4.96088,  2.89683,
               -0.362075, 2.23018, -2.96677,  0.790236, -1.326438),
    ),
    # ----- (d) IA · CR+OI · Col  — Eqs (7), (8) --------------------------
    "DF1_IA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-7.894955173,
        coefs=(-2.43565,  1.53913, -1.51665,  1.45582,  0.4961937,
               -0.050128, 1.258138, -0.8274299, -0.4884699, 0.1123605),
    ),
    "DF2_IA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-15.24062267,
        coefs=(-0.736658, -0.0788099, 0.065533, -1.130176, -2.130889,
                0.245709,  0.6816946, -1.3284307, 0.7709408, 0.295664),
    ),
    # ----- (e) CA · CR+OI · Col  — Eqs (9), (10) -------------------------
    "DF1_CA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-12.34961873,
        coefs=(-2.32173,  1.97128, -0.537435, 0.431388, -1.139286,
                0.527984, 0.9884038, -0.894467, 0.16138688, 0.0778358),
    ),
    "DF2_CA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=3.501318155,
        coefs=(-0.40691,  2.60576,  0.1610669, 1.345967, 0.4457959,
               -0.260127, -0.464534, 0.9211739, -1.2769499, -0.142884),
    ),
}


# ---------------------------------------------------------------------------
# VV13_MAJOR — Canonical field boundary geometry (Verma & Verma 2013, Fig 1)
# ---------------------------------------------------------------------------
# Each panel has a single triple-point inside the (-8, +8) frame plus three
# straight boundary segments radiating from the triple-point to the diagram
# edge.  Coordinates verbatim from the Figure 1 caption (PDF page 8 of the
# Verma_Intermediate.pdf, journal page 937 of Turkish J. Earth Sci).
VV13_MAJOR_FIELDS: Dict[str, Dict] = {
    "IACA_CROI_COL": {
        "triple": (-0.67554, 0.27663),
        "boundaries": (
            ((0.42744, -8.00000), ("IA+CA", "CR+OI")),
            ((8.00000,  5.33331), ("IA+CA", "Col")),
            ((-8.00000, 4.73569), ("CR+OI", "Col")),
        ),
    },
    "IA_CA_CROI": {
        "triple": (-0.63205, 0.08764),
        "boundaries": (
            ((8.00000,  7.69690), ("IA", "CA")),
            ((-1.50230, -8.00000), ("IA", "CR+OI")),
            ((-2.73408, 8.00000), ("CA", "CR+OI")),
        ),
    },
    "IA_CA_COL": {
        "triple": (-0.71170, 0.24138),
        "boundaries": (
            ((8.00000, -3.06676), ("IA", "CA")),
            ((-1.18110, 8.00000), ("IA", "Col")),
            ((-3.55140, -8.00000), ("CA", "Col")),
        ),
    },
    "IA_CROI_COL": {
        "triple": (-0.44102, 0.17933),
        "boundaries": (
            ((0.66776, -8.00000), ("IA", "CR+OI")),
            ((8.00000,  6.27226), ("IA", "Col")),
            ((-8.00000, 4.24657), ("CR+OI", "Col")),
        ),
    },
    "CA_CROI_COL": {
        "triple": (-0.033967, -0.10097),
        "boundaries": (
            ((-3.42497, 8.00000), ("CA", "CR+OI")),
            ((8.00000, -0.16286), ("CA", "Col")),
            ((-4.17272, -8.00000), ("CR+OI", "Col")),
        ),
    },
}


# ---------------------------------------------------------------------------
# Set 2 — Immobile majors + immobile traces.  Order:
# MgO, P2O5, Nb, Ni, V, Y, Zr.
# Denominator: TiO2_adj.  Traces are in ppm but TiO2 in wt%, so the trace
# numerators are converted ppm → wt% (÷ 10 000) BEFORE the log-ratio is
# computed (see VermaVerma2013ImMint in verma_multidim.py).
# ---------------------------------------------------------------------------

_VV13_PARTS_IMINT = ("MgO", "P2O5", "Nb", "Ni", "V", "Y", "Zr")

VV13_IMINT: Dict[str, DFCoefSet] = {
    # ----- (a) IA+CA · CR+OI · Col  — Eqs (11), (12) ----------------------
    "DF1_IACA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=1.90072648,
        coefs=(1.02293,  0.63053,  -0.93889,  -0.41538,
               1.676898, 0.453813,  0.5831823),
    ),
    "DF2_IACA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=-18.63750138,
        coefs=(0.248529, -0.477177, -0.336281, -0.131072,
               -1.712035, 0.213840, -2.008435),
    ),
    # ----- (b) IA · CA · CR+OI  — Eqs (13), (14) -------------------------
    "DF1_IA_CA_CROI": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=8.228368089,
        coefs=(0.8750597, 0.4279822, -0.6864967, -0.372419,
               1.924254,  0.835240,   0.8428416),
    ),
    "DF2_IA_CA_CROI": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=12.45160186,
        coefs=(-1.171625, -2.650912, 0.176065, 0.1183849,
               -0.18532798, 1.9213464, 0.3868149),
    ),
    # ----- (c) IA · CA · Col  — Eqs (15), (16) ---------------------------
    "DF1_IA_CA_COL": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=8.108721398,
        coefs=(-0.801371, 0.125028,   0.908386,  0.320442,
               -0.3683636, -0.6405806, 0.72337227),
    ),
    "DF2_IA_CA_COL": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=-20.63036447,
        coefs=(1.317201, 2.199955, -0.1235449, -0.1339918,
               -0.8720114, -1.7825807, -1.36498299),
    ),
    # ----- (d) IA · CR+OI · Col  — Eqs (17), (18) ------------------------
    "DF1_IA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=-4.468550646,
        coefs=(-0.85601, -0.300589,  0.861909,  0.384727,
               -1.5827037, -0.757282, -0.692422),
    ),
    "DF2_IA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=-17.04082095,
        coefs=(0.21504,  -0.503675, -0.32252,  -0.122383,
               -1.7097486, 0.426039, -1.980676),
    ),
    # ----- (e) CA · CR+OI · Col  — Eqs (19), (20) ------------------------
    "DF1_CA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=5.752160917,
        coefs=(-1.255543, -1.1082014,  1.437934,  0.5454469,
               -1.6196297,  0.3368725, -0.71359906),
    ),
    "DF2_CA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_IMINT, denominator="TiO2",
        intercept=-21.02758313,
        coefs=(-0.02400, -0.054413, -0.8608025, -0.174160,
               -1.6407186, 0.068523, -1.772088),
    ),
}

# MgO and P2O5 are already wt.%; the five traces are not.  Section 3.2:
# "for all trace to major element loge-ratios, trace element data were
# expressed in the same unit (wt.%) as the major element (TiO2)adj".
VV13_IMINT = _traces_in_ppm(VV13_IMINT, "Nb", "Ni", "V", "Y", "Zr")


# ---------------------------------------------------------------------------
# VV13_IMINT — Canonical field boundary geometry (Verma & Verma 2013, Fig 2)
# ---------------------------------------------------------------------------
# Coordinates verbatim from the Figure 2 caption (PDF page 12, journal page
# 941 of Turkish J. Earth Sci).
VV13_IMINT_FIELDS: Dict[str, Dict] = {
    "IACA_CROI_COL": {
        "triple": (-0.82858, 0.29965),
        "boundaries": (
            ((0.92190,  8.00000), ("IA+CA", "CR+OI")),
            ((6.39297, -8.00000), ("IA+CA", "Col")),
            ((-8.00000, -4.20284), ("CR+OI", "Col")),
        ),
    },
    "IA_CA_CROI": {
        "triple": (-0.95018, 0.45941),
        "boundaries": (
            ((8.00000, -3.76290), ("IA", "CA")),
            ((-1.24490, 8.00000), ("IA", "CR+OI")),
            ((-3.40451, -8.00000), ("CA", "CR+OI")),
        ),
    },
    "IA_CA_COL": {
        "triple": (0.60491, -0.23211),
        "boundaries": (
            ((-8.00000, 3.73126), ("IA", "CA")),
            ((0.95093, -8.00000), ("IA", "Col")),
            ((4.00195,  8.00000), ("CA", "Col")),
        ),
    },
    "IA_CROI_COL": {
        "triple": (0.62149, 0.34939),
        "boundaries": (
            ((-0.87616, 8.00000), ("IA", "CR+OI")),
            ((-6.61289, -8.00000), ("IA", "Col")),
            ((8.00000, -4.51524), ("CR+OI", "Col")),
        ),
    },
    "CA_CROI_COL": {
        "triple": (-0.028516, 0.35743),
        "boundaries": (
            ((-1.16430, 8.00000), ("CA", "CR+OI")),
            ((-7.33632, -8.00000), ("CA", "Col")),
            ((8.00000, -3.84452), ("CR+OI", "Col")),
        ),
    },
}


# ---------------------------------------------------------------------------
# Set 3 — Immobile trace elements only.  Order:
# La, Ce, Sm, Nb, Th, Y, Zr.
# Denominator: Yb.  All numerators and denominator are in ppm — units
# cancel, no conversion needed.
# ---------------------------------------------------------------------------

_VV13_PARTS_TR = ("La", "Ce", "Sm", "Nb", "Th", "Y", "Zr")

VV13_TRACE: Dict[str, DFCoefSet] = {
    # ----- (a) IA+CA · CR+OI · Col  — Eqs (21), (22) ----------------------
    "DF1_IACA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-3.815745639,
        coefs=(-0.1672589, -1.2542899, 1.295171,  1.3318361,
                0.2698636,  1.9286976, 0.18097357),
    ),
    "DF2_IACA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-3.305510646,
        coefs=(-0.2426713,  1.7265475, 0.4902224, -1.2755648,
                0.9602491,  0.8511852, -0.4894082),
    ),
    # ----- (b) IA · CA · CR+OI  — Eqs (23), (24) -------------------------
    "DF1_IA_CA_CROI": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-3.3845534709,
        coefs=(0.0178001, -1.2689712, 1.7407108, 1.324421438,
               0.0288819,  1.580888497, 0.17161461),
    ),
    "DF2_IA_CA_CROI": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-0.2920468400,
        coefs=(-2.099551, -2.044178, -0.41179008, 1.022466699,
                1.24448424,  1.87700276, 1.07017399797),
    ),
    # ----- (c) IA · CA · Col  — Eqs (25), (26) ---------------------------
    "DF1_IA_CA_COL": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-5.801482381,
        coefs=(0.092724, 0.752143, 0.9296053, 0.12351021,
               0.3479451, 1.472513, -0.0339674),
    ),
    "DF2_IA_CA_COL": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-3.684349292,
        coefs=(-2.038286, -0.073322, -1.360432, -0.07828951,
                1.8248761,  2.7738488, 0.44440139),
    ),
    # ----- (d) IA · CR+OI · Col  — Eqs (27), (28) ------------------------
    "DF1_IA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-2.9336489118,
        coefs=(0.7208951, -1.352147, 1.378563, 1.1641465,
               -0.0423769, 1.5584709, -0.1644980),
    ),
    "DF2_IA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=4.154732286,
        coefs=(0.2378909, -2.03548886, -0.2501036699, 1.34733326,
               -0.760673982, -0.786605747, 0.37736968328),
    ),
    # ----- (e) CA · CR+OI · Col  — Eqs (29), (30) ------------------------
    "DF1_CA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-0.87680549008,
        coefs=(-0.977026, -1.3886489, 1.36560, 1.8999127,
                0.5690460,  1.65772638, -0.30523813),
    ),
    "DF2_CA_CROI_COL": DFCoefSet(
        parts=_VV13_PARTS_TR, denominator="Yb",
        intercept=-3.915383182,
        coefs=(-0.086967, 1.1636159, 0.3635930, -0.90127239,
                1.1257989, 1.19149068, -0.39964298),
    ),
}


# ---------------------------------------------------------------------------
# VV13_TRACE — Canonical field boundary geometry (Verma & Verma 2013, Fig 3)
# ---------------------------------------------------------------------------
# Coordinates verbatim from the Figure 3 caption (PDF page 14, journal page
# 943 of Turkish J. Earth Sci).
VV13_TRACE_FIELDS: Dict[str, Dict] = {
    "IACA_CROI_COL": {
        "triple": (0.64148, 0.34301),
        "boundaries": (
            ((-0.69292, -8.00000), ("IA+CA", "CR+OI")),
            ((-6.91145, 8.00000), ("IA+CA", "Col")),
            ((8.00000, 3.04640), ("CR+OI", "Col")),
        ),
    },
    "IA_CA_CROI": {
        "triple": (0.58959, 0.68699),
        "boundaries": (
            ((-8.00000, -5.45793), ("IA", "CA")),
            ((0.87619, 8.00000), ("IA", "CR+OI")),
            ((3.67939, -8.00000), ("CA", "CR+OI")),
        ),
    },
    "IA_CA_COL": {
        "triple": (0.90473, 0.82230),
        "boundaries": (
            ((-8.00000, -7.28196), ("IA", "CA")),
            ((0.64537, 8.00000), ("IA", "Col")),
            ((4.86730, -8.00000), ("CA", "Col")),
        ),
    },
    "IA_CROI_COL": {
        "triple": (0.37157, -0.26385),
        "boundaries": (
            ((-0.87235, 8.00000), ("IA", "CR+OI")),
            ((-6.10890, -8.00000), ("IA", "Col")),
            ((8.00000, -2.82217), ("CR+OI", "Col")),
        ),
    },
    "CA_CROI_COL": {
        "triple": (-0.15459, 0.29462),
        "boundaries": (
            ((-0.10284, -8.00000), ("CA", "CR+OI")),
            ((-8.00000, 5.41425), ("CA", "Col")),
            ((8.00000, 4.74335), ("CR+OI", "Col")),
        ),
    },
}


# ---------------------------------------------------------------------------
# Verma & Agrawal (2011) - basic + ultrabasic rocks, immobile-trace DF set
# ---------------------------------------------------------------------------
# Canonical equations from Verma S.P. & Agrawal S. (2011), J. Geol. Soc.
# India 79, 519-525. Reproduced verbatim from Verma S.P. (2021) "Road to
# Geochemistry", Eqs. (12.74)–(12.83), pp. 515–517.
#
# Variables: Nb, V, Y, Zr — each divided by TiO2 in wt %, both adjusted
# to 100 % anhydrous (the ``adj`` subscript in the paper).  The four
# trace elements are in ppm except TiO2 which is in wt %.
#
# Five panels, each discriminating THREE tectonic groups (not pairs!):
#   (a) IAB · CRB+OIB · MORB    (Eqs 12.74 / 12.75)
#   (b) IAB · CRB · OIB         (Eqs 12.76 / 12.77)
#   (c) IAB · CRB · MORB        (Eqs 12.78 / 12.79)
#   (d) IAB · OIB · MORB        (Eqs 12.80 / 12.81)
#   (e) CRB · OIB · MORB        (Eqs 12.82 / 12.83)
#
# The "t2" subscript stays in the keys to remind future maintainers that
# this is the second trace-element-based set (first was Agrawal et al.
# 2008); we use shorter panel ids in the templates.
# ---------------------------------------------------------------------------

_VA11_PARTS = ("Nb", "V", "Y", "Zr")

VA11: Dict[str, DFCoefSet] = {
    # ----- Panel (a) IAB · CRB+OIB · MORB  — Eq 12.74 / 12.75 -------------
    "DF1_IAB_CRBOIB_MORB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=21.3603,
        coefs=(-0.6611, 2.2926, 1.6774, 1.0916),
    ),
    "DF2_IAB_CRBOIB_MORB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=4.8487,
        coefs=(0.4702, 3.7649, -3.9110, 2.2697),
    ),
    # ----- Panel (b) IAB · CRB · OIB  — Eq 12.76 / 12.77 -----------------
    "DF1_IAB_CRB_OIB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=22.7253,
        coefs=(-0.6146, 2.3510, 1.6828, 1.1911),
    ),
    "DF2_IAB_CRB_OIB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=22.2450,
        coefs=(1.3765, -0.9452, 4.0461, -2.0789),
    ),
    # ----- Panel (c) IAB · CRB · MORB  — Eq 12.78 / 12.79 ---------------
    "DF1_IAB_CRB_MORB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=18.7466,
        coefs=(-0.6624, 2.4498, 1.2867, 1.0920),
    ),
    "DF2_IAB_CRB_MORB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=3.3163,
        coefs=(0.4938, 3.4741, -3.8053, 2.0070),
    ),
    # ----- Panel (d) IAB · OIB · MORB  — Eq 12.80 / 12.81 ---------------
    "DF1_IAB_OIB_MORB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=32.9472,
        coefs=(-0.2646, 2.0491, 3.4565, 0.8573),
    ),
    "DF2_IAB_OIB_MORB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=0.1995,
        coefs=(0.01874, 4.0937, -4.8550, 2.9900),
    ),
    # ----- Panel (e) CRB · OIB · MORB  — Eq 12.82 / 12.83 ---------------
    "DF1_CRB_OIB_MORB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=16.0941,
        coefs=(-0.7829, 0.3379, 3.3239, -0.51232),
    ),
    "DF2_CRB_OIB_MORB": DFCoefSet(
        parts=_VA11_PARTS, denominator="TiO2",
        intercept=28.3592,
        coefs=(1.7478, -0.0421, 3.5301, -1.4503),
    ),
}

# Table 2 of Verma & Agrawal (2011) reports (TiO2)adj *and* the traces in
# ug/g, so every published ln-ratio is a ratio of like units.  Reading its
# mean ln(Nb/(TiO2)adj) = -8.18 for IAB back against (TiO2)adj = 9310 ug/g
# recovers Nb = 2.6 ug/g; treating TiO2 as wt.% would demand ln = +1.03.
VA11 = _traces_in_ppm(VA11, "Nb", "V", "Y", "Zr")


# ---------------------------------------------------------------------------
# VA11 — Canonical field boundary geometry (Verma & Agrawal 2011, Figure 1)
# ---------------------------------------------------------------------------
# Each panel has a single triple-point inside the (-8, +8) frame, plus three
# straight boundary segments that radiate from the triple-point and end at the
# diagram's outer edge.  Coordinates are taken verbatim from the Figure 1
# caption (page 8 of the PDF, journal page 31).  Each boundary lists the
# outer endpoint and the two group names it separates.
VA11_FIELDS: Dict[str, Dict] = {
    "IAB_CRBOIB_MORB": {
        "triple": (0.63849, 0.87812),
        "boundaries": (
            ((0.02820,  8.00000), ("IAB", "CRB+OIB")),
            ((-3.23180, -8.00000), ("CRB+OIB", "MORB")),
            ((8.00000, -4.55320), ("IAB", "MORB")),
        ),
    },
    "IAB_CRB_OIB": {
        "triple": (0.883172, -0.667465),
        "boundaries": (
            ((2.27820,  8.00000), ("IAB", "CRB")),
            ((-8.00000, 1.66740), ("CRB", "OIB")),
            ((1.87600, -8.00000), ("OIB", "IAB")),
        ),
    },
    "IAB_CRB_MORB": {
        "triple": (-0.016496, 0.972583),
        "boundaries": (
            ((-0.43580, 8.00000), ("IAB", "CRB")),
            ((8.00000, -5.79920), ("IAB", "MORB")),
            ((-4.19440, -8.00000), ("CRB", "MORB")),
        ),
    },
    "IAB_OIB_MORB": {
        "triple": (-0.322489, 1.040295),
        "boundaries": (
            ((-0.81840, 8.00000), ("IAB", "OIB")),
            ((8.00000, -4.36500), ("IAB", "MORB")),
            ((-3.72100, -8.00000), ("OIB", "MORB")),
        ),
    },
    "CRB_OIB_MORB": {
        "triple": (1.129586, -0.4194316),
        "boundaries": (
            ((-8.00000, 1.48500), ("CRB", "OIB")),
            ((3.32100,  8.00000), ("CRB", "MORB")),
            ((2.43000, -8.00000), ("OIB", "MORB")),
        ),
    },
}


# ---------------------------------------------------------------------------
# Verma et al. (2012) — Acid (granitic / felsic) rocks, 5 triplet panels
# ---------------------------------------------------------------------------
# Canonical equations from Verma S.K., Pandarinath K. & Rivera-Gomez M.A.
# (2012) "Statistical evaluation of tectonomagmatic discrimination diagrams
# for granitic rocks and proposal of new discriminant-function-based
# multidimensional diagrams for acid magmas", International Geology Review
# 54(3), 325-347. Table 3 (pp. 335-336), Eqs (1)–(10).
#
# Acid rocks are not produced in significant amounts in MORB or OIB
# settings, so the discrimination distinguishes only 4 tectonic groups:
# IA (Island Arc), CA (Continental Arc), CR (Continental Rift), Col
# (Collision).
#
# Five panels, each discriminating THREE groups at a time:
#   (A) IA+CA · CR · Col    — combined arcs vs CR vs Col (Eqs 1, 2)
#   (B) IA · CA · CR        — Eqs (3), (4)
#   (C) IA · CA · Col       — Eqs (5), (6)
#   (D) IA · CR · Col       — Eqs (7), (8)
#   (E) CA · CR · Col       — Eqs (9), (10)
#
# Variables (10 oxides ÷ SiO2_adj, Middlemost-adjusted) — order:
# TiO2, Al2O3, Fe2O3, FeO, MnO, MgO, CaO, Na2O, K2O, P2O5.
# ---------------------------------------------------------------------------

V12_ACID: Dict[str, DFCoefSet] = {
    # ----- (A) IA+CA · CR · Col  — Eqs (1), (2) ---------------------------
    "DF1_IACA_CR_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-1.58259,
        coefs=(0.36077,  0.95693, -2.09239, 0.93391, 0.42703,
               0.18732,  0.45615, 0.56098, -1.65167, -0.15580),
    ),
    "DF2_IACA_CR_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=6.691035,
        coefs=(0.472355, 1.36105, 0.109516, 0.699238, 0.739533,
              -0.027717, -0.244687, 0.231677, 0.173552, -0.353797),
    ),
    # ----- (B) IA · CA · CR  — Eqs (3), (4) ------------------------------
    "DF1_IA_CA_CR": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=6.2573,
        coefs=(-0.4786, -0.0871,  2.7433, -1.0665, -0.1389,
               -0.1907, -0.8516, -0.7139,  1.7166,  0.3386),
    ),
    "DF2_IA_CA_CR": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=0.9984,
        coefs=(-0.3204, -1.7185, -3.2046, 1.1210,  0.2170,
               -0.0745,  1.2505,  1.3142,  1.6616,  0.0186),
    ),
    # ----- (C) IA · CA · Col  — Eqs (5), (6) -----------------------------
    "DF1_IA_CA_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-3.0829,
        coefs=(-0.3620, -0.0342,  0.5198, -0.4980, -0.7223,
               -0.1229, -0.1388, -0.8174,  1.5074,  0.2684),
    ),
    "DF2_IA_CA_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-18.190,
        coefs=(-0.142,   1.984,   1.747, -0.735, -1.226,
                0.062,  -1.152, -3.189, -2.339,   0.495),
    ),
    # ----- (D) IA · CR · Col  — Eqs (7), (8) -----------------------------
    "DF1_IA_CR_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-2.1790,
        coefs=(0.0226,   1.2877, -2.6406,  2.9494,  0.1970,
               0.0673,   0.0620,  0.6219, -2.0579, -0.0751),
    ),
    "DF2_IA_CR_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=6.5170,
        coefs=(0.2786,  -1.0544,  0.8267,  0.3032, -0.4084,
              -0.0905, -0.3260,  0.1518,  0.6698, -0.2261),
    ),
    # ----- (E) CA · CR · Col  — Eqs (9), (10) ----------------------------
    "DF1_CA_CR_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=8.2616,
        coefs=(0.0645,  -1.7943,  0.0264,  0.6385,  0.3407,
              -0.0720, -0.3265,  0.1063,  1.8098, -0.0358),
    ),
    "DF2_CA_CR_COL": DFCoefSet(
        parts=_VV13_PARTS_MAJ, denominator="SiO2",
        intercept=-3.8959,
        coefs=(0.8760,   0.8018,  0.2472, -0.8796,  0.7540,
              -0.0006, -0.0624, -0.2052, -3.3091, -0.3526),
    ),
}


# ---------------------------------------------------------------------------
# V12_ACID — Canonical field boundary geometry (Verma et al. 2012, Fig 5)
# ---------------------------------------------------------------------------
# Coordinates verbatim from the Figure 5 caption (PDF page 14 of the
# Verma_Acid.pdf, journal page 337).
V12_ACID_FIELDS: Dict[str, Dict] = {
    "IACA_CR_COL": {
        "triple": (-0.52237, 0.105108),
        "boundaries": (
            ((3.0914,  8.00000), ("IA+CA", "CR")),
            ((6.5177, -8.00000), ("IA+CA", "Col")),
            ((-8.00000, -1.6511), ("CR", "Col")),
        ),
    },
    "IA_CA_CR": {
        "triple": (0.41929, -0.66705),
        "boundaries": (
            ((-8.00000, 4.7147), ("IA", "CA")),
            ((1.0939, -8.00000), ("IA", "CR")),
            ((4.1608,  8.00000), ("CA", "CR")),
        ),
    },
    "IA_CA_COL": {
        "triple": (0.13893, 1.18829),
        "boundaries": (
            ((-6.8768, -8.00000), ("IA", "CA")),
            ((0.13989, 8.00000), ("IA", "Col")),
            ((4.1472, -8.00000), ("CA", "Col")),
        ),
    },
    "IA_CR_COL": {
        "triple": (0.20518, -0.01689),
        "boundaries": (
            ((4.7956,  8.00000), ("IA", "CR")),
            ((2.1584, -8.00000), ("IA", "Col")),
            ((-8.00000, 1.6186), ("CR", "Col")),
        ),
    },
    "CA_CR_COL": {
        "triple": (0.22442, 0.015552),
        "boundaries": (
            ((4.6620,  8.00000), ("CA", "CR")),
            ((-8.00000, 0.53675), ("CA", "Col")),
            ((3.3907, -8.00000), ("CR", "Col")),
        ),
    },
}


# ---------------------------------------------------------------------------
# Verma, Pandarinath, Verma & Agrawal (2013) — Acid rocks, Set 1 (majors)
# ---------------------------------------------------------------------------
# Canonical equations from Verma S.P., Pandarinath K., Verma S.K., Agrawal S.
# (2013) "Fifteen new discriminant-function-based multi-dimensional robust
# diagrams for acid rocks and their application to Precambrian rocks",
# Lithos 168-169, 113-123.  Supplementary Table 5, Eqs. (1)–(10).
#
# Acid rocks discrimination among 4 tectonic settings:
#   IA (Island Arc), CA (Continental Arc), CR+OI (Continental Rift +
#   Ocean Island combined), Col (Collision).
#
# Five panels, each discriminating THREE groups at a time:
#   (a) IA+CA · CR+OI · Col   — Eqs (1), (2) [10 majors]
#   (b) IA · CA · CR+OI       — Eqs (3), (4) [9 majors — no Al2O3]
#   (c) IA · CA · Col         — Eqs (5), (6) [9 majors — no CaO]
#   (d) IA · CR+OI · Col      — Eqs (7), (8) [7 majors — no Fe2O3, FeO, MgO]
#   (e) CA · CR+OI · Col      — Eqs (9), (10) [9 majors — no CaO]
#
# Each equation uses a different subset of the 10 majors as selected by the
# LDA (stepwise variable selection); the parts tuple in each DFCoefSet
# lists only the variables with non-zero contribution.
# ---------------------------------------------------------------------------

_V13A_ALL10  = ("TiO2", "Al2O3", "Fe2O3", "FeO", "MnO",
                "MgO", "CaO", "Na2O", "K2O", "P2O5")
_V13A_NO_AL  = ("TiO2",          "Fe2O3", "FeO", "MnO",
                "MgO", "CaO", "Na2O", "K2O", "P2O5")
_V13A_NO_CA  = ("TiO2", "Al2O3", "Fe2O3", "FeO", "MnO",
                "MgO",        "Na2O", "K2O", "P2O5")
_V13A_NO_FE_MG = ("TiO2", "Al2O3",                "MnO",
                          "CaO", "Na2O", "K2O", "P2O5")

V13A_MACID: Dict[str, DFCoefSet] = {
    # ----- (a) IA+CA · CR+OI · Col  — Eqs (1), (2) ------------------------
    "DF1_IACA_CROI_COL": DFCoefSet(
        parts=_V13A_ALL10, denominator="SiO2",
        intercept=-2.12,
        coefs=(0.051,  0.226, -1.77,  1.83,  -0.065,
               0.134,  0.225,  0.742, -1.78,  0.146),
    ),
    "DF2_IACA_CROI_COL": DFCoefSet(
        parts=_V13A_ALL10, denominator="SiO2",
        intercept=2.54,
        coefs=(1.09,  -1.65,  -1.19,  1.03,   0.82,
               0.026, 0.023,  0.12,   0.085, -0.85),
    ),
    # ----- (b) IA · CA · CR+OI  — Eqs (3), (4)  [no Al2O3] ----------------
    "DF1_IA_CA_CROI": DFCoefSet(
        parts=_V13A_NO_AL, denominator="SiO2",
        intercept=2.65,
        coefs=(0.130, 0.62, -0.76, -0.083, -0.147,
              -0.239, -0.520, 2.04, -0.164),
    ),
    "DF2_IA_CA_CROI": DFCoefSet(
        parts=_V13A_NO_AL, denominator="SiO2",
        intercept=-2.98,
        coefs=(-0.045, 5.10, -5.15, 1.16, -0.453,
               -0.451, -2.45, -1.40, 0.0017),
    ),
    # ----- (c) IA · CA · Col  — Eqs (5), (6)  [no CaO] --------------------
    "DF1_IA_CA_COL": DFCoefSet(
        parts=_V13A_NO_CA, denominator="SiO2",
        intercept=-3.22,
        coefs=(-0.489, 2.27, 0.62, -1.24, -0.91,
               0.156, -1.23, 1.15, 0.409),
    ),
    "DF2_IA_CA_COL": DFCoefSet(
        parts=_V13A_NO_CA, denominator="SiO2",
        intercept=12.69,
        coefs=(0.68, 2.24, -3.90, 3.69, -0.374,
               0.255, 3.04, 1.16, -0.226),
    ),
    # ----- (d) IA · CR+OI · Col  — Eqs (7), (8)  [no Fe2O3,FeO,MgO] -------
    "DF1_IA_CROI_COL": DFCoefSet(
        parts=_V13A_NO_FE_MG, denominator="SiO2",
        intercept=4.29,
        coefs=(-0.144, -0.74, -0.443,
               0.075, 0.383, 2.58, -0.0243),
    ),
    "DF2_IA_CROI_COL": DFCoefSet(
        parts=_V13A_NO_FE_MG, denominator="SiO2",
        intercept=-2.60,
        coefs=(-0.87, 1.54, -0.75,
               0.023, 0.150, -0.320, 0.75),
    ),
    # ----- (e) CA · CR+OI · Col  — Eqs (9), (10)  [no CaO] ----------------
    "DF1_CA_CROI_COL": DFCoefSet(
        parts=_V13A_NO_CA, denominator="SiO2",
        intercept=-4.33,
        coefs=(-0.0218, 1.06, -1.65, 1.89, -0.296,
               0.119, 0.65, -2.43, 0.212),
    ),
    "DF2_CA_CROI_COL": DFCoefSet(
        parts=_V13A_NO_CA, denominator="SiO2",
        intercept=-0.92,
        coefs=(-1.08, 1.63, 0.99, -0.80, -0.78,
               -0.018, -0.223, 0.65, 0.73),
    ),
}


# ---------------------------------------------------------------------------
# V13A_MACID — Canonical field boundary geometry (Verma et al. 2013 acid,
# Fig 2 caption — Verma_Acid_2.pdf page 4).  Note: the published caption
# explicitly states these are "approximate" coordinates.
# ---------------------------------------------------------------------------
V13A_MACID_FIELDS: Dict[str, Dict] = {
    "IACA_CROI_COL": {
        "triple": (-0.002, -0.3),
        "boundaries": (
            ((1.7,  8.0), ("IA+CA", "CR+OI")),
            ((6.2, -8.0), ("IA+CA", "Col")),
            ((-8.0, -1.8), ("CR+OI", "Col")),
        ),
    },
    "IA_CA_CROI": {
        "triple": (-0.2, 0.7),
        "boundaries": (
            ((-8.0, -4.8), ("IA", "CA")),
            ((1.0,  8.0), ("IA", "CR+OI")),
            ((3.9, -8.0), ("CA", "CR+OI")),
        ),
    },
    "IA_CA_COL": {
        "triple": (0.3, -1.0),
        "boundaries": (
            ((-8.0, 6.4), ("IA", "CA")),
            ((0.8, -8.0), ("IA", "Col")),
            ((4.5,  8.0), ("CA", "Col")),
        ),
    },
    "IA_CROI_COL": {
        "triple": (-0.7, 0.5),
        "boundaries": (
            ((-2.6, -8.0), ("IA", "CR+OI")),
            ((-3.7,  8.0), ("IA", "Col")),
            ((8.0, -0.02), ("CR+OI", "Col")),
        ),
    },
    "CA_CROI_COL": {
        "triple": (0.4, 0.2),
        "boundaries": (
            ((1.0, -8.0), ("CA", "CR+OI")),
            ((8.0,  8.0), ("CA", "Col")),
            ((-8.0, 2.9), ("CR+OI", "Col")),
        ),
    },
}


# ---------------------------------------------------------------------------
# Verma et al. (2013) — Acid rocks, Set 2 (immobile majors + traces)
# ---------------------------------------------------------------------------
# Canonical equations from Supplementary Table 9, Eqs. (11)–(20).
# Variables: MgO, P2O5 (wt%, adjusted) and Nb, Y, Zr (ppm → wt%) ÷ TiO2.
# IMPORTANT: trace elements MUST be converted ppm → wt% (÷10 000) BEFORE
# the log-ratio (see footnote of Sup. Table 9).
#
# As with Set 1, the LDA stepwise selection means each equation uses a
# different subset of these 5 variables.
# ---------------------------------------------------------------------------

_V13A_MT_ALL5    = ("MgO", "P2O5", "Nb", "Y", "Zr")
_V13A_MT_NO_MGO  = ("P2O5", "Nb", "Y", "Zr")

V13A_MTACID: Dict[str, DFCoefSet] = {
    # ----- (a) IA+CA · CR+OI · Col  — Eqs (11), (12) ----------------------
    "DF1_IACA_CROI_COL": DFCoefSet(
        parts=_V13A_MT_ALL5, denominator="TiO2",
        intercept=4.70,
        coefs=(-0.091, -0.228, 0.73, -0.237, 0.58),
    ),
    "DF2_IACA_CROI_COL": DFCoefSet(
        parts=_V13A_MT_ALL5, denominator="TiO2",
        intercept=-3.71,
        coefs=(-0.268, -1.25, -0.476, 0.209, -0.082),
    ),
    # ----- (b) IA · CA · CR+OI  — Eqs (13), (14) -------------------------
    "DF1_IA_CA_CROI": DFCoefSet(
        parts=_V13A_MT_ALL5, denominator="TiO2",
        intercept=4.70,
        coefs=(-0.0018, -0.025, 1.06, -0.53, 0.301),
    ),
    "DF2_IA_CA_CROI": DFCoefSet(
        parts=_V13A_MT_ALL5, denominator="TiO2",
        intercept=3.70,
        coefs=(-0.197, 0.118, -0.72, 1.10, 0.74),
    ),
    # ----- (c) IA · CA · Col  — Eqs (15), (16)  [no MgO] ------------------
    "DF1_IA_CA_COL": DFCoefSet(
        parts=_V13A_MT_NO_MGO, denominator="TiO2",
        intercept=3.99,
        coefs=(0.248, 1.18, -0.86, 0.136),
    ),
    "DF2_IA_CA_COL": DFCoefSet(
        parts=_V13A_MT_NO_MGO, denominator="TiO2",
        intercept=7.28,
        coefs=(1.13, 0.382, 1.13, 0.68),
    ),
    # ----- (d) IA · CR+OI · Col  — Eqs (17), (18) ------------------------
    "DF1_IA_CROI_COL": DFCoefSet(
        parts=_V13A_MT_ALL5, denominator="TiO2",
        intercept=2.77,
        coefs=(0.095, -0.079, 1.10, -0.90, 0.333),
    ),
    "DF2_IA_CROI_COL": DFCoefSet(
        parts=_V13A_MT_ALL5, denominator="TiO2",
        intercept=-0.80,
        coefs=(-0.298, -1.00, -0.279, 0.339, 0.171),
    ),
    # ----- (e) CA · CR+OI · Col  — Eqs (19), (20) ------------------------
    "DF1_CA_CROI_COL": DFCoefSet(
        parts=_V13A_MT_ALL5, denominator="TiO2",
        intercept=3.73,
        coefs=(-0.081, -0.432, 0.444, -0.131, 0.82),
    ),
    "DF2_CA_CROI_COL": DFCoefSet(
        parts=_V13A_MT_ALL5, denominator="TiO2",
        intercept=-5.42,
        coefs=(-0.341, -1.11, -0.75, 0.271, -0.377),
    ),
}

# Same rule for the acid set: "all trace element data (ug.g-1) in these
# equations were first converted to wt.% before calculating the trace to
# major element log-ratios".
V13A_MTACID = _traces_in_ppm(V13A_MTACID, "Nb", "Y", "Zr")


# ---------------------------------------------------------------------------
# V13A_MTACID — Canonical field boundary geometry (Verma et al. 2013 acid,
# Fig 3 caption — Verma_Acid_2.pdf page 5).
# ---------------------------------------------------------------------------
V13A_MTACID_FIELDS: Dict[str, Dict] = {
    "IACA_CROI_COL": {
        "triple": (0.03, -0.03),
        "boundaries": (
            ((-0.07, 8.0), ("IA+CA", "CR+OI")),
            ((-8.0, -6.1), ("IA+CA", "Col")),
            ((8.0,  -5.8), ("CR+OI", "Col")),
        ),
    },
    "IA_CA_CROI": {
        "triple": (-0.3, 0.8),
        "boundaries": (
            ((-8.0, -6.1), ("IA", "CA")),
            ((0.6,   8.0), ("IA", "CR+OI")),
            ((4.9,  -8.0), ("CA", "CR+OI")),
        ),
    },
    "IA_CA_COL": {
        "triple": (-0.18, 0.93),
        "boundaries": (
            ((-5.62, -8.0), ("IA", "CA")),
            ((-0.27,  8.0), ("IA", "Col")),
            ((7.33,  -8.0), ("CA", "Col")),
        ),
    },
    "IA_CROI_COL": {
        "triple": (-0.7, -0.07),
        "boundaries": (
            ((-1.8,  8.0), ("IA", "CR+OI")),
            ((-4.8, -8.0), ("IA", "Col")),
            ((8.0,  -1.8), ("CR+OI", "Col")),
        ),
    },
    "CA_CROI_COL": {
        "triple": (-0.2, 0.1),
        "boundaries": (
            ((-8.0, -2.7), ("CA", "CR+OI")),
            ((1.7,   8.0), ("CA", "Col")),
            ((5.7,  -8.0), ("CR+OI", "Col")),
        ),
    },
}


# ---------------------------------------------------------------------------
# Verma et al. (2013) — Acid rocks, Set 3 (immobile traces only)
# ---------------------------------------------------------------------------
# Canonical equations from Supplementary Table 13, Eqs. (21)–(30).
# Variables: La, Ce, Sm, Nb, Th, Y, Zr — all ÷ Yb (all in ppm).
# Units cancel (trace/trace) so no ppm→wt% conversion is needed.
#
# LDA stepwise selection: panel (c) uses only 6 of the 7 traces
# (omits Y); all other panels use all 7.
# ---------------------------------------------------------------------------

_V13A_T_ALL7  = ("La", "Ce", "Sm", "Nb", "Th", "Y", "Zr")
_V13A_T_NO_Y  = ("La", "Ce", "Sm", "Nb", "Th",       "Zr")

V13A_TACID: Dict[str, DFCoefSet] = {
    # ----- (a) IA+CA · CR+OI · Col  — Eqs (21), (22) ----------------------
    "DF1_IACA_CROI_COL": DFCoefSet(
        parts=_V13A_T_ALL7, denominator="Yb",
        intercept=-9.50,
        coefs=(-4.99, 7.81, -4.43, 0.82, 0.063, 0.64, -0.57),
    ),
    "DF2_IACA_CROI_COL": DFCoefSet(
        parts=_V13A_T_ALL7, denominator="Yb",
        intercept=10.25,
        coefs=(2.32, -3.62, 2.62, 0.25, 0.84, -1.14, -1.27),
    ),
    # ----- (b) IA · CA · CR+OI  — Eqs (23), (24) -------------------------
    "DF1_IA_CA_CROI": DFCoefSet(
        parts=_V13A_T_ALL7, denominator="Yb",
        intercept=-9.61,
        coefs=(-5.21, 6.62, -3.63, 1.69, 0.33, 1.56, -0.49),
    ),
    "DF2_IA_CA_CROI": DFCoefSet(
        parts=_V13A_T_ALL7, denominator="Yb",
        intercept=-4.93,
        coefs=(-3.72, 4.79, -2.68, 0.16, -0.50, 1.04, -0.34),
    ),
    # ----- (c) IA · CA · Col  — Eqs (25), (26)  [no Y] --------------------
    "DF1_IA_CA_COL": DFCoefSet(
        parts=_V13A_T_NO_Y, denominator="Yb",
        intercept=-0.73,
        coefs=(-0.047, 1.08, -0.96, 0.84, 0.59, -0.88),
    ),
    "DF2_IA_CA_COL": DFCoefSet(
        parts=_V13A_T_NO_Y, denominator="Yb",
        intercept=5.10,
        coefs=(-4.07, 4.74, -0.077, -0.23, 0.77, -2.49),
    ),
    # ----- (d) IA · CR+OI · Col  — Eqs (27), (28) ------------------------
    "DF1_IA_CROI_COL": DFCoefSet(
        parts=_V13A_T_ALL7, denominator="Yb",
        intercept=-2.91,
        coefs=(0.26, 1.05, -1.00, 0.90, 0.54, 0.089, -0.62),
    ),
    "DF2_IA_CROI_COL": DFCoefSet(
        parts=_V13A_T_ALL7, denominator="Yb",
        intercept=-13.95,
        coefs=(-5.36, 8.41, -5.37, 0.48, -0.41, 1.12, 0.37),
    ),
    # ----- (e) CA · CR+OI · Col  — Eqs (29), (30) ------------------------
    "DF1_CA_CROI_COL": DFCoefSet(
        parts=_V13A_T_ALL7, denominator="Yb",
        intercept=-11.34,
        coefs=(-5.41, 8.44, -4.78, 0.78, -0.079, 0.64, -0.26),
    ),
    "DF2_CA_CROI_COL": DFCoefSet(
        parts=_V13A_T_ALL7, denominator="Yb",
        intercept=6.09,
        coefs=(1.68, -1.73, 0.52, 0.84, 1.04, -0.98, -1.41),
    ),
}


# ---------------------------------------------------------------------------
# V13A_TACID — Canonical field boundary geometry (Verma et al. 2013 acid,
# Fig 4 caption — Verma_Acid_2.pdf page 7).
# ---------------------------------------------------------------------------
V13A_TACID_FIELDS: Dict[str, Dict] = {
    "IACA_CROI_COL": {
        "triple": (0.5, -0.4),
        "boundaries": (
            ((-0.1, -8.0), ("IA+CA", "CR+OI")),
            ((-8.0,  6.0), ("IA+CA", "Col")),
            ((8.0,   7.2), ("CR+OI", "Col")),
        ),
    },
    "IA_CA_CROI": {
        "triple": (-0.01, 1.2),
        "boundaries": (
            ((-8.0, -5.4), ("IA", "CA")),
            ((1.0,   8.0), ("IA", "CR+OI")),
            ((6.0,  -8.0), ("CA", "CR+OI")),
        ),
    },
    "IA_CA_COL": {
        "triple": (-0.8, 2.9),
        "boundaries": (
            ((-3.6, -8.0), ("IA", "CA")),
            ((-0.7,  8.0), ("IA", "Col")),
            ((4.3,  -8.0), ("CA", "Col")),
        ),
    },
    "IA_CROI_COL": {
        "triple": (-1.2, -0.3),
        "boundaries": (
            ((-5.7,  8.0), ("IA", "CR+OI")),
            ((-1.8, -8.0), ("IA", "Col")),
            ((8.0,   3.0), ("CR+OI", "Col")),
        ),
    },
    "CA_CROI_COL": {
        "triple": (0.4, -0.3),
        "boundaries": (
            ((1.4,  -8.0), ("CA", "CR+OI")),
            ((-8.0,  3.1), ("CA", "Col")),
            ((5.8,   8.0), ("CR+OI", "Col")),
        ),
    },
}
