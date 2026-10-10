"""Frost et al. (2001) / Frost & Frost (2008) granitoid classification.

Four diagrams plotted in a 2 x 2 grid:
  (a) Fe-index   = FeO* / (FeO* + MgO)         vs SiO2
  (b) MALI       = Na2O + K2O - CaO            vs SiO2
  (c) ASI        = Al / (Ca - 1.67P + Na + K)  vs SiO2  (molar)
  (d) AI vs FSSI: AI = Al - (K + Na) molar
                  FSSI = Q - (Lc + 2*(Ne + Kp)) / 100  (from CIPW norm)

FSSI is taken from the CIPW norm if columns Q, Lc, Ne, Kp are present;
otherwise the panel renders an empty axis.

ASI is Shand's index, A/CNK, with Ca in apatite taken out: molecular
Al2O3 / (CaO - 1.67 P + Na2O + K2O), P per atom.  It is 1 for every
feldspar, which is what ASI = 1 between metaluminous and peraluminous
means.  It used to double Al, Na and K to cations and leave Ca alone,
which put anorthite at 2 and a granite at A/CNK 1.03 at 1.23.  AI is
still on the cation basis, Al - (Na + K) per atom; only its sign is
read, and the sign is the same on either basis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from .base import (
    Diagram,
    PlotOptions,
    draw_note,
    get_groups,
    normative,
    normative_note,
    resolve_column,
)


#: Magnesian / ferroan divide, as Frost & Frost (2008) publish it:
#: ``Fe-index = 0.46 + 0.005 · SiO2``.
FE_INDEX_INTERCEPT, FE_INDEX_SLOPE = 0.46, 0.005

# --------------------------------------------------------------------------
# MALI boundaries
# --------------------------------------------------------------------------
# These are the one part of this diagram with no published equation — the
# source draws them as curves.  Measured from Rollinson & Pease (2021)
# Figure 3.9b: the panel was calibrated on its own tick marks, the three
# blue curves separated by colour and traced column by column, then
# resampled onto a common SiO2 grid.  The nine-point polylines reproduce
# the traced curves to within 0.14 MALI.
#
# They replace three straight lines drawn between invented endpoints at
# SiO2 45 and 75, which had the wrong shape as well as the wrong values:
# the published boundaries flatten towards high silica.

MALI_BOUNDARIES = {
    "alkalic / alkali-calcic": (
        (52.0, 0.74), (55.0, 2.07), (58.0, 3.40), (61.0, 4.73),
        (64.0, 5.98), (67.0, 7.01), (70.0, 8.02), (73.0, 8.86),
        (74.5, 9.24)),
    "alkali-calcic / calc-alkalic": (
        (52.0, -1.91), (55.0, -0.47), (58.0, 1.03), (61.0, 2.38),
        (64.0, 3.70), (67.0, 4.89), (70.0, 6.08), (73.0, 7.01),
        (74.5, 7.48)),
    "calc-alkalic / calcic": (
        (52.0, -4.48), (55.0, -3.00), (58.0, -1.41), (61.0, 0.04),
        (64.0, 1.41), (67.0, 2.73), (70.0, 4.01), (73.0, 5.19),
        (74.5, 5.73)),
}

#: Field names, one per band, placed where the bands are widest.
MALI_LABELS = {
    "alkalic":       (57.0, 5.6),
    "alkali-calcic": (60.0, 3.6),
    "calc-alkalic":  (63.0, 2.5),
    "calcic":        (66.0, 0.2),
}


#: The four quadrants of AI against FSSI, named as Rollinson & Pease
#: (2021) Figure 3.9d names them: FSSI < 0 is silica-undersaturated,
#: AI < 0 is Al-deficient (peralkaline).  Placed at quadrant centres.
AI_FSSI_LABELS = {
    "silica-\nundersaturated\nAl adequate\nto excessive": (-1.25, 0.5),
    "silica-\nsaturated\nAl adequate\nto excessive":      (1.25, 0.5),
    "silica-\nundersaturated\nAl deficient":              (-1.25, -0.5),
    "silica-\nsaturated\nAl deficient":                   (1.25, -0.5),
}

#: Oxide molar masses (g/mol); IUPAC atomic weights give 101.9601,
#: 56.0770, 61.9785, 94.1956 and 141.9425.
MOLAR_MASS = {
    "Al2O3": 101.96,
    "CaO":    56.08,
    "Na2O":   61.98,
    "K2O":    94.20,
    "P2O5":  141.94,
}

#: Ca per P in apatite, as Frost et al. (2001) print it (5/3).
APATITE_CA_PER_P = 1.67


def _to_num(df, col):
    return pd.to_numeric(df[col], errors="coerce")


class Frost(Diagram):
    key = "frost"
    title = "Frost et al. 2001 / Frost & Frost 2008 – Granitoid classification"
    citation = ("Fe-index, MALI, ASI, AI and FSSI plotted as a 2x2 grid. "
                "Compute FSSI from the CIPW norm.")

    # ---------------------------------------------------------------- panels
    def _fe_index(self, df):
        si = resolve_column(df, ["SiO2"])
        feo = resolve_column(df, ["FeO"])
        fe2o3 = resolve_column(df, ["Fe2O3", "Fe2O3T", "Fe2O3t"])
        feoT = resolve_column(df, ["FeOT", "FeOt"])
        mg = resolve_column(df, ["MgO"])
        if not (si and mg and (feo or fe2o3 or feoT)):
            return None, None
        if feoT:
            feo_star = _to_num(df, feoT)
        elif fe2o3 and feo:
            feo_star = _to_num(df, feo) + 0.9 * _to_num(df, fe2o3)
        elif fe2o3:
            feo_star = 0.9 * _to_num(df, fe2o3)
        else:
            feo_star = _to_num(df, feo)
        return _to_num(df, si), feo_star / (feo_star + _to_num(df, mg))

    def _mali(self, df):
        si = resolve_column(df, ["SiO2"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        ca = resolve_column(df, ["CaO"])
        if not (si and na and k and ca):
            return None, None
        return _to_num(df, si), _to_num(df, na) + _to_num(df, k) - _to_num(df, ca)

    def _asi(self, df):
        si = resolve_column(df, ["SiO2"])
        al = resolve_column(df, ["Al2O3"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        ca = resolve_column(df, ["CaO"])
        p2 = resolve_column(df, ["P2O5"])
        if not (si and al and na and k and ca):
            return None, None
        # Molecular proportions of the oxides, so that ASI is Shand's
        # A/CNK and every feldspar has ASI = 1.  Doubling Al, Na and K
        # to cations without doubling Ca made anorthite 2.  P is counted
        # per atom, two per P2O5, against Ca = CaO in apatite.
        al_m = _to_num(df, al) / MOLAR_MASS["Al2O3"]
        na_m = _to_num(df, na) / MOLAR_MASS["Na2O"]
        k_m = _to_num(df, k) / MOLAR_MASS["K2O"]
        ca_m = _to_num(df, ca) / MOLAR_MASS["CaO"]
        p_m = _to_num(df, p2) / MOLAR_MASS["P2O5"] * 2.0 if p2 else 0.0
        asi = al_m / (ca_m - APATITE_CA_PER_P * p_m + na_m + k_m)
        return _to_num(df, si), asi

    def _ai_fssi(self, df):
        al = resolve_column(df, ["Al2O3"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if not (al and na and k):
            return None, None
        al_m = _to_num(df, al) / MOLAR_MASS["Al2O3"] * 2.0
        na_m = _to_num(df, na) / MOLAR_MASS["Na2O"] * 2.0
        k_m = _to_num(df, k) / MOLAR_MASS["K2O"] * 2.0
        ai = al_m - (k_m + na_m)
        norm = normative(df, ("Q",), ("Lc", "Ne", "Kp"))
        if norm is None:
            return ai, None
        # A sample with no norm keeps its NaN quartz and is left off; a
        # blank feldspathoid in a norm the dataset brings is one it lacks.
        lc, ne, kp = (norm[m].fillna(0.0) for m in ("Lc", "Ne", "Kp"))
        fssi = (norm["Q"] - (lc + 2.0 * (ne + kp))) / 100.0
        return ai, fssi

    # ---------------------------------------------------------------- plot
    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        axes = figure.subplots(2, 2)
        ax_fe, ax_mali, ax_asi, ax_ai = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

        # Reference lines
        # Fe-index boundary (Frost & Frost 2008) magnesian/ferroan
        x_si = np.array([45, 80])
        ax_fe.plot(x_si, FE_INDEX_INTERCEPT + FE_INDEX_SLOPE * x_si,
                   color="#b13a3a", lw=1.0, label="Magn / Ferroan")
        for polyline in MALI_BOUNDARIES.values():
            ax_mali.plot([p[0] for p in polyline], [p[1] for p in polyline],
                         color="#b13a3a", lw=0.9)
        for name, (x, y) in MALI_LABELS.items():
            ax_mali.text(x, y, name, color="#444", fontsize=7.5,
                         ha="center", va="center")

        ax_asi.axhline(1.0, color="#b13a3a", lw=1.0)
        ax_asi.text(48, 1.05, "peraluminous", color="#444", fontsize=8)
        ax_asi.text(48, 0.85, "metaluminous", color="#444", fontsize=8)

        ax_ai.axvline(0.0, color="#b13a3a", lw=0.7, ls="--")
        ax_ai.axhline(0.0, color="#b13a3a", lw=0.7, ls="--")
        for name, (x, y) in AI_FSSI_LABELS.items():
            ax_ai.text(x, y, name, color="#444", fontsize=7.5,
                       ha="center", va="center")

        # Data
        if df is not None and not df.empty:
            for label, sub, gs in get_groups(df, plot_style):
                color = gs.color if gs else "#1f77b4"
                marker = gs.marker if gs else "o"
                kwargs = dict(s=plot_style.point_size ** 2,
                              alpha=plot_style.alpha,
                              c=color, marker=marker, label=label,
                              edgecolors="black", linewidths=0.4)
                x, y = self._fe_index(sub)
                if x is not None and y is not None:
                    ax_fe.scatter(x, y, **kwargs)
                x, y = self._mali(sub)
                if x is not None and y is not None:
                    ax_mali.scatter(x, y, **kwargs)
                x, y = self._asi(sub)
                if x is not None and y is not None:
                    ax_asi.scatter(x, y, **kwargs)
                x, y = self._ai_fssi(sub)
                if x is not None and y is not None:
                    ax_ai.scatter(x, y, **kwargs)

        # Axis decoration
        ax_fe.set_xlabel("SiO$_2$ (wt.%)", **options.x_axis.label_kwargs())
        ax_fe.set_ylabel("Fe-index = FeO* / (FeO* + MgO)",
                         **options.y_axis.label_kwargs())
        ax_fe.set_xlim(45, 80)
        ax_fe.set_ylim(0.3, 1.0)
        ax_fe.set_title("(a) Fe-index", fontsize=10)

        ax_mali.set_xlabel("SiO$_2$ (wt.%)", **options.x_axis.label_kwargs())
        ax_mali.set_ylabel("MALI = Na$_2$O + K$_2$O − CaO",
                          **options.y_axis.label_kwargs())
        ax_mali.set_xlim(45, 80)
        ax_mali.set_ylim(-8, 14)
        ax_mali.set_title("(b) MALI", fontsize=10)

        ax_asi.set_xlabel("SiO$_2$ (wt.%)", **options.x_axis.label_kwargs())
        ax_asi.set_ylabel("ASI", **options.y_axis.label_kwargs())
        ax_asi.set_xlim(45, 80)
        ax_asi.set_ylim(0.5, 1.6)
        ax_asi.set_title("(c) Aluminium saturation index", fontsize=10)

        ax_ai.set_xlabel("FSSI", **options.x_axis.label_kwargs())
        ax_ai.set_ylabel("AI (molar Al − Na − K)",
                         **options.y_axis.label_kwargs())
        ax_ai.set_xlim(-2.5, 2.5)
        ax_ai.set_ylim(-1.0, 1.0)
        ax_ai.set_title("(d) AI vs FSSI", fontsize=10)
        note = normative_note(df, ("Q",))
        if note:
            draw_note(ax_ai, note)

        # Legend only on the first axis
        if options.legend.visible:
            handles, labels_ = ax_fe.get_legend_handles_labels()
            if handles:
                ax_fe.legend(loc=options.legend.location or "best",
                              fontsize=options.legend.font_size)

        figure.tight_layout()
