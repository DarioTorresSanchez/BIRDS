"""Ternary tectonic discrimination diagrams."""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd

from ...normalizations import TIO2_WT_TO_TI_PPM
from .base import (
    PlotOptions,
    TernaryDiagram,
    draw_ternary_frame,
    resolve_column,
    inverse_logratio as _inverse_logratio,
    ternary_to_xy,
)


# ---------------------------------------------------------------------------
# Common ternary helper
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Vermeesch (2006a) — the two QDA ternaries
# ---------------------------------------------------------------------------
#
# A quadratic discriminant analysis gives each class its own covariance,
# so its decision boundaries are conics in log-ratio space, and without
# the class covariances -- which the paper does not print -- they cannot
# be computed.  They can be read, though: Figures 34 and 35 draw them as
# vector Bezier curves.  Each control point below was taken from the
# PDF's own paths and turned into ternary fractions, which loses
# nothing, since a Bezier curve keeps its shape through the affine map
# from the page to the triangle.  These replace fields that had been
# sketched as quadrilaterals, with the triangle turned the wrong way up.
#
# Checked three ways (tests/test_vermeesch_qda_ternaries.py):
#
# * the same boundaries as Figures 45a and 46a draw them in log-ratio
#   space, mapped back with the natural logarithm, lie on these to a
#   median 0.3 % of the triangle's side -- base ten misses by 5-24 %,
#   so "log" in the paper is ln here too;
# * the test samples plotted in Figures 45b and 46b, classified by these
#   fields, give the paper's own test table (its Table 5): all 61 for
#   Na-Nb-Sr, and 82 of 85 for Ti-V-Sm, whose other three lie on the
#   drawn line, 0.05-0.31 % of the triangle's side from it -- about
#   the width of the stroke;
# * the apices are the paper's: 25 Nb and Ti/50 at the top.
#
# Each segment is a cubic Bezier, ``(top, left, right)`` fractions.

#: Figure 34.  MORB is a closed loop; OIB a lobe that leaves it and
#: returns to it; every other composition is IAB, on either side.
_QDA_NA_NB_SR = {
    "apices": ("25 Nb", "Na/100", "Sr"),
    "oib_lobe": (
        ((0.3772, 0.2694, 0.3534), (0.3594, 0.2522, 0.3884),
         (0.3425, 0.2254, 0.4321), (0.3385, 0.2020, 0.4595)),
        ((0.3385, 0.2020, 0.4595), (0.3297, 0.1496, 0.5208),
         (0.5008, 0.0596, 0.4396), (0.5497, 0.0520, 0.3983)),
        ((0.5497, 0.0520, 0.3983), (0.6212, 0.0410, 0.3378),
         (0.8174, 0.0129, 0.1697), (0.8174, 0.0257, 0.1569)),
        ((0.8174, 0.0257, 0.1569), (0.8174, 0.0457, 0.1369),
         (0.7848, 0.0664, 0.1488), (0.7527, 0.0939, 0.1534)),
    ),
    "morb": (
        ((0.7623, 0.0910, 0.1467), (0.8292, 0.0605, 0.1103),
         (0.9032, 0.0247, 0.0722), (0.9077, 0.0340, 0.0583)),
        ((0.9077, 0.0340, 0.0583), (0.9108, 0.0405, 0.0487),
         (0.8098, 0.1158, 0.0744), (0.7623, 0.1532, 0.0845)),
        ((0.7623, 0.1532, 0.0845), (0.7371, 0.1731, 0.0899),
         (0.5706, 0.2987, 0.1307), (0.3844, 0.4680, 0.1476)),
        ((0.3844, 0.4680, 0.1476), (0.2192, 0.6182, 0.1626),
         (0.0402, 0.8215, 0.1383), (0.0234, 0.8173, 0.1593)),
        ((0.0234, 0.8173, 0.1593), (0.0030, 0.8123, 0.1847),
         (0.0160, 0.7444, 0.2395), (0.0341, 0.6911, 0.2748)),
        ((0.0341, 0.6911, 0.2748), (0.0736, 0.5744, 0.3520),
         (0.1058, 0.4817, 0.4125), (0.2077, 0.3939, 0.3983)),
        ((0.2077, 0.3939, 0.3983), (0.2905, 0.3227, 0.3868),
         (0.3642, 0.2747, 0.3611), (0.4093, 0.2533, 0.3374)),
        ((0.4093, 0.2533, 0.3374), (0.4711, 0.2239, 0.3050),
         (0.7163, 0.1120, 0.1717), (0.7623, 0.0910, 0.1467)),
    ),
    "labels": (("IAB", (0.311, 0.615, 0.074)), ("MORB", (0.254, 0.475, 0.272)),
               ("OIB", (0.512, 0.140, 0.348)), ("IAB", (0.139, 0.228, 0.633))),
}

