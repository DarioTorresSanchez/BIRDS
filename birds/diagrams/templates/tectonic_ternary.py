"""Ternary tectonic discrimination diagrams."""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

from ...normalizations import TIO2_WT_TO_TI_PPM
from .base import (
    PlotOptions,
    TernaryDiagram,
    draw_ternary_frame,
    resolve_column,
    inverse_logratio as _inverse_logratio,
    scatter_groups,
    ternary_to_xy,
    ternary_xy,
)


# ---------------------------------------------------------------------------
# Common ternary helper
# ---------------------------------------------------------------------------

def _draw_ternary_fields(ax, fields: dict, *, linewidth: float = 0.9,
                          fontsize: float = 8,
                          label_overrides: Optional[dict] = None) -> None:
    """Draw labelled polygonal fields specified in ternary (A, B, C) %.

    ``label_overrides`` lets a caller pin a specific field's label at a
    chosen ternary position instead of the polygon centroid — useful for
    long, thin or trapezoidal fields whose visual middle does not match
    their mathematical centroid.  Keys are field names; values are
    ``(a, b, c)`` tuples in the same convention as the polygon vertices.
    """
    overrides = label_overrides or {}
    for name, abc in fields.items():
        a, b, c = zip(*abc)
        x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
        poly = Polygon(list(zip(x, y)), closed=True, fill=False,
                       edgecolor="#444", linewidth=linewidth, alpha=0.85,
                       zorder=2)
        ax.add_patch(poly)
        if name in overrides:
            oa, ob, oc = overrides[name]
            ox, oy = ternary_to_xy(pd.Series([oa]), pd.Series([ob]),
                                    pd.Series([oc]))
            cx, cy = float(ox.iloc[0]), float(oy.iloc[0])
        else:
            cx = float(np.mean(x))
            cy = float(np.mean(y))
        ax.text(cx, cy, name, ha="center", va="center",
                fontsize=fontsize, color="#333", alpha=0.9, zorder=3)


def _plot_ternary_data(ax, df: Optional[pd.DataFrame], plot_style,
                        abc_fn: Callable[[pd.DataFrame],
                                          Optional[Tuple[pd.Series, pd.Series, pd.Series]]]) -> None:
    """Scatter the grouped samples using a callable that returns (a, b, c).

    For the Petrography view's modal triangles; the diagrams here are
    :class:`TernaryDiagram` and scatter through their own mapping.
    """
    scatter_groups(ax, df, plot_style, lambda d: ternary_xy(abc_fn(d)))


# ---------------------------------------------------------------------------
# Wood (1980) Th – Hf/3 – Ta — refined by Vermeesch (2006a)
# ---------------------------------------------------------------------------

_WOOD_FIELDS = {
    # Approximate field boundaries in (Th, Hf/3, Ta) percent
    "N-MORB":        [(15, 65, 20), (5, 80, 15), (5, 90, 5), (15, 80, 5)],
    "E-MORB & WP\ntholeiites": [(15, 80, 5), (35, 60, 5), (35, 45, 20), (15, 65, 20)],
    "Within-plate\nalkaline":  [(35, 60, 5), (60, 35, 5), (60, 25, 15), (35, 45, 20)],
    "Volcanic arc\nbasalts":   [(60, 35, 5), (95, 0, 5), (75, 0, 25), (60, 25, 15)],
}


