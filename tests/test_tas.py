"""TAS field boundaries, against the published plotting coordinates.

Le Bas et al. (1986) give the TAS field boundaries as a list of labelled
vertices, reproduced in Rollinson & Pease (2021) Figure 3.1b under the
caption "Plotting coordinates for the field boundaries expressed as
'SiO2 and (Na2O + K2O)' after Le Bas et al. (1986)".  That list is the
source of truth here — TAS is a published table, not a drawn curve, so
nothing in this file is measured off a figure.

The fields are drawn as *closed, unfilled* outlines.  A field that the
frame bounds on one side therefore appears in the source as a short
vertex list, and its missing edges are the axes.  That is deliberate,
not an unclosed polygon.
"""

from __future__ import annotations

import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.tas import (
    _FOIDITE_LABEL,
    _PLUTONIC_FIELDS,
    _VOLCANIC_FIELDS,
    TASPlutonic,
    TASVolcanic,
)

#: Every vertex labelled in Rollinson & Pease (2021) Fig. 3.1b.
LE_BAS_VERTICES = {
    (41, 3), (45, 3), (41, 7), (45, 5), (52, 5), (49.4, 7.3),
    (57, 5.9), (63, 7), (69, 8), (45, 9.4), (48.4, 11.5),
    (52.5, 14), (53, 9.3), (57.6, 11.7), (61, 13.5),
}


def edges(fields) -> set:
    """Every segment the outlines draw, unordered and de-duplicated."""
    out = set()
    for pts in fields.values():
        n = len(pts)
        for i in range(n):
            a, b = pts[i], pts[(i + 1) % n]
            if a != b:
                out.add(tuple(sorted((a, b))))
    return out


def on_segment(p, a, b, tol=0.05) -> bool:
    """Is *p* on the line through *a* and *b*?"""
    (px, py), (ax, ay), (bx, by) = p, a, b
    if bx == ax:
        return abs(px - ax) < tol
    slope = (by - ay) / (bx - ax)
    return abs(py - (ay + slope * (px - ax))) < tol


class TestVolcanicVertices:
    """Every vertex either is published, sits on the frame, or lies on a
    published line extended to it."""

    def used(self):
        return {p for pts in _VOLCANIC_FIELDS.values() for p in pts}

    def test_every_published_vertex_is_used_or_on_a_drawn_line(self):
        used = self.used()
        for v in LE_BAS_VERTICES:
            if v in used:
                continue
            # (61, 13.5) is not stored; the boundary through it is drawn
            # out to (63, 14.5) instead.
            assert any(on_segment(v, a, b) for a, b in edges(_VOLCANIC_FIELDS)), v

    def test_no_invented_vertices(self):
        """Anything not published must sit on the x-axis or on a
        published ray — otherwise a boundary has been made up."""
        for p in self.used() - LE_BAS_VERTICES:
            if p[1] == 0:
                continue                       # field bottoms, on the frame
            assert any(
                on_segment(p, a, b, tol=0.15)
                for a in LE_BAS_VERTICES for b in LE_BAS_VERTICES if a != b
            ), p

    def test_the_phonolite_trachyte_line_follows_the_published_ray(self):
        """(63, 14.5) is (57.6, 11.7) → (61, 13.5) carried further."""
        assert on_segment((63, 14.5), (57.6, 11.7), (61, 13.5), tol=0.1)

    @pytest.mark.parametrize("a,b", [
        ((41, 3), (45, 3)), ((45, 5), (52, 5)), ((52, 5), (49.4, 7.3)),
        ((49.4, 7.3), (53, 9.3)), ((53, 9.3), (57.6, 11.7)),
        ((45, 9.4), (48.4, 11.5)), ((48.4, 11.5), (52.5, 14)),
        ((52, 5), (57, 5.9)), ((57, 5.9), (63, 7)), ((63, 7), (69, 8)),
        ((41, 7), (45, 9.4)), ((52.5, 14), (57.6, 11.7)),
    ])
    def test_published_boundary_is_drawn(self, a, b):
        assert tuple(sorted((a, b))) in edges(_VOLCANIC_FIELDS)


