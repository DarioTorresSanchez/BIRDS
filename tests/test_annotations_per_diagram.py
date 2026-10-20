"""Annotations belong to the diagram they were drawn on.

Classification, Tectonic, Petrography and Isotopes each show many
diagrams, and each kept one list of annotations for all of them: an
arrow drawn on TAS reappeared, at TAS's coordinates, on AFM, on Jensen
and on every other diagram of the view -- found by the 2026-10-20 audit
as arrows at x = 871 on a Sr-Nd plot.
"""

from __future__ import annotations

import pytest

from birds import annotations as _ann


@pytest.fixture
def window(qapp, full_df, plot_style):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = full_df
    w.style.copy_from(plot_style)
    w.on_dataset_replaced()
    return w


def _texts(view):
    return [t.get_text() for ax in view.canvas.figure.axes for t in ax.texts]


def _show(window, key):
    view = window.classification
    view.show_diagram(key, "volcanic")
    return view


def test_an_annotation_stays_on_its_own_diagram(window):
    window._open_classification_family("volcanic")
    view = _show(window, "tas_volcanic")
    view.annotation_ctl._add(_ann.TextAnnotation(x=55, y=6, text="on TAS"))
    assert "on TAS" in _texts(view)
    _show(window, "afm")
    assert "on TAS" not in _texts(view)
    assert view.annotation_ctl.group.list.count() == 0
    _show(window, "tas_volcanic")
    assert "on TAS" in _texts(view)
    assert view.annotation_ctl.group.list.count() == 1


def test_tectonic_diagrams_keep_their_own(window):
    window._open_tectonic("pearce2008_thyb_nbyb", "volcanic", "Mafic")
    view = window.tectonic
    view.annotation_ctl._add(_ann.TextAnnotation(x=1, y=1, text="Pearce"))
    window._open_tectonic("li2025_nbyb_thnb", "volcanic", "Mafic")
    assert "Pearce" not in _texts(view)
    window._open_tectonic("pearce2008_thyb_nbyb", "volcanic", "Mafic")
    assert "Pearce" in _texts(view)


def test_per_diagram_annotations_survive_a_session(window, tmp_path, qapp):
    from birds.main_window import BirdsMainWindow
    window._open_classification_family("volcanic")
    view = _show(window, "tas_volcanic")
    view.annotation_ctl._add(_ann.TextAnnotation(x=55, y=6, text="TAS note"))
    _show(window, "afm")
    view.annotation_ctl._add(_ann.TextAnnotation(x=0.3, y=0.3, text="AFM note"))
    window._session_path = tmp_path / "s.birds"
    window.on_save_session()

    other = BirdsMainWindow()
    other._load_session_path(tmp_path / "s.birds")
    other._open_classification_family("volcanic")
    reopened = other.classification
    reopened.show_diagram("afm", "volcanic")
    assert "AFM note" in _texts(reopened) and "TAS note" not in _texts(reopened)
    reopened.show_diagram("tas_volcanic", "volcanic")
    assert "TAS note" in _texts(reopened) and "AFM note" not in _texts(reopened)


def test_an_old_session_puts_its_annotations_on_the_saved_diagram(window):
    """Sessions written before this kept a plain list."""
    view = window.classification
    legacy = {"family": "volcanic", "diagram_key": "afm",
              "annotations": [_ann.TextAnnotation(x=0.3, y=0.3,
                                                  text="old").to_dict()]}
    view.restore(legacy)
    window.stack.setCurrentWidget(view)
    view.update_plot()
    assert view._diagram_key == "afm"
    assert "old" in _texts(view)
    view.show_diagram("tas_volcanic", "volcanic")
    assert "old" not in _texts(view)


def test_a_single_diagram_view_still_saves_a_plain_list():
    """The Map and the spider modes have one diagram each: their
    sessions look as they always did."""
    from birds.views.annotation_controller import AnnotationController

    class _View:
        def update_plot(self):
            pass

    ctl = AnnotationController(_View())
    ctl._add(_ann.TextAnnotation(x=1, y=2, text="a"))
    assert isinstance(ctl.serialize(), list)
    ctl.set_context("b")
    ctl._add(_ann.TextAnnotation(x=1, y=2, text="b"))
    data = ctl.serialize()
    assert set(data["by_diagram"]) == {"", "b"}
    ctl.restore(data)
    assert [a.text for a in ctl.annotations] == ["b"]
