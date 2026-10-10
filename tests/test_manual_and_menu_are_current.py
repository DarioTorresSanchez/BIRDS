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
    ("Ni-Cu-PGE metal references", CHALCOPHILE_NORMS),
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


# ---------------------------------------------------------------------------
# The menu bar, and the map's controls, as the manual names them
# ---------------------------------------------------------------------------

def _section(title_word):
    import manual_content

    for title, blocks in manual_content.SECTIONS:
        if title_word in title:
            return blocks
    raise AssertionError(f"the manual has no section on {title_word!r}")


@pytest.fixture(scope="module")
def menu_titles(qapp):
    from birds.main_window import BirdsMainWindow

    window = BirdsMainWindow()
    return [a.text().replace("&", "") for a in window.menuBar().actions()]


def test_the_manual_lists_every_menu_in_order(menu_titles):
    """It listed six, with the Map, Petrography, Norm, Isotopes and
    References menus missing and "14" tectonic diagrams."""
    blocks = _section("interface")
    items = next(b["items"] for b in blocks if b["type"] == "bullet")
    assert [item.split(" — ")[0] for item in items] == menu_titles
    words = {9: "nine", 10: "ten", 11: "eleven", 12: "twelve",
             13: "thirteen"}
    intro = " ".join(b.get("text", "") for b in blocks)
    assert f"{words[len(menu_titles)]} menus" in intro


def test_the_sections_are_numbered_in_order():
    import manual_content

    for n, (title, blocks) in enumerate(manual_content.SECTIONS, 1):
        assert title.startswith(f"{n}. "), title
        for block in blocks:
            sub = re.match(r"(\d+)\.\d+\s", block.get("text", ""))
            if block["type"] == "h2" and sub:
                assert int(sub.group(1)) == n, block["text"]


def test_the_manual_names_the_maps_tabs_and_controls(qapp, manual_text):
    """What the map section tells the user to click must exist, under
    the name it gives."""
    from birds.data_manager import DataManager
    from birds.plot_style import PlotStyle
    from birds.views.map_view import MapView

    view = MapView(DataManager(), PlotStyle())
    tabs = [view.display_tabs.tabText(i)
            for i in range(view.display_tabs.count())]
    for tab in tabs:
        assert f"{tab} — " in manual_text, tab
    # Both ways round: a name tested only for being *in* the manual
    # passes when the control is renamed to a piece of another name
    # ("Auto-fit" sits inside "Auto-fit to samples").
    named = {
        "Auto-fit to samples": view.auto_extent_chk,
        "Colour by the analysed variable": view.colour_by_value_chk,
        "Fit automatically": view.auto_fit_chk,
        "Clip to each group's sample hull": view.clip_chk,
        "Contour lines on the estimate": view.contours_chk,
        "Export grid for a GIS (.asc)…": view.export_grid_btn,
    }
    for name, widget in named.items():
        assert name in manual_text, name
        assert widget.text() == name, (name, widget.text())
    for combo in (view.pooling_combo,):
        for i in range(combo.count()):
            assert combo.itemText(i) in manual_text, combo.itemText(i)
    assert "Map → Sample locations and kriging…" in manual_text


def test_the_manual_names_the_majors_switch_and_the_mg_numbers(
        qapp, manual_text):
    from birds.derived import DERIVED
    from birds.views.widgets import AdjustedMajorsBox

    box = AdjustedMajorsBox()
    assert f"{box.title()} panel" in manual_text
    assert box.check.text() in manual_text
    for name in DERIVED:
        assert f"{name} — " in manual_text, name


def test_the_manual_names_the_session_menu_and_the_app_updater(
        qapp, manual_text):
    """Sections 4.5-4.6 and 13.3: the session commands by the names and
    shortcuts the Data menu shows, and the updater by a path that
    exists."""
    from PySide6.QtGui import QAction
    from PySide6.QtWidgets import QMenu

    from birds.main_window import BirdsMainWindow

    window = BirdsMainWindow()
    actions = {a.text(): a.shortcut().toString()
               for a in window.findChildren(QAction)}
    actions.update({m.title(): "" for m in window.findChildren(QMenu)})
    for name in ("Save session", "Save session as…", "Open session…",
                 "Recent sessions"):
        assert name in actions, name
        shortcut = actions[name]
        mentioned = f"Data → {name} ({shortcut})" if shortcut else \
            f"Data → {name}"
        assert mentioned in manual_text, mentioned
    root = Path(__file__).resolve().parents[1]
    scripts = set(re.findall(r"python3? (\S+\.py)\b", manual_text))
    assert "packaging/update_mac_app.py" in scripts
    for script in scripts:                  # every one it says to run
        assert (root / script).is_file(), script
    assert window._autosave_timer.interval() == 5 * 60 * 1000
    assert "every five minutes" in manual_text


# ---------------------------------------------------------------------------
# docs/DIAGRAM_PROVENANCE.md
# ---------------------------------------------------------------------------

def _menu_keys():
    from birds.diagrams.catalog import (
        CLASSIFICATION_PLUTONIC,
        CLASSIFICATION_VOLCANIC,
    )

    keys = [k for _l, k in CLASSIFICATION_VOLCANIC + CLASSIFICATION_PLUTONIC]
    keys += [k for cat in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC)
             for section in cat.values() for _l, k in section]
    return keys


@pytest.fixture(scope="module")
def provenance():
    return (Path(__file__).resolve().parents[1] / "docs"
            / "DIAGRAM_PROVENANCE.md").read_text(encoding="utf-8")


def test_the_provenance_counts_are_the_catalogues(provenance):
    """Its summary said 28 checked and 19 still to measure for two
    weeks after all but three had been settled."""
    keys = _menu_keys()
    assert f"**{len(set(keys))} unique diagrams**" in provenance
    assert f"The menus list {len(keys)} entries" in provenance

    summary = provenance.split("## Summary", 1)[1].split("\n---", 1)[0]
    rows = re.findall(r"^\| (.+?) \| \**(\d+)\** \|", summary, re.MULTILINE)
    counts = {label.strip("* "): int(n) for label, n in rows}
    total = counts.pop("Total")
    assert total == len(set(keys)) == sum(counts.values())

    blocked = provenance.split("## Still drawn by eye", 1)[1].split("\n## ")[0]
    named = set(re.findall(r"`(\w+)`", blocked.split("\n\n", 3)[2]))
    assert counts["Still drawn by eye, blocked on sources"] == len(named)
    assert named <= set(keys)


def test_every_diagram_in_the_menus_has_a_provenance_entry(provenance):
    missing = sorted(k for k in set(_menu_keys())
                     if f"`{k}`" not in provenance)
    assert not missing, f"no provenance entry: {missing}"
