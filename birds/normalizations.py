"""Reference normalising compositions for spider diagrams.

* REE chondrite values – Rollinson & Pease (2021), Table 4.7
* REE shale composites – Rollinson & Pease (2021), Table 4.8
* Multi-element normalisers – Rollinson & Pease (2021), Table 4.9

All concentrations are in ppm (μg g⁻¹). Major elements K, Ti and P are
already converted from wt.% oxide to ppm element so that they sit on the
same scale as the trace data.
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
    "Taylor & McLennan (1985) – CI calc. volatile-free": {
        "La": 0.3670, "Ce": 0.9570, "Pr": 0.1370, "Nd": 0.7110,
        "Sm": 0.2310, "Eu": 0.0870, "Gd": 0.3060, "Tb": 0.0580,
        "Dy": 0.3810, "Ho": 0.0851, "Er": 0.2490, "Tm": 0.0356,
        "Yb": 0.2480, "Lu": 0.0381, "Y": 2.2500,
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
        "Er": 3.075, "Tm": 0.4516, "Yb": 3.012, "Lu": 0.4386, "Y": 27.31,
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
        "Cs": 0.01880, "Rb": 0.605, "Ba": 6.85, "Th": 0.0849, "U": 0.0229,
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
    "E-MORB (Sun & McDonough 1989)": {
        "Cs": 0.063, "Rb": 5.04, "Ba": 57, "Th": 0.60, "U": 0.18,
        "Nb": 8.30, "Ta": 0.47, "K": 2100, "La": 6.30, "Ce": 15.0,
        "Pb": 0.60, "Pr": 2.05, "Sr": 155, "P": 1410, "Nd": 9.00,
        "Zr": 73, "Hf": 2.03, "Sm": 2.60, "Eu": 0.91, "Ti": 6000,
        "Gd": 2.97, "Tb": 0.53, "Dy": 3.55, "Ho": 0.79, "Y": 22,
        "Er": 2.31, "Tm": 0.356, "Yb": 2.37, "Lu": 0.354,
    },
    "N-MORB mean (Arevalo & McDonough 2010)": {
        "Cs": 0.019, "Rb": 1.500, "Ba": 16.60, "Th": 0.219, "U": 0.080,
        "Nb": 3.44, "Ta": 0.224, "K": 1620, "La": 3.77, "Ce": 11.5,
        "Pb": 0.57, "Pr": 1.910, "Sr": 130, "Nd": 9.80, "Zr": 90.1,
        "Hf": 2.40, "Sm": 3.25, "Eu": 1.22, "Ti": 8500, "Gd": 4.40,
        "Tb": 0.78, "Dy": 5.110, "Ho": 1.110, "Y": 30, "Er": 3.15,
        "Tm": 0.48, "Yb": 3.00, "Lu": 0.45,
    },
    "Upper Continental Crust (Rudnick & Gao 2014)": {
        "Cs": 4.9, "Rb": 82, "Ba": 628, "Th": 10.5, "U": 2.7,
        "Nb": 12, "Ta": 0.9, "K": 23200, "La": 31, "Ce": 63,
        "Pb": 17, "Pr": 7.1, "Sr": 320, "P": 655, "Nd": 27,
        "Zr": 193, "Hf": 5.3, "Sm": 4.7, "Eu": 1.0, "Ti": 3840,
        "Gd": 4.0, "Tb": 0.7, "Dy": 3.9, "Ho": 0.83, "Y": 21,
        "Er": 2.3, "Tm": 0.30, "Yb": 2.0, "Lu": 0.31,
    },
    "Bulk Continental Crust (Rudnick & Gao 2014)": {
        "Cs": 2.0, "Rb": 49, "Ba": 456, "Th": 5.6, "U": 1.3,
        "Nb": 8, "Ta": 0.7, "K": 15000, "La": 20, "Ce": 43,
        "Pb": 11, "Pr": 4.9, "Sr": 320, "P": 655, "Nd": 20,
        "Zr": 132, "Hf": 3.7, "Sm": 3.9, "Eu": 1.1, "Ti": 4320,
        "Gd": 3.7, "Tb": 0.6, "Dy": 3.6, "Ho": 0.77, "Y": 19,
        "Er": 2.1, "Tm": 0.28, "Yb": 1.9, "Lu": 0.30,
    },
    "NASC (Gromet et al. 1984)": {
        "Cs": 5.16, "Rb": 125, "Ba": 636, "Th": 12.3, "U": 2.66,
        "K": 31545, "La": 31.1, "Ce": 66.7, "Pb": 17.0,
        "Sr": 142, "Nd": 27.4, "Zr": 200, "Hf": 6.30,
        "Sm": 5.59, "Eu": 1.18, "Ti": 4707, "Tb": 0.85, "Y": 21.0,
        "Yb": 3.06, "Lu": 0.456,
    },
}


# ---------------------------------------------------------------------------
# Oxide → element conversion for major elements stored as wt.% oxide.
# Multiply the wt.% value by *factor* to obtain ppm of the element.
# ---------------------------------------------------------------------------

OXIDE_TO_ELEMENT_PPM: Dict[str, Tuple[str, float]] = {
    "K":  ("K2O",  8302),   # K2O wt% × 8302  -> K ppm
    "Ti": ("TiO2", 5995),   # TiO2 wt% × 5995 -> Ti ppm
    "P":  ("P2O5", 4365),
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
    """Return the normalising dict for *name*, regardless of category."""
    for group in (REE_CHONDRITES, REE_SHALES, MULTIELEMENT_NORMS):
        if name in group:
            return group[name]
    return None


def normaliser_categories() -> Dict[str, list[str]]:
    """Return categorised lists of normaliser names for UI population."""
    return {
        "REE — Chondrite": list(REE_CHONDRITES.keys()),
        "REE — Shale / crustal composite": list(REE_SHALES.keys()),
        "Multi-element": list(MULTIELEMENT_NORMS.keys()),
    }
