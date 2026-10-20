"""What the 2026-10-20 interface audit found, pinned.

The audit drove all 99 menu actions and every diagram over the user's
six saved sessions.  Besides the Rock_Type filter
(``test_rock_type_filter.py``) and the per-diagram annotations
(``test_annotations_per_diagram.py``) it found:

* most panel controls took effect only on *Update plot*;
* Bivariate opened on "No." against an empty "Sample_Label";
* Statistics printed 57.482333333333344, listed empty columns, and lost
  the "&" of "Anomalies & ratios";
* two restored settings were lost again if the session was saved before
  their lists filled;
* the multi-panel legend hung below the figure, cut off;
* the Isotopes menu did not list the isotopes-vs-SiO2 diagram.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure
from PySide6.QtCore import QEventLoop, QTimer


def _wait(ms=350):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()


@pytest.fixture
def window(qapp, full_df, plot_style):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    df = full_df.copy()
    df.insert(1, "No.", range(1, len(df) + 1))
    df.insert(2, "Sample_Label", np.nan)
    df["Latitude"] = np.linspace(19, 20, len(df))
    df["Longitude"] = np.linspace(-101, -100, len(df))
    w.data.df = df
    w.style.copy_from(plot_style)
    w.on_dataset_replaced()
    return w


@pytest.fixture
def draws(monkeypatch):
    count = [0]
    original = Figure.draw

    def counted(self, renderer):
        count[0] += 1
        return original(self, renderer)
    monkeypatch.setattr(Figure, "draw", counted)
    return count


# ---------------------------------------------------------------------------
# Controls redraw at once
# ---------------------------------------------------------------------------

def _redraws(draws, change):
    before = draws[0]
    change()
    _wait()
    return draws[0] - before


def _canvas_draws(view):
    """Count the view's own redraws (each update ends in one)."""
    count = [0]
    original = view.canvas.draw

    def counted(*a, **k):
        count[0] += 1
        return original(*a, **k)
    view.canvas.draw = counted
    return count


def test_axis_and_legend_controls_redraw_at_once(window, draws):
    window._open_bivariate("individual")
    ctrl = window.bivariate._individual
    assert _redraws(draws, lambda: ctrl.axis_grp.log_y.setChecked(True)) >= 1
    assert window.bivariate.canvas.figure.axes[0].get_yscale() == "log"
    assert _redraws(draws, lambda: ctrl.legend_grp.visible.setChecked(False)) >= 1
    assert _redraws(draws, lambda: ctrl.regression_grp.show.setChecked(True)) >= 1
    ctrl.axis_grp.x_label_edit.setText("silica")
    assert _redraws(draws, ctrl.axis_grp.x_label_edit.editingFinished.emit) >= 1
    assert window.bivariate.canvas.figure.axes[0].get_xlabel() == "silica"


def test_a_burst_of_changes_is_one_redraw(window):
    window._open_tectonic("pearce2008_thyb_nbyb", "volcanic", "Mafic")
    spin = window.tectonic.axis_grp.font_size
    count = _canvas_draws(window.tectonic)

    def spin_up():
        for _ in range(5):
            spin.setValue(spin.value() + 1)
    assert _redraws(count, spin_up) == 1


def test_isotope_and_map_options_redraw_at_once(window):
    window._open_isotopes("sr_nd")
    iso = _canvas_draws(window.isotopes)
    chk = window.isotopes.mantle_array_chk
    assert _redraws(iso, lambda: chk.setChecked(not chk.isChecked())) >= 1
    window._open_map()
    from PySide6.QtWidgets import QCheckBox
    scale = next(c for c in window.map.findChildren(QCheckBox)
                 if c.text() == "Show scale bar")
    mp = _canvas_draws(window.map)
    assert _redraws(mp, lambda: scale.setChecked(not scale.isChecked())) >= 1


def test_controls_with_their_own_handler_are_not_wired_twice(window):
    """The diagram picker already redraws: make_live must not add a
    second, delayed redraw on top."""
    window._open_classification_family("volcanic")
    combo = window.classification.diagram_combo
    assert not getattr(combo, "_live", False)
    count = _canvas_draws(window.classification)
    assert _redraws(count, lambda: combo.setCurrentIndex(1)) == 1


def test_a_control_can_be_kept_off_the_live_list(qapp):
    from PySide6.QtWidgets import QCheckBox, QWidget

    from birds.views.widgets import make_live
    box = QWidget()
    live, exempt = QCheckBox(box), QCheckBox(box)
    exempt.setProperty("liveExempt", True)
    assert make_live(box, lambda: None) == 1
    assert getattr(live, "_live", False) and not getattr(exempt, "_live", False)


# ---------------------------------------------------------------------------
# Bivariate opens on a Harker plot
# ---------------------------------------------------------------------------

def test_bivariate_opens_on_silica_against_magnesia(window):
    ctrl = window.bivariate._individual
    assert (ctrl.x_combo.currentText(), ctrl.y_combo.currentText()) == (
        "SiO2", "MgO")


def test_empty_columns_are_not_offered_and_context_comes_last(window):
    cols = window.bivariate._numeric_columns()
    assert "Sample_Label" not in cols                    # all blank
    assert cols.index("SiO2") < cols.index("No.")
    assert cols[-3:] == ["No.", "Latitude", "Longitude"]


