"""IUGS petrographic classification ternaries.

This module ships five classical modal-mineralogy classifiers used in
field petrography and thin-section work:

* ``streckeisen_qapf_plutonic``  – Streckeisen 1976 / IUGS 1989 double-
  triangle (QAP top, APF bottom) for coarse-grained rocks.
* ``streckeisen_qapf_volcanic``  – same double-triangle with the IUGS
  volcanic field names (rhyolite, dacite, trachyte, phonolite, …).
* ``gabbro_pl_px_ol``           – Plagioclase – Pyroxene – Olivine
  ternary for the gabbroic family (Le Maitre 2002).
* ``ultramafic_ol_opx_cpx``      – Olivine – Orthopyroxene –
  Clinopyroxene ternary for peridotites and pyroxenites
  (Streckeisen 1976).
* ``tuff_crystal_vitric_lithic`` – Pyroclastic tuff classification by
  the proportions of crystals, glass shards and lithic clasts
  (Schmid 1981, IUGS-recommended).

Inputs are modal proportions read from the *Petrography* sheet of the
data template (columns ``Q_mode``, ``A_mode``, ``P_mode``, …).  Each
diagram is silica-saturation aware (QAPF skips rows with both Q > 0 and
F > 0) and gracefully returns an empty plot when the required modal
columns are missing.

References
----------
- Streckeisen, A. (1976). To each plutonic rock its proper name.
  *Earth-Sci. Rev.* 12, 1-33.
- Le Bas, M.J. & Streckeisen, A. (1991). The IUGS systematics of
  igneous rocks. *J. Geol. Soc.* 148, 825-833.
- Le Maitre, R.W. (ed., 2002). *Igneous Rocks – A Classification and
  Glossary of Terms* (IUGS recommendations), 2nd ed., CUP.
- Schmid, R. (1981). Descriptive nomenclature and classification of
  pyroclastic deposits and fragments. *Geology* 9, 41-43.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd

from .base import (
    Diagram,
    PlotOptions,
    draw_ternary_frame,
    get_groups,
    resolve_column,
    ternary_to_xy,
)
from .tectonic_ternary import _draw_ternary_fields, _plot_ternary_data


# ---------------------------------------------------------------------------
# Common QAPF helpers
# ---------------------------------------------------------------------------

# Apex coordinates for the QAPF double-triangle. We share the A-P edge
# by drawing two triangles whose A and P apexes coincide at y = 0:
#
#                     Q  (0.5,  +√3/2)         ⎫  QAP triangle
#                                              ⎬  silica-saturated
#       A (0.0, 0)               P (1.0, 0)    ⎭  rocks plot here
#                                              ⎫  APF triangle
#                     F  (0.5,  −√3/2)         ⎬  silica-undersaturated
#                                              ⎭  rocks plot here

_HALF_HEIGHT = np.sqrt(3) / 2.0


def _qapf_position(q: float, a: float, p: float, f: float
                    ) -> Optional[Tuple[float, float]]:
    """Place one sample on the QAPF double-triangle.

    Per IUGS rules a single rock cannot have both quartz and foid: if Q
    is dominant the rock is silica-oversaturated (top triangle), if F
    is dominant it is silica-undersaturated (bottom triangle). We assign
    the sample to whichever of Q/F is larger (or to QAP when they tie at
    zero); the smaller is silently ignored.
    """
    q = max(float(q), 0.0)
    a = max(float(a), 0.0)
    p = max(float(p), 0.0)
    f = max(float(f), 0.0)
    if a + p == 0 and q == 0 and f == 0:
        return None
    if q >= f:
        total = q + a + p
        if total <= 0:
            return None
        q_n, a_n, p_n = q / total, a / total, p / total
        # Map (Q, A, P) onto (apex Q, apex A, apex P)
        x = 0.5 * a_n + 1.0 * p_n + 0.5 * q_n
        y = _HALF_HEIGHT * q_n
        return x, y
    total = f + a + p
    if total <= 0:
        return None
    f_n, a_n, p_n = f / total, a / total, p / total
    x = 0.5 * a_n + 1.0 * p_n + 0.5 * f_n
    y = -_HALF_HEIGHT * f_n
    return x, y


def _draw_qapf_frame(ax, axis_style, *, plutonic: bool) -> None:
    """Draw the QAPF double-triangle outline, apex labels and grid."""
    Q = (0.5,  _HALF_HEIGHT)
    F = (0.5, -_HALF_HEIGHT)
    A = (0.0, 0.0)
    P = (1.0, 0.0)
    # Upper triangle (QAP)
    ax.plot([A[0], Q[0], P[0], A[0]], [A[1], Q[1], P[1], A[1]],
            color="#333", linewidth=1.0)
    # Lower triangle (APF)
    ax.plot([A[0], F[0], P[0], A[0]], [A[1], F[1], P[1], A[1]],
            color="#333", linewidth=1.0)

    # Apex labels
    ax.text(Q[0], Q[1] + 0.04, "Q", ha="center", va="bottom",
            **axis_style.label_kwargs())
    ax.text(F[0], F[1] - 0.04, "F", ha="center", va="top",
            **axis_style.label_kwargs())
    ax.text(A[0] - 0.03, A[1], "A", ha="right", va="center",
            **axis_style.label_kwargs())
    ax.text(P[0] + 0.03, P[1], "P", ha="left", va="center",
            **axis_style.label_kwargs())

    # Silica-saturation labels along the shared edge
    suffix = "plutonic" if plutonic else "volcanic"
    ax.text(0.5, 0.0 + 0.015, f"silica-oversaturated ({suffix})",
            ha="center", va="bottom", fontsize=7, style="italic",
            color="#5b6478")
    ax.text(0.5, 0.0 - 0.015, f"silica-undersaturated ({suffix})",
            ha="center", va="top", fontsize=7, style="italic",
            color="#5b6478")

    ax.set_xlim(-0.12, 1.12)
    ax.set_ylim(-_HALF_HEIGHT - 0.10, _HALF_HEIGHT + 0.08)
    ax.set_aspect("equal")
    ax.axis("off")


# ---------------------------------------------------------------------------
# Field labels — collapsed sub-fields into the principal IUGS names so the
# diagram stays readable at print resolution. The full sub-classification
# is documented in Streckeisen (1976) and Le Bas & Streckeisen (1991).
# ---------------------------------------------------------------------------

_QAPF_PLUTONIC_LABELS: tuple[tuple[str, float, float, float, float, float, float], ...] = (
    # (label, x, y, font_size, rotation, alpha, color)
    # Top half (Q-saturated)
    ("Quartzolite",          0.50,  0.78, 7,  0, 0.85, "#333"),
    ("Quartz-rich\ngranitoid", 0.50, 0.60, 7, 0, 0.85, "#333"),
    ("Alkali fsp.\ngranite", 0.32,  0.42, 7,  0, 0.85, "#333"),
    ("Granite",              0.50,  0.42, 8,  0, 0.95, "#1c2237"),
    ("Granodiorite",         0.66,  0.42, 8,  0, 0.95, "#1c2237"),
    ("Tonalite",             0.82,  0.32, 8,  0, 0.95, "#1c2237"),
    ("Qz. alkali\nfsp. syenite", 0.27, 0.18, 6, 0, 0.85, "#333"),
    ("Qz. syenite",          0.42,  0.16, 7,  0, 0.85, "#333"),
    ("Qz. monzonite",        0.55,  0.16, 7,  0, 0.85, "#333"),
    ("Qz. monzo-\ndiorite",  0.69,  0.16, 6,  0, 0.85, "#333"),
    ("Qz. diorite /\ngabbro", 0.85, 0.18, 6,  0, 0.85, "#333"),
    ("Alkali fsp.\nsyenite", 0.18,  0.04, 7,  0, 0.95, "#1c2237"),
    ("Syenite",              0.36,  0.04, 8,  0, 0.95, "#1c2237"),
    ("Monzonite",            0.50,  0.04, 8,  0, 0.95, "#1c2237"),
    ("Monzo-\ndiorite",      0.66,  0.04, 7,  0, 0.95, "#1c2237"),
    ("Diorite /\nGabbro",    0.85,  0.05, 8,  0, 0.95, "#1c2237"),
    # Bottom half (F-undersaturated)
    ("Foid-bearing\nsyenite", 0.36, -0.07, 6, 0, 0.85, "#333"),
    ("Foid-bearing\nmonzonite", 0.55, -0.07, 6, 0, 0.85, "#333"),
    ("Foid-bearing\ndiorite/gabbro", 0.78, -0.07, 6, 0, 0.85, "#333"),
    ("Foid syenite",         0.35, -0.30, 7,  0, 0.95, "#1c2237"),
    ("Foid\nmonzosyenite",   0.50, -0.30, 7,  0, 0.95, "#1c2237"),
    ("Foid monzo-\ndiorite/gabbro", 0.70, -0.30, 6, 0, 0.95, "#1c2237"),
    ("Foidolite",            0.50, -0.65, 9,  0, 0.95, "#1c2237"),
)

_QAPF_VOLCANIC_LABELS: tuple[tuple[str, float, float, float, float, float, float], ...] = (
    ("Quartzolite",          0.50,  0.78, 7,  0, 0.85, "#333"),
    ("Rhyolite",             0.50,  0.42, 9,  0, 0.95, "#1c2237"),
    ("Alkali fsp.\nrhyolite", 0.32, 0.42, 7,  0, 0.85, "#333"),
    ("Dacite",               0.74,  0.36, 9,  0, 0.95, "#1c2237"),
    ("Quartz\ntrachyte",     0.36,  0.16, 7,  0, 0.85, "#333"),
    ("Quartz latite",        0.55,  0.16, 7,  0, 0.85, "#333"),
    ("Quartz\nandesite/basalt", 0.80, 0.16, 6, 0, 0.85, "#333"),
    ("Alkali fsp.\ntrachyte", 0.18, 0.04, 7,  0, 0.95, "#1c2237"),
    ("Trachyte",             0.36,  0.04, 8,  0, 0.95, "#1c2237"),
    ("Latite",               0.55,  0.04, 8,  0, 0.95, "#1c2237"),
    ("Andesite /\nBasalt",   0.85,  0.04, 8,  0, 0.95, "#1c2237"),
    ("Phonolitic\ntrachyte", 0.30, -0.10, 6, 0, 0.85, "#333"),
    ("Tephritic\nlatite",    0.55, -0.10, 6, 0, 0.85, "#333"),
    ("Tephritic\nbasalt",    0.80, -0.10, 6, 0, 0.85, "#333"),
    ("Phonolite",            0.32, -0.30, 8,  0, 0.95, "#1c2237"),
    ("Phono-\ntephrite",     0.50, -0.30, 7,  0, 0.95, "#1c2237"),
    ("Tephrite /\nBasanite", 0.70, -0.30, 7,  0, 0.95, "#1c2237"),
    ("Foidite",              0.50, -0.65, 10, 0, 0.95, "#1c2237"),
)


def _draw_qapf_internal_lines(ax) -> None:
    """Draw the IUGS field boundary lines inside the double-triangle.

    The full Streckeisen 1976 grid has 30+ sub-fields; we render the
    principal Q-isolines (90, 60, 20, 5 %) and the A/P ratio guides
    (90/10, 65/35, 35/65, 10/90) which are the most petrologically
    meaningful divisions.
    """
    # Q-isolines (top triangle)
    for q_pct in (0.05, 0.20, 0.60, 0.90):
        # Endpoints at A/(A+P) = 0 and 1, with Q = q_pct
        x0 = 0.5 * q_pct                  # A-side at A/(A+P)=1
        x1 = 1.0 - 0.5 * q_pct            # P-side at A/(A+P)=0
        y = q_pct * _HALF_HEIGHT
        ax.plot([x0, x1], [y, y], color="#888", lw=0.7, alpha=0.7)

    # F-isolines (bottom triangle)
    for f_pct in (0.10, 0.60):
        x0 = 0.5 * f_pct
        x1 = 1.0 - 0.5 * f_pct
        y = -f_pct * _HALF_HEIGHT
        ax.plot([x0, x1], [y, y], color="#888", lw=0.7, alpha=0.7)

    # A/P-ratio rays from Q apex down to A-P edge and then to F apex
    for ap_ratio in (0.10, 0.35, 0.65, 0.90):
        # x along the A-P edge at A/(A+P) = (1 - ap_ratio)
        x_edge = ap_ratio
        # Top ray: from (x_edge, 0) to Q apex (0.5, +√3/2)
        ax.plot([x_edge, 0.5], [0.0,  _HALF_HEIGHT],
                color="#888", lw=0.7, alpha=0.7)
        # Bottom ray: from (x_edge, 0) to F apex (0.5, -√3/2)
        ax.plot([x_edge, 0.5], [0.0, -_HALF_HEIGHT],
                color="#888", lw=0.7, alpha=0.7)


# ---------------------------------------------------------------------------
# QAPF base class — plutonic and volcanic share everything except labels
# ---------------------------------------------------------------------------

class _QAPFDiagram(Diagram):
    """Shared rendering for the Streckeisen QAPF double-triangle."""
    _is_plutonic: bool = True
    _labels: tuple = ()

    def _qapf_columns(self, df: pd.DataFrame
                       ) -> Optional[Tuple[pd.Series, pd.Series, pd.Series, pd.Series]]:
        cols = {}
        for key, candidates in (
            ("Q", ("Q_mode", "Q", "Quartz_mode", "Qtz")),
            ("A", ("A_mode", "A", "Alkali_feldspar_mode", "Alk_fsp", "Kfs")),
            ("P", ("P_mode", "P", "Plagioclase_mode", "Pl")),
            ("F", ("F_mode", "F", "Foid_mode", "Foid")),
        ):
            col = resolve_column(df, candidates)
            if col is None:
                return None
            cols[key] = pd.to_numeric(df[col], errors="coerce")
        return cols["Q"], cols["A"], cols["P"], cols["F"]

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        _draw_qapf_frame(ax, options.x_axis,
                          plutonic=self._is_plutonic)
        _draw_qapf_internal_lines(ax)
        for label, x, y, fs, rot, alpha, color in self._labels:
            ax.text(x, y, label, ha="center", va="center",
                    fontsize=fs, rotation=rot, alpha=alpha,
                    color=color, zorder=2)

        if df is not None and not df.empty:
            for group_label, sub, gs in get_groups(df, plot_style):
                cols = self._qapf_columns(sub)
                if cols is None:
                    continue
                q, a, p, f = cols
                xs, ys = [], []
                for i in q.index:
                    pos = _qapf_position(q[i], a[i], p[i], f[i])
                    if pos is None:
                        continue
                    xs.append(pos[0])
                    ys.append(pos[1])
                if not xs:
                    continue
                color = gs.color if gs else "#1f77b4"
                marker = gs.marker if gs else "o"
                show_markers = getattr(gs, "show_markers", True) if gs else True
                if show_markers:
                    ax.scatter(xs, ys,
                               s=plot_style.point_size ** 2,
                               alpha=plot_style.alpha,
                               c=color, marker=marker,
                               label=group_label,
                               edgecolors="black", linewidths=0.4,
                               zorder=4)

        self._apply_legend(ax, options)
        figure.tight_layout()


class StreckeisenQAPFPlutonic(_QAPFDiagram):
    key = "streckeisen_qapf_plutonic"
    title = "Streckeisen QAPF — plutonic rocks"
    citation = ("Streckeisen (1976); Le Bas & Streckeisen (1991). "
                "Modal Q, A (alkali feldspar), P (plagioclase) and F "
                "(feldspathoid) percentages renormalised so Q + A + P "
                "(top) or A + P + F (bottom) = 100.")
    _is_plutonic = True
    _labels = _QAPF_PLUTONIC_LABELS


class StreckeisenQAPFVolcanic(_QAPFDiagram):
    key = "streckeisen_qapf_volcanic"
    title = "Streckeisen QAPF — volcanic rocks"
    citation = ("Streckeisen (1978); Le Maitre (2002). IUGS-recommended "
                "volcanic equivalents of the QAPF plutonic fields: "
                "rhyolite ⇔ granite, dacite ⇔ granodiorite, trachyte ⇔ "
                "syenite, andesite/basalt ⇔ diorite/gabbro, phonolite ⇔ "
                "foid syenite, etc.")
    _is_plutonic = False
    _labels = _QAPF_VOLCANIC_LABELS


# ---------------------------------------------------------------------------
# Gabbro Pl – Px – Ol (Le Maitre 2002 / IUGS)
# ---------------------------------------------------------------------------
# Tuples encode (Pl%, Px%, Ol%) in the apex order (A=Pl on top, B=Px on
# left, C=Ol on right).  The classification follows the simplified IUGS
# scheme shown in Le Maitre (2002) / Geology-is-the-Way:
#
#   - Plag ≥ 90 ............. anorthosite (small cap at the Pl apex)
#   - 10 ≤ Plag ≤ 90 ........ gabbroid family, subdivided by the
#                              5 %-rule on Ol/(Ol+Px):
#         Ol/(Ol+Px) ≤ 0.05 → gabbro / gabbronorite / norite
#         0.05 < ratio < 0.95 → olivine gabbro / gabbronorite / norite
#         Ol/(Ol+Px) ≥ 0.95 → troctolite
#   - Plag < 10 ............. plagioclase-bearing ultramafic rocks
#
# The 5 %-rule endpoints (at Pl = 90 and 10) on the gabbro / olivine-gabbro
# boundary are:    Pl=90, Px=9.5, Ol=0.5     and    Pl=10, Px=85.5, Ol=4.5
# Symmetric values on the troctolite / olivine-gabbro boundary:
#                  Pl=90, Px=0.5, Ol=9.5     and    Pl=10, Px=4.5, Ol=85.5
# ---------------------------------------------------------------------------

_GABBRO_FIELDS: dict = {
    "Anorthosite":                  [(100, 0, 0), (90, 10, 0), (90, 0, 10)],
    # Inner side of the gabbro / troctolite wedges opens to ~3 % of the
    # mafic fraction at Pl = 90 (matching the Geology-is-the-Way figure)
    # and narrows to the canonical 5 %-rule positions at Pl = 10.
    "Gabbro /\nNorite /\nGabbronorite": [(90, 10, 0),  (10, 90, 0),
                                          (10, 85.5, 4.5), (90, 7, 3)],
    "Olivine gabbro /\nolivine gabbronorite /\nolivine norite":
                                    [(90, 7, 3),     (10, 85.5, 4.5),
                                     (10, 4.5, 85.5), (90, 3, 7)],
    "Troctolite":                   [(90, 3, 7),     (10, 4.5, 85.5),
                                     (10, 0, 90),    (90, 0, 10)],
    "Plagioclase-bearing\nultramafic rocks":
                                    [(10, 90, 0), (0, 100, 0),
                                     (0, 0, 100), (10, 0, 90)],
}

# Dashed reference isolines that mark the leuco-/meso-/mela- prefix
# boundaries inside the gabbroid family (Plag = 90, 65, 35, 10).
# Drawn on top of the field polygons with no rock-name labels — they only
# clarify which prefix should be appended to the rock name.
_GABBRO_PREFIX_ISOPLETHS = (
    # (Plag %, label drawn on the Pl-Ol right edge, label text)
    (90, "90", None),       # already a solid boundary of "Anorthosite"
    (65, "65", "(LEUCO-)"),
    (35, "35", "(MELA-)"),
    (10, "10", None),       # already a solid boundary of the ultramafic band
)


class GabbroPlPxOl(Diagram):
    key = "gabbro_pl_px_ol"
    title = "Plagioclase – Pyroxene – Olivine — gabbro classification"
    citation = ("Le Maitre (2002) / IUGS.  Modal classification of "
                "gabbroid rocks.  Apex Pl = plagioclase, Px = "
                "pyroxene (Opx + Cpx), Ol = olivine.  The 5 %-rule on "
                "Ol/(Ol+Px) splits the gabbroid band into gabbro/norite, "
                "olivine gabbro/norite, and troctolite.  Dashed lines at "
                "Pl = 65 and 35 mark the optional leuco-/mela- prefixes.")

    def _abc(self, df):
        pl = resolve_column(df, ("Pl_mode", "Plagioclase_mode", "Pl"))
        px = resolve_column(df, ("Px_mode", "Pyroxene_mode", "Px"))
        ol = resolve_column(df, ("Ol_mode", "Olivine_mode", "Ol"))
        if pl is None or px is None or ol is None:
            # Fallback — if the user only filled Opx + Cpx columns,
            # sum them on the fly.
            opx = resolve_column(df, ("Opx_mode", "Orthopyroxene_mode", "Opx"))
            cpx = resolve_column(df, ("Cpx_mode", "Clinopyroxene_mode", "Cpx"))
            if pl is None or ol is None or opx is None or cpx is None:
                return None
            px_s = (pd.to_numeric(df[opx], errors="coerce").fillna(0)
                    + pd.to_numeric(df[cpx], errors="coerce").fillna(0))
            return (pd.to_numeric(df[pl], errors="coerce"),
                    px_s,
                    pd.to_numeric(df[ol], errors="coerce"))
        return (pd.to_numeric(df[pl], errors="coerce"),
                pd.to_numeric(df[px], errors="coerce"),
                pd.to_numeric(df[ol], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Pl", "Px", "Ol"), options.x_axis)
        _draw_ternary_fields(ax, _GABBRO_FIELDS, fontsize=8)
        self._draw_prefix_isopleths(ax)
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()

    @staticmethod
    def _draw_prefix_isopleths(ax) -> None:
        """Dashed horizontal isolines at Plag = 65 and 35 with the
        leuco-/mela- prefix labels on the right (Pl-Ol) edge."""
        for plag, _tick, prefix in _GABBRO_PREFIX_ISOPLETHS:
            if prefix is None:
                continue
            # Build the isoline at constant Plag: (Pl=plag, Px=100-plag, Ol=0)
            # to (Pl=plag, Px=0, Ol=100-plag).
            a = pd.Series([plag, plag])
            b = pd.Series([100 - plag, 0])
            c = pd.Series([0, 100 - plag])
            xs, ys = ternary_to_xy(a, b, c)
            ax.plot(xs, ys, color="#777", linewidth=0.7,
                    linestyle="--", alpha=0.85, zorder=1)
            # Place the prefix label just outside the right edge.
            tx, ty = xs.iloc[1] + 0.015, ys.iloc[1] + 0.008
            ax.text(tx, ty, prefix, fontsize=7.5, color="#666",
                    style="italic", ha="left", va="center")


# ---------------------------------------------------------------------------
# Ultramafic Ol – Opx – Cpx (Streckeisen 1976)
# ---------------------------------------------------------------------------

_ULTRAMAFIC_FIELDS: dict = {
    # Apex order: A = Ol (top), B = Opx (left), C = Cpx (right).
    # Tuples are (Ol%, Opx%, Cpx%).
    #
    # IUGS / Le Maitre (2002) classification (Geology-is-the-Way figure):
    #   - Ol ≥ 90 ........ dunite (small cap)
    #   - 40 ≤ Ol < 90 ... peridotite (harzburgite / lherzolite / wehrlite)
    #                       split by 5 %-rule on Cpx/(Opx+Cpx); the strip
    #                       widens at the top to a 3-pp opening so the
    #                       labels are readable (same trick as the gabbro
    #                       diagram).
    #   -  5 ≤ Ol < 40 ... olivine pyroxenite (olivine ortho / webst /
    #                       clino), split by 5 %-rule.
    #   -  0 ≤ Ol <  5 ... pure pyroxenite, split by 10 %-rule on Cpx —
    #                       i.e. the "10/90" labels at the bottom edge:
    #                       orthopyroxenite (Cpx<10), websterite (10-90),
    #                       clinopyroxenite (Cpx>90).
    "Dunite":                  [(100, 0, 0), (90, 10, 0), (90, 0, 10)],
    # Peridotite zone — wedges open to ~4 % of the mafic fraction at the
    # top (Ol=90) and narrow to the canonical 5 %-rule positions at Ol=40.
    "Harzburgite":             [(90, 10, 0), (40, 60, 0),
                                (40, 57, 3), (90, 6, 4)],
    "Lherzolite":              [(90, 6, 4), (40, 57, 3),
                                (40, 3, 57), (90, 4, 6)],
    "Wehrlite":                [(90, 0, 10), (40, 0, 60),
                                (40, 3, 57), (90, 4, 6)],
    # Olivine-pyroxenite zone now starts at Ol = 10 (instead of Ol = 5),
    # so it dovetails with the bigger corner triangles below.  Inner
    # boundaries still follow the 5 %-rule, giving (10, 85.5, 4.5) and
    # (10, 4.5, 85.5) at the bottom.
    "Olivine\northopyroxenite": [(40, 60, 0), (10, 90, 0),
                                  (5, 90, 5), (40, 57, 3)],
    "Olivine\nwebsterite":     [(40, 57, 3), (5, 90, 5),
                                (5, 5, 90), (40, 3, 57)],
    "Olivine\nclinopyroxenite": [(40, 0, 60), (10, 0, 90),
                                  (5, 5, 90), (40, 3, 57)],
    # Pure-pyroxenite corners are full diagonal triangles defined by the
    # 10 %-rule: Opx ≥ 90 for orthopyroxenite and Cpx ≥ 90 for
    # clinopyroxenite — they cover ~10 % of each apex corner, matching
    # the reference Geology-is-the-Way figure.
    "Orthopyroxenite":         [(0, 100, 0), (10, 90, 0), (0, 90, 10)],
    "Websterite":              [(5, 90, 5), (5, 5, 90),
                                (0, 10, 90), (0, 90, 10)],
    "Clinopyroxenite":         [(0, 0, 100), (10, 0, 90), (0, 10, 90)],
}


class UltramaficOlOpxCpx(Diagram):
    key = "ultramafic_ol_opx_cpx"
    title = "Olivine – Orthopyroxene – Clinopyroxene — ultramafic rocks"
    citation = ("Streckeisen (1976) / Le Maitre (2002) / IUGS.  Modal "
                "classification of ultramafic rocks (Pl < 10 %). "
                "Peridotite zone (Ol 40-90 %) uses the 5 %-rule on Cpx/"
                "(Opx+Cpx); olivine-pyroxenite zone (Ol 5-40 %) uses the "
                "same 5 %-rule; pure pyroxenite zone (Ol < 5 %) uses the "
                "10 %-rule on Cpx (orthopyroxenite < 10 %, websterite "
                "10-90 %, clinopyroxenite > 90 %).  Apex Ol = olivine, "
                "Opx = orthopyroxene, Cpx = clinopyroxene.")

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
        # Pin the websterite label at Ol=5, midway between the two
        # corner triangles' diagonal hypotenuses — i.e. exactly at the
        # vertical mid-line of the corner triangles (which span Ol=0-10).
        _draw_ternary_fields(
            ax, _ULTRAMAFIC_FIELDS, fontsize=7.5,
            label_overrides={"Websterite": (5, 66, 66)},
        )
        self._draw_zone_labels(ax)
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()

    @staticmethod
    def _draw_zone_labels(ax) -> None:
        """Italic 'PERIDOTITE' / 'PYROXENITE' tags along the right (Ol-Cpx)
        edge, mirroring the Geology-is-the-Way figure."""
        # PERIDOTITE label sits around Ol≈65 on the right edge.
        a = pd.Series([65])
        b = pd.Series([0])
        c = pd.Series([35])
        x, y = ternary_to_xy(a, b, c)
        ax.text(x.iloc[0] + 0.02, y.iloc[0] + 0.005, "PERIDOTITE",
                fontsize=8, color="#666", style="italic",
                rotation=-60, ha="left", va="center")
        # PYROXENITE label sits around Ol≈20 on the right edge.
        a = pd.Series([20])
        b = pd.Series([0])
        c = pd.Series([80])
        x, y = ternary_to_xy(a, b, c)
        ax.text(x.iloc[0] + 0.02, y.iloc[0] + 0.005, "PYROXENITE",
                fontsize=8, color="#666", style="italic",
                rotation=-60, ha="left", va="center")


# ---------------------------------------------------------------------------
# Pyroclastic Crystal – Vitric – Lithic (Schmid 1981)
# ---------------------------------------------------------------------------

# Apex order: A = Lithic (top), B = Crystal (left), C = Vitric (right).
# Tuples are (Lithic%, Crystal%, Vitric%).
#
# Horizontal bands at Lithic = 50, 25, 10 split the triangle into four
# layers.  All three internal dividers — between Lithic-crystal /
# Lithic-vitric in band 2, Crystal-lithic / Vitric-lithic in band 3,
# and Crystal-vitric / Vitric-crystal in the bottom band — lie on a
# SINGLE radial line from the Lithic apex through (0, 25, 75) on the
# bottom edge (i.e. constant Crystal:Vitric = 1:3).  On this line:
#   at Lithic=50 → (50, 12.5, 37.5)
#   at Lithic=25 → (25, 18.75, 56.25)
#   at Lithic=10 → (10, 22.5, 67.5)
#   at Lithic= 0 → (0, 25, 75)
# The bottom band has two extra Crystal:Vitric sub-divisions at
# Vitric/(C+V) = 0.5 and 0.9 (the "50" and "10" ticks along the bottom).
_TUFF_FIELDS: dict = {
    # Top layer — Lithic ≥ 50
    "Lithic\ntuff":          [(100, 0, 0), (50, 50, 0), (50, 0, 50)],
    # Layer 2 — 25 ≤ Lithic < 50, divider on the 1:3 radial line
    "Lithic-\ncrystal tuff": [(50, 50, 0), (50, 12.5, 37.5),
                              (25, 18.75, 56.25), (25, 75, 0)],
    "Lithic-\nvitric tuff":  [(50, 0, 50), (50, 12.5, 37.5),
                              (25, 18.75, 56.25), (25, 0, 75)],
    # Layer 3 — 10 ≤ Lithic < 25, same 1:3 radial divider
    "Crystal-\nlithic tuff": [(25, 75, 0), (25, 18.75, 56.25),
                              (10, 22.5, 67.5), (10, 90, 0)],
    "Vitric-\nlithic tuff":  [(25, 0, 75), (25, 18.75, 56.25),
                              (10, 22.5, 67.5), (10, 0, 90)],
    # Bottom layer — Lithic < 10, divided by Vitric/(C+V) at 0.5, 0.75, 0.9
    "Crystal\ntuff":         [(10, 90, 0), (0, 100, 0),
                              (0, 50, 50), (10, 45, 45)],
    "Crystal-\nvitric tuff": [(10, 45, 45), (0, 50, 50),
                              (0, 25, 75), (10, 22.5, 67.5)],
    "Vitric-\ncrystal tuff": [(10, 22.5, 67.5), (0, 25, 75),
                              (0, 10, 90), (10, 9, 81)],
    "Vitric\ntuff":          [(10, 9, 81), (0, 10, 90),
                              (0, 0, 100), (10, 0, 90)],
}


class TuffCrystalVitricLithic(Diagram):
    key = "tuff_crystal_vitric_lithic"
    title = "Crystal – Vitric – Lithic — pyroclastic tuff classification"
    citation = ("Schmid (1981); IUGS.  Classification of pyroclastic "
                "deposits by the relative proportions of crystals, glass "
                "shards (vitric) and lithic clasts.  Apex Lithic (top), "
                "Crystal (left), Vitric (right).  Lithic content drives "
                "the principal name (Lithic / Lithic- / -Lithic / no "
                "lithic prefix) via horizontal bands at Lithic = 50, 25, "
                "10 %.  The bottom band (Lithic < 10) is further split "
                "by the Crystal/Vitric ratio at 50/25/10 % ticks.")

    def _abc(self, df):
        li = resolve_column(df, ("Lithic_pct", "Lithics_pct", "Lithic_mode"))
        cr = resolve_column(df, ("Crystal_pct", "Crystals_pct", "Crystal_mode"))
        vt = resolve_column(df, ("Vitric_pct", "Glass_pct", "Vitric_mode"))
        if cr is None or vt is None or li is None:
            return None
        return (pd.to_numeric(df[li], errors="coerce"),
                pd.to_numeric(df[cr], errors="coerce"),
                pd.to_numeric(df[vt], errors="coerce"))

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        draw_ternary_frame(ax, ("Lithic", "Crystal", "Vitric"),
                            options.x_axis)
        _draw_ternary_fields(ax, _TUFF_FIELDS, fontsize=7.5)
        _plot_ternary_data(ax, df, plot_style, self._abc)
        self._apply_legend(ax, options)
        figure.tight_layout()
