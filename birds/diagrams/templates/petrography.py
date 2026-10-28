"""IUGS petrographic classification ternaries.

Six modal-mineralogy classifiers used in field petrography and
thin-section work:

* ``streckeisen_qapf_plutonic``  – Streckeisen (1976) QAPF double
  triangle for coarse-grained rocks.
* ``streckeisen_qapf_volcanic``  – Streckeisen (1978) QAPF for
  fine-grained rocks, which has its own fields, not only its own names.
* ``gabbro_pl_px_ol``            – plagioclase – pyroxene – olivine, for
  the gabbroic rocks.
* ``ultramafic_ol_opx_cpx``      – olivine – orthopyroxene –
  clinopyroxene, for peridotites and pyroxenites (Streckeisen 1973).
* ``tuff_schmid_1981``           – vitric – crystal – lithic, the
  three-field tuff classification the IUGS recommends (Schmid 1981).
* ``pyroclastic_fisher_1966``    – blocks and bombs – lapilli – ash, the
  fragment-size classification of Fisher (1966), Figure 1.

Inputs are modal proportions read from the *Petrography* sheet of the
data template (``Q_mode``, ``A_mode``, ``P_mode``, ``F_mode``,
``Ol_mode``, ``Opx_mode``, ``Cpx_mode``, ``Px_mode``, ``Crystal_pct``,
``Vitric_pct``, ``Lithic_pct``, ``Blocks_bombs_pct``, ``Lapilli_pct``,
``Ash_pct``).

Provenance
----------
Every boundary here is a definition -- a percentage the IUGS fixed --
not a curve to measure.  They were checked on 2026-10-12 against the
BGS Rock Classification Scheme, Volume 1 (Gillespie & Styles 1999, BGS
Research Report RR 99-06), which reproduces the IUGS diagrams of Le
Maitre et al. (1989, 2002): Figures 11-12 for the plutonic QAPF, 19 for
the volcanic one, 13 for the gabbroic rocks, 16 for the ultramafic ones
and 7 for Schmid's tuffs.  ``docs/DIAGRAM_PROVENANCE.md`` lists what the
check found.

References
----------
- Streckeisen, A. (1973). Plutonic rocks: classification and
  nomenclature recommended by the IUGS Subcommission. *Geotimes* 18,
  26-30.
- Streckeisen, A. (1976). To each plutonic rock its proper name.
  *Earth-Sci. Rev.* 12, 1-33.
- Streckeisen, A. (1978). IUGS Subcommission on the Systematics of
  Igneous Rocks: classification and nomenclature of volcanic rocks,
  lamprophyres, carbonatites and melilitic rocks. *N. Jb. Miner. Abh.*
  134, 1-14.
- Schmid, R. (1981). Descriptive nomenclature and classification of
  pyroclastic deposits and fragments. *Geology* 9, 41-43.
- Le Maitre, R.W. (ed., 2002). *Igneous Rocks – A Classification and
  Glossary of Terms*, 2nd ed., Cambridge University Press.
- Gillespie, M.R. & Styles, M.T. (1999). BGS Rock Classification
  Scheme, Volume 1: Classification of igneous rocks. British Geological
  Survey Research Report RR 99-06.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd
from matplotlib.patches import Polygon

from .base import (
    Diagram,
    PlotOptions,
    TernaryDiagram,
    draw_group,
    draw_note,
    draw_ternary_frame,
    get_groups,
    resolve_column,
    ternary_to_xy,
)


# ---------------------------------------------------------------------------
# QAPF
# ---------------------------------------------------------------------------
#
# A sample sits in the upper triangle when it carries quartz and in the
# lower one when it carries a feldspathoid -- never both.  Its place is
# given by two numbers:
#
#   s = 100 Q/(Q+A+P)           upper triangle, s >= 0
#   s = -100 F/(A+P+F)          lower triangle, s < 0
#   r = 100 P/(A+P)
#
# A is at (0, 0), P at (1, 0), Q at (0.5, +h), F at (0.5, -h).  Every
# IUGS field is a box in (s, r) -- a range of Q or F against a range of
# P/(A+P) -- so the fields below are listed as boxes, and the lines, the
# field numbers and the name a sample gets all come from the same table.
#
# The plotted position used to be computed as 0.5 A + P + 0.5 Q, which
# puts the A corner at x = 0.5: every sample shifted right by half its
# alkali feldspar, a pure alkali-feldspar syenite on monzonite and a
# granite (Q30 A40 P30) on granodiorite.

_HALF_HEIGHT = np.sqrt(3) / 2.0

#: Streckeisen (1976), BGS RR 99-06 Figures 11-12:
#: ``(field number, name, s from, s to, r from, r to)``.
QAPF_PLUTONIC_FIELDS: Tuple[Tuple[str, str, float, float, float, float], ...] = (
    ("1a", "quartzolite", 90, 100, 0, 100),
    ("1b", "quartz-rich granitoid", 60, 90, 0, 100),
    ("2", "alkali feldspar granite", 20, 60, 0, 10),
    ("3", "granite", 20, 60, 10, 65),
    ("4", "granodiorite", 20, 60, 65, 90),
    ("5", "tonalite", 20, 60, 90, 100),
    ("6*", "quartz alkali feldspar syenite", 5, 20, 0, 10),
    ("7*", "quartz syenite", 5, 20, 10, 35),
    ("8*", "quartz monzonite", 5, 20, 35, 65),
    ("9*", "quartz monzodiorite / quartz monzogabbro", 5, 20, 65, 90),
    ("10*", "quartz diorite / quartz gabbro / quartz anorthosite",
     5, 20, 90, 100),
    ("6", "alkali feldspar syenite", 0, 5, 0, 10),
    ("7", "syenite", 0, 5, 10, 35),
    ("8", "monzonite", 0, 5, 35, 65),
    ("9", "monzodiorite / monzogabbro", 0, 5, 65, 90),
    ("10", "diorite / gabbro / anorthosite", 0, 5, 90, 100),
    ("6'", "foid-bearing alkali feldspar syenite", -10, 0, 0, 10),
    ("7'", "foid-bearing syenite", -10, 0, 10, 35),
    ("8'", "foid-bearing monzonite", -10, 0, 35, 65),
    ("9'", "foid-bearing monzodiorite / monzogabbro", -10, 0, 65, 90),
    ("10'", "foid-bearing diorite / gabbro / anorthosite", -10, 0, 90, 100),
    ("11", "foid syenite", -60, -10, 0, 10),
    ("12", "foid monzosyenite", -60, -10, 10, 50),
    ("13", "foid monzodiorite / foid monzogabbro", -60, -10, 50, 90),
    ("14", "foid diorite / foid gabbro", -60, -10, 90, 100),
    ("15", "foidolite", -100, -60, 0, 100),
)

#: Streckeisen (1978), BGS RR 99-06 Figure 19.  Not the plutonic fields
#: renamed: above Q 60 there is no volcanic name, dacite takes
#: P/(A+P) 65-100, basalt / andesite runs from Q 20 down to F 10 with no
#: line at 90, and the foidites divide.  Fields 9 and 10 with and
#: without * or ' are all basalt / andesite; colour index and SiO2 tell
#: them apart (Figure 21), the mode cannot.
QAPF_VOLCANIC_FIELDS: Tuple[Tuple[str, str, float, float, float, float], ...] = (
    ("", "", 90, 100, 0, 100),
    ("", "", 60, 90, 0, 100),
    ("2", "alkali feldspar rhyolite", 20, 60, 0, 10),
    ("3", "rhyolite", 20, 60, 10, 65),
    ("4–5", "dacite", 20, 60, 65, 100),
    ("6*", "quartz alkali feldspar trachyte", 5, 20, 0, 10),
    ("7*", "quartz trachyte", 5, 20, 10, 35),
    ("8*", "quartz latite", 5, 20, 35, 65),
    ("6", "alkali feldspar trachyte", 0, 5, 0, 10),
    ("7", "trachyte", 0, 5, 10, 35),
    ("8", "latite", 0, 5, 35, 65),
    ("9–10", "basalt / andesite", -10, 20, 65, 100),
    ("6'", "foid-bearing alkali feldspar trachyte", -10, 0, 0, 10),
    ("7'", "foid-bearing trachyte", -10, 0, 10, 35),
    ("8'", "foid-bearing latite", -10, 0, 35, 65),
    ("11", "phonolite", -60, -10, 0, 10),
    ("12", "tephritic phonolite", -60, -10, 10, 50),
    ("13", "phonolitic basanite (Ol > 10 %) / phonolitic tephrite",
     -60, -10, 50, 90),
    ("14", "basanite (Ol > 10 %) / tephrite", -60, -10, 90, 100),
    ("15a", "phonolitic foidite", -90, -60, 0, 50),
    ("15b", "tephritic foidite / basanitic foidite (Ol > 10 %)",
     -90, -60, 50, 100),
    ("15c", "foidite", -100, -90, 0, 100),
)

#: Sub-field lines the figures draw dashed: ``(r, s from, s to)``.  The
#: plutonic one splits granite into syeno- (3a) and monzogranite (3b);
#: the volcanic ones are drawn the same way inside rhyolite and dacite.
QAPF_PLUTONIC_DASHED = ((35, 20, 60),)
QAPF_VOLCANIC_DASHED = ((35, 20, 60), (90, 20, 60))


def qapf_xy(s, r):
    """(x, y) on the double triangle of a point at (s, r)."""
    s = np.asarray(s, dtype=float)
    r = np.asarray(r, dtype=float)
    t = np.abs(s) / 100.0
    return 0.5 * t + (1.0 - t) * r / 100.0, np.sign(s) * _HALF_HEIGHT * t


def _box_outline(s_lo, s_hi, r_lo, r_hi):
    """A field's outline as (s, r) vertices, through s = 0 where the box
    crosses from one triangle to the other: the edges are straight in
    each triangle and bend on the A-P line."""
    def run(s_from, s_to, r):
        pts = [(s_from, r)]
        if min(s_from, s_to) < 0 < max(s_from, s_to):
            pts.append((0.0, r))
        return pts
    return (run(s_lo, s_hi, r_lo) + [(s_hi, r_lo)]
            + run(s_hi, s_lo, r_hi) + [(s_lo, r_hi)])


def _polygon_centroid(xs, ys):
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    cross = xs * np.roll(ys, -1) - np.roll(xs, -1) * ys
    area = cross.sum() / 2.0
    if abs(area) < 1e-12:
        return float(xs.mean()), float(ys.mean())
    return (float(((xs + np.roll(xs, -1)) * cross).sum() / (6 * area)),
            float(((ys + np.roll(ys, -1)) * cross).sum() / (6 * area)))


def qapf_field(fields, s: float, r: float) -> Tuple[str, str]:
    """``(number, name)`` of the field holding (s, r), or ``("", "")``.

    Each box takes its lower bounds and leaves its upper ones to the
    next, except at 100, so a sample on a line has one name.
    """
    if not (np.isfinite(s) and np.isfinite(r)):
        return "", ""
    for number, name, s_lo, s_hi, r_lo, r_hi in fields:
        in_s = s_lo <= s < s_hi or (s_hi == 100 and s == 100)
        in_r = r_lo <= r < r_hi or (r_hi == 100 and r == 100)
        if in_s and in_r:
            return number, name
    return "", ""


def _draw_qapf_frame(ax, axis_style) -> None:
    """The double triangle, its apexes and the A-P line."""
    q, f = (0.5, _HALF_HEIGHT), (0.5, -_HALF_HEIGHT)
    a, p = (0.0, 0.0), (1.0, 0.0)
    ax.plot([a[0], q[0], p[0], f[0], a[0]], [a[1], q[1], p[1], f[1], a[1]],
            color="#333", linewidth=1.0, zorder=3)
    ax.plot([a[0], p[0]], [a[1], p[1]], color="#333", linewidth=1.0,
            zorder=3)
    style = axis_style.label_kwargs()
    ax.text(q[0], q[1] + 0.04, "Q", ha="center", va="bottom", **style)
    ax.text(f[0], f[1] - 0.04, "F", ha="center", va="top", **style)
    ax.text(a[0] - 0.03, a[1], "A", ha="right", va="center", **style)
    ax.text(p[0] + 0.03, p[1], "P", ha="left", va="center", **style)


def _qapf_key(fields) -> Tuple[str, str]:
    """The field-number key, split into the upper and lower triangle."""
    upper, lower, seen = [], [], set()
    for number, name, _s_lo, s_hi, _rl, _rh in fields:
        if not number or number in seen:
            continue
        seen.add(number)
        (upper if s_hi > 0 else lower).append(f"{number:>4}  {name}")
    return "\n".join(upper), "\n".join(lower)


class _QAPFDiagram(Diagram):
    """Shared rendering for the Streckeisen QAPF double triangle."""

    fields: tuple = ()
    dashed: tuple = ()

    _COLUMNS = (
        ("Q", ("Q_mode", "Q", "Quartz_mode", "Qtz")),
        ("A", ("A_mode", "A", "Alkali_feldspar_mode", "Alk_fsp", "Kfs")),
        ("P", ("P_mode", "P", "Plagioclase_mode", "Pl")),
        ("F", ("F_mode", "F", "Foid_mode", "Foid")),
    )

    def _modes(self, df: pd.DataFrame):
        """Q, A, P and F, with an absent mineral as 0, or ``None`` when
        the sheet has no feldspar columns at all."""
        found = {k: resolve_column(df, names) for k, names in self._COLUMNS}
        if found["A"] is None and found["P"] is None:
            return None
        values = {k: (pd.to_numeric(df[col], errors="coerce")
                      if col else pd.Series(np.nan, index=df.index))
                  for k, col in found.items()}
        frame = pd.DataFrame(values)
        blank = frame.isna().all(axis=1)
        frame = frame.fillna(0.0).clip(lower=0.0)
        frame[blank] = np.nan
        return frame

    def _sr(self, df: pd.DataFrame):
        """(s, r) per sample; NaN for a blank row, a row with nothing to
        place, and a row carrying both quartz and a feldspathoid, which
        the QAPF cannot hold."""
        modes = self._modes(df)
        if modes is None:
            return None, None
        q, a, p, f = (modes[k] for k in "QAPF")
        both = (q > 0) & (f > 0)
        feldspar = a + p
        upper = q + feldspar
        lower = f + feldspar
        s = pd.Series(np.where(f > 0, -100.0 * f / lower.where(lower > 0),
                               100.0 * q / upper.where(upper > 0)),
                      index=df.index)
        # A pure quartz or feldspathoid rock has no P/(A+P); it sits at
        # the apex whatever the ratio, so any value places it.
        r = (100.0 * p / feldspar.where(feldspar > 0)).where(
            feldspar > 0, 50.0)
        bad = both | modes.isna().any(axis=1)
        return s.mask(bad), r.mask(bad | s.isna())

    def _compute_xy(self, df: pd.DataFrame):
        s, r = self._sr(df)
        if s is None:
            return None, None
        x, y = qapf_xy(s, r)
        return (pd.Series(x, index=df.index), pd.Series(y, index=df.index))

    def classify(self, q: float, a: float, p: float, f: float
                 ) -> Tuple[str, str]:
        """``(field number, name)`` for one mode; ``("", "")`` when it
        cannot be placed or has no name on this diagram."""
        frame = pd.DataFrame({"Q": [q], "A": [a], "P": [p], "F": [f]})
        s, r = self._sr(frame)
        return qapf_field(self.fields, float(s.iloc[0]), float(r.iloc[0]))

    def classify_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Field number and name for every row of *df*."""
        s, r = self._sr(df)
        if s is None:
            return pd.DataFrame({"field": "", "name": ""}, index=df.index)
        pairs = [qapf_field(self.fields, a, b) for a, b in zip(s, r)]
        return pd.DataFrame(pairs, columns=["field", "name"], index=df.index)

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        for number, _name, s_lo, s_hi, r_lo, r_hi in self.fields:
            sr = _box_outline(s_lo, s_hi, r_lo, r_hi)
            x, y = qapf_xy([v[0] for v in sr], [v[1] for v in sr])
            ax.add_patch(Polygon(np.column_stack([x, y]), closed=True,
                                 fill=False, edgecolor="#555",
                                 linewidth=0.7, zorder=1))
            if number:
                cx, cy = _polygon_centroid(x, y)
                ax.text(cx, cy, number, ha="center", va="center",
                        fontsize=6.5, fontweight="bold", color="#1c2237",
                        zorder=2)
        for r, s_lo, s_hi in self.dashed:
            x, y = qapf_xy([s_lo, s_hi], [r, r])
            ax.plot(x, y, color="#777", linewidth=0.7, linestyle="--",
                    zorder=1)
        _draw_qapf_frame(ax, options.x_axis)
        upper, lower = _qapf_key(self.fields)
        key_style = dict(ha="left", va="top", fontsize=6, color="#333",
                         family="monospace", linespacing=1.25)
        ax.text(-0.82, _HALF_HEIGHT - 0.10, upper, **key_style)
        ax.text(-0.82, -0.08, lower, **key_style)

        if df is not None and not df.empty:
            for label, sub, gs in get_groups(df, plot_style):
                x, y = self._compute_xy(sub)
                if x is None:
                    continue
                keep = x.notna() & y.notna()
                if not keep.any():
                    continue
                draw_group(ax, x[keep], y[keep], label, gs, plot_style,
                           options)
            modes = self._modes(df)
            if modes is not None:
                both = int(((modes["Q"] > 0) & (modes["F"] > 0)).sum())
                if both:
                    draw_note(ax, (
                        f"{both} sample{'s' if both != 1 else ''} carr"
                        f"{'y' if both != 1 else 'ies'} both quartz and a "
                        "feldspathoid; the QAPF cannot place "
                        f"{'them' if both != 1 else 'it'}."))

        ax.set_xlim(-0.85, 1.15)
        ax.set_ylim(-_HALF_HEIGHT - 0.10, _HALF_HEIGHT + 0.08)
        ax.set_aspect("equal")
        ax.axis("off")
        self._apply_legend(ax, options)
        figure.tight_layout()


