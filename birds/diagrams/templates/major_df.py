"""Discriminant-function binary diagrams for oceanic basalts.

Two diagrams, both from Vermeesch (2006a), who reassessed earlier work
with the additive log-ratio transform:

* **Pearce (1976)** — seven major-element oxides over SiO2, without any
  iron term at all.  The diagram is named "major element oxides
  (without FeO)" for that reason.
* **Butler & Woronow (1986)** — Zr, Y and Sr over Ti.

Each plots **DF1 against DF2**, and each panel is split into IAB, MORB
and OIB by three straight boundaries radiating from a central point.
Both were previously implemented here as one-dimensional strip charts
with invented coefficients; see *Provenance*.

Provenance
----------
Equations transcribed from Rollinson & Pease (2021) Appendix 5.1
("Discriminant Function Equations for Tectonic Discrimination
Diagrams", Axes for Figure 5.5, Oceanic Basalts), and the boundary
geometry from the Figure 5.5 caption.

What was here before matched neither.  The Pearce function used an
``Fe2O3t`` term that the published equation does not contain, omitted
its ``MnO`` term, carried an intercept the equation has no room for,
and none of its seven coefficients matched.  The Butler & Woronow
function divided TiO2 by SiO2 and Zr and Y by Sr, where the published
axes divide Zr, Y and Sr by Ti; its "intercept" of −1.840 is in fact
the published Sr coefficient of DF2.  Both collapsed a two-axis
diagram onto one axis, which cannot reproduce a three-field split.
"""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .base import Diagram, PlotOptions, get_groups, resolve_column


# ---------------------------------------------------------------------------
# Published axes — Rollinson & Pease (2021) Appendix 5.1
# ---------------------------------------------------------------------------

#: Pearce (1976) / Vermeesch (2006a).  Every part is divided by SiO2.
PEARCE_1976_PARTS = ("Al2O3", "TiO2", "CaO", "MgO", "MnO", "K2O", "Na2O")
PEARCE_1976_DENOMINATOR = "SiO2"
PEARCE_1976_DF1 = (0.555, 3.822, 0.522, 1.293, -0.531, -0.145, -0.399)
PEARCE_1976_DF2 = (3.796, 0.008, -2.868, 0.313, 0.650, 1.421, -3.017)

#: Butler & Woronow (1986) / Vermeesch (2006a).  Every part over Ti.
BUTLER_WORONOW_PARTS = ("Zr", "Y", "Sr")
BUTLER_WORONOW_DENOMINATOR = "Ti"
BUTLER_WORONOW_DF1 = (0.016, -2.961, 1.500)
BUTLER_WORONOW_DF2 = (1.474, 2.143, 1.840)

# ---------------------------------------------------------------------------
# Field boundaries — Figure 5.5 caption.  Three straight boundaries run
# from a central point out to the given end points; each separates the
# two settings it is named for.
# ---------------------------------------------------------------------------

PEARCE_1976_FIELDS = {
    "centre": (-12.23, -1.37),
    "boundaries": (
        ((-12.0, 4.0), ("IAB", "OIB")),
        ((-8.0, -6.45), ("OIB", "MORB")),
        ((-18.0, -6.6), ("MORB", "IAB")),
    ),
    "labels": {"IAB": (-15.5, 1.5), "OIB": (-8.5, 0.5),
               "MORB": (-12.5, -5.5)},
}

BUTLER_WORONOW_FIELDS = {
    "centre": (12.17, -12.23),
    "boundaries": (
        ((15.9, -10.93), ("IAB", "OIB")),
        ((11.85, -16.0), ("OIB", "MORB")),
        ((5.02, -6.28), ("MORB", "IAB")),
    ),
    "labels": {"IAB": (13.5, -8.5), "OIB": (14.2, -14.0),
               "MORB": (8.5, -13.5)},
}

_LINE = dict(color="#444", linewidth=1.0, alpha=0.9, zorder=2)


#: 1 wt.% TiO2 = 5993.4 ppm Ti, from the mass ratio 47.867 / 79.866.
TIO2_WT_TO_TI_PPM = 5993.4


