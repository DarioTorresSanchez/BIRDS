"""AFM ternary – Alkalis – FeOT – MgO."""

from __future__ import annotations

import numpy as np
import pandas as pd
from .base import (
    Diagram,
    PlotOptions,
    draw_ternary_frame,
    get_groups,
    resolve_column,
    ternary_to_xy,
)

# New boundary curve recommended in Rollinson & Pease (2021, Fig. 3.18b),
# coordinates A, F, M (sum to 100).
_AFM_BOUNDARY = [
    (11, 39, 50), (14, 50, 36), (18, 56, 26),
    (28, 52, 20), (40, 45, 15), (70, 26, 4),
]

# Irvine & Baragar (1971) tholeiitic / calc-alkaline dividing curve
# (approximate, plotted as a dashed reference).
_IB_1971 = [
    (4, 35, 61), (8, 47, 45), (12, 51, 37), (18, 54, 28),
    (28, 49, 23), (40, 42, 18), (55, 31, 14), (70, 24, 6),
]


class AFM(Diagram):
    key = "afm"
    title = "AFM ternary – Tholeiitic vs Calc-alkaline"
    citation = ("Irvine & Baragar (1971); Kuno (1968); new boundary curve "
                "in Rollinson & Pease (2021, Fig. 3.18b). All Fe as FeO$_T$.")
    x_label = ""
    y_label = ""

    def _data_columns(self, df):
        a_na = resolve_column(df, ["Na2O"])
        a_k = resolve_column(df, ["K2O"])
        f_feo = resolve_column(df, ["FeOT", "FeO(T)", "FeOt", "FeO_total"])
        f_fe2o3 = resolve_column(df, ["Fe2O3T", "Fe2O3t", "Fe2O3"])
        f_feo_only = resolve_column(df, ["FeO"])
        m = resolve_column(df, ["MgO"])
        return a_na, a_k, f_feo, f_fe2o3, f_feo_only, m

    def _abc(self, df):
        a_na, a_k, f_feo, f_fe2o3, f_feo_only, m = self._data_columns(df)
        if not (a_na and a_k and m):
            return None
        alk = pd.to_numeric(df[a_na], errors="coerce") + pd.to_numeric(df[a_k], errors="coerce")
        mg = pd.to_numeric(df[m], errors="coerce")
        if f_feo:
            fe = pd.to_numeric(df[f_feo], errors="coerce")
        elif f_fe2o3 and f_feo_only:
            fe = pd.to_numeric(df[f_feo_only], errors="coerce") \
                 + pd.to_numeric(df[f_fe2o3], errors="coerce") * 0.8998
        elif f_fe2o3:
            fe = pd.to_numeric(df[f_fe2o3], errors="coerce") * 0.8998
        elif f_feo_only:
            fe = pd.to_numeric(df[f_feo_only], errors="coerce")
        else:
            return None
        return alk, fe, mg

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("A (Na$_2$O+K$_2$O)", "F (FeO$_T$)", "M (MgO)"),
                           options.x_axis)
        # Reference curves
        for curve, kw in (
            (_AFM_BOUNDARY, dict(color="#b13a3a", linewidth=1.4,
                                 label="Tholeiitic / Calc-alkaline\n(Rollinson 2021)")),
            (_IB_1971, dict(color="#1f3a93", linewidth=1.0, linestyle="--",
                            label="Irvine & Baragar 1971")),
        ):
            a, b, c = zip(*curve)
            x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
            ax.plot(x, y, **kw, zorder=2)
        # Label fields by hand
        ax.text(0.27, 0.40, "Calc-alkaline", ha="center", color="#333",
                fontsize=10, style="italic")
        ax.text(0.65, 0.32, "Tholeiitic", ha="center", color="#333",
                fontsize=10, style="italic")

        # Data
        if df is not None and not df.empty:
            for label, sub, gs in get_groups(df, plot_style):
                abc = self._abc(sub)
                if abc is None:
                    continue
                a, b, c = abc
                mask = a.notna() & b.notna() & c.notna()
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
        self._apply_legend(ax, options)
        figure.tight_layout()
