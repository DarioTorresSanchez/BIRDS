"""Haplogranite system Ab – Or – Q (Tuttle & Bowen 1958)."""

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


# Approximate water-saturated minimum/eutectic points (Tuttle & Bowen 1958
# and subsequent compilations in Rollinson & Pease 2021 Table 3.10).
# Columns: Ab, Or, Q, pressure (kb), kind ("min" or "eut")
_MIN_EUT = [
    # 0.5 kb minimum
    (30, 30, 40, 0.5, "min"),
    # 1.0 kb minimum
    (33, 29, 38, 1.0, "min"),
    # 2 kb minimum
    (39, 26, 35, 2.0, "min"),
    # 3 kb minimum
    (42, 25, 33, 3.0, "min"),
    # 5 kb eutectic
    (47, 22, 31, 5.0, "eut"),
    # 10 kb eutectic
    (56, 21, 23, 10.0, "eut"),
    # 20 kb eutectic
    (63, 19, 18, 20.0, "eut"),
    # 30 kb eutectic
    (67, 18, 15, 30.0, "eut"),
]


class Haplogranite(Diagram):
    key = "haplogranite"
    title = "Haplogranite system Ab – Or – Q (water-saturated)"
    citation = ("Tuttle & Bowen (1958); Johannes & Holz (1996); "
                "Rollinson & Pease (2021) Table 3.10.")

    def _abc(self, df):
        ab = resolve_column(df, ["Ab", "Albite"])
        orx = resolve_column(df, ["Or", "Orthoclase"])
        q = resolve_column(df, ["Q", "Qz", "Quartz"])
        if not (ab and orx and q):
            return None
        return (
            pd.to_numeric(df[ab], errors="coerce"),
            pd.to_numeric(df[orx], errors="coerce"),
            pd.to_numeric(df[q], errors="coerce"),
        )

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Q", "Ab", "Or"), options.x_axis)

        # Apex A = Q, B = Ab, C = Or
        xs, ys, labels = [], [], []
        for ab, orx, q, p, kind in _MIN_EUT:
            x, y = ternary_to_xy(pd.Series([q]), pd.Series([ab]), pd.Series([orx]))
            xs.append(x.iloc[0]); ys.append(y.iloc[0])
            labels.append(f"{p:g} kb")
        ax.plot(xs, ys, color="#b13a3a", marker="o", linewidth=1.1, ms=4,
                label="Minima / eutectics", zorder=2)
        for x, y, lbl in zip(xs, ys, labels):
            ax.text(x + 0.012, y, lbl, fontsize=7.5, color="#333",
                    va="center", zorder=3)

        if df is not None and not df.empty:
            for label, sub, gs in get_groups(df, plot_style):
                abc = self._abc(sub)
                if abc is None:
                    continue
                a, b, c = abc  # Ab, Or, Q
                mask = a.notna() & b.notna() & c.notna()
                a, b, c = a[mask], b[mask], c[mask]
                if a.empty:
                    continue
                # apex A = Q, B = Ab, C = Or
                x, y = ternary_to_xy(c, a, b)
                ax.scatter(x, y, s=plot_style.point_size ** 2,
                           alpha=plot_style.alpha,
                           c=gs.color if gs else "#1f77b4",
                           marker=gs.marker if gs else "o",
                           label=label, edgecolors="black", linewidths=0.4,
                           zorder=4)
        self._apply_legend(ax, options)
        figure.tight_layout()