# ---------------------------------------------------------------------------
# Cabanis & Lecolle (1989) La/10 – Y/15 – Nb/8
# ---------------------------------------------------------------------------
#
# C. R. Acad. Sci. 309 (II), 2023-2029, as redrawn with Verma's (2010)
# reassessment in Rollinson & Pease (2021) Figure 5.4d.
#
# **The apexes were wrong**, which is the error that matters: this put
# La/10 at the top where both sources put Y/15, so every sample was
# placed by the wrong pair of coordinates.  Published order is Y/15 at
# the apex, La/10 bottom left, Nb/8 bottom right.
#
# The seven fields that used to be drawn were quadrilaterals typed in
# ternary percent, approximating by eye a figure whose real structure
# is three wedges from the apex.  The two boundaries were measured
# twice, from two independent figures by two different pipelines:
#
#   source                                left (IAB|CRB)   right (CRB|OIB+MORB)
#   Rollinson & Pease Fig. 5.4d           61.9 / 38.1      37.9 / 62.1
#   the 1989 diagram as reproduced        62.0 / 38.0      38.1 / 61.9
#
# as La/10 and Nb/8 percent where the line meets the base.  They agree
# to 0.2 %, and the pair is symmetric about the median from the apex to
# 0.1 %, so 62/38 and 38/62 are used.  Each fits a straight line to
# about 1 px rms over 182 sampled rows.
#
# **The two do not both start at the apex.**  Only the left one
# reaches it, to within a pixel in both figures; the right one begins
# part of the way down it.  That branch is the one place the two
# sources disagree -- Y/15 = 89.4 % in Figure 5.4d against 80.9 % in
# the original -- and it matters only for very Y-rich samples, above
# which there is no CRB wedge to fall into.  Figure 5.4d's value is
# used, with the rest of its version.
#
# Cabanis & Lecolle's own figure subdivides the three further --
# calc-alkaline and VAT on the left, continental in the middle,
# N-MORB, E-MORB, alkaline and intercontinental rifts on the right --
# with short cross-lines.  Those are not drawn.  Verma (2010) measured
# how well they hold and the answer is: not well, outside the arc
# field.  Rollinson & Pease, redrawing the diagram with that
# reassessment in hand, show only these three.
#
# The grouping checks out against the original's own labels.  Placing
# each of them in ternary coordinates and reading La/(La+Nb):
# calc-alkali 77.6 % and VAT 76.7 % fall in the arc wedge, continental
# 49.9 % in the middle one, and E-MORB 23.7 %, alkaline 20.2 % and
# intercontinental rifts 20.0 % in the right one -- which is exactly
# how Figure 5.4d collapses them.

#: Where each boundary meets the La/10 – Nb/8 edge, in percent.
CABANIS_BOUNDARIES = {
    "IAB|CRB": (62.0, 38.0),
    "CRB|OIB+MORB": (38.0, 62.0),
}

#: Y/15 percent at which the right boundary leaves the left one.
CABANIS_BRANCH_Y = 89.4

#: The same branch measured on the original figure, for the record.
CABANIS_BRANCH_Y_ORIGINAL = 80.9

#: Verma's (2010) success rates, as Figure 5.4d labels the three fields.
CABANIS_FIELDS = (
    ("IAB\n(>74 %)", 100.0, 62.0),
    ("CRB\n(42 %)", 62.0, 38.0),
    ("OIB + MORB\n(29–62 %)", 38.0, 0.0),
)