class StreckeisenQAPFPlutonic(_QAPFDiagram):
    key = "streckeisen_qapf_plutonic"
    title = "Streckeisen QAPF — plutonic rocks"
    citation = ("Streckeisen (1976), as in BGS RR 99-06 Figures 11-12 "
                "and Le Maitre (2002). Modal Q (quartz), A (alkali "
                "feldspar), P (plagioclase) and F (feldspathoid), "
                "recast so Q + A + P (top) or A + P + F (bottom) = 100. "
                "Field numbers are IUGS's; the key gives the names. Not "
                "for rocks with more than 90 % mafic minerals.")
    fields = QAPF_PLUTONIC_FIELDS
    dashed = QAPF_PLUTONIC_DASHED


class StreckeisenQAPFVolcanic(_QAPFDiagram):
    key = "streckeisen_qapf_volcanic"
    title = "Streckeisen QAPF — volcanic rocks"
    citation = ("Streckeisen (1978), as in BGS RR 99-06 Figure 19 and Le "
                "Maitre (2002). The volcanic fields differ from the "
                "plutonic ones: no names above Q 60, dacite over "
                "P/(A+P) 65-100, basalt / andesite from Q 20 to F 10, "
                "and three foidites. Basanite against tephrite is "
                "olivine above or below 10 %; basalt against andesite "
                "needs colour index and SiO2.")
    fields = QAPF_VOLCANIC_FIELDS
    dashed = QAPF_VOLCANIC_DASHED


