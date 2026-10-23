"""Reservoirs against their own papers, read on 2026-10-23.

* Rudnick & Gao (2003) Table 11 -- upper, middle, lower and total crust;
* Workman & Hart (2005) Table 2 (traces) and Table 3 (majors) -- DMM;
* Hirose & Kushiro (1993) Table 2 -- KLB-1;
* Walter (1998) Table 1, column 1 -- KR4003;
* Hirschmann et al. (2003) Table 1, run 95MMH09 -- MIX1G.

Reading them found the middle crust's Pb and Sc at 15.3 and 22 for
15.2 and 19; a DMM whose Nb, Ta, Sr, Cr and Ni were not Workman &
Hart's and which carried Cs, Sc, V and Co they do not give; a KR4003
and a MIX1G that differed from their tables in almost every oxide; and
MIX1G cited to a *J. Petrol.* paper it is not in.  The three Sun &
McDonough (1989) basalts carried oxides the paper does not print, and
now carry its trace elements only.
"""

from __future__ import annotations

import pytest

from birds.normalizations import MULTIELEMENT_NORMS
from birds.reservoirs import RESERVOIRS

_MAJORS = ("SiO2", "TiO2", "Al2O3", "FeOT", "MnO", "MgO", "CaO", "Na2O",
           "K2O", "P2O5")

#: Rudnick & Gao (2003) Table 11, the elements the reservoirs carry.
RG03 = {
    "UCC": {
        "SiO2": 66.6, "TiO2": 0.64, "Al2O3": 15.4, "FeOT": 5.04,
        "MnO": 0.10, "MgO": 2.48, "CaO": 3.59, "Na2O": 3.27, "K2O": 2.80,
        "P2O5": 0.15,
        "Sc": 14.0, "V": 97, "Cr": 92, "Co": 17.3, "Ni": 47, "Cu": 28,
        "Zn": 67, "Ga": 17.5, "Rb": 84, "Sr": 320, "Y": 21, "Zr": 193,
        "Nb": 12, "Cs": 4.9, "Ba": 628, "La": 31, "Ce": 63, "Pr": 7.1,
        "Nd": 27, "Sm": 4.7, "Eu": 1.0, "Gd": 4.0, "Tb": 0.7, "Dy": 3.9,
        "Ho": 0.83, "Er": 2.3, "Tm": 0.30, "Yb": 2.0, "Lu": 0.31,
        "Hf": 5.3, "Ta": 0.9, "Pb": 17, "Th": 10.5, "U": 2.7,
    },
    "MCC": {
        "SiO2": 63.5, "TiO2": 0.69, "Al2O3": 15.0, "FeOT": 6.02,
        "MnO": 0.10, "MgO": 3.59, "CaO": 5.25, "Na2O": 3.39, "K2O": 2.30,
        "P2O5": 0.15,
        "Sc": 19, "V": 107, "Cr": 76, "Co": 22, "Ni": 33.5, "Cu": 26,
        "Zn": 69.5, "Ga": 17.5, "Rb": 65, "Sr": 282, "Y": 20, "Zr": 149,
        "Nb": 10, "Cs": 2.2, "Ba": 532, "La": 24, "Ce": 53, "Pr": 5.8,
        "Nd": 25, "Sm": 4.6, "Eu": 1.4, "Gd": 4.0, "Tb": 0.7, "Dy": 3.8,
        "Ho": 0.82, "Er": 2.3, "Tm": 0.32, "Yb": 2.2, "Lu": 0.4,
        "Hf": 4.4, "Ta": 0.6, "Pb": 15.2, "Th": 6.5, "U": 1.3,
    },
    "LCC": {
        "SiO2": 53.4, "TiO2": 0.82, "Al2O3": 16.9, "FeOT": 8.57,
        "MnO": 0.10, "MgO": 7.24, "CaO": 9.59, "Na2O": 2.65, "K2O": 0.61,
        "P2O5": 0.10,
        "Sc": 31, "V": 196, "Cr": 215, "Co": 38, "Ni": 88, "Cu": 26,
        "Zn": 78, "Ga": 13, "Rb": 11, "Sr": 348, "Y": 16, "Zr": 68,
        "Nb": 5, "Cs": 0.3, "Ba": 259, "La": 8, "Ce": 20, "Pr": 2.4,
        "Nd": 11, "Sm": 2.8, "Eu": 1.1, "Gd": 3.1, "Tb": 0.48, "Dy": 3.1,
        "Ho": 0.68, "Er": 1.9, "Tm": 0.24, "Yb": 1.5, "Lu": 0.25,
        "Hf": 1.9, "Ta": 0.6, "Pb": 4, "Th": 1.2, "U": 0.2,
    },
    "Bulk CC": {
        "SiO2": 60.6, "TiO2": 0.72, "Al2O3": 15.9, "FeOT": 6.71,
        "MnO": 0.10, "MgO": 4.66, "CaO": 6.41, "Na2O": 3.07, "K2O": 1.81,
        "P2O5": 0.13,
        "Sc": 21.9, "V": 138, "Cr": 135, "Co": 26.6, "Ni": 59, "Cu": 27,
        "Zn": 72, "Ga": 16, "Rb": 49, "Sr": 320, "Y": 19, "Zr": 132,
        "Nb": 8, "Cs": 2, "Ba": 456, "La": 20, "Ce": 43, "Pr": 4.9,
        "Nd": 20, "Sm": 3.9, "Eu": 1.1, "Gd": 3.7, "Tb": 0.6, "Dy": 3.6,
        "Ho": 0.77, "Er": 2.1, "Tm": 0.28, "Yb": 1.9, "Lu": 0.30,
        "Hf": 3.7, "Ta": 0.7, "Pb": 11, "Th": 5.6, "U": 1.3,
    },
}

