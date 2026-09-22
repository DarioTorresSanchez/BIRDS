"""High-Mg subdivision of Le Maitre (2002) — MgO vs Na2O + K2O.

The IUGS rule for naming the magnesian end of the volcanic series.
Unlike the diagrams whose boundaries are drawn curves, this one is a
picture of a *definition*, so its limits are the round numbers the
classification states:

======================  ==========  =================  ============
Rock                    MgO wt.%    Na2O + K2O wt.%    TiO2 wt.%
======================  ==========  =================  ============
Picrite                 > 12        < 3                —
Komatiite               > 18        < 2                < 1
Meimechite              > 18        < 2                > 1
======================  ==========  =================  ============

Komatiite and meimechite share the same area on this plane — TiO2 is
what separates them, and it is not one of the axes — so the inner field
carries both names with their TiO2 criteria, exactly as the source
figure labels it.

Provenance
----------
Checked against the published figure rather than assumed.  Its axes
were calibrated on their own labels and every drawn limit lands on the
definitional value: the vertical line at MgO 17.92, the horizontal at
Na2O + K2O 2.05, the left edge of the shaded field at MgO 12.01 and
its dashed top at 3.00.  All four agree with the stated rule to well
inside the reading precision of the figure, so the round values are
used here rather than the pixel measurements.

The visible range is deliberately a little wider than the figure, which
is cropped to the picrite envelope itself (MgO 12-30, alkalis 0-3).  A
sample that fails one of the criteria has to stay on screen to be seen
failing it; clipping it away would leave the sample counter reporting a
point nobody can find.
"""

from __future__ import annotations

import pandas as pd

from .base import Diagram, PlotOptions, resolve_column

# --------------------------------------------------------------------------
# The IUGS limits.  Named rather than inlined so the classification reads
# the same way the definition does.
# --------------------------------------------------------------------------

#: Lowest MgO for a picrite.
PICRITE_MGO = 12.0

#: Highest total alkalis for a picrite.
PICRITE_ALKALIS = 3.0

#: Lowest MgO for a komatiite or meimechite.
KOMATIITE_MGO = 18.0

#: Highest total alkalis for a komatiite or meimechite.
KOMATIITE_ALKALIS = 2.0

#: TiO2 dividing komatiite (below) from meimechite (above).
MEIMECHITE_TIO2 = 1.0

_LINE = dict(color="#444", linewidth=1.0, alpha=0.9, zorder=1)


class HighMgTAS(Diagram):
    key = "highmg_tas"
    title = "High-Mg subdivision – MgO vs Na$_2$O + K$_2$O"
    citation = ("Le Maitre, R.W. (ed.) (2002) Igneous Rocks: A "
                "Classification and Glossary of Terms, 2nd ed., CUP.  "
                "IUGS high-Mg subdivision: picrite MgO > 12 and "
                "Na₂O+K₂O < 3; komatiite and meimechite MgO > 18 and "
                "Na₂O+K₂O < 2, separated by TiO₂ = 1 wt.% (meimechite "
                "above).  TiO₂ is not an axis here, so the inner field "
                "carries both names.")
    x_label = "MgO (wt.%)"
    y_label = "Na$_2$O + K$_2$O (wt.%)"
    x_range = (8.0, 36.0)
    y_range = (0.0, 5.0)
    field_label_fontsize = 7.5

    def _compute_xy(self, df):
        mg = resolve_column(df, ["MgO"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if mg is None or na is None or k is None:
            return None, None
        mgo = pd.to_numeric(df[mg], errors="coerce")
        alkalis = (pd.to_numeric(df[na], errors="coerce")
                   + pd.to_numeric(df[k], errors="coerce"))
        return mgo, alkalis

    def _draw_background(self, ax, options: PlotOptions) -> None:
        x_hi = self.x_range[1]

        # Picrite envelope: MgO > 12 up to the alkali ceiling of 3.
        ax.plot([PICRITE_MGO, PICRITE_MGO], [0.0, PICRITE_ALKALIS], **_LINE)
        ax.plot([PICRITE_MGO, x_hi], [PICRITE_ALKALIS, PICRITE_ALKALIS],
                linestyle=(0, (5, 4)), **_LINE)

        # Komatiite / meimechite box: MgO > 18 under an alkali ceiling of 2.
        ax.plot([KOMATIITE_MGO, KOMATIITE_MGO], [0.0, KOMATIITE_ALKALIS],
                **_LINE)
        ax.plot([KOMATIITE_MGO, x_hi], [KOMATIITE_ALKALIS,
                                        KOMATIITE_ALKALIS], **_LINE)

        ax.text(14.6, 2.35, "Picrite", ha="center", va="center",
                fontsize=self.field_label_fontsize, color="#333", zorder=2)
        ax.text(25.0, 1.30,
                "Meimechite, TiO$_2$ > 1 wt.%\nKomatiite, TiO$_2$ < 1 wt.%",
                ha="center", va="center", linespacing=1.4,
                fontsize=self.field_label_fontsize, color="#333", zorder=2)

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    @staticmethod
    def classify(mgo: float, alkalis: float,
                 tio2: float | None = None) -> str:
        """Name one analysis under the IUGS rule.

        *tio2* is optional: without it a komatiite and a meimechite are
        indistinguishable, and saying so is better than picking one.
        """
        if pd.isna(mgo) or pd.isna(alkalis):
            return ""
        if mgo > KOMATIITE_MGO and alkalis < KOMATIITE_ALKALIS:
            if tio2 is None or pd.isna(tio2):
                return "Komatiite / meimechite"
            return ("Meimechite" if tio2 > MEIMECHITE_TIO2
                    else "Komatiite")
        if mgo > PICRITE_MGO and alkalis < PICRITE_ALKALIS:
            return "Picrite"
        return ""
