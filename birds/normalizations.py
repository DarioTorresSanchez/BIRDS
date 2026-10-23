"""Reference normalising compositions for spider diagrams.

* REE chondrite values – Rollinson & Pease (2021), Table 4.7
* REE shale composites – Rollinson & Pease (2021), Table 4.8
* Multi-element normalisers – Rollinson & Pease (2021), Table 4.9

All concentrations are in ppm (μg g⁻¹). Major elements K, Ti and P are
already converted from wt.% oxide to ppm element so that they sit on the
same scale as the trace data.

Every value was checked against those three tables on 2026-10-21 -- 366
of them, each read where the book prints it (``tests/data/
rollinson_pease_2021_tables.json``).  Checking found six that were not
the book's: PAAS Tm, Palme & O'Neill Cs, NASC Ti, and the upper crust's
Rb, K and Ti; a NASC that carried the upper crust's Pb and Y, which
Gromet et al. did not determine, and lacked the Ta they did; and
Arevalo & McDonough's global log-normal mean filed as an N-MORB.  What
the book's copy cannot confirm -- its Tables 4.7 and 4.9 are cut off at
the right, and Table 4.9 has no P -- was then read in the primary
sources on 2026-10-22 (``tests/test_normalisers_primary_sources.py``):
Boynton (1984) and the Sun & McDonough (1989) rows agree; Taylor &
McLennan's (1985) Y is 2.1, not 2.25, and Sun & McDonough's E-MORB P is
620, not 1410.  Rudnick & Gao's bulk crust, read on 2026-10-23 in the
2003 edition, has K 15026, Ti 4315 and P 567 where it carried 15000,
4320 and the upper crust's 655.
"""

from __future__ import annotations

from typing import Dict, Mapping, Tuple


# ---------------------------------------------------------------------------
# Element orders used on the x-axis
# ---------------------------------------------------------------------------

REE_ORDER: Tuple[str, ...] = (
    "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb",
    "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
)

# Some authors place Y between Dy and Ho on the REE plot
REE_ORDER_WITH_Y: Tuple[str, ...] = (
    "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb",
    "Dy", "Y", "Ho", "Er", "Tm", "Yb", "Lu",
)

# Standard multi-element order following Sun & McDonough (1989) / Rollinson
# Table 4.9 (left to right of decreasing incompatibility in basaltic systems)
MULTIELEMENT_ORDER: Tuple[str, ...] = (
    "Cs", "Rb", "Ba", "Th", "U", "Nb", "Ta", "K", "La", "Ce", "Pb",
    "Pr", "Sr", "P", "Nd", "Zr", "Hf", "Sm", "Eu", "Ti", "Gd", "Tb",
    "Dy", "Ho", "Y", "Er", "Tm", "Yb", "Lu",
)


# ---------------------------------------------------------------------------
# REE chondrite normalisers (ppm)
# ---------------------------------------------------------------------------