#: Workman & Hart (2005): Table 3 bulk DMM, Table 2 average DMM.
WH05_TABLE3 = {
    "SiO2": 44.71, "Al2O3": 3.98, "FeOT": 8.18, "MnO": 0.13,
    "MgO": 38.73, "CaO": 3.17, "Na2O": 0.13, "TiO2": 0.13,
    "K2O": 0.006, "P2O5": 0.019,
}
WH05_CR2O3, WH05_NIO = 0.57, 0.24
WH05_TABLE2 = {
    "Rb": 0.050, "Ba": 0.563, "Th": 0.0079, "U": 0.0032, "Nb": 0.1485,
    "Ta": 0.0096, "La": 0.192, "Ce": 0.550, "Pb": 0.018, "Pr": 0.107,
    "Nd": 0.581, "Sr": 7.664, "Zr": 5.082, "Hf": 0.157, "Sm": 0.239,
    "Eu": 0.096, "Ti": 716.3, "Gd": 0.358, "Tb": 0.070, "Dy": 0.505,
    "Ho": 0.115, "Y": 3.328, "Er": 0.348, "Yb": 0.365, "Lu": 0.058,
}

#: Hirose & Kushiro (1993) Table 2, KLB-1.
HK93_KLB1 = {
    "SiO2": 44.48, "TiO2": 0.16, "Al2O3": 3.59, "FeOT": 8.10,
    "MnO": 0.12, "MgO": 39.22, "CaO": 3.44, "Na2O": 0.30, "K2O": 0.02,
    "P2O5": 0.03,
}

#: Walter (1998) Table 1, column 1, KR4003.  No P2O5.
W98_KR4003 = {
    "SiO2": 44.9, "TiO2": 0.16, "Al2O3": 4.26, "FeOT": 8.02,
    "MnO": 0.13, "MgO": 37.3, "CaO": 3.45, "Na2O": 0.22, "K2O": 0.09,
}

#: Hirschmann et al. (2003) Table 1, 95MMH09 glass, "MIX1G bulk".
H03_MIX1G = {
    "SiO2": 45.6, "TiO2": 0.90, "Al2O3": 15.2, "FeOT": 7.8,
    "MnO": 0.15, "MgO": 16.67, "CaO": 11.48, "Na2O": 1.4, "K2O": 0.04,
    "P2O5": 0.01,
}


def _same(ours, printed):
    wrong = {el: (ours.get(el), v) for el, v in printed.items()
             if ours.get(el) is None or ours[el] != pytest.approx(v)}
    assert not wrong, wrong


