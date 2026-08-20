"""Ternary tectonic discrimination diagrams."""

from __future__ import annotations

from typing import Callable, Optional, Sequence, Tuple

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


_VRMS_SI_TI_SR = {
    "IAB":  [(10, 5, 85), (25, 10, 65), (30, 15, 55), (15, 10, 75)],
    "MORB": [(25, 25, 50), (40, 25, 35), (45, 35, 20), (30, 35, 35)],
    "OIB":  [(45, 35, 20), (60, 25, 15), (65, 15, 20), (50, 20, 30)],
}


class Vermeesch2006SiTiSr(Diagram):
    key = "vermeesch_SiTiSr"
    title = "Si/1000 − Ti/40 − Sr — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a). Uses SiO2 (wt% → Si ppm / 1000), "
                "Ti ppm / 40 and Sr ppm. Robust for OIB and IAB.")

    def _abc(self, df):
        si_ox = resolve_column(df, ["SiO2"])
        sr = resolve_column(df, ["Sr"])
        ti = _ti_ppm(df)
        if not (si_ox and sr) or ti is None:
            return None
        si_ppm = pd.to_numeric(df[si_ox], errors="coerce") * 0.4674 * 1e4
        return (si_ppm / 1000.0,
                ti / 40.0,
                pd.to_numeric(df[sr], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Si/1000", "Ti/40", "Sr"), options.x_axis)
        _draw_ternary_fields(ax, _VRMS_SI_TI_SR)
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()


_VRMS_EU_LU_SR = {
    "IAB":  [(5, 5, 90), (15, 10, 75), (20, 15, 65), (10, 10, 80)],
    "MORB": [(20, 25, 55), (30, 30, 40), (35, 40, 25), (25, 35, 40)],
    "OIB":  [(40, 30, 30), (55, 20, 25), (50, 15, 35), (35, 25, 40)],
}


class Vermeesch2006EuLuSr(Diagram):
    key = "vermeesch_EuLuSr"
    title = "100 Eu − 500 Lu − Sr — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a). 100 × Eu, 500 × Lu and Sr (all in ppm). "
                "REE-based ternary, complements the major-element ones.")

    def _abc(self, df):
        eu = resolve_column(df, ["Eu"])
        lu = resolve_column(df, ["Lu"])
        sr = resolve_column(df, ["Sr"])
        if not (eu and lu and sr):
            return None
        return (100.0 * pd.to_numeric(df[eu], errors="coerce"),
                500.0 * pd.to_numeric(df[lu], errors="coerce"),
                pd.to_numeric(df[sr], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("100 Eu", "500 Lu", "Sr"), options.x_axis)
        _draw_ternary_fields(ax, _VRMS_EU_LU_SR)
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()


_VRMS_V_TI_SC = {
    "IAB":  [(60, 5, 35), (80, 10, 10), (75, 5, 20), (55, 5, 40)],
    "MORB": [(35, 30, 35), (50, 30, 20), (60, 20, 20), (45, 25, 30)],
    "OIB":  [(20, 55, 25), (35, 55, 10), (40, 45, 15), (25, 50, 25)],
}


class Vermeesch2006VTiSc(Diagram):
    key = "vermeesch_VTiSc"
    title = "V − Ti/50 − 5 Sc — Vermeesch (2006a)"
    citation = ("Vermeesch (2006a). V, Ti ppm / 50 and 5 × Sc ppm. "
                "Discriminates IAB from MORB and OIB through compatible-"
                "element behaviour.")

    def _abc(self, df):
        v = resolve_column(df, ["V"])
        sc = resolve_column(df, ["Sc"])
        ti = _ti_ppm(df)
        if not (v and sc) or ti is None:
            return None
        return (pd.to_numeric(df[v], errors="coerce"),
                ti / 50.0,
                5.0 * pd.to_numeric(df[sc], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("V", "Ti/50", "5 Sc"), options.x_axis)
        _draw_ternary_fields(ax, _VRMS_V_TI_SC)
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()


_VRMS_SM_TI_V = {
    "IAB":  [(10, 10, 80), (25, 15, 60), (20, 25, 55), (10, 20, 70)],
    "MORB": [(20, 30, 50), (35, 35, 30), (40, 25, 35), (25, 25, 50)],
    "OIB":  [(45, 35, 20), (55, 30, 15), (50, 20, 30), (35, 25, 40)],
}


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
