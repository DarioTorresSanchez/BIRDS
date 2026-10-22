"""Nb/Zr vs Th/Nb tectonic discrimination — Godang, Saputro & Li (2024).

Godang, S., Saputro, S.P. & Li, H. (2024) The slab failure in Central
Java (Indonesia): new insight into its tectonic setting and origin.
*Solid Earth Sciences* 9(3), 100199 -- after Saputro et al. (2022) and
Sun, Zhang & Huang (2006).  As reproduced in Li, Godang & Saputro (2025)
*Lithosphere* 2025(2), lithosphere_2025_125 (CC BY 4.0), Figure 5,
which calls it a third-generation discrimination diagram.

Th/Nb runs across (log, 0.015-5) and Nb/Zr up (log, 0.01-1).  Li et
al. (2025, Section 4) use it beside their Nb/Yb vs Th/Nb diagram on
basaltic and rhyolitic rocks alike, so like that one it is offered for
every composition.

Nb/Zr sorts the mantle source -- enriched above the primitive mantle's
0.0627, slightly enriched (the transition) down to 0.04, depleted below
-- and Th/Nb the setting: below 0.04 source modification or
contamination; 0.04-0.11 the array of non-subduction basalts (N-MORB to
mantle plume, Pearce 2008), split at Nb/Zr 0.04, 0.0627 and 0.15 (Sun
et al.) into N-MORB, the transition, OIB and E-MORB, and mantle plume
basalts; past 0.11 on an enriched source the intracontinental rift
(La/Yb 20 separating enriched tholeiitic from alkali basalt, Saputro et
al.) and, past Th/Nb 0.67, the continental extensional zone / initial
rift basalts or alkaline arc; past 0.11 below 0.0627 the arcs, the
continental arc (ACM) above a diagonal from the primitive mantle and
the island arc (IA) below it.

Provenance
----------
The ratios are printed on the figure and used as printed: Th/Nb 0.04,
0.11 and 0.67, Nb/Zr 0.04, 0.0627 (PM) and 0.15, and La/Yb 20.  The
lengths of the lines and the diagonal were measured on Figure 5 (a
2205 x 1665 raster), calibrated on the labelled lines Th/Nb 0.04, 0.11
and 0.67 (773.4 px per decade) and the frame at Nb/Zr 0.01 and 1 (774
px per decade); the right edge lands on Th/Nb 4.985:

* Nb/Zr 0.0627 is the McDonough & Sun (1995) primitive mantle,
  0.658/10.5 = 0.06267, and the figure's PM dot (measured at Th/Nb
  0.1206, Nb/Zr 0.0630) is that composition, Th/Nb 0.0795/0.658 =
  0.1208;
* Nb/Zr 0.15 runs only across the array, Th/Nb 0.04-0.11; 0.0627 and
  0.04 from Th/Nb 0.04 to the right edge; Th/Nb 0.67 from Nb/Zr 0.0627
  up to the top;
* the diagonal is straight on the log axes from the PM dot to the lower
  right corner (5, 0.01): fitted along its length, slope -0.4936 against
  the -0.4931 those two points give, residuals under a pixel.

The paper's own Figure 7 (1895 x 1384 raster), measured afterwards and
on its own -- 650.3 px per decade on its lines Th/Nb 0.04, 0.11 and
0.67 -- agrees: Nb/Zr lines at 0.0625 and 0.0397, each line spanning
what is drawn here and no more, the PM dot at (0.121, 0.064), the
diagonal's slope -0.4940 and its end at Nb/Zr 0.0100.  It also draws
Wei et al.'s (2014) mixing lines A and B and boxes for the mantle
sources, which are interpretation rather than boundaries and are left
out.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from ...normalizations import MULTIELEMENT_NORMS
from .base import Diagram, resolve_column
from .li2025 import LA_YB_RIFT, TH_NB_ARRAY, TH_NB_LITHOSPHERIC

_PM = MULTIELEMENT_NORMS["Primitive Mantle (McDonough & Sun 1995)"]

#: Enriched | slightly enriched mantle source, the primitive mantle.
NB_ZR_PM = _PM["Nb"] / _PM["Zr"]
#: Slightly enriched (the transition) | depleted mantle source.
NB_ZR_DEPLETED = 0.04
#: OIB and E-MORB | mantle plume basalts, inside the array (Sun et al.).
NB_ZR_PLUME = 0.15

#: The primitive mantle dot, where the arc diagonal starts.
PM_POINT = (_PM["Th"] / _PM["Nb"], NB_ZR_PM)

X_RANGE = (0.015, 5.0)
Y_RANGE = (0.01, 1.0)

#: Continental arc (above) | island arc (below): from the PM dot to the
#: lower right corner, straight on the log axes.
DIAGONAL = (PM_POINT, (X_RANGE[1], Y_RANGE[0]))

TRANSITION = "transition (slightly enriched source)"

_LINE = dict(color="#333", linewidth=1.0, zorder=1)


def diagonal_nb_zr(th_nb):
    """Nb/Zr on the ACM | IA diagonal at the given Th/Nb."""
    (x0, y0), (x1, y1) = DIAGONAL
    slope = np.log10(y1 / y0) / np.log10(x1 / x0)
    return y0 * (np.asarray(th_nb, float) / x0) ** slope


def mantle_source(nb_zr: float) -> str:
    """The mantle source Figure 5's right-hand brackets name."""
    if not np.isfinite(nb_zr) or nb_zr <= 0:
        return ""
    if nb_zr >= NB_ZR_PM:
        return "enriched mantle source"
    if nb_zr >= NB_ZR_DEPLETED:
        return "slightly enriched mantle source"
    return "depleted mantle source"


