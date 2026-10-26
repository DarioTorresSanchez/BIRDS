"""Alkalic vs Sub-alkalic boundary on the TAS plane."""

from __future__ import annotations

import pandas as pd
from .base import Diagram, resolve_column


# Plotting coordinates from the figure caption of Rollinson & Pease (2021,
# Figure 3.3), confirmed by Rickwood (1989) Table 1.  Read again in the
# originals on 2026-10-26: MacDonald's (1968) Figure 1 dashes run from
# SiO2 39.85, alkalis 0.32 to 65.58, 9.77; Kuno's (1966) Figure 2 line
# between the alkali and high-alumina basalt series has this shape from
# SiO2 46 to 76 and lies 0-0.35 above these points, as close as that
# figure's own y axis -- out by 0.18 at its foot -- resolves.  Kuno's
# second line, high-alumina basalt | tholeiite, is not drawn.
_IRVINE_BARAGAR_1971 = [
    (39.2, 0.0), (40.0, 0.4), (43.2, 2.0), (45.0, 2.8), (48.0, 4.0),
    (50.0, 4.75), (53.7, 6.0), (55.0, 6.4), (60.0, 8.0), (65.0, 9.6),
    (66.4, 10.0),
]
_KUNO_1966 = [
    (45.85, 2.75), (46.85, 3.0), (50.0, 3.9), (50.3, 4.0), (53.1, 5.0),
    (55.0, 5.8), (55.6, 6.0), (60.0, 6.8), (61.5, 7.0), (65.0, 7.35),
    (70.0, 7.85), (71.6, 8.0), (75.0, 8.3), (76.4, 8.4),
]
_MACDONALD_1968 = [(39.8, 0.35), (65.5, 9.7)]


class AlkalicSubAlkalicBoundary(Diagram):
    key = "ib1971"
    title = "Alkalic vs Sub-alkalic boundary on TAS"
    citation = ("Irvine & Baragar (1971); MacDonald (1968); Kuno (1966). "
                "Plotting coordinates from Rollinson & Pease (2021), Fig. 3.3.")
    x_label = "SiO$_2$ (wt.%)"
    y_label = "Na$_2$O + K$_2$O (wt.%)"
    x_range = (35, 80)
    y_range = (0, 14)

    def _compute_xy(self, df):
        si = resolve_column(df, ["SiO2"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if not (si and na and k):
            return None, None
        return (
            pd.to_numeric(df[si], errors="coerce"),
            pd.to_numeric(df[na], errors="coerce")
            + pd.to_numeric(df[k], errors="coerce"),
        )

    def _draw_background(self, ax, options):
        ax.plot([p[0] for p in _IRVINE_BARAGAR_1971],
                [p[1] for p in _IRVINE_BARAGAR_1971],
                color="#1f3a93", linewidth=1.4, label="Irvine & Baragar 1971")
        ax.plot([p[0] for p in _KUNO_1966], [p[1] for p in _KUNO_1966],
                color="#117a37", linewidth=1.1, linestyle="--",
                label="Kuno 1966")
        ax.plot([p[0] for p in _MACDONALD_1968], [p[1] for p in _MACDONALD_1968],
                color="#b13a3a", linewidth=1.1, linestyle=":",
                label="MacDonald 1968")
        ax.text(70, 12, "Alkalic", fontsize=11, color="#5b6478", style="italic")
        ax.text(70, 4, "Sub-alkalic", fontsize=11, color="#5b6478", style="italic")
