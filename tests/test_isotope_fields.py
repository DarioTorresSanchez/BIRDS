"""Sr-Nd mantle fields, measured from the published figure.

Every expected number is an independent reading of the figure taken
from something the module does not store — a tick, a frame edge, or a
published reference value — so a refactor that nudges a field fails
here rather than quietly relabelling somebody's basalts.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.isotope_fields import (
    BSE_SR_87_86,
    CHUR_ND_143_144,
    FIELDS_BY_NAME,
    MANTLE_ARRAY,
    MANTLE_ARRAY_LABEL,
    MANTLE_ARRAY_LOWER,
    MANTLE_ARRAY_UPPER,
    SR_ND_FIELDS,
    SR_ND_WINDOW,
    array_slope,
    resolve_field,
)

#: One pixel of the source figure, in data units.
PX_SR = 1.951e-5
PX_ND = 5.862e-6


def nd_on(bound, sr: float) -> float:
    (x0, y0), (x1, y1) = bound
    return y0 + (sr - x0) * (y1 - y0) / (x1 - x0)


class TestReferenceLines:
    def test_the_horizontal_line_is_chur(self):
        """It is labelled "0 εNd", and it measured 0.5126357."""
        assert CHUR_ND_143_144 == pytest.approx(0.5126357, abs=PX_ND)

    def test_chur_matches_the_published_value(self):
        assert CHUR_ND_143_144 == 0.512638     # Jacobsen & Wasserburg 1980

    def test_the_vertical_line_measured_where_it_is_set(self):
        assert BSE_SR_87_86 == pytest.approx(0.705126, abs=2 * PX_SR)

    def test_epsilon_sr_is_referred_to_the_vertical_line(self):
        """The older uniform reservoir, 0.7045, is 32 px away; εSr is
        referred to the BSE the figure draws instead (decided
        2026-10-08), so εSr = 0 falls on the line."""
        from birds.views.isotopes import SR_UR_87_86
        assert SR_UR_87_86 == BSE_SR_87_86
        assert abs(BSE_SR_87_86 - 0.7045) > 20 * PX_SR

    def test_the_vertical_line_crosses_the_bse_box(self):
        sr0, sr1, _, _ = FIELDS_BY_NAME["BSE"].bounds()
        assert sr0 < BSE_SR_87_86 < sr1

    def test_chur_crosses_the_bse_box(self):
        _, _, nd0, nd1 = FIELDS_BY_NAME["BSE"].bounds()
        assert nd0 < CHUR_ND_143_144 < nd1


class TestWindow:
    def test_the_axis_range_is_the_frame(self):
        """Measured 0.70101-0.70899 and 0.51200-0.51365."""
        (x0, x1), (y0, y1) = SR_ND_WINDOW
        assert x0 == pytest.approx(0.70101, abs=PX_SR)
        assert x1 == pytest.approx(0.70899, abs=PX_SR)
        assert y0 == pytest.approx(0.51200, abs=PX_ND)
        assert y1 == pytest.approx(0.51365, abs=PX_ND)

    def test_the_top_runs_past_the_last_labelled_tick(self):
        """Cutting at 0.5135 would slice the top off DM."""
        _, (_, y1) = SR_ND_WINDOW
        assert y1 > 0.5135
        assert FIELDS_BY_NAME["DM"].bounds()[3] < y1

    def test_every_field_fits_inside_it(self):
        (x0, x1), (y0, y1) = SR_ND_WINDOW
        for fld in SR_ND_FIELDS:
            sr0, sr1, nd0, nd1 = fld.bounds()
            assert x0 <= sr0 and sr1 <= x1, fld.name
            assert y0 <= nd0 and nd1 <= y1, fld.name

    def test_every_label_fits_inside_it(self):
        (x0, x1), (y0, y1) = SR_ND_WINDOW
        for fld in SR_ND_FIELDS:
            assert x0 < fld.label[0] < x1, fld.name
            assert y0 < fld.label[1] < y1, fld.name


class TestMantleArray:
    def test_two_bounds_are_drawn(self):
        assert len(MANTLE_ARRAY) == 2

    def test_they_are_parallel(self):
        """Fitted slopes agree to better than a quarter of a per cent."""
        upper = array_slope(MANTLE_ARRAY_UPPER)
        lower = array_slope(MANTLE_ARRAY_LOWER)
        assert upper == pytest.approx(lower, rel=0.01)

    def test_the_slope_is_the_measured_one(self):
        assert array_slope() == pytest.approx(-0.2035, abs=0.002)

    def test_the_slope_is_negative(self):
        """Sr and Nd are anticorrelated; a positive slope is a sign slip."""
        assert array_slope() < 0

    def test_in_epsilon_units_it_matches_the_classic_relation(self):
        """εNd ≈ -0.25 to -0.33 εSr for the mantle array."""
        from birds.views.isotopes import SR_UR_87_86
        eps = array_slope() * (SR_UR_87_86 / CHUR_ND_143_144)
        assert -0.34 < eps < -0.24

    def test_the_bounds_never_cross(self):
        for sr in np.linspace(0.7014, 0.7060, 24):
            assert nd_on(MANTLE_ARRAY_UPPER, sr) > nd_on(MANTLE_ARRAY_LOWER,
                                                         sr)

    @pytest.mark.parametrize("name", ["DM", "PREMA", "BSE"])
    def test_the_upper_bound_runs_through_these(self, name):
        """The figure draws it through all three."""
        sr0, sr1, nd0, nd1 = FIELDS_BY_NAME[name].bounds()
        mid = (sr0 + sr1) / 2.0
        assert nd0 <= nd_on(MANTLE_ARRAY_UPPER, mid) <= nd1, name

    def test_the_lower_bound_runs_through_himu(self):
        sr0, sr1, nd0, nd1 = FIELDS_BY_NAME["HIMU"].bounds()
        mid = (sr0 + sr1) / 2.0
        assert nd0 <= nd_on(MANTLE_ARRAY_LOWER, mid) <= nd1

    def test_the_label_is_set_just_above_the_upper_bound(self):
        """The figure writes it along that line, not inside the band."""
        sr, nd = MANTLE_ARRAY_LABEL
        above = nd - nd_on(MANTLE_ARRAY_UPPER, sr)
        assert 0 < above < 0.0002
        assert nd > nd_on(MANTLE_ARRAY_LOWER, sr)

    def test_the_bounds_stop_short_of_the_frame(self):
        """The figure draws them in mid-air, not across the whole panel."""
        (x0, x1), _ = SR_ND_WINDOW
        for (a, _), (b, _) in MANTLE_ARRAY:
            assert a > x0 and b < x1


class TestFields:
    def test_all_six_components_are_present(self):
        assert {f.name for f in SR_ND_FIELDS} == {
            "DM", "PREMA", "HIMU", "BSE", "EMI", "EMII"}

    def test_emii_is_named_but_not_outlined(self):
        """The figure labels the region without enclosing it."""
        assert not FIELDS_BY_NAME["EMII"].is_drawn

    def test_every_other_field_is_outlined(self):
        for fld in SR_ND_FIELDS:
            if fld.name != "EMII":
                assert fld.is_drawn, fld.name

    def test_outlines_have_at_least_three_vertices(self):
        for fld in SR_ND_FIELDS:
            if fld.is_drawn:
                assert len(fld.vertices) >= 3, fld.name

    def test_no_outline_is_closed_by_repeating_its_first_vertex(self):
        """matplotlib closes the polygon; a repeat would draw a spur."""
        for fld in SR_ND_FIELDS:
            if fld.is_drawn:
                assert fld.vertices[0] != fld.vertices[-1], fld.name

    @pytest.mark.parametrize("name,sr0,sr1,nd0,nd1", [
        ("DM",    0.70173, 0.70236, 0.513272, 0.513553),
        ("PREMA", 0.70329, 0.70353, 0.512961, 0.513043),
        ("HIMU",  0.70273, 0.70325, 0.512850, 0.512949),
        ("BSE",   0.70479, 0.70546, 0.512533, 0.512691),
        ("EMI",   0.70397, 0.70569, 0.512000, 0.512252),
    ])
    def test_measured_extents(self, name, sr0, sr1, nd0, nd1):
        got = FIELDS_BY_NAME[name].bounds()
        assert got[0] == pytest.approx(sr0, abs=PX_SR)
        assert got[1] == pytest.approx(sr1, abs=PX_SR)
        assert got[2] == pytest.approx(nd0, abs=PX_ND)
        assert got[3] == pytest.approx(nd1, abs=PX_ND)

    def test_emi_is_cut_off_by_the_axis(self):
        """Its base is the frame, so the drawn field is not the whole one."""
        emi = FIELDS_BY_NAME["EMI"]
        assert emi.open_below
        assert emi.bounds()[2] == pytest.approx(SR_ND_WINDOW[1][0])

    def test_the_components_are_ordered_by_neodymium(self):
        drawn = [f for f in SR_ND_FIELDS if f.is_drawn]
        tops = [f.bounds()[3] for f in drawn]
        assert tops == sorted(tops, reverse=True)

    def test_dm_is_the_most_depleted_and_emi_the_least(self):
        nd = {f.name: f.centre()[1] for f in SR_ND_FIELDS if f.is_drawn}
        assert nd["DM"] == max(nd.values())
        assert nd["EMI"] == min(nd.values())

    def test_emii_is_the_most_radiogenic_in_strontium(self):
        sr = {f.name: f.centre()[0] for f in SR_ND_FIELDS}
        assert sr["EMII"] == max(sr.values())

    def test_no_two_outlines_overlap(self):
        """They are distinct components; an overlap would hide one."""
        drawn = [f for f in SR_ND_FIELDS if f.is_drawn]
        for i, a in enumerate(drawn):
            for b in drawn[i + 1:]:
                a0, a1, a2, a3 = a.bounds()
                b0, b1, b2, b3 = b.bounds()
                apart = (a1 < b0 or b1 < a0 or a3 < b2 or b3 < a2)
                assert apart, f"{a.name} overlaps {b.name}"

    def test_colours_are_hex(self):
        for fld in SR_ND_FIELDS:
            assert fld.colour.startswith("#") and len(fld.colour) == 7

    def test_hatched_fields_are_the_ones_the_figure_hatches(self):
        hatched = {f.name for f in SR_ND_FIELDS if f.hatch}
        assert hatched == {"HIMU", "EMI"}


class TestLegacyNames:
    @pytest.mark.parametrize("old,new", [("EM1", "EMI"), ("EM2", "EMII")])
    def test_old_session_keys_still_resolve(self, old, new):
        assert resolve_field(old).name == new

    def test_current_names_resolve_to_themselves(self):
        for fld in SR_ND_FIELDS:
            assert resolve_field(fld.name) is fld

    def test_an_unknown_name_is_not_guessed(self):
        assert resolve_field("EM3") is None


class TestViewIntegration:
    def frame(self):
        return pd.DataFrame({
            "Sample_Name": ["a", "b", "c"],
            "87Sr/86Sr": [0.70312, 0.70405, 0.70521],
            "143Nd/144Nd": [0.512930, 0.512710, 0.512560],
            "Suite": ["s", "s", "s"],
        })

    def view(self, qapp, df=None):
        from birds.data_manager import DataManager
        from birds.plot_style import GroupStyle, PlotStyle
        from birds.views.isotopes import IsotopesView
        dm = DataManager()
        dm.df = self.frame() if df is None else df
        style = PlotStyle()
        style.group_columns = ["Suite"]
        style.groups = [GroupStyle(name="s")]
        v = IsotopesView(dm, style)
        v._populate_columns()
        v.update_plot()
        return v

    def test_the_default_view_is_the_published_window(self, qapp):
        ax = self.view(qapp).canvas.figure.axes[0]
        assert ax.get_xlim() == pytest.approx(SR_ND_WINDOW[0])
        assert ax.get_ylim() == pytest.approx(SR_ND_WINDOW[1])

    def test_data_outside_the_window_widens_it(self, qapp):
        """Clipping a sample away would still count it as plotted."""
        df = self.frame()
        df.loc[0, "87Sr/86Sr"] = 0.7200
        df.loc[0, "143Nd/144Nd"] = 0.51150
        ax = self.view(qapp, df).canvas.figure.axes[0]
        assert ax.get_xlim()[1] > 0.7200
        assert ax.get_ylim()[0] < 0.51150

    def test_data_inside_the_window_does_not_shrink_it(self, qapp):
        ax = self.view(qapp).canvas.figure.axes[0]
        assert ax.get_xlim()[0] <= SR_ND_WINDOW[0][0]
        assert ax.get_xlim()[1] >= SR_ND_WINDOW[0][1]

    def test_fields_are_drawn_below_the_samples(self, qapp):
        """A filled field over the data would hide it."""
        ax = self.view(qapp).canvas.figure.axes[0]
        assert ax.patches, "no fields drawn"
        top_field = max(p.get_zorder() for p in ax.patches)
        assert all(c.get_zorder() > top_field for c in ax.collections)

    def test_fields_are_plain_white_with_an_outline(self, qapp):
        """Unfilled and unhatched, so the samples stay legible over them."""
        ax = self.view(qapp).canvas.figure.axes[0]
        for patch in ax.patches:
            assert patch.get_facecolor()[:3] == (1.0, 1.0, 1.0)
            assert patch.get_hatch() is None
            assert patch.get_edgecolor()[3] > 0
            assert patch.get_linewidth() > 0

    def test_the_rules_are_drawn_over_the_fields(self, qapp):
        """A white field would otherwise break the line it sits on."""
        ax = self.view(qapp).canvas.figure.axes[0]
        top_field = max(p.get_zorder() for p in ax.patches)
        rules = [ln for ln in ax.lines if ln.get_zorder() > 1]
        assert rules, "no reference lines drawn"
        assert all(ln.get_zorder() > top_field for ln in rules)

    def test_the_source_fills_are_still_recorded(self):
        """The view does not draw them, but the measurement keeps them."""
        for fld in SR_ND_FIELDS:
            assert fld.colour.startswith("#")
        assert {f.name for f in SR_ND_FIELDS if f.hatch} == {"HIMU", "EMI"}

    def test_every_field_name_reaches_the_plot(self, qapp):
        ax = self.view(qapp).canvas.figure.axes[0]
        texts = {t.get_text() for t in ax.texts}
        for fld in SR_ND_FIELDS:
            assert fld.name in texts, fld.name
        assert "Mantle array" in texts

    def test_unchecking_a_field_removes_it_and_its_label(self, qapp):
        v = self.view(qapp)
        v.res_checks["HIMU"].setChecked(False)
        v.update_plot()
        texts = {t.get_text() for t in v.canvas.figure.axes[0].texts}
        assert "HIMU" not in texts
        assert "DM" in texts

    def test_the_legend_lists_groups_not_fields(self, qapp):
        ax = self.view(qapp).canvas.figure.axes[0]
        legend = ax.get_legend()
        assert legend is not None
        labels = {t.get_text() for t in legend.get_texts()}
        assert "s" in labels
        assert not labels & {f.name for f in SR_ND_FIELDS}

    def test_the_array_can_be_switched_off(self, qapp):
        v = self.view(qapp)
        v.mantle_array_chk.setChecked(False)
        v.update_plot()
        texts = {t.get_text() for t in v.canvas.figure.axes[0].texts}
        assert "Mantle array" not in texts

    def test_a_session_written_with_the_old_names_restores(self, qapp):
        v = self.view(qapp)
        state = v.serialize()
        state["reservoirs"] = {"EM1": False, "EM2": False, "DM": True}
        v.restore(state)
        assert not v.res_checks["EMI"].isChecked()
        assert not v.res_checks["EMII"].isChecked()
        assert v.res_checks["DM"].isChecked()

    def test_a_round_trip_through_serialize_keeps_the_toggles(self, qapp):
        v = self.view(qapp)
        v.res_checks["BSE"].setChecked(False)
        state = v.serialize()
        v.res_checks["BSE"].setChecked(True)
        v.restore(state)
        assert not v.res_checks["BSE"].isChecked()

# ==========================================================================
# Lead
# ==========================================================================

from birds.isotope_fields import (  # noqa: E402
    NHRL_207_206,
    NHRL_208_206,
    PB207_WINDOW,
    PB208_WINDOW,
    nhrl,
    pb_window,
)


class TestNhrl:
    """The one reference the Pb panels carry."""

    def test_hart_coefficients_are_kept_exactly(self):
        """A published equation, not a curve traced off a redrawing."""
        assert NHRL_207_206 == (0.1084, 13.491)
        assert NHRL_208_206 == (1.209, 15.627)

    def test_the_figure_agrees_with_the_published_slope(self):
        """Traced 1.1942 on the 208Pb panel and 0.1198 on the 207Pb one."""
        assert NHRL_208_206[0] == pytest.approx(1.1942, rel=0.02)
        assert NHRL_207_206[0] == pytest.approx(0.1198, rel=0.12)

    def test_it_evaluates_on_both_planes(self):
        assert nhrl(18.0, "207") == pytest.approx(0.1084 * 18.0 + 13.491)
        assert nhrl(18.0, "208") == pytest.approx(1.209 * 18.0 + 15.627)

    def test_it_is_vectorised(self):
        xs = np.array([17.0, 18.0, 19.0])
        assert np.allclose(nhrl(xs, "208"), 1.209 * xs + 15.627)

    def test_it_rises_on_both_planes(self):
        for which in ("207", "208"):
            assert nhrl(19.0, which) > nhrl(17.0, which)

    def test_the_two_planes_are_not_the_same_line(self):
        """Passing the wrong plane would draw the 207 line on the 208 axes."""
        assert nhrl(18.0, "207") != pytest.approx(nhrl(18.0, "208"))


class TestPbWindows:
    """Only the fallback for a panel with no data in it."""

    def test_they_are_the_measured_frames(self):
        assert PB207_WINDOW == ((15.0, 22.5), (15.15, 16.00))
        assert PB208_WINDOW == ((15.0, 22.5), (37.18, 41.81))

    def test_pb_window_dispatches(self):
        assert pb_window("207") == PB207_WINDOW
        assert pb_window("208") == PB208_WINDOW

    def test_the_nhrl_crosses_each_frame(self):
        """A fallback window the line misses would open on an empty plot."""
        for y_iso in ("207", "208"):
            (x0, x1), (y0, y1) = pb_window(y_iso)
            lo, hi = nhrl(x0, y_iso), nhrl(x1, y_iso)
            assert min(lo, hi) < y1 and max(lo, hi) > y0


class TestPbViewIntegration:
    def frame(self):
        return pd.DataFrame({
            "Sample_Name": ["a", "b", "c"],
            "206Pb/204Pb": [18.15, 18.42, 18.90],
            "207Pb/204Pb": [15.61, 15.65, 15.70],
            "208Pb/204Pb": [38.30, 38.62, 39.05],
            "Suite": ["s", "s", "s"],
        })

    def view(self, qapp, key="pb_207", df=None):
        from birds.data_manager import DataManager
        from birds.plot_style import GroupStyle, PlotStyle
        from birds.views.isotopes import IsotopesView
        dm = DataManager()
        dm.df = self.frame() if df is None else df
        style = PlotStyle()
        style.group_columns = ["Suite"]
        style.groups = [GroupStyle(name="s")]
        v = IsotopesView(dm, style)
        v._populate_columns()
        v.diagram_combo.setCurrentIndex(v.diagram_combo.findData(key))
        v.update_plot()
        return v

    @pytest.mark.parametrize("key,col", [("pb_207", "207Pb/204Pb"),
                                         ("pb_208", "208Pb/204Pb")])
    def test_the_axes_follow_the_data(self, qapp, key, col):
        """Pb ratios span a narrow range; a fixed frame would shrink
        the dataset to a blob in the middle."""
        df = self.frame()
        ax = self.view(qapp, key, df).canvas.figure.axes[0]
        assert ax.get_xlim()[0] < df["206Pb/204Pb"].min()
        assert ax.get_xlim()[1] > df["206Pb/204Pb"].max()
        assert ax.get_xlim()[1] - ax.get_xlim()[0] < 3.0

    def test_an_empty_panel_falls_back_to_the_published_frame(self, qapp):
        df = self.frame()
        df[["206Pb/204Pb", "207Pb/204Pb"]] = np.nan
        ax = self.view(qapp, "pb_207", df).canvas.figure.axes[0]
        assert ax.get_xlim() == pytest.approx(PB207_WINDOW[0])
        assert ax.get_ylim() == pytest.approx(PB207_WINDOW[1])

    def test_a_single_sample_still_gets_room_around_it(self, qapp):
        """Zero spread must not collapse the axes onto the point."""
        df = self.frame().iloc[:1]
        ax = self.view(qapp, "pb_207", df).canvas.figure.axes[0]
        assert ax.get_xlim()[1] > ax.get_xlim()[0]
        assert ax.get_ylim()[1] > ax.get_ylim()[0]

    @pytest.mark.parametrize("key", ["pb_207", "pb_208"])
    def test_the_nhrl_is_drawn_on_both_planes(self, qapp, key):
        labels = (self.view(qapp, key).canvas.figure.axes[0]
                  .get_legend_handles_labels()[1])
        assert any("NHRL" in t for t in labels), key

    def test_the_nhrl_spans_the_whole_width(self, qapp):
        ax = self.view(qapp).canvas.figure.axes[0]
        line = next(ln for ln in ax.lines if "NHRL" in str(ln.get_label()))
        xs = line.get_xdata()
        assert min(xs) == pytest.approx(ax.get_xlim()[0])
        assert max(xs) == pytest.approx(ax.get_xlim()[1])

    def test_the_nhrl_can_be_switched_off(self, qapp):
        v = self.view(qapp)
        v.nhrl_chk.setChecked(False)
        v.update_plot()
        labels = (v.canvas.figure.axes[0]
                  .get_legend_handles_labels()[1])
        assert not any("NHRL" in t for t in labels)

    def test_nothing_else_is_drawn_on_the_pb_panels(self, qapp):
        """No reservoir boxes, no BSE, no geochron."""
        for key in ("pb_207", "pb_208"):
            ax = self.view(qapp, key).canvas.figure.axes[0]
            assert not ax.patches, key
            assert not ax.texts, key
            assert len(ax.lines) == 1, key

    def test_the_nhrl_sits_below_the_samples(self, qapp):
        ax = self.view(qapp).canvas.figure.axes[0]
        line = ax.lines[0]
        assert all(c.get_zorder() > line.get_zorder()
                   for c in ax.collections)

    def test_the_toggle_survives_a_session_round_trip(self, qapp):
        v = self.view(qapp)
        v.nhrl_chk.setChecked(False)
        state = v.serialize()
        v.nhrl_chk.setChecked(True)
        v.restore(state)
        assert not v.nhrl_chk.isChecked()

    @pytest.mark.parametrize("key,y_iso", [("pb_207", "207"),
                                           ("pb_208", "208")])
    def test_the_nhrl_stays_on_screen(self, qapp, key, y_iso):
        """A suite that sits well off the line would otherwise push it
        out of view, losing the comparison the line exists to make."""
        ax = self.view(qapp, key).canvas.figure.axes[0]
        x_lo, x_hi = ax.get_xlim()
        y_lo, y_hi = ax.get_ylim()
        for x in (x_lo, x_hi):
            assert y_lo <= nhrl(x, y_iso) <= y_hi

    def test_switching_the_nhrl_off_lets_the_axes_close_in(self, qapp):
        v = self.view(qapp)
        with_line = v.canvas.figure.axes[0].get_ylim()
        v.nhrl_chk.setChecked(False)
        v.update_plot()
        without = v.canvas.figure.axes[0].get_ylim()
        assert (without[1] - without[0]) < (with_line[1] - with_line[0])