def test_the_default_falls_back_without_majors():
    from birds.views.bivariate import _default_axes
    assert _default_axes(["La", "Yb"]) == ("La", "Yb")
    assert _default_axes(["SiO2_adj", "MgO_adj"]) == ("SiO2_adj", "MgO_adj")
    assert _default_axes([]) == ("", "")


# ---------------------------------------------------------------------------
# Statistics shows what it means
# ---------------------------------------------------------------------------

def test_statistics_cells_read_as_numbers(qapp):
    from birds.views.statistics import display_value
    assert display_value(57.482333333333344) == "57.4823"
    assert display_value(120.0) == "120"
    assert display_value(0.0114999999) == "0.0115"
    assert display_value(np.nan) == "" and display_value(None) == ""
    assert display_value("Group 1") == "Group 1"


def test_the_ampersand_of_a_tab_is_shown(window):
    window._open_statistics()
    tabs = window.statistics.tabs
    titles = [tabs.tabText(i) for i in range(tabs.count())]
    anomalies = next(t for t in titles if t.startswith("Anomalies"))
    assert "&&" in anomalies                  # Qt shows it as a single &


def test_empty_columns_leave_the_descriptive_table(window):
    window._open_statistics()
    rows = list(window.statistics.descriptive_frame.index)
    assert "Sample_Label" not in rows and "SiO2" in rows


# ---------------------------------------------------------------------------
# Restored settings survive being saved again
# ---------------------------------------------------------------------------

def test_a_restored_correlation_subset_survives_an_early_save(window):
    stats = window.statistics
    stats.restore({"correlation_subset": "A"})
    assert stats.serialize()["correlation_subset"] == "A"
    window._open_statistics()
    assert stats.corr_group_combo.currentData() == "A"


def test_a_restored_variogram_group_survives_an_early_save(window):
    state = window.map.serialize()
    state["param_group"] = "B"
    window.map.restore(state)
    assert window.map.serialize()["param_group"] == "B"


# ---------------------------------------------------------------------------
# The multi-panel legend, inside the figure
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", ["verma_agrawal_2011", "frost"])
def test_the_shared_legend_sits_inside_the_figure(full_df, plot_style, key):
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    from birds.diagrams.registry import get_diagram
    from birds.diagrams.templates.base import PlotOptions
    fig = Figure(figsize=(12, 8))
    FigureCanvasAgg(fig)
    get_diagram(key).plot(fig, full_df, plot_style, PlotOptions())
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    legends = list(fig.legends) + [ax.get_legend() for ax in fig.axes
                                   if ax.get_legend() is not None]
    assert legends, key
    box = fig.bbox
    for legend in legends:
        extent = legend.get_window_extent(renderer)
        assert extent.x0 >= box.x0 - 1 and extent.y0 >= box.y0 - 1
        assert extent.x1 <= box.x1 + 1 and extent.y1 <= box.y1 + 1


# ---------------------------------------------------------------------------
# Every isotope diagram is in the menu
# ---------------------------------------------------------------------------

def test_the_isotopes_menu_lists_every_diagram(window):
    from PySide6.QtWidgets import QMenu
    menu = next(m for m in window.findChildren(QMenu)
                if m.title().replace("&", "") == "Isotopes")
    entries = [a.text() for a in menu.actions() if not a.isSeparator()]
    assert len(entries) == window.isotopes.diagram_combo.count()
    sio2 = next(a for a in menu.actions() if "SiO₂" in a.text())
    sio2.trigger()
    assert window.isotopes.diagram_combo.currentData() == "vs_sio2"


def test_frame_survives(window):
    """Nothing above writes into the data."""
    assert isinstance(window.data.df, pd.DataFrame)


# ---------------------------------------------------------------------------
# The map recognises UTM numbers in degree columns
# ---------------------------------------------------------------------------

def test_utm_numbers_in_degree_columns_are_named(window):
    """Several of the user's sessions keep easting and northing in
    Latitude / Longitude; the map only said nothing could be parsed."""
    window.data.df["Latitude"] = np.linspace(639_000, 681_000, len(window.data.df))
    window.data.df["Longitude"] = np.linspace(2_088_000, 2_176_000,
                                              len(window.data.df))
    window._open_map()
    _samples, message = window.map._collect()
    assert "UTM" in message and "not degrees" in message


def test_real_degrees_get_no_utm_hint(window):
    window._open_map()
    samples, message = window.map._collect()
    assert message is None and samples
    assert window.map._utm_hint() == ""


# ---------------------------------------------------------------------------
# Controls made later still mark the session modified
# ---------------------------------------------------------------------------

def test_the_spiders_second_mode_marks_the_session_modified(window):
    """Its panel is built the first time it opens -- after the window
    wired its tracking -- so its changes went unrecorded and closing did
    not offer to save them."""
    for mode in ("ree", "multielement"):
        window._open_spider(mode)
        window.setWindowModified(False)
        chk = window.spider._controls[mode].connect_chk
        chk.setChecked(not chk.isChecked())
        assert window.isWindowModified(), mode


def test_tracking_is_wired_once_however_often_it_runs(window):
    from PySide6.QtCore import SIGNAL
    chk = window.tectonic.axis_grp.log_x
    before = chk.receivers(SIGNAL("toggled(bool)"))
    for _ in range(3):
        window._wire_dirty_signals()
    assert chk.receivers(SIGNAL("toggled(bool)")) == before
