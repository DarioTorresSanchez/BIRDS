"""Bivariate tectonic discrimination diagrams.

Coordinates compiled from Rollinson & Pease (2021) Chapter 5 figure
captions and the original references cited below each class.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Diagram, inverse_logratio, resolve_column


#: 1 wt.% TiO2 = 5993.4 ppm Ti, from the mass ratio 47.867 / 79.866.
#: Was 5995 in four places, which is 0.03 % high — harmless on a plot,
#: but a constant with a known value has no reason to be approximate.
TIO2_WT_TO_TI_PPM = 5993.4


# ---------------------------------------------------------------------------
# Pearce (2008) — mafic crustal input and melting depth proxies
# ---------------------------------------------------------------------------
#
# Both panels of Pearce (2008) Fig. 2, measured from the published
# figure.  Its axes were calibrated on their own decade marks, the
# array bounds fitted by RANSAC over the drawn lines, and the three
# reference markers located: they land on the Sun & McDonough (1989)
# values the paper cites, to better than 1 % in Th/Yb and TiO2/Yb,
# which is what fixes the calibration.
#
# NOTE the y axis of panel (b): Pearce plots **TiO2 in wt.% over Yb in
# ppm**, not Ti in ppm over Yb.  The two differ by a factor of 5993,
# so field boundaries taken from one and applied to the other are
# meaningless.  This module had the ppm form with boundaries that
# belonged to neither.

#: Sun & McDonough (1989) reservoirs, the ones Pearce plots.  Trace
#: elements in ppm; Ti in ppm, converted to TiO2 wt.% where needed.
SUN_MCDONOUGH_1989 = {
    "N-MORB": {"Nb": 2.33, "Th": 0.12, "Yb": 3.05, "Ti": 7600.0},
    "E-MORB": {"Nb": 8.30, "Th": 0.60, "Yb": 2.37, "Ti": 6000.0},
    "OIB":    {"Nb": 48.0, "Th": 4.00, "Yb": 2.16, "Ti": 17200.0},
}


def _ratio_point(name, y_kind):
    r = SUN_MCDONOUGH_1989[name]
    x = r["Nb"] / r["Yb"]
    if y_kind == "Th":
        return x, r["Th"] / r["Yb"]
    return x, (r["Ti"] / TIO2_WT_TO_TI_PPM) / r["Yb"]


# --- panel (a): Th/Yb vs Nb/Yb ---------------------------------------
#
# The MORB-OIB array is a band of constant Th/Nb: fitting the drawn
# bounds with a free slope gives 1.03 and 1.06 in log-log, and forcing
# the slope to 1 costs almost nothing (mean residual 0.049 against
# 0.046 dex, and 0.052 against 0.037).  A constant ratio is also what
# the diagram means, Th/Nb being the crustal-input proxy.
MORB_OIB_ARRAY_TH_NB = (0.043, 0.096)

#: Pearce filters out crustal contamination at Th/Nb > 0.2 (pp. 30, 41).
CRUSTAL_CONTAMINATION_TH_NB = 0.2

# --- panel (b): TiO2/Yb vs Nb/Yb -------------------------------------
#
# Three near-parallel bounds, each fitted as TiO2/Yb = a (Nb/Yb)^b.
# The slopes agree to within 0.006, so the arrays are parallel bands.
MORB_ARRAY_TIO2_YB = ((0.2820, 0.0433), (0.6293, 0.0489))
OIB_ARRAY_TIO2_YB = ((0.6293, 0.0489), (2.2711, 0.0435))

#: Tholeiitic / alkalic divide inside the OIB array; it spans the array
#: from (8.5, 2.49) down to (18.2, 0.73).  Fitted residual 0.002 dex.
OIB_THOLEIITIC_ALKALIC = (82.575, -1.6318)

#: N-MORB / E-MORB divide, "the C1 chondrite value" (Fig. 2 caption).
N_E_MORB_NB_YB = 1.45

_ARRAY_LINE = dict(color="#444", linewidth=1.0, alpha=0.9, zorder=1)


def _power(coefs, xs):
    a, b = coefs
    return a * np.asarray(xs, dtype=float) ** b


def _mark_reservoirs(ax, y_kind):
    for name in SUN_MCDONOUGH_1989:
        x, y = _ratio_point(name, y_kind)
        ax.scatter([x], [y], marker="s", s=34, c="black", zorder=4)
        ax.annotate(name, (x, y), xytext=(7, -3),
                    textcoords="offset points", fontsize=8, zorder=4)


class Pearce2008ThYbNbYb(Diagram):
    key = "pearce2008_thyb_nbyb"
    title = "Th/Yb vs Nb/Yb — Pearce (2008)"
    citation = ("Pearce (2008) Lithos 100, 14-48, Fig. 2a.  The MORB-OIB "
                "array is a band of constant Th/Nb, measured at 0.043 to "
                "0.096; a sample above it carries crustal input, by "
                "subduction, contamination or recycling.  Pearce filters "
                "out significant contamination at Th/Nb > 0.2.  Reference "
                "compositions are Sun & McDonough (1989).")
    x_label = "Nb/Yb"
    y_label = "Th/Yb"
    x_range = (0.1, 100.0)
    y_range = (0.01, 10.0)
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
        xs = np.array(self.x_range)
        low, high = MORB_OIB_ARRAY_TH_NB
        ax.fill_between(xs, low * xs, high * xs, color="#888", alpha=0.15,
                        zorder=0)
        for ratio in (low, high):
            ax.plot(xs, ratio * xs, **_ARRAY_LINE)
        ax.plot(xs, CRUSTAL_CONTAMINATION_TH_NB * xs, color="#b13a3a",
                linewidth=1.0, linestyle="--", alpha=0.8, zorder=1)
        ax.text(2.2, 2.2 * CRUSTAL_CONTAMINATION_TH_NB * 1.45,
                "Th/Nb = 0.2", fontsize=7.5, color="#b13a3a",
                ha="center")
        _mark_reservoirs(ax, "Th")
        ax.text(25, 25 * (low * high) ** 0.5, "MORB-OIB array",
                fontsize=9, style="italic", color="#333", ha="center")
        ax.text(0.5, 3.0, "volcanic arc / crustal input",
                fontsize=9, style="italic", color="#333")


class Pearce2008TiYbNbYb(Diagram):
    key = "pearce2008_tiyb_nbyb"
    title = "TiO$_2$/Yb vs Nb/Yb — Pearce (2008)"
    citation = ("Pearce (2008) Lithos 100, 14-48, Fig. 2b.  TiO2 in wt.% "
                "over Yb in ppm, as the paper plots it — not Ti in ppm, "
                "which differs by a factor of 5993 and would put every "
                "boundary in the wrong place.  High TiO2/Yb means garnet "
                "in the residue, so deep melting: the OIB array sits "
                "above the shallow-melting MORB array.  Bounds measured "
                "from the figure; the N-MORB / E-MORB divide at "
                "Nb/Yb = 1.45 is the C1 chondrite value the caption "
                "states.  Reference compositions are Sun & McDonough "
                "(1989).")
    x_label = "Nb/Yb"
    y_label = "TiO$_2$/Yb  (wt.% / ppm)"
    x_range = (0.1, 100.0)
    y_range = (0.1, 10.0)
    log_x = True
    log_y = True

    def _compute_xy(self, df):
        nb = resolve_column(df, ["Nb"])
        yb = resolve_column(df, ["Yb"])
        tio2 = resolve_column(df, ["TiO2"])
        ti_el = resolve_column(df, ["Ti"])
        if not (nb and yb and (tio2 or ti_el)):
            return None, None
        yb_s = pd.to_numeric(df[yb], errors="coerce")
        if tio2:
            tio2_wt = pd.to_numeric(df[tio2], errors="coerce")
        else:
            tio2_wt = (pd.to_numeric(df[ti_el], errors="coerce")
                       / TIO2_WT_TO_TI_PPM)
        return (pd.to_numeric(df[nb], errors="coerce") / yb_s,
                tio2_wt / yb_s)

    def _draw_background(self, ax, options):
        xs = np.logspace(np.log10(self.x_range[0]),
                         np.log10(self.x_range[1]), 200)
        morb_lo, morb_hi = MORB_ARRAY_TIO2_YB
        _oib_lo, oib_hi = OIB_ARRAY_TIO2_YB
        ax.fill_between(xs, _power(morb_lo, xs), _power(morb_hi, xs),
                        color="#888", alpha=0.18, zorder=0)
        for coefs in (morb_lo, morb_hi, oib_hi):
            ax.plot(xs, _power(coefs, xs), **_ARRAY_LINE)

        # Tholeiitic / alkalic divide, drawn only where it crosses the
        # OIB array, which is the only place the paper draws it.
        th_alk = _power(OIB_THOLEIITIC_ALKALIC, xs)
        inside = (th_alk >= _power(morb_hi, xs)) & (th_alk <= _power(oib_hi, xs))
        ax.plot(xs[inside], th_alk[inside], color="#444", linewidth=1.0,
                linestyle="--", zorder=1)
        ax.text(9.0, 2.9, "Th", fontsize=8, color="#333", ha="right")
        ax.text(20.0, 2.9, "Alk", fontsize=8, color="#333")

        # N-MORB / E-MORB divide, within the MORB array only.
        ax.plot([N_E_MORB_NB_YB, N_E_MORB_NB_YB],
                [_power(morb_lo, N_E_MORB_NB_YB) * 0.75,
                 _power(morb_hi, N_E_MORB_NB_YB)],
                color="#444", linewidth=1.0, linestyle="--", zorder=1)
        ax.text(N_E_MORB_NB_YB * 0.85, 0.185, "N", fontsize=8, color="#333",
                ha="right")
        ax.text(N_E_MORB_NB_YB * 1.15, 0.185, "E", fontsize=8, color="#333")

        _mark_reservoirs(ax, "Ti")
        ax.text(0.5, 1.5, "OIB array\n(deep melting)", fontsize=9,
                style="italic", color="#333")
        ax.text(30, 0.42, "MORB array\n(shallow melting)", fontsize=9,
                style="italic", color="#333", ha="center")


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
            ti_ppm = pd.to_numeric(df[ti_ox], errors="coerce") * TIO2_WT_TO_TI_PPM
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
            ti_ppm = pd.to_numeric(df[ti_ox], errors="coerce") * TIO2_WT_TO_TI_PPM
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

#: Vermeesch (2006a) Table 6, Figure 38b.  Unlike his ternary LDAs,
#: this one is not three rays from a triple point but **two straight
#: segments**, each given by its two endpoints -- which is why the x
#: column of Table 6 repeats as -13, -7, -13, -7.  The axes are
#: ln(Zr/(1e6 - Zr - Ti)) and ln(Ti/(1e6 - Zr - Ti)), the additive
#: log-ratio of the three-part composition (Zr, Ti, everything else) in
#: ppm, so mapping a boundary back to Zr-Ti is the same softmax the
#: ternaries use, scaled by 1e6.  Straight there, curved here.
_PEARCE_CANN_LDA = {
    "upper": (((-13.0, -4.28), (-7.0, -4.45)), ("OIB", "MORB")),
    "lower": (((-13.0, -5.36), (-7.0, -4.72)), ("MORB", "IAB")),
}

#: How far past the published endpoints to carry each boundary, as a
#: fraction of the segment, so the curve crosses the whole frame
#: instead of stopping in mid-air at the anchor.
_PEARCE_CANN_OVERRUN = 0.6

#: The closure the log-ratio denominator is taken against: Zr and Ti in
#: ppm against the 1e6 ppm of the whole rock.
_PPM_CLOSURE = 1.0e6


def _pearce_cann_boundary(segment):
    """One decision boundary, as (Zr ppm, Ti ppm) along its length."""
    (x0, y0), (x1, y1) = segment
    t = np.linspace(-_PEARCE_CANN_OVERRUN, 1.0 + _PEARCE_CANN_OVERRUN, 200)
    xs = x0 + (x1 - x0) * t
    ys = y0 + (y1 - y0) * t
    _rest, zr, ti = inverse_logratio(xs, ys)
    return zr * _PPM_CLOSURE, ti * _PPM_CLOSURE


class PearceCann1973ZrTi(Diagram):
    key = "pearce_cann_1973_ZrTi"
    title = "Zr vs Ti — Pearce & Cann (1973) / Vermeesch (2006a)"
    citation = ("Pearce & Cann (1973), with the decision boundaries "
                "Vermeesch (2006a) derived for it by linear discriminant "
                "analysis (his Figure 38).  The analysis is done on "
                "ln(Zr/rest) and ln(Ti/rest), where the boundaries are "
                "two straight lines; mapped back to Zr-Ti they curve.  "
                "Anchor points from his Table 6.  OIB above, IAB below, "
                "MORB between.")
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
            ti_ppm = pd.to_numeric(df[ti_ox], errors="coerce") * TIO2_WT_TO_TI_PPM
        return pd.to_numeric(df[zr], errors="coerce"), ti_ppm

    def _draw_background(self, ax, options):
        for segment, _pair in _PEARCE_CANN_LDA.values():
            zr, ti = _pearce_cann_boundary(segment)
            ax.plot(zr, ti, color="#444", lw=0.9, alpha=0.9, zorder=2)
        # Labels sit between the two boundaries, and outside them, at a
        # Zr the frame actually shows.
        at_zr = 60.0
        upper = _pearce_cann_boundary(_PEARCE_CANN_LDA["upper"][0])
        lower = _pearce_cann_boundary(_PEARCE_CANN_LDA["lower"][0])
        top = float(np.interp(at_zr, upper[0], upper[1]))
        bottom = float(np.interp(at_zr, lower[0], lower[1]))
        for name, height in (("OIB", top * 1.9),
                             ("MORB", np.sqrt(top * bottom)),
                             ("IAB", bottom / 2.2)):
            ax.text(at_zr, height, name, fontsize=11, style="italic",
                    color="#333", ha="center", va="center")


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

# ---------------------------------------------------------------------------
# Pearce, Harris & Tindle (1984) — the four granitoid discriminants
# ---------------------------------------------------------------------------
#
# These four are among the rare diagrams of this era whose authors
# printed the boundary coordinates outright, in the captions of their
# Figures 3 and 4.  Nothing here is measured off a figure.
#
# Two of the printed coordinates are wrong, and Verma et al. (2012)
# corrected both in the course of re-evaluating these diagrams against
# the original authors' own database.  The corrections are used here,
# and each is checkable from the geometry of the figure rather than
# taken on trust:
#
# * **Yb-Ta, syn-COLG/WPG.** Printed as "(55,20) to (3,2)".  syn-COLG
#   lies upper-left of the triple point and WPG upper-right, so their
#   boundary has to leave (3,2) going up and to the left; (55,20) is
#   down and to the right, which would put the boundary on the far side
#   of the diagram from the two fields it divides.  Verma's (0.1,100)
#   runs the way Figure 3b draws it.
# * **Rb-(Yb+Ta), syn-COLG/VAG.** Printed as ending at "(6,2000)",
#   where the other two boundaries of that junction both start at
#   (6,200).  A triple point has to be one point.  Figure 4b draws the
#   junction at Rb = 200, so the printed 2000 is a factor of ten.
#
# ``(x, y)`` throughout, in the axis order each diagram plots.

#: Dashed in the source: the upper limit for ocean-ridge granites from
#: anomalous ridge segments, not a field boundary in its own right.
_P84_ANOMALOUS = "ORG (anomalous ridges)"

_PEARCE_1984 = {
    "Y-Nb": {
        "boundaries": (
            (((1.0, 2000.0), (50.0, 10.0)), "solid", ("VAG+syn-COLG", "WPG")),
            (((40.0, 1.0), (50.0, 10.0)), "solid", ("VAG+syn-COLG", "ORG")),
            (((50.0, 10.0), (1000.0, 100.0)), "solid", ("WPG", "ORG")),
            (((25.0, 25.0), (1000.0, 400.0)), "dashed", ("WPG", _P84_ANOMALOUS)),
        ),
        "labels": {"WPG": (11.0, 180.0),
                   "VAG +\nsyn-COLG": (3.5, 20.0),
                   "ORG": (250.0, 4.0)},
    },
    "Yb-Ta": {
        "boundaries": (
            # Corrected from the printed (55, 20); see the note above.
            (((0.1, 100.0), (3.0, 2.0)), "solid", ("syn-COLG", "WPG")),
            (((0.1, 0.35), (3.0, 2.0)), "solid", ("VAG", "syn-COLG")),
            (((3.0, 2.0), (5.0, 1.0)), "solid", ("VAG", "WPG")),
            (((5.0, 0.05), (5.0, 1.0)), "solid", ("VAG", "ORG")),
            (((5.0, 1.0), (100.0, 7.0)), "solid", ("WPG", "ORG")),
            (((3.0, 2.0), (100.0, 20.0)), "dashed", ("WPG", _P84_ANOMALOUS)),
        ),
        "labels": {"syn-COLG": (0.35, 7.0), "WPG": (3.5, 35.0),
                   "VAG": (0.6, 0.2), "ORG": (25.0, 0.35)},
    },
    "YNb-Rb": {
        "boundaries": (
            (((2.0, 80.0), (55.0, 300.0)), "solid", ("VAG", "syn-COLG")),
            (((55.0, 300.0), (400.0, 2000.0)), "solid", ("syn-COLG", "WPG")),
            (((55.0, 300.0), (51.5, 8.0)), "solid", ("VAG", "WPG")),
            (((51.5, 8.0), (50.0, 1.0)), "solid", ("VAG", "ORG")),
            (((51.5, 8.0), (2000.0, 400.0)), "solid", ("WPG", "ORG")),
        ),
        "labels": {"syn-COLG": (5.0, 700.0), "WPG": (350.0, 700.0),
                   "VAG": (7.0, 9.0), "ORG": (400.0, 7.0)},
    },
    "YbTa-Rb": {
        "boundaries": (
            # Corrected from the printed (6, 2000); see the note above.
            (((0.5, 140.0), (6.0, 200.0)), "solid", ("syn-COLG", "VAG")),
            (((6.0, 200.0), (50.0, 2000.0)), "solid", ("syn-COLG", "WPG")),
            (((6.0, 200.0), (6.0, 8.0)), "solid", ("VAG", "WPG")),
            (((6.0, 8.0), (6.0, 1.0)), "solid", ("VAG", "ORG")),
            (((6.0, 8.0), (200.0, 400.0)), "solid", ("WPG", "ORG")),
        ),
        "labels": {"syn-COLG": (1.3, 800.0), "WPG": (40.0, 800.0),
                   "VAG": (1.3, 8.0), "ORG": (40.0, 5.0)},
    },
}


class _Pearce1984(Diagram):
    """Shared drawing for the four granitoid discriminants."""

    panel: str = ""
    log_x = True
    log_y = True

    def _draw_background(self, ax, options):
        spec = _PEARCE_1984[self.panel]
        for (start, end), style, _pair in spec["boundaries"]:
            ax.plot([start[0], end[0]], [start[1], end[1]],
                    color="#444", lw=1.0,
                    ls="--" if style == "dashed" else "-",
                    zorder=2)
        for name, (x, y) in spec["labels"].items():
            ax.text(x, y, name, fontsize=10, style="italic", color="#333",
                    ha="center", va="center", zorder=3)


class Pearce1984YNb(_Pearce1984):
    key = "pearce1984_YNb"
    title = "Nb vs Y — Pearce et al. (1984)"
    citation = ("Pearce, Harris & Tindle (1984) Figure 3a, boundary "
                "coordinates from its caption.  Volcanic-arc and "
                "syn-collision granites are not separated on this "
                "diagram — the authors say so — so use the Yb-Ta one "
                "to tell them apart.  The dashed line is the upper "
                "limit for ocean-ridge granites from anomalous ridge "
                "segments.")
    panel = "Y-Nb"
    x_label = "Y (ppm)"
    y_label = "Nb (ppm)"
    x_range = (1, 2000)
    y_range = (1, 2000)

    def _compute_xy(self, df):
        y = resolve_column(df, ["Y"])
        nb = resolve_column(df, ["Nb"])
        if not (y and nb):
            return None, None
        return (pd.to_numeric(df[y], errors="coerce"),
                pd.to_numeric(df[nb], errors="coerce"))


class Pearce1984YbTa(_Pearce1984):
    key = "pearce1984_YbTa"
    title = "Ta vs Yb — Pearce et al. (1984)"
    citation = ("Pearce, Harris & Tindle (1984) Figure 3b, boundary "
                "coordinates from its caption, with the syn-COLG/WPG "
                "boundary as corrected by Verma et al. (2012): the "
                "printed (55,20) points away from the two fields it "
                "divides.  This is the diagram that separates volcanic-"
                "arc from syn-collision granites.")
    panel = "Yb-Ta"
    x_label = "Yb (ppm)"
    y_label = "Ta (ppm)"
    x_range = (0.1, 100)
    y_range = (0.05, 100)

    def _compute_xy(self, df):
        yb = resolve_column(df, ["Yb"])
        ta = resolve_column(df, ["Ta"])
        if not (yb and ta):
            return None, None
        return (pd.to_numeric(df[yb], errors="coerce"),
                pd.to_numeric(df[ta], errors="coerce"))


class Pearce1984YNbRb(_Pearce1984):
    key = "pearce1984_YNbRb"
    title = "Rb vs (Y + Nb) — Pearce et al. (1984)"
    citation = ("Pearce, Harris & Tindle (1984) Figure 4a, boundary "
                "coordinates from its caption.  Adding Rb to the Y-Nb "
                "pair is what separates volcanic-arc from syn-collision "
                "granites; Rb is mobile, so prefer the Yb-Ta diagram "
                "for altered rocks.")
    panel = "YNb-Rb"
    x_label = "Y + Nb (ppm)"
    y_label = "Rb (ppm)"
    x_range = (1, 2000)
    y_range = (1, 2000)

    def _compute_xy(self, df):
        y = resolve_column(df, ["Y"])
        nb = resolve_column(df, ["Nb"])
        rb = resolve_column(df, ["Rb"])
        if not (y and nb and rb):
            return None, None
        return (pd.to_numeric(df[y], errors="coerce")
                + pd.to_numeric(df[nb], errors="coerce"),
                pd.to_numeric(df[rb], errors="coerce"))


class Pearce1984YbTaRb(_Pearce1984):
    key = "pearce1984_YbTaRb"
    title = "Rb vs (Yb + Ta) — Pearce et al. (1984)"
    citation = ("Pearce, Harris & Tindle (1984) Figure 4b, boundary "
                "coordinates from its caption, with the syn-COLG/VAG "
                "boundary as corrected by Verma et al. (2012): the "
                "printed endpoint (6,2000) misses the junction at "
                "(6,200) that the other two boundaries share.  Rb is "
                "mobile, so prefer the Yb-Ta diagram for altered rocks.")
    panel = "YbTa-Rb"
    x_label = "Yb + Ta (ppm)"
    y_label = "Rb (ppm)"
    x_range = (0.5, 1000)
    y_range = (1, 2000)

    def _compute_xy(self, df):
        yb = resolve_column(df, ["Yb"])
        ta = resolve_column(df, ["Ta"])
        rb = resolve_column(df, ["Rb"])
        if not (yb and ta and rb):
            return None, None
        return (pd.to_numeric(df[yb], errors="coerce")
                + pd.to_numeric(df[ta], errors="coerce"),
                pd.to_numeric(df[rb], errors="coerce"))

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
# Yang et al. (2019) — major-element log-ratios as a source-lithology proxy
# ---------------------------------------------------------------------------
#
# Equations transcribed from Table 1 of Yang, Li, Jiang, Xu, Guo, Li &
# Zhang (2019), J. Geophys. Res. Solid Earth 124, 3429-3480,
# doi:10.1029/2018JB016145.  All oxides in wt.%.
#
# FCMS and FCKANTMS are *residuals*: the measured ln(FeO/CaO) minus the
# value a lherzolite melt of the same ln(MgO/SiO2) would have.  A melt
# of primitive-mantle-like lherzolite therefore sits at zero - the
# paper reports 0.00 +/- 0.08 - and a melt of a mafic (pyroxenite or
# hornblendite) source sits above it.  They are dimensionless numbers
# of order 0.1, not oxide sums of order 10.
#
# This module previously computed both as plain linear combinations of
# oxide wt.%, e.g. "FCMS = SiO2 + 0.99 K2O - 1.32 Al2O3 - 0.78 MgO",
# on axes running to +/- 20.  Neither expression appears in the paper,
# and neither is a log-ratio.  It also plotted FCMS against FCKANTMS,
# which the paper notes are near-equivalent ("FCMS is very close to
# FCKANTMS"), so that pair carries almost no discrimination.  The axes
# used here are the ones the paper recommends.
# It also cited the wrong journal and authors.

#: Equation (1): ln(FeO/CaO) of a lherzolite melt, as a cubic in
#: ln(MgO/SiO2).  Highest power first.
YANG_LHERZOLITE_TREND = (0.058, 0.636, 1.850, 1.170)

#: Equation (7): the same trend recalibrated for FCKANT.
YANG_FCKANT_TREND = (0.062, 0.641, 1.871, 1.201)

#: Constant of equation (8).
YANG_FCKANTMS_CONSTANT = 1.473

#: Coefficients of the three log-ratio corrections in equations (6)/(8).
YANG_K_AL, YANG_TI_NA, YANG_NA_K_TI = 0.08, 0.052, 0.036


def _ln_ratio(df, num, den):
    a = resolve_column(df, [num])
    b = resolve_column(df, [den])
    if a is None or b is None:
        return None
    x = pd.to_numeric(df[a], errors="coerce")
    y = pd.to_numeric(df[b], errors="coerce")
    return np.log(x.where(x > 0) / y.where(y > 0))


def _yang_feo_cao(df):
    """ln(FeO/CaO), all iron as FeO — the convention of the
    experimental melts these parameters were calibrated on."""
    from ...preprocess import get_feot
    cao = resolve_column(df, ["CaO"])
    if cao is None:
        return None
    canon = {}
    for name in ("FeO", "Fe2O3", "FeOt", "Fe2O3t"):
        col = resolve_column(df, [name])
        if col is not None:
            canon[name] = pd.to_numeric(df[col], errors="coerce")
    if not canon:
        return None
    feot = get_feot(pd.DataFrame(canon, index=df.index))
    if feot is None:
        return None
    ca = pd.to_numeric(df[cao], errors="coerce")
    return np.log(feot.where(feot > 0) / ca.where(ca > 0))


def _cubic(coefs, x):
    a, b, c, d = coefs
    return a * x ** 3 + b * x ** 2 + c * x + d


def _yang_fcms(df):
    """FCMS, equation (2) of Table 1."""
    fc = _yang_feo_cao(df)
    ms = _ln_ratio(df, "MgO", "SiO2")
    if fc is None or ms is None:
        return None
    return fc - _cubic(YANG_LHERZOLITE_TREND, ms)


def _yang_fckantms(df):
    """FCKANTMS, equation (8) of Table 1."""
    fc = _yang_feo_cao(df)
    ms = _ln_ratio(df, "MgO", "SiO2")
    k_al = _ln_ratio(df, "K2O", "Al2O3")
    ti_na = _ln_ratio(df, "TiO2", "Na2O")
    na_k = _ln_ratio(df, "Na2O", "K2O")
    na_ti = _ln_ratio(df, "Na2O", "TiO2")
    if any(v is None for v in (fc, ms, k_al, ti_na, na_k, na_ti)):
        return None
    a, b, c, _d = YANG_FCKANT_TREND
    return (fc
            - YANG_K_AL * k_al
            - YANG_TI_NA * ti_na
            - YANG_NA_K_TI * na_k * na_ti
            - a * ms ** 3 - b * ms ** 2 - c * ms
            - YANG_FCKANTMS_CONSTANT)


def _yang_silica_index(df):
    """ln(SiO2 / (CaO + Na2O + TiO2)), the x axis of Figure 7b."""
    si = resolve_column(df, ["SiO2"])
    parts = [resolve_column(df, [n]) for n in ("CaO", "Na2O", "TiO2")]
    if si is None or any(p is None for p in parts):
        return None
    total = sum(pd.to_numeric(df[p], errors="coerce") for p in parts)
    sio2 = pd.to_numeric(df[si], errors="coerce")
    return np.log(sio2.where(sio2 > 0) / total.where(total > 0))


# Boundaries, verbatim from the Figure 7 caption.  X is the silica
# index, Y is FCKANTMS.
YANG_TRANSITIONAL_UPPER = ((-0.5, -0.2), (1.0, 0.37), (1.5, 0.37))
YANG_PERIDOTITE_EVOLVED = ((-0.4, -0.75), (1.05, 0.15), (1.3, 0.35),
                           (2.8, 1.75))
YANG_PERIDOTITE_PRIMARY = ((-0.4, -1.45), (1.05, 0.05), (1.3, 0.15),
                           (2.9, 1.7))


class Yang2019FCKANTMS(Diagram):
    """FCKANTMS vs ln(SiO2/(CaO+Na2O+TiO2)) — Yang et al. (2019)."""

    key = "yang_2019_fckantms"
    title = ("FCKANTMS vs ln(SiO$_2$/(CaO+Na$_2$O+TiO$_2$)) — "
             "Yang et al. (2019)")
    citation = ("Yang et al. (2019) JGR Solid Earth 124, 3429-3480, "
                "Fig. 7b.  FCKANTMS is equation (8) of their Table 1: "
                "the measured ln(FeO/CaO) minus what a lherzolite melt "
                "of the same ln(MgO/SiO2) would have, after correcting "
                "for melting degree and pressure.  A peridotite melt "
                "sits at 0.00 ± 0.08; a melt above the Mg#-labelled "
                "boundaries cannot come from normal peridotite or "
                "harzburgite.  All iron as FeO.  Boundary coordinates "
                "verbatim from the figure caption.")
    x_label = "ln(SiO$_2$ / (CaO + Na$_2$O + TiO$_2$))"
    y_label = "FCKANTMS"
    x_range = (-0.5, 4.5)
    y_range = (-2.0, 2.0)

    def _compute_xy(self, df):
        x = _yang_silica_index(df)
        y = _yang_fckantms(df)
        if x is None or y is None:
            return None, None
        return x, y

    def _draw_background(self, ax, options):
        for poly, style, label, offset in (
            (YANG_PERIDOTITE_EVOLVED, dict(color="#444", lw=1.1, ls="--"),
             "Mg# = 0.5–0.6", (5, 4)),
            (YANG_PERIDOTITE_PRIMARY, dict(color="#444", lw=1.1, ls="--"),
             "Mg# = 0.7", (5, -10)),
            (YANG_TRANSITIONAL_UPPER,
             dict(color="#2a9d5c", lw=1.1, ls="--"), "transitional", (5, -3)),
        ):
            ax.plot([q[0] for q in poly], [q[1] for q in poly], **style)
            ax.annotate(label, poly[-1], xytext=offset,
                        textcoords="offset points", fontsize=7.5,
                        color=style["color"])
        ax.axhline(0.0, color="#888", lw=0.7, zorder=0)
        ax.text(0.1, 1.6, "mafic lithology", fontsize=9, style="italic",
                color="#333")
        ax.text(2.7, -1.6, "peridotite / harzburgite", fontsize=9,
                style="italic", color="#333", ha="center")