class CabanisLecolle1989(TernaryDiagram):
    key = "cabanis_lecolle_1989"
    title = "La/10 – Y/15 – Nb/8 — Cabanis & Lecolle (1989)"
    citation = ("Cabanis & Lecolle (1989), on the boundaries Rollinson "
                "& Pease (2021) Fig. 5.4d draws after Verma's (2010) "
                "reassessment. Two straight lines from the Y/15 apex "
                "to La/10 = 62 % and 38 % on the opposite edge, "
                "measured from that figure and from the original and "
                "agreeing to 0.2 %. Reliable only for island-arc and "
                "back-arc basalts, better than 74 %; continental rift "
                "basalts are misclassified 42 % of the time and "
                "OIB + MORB between 29 and 62 %. Cabanis & Lecolle's "
                "finer subdivisions are not drawn — those are the ones "
                "the reassessment found do not hold.")

    def _abc(self, df):
        la = resolve_column(df, ["La"])
        y = resolve_column(df, ["Y"])
        nb = resolve_column(df, ["Nb"])
        if not (la and y and nb):
            return None
        # (apex, left, right) = (Y/15, La/10, Nb/8)
        return (pd.to_numeric(df[y], errors="coerce") / 15.0,
                pd.to_numeric(df[la], errors="coerce") / 10.0,
                pd.to_numeric(df[nb], errors="coerce") / 8.0)

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Y / 15", "La / 10", "Nb / 8"),
                           options.x_axis)
        def xy(a, b, c):
            x, y = ternary_to_xy(pd.Series([a]), pd.Series([b]),
                                 pd.Series([c]))
            return float(x.iloc[0]), float(y.iloc[0])

        # Left boundary: apex to La/10 = 62 % on the opposite edge.
        la_l, nb_l = CABANIS_BOUNDARIES["IAB|CRB"]
        apex = xy(1.0, 0.0, 0.0)
        left_base = xy(0.0, la_l, nb_l)
        ax.plot(*zip(apex, left_base), color="#444", lw=1.0, zorder=2)

        # Right boundary: it leaves the left one part of the way down,
        # rather than starting at the apex.
        f = CABANIS_BRANCH_Y / 100.0
        branch = xy(f * 100.0, (1 - f) * la_l, (1 - f) * nb_l)
        la_r, nb_r = CABANIS_BOUNDARIES["CRB|OIB+MORB"]
        ax.plot(*zip(branch, xy(0.0, la_r, nb_r)),
                color="#444", lw=1.0, zorder=2)
        for name, la_hi, la_lo in CABANIS_FIELDS:
            # label each wedge near the base, at the middle of its span
            mid_la = (la_hi + la_lo) / 2.0
            lx, ly = ternary_to_xy(pd.Series([12.0]), pd.Series([mid_la]),
                                   pd.Series([100.0 - mid_la]))
            ax.text(float(lx.iloc[0]), float(ly.iloc[0]), name,
                    ha="center", va="center", fontsize=8, color="#333",
                    zorder=3)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


# ---------------------------------------------------------------------------
# Vermeesch (2006a) — five refined ternary discriminants
# (Earth-Sci. Rev. 75, fig. 1-5). Coordinates are approximate field
# centroids reproducing the topology of the published diagrams.
# ---------------------------------------------------------------------------

def _ti_ppm(df: pd.DataFrame) -> Optional[pd.Series]:
    """Return Ti in ppm — direct column or computed from TiO2 wt%."""
    ti = resolve_column(df, ["Ti"])
    if ti is not None:
        return pd.to_numeric(df[ti], errors="coerce")
    ox = resolve_column(df, ["TiO2"])
    if ox is None:
        return None
    return pd.to_numeric(df[ox], errors="coerce") * TIO2_WT_TO_TI_PPM


_VRMS_NA_NB_SR = {
    "IAB":  [(5, 5, 90), (15, 5, 80), (20, 15, 65), (10, 15, 75)],
    "MORB": [(15, 35, 50), (25, 30, 45), (30, 45, 25), (20, 50, 30)],
    "OIB":  [(35, 40, 25), (45, 35, 20), (50, 25, 25), (40, 25, 35)],
}


