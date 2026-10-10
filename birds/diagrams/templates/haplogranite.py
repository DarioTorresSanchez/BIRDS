"""Haplogranite system Ab – Or – Q (Tuttle & Bowen 1958)."""

from __future__ import annotations

import pandas as pd
from .base import (
    PlotOptions,
    TernaryDiagram,
    draw_note,
    draw_ternary_frame,
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


class Haplogranite(TernaryDiagram):
    key = "haplogranite"
    title = "Haplogranite system Ab – Or – Q (water-saturated)"
    citation = ("Tuttle & Bowen (1958); Johannes & Holz (1996); "
                "Rollinson & Pease (2021) Table 3.10.")

    _MINERALS = ("Ab", "Or", "Q")

    def _abc(self, df):
        """(Q, Ab, Or) from each sample's norm; NaN where it has none."""
        norm = normative(df, self._MINERALS)
        if norm is None:
            return None
        return norm["Q"], norm["Ab"], norm["Or"]

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

        self._scatter_samples(ax, df, plot_style)
        note = normative_note(df, self._MINERALS)
        if note:
            draw_note(ax, note)
        self._apply_legend(ax, options)
        figure.tight_layout()
