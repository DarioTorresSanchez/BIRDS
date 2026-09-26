"""Hanski et al. (2001) high-Mg — boundaries measured from the figure.

Every expected value is an independent reading of the published figure
taken between the endpoints the module stores, so a refactor that
nudges a boundary fails here rather than quietly renaming komatiites.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.hanski import (
    _AL_DIVIDE,
    _BONINITE,
    _BOUNDARIES,
    _LABELS,
    _MEIMECHITE,
    _PICRITE_KOMATIITE,
    _TI_ENRICHED,
)

DIAGRAM = "hanski"


def ti_at(boundary, al: float) -> float:
    """[TiO2] of a sub-horizontal boundary at a given [Al2O3]."""
    (x0, y0), (x1, y1) = boundary
    return float(y0 + (al - x0) * (y1 - y0) / (x1 - x0))


def al_at(boundary, ti: float) -> float:
    """[Al2O3] of the steep divider at a given [TiO2]."""
    (x0, y0), (x1, y1) = boundary
    return float(x0 + (ti - y0) * (x1 - x0) / (y1 - y0))


class TestAxes:
    def test_limits_match_the_published_figure(self):
        diagram = get_diagram(DIAGRAM)
        assert diagram.x_range == (0.0, 0.25)
        assert diagram.y_range == (0.0, 0.13)

    def test_axes_are_linear(self):
        diagram = get_diagram(DIAGRAM)
        assert not getattr(diagram, "log_x", False)
        assert not getattr(diagram, "log_y", False)


class TestSubHorizontalBoundaries:
    @pytest.mark.parametrize("al,expected", [
        (0.02, 0.09022), (0.06, 0.09195), (0.10, 0.09369),
        (0.14, 0.09542), (0.18, 0.09716), (0.22, 0.09889),
    ])
    def test_meimechite(self, al, expected):
        assert ti_at(_MEIMECHITE, al) == pytest.approx(expected, abs=0.0004)

    @pytest.mark.parametrize("al,expected", [
        (0.02, 0.02057), (0.06, 0.02231), (0.10, 0.02379),
        (0.14, 0.02553), (0.18, 0.02702),
    ])
    def test_picrite_komatiite(self, al, expected):
        assert ti_at(_PICRITE_KOMATIITE, al) == pytest.approx(
            expected, abs=0.0004)

    @pytest.mark.parametrize("al,expected", [
        (0.02, 0.01066), (0.06, 0.01214), (0.10, 0.01388),
        (0.14, 0.01537), (0.18, 0.01710),
    ])
    def test_ti_enriched(self, al, expected):
        assert ti_at(_TI_ENRICHED, al) == pytest.approx(expected, abs=0.0004)

    @pytest.mark.parametrize("al,expected", [
        (0.10, 0.00397), (0.14, 0.00545), (0.18, 0.00694), (0.22, 0.00867),
    ])
    def test_boninite(self, al, expected):
        assert ti_at(_BONINITE, al) == pytest.approx(expected, abs=0.0004)

    def test_boninite_passes_through_the_origin(self):
        assert ti_at(_BONINITE, 0.0) == pytest.approx(0.0, abs=0.0005)

    def test_they_never_cross(self):
        """A crossing would swap two fields over part of the diagram."""
        ordered = (_BONINITE, _TI_ENRICHED, _PICRITE_KOMATIITE,
                   _MEIMECHITE)
        for al in np.linspace(0.0, 0.25, 26):
            values = [ti_at(b, al) for b in ordered]
            assert values == sorted(values), f"boundaries cross at {al}"

    def test_they_are_nearly_parallel(self):
        """The figure draws them as a family; slopes agree within 10 %."""
        slopes = [(y1 - y0) / (x1 - x0)
                  for (x0, y0), (x1, y1) in
                  (_BONINITE, _TI_ENRICHED, _PICRITE_KOMATIITE,
                   _MEIMECHITE)]
        assert max(slopes) / min(slopes) < 1.10

    def test_all_rise_towards_higher_alumina(self):
        for boundary in (_BONINITE, _TI_ENRICHED, _PICRITE_KOMATIITE,
                         _MEIMECHITE):
            assert boundary[1][1] > boundary[0][1]


class TestAluminaDivide:
    @pytest.mark.parametrize("ti,expected", [
        (0.01, 0.16646), (0.02, 0.15716), (0.04, 0.13936),
        (0.06, 0.12156), (0.08, 0.10336),
    ])
    def test_position(self, ti, expected):
        assert al_at(_AL_DIVIDE, ti) == pytest.approx(expected, abs=0.0008)

    def test_it_leans_towards_lower_alumina_as_titanium_rises(self):
        assert _AL_DIVIDE[1][0] > _AL_DIVIDE[0][0]
        assert _AL_DIVIDE[1][1] < _AL_DIVIDE[0][1]

    def test_it_meets_the_meimechite_line_at_its_top(self):
        top_al, top_ti = _AL_DIVIDE[0]
        assert ti_at(_MEIMECHITE, top_al) == pytest.approx(top_ti,
                                                           abs=0.0006)

    def test_it_meets_the_boninite_line_at_its_bottom(self):
        low_al, low_ti = _AL_DIVIDE[1]
        assert ti_at(_BONINITE, low_al) == pytest.approx(low_ti, abs=0.0006)

    def test_it_is_not_vertical(self):
        assert abs(_AL_DIVIDE[1][0] - _AL_DIVIDE[0][0]) > 0.05


class TestFields:
    def test_all_eight_fields_are_named(self):
        assert len(_LABELS) == 8
        assert len({n for n, _x, _y in _LABELS}) == 8

    def test_every_label_is_inside_the_axes(self):
        diagram = get_diagram(DIAGRAM)
        for name, x, y in _LABELS:
            assert diagram.x_range[0] <= x <= diagram.x_range[1], name
            assert diagram.y_range[0] <= y <= diagram.y_range[1], name

    @pytest.mark.parametrize("name,side", [
        ("Al-depleted\nPicrite", "left"),
        ("Ti-enriched, Al-depleted komatiite", "left"),
        ("Al-depleted komatiite", "left"),
        ("Picrite", "right"),
        ("Ti-enriched komatiite", "right"),
        ("Al-undepleted\nkomatiite", "right"),
    ])
    def test_labels_sit_on_their_side_of_the_divide(self, name, side):
        x, y = next((x, y) for n, x, y in _LABELS if n == name)
        divide = al_at(_AL_DIVIDE, y)
        assert (x < divide) if side == "left" else (x > divide), name

    def test_meimechite_sits_above_its_boundary(self):
        x, y = next((x, y) for n, x, y in _LABELS if n == "Meimechite")
        assert y > ti_at(_MEIMECHITE, x)

    def test_boninite_sits_below_its_boundary(self):
        x, y = next((x, y) for n, x, y in _LABELS if n == "Boninite")
        assert y < ti_at(_BONINITE, x)


def field_of(al: float, ti: float) -> str:
    """Name the field a projected point falls in."""
    depleted = al < al_at(_AL_DIVIDE, ti)
    if ti > ti_at(_MEIMECHITE, al):
        return "Meimechite"
    if ti > ti_at(_PICRITE_KOMATIITE, al):
        return "Al-depleted picrite" if depleted else "Picrite"
    if ti > ti_at(_TI_ENRICHED, al):
        return ("Ti-enriched, Al-depleted komatiite" if depleted
                else "Ti-enriched komatiite")
    if ti > ti_at(_BONINITE, al):
        return ("Al-depleted komatiite" if depleted
                else "Al-undepleted komatiite")
    return "Boninite"


def project(analysis: dict) -> tuple[float, float]:
    """[Al2O3], [TiO2] of one analysis given as an oxide dict."""
    xs, ys = get_diagram(DIAGRAM)._compute_xy(pd.DataFrame([analysis]))
    return float(xs.iloc[0]), float(ys.iloc[0])


class TestProjectionAgainstThePaper:
    """Table 1 of Hanski et al. (2001), projected and classified.

    The paper states where these rocks land: "the Jeesiorova komatiites
    display similar [Al2O3] values [to Munro Township] but are in most
    cases distinctly higher in [TiO2] and plot within the field of
    Ti-enriched komatiites" (p. 865).  Fe2O3* is total iron.
    """

    # Sample, SiO2, TiO2, Al2O3, Fe2O3*, MnO, MgO, CaO, Na2O, K2O, P2O5
    JEESIOROVA = [
        ("17-EJH-97",  40.74, 0.67,  8.00, 10.71, 0.12, 23.09, 7.92, 0.11, 0.05, 0.04),
        ("13-EJH-97",  41.87, 0.47,  6.67, 11.06, 0.20, 25.44, 6.66, 0.09, 0.03, 0.02),
        ("12d-PPR-97", 42.29, 0.63,  6.48, 11.23, 0.14, 23.73, 7.96, 0.12, 0.01, 0.03),
        ("12c-PPR-97", 40.68, 0.76,  7.71, 12.70, 0.20, 21.92, 8.66, 0.15, 0.01, 0.04),
        ("12-PPR-97",  38.06, 0.70,  7.10, 10.81, 0.16, 23.48, 9.32, 0.08, 0.01, 0.04),
        ("10d-PPR-97", 41.66, 0.64,  6.59, 11.25, 0.15, 24.51, 7.21, 0.14, 0.02, 0.03),
        ("17.1-PPR",   39.95, 0.52,  7.62, 13.40, 0.21, 24.20, 6.77, 0.11, 0.07, 0.03),
        ("9-PPR-97",   45.63, 0.96, 12.48, 11.02, 0.13, 11.58, 9.09, 3.19, 0.07, 0.06),
        ("8-PPR-97",   44.43, 0.61,  7.13, 11.66, 0.16, 21.60, 8.19, 0.11, 0.03, 0.03),
        ("7-PPR-97",   41.78, 0.74,  9.35, 15.20, 0.18, 15.89, 9.93, 0.62, 0.06, 0.04),
        ("8-EJH-97",   45.79, 0.80, 10.26, 11.91, 0.21, 16.13, 9.64, 1.35, 0.12, 0.04),
    ]
    COLUMNS = ("SiO2", "TiO2", "Al2O3", "Fe2O3T", "MnO", "MgO", "CaO",
               "Na2O", "K2O", "P2O5")

    @classmethod
    def frame(cls) -> pd.DataFrame:
        df = pd.DataFrame([r[1:] for r in cls.JEESIOROVA],
                          columns=list(cls.COLUMNS))
        df.insert(0, "Sample_Name", [r[0] for r in cls.JEESIOROVA])
        return df

    def projected(self):
        df = self.frame()
        xs, ys = get_diagram(DIAGRAM)._compute_xy(df)
        return list(zip(df["Sample_Name"], xs, ys))

    def test_every_sample_lands_inside_the_diagram(self):
        """The defect this replaces put all of them off the plot."""
        diagram = get_diagram(DIAGRAM)
        for name, x, y in self.projected():
            assert diagram.x_range[0] <= x <= diagram.x_range[1], name
            assert diagram.y_range[0] <= y <= diagram.y_range[1], name

    def test_most_are_ti_enriched_komatiites_as_the_paper_states(self):
        named = [(n, field_of(x, y)) for n, x, y in self.projected()]
        hits = [n for n, f in named if f == "Ti-enriched komatiite"]
        assert len(hits) >= 9, named

    def test_none_is_a_picrite_a_meimechite_or_a_boninite(self):
        """They are komatiitic rocks; only the Ti band should vary."""
        for name, x, y in self.projected():
            assert "komatiite" in field_of(x, y), (name, field_of(x, y))

    def test_alumina_matches_munro_township_not_barberton(self):
        """The paper compares them to the Al-undepleted suites."""
        for name, x, y in self.projected():
            assert x > al_at(_AL_DIVIDE, y), name

    @pytest.mark.parametrize("name,al,ti", [
        ("10d-PPR-97", 0.1847, 0.02290),
        ("17-EJH-97",  0.2113, 0.02260),
    ])
    def test_hand_computed_values(self, name, al, ti):
        """Worked through by hand from the published analysis."""
        got = dict((n, (x, y)) for n, x, y in self.projected())[name]
        assert got[0] == pytest.approx(al, abs=0.0005)
        assert got[1] == pytest.approx(ti, abs=0.0005)

    def test_the_suite_forms_one_tight_cluster(self):
        """MgO spans 11.6-25.4 wt %, yet the projection collapses it.

        That is the whole point of projecting from olivine, and it is
        the property most sensitive to getting the projection wrong.
        """
        xs = [x for _n, x, _y in self.projected()]
        assert max(xs) - min(xs) < 0.07

    def test_a_peuramaa_picrite_plots_in_the_picrite_field(self):
        """The other suite in the paper: "still higher [TiO2] and
        accordingly plot within the picrite field", with a very low
        Al2O3/TiO2 of 5.0-6.5 and MgO near 17-18 wt % (p. 861, 865)."""
        x, y = project(dict(SiO2=45.0, TiO2=1.90, Al2O3=10.5,
                            Fe2O3T=13.5, MnO=0.18, MgO=17.5, CaO=9.0,
                            Na2O=1.3, K2O=0.2, P2O5=0.18))
        assert field_of(x, y) == "Picrite"

    def test_chondritic_alumina_titania_stays_in_the_komatiite_band(self):
        """"The Al-undepleted Munro Township and Gorgona Island
        komatiites straddle the line with Al2O3/TiO2 of 20" — so that
        ray must not leave the komatiite band anywhere on the plot.

        It does cross the oblique Al divide, which is correct: the
        paper notes Barberton samples that "overlap with the
        Al-undepleted komatiites in terms of the Al2O3/TiO2 value".
        """
        # Sharing one denominator, [Al2O3]/[TiO2] is the molar ratio.
        molar = 20.0 * 79.8658 / 101.9613
        for al in np.linspace(0.02, 0.25, 12):
            ti = al / molar
            assert field_of(al, ti).endswith("komatiite"), al
            assert "Ti-enriched" not in field_of(al, ti), al


class TestProjectionProperties:
    """Properties the projection must have, independent of any figure."""

    BASALT = dict(SiO2=45.0, TiO2=0.64, Al2O3=6.59, Fe2O3T=11.25,
                  MnO=0.15, MgO=20.0, CaO=7.21, Na2O=0.14, K2O=0.02,
                  P2O5=0.03)

    def test_an_olivine_control_line_collapses_to_one_point(self):
        """The defining property: "All rock or liquid compositions that
        lie on an olivine control line have constant [Al2O3] and [TiO2]
        values and therefore a fixed position on the diagram" (p. 865).
        """
        mw_fo, mw_fa, mw_si = 40.3044, 71.8444, 60.0843
        mw_fe2o3 = 159.6882
        rows = []
        for grams in (0.0, 10.0, 20.0, 30.0, 40.0):   # Fo90 added to 100 g
            n = grams / (1.8 * mw_fo + 0.2 * mw_fa + mw_si)
            row = dict(self.BASALT)
            row["SiO2"] += n * mw_si
            row["MgO"] += 1.8 * n * mw_fo
            row["Fe2O3T"] += 0.2 * n * mw_fe2o3 / 2.0
            rows.append(row)
        xs, ys = get_diagram(DIAGRAM)._compute_xy(pd.DataFrame(rows))
        spread = rows[-1]["MgO"] - rows[0]["MgO"]
        assert spread > 15.0, f"only {spread:.1f} wt % MgO of olivine added"
        assert float(xs.max() - xs.min()) < 1e-6
        assert float(ys.max() - ys.min()) < 1e-6

    def test_olivine_itself_has_no_position(self):
        """Forsterite is the projection point, where the denominator
        vanishes.  A NaN keeps it off the plot; a signed infinity would
        put it in a field."""
        x, y = project(dict(SiO2=42.7, TiO2=0.0, Al2O3=0.0, FeO=0.0,
                            MgO=57.3, CaO=0.0))
        assert np.isnan(x) and np.isnan(y)

    def test_a_dunite_is_dropped_rather_than_sign_flipped(self):
        """Past the projection point the denominator turns negative and
        the old code mirrored the sample across the diagram."""
        x, y = project(dict(SiO2=41.0, TiO2=0.05, Al2O3=0.6, FeO=8.0,
                            MgO=48.0, CaO=0.4))
        assert np.isnan(x) or x >= 0.0
        assert np.isnan(y) or y >= 0.0

    def test_loss_on_ignition_does_not_move_a_sample(self):
        """Normalising the oxides to unity recalculates anhydrous, so a
        hydrated komatiite plots with its fresh equivalent."""
        fresh = project(self.BASALT)
        altered = project(dict(self.BASALT, LOI=8.0, H2O=1.5))
        assert altered[0] == pytest.approx(fresh[0])
        assert altered[1] == pytest.approx(fresh[1])

    def test_all_iron_is_taken_as_ferrous(self):
        """"For simplicity, all iron is taken as ferrous" — a split
        analysis must match the same iron reported as a total."""
        split = dict(self.BASALT)
        del split["Fe2O3T"]
        split["FeO"], split["Fe2O3"] = 6.0, 4.5819  # ≡ 11.25 Fe2O3t
        assert project(split)[0] == pytest.approx(project(self.BASALT)[0],
                                                  rel=2e-3)

    def test_ferric_iron_is_added_not_ignored(self):
        """The old code read FeO alone and silently dropped Fe2O3."""
        both = dict(self.BASALT)
        del both["Fe2O3T"]
        both["FeO"], both["Fe2O3"] = 6.0, 5.0
        ferrous_only = dict(both, Fe2O3=0.0)
        assert project(both)[0] != pytest.approx(project(ferrous_only)[0])

    def test_the_scale_is_that_of_the_published_axes(self):
        """A komatiite belongs on the plot, not three orders off it."""
        diagram = get_diagram(DIAGRAM)
        x, y = project(dict(SiO2=46.0, TiO2=0.35, Al2O3=7.8, FeO=10.5,
                            MnO=0.17, MgO=28.0, CaO=6.8, Na2O=0.1,
                            K2O=0.02, P2O5=0.03))
        assert diagram.x_range[0] < x < diagram.x_range[1]
        assert diagram.y_range[0] < y < diagram.y_range[1]


class TestRequiredColumns:
    def test_missing_columns_are_reported_not_guessed(self):
        diagram = get_diagram(DIAGRAM)
        xs, ys = diagram._compute_xy(pd.DataFrame({"Al2O3": [8.0]}))
        assert xs is None and ys is None

    @pytest.mark.parametrize("dropped", ["SiO2", "TiO2", "Al2O3", "MgO",
                                         "CaO"])
    def test_each_essential_oxide_is_required(self, dropped):
        """Treating an absent oxide as zero would shift every point."""
        analysis = dict(TestProjectionProperties.BASALT)
        del analysis[dropped]
        xs, ys = get_diagram(DIAGRAM)._compute_xy(pd.DataFrame([analysis]))
        assert xs is None and ys is None

    def test_iron_is_required(self):
        analysis = dict(TestProjectionProperties.BASALT)
        del analysis["Fe2O3T"]
        xs, ys = get_diagram(DIAGRAM)._compute_xy(pd.DataFrame([analysis]))
        assert xs is None and ys is None

    def test_minor_oxides_are_optional(self):
        """Dropping MnO or P2O5 shifts the sum by well under a per cent."""
        full = project(TestProjectionProperties.BASALT)
        lean = dict(TestProjectionProperties.BASALT)
        for oxide in ("MnO", "P2O5", "K2O"):
            del lean[oxide]
        assert project(lean)[0] == pytest.approx(full[0], rel=0.01)

    def test_column_names_are_matched_case_insensitively(self):
        analysis = {k.lower(): v
                    for k, v in TestProjectionProperties.BASALT.items()}
        xs, _ys = get_diagram(DIAGRAM)._compute_xy(pd.DataFrame([analysis]))
        assert xs is not None
        assert float(xs.iloc[0]) == pytest.approx(
            project(TestProjectionProperties.BASALT)[0])

    def test_the_citation_no_longer_carries_a_warning(self):
        citation = get_diagram(DIAGRAM).citation.lower()
        assert "unverified" not in citation
        assert "warning" not in citation

    def test_the_citation_names_the_actual_authors(self):
        """The earlier text credited an author list from another paper."""
        citation = get_diagram(DIAGRAM).citation
        for author in ("Hanski", "Huhma", "Rastas", "Kamenetsky"):
            assert author in citation
        assert "Journal of Petrology" in citation


class TestRendering:
    def test_draws_five_boundaries_and_eight_labels(self, qapp):
        from matplotlib.figure import Figure

        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle
        fig = Figure(figsize=(7, 5))
        get_diagram(DIAGRAM).plot(fig, None, PlotStyle(), PlotOptions())
        ax = fig.axes[0]
        assert len([ln for ln in ax.lines if len(ln.get_xdata()) == 2]) \
            >= len(_BOUNDARIES)
        texts = {t.get_text() for t in ax.texts}
        for name, _x, _y in _LABELS:
            assert name in texts
        fig.clf()
