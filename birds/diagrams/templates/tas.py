"""TAS (Total Alkalis vs Silica) diagrams – volcanic and plutonic."""

from __future__ import annotations

import pandas as pd
from .base import Diagram, resolve_column


# ---------------------------------------------------------------------------
# Volcanic (Le Bas et al. 1986; Le Maitre et al. 2002)
# ---------------------------------------------------------------------------

# Field polygons follow Le Bas et al. (1986, J. Petrol. 27, 745–750) and the
# IUGS revision by Le Maitre et al. (2002, "Igneous Rocks: A Classification
# and Glossary of Terms").  All vertices use SiO2 wt% on X and (Na2O+K2O)
# wt% on Y; compositions must be renormalised to 100 % anhydrous beforehand.
_VOLCANIC_FIELDS = {
    "Picrobasalt":              [(41, 0), (45, 0), (45, 3), (41, 3)],
    "Basalt":                   [(45, 0), (52, 0), (52, 5), (45, 5)],
    "Basaltic\nandesite":       [(52, 0), (57, 0), (57, 5.9), (52, 5)],
    "Andesite":                 [(57, 0), (63, 0), (63, 7), (57, 5.9)],
    "Dacite":                   [(63, 0), (77,0), (69, 8), (63, 7)],
    "Rhyolite":                 [(77,0), (69, 8)],
    "Trachybasalt":             [(45, 5), (52, 5), (49.4, 7.3), (49.4, 7.3)],
    "Basaltic\ntrachyandesite": [(52, 5), (57, 5.9), (53, 9.3), (49.4, 7.3)],
    "Trachyandesite":           [(57, 5.9), (63, 7), (57.6, 11.7), (53, 9.3)],
    "Trachyte /\nTrachydacite": [(69,8),(69,12)],
    "Tephrite /\nBasanite":     [(41, 3), (45, 3), (45,5),(49.4,7.3),(45,9.4),(41, 7)],
    "Phonotephrite":            [(45, 9.4), (49.4, 7.3),
                                 (53, 9.3), (48.4, 11.5)],
    "Tephriphonolite":          [(48.4, 11.5), (53, 9.3),
                                 (57.6, 11.7), (52.5, 14)],
    "Phonolite":                [(57.6,11.7),(63,14.5),
                                 (57.6,11.7),(52.5,14),(50,15.083)],

}


# Irvine & Baragar (1971) alkaline / sub-alkaline boundary on the TAS
# plane. Coordinates from Rollinson & Pease (2021), Fig. 3.3 — same list
# used by the standalone ``ib1971`` diagram so we stay self-consistent.
_IB1971_BOUNDARY = [
    (39.2, 0.0), (40.0, 0.4), (43.2, 2.0), (45.0, 2.8), (48.0, 4.0),
    (50.0, 4.75), (53.7, 6.0), (55.0, 6.4), (60.0, 8.0), (65.0, 8.8),
    (77.4, 10.0),
]


def _draw_ib_boundary(ax, x_max: float = 78.0) -> None:
    """Draw the Irvine & Baragar (1971) alkaline / sub-alkaline curve on
    top of an existing TAS axis, plus the two side labels.  Extends the
    last segment horizontally to the right edge so the curve doesn't
    stop short inside the Rhyolite / Granite field.
    """
    xs = [p[0] for p in _IB1971_BOUNDARY]
    ys = [p[1] for p in _IB1971_BOUNDARY]
    # Extend the curve flat to the right edge of the panel.
    if xs[-1] < x_max:
        xs.append(x_max)
        ys.append(ys[-1])
    ax.plot(xs, ys, color="#1f3a93", linewidth=1.4, linestyle="--",
            alpha=0.85, zorder=2,
            label="Irvine & Baragar (1971)")
    # Tiny italic labels on either side of the curve.  Positioned at
    # SiO2 ≈ 70 where the curve is roughly flat — high-Si rocks land
    # cleanly above (alkaline) or below (sub-alkaline).
    ax.text(70, 11.0, "Alkaline", fontsize=8.5, color="#1f3a93",
            style="italic", alpha=0.9, ha="center", zorder=2)
    ax.text(70, 8.6, "Sub-alkaline", fontsize=8.5, color="#1f3a93",
            style="italic", alpha=0.9, ha="center", zorder=2)