REE_CHONDRITES: Dict[str, Mapping[str, float]] = {
    "Sun & McDonough (1989) – CI": {
        "La": 0.2370, "Ce": 0.6120, "Pr": 0.0950, "Nd": 0.4670,
        "Sm": 0.1530, "Eu": 0.0580, "Gd": 0.2055, "Tb": 0.0374,
        "Dy": 0.2540, "Ho": 0.0566, "Er": 0.1655, "Tm": 0.0255,
        "Yb": 0.1700, "Lu": 0.0254, "Y": 1.5700,
    },
    "McDonough & Sun (1995) – CI": {
        "La": 0.2370, "Ce": 0.6130, "Pr": 0.0928, "Nd": 0.4570,
        "Sm": 0.1480, "Eu": 0.0563, "Gd": 0.1990, "Tb": 0.0361,
        "Dy": 0.2460, "Ho": 0.0546, "Er": 0.1600, "Tm": 0.0247,
        "Yb": 0.1610, "Lu": 0.0246, "Y": 1.5700,
    },
    "Anders & Grevesse (1989) – CI avg": {
        "La": 0.2347, "Ce": 0.6032, "Pr": 0.0891, "Nd": 0.4524,
        "Sm": 0.1471, "Eu": 0.0560, "Gd": 0.1966, "Tb": 0.0363,
        "Dy": 0.2427, "Ho": 0.0556, "Er": 0.1589, "Tm": 0.0242,
        "Yb": 0.1625, "Lu": 0.0243, "Y": 1.5600,
    },
    "Pourmand et al. (2012)": {
        "La": 0.2469, "Ce": 0.6321, "Pr": 0.0959, "Nd": 0.4864,
        "Sm": 0.1556, "Eu": 0.0599, "Gd": 0.2003, "Tb": 0.0378,
        "Dy": 0.2577, "Ho": 0.0554, "Er": 0.1667, "Tm": 0.0261,
        "Yb": 0.1694, "Lu": 0.0256, "Y": 1.3950,
    },
    "Barrat et al. (2012) – Orgueil": {
        "La": 0.2350, "Ce": 0.6000, "Pr": 0.0910, "Nd": 0.4640,
        "Sm": 0.1530, "Eu": 0.0586, "Gd": 0.2060, "Tb": 0.0375,
        "Dy": 0.2540, "Ho": 0.0566, "Er": 0.1660, "Tm": 0.0262,
        "Yb": 0.1680, "Lu": 0.0246, "Y": 1.5600,
    },
    "Boynton (1984)": {
        "La": 0.310, "Ce": 0.808, "Pr": 0.122, "Nd": 0.600,
        "Sm": 0.195, "Eu": 0.0735, "Gd": 0.259, "Tb": 0.0474,
        "Dy": 0.322, "Ho": 0.0718, "Er": 0.210, "Tm": 0.0324,
        "Yb": 0.209, "Lu": 0.0322,
    },
    # Appendix 2 of the book (p. 298): Evensen et al.'s CI x 1.5.  Y is
    # 2.1 there; it was 2.25.
    "Taylor & McLennan (1985) – CI calc. volatile-free": {
        "La": 0.3670, "Ce": 0.9570, "Pr": 0.1370, "Nd": 0.7110,
        "Sm": 0.2310, "Eu": 0.0870, "Gd": 0.3060, "Tb": 0.0580,
        "Dy": 0.3810, "Ho": 0.0851, "Er": 0.2490, "Tm": 0.0356,
        "Yb": 0.2480, "Lu": 0.0381, "Y": 2.1,
    },
    "Wakita et al. (1971) – ordinary chondrites": {
        "La": 0.340, "Ce": 0.910, "Pr": 0.121, "Nd": 0.640,
        "Sm": 0.195, "Eu": 0.073, "Gd": 0.260, "Tb": 0.047,
        "Dy": 0.300, "Ho": 0.078, "Er": 0.200, "Tm": 0.032,
        "Yb": 0.220, "Lu": 0.034,
    },
}


# ---------------------------------------------------------------------------
# REE shale composites (ppm) — typical for sediment normalisation
# ---------------------------------------------------------------------------

