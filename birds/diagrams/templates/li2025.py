"""Nb/Yb vs Th/Nb tectonic discrimination — Li, Godang & Saputro (2025).

Li, H., Godang, S. & Saputro, S.P. (2025) Revealing unmapped tectonic
settings through geochemical fingerprinting of Th-Nb-Yb.  *Lithosphere*
2025(2), lithosphere_2025_125, doi 10.2113/2025/lithosphere_2025_125
(CC BY 4.0).  Figure 1.

Th/Nb runs across and Nb/Yb up, both on log axes (0.015-10 and
0.1-100), and the diagram is meant for **mafic to felsic** igneous rocks
alike (Section 2.1) -- not for mafic rocks only -- though not as a
primary tool for rocks of continental-collision settings (Section 2.3).

Nine settings: {1} N-MORB, {2} E-MORB, {3} OIB and mantle plume -- the
mantle array of Pearce (2008) at Th/Nb 0.04-0.11 -- {4} intracontinental
rift, {5} island arc, {6} active continental margin, {7} sub-alkaline
enriched tholeiitic (new in the paper), and {8} alkaline arc / {9}
continental extensional setting, which share the field Th/Nb > 0.67 and
Nb/Yb > 6 and are told apart by TiO2 against Al2O3.

Provenance
----------
The paper states most boundaries as ratios, and those are used as
stated: Th/Nb 0.04, 0.11 and 0.67; Nb/Yb 6 (sub-alkaline | alkaline,
from Nb/Y 0.6561 of Pearce 1996) and 4 (slab failure or assimilation
with alkaline magma, from Godang et al.); Th/Yb 0.35 and 0.65 (Barrett &
MacLean), which are straight lines of slope -1 on these log axes; La/Yb
20 inside the rift field; and TiO2 = -1.1610 + 0.1935 Al2O3 between
{8} and {9}.  What the text leaves out was measured on Figure 1 (a
2203 x 2317 raster), its axes calibrated on the labelled lines Th/Nb
0.04, 0.11, 0.67 and the frame at Nb/Yb 0.1 and 100 (717.7 and 718.7
px per decade, the labelled lines landing within 2 px):

* the lower horizontal, between N-MORB and E-MORB, at Nb/Yb 1.49 --
  the primitive mantle of McDonough & Sun (1995), 0.658/0.441 = 1.492,
  whose point the figure plots on it;
* the right side of field {7}: Th/Nb 0.24, from Nb/Yb 6 down to where
  Th/Yb = 0.65 takes over (0.65/0.24 = 2.71; measured 2.69);
* the magmatic-interaction line of Wei et al. between asthenospheric and
  lithospheric mantle sources, its eleven 0-100 % points;
* the AFC and subduction vectors of Pearce (2008), as drawn.

The reference stars are Sun & McDonough's (1989) N-MORB, E-MORB and
OIB, the PM McDonough & Sun's (1995); the figure's stars land on them.
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from ...normalizations import MULTIELEMENT_NORMS
from .base import Diagram, resolve_column

#: Mantle array: Th/Nb 0.04-0.11.  Above 0.67 (with Nb/Yb > 6), the
#: enriched lithospheric mantle source.
TH_NB_ARRAY = (0.04, 0.11)
TH_NB_LITHOSPHERIC = 0.67

#: Sub-alkaline | alkaline.
NB_YB_ALKALINE = 6.0
#: Slab failure or assimilation with alkaline magma, Nb/Yb > 4.
NB_YB_SLAB = 4.0

_PM = MULTIELEMENT_NORMS["Primitive Mantle (McDonough & Sun 1995)"]
#: N-MORB | E-MORB, through the primitive mantle (measured 1.489).
NB_YB_PM = _PM["Nb"] / _PM["Yb"]

#: Island arc | transitional | continental arc (Barrett & MacLean).
TH_YB_ARC = (0.35, 0.65)

#: Right side of the sub-alkaline enriched tholeiitic field, measured.
TH_NB_FIELD7 = 0.24

#: Enriched tholeiitic | alkali basalt inside the rift field.
LA_YB_RIFT = 20.0

#: TiO2 = a + b Al2O3 (wt %): above it continental extensional, below
#: it alkaline arc (Shaban et al., after Müller & Groves).
TIO2_AL2O3 = (-1.1610, 0.1935)

#: Wei et al.'s interaction line, 0 % (asthenospheric) to 100 %
#: (lithospheric) in steps of 10, as (Th/Nb, Nb/Yb), measured.
INTERACTION_LINE = (
    (0.0859, 12.950), (0.1106, 11.298), (0.1418, 9.851), (0.1794, 8.519),
    (0.2252, 7.273), (0.2845, 6.107), (0.3625, 5.047), (0.4710, 4.074),
    (0.5872, 3.387), (0.7212, 2.833), (0.8803, 2.355),
)

#: Pearce's (2008) vectors as Figure 1 draws them, measured.
AFC_VECTOR = ((0.402, 0.977), (0.535, 1.122), (0.647, 1.235),
              (0.758, 1.359), (0.882, 1.496), (0.98, 1.647), (1.093, 1.814),
              (1.201, 1.996), (1.308, 2.198), (1.424, 2.42), (1.518, 2.664),
              (1.604, 2.932), (1.672, 3.228), (1.743, 3.554), (1.788, 3.913),
              (1.871, 4.742))
SUBDUCTION_VECTOR = ((0.447, 0.783), (0.797, 0.851), (0.966, 0.885),
                     (1.171, 0.905), (1.420, 0.934), (1.721, 0.968))

X_RANGE = (0.015, 10.0)
Y_RANGE = (0.1, 100.0)

_REFERENCES = {
    "N-MORB": "N-MORB (Sun & McDonough 1989)",
    "E-MORB": "E-MORB (Sun & McDonough 1989)",
    "PM": "Primitive Mantle (McDonough & Sun 1995)",
}
#: Sun & McDonough (1989) OIB, not among the normalisers.
_OIB = {"Th": 4.0, "Nb": 48.0, "Yb": 2.16}

_LINE = dict(color="#333", linewidth=1.0, zorder=1)


def reference_points() -> dict:
    """(Th/Nb, Nb/Yb) of the reference compositions Figure 1 plots."""
    out = {}
    for label, name in _REFERENCES.items():
        r = MULTIELEMENT_NORMS[name]
        out[label] = (r["Th"] / r["Nb"], r["Nb"] / r["Yb"])
    out["OIB"] = (_OIB["Th"] / _OIB["Nb"], _OIB["Nb"] / _OIB["Yb"])
    return out


def classify(th_nb: float, nb_yb: float, *, la_yb: Optional[float] = None,
             tio2: Optional[float] = None,
             al2o3: Optional[float] = None) -> str:
    """The setting Figure 1 names for one sample; "" outside its fields.

    La/Yb splits the rift field into enriched tholeiitic and alkali
    basalt, and TiO2 against Al2O3 the lithospheric field into
    continental extensional and alkaline arc; without them those fields
    are named whole.  Between Nb/Yb 4 and 6 an arc sample is flagged as
    slab failure or assimilation with alkaline magma.
    """
    if not (np.isfinite(th_nb) and np.isfinite(nb_yb)) or th_nb <= 0 \
            or nb_yb <= 0:
        return ""
    low, high = TH_NB_ARRAY
    if th_nb < low:
        return ""
    if th_nb < high:
        if nb_yb < NB_YB_PM:
            return "N-MORB"
        return "E-MORB" if nb_yb < NB_YB_ALKALINE else "OIB / mantle plume"
    if nb_yb >= NB_YB_ALKALINE:
        if th_nb < TH_NB_LITHOSPHERIC:
            name = "intracontinental rift"
            if la_yb is not None and np.isfinite(la_yb):
                name += (" (alkali basalt)" if la_yb > LA_YB_RIFT
                         else " (enriched tholeiitic)")
            return name
        if tio2 is not None and al2o3 is not None \
                and np.isfinite(tio2) and np.isfinite(al2o3):
            a, b = TIO2_AL2O3
            return ("continental extensional setting"
                    if tio2 > a + b * al2o3 else "alkaline arc")
        return "continental extensional setting / alkaline arc"
    if th_nb < TH_NB_FIELD7 and nb_yb >= NB_YB_PM:
        return "sub-alkaline enriched tholeiitic"
    th_yb = th_nb * nb_yb
    if th_yb < TH_YB_ARC[0]:
        name = "island arc (tholeiitic)"
    elif th_yb < TH_YB_ARC[1]:
        name = "island arc to continental arc (transitional)"
    else:
        name = "continental arc / ACM (calc-alkaline)"
    if nb_yb >= NB_YB_SLAB:
        name += ", slab failure or alkaline assimilation"
    return name


class Li2025NbYbThNb(Diagram):
    key = "li2025_nbyb_thnb"
    title = "Nb/Yb vs Th/Nb — Li et al. (2025)"
    citation = ("Li, Godang & Saputro (2025) Lithosphere 2025(2), "
                "lithosphere_2025_125, Fig. 1. For mafic to felsic "
                "igneous rocks; a supporting tool only for "
                "continental-collision settings. Th/Nb 0.04-0.11 is the "
                "mantle array; Nb/Yb 6 divides sub-alkaline from "
                "alkaline and Th/Yb 0.35 / 0.65 island arc, transitional "
                "and continental arc. In the rift field La/Yb 20 divides "
                "enriched tholeiitic from alkali basalt; above Th/Nb "
                "0.67, TiO2 > -1.1610 + 0.1935 Al2O3 is continental "
                "extensional, below it alkaline arc.")
    x_label = "Th/Nb"
    y_label = "Nb/Yb"
    x_range = X_RANGE
    y_range = Y_RANGE
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        th = resolve_column(df, ["Th"])
        nb = resolve_column(df, ["Nb"])
        yb = resolve_column(df, ["Yb"])
        if not (th and nb and yb):
            return None, None
        nb_s = pd.to_numeric(df[nb], errors="coerce")
        return (pd.to_numeric(df[th], errors="coerce") / nb_s,
                nb_s / pd.to_numeric(df[yb], errors="coerce"))

    def classify_frame(self, df: pd.DataFrame) -> pd.Series:
        """The setting of every sample, using La, TiO2 and Al2O3 where
        the dataset has them."""
        x, y = self._compute_xy(df)
        if x is None:
            return pd.Series("", index=df.index, dtype=object)

        def column(names):
            col = resolve_column(df, names)
            return (pd.to_numeric(df[col], errors="coerce") if col
                    else pd.Series(np.nan, index=df.index))

        la_yb = column(["La"]) / column(["Yb"])
        tio2, al2o3 = column(["TiO2"]), column(["Al2O3"])
        return pd.Series(
            [classify(a, b, la_yb=c, tio2=d, al2o3=e)
             for a, b, c, d, e in zip(x, y, la_yb, tio2, al2o3)],
            index=df.index, dtype=object)

    def _draw_background(self, ax, options):
        x_lo, x_hi = X_RANGE
        y_lo, y_hi = Y_RANGE
        low, high = TH_NB_ARRAY
        ax.plot([low, low], [y_lo, y_hi], **_LINE)
        ax.plot([high, high], [y_lo, y_hi], **_LINE)
        ax.plot([TH_NB_LITHOSPHERIC] * 2, [NB_YB_ALKALINE, y_hi], **_LINE)
        ax.plot([0.027, x_hi], [NB_YB_ALKALINE] * 2, color="#7b1f1f",
                linewidth=1.3, zorder=1)
        ax.plot([TH_NB_FIELD7, x_hi], [NB_YB_SLAB] * 2, color="#e66a1e",
                linewidth=1.3, zorder=1)
        # N-MORB | E-MORB, then island arc below Th/Yb 0.35
        corner_35 = TH_YB_ARC[0] / NB_YB_PM
        ax.plot([0.0325, corner_35], [NB_YB_PM] * 2, **_LINE)
        ax.plot([corner_35, TH_YB_ARC[0] / y_lo], [NB_YB_PM, y_lo], **_LINE)
        # field {7}, then calc-alkaline above Th/Yb 0.65
        corner_65 = TH_YB_ARC[1] / TH_NB_FIELD7
        ax.plot([TH_NB_FIELD7] * 2, [NB_YB_ALKALINE, corner_65], **_LINE)
        ax.plot([TH_NB_FIELD7, TH_YB_ARC[1] / y_lo], [corner_65, y_lo],
                **_LINE)

        # Wei et al.'s interaction line, with its 10 % steps
        xs, ys = zip(*INTERACTION_LINE)
        ax.plot(xs, ys, color="black", linewidth=1.1, marker="o",
                markersize=3, zorder=2)
        for pct, (x, y) in zip(range(10, 101, 10), INTERACTION_LINE[1:]):
            ax.annotate(f"{pct}%", (x, y), xytext=(4, 3),
                        textcoords="offset points", fontsize=6.5,
                        style="italic", zorder=2)
        ax.text(0.30, 9.0, "magmatic interaction between\nasthenospheric "
                "and lithospheric\nmantle sources", fontsize=7,
                color="#1f3a93", rotation=-28, ha="center", va="center")

        for path, colour, label in ((AFC_VECTOR, "#2aa7d6", "AFC vector"),
                                    (SUBDUCTION_VECTOR, "black",
                                     "subduction vector")):
            xs, ys = zip(*path)
            ax.plot(xs[:-1], ys[:-1], color=colour, linewidth=1.2, zorder=2)
            ax.annotate("", xy=path[-1], xytext=path[-2],
                        arrowprops=dict(arrowstyle="-|>", color=colour,
                                        linewidth=1.2), zorder=2)
            ax.annotate(label, path[-1], xytext=(4, -10 if colour == "black"
                                                 else 4),
                        textcoords="offset points", fontsize=7,
                        color=colour, zorder=2)

        for name, (x, y) in reference_points().items():
            marker, colour = ("o", "#7b2d8e") if name == "PM" else ("*",
                                                                    "black")
            ax.scatter([x], [y], marker=marker, s=60, c=colour, zorder=4,
                       edgecolors="white", linewidths=0.6)
            ax.annotate(name, (x, y), xytext=(5, 4),
                        textcoords="offset points", fontsize=7.5,
                        color=colour, zorder=4)

        text = dict(fontsize=7.5, color="#333", ha="center", va="center",
                    zorder=2)
        ax.text(0.066, 50, "N-MORB, E-MORB,\nOIB, mantle plume", **text)
        ax.text(0.27, 50, "Intracontinental rift\nLa/Yb < 20 enriched "
                "tholeiitic\nLa/Yb > 20 alkali basalt", **text)
        ax.text(2.6, 25, "Continental extensional zone /\ninitial rift "
                "basalts or alkaline arc", **text)
        ax.text(0.165, 3.0, "sub-alkaline\nenriched\ntholeiitic", **text)
        ax.text(2.0, 1.5, "Continental arc (ACM)", **text)
        ax.text(0.4, 0.25, "Island arc (IA)", **text)
        ax.text(3.2, 0.35, "Tholeiitic", rotation=-45, **text)
        ax.text(4.3, 0.42, "Transitional", rotation=-45, **text)
        ax.text(5.6, 0.6, "Calc-alkaline", rotation=-45, **text)
        ax.text(2.2, NB_YB_SLAB * 1.12, "slab failure or assimilation "
                "with alkaline magma (Nb/Yb > 4)", fontsize=6.5,
                color="#e66a1e", ha="center", zorder=2)
        for name, y in (("N-MORB", 0.9), ("E-MORB", 3.0),
                        ("OIB / plume", 25)):
            ax.text(0.047, y, name, rotation=90, fontsize=7, color="#555",
                    ha="center", va="center", zorder=2)
        line_label = dict(fontsize=6.5, color="#333", rotation=90,
                          ha="right", va="bottom", zorder=2)
        for th_nb in (*TH_NB_ARRAY, TH_NB_LITHOSPHERIC):
            ax.text(th_nb * 0.97, 0.105 if th_nb < 0.5 else 6.4,
                    f"Th/Nb = {th_nb:g}", **line_label)
        ax.text(x_hi * 0.97, NB_YB_ALKALINE * 1.05, "Nb/Yb = 6",
                fontsize=7, color="#7b1f1f", ha="right", va="bottom",
                zorder=2)
        for th_yb in TH_YB_ARC:
            ax.text(th_yb / 0.13 * 0.9, 0.13, f"Th/Yb = {th_yb:g}",
                    fontsize=6.5, color="#333", rotation=-45, ha="center",
                    va="center", zorder=2)
        ax.text(0.019, 15, "alkaline", rotation=90, color="#7b1f1f",
                fontsize=8, ha="center", zorder=2)
        ax.text(0.019, 2.4, "sub-alkaline", rotation=90, color="#7b1f1f",
                fontsize=8, ha="center", zorder=2)
