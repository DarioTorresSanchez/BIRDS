"""Reference compositions and the bibliography that must back them."""

from __future__ import annotations

import pytest

from birds.normalizations import (
    CHALCOPHILE_NORMS,
    CHALCOPHILE_ORDER,
    MULTIELEMENT_NORMS,
    REE_CHONDRITES,
    REE_ORDER,
    REE_SHALES,
    chalcophile_order,
    get_normaliser,
    is_chalcophile_normaliser,
    normaliser_categories,
)

ALL_GROUPS = (REE_CHONDRITES, REE_SHALES, MULTIELEMENT_NORMS,
              CHALCOPHILE_NORMS)
ALL_NAMES = [n for g in ALL_GROUPS for n in g]


@pytest.mark.parametrize("name", ALL_NAMES)
def test_every_normaliser_resolves(name):
    assert get_normaliser(name) is not None


@pytest.mark.parametrize("name", ALL_NAMES)
def test_values_are_positive_and_finite(name):
    """A zero or negative normaliser silently produces inf / NaN ratios."""
    for element, value in get_normaliser(name).items():
        assert isinstance(value, (int, float)), f"{name}/{element}"
        assert value > 0, f"{name}/{element} = {value}"


@pytest.mark.parametrize("name", list(REE_CHONDRITES) + list(REE_SHALES))
def test_ree_normalisers_cover_the_lanthanides(name):
    values = get_normaliser(name)
    missing = [el for el in REE_ORDER if el not in values]
    assert not missing, f"{name} is missing {missing}"


def _duplicated_names() -> list[str]:
    seen, dupes = set(), []
    for group in ALL_GROUPS:
        for name in group:
            if name in seen and name not in dupes:
                dupes.append(name)
            seen.add(name)
    return dupes


@pytest.mark.parametrize("name", _duplicated_names() or [None])
def test_duplicated_names_agree_on_shared_elements(name):
    """The same reference must not carry two different value sets."""
    if name is None:
        pytest.skip("no name appears in more than one category")
    tables = [g[name] for g in ALL_GROUPS if name in g]
    first = tables[0]
    for other in tables[1:]:
        for element in set(first) & set(other):
            assert first[element] == pytest.approx(other[element]), (
                f"{name}/{element} differs between categories")


@pytest.mark.parametrize("name", _duplicated_names() or [None])
def test_duplicated_names_resolve_to_the_richest_table(name):
    """Resolving to the narrow table silently drops half a spidergram."""
    if name is None:
        pytest.skip("no name appears in more than one category")
    tables = [g[name] for g in ALL_GROUPS if name in g]
    assert len(get_normaliser(name)) == max(len(t) for t in tables)


class TestChalcophile:
    @pytest.mark.parametrize("name", list(CHALCOPHILE_NORMS))
    def test_axis_only_asks_for_metals_the_reference_has(self, name):
        """Becker et al. report no Rh or Au — the axis must not invent them."""
        values = CHALCOPHILE_NORMS[name]
        assert set(chalcophile_order(name)) <= set(values)

    @pytest.mark.parametrize("name", list(CHALCOPHILE_NORMS))
    def test_axis_keeps_the_sulphide_compatibility_order(self, name):
        """Ni first, Cu last — the order is what makes the plot readable."""
        order = chalcophile_order(name)
        assert order[0] == "Ni" and order[-1] == "Cu"
        ranks = [CHALCOPHILE_ORDER.index(el) for el in order
                 if el in CHALCOPHILE_ORDER]
        assert ranks == sorted(ranks)

    @pytest.mark.parametrize("name", list(CHALCOPHILE_NORMS))
    def test_flagged_as_chalcophile(self, name):
        assert is_chalcophile_normaliser(name)

    @pytest.mark.parametrize(
        "name", list(REE_CHONDRITES) + list(REE_SHALES)
        + list(MULTIELEMENT_NORMS))
    def test_classical_normalisers_are_not_flagged(self, name):
        """A false positive would swap the x-axis out from under the user."""
        assert not is_chalcophile_normaliser(name)


