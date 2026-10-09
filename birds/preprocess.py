"""Pre-processing of major-element data for igneous rocks.

Two independent operations are exposed:

* :func:`adjust_to_100` — re-scale every major oxide so the row sums to
  100 wt %, optionally zeroing out volatile species first
  (anhydrous / volatile-free recalculation).
* :func:`partition_iron` — split total iron between Fe₂O₃ and FeO using
  one of four published conventions (Middlemost 1989, Le Maitre 1976,
  user-fixed ratio, or "none" to leave the analysis untouched).

Both functions are *pure*: they return a new DataFrame and never modify
the input. They are intentionally backend-only so they can be tested in
isolation and reused by both the GUI dialog and the CIPW module.

References
----------
- Le Maitre, R.W. (1976). Some problems of the projection of chemical data
  into mineralogical classifications. *Contrib. Mineral. Petrol.* 56,
  181-189.
- Middlemost, E.A.K. (1989). Iron oxidation ratios, norms and the
  classification of volcanic rocks. *Chem. Geol.* 77, 19-26.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Constants — oxide column names recognised by the module
# ---------------------------------------------------------------------------

# Oxides that participate in the 100 % rescale (and in CIPW downstream).
MAJOR_OXIDES: Sequence[str] = (
    "SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO", "MnO", "MgO", "CaO",
    "Na2O", "K2O", "P2O5", "Cr2O3", "NiO",
)

# Species that get zeroed out by the anhydrous (volatile-free) recalc.
VOLATILES: Sequence[str] = (
    "LOI", "H2O", "H2O+", "H2O-", "CO2", "Cl", "F", "S", "SO3",
)

# Mass-balance factor between FeOt and Fe2O3:
#   1 mole Fe2O3 (159.69 g/mol)  ==  2 mole FeO (71.844 g/mol each)
#   ⇒  1 g Fe2O3  ⇄  (2 × 71.844 / 159.69) g FeO  =  0.89981 g FeO
FE2O3_TO_FEO: float = 0.89981
FEO_TO_FE2O3: float = 1.0 / FE2O3_TO_FEO   # ≈ 1.11135


# ---------------------------------------------------------------------------
# Options dataclasses (for the dialog & for the CIPW caller)
# ---------------------------------------------------------------------------

@dataclass
class AdjustOptions:
    """Options for :func:`adjust_to_100`."""
    mode: str = "anhydrous"   # "anhydrous" | "simple" | "none"

    def __post_init__(self) -> None:
        if self.mode not in {"anhydrous", "simple", "none"}:
            raise ValueError(
                f"adjust_to_100 mode must be 'anhydrous', 'simple' or "
                f"'none' (got {self.mode!r})"
            )


@dataclass
class IronOptions:
    """Options for :func:`partition_iron`."""
    rule: str = "middlemost"  # "middlemost" | "le_maitre" | "fixed" | "none"
    fixed_ratio: float = 0.15  # Fe2O3 / (Fe2O3 + FeO) used when rule == "fixed"

    def __post_init__(self) -> None:
        if self.rule not in {"middlemost", "le_maitre", "fixed", "none"}:
            raise ValueError(
                f"partition_iron rule must be 'middlemost', 'le_maitre', "
                f"'fixed' or 'none' (got {self.rule!r})"
            )
        if not (0.0 <= self.fixed_ratio <= 1.0):
            raise ValueError("fixed_ratio must be in [0, 1]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _present(df: pd.DataFrame, names: Iterable[str]) -> list[str]:
    """Return the subset of *names* that actually exist as columns in *df*."""
    cols = set(df.columns)
    return [n for n in names if n in cols]


_FEOT_ALIASES = ("FeOt", "FeO_T", "FeO*", "FeOT", "FeO(T)", "FeOtot",
                 "FeO_tot")
_FE2O3T_ALIASES = ("Fe2O3t", "Fe2O3_T", "Fe2O3*", "Fe2O3T", "Fe2O3(T)")


def _numeric_column(df: pd.DataFrame, names: Iterable[str]) -> Optional[pd.Series]:
    """Return the first column in *names* present in *df* as a numeric
    Series (NaN-filled), or ``None`` if none of them exist."""
    for n in names:
        if n in df.columns:
            return pd.to_numeric(df[n], errors="coerce")
    return None


def get_feot(df: pd.DataFrame) -> Optional[pd.Series]:
    """Return total iron as FeO (FeOt) per sample, row-wise.

    The function combines every available iron source (FeOt / Fe₂O₃t /
    FeO + Fe₂O₃) and falls back **per row** when one source is missing.
    The precedence is:

    1. ``FeO + 0.8998 × Fe₂O₃`` whenever either is reported and the sum
       is positive (most common case).
    2. ``FeOt`` (or aliases) for rows where the FeO/Fe₂O₃ pair is absent
       or sums to zero.
    3. ``Fe₂O₃t × 0.8998`` as the last-resort fallback.

    Returns ``None`` only if no iron column is present at all.
    """
    feo = _numeric_column(df, ("FeO",))
    fe2o3 = _numeric_column(df, ("Fe2O3",))
    feot_direct = _numeric_column(df, _FEOT_ALIASES)
    fe2o3t = _numeric_column(df, _FE2O3T_ALIASES)

    if feo is None and fe2o3 is None and feot_direct is None and fe2o3t is None:
        return None

    # Start with FeO + 0.8998 × Fe2O3 (zero where missing)
    zeros = pd.Series(0.0, index=df.index, dtype="float64")
    feo_s = feo.fillna(0.0) if feo is not None else zeros
    fe2o3_s = fe2o3.fillna(0.0) if fe2o3 is not None else zeros
    computed = feo_s + FE2O3_TO_FEO * fe2o3_s

    # Where computed is essentially zero, prefer FeOt (or Fe2O3t)
    fallback = None
    if feot_direct is not None:
        fallback = feot_direct
    elif fe2o3t is not None:
        fallback = fe2o3t * FE2O3_TO_FEO
    if fallback is not None:
        computed = computed.where(computed > 1e-9, fallback)
    return computed


def consolidate_iron(df: pd.DataFrame) -> pd.DataFrame:
    """Materialise FeO / Fe₂O₃ from FeOt when the split is missing.

    When the dataset reports only ``FeOt`` (a common lab convention),
    we copy that value into ``FeO`` so the 100 %-rescale and the iron
    partition treat it as a real oxide. Fe₂O₃ is initialised to 0 in
    that case; the partition step splits the iron afterwards.

    Returns a copy of *df* with ``FeO`` / ``Fe2O3`` always present
    and consistent with ``FeOt`` (which is also written back as the
    canonical total).
    """
    out = df.copy()
    feot = get_feot(out)
    if feot is None:
        return out

    feo = pd.to_numeric(out["FeO"], errors="coerce").fillna(0.0) \
          if "FeO" in out.columns else pd.Series(0.0, index=out.index)
    fe2o3 = pd.to_numeric(out["Fe2O3"], errors="coerce").fillna(0.0) \
            if "Fe2O3" in out.columns else pd.Series(0.0, index=out.index)
    existing = feo + FE2O3_TO_FEO * fe2o3

    # Rows where FeO/Fe2O3 already account for the iron → keep as is.
    # Rows where they don't (sum ≈ 0 but FeOt > 0) → use FeOt as FeO.
    mask_missing = (existing < 1e-9) & (feot > 1e-9)
    out["FeO"] = feo.where(~mask_missing, feot)
    out["Fe2O3"] = fe2o3.where(~mask_missing, 0.0)
    out["FeOt"] = feot.round(6)
    return out


# ---------------------------------------------------------------------------
# 100 % adjustment
# ---------------------------------------------------------------------------

def adjust_to_100(df: pd.DataFrame,
                  options: AdjustOptions | str = "anhydrous"
                  ) -> pd.DataFrame:
    """Re-scale the major oxides so each row sums to 100 wt %.

    Parameters
    ----------
    df
        Input DataFrame. Non-major columns are kept untouched.
    options
        Either an :class:`AdjustOptions` instance or the string ``"anhydrous"``
        / ``"simple"`` / ``"none"``.

    Modes
    -----
    ``anhydrous``  Volatile species (LOI, H₂O, CO₂, …) are set to zero
                   before the rescale → "volatile-free" recalculation.
                   This is the standard pre-processing for igneous
                   plotting (TAS, AFM, …).
    ``simple``     Pure proportional rescaling: divide each oxide by the
                   row sum × 100. Volatiles kept.
    ``none``       Return a copy of *df* unchanged.
    """
    if isinstance(options, str):
        options = AdjustOptions(mode=options)
    if options.mode == "none":
        return df.copy()

    out = df.copy()
    majors = _present(out, MAJOR_OXIDES)
    if not majors:
        return out

    # Coerce to numeric just for the rescale; we put the values back in place
    numeric = out[majors].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    if options.mode == "anhydrous":
        # Drop volatiles by setting them to 0 before computing the row sum.
        for v in _present(out, VOLATILES):
            out[v] = 0.0
        denom = numeric.sum(axis=1)
    else:  # "simple"
        # Include volatiles in the denominator so the rest gets scaled
        # consistently. Volatile columns themselves are NOT rescaled
        # (they keep their absolute values), which matches the typical
        # workflow where volatiles are reported in a separate block.
        vols_present = _present(out, VOLATILES)
        vol_numeric = (out[vols_present].apply(pd.to_numeric, errors="coerce")
                       .fillna(0.0) if vols_present else pd.DataFrame(0,
                                                                       index=out.index,
                                                                       columns=["_z"]))
        denom = numeric.sum(axis=1) + vol_numeric.sum(axis=1)

    safe = denom.replace(0, np.nan)
    for c in majors:
        out[c] = (numeric[c] / safe) * 100.0

    return out


# ---------------------------------------------------------------------------
# Iron partition
# ---------------------------------------------------------------------------

# Pre-published ratios — Fe2O3 / (Fe2O3 + FeO) — used by the rock-type rules.
# Both Middlemost (1989) and Le Maitre (1976) were originally given as
# tables keyed by TAS rock name; we collapse them onto SiO₂ × (Na₂O+K₂O)
# breakpoints for a fully automatic application.

def _is_alkaline(si: pd.Series, alk: pd.Series) -> pd.Series:
    """Macdonald & Katsura (1964) alkaline/sub-alkaline boundary.

    Returns True where (Na₂O+K₂O) plots above the line
    ``alk = 0.37 × SiO₂ − 14.43``, which is the textbook divider
    between tholeiitic (sub-alkaline) and alkaline basalts at
    SiO₂ ≈ 45-65 wt%.
    """
    return alk > 0.37 * si - 14.43


def _middlemost_ratio(si: pd.Series, alk: pd.Series) -> pd.Series:
    """Middlemost (1989) Fe₂O₃/(Fe₂O₃+FeO) by TAS sector + alkalinity.

    Sub-alkaline default by SiO₂ bin:
      <45 picro-basalt 0.20  ·  45-63 basalt → andesite 0.15  ·
      63-69 dacite 0.20  ·  ≥69 rhyolite 0.30
    Alkaline override (above Macdonald-Katsura): the slightly more
    oxidised character of alkaline magmas shifts the ratio to 0.20-0.40.
    """
    r = pd.Series(0.30, index=si.index, dtype=float)   # rhyolite default
    r[si < 45] = 0.20
    r[(si >= 45) & (si < 63)] = 0.15
    r[(si >= 63) & (si < 69)] = 0.20

    alkaline = _is_alkaline(si, alk).fillna(False)
    r[alkaline & (si < 45)] = 0.30
    r[alkaline & (si >= 45) & (si < 52)] = 0.20    # trachy-basalt
    r[alkaline & (si >= 52) & (si < 63)] = 0.30    # trachy-andesite, phonolite
    r[alkaline & (si >= 63) & (si < 69)] = 0.30    # trachy-dacite, trachyte
    r[alkaline & (si >= 69)] = 0.40                # peralkaline rhyolite
    return r


def _le_maitre_ratio(si: pd.Series, _alk: pd.Series) -> pd.Series:
    """Le Maitre (1976) — coarser categorisation, alkalinity-blind."""
    r = pd.Series(0.20, index=si.index, dtype=float)
    r[si < 52] = 0.15
    r[(si >= 52) & (si < 63)] = 0.30
    r[si >= 63] = 0.40
    return r


def partition_iron(df: pd.DataFrame,
                   options: IronOptions | str = "middlemost"
                   ) -> pd.DataFrame:
    """Split total iron between Fe₂O₃ and FeO according to *options.rule*.

    Returns a copy of *df* with the ``Fe2O3`` and ``FeO`` columns
    overwritten. ``FeOt`` is kept (and updated to reflect the new total
    iron content, which is conserved by the partition).

    The partition is mass-balanced via
    ``FeOt = FeO + 0.8998 × Fe2O3``.
    """
    if isinstance(options, str):
        options = IronOptions(rule=options)
    if options.rule == "none":
        return df.copy()

    out = df.copy()
    feot = get_feot(out)
    if feot is None:
        # No iron columns at all — nothing to do.
        return out

    if options.rule == "fixed":
        r = pd.Series(options.fixed_ratio, index=out.index, dtype=float)
    elif options.rule in ("middlemost", "le_maitre"):
        si = pd.to_numeric(out.get("SiO2", pd.Series(np.nan, index=out.index)),
                           errors="coerce")
        na = pd.to_numeric(out.get("Na2O", pd.Series(0.0, index=out.index)),
                           errors="coerce").fillna(0.0)
        k = pd.to_numeric(out.get("K2O", pd.Series(0.0, index=out.index)),
                          errors="coerce").fillna(0.0)
        alk = na + k
        rule_fn = (_middlemost_ratio if options.rule == "middlemost"
                   else _le_maitre_ratio)
        r = rule_fn(si, alk)
    else:                                               # pragma: no cover
        return out

    # Mass-balance solve.
    # Let r = Fe₂O₃ / (Fe₂O₃ + FeO_metal_mass).  We want:
    #   FeOt = FeO + 0.8998 × Fe₂O₃
    # and:
    #   FeO  = (1 − r) × X
    #   Fe₂O₃ = r × X
    # ⇒  FeOt = (1 − r) X + 0.8998 r X = X (1 − 0.1002 r)
    # ⇒  X = FeOt / (1 − 0.1002 r)
    denom = 1.0 - (1.0 - FE2O3_TO_FEO) * r
    X = feot / denom
    out["Fe2O3"] = (r * X).round(6)
    out["FeO"] = ((1.0 - r) * X).round(6)
    out["FeOt"] = feot.round(6)         # keep the total iron explicit
    return out


# ---------------------------------------------------------------------------
# Convenience wrapper for the dialog
# ---------------------------------------------------------------------------

def pre_process(df: pd.DataFrame,
                adjust: AdjustOptions | str = "anhydrous",
                iron: IronOptions | str = "middlemost"
                ) -> pd.DataFrame:
    """Run the canonical pre-process pipeline.

    Steps
    -----
    1. **Consolidate iron.** When the user only reported FeOt, copy it
       into FeO so the iron is included in the rescale.
    2. **Adjust to 100 wt %** using *adjust* (anhydrous by default).
    3. **Partition iron** between Fe₂O₃ and FeO using *iron*.
    4. **Re-rescale to 100 wt %** to absorb the small mass change
       introduced by the partition (oxygen added when oxidising FeO
       to Fe₂O₃, or removed when doing the reverse). The second
       rescale uses the same mode as the first, so volatile handling
       is consistent.

    Pure function: returns a new DataFrame.
    """
    out = consolidate_iron(df)
    out = adjust_to_100(out, adjust)
    out = partition_iron(out, iron)
    # Second rescale closes the small mass change introduced by the
    # partition; with ``adjust="none"`` it is a no-op (early return).
    out = adjust_to_100(out, adjust)
    # FeOt is not one of the rescaled oxides, so both rescales left it
    # behind -- by the LOI removed when the iron is not partitioned, by
    # ~0.15 % when it is.  Total iron is whatever FeO and Fe2O3 now are.
    if {"FeOt", "FeO", "Fe2O3"} <= set(out.columns):
        feo = pd.to_numeric(out["FeO"], errors="coerce")
        fe2o3 = pd.to_numeric(out["Fe2O3"], errors="coerce")
        out["FeOt"] = (feo + FE2O3_TO_FEO * fe2o3).round(6)
    return out


# ---------------------------------------------------------------------------
# Adjusted twins: the analysed values stay, the adjusted ones sit beside
# ---------------------------------------------------------------------------
#
# Pre-processing used to overwrite the analysed oxides with the adjusted
# ones.  From then on every diagram plotted adjusted values with nothing
# to say so, and the analysed values were gone.  Now the adjusted values
# are added as ``SiO2_adj``, ``TiO2_adj``, … and the analysed columns are
# left as they were; each major-element view chooses which to read.

#: Suffix of the columns pre-processing adds.
ADJ_SUFFIX = "_adj"

#: Columns that get an adjusted twin: the major oxides and total iron.
ADJUSTABLE: Sequence[str] = (*MAJOR_OXIDES, "FeOt")

_IRON_COLUMNS = ("FeO", "Fe2O3", "FeOt")

#: Plain-language names of the options, shared by the dialog and by the
#: panels that say which values a diagram is using.
ADJUST_LABELS = {
    "anhydrous": "anhydrous (volatile-free) to 100 wt %",
    "simple": "proportionally to 100 wt %",
    "none": "not rescaled",
}
IRON_LABELS = {
    "middlemost": "Fe₂O₃/FeO after Middlemost (1989)",
    "le_maitre": "Fe₂O₃/FeO after Le Maitre (1976)",
    "fixed": "Fe₂O₃/(Fe₂O₃+FeO) fixed at {ratio:g}",
    "none": "Fe₂O₃/FeO as analysed",
}


def adjusted_name(column: str) -> str:
    """``SiO2`` → ``SiO2_adj``."""
    return f"{column}{ADJ_SUFFIX}"


def has_adjusted(df: Optional[pd.DataFrame]) -> bool:
    """True when *df* carries adjusted twins of any major oxide."""
    return df is not None and any(adjusted_name(c) in df.columns
                                  for c in ADJUSTABLE)


def _has_iron(df: pd.DataFrame) -> pd.Series:
    """Per row: was any form of iron reported at all?"""
    names = ("FeO", "Fe2O3", *_FEOT_ALIASES, *_FE2O3T_ALIASES)
    present = [n for n in names if n in df.columns]
    if not present:
        return pd.Series(False, index=df.index)
    return (df[present].apply(pd.to_numeric, errors="coerce")
            .notna().any(axis=1))


def attach_adjusted(df: pd.DataFrame,
                    adjust: AdjustOptions | str = "anhydrous",
                    iron: IronOptions | str = "middlemost") -> pd.DataFrame:
    """A copy of *df* with adjusted twins of its major oxides added.

    The analysed columns are not touched.  Running it again replaces the
    twins, always computed from the analysed values.

    An oxide that was not analysed stays missing in its twin: the 100 %
    rescale counts it as zero, but writing 0.000 wt % into the table
    would report a measurement nobody made.  Iron is the exception --
    the partition creates FeO, Fe₂O₃ and FeOt from whichever form was
    reported -- and is missing only where no iron was reported at all.
    """
    analysed = df[[c for c in df.columns
                   if not str(c).endswith(ADJ_SUFFIX)]]
    processed = pre_process(analysed, adjust, iron)
    out = df.copy()
    iron_rows = _has_iron(analysed)
    for col in ADJUSTABLE:
        if col not in processed.columns:
            continue
        values = pd.to_numeric(processed[col], errors="coerce")
        if col in _IRON_COLUMNS:
            values = values.where(iron_rows)
        elif col in analysed.columns:
            values = values.where(
                pd.to_numeric(analysed[col], errors="coerce").notna())
        else:
            continue
        out[adjusted_name(col)] = values
    return out


def with_adjusted_majors(df: Optional[pd.DataFrame]
                         ) -> Optional[pd.DataFrame]:
    """*df* as a major-element diagram should read it when the adjusted
    values are in use: each oxide column holds its adjusted twin.

    The diagrams look up ``SiO2``, never ``SiO2_adj``, so the swap is
    made here, once, for all of them.  Total iron is written into every
    alias the dataset carries (FeOT, Fe2O3T, …): a diagram that happened
    to read one of those would otherwise get the analysed value.
    """
    if not has_adjusted(df):
        return df
    out = df.copy()
    for col in ADJUSTABLE:
        twin = adjusted_name(col)
        if twin in out.columns:
            out[col] = out[twin]
    twin = adjusted_name("FeOt")
    if twin in out.columns:
        feot = pd.to_numeric(out[twin], errors="coerce")
        for alias in _FEOT_ALIASES:
            if alias in out.columns:
                out[alias] = feot
        for alias in _FE2O3T_ALIASES:
            if alias in out.columns:
                out[alias] = feot * FEO_TO_FE2O3
    return out


def describe_adjustment(settings: Optional[dict]) -> str:
    """How the twins were made, in words: "anhydrous (volatile-free) to
    100 wt %, Fe₂O₃/FeO after Middlemost (1989)"."""
    if not settings:
        return "settings not recorded"
    mode = ADJUST_LABELS.get(settings.get("mode", ""), "")
    iron = IRON_LABELS.get(settings.get("iron", ""), "")
    iron = iron.format(ratio=float(settings.get("ratio", 0.15)))
    return ", ".join(part for part in (mode, iron) if part)
