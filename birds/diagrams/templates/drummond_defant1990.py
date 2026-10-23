"""(La/Yb)_N vs Yb_N — Drummond & Defant (1990), Figure 10.

Drummond, M. S. & Defant, M. J. (1990) A model for trondhjemite-
tonalite-dacite genesis and crustal growth via slab melting: Archean to
modern comparisons.  *J. Geophys. Res.* 95(B13), 21503-21521.

Figure 10, "modified after Jahn et al. [1981] and Martin [1986]", draws
three time-tectonic fields: the Archean trondhjemite-tonalite-
granodiorite (TTG) field, dotted; post-Archean granitic rocks,
unpatterned; and the range of MORB values, a diagonally shaded bar
along the foot of the frame.  The authors' point is that every high-Al
TTD they compiled, Cenozoic as well as Archean, falls in the TTG field
Martin (1986) had called Archean-only.

This is the figure the key ``defant_drummond_YbLaYb`` was meant to
draw.  Defant & Drummond's *Nature* paper of the same year, which the
key was attributed to, has no Yb-La/Yb figure; this one does.

Provenance
----------
Measured on the figure's image in the PDF (671 x 428 px).  The axes
were calibrated on their ticks -- 24.25 px per unit of Yb_N, 2.456 px
per unit of (La/Yb)_N -- and each edge of the two outlined fields was
fitted to the ink along it, the vertices being where neighbouring edges
cross.  The overlay of the result on the scan follows both outlines.
The MORB bar is filled, so its extent is the run of ink along it:
Yb_N 7.91-15.99, and from the axis up to the line at (La/Yb)_N 5.2.

Two checks on the measurement come from the caption, not the figure.
Its melting models start from "a MORB source having Yb_N = 10 and
(La/Yb)_N = 1" and from one with Yb_N = 12, and both sources sit inside
the measured bar.  And the TTG field is Martin's field redrawn: every
vertex lies within 1.7 in (La/Yb)_N and 0.12 in Yb_N of Martin's Figure
1 (see ``martin1986``), the post-Archean field less closely, its lower
right corner at 5.3 here against 3.8 there.  The two figures are drawn
alike, so they agree as drawings; their normalisations need not --
Martin names no chondrite, and BIRDS draws his on Boynton's.

The chondrite
-------------
The paper names its chondrite once, in the caption of Figure 1:
Wakita et al. (1971).  Figures 5 to 10 say only "chondrite-normalized",
and the same normalisation throughout is the reading taken here.

What is not drawn
-----------------
The four partial-melting curves (amphibolite, 10 % garnet amphibolite,
eclogite, 20 % hornblende eclogite) are model results computed with
Martin's (1987) partition coefficients, not fields, and are left out.

The adakite threshold
---------------------
"Y and Yb <= 18 and 1.9 p.p.m." is Defant & Drummond (1990, *Nature*,
page 663), not this paper.  It is drawn as a dotted line labelled with
that source, at Yb_N = 1.9 / 0.220 = 8.64 on Wakita's chondrite, because
it is what the diagram was used for.  It lands just right of the TTG
field's right edge at 8.35, which is 1.84 ppm Yb.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ...normalizations import REE_CHONDRITES
from .base import Diagram, resolve_column
from .tectonic_bivariate import DD_ADAKITE_YB_MAX

#: The chondrite (La/Yb)_N and Yb_N are taken against.
CHONDRITE = "Wakita et al. (1971) – ordinary chondrites"
_CH = REE_CHONDRITES[CHONDRITE]

#: Figure 10's frame: the Yb_N axis is ticked to 25 and drawn on to 27,
#: the (La/Yb)_N axis is ticked to 150 and drawn on to 170.
X_RANGE = (0.0, 27.0)
Y_RANGE = (0.0, 170.0)

#: Archean TTG field, (Yb_N, (La/Yb)_N), clockwise from the top left.
TTG_FIELD = (
    (0.36, 149.0), (1.55, 149.0), (2.46, 70.3), (4.98, 39.8),
    (8.35, 24.9), (8.35, 4.1), (3.04, 4.9), (1.05, 15.3), (0.33, 35.2),
)

#: Post-Archean granitic rocks.
POST_ARCHEAN_FIELD = (
    (4.62, 29.3), (19.98, 10.4), (19.98, 5.3), (4.62, 4.0),
)

#: The MORB bar: Yb_N from, Yb_N to, (La/Yb)_N from, (La/Yb)_N to.
MORB_RANGE = (7.9, 16.0, 0.0, 5.2)

#: The adakite threshold of the companion Nature paper, in Yb_N.
ADAKITE_YB_N_MAX = DD_ADAKITE_YB_MAX / _CH["Yb"]

TTG = "Archean TTG"
POST_ARCHEAN = "post-Archean granitic rocks"
MORB = "MORB range"


def _morb_field():
    lo, hi, bot, top = MORB_RANGE
    return ((lo, bot), (lo, top), (hi, top), (hi, bot))


FIELDS = ((TTG, TTG_FIELD), (POST_ARCHEAN, POST_ARCHEAN_FIELD),
          (MORB, _morb_field()))


def _inside(field, x, y):
    from matplotlib.path import Path
    pts = np.column_stack([np.asarray(x, float), np.asarray(y, float)])
    ok = np.isfinite(pts).all(axis=1)
    return ok & Path(field).contains_points(np.where(ok[:, None], pts, 0.0))


def classify(yb_n, la_yb_n) -> np.ndarray:
    """The field of each point; "" outside all three.  The fields
    overlap -- TTG and post-Archean at Yb_N 4.6-8.4, the MORB bar with
    both along its top -- and a sample in two is named as both."""
    hits = [np.where(_inside(field, yb_n, la_yb_n), name, "")
            for name, field in FIELDS]
    out = []
    for names in zip(*hits):
        out.append(" or ".join(n for n in names if n))
    return np.array(out, dtype=object)


def normalised(df: pd.DataFrame):
    """(Yb_N, (La/Yb)_N), or (None, None) without La or Yb."""
    la = resolve_column(df, ["La"])
    yb = resolve_column(df, ["Yb"])
    if not (la and yb):
        return None, None
    yb_n = pd.to_numeric(df[yb], errors="coerce") / _CH["Yb"]
    yb_n = yb_n.where(yb_n > 0)
    la_n = pd.to_numeric(df[la], errors="coerce") / _CH["La"]
    return yb_n, la_n / yb_n


class DrummondDefant1990LaYbN(Diagram):
    # The key is the old one, which saved sessions store.
    key = "defant_drummond_YbLaYb"
    title = "(La/Yb)N vs YbN — Drummond & Defant (1990)"
    citation = ("Drummond & Defant (1990) J. Geophys. Res. 95, "
                "21503-21521, Figure 10, after Jahn et al. (1981) and "
                "Martin (1986): Archean TTG, post-Archean granitic rocks "
                "and the range of MORB, all three measured on the "
                "figure; its melting curves are not drawn. Normalised "
                "to Wakita et al. (1971), the chondrite the paper names. "
                "The dotted line is the adakite limit Yb ≤ 1.9 ppm of "
                "Defant & Drummond (1990, Nature), not part of the "
                "figure.")
    x_label = "YbN"
    y_label = "(La/Yb)N"
    x_range = X_RANGE
    y_range = Y_RANGE

    def _compute_xy(self, df):
        return normalised(df)

    def classify_frame(self, df: pd.DataFrame) -> pd.Series:
        x, y = self._compute_xy(df)
        if x is None:
            return pd.Series("", index=df.index, dtype=object)
        return pd.Series(classify(x, y), index=df.index, dtype=object)

    def _draw_background(self, ax, options):
        from matplotlib.patches import Polygon
        ax.add_patch(Polygon(TTG_FIELD, closed=True, facecolor="#e9d9c4",
                             alpha=0.55, edgecolor="#333", linewidth=1.0,
                             zorder=0))
        ax.add_patch(Polygon(POST_ARCHEAN_FIELD, closed=True, fill=False,
                             edgecolor="#333", linewidth=1.0, zorder=0))
        ax.add_patch(Polygon(_morb_field(), closed=True, facecolor="none",
                             edgecolor="#333", hatch="////", linewidth=0.8,
                             zorder=0))
        ax.axvline(ADAKITE_YB_N_MAX, color="#444", lw=1.0, linestyle=":",
                   zorder=0)
        ax.text(ADAKITE_YB_N_MAX - 0.15, 0.98,
                "adakite: Yb ≤ 1.9 ppm (Nature 1990)",
                transform=ax.get_xaxis_transform(), fontsize=8,
                color="#333", style="italic", ha="right", va="top",
                rotation=90, zorder=0)
        text = dict(fontsize=8.5, color="#333", style="italic",
                    va="center", zorder=1)
        ax.text(3.0, 110, "Archean TTG", ha="left", **text)
        ax.text(14.5, 24, "Post-Archean\ngranitic rocks", ha="center",
                **text)
        ax.text(16.4, 2.6, "MORB", ha="left", **text)