class TestVolcanicFields:
    def test_all_fourteen_outlines_are_present(self):
        assert len(_VOLCANIC_FIELDS) == 14

    def test_every_field_label_matches_an_outline(self):
        """An override keyed on a name no outline uses never fires."""
        assert not set(TASVolcanic.field_label_pos) - set(_VOLCANIC_FIELDS)

    def test_foidite_is_named_without_an_outline_of_its_own(self):
        """Its every edge is drawn by a neighbour or by the frame."""
        assert "Foidite" not in _VOLCANIC_FIELDS
        for a, b in (((41, 0), (41, 3)), ((41, 3), (41, 7)),
                     ((41, 7), (45, 9.4)), ((45, 9.4), (48.4, 11.5)),
                     ((48.4, 11.5), (52.5, 14))):
            assert tuple(sorted((a, b))) in edges(_VOLCANIC_FIELDS)

    def test_the_foidite_label_sits_in_its_own_region(self):
        x, y = _FOIDITE_LABEL
        assert x < 41            # left of the picrobasalt / tephrite edge
        assert 3 < y < 16

    def test_the_phonolite_closing_edge_stays_invisible(self):
        """It is a retrace, and it must remain collinear with the real
        boundary or it will draw a line across the field."""
        assert on_segment((52.5, 14), (50, 15.083), (57.6, 11.7), tol=0.05)


class TestPlutonicFields:
    def test_every_field_label_matches_an_outline(self):
        assert not set(TASPlutonic.field_label_pos) - set(_PLUTONIC_FIELDS)

    def test_the_foid_boundaries_are_shared_with_the_volcanic_diagram(self):
        """Middlemost keeps Le Bas's vertices where the two overlap."""
        shared = edges(_PLUTONIC_FIELDS) & edges(_VOLCANIC_FIELDS)
        assert ((45, 9.4), (49.4, 7.3)) in shared or (
            (49.4, 7.3), (45, 9.4)) in shared


class TestRendering:
    def frame(self):
        from birds.diagrams.templates.base import PlotOptions
        from birds.plot_style import PlotStyle
        from matplotlib.figure import Figure
        return Figure(figsize=(8, 6)), PlotStyle(), PlotOptions()

    def texts(self, key, qapp):
        fig, style, opts = self.frame()
        get_diagram(key).plot(fig, None, style, opts)
        out = {t.get_text() for t in fig.axes[0].texts}
        fig.clf()
        return out

    def test_foidite_reaches_the_volcanic_plot(self, qapp):
        assert "Foidite" in self.texts("tas_volcanic", qapp)

    def test_every_volcanic_field_is_named_on_the_plot(self, qapp):
        drawn = self.texts("tas_volcanic", qapp)
        for name in _VOLCANIC_FIELDS:
            assert name in drawn, name

    def test_every_plutonic_field_is_named_on_the_plot(self, qapp):
        drawn = self.texts("tas_plutonic", qapp)
        for name in _PLUTONIC_FIELDS:
            assert name in drawn, name

    def test_samples_are_plotted_against_total_alkalis(self, qapp):
        df = pd.DataFrame({"SiO2": [50.0], "Na2O": [2.0], "K2O": [1.0]})
        xs, ys = get_diagram("tas_volcanic")._compute_xy(df)
        assert float(xs.iloc[0]) == pytest.approx(50.0)
        assert float(ys.iloc[0]) == pytest.approx(3.0)

    def test_missing_columns_are_reported_not_guessed(self, qapp):
        xs, ys = get_diagram("tas_volcanic")._compute_xy(
            pd.DataFrame({"SiO2": [50.0]}))
        assert xs is None and ys is None


# ==========================================================================
# Naming a composition
# ==========================================================================