class TASVolcanic(Diagram):
    key = "tas_volcanic"
    title = "Total Alkalis – Silica (TAS) – Volcanic rocks"
    citation = ("Le Bas et al. (1986); Le Maitre et al. (2002); "
                "Irvine & Baragar (1971) alkaline boundary overlaid. "
                "Recalculate to 100 % anhydrous wt.% oxides.")
    x_label = "SiO$_2$ (wt.%)"
    y_label = "Na$_2$O + K$_2$O (wt.%)"
    x_range = (35, 78)
    y_range = (0, 16)
    field_polygons = _VOLCANIC_FIELDS
    field_label_pos = {
        "Foidite":         (39, 12.5),
        "Phonolite":       (56.5, 14),       # centred in the new pentagon
        "Picrobasalt":     (43, 1.5),
        "Basalt":          (48.5, 2.5),
        "Basaltic\nandesite": (54.5, 3),
        "Andesite":        (60, 3.5),
        "Dacite":          (67, 3.5),
        "Rhyolite":        (75, 8),
        "Trachybasalt":    (48.5, 5.5),          # bottom-centre (widest part)
        "Basaltic\ntrachyandesite": (53.5, 6.8),
        "Trachyandesite":  (57.5, 8.5),
        "Trachyte /\nTrachydacite": (65, 10),
        "Tephrite /\nBasanite": (43, 6.0),
        "Phonotephrite":   (48.5, 9.0),
        "Tephriphonolite": (53, 12.0),
    }

    def _compute_xy(self, df):
        si = resolve_column(df, ["SiO2"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if not (si and na and k):
            return None, None
        x = pd.to_numeric(df[si], errors="coerce")
        y = (pd.to_numeric(df[na], errors="coerce")
             + pd.to_numeric(df[k], errors="coerce"))
        return x, y

    def _draw_background(self, ax, options) -> None:
        super()._draw_background(ax, options)
        _draw_ib_boundary(ax, x_max=self.x_range[1])


# ---------------------------------------------------------------------------
# Plutonic (Middlemost (1994))
# ---------------------------------------------------------------------------
# Field polygons follow Middlemost (1994)

_PLUTONIC_FIELDS = {
    "Peridot\ngabbro":   [(41,0), (41,3), (45, 3), (45,0)],
    "Gabbro":            [(45, 0), (45,5), (52, 5), (52,0)],
    "Gabbro\ndiorite":   [(52, 0), (52,5), (57,5.9), (57, 0)],
    "Diorite":           [(57,0), (57,5.9), (63,7), (63, 0)],
    "Granodiorite":      [(63,0), (63,7), (69,8), (77.3,0)],
    "Granite":           [(77.3,0),(87.5,4.7),(85.9,6.8),(71.8,13.5),(69,8)],
    "Quartz\nMonzonite": [(71.8,13.5),(61,8.74),(63,7),(69,8),(71.8,13.5)],
    "Syenite":           [(71.8,13.5),(61,8.74),(57.6,11.7),(61,13.5),(63,16.2),(71.8,13.5)],
    "Monzonite":         [(63,7),(61,8.74),(57.6,11.7),(53,9.3),(57,5.9)],
    "Monzo\ndiorite":    [(57,5.9),(53,9.3),(49.4,7.3),(52,5)],
    "Monzo\n-gabbro":    [(52,5),(49.4,7.3),(45,5),(52,5)],
    "Foid\ngabbro":      [(41,3),(45,3),(45,5),(49.4,7.3),(45,9.4),(41,7),(41,3)],
    "Foidolite":         [(41,3),(37,3),(35,9),(37,14),(52.3,18),(57,18),(52.5,14),(48.4,11.5),(45,9.4),(41,7),(41,3)],
    "Foid\nMonzodiorite":[(45,9.4),(49.4,7.3)],
    "Foid\nMonzosyenite":[(48.4,11.5),(53,9.3)],
    "Foid\nSyenite":     [(52.5,14),(57,18),(63,16.2),(61,13.5),(57.6,11.7),(52.5,14)],

}


class TASPlutonic(Diagram):
    key = "tas_plutonic"
    title = "Total Alkalis – Silica (TAS) – Plutonic rocks"
    citation = ("Middlemost (1994); "
                "Irvine & Baragar (1971) alkaline boundary overlaid.")
    x_label = "SiO$_2$ (wt.%)"
    y_label = "Na$_2$O + K$_2$O (wt.%)"
    x_range = (30, 90)
    y_range = (0, 19)
    field_polygons = _PLUTONIC_FIELDS
    field_label_pos = {
        "Foidolite":      (40, 12.5),
        "Foid syenite":   (56.5, 15),
        "Peridotgabbro":  (40, 1.5),
        "Gabbro":         (48.5, 2.5),
        "Diorite":        (60, 3.0),
        "Granodiorite":   (70, 3.5),
        "Granite":        (80, 5.0),
        "Monzogabbro":    (47, 6.5),
        "Monzodiorite":   (52, 7.2),
        "Monzonite":      (58, 8.5),
        "Syenite":        (65, 12),
        "Quartz\nMonzonite": (66, 8.5),
        "Foid gabbro":    (43, 7.0),
        "Foid\nMonzodiorite": (49, 10),
        "Foid\nMonzosyenite": (53, 12),
    }

    def _compute_xy(self, df):
        si = resolve_column(df, ["SiO2"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if not (si and na and k):
            return None, None
        x = pd.to_numeric(df[si], errors="coerce")
        y = (pd.to_numeric(df[na], errors="coerce")
             + pd.to_numeric(df[k], errors="coerce"))
        return x, y

    def _draw_background(self, ax, options) -> None:
        super()._draw_background(ax, options)
        _draw_ib_boundary(ax, x_max=self.x_range[1])