def classify(th_nb: float, nb_zr: float, *,
             la_yb: Optional[float] = None) -> str:
    """The setting Figure 5 names for one sample; "" without a ratio.

    La/Yb splits the rift field into enriched tholeiitic and alkali
    basalt; without it the field is named whole.  An arc sample carries
    its mantle source, depleted or slightly enriched.
    """
    if not (np.isfinite(th_nb) and np.isfinite(nb_zr)) or th_nb <= 0 \
            or nb_zr <= 0:
        return ""
    low, high = TH_NB_ARRAY
    if th_nb < low:
        return "source modification or contamination"
    if th_nb < high:
        if nb_zr >= NB_ZR_PLUME:
            return "mantle plume basalts"
        if nb_zr >= NB_ZR_PM:
            return "OIB and E-MORB"
        return TRANSITION if nb_zr >= NB_ZR_DEPLETED else "N-MORB"
    if nb_zr >= NB_ZR_PM:
        if th_nb < TH_NB_LITHOSPHERIC:
            name = "intracontinental rift"
            if la_yb is not None and np.isfinite(la_yb):
                name += (" (alkali basalt)" if la_yb > LA_YB_RIFT
                         else " (enriched tholeiitic)")
            return name
        return ("continental extensional zone / initial rift basalts "
                "or alkaline arc")
    name = ("continental arc (ACM)" if nb_zr > diagonal_nb_zr(th_nb)
            else "island arc (IA)")
    return f"{name}, {mantle_source(nb_zr)}"


