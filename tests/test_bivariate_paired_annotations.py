"""Annotations, Identify sample included, in Bivariate → Paired.

Paired draws a grid of panels, so a click has to land on the panel it
was made in: the sample identified is the nearest on that panel's X-Y
pair, and the label is drawn there and only there -- and stays with the
pair when the grid is rearranged or the session reopened.
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from birds.data_manager import DataManager
from birds.plot_style import GroupStyle, PlotStyle
from birds.views.widgets import ANN_MODE_NONE, ANN_MODE_SAMPLE

N = 6


@pytest.fixture
def view(qapp):
    from birds.views.bivariate import BivariateView

    data = DataManager()
    data.df = pd.DataFrame({
        "Sample_Name": [f"S{i}" for i in range(N)],
        "SiO2": np.linspace(45, 70, N),
        "MgO": np.linspace(12, 1, N),
        "Al2O3": [14.0, 18.0, 15.0, 16.5, 13.0, 17.0],
        "CaO": [11.0, 9.0, 8.0, 5.0, 3.0, 1.0],
        "Group": ["a", "a", "a", "b", "b", "b"],
    })
    v = BivariateView(data, PlotStyle())
    v.set_mode("paired")
    return v


def _select(v, xs, ys, layout="auto"):
    ctrl = v._paired
    for lst, names in ((ctrl.x_list, xs), (ctrl.y_list, ys)):
        lst.clearSelection()
        for i in range(lst.count()):
            if lst.item(i).text() in names:
                lst.item(i).setSelected(True)
    ctrl.grid_layout_combo.setCurrentIndex(
        ctrl.grid_layout_combo.findData(layout))
    v.update_plot()


def _axes_of(v, pair):
    return next(ax for ax, p in v._paired_axes.items() if p == pair)


def _click(v, ax, x, y, button=1):
    v._on_canvas_click(SimpleNamespace(inaxes=ax, xdata=x, ydata=y,
                                       button=button, key=None))


def _identify(v, pair, sample):
    df = v.data.df
    row = df.index[df["Sample_Name"] == sample][0]
    ax = _axes_of(v, pair)
    v._paired.annotations_grp.btn_sample.click()
    _click(v, ax, df.at[row, pair[0]] * 1.01, df.at[row, pair[1]] * 0.99)


def _labels(ax):
    return [t.get_text() for t in ax.texts]


def test_the_paired_panel_has_the_annotation_tools(view):
    grp = view._paired.annotations_grp
    assert grp.btn_sample.text() == "Identify sample"
    assert view.controls_stack.currentWidget() is view._paired


def test_identify_names_the_sample_on_the_panel_clicked(view):
    _select(view, ["SiO2"], ["MgO", "Al2O3", "CaO"])
    assert len(view._paired_axes) == 3
    _identify(view, ("SiO2", "Al2O3"), "S3")
    [(panel, ann)] = view._paired_annotations
    assert panel == ("SiO2", "Al2O3") and ann.label == "S3"
    df = view.data.df
    assert (ann.px, ann.py) == pytest.approx((df.at[3, "SiO2"],
                                              df.at[3, "Al2O3"]))
    for ax, pair in view._paired_axes.items():
        assert ("S3" in _labels(ax)) == (pair == ("SiO2", "Al2O3"))
    # The tool disarms after one sample, as everywhere else.
    assert not view._paired.annotations_grp.btn_sample.isChecked()
    assert "Al2O3 vs SiO2" in view._paired.annotations_grp.list.item(0).text()


def test_the_nearest_sample_is_found_on_that_panels_pair(view):
    """S1 and S4 swap places between MgO and Al2O3: a click resolved
    against the wrong pair would name the other one."""
    _select(view, ["SiO2"], ["MgO", "Al2O3"])
    ax = _axes_of(view, ("SiO2", "Al2O3"))
    hit = view._resolve_sample_in(ax, 64.9, 13.1)
    assert hit[2] == "S4"
    ax = _axes_of(view, ("SiO2", "MgO"))
    assert view._resolve_sample_in(ax, 50.1, 9.8)[2] == "S1"


def test_in_the_matrix_each_cell_is_its_own_pair(view):
    _select(view, ["SiO2", "MgO"], ["Al2O3", "CaO"], layout="matrix")
    assert set(view._paired_axes.values()) == {
        ("SiO2", "Al2O3"), ("MgO", "Al2O3"), ("SiO2", "CaO"), ("MgO", "CaO")}
    _identify(view, ("MgO", "CaO"), "S2")
    assert view._paired_annotations[0][0] == ("MgO", "CaO")
    assert "S2" in _labels(_axes_of(view, ("MgO", "CaO")))
    assert "S2" not in _labels(_axes_of(view, ("SiO2", "CaO")))


def test_the_label_follows_its_pair_when_the_grid_changes(view):
    _select(view, ["SiO2"], ["MgO", "Al2O3", "CaO"])
    _identify(view, ("SiO2", "CaO"), "S5")
    _select(view, ["SiO2"], ["CaO", "Al2O3"], layout="1")
    assert "S5" in _labels(_axes_of(view, ("SiO2", "CaO")))
    assert "S5" not in _labels(_axes_of(view, ("SiO2", "Al2O3")))
    # A pair no longer shown keeps its annotations for when it returns.
    _select(view, ["SiO2"], ["MgO"])
    assert len(view._paired_annotations) == 1
    assert all("S5" not in _labels(ax) for ax in view._paired_axes)


def test_right_click_deletes_on_the_panel_clicked_only(view):
    _select(view, ["SiO2"], ["MgO", "Al2O3"])
    _identify(view, ("SiO2", "MgO"), "S2")
    _identify(view, ("SiO2", "Al2O3"), "S2")
    df = view.data.df
    _click(view, _axes_of(view, ("SiO2", "Al2O3")),
           df.at[2, "SiO2"], df.at[2, "Al2O3"], button=3)
    assert [p for p, _a in view._paired_annotations] == [("SiO2", "MgO")]


def test_a_line_keeps_both_ends_on_one_panel(view):
    _select(view, ["SiO2"], ["MgO", "Al2O3"])
    view._paired.annotations_grp.btn_line.click()
    _click(view, _axes_of(view, ("SiO2", "MgO")), 50, 10)
    # The second click lands on another panel: the line starts there.
    _click(view, _axes_of(view, ("SiO2", "Al2O3")), 50, 14)
    assert view._paired_annotations == []
    _click(view, _axes_of(view, ("SiO2", "Al2O3")), 60, 17)
    [(panel, line)] = view._paired_annotations
    assert panel == ("SiO2", "Al2O3")
    assert (line.x1, line.y1, line.x2, line.y2) == (50, 14, 60, 17)


def test_a_switched_off_group_cannot_be_identified(view):
    view.plot_style.group_columns = ["Group"]
    view.plot_style.groups = [GroupStyle(name="a"),
                              GroupStyle(name="b", visible=False)]
    _select(view, ["SiO2"], ["MgO"])
    ax = _axes_of(view, ("SiO2", "MgO"))
    df = view.data.df
    # Right on S4, which is hidden: the nearest drawn sample is S2.
    assert view._resolve_sample_in(ax, df.at[4, "SiO2"],
                                   df.at[4, "MgO"])[2] == "S2"


def test_individual_annotations_stay_apart(view):
    _select(view, ["SiO2"], ["MgO"])
    _identify(view, ("SiO2", "MgO"), "S1")
    view.set_mode("individual")
    assert view._annotations == []
    assert view._individual.annotations_grp.list.count() == 0
    # A tool armed in Paired is not left armed in Individual.
    view.set_mode("paired")
    view._paired.annotations_grp.btn_sample.click()
    assert view._ann_mode == ANN_MODE_SAMPLE
    view.set_mode("individual")
    assert view._ann_mode == ANN_MODE_NONE
    assert not view._paired.annotations_grp.btn_sample.isChecked()


def test_paired_annotations_survive_a_session(view, qapp):
    from birds.views.bivariate import BivariateView

    _select(view, ["SiO2"], ["MgO", "Al2O3"])
    _identify(view, ("SiO2", "Al2O3"), "S3")
    state = view.serialize()
    other = BivariateView(view.data, PlotStyle())
    other.restore(state)
    [(panel, ann)] = other._paired_annotations
    assert panel == ("SiO2", "Al2O3") and ann.label == "S3"
    assert other._paired.annotations_grp.list.count() == 1
    assert "S3" in _labels(_axes_of(other, ("SiO2", "Al2O3")))


def test_a_selection_is_ringed_on_every_panel(view):
    _select(view, ["SiO2"], ["MgO", "Al2O3"])
    groups = view._selection_points({"S3"})
    assert len(groups) == 2
    df = view.data.df
    for ax, pts in groups:
        x_col, y_col = view._paired_axes[ax]
        assert pts == [(df.at[3, x_col], df.at[3, y_col])]


def test_brushing_hands_the_clicked_panel_to_the_view(view):
    """Alt-click on a Paired panel selects that panel's nearest sample."""
    from birds.selection import SelectionBus
    from birds.views.brushing import wire_brushing

    bus = SelectionBus()
    wire_brushing(view, bus)
    _select(view, ["SiO2"], ["MgO", "Al2O3"])
    ax = _axes_of(view, ("SiO2", "Al2O3"))
    df = view.data.df
    event = SimpleNamespace(inaxes=ax, xdata=df.at[4, "SiO2"],
                            ydata=df.at[4, "Al2O3"], button=1, key="alt",
                            name="button_press_event",
                            canvas=view.canvas.canvas)
    view.canvas.canvas.callbacks.process("button_press_event", event)
    assert set(bus.names) == {"S4"}
