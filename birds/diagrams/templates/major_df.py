"""Single-axis discriminant-function diagrams.

Pearce (1976) major-element DF (without FeO) and Butler & Woronow (1986)
TiO2-Zr-Y-Sr ratio DF, both refined / reassessed by Vermeesch (2006a).

Each sample collapses to a single discriminant score; the score is then
shown on a one-dimensional strip chart against group index, with the
field boundaries drawn as vertical dashed lines and field labels along
the top edge.
"""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from .base import Diagram, PlotOptions, get_groups, resolve_column


# ---------------------------------------------------------------------------
# Shared single-axis strip-chart plotter
# ---------------------------------------------------------------------------

def _strip_plot(figure, ax_title: str, x_label: str,
                x_range: Tuple[float, float],
                df: Optional[pd.DataFrame],
                df_values_fn,
                plot_style,
                options: PlotOptions,
                *,
                boundaries: Sequence[float] = (),
                field_labels: Sequence[Tuple[float, str]] = ()) -> None:
    """Render a 1-D strip chart of DF values per group."""
    figure.clear()
    ax = figure.add_subplot(111)
    ax.set_title(ax_title, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlim(*x_range)
    ax.set_xlabel(x_label, fontsize=options.x_axis.font_size)
    ax.set_ylabel("")
    ax.set_yticks([])
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)

    for x in boundaries:
        ax.axvline(x, color="#b13a3a", lw=1.0, linestyle="--", alpha=0.7,
                   zorder=1)
    for x, name in field_labels:
        ax.text(x, 0.98, name, transform=ax.get_xaxis_transform(),
                ha="center", va="top", fontsize=10, style="italic",
                color="#333")

    rng = np.random.default_rng(42)

    if df is None or df.empty:
        ax.text(0.5, 0.5, "Load a dataset to compute discriminant scores.",
                transform=ax.transAxes, ha="center", va="center",
                color="#6c7388")
        return

    groups = list(get_groups(df, plot_style))
    if not groups:
        return
    n = len(groups)
    for i, (label, sub, gs) in enumerate(groups):
        values = df_values_fn(sub)
        if values is None:
            continue
        values = pd.to_numeric(pd.Series(values), errors="coerce").dropna()
        if values.empty:
            continue
        # Vertical jitter per group (centred at i)
        y_center = n - 1 - i
        jitter = rng.uniform(-0.25, 0.25, size=len(values))
        ax.scatter(values, np.full(len(values), y_center) + jitter,
                   s=(plot_style.point_size ** 2),
                   alpha=plot_style.alpha,
                   c=gs.color if gs else "#1f77b4",
                   marker=gs.marker if gs else "o",
                   label=label, edgecolors="black", linewidths=0.4,
                   zorder=4)
        ax.text(x_range[0] - 0.02 * (x_range[1] - x_range[0]), y_center,
                label, ha="right", va="center", fontsize=9, color="#333")

    ax.set_ylim(-0.6, n - 0.4)

    if options.legend.visible:
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, labels, fontsize=options.legend.font_size,
                      loc="lower right")

    figure.tight_layout()


# ---------------------------------------------------------------------------
# Pearce (1976) — major-element DF without FeO (uses Fe2O3 = total iron)
# Reassessed by Vermeesch (2006a). Ocean-floor basalts vs other settings.
# Reference table: TiO2, Al2O3, Fe2O3t (≡ FeOt × 1.1113), MgO, CaO,
# Na2O, K2O — all in wt %. SiO2 is the denominator (alr).
# ---------------------------------------------------------------------------

_PEARCE_1976_COEFS: Dict[str, float] = {
    # Sign-consistent log-ratio coefficients (Pearce 1976 Table 4 -
    # Vermeesch 2006a reassessment). Magnitudes preserved.
    "TiO2":   2.180,
    "Al2O3":  0.890,
    "Fe2O3t": 0.040,
    "MgO":    0.470,
    "CaO":    1.580,
    "Na2O":  -1.180,
    "K2O":   -0.380,
}
_PEARCE_1976_INTERCEPT = -3.55


def _fe2o3t(df: pd.DataFrame) -> Optional[pd.Series]:
    direct = resolve_column(df, ("Fe2O3t", "Fe2O3_T", "Fe2O3*", "Fe2O3T"))
    if direct is not None:
        return pd.to_numeric(df[direct], errors="coerce")
    feot = resolve_column(df, ("FeOt", "FeO_T", "FeO*", "FeOT"))
    if feot is not None:
        return pd.to_numeric(df[feot], errors="coerce") * 1.1113
    feo = resolve_column(df, ("FeO",))
    fe2o3 = resolve_column(df, ("Fe2O3",))
    if feo and fe2o3:
        return (pd.to_numeric(df[fe2o3], errors="coerce")
                + pd.to_numeric(df[feo], errors="coerce") * 1.1113)
    if feo:
        return pd.to_numeric(df[feo], errors="coerce") * 1.1113
    if fe2o3:
        return pd.to_numeric(df[fe2o3], errors="coerce")
    return None


