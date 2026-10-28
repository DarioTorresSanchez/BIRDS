"""Diagram names with an "&" keep it in the menus.

In a Qt menu "&" marks the shortcut letter and is not drawn, so the
Tectonic menu read "Pearce  Gale 1977", "Butler  Woronow", "Verma
Agrawal 2011"; seen while taking the README screenshots.  "&&" draws
one "&".
"""

from __future__ import annotations

import pytest
from PySide6.QtWidgets import QMenu

from birds.diagrams.catalog import TECTONIC_PLUTONIC, TECTONIC_VOLCANIC


@pytest.fixture(scope="module")
def tectonic_menu(qapp):
    from birds.main_window import BirdsMainWindow
    window = BirdsMainWindow()
    bar = window.menuBar()
    return next(m for m in bar.findChildren(QMenu)
                if m.parent() is bar and m.title() == "&Tectonic diagrams")


def _entries(menu, family):
    family_menu = next(m for m in menu.findChildren(QMenu)
                       if m.parent() is menu and m.title() == family)
    for sub in family_menu.findChildren(QMenu):
        if sub.parent() is family_menu:
            for action in sub.actions():
                yield sub.title(), action.text()


@pytest.mark.parametrize("family, catalogue", [
    ("Volcanic", TECTONIC_VOLCANIC), ("Plutonic", TECTONIC_PLUTONIC),
])
def test_every_tectonic_entry_shows_its_name_whole(tectonic_menu, family,
                                                   catalogue):
    shown = {(c, text.replace("&&", "&")) for c, text in
             _entries(tectonic_menu, family)}
    wanted = {(c, label) for c, entries in catalogue.items()
              for label, _ in entries}
    assert shown == wanted
    for _, text in _entries(tectonic_menu, family):
        # every "&" doubled: none is taken as a shortcut marker
        assert "&" not in text.replace("&&", "")


def test_the_names_with_an_ampersand_are_there(tectonic_menu):
    texts = [t for _, t in _entries(tectonic_menu, "Volcanic")]
    assert "Zr/Y vs Ti/Y - Pearce && Gale 1977" in texts
    assert "TiO2-Nb-V-Y-Zr DF set (5 panels) - Verma && Agrawal 2011" in texts
