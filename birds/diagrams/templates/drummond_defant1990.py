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


# ---------------------------------------------------------------------------
# Figure 11 — Sr/Y against Y
# ---------------------------------------------------------------------------
#
# "Y (ppm) versus Sr/Y diagram with Archean and Cenozoic high-Al TTD
# data displayed in conjunction with basalt partial melting curves".
# Frame Y 0-50, Sr/Y 0-500.  It draws one field, the island-arc
# andesite-dacite-rhyolite (ADR) fractionation suite, as a stipple of
# crosses with no outline; the rest is data and four melting curves
# (eclogite and 10 % garnet amphibolite restites, from an Archean mafic
# composite and from MORB), which are model results and are not drawn,
# as on Figure 10.
#
# Measured on the 2452 x 3386 scan of page 21,510: the axes on their
# inward ticks, Y 5-50 (25.20 px per unit, residuals under 4.5 px) and
# Sr/Y 0-500 (1.696 px per unit).  The crosses of the stipple were found
# as connected components, 43 of them, and the field is their envelope
# taken half a stipple spacing out -- 0.6 in Y, 4.5 in Sr/Y -- because
# the pattern has no edge of its own.  Its rows end at Y 26.9 (Sr/Y 30),
# 43.4 (15) and 48.8 (5): the field steps down to the right.  Good to
# about 1 in Y and 5 in Sr/Y, which is the spacing of the stipple.

#: Figure 11's frame.
FIG11_X_RANGE = (0.0, 50.0)
FIG11_Y_RANGE = (0.0, 500.0)

#: Island-arc ADR fractionation suite, (Y, Sr/Y), the envelope of the
#: stipple; it runs off the right-hand edge of the frame.
ADR_FIELD = (
    (16.8, 0.0), (16.8, 38.8), (27.5, 34.6), (44.0, 19.4), (49.4, 9.1),
    (50.0, 9.1), (50.0, 0.0),
)

ADR = "island-arc ADR"


def classify_fig11(y, sr_y) -> np.ndarray:
    """"island-arc ADR" inside the field, "" elsewhere -- the figure
    outlines nothing else."""
    return np.where(_inside(ADR_FIELD, y, sr_y), ADR, "").astype(object)


class DrummondDefant1990YSrY(Diagram):
    key = "drummond_defant_1990_YSrY"
    title = "Sr/Y vs Y — Drummond & Defant (1990)"
    citation = ("Drummond & Defant (1990) J. Geophys. Res. 95, "
                "21503-21521, Figure 11: high-Al trondhjemite-tonalite-"
                "dacite against the island-arc andesite-dacite-rhyolite "
                "fractionation suite. The ADR field is the envelope of "
                "the stipple the figure draws it with, good to about 1 "
                "in Y and 5 in Sr/Y; the melting curves are not drawn.")
    x_label = "Y (ppm)"
    y_label = "Sr/Y"
    x_range = FIG11_X_RANGE
    y_range = FIG11_Y_RANGE

    def _compute_xy(self, df):
        sr = resolve_column(df, ["Sr"])
        y = resolve_column(df, ["Y"])
        if not (sr and y):
            return None, None
        y_s = pd.to_numeric(df[y], errors="coerce")
        y_s = y_s.where(y_s > 0)
        return y_s, pd.to_numeric(df[sr], errors="coerce") / y_s

    def classify_frame(self, df: pd.DataFrame) -> pd.Series:
        x, y = self._compute_xy(df)
        if x is None:
            return pd.Series("", index=df.index, dtype=object)
        return pd.Series(classify_fig11(x, y), index=df.index, dtype=object)

    def _draw_background(self, ax, options):
        from matplotlib.patches import Polygon
        # A stipple, as the figure draws it, inside a dotted edge it does
        # not have -- the envelope is ours.
        ax.add_patch(Polygon(ADR_FIELD, closed=True, facecolor="none",
                             edgecolor="#666", hatch="..", linewidth=0.8,
                             linestyle=":", zorder=0))
        ax.text(33.0, 45.0, "Island-arc ADR\nfractionation suite",
                fontsize=8.5, color="#333", style="italic", ha="center",
                va="bottom", zorder=1)
        ax.text(3.0, 470.0, "High-Al TTD: high Sr/Y, low Y", fontsize=8.5,
                color="#555", style="italic", ha="left", va="top",
                zorder=1)
