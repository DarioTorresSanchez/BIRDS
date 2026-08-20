"""Normative An – Ab – Or classification of granitoids (Barker 1979)."""

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

# Approximate field boundaries (Barker 1979, after O'Connor 1965)
# Expressed as (An, Ab, Or) — sum to 100.
_FIELDS = {
    "Tonalite":    [(60, 40, 0), (30, 70, 0), (30, 64, 6), (50, 44, 6), (60, 35, 5)],
    "Trondhjemite":[(30, 70, 0), (10, 90, 0), (10, 84, 6), (30, 64, 6)],
    "Granodiorite":[(50, 44, 6), (30, 64, 6), (10, 84, 6),
                    (10, 70, 20), (30, 50, 20), (50, 30, 20)],
    "Granite":     [(30, 50, 20), (10, 70, 20), (0, 35, 65),
                    (0, 10, 90), (10, 10, 80), (30, 30, 40)],
    "Trondhjemite/Granite boundary": [],
}


class BarkerAnAbOr(Diagram):
    key = "barker_anaborn"
    title = "Normative An – Ab – Or granitoid classification"
    citation = "Barker (1979), modified from O'Connor (1965)."

    def _abc(self, df):
        ab = resolve_column(df, ["Ab", "ab", "Albite"])
        an = resolve_column(df, ["An", "an", "Anorthite"])
        orx = resolve_column(df, ["Or", "or", "Orthoclase"])
        if not (ab and an and orx):
            return None
        return (
            pd.to_numeric(df[an], errors="coerce"),
            pd.to_numeric(df[ab], errors="coerce"),
            pd.to_numeric(df[orx], errors="coerce"),
        )

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("An", "Ab", "Or"), options.x_axis)

        from matplotlib.patches import Polygon
        for name, abc in _FIELDS.items():
            if not abc:
                continue
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
