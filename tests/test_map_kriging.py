"""The Map view's spatial analysis, through the widget.

The arithmetic is tested in test_geostats.py and the drawing in
test_spatial_plots.py; this is the wiring: the five displays, the
controls and what they reach, the variogram set by hand, the export
for a GIS and the session that brings it all back.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import QuadMesh

from birds.coords import km_per_degree_lat, km_per_degree_lon
from birds.geostats import POOLED_LABEL

DISPLAYS = ["samples", "estimate", "uncertainty", "variogram", "cv"]


def _unit(n, seed, lon0, level, name, lat0=19.2, side_km=30.0):
    rng = np.random.default_rng(seed)
    xk = rng.uniform(0, side_km, n)
    yk = rng.uniform(0, side_km, n)
    return pd.DataFrame({
        "Sample": [f"{name}-{i}" for i in range(n)],
        "Unit": name,
        "Latitude": lat0 + yk / km_per_degree_lat(lat0),
        "Longitude": lon0 + xk / km_per_degree_lon(lat0),
        "Cu": np.exp(level + xk / 20.0 + 0.3 * np.sin(yk / 6.0)),
        "SiO2": 50.0 + 0.3 * xk + rng.normal(0, 0.5, n),
        "Rock": "granite",
    })


def _make_view(df):
    from birds.data_manager import DataManager
    from birds.plot_style import GroupStyle, PlotStyle
    from birds.views.map_view import MapView

    data = DataManager()
    data.df = df
    style = PlotStyle(group_columns=["Unit"], groups=[
        GroupStyle(name="Pluton", color="#1f77b4", marker="o"),
        GroupStyle(name="Host", color="#d62728", marker="s"),
    ])
    v = MapView(data, style)
    v.show_map()
    return v


@pytest.fixture
def frame():
    return pd.concat([_unit(40, 1, -99.0, 1.0, "Pluton"),
                      _unit(35, 2, -98.5, 3.0, "Host")], ignore_index=True)


@pytest.fixture
def view(qapp, frame):
    return _make_view(frame)


def _show(view, display):
    """Switch to *display* -- or redraw it, if it is already showing."""
    i = DISPLAYS.index(display)
    if view.display_tabs.currentIndex() == i:
        view.update_plot()
    else:
        view.display_tabs.setCurrentIndex(i)
    return view.canvas.figure.axes[0]


def _meshes(ax):
    return [c for c in ax.collections if isinstance(c, QuadMesh)]


# ---------------------------------------------------------------------------
# Choosing what to krige
# ---------------------------------------------------------------------------

def test_the_tabs_are_the_five_displays(view):
    tabs = [view.display_tabs.tabText(i)
            for i in range(view.display_tabs.count())]
    assert tabs == ["Samples", "Kriged estimate", "Uncertainty",
                    "Variogram", "Cross-validation"]
    assert view._display() == "samples"


def test_only_numeric_columns_that_are_not_coordinates_are_offered(view):
    offered = [view.variable_combo.itemText(i)
               for i in range(view.variable_combo.count())]
    assert offered == ["Cu", "SiO2"]


def test_the_defaults_are_the_ones_chosen(view):
    assert view._transform() == "log"
    assert view._pooled() is False
    assert view._model_kind() == "spherical"
    assert view.clip_chk.isChecked()
    assert view.cells_spin.value() == 100


# ---------------------------------------------------------------------------
# The displays
# ---------------------------------------------------------------------------

def test_the_estimate_is_one_surface_per_group(view):
    ax = _show(view, "estimate")
    assert len(_meshes(ax)) == 2
    assert [r.label for r in view._results] == ["Pluton", "Host"]
    assert view.title_label.text() == "Kriged Cu"
    assert len(ax.child_axes) == 1                       # the colorbar


def test_pooled_the_estimate_is_one_surface(view):
    view.pooling_combo.setCurrentIndex(1)
    ax = _show(view, "estimate")
    assert len(_meshes(ax)) == 1
    assert [r.label for r in view._results] == [POOLED_LABEL]


def test_the_surface_is_blank_outside_the_hulls_unless_asked(view):
    ax = _show(view, "estimate")
    assert all(np.ma.getmaskarray(m.get_array()).any() for m in _meshes(ax))
    view.clip_chk.setChecked(False)
    view.update_plot()
    ax = view.canvas.figure.axes[0]
    assert not any(np.ma.getmaskarray(m.get_array()).any()
                   for m in _meshes(ax))


def test_the_grid_follows_the_cells_asked_for(view):
    view.cells_spin.setValue(40)
    ax = _show(view, "uncertainty")
    rows, cols = _meshes(ax)[0].get_array().shape
    assert max(rows, cols) == 40


def test_the_surface_fills_the_map_frame(view):
    ax = _show(view, "estimate")
    (x0, y0), (x1, y1) = _meshes(ax)[0].get_datalim(
        ax.transData).get_points()
    assert (x0, y0) == pytest.approx((ax.get_xlim()[0], ax.get_ylim()[0]))
    assert x1 >= ax.get_xlim()[1] - 1e-9 and y1 >= ax.get_ylim()[1] - 1e-9


def test_the_variogram_and_cross_validation_are_graphs(view):
    ax = _show(view, "variogram")
    assert ax.get_xlabel() == "Distance (km)"
    assert ax.get_ylabel() == "Semivariance of ln(Cu)"
    ax = _show(view, "cv")
    assert ax.get_xscale() == "log"
    assert ax.get_xlabel() == "Observed Cu"


@pytest.mark.parametrize("display", DISPLAYS)
def test_maps_carry_the_map_furniture_and_graphs_do_not(view, display):
    ax = _show(view, display)
    is_map = display in ("samples", "estimate", "uncertainty")
    assert (ax.get_xlabel() == "Longitude") == is_map
    assert bool(view._scale_artists) == is_map
    assert view.annotation_ctl.enabled == is_map
    assert view.summary.isVisibleTo(view) == (display != "samples")


def test_annotations_and_selection_stay_off_the_graphs(view):
    ax = _show(view, "samples")
    x, y = np.mean(ax.get_xlim()), np.mean(ax.get_ylim())
    assert view._resolve_sample(x, y) is not None
    _show(view, "variogram")
    assert view._resolve_sample(x, y) is None
    assert view._selection_points({"Pluton-0"}) == []


def test_samples_can_be_coloured_by_the_variable(view):
    view.colour_by_value_chk.setChecked(True)
    ax = _show(view, "samples")
    coloured = [c for c in ax.collections if c.get_array() is not None]
    assert coloured and all(c.cmap.name == "viridis" for c in coloured)
    assert len(ax.child_axes) == 1                       # its colorbar
    labels = [t.get_text() for t in ax.get_legend().get_texts()]
    assert labels == ["Pluton", "Host"]


def test_the_summary_reports_each_group(view):
    _show(view, "estimate")
    text = view.summary.toPlainText()
    assert "Pluton" in text and "Host" in text and "Skill" in text


def test_a_group_too_small_to_krige_is_named_not_fatal(qapp, frame):
    dyke = _unit(3, 9, -98.8, 2.0, "Dyke")
    v = _make_view(pd.concat([frame, dyke], ignore_index=True))
    ax = _show(v, "estimate")
    assert len(_meshes(ax)) == 2
    assert "Dyke" in v.summary.toPlainText()
    assert "not kriged" in v.summary.toPlainText()


def test_a_dataset_with_nothing_to_krige_says_so(qapp, frame):
    v = _make_view(frame[["Sample", "Unit", "Latitude", "Longitude"]])
    assert v.variable_combo.count() == 0
    ax = _show(v, "estimate")
    assert "Choose a variable" in ax.texts[0].get_text()


def test_hidden_groups_are_left_out(view):
    view.plot_style.groups[1].visible = False
    _show(view, "estimate")
    assert [r.label for r in view._results] == ["Pluton"]


def test_redrawing_does_not_pile_up_callbacks(view):
    for display in ("samples", "estimate", "samples", "uncertainty"):
        ax = _show(view, display)
    view.update_plot()
    ax = view.canvas.figure.axes[0]
    assert len(ax.callbacks.callbacks.get("xlim_changed", {})) == 1
    assert len(view._scale_artists) == 2


# ---------------------------------------------------------------------------
# The frame when auto-fit is off
# ---------------------------------------------------------------------------

def test_with_auto_fit_off_a_zoom_survives_an_update(view):
    view.auto_extent_chk.setChecked(False)
    ax = _show(view, "samples")
    ax.set_xlim(-98.9, -98.6)
    ax.set_ylim(19.25, 19.4)
    ax = _show(view, "estimate")
    assert ax.get_xlim() == pytest.approx((-98.9, -98.6))
    assert ax.get_ylim() == pytest.approx((19.25, 19.4))


def test_with_auto_fit_on_the_frame_is_rebuilt(view):
    ax = _show(view, "samples")
    full = ax.get_xlim()
    ax.set_xlim(-98.9, -98.6)
    view.update_plot()
    assert view.canvas.figure.axes[0].get_xlim() == pytest.approx(full)


# ---------------------------------------------------------------------------
# A variogram set by hand
# ---------------------------------------------------------------------------

def _by_hand(view, label="Host"):
    _show(view, "variogram")
    view.param_group_combo.setCurrentText(label)
    view.auto_fit_chk.setChecked(False)


def test_unticking_the_fit_starts_from_the_fitted_values(view):
    _show(view, "variogram")
    fitted = view._results[1].analysis.model
    _by_hand(view)
    assert view._overrides["Host"] == (fitted.nugget, fitted.sill,
                                       fitted.range_km)
    assert view.range_spin.isEnabled()


def test_a_range_typed_in_is_used_for_that_group_only(view):
    _by_hand(view)
    view.range_spin.setValue(7.5)
    view.range_spin.editingFinished.emit()
    host, pluton = view._results[1], view._results[0]
    assert host.analysis.model.range_km == 7.5
    assert host.analysis.fit.message == "set by hand"
    assert pluton.analysis.fit.message != "set by hand"
    assert "(by hand)" in view.summary.toPlainText()


def test_an_untouched_box_keeps_the_full_precision_value(view):
    _by_hand(view)
    sill = view._overrides["Host"][1]
    view.range_spin.setValue(7.5)
    view.range_spin.editingFinished.emit()
    assert view._overrides["Host"][1] == sill          # not rounded


def test_ticking_the_fit_again_goes_back_to_fitting(view):
    _by_hand(view)
    view.range_spin.setValue(7.5)
    view.range_spin.editingFinished.emit()
    view.auto_fit_chk.setChecked(True)
    assert "Host" not in view._overrides
    assert view._results[1].analysis.fit.message != "set by hand"


def test_the_sill_cannot_go_below_the_nugget_or_to_zero(view):
    _by_hand(view)
    view.nugget_spin.setValue(0.0)
    view.nugget_spin.editingFinished.emit()
    view.sill_spin.setValue(0.0)
    assert view.sill_spin.value() > 0
    view.nugget_spin.setValue(view.sill_spin.value() + 1.0)
    view.nugget_spin.editingFinished.emit()
    assert view.sill_spin.value() >= view.nugget_spin.value()


def test_parameters_set_for_one_variable_are_dropped_for_another(view):
    _by_hand(view)
    view.variable_combo.setCurrentText("SiO2")
    view.update_plot()
    assert view._overrides == {}
    assert all(r.analysis.fit.message != "set by hand"
               for r in view._results)


# ---------------------------------------------------------------------------
# Export for a GIS
# ---------------------------------------------------------------------------

def test_the_grid_is_exported_for_a_gis(view, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    target = tmp_path / "cu_kriged.asc"
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *a, **k: (str(target), ""))
    shown = []
    monkeypatch.setattr(QMessageBox, "information",
                        lambda _parent, _title, text: shown.append(text))
    view.export_grid()
    for name in ("cu_kriged_Pluton.asc", "cu_kriged_Pluton_sd.asc",
                 "cu_kriged_Host.asc", "cu_kriged_Host.prj", "cu_kriged.txt"):
        assert (tmp_path / name).exists(), name
    assert "cu_kriged_Host_sd.asc" in shown[0]


def test_a_cancelled_export_writes_nothing(view, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *a, **k: ("", ""))
    monkeypatch.chdir(tmp_path)
    view.export_grid()
    assert not list(tmp_path.iterdir())


def test_with_nothing_kriged_the_export_explains(qapp, frame, monkeypatch):
    from PySide6.QtWidgets import QFileDialog, QMessageBox

    v = _make_view(frame[["Sample", "Unit", "Latitude", "Longitude"]])
    asked = []
    monkeypatch.setattr(QFileDialog, "getSaveFileName",
                        lambda *a, **k: asked.append(1) or ("", ""))
    shown = []
    monkeypatch.setattr(QMessageBox, "information",
                        lambda _parent, _title, text: shown.append(text))
    v.export_grid()
    assert not asked
    assert "Nothing has been kriged" in shown[0]


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------

def test_a_session_brings_the_analysis_back(qapp, frame):
    v = _make_view(frame)
    v.variable_combo.setCurrentText("SiO2")
    v.transform_combo.setCurrentIndex(1)
    v.pooling_combo.setCurrentIndex(1)
    v.model_combo.setCurrentIndex(2)
    v.lags_spin.setValue(8)
    v.max_lag_spin.setValue(25.0)
    v.cells_spin.setValue(60)
    v.clip_chk.setChecked(False)
    v.buffer_spin.setValue(1.5)
    v.contours_chk.setChecked(True)
    v.colour_by_value_chk.setChecked(True)
    _show(v, "variogram")
    v.auto_fit_chk.setChecked(False)
    v.range_spin.setValue(12.0)
    v.range_spin.editingFinished.emit()
    state = v.serialize()

    w = _make_view(frame)
    w.restore(state)
    w.update_plot()
    assert w._display() == "variogram"
    assert w._variable() == "SiO2"
    assert w._transform() == "none"
    assert w._pooled() is True
    assert w._model_kind() == "gaussian"
    assert (w.lags_spin.value(), w.max_lag_spin.value()) == (8, 25.0)
    assert w.cells_spin.value() == 60
    assert not w.clip_chk.isChecked()
    assert w.buffer_spin.value() == 1.5
    assert w.contours_chk.isChecked() and w.colour_by_value_chk.isChecked()
    assert w._overrides == v._overrides
    assert w._results[0].analysis.model.range_km == 12.0
    assert w.param_group_combo.currentText() == POOLED_LABEL


def test_restored_columns_survive_opening_the_view(qapp, frame):
    frame = frame.assign(Lat2=frame["Latitude"], Lon2=frame["Longitude"])
    v = _make_view(frame)
    v.restore({"fmt": "decimal", "lat": "Lat2", "lon": "Lon2",
               "variable": "SiO2"})
    v.show_map()                        # what opening the view does
    assert v.lat_combo.currentText() == "Lat2"
    assert v.lon_combo.currentText() == "Lon2"
    assert v._variable() == "SiO2"


def test_a_session_restored_before_the_view_was_ever_opened(qapp, frame):
    """What loading a session does: restore first, open the view later."""
    from birds.data_manager import DataManager
    from birds.plot_style import PlotStyle
    from birds.views.map_view import MapView

    data = DataManager()
    data.df = frame.assign(Lat2=frame["Latitude"])
    v = MapView(data, PlotStyle(group_columns=["Unit"]))
    v.restore({"fmt": "decimal", "lat": "Lat2", "lon": "Longitude",
               "variable": "SiO2", "display": "estimate"})
    v.show_map()
    assert v.lat_combo.currentText() == "Lat2"
    assert v._variable() == "SiO2"
    assert v._display() == "estimate"
    assert len(_meshes(v.canvas.figure.axes[0])) == 2


def test_a_session_from_before_the_kriging_still_opens(qapp, frame):
    v = _make_view(frame)
    v.restore({"fmt": "decimal", "lat": "Latitude", "lon": "Longitude",
               "axes_crs": "lonlat", "annotations": []})
    v.update_plot()
    assert v._display() == "samples"
    assert v._variable() == "Cu"
    assert v._overrides == {}


def test_a_saved_zoom_is_kept_when_auto_fit_is_off(qapp, frame):
    v = _make_view(frame)
    v.auto_extent_chk.setChecked(False)
    ax = _show(v, "samples")
    ax.set_xlim(-98.9, -98.6)
    state = v.serialize()
    w = _make_view(frame)
    w.restore(state)
    w.update_plot()
    assert w.canvas.figure.axes[0].get_xlim() == pytest.approx((-98.9,
                                                                -98.6))