REE_SHALES: Dict[str, Mapping[str, float]] = {
    "NASC (McLennan 1989)": {
        "La": 32.00, "Ce": 73.00, "Pr": 7.90, "Nd": 33.00, "Sm": 5.70,
        "Eu": 1.24, "Gd": 5.20, "Tb": 0.85, "Dy": 5.80, "Ho": 1.04,
        "Er": 3.40, "Tm": 0.50, "Yb": 3.10, "Lu": 0.48, "Y": 27.0,
    },
    "PAAS (Pourmand et al. 2012)": {
        "La": 44.56, "Ce": 88.25, "Pr": 10.15, "Nd": 37.32, "Sm": 6.884,
        "Eu": 1.215, "Gd": 6.043, "Tb": 0.8914, "Dy": 5.325, "Ho": 1.053,
        "Er": 3.075, "Tm": 0.451, "Yb": 3.012, "Lu": 0.4386, "Y": 27.31,
    },
    "MUQ (Kamber et al. 2005)": {
        "La": 32.51, "Ce": 71.09, "Pr": 8.46, "Nd": 32.91, "Sm": 6.88,
        "Eu": 1.57, "Gd": 6.36, "Tb": 0.99, "Dy": 5.89, "Ho": 1.22,
        "Er": 3.37, "Tm": 0.51, "Yb": 3.25, "Lu": 0.49, "Y": 31.85,
    },
    "European Shale (Bau et al. 2018)": {
        "La": 44.30, "Ce": 88.50, "Pr": 10.60, "Nd": 39.50, "Sm": 7.30,
        "Eu": 1.48, "Gd": 6.34, "Tb": 0.944, "Dy": 5.86, "Ho": 1.17,
        "Er": 3.43, "Tm": 0.492, "Yb": 3.26, "Lu": 0.485, "Y": 31.9,
    },
    "World Shale Average (Bau et al. 2018)": {
        "La": 40.30, "Ce": 83.30, "Pr": 9.54, "Nd": 36.60, "Sm": 6.63,
        "Eu": 1.31, "Gd": 5.86, "Tb": 0.90, "Dy": 5.66, "Ho": 1.09,
        "Er": 3.30, "Tm": 0.48, "Yb": 3.12, "Lu": 0.47, "Y": 28.7,
    },
    "Upper Continental Crust (Rudnick & Gao 2014)": {
        "La": 31.0, "Ce": 63.0, "Pr": 7.1, "Nd": 27.0, "Sm": 4.7,
        "Eu": 1.0, "Gd": 4.0, "Tb": 0.7, "Dy": 3.9, "Ho": 0.83,
        "Er": 2.3, "Tm": 0.30, "Yb": 2.0, "Lu": 0.31, "Y": 21.0,
    },
}


# ---------------------------------------------------------------------------
# Multi-element normalisers (ppm)
# Trace elements as given; K, Ti, P already converted to ppm element.
# ---------------------------------------------------------------------------

