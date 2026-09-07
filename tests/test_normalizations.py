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
    ])
    def test_removed_or_wrong_citations_absent(self, fragment):
        from birds.references import REFERENCES
        blob = " ".join(c for _, items in REFERENCES for c, _ in items)
        assert fragment not in blob
