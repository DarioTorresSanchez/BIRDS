"""Adjusted majors beside the analysed ones, one switch to choose, and Mg#.

Pre-processing used to overwrite the analysed oxides with the adjusted
ones, after which every diagram plotted adjusted values with nothing to
say so and the analysed values were gone.  Now the adjusted values are
added as ``SiO2_adj``, … ; a "Major elements" switch, shown in every view
that reads majors and shared by all of them, chooses which the diagrams
use; and the bivariate view lists the ``*_adj`` columns and three Mg#
variants as axes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.data_manager import DataManager
from birds.derived import MG_NUMBER, MG_NUMBER_ADJ, MG_NUMBER_FEOT, available
from birds.expression import evaluate, evaluate_scalar
from birds.preprocess import (
    MAJOR_OXIDES,
    attach_adjusted,
    describe_adjustment,
    has_adjusted,
    with_adjusted_majors,
)

#: Wet analyses: LOI 1-5 wt.%, total iron as Fe2O3T, P2O5 missing in one.
RAW = pd.DataFrame({
    "Sample_Name": ["A", "B", "C"],
    "SiO2": [48.0, 55.0, 68.0],
    "TiO2": [1.8, 1.1, 0.4],
    "Al2O3": [15.5, 16.8, 14.6],
    "Fe2O3T": [11.0, 8.0, 3.2],
    "MnO": [0.17, 0.14, 0.06],
    "MgO": [8.0, 4.2, 0.8],
    "CaO": [10.5, 7.4, 2.1],
    "Na2O": [2.6, 3.6, 4.1],
    "K2O": [0.4, 1.6, 3.9],
    "P2O5": [0.22, 0.25, np.nan],
    "LOI": [2.0, 3.5, 1.0],
    "La": [8.0, 20.0, 35.0],
    "Nb": [3.0, 6.0, 12.0],
    "Yb": [2.5, 2.2, 1.9],
})
SETTINGS = {"mode": "anhydrous", "iron": "middlemost", "ratio": 0.15}


@pytest.fixture
def adjusted():
    return attach_adjusted(RAW)


# ---------------------------------------------------------------------------
# The twins
# ---------------------------------------------------------------------------

def test_the_analysed_values_are_kept(adjusted):
    pd.testing.assert_frame_equal(adjusted[RAW.columns], RAW)


def test_each_sample_adds_up_to_100(adjusted):
    oxides = [c for c in adjusted.columns
              if c.endswith("_adj") and c != "FeOt_adj"]
    assert adjusted[oxides].sum(axis=1).to_numpy() == pytest.approx(100.0)


def test_an_oxide_not_analysed_stays_missing(adjusted):
    """Counted as zero in the sum, but not reported as 0.000 wt.%."""
    assert np.isnan(adjusted.loc[2, "P2O5_adj"])
    assert adjusted.loc[0, "P2O5_adj"] > 0


@pytest.mark.parametrize("iron", ["middlemost", "none"])
def test_total_iron_agrees_with_the_split_after_every_rescale(iron):
    """FeOt is not a rescaled oxide, so pre_process left it behind: by
    ~0.15 % after the partition's second rescale, and by the whole LOI
    when the iron was not partitioned."""
    from birds.preprocess import pre_process
    out = pre_process(RAW, "anhydrous", iron)
    assert (out["FeO"] + 0.89981 * out["Fe2O3"]).to_numpy() == \
        pytest.approx(out["FeOt"], rel=1e-6)


def test_iron_is_split_from_whatever_total_was_reported(adjusted):
    for column in ("FeO_adj", "Fe2O3_adj", "FeOt_adj"):
        assert adjusted[column].notna().all(), column
    feot = adjusted["FeO_adj"] + 0.89981 * adjusted["Fe2O3_adj"]
    assert feot.to_numpy() == pytest.approx(adjusted["FeOt_adj"], rel=1e-5)


def test_a_sample_with_no_iron_has_no_adjusted_iron():
    raw = RAW.copy()
    raw.loc[1, "Fe2O3T"] = np.nan
    out = attach_adjusted(raw)
    assert out[["FeO_adj", "Fe2O3_adj", "FeOt_adj"]].loc[1].isna().all()
    assert out[["FeO_adj", "Fe2O3_adj"]].loc[0].notna().all()


def test_running_it_again_starts_from_the_analysed_values(adjusted):
    again = attach_adjusted(adjusted, "simple", "none")
    once = attach_adjusted(RAW, "simple", "none")
    pd.testing.assert_frame_equal(again, once)


def test_the_diagrams_read_the_twins_under_the_plain_names(adjusted):
    view = with_adjusted_majors(adjusted)
    for oxide in ("SiO2", "MgO", "K2O"):
        assert view[oxide].equals(adjusted[f"{oxide}_adj"])
    assert view["FeO"].equals(adjusted["FeO_adj"])
    # Total iron under the dataset's own alias agrees with the twins, so
    # a diagram reading Fe2O3T does not get the analysed value.
    assert (view["Fe2O3T"] * 0.89981).to_numpy() == pytest.approx(
        adjusted["FeOt_adj"], rel=1e-4)
    # And the original frame is untouched.
    assert adjusted["SiO2"].equals(RAW["SiO2"])


def test_without_twins_nothing_is_swapped():
    assert with_adjusted_majors(RAW) is RAW
    assert not has_adjusted(RAW)


def test_the_settings_read_as_words():
    assert describe_adjustment(SETTINGS) == (
        "anhydrous (volatile-free) to 100 wt %, Fe₂O₃/FeO after "
        "Middlemost (1989)")
    assert "fixed at 0.2" in describe_adjustment(
        {"mode": "simple", "iron": "fixed", "ratio": 0.2})
    assert describe_adjustment(None) == "settings not recorded"


def test_the_data_manager_hands_out_what_the_switch_says(adjusted):
    data = DataManager()
    data.df = adjusted
    assert data.majors_df()["SiO2"].equals(adjusted["SiO2_adj"])
    data.use_adjusted = False
    assert data.majors_df() is adjusted
    data.use_adjusted = True
    data.df = RAW
    assert data.majors_df() is RAW
    assert not data.adjusted_in_use()


# ---------------------------------------------------------------------------
# Mg#
# ---------------------------------------------------------------------------

def test_mg_number_of_pyrolite_is_the_published_one():
    """McDonough & Sun (1995), Table 4: 100Mg/(Mg+Fe) = 89.3."""
    pyrolite = pd.DataFrame({"MgO": [37.8], "FeOt": [8.05]})
    assert evaluate(pyrolite, MG_NUMBER_FEOT).iloc[0] == pytest.approx(
        89.3, abs=0.05)


def test_mg_number_with_all_iron_ferrous_ignores_the_adjustment(adjusted):
    assert evaluate(adjusted, MG_NUMBER_FEOT).to_numpy() == pytest.approx(
        evaluate(with_adjusted_majors(adjusted), MG_NUMBER_FEOT), abs=0.01)


def test_the_strict_mg_number_needs_a_measured_iron_split(adjusted):
    assert MG_NUMBER not in available(RAW)
    split = RAW.drop(columns="Fe2O3T").assign(FeO=[8.0, 6.0, 2.0],
                                              Fe2O3=[2.0, 2.0, 1.0])
    assert MG_NUMBER in available(split)
    # Ferric iron removed from the denominator raises it.
    assert (evaluate(split, MG_NUMBER)
            > evaluate(split, MG_NUMBER_FEOT)).all()


def test_the_adjusted_mg_number_takes_ferrous_iron_from_the_partition(
        adjusted):
    assert MG_NUMBER_ADJ in available(adjusted)
    assert MG_NUMBER_ADJ not in available(RAW)
    mgo = adjusted["MgO_adj"] / 40.304
    feo = adjusted["FeO_adj"] / 71.844
    expected = (100 * mgo / (mgo + feo)).round(2)
    assert evaluate(adjusted, MG_NUMBER_ADJ).to_numpy() == pytest.approx(
        expected)
    assert (evaluate(adjusted, MG_NUMBER_ADJ)
            > evaluate(adjusted, MG_NUMBER_FEOT)).all()


def test_the_axis_and_the_statistics_table_agree(adjusted):
    from birds.stats_engine import compute_mg_number
    table = compute_mg_number(adjusted)
    assert evaluate(adjusted, MG_NUMBER_FEOT).equals(
        table["Mg#_FeOt"].rename(MG_NUMBER_FEOT))


def test_mg_number_works_inside_an_expression(adjusted):
    assert evaluate(adjusted, "Mg#_FeOt/100").to_numpy() == pytest.approx(
        evaluate(adjusted, MG_NUMBER_FEOT) / 100)
    assert evaluate(adjusted, "log(Mg#_adj)").to_numpy() == pytest.approx(
        np.log(evaluate(adjusted, MG_NUMBER_ADJ)))


def test_a_column_the_user_called_mg_number_wins():
    own = RAW.assign(**{"Mg#": [1.0, 2.0, 3.0]})
    assert evaluate(own, "Mg#").tolist() == [1.0, 2.0, 3.0]
    assert MG_NUMBER not in available(own)


def test_reservoirs_answer_on_derived_and_adjusted_axes():
    from birds.reservoirs import RESERVOIRS
    pm = RESERVOIRS["Primitive mantle (McDonough & Sun 1995)"]
    assert evaluate_scalar(pm, MG_NUMBER_FEOT) == pytest.approx(89.3,
                                                                abs=0.05)
    # Reference compositions are published volatile-free: on an axis of
    # adjusted majors they read their plain values.
    assert evaluate_scalar(pm, "SiO2_adj") == pm["SiO2"]
    assert evaluate_scalar(pm, "SiO2_adj/MgO_adj") == pytest.approx(
        pm["SiO2"] / pm["MgO"])


# ---------------------------------------------------------------------------
# Through the program
# ---------------------------------------------------------------------------

@pytest.fixture
def window(qapp):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    w.data.df = RAW.copy()
    w.on_dataset_replaced()
    return w


def _show(window, view):
    """Bring *view* on screen, as its menu entry does: a page behind
    another holds its redraws until it is shown."""
    window.stack.setCurrentWidget(view)
    return view


def _preprocess(window, mode="anhydrous", iron="middlemost"):
    from birds.dialogs.preprocess_dialog import PreprocessDialog
    dialog = PreprocessDialog(window.data, window)
    dialog.adjust_combo.setCurrentIndex(dialog.adjust_combo.findData(mode))
    dialog.iron_combo.setCurrentIndex(dialog.iron_combo.findData(iron))
    dialog._apply()
    window.refresh_variable_lists()


def test_applying_the_dialog_adds_twins_and_turns_the_switch_on(window):
    _preprocess(window, "anhydrous", "le_maitre")
    df = window.data.df
    assert df["SiO2"].equals(RAW["SiO2"])
    assert {f"{c}_adj" for c in ("SiO2", "TiO2", "MgO", "FeO")} <= set(df)
    assert window.data.adjust_settings == {
        "mode": "anhydrous", "iron": "le_maitre", "ratio": 0.15}
    assert window.data.adjusted_in_use()


def test_the_classification_follows_the_switch(window):
    from birds.diagrams.registry import get_diagram
    _preprocess(window)
    view = _show(window, window.classification)
    view.set_family("volcanic")
    view.update_plot()
    tas = get_diagram(view._diagram_key)

    xs, _ = tas._compute_xy(view._rock_type_filtered_df())
    assert xs.to_numpy() == pytest.approx(window.data.df["SiO2_adj"])
    view.majors_box.check.setChecked(False)
    assert not window.data.use_adjusted
    xs, _ = tas._compute_xy(view._rock_type_filtered_df())
    assert xs.to_numpy() == pytest.approx(RAW["SiO2"])


def test_one_switch_for_every_view(window):
    _preprocess(window)
    _show(window, window.classification).update_plot()  # the shared state
    window.classification.majors_box.check.setChecked(False)
    assert not window.data.use_adjusted
    for view in (window.tectonic, window.classification):
        _show(window, view).update_plot()
        assert not view.majors_box.check.isChecked()
    window.statistics.refresh()
    assert not window.statistics.majors_box.check.isChecked()
    window.tectonic.majors_box.check.setChecked(True)
    _show(window, window.classification).update_plot()
    assert window.classification.majors_box.check.isChecked()


def test_without_twins_the_switch_is_off_and_says_how_to_get_them(window):
    view = window.classification
    view.update_plot()
    assert not view.majors_box.check.isEnabled()
    assert not view.majors_box.check.isChecked()
    assert "Pre-process majors" in view.majors_box.status.text()


def test_the_panel_says_how_the_values_were_adjusted(window):
    _preprocess(window, "anhydrous", "middlemost")
    view = _show(window, window.tectonic)
    view.update_plot()
    assert "Middlemost (1989)" in view.majors_box.status.text()
    assert "anhydrous" in view.majors_box.status.text()


def test_the_spider_reads_potassium_from_the_switch(window):
    from birds.views.spider import _element_series
    _preprocess(window)
    view = window.spider
    view.set_mode("multielement")
    ctrl = view._controls["multielement"]
    assert ctrl.majors_box is not None
    assert view._controls["ree"].majors_box is None    # REE: no majors
    k_adj = _element_series(window.data.majors_df(), "K")
    k_raw = _element_series(window.data.df, "K")
    assert k_adj.to_numpy() == pytest.approx(window.data.df["K2O_adj"]
                                              * 8302, rel=1e-3)
    assert not np.allclose(k_adj, k_raw)


def test_the_statistics_follow_the_switch(window):
    _preprocess(window)
    stats = window.statistics
    stats.refresh()
    assert "Mg#_adj" in stats._ratios.columns
    assert "Mg#_FeOt" in stats._ratios.columns
    stats.majors_box.check.setChecked(False)
    assert "Mg#_adj" not in stats._ratios.columns


def test_the_tectonic_table_and_diagram_read_the_same_majors(window):
    from birds.tectonic_results import compute_results
    _preprocess(window)
    stats = window.statistics
    stats.refresh()
    stats._populate_tectonic_tree()
    for cat_i in range(stats.tect_tree.topLevelItemCount()):
        cat = stats.tect_tree.topLevelItem(cat_i)
        for c_i in range(cat.childCount()):
            child = cat.child(c_i)
            from PySide6.QtCore import Qt
            key = child.data(0, Qt.ItemDataRole.UserRole)
            child.setCheckState(0, Qt.CheckState.Checked
                                if key == "pearce2008.ti_yb"
                                else Qt.CheckState.Unchecked)
    stats._update_tectonic()
    expected = compute_results(window.data.majors_df(),
                               ["pearce2008.ti_yb"])
    pd.testing.assert_frame_equal(stats._tectonic, expected)
    analysed = compute_results(window.data.df, ["pearce2008.ti_yb"])
    assert not stats._tectonic.equals(analysed)


def test_the_norm_is_computed_from_the_selected_majors(window):
    from birds.cipw import compute_cipw
    _preprocess(window)
    norm = window.norm
    norm.attach_chk.setChecked(False)
    norm.compute()
    expected = compute_cipw(window.data.majors_df())
    pd.testing.assert_frame_equal(norm._result, expected)
    assert "Majors    : adjusted" in norm.summary_label.text()
    norm.majors_box.check.setChecked(False)          # recomputes
    pd.testing.assert_frame_equal(norm._result, compute_cipw(RAW))
    assert "Majors    : as analysed" in norm.summary_label.text()


def test_the_bivariate_lists_each_twin_beside_its_oxide(window):
    _preprocess(window)
    combo = window.bivariate._individual.x_combo
    names = [combo.itemText(i) for i in range(combo.count())]
    for oxide in ("SiO2", "TiO2", "MgO", "K2O"):
        assert names.index(f"{oxide}_adj") == names.index(oxide) + 1
    # Mg# right after MgO and its twin; no strict Mg# without an FeO split.
    at = names.index("MgO_adj")
    assert names[at + 1: at + 3] == ["Mg#_FeOt", "Mg#_adj"]
    assert "Mg#" not in names
    # The twins and the derived variables are marked and explained.
    from PySide6.QtCore import Qt
    tip = combo.itemData(names.index("SiO2_adj"), Qt.ItemDataRole.ToolTipRole)
    assert "adjusted to 100 %" in tip
    tip = combo.itemData(names.index("Mg#_FeOt"), Qt.ItemDataRole.ToolTipRole)
    assert "Fe²⁺" in tip


def test_the_bivariate_plots_mg_number(window):
    _preprocess(window)
    view = _show(window, window.bivariate)
    view._individual.x_combo.setCurrentText("SiO2_adj")
    view._individual.y_combo.setCurrentText("Mg#_adj")
    view.update_plot()
    ax = view.canvas.figure.axes[0]
    points = np.vstack([np.asarray(c.get_offsets()) for c in ax.collections
                        if len(c.get_offsets())])
    assert sorted(points[:, 1]) == pytest.approx(
        sorted(evaluate(window.data.df, "Mg#_adj").to_numpy()))


def test_the_switch_and_its_settings_survive_a_session(window, tmp_path):
    from birds.main_window import BirdsMainWindow
    _preprocess(window, "simple", "fixed")
    window.data.use_adjusted = False
    path = tmp_path / "s.birds"
    window._session_path = path
    window.on_save_session()

    reloaded = BirdsMainWindow()
    reloaded._load_session_path(path)
    assert reloaded.data.use_adjusted is False
    assert reloaded.data.adjust_settings["mode"] == "simple"
    assert reloaded.data.adjust_settings["iron"] == "fixed"
    assert "SiO2_adj" in reloaded.data.df.columns


def test_new_data_forget_the_old_adjustment(window):
    _preprocess(window)
    window.data.use_adjusted = False
    window.data.df = RAW.copy()
    window.on_dataset_replaced()
    assert window.data.adjust_settings is None
    assert window.data.use_adjusted is True


def test_every_major_oxide_gets_a_twin():
    full = pd.DataFrame({ox: [1.0] for ox in MAJOR_OXIDES})
    out = attach_adjusted(full)
    assert {f"{ox}_adj" for ox in MAJOR_OXIDES} <= set(out.columns)


def test_the_tectonic_diagram_follows_the_switch(window):
    """Pearce (2008) TiO2/Yb reads TiO2: adjusted, or as analysed."""
    from birds.diagrams.registry import get_diagram
    _preprocess(window)
    view = _show(window, window.tectonic)
    view.show_diagram("pearce2008_tiyb_nbyb", "volcanic", "Mafic")
    view.update_plot()
    diagram = get_diagram("pearce2008_tiyb_nbyb")
    df = window.data.df
    _xs, ys = diagram._compute_xy(view._composition_filtered_df(diagram))
    assert ys.to_numpy() == pytest.approx(
        (df["TiO2_adj"] / df["Yb"]).loc[ys.index])
    view.majors_box.check.setChecked(False)
    _xs, ys = diagram._compute_xy(view._composition_filtered_df(diagram))
    assert ys.to_numpy() == pytest.approx(
        (df["TiO2"] / df["Yb"]).loc[ys.index])


# ---------------------------------------------------------------------------
# Mg# in the statistics tables and the exported report
# ---------------------------------------------------------------------------

def test_with_derived_adds_the_mg_numbers_as_columns(adjusted):
    from birds.derived import with_derived
    out = with_derived(adjusted)
    assert {MG_NUMBER_FEOT, MG_NUMBER_ADJ} <= set(out.columns)
    assert MG_NUMBER not in out.columns          # no measured FeO split
    assert out[MG_NUMBER_FEOT].equals(evaluate(adjusted, MG_NUMBER_FEOT))
    own = RAW.assign(Mg_note=1).assign(**{"Mg#_FeOt": [1.0, 2.0, 3.0]})
    assert with_derived(own)["Mg#_FeOt"].tolist() == [1.0, 2.0, 3.0]


def test_the_statistics_report_mg_number_beside_the_oxides(window):
    _preprocess(window)
    stats = window.statistics
    stats.refresh()
    assert {MG_NUMBER_FEOT, MG_NUMBER_ADJ} <= set(stats._descriptive.index) \
        | set(stats._descriptive.columns)
    # The paper table: majors with their twins, Mg# at the foot of the
    # block, ticked on first open with the analysed majors.
    picked = stats._paper_checked_variables()
    assert MG_NUMBER_FEOT in picked and MG_NUMBER_ADJ in picked
    assert "SiO2" in picked and "SiO2_adj" not in picked
    items = [it.text(0) for it in stats._iter_paper_items()]
    assert items.index("SiO2_adj") == items.index("SiO2") + 1
    majors_end = max(items.index(c) for c in items
                     if c.startswith(("SiO2", "P2O5", "FeOt")))
    assert items.index(MG_NUMBER_FEOT) > majors_end
    assert MG_NUMBER_FEOT in stats._paper.index


def _export(window, tmp_path, monkeypatch, **sections):
    import birds.main_window as mw
    path = tmp_path / "report.xlsx"
    flags = {"raw": True, "adjusted": True, "cipw": True,
             "descriptive": True, "anomalies": True, "ratios": True,
             "tectonic": True}
    flags.update(sections)

    class _Dialog:
        DialogCode = mw.SaveStatisticsDialog.DialogCode

        def __init__(self, *_a, **_k):
            self.sections, self.path, self.fmt = flags, path, "xlsx"

        def exec(self):
            return self.DialogCode.Accepted

    monkeypatch.setattr(mw, "SaveStatisticsDialog", _Dialog)
    window.statistics.refresh()
    window.on_save_file()
    return pd.read_excel(path, sheet_name=None, index_col=0)


def _sheet(book, prefix):
    return next(frame for name, frame in book.items()
                if name.startswith(prefix))


def test_the_exported_report_carries_mg_number(window, tmp_path,
                                               monkeypatch):
    _preprocess(window)
    book = _export(window, tmp_path, monkeypatch)
    paper = _sheet(book, "Paper table")
    assert MG_NUMBER_FEOT in paper.index and MG_NUMBER_ADJ in paper.index
    descriptive = _sheet(book, "Descriptive")
    assert MG_NUMBER_FEOT in set(descriptive.index) | set(descriptive)
    ratios = _sheet(book, "Trace-element")
    assert MG_NUMBER_FEOT in ratios.columns
    assert MG_NUMBER_ADJ in ratios.columns         # the switch is on


def test_the_export_uses_the_adjustment_that_was_chosen(window, tmp_path,
                                                        monkeypatch):
    """It used to recompute its own (anhydrous, Middlemost), whatever
    had been chosen, and put the twins in the "Original data" sheet."""
    _preprocess(window, "anhydrous", "le_maitre")
    book = _export(window, tmp_path, monkeypatch)
    original = _sheet(book, "Original data")
    assert not [c for c in original.columns if str(c).endswith("_adj")]
    adjusted = _sheet(book, "Adjusted data")
    assert adjusted["FeO_adj"].to_numpy() == pytest.approx(
        window.data.df["FeO_adj"].to_numpy())
    from birds.cipw import compute_cipw
    cipw = _sheet(book, "CIPW")
    expected = compute_cipw(window.data.majors_df())
    assert cipw["norm_Q"].to_numpy() == pytest.approx(
        expected["norm_Q"].to_numpy())


def test_the_exported_ratios_follow_the_switch(window, tmp_path,
                                               monkeypatch):
    _preprocess(window)
    window.data.use_adjusted = False
    book = _export(window, tmp_path, monkeypatch)
    ratios = _sheet(book, "Trace-element")
    assert MG_NUMBER_ADJ not in ratios.columns
    pd.testing.assert_frame_equal(
        ratios, window.statistics.ratio_frame(), check_dtype=False,
        check_names=False, check_index_type=False)
