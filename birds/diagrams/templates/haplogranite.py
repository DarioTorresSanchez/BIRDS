"""Haplogranite system Ab – Or – Q (Tuttle & Bowen 1958)."""

from __future__ import annotations

import pandas as pd
from .base import (
    Diagram,
    PlotOptions,
    draw_note,
    draw_ternary_frame,
    get_groups,
    normative,
    normative_note,
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

    _MINERALS = ("Ab", "Or", "Q")

    def _compute_xy(self, df):
        """Each sample on the triangle (Q at the top, Ab left, Or right),
        from its norm; NaN where it has none.  The sample tally and
        Identify-sample read the same mapping as the plot."""
        norm = normative(df, self._MINERALS)
        if norm is None:
            return None, None
        return ternary_to_xy(norm["Q"], norm["Ab"], norm["Or"])

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Q", "Ab", "Or"), options.x_axis)

        # Apex A = Q, B = Ab, C = Or
        xs, ys, labels = [], [], []
        for ab, orx, q, p, _kind in _MIN_EUT:
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
                x, y = self._compute_xy(sub)
                if x is None:
                    continue
                mask = x.notna() & y.notna()
                if not mask.any():
                    continue
                ax.scatter(x[mask], y[mask], s=plot_style.point_size ** 2,
                           alpha=plot_style.alpha,
                           c=gs.color if gs else "#1f77b4",
                           marker=gs.marker if gs else "o",
                           label=label, edgecolors="black", linewidths=0.4,
                           zorder=4)
        note = normative_note(df, self._MINERALS)
        if note:
            draw_note(ax, note)
        self._apply_legend(ax, options)
        figure.tight_layout()
