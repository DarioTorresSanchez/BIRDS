"""K2O vs SiO2 — subdivision of the sub-alkalic series.

Two schemes on one plane, exactly as Rollinson & Pease (2021)
Figure 3.4 compiles them:

* **Le Maitre et al. (1989)** split sub-alkalic rocks into low-, medium-
  and high-K with two straight dashed lines between SiO2 48 and 68, plus
  a vertical at SiO2 = 48 below which the subdivision is not applied.
* **Rickwood (1989)** draws each division as a *band* rather than a
  line, because the boundaries of Peccerillo & Taylor (1976), Ewart
  (1982), Innocenti et al. (1982), Carr (1985) and Middlemost (1985)
  disagree by about that much.  All three bands are drawn here; reading
  a sample as "high-K" when it sits inside a band overstates what the
  scheme can tell you.

Provenance
----------
Nothing here is measured.  The caption of Figure 3.4 prints every
plotting coordinate, and all of them are transcribed verbatim below.
The earlier version of this module carried only the upper bound of the
shoshonite band — with its first point rounded from 1.38 to 1.4 —
described it as the band's midpoint, and left out both the Le Maitre
vertical and the other two bands entirely.
"""

from __future__ import annotations

import pandas as pd

from .base import Diagram, resolve_column

# --------------------------------------------------------------------------
# Le Maitre et al. (1989) — straight dashed lines, as (start, end).
# --------------------------------------------------------------------------

LM89_LINES = {
    "low-K / medium-K":  ((48.0, 0.3), (68.0, 1.2)),
    "medium-K / high-K": ((48.0, 1.2), (68.0, 3.1)),
}

#: SiO2 below which Le Maitre et al. do not apply the subdivision.
LM89_SIO2_MIN = 48.0

# --------------------------------------------------------------------------
# Rickwood (1989) — each division is a band, given as (upper, lower).
# --------------------------------------------------------------------------

RICKWOOD_BANDS = {
    "shoshonitic / high-K": (
        ((45.0, 1.38), (48.0, 1.7), (56.0, 3.3), (63.0, 4.2), (70.0, 5.1)),
        ((45.0, 1.37), (48.0, 1.6), (56.0, 2.98), (63.0, 3.87), (70.0, 4.61)),
    ),
    "high-K / calc-alkalic": (
        ((45.0, 0.98), (49.0, 1.28), (52.0, 1.5), (63.0, 2.48),
         (70.0, 3.1), (75.0, 3.43)),
        ((45.0, 0.92), (49.0, 1.1), (52.0, 1.35), (63.0, 2.32),
         (70.0, 2.86), (75.0, 3.25)),
    ),
    "calc-alkalic / low-K": (
        ((45.0, 0.2), (48.0, 0.41), (61.0, 0.97), (70.0, 1.38), (75.0, 1.51)),
        ((45.0, 0.15), (48.0, 0.3), (61.0, 0.8), (70.0, 1.23), (75.0, 1.44)),
    ),
}

_BAND = dict(color="#444", linewidth=0.8, alpha=0.9, zorder=1)
_DASH = dict(color="#444", linewidth=0.9, linestyle="--", alpha=0.9, zorder=1)


class K2OvsSiO2(Diagram):
    key = "k2o_sio2"
    title = "K$_2$O vs SiO$_2$ – Sub-alkalic series subdivision"
    citation = ("Peccerillo & Taylor (1976); Le Maitre et al. (1989) "
                "low-/medium-/high-K lines; Rickwood (1989) bands.  "
                "Plotting coordinates from Rollinson & Pease (2021) "
                "Fig. 3.4 caption.  Rickwood's divisions are bands, not "
                "lines — a sample inside one is not resolved by this "
                "scheme.")
    x_label = "SiO$_2$ (wt.%)"
    y_label = "K$_2$O (wt.%)"
    x_range = (45, 80)
    y_range = (0, 8)
    field_polygons = {}  # boundaries handled in _draw_background

    def _compute_xy(self, df):
        si = resolve_column(df, ["SiO2"])
        k = resolve_column(df, ["K2O"])
        if not (si and k):
            return None, None
        return (pd.to_numeric(df[si], errors="coerce"),
                pd.to_numeric(df[k], errors="coerce"))

    def _draw_background(self, ax, options):
        # Rickwood's bands: both bounds drawn, with a light fill between
        # them so the width reads as the uncertainty it represents.
        for upper, lower in RICKWOOD_BANDS.values():
            for polyline in (upper, lower):
                ax.plot([p[0] for p in polyline], [p[1] for p in polyline],
                        **_BAND)
            # Both bounds of a band are given at the same SiO2 values.
            ax.fill_between([p[0] for p in upper],
                            [p[1] for p in upper], [p[1] for p in lower],
                            color="#888", alpha=0.18, linewidth=0, zorder=0)

        # Le Maitre's straight lines and the vertical they start from.
        for label, ((x1, y1), (x2, y2)) in LM89_LINES.items():
            ax.plot([x1, x2], [y1, y2], **_DASH)
            ax.text(x2, y2, "  " + label, fontsize=7.5, color="#333",
                    va="center")
        ax.plot([LM89_SIO2_MIN, LM89_SIO2_MIN], [0.0, LM89_LINES[
            "medium-K / high-K"][0][1]], **_DASH)

        ax.text(66, 0.45, "Low-K (tholeiitic)", fontsize=7.5, color="#333")
        ax.text(66, 1.75, "Medium-K (calc-alkalic)", fontsize=7.5,
                color="#333")
        ax.text(60, 3.55, "High-K (calc-alkalic)", fontsize=7.5, color="#333")
        ax.text(57, 4.6, "Shoshonitic", fontsize=7.5, color="#333")