class TestPublishedMetalValues:
    """Ni-Cu-PGE values pinned to the page they were read from.

    In ng/g as printed; the table holds ppm.  Checking them found the
    Fischer-Gödde primitive-mantle Au at 1.0 where the paper gives 1.7,
    and a CI entry credited to Horan et al. (2003) whose numbers that
    paper does not contain.
    """

    @pytest.mark.parametrize("metal, ng_g", [
        # Fischer-Gödde et al. (2011), Chem. Geol. 280, Table 3 and §5.3.
        ("Ir", 3.5), ("Rh", 1.2), ("Pt", 7.6), ("Pd", 7.1), ("Re", 0.35),
        ("Au", 1.7),
    ])
    def test_fischer_godde_primitive_mantle(self, metal, ng_g):
        table = CHALCOPHILE_NORMS["Primitive Mantle (Fischer-Gödde et al. 2011)"]
        assert table[metal] * 1000 == pytest.approx(ng_g, rel=1e-9)

    @pytest.mark.parametrize("metal, ng_g", [
        # Fischer-Gödde et al. (2010), GCA 74, Table 3, "Mean CI".
        ("Re", 40.7), ("Os", 491), ("Ir", 462), ("Ru", 688), ("Pt", 943),
        ("Rh", 133), ("Pd", 563), ("Au", 149),
    ])
    def test_fischer_godde_ci_chondrite(self, metal, ng_g):
        table = CHALCOPHILE_NORMS["CI Chondrite (Fischer-Gödde et al. 2010)"]
        assert table[metal] * 1000 == pytest.approx(ng_g, rel=1e-9)

    @pytest.mark.parametrize("metal, ng_g", [
        # Becker et al. (2006) as quoted by Fischer-Gödde et al. (2011).
        ("Ir", 3.5), ("Pt", 7.6), ("Pd", 7.1), ("Re", 0.35),
    ])
    def test_becker_primitive_upper_mantle(self, metal, ng_g):
        table = CHALCOPHILE_NORMS["Primitive Upper Mantle (Becker et al. 2006)"]
        assert table[metal] * 1000 == pytest.approx(ng_g, rel=1e-9)

    @pytest.mark.parametrize("name", [
        n for n in CHALCOPHILE_NORMS if "Mantle" in n])
    def test_primitive_mantle_nickel_and_copper(self, name):
        """McDonough & Sun (1995), Table 5: Ni 1960, Cu 30 ppm.  Ni also
        agrees with McDonough (2014a), 0.196 wt.%, in Rollinson & Pease
        (2021), Table 3.2a.  The depleted mantle's own Cu is unchecked."""
        table = CHALCOPHILE_NORMS[name]
        assert table["Ni"] == pytest.approx(PYROLITE["Ni"])
        if "Depleted" not in name:
            assert table["Cu"] == pytest.approx(PYROLITE["Cu"])

    def test_ci_nickel_and_copper(self):
        """McDonough & Sun (1995), Table 2.  They were 10910 and 126."""
        table = CHALCOPHILE_NORMS["CI Chondrite (Fischer-Gödde et al. 2010)"]
        assert table["Ni"] == pytest.approx(CI["Ni"])
        assert table["Cu"] == pytest.approx(CI["Cu"])

    @pytest.mark.parametrize("old", [
        "CI Chondrite (Horan et al. 2003 / McDonough & Sun 1995)",
        "Primitive Mantle (Barnes & Maier 1999)",
    ])
    def test_a_session_saved_under_an_old_name_still_finds_it(self, old):
        from birds.normalizations import current_name
        assert old not in CHALCOPHILE_NORMS
        assert current_name(old) in CHALCOPHILE_NORMS
        assert current_name("Boynton (1984)") == "Boynton (1984)"


# ---------------------------------------------------------------------------
# McDonough & Sun (1995), Chem. Geol. 120, read from the rendered tables
# ---------------------------------------------------------------------------
#
# Table 2, "This study" column, and Table 5, "Pyrolite" column, in ppm
# (the paper prints Nb to U in ppb).  Every table B.I.R.D.S credits to
# this paper must agree with them.

_PPB = 1e-3
CI = dict(
    K=550, Ti=440, P=1080, Sc=5.92, V=56, Cr=2650, Co=500, Ni=10500,
    Cu=120, Rb=2.30, Sr=7.25, Y=1.57,
    Zr=3.82, Nb=240 * _PPB, Cs=190 * _PPB, Ba=2410 * _PPB, La=237 * _PPB,
    Ce=613 * _PPB, Pr=92.8 * _PPB, Nd=457 * _PPB, Sm=148 * _PPB,
    Eu=56.3 * _PPB, Gd=199 * _PPB, Tb=36.1 * _PPB, Dy=246 * _PPB,
    Ho=54.6 * _PPB, Er=160 * _PPB, Tm=24.7 * _PPB, Yb=161 * _PPB,
    Lu=24.6 * _PPB, Hf=103 * _PPB, Ta=13.6 * _PPB, Pb=2470 * _PPB,
    Th=29 * _PPB, U=7.4 * _PPB, Re=40 * _PPB, Os=490 * _PPB,
    Ir=455 * _PPB, Ru=710 * _PPB, Rh=130 * _PPB, Pt=1010 * _PPB,
    Pd=550 * _PPB, Au=140 * _PPB,
)
PYROLITE = dict(
    K=240, Ti=1205, P=90, Sc=16.2, V=82, Cr=2625, Co=105, Ni=1960,
    Cu=30, Rb=0.600, Sr=19.9, Y=4.30,
    Zr=10.5, Nb=658 * _PPB, Cs=21 * _PPB, Ba=6600 * _PPB, La=648 * _PPB,
    Ce=1675 * _PPB, Pr=254 * _PPB, Nd=1250 * _PPB, Sm=406 * _PPB,
    Eu=154 * _PPB, Gd=544 * _PPB, Tb=99 * _PPB, Dy=674 * _PPB,
    Ho=149 * _PPB, Er=438 * _PPB, Tm=68 * _PPB, Yb=441 * _PPB,
    Lu=67.5 * _PPB, Hf=283 * _PPB, Ta=37 * _PPB, Pb=150 * _PPB,
    Th=79.5 * _PPB, U=20.3 * _PPB, Re=0.28 * _PPB, Os=3.4 * _PPB,
    Ir=3.2 * _PPB, Ru=5.0 * _PPB, Rh=0.9 * _PPB, Pt=7.1 * _PPB,
    Pd=3.9 * _PPB, Au=1.0 * _PPB,
)
#: Table 4, pyrolite model 1, wt.% (FeO is all the iron).
PYROLITE_MAJORS = dict(SiO2=45.0, TiO2=0.201, Al2O3=4.45, FeOT=8.05,
                       MnO=0.135, MgO=37.8, CaO=3.55, Na2O=0.36,
                       K2O=0.029, P2O5=0.021)


