"""Ternary tectonic discrimination diagrams."""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

from .base import (
    Diagram,
    PlotOptions,
    draw_ternary_frame,
    get_groups,
    resolve_column,
    ternary_to_xy,
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
    """Scatter the grouped samples using a callable that returns (a, b, c)."""
    if df is None or df.empty:
        return
    for label, sub, gs in get_groups(df, plot_style):
        abc = abc_fn(sub)
        if abc is None:
            continue
        a, b, c = abc
        mask = a.notna() & b.notna() & c.notna() & (a + b + c > 0)
        a, b, c = a[mask], b[mask], c[mask]
        if a.empty:
            continue
        x, y = ternary_to_xy(a, b, c)
        ax.scatter(x, y, s=plot_style.point_size ** 2,
                   alpha=plot_style.alpha,
                   c=gs.color if gs else "#1f77b4",
                   marker=gs.marker if gs else "o",
                   label=label, edgecolors="black", linewidths=0.4,
                   zorder=4)


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


class Wood1980ThHfTa(Diagram):
    key = "wood_1980_ThHfTa"
    title = "Th – Hf/3 – Ta — Wood (1980) / Vermeesch (2006a)"
    citation = ("Wood (1980); refined by Vermeesch (2006a). 74 % success "
                "for IAB; 100 % for OIB.")

    def _abc(self, df):
        th = resolve_column(df, ["Th"])
        hf = resolve_column(df, ["Hf"])
        ta = resolve_column(df, ["Ta"])
        if not (th and hf and ta):
            return None
        return (pd.to_numeric(df[th], errors="coerce"),
                pd.to_numeric(df[hf], errors="coerce") / 3.0,
                pd.to_numeric(df[ta], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Th", "Hf / 3", "Ta"), options.x_axis)

        # Draw fields
        for name, abc in _WOOD_FIELDS.items():
            a, b, c = zip(*abc)
            x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
            poly = Polygon(list(zip(x, y)), closed=True, fill=False,
                           edgecolor="#444", linewidth=0.9, alpha=0.85,
                           zorder=2)
            ax.add_patch(poly)
            cx = float(np.mean(x))
            cy = float(np.mean(y))
            ax.text(cx, cy, name, ha="center", va="center", fontsize=8,
                    color="#333", alpha=0.9, zorder=3)

        # Plot data
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()


# ---------------------------------------------------------------------------
# Cabanis & Lecolle (1989) La/10 – Y/15 – Nb/8
# ---------------------------------------------------------------------------

_CABANIS_FIELDS = {
    "Calc-alkaline\nbasalt":  [(25, 55, 20), (35, 50, 15), (45, 35, 20), (30, 45, 25)],
    "Tholeiite\n(VA)":        [(10, 70, 20), (25, 55, 20), (30, 45, 25), (15, 60, 25)],
    "N-MORB":                 [(5, 75, 20), (10, 70, 20), (15, 60, 25), (10, 65, 25)],
    "E-MORB":                 [(15, 55, 30), (25, 45, 30), (30, 35, 35), (20, 50, 30)],
    "OIB":                    [(40, 25, 35), (60, 10, 30), (50, 5, 45), (30, 25, 45)],
    "Continental\ntholeiite": [(15, 60, 25), (25, 50, 25), (30, 40, 30), (20, 50, 30)],
    "Back-arc\nbasalt":       [(10, 65, 25), (20, 55, 25), (25, 45, 30), (15, 55, 30)],
}


class CabanisLecolle1989(Diagram):
    key = "cabanis_lecolle_1989"
    title = "La/10 – Y/15 – Nb/8 — Cabanis & Lecolle (1989)"
    citation = ("Cabanis & Lecolle (1989). Robust for arc + back-arc "
                "(<24 % misclassification) and N-MORB; CRB / OIB / E-MORB "
                "less reliable per Verma (2010).")

    def _abc(self, df):
        la = resolve_column(df, ["La"])
        y = resolve_column(df, ["Y"])
        nb = resolve_column(df, ["Nb"])
        if not (la and y and nb):
            return None
        return (pd.to_numeric(df[la], errors="coerce") / 10.0,
                pd.to_numeric(df[y], errors="coerce") / 15.0,
                pd.to_numeric(df[nb], errors="coerce") / 8.0)

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("La / 10", "Y / 15", "Nb / 8"),
                           options.x_axis)
        for name, abc in _CABANIS_FIELDS.items():
            a, b, c = zip(*abc)
            x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
            poly = Polygon(list(zip(x, y)), closed=True, fill=False,
                           edgecolor="#444", linewidth=0.7, alpha=0.7,
                           zorder=2)
            ax.add_patch(poly)
            cx = float(np.mean(x))
            cy = float(np.mean(y))
            ax.text(cx, cy, name, ha="center", va="center", fontsize=7,
                    color="#333", alpha=0.9, zorder=3)
        _plot_ternary_data(ax, df, plot_style, self._abc)
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
    return pd.to_numeric(df[ox], errors="coerce") * 5995.0


_VRMS_NA_NB_SR = {
    "IAB":  [(5, 5, 90), (15, 5, 80), (20, 15, 65), (10, 15, 75)],
    "MORB": [(15, 35, 50), (25, 30, 45), (30, 45, 25), (20, 50, 30)],
    "OIB":  [(35, 40, 25), (45, 35, 20), (50, 25, 25), (40, 25, 35)],
}


class Vermeesch2006NaNbSr(Diagram):
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
        _plot_ternary_data(ax, df, plot_style, self._abc)
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


def _inverse_logratio(x, y):
    """``(ln(B/A), ln(C/A))`` back to ternary ``(A, B, C)`` summing to 1.

    The softmax of ``(0, x, y)``, computed against the largest exponent
    so a boundary walked far from the triple point does not overflow.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    top = np.maximum(np.maximum(x, y), 0.0)
    ea, eb, ec = np.exp(-top), np.exp(x - top), np.exp(y - top)
    total = ea + eb + ec
    return ea / total, eb / total, ec / total


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


class _VermeeschLDATernary(Diagram):
    """Shared plumbing for the three log-ratio LDA ternaries."""

    spec: dict = {}
    apices: Tuple[str, str, str] = ("", "", "")

    def _abc(self, df):                                   # pragma: no cover
        raise NotImplementedError

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, self.apices, options.x_axis)
        _draw_lda_boundaries(ax, self.spec)
        _plot_ternary_data(ax, df, plot_style, self._abc)
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
class Vermeesch2006SmTiV(Diagram):
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
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()


# ---------------------------------------------------------------------------
# Harris et al. (1986) — Hf − Rb/10 − 3 Ta granitoid discrimination
# ---------------------------------------------------------------------------

_HARRIS_FIELDS = {
    "Volcanic-arc\ngranites":      [(15, 50, 35), (25, 60, 15), (35, 50, 15), (20, 40, 40)],
    "Within-plate\ngranites":      [(40, 25, 35), (55, 15, 30), (45, 10, 45), (35, 20, 45)],
    "Syn-collisional\ngranites":   [(20, 65, 15), (35, 55, 10), (45, 45, 10), (30, 55, 15)],
    "Post-collisional\ngranites":  [(30, 50, 20), (45, 35, 20), (40, 30, 30), (30, 40, 30)],
}


class Harris1986HfRbTa(Diagram):
    key = "harris_1986_HfRbTa"
    title = "Hf − Rb/10 − 3 Ta — Harris et al. (1986)"
    citation = ("Harris, Pearce & Tindle (1986). Granitoid discrimination "
                "into volcanic-arc, within-plate, syn-collisional and "
                "post-collisional fields. Apex coordinates: Hf, Rb/10 and "
                "3 × Ta (all in ppm).")

    def _abc(self, df):
        hf = resolve_column(df, ["Hf"])
        rb = resolve_column(df, ["Rb"])
        ta = resolve_column(df, ["Ta"])
        if not (hf and rb and ta):
            return None
        return (pd.to_numeric(df[hf], errors="coerce"),
                pd.to_numeric(df[rb], errors="coerce") / 10.0,
                3.0 * pd.to_numeric(df[ta], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Hf", "Rb / 10", "3 Ta"), options.x_axis)
        _draw_ternary_fields(ax, _HARRIS_FIELDS, fontsize=7.5)
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()
