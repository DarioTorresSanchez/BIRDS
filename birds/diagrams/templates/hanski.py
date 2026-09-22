"""Hanski et al. (2001) high-Mg classification — [Al2O3] vs [TiO2].

Eight fields for high-magnesian rocks, separated by five straight
boundaries: four sub-parallel lines rising gently to the right, cut by
one steep divider that splits every picrite and komatiite band into an
Al-depleted (left) and an Al-undepleted (right) half.

    Meimechite                          above the top line
    Al-depleted picrite   | Picrite     between top line and 0.02 line
    Ti-enriched, Al-depl. | Ti-enriched komatiite
    Al-depleted komatiite | Al-undepleted komatiite
    Boninite                            below the bottom line

Provenance of the boundaries
----------------------------
Measured from the published figure.  The axes were calibrated on their
own tick marks (fourteen on [TiO2], every 0.01 up to 0.13; six on
[Al2O3] every 0.05 up to 0.25), the line network was isolated by
connected-component analysis, skeletonised, and each boundary fitted by
least squares with outlier rejection.  Residuals closed under 1 px for
four of the five boundaries and 2.4 px for the lowest one.

The four sub-horizontal boundaries turn out to be very nearly parallel:
a joint fit with a single shared slope gives 0.0407 with a mean
residual of 0.37 px, and intercepts of 0.0000, 0.0097, 0.0198 and
0.0897.  That is close enough to a family of lines of slope 0.04
through 0, 0.01, 0.02 and 0.09 that the published definition is
probably exactly that.  The individually fitted values are kept here
because they are what was measured; if the paper states round numbers,
swapping them in moves every boundary by under a pixel.

.. warning::
   The **axis projection is unverified**.  ``[Al2O3]`` and ``[TiO2]``
   are bracketed in the source because they are olivine-projected
   quantities, not raw oxides, and the projection currently
   implemented below is demonstrably wrong: its denominator goes
   negative for every komatiite and meimechite, which are exactly the
   rocks this diagram classifies, so the plotted points land outside
   the diagram entirely.  The boundaries are right; what is plotted
   against them is not, until the projection is taken from the paper.
   See :meth:`HanskiHighMg._compute_xy`.
"""

from __future__ import annotations

import pandas as pd

from .base import Diagram, PlotOptions, resolve_column


# --------------------------------------------------------------------------
# Boundaries, as (x, y) endpoint pairs in ([Al2O3], [TiO2]).
# All straight; the four sub-horizontal ones span the full Al range.
# --------------------------------------------------------------------------

#: Meimechite ↔ picrites.
_MEIMECHITE = ((0.0, 0.08949), (0.25, 0.10005))

#: Picrites ↔ Ti-enriched komatiites.
_PICRITE_KOMATIITE = ((0.0, 0.01979), (0.25, 0.02993))

#: Ti-enriched komatiites ↔ the komatiites below them.
_TI_ENRICHED = ((0.0, 0.00985), (0.25, 0.01976))

#: Komatiites ↔ boninite.  Passes through the origin.
_BONINITE = ((0.0, 0.00004), (0.25, 0.00975))

#: The steep Al-depleted / Al-undepleted divider, from where it meets
#: the meimechite line down to where it meets the boninite line.
_AL_DIVIDE = ((0.09135, 0.09335), (0.16946, 0.00662))

_BOUNDARIES = (_MEIMECHITE, _PICRITE_KOMATIITE, _TI_ENRICHED,
               _BONINITE, _AL_DIVIDE)

#: Field names at the positions the figure sets them.
_LABELS: tuple = (
    ("Meimechite",                     0.1218, 0.11282),
    ("Picrite",                        0.1947, 0.06476),
    ("Al-depleted\nPicrite",           0.0677, 0.05365),
    ("Ti-enriched, Al-depleted komatiite", 0.0812, 0.01702),
    ("Ti-enriched komatiite",          0.2077, 0.02430),
    ("Al-depleted komatiite",          0.0870, 0.00812),
    ("Al-undepleted\nkomatiite",       0.2090, 0.01340),
    ("Boninite",                       0.2210, 0.00350),
)

_LINE = dict(color="#444", linewidth=0.9, alpha=0.9, zorder=1)


class HanskiHighMg(Diagram):
    key = "hanski"
    title = "Hanski high-Mg plot – [Al$_2$O$_3$] vs [TiO$_2$]"
    citation = ("Hanski, E., Walker, R.J., Huhma, H. & Suominen, I. "
                "(2001).  High-Mg classification projected from olivine, "
                "all Fe as ferrous.  Boundaries measured from the "
                "published figure.  WARNING: the olivine projection used "
                "for the axes is unverified and currently returns "
                "negative values for komatiites — treat plotted "
                "positions as provisional until it is taken from the "
                "paper.")
    x_label = "[Al$_2$O$_3$]"
    y_label = "[TiO$_2$]"
    x_range = (0.0, 0.25)
    y_range = (0.0, 0.13)
    field_label_fontsize = 7.0

    def _compute_xy(self, df):
        """Olivine-projected [Al2O3] and [TiO2].

        .. warning::
           This projection is **not** verified against Hanski et al.
           The denominator ``2/3 − MgO − FeO`` (in moles) is negative
           for any rock with more than roughly 25 wt % MgO, which puts
           every komatiite and meimechite off the diagram with a sign
           flip rather than merely in the wrong field.  It is left in
           place so the view still renders, but the numbers it produces
           should not be read as compositions.
        """
        al = _to_mol(df, ["Al2O3"], 101.96)
        ti = _to_mol(df, ["TiO2"], 79.90)
        mg = _to_mol(df, ["MgO"], 40.30)
        fe = _to_mol(df, ["FeO"], 71.85)
        if fe is None:
            fe2o3 = _to_mol(df, ["Fe2O3", "Fe2O3T", "Fe2O3t"], 159.69)
            if fe2o3 is not None:
                fe = 2 * fe2o3
        if any(v is None for v in (al, ti, mg, fe)):
            return None, None
        denom = (2.0 / 3.0) - mg - fe
        return al / denom, ti / denom

    def _draw_background(self, ax, options: PlotOptions) -> None:
        for (x0, y0), (x1, y1) in _BOUNDARIES:
            ax.plot([x0, x1], [y0, y1], **_LINE)
        for name, x, y in _LABELS:
            ax.text(x, y, name, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#333",
                    alpha=0.95, zorder=2, linespacing=1.2)


def _to_mol(df, candidates, mw):
    col = resolve_column(df, candidates)
    if col is None:
        return None
    return pd.to_numeric(df[col], errors="coerce") / mw
