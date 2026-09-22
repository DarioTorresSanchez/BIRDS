"""Hastie et al. (2007) Th–Co classification for altered arc rocks.

Th and Co are far less mobile than K2O and SiO2 during sea-floor
alteration, weathering and low-grade metamorphism, so this diagram
replaces the K2O–SiO2 (Peccerillo & Taylor 1976) plot for altered /
ancient volcanic-arc rocks:

* X axis — Co (ppm), LINEAR and **reversed** (70 → 0) so silica
  increases to the right like a conventional Harker plot;
* Y axis — Th (ppm), log scale 0.01 → 100;
* two **sloping** boundaries split the rock series into B (basalt) |
  BA/A (basaltic andesite–andesite) | D/R* (dacite, rhyolite; latites
  and trachytes also plot here).  They are straight in
  (Co, log10 Th) space and lean towards lower Co as Th rises — a
  rock's silica proxy depends on both elements, not on Co alone;
* two sub-horizontal boundaries, also straight in (Co, log10 Th)
  space, separate the island-arc tholeiite (IAT), calc-alkaline (CA)
  and high-K + shoshonitic (H-K and SHO) series — the immobile-element
  analogues of the low-/medium-/high-K fields.

Provenance of the boundaries
----------------------------
All four lines were measured from the published figure rather than
transcribed from equations.  The figure was calibrated on its own axis
ticks (Co 70→0 across the frame; four decades of Th, 0.01 → 100), the
line pixels were extracted and fitted by least squares with outlier
rejection.  Every fit closed to under one pixel of maximum residual
over 350–450 sampled points, so the anchors below carry roughly
half a percent of reading error — far finer than the line width in the
source figure.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Diagram, PlotOptions, resolve_column


# --------------------------------------------------------------------------
# Series boundaries — anchored at the two ends of the Co axis.
# Straight in (Co, log10 Th) space, which is how the figure draws them.
# --------------------------------------------------------------------------

#: Tholeiite ↔ calc-alkaline, as (Co, Th) at Co = 70 and Co = 0.
_IAT_CA = ((70.0, 0.2444), (0.0, 1.3436))

#: Calc-alkaline ↔ high-K calc-alkaline + shoshonite.
_CA_HK = ((70.0, 2.2007), (0.0, 8.9606))

# --------------------------------------------------------------------------
# Composition dividers — anchored at the two ends of the Th axis.
# Straight in (Co, log10 Th) space; note these are NOT vertical.
# --------------------------------------------------------------------------

#: B ↔ BA/A, as (Th, Co) at Th = 0.01 and Th = 100.
_B_BAA = ((0.01, 38.332), (100.0, 24.011))

#: BA/A ↔ D/R*.
_BAA_DR = ((0.01, 23.030), (100.0, 6.908))

_LINE = dict(color="#444", linewidth=0.9, alpha=0.9, zorder=1)


def _log_segment(p0, p1, n: int = 64):
    """Densify a segment that is straight in (x, log10 y) space.

    Matplotlib joins two points with a straight line *in screen space*,
    which on a log axis is not the same curve the figure draws, so the
    segment is sampled before plotting.
    """
    (x0, y0), (x1, y1) = p0, p1
    xs = np.linspace(x0, x1, n)
    ys = 10.0 ** np.linspace(np.log10(y0), np.log10(y1), n)
    return xs, ys


def _log_segment_x(p0, p1, n: int = 64):
    """Same, for a line anchored at two *Th* values instead of two Co."""
    (y0, x0), (y1, x1) = p0, p1
    ys = 10.0 ** np.linspace(np.log10(y0), np.log10(y1), n)
    xs = np.linspace(x0, x1, n)
    return xs, ys


class Hastie2007ThCo(Diagram):
    key = "hastie_2007_thco"
    title = "Th – Co — altered arc rocks (Hastie et al. 2007)"
    citation = ("Hastie, A. R., Kerr, A. C., Pearce, J. A. & Mitchell, "
                "S. F. (2007) J. Petrology 48(12), 2341-2357.  Immobile-"
                "element (Th, Co) replacement for the K2O-SiO2 plot in "
                "altered volcanic-arc rocks.  Columns: B = basalt, "
                "BA/A = basaltic andesite / andesite, D/R* = dacite / "
                "rhyolite, also latite & trachyte.  Bands: IAT = "
                "island-arc tholeiite; CA = calc-alkaline; H-K & SHO = "
                "high-K and shoshonite.  All four boundaries measured "
                "from the published figure (fits closed to <1 px).")
    x_label = "Co (ppm)"
    y_label = "Th (ppm)"
    x_range = (70.0, 0.0)        # reversed axis — SiO2 proxy increases →
    y_range = (0.01, 100.0)
    log_y = True

    def _compute_xy(self, df):
        co = resolve_column(df, ("Co",))
        th = resolve_column(df, ("Th",))
        if co is None or th is None:
            return None, None
        return (pd.to_numeric(df[co], errors="coerce"),
                pd.to_numeric(df[th], errors="coerce"))

    def _draw_background(self, ax, options: PlotOptions) -> None:
        # Series boundaries — sub-horizontal, rising towards low Co.
        for anchors in (_IAT_CA, _CA_HK):
            ax.plot(*_log_segment(*anchors), **_LINE)
        # Composition dividers — steep, leaning towards low Co as Th rises.
        for anchors in (_B_BAA, _BAA_DR):
            ax.plot(*_log_segment_x(*anchors), **_LINE)

        # Series names, set in the left margin as in the source figure.
        ax.text(68.5, 30.0, "High-K calc-alkaline\nand Shoshonite Series",
                fontsize=8.5, color="#333", ha="left", va="center",
                linespacing=1.3, zorder=2)
        ax.text(68.5, 1.15, "Calc-alkaline\nSeries",
                fontsize=8.5, color="#333", ha="left", va="center",
                linespacing=1.3, zorder=2)
        ax.text(68.5, 0.12, "Tholeiite\nSeries",
                fontsize=8.5, color="#333", ha="left", va="center",
                linespacing=1.3, zorder=2)

        # Column names along the bottom edge, between the steep lines.
        for co_val, name in ((50.0, "B"), (29.5, "BA/A"), (14.5, "D/R*")):
            ax.text(co_val, 0.018, name, fontsize=8.5, color="#333",
                    ha="center", va="center", zorder=2)
