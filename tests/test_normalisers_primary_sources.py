"""Normalisers and reservoirs against their own papers.

What Rollinson & Pease (2021) could not confirm -- its copy cuts off the
right of Tables 4.7 and 4.9, and Table 4.9 has no P -- was read in the
primary sources on 2026-10-22, every value from the rendered page:

* Boynton (1984), Table 3.3, "Recommended chondrite";
* Taylor & McLennan (1985), Appendix 2 (p. 298), Table 2.15 (upper
  crust) and Table 3.5 (bulk crust), scanned;
* Sun & McDonough (1989), Table 1;
* McDonough & Sun (1995), Tables 2 and 5, for P, K and Ti.

Reading them found Taylor & McLennan's Y at 2.25 where the book prints
2.1, Sun & McDonough's E-MORB P at 1410 where the paper prints 620 --
in the normaliser and in the reservoir both -- and a Taylor & McLennan
upper crust whose oxides had been recomputed from its element
percentages, with a P2O5 the table does not have.
"""

from __future__ import annotations

import pytest

from birds.normalizations import (
    MULTIELEMENT_NORMS,
    REE_CHONDRITES,
)
from birds.reservoirs import RESERVOIRS

BOYNTON_1984 = {
    "La": 0.310, "Ce": 0.808, "Pr": 0.122, "Nd": 0.600, "Sm": 0.195,
    "Eu": 0.0735, "Gd": 0.259, "Tb": 0.0474, "Dy": 0.322, "Ho": 0.0718,
    "Er": 0.210, "Tm": 0.0324, "Yb": 0.209, "Lu": 0.0322,
}

TAYLOR_MCLENNAN_1985_CHONDRITE = {
    "La": 0.367, "Ce": 0.957, "Pr": 0.137, "Nd": 0.711, "Sm": 0.231,
    "Eu": 0.087, "Gd": 0.306, "Tb": 0.058, "Dy": 0.381, "Ho": 0.0851,
    "Er": 0.249, "Tm": 0.0356, "Yb": 0.248, "Lu": 0.0381, "Y": 2.1,
}

#: Sun & McDonough (1989) Table 1, in the order it prints them.
SM89 = {
    "CI": {"La": 0.237, "Ce": 0.612, "Pr": 0.095, "Nd": 0.467,
           "Sm": 0.153, "Eu": 0.058, "Gd": 0.2055, "Tb": 0.0374,
           "Dy": 0.2540, "Ho": 0.0566, "Er": 0.1655, "Tm": 0.0255,
           "Yb": 0.170, "Lu": 0.0254, "Y": 1.57},
    "N-MORB": {"Cs": 0.0070, "Rb": 0.56, "Ba": 6.30, "Th": 0.120,
               "U": 0.047, "Nb": 2.33, "Ta": 0.132, "K": 600, "La": 2.50,
               "Ce": 7.50, "Pb": 0.30, "Pr": 1.32, "Sr": 90, "P": 510,
               "Nd": 7.30, "Sm": 2.63, "Zr": 74, "Hf": 2.05, "Eu": 1.02,
               "Ti": 7600, "Gd": 3.680, "Tb": 0.670, "Dy": 4.550,
               "Y": 28, "Ho": 1.01, "Er": 2.97, "Tm": 0.456, "Yb": 3.05,
               "Lu": 0.455},
    "E-MORB": {"Cs": 0.063, "Rb": 5.04, "Ba": 57, "Th": 0.60, "U": 0.18,
               "Nb": 8.30, "Ta": 0.47, "K": 2100, "La": 6.30, "Ce": 15.0,
               "Pb": 0.60, "Pr": 2.05, "Sr": 155, "P": 620, "Nd": 9.00,
               "Sm": 2.60, "Zr": 73, "Hf": 2.03, "Eu": 0.91, "Ti": 6000,
               "Gd": 2.970, "Tb": 0.530, "Dy": 3.550, "Y": 22,
               "Ho": 0.790, "Er": 2.31, "Tm": 0.356, "Yb": 2.37,
               "Lu": 0.354},
    "OIB": {"Cs": 0.387, "Rb": 31.0, "Ba": 350, "Th": 4.00, "U": 1.02,
            "Nb": 48.0, "Ta": 2.70, "K": 12000, "La": 37.0, "Ce": 80.0,
            "Pb": 3.20, "Pr": 9.70, "Sr": 660, "P": 2700, "Nd": 38.5,
            "Sm": 10.0, "Zr": 280, "Hf": 7.80, "Eu": 3.00, "Ti": 17200,
            "Gd": 7.620, "Tb": 1.050, "Dy": 5.600, "Y": 29, "Ho": 1.06,
            "Er": 2.62, "Tm": 0.350, "Yb": 2.16, "Lu": 0.300},
}