class Vermeesch2006NaNbSr(TernaryDiagram):
    key = "vermeesch_NaNbSr"
    title = "Na − 25 Nb − Sr — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a). Mafic discrimination using Na (wt% × "
                "100), 25 × Nb (ppm) and Sr (ppm). Best for OIB and IAB; "
                "MORB intermediate.")

    def _abc(self, df):
        na_ox = resolve_column(df, ["Na2O"])
        nb = resolve_column(df, ["Nb"])
        sr = resolve_column(df, ["Sr"])
        if not (na_ox and nb and sr):
            return None
        na = pd.to_numeric(df[na_ox], errors="coerce") * 0.7419 * 1e4 / 100.0
        return (na,
                25.0 * pd.to_numeric(df[nb], errors="coerce"),
                pd.to_numeric(df[sr], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Na/100", "25 Nb", "Sr"), options.x_axis)
        _draw_ternary_fields(ax, _VRMS_NA_NB_SR)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


# ---------------------------------------------------------------------------
# Vermeesch (2006a) — the three log-ratio LDA ternaries
# ---------------------------------------------------------------------------
#
# These are not diagrams with fields drawn on them.  Vermeesch runs a
# linear discriminant analysis in log-ratio space, where the decision
# boundaries come out straight, and then maps them back to the ternary,
# where they come out curved: "the transformed decision boundaries are
# no longer linear, but curved."  Tracing a polygon off the printed
# triangle would approximate a curve that can simply be computed.
#
# Each boundary is a ray from the triple point, and Table 6 gives four
# anchor points per diagram in log-ratio coordinates: node 3 is the
# triple point, nodes 1, 2 and 4 the three ray ends.  The axes are
# ln(B/A) and ln(C/A) with A the top apex, which is the ordinary
# additive log-ratio, so the inverse is a softmax.
#
# The logarithm is natural, not base ten.  The paper writes "log"
# throughout, but with ln a reference N-MORB, OIB and IAB land inside
# their own published clouds on every one of the three figures, while
# log10 bunches all three near the origin outside them.

#: ``(top, left, right)`` apex labels, matching the published figures.
#: The frame helper puts the first apex at the top.
_LDA_SI_TI_SR_APICES = ("Ti/40", "Si/1000", "Sr")
_LDA_EU_LU_SR_APICES = ("500 Lu", "100 Eu", "Sr")
_LDA_TI_V_SC_APICES = ("Ti/50", "V", "5 Sc")

#: Anchor points from Vermeesch (2006a) Table 6, as ``(ln(B/A),
#: ln(C/A))``.  ``triple`` is node 3; each boundary runs from it to the
#: node given, and separates the two fields named.
_LDA_SI_TI_SR = {
    "axes": ("ln(Si / 25 Ti)", "ln(40 Sr / Ti)"),
    "triple": (-0.05, 0.39),
    "boundaries": (
        ((-0.2, 2.98), ("IAB", "OIB")),     # node 2
        ((-1.26, -2.15), ("OIB", "MORB")),  # node 1
        ((2.0, -0.77), ("MORB", "IAB")),    # node 4
    ),
}

_LDA_EU_LU_SR = {
    "axes": ("ln(Eu / 5 Lu)", "ln(Sr / 500 Lu)"),
    "triple": (0.03, 1.0),
    "boundaries": (
        ((0.5, 2.33), ("IAB", "OIB")),      # node 2
        ((-1.23, -1.0), ("IAB", "MORB")),   # node 1
        ((-0.61, -5.0), ("MORB", "OIB")),   # node 4
    ),
}

_LDA_TI_V_SC = {
    "axes": ("ln(50 V / Ti)", "ln(250 Sc / Ti)"),
    "triple": (0.57, -0.39),
    "boundaries": (
        ((1.1, 2.0), ("MORB", "IAB")),      # node 2
        ((-2.0, -0.54), ("MORB", "OIB")),   # node 1
        ((2.0, -1.41), ("OIB", "IAB")),     # node 4
    ),
}

#: How far along each ray to walk, in log-ratio units.  The inverse
#: log-ratio map never leaves the simplex, so a boundary only reaches
#: the triangle's edge in the limit; by 40 the curve is within a pixel
#: of it at any sane figure size.
_LDA_RAY_REACH = 40.0

#: 1 wt.% oxide to ppm of the element, from the mass ratios.
_SI_WT_TO_PPM = 4674.0
_TI_WT_TO_PPM = 5993.4


def _lda_boundary_xy(triple, end):
    """The ternary path of one decision boundary.

    Straight in log-ratio space, curved here.  Sampled on a squared
    parameter so the points bunch near the triple point, where the
    curvature is, and thin out along the tail, where it is straight.
    """
    t = np.linspace(0.0, 1.0, 240) ** 2 * _LDA_RAY_REACH
    direction = np.array(end, dtype=float) - np.array(triple, dtype=float)
    norm = np.hypot(*direction)
    if norm == 0:
        return np.array([]), np.array([])
    direction = direction / norm
    xs = triple[0] + direction[0] * t
    ys = triple[1] + direction[1] * t
    a, b, c = _inverse_logratio(xs, ys)
    return ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))


