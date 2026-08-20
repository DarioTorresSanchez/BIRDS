"""Winchester & Floyd (1977) Zr/TiO2 – Nb/Y classification.

The workhorse diagram for naming **altered** volcanic rocks.  Zr, Ti,
Nb and Y are the four least-mobile elements during sea-floor
alteration, weathering and greenschist-facies metamorphism, so their
ratios still record the primary magmatic composition long after the
alkalis (and therefore the TAS name) have been reset.

Axes
----
* **X — Nb/Y**: an alkalinity proxy.  Sub-alkaline rocks sit below
  ~0.6, alkaline above; strongly silica-undersaturated (foidal) rocks
  reach Nb/Y > 3.
* **Y — Zr/TiO2 × 0.0001**: a differentiation proxy standing in for
  SiO2.  The factor 0.0001 converts wt.% TiO2 to ppm, so the plotted
  value is the dimensionless ppm/ppm mass ratio
  ``Zr / (TiO2 × 10 000)``.  Basalts ≈ 0.003-0.008, andesites ≈ 0.02,
  dacites ≈ 0.06, rhyolites > 0.3.

Both axes are logarithmic.

.. warning::
   The field-boundary coordinates below are a DIGITISATION of the
   published figure, not values tabulated by the authors (Winchester &
   Floyd give the diagram graphically only).  The topology — which
   field borders which, and the axis conventions — is canonical, but
   individual vertices carry roughly ±5 % uncertainty.  Verify against
   the original figure before using field assignments in print.
"""

from __future__ import annotations

import pandas as pd

from .base import Diagram, resolve_column


# Field polygons in (Nb/Y, Zr/TiO2×0.0001).  Vertices are given in the
# order they are walked; all coordinates are strictly positive so the
# polygons render correctly on the log-log axes.
#
# Sub-alkaline stack (left) is bounded on the right by a boundary that
# steps outward with increasing differentiation:
#     (0.60, 0.001) → (0.60, 0.030) → (0.90, 0.100)
#                   → (1.30, 0.600) → (1.60, 10.0)
_WF_FIELDS: dict = {
    # ---- sub-alkaline series (left column) --------------------------
    "Sub-alkaline\nbasalt":   [(0.01, 0.001), (0.60, 0.001),
                                (0.60, 0.008), (0.01, 0.008)],
    "Andesite /\nbasalt":     [(0.01, 0.008), (0.60, 0.008),
                                (0.60, 0.020), (0.01, 0.020)],
    "Andesite":               [(0.01, 0.020), (0.60, 0.020),
                                (0.60, 0.030), (0.90, 0.060),
                                (0.01, 0.060)],
    "Rhyodacite /\ndacite":   [(0.01, 0.060), (0.90, 0.060),
                                (0.90, 0.100), (1.30, 0.300),
                                (0.01, 0.300)],
    "Rhyolite":               [(0.01, 0.300), (1.30, 0.300),
                                (1.30, 0.600), (1.60, 10.0),
                                (0.01, 10.0)],
    # ---- alkaline series (right of the divider) ----------------------
    "Alkali\nbasalt":         [(0.60, 0.001), (2.50, 0.001),
                                (2.50, 0.030), (0.60, 0.030)],
    "Trachy-\nandesite":      [(0.60, 0.030), (2.50, 0.030),
                                (2.80, 0.150), (0.90, 0.150),
                                (0.90, 0.100)],
    "Trachyte":               [(0.90, 0.150), (2.80, 0.150),
                                (3.20, 0.700), (1.35, 0.700),
                                (1.30, 0.600), (1.30, 0.300)],
    "Comendite /\npantellerite": [(1.35, 0.700), (3.20, 0.700),
                                   (3.20, 10.0), (1.60, 10.0)],
    # ---- strongly alkaline / foidal (far right) ----------------------
    "Basanite /\nnephelinite": [(2.50, 0.001), (100.0, 0.001),
                                 (100.0, 0.060), (2.65, 0.060),
                                 (2.50, 0.030)],
    "Phonolite":              [(2.65, 0.060), (100.0, 0.060),
                                (100.0, 10.0), (3.20, 10.0),
                                (3.20, 0.700), (2.80, 0.150)],
}

# Log-space label positions — the base class centroid would sit at the
# arithmetic mean of log-distributed vertices and drift badly here.
_WF_LABEL_POS: dict = {
    "Sub-alkaline\nbasalt":      (0.07, 0.0030),
    "Andesite /\nbasalt":        (0.07, 0.0130),
    "Andesite":                  (0.07, 0.0350),
    "Rhyodacite /\ndacite":      (0.07, 0.1400),
    "Rhyolite":                  (0.07, 1.7000),
    "Alkali\nbasalt":            (1.25, 0.0055),
    "Trachy-\nandesite":         (1.55, 0.0700),
    "Trachyte":                  (2.00, 0.3400),
    "Comendite /\npantellerite": (2.10, 2.4000),
    "Basanite /\nnephelinite":   (12.0, 0.0090),
    "Phonolite":                 (12.0, 0.9000),
}


class WinchesterFloyd1977(Diagram):
    key = "winchester_floyd_1977"
    title = "Zr/TiO₂ – Nb/Y — altered volcanic rocks (Winchester & Floyd 1977)"
    citation = ("Winchester, J.A. & Floyd, P.A. (1977) Chemical Geology "
                "20, 325-343.  Immobile-element replacement for the TAS "
                "diagram in altered, weathered or metamorphosed volcanic "
                "rocks.  X = Nb/Y (alkalinity proxy), Y = Zr/TiO₂ × "
                "0.0001 = Zr(ppm)/TiO₂(ppm) (differentiation proxy, SiO₂ "
                "stand-in).  Both axes logarithmic.  Field boundaries "
                "are a digitisation of the published figure (the authors "
                "give it graphically only) — verify against the original "
                "before publishing field assignments.")
    x_label = "Nb / Y"
    y_label = "Zr / TiO$_2$ $\\times$ 0.0001"
    x_range = (0.01, 100.0)
    y_range = (0.001, 10.0)
    log_x = True
    log_y = True
    field_polygons = _WF_FIELDS
    field_label_pos = _WF_LABEL_POS
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
        yv = zr_v / ti_ppm
        return x, yv
