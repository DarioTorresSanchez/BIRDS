"""Hanski et al. (2001) high-Mg diagram – [Al2O3] vs [TiO2]."""

from __future__ import annotations

import pandas as pd
from .base import Diagram, resolve_column


def _to_mol(df, candidates, mw):
    col = resolve_column(df, candidates)
    if col is None:
        return None
    return pd.to_numeric(df[col], errors="coerce") / mw


class HanskiHighMg(Diagram):
    key = "hanski"
    title = "Hanski high-Mg plot – [Al$_2$O$_3$] vs [TiO$_2$]"
    citation = "Hanski et al. (2001). Projected from olivine; all Fe as ferrous."
    x_label = "[Al$_2$O$_3$]"
    y_label = "[TiO$_2$]"
    x_range = (0, 1.6)
    y_range = (0, 0.5)
    field_polygons = {
        "Al-undepleted komatiite": [(0.6, 0.0), (1.2, 0.0), (1.2, 0.15), (0.6, 0.15)],
        "Al-depleted komatiite":   [(0.0, 0.10), (0.6, 0.10), (0.6, 0.5), (0.0, 0.5)],
        "Picrite":                 [(0.6, 0.15), (1.2, 0.15), (1.2, 0.5), (0.6, 0.5)],
        "Komatiitic basalt":       [(1.2, 0.0), (1.6, 0.0), (1.6, 0.5), (1.2, 0.5)],
    }
    field_label_pos = {
        "Al-undepleted komatiite": (0.9, 0.07),
        "Al-depleted komatiite":   (0.3, 0.30),
        "Picrite":                 (0.9, 0.32),
        "Komatiitic basalt":       (1.4, 0.25),
    }

    def _compute_xy(self, df):
        al = _to_mol(df, ["Al2O3"], 101.96)
        ti = _to_mol(df, ["TiO2"], 79.90)
        mg = _to_mol(df, ["MgO"], 40.30)
        fe = _to_mol(df, ["FeO"], 71.85)
        if fe is None:
            fe2o3 = _to_mol(df, ["Fe2O3", "Fe2O3T", "Fe2O3t"], 159.69)
            if fe2o3 is not None:
                fe = 2 * fe2o3
        if any(v is None for v in (al, ti, mg, fe)):
            return None, None
        denom = (2.0 / 3.0) - mg - fe
        x = al / denom
        y = ti / denom
        return x, y
