"""TAS (Total Alkalis vs Silica) diagrams – volcanic and plutonic."""

from __future__ import annotations

import numpy as np
import pandas as pd
from matplotlib.path import Path

from .base import Diagram, resolve_column
from .ib1971 import _IRVINE_BARAGAR_1971 as _IB1971_BOUNDARY


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
    # Open at the top, where the frame closes it.  Every entry here is
    # drawn as a *closed* outline, so the vertex list walks out to
    # (63, 14.5) and straight back before tracing the left side: that
    # retraced segment is invisible, whereas ordering the four points
    # around the field would draw a line right across its top.  The
    # closing edge (50, 15.083) → (57.6, 11.7) is collinear with the
    # real boundary to within 0.03 wt.%, so it hides under it.
    "Phonolite":                [(57.6,11.7),(63,14.5),
                                 (57.6,11.7),(52.5,14),(50,15.083)],

}

# Foidite occupies the whole upper-left region.  It needs no outline of
# its own — every edge it has is already drawn by Tephrite/Basanite,
# Phonotephrite, Tephriphonolite, Phonolite and Picrobasalt, and the
# rest is the frame — but it still needs its name.
_FOIDITE_LABEL = (39.0, 12.5)


# ---------------------------------------------------------------------------
# Naming a composition
# ---------------------------------------------------------------------------
#
# The outlines above are what gets drawn, and they are also what decides
# the name: the classification regions are built *from* them, so a name
# can never drift away from the picture.  Ten of the fourteen close on
# their own and are used as they stand.  The other four stop at the
# frame rather than closing, and Foidite has no outline at all, so those
# five are given an explicit closed form here.
#
# The domain runs a little past the published frame (16 wt.% alkalis) so
# that a rare ultra-alkaline analysis still gets named rather than
# silently dropped.

CLASSIFY_SIO2_RANGE = (30.0, 100.0)
CLASSIFY_ALKALI_MAX = 20.0


def _x_on(p, q, y: float) -> float:
    """x where the line through *p* and *q* reaches height *y*."""
    (x0, y0), (x1, y1) = p, q
    return x0 + (y - y0) * (x1 - x0) / (y1 - y0)


def _y_on(p, q, x: float) -> float:
    (x0, y0), (x1, y1) = p, q
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


# Where the Foidite / Phonolite line leaves the top of the domain, and
# where the Phonolite / Trachyte line crosses the SiO2 = 69 edge of the
# Trachyte field.  Both are read off the stored vertices, not retyped.
_X_FOIDITE_TOP = _x_on((52.5, 14), (50, 15.083), CLASSIFY_ALKALI_MAX)
_Y_TRACHYTE_69 = _y_on((57.6, 11.7), (61, 13.5), 69.0)

_VOLCANIC_CLOSURES = {
    # No outline of its own; bounded by its neighbours and the frame.
    "Foidite": [(CLASSIFY_SIO2_RANGE[0], 0), (41, 0), (41, 7), (45, 9.4),
                (48.4, 11.5), (52.5, 14), (_X_FOIDITE_TOP,
                                           CLASSIFY_ALKALI_MAX),
                (CLASSIFY_SIO2_RANGE[0], CLASSIFY_ALKALI_MAX)],
    # Drawn as the single dacite boundary; open right and up.
    "Rhyolite": [(77, 0), (CLASSIFY_SIO2_RANGE[1], 0),
                 (CLASSIFY_SIO2_RANGE[1], CLASSIFY_ALKALI_MAX),
                 (69, CLASSIFY_ALKALI_MAX), (69, 8)],
    # Drawn as the SiO2 = 69 segment; closes against the phonolite line.
    "Trachyte /\nTrachydacite": [(63, 7), (69, 8), (69, _Y_TRACHYTE_69),
                                 (57.6, 11.7)],
    # Drawn with a retraced edge; the closed form drops it.
    "Phonolite": [(52.5, 14), (57.6, 11.7), (69, _Y_TRACHYTE_69),
                  (69, CLASSIFY_ALKALI_MAX),
                  (_X_FOIDITE_TOP, CLASSIFY_ALKALI_MAX)],
}