def _titanium_ppm(df: pd.DataFrame) -> Optional[pd.Series]:
    """Ti in ppm, from a Ti column or converted from TiO2 wt.%.

    The units are not cosmetic here.  Butler & Woronow's three
    coefficients sum to -1.445, so feeding Ti as wt.% instead of ppm
    shifts DF1 by -1.445 x ln(10000), about -13.3 — right across the
    diagram.
    """
    col = resolve_column(df, ("Ti",))
    if col is not None:
        return pd.to_numeric(df[col], errors="coerce")
    col = resolve_column(df, ("TiO2",))
    if col is None:
        return None
    return pd.to_numeric(df[col], errors="coerce") * TIO2_WT_TO_TI_PPM


def _column(df: pd.DataFrame, name: str, derived: dict):
    if name in derived:
        return derived[name](df)
    col = resolve_column(df, (name,))
    return None if col is None else pd.to_numeric(df[col], errors="coerce")


def _alr(df: pd.DataFrame, parts: Sequence[str], denominator: str,
         derived: Optional[dict] = None):
    """``ln(part / denominator)`` for every part, or ``None`` if any is
    missing.  Non-positive values become NaN — a log-ratio has nothing
    to say about a zero or a censored measurement."""
    derived = derived or {}
    den = _column(df, denominator, derived)
    if den is None:
        return None
    den = den.where(den > 0)
    out = []
    for part in parts:
        num = _column(df, part, derived)
        if num is None:
            return None
        out.append(np.log(num.where(num > 0) / den))
    return out


def _score(ratios, coefs) -> pd.Series:
    total = ratios[0] * coefs[0]
    for r, c in zip(ratios[1:], coefs[1:]):
        total = total + r * c
    return total


class _DFBinary(Diagram):
    """Shared plumbing for a DF1-vs-DF2 panel with three fields."""

    parts: Tuple[str, ...] = ()
    denominator: str = ""
    df1_coefs: Tuple[float, ...] = ()
    df2_coefs: Tuple[float, ...] = ()
    fields: dict = {}
    derived: dict = {}
    x_label = "DF1"
    y_label = "DF2"

    def _compute_xy(self, df):
        ratios = _alr(df, self.parts, self.denominator, self.derived)
        if ratios is None:
            return None, None
        return _score(ratios, self.df1_coefs), _score(ratios, self.df2_coefs)

    def _draw_background(self, ax, options: PlotOptions) -> None:
        cx, cy = self.fields["centre"]
        for (ex, ey), _pair in self.fields["boundaries"]:
            ax.plot([cx, ex], [cy, ey], **_LINE)
        ax.scatter([cx], [cy], marker="+", s=60, c="#444", zorder=3)
        for name, (x, y) in self.fields["labels"].items():
            ax.text(x, y, name, ha="center", va="center", fontsize=9,
                    color="#333", zorder=3)

    def _fit_axes(self, ax, df) -> None:
        """Frame the published boundaries and whatever data there is.

        A fixed window would hide a sample that falls outside it while
        the sample counter still reported it as plotted.
        """
        cx, cy = self.fields["centre"]
        xs = [cx] + [e[0] for e, _p in self.fields["boundaries"]]
        ys = [cy] + [e[1] for e, _p in self.fields["boundaries"]]
        if df is not None and not df.empty:
            dx, dy = self._compute_xy(df)
            if dx is not None:
                xs += dx.dropna().tolist()
                ys += dy.dropna().tolist()
        pad_x = max((max(xs) - min(xs)) * 0.10, 0.5)
        pad_y = max((max(ys) - min(ys)) * 0.10, 0.5)
        ax.set_xlim(min(xs) - pad_x, max(xs) + pad_x)
        ax.set_ylim(min(ys) - pad_y, max(ys) + pad_y)

    def plot(self, figure, df, plot_style, options: PlotOptions):
        figure.clear()
        ax = figure.add_subplot(111)
        self._draw_background(ax, options)
        if df is not None and not df.empty:
            xs_all, ys_all = self._compute_xy(df)
            if xs_all is not None:
                for label, sub, gs in get_groups(df, plot_style):
                    xs = xs_all.loc[sub.index]
                    ys = ys_all.loc[sub.index]
                    mask = xs.notna() & ys.notna()
                    if not mask.any():
                        continue
                    ax.scatter(xs[mask], ys[mask],
                               s=plot_style.point_size ** 2,
                               alpha=plot_style.alpha,
                               c=gs.color if gs else "#1f77b4",
                               marker=gs.marker if gs else "o",
                               label=label, edgecolors="black",
                               linewidths=0.4, zorder=5)
        ax.set_title(self.title, fontsize=11, fontweight="bold", pad=8)
        self._fit_axes(ax, df)
        self._apply_axes(ax, options)
        self._apply_legend(ax, options)
        figure.tight_layout()