# ---------------------------------------------------------------------------
# The ternaries: fields as polygons, labels laid out by hand
# ---------------------------------------------------------------------------

def _draw_fields(ax, fields: dict) -> None:
    """Field outlines, without labels; each diagram places its own."""
    for abc in fields.values():
        a, b, c = zip(*abc)
        x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
        ax.add_patch(Polygon(np.column_stack([x, y]), closed=True,
                             fill=False, edgecolor="#444", linewidth=0.9,
                             alpha=0.85, zorder=2))


def _xy(abc) -> Tuple[float, float]:
    x, y = ternary_to_xy(pd.Series([abc[0]]), pd.Series([abc[1]]),
                         pd.Series([abc[2]]))
    return float(x.iloc[0]), float(y.iloc[0])


def _draw_labels(ax, labels, fontsize: float = 7.5) -> None:
    """Each label inside its field, or outside with a leader line to it.

    *labels* is ``(text, (a, b, c) in the field, text position (x, y)
    or None for inside, horizontal alignment)``.
    """
    for text, abc, outside, ha in labels:
        at = _xy(abc)
        if outside is None:
            ax.text(*at, text, ha="center", va="center", fontsize=fontsize,
                    color="#333", zorder=3)
        else:
            ax.annotate(text, xy=at, xytext=outside, ha=ha, va="center",
                        fontsize=fontsize, color="#333", zorder=3,
                        arrowprops=dict(arrowstyle="-", color="#666",
                                        linewidth=0.6, shrinkA=2,
                                        shrinkB=0))