#: Fields the TAS names only in pairs, because what separates them is
#: normative and not an axis of this plane.  Same treatment as komatiite
#: vs meimechite in :mod:`birds.diagrams.templates.highmg_tas`: without
#: the extra number, say both names rather than pick one.
# Keyed on the *cleaned* name — several outlines carry a newline for
# layout, and matching on the raw key silently misses them.
_VOLCANIC_SPLITS = {
    "Tephrite / Basanite": ("normative_ol", 10.0, "Tephrite", "Basanite"),
    "Trachyte / Trachydacite": ("normative_q", 20.0,
                                "Trachyte", "Trachydacite"),
}


def _volcanic_regions():
    """name → closed vertex list, built once from the drawn outlines."""
    out = dict(_VOLCANIC_CLOSURES)
    for name, verts in _VOLCANIC_FIELDS.items():
        out.setdefault(name, list(verts))
    return out


# Built once: fifteen small paths, and ``contains_points`` is vectorised.
_VOLCANIC_PATHS = tuple(
    (name.replace("\n", " "), Path(verts))
    for name, verts in _volcanic_regions().items()
)


def _classify_points(points, paths, splits, *, normative_ol, normative_q):
    """Name a sequence of (SiO2, alkalis) pairs against *paths*.

    A composition sitting exactly on a boundary is given the name of the
    first field that claims it, in the order the outlines are declared —
    the IUGS scheme does not assign boundaries either way, so any
    consistent rule will do, and a stated one beats an accidental one.

    *splits* names the fields that the plane cannot separate on its own;
    the plutonic scheme has none, because Middlemost draws the quartz
    monzonite field rather than splitting a trachyte field by normative
    quartz.
    """
    pts = np.asarray(points, dtype=float).reshape(-1, 2)
    names = [""] * len(pts)
    finite = np.isfinite(pts).all(axis=1)
    for clean, path in paths:
        inside = np.zeros(len(pts), dtype=bool)
        if finite.any():
            inside[finite] = path.contains_points(pts[finite])
        split = splits.get(clean)
        for i in np.flatnonzero(inside):
            if names[i]:
                continue
            if split is None:
                names[i] = clean
                continue
            which, limit, below, above = split
            value = (normative_ol if which == "normative_ol"
                     else normative_q)[i]
            if value is None or not np.isfinite(value):
                names[i] = clean
            else:
                names[i] = below if value < limit else above
    return names


# Irvine & Baragar (1971) alkaline / sub-alkaline boundary on the TAS
# plane.  Imported rather than copied: this file used to carry its own
# list, which had drifted to (65.0, 8.8) and (77.4, 10.0) against the
# published (65.0, 9.6) and (66.4, 10.0) while a comment claimed the two
# were the same.  The error reached 1 wt.% alkalis near SiO2 66, enough
# to call an alkaline trachyte sub-alkaline.  See the import above.


