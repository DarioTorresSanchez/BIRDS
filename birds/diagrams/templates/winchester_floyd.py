"""Winchester & Floyd (1977) Zr/TiO2 – Nb/Y classification.

The workhorse diagram for naming **altered** volcanic rocks.  Zr, Ti,
Nb and Y are the four least-mobile elements during sea-floor
alteration, weathering and greenschist-facies metamorphism, so their
ratios still record the primary magmatic composition long after the
alkalis (and therefore the TAS name) have been reset.

Axes
----
* **X — Nb/Y**: an alkalinity proxy.  The sub-alkaline / alkaline
  divide is the vertical line at Nb/Y = 0.64; strongly
  silica-undersaturated (foidal) rocks reach Nb/Y > 3.
* **Y — Zr/TiO2 × 0.0001**: a differentiation proxy standing in for
  SiO2.  The factor 0.0001 converts wt.% TiO2 to ppm, so the plotted
  value is the dimensionless ppm/ppm mass ratio
  ``Zr / (TiO2 × 10 000)``.  Basalts ≈ 0.003-0.008, andesites ≈ 0.02,
  dacites ≈ 0.06, rhyolites > 0.3.

Both axes are logarithmic, and the axis limits match the published
figure exactly — Nb/Y 0.01 → 10, Zr/TiO2 0.001 → 5.  Outside that box
the scheme simply does not define a field, so the boundaries are not
extrapolated to fill a wider frame.

Solid and dashed boundaries
---------------------------
The original distinguishes the two, and so does this implementation:
a **dashed** boundary is one the authors drew as approximate because
the data did not constrain it tightly.  Reading a rock's name off a
dashed boundary carries the uncertainty the authors intended, and
flattening both into one line style would hide that.

Provenance
----------
Measured from the published figure.  The axes were calibrated on their
own tick marks, the drawing was separated into a solid line network, a
set of dashes and the lettering by connected-component analysis, the
network was skeletonised to recover its junctions, and each boundary
was reduced to a polyline in log-log space.

Two cautions about the source image, both checked rather than assumed:

* Its **Nb/Y = 0.1 tick is misplaced** — it sits where 0.05 belongs.
  The other three ticks (0.01 and 10 at the frame edges, 1 in the
  middle) agree on one scale to better than a pixel, and the
  sub-alkaline / alkaline divide then lands at Nb/Y = 0.64, the value
  the literature quotes for it.  That calibration is the one used
  here; the stray tick is a defect of the redrawing.
* The Zr/TiO2 axis is clean: three ticks a decade apart to the pixel,
  with the frame edges falling on 0.001 and 5.0.
"""

from __future__ import annotations

import pandas as pd

from .base import Diagram, PlotOptions, resolve_column


#: Sub-alkaline / alkaline divide — the diagram's backbone.
SUBALKALINE_LIMIT = 0.6409

# --------------------------------------------------------------------------
# Boundaries, as polylines in (Nb/Y, Zr/TiO2 × 0.0001).
# Straight segments in log-log space, which is how the figure draws them.
# --------------------------------------------------------------------------

_SOLID: tuple = (
    # Comendite/pantellerite ↔ phonolite + trachyte, from the top edge.
    ((1.5747, 4.9055), (1.8575, 1.3401), (1.1850, 0.0963)),
    # Rhyolite ↔ comendite/pantellerite.
    ((0.3311, 0.7094), (0.9250, 0.1300)),
    # Rhyolite ↔ trachyte, the short link between the two junctions.
    ((0.9250, 0.1300), (1.1800, 0.0957)),
    # Rhyolite ↔ trachyandesite.
    ((0.6409, 0.0845), (0.9250, 0.1300)),
    # The sub-alkaline / alkaline divide.  It stops just short of the
    # bottom axis in the figure, and is left that way rather than
    # stretched to the frame.
    ((0.6409, 0.0845), (0.6409, 0.00162)),
    # Trachyte ↔ trachyandesite.
    ((1.1800, 0.0951), (5.3345, 0.0395)),
    # Trachyandesite ↔ alkali basalt.
    ((0.6409, 0.0191), (1.3850, 0.0247), (2.8587, 0.0152)),
    # Trachyandesite ↔ basanite/nephelinite.
    ((2.8587, 0.0152), (5.3345, 0.0395)),
    # Alkali basalt ↔ basanite/nephelinite.  Stops short of the frame,
    # exactly as the figure draws it.
    ((2.8587, 0.0152), (2.8587, 0.0041)),
    # Andesite ↔ rhyodacite/dacite — solid where it meets the divide.
    ((0.3190, 0.0250), (0.6409, 0.0269)),
    # Andesite/basalt ↔ andesite — solid where it meets the divide.
    ((0.4822, 0.0139), (0.6409, 0.0187)),
)