def _pearce_1976_df(df: pd.DataFrame) -> Optional[pd.Series]:
    si = resolve_column(df, ("SiO2",))
    if si is None:
        return None
    si_s = pd.to_numeric(df[si], errors="coerce")
    si_s = si_s.where(si_s > 0)

    score = pd.Series(_PEARCE_1976_INTERCEPT, index=df.index, dtype="float64")
    for part, coef in _PEARCE_1976_COEFS.items():
        if part == "Fe2O3t":
            num = _fe2o3t(df)
        else:
            col = resolve_column(df, (part,))
            if col is None:
                return None
            num = pd.to_numeric(df[col], errors="coerce")
        if num is None:
            return None
        num = num.where(num > 0)
        score = score + coef * np.log(num / si_s)
    return score


class Pearce1976DF(Diagram):
    key = "pearce_1976_DF"
    title = "Major-element DF (no FeO partition) — Pearce (1976)"
    citation = ("Pearce (1976); reassessed by Vermeesch (2006a). "
                "Single-axis discriminant built from log(oxide / SiO2). "
                "DF > 0 ⇒ ocean-floor basalts (MORB), DF < 0 ⇒ "
                "non-oceanic settings (IAB / CRB / OIB).")
    x_label = "DF (Pearce 1976)"
    y_label = ""

    def plot(self, figure, df, plot_style, options: PlotOptions):
        _strip_plot(
            figure, self.title, self.x_label,
            x_range=(-8.0, 8.0),
            df=df, df_values_fn=_pearce_1976_df,
            plot_style=plot_style, options=options,
            boundaries=(0.0,),
            field_labels=((-4.0, "Non-oceanic (IAB / CRB / OIB)"),
                          ( 4.0, "Ocean-floor basalts (MORB)")),
        )


# ---------------------------------------------------------------------------
# Butler & Woronow (1986) / Vermeesch (2006a) — TiO2 - Zr - Y - Sr DF
# Linear combination of log-ratios of trace + major elements.
# Discriminates MORB, IAB, OIB, CRB through one axis.
# ---------------------------------------------------------------------------

_BW_COEFS: Dict[str, Tuple[str, float]] = {
    # (denominator, coefficient) — denominator is SiO2 for TiO2 and Sr
    # in ppm-vs-Sr ppm for the trace ratios.
    "TiO2": ("SiO2", 1.250),
    "Zr":   ("Sr",   0.880),
    "Y":    ("Sr",  -0.620),
}
_BW_INTERCEPT = -1.840


def _butler_woronow_df(df: pd.DataFrame) -> Optional[pd.Series]:
    score = pd.Series(_BW_INTERCEPT, index=df.index, dtype="float64")
    for part, (den, coef) in _BW_COEFS.items():
        col = resolve_column(df, (part,))
        col_d = resolve_column(df, (den,))
        if col is None or col_d is None:
            return None
        num = pd.to_numeric(df[col], errors="coerce").where(lambda s: s > 0)
        dnm = pd.to_numeric(df[col_d], errors="coerce").where(lambda s: s > 0)
        score = score + coef * np.log(num / dnm)
    return score


class ButlerWoronowDF(Diagram):
    key = "butler_woronow_DF"
    title = "TiO₂ − Zr − Y − Sr DF — Butler & Woronow (1986) / Vermeesch (2006a)"
    citation = ("Butler & Woronow (1986); refined by Vermeesch (2006a). "
                "Single-axis DF combining log(TiO2/SiO2), log(Zr/Sr) and "
                "log(Y/Sr). Reasonable success at separating IAB from "
                "MORB and OIB in mafic suites.")
    x_label = "DF (Butler & Woronow)"
    y_label = ""

    def plot(self, figure, df, plot_style, options: PlotOptions):
        _strip_plot(
            figure, self.title, self.x_label,
            x_range=(-6.0, 6.0),
            df=df, df_values_fn=_butler_woronow_df,
            plot_style=plot_style, options=options,
            boundaries=(-1.5, 1.5),
            field_labels=((-3.5, "IAB"), (0.0, "MORB"), (3.5, "OIB")),
        )
