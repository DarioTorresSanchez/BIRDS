"""Hastie et al. (2007) Th–Co classification for altered arc rocks.

Th and Co are far less mobile than K2O and SiO2 during sea-floor
alteration, weathering and low-grade metamorphism, so this diagram
replaces the K2O–SiO2 (Peccerillo & Taylor 1976) plot for altered /
ancient volcanic-arc rocks:

* X axis — Co (ppm), LINEAR and **reversed** (70 → 0) so silica
  increases to the right like a conventional Harker plot;
* Y axis — Th (ppm), log scale 0.01 → 100;
* vertical guides at Co = 45 and Co = 24 split the rock series into
  B (basalt) | BA/A (basaltic andesite–andesite) | D/R* (dacite,
  rhyolite; latites and trachytes also plot here);
* two sub-horizontal boundaries (straight in log-Th space) separate
  the island-arc tholeiite (IAT), calc-alkaline (CA) and high-K +
  shoshonitic (H-K and SHO) series — the immobile-element analogues
  of the low-/medium-/high-K fields.

.. warning::
   The series-boundary anchor values below are an APPROXIMATE
   digitisation of Figure 2 of Hastie et al. (2007) and should be
   calibrated against the published figure before use in print.
   The overall topology (axes, columns, three bands) is canonical.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Diagram, PlotOptions, resolve_column


# Boundary anchors as (Co, Th) pairs.  Straight segments in
# (Co, log10 Th) space, matching how the published figure draws them.
_IAT_CA_ANCHORS = ((70.0, 0.10), (45.0, 0.15), (24.0, 0.35), (0.0, 0.90))
_CA_HK_ANCHORS = ((70.0, 0.60), (45.0, 1.00), (24.0, 2.20), (0.0, 6.00))


def _boundary_xy(anchors) -> tuple[np.ndarray, np.ndarray]:
    """Densify a polyline defined in (Co, log10 Th) space so it renders
    as intended on the log axis."""
    xs_out: list[float] = []
    ys_out: list[float] = []
    for (x0, y0), (x1, y1) in zip(anchors[:-1], anchors[1:]):
        xs = np.linspace(x0, x1, 24)
        ly = np.linspace(np.log10(y0), np.log10(y1), 24)
        xs_out.extend(xs)
        ys_out.extend(10.0 ** ly)
    return np.asarray(xs_out), np.asarray(ys_out)


class Hastie2007ThCo(Diagram):
    key = "hastie_2007_thco"
    title = "Th – Co — altered arc rocks (Hastie et al. 2007)"
    citation = ("Hastie, A. R., Kerr, A. C., Pearce, J. A. & Mitchell, "
                "S. F. (2007) J. Petrology 48(12), 2341-2357.  Immobile-"
                "element (Th, Co) replacement for the K2O-SiO2 plot in "
                "altered volcanic-arc rocks.  Columns: B = basalt "
                "(Co 70-45), BA/A = basaltic andesite / andesite "
                "(45-24), D/R* = dacite / rhyolite, also latite & "
                "trachyte (24-0).  Bands: IAT = island-arc tholeiite; "
                "CA = calc-alkaline; H-K & SHO = high-K and shoshonite. "
                "Series boundaries are an approximate digitisation of "
                "Fig. 2 — calibrate before publication use.")
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
        # Vertical rock-series guides.
        for co_val in (45.0, 24.0):
            ax.axvline(co_val, color="#444", linewidth=0.9, alpha=0.85,
                       zorder=1)
        # Series boundaries — straight in log space.
        for anchors in (_IAT_CA_ANCHORS, _CA_HK_ANCHORS):
            xs, ys = _boundary_xy(anchors)
            ax.plot(xs, ys, color="#444", linewidth=0.9, alpha=0.85,
                    zorder=1)
        # Band labels (positions chosen inside the BA/A column).
        ax.text(34, 0.045, "IAT", fontsize=9, color="#333",
                ha="center", va="center", zorder=2)
        ax.text(57.5, 0.30, "CA", fontsize=9, color="#333",
                ha="center", va="center", zorder=2)
        ax.text(34, 15.0, "H-K and SHO", fontsize=9, color="#333",
                ha="center", va="center", zorder=2)
        # Column headers along the top edge.
        ax.text(57.5, 60, "B", fontsize=8.5, color="#555",
                ha="center", va="center", style="italic", zorder=2)
        ax.text(34.5, 60, "BA/A", fontsize=8.5, color="#555",
                ha="center", va="center", style="italic", zorder=2)
        ax.text(12, 60, "D/R*", fontsize=8.5, color="#555",
                ha="center", va="center", style="italic", zorder=2)