_DASHED: tuple = (
    # Andesite ↔ rhyodacite/dacite.
    ((0.0229, 0.0597), (0.3190, 0.0250)),
    # Rhyodacite/dacite ↔ rhyolite.
    ((0.1948, 0.1186), (0.5685, 0.0869)),
    # Andesite/basalt ↔ andesite.
    ((0.0735, 0.0122), (0.4440, 0.0138)),
    # Sub-alkaline basalt ↔ andesite/basalt: flat, then climbing to
    # join the solid stub at the divide.
    ((0.0277, 0.0047), (0.2127, 0.0055), (0.4822, 0.0139)),
    # Phonolite ↔ trachyte, carrying on from the solid line above it.
    # It curves, so it keeps more vertices than the straight boundaries.
    ((1.9093, 1.1504), (2.0547, 0.5975), (2.9656, 0.3286),
     (4.2025, 0.2516), (5.9009, 0.1889), (8.9166, 0.1484)),
    # Trachyandesite ↔ basanite/nephelinite, out to the right edge.
    ((6.2634, 0.0398), (8.9797, 0.0398)),
)

#: Field names at the positions the figure sets them.
_LABELS: tuple = (
    ("Sub-alkaline\nbasalt",       0.0950, 0.00187),
    ("Andesite /\nbasalt",         0.0422, 0.00753),
    ("Andesite",                   0.0216, 0.03812),
    ("Rhyodacite /\ndacite",       0.0424, 0.09694),
    ("Rhyolite",                   0.2616, 0.29180),
    ("Comendite /\npantellerite",  0.7917, 1.63223),
    ("Phonolite",                  5.3886, 1.89660),
    ("Trachyte",                   2.8289, 0.14663),
    ("Trachy-\nandesite",          1.7967, 0.03440),
    ("Alkali\nbasalt",             1.3710, 0.00493),
    ("Basanite /\nnephelinite",    5.8718, 0.00842),
)

_LINE = dict(color="#444", linewidth=0.9, alpha=0.9, zorder=1)


class WinchesterFloyd1977(Diagram):
    key = "winchester_floyd_1977"
    title = "Zr/TiO₂ – Nb/Y — altered volcanic rocks (Winchester & Floyd 1977)"
    citation = ("Winchester, J.A. & Floyd, P.A. (1977) Chemical Geology "
                "20, 325-343.  Immobile-element replacement for the TAS "
                "diagram in altered, weathered or metamorphosed volcanic "
                "rocks.  X = Nb/Y (alkalinity proxy; sub-alkaline / "
                "alkaline divide at 0.64), Y = Zr/TiO₂ × 0.0001 = "
                "Zr(ppm)/TiO₂(ppm) (differentiation proxy, SiO₂ "
                "stand-in).  Both axes logarithmic.  Boundaries measured "
                "from the published figure; dashed ones are those the "
                "authors themselves drew as approximate.")
    x_label = "Nb / Y"
    y_label = "Zr / TiO$_2$ $\\times$ 0.0001"
    x_range = (0.01, 10.0)
    y_range = (0.001, 5.0)
    log_x = True
    log_y = True
    field_label_fontsize = 7.0

    def _compute_xy(self, df):
        nb = resolve_column(df, ("Nb",))
        y_col = resolve_column(df, ("Y",))
        zr = resolve_column(df, ("Zr",))
        ti = resolve_column(df, ("TiO2", "TiO₂"))
        if nb is None or y_col is None or zr is None or ti is None:
            return None, None
        nb_v = pd.to_numeric(df[nb], errors="coerce")
        y_v = pd.to_numeric(df[y_col], errors="coerce")
        zr_v = pd.to_numeric(df[zr], errors="coerce")
        ti_v = pd.to_numeric(df[ti], errors="coerce")
        # Mask non-positive denominators so the log axes stay defined.
        x = nb_v / y_v.where(y_v > 0)
        # TiO2 arrives in wt.% — convert to ppm so the ratio matches the
        # "× 0.0001" axis convention.
        ti_ppm = ti_v.where(ti_v > 0) * 10_000.0
        return x, zr_v / ti_ppm

    def _draw_background(self, ax, options: PlotOptions) -> None:
        for polyline in _SOLID:
            ax.plot([p[0] for p in polyline], [p[1] for p in polyline],
                    linestyle="-", **_LINE)
        for polyline in _DASHED:
            ax.plot([p[0] for p in polyline], [p[1] for p in polyline],
                    linestyle=(0, (5, 4)), **_LINE)
        for name, x, y in _LABELS:
            ax.text(x, y, name, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#333",
                    alpha=0.95, zorder=2, linespacing=1.2)
