"""Bivariate tectonic discrimination diagrams.

Coordinates compiled from Rollinson & Pease (2021) Chapter 5 figure
captions and the original references cited below each class.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Diagram, resolve_column


# ---------------------------------------------------------------------------
# Pearce (2008) — mafic crustal input and melting depth proxies
# ---------------------------------------------------------------------------

class Pearce2008ThYbNbYb(Diagram):
    key = "pearce2008_thyb_nbyb"
    title = "Th/Yb vs Nb/Yb — Pearce (2008)"
    citation = ("Pearce (2008). MORB-OIB array bounded by Th/Nb ≈ 0.07 "
                "(lower) and 0.32 (upper). Samples plotting above the array "
                "carry a crustal / subduction component.")
    x_label = "Nb/Yb"
    y_label = "Th/Yb"
    x_range = (0.1, 100.0)
    y_range = (0.01, 100.0)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        nb = resolve_column(df, ["Nb"])
        yb = resolve_column(df, ["Yb"])
        th = resolve_column(df, ["Th"])
        if not (nb and yb and th):
            return None, None
        yb_s = pd.to_numeric(df[yb], errors="coerce")
        return (pd.to_numeric(df[nb], errors="coerce") / yb_s,
                pd.to_numeric(df[th], errors="coerce") / yb_s)

    def _draw_background(self, ax, options):
        xs = np.array([0.1, 100.0])
        ax.fill_between(xs, 0.07 * xs, 0.32 * xs,
                        color="#888", alpha=0.10, zorder=0,
                        label="_MORB–OIB array")
        ax.plot(xs, 0.07 * xs, color="#444", linewidth=1.0)
        ax.plot(xs, 0.32 * xs, color="#444", linewidth=1.0)
        # Reference compositions
        for name, x, y in (
            ("N-MORB", 0.76, 0.04),
            ("E-MORB", 2.70, 0.20),
            ("OIB", 22.0, 1.85),
            ("Bulk CC", 16.1, 5.6),
        ):
            ax.scatter([x], [y], marker="*", s=130, c="white",
                       edgecolors="black", linewidths=1.0, zorder=3)
            ax.annotate(name, (x, y), xytext=(6, 6),
                        textcoords="offset points", fontsize=8)
        ax.text(20, 0.45, "MORB–OIB array", fontsize=9,
                style="italic", color="#333")
        ax.text(0.4, 8, "Volcanic-arc / crustal input",
                fontsize=9, style="italic", color="#333", ha="center")


class Pearce2008TiYbNbYb(Diagram):
    key = "pearce2008_tiyb_nbyb"
    title = "Ti/Yb vs Nb/Yb — Pearce (2008)"
    citation = ("Pearce (2008). High Ti/Yb (>≈5000) indicates residual "
                "garnet in the source ⇒ OIB / deep melting; flat MORB array "
                "below indicates spinel-facies melting.")
    x_label = "Nb/Yb"
    y_label = "Ti/Yb (ppm/ppm)"
    x_range = (0.1, 100.0)
    y_range = (1000, 30000)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        nb = resolve_column(df, ["Nb"])
        yb = resolve_column(df, ["Yb"])
        ti_el = resolve_column(df, ["Ti"])
        ti_ox = resolve_column(df, ["TiO2"])
        if not (nb and yb and (ti_el or ti_ox)):
            return None, None
        yb_s = pd.to_numeric(df[yb], errors="coerce")
        if ti_el:
            ti_ppm = pd.to_numeric(df[ti_el], errors="coerce")
        else:
            ti_ppm = pd.to_numeric(df[ti_ox], errors="coerce") * 5995
        return (pd.to_numeric(df[nb], errors="coerce") / yb_s,
                ti_ppm / yb_s)

    def _draw_background(self, ax, options):
        # MORB field ~ Ti/Yb 2000-4500
        ax.axhspan(2000, 4500, color="#88c0d0", alpha=0.12, zorder=0)
        # OIB field above ~5000
        xs = np.array([0.1, 100.0])
        ax.fill_between(xs, 5000, 30000, color="#d08770", alpha=0.08, zorder=0)
        # Discriminant boundary at Ti/Yb ≈ 5000 (Pearce 2008 figure)
        ax.axhline(5000, color="#b13a3a", linewidth=1.2, linestyle="--")
        for name, x, y in (
            ("N-MORB", 0.76, 2495),
            ("E-MORB", 2.70, 2530),
            ("OIB", 22.0, 7970),
        ):
            ax.scatter([x], [y], marker="*", s=130, c="white",
                       edgecolors="black", linewidths=1.0, zorder=3)
            ax.annotate(name, (x, y), xytext=(6, 6),
                        textcoords="offset points", fontsize=8)
        ax.text(15, 12000, "OIB array (garnet residue)",
                fontsize=9, style="italic", color="#333")
        ax.text(15, 2700, "MORB array (spinel facies)",
                fontsize=9, style="italic", color="#333")


# ---------------------------------------------------------------------------
# Pearce & Gale (1977) — mafic within-plate vs plate-margin
# ---------------------------------------------------------------------------

class PearceGale1977(Diagram):
    key = "pearce_gale_1977"
    title = "Ti/Y vs Zr/Y — Pearce & Gale (1977)"
    citation = ("Pearce & Gale (1977). Boundary at Zr/Y ≈ 3 / Ti/Y ≈ 350 "
                "separates within-plate (above) from plate-margin (below) "
                "basalts. Reassessed by Verma (2010): <11 % misclassified "
                "excluding E-MORB.")
    x_label = "Zr/Y"
    y_label = "Ti/Y"
    x_range = (1, 30)
    y_range = (100, 1000)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        zr = resolve_column(df, ["Zr"])
        y = resolve_column(df, ["Y"])
        ti_el = resolve_column(df, ["Ti"])
        ti_ox = resolve_column(df, ["TiO2"])
        if not (zr and y and (ti_el or ti_ox)):
            return None, None
        y_s = pd.to_numeric(df[y], errors="coerce")
        if ti_el:
            ti_ppm = pd.to_numeric(df[ti_el], errors="coerce")
        else:
            ti_ppm = pd.to_numeric(df[ti_ox], errors="coerce") * 5995
        return (pd.to_numeric(df[zr], errors="coerce") / y_s, ti_ppm / y_s)

    def _draw_background(self, ax, options):
        # Boundary from Rollinson Fig 5.2a captioned (513, 0) and (313, 7.5)
        # — but in Zr/Y, Ti/Y space. Approximate dividing line.
        ax.plot([1, 30], [513, 313], color="#444", linewidth=1.2,
                linestyle="--")
        ax.text(8, 700, "Within-plate basalts",
                fontsize=10, style="italic", color="#333")
        ax.text(8, 200, "Plate-margin basalts",
                fontsize=10, style="italic", color="#333")


# ---------------------------------------------------------------------------
# Shervais (1982) / Vermeesch (2006) — Ti vs V (mafic)
# ---------------------------------------------------------------------------

class Shervais1982TiV(Diagram):
    key = "shervais_1982_TiV"
    title = "Ti vs V — Shervais (1982) / Vermeesch (2006)"
    citation = ("Shervais (1982); Vermeesch (2006a) reassessed boundaries. "
                "Ti/V < 20 ⇒ IAB, 20–50 ⇒ MORB / back-arc, >50 ⇒ OIB.")
    x_label = "Ti/1000 (ppm)"
    y_label = "V (ppm)"
    x_range = (0, 25)
    y_range = (0, 600)
    log_x = False
    log_y = False

    def _compute_xy(self, df):
        ti_el = resolve_column(df, ["Ti"])
        ti_ox = resolve_column(df, ["TiO2"])
        v = resolve_column(df, ["V"])
        if not ((ti_el or ti_ox) and v):
            return None, None
        if ti_el:
            ti_ppm = pd.to_numeric(df[ti_el], errors="coerce")
        else:
            ti_ppm = pd.to_numeric(df[ti_ox], errors="coerce") * 5995
        return (ti_ppm / 1000.0, pd.to_numeric(df[v], errors="coerce"))

    def _draw_background(self, ax, options):
        xs = np.linspace(0, 25, 200)
        # Lines passing through origin: V/(Ti/1000) = 10, 20, 50, 100
        for ratio, label in ((100, "Ti/V = 10"), (50, "Ti/V = 20"),
                             (20, "Ti/V = 50"), (10, "Ti/V = 100")):
            ax.plot(xs, ratio * xs, color="#444", linewidth=0.8,
                    linestyle=":", alpha=0.7)
            # label at the right edge if within ylim
            y_end = ratio * xs[-1]
            if y_end < 580:
                ax.text(xs[-1] + 0.2, y_end, label, fontsize=7,
                        color="#666", va="center")
        ax.text(2.5, 450, "IAB / arc tholeiite\n(Ti/V < 20)", fontsize=9,
                style="italic", color="#333")
        ax.text(10, 350, "MORB / BAB\n(Ti/V = 20–50)", fontsize=9,
                style="italic", color="#333", ha="center")
        ax.text(20, 120, "OIB (Ti/V > 50)", fontsize=9,
                style="italic", color="#333", ha="center")


# ---------------------------------------------------------------------------
# Pearce & Cann (1973) Zr vs Ti
# ---------------------------------------------------------------------------

class PearceCann1973ZrTi(Diagram):
    key = "pearce_cann_1973_ZrTi"
    title = "Zr vs Ti — Pearce & Cann (1973)"
    citation = ("Pearce & Cann (1973); Vermeesch (2006a) redefined "
                "boundaries (Fig. 5.2c). Good for OIB and IAB; less "
                "reliable for MORB.")
    x_label = "Zr (ppm)"
    y_label = "Ti (ppm)"
    x_range = (10, 1000)
    y_range = (500, 30000)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        zr = resolve_column(df, ["Zr"])
        ti_el = resolve_column(df, ["Ti"])
        ti_ox = resolve_column(df, ["TiO2"])
        if not (zr and (ti_el or ti_ox)):
            return None, None
        if ti_el:
            ti_ppm = pd.to_numeric(df[ti_el], errors="coerce")
        else:
            ti_ppm = pd.to_numeric(df[ti_ox], errors="coerce") * 5995
        return pd.to_numeric(df[zr], errors="coerce"), ti_ppm

    def _draw_background(self, ax, options):
        # Approximate refined boundaries (Vermeesch 2006a)
        # IAB: low Ti/Zr (~50)
        # OIB: high Ti and Zr
        # MORB: intermediate
        xs = np.array([10, 1000])
        ax.plot(xs, 30 * xs, color="#444", lw=0.8, ls=":")    # Ti/Zr ≈ 30 (IAB upper)
        ax.plot(xs, 110 * xs, color="#444", lw=0.8, ls=":")  # Ti/Zr ≈ 110 (OIB lower)
        ax.text(80, 1500, "IAB", fontsize=11, style="italic", color="#333")
        ax.text(80, 6000, "MORB", fontsize=11, style="italic", color="#333")
        ax.text(80, 20000, "OIB", fontsize=11, style="italic", color="#333")


# ---------------------------------------------------------------------------
# Saccani (2015) NbN vs ThN (N-MORB normalised)
# ---------------------------------------------------------------------------

_NMORB_SUN = {"Nb": 2.33, "Th": 0.12, "Yb": 3.05, "Dy": 4.55, "Ce": 7.50}


class Saccani2015NbTh(Diagram):
    key = "saccani2015_nb_th"
    title = "Nb_N vs Th_N — Saccani (2015)"
    citation = ("Saccani (2015). Values normalised to N-MORB (Sun & "
                "McDonough 1989). >94 % discrimination between MORB-OIB "
                "and volcanic-arc arrays.")
    x_label = "Nb / Nb$_{N-MORB}$"
    y_label = "Th / Th$_{N-MORB}$"
    x_range = (0.01, 100)
    y_range = (0.01, 200)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        nb = resolve_column(df, ["Nb"])
        th = resolve_column(df, ["Th"])
        if not (nb and th):
            return None, None
        return (pd.to_numeric(df[nb], errors="coerce") / _NMORB_SUN["Nb"],
                pd.to_numeric(df[th], errors="coerce") / _NMORB_SUN["Th"])

    def _draw_background(self, ax, options):
        xs = np.array([0.01, 100.0])
        # MORB-OIB array bounded approximately by Th_N / Nb_N = 1 (above) and
        # 0.1 (below) on log-log.
        ax.fill_between(xs, 0.1 * xs, 1.0 * xs, color="#888",
                        alpha=0.10, zorder=0)
        ax.plot(xs, 0.1 * xs, color="#444", lw=1.0)
        ax.plot(xs, 1.0 * xs, color="#444", lw=1.0)
        ax.text(5, 0.6, "MORB–OIB array", fontsize=10, color="#333",
                style="italic")
        ax.text(0.05, 8, "Volcanic-arc array (subduction)",
                fontsize=10, color="#333", style="italic")


# ---------------------------------------------------------------------------
# Defant & Drummond (1990) — adakite vs classic arc
# ---------------------------------------------------------------------------

class DefantDrummondYSrY(Diagram):
    key = "defant_drummond_YSrY"
    title = "Y vs Sr/Y — Defant & Drummond (1990)"
    citation = ("Defant & Drummond (1990). Adakites: Sr/Y > 40 at low Y "
                "(<≈18 ppm). Classic arc andesite-dacite-rhyolite (ADR) "
                "below.")
    x_label = "Y (ppm)"
    y_label = "Sr/Y"
    x_range = (0, 50)
    y_range = (0, 200)

    def _compute_xy(self, df):
        sr = resolve_column(df, ["Sr"])
        y = resolve_column(df, ["Y"])
        if not (sr and y):
            return None, None
        y_s = pd.to_numeric(df[y], errors="coerce")
        return y_s, pd.to_numeric(df[sr], errors="coerce") / y_s

    def _draw_background(self, ax, options):
        # Approximate adakite boundary (curved): goes through (0, ~120) -> (18, 40) -> (45, 20)
        x_curve = np.array([0, 6, 12, 18, 30, 45])
        y_curve = np.array([120, 80, 55, 40, 28, 20])
        ax.plot(x_curve, y_curve, color="#444", lw=1.2, linestyle="--")
        ax.text(5, 130, "Adakites", fontsize=11, color="#333", style="italic")
        ax.text(28, 60, "Classic arc ADR", fontsize=10, color="#333",
                style="italic")


class DefantDrummondYbLaYb(Diagram):
    key = "defant_drummond_YbLaYb"
    title = "Yb vs La/Yb — Defant & Drummond (1990)"
    citation = ("Defant & Drummond (1990). Adakites: La/Yb > 20 at low Yb "
                "(<≈1.9 ppm). Classic ADR shows lower La/Yb at higher Yb.")
    x_label = "Yb (ppm)"
    y_label = "La/Yb"
    x_range = (0, 6)
    y_range = (0, 80)

    def _compute_xy(self, df):
        la = resolve_column(df, ["La"])
        yb = resolve_column(df, ["Yb"])
        if not (la and yb):
            return None, None
        yb_s = pd.to_numeric(df[yb], errors="coerce")
        return yb_s, pd.to_numeric(df[la], errors="coerce") / yb_s

    def _draw_background(self, ax, options):
        x_curve = np.array([0, 0.6, 1.2, 1.9, 3.0, 6.0])
        y_curve = np.array([60, 42, 30, 20, 12, 6])
        ax.plot(x_curve, y_curve, color="#444", lw=1.2, linestyle="--")
        ax.text(0.4, 55, "Adakites", fontsize=11, color="#333", style="italic")
        ax.text(3.5, 25, "Classic arc ADR", fontsize=10, color="#333",
                style="italic")


# ---------------------------------------------------------------------------
# Pearce et al. (1984) — granitoid discriminants
# ---------------------------------------------------------------------------

class Pearce1984YbTa(Diagram):
    key = "pearce1984_YbTa"
    title = "Ta vs Yb — Pearce et al. (1984)"
    citation = ("Pearce et al. (1984); Verma et al. (2012). WPG: 0 % "
                "misclassified; VAG: ~11 %; S-COLG: ~25 %.")
    x_label = "Yb (ppm)"
    y_label = "Ta (ppm)"
    x_range = (0.1, 100)
    y_range = (0.05, 100)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        yb = resolve_column(df, ["Yb"])
        ta = resolve_column(df, ["Ta"])
        if not (yb and ta):
            return None, None
        return (pd.to_numeric(df[yb], errors="coerce"),
                pd.to_numeric(df[ta], errors="coerce"))

    def _draw_background(self, ax, options):
        # Boundary coordinates from Rollinson Fig 5.8a (caption)
        ax.plot([0.1, 3], [0.35, 2], color="#444", lw=1.0)   # VAG / S-COLG
        ax.plot([0.1, 3], [100, 2], color="#444", lw=1.0)    # S-COLG / WPG
        ax.plot([3, 5], [2, 1], color="#444", lw=1.0)        # VAG / WPG (kink)
        ax.plot([5, 100], [1, 7], color="#444", lw=1.0)      # WPG / ORG
        ax.plot([5, 5], [0.05, 1], color="#444", lw=1.0)     # VAG / ORG
        ax.text(0.3, 7, "S-COLG", fontsize=11, style="italic", color="#333")
        ax.text(0.3, 0.15, "VAG", fontsize=11, style="italic", color="#333")
        ax.text(20, 20, "WPG", fontsize=11, style="italic", color="#333")
        ax.text(20, 0.2, "ORG", fontsize=11, style="italic", color="#333")


class Pearce1984YNb(Diagram):
    key = "pearce1984_YNb"
    title = "Nb vs Y — Pearce et al. (1984)"
    citation = ("Pearce et al. (1984); Verma et al. (2012). Three rays "
                "meeting at central (50, 10) define VAG+S-COLG / WPG / "
                "ORG fields.")
    x_label = "Y (ppm)"
    y_label = "Nb (ppm)"
    x_range = (1, 2000)
    y_range = (1, 2000)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        y = resolve_column(df, ["Y"])
        nb = resolve_column(df, ["Nb"])
        if not (y and nb):
            return None, None
        return (pd.to_numeric(df[y], errors="coerce"),
                pd.to_numeric(df[nb], errors="coerce"))

    def _draw_background(self, ax, options):
        # Three rays meeting at central point (50, 10)
        ax.plot([50, 1], [10, 2000], color="#444", lw=1.0)   # VAG+S-COLG/WPG
        ax.plot([50, 1000], [10, 100], color="#444", lw=1.0)  # WPG/ORG
        ax.plot([50, 40], [10, 1], color="#444", lw=1.0)      # ORG/VAG+S-COLG (short)
        ax.plot([50, 50], [10, 1], color="#444", lw=1.0)      # extension
        ax.text(3, 100, "WPG", fontsize=12, style="italic", color="#333")
        ax.text(3, 3, "VAG +\nS-COLG", fontsize=10, style="italic",
                color="#333", ha="center")
        ax.text(300, 3, "ORG", fontsize=12, style="italic", color="#333")


class Pearce1984YbTaRb(Diagram):
    key = "pearce1984_YbTaRb"
    title = "Rb vs (Yb + Ta) — Pearce et al. (1984)"
    citation = "Pearce et al. (1984). Alternative formulation using Rb."
    x_label = "Yb + Ta (ppm)"
    y_label = "Rb (ppm)"
    x_range = (0.5, 1000)
    y_range = (1, 2000)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        yb = resolve_column(df, ["Yb"])
        ta = resolve_column(df, ["Ta"])
        rb = resolve_column(df, ["Rb"])
        if not (yb and ta and rb):
            return None, None
        return (pd.to_numeric(df[yb], errors="coerce")
                + pd.to_numeric(df[ta], errors="coerce"),
                pd.to_numeric(df[rb], errors="coerce"))

    def _draw_background(self, ax, options):
        # Approximate boundaries (Pearce et al. 1984 fig 4)
        ax.plot([0.5, 6], [400, 80], color="#444", lw=1.0)    # S-COLG/VAG
        ax.plot([6, 6], [80, 4], color="#444", lw=1.0)        # VAG/ORG
        ax.plot([6, 1000], [80, 700], color="#444", lw=1.0)   # WPG upper
        ax.plot([6, 1000], [4, 30], color="#444", lw=1.0)     # WPG/ORG lower
        ax.text(1, 600, "S-COLG", fontsize=10, style="italic", color="#333")
        ax.text(2, 30, "VAG", fontsize=11, style="italic", color="#333")
        ax.text(80, 400, "WPG", fontsize=11, style="italic", color="#333")
        ax.text(60, 5, "ORG", fontsize=11, style="italic", color="#333")


class Pearce1984YNbRb(Diagram):
    key = "pearce1984_YNbRb"
    title = "Rb vs (Y + Nb) — Pearce et al. (1984)"
    citation = "Pearce et al. (1984). Alternative formulation using Rb."
    x_label = "Y + Nb (ppm)"
    y_label = "Rb (ppm)"
    x_range = (1, 2000)
    y_range = (1, 2000)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        y = resolve_column(df, ["Y"])
        nb = resolve_column(df, ["Nb"])
        rb = resolve_column(df, ["Rb"])
        if not (y and nb and rb):
            return None, None
        return (pd.to_numeric(df[y], errors="coerce")
                + pd.to_numeric(df[nb], errors="coerce"),
                pd.to_numeric(df[rb], errors="coerce"))

    def _draw_background(self, ax, options):
        ax.plot([1, 50], [400, 80], color="#444", lw=1.0)
        ax.plot([50, 50], [80, 4], color="#444", lw=1.0)
        ax.plot([50, 2000], [80, 800], color="#444", lw=1.0)
        ax.plot([50, 2000], [4, 30], color="#444", lw=1.0)
        ax.text(3, 600, "S-COLG", fontsize=10, style="italic", color="#333")
        ax.text(10, 25, "VAG", fontsize=11, style="italic", color="#333")
        ax.text(300, 400, "WPG", fontsize=11, style="italic", color="#333")
        ax.text(400, 6, "ORG", fontsize=11, style="italic", color="#333")


# ---------------------------------------------------------------------------
# Saccani (2015) — additional discriminants
# Values normalised to N-MORB (Sun & McDonough 1989) using the same
# reference dictionary as :class:`Saccani2015NbTh`.
# ---------------------------------------------------------------------------

class Saccani2015DyYb(Diagram):
    """DyN vs YbN — distinguishes IAT from Boninite arrays."""
    key = "saccani2015_dy_yb"
    title = "Dy$_N$ vs Yb$_N$ — Saccani (2015)"
    citation = ("Saccani (2015). N-MORB normalised (Sun & McDonough 1989). "
                "Boninites form a low-Dy_N / low-Yb_N cluster (depleted, "
                "U-shaped REE); island-arc tholeiites (IAT) plot along the "
                "main MORB array.")
    x_label = "Yb / Yb$_{N-MORB}$"
    y_label = "Dy / Dy$_{N-MORB}$"
    x_range = (0.05, 10)
    y_range = (0.05, 10)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        dy = resolve_column(df, ["Dy"])
        yb = resolve_column(df, ["Yb"])
        if not (dy and yb):
            return None, None
        return (pd.to_numeric(df[yb], errors="coerce") / _NMORB_SUN["Yb"],
                pd.to_numeric(df[dy], errors="coerce") / _NMORB_SUN["Dy"])

    def _draw_background(self, ax, options):
        xs = np.array([0.05, 10.0])
        # MORB / IAT array follows Dy_N ≈ Yb_N (chondritic Dy/Yb)
        ax.fill_between(xs, 0.85 * xs, 1.25 * xs, color="#88c0d0",
                        alpha=0.12, zorder=0)
        ax.plot(xs, xs, color="#444", lw=1.0)
        # Boninite envelope — low Yb_N, slightly lower Dy_N
        bx = np.array([0.08, 0.15, 0.30, 0.55, 0.30, 0.12, 0.08])
        by = np.array([0.08, 0.10, 0.22, 0.45, 0.55, 0.20, 0.08])
        ax.fill(bx, by, color="#d08770", alpha=0.18, zorder=0)
        ax.plot(bx, by, color="#a04c2e", lw=1.0)
        ax.text(2.0, 0.7, "MORB / IAT array",
                fontsize=10, style="italic", color="#333")
        ax.text(0.10, 0.18, "Boninites", fontsize=10, style="italic",
                color="#a04c2e")


class Saccani2015CeDyYb(Diagram):
    """CeN/YbN vs DyN/YbN — discriminates N-MORB from G-MORB and OIB."""
    key = "saccani2015_ce_dy_yb"
    title = "Ce$_N$/Yb$_N$ vs Dy$_N$/Yb$_N$ — Saccani (2015)"
    citation = ("Saccani (2015). Two normalised inter-REE ratios that "
                "separate N-MORB (depleted, low Ce_N/Yb_N) from "
                "Garnet-influenced MORB (G-MORB / E-MORB, garnet residue) "
                "and OIB along an LREE-enrichment trend.")
    x_label = "Dy$_N$ / Yb$_N$"
    y_label = "Ce$_N$ / Yb$_N$"
    x_range = (0.5, 3.5)
    y_range = (0.5, 50)
    log_x = False
    log_y = True

    def _compute_xy(self, df):
        ce = resolve_column(df, ["Ce"])
        dy = resolve_column(df, ["Dy"])
        yb = resolve_column(df, ["Yb"])
        if not (ce and dy and yb):
            return None, None
        ce_n = pd.to_numeric(df[ce], errors="coerce") / _NMORB_SUN["Ce"]
        dy_n = pd.to_numeric(df[dy], errors="coerce") / _NMORB_SUN["Dy"]
        yb_n = pd.to_numeric(df[yb], errors="coerce") / _NMORB_SUN["Yb"]
        return dy_n / yb_n, ce_n / yb_n

    def _draw_background(self, ax, options):
        # N-MORB: low Ce_N/Yb_N (~0.5-1.5) and Dy_N/Yb_N ≈ 1
        ax.fill_between([0.7, 1.3], [0.5, 0.5], [2.5, 2.5],
                        color="#88c0d0", alpha=0.15, zorder=0)
        ax.text(1.0, 1.3, "N-MORB", fontsize=10, style="italic",
                color="#333", ha="center")
        # G-MORB / E-MORB: higher Ce_N/Yb_N, slightly higher Dy_N/Yb_N
        ax.fill_between([1.0, 2.0], [2.5, 2.5], [10.0, 10.0],
                        color="#a3be8c", alpha=0.15, zorder=0)
        ax.text(1.5, 5.0, "E-MORB / G-MORB", fontsize=10, style="italic",
                color="#333", ha="center")
        # OIB: very high Ce_N/Yb_N, Dy_N/Yb_N > 1.5
        ax.fill_between([1.5, 3.5], [10.0, 10.0], [50.0, 50.0],
                        color="#d08770", alpha=0.15, zorder=0)
        ax.text(2.5, 25.0, "OIB", fontsize=10, style="italic",
                color="#333", ha="center")


# ---------------------------------------------------------------------------
# Yang et al. (2019) — high-Mg source proxy
# FCMS and FCKANTMS are oxide-based proxies for mantle vs. lithospheric
# source of high-Mg melts. Reference: Yang, Wang, Castillo (2019), Lithos.
# ---------------------------------------------------------------------------

def _yang_fcms(df):
    """FCMS = SiO2 + K2O × 0.99 − Al2O3 × 1.32 − MgO × 0.78."""
    si = resolve_column(df, ["SiO2"])
    k = resolve_column(df, ["K2O"])
    al = resolve_column(df, ["Al2O3"])
    mg = resolve_column(df, ["MgO"])
    if not (si and k and al and mg):
        return None
    return (pd.to_numeric(df[si], errors="coerce")
            + 0.99 * pd.to_numeric(df[k], errors="coerce")
            - 1.32 * pd.to_numeric(df[al], errors="coerce")
            - 0.78 * pd.to_numeric(df[mg], errors="coerce"))


def _yang_fckantms(df):
    """FCKANTMS = K2O × 1.32 + Na2O × 0.49 + Al2O3 × 0.10
                 + TiO2 × 0.95 − CaO × 0.18 − MgO × 0.32 − SiO2 × 0.04.

    Approximation of the linear combination published by Yang et al.
    (2019) for distinguishing peridotite-derived vs pyroxenite-/
    carbonatite-influenced sources.
    """
    parts = {n: resolve_column(df, [n]) for n in
             ("K2O", "Na2O", "Al2O3", "TiO2", "CaO", "MgO", "SiO2")}
    if any(v is None for v in parts.values()):
        return None
    return (1.32 * pd.to_numeric(df[parts["K2O"]],   errors="coerce")
            + 0.49 * pd.to_numeric(df[parts["Na2O"]],  errors="coerce")
            + 0.10 * pd.to_numeric(df[parts["Al2O3"]], errors="coerce")
            + 0.95 * pd.to_numeric(df[parts["TiO2"]],  errors="coerce")
            - 0.18 * pd.to_numeric(df[parts["CaO"]],   errors="coerce")
            - 0.32 * pd.to_numeric(df[parts["MgO"]],   errors="coerce")
            - 0.04 * pd.to_numeric(df[parts["SiO2"]],  errors="coerce"))


class Yang2019FCKANTMS(Diagram):
    """FCMS vs FCKANTMS — Yang et al. (2019) source proxy for high-Mg
    igneous rocks (peridotite vs pyroxenite / metasomatised lithospheric
    mantle).
    """
    key = "yang_2019_fckantms"
    title = "FCMS vs FCKANTMS — Yang et al. (2019)"
    citation = ("Yang, Wang & Castillo (2019), Lithos. Two oxide-based "
                "linear combinations (FCMS and FCKANTMS) that proxy the "
                "source of high-Mg / picritic to ultramafic melts. "
                "Peridotite (asthenospheric) melts cluster at FCMS > 5 "
                "and FCKANTMS < 4; pyroxenite / metasomatised lithospheric "
                "sources plot at lower FCMS and higher FCKANTMS.")
    x_label = "FCMS"
    y_label = "FCKANTMS"
    x_range = (-20, 30)
    y_range = (-5, 25)

    def _compute_xy(self, df):
        fcms = _yang_fcms(df)
        fck  = _yang_fckantms(df)
        if fcms is None or fck is None:
            return None, None
        return fcms, fck

    def _draw_background(self, ax, options):
        # Approximate fields (Yang et al. 2019 fig. 7)
        ax.fill_between([5, 30], [-5, -5], [4, 4], color="#88c0d0",
                        alpha=0.15, zorder=0)
        ax.text(15, 0.5, "Peridotite-derived\n(asthenospheric)",
                fontsize=9, style="italic", color="#333", ha="center")
        ax.fill_between([-20, 5], [4, 4], [25, 25], color="#d08770",
                        alpha=0.12, zorder=0)
        ax.text(-7, 15, "Pyroxenite /\nmetasomatised\nlithosphere",
                fontsize=9, style="italic", color="#333", ha="center")
        ax.axhline(4, color="#444", lw=0.8, ls="--")
        ax.axvline(5, color="#444", lw=0.8, ls="--")
