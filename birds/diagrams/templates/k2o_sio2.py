"""K2O vs SiO2 (sub-alkalic series subdivision)."""

from __future__ import annotations

import pandas as pd
from .base import Diagram, resolve_column


# Le Maitre et al. (1989) low-K / medium-K / high-K dividing lines for
# sub-alkalic rocks (SiO2 48-68). Each line is given as two endpoints.
_LM89_LINES = {
    "low-K / medium-K":  ((48.0, 0.3), (68.0, 1.2)),
    "medium-K / high-K": ((48.0, 1.2), (68.0, 3.1)),
}

# Rickwood (1989) high-K / shoshonitic boundary band (one curve, midpoint)
_RICKWOOD_SHOSHONITE = [(45, 1.4), (48, 1.7), (56, 3.3), (63, 4.2), (70, 5.1)]


class K2OvsSiO2(Diagram):
    key = "k2o_sio2"
    title = "K$_2$O vs SiO$_2$ – Sub-alkalic series subdivision"
    citation = ("Peccerillo & Taylor (1976); Le Maitre et al. (1989); "
                "Rickwood (1989).")
    x_label = "SiO$_2$ (wt.%)"
    y_label = "K$_2$O (wt.%)"
    x_range = (45, 80)
    y_range = (0, 8)
    field_polygons = {}  # boundaries handled in _draw_background

    def _compute_xy(self, df):
        si = resolve_column(df, ["SiO2"])
        k = resolve_column(df, ["K2O"])
        if not (si and k):
            return None, None
        return (pd.to_numeric(df[si], errors="coerce"),
                pd.to_numeric(df[k], errors="coerce"))

    def _draw_background(self, ax, options):
        for label, ((x1, y1), (x2, y2)) in _LM89_LINES.items():
            ax.plot([x1, x2], [y1, y2], color="#444", linewidth=0.9,
                    linestyle="--", zorder=1)
            ax.text(x2, y2, "  " + label, fontsize=7.5, color="#333",
                    va="center")
        xs = [p[0] for p in _RICKWOOD_SHOSHONITE]
        ys = [p[1] for p in _RICKWOOD_SHOSHONITE]
        ax.plot(xs, ys, color="#444", linewidth=0.9, linestyle=":", zorder=1)
        ax.text(xs[-1], ys[-1], "  high-K / shoshonitic\n(Rickwood 1989)",
                fontsize=7.5, color="#333", va="center")
        # rough field labels
        ax.text(60, 0.4, "Low-K (Tholeiitic)", fontsize=7.5, color="#333")
        ax.text(60, 1.5, "Medium-K (Calc-alkalic)", fontsize=7.5, color="#333")
        ax.text(60, 3.0, "High-K (Calc-alkalic)", fontsize=7.5, color="#333")
        ax.text(60, 5.0, "Shoshonitic", fontsize=7.5, color="#333")