def _lda_field_label_xy(spec, field):
    """A point inside *field*, on the bisector of the sector it owns.

    Placed by angle rather than by hand so a label cannot drift away
    from the field it names when an anchor point is corrected.
    """
    triple = spec["triple"]
    angles = []
    for end, pair in spec["boundaries"]:
        if field in pair:
            angles.append(np.arctan2(end[1] - triple[1],
                                     end[0] - triple[0]))
    if len(angles) != 2:
        return None
    low, high = sorted(angles)
    # The sector between the two rays is the one that does not contain
    # the third; a span over pi means the field wraps the other way.
    middle = (low + high) / 2.0
    if high - low > np.pi:
        middle += np.pi
    radius = 2.2
    a, b, c = _inverse_logratio(triple[0] + radius * np.cos(middle),
                                triple[1] + radius * np.sin(middle))
    x, y = ternary_to_xy(pd.Series([float(a)]), pd.Series([float(b)]),
                         pd.Series([float(c)]))
    return float(x.iloc[0]), float(y.iloc[0])


def _draw_lda_boundaries(ax, spec) -> None:
    for end, _pair in spec["boundaries"]:
        x, y = _lda_boundary_xy(spec["triple"], end)
        ax.plot(x, y, color="#444", linewidth=0.9, alpha=0.9, zorder=2)
    for field in sorted({f for _e, pair in spec["boundaries"] for f in pair}):
        placed = _lda_field_label_xy(spec, field)
        if placed is None:
            continue
        ax.text(placed[0], placed[1], field, ha="center", va="center",
                fontsize=8, color="#333", alpha=0.9, zorder=3)


class _VermeeschLDATernary(TernaryDiagram):
    """Shared plumbing for the three log-ratio LDA ternaries."""

    spec: dict = {}
    apices: Tuple[str, str, str] = ("", "", "")

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, self.apices, options.x_axis)
        _draw_lda_boundaries(ax, self.spec)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


class Vermeesch2006SiTiSr(_VermeeschLDATernary):
    key = "vermeesch_SiTiSr"
    title = "Si/1000 − Ti/40 − Sr — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a) Figure 42, the best of all ternary "
                "linear discriminant analyses he tried.  Si (from SiO2) "
                "over 1000, Ti (from TiO2) over 40 and Sr, all in ppm.  "
                "The boundaries are an LDA in ln(Si/25Ti) — ln(40Sr/Ti) "
                "space, mapped back here, so they curve; the anchor "
                "points are from his Table 6.")
    spec = _LDA_SI_TI_SR
    apices = _LDA_SI_TI_SR_APICES

    def _abc(self, df):
        si_ox = resolve_column(df, ["SiO2"])
        ti_ox = resolve_column(df, ["TiO2"])
        sr = resolve_column(df, ["Sr"])
        if not (si_ox and ti_ox and sr):
            return None
        si = pd.to_numeric(df[si_ox], errors="coerce") * _SI_WT_TO_PPM
        ti = pd.to_numeric(df[ti_ox], errors="coerce") * _TI_WT_TO_PPM
        return (ti / 40.0, si / 1000.0,
                pd.to_numeric(df[sr], errors="coerce"))