@pytest.mark.parametrize("part", ["UCC", "MCC", "LCC", "Bulk CC"])
def test_rudnick_gao_2003_table_11(part):
    """The middle crust's Pb and Sc were 15.3 and 22."""
    ours = RESERVOIRS[f"{part} (Rudnick & Gao 2003)"]
    _same(ours, RG03[part])
    # Nothing beyond the table but the upper crust's K and Ti, which
    # are its K2O and TiO2 as element.
    assert set(ours) - set(RG03[part]) <= {"K", "Ti"}


def test_the_bulk_crust_normaliser_is_table_11():
    """K, Ti and P were 15000, 4320 and 655, the last the upper crust's;
    every trace element already agreed."""
    norm = MULTIELEMENT_NORMS["Bulk Continental Crust (Rudnick & Gao 2014)"]
    bulk = RG03["Bulk CC"]
    _same(norm, {el: bulk[el] for el in norm if el in bulk})
    assert norm["K"] == round(bulk["K2O"] * 8301.47) == 15026
    assert norm["Ti"] == round(bulk["TiO2"] * 5993.4) == 4315
    assert norm["P"] == round(bulk["P2O5"] * 4364.3) == 567


def test_the_2003_upper_crust_is_the_one_rollinson_and_pease_print():
    """Why the 2003 edition can stand in for the 2014 one the
    normalisers are named after: the upper-crust normaliser, checked
    against Rollinson & Pease's 2014 column, equals the 2003 table."""
    norm = MULTIELEMENT_NORMS["Upper Continental Crust (Rudnick & Gao 2014)"]
    ucc = RG03["UCC"]
    _same(norm, {el: ucc[el] for el in norm if el in ucc})


def test_workman_hart_2005():
    """Nb, Ta and Sr were 0.21, 0.0138 and 7.66; Cr and Ni 2500 and
    1960 for the 3900 and 1886 of the table's oxides."""
    dmm = RESERVOIRS["Depleted MORB mantle (Workman & Hart 2005)"]
    _same(dmm, WH05_TABLE3)
    _same(dmm, WH05_TABLE2)
    assert dmm["Cr"] == round(WH05_CR2O3 * 6842, -2) == 3900
    assert dmm["Ni"] == round(WH05_NIO * 7858) == 1886


def test_workman_hart_2005_carries_nothing_they_do_not_give():
    dmm = RESERVOIRS["Depleted MORB mantle (Workman & Hart 2005)"]
    extra = set(dmm) - set(WH05_TABLE3) - set(WH05_TABLE2) - {"Cr", "Ni"}
    assert not extra, extra
    for gone in ("Cs", "Sc", "V", "Co"):
        assert gone not in dmm


@pytest.mark.parametrize("name, printed", [
    ("Spinel lherzolite (KLB-1)", HK93_KLB1),
    ("Garnet lherzolite (KR4003)", W98_KR4003),
    ("Pyroxenite (MIX1G)", H03_MIX1G),
])
def test_experimental_starting_compositions(name, printed):
    """KLB-1 was right; KR4003 and MIX1G differed in most oxides."""
    ours = RESERVOIRS[name]
    _same(ours, printed)
    assert set(ours) == set(printed)


def test_kr4003_has_no_p2o5():
    """Walter's Table 1 prints none; this one used to carry 0.02."""
    assert "P2O5" not in RESERVOIRS["Garnet lherzolite (KR4003)"]


@pytest.mark.parametrize("basalt", ["N-MORB", "E-MORB", "OIB"])
def test_sun_mcdonough_basalts_carry_no_oxides(basalt):
    """Table 1 of Sun & McDonough (1989) is trace elements only."""
    ours = RESERVOIRS[f"{basalt} (Sun & McDonough 1989)"]
    assert not set(ours) & set(_MAJORS)


def test_mix1g_is_cited_where_it_is_published():
    from birds import reservoirs
    doc = reservoirs.__doc__
    assert "Geology* 31, 481-484" in doc
    assert "Kogiso" in doc
    from birds.references import REFERENCES
    blob = " ".join(c for _, items in REFERENCES for c, _ in items)
    for fragment in ("10.1130/0091-7613(2003)031<0481:AMGBPM>2.0.CO;2",
                     "10.1016/j.epsl.2004.12.005",
                     "10.1016/0012-821X(93)90077-M",
                     "10.1093/petroj/39.1.29",
                     "10.1016/B0-08-043751-6/03016-4"):
        assert fragment in blob
