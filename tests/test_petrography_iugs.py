"""The modal classification diagrams, against the IUGS definitions.

Every boundary is a percentage the IUGS fixed, checked against the BGS
Rock Classification Scheme, Volume 1 (Gillespie & Styles 1999, RR
99-06), which reproduces the IUGS figures.  What the check found:

* QAPF placed every sample at 0.5 A + P + 0.5 Q, with the A corner at
  x = 0: half the alkali feldspar too far right, a granite on
  granodiorite and an alkali-feldspar syenite on monzonite.
* QAPF drew the P/(A+P) lines through the quartzolite and quartz-rich
  fields, and 10/35/65/90 through the foid fields where they are
  10/50/90; the volcanic diagram was the plutonic one renamed, with
  names the IUGS does not use.
* Gabbroic and ultramafic strips opened by invented amounts instead of
  being the constant 5 % lines; the gabbroic diagram never found the
  template's plagioclase (P_mode), and a blank Px_mode hid every row.
* The tuff diagram cited Schmid (1981) for a scheme that is not his,
  and its dividers were rays where the figure draws lines of constant
  crystal content.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.collections import PathCollection
from matplotlib.figure import Figure
from matplotlib.path import Path

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import PlotOptions, ternary_to_xy
from birds.diagrams.templates.petrography import (
    GABBRO_FIELDS,
    QAPF_PLUTONIC_FIELDS,
    QAPF_VOLCANIC_FIELDS,
    SCHMID_TUFF_FIELDS,
    TUFF_FIELDS,
    ULTRAMAFIC_FIELDS,
    _box_outline,
    _GABBRO_LABELS,
    _polygon_centroid,
    _SCHMID_LABELS,
    _ULTRAMAFIC_LABELS,
    field_of,
    qapf_field,
    qapf_xy,
)
from birds.plot_style import PlotStyle

PLUTONIC = get_diagram("streckeisen_qapf_plutonic")
VOLCANIC = get_diagram("streckeisen_qapf_volcanic")


def _drawn(fig):
    pts = [np.asarray(c.get_offsets(), float) for c in fig.axes[0].collections
           if isinstance(c, PathCollection)]
    return np.vstack(pts) if pts else np.empty((0, 2))


def _render(key, df):
    fig = Figure()
    get_diagram(key).plot(fig, df, PlotStyle(), PlotOptions())
    return fig


# ---------------------------------------------------------------------------
# QAPF: the definitions
# ---------------------------------------------------------------------------

def _boxes(fields):
    return {num: (s0, s1, r0, r1) for num, _n, s0, s1, r0, r1 in fields if num}


def test_plutonic_fields_are_streckeisens():
    """BGS RR 99-06 Figures 11-12."""
    box = _boxes(QAPF_PLUTONIC_FIELDS)
    assert box["1a"] == (90, 100, 0, 100) and box["1b"] == (60, 90, 0, 100)
    for row, (s0, s1) in (("", (20, 60)), ("*", (5, 20)), ("", (0, 5)),
                          ("'", (-10, 0))):
        cuts = (0, 10, 35, 65, 90, 100)
        numbers = (("2", "3", "4", "5") if (s0, s1) == (20, 60) else
                   tuple(f"{n}{row}" for n in (6, 7, 8, 9, 10)))
        if (s0, s1) == (20, 60):
            cuts = (0, 10, 65, 90, 100)          # 3a/3b only dashed
        for n, r0, r1 in zip(numbers, cuts, cuts[1:]):
            assert box[n] == (s0, s1, r0, r1), n
    for n, r0, r1 in (("11", 0, 10), ("12", 10, 50), ("13", 50, 90),
                      ("14", 90, 100)):
        assert box[n] == (-60, -10, r0, r1), n
    assert box["15"] == (-100, -60, 0, 100)


def test_volcanic_fields_are_not_the_plutonic_ones_renamed():
    """BGS RR 99-06 Figure 19 (after Streckeisen 1978)."""
    names = {n: name for n, name, *_ in QAPF_VOLCANIC_FIELDS if n}
    box = _boxes(QAPF_VOLCANIC_FIELDS)
    assert box["4–5"] == (20, 60, 65, 100) and names["4–5"] == "dacite"
    assert box["9–10"] == (-10, 20, 65, 100)
    assert names["9–10"] == "basalt / andesite"
    assert box["12"] == (-60, -10, 10, 50)
    assert names["12"] == "tephritic phonolite"
    assert box["15a"] == (-90, -60, 0, 50) and box["15b"] == (-90, -60, 50, 100)
    assert box["15c"] == (-100, -90, 0, 100)
    # Nothing above Q 60 has a volcanic name.
    assert qapf_field(QAPF_VOLCANIC_FIELDS, 75, 40) == ("", "")
    for wrong in ("quartzolite", "phonolitic trachyte", "tephritic latite",
                  "tephritic basalt", "quartz andesite"):
        assert not any(wrong in name for name in names.values()), wrong


@pytest.mark.parametrize("fields", [QAPF_PLUTONIC_FIELDS,
                                    QAPF_VOLCANIC_FIELDS])
def test_the_fields_tile_the_double_triangle(fields):
    for s in np.linspace(-99.5, 99.5, 200):
        for r in np.linspace(0.25, 99.75, 100):
            hits = [f for f in fields
                    if f[2] <= s < f[3] and f[4] <= r < f[5]]
            assert len(hits) == 1, (s, r, [h[0] for h in hits])


@pytest.mark.parametrize("fields", [QAPF_PLUTONIC_FIELDS,
                                    QAPF_VOLCANIC_FIELDS])
def test_each_number_sits_in_its_own_field(fields):
    for number, _name, s0, s1, r0, r1 in fields:
        if not number:
            continue
        sr = _box_outline(s0, s1, r0, r1)
        x, y = qapf_xy([v[0] for v in sr], [v[1] for v in sr])
        assert Path(np.column_stack([x, y])).contains_point(
            _polygon_centroid(x, y)), number


# ---------------------------------------------------------------------------
# QAPF: where samples go
# ---------------------------------------------------------------------------

def _mode(q=0.0, a=0.0, p=0.0, f=0.0):
    return pd.DataFrame({"Q_mode": [q], "A_mode": [a], "P_mode": [p],
                         "F_mode": [f]})


@pytest.mark.parametrize("q, a, p, f, xy", [
    (0, 100, 0, 0, (0.0, 0.0)),               # was drawn at x = 0.5
    (0, 0, 100, 0, (1.0, 0.0)),
    (100, 0, 0, 0, (0.5, np.sqrt(3) / 2)),
    (0, 0, 0, 100, (0.5, -np.sqrt(3) / 2)),
    (30, 40, 30, 0, (0.45, 0.3 * np.sqrt(3) / 2)),   # was at x = 0.65
])
def test_corners_and_a_granite_sit_where_they_should(q, a, p, f, xy):
    x, y = PLUTONIC._compute_xy(_mode(q, a, p, f))
    assert (x.iloc[0], y.iloc[0]) == pytest.approx(xy)


@pytest.mark.parametrize("q, a, p, f, plutonic, volcanic", [
    (30, 40, 30, 0, "granite", "rhyolite"),
    (30, 0, 70, 0, "tonalite", "dacite"),
    (0, 95, 5, 0, "alkali feldspar syenite", "alkali feldspar trachyte"),
    (2, 70, 28, 0, "syenite", "trachyte"),
    (10, 20, 70, 0, "quartz monzodiorite / quartz monzogabbro",
     "basalt / andesite"),
    (0, 65, 5, 30, "foid syenite", "phonolite"),
    (0, 30, 40, 30, "foid monzodiorite / foid monzogabbro",
     "phonolitic basanite (Ol > 10 %) / phonolitic tephrite"),
    (0, 15, 5, 80, "foidolite", "phonolitic foidite"),
    (0, 1, 1, 98, "foidolite", "foidite"),
])
def test_modes_are_named_as_the_iugs_names_them(q, a, p, f, plutonic,
                                                 volcanic):
    assert PLUTONIC.classify(q, a, p, f)[1] == plutonic
    assert VOLCANIC.classify(q, a, p, f)[1] == volcanic


def test_quartz_and_a_feldspathoid_together_are_left_off_and_named():
    df = pd.concat([_mode(30, 40, 30), _mode(3, 50, 45, 2)],
                   ignore_index=True)
    fig = _render("streckeisen_qapf_plutonic", df)
    assert len(_drawn(fig)) == 1
    assert any("both quartz and a feldspathoid" in t.get_text()
               for t in fig.axes[0].texts)
    assert PLUTONIC.classify(3, 50, 45, 2) == ("", "")


def test_a_blank_mineral_counts_as_absent():
    """A granite with F_mode left blank used to vanish."""
    df = _mode(30, 40, 30).assign(F_mode=np.nan)
    assert PLUTONIC.classify_frame(df)["name"].iloc[0] == "granite"
    blank = _mode().iloc[[0]].assign(Q_mode=np.nan, A_mode=np.nan,
                                     P_mode=np.nan, F_mode=np.nan)
    x, _y = PLUTONIC._compute_xy(blank)
    assert x.isna().all()


def test_the_plot_draws_what_the_mapping_gives():
    df = pd.concat([_mode(30, 40, 30), _mode(0, 65, 5, 30),
                    _mode(5, 5, 90)], ignore_index=True)
    x, y = PLUTONIC._compute_xy(df)
    np.testing.assert_allclose(_drawn(_render("streckeisen_qapf_plutonic",
                                              df)),
                               np.column_stack([x, y]))


# ---------------------------------------------------------------------------
# Gabbroic, ultramafic and tuff triangles
# ---------------------------------------------------------------------------

def _tiles(fields):
    """Every interior point of the triangle in exactly one field."""
    paths = []
    for vertices in fields.values():
        a, b, c = zip(*vertices)
        x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
        paths.append(Path(np.column_stack([x, y])))
    rng = np.random.default_rng(1)
    abc = rng.dirichlet((1, 1, 1), 4000) * 100
    x, y = ternary_to_xy(pd.Series(abc[:, 0]), pd.Series(abc[:, 1]),
                         pd.Series(abc[:, 2]))
    pts = np.column_stack([x, y])
    counts = sum(p.contains_points(pts).astype(int) for p in paths)
    # Points within a hair of a boundary may sit in neither or both.
    return np.mean(counts == 1)


@pytest.mark.parametrize("fields", [GABBRO_FIELDS, ULTRAMAFIC_FIELDS,
                                    TUFF_FIELDS, SCHMID_TUFF_FIELDS])
def test_the_fields_tile_the_triangle(fields):
    assert _tiles(fields) > 0.999


def test_the_gabbroic_strips_are_the_5_percent_lines():
    """BGS Figure 13: under 5 % olivine, under 5 % pyroxene."""
    inner_gabbro = [v for v in GABBRO_FIELDS["gabbro / gabbronorite / norite"]
                    if v[2] > 0]
    inner_troctolite = [v for v in GABBRO_FIELDS["troctolite"] if v[1] > 0]
    assert all(v[2] == 5 for v in inner_gabbro)
    assert all(v[1] == 5 for v in inner_troctolite)
    assert (90, 5, 5) in inner_gabbro and (10, 85, 5) in inner_gabbro


def test_the_ultramafic_strips_are_the_5_percent_lines():
    """BGS Figure 16: harzburgite under 5 % Cpx, wehrlite under 5 % Opx,
    both from the middle of the Ol 90 line to the Ol 5 line."""
    for name, index in (("harzburgite", 2), ("olivine orthopyroxenite", 2),
                        ("wehrlite", 1), ("olivine clinopyroxenite", 1)):
        inner = [v for v in ULTRAMAFIC_FIELDS[name] if v[index] > 0]
        assert all(v[index] == 5 for v in inner), name
    assert (90, 5, 5) in ULTRAMAFIC_FIELDS["lherzolite"]
    assert (5, 90, 5) in ULTRAMAFIC_FIELDS["websterite"]


@pytest.mark.parametrize("fields, labels", [
    (GABBRO_FIELDS, _GABBRO_LABELS),
    (ULTRAMAFIC_FIELDS, _ULTRAMAFIC_LABELS),
    (SCHMID_TUFF_FIELDS, _SCHMID_LABELS),
])
def test_each_label_points_into_its_own_field(fields, labels):
    for text, abc, _outside, _ha in labels:
        name = field_of(fields, abc)
        assert name is not None, text
        assert name.split(" / ")[0].split()[0] in text.replace("\n", " "), (
            text, name)


@pytest.mark.parametrize("v, c, lithic, name", [
    (70, 20, 10, "vitric tuff"), (20, 60, 20, "crystal tuff"),
    (25, 25, 50, "lithic tuff"), (40, 35, 25, "vitric tuff"),
])
def test_schmid_names_a_tuff_for_its_dominant_component(v, c, lithic, name):
    assert field_of(SCHMID_TUFF_FIELDS, (v, c, lithic)) == name


@pytest.mark.parametrize("lithic, crystal, vitric, name", [
    (40, 30, 30, "Lithic-\ncrystal tuff"),    # was lithic-vitric: ray at 12.5
    (40, 20, 40, "Lithic-\nvitric tuff"),
    (15, 30, 55, "Crystal-\nlithic tuff"),
    (5, 55, 40, "Crystal\ntuff"),
    (5, 40, 55, "Crystal-\nvitric tuff"),
    (5, 15, 80, "Vitric-\ncrystal tuff"),
    (5, 5, 90, "Vitric\ntuff"),
])
def test_the_banded_tuff_divides_on_constant_crystal(lithic, crystal,
                                                     vitric, name):
    assert field_of(TUFF_FIELDS, (lithic, crystal, vitric)) == name


def test_the_gabbroic_diagram_reads_the_template_columns():
    template = pd.DataFrame({"Sample_Name": ["g"], "P_mode": [60.0],
                             "Ol_mode": [3.0], "Opx_mode": [10.0],
                             "Cpx_mode": [25.0], "Px_mode": [np.nan]})
    a, b, c = get_diagram("gabbro_pl_px_ol")._abc(template)
    assert (a.iloc[0], b.iloc[0], c.iloc[0]) == (60.0, 35.0, 3.0)
    assert len(_drawn(_render("gabbro_pl_px_ol", template))) == 1


def test_the_tuff_diagrams_say_whose_they_are():
    assert "Schmid (1981)" in get_diagram("tuff_schmid_1981").citation
    banded = get_diagram("tuff_crystal_vitric_lithic").citation
    assert "not identified" in banded and "use Schmid (1981)" in banded