import numpy as np  # noqa: E402

from birds.diagrams.templates.tas import (  # noqa: E402
    CLASSIFY_ALKALI_MAX,
    CLASSIFY_SIO2_RANGE,
    _VOLCANIC_PATHS,
    _VOLCANIC_SPLITS,
    _volcanic_regions,
)


class TestClassificationRegions:
    def test_the_regions_come_from_the_drawn_outlines(self):
        """Eleven of the fourteen outlines close on their own and are
        reused as they stand, so a name cannot drift from the picture.
        Only Rhyolite, Trachyte/Trachydacite and Phonolite are rebuilt —
        plus Foidite, which has no outline of its own."""
        regions = _volcanic_regions()
        reused = [n for n, v in _VOLCANIC_FIELDS.items()
                  if list(v) == regions.get(n)]
        assert len(reused) == 11
        assert len(_VOLCANIC_FIELDS) - len(reused) == 3

    def test_the_only_closed_ones_are_those_the_frame_bounds(self):
        regions = _volcanic_regions()
        rebuilt = {n for n, v in regions.items()
                   if list(_VOLCANIC_FIELDS.get(n, [])) != v}
        assert rebuilt == {"Foidite", "Rhyolite",
                           "Trachyte /\nTrachydacite", "Phonolite"}

    def test_every_field_has_a_region(self):
        assert set(_volcanic_regions()) == set(_VOLCANIC_FIELDS) | {"Foidite"}

    def test_the_regions_tile_the_plane(self):
        """No composition may fall in a gap or in two fields at once."""
        xs = np.arange(CLASSIFY_SIO2_RANGE[0] + 0.13,
                       CLASSIFY_SIO2_RANGE[1], 0.37)
        ys = np.arange(0.11, CLASSIFY_ALKALI_MAX, 0.19)
        gaps, overlaps = [], []
        for x in xs:
            pts = np.column_stack([np.full_like(ys, x), ys])
            counts = np.zeros(len(ys), dtype=int)
            for _name, path in _VOLCANIC_PATHS:
                counts += path.contains_points(pts)
            for y, c in zip(ys, counts):
                if c == 0:
                    gaps.append((round(x, 2), round(y, 2)))
                elif c > 1:
                    overlaps.append((round(x, 2), round(y, 2)))
        assert not gaps, gaps[:5]
        assert not overlaps, overlaps[:5]

    def test_every_split_key_names_a_real_field(self):
        """A key carrying the layout newline would silently never fire."""
        names = {clean for clean, _ in _VOLCANIC_PATHS}
        assert not set(_VOLCANIC_SPLITS) - names

    def test_no_region_name_keeps_its_layout_newline(self):
        assert not [n for n, _ in _VOLCANIC_PATHS if "\n" in n]