# ---------------------------------------------------------------------------
# Gabbroic rocks, plagioclase – pyroxene – olivine
# ---------------------------------------------------------------------------
#
# BGS RR 99-06 Figure 13 (after Streckeisen 1976).  (Pl, Px, Ol) %, Pl
# at the top.  Anorthosite above Pl 90; plagioclase-bearing ultramafic
# rocks below Pl 10.  Between them gabbro / gabbronorite / norite has
# less than 5 % olivine and troctolite less than 5 % pyroxene: strips of
# constant width along the two sides, which meet at the middle of the
# Pl 90 line.  They used to open from about 3 % at Pl 90 to 5 % of the
# mafic minerals at Pl 10, which is no rule at all.  Measured on the
# reference figure in the project material, the inner lines keep the
# same distance from their sides from top to bottom, as a percentage of
# the whole and not of the mafic part would.

GABBRO_FIELDS: dict = {
    "anorthosite": [(100, 0, 0), (90, 10, 0), (90, 0, 10)],
    "gabbro / gabbronorite / norite": [(90, 10, 0), (10, 90, 0),
                                       (10, 85, 5), (90, 5, 5)],
    "olivine gabbro / olivine gabbronorite / olivine norite":
        [(90, 5, 5), (10, 85, 5), (10, 5, 85)],
    "troctolite": [(90, 0, 10), (10, 0, 90), (10, 5, 85), (90, 5, 5)],
    "plagioclase-bearing ultramafic rocks": [(10, 90, 0), (0, 100, 0),
                                             (0, 0, 100), (10, 0, 90)],
}

