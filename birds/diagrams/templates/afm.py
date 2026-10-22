"""AFM ternary – Alkalis – FeOT – MgO."""

from __future__ import annotations

import pandas as pd
from .base import (
    PlotOptions,
    TernaryDiagram,
    draw_ternary_frame,
    resolve_column,
    ternary_to_xy,
)

# New boundary curve recommended in Rollinson & Pease (2021, Fig. 3.18b),
# coordinates A, F, M (sum to 100).
_AFM_BOUNDARY = [
    (11, 39, 50), (14, 50, 36), (18, 56, 26),
    (28, 52, 20), (40, 45, 15), (70, 26, 4),
]

# Irvine & Baragar (1971, Fig. 2A) and Kuno (1968, Fig. 14) dividing
# curves, as Rickwood (1989, Table 3) measured them on the published
# figures.  The Irvine & Baragar curve used to be an approximation that
# ran up to 8 units of F off theirs -- (40, 42, 18) where their line
# passes (47.6, 42.4, 10) and (29.6, 52.6, 17.8) -- and Kuno, cited,
# was not drawn at all.
_IB_1971 = [
    (58.8, 36.2, 5), (47.6, 42.4, 10), (29.6, 52.6, 17.8),
    (25.4, 54.6, 20), (21.4, 54.6, 24), (19.4, 52.8, 27.8),
    (18.9, 51.1, 30), (16.6, 43.4, 40), (15, 35, 50),
]
_KUNO_1968 = [
    (72, 24, 4), (50, 39.5, 10.5), (34.5, 50, 15.5), (21.5, 57, 21.5),
    (16.5, 58, 25.5), (12.5, 55.5, 32), (9.5, 50.5, 40),
]


class AFM(TernaryDiagram):
    key = "afm"
    title = "AFM ternary – Tholeiitic vs Calc-alkaline"
    citation = ("Irvine & Baragar (1971) and Kuno (1968), as measured by "
                "Rickwood (1989, Table 3); new boundary curve in Rollinson "
                "& Pease (2021, Fig. 3.18b). All Fe as FeO$_T$.")
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
            (_KUNO_1968, dict(color="#4d7a3a", linewidth=1.0, linestyle=":",
                              label="Kuno 1968")),
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
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()
