"""Normative An – Ab – Or classification of granitoids (Barker 1979).

Four fields on the normative feldspar triangle, after O'Connor (1965):

    Tonalite      Or below 20, anorthite-rich
    Trondhjemite  Or below 20, albite-rich (the low-An corner)
    Granodiorite  Or between 20 and 35
    Granite       Or above 35

The two principal boundaries are lines of constant Or — 20 between
tonalite/trondhjemite and granodiorite, 35 between granodiorite and
granite.  The figure confirms both twice over: their tick labels on the
An–Or edge read An = 80 and An = 65, which is where Or = 20 and Or = 35
meet that edge, and the third labelled value, An = 70, marks the Or = 30
where the trondhjemite/granite boundary reaches the base.

Provenance
----------
Measured from the published figure.  The triangle's three apexes were
located from its own frame, the drawing skeletonised, the three sides
masked off and the remaining network walked as a graph to recover the
boundary segments and the two junctions where they meet near the
albite corner.

The boundaries are drawn as the finite segments the figure draws, not
closed into polygons.  Closing them would mean inventing where each
field ends against the upper edges, which the source deliberately
leaves open.
"""

from __future__ import annotations

import pandas as pd

from .base import (
    Diagram,
    PlotOptions,
    draw_note,
    draw_ternary_frame,
    get_groups,
    normative,
    normative_note,
    ternary_to_xy,
)

#: Or content dividing tonalite/trondhjemite from granodiorite.
GRANODIORITE_OR = 20.0

#: Or content dividing granodiorite from granite.
GRANITE_OR = 35.0

# --------------------------------------------------------------------------
# Boundaries as polylines in (An, Ab, Or).  Two junctions sit close
# together near the albite corner; both are kept as measured.
# --------------------------------------------------------------------------

# The two principal lines measure Or = 20.20 ± 0.07 and 34.84 ± 0.07
# across their length — within a pixel of the definitional 20 and 35
# that the An–Or edge labels mark, so the round values are used.

#: Where the trondhjemite/tonalite boundary meets the Or = 20 line.
_J1 = (20.0, 60.0, GRANODIORITE_OR)

#: Where the trondhjemite/granite boundary leaves the network.
_J2 = (17.6, 58.1, 24.3)

_BOUNDARIES: tuple = (
    # Tonalite | granodiorite — constant Or, stopping where the figure does.
    ((49.4, 30.6, GRANODIORITE_OR), _J1),
    # Trondhjemite | tonalite, out to the Ab–An edge at Ab = 70.
    (_J1, (30.0, 70.0, 0.0)),
    # The short link between the two junctions.
    (_J1, _J2),
    # Trondhjemite | granite, down to the base at Or = 30.
    (_J2, (0.0, 70.0, 30.0)),
    # Granodiorite | granite — a short step, then constant Or.
    (_J2, (15.5, 49.5, GRANITE_OR), (39.9, 25.1, GRANITE_OR)),
)

#: Field names at the positions the figure sets them.
_LABELS: tuple = (
    ("Tonalite",     36.5, 51.6, 12.0),
    ("Granodiorite", 33.9, 37.9, 28.2),
    ("Granite",      14.9, 29.3, 55.7),
    ("Trondhjemite",  8.7, 76.7, 14.6),
)

_LINE = dict(color="#444", linewidth=0.9, alpha=0.9, zorder=2)


class BarkerAnAbOr(Diagram):
    key = "barker_anaborn"
    title = "Normative An – Ab – Or granitoid classification"
    citation = ("Barker, F. (1979) Trondhjemite: definition, environment "
                "and hypotheses of origin.  In: Trondhjemites, Dacites "
                "and Related Rocks, Elsevier, 1-12; after O'Connor "
                "(1965).  Granodiorite spans Or 20-35; granite lies "
                "above Or 35; below Or 20 the anorthite-rich half is "
                "tonalite and the albite-rich corner trondhjemite.  "
                "Boundaries measured from the published figure.")

    _MINERALS = ("An", "Ab", "Or")

    def _compute_xy(self, df):
        """Each sample on the triangle (An at the top), from its norm;
        NaN where it has none.  The sample tally and Identify-sample read
        the same mapping as the plot."""
        norm = normative(df, self._MINERALS)
        if norm is None:
            return None, None
        return ternary_to_xy(norm["An"], norm["Ab"], norm["Or"])

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("An", "Ab", "Or"), options.x_axis)

        for polyline in _BOUNDARIES:
            a, b, c = zip(*polyline)
            x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
            ax.plot(x, y, **_LINE)

        for name, a, b, c in _LABELS:
            x, y = ternary_to_xy(pd.Series([a]), pd.Series([b]),
                                 pd.Series([c]))
            ax.text(float(x.iloc[0]), float(y.iloc[0]), name,
                    ha="center", va="center", fontsize=8, color="#333",
                    alpha=0.95, zorder=3)

        if df is not None and not df.empty:
            for label, sub, gs in get_groups(df, plot_style):
                x, y = self._compute_xy(sub)
                if x is None:
                    continue
                mask = x.notna() & y.notna()
                if not mask.any():
                    continue
                ax.scatter(x[mask], y[mask], s=plot_style.point_size ** 2,
                           alpha=plot_style.alpha,
                           c=gs.color if gs else "#1f77b4",
                           marker=gs.marker if gs else "o",
                           label=label, edgecolors="black", linewidths=0.4,
                           zorder=4)
        note = normative_note(df, self._MINERALS)
        if note:
            draw_note(ax, note)
        self._apply_legend(ax, options)
        figure.tight_layout()

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    @staticmethod
    def classify(an: float, ab: float, orx: float) -> str:
        """Name one analysis from its normative An, Ab and Or.

        The three are renormalised to 100 first, so a CIPW norm that
        does not sum exactly still classifies.
        """
        if any(pd.isna(v) for v in (an, ab, orx)):
            return ""
        total = an + ab + orx
        if total <= 0:
            return ""
        an, ab, orx = (100.0 * v / total for v in (an, ab, orx))
        if orx > GRANITE_OR:
            return "Granite"
        if orx > GRANODIORITE_OR:
            return "Granodiorite"
        # Below Or 20 the split is the trondhjemite/tonalite line, which
        # runs from (An 30, Ab 70, Or 0) to the junction at Or 20.
        (an1, _ab1, or1), (an0, _ab0, or0) = _J1, (30.0, 70.0, 0.0)
        limit = an0 + (orx - or0) * (an1 - an0) / (or1 - or0)
        return "Tonalite" if an > limit else "Trondhjemite"