MULTIELEMENT_NORMS: Dict[str, Mapping[str, float]] = {
    "Primitive Mantle (McDonough & Sun 1995)": {
        "Cs": 0.0210, "Rb": 0.600, "Ba": 6.60, "Th": 0.0795, "U": 0.0203,
        "Nb": 0.658, "Ta": 0.0370, "K": 240, "La": 0.6480, "Ce": 1.6750,
        "Pb": 0.150, "Pr": 0.2540, "Sr": 19.900, "P": 90, "Nd": 1.2500,
        "Zr": 10.500, "Hf": 0.2830, "Sm": 0.4060, "Eu": 0.1540, "Ti": 1205,
        "Gd": 0.5440, "Tb": 0.0990, "Dy": 0.6740, "Ho": 0.1490, "Y": 4.30,
        "Er": 0.4380, "Tm": 0.0680, "Yb": 0.4410, "Lu": 0.0675,
    },
    "Primitive Mantle (Palme & O'Neill 2014)": {
        # Cs was 0.0188, one digit from the CI chondrite's 0.1880.
        "Cs": 0.0180, "Rb": 0.605, "Ba": 6.85, "Th": 0.0849, "U": 0.0229,
        "Nb": 0.595, "Ta": 0.0430, "K": 260, "La": 0.6832, "Ce": 1.7529,
        "Pb": 0.185, "Pr": 0.2657, "Sr": 22.0, "Nd": 1.3410, "Zr": 10.30,
        "Hf": 0.3014, "Sm": 0.4347, "Eu": 0.1665, "Ti": 1265, "Gd": 0.5855,
        "Tb": 0.1075, "Dy": 0.7239, "Ho": 0.1597, "Y": 4.13, "Er": 0.4684,
        "Tm": 0.0738, "Yb": 0.4774, "Lu": 0.0708,
    },
    "CI Chondrite (McDonough & Sun 1995)": {
        "Cs": 0.190, "Rb": 2.30, "Ba": 2.41, "Th": 0.0290, "U": 0.0074,
        "Nb": 0.240, "Ta": 0.0136, "K": 550, "La": 0.2370, "Ce": 0.6130,
        "Pb": 2.470, "Pr": 0.0928, "Sr": 7.250, "P": 1080, "Nd": 0.4570,
        "Zr": 3.820, "Hf": 0.1030, "Sm": 0.1480, "Eu": 0.0563, "Ti": 440,
        "Gd": 0.1990, "Tb": 0.0361, "Dy": 0.2460, "Ho": 0.0546, "Y": 1.5700,
        "Er": 0.1600, "Tm": 0.0247, "Yb": 0.1610, "Lu": 0.0246,
    },
    "N-MORB (Sun & McDonough 1989)": {
        "Cs": 0.007, "Rb": 0.56, "Ba": 6.3, "Th": 0.12, "U": 0.047,
        "Nb": 2.33, "Ta": 0.132, "K": 600, "La": 2.50, "Ce": 7.50,
        "Pb": 0.30, "Pr": 1.32, "Sr": 90, "P": 510, "Nd": 7.30,
        "Zr": 74, "Hf": 2.05, "Sm": 2.63, "Eu": 1.02, "Ti": 7600,
        "Gd": 3.68, "Tb": 0.67, "Dy": 4.55, "Ho": 1.01, "Y": 28,
        "Er": 2.97, "Tm": 0.456, "Yb": 3.05, "Lu": 0.455,
    },
    # Table 1 of the paper; P was 1410 where it prints 620.
    "E-MORB (Sun & McDonough 1989)": {
        "Cs": 0.063, "Rb": 5.04, "Ba": 57, "Th": 0.60, "U": 0.18,
        "Nb": 8.30, "Ta": 0.47, "K": 2100, "La": 6.30, "Ce": 15.0,
        "Pb": 0.60, "Pr": 2.05, "Sr": 155, "P": 620, "Nd": 9.00,
        "Zr": 73, "Hf": 2.03, "Sm": 2.60, "Eu": 0.91, "Ti": 6000,
        "Gd": 2.97, "Tb": 0.53, "Dy": 3.55, "Ho": 0.79, "Y": 22,
        "Er": 2.31, "Tm": 0.356, "Yb": 2.37, "Lu": 0.354,
    },
    # Table 4.9's "Global LN-mean": the log-normal mean of all MORB, not
    # an N-MORB average.  It used to be listed as "N-MORB mean".
    "Global MORB, log-normal mean (Arevalo & McDonough 2010)": {
        "Cs": 0.019, "Rb": 1.500, "Ba": 16.60, "Th": 0.219, "U": 0.080,
        "Nb": 3.44, "Ta": 0.224, "K": 1620, "La": 3.77, "Ce": 11.5,
        "Pb": 0.57, "Pr": 1.910, "Sr": 130, "Nd": 9.80, "Zr": 90.1,
        "Hf": 2.40, "Sm": 3.25, "Eu": 1.22, "Ti": 8500, "Gd": 4.40,
        "Tb": 0.78, "Dy": 5.110, "Ho": 1.110, "Y": 30, "Er": 3.15,
        "Tm": 0.48, "Yb": 3.00, "Lu": 0.45,
    },
    # Rb, K and Ti were 82, 23200 and 3840.
    "Upper Continental Crust (Rudnick & Gao 2014)": {
        "Cs": 4.9, "Rb": 84, "Ba": 628, "Th": 10.5, "U": 2.7,
        "Nb": 12, "Ta": 0.9, "K": 23244, "La": 31, "Ce": 63,
        "Pb": 17, "Pr": 7.1, "Sr": 320, "P": 655, "Nd": 27,
        "Zr": 193, "Hf": 5.3, "Sm": 4.7, "Eu": 1.0, "Ti": 3836,
        "Gd": 4.0, "Tb": 0.7, "Dy": 3.9, "Ho": 0.83, "Y": 21,
        "Er": 2.3, "Tm": 0.30, "Yb": 2.0, "Lu": 0.31,
    },
    # Read in Rudnick & Gao (2003) Table 11, whose upper-crust column is
    # the one Rollinson & Pease print for 2014, value for value.  K, Ti
    # and P were 15000, 4320 and 655 -- the last the upper crust's --
    # and are now the table's K2O 1.81, TiO2 0.72 and P2O5 0.13.
    "Bulk Continental Crust (Rudnick & Gao 2014)": {
        "Cs": 2.0, "Rb": 49, "Ba": 456, "Th": 5.6, "U": 1.3,
        "Nb": 8, "Ta": 0.7, "K": 15026, "La": 20, "Ce": 43,
        "Pb": 11, "Pr": 4.9, "Sr": 320, "P": 567, "Nd": 20,
        "Zr": 132, "Hf": 3.7, "Sm": 3.9, "Eu": 1.1, "Ti": 4315,
        "Gd": 3.7, "Tb": 0.6, "Dy": 3.6, "Ho": 0.77, "Y": 19,
        "Er": 2.1, "Tm": 0.28, "Yb": 1.9, "Lu": 0.30,
    },
    # Table 4.9 marks Nb, Pb, Pr, Gd, Dy, Ho, Y, Er and Tm "not
    # determined".  This entry used to carry Pb 17 and Y 21 -- the upper
    # crust's, one column over -- and lacked Ta; Ti was 4707.
    "NASC (Gromet et al. 1984)": {
        "Cs": 5.16, "Rb": 125, "Ba": 636, "Th": 12.3, "U": 2.66,
        "Ta": 1.12, "K": 31545, "La": 31.1, "Ce": 66.7,
        "Sr": 142, "Nd": 27.4, "Zr": 200, "Hf": 6.30,
        "Sm": 5.59, "Eu": 1.18, "Ti": 4705, "Tb": 0.85,
        "Yb": 3.06, "Lu": 0.456,
    },
}