class Vermeesch2006EuLuSr(_VermeeschLDATernary):
    key = "vermeesch_EuLuSr"
    title = "100 Eu − 500 Lu − Sr — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a) Figure 43.  100 × Eu, 500 × Lu and "
                "Sr, all in ppm.  The boundaries are an LDA in "
                "ln(Eu/5Lu) — ln(Sr/500Lu) space, mapped back here, so "
                "they curve; the anchor points are from his Table 6.  "
                "Needs Lu, which many routine analyses omit.")
    spec = _LDA_EU_LU_SR
    apices = _LDA_EU_LU_SR_APICES

    def _abc(self, df):
        eu = resolve_column(df, ["Eu"])
        lu = resolve_column(df, ["Lu"])
        sr = resolve_column(df, ["Sr"])
        if not (eu and lu and sr):
            return None
        return (500.0 * pd.to_numeric(df[lu], errors="coerce"),
                100.0 * pd.to_numeric(df[eu], errors="coerce"),
                pd.to_numeric(df[sr], errors="coerce"))


class Vermeesch2006VTiSc(_VermeeschLDATernary):
    key = "vermeesch_VTiSc"
    title = "V − Ti/50 − 5 Sc — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a) Figure 44, his best ternary LDA using "
                "only incompatible elements, which makes it the one to "
                "reach for when alteration is a worry.  V, Ti (from "
                "TiO2) over 50 and 5 × Sc, all in ppm.  The boundaries "
                "are an LDA in ln(50V/Ti) — ln(250Sc/Ti) space, mapped "
                "back here, so they curve; the anchor points are from "
                "his Table 6.")
    spec = _LDA_TI_V_SC
    apices = _LDA_TI_V_SC_APICES

    def _abc(self, df):
        v = resolve_column(df, ["V"])
        ti_ox = resolve_column(df, ["TiO2"])
        sc = resolve_column(df, ["Sc"])
        if not (v and ti_ox and sc):
            return None
        ti = pd.to_numeric(df[ti_ox], errors="coerce") * _TI_WT_TO_PPM
        return (ti / 50.0,
                pd.to_numeric(df[v], errors="coerce"),
                5.0 * pd.to_numeric(df[sc], errors="coerce"))


_VRMS_SM_TI_V = {
    "IAB":  [(10, 10, 80), (25, 15, 60), (20, 25, 55), (10, 20, 70)],
    "MORB": [(20, 30, 50), (35, 35, 30), (40, 25, 35), (25, 25, 50)],
    "OIB":  [(45, 35, 20), (55, 30, 15), (50, 20, 30), (35, 25, 40)],
}


