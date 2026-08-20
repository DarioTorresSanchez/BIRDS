"""Frost et al. (2001) / Frost & Frost (2008) granitoid classification.

Four diagrams plotted in a 2 x 2 grid:
  (a) Fe-index   = FeO* / (FeO* + MgO)         vs SiO2
  (b) MALI       = Na2O + K2O - CaO            vs SiO2
  (c) ASI        = Al / (Ca - 1.67P + Na + K)  vs SiO2  (molar)
  (d) AI vs FSSI: AI = Al - (K + Na) molar
                  FSSI = Q - (Lc + 2*(Ne + Kp)) / 100  (from CIPW norm)

FSSI is taken from the CIPW norm if columns Q, Lc, Ne, Kp are present;
otherwise the panel renders an empty axis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from .base import Diagram, PlotOptions, get_groups, resolve_column


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
        # Molar
        al_m = _to_num(df, al) / 101.96 * 2.0
        na_m = _to_num(df, na) / 61.98 * 2.0
        k_m = _to_num(df, k) / 94.20 * 2.0
        ca_m = _to_num(df, ca) / 56.08
        p_m = _to_num(df, p2) / 141.95 * 2.0 if p2 else 0.0
        asi = al_m / (ca_m - 1.67 * p_m + na_m + k_m)
        return _to_num(df, si), asi

    def _ai_fssi(self, df):
        al = resolve_column(df, ["Al2O3"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        q = resolve_column(df, ["Q", "q", "Quartz"])
        lc = resolve_column(df, ["Lc", "lc", "Leucite"])
        ne = resolve_column(df, ["Ne", "ne", "Nepheline"])
        kp = resolve_column(df, ["Kp", "kp", "Kaliophilite"])
        if not (al and na and k):
            return None, None
        al_m = _to_num(df, al) / 101.96 * 2.0
        na_m = _to_num(df, na) / 61.98 * 2.0
        k_m = _to_num(df, k) / 94.20 * 2.0
        ai = al_m - (k_m + na_m)
        if q is None:
            return ai, None
        q_v = _to_num(df, q).fillna(0)
        lc_v = _to_num(df, lc).fillna(0) if lc else 0
        ne_v = _to_num(df, ne).fillna(0) if ne else 0
        kp_v = _to_num(df, kp).fillna(0) if kp else 0
        fssi = (q_v - (lc_v + 2.0 * (ne_v + kp_v))) / 100.0
        return ai, fssi

    # ---------------------------------------------------------------- plot
    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        axes = figure.subplots(2, 2)
        ax_fe, ax_mali, ax_asi, ax_ai = axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]

        # Reference lines
        # Fe-index boundary (Frost & Frost 2008) magnesian/ferroan
        x_si = np.array([45, 80])
        ax_fe.plot(x_si, 0.46 + 0.005 * x_si, color="#b13a3a", lw=1.0,
                   label="Magn / Ferroan")
        # MALI field boundaries (Frost & Frost 2008): three diagonal lines
        # connecting endpoints at SiO2 = 45 and SiO2 = 75 wt.%.
        mali_x = [45, 75]
        ax_mali.plot(mali_x, [-1, 10], color="#b13a3a", lw=0.9, ls="--")
        ax_mali.plot(mali_x, [-3.8, 8], color="#b13a3a", lw=0.9, ls="--")
        ax_mali.plot(mali_x, [-5, 6], color="#b13a3a", lw=0.9, ls="--")
        # Labels placed inside each band at SiO2 ~ 72 (near the right edge
        # where the bands are widest).
        ax_mali.text(72, 11, "alkalic", color="#444", fontsize=7.5)
        ax_mali.text(72, 7.8, "alkali-calcic", color="#444", fontsize=7.5)
        ax_mali.text(72, 5.8, "calc-alkalic", color="#444", fontsize=7.5)
        ax_mali.text(72, 2.0, "calcic", color="#444", fontsize=7.5)

        ax_asi.axhline(1.0, color="#b13a3a", lw=1.0)
        ax_asi.text(48, 1.05, "peraluminous", color="#444", fontsize=8)
        ax_asi.text(48, 0.85, "metaluminous", color="#444", fontsize=8)

        ax_ai.axvline(0.0, color="#b13a3a", lw=0.7, ls="--")
        ax_ai.axhline(0.0, color="#b13a3a", lw=0.7, ls="--")
        ax_ai.text(-2.0, 0.4, "metaluminous\nsilica-saturated", color="#444",
                   fontsize=7.5)
        ax_ai.text(0.5, 0.4, "peralkaline\nsilica-saturated", color="#444",
                   fontsize=7.5)

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

        # Legend only on the first axis
        if options.legend.visible:
            handles, labels_ = ax_fe.get_legend_handles_labels()
            if handles:
                ax_fe.legend(loc=options.legend.location or "best",
                              fontsize=options.legend.font_size)

        figure.tight_layout()
