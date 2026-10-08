"""A/CNK vs A/NK aluminium-saturation diagram – Maniar & Piccoli (1989).

X-axis : A/CNK = molar Al2O3 / (CaO + Na2O + K2O)  (Shand's index)
Y-axis : A/NK  = molar Al2O3 / (Na2O + K2O)

The two reference lines at A/CNK = 1 and A/NK = 1 split the plane into
three classification fields (Shand 1943; Maniar & Piccoli 1989):

  - Peraluminous : A/CNK > 1
  - Metaluminous : A/CNK < 1 and A/NK > 1
  - Peralkaline  : A/NK  < 1

Every feldspar, and every mixture of feldspars, has A/CNK = 1 exactly,
and an alkali feldspar sits on A/NK = 1 as well: the lines are where Al
is just enough to make feldspar out of the Ca, Na and K present.

Provenance
----------
Nothing here is measured or transcribed.  Both boundaries are the
definitions themselves, and the third line drawn is arithmetic:
A/NK / A/CNK = (CaO + Na2O + K2O) / (Na2O + K2O), which is never below
1 while CaO >= 0 and is exactly 1 when CaO = 0.  So the diagonal
A/NK = A/CNK is the CaO-free limit and nothing plots below it -- in
particular not in the lower-right quadrant, which would have to be
peraluminous and peralkaline at once.  The diagonal is not a field
boundary, and peralkaline rocks fall in the small triangle above it,
left of A/CNK = 1 and below A/NK = 1.

An earlier version stored the diagonal under the name "Peralkaline"
and put that label at (1.25, 0.75), in the quadrant no composition can
reach, while this docstring said the quadrant was left unlabelled.

Whether Maniar & Piccoli draw the diagonal, and on what frame, needs
the paper, which is not among the sources on disk; the frame here is
not taken from it.
"""

from __future__ import annotations

import pandas as pd
from .base import Diagram, resolve_column


#: Oxide molar masses (g/mol), to convert wt.% to moles.  IUPAC atomic
#: weights give 101.9601, 56.0770, 61.9785 and 94.1956.
MOLAR_MASS = {
    "Al2O3": 101.96,
    "CaO":    56.08,
    "Na2O":   61.98,
    "K2O":    94.20,
}

#: Shand's boundaries, by definition.
A_CNK_BOUNDARY = 1.0
A_NK_BOUNDARY = 1.0

_LINE = dict(color="#444", linewidth=0.9, alpha=0.9, zorder=1)


class ManiarPiccolli1989(Diagram):
    # Key and class keep the old misspelling: saved sessions store the key.
    key = "maniar_piccolli"
    title = "A/CNK – A/NK aluminium saturation – Maniar & Piccoli (1989)"
    citation = ("Maniar, P.D. & Piccoli, P.M. (1989). Tectonic "
                "discrimination of granitoids. GSA Bulletin 101, 635–643. "
                "Original index after Shand (1943).  The diagonal is "
                "A/NK = A/CNK, where CaO = 0; no composition plots "
                "below it.")
    x_label = "A/CNK = molar Al$_2$O$_3$ / (CaO + Na$_2$O + K$_2$O)"
    y_label = "A/NK  = molar Al$_2$O$_3$ / (Na$_2$O + K$_2$O)"
    x_range = (0.5, 2.0)
    y_range = (0.4, 4.0)
    field_polygons = {}  # boundaries handled in _draw_background

    field_label_pos = {
        "Peraluminous":  (1.50, 2.6),
        "Metaluminous":  (0.75, 2.6),
        "Peralkaline":   (0.66, 0.88),
    }
    field_label_fontsize = 9.0

    def _draw_background(self, ax, options):
        (x0, x1), (y0, y1) = self.x_range, self.y_range
        ax.plot([A_CNK_BOUNDARY, A_CNK_BOUNDARY], [y0, y1], **_LINE)
        ax.plot([x0, x1], [A_NK_BOUNDARY, A_NK_BOUNDARY], **_LINE)
        ax.plot([x0, x1], [x0, x1], **_LINE)            # CaO = 0
        for name, (px, py) in self.field_label_pos.items():
            ax.text(px, py, name, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#333",
                    alpha=0.95, zorder=2)

    def _compute_xy(self, df):
        al = resolve_column(df, ["Al2O3"])
        ca = resolve_column(df, ["CaO"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if not (al and ca and na and k):
            return None, None
        al_m = pd.to_numeric(df[al], errors="coerce") / MOLAR_MASS["Al2O3"]
        ca_m = pd.to_numeric(df[ca], errors="coerce") / MOLAR_MASS["CaO"]
        na_m = pd.to_numeric(df[na], errors="coerce") / MOLAR_MASS["Na2O"]
        k_m  = pd.to_numeric(df[k],  errors="coerce") / MOLAR_MASS["K2O"]
        a_cnk = al_m / (ca_m + na_m + k_m)
        a_nk  = al_m / (na_m + k_m)
        return a_cnk, a_nk
