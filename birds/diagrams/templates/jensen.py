"""Jensen cation plot for high-Mg volcanic rocks."""

from __future__ import annotations

import pandas as pd
from .base import (
    Diagram,
    PlotOptions,
    draw_ternary_frame,
    get_groups,
    resolve_column,
    ternary_to_xy,
)

# Boundary coordinates (Al, Fe+Ti, Mg) from Jensen & Pyke (1982) (corrected),
# reproduced in Rollinson & Pease (2021) Fig. 3.8b. Sum to 100.
_TH_CA_BOUNDARY = [
    (90, 10, 0), (53.5, 28.5, 18), (52.5, 29, 18.5), (51.5, 29, 19.5),
    (50.5, 27.5, 22), (50.3, 25, 24.7), (50.8, 20, 29.2), (51.5, 12.5, 36),
]


class Jensen(Diagram):
    key = "jensen"
    title = "Jensen cation plot – Al – (Fe+Ti) – Mg"
    citation = ("Jensen (1976); Jensen & Pyke (1982). Cation %. "
                "Coordinates from Rollinson & Pease (2021) Fig. 3.8b.")

    def _abc(self, df):
        ti = resolve_column(df, ["TiO2"])
        al = resolve_column(df, ["Al2O3"])
        feo = resolve_column(df, ["FeO"])
        fe2o3 = resolve_column(df, ["Fe2O3", "Fe2O3T", "Fe2O3t"])
        feoT = resolve_column(df, ["FeOT", "FeOt"])
        mg = resolve_column(df, ["MgO"])
        if not (al and mg and ti and (feo or fe2o3 or feoT)):
            return None
        ti_cat = pd.to_numeric(df[ti], errors="coerce") / 79.90
        al_cat = pd.to_numeric(df[al], errors="coerce") / 101.96 * 2.0
        mg_cat = pd.to_numeric(df[mg], errors="coerce") / 40.30
        if feoT:
            fe_cat = pd.to_numeric(df[feoT], errors="coerce") / 71.85
        elif feo and fe2o3:
            fe_cat = (pd.to_numeric(df[feo], errors="coerce") / 71.85
                      + pd.to_numeric(df[fe2o3], errors="coerce") / 159.69 * 2.0)
        elif fe2o3:
            fe_cat = pd.to_numeric(df[fe2o3], errors="coerce") / 159.69 * 2.0
        else:
            fe_cat = pd.to_numeric(df[feo], errors="coerce") / 71.85
        # Recast as percentages of (Al, Fe+Ti, Mg)
        a = al_cat
        b = fe_cat + ti_cat
        c = mg_cat
        total = a + b + c
        return a / total * 100, b / total * 100, c / total * 100

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Al", "Fe + Ti", "Mg"), options.x_axis)

        # Tholeiitic / calc-alkaline boundary
        a, b, c = zip(*_TH_CA_BOUNDARY)
        x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
        ax.plot(x, y, color="#b13a3a", linewidth=1.3,
                label="Th / CA boundary (Jensen & Pyke 1982)", zorder=2)
        ax.text(0.30, 0.42, "Calc-alkaline", color="#333", fontsize=9,
                style="italic")
        ax.text(0.55, 0.18, "Tholeiitic", color="#333", fontsize=9,
                style="italic")
        ax.text(0.85, 0.08, "Komatiitic\nbasalts", color="#333", fontsize=8,
                ha="center")
        ax.text(0.92, 0.02, "Komatiites", color="#333", fontsize=8,
                ha="center")

        if df is not None and not df.empty:
            for label, sub, gs in get_groups(df, plot_style):
                abc = self._abc(sub)
                if abc is None:
                    continue
                aa, bb, cc = abc
                mask = aa.notna() & bb.notna() & cc.notna()
                aa, bb, cc = aa[mask], bb[mask], cc[mask]
                if aa.empty:
                    continue
                x, y = ternary_to_xy(aa, bb, cc)
                ax.scatter(x, y, s=plot_style.point_size ** 2,
                           alpha=plot_style.alpha,
                           c=gs.color if gs else "#1f77b4",
                           marker=gs.marker if gs else "o",
                           label=label, edgecolors="black", linewidths=0.4,
                           zorder=4)
        self._apply_legend(ax, options)
        figure.tight_layout()