class Pearce1976DF(_DFBinary):
    key = "pearce_1976_DF"
    title = "Major-element DF (no iron) — Pearce (1976) / Vermeesch (2006a)"
    citation = ("Pearce (1976), reassessed by Vermeesch (2006a).  DF1-DF2 "
                "from ln(oxide / SiO2) for Al₂O₃, TiO₂, CaO, MgO, MnO, "
                "K₂O and Na₂O — the diagram carries no iron term.  "
                "Equations from Rollinson & Pease (2021) Appendix 5.1; "
                "field boundaries from the Fig. 5.5 caption.  About 7 % "
                "of the trial data are misclassified.")
    parts = PEARCE_1976_PARTS
    denominator = PEARCE_1976_DENOMINATOR
    df1_coefs = PEARCE_1976_DF1
    df2_coefs = PEARCE_1976_DF2
    fields = PEARCE_1976_FIELDS


class ButlerWoronowDF(_DFBinary):
    key = "butler_woronow_DF"
    title = "Zr − Y − Sr − Ti DF — Butler & Woronow (1986) / Vermeesch (2006a)"
    citation = ("Butler & Woronow (1986), reassessed by Vermeesch "
                "(2006a).  DF1-DF2 from ln(Zr/Ti), ln(Y/Ti) and "
                "ln(Sr/Ti), all in ppm.  Equations from Rollinson & "
                "Pease (2021) Appendix 5.1; field boundaries from the "
                "Fig. 5.5 caption.  Sr is mobile — keep this one for "
                "unaltered rocks.  CAUTION: the book's own equations "
                "and its figure axes disagree here.  Reference "
                "basalts put through the printed equations land about "
                "13 DF2 units below the printed field boundaries, and "
                "no change of units closes the gap; their relative "
                "arrangement (MORB left, OIB lower right, IAB upper "
                "right) is right, so the offset sits in the boundary "
                "coordinates rather than the axes.  Read the "
                "separation, not the field name, until Vermeesch "
                "(2006a) itself has been checked.")
    parts = BUTLER_WORONOW_PARTS
    denominator = BUTLER_WORONOW_DENOMINATOR
    df1_coefs = BUTLER_WORONOW_DF1
    df2_coefs = BUTLER_WORONOW_DF2
    fields = BUTLER_WORONOW_FIELDS
    derived = {"Ti": _titanium_ppm}


# ---------------------------------------------------------------------------
# Scores as plain functions, for the statistics tables
# ---------------------------------------------------------------------------

def _axis(parts, denominator, coefs, derived=None):
    def compute(df: pd.DataFrame) -> Optional[pd.Series]:
        ratios = _alr(df, parts, denominator, derived)
        return None if ratios is None else _score(ratios, coefs)
    return compute


pearce_1976_df1 = _axis(PEARCE_1976_PARTS, PEARCE_1976_DENOMINATOR,
                        PEARCE_1976_DF1)
pearce_1976_df2 = _axis(PEARCE_1976_PARTS, PEARCE_1976_DENOMINATOR,
                        PEARCE_1976_DF2)
butler_woronow_df1 = _axis(BUTLER_WORONOW_PARTS, BUTLER_WORONOW_DENOMINATOR,
                           BUTLER_WORONOW_DF1, {"Ti": _titanium_ppm})
butler_woronow_df2 = _axis(BUTLER_WORONOW_PARTS, BUTLER_WORONOW_DENOMINATOR,
                           BUTLER_WORONOW_DF2, {"Ti": _titanium_ppm})