@pytest.mark.parametrize("table, reference", [
    (REE_CHONDRITES["McDonough & Sun (1995) – CI"], CI),
    (MULTIELEMENT_NORMS["CI Chondrite (McDonough & Sun 1995)"], CI),
    (MULTIELEMENT_NORMS["Primitive Mantle (McDonough & Sun 1995)"], PYROLITE),
    (CHALCOPHILE_NORMS["Primitive Mantle, metals (McDonough & Sun 1995)"],
     PYROLITE),
], ids=["REE CI", "multi-element CI", "multi-element PM", "metals PM"])
def test_every_value_credited_to_mcdonough_and_sun_is_theirs(table,
                                                            reference):
    assert set(table) <= set(reference)
    for element, value in table.items():
        assert value == pytest.approx(reference[element], rel=1e-9), element


def test_the_primitive_mantle_reservoir_is_mcdonough_and_suns():
    """Its majors were 44.95 SiO2, 0.20 TiO2, 0.13 MnO and 37.78 MgO,
    none of which the paper prints."""
    from birds.reservoirs import RESERVOIRS

    table = RESERVOIRS["Primitive mantle (McDonough & Sun 1995)"]
    reference = {**PYROLITE, **PYROLITE_MAJORS}
    assert set(table) <= set(reference)
    for element, value in table.items():
        assert value == pytest.approx(reference[element], rel=1e-9), element


def test_categories_expose_every_normaliser():
    listed = {n for names in normaliser_categories().values() for n in names}
    assert listed == set(ALL_NAMES)


class TestBibliography:
    """Each diagram's printed citation must exist in the bibliography."""

    def test_no_orphan_sections(self):
        from birds.references import REFERENCES
        for title, items in REFERENCES:
            assert items, f"section '{title}' is empty"
            for citation, description in items:
                assert citation.strip() and description.strip()

    @pytest.mark.parametrize("fragment", [
        "Revista Mexicana de Ciencias",   # Verma & Agrawal 2011
        "931-995",                        # Verma & Verma 2013
        "10.1080/00206814.2010.543784",   # Verma et al. 2012
        "168-169",                        # Verma et al. 2013 acid
        "Barnes",                         # Ni-Cu-PGE normalisers
        "Becker",
        "10.1016/j.gca.2009.09.024",      # Fischer-Gödde et al. 2010
        "10.1016/j.chemgeo.2010.11.024",  # Fischer-Gödde et al. 2011
        "10.1016/S0009-2541(02)00405-9",  # Horan et al. 2003
    ])
    def test_verified_citations_present(self, fragment):
        from birds.references import REFERENCES
        blob = " ".join(c for _, items in REFERENCES for c, _ in items)
        assert fragment in blob

    @pytest.mark.parametrize("fragment", [
        "SINCLAS",        # CIPW variant removed
        "Hutchison",      # CIPW variant removed
        "UBIA",           # diagram removed
        "543783",         # wrong DOI
        "931-948",        # wrong page range
        "6027-6048",      # Fischer-Gödde: not the chondrite paper
        "10.1016/j.gca.2011.07.038",
        "element concentrations in chondrites",   # Horan: wrong title
    ])
    def test_removed_or_wrong_citations_absent(self, fragment):
        from birds.references import REFERENCES
        blob = " ".join(c for _, items in REFERENCES for c, _ in items)
        assert fragment not in blob


def test_the_spider_view_restores_a_renamed_reference(qapp):
    """A session saved before the CI entry was renamed must reopen on
    the same reference, not silently on the default."""
    from birds.data_manager import DataManager
    from birds.normalizations import current_name
    from birds.plot_style import PlotStyle
    from birds.views.spider import SpiderView

    old = "CI Chondrite (Horan et al. 2003 / McDonough & Sun 1995)"
    view = SpiderView(DataManager(), PlotStyle())
    view.restore({"mode": "multielement",
                  "multielement": {"normaliser": old}})
    combo = view._controls["multielement"].norm_combo
    assert combo.currentText() == current_name(old)