_GABBRO_LABELS = (
    ("anorthosite", (96, 2, 2), (0.30, 0.93), "right"),
    ("gabbro\ngabbronorite\nnorite", (50, 47.5, 2.5), (0.06, 0.56), "right"),
    ("olivine gabbro\nolivine gabbronorite\nolivine norite",
     (45, 27.5, 27.5), None, "center"),
    ("troctolite", (50, 2.5, 47.5), (0.94, 0.56), "left"),
    ("plagioclase-bearing ultramafic rocks", (5, 47.5, 47.5), None,
     "center"),
)

#: The prefixes Figure 13 sets beside the gabbroids: leuco- for Pl 65-90,
#: meso- 35-65, mela- 10-35.
_GABBRO_PREFIXES = ((65, 90, "(leuco-)"), (35, 65, "(meso-)"),
                    (10, 35, "(mela-)"))


class GabbroPlPxOl(TernaryDiagram):
    key = "gabbro_pl_px_ol"
    title = "Plagioclase – Pyroxene – Olivine — gabbroic rocks"
    citation = ("Streckeisen (1976), as in BGS RR 99-06 Figure 13 and Le "
                "Maitre (2002). Pl = plagioclase, Px = pyroxene (Opx + "
                "Cpx), Ol = olivine. Gabbro / gabbronorite / norite has "
                "under 5 % olivine and troctolite under 5 % pyroxene; "
                "dashed lines at Pl 65 and 35 bound the leuco-, meso- "
                "and mela- prefixes.")

    def _abc(self, df):
        # The template's plagioclase is P_mode, as on the QAPF; the
        # diagram used to look only for Pl_mode and found nothing.
        pl = resolve_column(df, ("Pl_mode", "Plagioclase_mode", "Pl",
                                 "P_mode"))
        ol = resolve_column(df, ("Ol_mode", "Olivine_mode", "Ol"))
        if pl is None or ol is None:
            return None
        # Px where given, else Opx + Cpx, row by row: the template has
        # all three, and a blank Px_mode column hid every sample.
        px = resolve_column(df, ("Px_mode", "Pyroxene_mode", "Px"))
        opx = resolve_column(df, ("Opx_mode", "Orthopyroxene_mode", "Opx"))
        cpx = resolve_column(df, ("Cpx_mode", "Clinopyroxene_mode", "Cpx"))
        pyroxene = (pd.to_numeric(df[px], errors="coerce") if px
                    else pd.Series(np.nan, index=df.index))
        if opx or cpx:
            parts = [pd.to_numeric(df[c], errors="coerce")
                     for c in (opx, cpx) if c]
            both = pd.concat(parts, axis=1)
            summed = both.sum(axis=1).where(both.notna().any(axis=1))
            pyroxene = pyroxene.fillna(summed)
        if pyroxene.isna().all():
            return None
        return (pd.to_numeric(df[pl], errors="coerce"), pyroxene,
                pd.to_numeric(df[ol], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Pl", "Px", "Ol"), options.x_axis)
        _draw_fields(ax, GABBRO_FIELDS)
        for plag in (65, 35):
            x, y = ternary_to_xy(pd.Series([plag, plag]),
                                 pd.Series([100 - plag, 0]),
                                 pd.Series([0, 100 - plag]))
            ax.plot(x, y, color="#777", linewidth=0.7, linestyle="--",
                    alpha=0.85, zorder=1)
        for low, high, prefix in _GABBRO_PREFIXES:
            mid = (low + high) / 2.0
            x, y = _xy((mid, 0, 100 - mid))
            ax.text(x + 0.16, y, prefix, fontsize=7.5, color="#666",
                    style="italic", ha="left", va="center")
        _draw_labels(ax, _GABBRO_LABELS)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


# ---------------------------------------------------------------------------
# Ultramafic rocks, olivine – orthopyroxene – clinopyroxene
# ---------------------------------------------------------------------------
#
# BGS RR 99-06 Figure 16 (after Streckeisen 1973).  (Ol, Opx, Cpx) %,
# Ol at the top.  Dunite above Ol 90; peridotites Ol 40-90; olivine
# pyroxenites Ol 5-40; below Ol 5 the pyroxenites, with orthopyroxenite
# and clinopyroxenite where one pyroxene is over 90 %.  Harzburgite and
# olivine orthopyroxenite have under 5 % Cpx, wehrlite and olivine
# clinopyroxenite under 5 % Opx: strips of constant width, as on the
# gabbroic diagram, meeting at the middle of the Ol 90 line and ending
# on the Ol 5 line where it meets the corner triangles.  They used to
# open from 4 % at Ol 90 to 3 % at Ol 40.

ULTRAMAFIC_FIELDS: dict = {
    "dunite": [(100, 0, 0), (90, 10, 0), (90, 0, 10)],
    "harzburgite": [(90, 10, 0), (40, 60, 0), (40, 55, 5), (90, 5, 5)],
    "lherzolite": [(90, 5, 5), (40, 55, 5), (40, 5, 55)],
    "wehrlite": [(90, 0, 10), (40, 0, 60), (40, 5, 55), (90, 5, 5)],
    "olivine orthopyroxenite": [(40, 60, 0), (10, 90, 0), (5, 90, 5),
                                (40, 55, 5)],
    "olivine websterite": [(40, 55, 5), (5, 90, 5), (5, 5, 90),
                           (40, 5, 55)],
    "olivine clinopyroxenite": [(40, 0, 60), (10, 0, 90), (5, 5, 90),
                                (40, 5, 55)],
    "orthopyroxenite": [(0, 100, 0), (10, 90, 0), (0, 90, 10)],
    "websterite": [(5, 90, 5), (5, 5, 90), (0, 10, 90), (0, 90, 10)],
    "clinopyroxenite": [(0, 0, 100), (10, 0, 90), (0, 10, 90)],
}

_ULTRAMAFIC_LABELS = (
    ("dunite", (96, 2, 2), (0.30, 0.93), "right"),
    ("harzburgite", (65, 32.5, 2.5), (0.10, 0.68), "right"),
    ("lherzolite", (65, 17.5, 17.5), None, "center"),
    ("wehrlite", (65, 2.5, 32.5), (0.90, 0.68), "left"),
    ("olivine\northopyroxenite", (22, 75.5, 2.5), (-0.04, 0.30), "right"),
    ("olivine websterite", (22, 39, 39), None, "center"),
    ("olivine\nclinopyroxenite", (22, 2.5, 75.5), (1.04, 0.30), "left"),
    ("websterite", (2.5, 48.75, 48.75), None, "center"),
    ("orthopyroxenite", (2, 95, 3), (0.14, -0.08), "center"),
    ("clinopyroxenite", (2, 3, 95), (0.86, -0.08), "center"),
)


class UltramaficOlOpxCpx(TernaryDiagram):
    key = "ultramafic_ol_opx_cpx"
    title = "Olivine – Orthopyroxene – Clinopyroxene — ultramafic rocks"
    citation = ("Streckeisen (1973), as in BGS RR 99-06 Figure 16 and Le "
                "Maitre (2002). For rocks with under 10 % plagioclase. "
                "Dunite above Ol 90, peridotites Ol 40-90, olivine "
                "pyroxenites Ol 5-40, pyroxenites below; harzburgite and "
                "olivine orthopyroxenite have under 5 % Cpx, wehrlite "
                "and olivine clinopyroxenite under 5 % Opx, and "
                "orthopyroxenite / clinopyroxenite over 90 % of one "
                "pyroxene.")

    def _abc(self, df):
        ol = resolve_column(df, ("Ol_mode", "Olivine_mode", "Ol"))
        opx = resolve_column(df, ("Opx_mode", "Orthopyroxene_mode", "Opx"))
        cpx = resolve_column(df, ("Cpx_mode", "Clinopyroxene_mode", "Cpx"))
        if ol is None or opx is None or cpx is None:
            return None
        return (pd.to_numeric(df[ol], errors="coerce"),
                pd.to_numeric(df[opx], errors="coerce"),
                pd.to_numeric(df[cpx], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Ol", "Opx", "Cpx"), options.x_axis)
        _draw_fields(ax, ULTRAMAFIC_FIELDS)
        _draw_labels(ax, _ULTRAMAFIC_LABELS)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


# ---------------------------------------------------------------------------
# Tuffs
# ---------------------------------------------------------------------------

#: Schmid (1981), BGS RR 99-06 Figure 7, as ``(Vitric, Crystal, Lithic)``
#: %: each tuff is named for its dominant component, so the three lines
#: run from the centre to the middle of each side.
SCHMID_TUFF_FIELDS: dict = {
    "vitric tuff": [(100, 0, 0), (50, 50, 0), (100 / 3, 100 / 3, 100 / 3),
                    (50, 0, 50)],
    "crystal tuff": [(0, 100, 0), (0, 50, 50), (100 / 3, 100 / 3, 100 / 3),
                     (50, 50, 0)],
    "lithic tuff": [(0, 0, 100), (50, 0, 50), (100 / 3, 100 / 3, 100 / 3),
                    (0, 50, 50)],
}

_SCHMID_LABELS = (
    ("vitric tuff\n(vitric ash)", (66, 17, 17), None, "center"),
    ("crystal tuff\n(crystal ash)", (17, 66, 17), None, "center"),
    ("lithic tuff\n(lithic ash)", (17, 17, 66), None, "center"),
)


def _tuff_columns(df):
    vitric = resolve_column(df, ("Vitric_pct", "Glass_pct", "Vitric_mode",
                                 "Vitric", "Glass"))
    crystal = resolve_column(df, ("Crystal_pct", "Crystals_pct",
                                  "Crystal_mode", "Crystal"))
    lithic = resolve_column(df, ("Lithic_pct", "Lithics_pct",
                                 "Lithic_mode", "Lithic"))
    if vitric is None or crystal is None or lithic is None:
        return None
    return {k: pd.to_numeric(df[c], errors="coerce")
            for k, c in (("V", vitric), ("C", crystal), ("L", lithic))}


class TuffSchmid1981(TernaryDiagram):
    key = "tuff_schmid_1981"
    title = "Vitric – Crystal – Lithic — tuffs (Schmid 1981)"
    citation = ("Schmid (1981), the classification the IUGS recommends, "
                "as in BGS RR 99-06 Figure 7 and Le Maitre (2002). Glass "
                "(pumice and shards) at the top, crystals and crystal "
                "fragments left, rock fragments right; a tuff is named "
                "for its dominant component, an ash likewise when "
                "unconsolidated.")

    def _abc(self, df):
        parts = _tuff_columns(df)
        if parts is None:
            return None
        return parts["V"], parts["C"], parts["L"]

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Glass", "Crystals", "Rock fragments"),
                           options.x_axis)
        _draw_fields(ax, SCHMID_TUFF_FIELDS)
        _draw_labels(ax, _SCHMID_LABELS, fontsize=8)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


# ---------------------------------------------------------------------------
# Pyroclastic rocks by fragment size — Fisher (1966)
# ---------------------------------------------------------------------------
#
# Fisher, R. V. (1966) Rocks composed of volcanic fragments and their
# classification.  Earth-Science Reviews 1, 287-298, Figure 1: "Mixture
# terms and end-member terms used for pyroclastic fragments".  Blocks
# and bombs (> 64 mm) at the top, lapilli (64-2 mm) left, ash (< 2 mm)
# right; five names.
#
# Fisher prints no percentages: "Precise percentage boundaries for the
# mixtures are not given, because they vary from perhaps as much as 40 %
# to as little as 15 %, depending upon the prejudices of the individual"
# (p. 293).  The lines of the figure are at thirds, and are used as
# drawn.  Measured on the 1950 x 2850 scan of page 292, with the sides
# fitted to within 1.6 px: the two horizontal lines at blocks 66.4 and
# 33.0 %, the lapillistone divider at lapilli 66.9 % and the tuff
# divider at ash 67.2 %, each parallel to its side to 0.01 in slope.
# Schmid (1981), the IUGS version, puts the same names at 75 and 25 %
# (from Le Maitre 2002; not re-read for this diagram).

_THIRD = 100 / 3

#: Fisher (1966) Figure 1, as ``(Blocks and bombs, Lapilli, Ash)`` %.
FISHER_1966_FIELDS: dict = {
    "pyroclastic breccia": [(100, 0, 0), (2 * _THIRD, _THIRD, 0),
                            (2 * _THIRD, 0, _THIRD)],
    "tuff-breccia": [(2 * _THIRD, _THIRD, 0), (_THIRD, 2 * _THIRD, 0),
                     (_THIRD, 0, 2 * _THIRD), (2 * _THIRD, 0, _THIRD)],
    "lapillistone": [(_THIRD, 2 * _THIRD, 0), (0, 100, 0),
                     (0, 2 * _THIRD, _THIRD)],
    "lapilli-tuff": [(_THIRD, 2 * _THIRD, 0), (0, 2 * _THIRD, _THIRD),
                     (0, _THIRD, 2 * _THIRD), (_THIRD, 0, 2 * _THIRD)],
    "tuff": [(_THIRD, 0, 2 * _THIRD), (0, _THIRD, 2 * _THIRD),
             (0, 0, 100)],
}

_FISHER_LABELS = (
    ("Pyroclastic\nbreccia", (80, 10, 10), None, "center"),
    ("Tuff-breccia", (50, 25, 25), None, "center"),
    ("Lapillistone", (10, 80, 10), None, "center"),
    ("Lapilli-tuff", (15, 42.5, 42.5), None, "center"),
    ("Tuff", (10, 10, 80), None, "center"),
)


def _fragment_size_columns(df):
    blocks = resolve_column(df, ("Blocks_bombs_pct", "Blocks_pct",
                                 "Bombs_pct", "Block_bomb_pct", "Blocks"))
    lapilli = resolve_column(df, ("Lapilli_pct", "Lapilli"))
    ash = resolve_column(df, ("Ash_pct", "Ash"))
    if blocks is None or lapilli is None or ash is None:
        return None
    return tuple(pd.to_numeric(df[c], errors="coerce")
                 for c in (blocks, lapilli, ash))


class PyroclasticFisher1966(TernaryDiagram):
    key = "pyroclastic_fisher_1966"
    title = "Blocks – Lapilli – Ash — pyroclastic rocks (Fisher 1966)"
    citation = ("Fisher (1966) Earth-Sci. Rev. 1, 287-298, Figure 1: "
                "pyroclastic rocks named by the size of their fragments — "
                "blocks and bombs over 64 mm, lapilli 64-2 mm, ash under "
                "2 mm. Fisher gives no percentages for the boundaries; "
                "they are drawn, and taken here, at thirds. The IUGS "
                "version (Schmid 1981) puts them at 75 and 25 %.")

    def _abc(self, df):
        return _fragment_size_columns(df)

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Blocks and bombs\n> 64 mm",
                                "Lapilli\n64-2 mm", "Ash\n< 2 mm"),
                           options.x_axis)
        _draw_fields(ax, FISHER_1966_FIELDS)
        _draw_labels(ax, _FISHER_LABELS, fontsize=8)
        self._scatter_samples(ax, df, plot_style)
        self._apply_legend(ax, options)
        figure.tight_layout()


def field_of(fields: dict, abc) -> Optional[str]:
    """The name of the field of *fields* holding the point *abc*, or
    ``None``; for checking that labels and samples land where meant."""
    from matplotlib.path import Path

    point = _xy(abc)
    for name, vertices in fields.items():
        a, b, c = zip(*vertices)
        x, y = ternary_to_xy(pd.Series(a), pd.Series(b), pd.Series(c))
        if Path(np.column_stack([x, y])).contains_point(point):
            return name
    return None
