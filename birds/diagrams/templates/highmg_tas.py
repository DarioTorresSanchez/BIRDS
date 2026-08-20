"""High-Mg subdivision on the TAS plane (Le Maitre et al. 2002)."""

from __future__ import annotations

import pandas as pd
from .base import Diagram, resolve_column


class HighMgTAS(Diagram):
    key = "highmg_tas"
    title = "High-Mg subdivision – MgO vs TiO$_2$"
    citation = "Le Maitre et al. (2002), Rollinson & Pease (2021) Fig. 3.8a."
    x_label = "MgO (wt.%)"
    y_label = "TiO$_2$ (wt.%)"
    x_range = (8, 35)
    y_range = (0, 4)
    field_polygons = {
        "Komatiite": [(18, 0), (35, 0), (35, 1.0), (18, 1.0)],
        "Meimechite": [(18, 1.0), (35, 1.0), (35, 4.0), (18, 4.0)],
        "Picrite": [(12, 0), (18, 0), (18, 4.0), (12, 4.0)],
        "Boninite": [(8, 0), (12, 0), (12, 0.5), (8, 0.5)],
    }
    field_label_pos = {
        "Komatiite":  (27, 0.45),
        "Meimechite": (27, 2.5),
        "Picrite":    (15, 2.0),
        "Boninite":   (10, 0.25),
    }

    def _compute_xy(self, df):
        mg = resolve_column(df, ["MgO"])
        ti = resolve_column(df, ["TiO2"])
        if not (mg and ti):
            return None, None
        return (pd.to_numeric(df[mg], errors="coerce"),
                pd.to_numeric(df[ti], errors="coerce"))
