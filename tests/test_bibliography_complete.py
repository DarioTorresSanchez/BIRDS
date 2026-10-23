"""The bibliography, checked against Crossref and the papers on 2026-10-23.

Every DOI was resolved on Crossref and its title, first author, year,
volume and first page compared with the citation; every citation
without one was searched for.  What that found:

* Yang et al. (2019) was cited as a *Lithos* paper by other authors
  that does not exist; it is Yang, Li, Jiang, Xu, Guo, Li & Zhang,
  *JGR Solid Earth* 124, 3458-3490 -- and the diagrams gave its pages
  as 3429-3480.
* The Hanski entry was another Hanski (2001), on Os-Nd isotopes in
  *Precambrian Research*; the diagram's is the *J. Petrol.* paper.
* Verma's book is *Road from Geochemistry to Geochemometrics*,
  Springer 2020, not "Road to geochemistry", Elsevier 2021, whose DOI
  did not resolve.
* The PySide6 "DOI" was a Zenodo record of a figure in a paper on
  millipedes.
* Cross et al. is 1902, *J. Geol.* 10, not 1903 and 11.

Diagrams, normalisers and reservoirs named authors the bibliography
did not hold -- Frost & Frost 2008, Hanski 1992, Jahn et al. 1981,
Jensen & Pyke 1982, Kuno 1966, MacDonald 1968, Le Maitre et al. 1989,
Shand 1943, Verma 2010 and the sources of seven normalisers.  The tests
below find any such gap from the names themselves.
"""

from __future__ import annotations

import re
import unicodedata

import pytest

from birds.references import REFERENCES

_AUTHOR_YEAR = re.compile(
    r"([A-Z][A-Za-zÀ-ÿ'\-]+)(?: (?:&|and) [A-Z][A-Za-zÀ-ÿ'\-]+)?"
    r"(?: et al\.)?,? \(?((?:1[89]|20)\d\d)[a-z]?\)?")

#: Words the pattern takes for an author that are not one.
_NOT_AUTHORS = {"Figure", "Fig", "Table", "Lithosphere", "Nature", "JGR",
                "Geology", "Lithos", "Earth", "The", "Supplementary",
                "Verma's"}


def _fold(text: str) -> str:
    return (unicodedata.normalize("NFKD", text).encode("ascii", "ignore")
            .decode().lower())


_BIB = [_fold(c) for _, items in REFERENCES for c, _ in items]
_BLOB = " ".join(c for _, items in REFERENCES for c, _ in items)


def _cited(texts):
    found = set()
    for text in texts:
        for m in _AUTHOR_YEAR.finditer(text):
            if m.group(1) not in _NOT_AUTHORS:
                found.add((m.group(1), m.group(2)))
    return found


def _missing(pairs):
    return sorted((name, year) for name, year in pairs
                  if not any(_fold(name) in c[:160] and year in c[:220]
                             for c in _BIB))


def test_every_author_a_diagram_cites_is_in_the_bibliography():
    from birds.diagrams.registry import _REGISTRY
    texts = [f"{d.title} {d.citation}" for d in _REGISTRY.values()]
    assert _missing(_cited(texts)) == []


def test_every_normaliser_and_reservoir_source_is_in_the_bibliography():
    from birds import normalizations as N
    from birds.reservoirs import RESERVOIRS
    names = [*N.REE_CHONDRITES, *N.REE_SHALES, *N.MULTIELEMENT_NORMS,
             *RESERVOIRS]
    assert _missing(_cited(names)) == []


def test_every_index_description_source_is_in_the_bibliography():
    from birds import stats_engine as S
    texts = [*S.ANOMALY_DESCRIPTIONS.values(),
             *S.ALTERATION_DESCRIPTIONS.values(), *S.RATIO_NOTES.values()]
    assert _missing(_cited(texts)) == []


@pytest.mark.parametrize("fragment", [
    "10.1029/2018JB016145",                 # Yang et al. 2019
    "3458-3490",
    "10.1093/petrology/42.5.855",           # Hanski et al. 2001
    "10.1007/978-981-13-9278-8",            # Verma 2020
    "10.1086/621030",                       # Cross et al. 1902
    "10.1093/petrology/egn054",             # Frost & Frost 2008
    "10.1016/S0016-7037(81)80002-6",        # Jahn et al. 1981
    "10.3906/yer-0901-6",                   # Verma 2010
    "10.1016/0012-8252(66)90010-9",         # Fisher 1966
    "10.1016/0012-821X(86)90038-5",         # Hofmann et al. 1986
    "10.1016/j.chemgeo.2011.08.011",        # Pourmand et al. 2012
])
def test_corrected_citations_present(fragment):
    assert fragment in _BLOB


@pytest.mark.parametrize("fragment", [
    "Re-evaluating geochemical",            # the Yang paper that is not
    "3429",
    "Akanvaara",                            # the other Hanski 2001
    "Road to geochemistry",
    "C2019-0-04415-4",
    "zenodo.7891302",
    "(1903)",
])
def test_wrong_citations_absent(fragment):
    assert fragment not in _BLOB


def test_the_diagrams_give_yangs_pages_as_printed():
    from birds.diagrams.registry import _REGISTRY
    for key in ("yang_2019_fcms", "yang_2019_fckantms"):
        assert "3458-3490" in _REGISTRY[key].citation


def test_no_doi_appears_twice_for_different_works():
    dois = re.findall(r"https://doi\.org/(\S+)", _BLOB)
    by_doi = {}
    for _, items in REFERENCES:
        for cit, _desc in items:
            for doi in re.findall(r"https://doi\.org/(\S+)", cit):
                by_doi.setdefault(doi, set()).add(cit.split("(")[0])
    shared = {d: a for d, a in by_doi.items() if len(a) > 1}
    # Pearce (2008) and Verma (2015) are each cited twice, once for the
    # diagrams and once for their anomalies; the same work.
    assert set(shared) <= {"10.1016/j.lithos.2007.06.016",
                           "10.3906/yer-1412-31"}, shared
    assert len(dois) >= 100
