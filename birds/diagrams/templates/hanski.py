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

The axes are *not* raw oxides — the brackets mark them as projected
from olivine, which is what lets the diagram classify rocks that have
accumulated or lost olivine.  See :func:`mole_proportions` and
:meth:`HanskiHighMg._compute_xy`.

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
0.0897.  The paper states that construction explicitly — komatiites
and boninites are separated by "a line projecting to the origin and
therefore having a constant Al2O3/TiO2 ratio", and the lines above it
"were drawn parallel to the komatiite–boninite boundary" (p. 865).
The measurements agree: the lowest line's fitted intercept is 0.00004,
and the four slopes scatter by under 0.0004.  The individually fitted
values are kept here because they are what was measured.
"""

from __future__ import annotations

import pandas as pd

from ...cipw import MW_OXIDE
from ...preprocess import get_feot
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


# --------------------------------------------------------------------------
# The olivine projection
# --------------------------------------------------------------------------

#: Mole proportion of MgO + FeO in olivine.  Normalised to unity,
#: (Mg,Fe)2SiO4 is two parts (Mg,Fe)O to one part SiO2, so the mafic
#: pair accounts for 2/3 of it.  This is the point projected from, and
#: the number the paper's denominator subtracts from.
OLIVINE_MAFIC_FRACTION = 2.0 / 3.0

#: Oxides entering the mole-proportion sum.  Iron appears once, as FeO:
#: the paper takes all of it as ferrous.
PROJECTION_OXIDES: tuple = (
    "SiO2", "TiO2", "Al2O3", "FeO", "MnO", "MgO", "CaO", "Na2O", "K2O",
    "P2O5", "Cr2O3", "NiO",
)

#: Oxides whose absence would throw the sum off by more than a per cent
#: or two.  Every whole-rock major-element analysis reports them; the
#: remaining oxides above are used when present and skipped when not.
#: Iron is required too, but is resolved separately.
_REQUIRED_OXIDES: tuple = ("SiO2", "TiO2", "Al2O3", "MgO", "CaO")

#: Iron columns under the exact spellings :func:`get_feot` expects,
#: each with the lab conventions that mean the same thing.
_IRON_SOURCES: dict = {
    "FeO":    ("FeO",),
    "Fe2O3":  ("Fe2O3",),
    "FeOt":   ("FeOt", "FeO_T", "FeO*", "FeO(T)", "FeOtot", "FeO_tot"),
    "Fe2O3t": ("Fe2O3t", "Fe2O3_T", "Fe2O3*", "Fe2O3(T)"),
}


def _iron_as_feo(df: pd.DataFrame):
    """Total iron as FeO in wt %, or ``None`` if no iron is reported.

    Delegates to :func:`birds.preprocess.get_feot`, which combines
    every available iron source row by row, after renaming the columns
    to the exact spellings it matches on.
    """
    canonical = {}
    for name, aliases in _IRON_SOURCES.items():
        col = resolve_column(df, aliases)
        if col is not None:
            canonical[name] = pd.to_numeric(df[col], errors="coerce")
    if not canonical:
        return None
    return get_feot(pd.DataFrame(canonical, index=df.index))


def mole_proportions(df: pd.DataFrame):
    """Major oxides as mole proportions normalised to unity.

    All iron is taken as ferrous, as the paper specifies.  Volatiles
    are not oxides of the projection and are excluded, so the result is
    the anhydrous composition whether or not LOI was reported.

    Returns ``None`` when a required oxide or all iron is missing —
    guessing a zero for an unreported oxide would shift the whole
    normalisation and move every point on the diagram.
    """
    canonical = {}
    for oxide in PROJECTION_OXIDES:
        if oxide == "FeO":
            continue
        col = resolve_column(df, [oxide])
        if col is not None:
            canonical[oxide] = pd.to_numeric(df[col], errors="coerce")
    if any(oxide not in canonical for oxide in _REQUIRED_OXIDES):
        return None
    feot = _iron_as_feo(df)
    if feot is None:
        return None
    canonical["FeO"] = feot

    moles = pd.DataFrame(
        {oxide: series / MW_OXIDE[oxide]
         for oxide, series in canonical.items()},
        index=df.index,
    )
    total = moles.sum(axis=1, skipna=True)
    return moles.div(total.where(total > 0), axis=0)


class HanskiHighMg(Diagram):
    key = "hanski"
    title = "Hanski high-Mg plot – [Al$_2$O$_3$] vs [TiO$_2$]"
    citation = ("Hanski, E., Huhma, H., Rastas, P. & Kamenetsky, V.S. "
                "(2001) The Palaeoproterozoic komatiite–picrite "
                "association of Finnish Lapland.  Journal of Petrology "
                "42(5), 855-876; projection after Hanski (1992).  "
                "[Al₂O₃] and [TiO₂] are mole proportions normalised to "
                "unity and projected from olivine: [X] = X / (2/3 − MgO "
                "− FeO), all iron as ferrous.  Compositions on one "
                "olivine control line share a single point, so the "
                "diagram classifies a rock series rather than a rock — "
                "komatiite and komatiitic basalt are not separated here "
                "and have to be told apart on MgO.  Boundaries measured "
                "from the published figure.")
    x_label = "[Al$_2$O$_3$]"
    y_label = "[TiO$_2$]"
    x_range = (0.0, 0.25)
    y_range = (0.0, 0.13)
    field_label_fontsize = 7.0

    def _compute_xy(self, df):
        """Olivine-projected [Al2O3] and [TiO2], after Hanski (1992).

        The analysis is converted to mole proportions normalised to
        unity, all iron as ferrous, and each of Al2O3 and TiO2 divided
        by ``2/3 − MgO − FeO``.  Dividing by the distance to olivine is
        what makes the result invariant: adding or removing olivine
        scales the numerator and the denominator by the same factor, so
        a whole olivine control line collapses onto one point.
        """
        mol = mole_proportions(df)
        if mol is None:
            return None, None
        denom = OLIVINE_MAFIC_FRACTION - mol["MgO"] - mol["FeO"]
        # No rock is more olivine-rich than olivine itself, so the
        # denominator only reaches zero at the projection point, where
        # the composition has no position on the diagram.  NaN keeps
        # such a sample out of the plot and out of the plotted count,
        # rather than flipping its sign onto the far side.
        denom = denom.where(denom > 1e-9)
        return mol["Al2O3"] / denom, mol["TiO2"] / denom

    def _draw_background(self, ax, options: PlotOptions) -> None:
        for (x0, y0), (x1, y1) in _BOUNDARIES:
            ax.plot([x0, x1], [y0, y1], **_LINE)
        for name, x, y in _LABELS:
            ax.text(x, y, name, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#333",
                    alpha=0.95, zorder=2, linespacing=1.2)