#: Figure 35.  OIB is a dome against the 50 Sm - Ti/50 edge; MORB a
#: small lens under its right end; below them, IAB.
_QDA_TI_V_SM = {
    "apices": ("Ti/50", "50 Sm", "V"),
    "oib": (
        ((0.3322, 0.6665, 0.0013), (0.5022, 0.4637, 0.0341),
         (0.6030, 0.3829, 0.0140), (0.6051, 0.2656, 0.1293)),
        ((0.6051, 0.2656, 0.1293), (0.6065, 0.1854, 0.2081),
         (0.3869, 0.1262, 0.4869), (0.3509, 0.1479, 0.5013)),
        ((0.3509, 0.1479, 0.5013), (0.3328, 0.1587, 0.5085),
         (0.3100, 0.2093, 0.4807), (0.3192, 0.2275, 0.4533)),
        ((0.3192, 0.2275, 0.4533), (0.3290, 0.2471, 0.4239),
         (0.3606, 0.2823, 0.3571), (0.3363, 0.3406, 0.3230)),
        ((0.3363, 0.3406, 0.3230), (0.3240, 0.3702, 0.3058),
         (0.3040, 0.3731, 0.3230), (0.2796, 0.4109, 0.3095)),
        ((0.2796, 0.4109, 0.3095), (0.2578, 0.4447, 0.2975),
         (0.2366, 0.6928, 0.0706), (0.0747, 0.9237, 0.0016)),
    ),
    "morb_lower": (
        ((0.2791, 0.4106, 0.3103), (0.2444, 0.3340, 0.4217),
         (0.1871, 0.2076, 0.6054), (0.2245, 0.1903, 0.5852)),
        ((0.2245, 0.1903, 0.5852), (0.2531, 0.1771, 0.5698),
         (0.2588, 0.1790, 0.5622), (0.3160, 0.2004, 0.4836)),
    ),
    "labels": (("OIB", (0.431, 0.383, 0.186)), ("MORB", (0.281, 0.292, 0.426)),
               ("IAB", (0.109, 0.454, 0.437))),
}