#: Taylor & McLennan (1985) Tables 2.15 and 3.5: the oxides and the
#: trace elements the reservoirs carry.
TM85_UPPER = {
    "SiO2": 66.0, "TiO2": 0.5, "Al2O3": 15.2, "FeOT": 4.5, "MgO": 2.2,
    "CaO": 4.2, "Na2O": 3.9, "K2O": 3.4,
    "Rb": 112, "Sr": 350, "Y": 22, "Zr": 190, "Nb": 25, "Cs": 3.7,
    "Ba": 550, "La": 30, "Ce": 64, "Pr": 7.1, "Nd": 26, "Sm": 4.5,
    "Eu": 0.88, "Gd": 3.8, "Tb": 0.64, "Dy": 3.5, "Ho": 0.80, "Er": 2.3,
    "Tm": 0.33, "Yb": 2.2, "Lu": 0.32, "Hf": 5.8, "Ta": 2.2, "Pb": 20,
    "Th": 10.7, "U": 2.8, "Sc": 11, "V": 60, "Cr": 35, "Co": 10,
    "Ni": 20, "Cu": 25,
}
TM85_BULK = {
    "SiO2": 57.3, "TiO2": 0.9, "Al2O3": 15.9, "FeOT": 9.1, "MgO": 5.3,
    "CaO": 7.4, "Na2O": 3.1, "K2O": 1.1,
    "Rb": 32, "Sr": 260, "Y": 20, "Zr": 100, "Nb": 11, "Cs": 1.0,
    "Ba": 250, "La": 16, "Ce": 33, "Pr": 3.9, "Nd": 16, "Sm": 3.5,
    "Eu": 1.1, "Gd": 3.3, "Tb": 0.60, "Dy": 3.7, "Ho": 0.78, "Er": 2.2,
    "Tm": 0.32, "Yb": 2.2, "Lu": 0.30, "Hf": 3.0, "Ta": 1.0, "Pb": 8.0,
    "Th": 3.5, "U": 0.91, "Sc": 30, "V": 230, "Cr": 185, "Co": 29,
    "Ni": 105, "Cu": 75, "Zn": 80,
}


def _same(ours, printed):
    wrong = {el: (ours.get(el), v) for el, v in printed.items()
             if ours.get(el) is None or ours[el] != pytest.approx(v)}
    assert not wrong, wrong


def test_boynton_1984():
    _same(REE_CHONDRITES["Boynton (1984)"], BOYNTON_1984)
    assert set(REE_CHONDRITES["Boynton (1984)"]) == set(BOYNTON_1984)


def test_taylor_mclennan_1985_chondrite():
    """Y was 2.25; Appendix 2 prints 2.1."""
    ours = REE_CHONDRITES["Taylor & McLennan (1985) – CI calc. volatile-free"]
    _same(ours, TAYLOR_MCLENNAN_1985_CHONDRITE)


def test_sun_mcdonough_1989_chondrite():
    _same(REE_CHONDRITES["Sun & McDonough (1989) – CI"], SM89["CI"])


@pytest.mark.parametrize("basalt", ["N-MORB", "E-MORB"])
def test_sun_mcdonough_1989_morb_normalisers(basalt):
    """E-MORB P was 1410; Table 1 prints 620."""
    ours = MULTIELEMENT_NORMS[f"{basalt} (Sun & McDonough 1989)"]
    _same(ours, SM89[basalt])
    assert set(ours) <= set(SM89[basalt])


@pytest.mark.parametrize("basalt", ["N-MORB", "E-MORB", "OIB"])
def test_sun_mcdonough_1989_reservoir_traces(basalt):
    ours = RESERVOIRS[f"{basalt} (Sun & McDonough 1989)"]
    _same(ours, {el: v for el, v in SM89[basalt].items() if el in ours})


@pytest.mark.parametrize("name, element, value", [
    # McDonough & Sun (1995): Table 2 for CI, Table 5 for pyrolite.
    ("CI Chondrite (McDonough & Sun 1995)", "P", 1080),
    ("CI Chondrite (McDonough & Sun 1995)", "K", 550),
    ("CI Chondrite (McDonough & Sun 1995)", "Ti", 440),
    ("Primitive Mantle (McDonough & Sun 1995)", "P", 90),
    ("Primitive Mantle (McDonough & Sun 1995)", "K", 240),
    ("Primitive Mantle (McDonough & Sun 1995)", "Ti", 1205),
])
def test_mcdonough_sun_1995_p_k_ti(name, element, value):
    assert MULTIELEMENT_NORMS[name][element] == value


@pytest.mark.parametrize("name, printed", [
    ("UCC (Taylor & McLennan 1985)", TM85_UPPER),
    ("Bulk CC (Taylor & McLennan 1985)", TM85_BULK),
])
def test_taylor_mclennan_1985_reservoirs(name, printed):
    """The upper crust's oxides used to be recomputed from its element
    percentages (SiO2 65.89 for 66.0), with a P2O5 it does not print."""
    ours = RESERVOIRS[name]
    _same(ours, printed)
    assert "P2O5" not in ours


def test_rudnick_gao_upper_crust_reservoir_follows_its_own_oxides():
    """Rb, K and Ti were 82, 23200 and 3840, as the normaliser carried
    them before it was checked; K and Ti follow from K2O and TiO2."""
    from birds.normalizations import OXIDE_TO_ELEMENT_PPM
    ucc = RESERVOIRS["UCC (Rudnick & Gao 2003)"]
    assert ucc["Rb"] == 84
    assert ucc["K"] == pytest.approx(ucc["K2O"] * 8301.5, abs=1)
    assert ucc["Ti"] == pytest.approx(
        ucc["TiO2"] * OXIDE_TO_ELEMENT_PPM["Ti"][1], abs=1)
    norm = MULTIELEMENT_NORMS["Upper Continental Crust (Rudnick & Gao 2014)"]
    assert (ucc["Rb"], ucc["K"], ucc["Ti"]) == (norm["Rb"], norm["K"],
                                                norm["Ti"])