# ---------------------------------------------------------------------------
# Chalcophile / siderophile metals — Ni-Cu-PGE deposits
# ---------------------------------------------------------------------------
#
# Mantle-normalised metal patterns are the standard diagnostic tool in
# magmatic sulphide petrology: the metals are plotted in order of
# *decreasing compatibility with sulphide liquid* rather than by
# incompatibility, so the axis is a completely different one from the
# Sun & McDonough multi-element order.  A pattern's slope then reads
# directly as the sulphide's history — high R-factor, fractionation of
# monosulphide solid solution, or a late-stage Cu-rich residue.
#
# Every value below was checked page by page against its paper on
# 2026-10-08, reading the rendered tables rather than the text layer:
#
# * McDonough & Sun (1995), Chem. Geol. 120: Table 5 ("Pyrolite") for
#   the first entry and every primitive-mantle Ni and Cu; Table 2 for CI
#   Ni and Cu;
# * Becker et al. (2006), GCA 70, §5.3 (pp. 4541-4542);
# * Fischer-Gödde et al. (2011), Chem. Geol. 280, Table 3 and §5.3, and
#   (2010), GCA 74, Table 3;
# * Salters & Stracke (2004), G-cubed 5, Table 6.
#
# Checking found: the Fischer-Gödde primitive-mantle Au at 1.0 ng/g
# where the paper gives 1.7; a CI entry credited to Horan et al. (2003)
# whose numbers are not in that paper; CI Ni and Cu matching no column of
# McDonough & Sun's Table 2; a first entry credited to Barnes & Maier
# (1999) that is McDonough & Sun's pyrolite to the last digit; a
# depleted-mantle entry that carried the *primitive* mantle's noble
# metals, seven of its nine values wrong; and Becker et al.'s gold
# estimate missing.

# Order of decreasing compatibility in sulphide liquid (Barnes & Lightfoot
# 2005; Barnes & Ripley 2016).  Ni and Cu bracket the noble metals.
CHALCOPHILE_ORDER: Tuple[str, ...] = (
    "Ni", "Os", "Ir", "Ru", "Rh", "Pt", "Pd", "Au", "Cu",
)

# Same order with Re and Ag, reported by some laboratories.
CHALCOPHILE_ORDER_EXTENDED: Tuple[str, ...] = (
    "Ni", "Os", "Ir", "Ru", "Rh", "Pt", "Pd", "Re", "Au", "Ag", "Cu",
)

