"""(La/Yb)_N vs Yb_N — Martin (1986), Archean TTG and post-Archean granitoids.

Martin, H. (1986) Effect of steeper Archean geothermal gradient on
geochemistry of subduction-zone magmas.  *Geology* 14, 753-756.

Figure 1 sets the granitic rocks of the Archean against those that came
after: Archean tonalite-trondhjemite-granodiorite (TTG), with high
(La/Yb)_N "from 5 to more than 150" and low Yb, 0.3 < Yb_N < 8.5, and
post-2.5 Ga granitic rocks with (La/Yb)_N mostly under 20 and
4.5 < Yb_N < 20.  The first, Martin argues, are melts of subducted
oceanic crust leaving garnet and hornblende behind; the second, melts
of the hydrated mantle wedge.

Provenance
----------
Both fields were measured on Figure 1, the only figure that draws them
together, from the 2566 x 3282 scan of page 753: the axes were
calibrated on their ticks -- Yb_N 0, 10 and 20 (45.98 px per unit),
(La/Yb)_N 0, 50, 100 and 150 (4.57 px per unit) -- and each edge of
each field was fitted to the ink along it, the vertices being where
neighbouring edges cross.  The caption's own numbers bound what was
measured: Yb_N 0.31-8.47 against its 0.3-8.5 for the TTG, 4.47-20.0
against 4.5-20 for the others.

Figure 4 draws the two fields again, apart: the post-Archean one in its
inset A agrees with Figure 1 within 0.5 in (La/Yb)_N; the TTG field of
4B is drawn a little narrower, its top at 148 for 150 and its steep
edge up to 0.33 in Yb_N to the left.  Figure 1 is the one used.

Martin does not say which chondrite he normalised to.  Boynton (1984),
the recommended chondrite of its day, is used here, and the citation
says so: another chondrite moves Yb_N by up to a third.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ...normalizations import REE_CHONDRITES
from .base import Diagram, resolve_column

#: The chondrite (La/Yb)_N and Yb_N are taken against.
CHONDRITE = "Boynton (1984)"
_CH = REE_CHONDRITES[CHONDRITE]

#: Figure 1's frame: Yb_N 0-25, (La/Yb)_N 0-177.
X_RANGE = (0.0, 25.0)
Y_RANGE = (0.0, 177.0)

#: Archean TTG field, (Yb_N, (La/Yb)_N), clockwise from the top left.
TTG_FIELD = (
    (0.31, 150.0), (1.59, 150.0), (2.50, 70.3), (5.01, 41.5),
    (8.31, 25.8), (8.47, 4.1), (2.92, 5.5), (1.02, 15.5), (0.31, 35.6),
)

#: Post-Archean (post-2.5 Ga) granitoid field.
POST_ARCHEAN_FIELD = (
    (4.47, 30.6), (20.0, 10.0), (20.0, 3.8), (4.50, 4.0),
)

TTG = "Archean TTG"
POST_ARCHEAN = "post-Archean granitoids"
OVERLAP = "Archean TTG or post-Archean granitoids"


def _inside(field, x, y):
    from matplotlib.path import Path
    pts = np.column_stack([np.asarray(x, float), np.asarray(y, float)])
    ok = np.isfinite(pts).all(axis=1)
    return ok & Path(field).contains_points(np.where(ok[:, None], pts, 0.0))


def classify(yb_n, la_yb_n) -> np.ndarray:
    """The field of each point; "" outside both.  The two fields
    overlap at Yb_N 4.5-8.5, and a sample there is named as both."""
    ttg = _inside(TTG_FIELD, yb_n, la_yb_n)
    post = _inside(POST_ARCHEAN_FIELD, yb_n, la_yb_n)
    return np.where(ttg & post, OVERLAP,
                    np.where(ttg, TTG, np.where(post, POST_ARCHEAN, "")))


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


class Martin1986LaYbN(Diagram):
    key = "martin_1986_LaYbN"
    title = "(La/Yb)N vs YbN — Martin (1986)"
    citation = ("Martin (1986) Geology 14, 753-756, Figure 1: Archean "
                "tonalite-trondhjemite-granodiorite (TTG), melts of "
                "subducted oceanic crust leaving garnet and hornblende, "
                "against post-Archean granitoids from the mantle wedge. "
                "Both fields measured on the figure. Martin does not "
                "name his chondrite; Boynton (1984) is used here, and "
                "another moves YbN by up to a third.")
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
        for field, colour in ((TTG_FIELD, "#e9d9c4"),
                              (POST_ARCHEAN_FIELD, "#d6e4f0")):
            ax.add_patch(Polygon(field, closed=True, facecolor=colour,
                                 alpha=0.55, edgecolor="#333",
                                 linewidth=1.0, zorder=0))
        text = dict(fontsize=8.5, color="#333", style="italic",
                    ha="center", va="center", zorder=1)
        ax.text(5.2, 95, "Archean TTG", **text)
        ax.text(14.5, 26, "Post-Archean\ngranitoids", **text)