def _draw_ib_boundary(ax, x_max: float = 78.0,
                      side_label_x: float = 70.0) -> None:
    """Draw the Irvine & Baragar (1971) alkaline / sub-alkaline curve on
    top of an existing TAS axis, plus the two side labels.

    The published curve stops at SiO2 = 66.4.  It is carried flat to the
    right edge so the high-silica half of the plot is not left without a
    boundary, but that tail is an extrapolation and is drawn faded to
    say so — Irvine and Baragar did not put a line there.
    """
    xs = [p[0] for p in _IB1971_BOUNDARY]
    ys = [p[1] for p in _IB1971_BOUNDARY]
    ax.plot(xs, ys, color="#1f3a93", linewidth=1.4, linestyle="--",
            alpha=0.85, zorder=2,
            label="Irvine & Baragar (1971)")
    if xs[-1] < x_max:
        ax.plot([xs[-1], x_max], [ys[-1], ys[-1]], color="#1f3a93",
                linewidth=1.4, linestyle="--", alpha=0.35, zorder=2)
    # Tiny italic labels on either side of the flat stretch of the
    # curve, at *side_label_x* -- 70 on the volcanic diagram, further out
    # on the plutonic one, where 70 lands on Quartz Monzonite.
    ax.text(side_label_x, 11.0, "Alkaline", fontsize=8.5, color="#1f3a93",
            style="italic", alpha=0.9, ha="center", zorder=2)
    ax.text(side_label_x, 8.6, "Sub-alkaline", fontsize=8.5,
            color="#1f3a93", style="italic", alpha=0.9, ha="center",
            zorder=2)


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
        "Phonolite":       (56.5, 14),       # centred in the new pentagon
        "Picrobasalt":     (43, 0.55),       # under the I&B line
        "Basalt":          (48.5, 2.5),
        "Basaltic\nandesite": (54.5, 3),
        "Andesite":        (60, 3.5),
        "Dacite":          (67, 3.5),
        "Rhyolite":        (75, 8),
        "Trachybasalt":    (48.5, 5.5),          # bottom-centre (widest part)
        "Basaltic\ntrachyandesite": (52.6, 7.25),  # clear of the I&B line
        "Trachyandesite":  (57.5, 8.5),
        "Trachyte /\nTrachydacite": (65.6, 11.35),  # above the I&B line
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
        ax.text(*_FOIDITE_LABEL, "Foidite", ha="center", va="center",
                fontsize=self.field_label_fontsize, color="#333",
                alpha=0.95, zorder=2)
        _draw_ib_boundary(ax, x_max=self.x_range[1])

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    @staticmethod
    def classify(sio2: float, alkalis: float, *,
                 normative_ol: float | None = None,
                 normative_q: float | None = None) -> str:
        """Name one composition from its SiO2 and Na2O + K2O.

        Both are wt.% and must already be recalculated to 100 %
        anhydrous, as the IUGS scheme requires — the same condition the
        diagram itself carries.

        ``normative_ol`` and ``normative_q`` resolve the two pairs the
        TAS plane cannot separate on its own.  Without them the pair is
        returned whole, which is more useful than guessing a half of it.
        Returns ``""`` for a composition off the diagram.
        """
        names = _classify_points([(sio2, alkalis)],
                                 _VOLCANIC_PATHS, _VOLCANIC_SPLITS,
                                 normative_ol=[normative_ol],
                                 normative_q=[normative_q])
        return names[0]

    @staticmethod
    def classify_frame(df: pd.DataFrame) -> pd.Series:
        """Name every row of *df*, as a Series aligned to its index.

        Reads SiO2, Na2O and K2O, and uses the normative ``Ol`` and
        ``Q`` columns of a CIPW norm when they are present.  A row
        missing an input, or falling off the diagram, gets ``""``.
        """
        si = resolve_column(df, ["SiO2"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if not (si and na and k):
            return pd.Series([""] * len(df), index=df.index, dtype="object")
        x = pd.to_numeric(df[si], errors="coerce")
        y = (pd.to_numeric(df[na], errors="coerce")
             + pd.to_numeric(df[k], errors="coerce"))

        def optional(*aliases):
            col = resolve_column(df, list(aliases))
            if col is None:
                return [None] * len(df)
            return pd.to_numeric(df[col], errors="coerce").tolist()

        names = _classify_points(
            list(zip(x.tolist(), y.tolist())),
            _VOLCANIC_PATHS, _VOLCANIC_SPLITS,
            normative_ol=optional("Ol", "norm_Ol", "Olivine"),
            normative_q=optional("Q", "norm_Q", "Quartz"),
        )
        return pd.Series(names, index=df.index, dtype="object")


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


# ---------------------------------------------------------------------------
# Naming a plutonic composition
# ---------------------------------------------------------------------------
#
# Same arrangement as the volcanic scheme above: the regions are built
# *from* the outlines that get drawn, so a name cannot drift away from
# the picture.
#
# Fourteen of the sixteen close on their own.  Two are stored as the
# single boundary segment each contributes to the drawing -- the rest
# of their edges belong to their neighbours and would be drawn twice --
# so those two are given a closed form here.  That is the whole of what
# used to stand in the way: with them closed, the sixteen tile the
# diagram exactly, with no overlap and no interior gap.
#
# Middlemost's own text is what says they may be closed this way.  He
# sets the plutonic scheme out as the volcanic one renamed -- gabbro
# for basalt, diorite for andesite, granodiorite for dacite, syenite
# for trachyte, granite for rhyolite, foid gabbro for tephrite, and so
# on -- so the two fields here are the volcanic phonotephrite and
# tephriphonolite under plutonic names, and take their vertices.
# Checked against Figure 4 rather than taken on trust: both closures
# land on its drawn outlines.
#
# Not every field of Figure 4 is drawn here.  Quartzolite, beyond the
# granite field, and the tawite/urtite/italite group above foidolite
# are what Middlemost calls "outside the main sequence of plutonic
# rocks"; a composition there is left unnamed rather than forced into
# a neighbour.

_PLUTONIC_CLOSURES = {
    "Foid\nMonzodiorite": [(45, 9.4), (49.4, 7.3), (53, 9.3), (48.4, 11.5)],
    "Foid\nMonzosyenite": [(48.4, 11.5), (53, 9.3), (57.6, 11.7),
                           (52.5, 14)],
}


def _plutonic_regions():
    """name → closed vertex list, built once from the drawn outlines."""
    out = dict(_PLUTONIC_CLOSURES)
    for name, verts in _PLUTONIC_FIELDS.items():
        out.setdefault(name, list(verts))
    return out


#: Outline key → the name Middlemost writes in his text.  The keys are
#: what the figure needs to fit the label inside the field, which is
#: not always the rock's name: "Monzo\n-gabbro" has to come back as
#: monzogabbro and "Gabbro\ndiorite" as gabbroic diorite.  Stripping
#: the newline is not enough, so the mapping is explicit.
_PLUTONIC_NAMES = {
    "Peridot\ngabbro": "Peridotgabbro",
    "Gabbro": "Gabbro",
    "Gabbro\ndiorite": "Gabbroic diorite",
    "Diorite": "Diorite",
    "Granodiorite": "Granodiorite",
    "Granite": "Granite",
    "Quartz\nMonzonite": "Quartz monzonite",
    "Syenite": "Syenite",
    "Monzonite": "Monzonite",
    "Monzo\ndiorite": "Monzodiorite",
    "Monzo\n-gabbro": "Monzogabbro",
    "Foid\ngabbro": "Foid gabbro",
    "Foidolite": "Foidolite",
    "Foid\nMonzodiorite": "Foid monzodiorite",
    "Foid\nMonzosyenite": "Foid monzosyenite",
    "Foid\nSyenite": "Foid syenite",
}

_PLUTONIC_PATHS = tuple(
    (_PLUTONIC_NAMES[name], Path(verts))
    for name, verts in _plutonic_regions().items()
)


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
        "Foid\nSyenite":   (56.5, 15),
        "Peridot\ngabbro":  (43.8, 0.7),     # in its field, under the I&B line
        "Gabbro":         (48.5, 2.5),
        "Diorite":        (60, 3.0),
        "Granodiorite":   (70, 3.5),
        "Granite":        (80, 5.0),
        "Monzo\n-gabbro":   (47.6, 6.3),
        "Monzo\ndiorite":   (52, 7.2),
        "Monzonite":      (57, 9.3),
        "Syenite":        (65, 12),
        "Quartz\nMonzonite": (66.6, 8.25),
        "Foid\ngabbro":    (42.8, 7.6),
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
        _draw_ib_boundary(ax, x_max=self.x_range[1], side_label_x=80.0)

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    @staticmethod
    def classify(sio2: float, alkalis: float) -> str:
        """Name one plutonic composition from SiO2 and Na2O + K2O.

        Both wt.%, recalculated to 100 % anhydrous, as for the volcanic
        diagram.  Returns ``""`` for a composition off the diagram —
        including the two corners Middlemost names but does not draw
        here, quartzolite beyond SiO2 ~87 and the tawite/urtite/italite
        group above the foidolite field, which he calls "outside the
        main sequence of plutonic rocks".

        Unlike the volcanic scheme this takes no normative arguments.
        It needs none: Middlemost gives foid gabbro one name where the
        volcanic plane splits tephrite from basanite, and he draws the
        quartz monzonite field instead of splitting a trachyte field at
        20 % normative quartz.
        """
        return _classify_points([(sio2, alkalis)],
                                _PLUTONIC_PATHS, {},
                                normative_ol=[None],
                                normative_q=[None])[0]

    @staticmethod
    def classify_frame(df: pd.DataFrame) -> pd.Series:
        """Name every row of *df*, as a Series aligned to its index."""
        si = resolve_column(df, ["SiO2"])
        na = resolve_column(df, ["Na2O"])
        k = resolve_column(df, ["K2O"])
        if not (si and na and k):
            return pd.Series([""] * len(df), index=df.index, dtype="object")
        x = pd.to_numeric(df[si], errors="coerce")
        y = (pd.to_numeric(df[na], errors="coerce")
             + pd.to_numeric(df[k], errors="coerce"))
        names = _classify_points(list(zip(x.tolist(), y.tolist())),
                                 _PLUTONIC_PATHS, {},
                                 normative_ol=[None] * len(df),
                                 normative_q=[None] * len(df))
        return pd.Series(names, index=df.index, dtype="object")
