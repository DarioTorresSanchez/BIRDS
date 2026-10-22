"""The three earlier basic-rock DF sets of Verma's group.

Agrawal et al. (2004), adjusted majors; Verma et al. (2006), major
log-ratios; Agrawal et al. (2008), La-Sm-Yb-Nb over Th.  Each has five
panels over IAB, CRB, OIB and MORB, and each paper gives its fields as
the end points of their boundaries in the figure captions.  The
functions are checked against the authors' Statistica sheet in
``test_verma_statistica_sheet.py``; here, the fields.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates import verma_multidim as M
from birds.diagrams.templates.verma_coefficients import A04, A04_FIELDS

KEYS = ("agrawal_2004_basic", "verma_2006_basic", "agrawal_2008_basic")


def _panels():
    for key in KEYS:
        diagram = get_diagram(key)
        for panel_key, *groups in diagram.panel_groups:
            yield key, panel_key, tuple(groups)


PANELS = list(_panels())


def _area(verts):
    v = np.asarray(verts, float)
    x, y = v[:, 0], v[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


@pytest.mark.parametrize("key, panel, groups", PANELS)
def test_the_fields_are_the_panels_groups_and_fill_the_frame(key, panel,
                                                              groups):
    regions = M.field_regions(get_diagram(key).fields[panel])
    assert sorted(regions) == sorted(groups)
    assert sum(_area(v) for v in regions.values()) == pytest.approx(256.0)


@pytest.mark.parametrize("key, panel, groups", PANELS)
def test_each_boundary_divides_the_two_fields_it_names(key, panel, groups):
    geom = get_diagram(key).fields[panel]
    for p, q, pair in M.field_segments(geom):
        p, q = np.asarray(p, float), np.asarray(q, float)
        mid = (p + q) / 2
        normal = np.array([q[1] - p[1], p[0] - q[0]])
        normal /= np.linalg.norm(normal)
        sides = M.field_of(geom, [mid[0] + 0.05 * normal[0],
                                  mid[0] - 0.05 * normal[0]],
                           [mid[1] + 0.05 * normal[1],
                            mid[1] - 0.05 * normal[1]])
        assert set(sides) == set(pair), (panel, pair, list(sides))


#: Where each paper's figure prints its field names, read off the page.
FIGURE_LABELS = {
    ("agrawal_2004_basic", "IAB_CRB_OIB_MORB"):
        {"MORB": (-2.5, 4.5), "OIB": (3.5, 3.5), "IAB": (-4, -1),
         "CRB": (1, -3)},
    ("agrawal_2004_basic", "IAB_CRB_OIB"):
        {"IAB": (-3, 3.5), "OIB": (2.5, 3.5), "CRB": (0, -4.5)},
    ("agrawal_2004_basic", "IAB_CRB_MORB"):
        {"CRB": (-4, 3.5), "IAB": (3, 3.5), "MORB": (0, -4)},
    ("agrawal_2004_basic", "IAB_OIB_MORB"):
        {"IAB": (-4, 0), "MORB": (-1, 4.5), "OIB": (4.5, 0)},
    ("agrawal_2004_basic", "CRB_OIB_MORB"):
        {"MORB": (-4, 1), "OIB": (4, 3.5), "CRB": (4, -4)},
    ("verma_2006_basic", "IAB_CRB_OIB_MORB"):
        {"CRB": (0, 5), "IAB": (5, 0), "OIB": (-5, 2.5), "MORB": (-3, -4)},
    ("verma_2006_basic", "IAB_CRB_OIB"):
        {"IAB": (-5, 0), "CRB": (1, 5), "OIB": (4, -2.5)},
    ("verma_2006_basic", "IAB_CRB_MORB"):
        {"MORB": (-4, 3), "CRB": (3, 4), "IAB": (3, -4)},
    ("verma_2006_basic", "IAB_OIB_MORB"):
        {"IAB": (-5, 2.5), "OIB": (4, 2), "MORB": (0, -4.5)},
    ("verma_2006_basic", "CRB_OIB_MORB"):
        {"MORB": (-5, -1), "OIB": (-1, 5), "CRB": (3, -3)},
    ("agrawal_2008_basic", "IAB_CRBOIB_MORB"):
        {"MORB": (-4, 6), "IAB": (-5, -5), "CRB+OIB": (4, 1)},
    ("agrawal_2008_basic", "IAB_CRB_OIB"):
        {"IAB": (-5, 1), "OIB": (2, 4), "CRB": (0, -5)},
    ("agrawal_2008_basic", "IAB_CRB_MORB"):
        {"MORB": (0, 5), "CRB": (5, -1), "IAB": (-5, -5)},
    ("agrawal_2008_basic", "IAB_OIB_MORB"):
        {"MORB": (0, 5), "OIB": (5, 0), "IAB": (-4, -5)},
    ("agrawal_2008_basic", "CRB_OIB_MORB"):
        {"OIB": (-4, 3), "MORB": (4, 1), "CRB": (-3, -4)},
}


@pytest.mark.parametrize("key, panel", list(FIGURE_LABELS))
def test_each_field_lies_where_the_figure_names_it(key, panel):
    geom = get_diagram(key).fields[panel]
    labels = FIGURE_LABELS[(key, panel)]
    got = M.field_of(geom, [p[0] for p in labels.values()],
                     [p[1] for p in labels.values()])
    assert list(got) == list(labels)


@pytest.mark.parametrize("key, panel", [
    ("agrawal_2004_basic", "IAB_CRB_OIB_MORB"),
    ("verma_2006_basic", "IAB_CRB_OIB_MORB"),
])
def test_four_groups_meet_at_two_triple_points(key, panel):
    """Figure 2 of 2004 and Figure 5 of 2006: three boundaries end at
    each of two points inside the frame, one boundary joins them."""
    ends = [tuple(pt) for p, q, _ in M.field_segments(
        get_diagram(key).fields[panel]) for pt in (p, q)]
    inner = {pt for pt in ends if max(abs(pt[0]), abs(pt[1])) < 7.99}
    assert len(inner) == 2
    assert all(ends.count(pt) == 3 for pt in inner)


def test_the_2004_ib_crb_boundary_closes_at_its_triple_point():
    """The caption ends it at (-0.52, -0.99); the other two boundaries
    through that point end at (-0.52, -1.03)."""
    segments = A04_FIELDS["IAB_CRB_OIB_MORB"]["segments"]
    iab_crb = next(s for s in segments if s[2] == ("IAB", "CRB"))
    assert iab_crb[1] == (-0.52, -1.03)


# ---------------------------------------------------------------------------
# The functions
# ---------------------------------------------------------------------------

def test_the_2004_functions_take_the_oxides_themselves():
    """No log-ratio: DF = constant + sum of coefficient x oxide, and an
    oxide at zero is a value, not a gap."""
    sample = {"SiO2": 49.0, "TiO2": 1.5, "Al2O3": 15.0, "Fe2O3": 2.0,
              "FeO": 8.0, "MnO": 0.17, "MgO": 8.0, "CaO": 11.0,
              "Na2O": 2.5, "K2O": 0.0, "P2O5": 0.2}
    df = pd.DataFrame([sample])
    coef = A04["DF1_IAB_CRB_OIB_MORB"]
    lr = M._logratios_for_coef(df, coef)
    expected = coef.intercept + sum(c * sample[p]
                                    for p, c in zip(coef.parts, coef.coefs))
    assert M._apply_df(lr, coef).iloc[0] == pytest.approx(expected)


def test_a_missing_oxide_is_named(full_df, plot_style):
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    df = full_df.drop(columns=[c for c in full_df.columns
                               if c.startswith("MnO")])
    diagram = get_diagram("agrawal_2004_basic")
    assert diagram._compute_xy_for_panel(diagram.panels[0], df) == (None,
                                                                    None)
    fig = Figure()
    diagram.plot(fig, df, plot_style, PlotOptions())
    message = next(t.get_text() for t in fig.axes[0].texts
                   if t.get_text().startswith("Missing"))
    assert "MnO" in message and "None" not in message


@pytest.mark.parametrize("key", KEYS)
def test_classify_panel_names_the_field_of_each_sample(key, full_df):
    diagram = get_diagram(key)
    for panel_key, *groups in diagram.panel_groups:
        got = diagram.classify_panel(full_df, panel_key)
        assert len(got) == len(full_df)
        assert set(got) - {""} <= set(groups)


@pytest.mark.parametrize("key", KEYS)
def test_the_plot_draws_five_panels_with_their_fields(key, full_df,
                                                      plot_style):
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    fig = Figure(figsize=(12, 8))
    get_diagram(key).plot(fig, full_df, plot_style, PlotOptions())
    panels = [ax for ax in fig.axes if ax.get_title()]
    assert len(panels) == 5
    for ax, (_panel, *groups) in zip(panels, get_diagram(key).panel_groups):
        assert set(groups) <= {t.get_text() for t in ax.texts}
        assert ax.get_xlim() == (-8, 8) and ax.get_ylim() == (-8, 8)


@pytest.mark.parametrize("key", KEYS)
def test_they_are_in_both_mafic_menus(key):
    from birds.diagrams.catalog import TECTONIC_PLUTONIC, TECTONIC_VOLCANIC
    for menu in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC):
        assert key in [k for _label, k in menu["Mafic"]]