def _bezier_fractions(segments, n: int = 48) -> np.ndarray:
    """Sample cubic Bezier segments given as ternary fractions."""
    t = np.linspace(0.0, 1.0, n)[:, None]
    parts = []
    for p0, p1, p2, p3 in segments:
        p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
        parts.append(((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1
                     + 3 * (1 - t) * t * t * p2 + t ** 3 * p3)
    return np.vstack(parts)


def _nearest(points: np.ndarray, target) -> int:
    return int(np.argmin(((points - np.asarray(target, float)) ** 2).sum(1)))


def qda_fields(spec: dict) -> dict:
    """The fields of a QDA ternary as closed outlines of ``(top, left,
    right)`` fractions: MORB and OIB; IAB is everywhere else."""
    if "oib_lobe" in spec:
        morb = _bezier_fractions(spec["morb"])
        lobe = _bezier_fractions(spec["oib_lobe"])
        # The lobe leaves the MORB loop and comes back to it: close it
        # along the stretch of loop between its two ends.
        i, j = sorted((_nearest(morb, lobe[-1]), _nearest(morb, lobe[0])))
        arc = morb[i:j + 1]
        if np.linalg.norm(arc[0] - lobe[-1]) > np.linalg.norm(arc[-1] - lobe[-1]):
            arc = arc[::-1]
        return {"MORB": morb, "OIB": np.vstack([lobe, arc])}
    dome = _bezier_fractions(spec["oib"])
    lower = _bezier_fractions(spec["morb_lower"])
    # The dome starts and ends on the 50 Sm - Ti/50 edge: it closes
    # along it.  The lens is its lower curve and the stretch of the dome
    # above it.
    i, j = _nearest(dome, lower[-1]), _nearest(dome, lower[0])
    lens = np.vstack([lower, dome[min(i, j):max(i, j) + 1]])
    return {"MORB": lens, "OIB": np.vstack([dome, dome[:1]])}


def _fraction_xy(fractions: np.ndarray):
    x, y = ternary_to_xy(pd.Series(fractions[:, 0]),
                         pd.Series(fractions[:, 1]),
                         pd.Series(fractions[:, 2]))
    return np.column_stack([x.to_numpy(), y.to_numpy()])


def qda_field(spec: dict, top, left, right) -> pd.Series:
    """The field -- IAB, MORB or OIB -- each composition falls in; ""
    where a value is missing."""
    from matplotlib.path import Path as _Path
    top, left, right = (pd.Series(v, dtype=float).reset_index(drop=True)
                        for v in (top, left, right))
    x, y = ternary_to_xy(top, left, right)
    points = np.column_stack([x.to_numpy(), y.to_numpy()])
    fields = {name: _Path(_fraction_xy(outline))
              for name, outline in qda_fields(spec).items()}
    out = []
    for p in points:
        if not np.all(np.isfinite(p)):
            out.append("")
        elif fields["MORB"].contains_point(p):
            out.append("MORB")
        elif fields["OIB"].contains_point(p):
            out.append("OIB")
        else:
            out.append("IAB")
    return pd.Series(out, dtype=object)


def _draw_qda_fields(ax, spec) -> None:
    for outline in qda_fields(spec).values():
        xy = _fraction_xy(outline)
        ax.plot(xy[:, 0], xy[:, 1], color="#444", linewidth=0.9,
                alpha=0.9, zorder=2)
    for name, (a, b, c) in spec["labels"]:
        (x, y), = _fraction_xy(np.array([[a, b, c]]))
        ax.text(x, y, name, ha="center", va="center", fontsize=8,
                color="#333", alpha=0.9, zorder=3)


class _VermeeschQDATernary(TernaryDiagram):
    """Shared plumbing for the two QDA ternaries."""

    spec: dict = {}

    def classify_frame(self, df: pd.DataFrame) -> pd.Series:
        """The QDA field of every sample; "" without the elements."""
        abc = self._abc(df)
        if abc is None:
            return pd.Series("", index=df.index, dtype=object)
        out = qda_field(self.spec, *abc)
        out.index = df.index
        return out

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, self.spec["apices"], options.x_axis)
        _draw_qda_fields(ax, self.spec)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


class Vermeesch2006NaNbSr(_VermeeschQDATernary):
    key = "vermeesch_NaNbSr"
    title = "Na/100 − 25 Nb − Sr — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a) Figure 34: the best quadratic "
                "discriminant ternary, Na (ppm)/100, 25 × Nb and Sr (ppm). "
                "Its boundaries are read from the paper's vector figure; "
                "they reproduce the paper's test classification. Na is "
                "mobile: trust it only on fresh basalt.")
    spec = _QDA_NA_NB_SR

    def _abc(self, df):
        na_ox = resolve_column(df, ["Na2O"])
        nb = resolve_column(df, ["Nb"])
        sr = resolve_column(df, ["Sr"])
        if not (na_ox and nb and sr):
            return None
        na = pd.to_numeric(df[na_ox], errors="coerce") * 0.7419 * 1e4 / 100.0
        return (25.0 * pd.to_numeric(df[nb], errors="coerce"),
                na,
                pd.to_numeric(df[sr], errors="coerce"))


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


class Vermeesch2006SmTiV(_VermeeschQDATernary):
    key = "vermeesch_SmTiV"
    title = "Ti/50 − 50 Sm − V — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a) Figure 35: the best quadratic "
                "discriminant ternary from immobile elements, Ti (ppm)/50, "
                "50 × Sm and V (ppm). Its boundaries are read from the "
                "paper's vector figure; they reproduce its test "
                "classification. Useful when Sr or Lu are missing.")
    spec = _QDA_TI_V_SM

    def _abc(self, df):
        sm = resolve_column(df, ["Sm"])
        v = resolve_column(df, ["V"])
        ti = _ti_ppm(df)
        if not (sm and v) or ti is None:
            return None
        return (ti / 50.0,
                50.0 * pd.to_numeric(df[sm], errors="coerce"),
                pd.to_numeric(df[v], errors="coerce"))


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
