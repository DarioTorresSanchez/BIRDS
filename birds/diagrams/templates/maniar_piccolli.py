"""A/CNK vs A/NK aluminium-saturation diagram – Maniar & Piccolli (1989).

X-axis : A/CNK = molar Al2O3 / (CaO + Na2O + K2O)  (Shand's index)
Y-axis : A/NK  = molar Al2O3 / (Na2O + K2O)

The two reference lines at A/CNK = 1 and A/NK = 1 split the plane into
three classification fields (Shand 1943; Maniar & Piccolli 1989):

  - Peraluminous : A/CNK > 1
  - Metaluminous : A/CNK ≤ 1 and A/NK ≥ 1
  - Peralkaline  : A/NK  < 1

Because A/NK ≥ A/CNK for any composition with non-negative CaO, the
lower-right region (A/CNK > 1, A/NK < 1) is geochemically inaccessible
and is left unlabelled.
"""

from __future__ import annotations

import pandas as pd
from .base import Diagram, resolve_column


# Molecular weights (g/mol) used to convert oxide wt% to moles.
_MW = {
    "Al2O3": 101.96,
    "CaO":    56.08,
    "Na2O":   61.98,
    "K2O":    94.20,
}


class ManiarPiccolli1989(Diagram):
    key = "maniar_piccolli"
    title = "A/CNK – A/NK aluminium saturation – Maniar & Piccolli (1989)"
    citation = ("Maniar, P.D. & Piccolli, P.M. (1989). Tectonic "
                "discrimination of granitoids. GSA Bulletin 101, 635–643. "
                "Original index after Shand (1943).")
    x_label = "A/CNK = molar Al$_2$O$_3$ / (CaO + Na$_2$O + K$_2$O)"
    y_label = "A/NK  = molar Al$_2$O$_3$ / (Na$_2$O + K$_2$O)"
    x_range = (0.5, 2.0)
    y_range = (0.4, 4.0)

    field_polygons = {
        "Peraluminous":  [(1.0, 0.4), (1,4)],
        "Metaluminous":  [(0.5, 1.0), (2, 1.0)],
        "Peralkaline":   [(0.5, 0.5), (2.0, 2)],
    }
    field_label_pos = {
        "Peraluminous":  (1.50, 2.6),
        "Metaluminous":  (0.75, 2.6),
        "Peralkaline":   (1.25, 0.75),
    }
    field_label_fontsize = 9.0

    def _compute_xy(self, df):
        al = resolve_column(df, ["Al2O3"])
        ca = resolve_column(df, ["CaO"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if not (al and ca and na and k):
            return None, None
        al_m = pd.to_numeric(df[al], errors="coerce") / _MW["Al2O3"]
        ca_m = pd.to_numeric(df[ca], errors="coerce") / _MW["CaO"]
        na_m = pd.to_numeric(df[na], errors="coerce") / _MW["Na2O"]
        k_m  = pd.to_numeric(df[k],  errors="coerce") / _MW["K2O"]
        a_cnk = al_m / (ca_m + na_m + k_m)
        a_nk  = al_m / (na_m + k_m)
        return a_cnk, a_nk
