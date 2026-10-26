"""Statistics, REE anomalies, trace-element ratios and I/O helpers.

Chondrite normalising values follow Sun & McDonough (1989), the de-facto
standard used by Saccani 2015 and by most multi-element software. Adding
alternative reference suites (Boynton 1984, Palme & O'Neill 2014, Barrat
et al. 2012, Pourmand et al. 2012, McDonough & Sun 1995) is a future
extension – the engine is structured to accept any dict-shaped normaliser.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Mapping, Optional

import numpy as np
import pandas as pd
from scipy import stats as _scipy_stats

from .normalizations import (
    MULTIELEMENT_NORMS,
    OXIDE_TO_ELEMENT_PPM,
    REE_CHONDRITES,
    TIO2_WT_TO_TI_PPM,
    get_normaliser as _get_normaliser,
)


# ---------------------------------------------------------------------------
# Reference compositions
# ---------------------------------------------------------------------------

CHONDRITE_SUN_MCDONOUGH_1989: Mapping[str, float] = {
    "La": 0.2370, "Ce": 0.6120, "Pr": 0.0950, "Nd": 0.4670, "Sm": 0.1530,
    "Eu": 0.0580, "Gd": 0.2055, "Tb": 0.0374, "Dy": 0.2540, "Ho": 0.0566,
    "Er": 0.1655, "Tm": 0.0255, "Yb": 0.1700, "Lu": 0.0254,  "Y": 1.5700,
}

# Primitive-mantle reference used by the Nb / Ta / Ti anomalies. These
# anomalies are conventionally read off a PM-normalised multi-element
# spider diagram, not a chondrite-normalised REE pattern, so we pick the
# PM column from the multi-element normaliser table.
_PRIMITIVE_MANTLE: Mapping[str, float] = MULTIELEMENT_NORMS[
    "Primitive Mantle (McDonough & Sun 1995)"
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    """Return the actual column name in *df* matching any of *candidates*
    case-insensitively."""
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for name in candidates:
        actual = lookup.get(name.lower())
        if actual is not None:
            return actual
    return None


def _element_ppm(df: pd.DataFrame, symbol: str) -> Optional[pd.Series]:
    """*symbol* in ppm: its own column, or for a major element reported
    only as an oxide, the oxide converted -- Ti from TiO2 × 5993.4, as
    the discrimination diagrams and the spider diagrams convert it.
    Without this a dataset carrying TiO2 but no Ti column had no Ti/Y,
    Ti/V or Ti/Ti*, though every diagram plotted its Ti."""
    col = _resolve_column(df, [symbol])
    if col is not None:
        return pd.to_numeric(df[col], errors="coerce")
    if symbol in OXIDE_TO_ELEMENT_PPM:
        oxide, factor = OXIDE_TO_ELEMENT_PPM[symbol]
        oxide_col = _resolve_column(df, [oxide])
        if oxide_col is not None:
            return pd.to_numeric(df[oxide_col], errors="coerce") * factor
    return None


# ---------------------------------------------------------------------------
# Computations
# ---------------------------------------------------------------------------

def compute_descriptive(df: pd.DataFrame) -> pd.DataFrame:
    """Return a per-column descriptive statistics table (count/mean/std/…)."""
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return pd.DataFrame()
    return numeric.describe().T.round(4)


def compute_descriptive_full(df: pd.DataFrame) -> pd.DataFrame:
    """Extended descriptive statistics including robust measures.

    Adds median, MAD (median absolute deviation), %RSD, skewness and
    kurtosis to the standard ``describe()`` output.
    """
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return pd.DataFrame()
    base = numeric.describe().T
    mean = numeric.mean()
    median = numeric.median()
    base["median"] = median
    base["MAD"] = (numeric - median).abs().median()
    with np.errstate(divide="ignore", invalid="ignore"):
        base["%RSD"] = (numeric.std() / mean * 100).replace([np.inf, -np.inf], np.nan)
    base["skewness"] = numeric.apply(
        lambda x: _scipy_stats.skew(x.dropna(), bias=False) if x.dropna().size > 2 else np.nan
    )
    base["kurtosis"] = numeric.apply(
        lambda x: _scipy_stats.kurtosis(x.dropna(), bias=False) if x.dropna().size > 3 else np.nan
    )
    return base.round(4)


def compute_descriptive_by_group(
    df: pd.DataFrame, group_columns: Optional[List[str]] = None
) -> pd.DataFrame:
    """Per-group descriptive statistics.

    Returns a multi-indexed DataFrame with rows = group labels and columns
    indexed by (element, statistic). If no group_columns are given (or none
    are present in the data) an empty DataFrame is returned.
    """
    if not group_columns:
        return pd.DataFrame()
    present = [c for c in group_columns if c in df.columns]
    if not present:
        return pd.DataFrame()
    numeric = df.select_dtypes(include="number")
    if numeric.empty:
        return pd.DataFrame()

    if len(present) == 1:
        label = df[present[0]].astype("string")
    else:
        label = df[present].astype("string").fillna("NA").agg(" | ".join, axis=1)
    label.name = "Group"

    groups = numeric.groupby(label, dropna=True)
    summary = groups.agg(["count", "mean", "std", "median"])
    return summary.round(4)


# ---------------------------------------------------------------------------
# Publication-ready summary table
# ---------------------------------------------------------------------------

def _sig_round(value: float, sig: int) -> float:
    """Round *value* to *sig* significant figures."""
    if not np.isfinite(value) or value == 0:
        return 0.0
    exponent = int(np.floor(np.log10(abs(value))))
    return round(value, -(exponent - sig + 1))


def _decimals_for(value: float, sig: int) -> int:
    """Number of decimal places needed to show *value* to *sig* sig-figs."""
    if not np.isfinite(value) or value == 0:
        return 2
    exponent = int(np.floor(np.log10(abs(value))))
    return max(0, sig - 1 - exponent)


def format_mean_sd(mean: float, sd: float, n: int,
                   sd_sig: int = 2, fallback_sig: int = 3) -> str:
    """Format one cell as ``mean ± sd`` with uncertainty-driven rounding.

    The convention every journal expects: round the standard deviation
    to *sd_sig* significant figures, then quote the mean to the SAME
    decimal place.  ``52.337 ± 1.4213`` becomes ``52.3 ± 1.4``;
    ``0.02341 ± 0.00187`` becomes ``0.0234 ± 0.0019``.

    Degenerate cases:

    * ``n == 0`` or a non-finite mean → ``"n.d."`` (not determined);
    * ``n == 1`` (or sd is 0 / non-finite) → the mean alone, quoted to
      *fallback_sig* significant figures, with no ± term.
    """
    if n == 0 or mean is None or not np.isfinite(mean):
        return "n.d."
    if n == 1 or sd is None or not np.isfinite(sd) or sd == 0:
        dec = _decimals_for(mean, fallback_sig)
        return f"{mean:.{dec}f}"
    sd_r = _sig_round(sd, sd_sig)
    dec = _decimals_for(sd_r, sd_sig)
    return f"{mean:.{dec}f} ± {sd_r:.{dec}f}"


def _group_labels(df: pd.DataFrame,
                  group_columns: Optional[List[str]]) -> Optional[pd.Series]:
    """Combined group label per row, or None when no grouping applies."""
    if not group_columns:
        return None
    present = [c for c in group_columns if c in df.columns]
    if not present:
        return None
    if len(present) == 1:
        return df[present[0]].astype("string")
    return df[present].astype("string").fillna("NA").agg(" | ".join, axis=1)


def compute_paper_table(
    df: pd.DataFrame,
    group_columns: Optional[List[str]] = None,
    variables: Optional[List[str]] = None,
    group_order: Optional[List[str]] = None,
    sd_sig: int = 2,
) -> pd.DataFrame:
    """Build a publication-ready ``mean ± 1σ (n)`` summary table.

    Rows are the numeric variables (oxides, traces, ratios…), columns
    are the sample groups, and the first row reports the group size.
    Every cell is already a formatted string, so the frame can be
    pasted straight into a manuscript or handed to
    :func:`paper_table_to_latex` / :func:`paper_table_to_markdown`.

    * *group_columns* — the grouping columns (usually
      ``plot_style.group_columns``).  With no grouping the table gets a
      single ``All samples`` column.
    * *variables* — restrict / order the rows; defaults to every numeric
      column in *df*.
    * *group_order* — order the columns (usually the user's group order
      from Edit plot); unknown labels are appended alphabetically.

    ``n`` is the count of **finite** values for that variable in that
    group, which is what a reader needs — it can legitimately differ
    from the group size when a sample lacks one element.
    """
    numeric = df.select_dtypes(include="number")
    if variables:
        keep = [v for v in variables if v in numeric.columns]
        numeric = numeric[keep] if keep else numeric.iloc[:, :0]
    if numeric.empty:
        return pd.DataFrame()

    labels = _group_labels(df, group_columns)
    if labels is None:
        buckets = {"All samples": numeric}
    else:
        uniques = [u for u in pd.unique(labels.dropna())]
        if group_order:
            ordered = [g for g in group_order if g in uniques]
            ordered += sorted(u for u in uniques if u not in ordered)
        else:
            ordered = sorted(uniques)
        buckets = {str(g): numeric[labels == g] for g in ordered}

    rows: dict[str, dict[str, str]] = {}
    n_row: dict[str, str] = {}
    for gname, sub in buckets.items():
        n_row[gname] = str(len(sub))
    rows["n (samples)"] = n_row

    for var in numeric.columns:
        cells: dict[str, str] = {}
        for gname, sub in buckets.items():
            series = pd.to_numeric(sub[var], errors="coerce").dropna()
            cell = format_mean_sd(
                float(series.mean()) if len(series) else np.nan,
                float(series.std(ddof=1)) if len(series) > 1 else np.nan,
                len(series), sd_sig=sd_sig,
            )
            # Only annotate n when this variable was measured on fewer
            # samples than the group holds — otherwise the header n row
            # already says it and repeating it clutters the table.
            if cell != "n.d." and len(series) != len(sub):
                cell = f"{cell} (n={len(series)})"
            cells[gname] = cell
        rows[str(var)] = cells

    table = pd.DataFrame.from_dict(rows, orient="index")
    table.index.name = "Variable"
    return table


def paper_table_to_markdown(table: pd.DataFrame) -> str:
    """Render a :func:`compute_paper_table` frame as a pipe table."""
    if table is None or table.empty:
        return ""
    cols = list(table.columns)
    head = "| " + " | ".join([str(table.index.name or "Variable")] + cols) + " |"
    rule = "|" + "|".join(["---"] * (len(cols) + 1)) + "|"
    body = [
        "| " + " | ".join([str(idx)] + [str(row[c]) for c in cols]) + " |"
        for idx, row in table.iterrows()
    ]
    return "\n".join([head, rule] + body)


def paper_table_to_latex(table: pd.DataFrame,
                         caption: str = "Major- and trace-element summary.",
                         label: str = "tab:geochem") -> str:
    """Render a :func:`compute_paper_table` frame as a booktabs table.

    ``±`` becomes ``$\\pm$`` and the whole table is wrapped in a
    ``table`` float, ready to drop into a manuscript.  Requires
    ``\\usepackage{booktabs}``.
    """
    if table is None or table.empty:
        return ""
    cols = list(table.columns)
    align = "l" + "c" * len(cols)
    esc = lambda s: (str(s).replace("±", r"$\pm$")
                     .replace("#", r"\#").replace("_", r"\_")
                     .replace("%", r"\%"))
    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        f"  \\caption{{{esc(caption)}}}",
        f"  \\label{{{label}}}",
        f"  \\begin{{tabular}}{{{align}}}",
        r"    \toprule",
        "    " + " & ".join([esc(table.index.name or "Variable")]
                            + [esc(c) for c in cols]) + r" \\",
        r"    \midrule",
    ]
    for idx, row in table.iterrows():
        lines.append("    " + " & ".join([esc(idx)]
                                          + [esc(row[c]) for c in cols])
                     + r" \\")
    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
    ]
    return "\n".join(lines)


def compute_anomalies(
    df: pd.DataFrame, normaliser: Mapping[str, float] | None = None
) -> pd.DataFrame:
    """Compute per-sample Eu/Eu* and Ce/Ce* using a chondrite normalisation.

    Eu/Eu* = Eu_N / sqrt(Sm_N * Gd_N)            (Taylor & McLennan, 1985)
    Ce/Ce* = Ce_N / sqrt(La_N * Pr_N)
    """
    n = normaliser or CHONDRITE_SUN_MCDONOUGH_1989
    out = pd.DataFrame(index=df.index)

    sm = _resolve_column(df, ["Sm"])
    eu = _resolve_column(df, ["Eu"])
    gd = _resolve_column(df, ["Gd"])
    if sm and eu and gd:
        with np.errstate(invalid="ignore", divide="ignore"):
            sm_n = pd.to_numeric(df[sm], errors="coerce") / n["Sm"]
            eu_n = pd.to_numeric(df[eu], errors="coerce") / n["Eu"]
            gd_n = pd.to_numeric(df[gd], errors="coerce") / n["Gd"]
            eu_star = np.sqrt(sm_n * gd_n)
            out["Eu/Eu*"] = (eu_n / eu_star).round(4)

    la = _resolve_column(df, ["La"])
    ce = _resolve_column(df, ["Ce"])
    pr = _resolve_column(df, ["Pr"])
    if la and ce and pr:
        with np.errstate(invalid="ignore", divide="ignore"):
            la_n = pd.to_numeric(df[la], errors="coerce") / n["La"]
            ce_n = pd.to_numeric(df[ce], errors="coerce") / n["Ce"]
            pr_n = pd.to_numeric(df[pr], errors="coerce") / n["Pr"]
            ce_star = np.sqrt(la_n * pr_n)
            out["Ce/Ce*"] = (ce_n / ce_star).round(4)

    return out


def compute_anomalies_extended(
    df: pd.DataFrame, normaliser_name: Optional[str] = None
) -> pd.DataFrame:
    """All REE anomalies + normalised REE summary ratios per sample.

    Computes the following indices per sample:

    REE anomalies (chondrite-normalised):
        * Eu/Eu* = Eu_N / sqrt(Sm_N · Gd_N)
        * Ce/Ce* = Ce_N / sqrt(La_N · Pr_N)
        * Pr/Pr* = Pr_N / sqrt(Ce_N · Nd_N)
        * Gd/Gd* = Gd_N / sqrt(Sm_N · Tb_N)
        * Dy/Dy* = Dy_N / sqrt(Tb_N · Ho_N)
        * Y/Y*   = Y_N  / sqrt(Dy_N · Ho_N)

    Multi-element anomalies (PM-normalised, geometric mean):
        * Ta/Ta* = Ta_PM / sqrt(Nb_PM · La_PM)
        * Ti/Ti* = Ti_PM / sqrt(Eu_PM · Gd_PM)
        * Nb/Nb* = Nb_PM / sqrt(Th_PM · La_PM)   (Pearce 2008)

    Verma (2015) HFSE anomalies (arithmetic mean of Ba and La):
        * Nb/Nb*_V(PM) = 2 · Nb_PM / (Ba_PM + La_PM)
        * Ta/Ta*_V(PM) = 2 · Ta_PM / (Ba_PM + La_PM)
        * Nb/Nb*_V(CN) = 2 · Nb_CN / (Ba_CN + La_CN)   (CI Chondrite)
        * Ta/Ta*_V(CN) = 2 · Ta_CN / (Ba_CN + La_CN)

    Plus the raw Y/Ho ratio (chondritic ≈ 28) and the chondrite-
    normalised summary ratios (La/Yb)_N, (La/Sm)_N, (Gd/Yb)_N and
    (Sm/Yb)_N.

    Ti is the Ti column, or TiO2 × 5993.4 when there is none -- so pass
    the majors the diagrams read (``DataManager.majors_df``) for Ti/Ti*
    to follow the adjusted-majors switch.

    ``normaliser_name`` can be the name of any REE chondrite reference
    registered in :mod:`birds.normalizations`. Defaults to Sun &
    McDonough (1989).
    """
    n = None
    if normaliser_name:
        n = _get_normaliser(normaliser_name)
    if n is None:
        n = CHONDRITE_SUN_MCDONOUGH_1989

    out = pd.DataFrame(index=df.index)

    def normed(symbol):
        col = _resolve_column(df, [symbol])
        if col is None or symbol not in n:
            return None
        with np.errstate(invalid="ignore", divide="ignore"):
            return pd.to_numeric(df[col], errors="coerce") / n[symbol]

    la_n = normed("La"); ce_n = normed("Ce"); pr_n = normed("Pr")
    nd_n = normed("Nd"); sm_n = normed("Sm"); eu_n = normed("Eu")
    gd_n = normed("Gd"); tb_n = normed("Tb"); dy_n = normed("Dy")
    ho_n = normed("Ho"); yb_n = normed("Yb"); y_n = normed("Y")

    def _safe(num, den):
        with np.errstate(invalid="ignore", divide="ignore"):
            return num / den

    if all(x is not None for x in (sm_n, eu_n, gd_n)):
        out["Eu/Eu*"] = _safe(eu_n, np.sqrt(sm_n * gd_n)).round(4)
    if all(x is not None for x in (la_n, ce_n, pr_n)):
        out["Ce/Ce*"] = _safe(ce_n, np.sqrt(la_n * pr_n)).round(4)
    if all(x is not None for x in (ce_n, pr_n, nd_n)):
        out["Pr/Pr*"] = _safe(pr_n, np.sqrt(ce_n * nd_n)).round(4)
    if all(x is not None for x in (sm_n, gd_n, tb_n)):
        out["Gd/Gd*"] = _safe(gd_n, np.sqrt(sm_n * tb_n)).round(4)
    if all(x is not None for x in (tb_n, dy_n, ho_n)):
        # Dy/Dy* uses Tb-Ho as immediate neighbours in the lanthanide
        # pattern (Tb → Dy → Ho).  Sensitive to MREE depletion / garnet
        # fractionation.
        out["Dy/Dy*"] = _safe(dy_n, np.sqrt(tb_n * ho_n)).round(4)
    if all(x is not None for x in (dy_n, y_n, ho_n)):
        out["Y/Y*"] = _safe(y_n, np.sqrt(dy_n * ho_n)).round(4)

    # Raw Y/Ho ratio (chondritic ≈ 28)
    y_col = _resolve_column(df, ["Y"])
    ho_col = _resolve_column(df, ["Ho"])
    if y_col and ho_col:
        with np.errstate(invalid="ignore", divide="ignore"):
            out["Y/Ho"] = (
                pd.to_numeric(df[y_col], errors="coerce")
                / pd.to_numeric(df[ho_col], errors="coerce")
            ).round(3)

    # ----- Multi-element anomalies (PM-normalised) ----------------------
    # Ta/Ta* and Ti/Ti* live on the spider diagram, not on the REE
    # pattern, so they use Sun & McDonough (1989) primitive mantle
    # rather than the chondrite normaliser picked above.
    def normed_pm(symbol):
        values = _element_ppm(df, symbol)
        if values is None or symbol not in _PRIMITIVE_MANTLE:
            return None
        with np.errstate(invalid="ignore", divide="ignore"):
            return values / _PRIMITIVE_MANTLE[symbol]

    nb_pm = normed_pm("Nb"); ta_pm = normed_pm("Ta"); la_pm = normed_pm("La")
    ti_pm = normed_pm("Ti"); eu_pm = normed_pm("Eu"); gd_pm = normed_pm("Gd")
    th_pm = normed_pm("Th")
    if all(x is not None for x in (nb_pm, ta_pm, la_pm)):
        # Ta/Ta* = Ta_PM / sqrt(Nb_PM × La_PM) — neighbours of Ta on the
        # Sun & McDonough (1989) multi-element ordering.
        out["Ta/Ta*"] = _safe(ta_pm, np.sqrt(nb_pm * la_pm)).round(4)
    if all(x is not None for x in (nb_pm, th_pm, la_pm)):
        # Nb/Nb* = Nb_PM / sqrt(Th_PM × La_PM) — Pearce (2008).  The
        # canonical "Nb-negative anomaly" of arc magmas: values < 1 are
        # diagnostic of slab-derived flux, values ≈ 1 of OIB / intra-
        # plate sources.  Th and La are used as anchors (skipping U/Ta)
        # because they have similar incompatibility to Nb in a sub-arc
        # mantle and provide a clean LILE/LREE background.
        out["Nb/Nb*"] = _safe(nb_pm, np.sqrt(th_pm * la_pm)).round(4)
    if all(x is not None for x in (ti_pm, eu_pm, gd_pm)):
        # Ti/Ti* = Ti_PM / sqrt(Eu_PM × Gd_PM) — diagnostic of titanite /
        # Fe-Ti oxide fractionation and of HFSE depletion in arc magmas.
        out["Ti/Ti*"] = _safe(ti_pm, np.sqrt(eu_pm * gd_pm)).round(4)

    # ----- Verma (2015) Nb/Nb* and Ta/Ta* anomalies ----------------------
    # Alternative formulation using the ARITHMETIC mean of Ba and La as
    # the denominator instead of the geometric mean of Th-La (Pearce 2008)
    # or Nb-La (canonical Ta/Ta*).  Verma argues Ba+La gives a more
    # robust LILE/LREE anchor when Th is altered, and it is the standard
    # in the multi-dimensional discrimination diagrams of his group
    # (Verma et al. 2015–2017).  Computed against BOTH Primitive Mantle
    # (PM) and CI Chondrite (CN) so the user can pick the convention
    # used in their target paper.
    ba_pm = normed_pm("Ba")
    if all(x is not None for x in (nb_pm, ba_pm, la_pm)):
        # Nb/Nb*_V(PM) = 2 · Nb_PM / (Ba_PM + La_PM)
        out["Nb/Nb*_V(PM)"] = _safe(
            2.0 * nb_pm, ba_pm + la_pm
        ).round(4)
    if all(x is not None for x in (ta_pm, ba_pm, la_pm)):
        # Ta/Ta*_V(PM) = 2 · Ta_PM / (Ba_PM + La_PM)
        out["Ta/Ta*_V(PM)"] = _safe(
            2.0 * ta_pm, ba_pm + la_pm
        ).round(4)

    # CI Chondrite version — uses the multi-element CN reference (which
    # contains Ba, Nb, Ta, La) rather than the REE-only chondrite picked
    # by ``normaliser_name``.  Falls back silently when the CN ref is
    # absent from the catalogue (e.g. a custom build that stripped it).
    _CN = MULTIELEMENT_NORMS.get("CI Chondrite (McDonough & Sun 1995)")
    if _CN is not None:
        def normed_cn(symbol):
            col = _resolve_column(df, [symbol])
            if col is None or symbol not in _CN:
                return None
            with np.errstate(invalid="ignore", divide="ignore"):
                return pd.to_numeric(df[col], errors="coerce") / _CN[symbol]

        nb_cn = normed_cn("Nb"); ta_cn = normed_cn("Ta")
        ba_cn = normed_cn("Ba"); la_cn = normed_cn("La")
        if all(x is not None for x in (nb_cn, ba_cn, la_cn)):
            out["Nb/Nb*_V(CN)"] = _safe(
                2.0 * nb_cn, ba_cn + la_cn
            ).round(4)
        if all(x is not None for x in (ta_cn, ba_cn, la_cn)):
            out["Ta/Ta*_V(CN)"] = _safe(
                2.0 * ta_cn, ba_cn + la_cn
            ).round(4)

    # Normalised REE summary ratios
    if la_n is not None and yb_n is not None:
        out["(La/Yb)N"] = _safe(la_n, yb_n).round(3)
    if la_n is not None and sm_n is not None:
        out["(La/Sm)N"] = _safe(la_n, sm_n).round(3)
    if gd_n is not None and yb_n is not None:
        out["(Gd/Yb)N"] = _safe(gd_n, yb_n).round(3)
    if sm_n is not None and yb_n is not None:
        out["(Sm/Yb)N"] = _safe(sm_n, yb_n).round(3)

    return out


def compute_correlation_matrix(
    df: pd.DataFrame,
    columns: Optional[Iterable[str]] = None,
    method: str = "pearson",
    max_cols: int = 30,
) -> pd.DataFrame:
    """Return the correlation matrix of numeric columns.

    Parameters
    ----------
    df
        Input dataset.
    columns
        Explicit subset of column names to use. When ``None`` (default),
        every numeric column with enough variance is included, capped at
        ``max_cols`` (preferring the ones with most non-null values).
        When given, ``max_cols`` is ignored — the user is in control.
    method
        Correlation method passed to :func:`pandas.DataFrame.corr`:
        ``"pearson"``, ``"spearman"`` or ``"kendall"``.
    max_cols
        Soft cap used only when ``columns`` is ``None``.
    """
    numeric = df.select_dtypes(include="number")
    if numeric.shape[1] < 2:
        return pd.DataFrame()

    if columns is None:
        # Drop columns that are entirely NaN or constant
        keep = [c for c in numeric.columns
                if numeric[c].notna().sum() > 1
                and numeric[c].nunique(dropna=True) > 1]
        sub = numeric[keep]
        if sub.shape[1] > max_cols:
            order = sub.notna().sum().sort_values(ascending=False)
            sub = sub[order.index[:max_cols]]
    else:
        wanted = [c for c in columns if c in numeric.columns]
        if len(wanted) < 2:
            return pd.DataFrame()
        sub = numeric[wanted]

    if sub.shape[1] < 2:
        return pd.DataFrame()
    return sub.corr(method=method).round(3)


def available_normalisers() -> list[str]:
    """Return the names of REE chondrite normalisers from
    :mod:`birds.normalizations`."""
    return list(REE_CHONDRITES.keys())


# (Numerator, denominator) pairs collected from Rollinson & Pease (2021)
# Table 4.11 and Pearce (2008). Any pair where one element is absent from
# the dataset is silently skipped.
RATIO_DEFINITIONS: tuple[tuple[str, str, str], ...] = (
    # Light → heavy REE ratios (LREE/HREE fractionation, garnet residue)
    ("La/Yb",  "La",  "Yb"),
    ("La/Sm",  "La",  "Sm"),
    ("Gd/Yb",  "Gd",  "Yb"),
    ("Ce/Yb",  "Ce",  "Yb"),
    ("Sm/Yb",  "Sm",  "Yb"),
    ("Dy/Yb",  "Dy",  "Yb"),  # MREE/HREE — sensitive to garnet
    ("Dy/Y",   "Dy",  "Y"),   # geochemical twin pair (chondritic ≈ 0.18)
    # HFSE pairs (source / fluid-mobility indicators)
    ("Zr/Hf",  "Zr",  "Hf"),  # chondritic ≈ 36; HFSE pair, near-conservative
    ("Nb/Ta",  "Nb",  "Ta"),  # chondritic ≈ 17.5; differentiates crust vs OIB
    ("Zr/Y",   "Zr",  "Y"),
    ("Zr/Nb",  "Zr",  "Nb"),
    ("Nb/Y",   "Nb",  "Y"),
    ("Nb/Yb",  "Nb",  "Yb"),
    # LILE / Th / Ti diagnostics
    ("Th/Yb",  "Th",  "Yb"),
    ("Th/Nb",  "Th",  "Nb"),
    ("Ti/Y",   "Ti",  "Y"),
    ("Ti/V",   "Ti",  "V"),
    ("Ba/Nb",  "Ba",  "Nb"),
    ("Rb/Sr",  "Rb",  "Sr"),
    # Mantle against crust: about constant in oceanic basalts, low in
    # continental crust, so a drop marks crustal input (Hofmann et al.
    # 1986).
    ("Nb/U",   "Nb",  "U"),
    ("Ce/Pb",  "Ce",  "Pb"),
)

#: What a ratio is beyond its two elements, where that needs saying.
#: The reference values are the ratios of the reservoirs BIRDS carries,
#: each checked against its paper: Sun & McDonough (1989) Table 1,
#: McDonough & Sun (1995) Table 5, Rudnick & Gao (2003) Table 11.
RATIO_NOTES: Mapping[str, str] = {
    "Nb/U": "About constant in oceanic basalts and low in continental "
            "crust, so it falls with crustal input (Hofmann et al. "
            "1986): N-MORB 50, OIB 47, primitive mantle 32, bulk "
            "continental crust 6.2.",
    "Ce/Pb": "About constant in oceanic basalts and low in continental "
             "crust (Hofmann et al. 1986): N-MORB, E-MORB and OIB 25, "
             "primitive mantle 11, bulk continental crust 3.9.",
}


def compute_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """Per-sample trace-element ratios commonly used in petrogenesis.

    Ti is the Ti column, or TiO2 × 5993.4 when there is none."""
    out = pd.DataFrame(index=df.index)
    for name, num, den in RATIO_DEFINITIONS:
        numerator = _element_ppm(df, num)
        denominator = _element_ppm(df, den)
        if numerator is None or denominator is None:
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = numerator / denominator.where(denominator != 0, np.nan)
        out[name] = ratio.round(4)
    # Magnesium number — the differentiation index of every mafic study.
    mg = compute_mg_number(df)
    for col in mg.columns:
        out[col] = mg[col]
    # Weathering / hydrothermal-alteration indices from the majors.
    alteration = compute_alteration_indices(df)
    for col in alteration.columns:
        out[col] = alteration[col]
    return out


# Molecular weights used by the molar indices.
_MW_MGO = 40.304
_MW_FEO = 71.844


def compute_mg_number(df: pd.DataFrame) -> pd.DataFrame:
    """Magnesium number, ``Mg# = 100 · Mg / (Mg + Fe²⁺)`` in MOLAR
    proportions — the standard fractionation index for mafic magmas
    (primitive mantle-derived melts ≈ 68-75; evolved basalts < 50).

    Two flavours are emitted because the literature uses both and they
    are **not** interchangeable:

    * ``Mg#``      — strict definition using the *measured* ferrous iron
      (the ``FeO`` column).  Only produced when FeO was actually
      analysed and reported separately from Fe₂O₃.
    * ``Mg#_FeOt`` — the "all iron as Fe²⁺" convention, computed from
      total iron (FeO + 0.8998·Fe₂O₃, or a reported FeOt / Fe₂O₃t).
      This is what most papers mean when a rock only has total iron.
      It is always ≤ the strict ``Mg#``.

    A dataset that reports only total iron yields just ``Mg#_FeOt``;
    one with a real FeO/Fe₂O₃ split yields both, and the gap between
    them is a direct read-out of the sample's oxidation state.
    """
    from .preprocess import get_feot

    out = pd.DataFrame(index=df.index)
    mgo_col = _resolve_column(df, ["MgO"])
    if mgo_col is None:
        return out
    mgo = pd.to_numeric(df[mgo_col], errors="coerce") / _MW_MGO

    def _mg_number(feo_wt: pd.Series) -> pd.Series:
        feo_mol = feo_wt / _MW_FEO
        with np.errstate(divide="ignore", invalid="ignore"):
            total = mgo + feo_mol
            return (100.0 * mgo / total.where(total > 0, np.nan)).round(2)

    # Strict Mg# — needs a measured FeO column AND a separate Fe2O3, else
    # "FeO" is really total iron under another name and the strict
    # variant would be indistinguishable from Mg#_FeOt.
    feo_col = _resolve_column(df, ["FeO"])
    fe2o3_col = _resolve_column(df, ["Fe2O3"])
    if feo_col is not None and fe2o3_col is not None:
        out["Mg#"] = _mg_number(pd.to_numeric(df[feo_col], errors="coerce"))

    feot = get_feot(df)
    if feot is not None:
        out["Mg#_FeOt"] = _mg_number(feot)
    return out


# Molecular weights for the molar alteration indices.
_MW_OXIDES = {
    "Al2O3": 101.96, "CaO": 56.08, "Na2O": 61.98,
    "K2O": 94.20, "P2O5": 141.94, "MgO": 40.30,
}


def _molar(df: pd.DataFrame, oxide: str) -> Optional[pd.Series]:
    col = _resolve_column(df, [oxide])
    if col is None:
        return None
    return pd.to_numeric(df[col], errors="coerce") / _MW_OXIDES[oxide]


def compute_alteration_indices(df: pd.DataFrame) -> pd.DataFrame:
    """Chemical weathering / alteration indices.

    * **CIA** (Chemical Index of Alteration; Nesbitt & Young 1982):
      ``100 · Al2O3 / (Al2O3 + CaO* + Na2O + K2O)`` in MOLAR
      proportions, where CaO* is silicate-hosted Ca.  Only the apatite
      correction is applied — ``CaO* = CaO − (10/3)·P2O5`` (molar) —
      which is the appropriate convention for IGNEOUS rocks where Ca
      lives in plagioclase / clinopyroxene.  (The additional McLennan
      1993 carbonate clamp CaO* ≤ Na2O is a sedimentary-rock
      convention and is deliberately NOT applied here: it would gut
      the Ca of every fresh basalt.)  Fresh basalts ≈ 30-45, fresh
      granites ≈ 45-55, intense weathering → 100.

    * **AI_Ishikawa** (Ishikawa et al. 1976 alteration index):
      ``100 · (K2O + MgO) / (K2O + MgO + Na2O + CaO)`` in wt.%, the
      "変質強度" of the footnote to their Table 1 -- Na and Ca leached,
      K and Mg added by hydrothermal sericite-chlorite alteration.
      They give no threshold; around the Fukasawa kuroko orebodies it
      is over 90.  The "fresh 20-60" often quoted with it is Large et
      al.'s (2001), not theirs, and is not stated here.

    Missing input oxides simply omit the corresponding index column.
    """
    out = pd.DataFrame(index=df.index)

    al = _molar(df, "Al2O3")
    ca = _molar(df, "CaO")
    na = _molar(df, "Na2O")
    k = _molar(df, "K2O")
    p = _molar(df, "P2O5")
    if al is not None and ca is not None and na is not None and k is not None:
        ca_star = ca - (10.0 / 3.0) * p if p is not None else ca.copy()
        ca_star = ca_star.clip(lower=0)
        with np.errstate(divide="ignore", invalid="ignore"):
            denom = al + ca_star + na + k
            cia = 100.0 * al / denom.where(denom > 0, np.nan)
        out["CIA"] = cia.round(2)

    k_w = _resolve_column(df, ["K2O"])
    mg_w = _resolve_column(df, ["MgO"])
    na_w = _resolve_column(df, ["Na2O"])
    ca_w = _resolve_column(df, ["CaO"])
    if all(c is not None for c in (k_w, mg_w, na_w, ca_w)):
        kk = pd.to_numeric(df[k_w], errors="coerce")
        mm = pd.to_numeric(df[mg_w], errors="coerce")
        nn = pd.to_numeric(df[na_w], errors="coerce")
        cc = pd.to_numeric(df[ca_w], errors="coerce")
        with np.errstate(divide="ignore", invalid="ignore"):
            denom = kk + mm + nn + cc
            ai = 100.0 * (kk + mm) / denom.where(denom > 0, np.nan)
        out["AI_Ishikawa"] = ai.round(2)

    return out


# ---------------------------------------------------------------------------
# What each per-sample index is, for tooltips
# ---------------------------------------------------------------------------

#: The anomalies of :func:`compute_anomalies_extended`, as computed.
#: The chondrite of the REE ones is the one picked; the multi-element
#: ones use the primitive mantle or CI chondrite named.
ANOMALY_DESCRIPTIONS: Mapping[str, str] = {
    "Eu/Eu*": "Eu_N / √(Sm_N · Gd_N), chondrite-normalised "
              "(Taylor & McLennan 1985). < 1: plagioclase removed.",
    "Ce/Ce*": "Ce_N / √(La_N · Pr_N), chondrite-normalised. Departs "
              "from 1 where Ce⁴⁺ was mobilised (oxidation, seawater).",
    "Pr/Pr*": "Pr_N / √(Ce_N · Nd_N), chondrite-normalised.",
    "Gd/Gd*": "Gd_N / √(Sm_N · Tb_N), chondrite-normalised.",
    "Dy/Dy*": "Dy_N / √(Tb_N · Ho_N), chondrite-normalised; sensitive "
              "to MREE depletion and garnet.",
    "Y/Y*": "Y_N / √(Dy_N · Ho_N), chondrite-normalised.",
    "Y/Ho": "Y / Ho, ppm/ppm (chondritic ≈ 28).",
    "Ta/Ta*": "Ta_PM / √(Nb_PM · La_PM), primitive mantle "
              "(McDonough & Sun 1995).",
    "Nb/Nb*": "Nb_PM / √(Th_PM · La_PM), primitive mantle (Pearce "
              "2008). < 1: the Nb trough of arc magmas.",
    "Ti/Ti*": "Ti_PM / √(Eu_PM · Gd_PM), primitive mantle; Ti from "
              "TiO2 × 5993.4 when there is no Ti column. < 1: Fe-Ti "
              "oxide or titanite removed.",
    "Nb/Nb*_V(PM)": "2 · Nb_PM / (Ba_PM + La_PM), primitive mantle "
                    "(Verma 2015).",
    "Ta/Ta*_V(PM)": "2 · Ta_PM / (Ba_PM + La_PM), primitive mantle "
                    "(Verma 2015).",
    "Nb/Nb*_V(CN)": "2 · Nb_CN / (Ba_CN + La_CN), CI chondrite "
                    "(Verma 2015).",
    "Ta/Ta*_V(CN)": "2 · Ta_CN / (Ba_CN + La_CN), CI chondrite "
                    "(Verma 2015).",
    "(La/Yb)N": "La_N / Yb_N, chondrite-normalised: slope of the REE "
                "pattern.",
    "(La/Sm)N": "La_N / Sm_N, chondrite-normalised: LREE slope.",
    "(Gd/Yb)N": "Gd_N / Yb_N, chondrite-normalised: MREE/HREE, garnet.",
    "(Sm/Yb)N": "Sm_N / Yb_N, chondrite-normalised: MREE/HREE, garnet.",
}

#: The alteration indices of :func:`compute_alteration_indices`.
ALTERATION_DESCRIPTIONS: Mapping[str, str] = {
    "CIA": "Chemical Index of Alteration, 100·Al2O3/(Al2O3+CaO*+Na2O+"
           "K2O) molar, CaO* corrected for apatite (Nesbitt & Young "
           "1982). Fresh basalt ≈ 30-45, granite ≈ 45-55.",
    "AI_Ishikawa": "Alteration index, 100·(K2O+MgO)/(K2O+MgO+Na2O+CaO) "
                   "wt % (Ishikawa et al. 1976): rises as hydrothermal "
                   "alteration leaches Na and Ca and adds K and Mg; over "
                   "90 around the Fukasawa kuroko orebodies.",
}


def ratio_description(name: str) -> Optional[str]:
    """What the ratio *name* of :data:`RATIO_DEFINITIONS` is."""
    for ratio, num, den in RATIO_DEFINITIONS:
        if ratio == name:
            text = f"{num} / {den}, ppm/ppm."
            if "Ti" in (num, den):
                text += (f" Ti from TiO2 × {TIO2_WT_TO_TI_PPM:g} when "
                         "there is no Ti column.")
            if name in RATIO_NOTES:
                text += " " + RATIO_NOTES[name]
            return text
    return None


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_sections(
    path: str | Path,
    sections: dict[str, pd.DataFrame],
    fmt: str = "xlsx",
) -> None:
    """Write *sections* (label → DataFrame) to *path*.

    ``fmt='xlsx'``: each section becomes a sheet.
    ``fmt='csv'``: sections are concatenated, separated by a ``# label`` header.
    """
    path = Path(path)
    sections = {k: v for k, v in sections.items() if v is not None and not v.empty}
    if not sections:
        raise ValueError("Nothing to export – every section is empty.")

    if fmt == "xlsx":
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            for label, frame in sections.items():
                # Excel refuses a colon, either slash, ?, * and square
                # brackets in a sheet name, and more than 31 characters.
                safe = label
                for ch in ':\\/?*[]':
                    safe = safe.replace(ch, "_")
                safe = safe[:31]
                frame.to_excel(writer, sheet_name=safe, index=True)
    elif fmt == "csv":
        with open(path, "w", encoding="utf-8") as fh:
            first = True
            for label, frame in sections.items():
                if not first:
                    fh.write("\n\n")
                fh.write(f"# {label}\n")
                frame.to_csv(fh, index=True)
                first = False
    else:
        raise ValueError(f"Unknown export format: {fmt!r}")