# Still a hand-drawn envelope: Figure 46 is a QDA, whose boundaries
# are conics in log-ratio space rather than the straight rays of
# Table 6, so it has no anchor points to rebuild it from.
class Vermeesch2006SmTiV(TernaryDiagram):
    key = "vermeesch_SmTiV"
    title = "50 Sm − Ti/50 − V — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a). 50 × Sm, Ti ppm / 50 and V ppm. "
                "Last of the 5 refined ternaries, useful when Sr / "
                "Lu data are missing.")

    def _abc(self, df):
        sm = resolve_column(df, ["Sm"])
        v = resolve_column(df, ["V"])
        ti = _ti_ppm(df)
        if not (sm and v) or ti is None:
            return None
        return (50.0 * pd.to_numeric(df[sm], errors="coerce"),
                ti / 50.0,
                pd.to_numeric(df[v], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("50 Sm", "Ti/50", "V"), options.x_axis)
        _draw_ternary_fields(ax, _VRMS_SM_TI_V)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


#: Vermeesch (2006a) Table 6 and Figure 41b, the LDA that replaces the
#: fields Wood drew by eye.  Same shape as the other three ternaries --
#: node 3 the triple point, the rest ray ends -- and the same axes,
#: ln(B/A) and ln(C/A) with A the top apex.
#:
#: Node 2 is used with both its signs flipped.  Table 6 prints it as
#: (1.43, -1.5), which puts it on the opposite side of the origin from
#: where Figure 41b draws it, and sends a reference N-MORB into the OIB
#: field.  Measuring the figure settles it: detecting the four numbered
#: discs and calibrating the axes on nodes 1, 3 and 4 -- which do agree
#: with the table, and reproduce node 3 as (-0.076, -0.864) against a
#: published (-0.07, -0.86) -- puts node 2 at (-1.44, +1.50), matching
#: the printed magnitudes to a hundredth with both signs reversed.
_LDA_TH_TA_HF_APICES = ("Hf/3", "Th", "Ta")

_LDA_TH_TA_HF = {
    "axes": ("ln(3 Th / Hf)", "ln(3 Ta / Hf)"),
    "triple": (-0.07, -0.86),
    "boundaries": (
        ((-1.43, 1.5), ("OIB", "MORB")),    # node 2, signs corrected
        ((-1.49, -2.48), ("MORB", "IAB")),  # node 1
        ((2.81, 1.0), ("IAB", "OIB")),      # node 4
    ),
}


class Wood1980ThHfTa(_VermeeschLDATernary):
    key = "wood_1980_ThHfTa"
    title = "Th – Hf/3 – Ta — Wood (1980) / Vermeesch (2006a)"
    citation = ("Wood (1980), with the decision boundaries Vermeesch "
                "(2006a) derived for it by linear discriminant analysis "
                "(his Figure 41b) in place of the fields Wood drew by "
                "eye.  Th, Hf/3 and Ta in ppm.  The analysis is done in "
                "ln(3Th/Hf) — ln(3Ta/Hf) space, where the boundaries are "
                "straight; mapped back here they curve.  One of the four "
                "anchor points of his Table 6 is used with its signs "
                "corrected against the figure — see the note at the "
                "coefficients.")
    spec = _LDA_TH_TA_HF
    apices = _LDA_TH_TA_HF_APICES

    def _abc(self, df):
        th = resolve_column(df, ["Th"])
        hf = resolve_column(df, ["Hf"])
        ta = resolve_column(df, ["Ta"])
        if not (th and hf and ta):
            return None
        return (pd.to_numeric(df[hf], errors="coerce") / 3.0,
                pd.to_numeric(df[th], errors="coerce"),
                pd.to_numeric(df[ta], errors="coerce"))


# ---------------------------------------------------------------------------
# Harris, Pearce & Tindle (1986) Rb/30 – Hf – Ta×3
# ---------------------------------------------------------------------------
#
# Geol. Soc. London Spec. Publ. 19, 67-81, Figure 6.  Two errors, and
# the first is the one that matters.
#
# **The apexes were wrong.**  Hf sat at the top with Rb bottom left;
# Figure 6 puts **Rb/30 at the apex**, Hf bottom left and Ta×3 bottom
# right.  **And the divisor was wrong**: Rb/10 where the figure, its
# caption and Figure 7 all say Rb/30.  Between them every sample was
# placed by the wrong pair of coordinates and with one of them three
# times too large.  The four fields under it were quadrilaterals typed
# in ternary percent.
#
# Measured off Figure 6.  Its triangle is equilateral to 0.04 % -- the
# fitted edges give a height of 1739.6 px against 1738.9 for the
# measured width -- which is what fixes the calibration.  The dotted
# boundaries separate cleanly from the data because the two populations
# do not overlap in size: 241 components of 32-64 px for the dots of
# the boundaries, 133 of 256-4096 px for the triangles and squares.
# RANSAC over the dots recovers five segments carrying 245 of 260 dots,
# each straight to 0.5-4.3 px rms against a triangle 2008 px wide.
#
# The near-vertical boundary does curve slightly.  Fitting its 69 dots
# with a parabola instead of a line improves the residual from 4.0 to
# 2.8 px and bows by 9.3 px at most, which is 0.46 % of the triangle's
# width -- so it is drawn straight.
#
# It has no single triple point.  Two branches leave it about four
# units apart: the VA|WP boundary at Rb/30 = 26.2 % and the III|WP one
# at 22.5 %, with a short stem of the vertical between them.  That is
# what the figure draws, and fitting the three as concurrent lines put
# their pairwise intersections up to 11 units apart, which is how the
# stem was noticed.

#: Vertices of the boundary network, in (Rb/30, Hf, Ta×3) percent.
_HARRIS_BEND = (71.8, 13.7, 14.5)        # vertical meets the Group-II top
_HARRIS_VA_WP_BRANCH = (26.2, 40.5, 33.3)
_HARRIS_III_WP_BRANCH = (22.5, 42.4, 35.2)
_HARRIS_GREEN_START = (50.3, 26.8, 22.9)  # II|III leaves the vertical

#: The five dotted segments of Figure 6, each a polyline.  Ends that
#: run off to a side of the triangle are extended to meet it.
HARRIS_BOUNDARIES = {
    "VA | Group II–III": (_HARRIS_BEND, _HARRIS_VA_WP_BRANCH,
                          _HARRIS_III_WP_BRANCH),
    "top of Group II": (_HARRIS_BEND, (76.7, 0.0, 23.3)),
    "Group II | Group III": (_HARRIS_GREEN_START, (29.6, 0.0, 70.4)),
    "Group III | WP": (_HARRIS_III_WP_BRANCH, (18.8, 0.0, 81.2)),
    "VA | WP": (_HARRIS_VA_WP_BRANCH, (0.0, 82.1, 17.9)),
}

#: Where Figure 6 puts each of its four labels, measured with the rest.
#: Group II is syn-collision and Group III late or post-collision, per
#: the paper's summary; the figure itself prints only the numerals.
HARRIS_FIELD_LABELS = (
    ("VA", 32.0, 61.7, 6.4),
    ("Group II\n(syn-collision)", 60.0, 11.0, 29.1),
    ("Group III\n(late/post-collision)", 36.3, 20.3, 43.4),
    ("WP", 5.3, 51.9, 42.7),
)


class Harris1986HfRbTa(TernaryDiagram):
    key = "harris_1986_HfRbTa"
    title = "Rb/30 − Hf − Ta×3 — Harris et al. (1986)"
    citation = ("Harris, Pearce & Tindle (1986) Fig. 6, boundaries "
                "measured off the published figure. Apexes are Rb/30 "
                "at the top, Hf bottom left and 3 × Ta bottom right, "
                "all in ppm. Separates volcanic-arc (VA) and "
                "within-plate (WP) granites from the two collision "
                "groups: Group II, the syn-collision peraluminous "
                "leucogranites, and Group III, the late or "
                "post-collision calc-alkaline intrusions, which the "
                "paper says can be told from volcanic-arc rocks only "
                "by their higher Ta/Hf and Ta/Zr.")

    def _abc(self, df):
        hf = resolve_column(df, ["Hf"])
        rb = resolve_column(df, ["Rb"])
        ta = resolve_column(df, ["Ta"])
        if not (hf and rb and ta):
            return None
        # (apex, left, right) = (Rb/30, Hf, Ta x 3)
        return (pd.to_numeric(df[rb], errors="coerce") / 30.0,
                pd.to_numeric(df[hf], errors="coerce"),
                3.0 * pd.to_numeric(df[ta], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Rb / 30", "Hf", "3 Ta"), options.x_axis)
        for poly in HARRIS_BOUNDARIES.values():
            a, b, c = zip(*poly)
            x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
            ax.plot(x, y, color="#444", lw=0.9, linestyle=(0, (2, 2)),
                    zorder=2)
        for name, a, b, c in HARRIS_FIELD_LABELS:
            x, y = ternary_to_xy(pd.Series([a]), pd.Series([b]),
                                 pd.Series([c]))
            ax.text(float(x.iloc[0]), float(y.iloc[0]), name,
                    ha="center", va="center", fontsize=7.5, color="#333",
                    zorder=3)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()
