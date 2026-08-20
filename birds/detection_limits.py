"""Detection-limit (censored value) handling for imported lab tables.

Real-world laboratory exports routinely contain *censored* values:

* ``<0.5``, ``< 0.5``, ``<LOD``, ``≤0.5`` — below the reported detection
  limit with the limit value attached;
* ``b.d.l.``, ``bdl``, ``n.d.``, ``nd``, ``n.a.``, ``—`` — below limit
  (or not analysed) with **no** numeric limit attached.

Left untreated, ``pd.to_numeric(errors="coerce")`` silently turns all of
these into NaN, so the sample vanishes from every diagram without the
user ever knowing why.  This module converts them *explicitly* under a
user-selected policy and returns a boolean mask so views can flag the
substituted cells.

Policies
--------
* ``"half"``   — replace ``<X`` with ``X / 2``   (most common convention)
* ``"sqrt2"``  — replace ``<X`` with ``X / √2`` (Croghan & Egeghy 2003)
* ``"nan"``    — treat every censored value as missing

Textual markers with no numeric limit (``b.d.l.`` …) always become NaN —
there is no number to halve — but they are still flagged in the mask so
the table view can show them distinctly.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import pandas as pd


# "<0.5", "< 0.5", "≤0.5", "<=0.5" — captures the numeric limit.
_CENSOR_RE = re.compile(r"^\s*[<≤]=?\s*([0-9]*\.?[0-9]+(?:[eE][+-]?\d+)?)\s*$")

# Textual below-detection / not-determined markers (case-insensitive,
# dots optional).  The bare dash only counts when the whole cell is a
# dash — real negative numbers parse as numeric first.
_BDL_TEXT = {
    "bdl", "b.d.l", "b.d.l.", "bd", "b.d.", "b.d",
    "nd", "n.d", "n.d.", "na", "n.a", "n.a.",
    "<lod", "<dl", "<d.l.", "below detection", "below dl",
    "-", "—", "–",
}

POLICIES = ("half", "sqrt2", "nan")

POLICY_LABELS = {
    "half":  "Replace <x with x/2 (recommended)",
    "sqrt2": "Replace <x with x/√2",
    "nan":   "Treat as missing (NaN)",
}


@dataclass
class BdlReport:
    """Summary of one :func:`scan_and_convert` pass."""
    n_censored: int = 0                    # "<X" cells with numeric limit
    n_textual: int = 0                     # bdl/nd cells without a limit
    columns: dict = field(default_factory=dict)   # col -> count
    policy: str = "half"
    # Reported detection limits, aligned to the converted frame: the X
    # behind each "<X", NaN everywhere else (including textual markers,
    # which carry no limit).  Keeping them lets the user switch policy
    # later without re-importing — see :func:`reapply_policy`.
    limits: Optional[pd.DataFrame] = None

    @property
    def total(self) -> int:
        return self.n_censored + self.n_textual

    def summary(self) -> str:
        if self.total == 0:
            return ""
        ncols = len(self.columns)
        return (f"{self.total} below-detection value"
                f"{'s' if self.total != 1 else ''} in {ncols} column"
                f"{'s' if ncols != 1 else ''} "
                f"({POLICY_LABELS.get(self.policy, self.policy)})")


def _convert_cell(raw, policy: str):
    """Classify one cell.

    Returns ``(value, kind, limit)`` where kind is ``"num"`` (plain
    number), ``"censored"`` (<X pattern), ``"textual"`` (bdl marker),
    ``"blank"`` (empty / NaN) or ``"other"`` (unparseable text), and
    *limit* is the reported detection limit for censored cells (NaN
    otherwise).

    ``"blank"`` and ``"other"`` are kept apart on purpose: a column of
    markers padded with empty cells is still an analyte, while one that
    carries real words is a descriptive column and must not be touched.
    """
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return np.nan, "blank", np.nan
    if isinstance(raw, (int, float, np.integer, np.floating)):
        return float(raw), "num", np.nan
    s = str(raw).strip()
    if not s:
        return np.nan, "blank", np.nan
    m = _CENSOR_RE.match(s)
    if m:
        limit = float(m.group(1))
        return apply_policy(limit, policy), "censored", limit
    if s.lower() in _BDL_TEXT:
        return np.nan, "textual", np.nan
    # Plain numeric text ("1.23", "1,23" is NOT handled here — the
    # robust reader normalises decimal commas before we run).
    try:
        return float(s), "num", np.nan
    except ValueError:
        return np.nan, "other", np.nan


def apply_policy(limit: float, policy: str) -> float:
    """Substituted value for a reported detection *limit* under *policy*."""
    if limit is None or (isinstance(limit, float) and math.isnan(limit)):
        return np.nan
    if policy == "half":
        return limit / 2.0
    if policy == "sqrt2":
        return limit / math.sqrt(2.0)
    return np.nan


def scan_and_convert(
    df: Optional[pd.DataFrame],
    policy: str = "half",
) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], BdlReport]:
    """Convert censored values in every affected column of *df*.

    Only object-dtype columns containing at least one censored / textual
    marker are touched; pure-text columns (Sample_Name, Group, …) pass
    through unchanged.  Returns ``(converted_df, mask_df, report)``:

    * ``converted_df`` — copy of *df* with affected columns numeric;
    * ``mask_df``      — boolean frame, True where a value was censored
      (same shape as *df*); ``None`` when nothing was found;
    * ``report``       — counts for the import-preview summary.

    Raises ``ValueError`` on an unknown *policy* — silently falling back
    would discard every censored value without telling anyone.
    """
    if policy not in POLICIES:
        raise ValueError(
            f"Unknown detection-limit policy {policy!r}; "
            f"expected one of {', '.join(POLICIES)}.")
    report = BdlReport(policy=policy)
    if df is None or df.empty:
        return df, None, report

    out = df.copy()
    mask = pd.DataFrame(False, index=df.index, columns=df.columns)
    limit_frame = pd.DataFrame(np.nan, index=df.index, columns=df.columns,
                               dtype=float)
    any_flag = False

    for col in df.columns:
        # Text-bearing columns arrive as classic ``object`` OR as the
        # pandas-3 ``str`` dtype depending on the reader — accept both.
        if not (pd.api.types.is_object_dtype(df[col])
                or pd.api.types.is_string_dtype(df[col])):
            continue
        series = df[col]
        kinds = []
        values = []
        limits = []
        n_cens = n_text = n_num = n_other = 0
        for raw in series:
            v, kind, limit = _convert_cell(raw, policy)
            values.append(v)
            kinds.append(kind)
            limits.append(limit)
            if kind == "censored":
                n_cens += 1
            elif kind == "textual":
                n_text += 1
            elif kind == "num":
                n_num += 1
            elif kind == "other":
                n_other += 1
        if (n_cens + n_text) == 0:
            continue                      # nothing censored in this column
        # A column with no numeric anchor at all is ambiguous: it is
        # either an analyte that never rose above detection (every cell
        # a marker) or a descriptive column that happens to use "-" as
        # a placeholder.  Real words settle it — those stay untouched.
        if (n_num + n_cens) == 0 and n_other:
            continue
        out[col] = pd.Series(values, index=series.index, dtype=float)
        col_mask = pd.Series([k in ("censored", "textual") for k in kinds],
                             index=series.index)
        mask[col] = col_mask
        limit_frame[col] = pd.Series(limits, index=series.index, dtype=float)
        any_flag = True
        report.n_censored += n_cens
        report.n_textual += n_text
        report.columns[col] = n_cens + n_text

    if any_flag:
        report.limits = limit_frame
    return out, (mask if any_flag else None), report


def reapply_policy(
    df: pd.DataFrame,
    mask: Optional[pd.DataFrame],
    limits: Optional[pd.DataFrame],
    policy: str,
) -> tuple[pd.DataFrame, int]:
    """Rewrite the flagged cells of *df* under a different *policy*.

    Lets the user compare ``x/2`` against ``x/√2`` without re-importing.
    Only cells that ``mask`` marks **and** for which a reported limit is
    known are touched; textual markers (``b.d.l.``) have no limit and
    stay NaN under every policy.

    Returns ``(new_df, n_changed)``.  *df* is not modified in place.
    """
    if policy not in POLICIES:
        raise ValueError(
            f"Unknown detection-limit policy {policy!r}; "
            f"expected one of {', '.join(POLICIES)}.")
    out = df.copy()
    if mask is None or limits is None or df is None or df.empty:
        return out, 0
    changed = 0
    for col in limits.columns:
        if col not in out.columns or col not in mask.columns:
            continue
        col_limits = limits[col].reindex(out.index)
        flagged = mask[col].reindex(out.index).fillna(False).astype(bool)
        target = flagged & col_limits.notna()
        if not target.any():
            continue
        new_values = col_limits[target].map(lambda x: apply_policy(x, policy))
        # The column may still be text if this sheet was never converted.
        out[col] = pd.to_numeric(out[col], errors="coerce")
        out.loc[target, col] = new_values
        changed += int(target.sum())
    return out, changed