class Godang2024NbZrThNb(Diagram):
    key = "godang2024_nbzr_thnb"
    title = "Nb/Zr vs Th/Nb — Godang et al. (2024)"
    citation = ("Godang, Saputro & Li (2024) Solid Earth Sciences 9(3) "
                "100199, after Saputro et al. (2022) and Sun et al. "
                "(2006); as Li et al. (2025) Lithosphere Fig. 5. For "
                "mafic to felsic igneous rocks. Nb/Zr 0.0627 (primitive "
                "mantle) and 0.04 divide enriched, slightly enriched and "
                "depleted sources; Th/Nb 0.04-0.11 is the array of "
                "non-subduction basalts, Nb/Zr 0.15 separating mantle "
                "plume basalts; Th/Nb 0.67 separates intracontinental "
                "rift (La/Yb 20: enriched tholeiitic | alkali basalt) "
                "from continental extension or alkaline arc; below "
                "0.0627 the diagonal from PM separates continental arc "
                "from island arc.")
    x_label = "Th/Nb"
    y_label = "Nb/Zr"
    x_range = X_RANGE
    y_range = Y_RANGE
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        th = resolve_column(df, ["Th"])
        nb = resolve_column(df, ["Nb"])
        zr = resolve_column(df, ["Zr"])
        if not (th and nb and zr):
            return None, None
        nb_s = pd.to_numeric(df[nb], errors="coerce")
        return (pd.to_numeric(df[th], errors="coerce") / nb_s,
                nb_s / pd.to_numeric(df[zr], errors="coerce"))

    def classify_frame(self, df: pd.DataFrame) -> pd.Series:
        """The setting of every sample, using La/Yb where the dataset
        has La and Yb."""
        x, y = self._compute_xy(df)
        if x is None:
            return pd.Series("", index=df.index, dtype=object)
        la, yb = resolve_column(df, ["La"]), resolve_column(df, ["Yb"])
        la_yb = (pd.to_numeric(df[la], errors="coerce")
                 / pd.to_numeric(df[yb], errors="coerce")
                 if la and yb else pd.Series(np.nan, index=df.index))
        return pd.Series([classify(a, b, la_yb=c)
                          for a, b, c in zip(x, y, la_yb)],
                         index=df.index, dtype=object)

    def _draw_background(self, ax, options):
        x_lo, x_hi = X_RANGE
        y_lo, y_hi = Y_RANGE
        low, high = TH_NB_ARRAY
        ax.plot([low, low], [y_lo, y_hi], **_LINE)
        ax.plot([high, high], [y_lo, y_hi], color="#333", linewidth=2.2,
                zorder=1)
        ax.plot([TH_NB_LITHOSPHERIC] * 2, [NB_ZR_PM, y_hi], **_LINE)
        ax.plot([low, high], [NB_ZR_PLUME] * 2, **_LINE)
        ax.plot([low, x_hi], [NB_ZR_PM] * 2, **_LINE)
        ax.plot([low, x_hi], [NB_ZR_DEPLETED] * 2, **_LINE)
        (x0, y0), (x1, y1) = DIAGONAL
        ax.plot([x0, x1], [y0, y1], **_LINE)

        ax.scatter([PM_POINT[0]], [PM_POINT[1]], s=55, c="#7b2d8e",
                   edgecolors="white", linewidths=0.6, zorder=4)
        ax.annotate("PM", PM_POINT, xytext=(-2, 6),
                    textcoords="offset points", fontsize=8,
                    color="#7b2d8e", fontweight="bold", zorder=4)

        # Th/Nb < 0.04, its arrow pointing away from the array
        ax.annotate("", xy=(0.017, 0.5), xytext=(low, 0.5),
                    arrowprops=dict(arrowstyle="-|>", color="#333",
                                    linewidth=1.0), zorder=2)
        ax.text(0.0245, 0.44, "source modification\nor contamination",
                fontsize=6.5, color="#333", ha="center", va="top",
                style="italic", zorder=2)

        text = dict(fontsize=7.5, color="#333", ha="center", va="center",
                    style="italic", zorder=2)
        ax.text(0.066, 0.35, "Mantle plume\nbasalts", **text)
        ax.text(0.066, 0.085, "OIB and\nE-MORB", **text)
        ax.text(0.066, 0.02, "N-MORB", **text)
        ax.text(low * 0.96, 0.06, "array of basalts from non-subduction "
                "settings\n(N-MORB to mantle plume; Pearce 2008)",
                rotation=90, fontsize=6.5, color="#555", ha="right",
                va="center", zorder=2)
        ax.text(0.27, 0.68, "Intracontinental rift\n(enriched tholeiitic "
                "&\nalkali basalts)", **text)
        ax.text(0.27, 0.46, "La/Yb < 20 enriched tholeiitic\n"
                "La/Yb > 20 alkali basalt", fontsize=6.5, color="#333",
                ha="center", va="center", zorder=2)
        ax.text(1.8, 0.25, "Continental extensional\nzone / initial rift "
                "basalts\nor alkaline arc", **text)
        ax.text(1.4, 0.0185, "Continental arc (ACM)", rotation=-27,
                **text)
        ax.text(1.2, 0.0128, "Island arc (IA)", rotation=-27, **text)
        ax.text(1.6, 0.05, "— transition —", fontsize=7, color="#333",
                ha="center", va="center", zorder=2)

        line_label = dict(fontsize=6.5, color="#333", rotation=90,
                          ha="right", va="top", zorder=2)
        for th_nb in (*TH_NB_ARRAY, TH_NB_LITHOSPHERIC):
            ax.text(th_nb * 0.97, y_hi * 0.97, f"Th/Nb = {th_nb:g}",
                    **line_label)
        ax.text(low * 1.03, NB_ZR_PLUME * 1.04, "Nb/Zr = 0.15",
                fontsize=6.5, color="#333", ha="left", va="bottom",
                zorder=2)
        for nb_zr, label in ((NB_ZR_PM, "Nb/Zr = 0.0627 (PM)"),
                             (NB_ZR_DEPLETED, "Nb/Zr = 0.04")):
            ax.text(x_hi * 0.97, nb_zr * 1.04, label, fontsize=6.5,
                    color="#333", ha="right", va="bottom", zorder=2)

        source = dict(fontsize=7, color="#1f3a93", rotation=90,
                      ha="center", va="center", style="italic", zorder=2)
        ax.text(4.35, 0.25, "enriched mantle source", **source)
        ax.text(4.35, 0.0205, "depleted\nmantle source", **source)
        ax.text(x_hi * 0.97, 0.0505, "slightly", fontsize=6.5,
                color="#1f3a93", ha="right", va="center", style="italic",
                zorder=2)