CHALCOPHILE_NORMS: Dict[str, Mapping[str, float]] = {
    # McDonough & Sun (1995), Table 5, pyrolite: the primitive mantle most
    # Ni-Cu-PGE papers normalise to.  It used to be credited to Barnes &
    # Maier (1999), who did not originate these numbers.
    "Primitive Mantle, metals (McDonough & Sun 1995)": {
        "Ni": 1960.0, "Os": 0.0034, "Ir": 0.0032, "Ru": 0.0050,
        "Rh": 0.0009, "Pt": 0.0071, "Pd": 0.0039, "Au": 0.0010,
        "Cu": 30.0,
    },
    # Primitive upper mantle from peridotite massifs and xenoliths,
    # Becker et al. (2006, §5.3): Os 3.9, Ir 3.5, Ru 7.0, Pt 7.6, Pd 7.1,
    # Re 0.35 ng/g, and Au 1.9 ± 0.6 ng/g -- "relatively imprecise", from
    # earlier analyses of the same samples.  Rh was not analysed.  Ni
    # and Cu are McDonough & Sun's (1995), so the axis does not break.
    "Primitive Upper Mantle (Becker et al. 2006)": {
        "Ni": 1960.0, "Os": 0.0039, "Ir": 0.0035, "Ru": 0.0070,
        "Pt": 0.0076, "Pd": 0.0071, "Re": 0.00035, "Au": 0.0019,
        "Cu": 30.0,
    },
    # The primitive-mantle model of Fischer-Gödde et al. (2011, Chem.
    # Geol. 280, Table 3 and §5.3): their Rh, 1.2 ± 0.2 ng/g, and Au,
    # 1.7 ± 0.5 ng/g, with the Ir, Pt, Pd and Re of Becker et al.
    # (2006).  Table 3 leaves out Os and Ru, which are Becker's too, and
    # Ni and Cu, which are McDonough & Sun's (1995), as its footnote says.
    "Primitive Mantle (Fischer-Gödde et al. 2011)": {
        "Ni": 1960.0, "Os": 0.0039, "Ir": 0.0035, "Ru": 0.0070,
        "Rh": 0.0012, "Pt": 0.0076, "Pd": 0.0071, "Re": 0.00035,
        "Au": 0.0017, "Cu": 30.0,
    },
    # CI chondrite — the reference for metal/metal ratios and for
    # judging whether a sulphide liquid kept a chondritic HSE budget.
    # Fischer-Gödde et al. (2010, GCA 74, Table 3, "Mean CI"): Orgueil
    # and Ivuna by isotope dilution -- theirs, Walker et al.'s (2002) and
    # Horan et al.'s (2003) -- adjusted to a CI Ir of 462 ng/g.  Ni and
    # Cu, which it does not measure, are McDonough & Sun's (1995, Table
    # 2).  They were 10910 and 126 ppm, which matches none of that
    # table's four columns.
    "CI Chondrite (Fischer-Gödde et al. 2010)": {
        "Ni": 10500.0, "Os": 0.491, "Ir": 0.462, "Ru": 0.688,
        "Rh": 0.133, "Pt": 0.943, "Pd": 0.563, "Re": 0.0407,
        "Au": 0.149, "Cu": 120.0,
    },
    # Depleted MORB mantle — the sensible reference for oceanic and
    # ophiolite-hosted sulphide occurrences.  Salters & Stracke (2004),
    # Table 6.  It used to carry McDonough & Sun's primitive-mantle noble
    # metals and Cu 24: seven of nine values wrong.
    "Depleted MORB Mantle (Salters & Stracke 2004)": {
        "Ni": 1960.0, "Os": 0.00299, "Ir": 0.0029, "Ru": 0.0057,
        "Rh": 0.0010, "Pt": 0.0062, "Pd": 0.0052, "Re": 0.000157,
        "Au": 0.0010, "Cu": 30.0,
    },
}


#: Names a reference used to carry, mapped to the name it carries now,
#: so a session saved under the old name still finds it.
RENAMED_NORMALISERS: Dict[str, str] = {
    "CI Chondrite (Horan et al. 2003 / McDonough & Sun 1995)":
        "CI Chondrite (Fischer-Gödde et al. 2010)",
    "Primitive Mantle (Barnes & Maier 1999)":
        "Primitive Mantle, metals (McDonough & Sun 1995)",
    "N-MORB mean (Arevalo & McDonough 2010)":
        "Global MORB, log-normal mean (Arevalo & McDonough 2010)",
}


