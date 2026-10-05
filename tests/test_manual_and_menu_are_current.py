"""The manual and the menu must describe the program as it is.

Both had gone stale, and neither in a way anyone would notice by
looking. The manual still said "52 plotting templates", "33 tectonic
diagrams", "14 published discriminators" and "Five tabs"; the tectonic
menu still named eleven diagrams by the axis order they had *before*
this autumn's corrections, so the combo said "Ti/Y vs Zr/Y" while the
plot it opened was titled "Zr/Y vs Ti/Y".

Counts in prose drift silently because nothing recomputes them. These
tests recompute them.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

from birds.diagrams.catalog import (
    TECTONIC_PLUTONIC,
    TECTONIC_VOLCANIC,
)
from birds.diagrams.registry import _REGISTRY, get_diagram
from birds.normalizations import (
    CHALCOPHILE_NORMS,
    MULTIELEMENT_NORMS,
    REE_CHONDRITES,
    REE_SHALES,
)
from birds.tectonic_results import DISCRIMINATORS

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs"))


@pytest.fixture(scope="module")
def manual_text():
    import manual_content

    out = []
    for _title, blocks in manual_content.SECTIONS:
        for block in blocks:
            if "text" in block:
                out.append(block["text"])
            out.extend(block.get("items", []))
    return " ".join(out)


def _count_before(text, phrase):
    """The integer immediately preceding *phrase*."""
    m = re.search(r"(\d+)\s+" + re.escape(phrase), text)
    assert m, f"the manual no longer says anything about {phrase!r}"
    return int(m.group(1))


# ---------------------------------------------------------------------------
# The manual's counts
# ---------------------------------------------------------------------------

def test_the_template_count_is_right(manual_text):
    assert _count_before(manual_text, "plotting templates") == len(_REGISTRY)


def test_the_tectonic_diagram_count_is_right(manual_text):
    keys = {k for cat in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC)
            for section in cat.values() for _label, k in section}
    assert _count_before(manual_text, "tectonic diagrams") == len(keys)
    assert _count_before(manual_text, "published discriminators") == len(keys)


def test_the_normaliser_count_is_right(manual_text):
    total = (len(REE_CHONDRITES) + len(REE_SHALES)
             + len(MULTIELEMENT_NORMS) + len(CHALCOPHILE_NORMS))
    assert _count_before(manual_text, "published normalisers") == total


@pytest.mark.parametrize("phrase, table", [
    ("REE chondrite normalisers", REE_CHONDRITES),
    ("REE shale composites", REE_SHALES),
    ("multi-element references", MULTIELEMENT_NORMS),
])
def test_the_spider_tables_are_counted_right(manual_text, phrase, table):
    assert _count_before(manual_text, phrase) == len(table)


def test_the_discriminator_row_count_is_right(manual_text):
    assert _count_before(manual_text, "tectonic\ndiscrimination parameters"
                         .replace("\n", " ")) == len(DISCRIMINATORS)
    assert _count_before(manual_text, "parameters, ticked") == len(
        DISCRIMINATORS)


def test_the_statistics_tab_count_is_right(manual_text):
    """Eight now; it said five, from before the paper, tectonic and
    plot tabs were added."""
    from birds.views import statistics

    source = Path(statistics.__file__).read_text()
    tabs = re.findall(r"self\._add_tab\(", source)
    words = {5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"}
    assert f"{words[len(tabs)]} tabs" in manual_text


# ---------------------------------------------------------------------------
# The menu against the plot it opens
# ---------------------------------------------------------------------------

def _axes(label):
    """The (y, x) pair a label names, or None if it names no pair."""
    head = re.split(r"\s+[-—]\s+", label)[0]
    head = re.sub(r"\([^)]*\)", " ", head)            # drop parentheticals
    # Titles carry mathtext for subscripts -- "Th$_N$", "TiO$_2$" --
    # and the menu spells the same thing plainly, so both are reduced
    # to bare letters and digits before comparing.
    head = re.sub(r"[${}_\\]", "", head)
    head = head.replace("\u2212", "-").replace("\u00d7", "x")
    parts = re.split(r"\s+vs\.?\s+", head)
    if len(parts) != 2:
        return None
    return tuple(p.strip().lower().replace(" ", "") for p in parts)


CATALOGUE = sorted({
    (label, key)
    for cat in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC)
    for section in cat.values()
    for label, key in section
})


@pytest.mark.parametrize("label, key", CATALOGUE)
def test_the_menu_names_the_axes_the_plot_draws(label, key):
    """A combo entry and the plot title it opens must agree.

    Eleven of these disagreed: the menu kept the axis order from
    before the diagrams were rebuilt from their sources, so a user
    picked "Ti/Y vs Zr/Y" and got a plot titled "Zr/Y vs Ti/Y".
    """
    menu = _axes(label)
    title = _axes(get_diagram(key).title)
    if menu is None or title is None:
        pytest.skip("not an 'A vs B' label")
    assert menu == title, f"{key}: menu {menu}, plot {title}"


def test_every_catalogue_entry_resolves():
    for _label, key in CATALOGUE:
        assert get_diagram(key) is not None, key


def test_every_diagram_is_reachable_from_some_menu():
    """A template nobody can open is a template nobody tests by hand."""
    from birds.diagrams.catalog import (
        CLASSIFICATION_PLUTONIC,
        CLASSIFICATION_VOLCANIC,
    )

    from birds.views.petrography import _PETROGRAPHY_CATALOG

    listed = {k for _l, k in CATALOGUE}
    listed |= {k for _l, k in CLASSIFICATION_VOLCANIC}
    listed |= {k for _l, k in CLASSIFICATION_PLUTONIC}
    listed |= {k for _l, k in _PETROGRAPHY_CATALOG}
    unreachable = set(_REGISTRY) - listed
    assert not unreachable, f"not in any menu: {sorted(unreachable)}"
