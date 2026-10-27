"""The header above each plot shows subscripts, not mathtext.

Diagram titles and citations are written for matplotlib ("Yb$_N$"), which
renders them on the figure; the QLabel above the plot showed them as
typed -- "Yb$_N$ vs Dy$_N$ — Saccani (2015)".
"""

from __future__ import annotations

import pytest

from birds.diagrams.registry import _REGISTRY
from birds.views.base import header_html


@pytest.mark.parametrize("text, html", [
    ("Yb$_N$ vs Dy$_N$ — Saccani (2015)",
     "Yb<sub>N</sub> vs Dy<sub>N</sub> — Saccani (2015)"),
    ("K$_2$O vs SiO$_2$", "K<sub>2</sub>O vs SiO<sub>2</sub>"),
    ("$^{87}$Sr/$^{86}$Sr", "<sup>87</sup>Sr/<sup>86</sup>Sr"),
    ("Pearce & Gale (1977)", "Pearce &amp; Gale (1977)"),
    ("Ti/V < 20 ⇒ IAB", "Ti/V &lt; 20 ⇒ IAB"),
    ("All Fe as FeO$_T$.", "All Fe as FeO<sub>T</sub>."),
    ("", ""),
])
def test_mathtext_becomes_rich_text(text, html):
    assert header_html(text) == html


@pytest.mark.parametrize("key", sorted(_REGISTRY))
def test_no_header_shows_a_dollar_sign(key):
    diagram = _REGISTRY[key]
    for text in (diagram.title, diagram.citation):
        assert "$" not in header_html(text or "")


@pytest.mark.parametrize("open_view, key", [
    (lambda w: w._open_tectonic("saccani2015_dy_yb", "volcanic", "Mafic"),
     "saccani2015_dy_yb"),
    (lambda w: w.classification.show_diagram("k2o_sio2", "volcanic"),
     "k2o_sio2"),
])
def test_the_view_header_is_rich_text(qapp, open_view, key):
    from PySide6.QtCore import Qt

    from birds.main_window import BirdsMainWindow
    window = BirdsMainWindow()
    open_view(window)
    view = (window.tectonic if key.startswith("saccani")
            else window.classification)
    assert view.title_label.textFormat() == Qt.TextFormat.RichText
    assert "$" not in view.title_label.text()
    assert "<sub>" in view.title_label.text()