def current_name(name: str) -> str:
    """*name*, or the name that reference goes by now."""
    return RENAMED_NORMALISERS.get(name, name)


# ---------------------------------------------------------------------------
# Oxide → element conversion for major elements stored as wt.% oxide.
# Multiply the wt.% value by *factor* to obtain ppm of the element.
# ---------------------------------------------------------------------------

#: 1 wt.% TiO2 = 5993.4 ppm Ti, from the mass ratio 47.867 / 79.866.
#:
#: This one lives here, on its own, because three parts of the program
#: convert TiO2 to Ti and they must not answer differently: the
#: discrimination diagrams, the statistics table, and this table.  The
#: value was 5995 in several of them, which is what the older atomic
#: weight Ti = 47.90 gives.
#:
#: These ten are stoichiometry, not measurements, so each is its own
#: mass ratio rounded to four figures and nothing else.  Checking them
#: that way found two that were not: Ti, 0.025 % high because of the
#: old weight, and P, 0.017 % high from rounding 4364.27 upward.
TIO2_WT_TO_TI_PPM = 5993.4

OXIDE_TO_ELEMENT_PPM: Dict[str, Tuple[str, float]] = {
    "K":  ("K2O",  8302),   # K2O wt% × 8302  -> K ppm
    "Ti": ("TiO2", TIO2_WT_TO_TI_PPM),
    "P":  ("P2O5", 4364),   # 4365 was a rounding slip: the ratio is 4364.27
    "Si": ("SiO2", 4674),
    "Al": ("Al2O3", 5293),
    "Mg": ("MgO",  6030),
    "Ca": ("CaO",  7147),
    "Na": ("Na2O", 7419),
    "Mn": ("MnO",  7745),
    "Fe": ("FeO",  7773),
}


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_normaliser(name: str) -> Mapping[str, float] | None:
    """Return the normalising dict for *name*, regardless of category.

    A few references are legitimately listed in more than one category —
    Rudnick & Gao's Upper Continental Crust is both a REE composite and a
    multi-element normaliser — and the tables differ only in how many
    elements they carry.  Returning the first match would hand the
    multi-element view the REE-only subset, silently dropping Cs, Rb, Ba,
    Th, U, Nb, Ta, K, Pb, Sr, P, Zr, Hf and Ti from the diagram with no
    warning.  The richest table is therefore the one that wins; the
    narrower views simply ask for fewer elements than it offers.
    """
    matches = [group[name] for group in
               (REE_CHONDRITES, REE_SHALES, MULTIELEMENT_NORMS,
                CHALCOPHILE_NORMS)
               if name in group]
    if not matches:
        return None
    return max(matches, key=len)


def is_chalcophile_normaliser(name: str) -> bool:
    """True when *name* is a Ni-Cu-PGE metal reference.

    The chalcophile references carry their own x-axis (ordered by
    compatibility with sulphide liquid), so the caller must switch the
    element order rather than reuse the incompatibility order.
    """
    return name in CHALCOPHILE_NORMS


def chalcophile_order(name: str) -> Tuple[str, ...]:
    """Metal order for *name*, trimmed to the metals it actually carries.

    Becker et al. (2006) report Re but no Rh or Au, so the extended axis
    is used only when the reference has something to put on it.
    """
    values = CHALCOPHILE_NORMS.get(name, {})
    extended = [el for el in CHALCOPHILE_ORDER_EXTENDED if el in values]
    return tuple(extended) if extended else CHALCOPHILE_ORDER


def normaliser_categories() -> Dict[str, list[str]]:
    """Return categorised lists of normaliser names for UI population."""
    return {
        "REE — Chondrite": list(REE_CHONDRITES.keys()),
        "REE — Shale / crustal composite": list(REE_SHALES.keys()),
        "Multi-element": list(MULTIELEMENT_NORMS.keys()),
        "Ni-Cu-PGE metals": list(CHALCOPHILE_NORMS.keys()),
    }
