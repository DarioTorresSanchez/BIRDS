"""Bivariate tectonic discrimination diagrams.

Coordinates compiled from Rollinson & Pease (2021) Chapter 5 figure
captions and the original references cited below each class.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ...normalizations import REE_CHONDRITES, TIO2_WT_TO_TI_PPM
from .base import Diagram, inverse_logratio, resolve_column


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
#
# Geol. Soc. London Spec. Publ. 7, 14-24, Figure 3.  Everything about
# how this was drawn was wrong, in the way Saccani's Figures 8 and 9
# were: the **axes were swapped** -- Pearce & Gale put Ti/Y across the
# bottom and Zr/Y up the side -- **both were logarithmic** where the
# figure is linear on both, and the frame, (1, 30) by (100, 1000), was
# invented.  The published one runs Ti/Y 0 to about 1100 against Zr/Y
# 0 to about 8.  The fields went with the axes: within-plate is to the
# **right**, at high Ti/Y, not above.
#
# The boundary coordinates are printed, in the caption of Rollinson &
# Pease (2021) Figure 5.2a: "Boundary coordinates: (513, 0) and
# (313, 7.5)", as (Ti/Y, Zr/Y).  They were already quoted in a comment
# here and then drawn as if they were (Zr/Y, Ti/Y) pairs, which put a
# line from (1, 513) to (30, 313) on the plot -- unrelated to either
# reading.
#
# Checked against Pearce & Gale's own Figure 3 by measuring it.  With
# the axes calibrated on their tick labels, the drawn line fits a
# straight line to an rms of 0.3 in Ti/Y over 144 sampled rows and
# gives (521.6, 0) and (303.3, 7.5): 1.7 % and 3.1 % from the printed
# pair, against a calibration uncertainty of about 4 units in Ti/Y.
# The printed pair is what is used, as published numbers rather than
# my measurement of a 1977 half-tone; the measurement is recorded as
# the independent check that it agrees.

#: Rollinson & Pease (2021) Fig. 5.2a caption, as (Ti/Y, Zr/Y).
PEARCE_GALE_BOUNDARY = ((513.0, 0.0), (313.0, 7.5))

#: Measured off Pearce & Gale's own Figure 3, for the record.
PEARCE_GALE_MEASURED = ((521.6, 0.0), (303.3, 7.5))

#: Rollinson & Pease's frame rather than Pearce & Gale's.  Figure 3
#: runs Ti/Y to about 1118 and Zr/Y only to about 7.9, which clips an
#: ordinary ocean-island basalt: Sun & McDonough's OIB sits at Zr/Y
#: 9.7.  Figure 5.2a redraws the same diagram on 0-1200 by 0-18, which
#: is also the frame the printed boundary coordinates come with.
PEARCE_GALE_X_RANGE = (0, 1200)
PEARCE_GALE_Y_RANGE = (0, 18)

#: Verma's (2010) success rates, as Figure 5.2a labels its two fields.
PEARCE_GALE_RATES = {"plate margin": 90, "within-plate": 89}


class PearceGale1977(Diagram):
    key = "pearce_gale_1977"
    title = "Zr/Y vs Ti/Y — Pearce & Gale (1977)"
    citation = ("Pearce & Gale (1977) Fig. 3, on the frame Rollinson & "
                "Pease (2021) Fig. 5.2a redraws it on. Boundary "
                "coordinates (513, 0) and (313, 7.5) in Ti/Y–Zr/Y are "
                "printed in that caption and confirmed by measuring "
                "the original figure. Within-plate basalts "
                "(continental rift, ocean island) plot to the right at "
                "better than 89 %, plate-margin basalts (island arc, "
                "continental arc, N-MORB) to the left at better than "
                "90 %, per Verma's (2010) reassessment over ~4000 "
                "analyses — but only with E-MORB excluded, which this "
                "diagram does not separate. Neither source draws the "
                "boundary above Zr/Y = 7.5, so it is not extended "
                "there.")
    x_label = "Ti/Y"
    y_label = "Zr/Y"
    x_range = PEARCE_GALE_X_RANGE
    y_range = PEARCE_GALE_Y_RANGE

    def _compute_xy(self, df):
        zr = resolve_column(df, ["Zr"])
        y = resolve_column(df, ["Y"])
        ti_el = resolve_column(df, ["Ti"])
        ti_ox = resolve_column(df, ["TiO2"])
        if not (zr and y and (ti_el or ti_ox)):
            return None, None
        y_s = pd.to_numeric(df[y], errors="coerce")
        y_s = y_s.where(y_s > 0)
        if ti_el:
            ti_ppm = pd.to_numeric(df[ti_el], errors="coerce")
        else:
            ti_ppm = pd.to_numeric(df[ti_ox], errors="coerce") * TIO2_WT_TO_TI_PPM
        return (ti_ppm / y_s, pd.to_numeric(df[zr], errors="coerce") / y_s)

    def _draw_background(self, ax, options):
        # Drawn as the segment it is published as.  Figure 5.2a stops
        # it at Zr/Y = 7.5 and Figure 3's own frame barely reaches 7.9,
        # so neither source says where it goes above that and it is not
        # extrapolated there.
        (x0, y0), (x1, y1) = PEARCE_GALE_BOUNDARY
        ax.plot([x0, x1], [y0, y1], color="#444", lw=1.4, zorder=0)
        ax.text(200, 5.0, "plate margin\nbasalts\n(>90 %)", fontsize=9,
                style="italic", color="#333", ha="center", va="center",
                zorder=0)
        ax.text(750, 10.5, "within-plate\nbasalts\n(>89 %)", fontsize=9,
                style="italic", color="#333", ha="center", va="center",
                zorder=0)


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
# Saccani (2015) — Th-Nb and Ce-Dy-Yb systematics
# ---------------------------------------------------------------------------
#
# Saccani says plainly that the boundaries of his Figures 5, 8 and 9
# "were drawn by eye in order to obtain the best discrimination between
# different basaltic types", so there is no analysis to recompute.  What
# he does give, printed in brackets on each of the three figures beside
# an arrow pointing at the end it belongs to, are the coordinates of
# every line.  Those are what is used here; nothing is measured off a
# figure.
#
# Figure 5 is normalised to N-MORB.  Figures 8 and 9 are normalised to
# **chondrite** — both captions say so — and were being drawn here
# against N-MORB, which shrinks Dy by 17.9 and Yb by 17.9 and puts every
# sample off the frame of axes that run to 25.  Their axes were also the
# wrong way round, and both are linear rather than logarithmic.
#
# Figure 12a names fields inside the Th-Nb frame (CAB, BABB, IAT and
# boninite, and so on) and draws envelopes for them.  Those are not
# reproduced: they carry no coordinates, they overlap heavily, and the
# paper measures that overlap itself — 25 % of the MORB-OIB array
# samples fall in the wrong sub-type.  The two arrays, which the text
# quantifies at better than 99 % each, are what this diagram draws.

_NMORB_SUN = {"Nb": 2.33, "Th": 0.12, "Yb": 3.05, "Dy": 4.55, "Ce": 7.50}

#: Chondrite for Figures 8 and 9, taken from the table the spider
#: diagrams already normalise against rather than copied, so the two
#: cannot drift apart.  Ce 0.612, Dy 0.254, Yb 0.17 ppm.
_SACCANI_CHONDRITE = REE_CHONDRITES["Sun & McDonough (1989) – CI"]

#: Primordial mantle in Figure 5a's own coordinates, printed on the
#: figure as (x=0.306; y=0.708).  Sun & McDonough's PM over their
#: N-MORB: Nb 0.713/2.33 and Th 0.0850/0.12 give exactly these.  Three
#: of the four segments start or end here.
_SACCANI_PM = (0.306, 0.708)

#: Figure 5a, each segment with the endpoints printed beside it.  The
#: first is the one that discriminates: ">99% of the analyzed basaltic
#: rocks from oceanic, subduction-unrelated settings plot below the
#: segment between the primordial mantle (PM) composition and the point
#: with co-ordinates NbN = 100; ThN = 1000", and ">99% of
#: subduction-related basaltic rocks plot above this segment".
_SACCANI_TH_NB_LINES = (
    (_SACCANI_PM, (100.0, 1000.0)),   # MORB-OIB array below, arc array above
    ((0.01, 0.1), _SACCANI_PM),       # its continuation below PM
    ((0.01, 20.0), (2.2, 8.0)),       # upper bound, inside the arc array
    (_SACCANI_PM, (0.5, 0.01)),       # the near-vertical one, down from PM
)

#: Figure 8, the one separation line: (x=0.4; y=1.5) to (x=2; y=0.9).
_SACCANI_CE_YB_LINE = ((0.4, 1.5), (2.0, 0.9))

#: Figure 9, the one separation line: (x=7; y=25) to (x=9.5; y=0).
_SACCANI_DY_YB_LINE = ((7.0, 25.0), (9.5, 0.0))

#: "99.5% of boninites have DyN < 8.5 and 99% of IATs have DyN > 8.5" —
#: a second and simpler rule the paper gives for the same two types.
_SACCANI_BONINITE_DY_N = 8.5


class Saccani2015NbTh(Diagram):
    key = "saccani2015_nb_th"
    title = "Th$_N$ vs Nb$_N$ — Saccani (2015)"
    citation = ("Saccani (2015) Fig. 5a; the line coordinates are "
                "printed on that figure. Nb and Th normalised to N-MORB "
                "(Sun & McDonough 1989). More than 99 % of "
                "subduction-unrelated oceanic basalts plot below the "
                "segment from primordial mantle to (100, 1000), and "
                "more than 99 % of subduction-related ones above it. "
                "The author states that he drew these lines by eye.")
    x_label = "Nb$_N$"
    y_label = "Th$_N$"
    x_range = (0.01, 100)
    y_range = (0.01, 1000)
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
        for (x0, y0), (x1, y1) in _SACCANI_TH_NB_LINES:
            ax.plot([x0, x1], [y0, y1], color="#444", lw=1.0, zorder=0)
        ax.plot([_SACCANI_PM[0]], [_SACCANI_PM[1]], marker="s",
                markersize=5, color="#222", linestyle="none", zorder=0)
        # The published figure rotates the two array names along the
        # boundary.  Here they are horizontal: the line is at 45° in
        # axes fraction, but only because the frame spans four decades
        # of Nb against five of Th, and the angle it subtends on screen
        # moves with the shape of the canvas.
        ax.annotate("PM", _SACCANI_PM, textcoords="offset points",
                    xytext=(-7, 0), fontsize=9, color="#222",
                    ha="right", va="center", zorder=0)
        ax.text(0.05, 3.0, "VOLCANIC ARC ARRAY", fontsize=9, color="#333",
                style="italic", ha="center", va="center", zorder=0)
        ax.text(15.0, 2.0, "MORB – OIB ARRAY", fontsize=9, color="#333",
                style="italic", ha="center", va="center", zorder=0)


# ---------------------------------------------------------------------------
# Defant & Drummond (1990) — adakite vs classic arc
# ---------------------------------------------------------------------------
#
# Nature 347, 662-665.  The paper has exactly three figures: Y or Yb
# against the age of the subducting lithosphere (Fig. 1), Sr/Y against Y
# (Fig. 2), and a chondrite-normalised spider (Fig. 3).
#
# Two things follow, and both were wrong here before.
#
# **Figure 2 draws no adakite field.**  Its adakites are plotted as
# crosses and nothing encloses them.  What it does draw is three
# labelled fields -- boninite, island-arc andesite-dacite-rhyolite and
# MORB -- four model melting curves, and an AFC trend arrow.  The
# dashed "adakite boundary" that used to be here, and the "Sr/Y > 40"
# in its citation, are in neither the figure nor the text.
#
# What the paper does give for adakites is a list of numbers, in the
# second paragraph of page 663: "low Y and HREE relative to island-arc
# ADRs (for example, Y and Yb <= 18 and 1.9 p.p.m., respectively), high
# Sr relative to island-arc ADR (rarely <400 p.p.m.)", together with
# SiO2 >= 56 %, Al2O3 >= 15 % and usually MgO < 3 %.  Those two trace
# thresholds are exact, quotable, and are what both diagrams now draw.
#
# **There is no Yb against La/Yb figure in this paper at all.**
# Rollinson & Pease (2021) list one in their table of discrimination
# diagrams, attributed to Defant & Drummond (1990) and marked
# "unevaluated", and that is where the attribution here came from.  The
# figure is Drummond & Defant (1990, J. Geophys. Res.) Figure 10, drawn
# in drummond_defant1990.py under the key the attribution gave it.

#: Figure 2's own frame.  It was (0, 50) by (0, 200) here, so a sample
#: landed at less than half its published Y and more than twice its
#: published Sr/Y relative to anything drawn on it.
DD_FIG2_X_RANGE = (0, 25)
DD_FIG2_Y_RANGE = (0, 500)

#: "Y and Yb <= 18 and 1.9 p.p.m., respectively" — page 663.  Adakites
#: lie to the left of these on the two diagrams.
DD_ADAKITE_Y_MAX = 18.0
DD_ADAKITE_YB_MAX = 1.9

#: Island-arc andesite-dacite-rhyolite field, measured off Figure 2.
#: The axes were calibrated on their own tick labels (residuals 1.5 px
#: in Y and 1.7 px in Sr/Y, against 83 px per unit of Y and 3.1 px per
#: unit of Sr/Y), then the dashes of the outline were located as
#: connected components and their centroids converted.  Good to about
#: 0.3 in Y and 3 in Sr/Y; it is a 1990 half-tone scan and the outline
#: is dashed through a dense scatter.
DD_ISLAND_ARC_ADR = (
    (17.9, 3.0), (17.9, 32.1), (18.4, 48.0), (19.1, 58.7), (20.0, 59.6),
    (21.0, 52.9), (21.9, 44.3), (22.7, 36.7), (23.5, 31.0), (24.3, 26.0),
    (25.0, 21.0), (25.0, 3.0),
)

#: MORB field, the solid bar along the foot of Figure 2.  This one is
#: exact rather than approximate: it is filled, so its edges were read
#: as the longest unbroken runs of ink, giving Y 19.97-25.01 and Sr/Y
#: -1.8 to 15.2.  It starts on the Y = 20 gridline and runs off the
#: right-hand edge of the frame.
DD_MORB_FIELD = (20.0, 25.0, 0.0, 15.0)

# The boninite field of Figure 2 is deliberately **not** drawn.  Its
# outline does not resolve unambiguously in the scan: the long dashed
# line at Sr/Y ~ 49 that runs right from about Y = 2 may be its top
# edge or may be a separate boundary, and the two readings give fields
# of quite different extent.  Guessing which would be inventing a
# boundary, which is the fault this diagram already had.


class DefantDrummondYSrY(Diagram):
    key = "defant_drummond_YSrY"
    title = "Sr/Y vs Y — Defant & Drummond (1990)"
    citation = ("Defant & Drummond (1990) Fig. 2, fields measured off "
                "the published figure. The paper draws no adakite "
                "envelope — its adakites are plotted as crosses — so "
                "the line shown is its stated threshold instead: "
                "adakites have Y ≤ 18 ppm, with Sr rarely below "
                "400 ppm, against island-arc andesite-dacite-rhyolite "
                "at higher Y and lower Sr/Y. The boninite field of "
                "Fig. 2 is not reproduced; its outline does not resolve "
                "in the scan.")
    x_label = "Y (ppm)"
    y_label = "Sr/Y"
    x_range = DD_FIG2_X_RANGE
    y_range = DD_FIG2_Y_RANGE

    def _compute_xy(self, df):
        sr = resolve_column(df, ["Sr"])
        y = resolve_column(df, ["Y"])
        if not (sr and y):
            return None, None
        y_s = pd.to_numeric(df[y], errors="coerce")
        y_s = y_s.where(y_s > 0)
        return y_s, pd.to_numeric(df[sr], errors="coerce") / y_s

    def _draw_background(self, ax, options):
        xs = [p[0] for p in DD_ISLAND_ARC_ADR] + [DD_ISLAND_ARC_ADR[0][0]]
        ys = [p[1] for p in DD_ISLAND_ARC_ADR] + [DD_ISLAND_ARC_ADR[0][1]]
        ax.plot(xs, ys, color="#444", lw=1.1, linestyle="--", zorder=0)
        lo, hi, bot, top = DD_MORB_FIELD
        ax.fill_between([lo, hi], [bot, bot], [top, top], color="#222",
                        zorder=0)
        ax.axvline(DD_ADAKITE_Y_MAX, color="#444", lw=1.2, zorder=0)
        ax.text(DD_ADAKITE_Y_MAX - 0.5, 430, "adakite: Y ≤ 18 ppm",
                fontsize=9, color="#333", style="italic", ha="right",
                va="center", zorder=0)
        ax.text(21.4, 72, "Island arc ADR", fontsize=9, color="#333",
                style="italic", ha="center", va="bottom", zorder=0)
        ax.text(22.5, 7.0, "MORB", fontsize=8, color="#fff",
                style="italic", ha="center", va="center", zorder=0)


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
# Saccani (2015) Figures 8 and 9 — chondrite-normalised Ce, Dy and Yb
# ---------------------------------------------------------------------------
#
# Both are linear, both carry one separation line, and both print that
# line's two ends on the figure.  See the note above Saccani2015NbTh.

class Saccani2015DyYb(Diagram):
    """DyN vs YbN — separates boninite from island-arc tholeiite."""
    key = "saccani2015_dy_yb"
    title = "Yb$_N$ vs Dy$_N$ — Saccani (2015)"
    citation = ("Saccani (2015) Fig. 9; the separation-line coordinates "
                "are printed on that figure. Chondrite-normalised (Sun "
                "& McDonough 1989). Boninite plots left of the line and "
                "island-arc tholeiite right, at stated rates of 100 % "
                "and 99 %. The paper gives a simpler rule for the same "
                "pair: 99.5 % of boninites have Dy_N below 8.5 and 99 % "
                "of IATs above it.")
    x_label = "Dy$_N$"
    y_label = "Yb$_N$"
    x_range = (0, 25)
    y_range = (0, 25)
    log_x = False
    log_y = False

    def _compute_xy(self, df):
        dy = resolve_column(df, ["Dy"])
        yb = resolve_column(df, ["Yb"])
        if not (dy and yb):
            return None, None
        return (pd.to_numeric(df[dy], errors="coerce")
                / _SACCANI_CHONDRITE["Dy"],
                pd.to_numeric(df[yb], errors="coerce")
                / _SACCANI_CHONDRITE["Yb"])

    def _draw_background(self, ax, options):
        (x0, y0), (x1, y1) = _SACCANI_DY_YB_LINE
        ax.plot([x0, x1], [y0, y1], color="#444", lw=1.2, zorder=0)
        # Figure 9 writes these two just either side of the line, where
        # its own clouds leave a gap.  Here they sit higher, above where
        # both clouds reach, so that they cannot land on a sample.
        ax.text(3.5, 22.0, "Boninite\n(100 %)", fontsize=10, style="italic",
                color="#333", ha="center", va="center", zorder=0)
        ax.text(16.0, 22.0, "IAT\n(99 %)", fontsize=10, style="italic",
                color="#333", ha="center", va="center", zorder=0)


class Saccani2015CeDyYb(Diagram):
    """(Dy/Yb)N vs (Ce/Yb)N — separates G-MORB from N-MORB."""
    key = "saccani2015_ce_dy_yb"
    title = "(Dy/Yb)$_N$ vs (Ce/Yb)$_N$ — Saccani (2015)"
    citation = ("Saccani (2015) Fig. 8; the separation-line coordinates "
                "are printed on that figure. Chondrite-normalised (Sun "
                "& McDonough 1989). Garnet-influenced MORB plots above "
                "the line and normal MORB below, at stated rates of "
                "96 % and 99 %.")
    x_label = "(Ce/Yb)$_N$"
    y_label = "(Dy/Yb)$_N$"
    x_range = (0, 2.5)
    y_range = (0.5, 2)
    log_x = False
    log_y = False

    def _compute_xy(self, df):
        ce = resolve_column(df, ["Ce"])
        dy = resolve_column(df, ["Dy"])
        yb = resolve_column(df, ["Yb"])
        if not (ce and dy and yb):
            return None, None
        ce_n = pd.to_numeric(df[ce], errors="coerce") / _SACCANI_CHONDRITE["Ce"]
        dy_n = pd.to_numeric(df[dy], errors="coerce") / _SACCANI_CHONDRITE["Dy"]
        yb_n = pd.to_numeric(df[yb], errors="coerce") / _SACCANI_CHONDRITE["Yb"]
        yb_n = yb_n.where(yb_n > 0)
        return ce_n / yb_n, dy_n / yb_n

    def _draw_background(self, ax, options):
        (x0, y0), (x1, y1) = _SACCANI_CE_YB_LINE
        ax.plot([x0, x1], [y0, y1], color="#444", lw=1.2, zorder=0)
        # As on Figure 9, away from where the published clouds sit: both
        # of these are at the right-hand end, one above the line and one
        # below, rather than rotated along it as Figure 8 draws them.
        ax.text(1.85, 1.78, "G-MORB (96 %)", fontsize=10, style="italic",
                color="#333", ha="center", va="center", zorder=0)
        ax.text(1.75, 0.62, "N-MORB (99 %)", fontsize=10, style="italic",
                color="#333", ha="center", va="center", zorder=0)


# ---------------------------------------------------------------------------
# Yang et al. (2019) — major-element log-ratios as a source-lithology proxy
# ---------------------------------------------------------------------------
#
# Equations transcribed from Table 1 of Yang, Li, Jiang, Xu, Guo, Li &
# Zhang (2019), J. Geophys. Res. Solid Earth 124, 3458-3490,
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


#: Figure 1a's own frame, where the lherzolite trend is drawn.
YANG_FIG1A_X_RANGE = (-3.5, 1.0)
YANG_FIG1A_Y_RANGE = (-1.4, 1.4)


class Yang2019FCMS(Diagram):
    """ln(FeO/CaO) vs ln(MgO/SiO2), with the lherzolite trend drawn.

    FCMS had no diagram: the statistics table reported it and there
    was nothing to read the number against.  This is the plane it is
    defined in.

    Yang et al. publish no discrimination diagram for FCMS and no
    field boundaries for it -- Figure 7's caption is the only place in
    the paper that gives boundary coordinates, and those are for
    FCKANTMS.  So none are drawn here.  What is published, and what
    this draws, is the lherzolite trend itself: the cubic of equation
    (2), printed on Figure 1a beside the curve, repeated in Table 1
    and again in the conclusions.  FCMS *is* the vertical distance
    from it, so a sample's FCMS can be read off the plot directly.
    """

    key = "yang_2019_fcms"
    title = "ln(FeO/CaO) vs ln(MgO/SiO$_2$) — Yang et al. (2019)"
    citation = ("Yang et al. (2019) JGR Solid Earth 124, 3458-3490, "
                "Fig. 1a. The curve is their lherzolite trend, the "
                "cubic of equation (2), printed on the figure: "
                "y = 0.058x³ + 0.636x² + 1.850x + 1.170, R² = 0.944. "
                "FCMS is the vertical distance from it, so lherzolite "
                "melts sit near zero and pyroxenite and hornblendite "
                "melts well above or below. The paper draws no field "
                "boundaries on this plane and none are invented here. "
                "It also warns that lherzolite melts scatter about the "
                "curve, because ln(FeO/CaO) and ln(MgO/SiO₂) both "
                "depend on melting degree and pressure — which is why "
                "FCKANTMS, which corrects for both, is the parameter "
                "the paper's conclusions recommend. All iron as FeO.")
    x_label = "ln(MgO / SiO$_2$)"
    y_label = "ln(FeO / CaO)"
    x_range = YANG_FIG1A_X_RANGE
    y_range = YANG_FIG1A_Y_RANGE

    def _compute_xy(self, df):
        x = _ln_ratio(df, "MgO", "SiO2")
        y = _yang_feo_cao(df)
        if x is None or y is None:
            return None, None
        return x, y

    def _draw_background(self, ax, options):
        xs = np.linspace(*YANG_FIG1A_X_RANGE, 200)
        ax.plot(xs, _cubic(YANG_LHERZOLITE_TREND, xs), color="#444",
                lw=1.3, zorder=0)
        ax.annotate("lherzolite trend  (FCMS = 0)", (-1.9, -0.47),
                    xytext=(0, -14), textcoords="offset points",
                    fontsize=8.5, style="italic", color="#333",
                    ha="center", zorder=0)
        ax.text(-2.6, 0.95, "FCMS > 0", fontsize=9, style="italic",
                color="#333", zorder=0)
        ax.text(-2.6, -1.15, "FCMS < 0", fontsize=9, style="italic",
                color="#333", zorder=0)


class Yang2019FCKANTMS(Diagram):
    """FCKANTMS vs ln(SiO2/(CaO+Na2O+TiO2)) — Yang et al. (2019)."""

    key = "yang_2019_fckantms"
    title = ("FCKANTMS vs ln(SiO$_2$/(CaO+Na$_2$O+TiO$_2$)) — "
             "Yang et al. (2019)")
    citation = ("Yang et al. (2019) JGR Solid Earth 124, 3458-3490, "
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