class TestClassify:
    @pytest.mark.parametrize("sio2,alkalis,expected", [
        (42, 2.0, "Picrobasalt"),
        (50, 3.0, "Basalt"),
        (54, 3.0, "Basaltic andesite"),
        (60, 3.5, "Andesite"),
        (70, 4.0, "Dacite"),
        (74, 9.0, "Rhyolite"),
        (48, 6.0, "Trachybasalt"),
        (55, 7.0, "Basaltic trachyandesite"),
        (59, 8.5, "Trachyandesite"),
        (66, 12.0, "Trachyte / Trachydacite"),
        (43, 6.0, "Tephrite / Basanite"),
        (48, 9.5, "Phonotephrite"),
        (52, 11.5, "Tephriphonolite"),
        (56, 14.5, "Phonolite"),
        (38, 10.0, "Foidite"),
        (36, 1.0, "Foidite"),
    ])
    def test_names(self, sio2, alkalis, expected):
        assert TASVolcanic.classify(sio2, alkalis) == expected

    def test_the_published_label_position_names_its_own_field(self):
        """Each label sits inside the field it names — a strong check,
        since the positions were placed by eye and the regions by rule."""
        for name, (x, y) in TASVolcanic.field_label_pos.items():
            assert TASVolcanic.classify(x, y) == name.replace("\n", " ")

    def test_foidite_label_names_foidite(self):
        assert TASVolcanic.classify(*_FOIDITE_LABEL) == "Foidite"

    def test_olivine_splits_tephrite_from_basanite(self):
        assert TASVolcanic.classify(43, 6, normative_ol=5) == "Tephrite"
        assert TASVolcanic.classify(43, 6, normative_ol=15) == "Basanite"

    def test_quartz_splits_trachyte_from_trachydacite(self):
        assert TASVolcanic.classify(66, 12, normative_q=10) == "Trachyte"
        assert TASVolcanic.classify(66, 12, normative_q=30) == "Trachydacite"

    def test_the_pair_is_kept_whole_without_the_normative_value(self):
        """Saying both beats guessing one."""
        assert TASVolcanic.classify(43, 6) == "Tephrite / Basanite"
        assert TASVolcanic.classify(66, 12) == "Trachyte / Trachydacite"
        assert TASVolcanic.classify(43, 6, normative_ol=float("nan")) == \
            "Tephrite / Basanite"

    def test_a_normative_value_for_the_wrong_field_is_ignored(self):
        assert TASVolcanic.classify(50, 3, normative_q=30) == "Basalt"

    def test_off_the_diagram_gives_no_name(self):
        assert TASVolcanic.classify(25, 5) == ""
        assert TASVolcanic.classify(50, CLASSIFY_ALKALI_MAX + 1) == ""

    def test_blank_input_gives_no_name(self):
        assert TASVolcanic.classify(float("nan"), 5) == ""
        assert TASVolcanic.classify(50, float("nan")) == ""

    def test_the_domain_reaches_past_the_published_frame(self):
        """A rare ultra-alkaline analysis should still get a name."""
        assert CLASSIFY_ALKALI_MAX > 16
        assert TASVolcanic.classify(50, 17) != ""


class TestClassifyFrame:
    def test_names_every_row(self):
        df = pd.DataFrame({"SiO2": [50, 70, 38], "Na2O": [2, 2.5, 6],
                           "K2O": [1, 1.5, 4]})
        assert TASVolcanic.classify_frame(df).tolist() == [
            "Basalt", "Dacite", "Foidite"]

    def test_it_uses_the_norm_columns_when_they_are_there(self):
        df = pd.DataFrame({"SiO2": [43, 66], "Na2O": [4, 7],
                           "K2O": [2, 5], "Ol": [15, 0], "Q": [0, 30]})
        assert TASVolcanic.classify_frame(df).tolist() == [
            "Basanite", "Trachydacite"]

    def test_it_keeps_the_index(self):
        df = pd.DataFrame({"SiO2": [50], "Na2O": [2], "K2O": [1]},
                          index=["sample-7"])
        assert TASVolcanic.classify_frame(df).index.tolist() == ["sample-7"]

    def test_missing_columns_give_blanks_not_an_error(self):
        out = TASVolcanic.classify_frame(pd.DataFrame({"SiO2": [50]}))
        assert out.tolist() == [""]

    def test_a_blank_row_gives_a_blank_name(self):
        df = pd.DataFrame({"SiO2": [50, None], "Na2O": [2, 2],
                           "K2O": [1, 1]})
        assert TASVolcanic.classify_frame(df).tolist() == ["Basalt", ""]

    def test_it_agrees_with_the_scalar_form(self):
        rng = np.random.default_rng(0)
        si = rng.uniform(35, 78, 200)
        alk = rng.uniform(0, 15, 200)
        df = pd.DataFrame({"SiO2": si, "Na2O": alk / 2, "K2O": alk / 2})
        batch = TASVolcanic.classify_frame(df).tolist()
        one = [TASVolcanic.classify(a, b) for a, b in zip(si, alk)]
        assert batch == one
