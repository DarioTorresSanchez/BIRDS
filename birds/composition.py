"""SiO2-based compositional classifier for igneous rocks.

Used by the Verma multidimensional discriminant diagrams to pre-filter
the sample set so each panel only sees samples of the composition the
underlying equations were calibrated for.

Boundaries follow the IUGS / TAS strict convention (Le Bas et al. 1986;
Le Maitre 2002), which also matches what Verma & Agrawal (2011),
Verma & Verma (2013) and Verma et al. (2012) use in their training-set
filters:

    Ultrabasic      SiO2  <  45
    Basic           45  ≤  SiO2  <  52
    Intermediate    52  ≤  SiO2  <  63
    Acid            SiO2  ≥  63

Composition keys recognised by ``filter_by_composition``:

* ``"ultrabasic"``
* ``"basic"``
* ``"basic+ultrabasic"`` — for Verma & Agrawal 2011 (one diagram, two
  fields).
* ``"intermediate"``
* ``"acid"``
* ``"high-mg"`` — komatiite / picrite / boninite (SiO2 ≤ 52 AND
  MgO ≥ 8 wt %).
* ``None`` or unknown — no filtering.
"""

from __future__ import annotations

from typing import Optional, Tuple

import pandas as pd

# Strict boundaries (wt %) used in Le Bas et al. 1986 / Le Maitre 2002
# and Verma & co-authors' own calibration filters.
ULTRABASIC_MAX = 45.0
BASIC_MAX      = 52.0
INTERMEDIATE_MAX = 63.0

# ---------------------------------------------------------------------------
# Rock-type filter (Volcanic / Plutonic / etc.)
# ---------------------------------------------------------------------------

# Aliases for the user-facing Rock_Type column.  Case-insensitive and
# tolerant of underscores / spaces because legacy datasets may follow
# different conventions.
_ROCK_TYPE_ALIASES = ("Rock_Type", "RockType", "Rock Type",
                      "rock_type", "Rocktype", "rocktype",
                      "Tipo_de_Roca", "Tipo de Roca",
                      "Lithology_Family", "Family")

# What counts as "volcanic" vs "plutonic" when the user picks one of
# those families in the Classification or Tectonic menus.  Empty / unknown
# values are kept on both families so they don't get silently dropped.
VOLCANIC_VALUES  = {"volcanic", "sub-volcanic", "subvolcanic",
                    "pyroclastic", "extrusive"}
PLUTONIC_VALUES  = {"plutonic", "intrusive", "vein"}

# Names returned by ``classify_sio2``.
_LABELS = ("ultrabasic", "basic", "intermediate", "acid")

# Column aliases — checked in order; the first one present wins.  Always
# prefer the Middlemost-adjusted column over the raw one because Verma's
# equations are calibrated on 100 %-anhydrous compositions.
_SIO2_ADJ_ALIASES = ("SiO2_adj", "SiO2adj", "SiO2(adj)", "SiO2 adj",
                     "SiO2adjusted", "SiO2_adjusted")
_SIO2_RAW_ALIASES = ("SiO2", "SiO₂", "SIO2", "Sio2")
_MGO_ALIASES = ("MgO_adj", "MgO", "MgOadj")


def _resolve(df: pd.DataFrame, aliases: Tuple[str, ...]) -> Optional[str]:
    """Return the first column in *df* matching *aliases* (case-insensitive)."""
    lowered = {c.lower(): c for c in df.columns}
    for a in aliases:
        if a in df.columns:
            return a
        if a.lower() in lowered:
            return lowered[a.lower()]
    return None


def _resolve_sio2(df: pd.DataFrame) -> Tuple[Optional[str], str]:
    """Return ``(column_name, source_label)`` where source is 'adj' or
    'raw'.  Falls back to raw SiO2 if the preprocessed column isn't
    present.  ``column_name`` is None if neither exists."""
    col = _resolve(df, _SIO2_ADJ_ALIASES)
    if col is not None:
        return col, "adj"
    col = _resolve(df, _SIO2_RAW_ALIASES)
    if col is not None:
        return col, "raw"
    return None, "missing"


def classify_sio2(df: pd.DataFrame) -> pd.Series:
    """Return a ``pd.Series`` of composition labels (one of ``_LABELS`` or
    ``None``) for every row in *df*, derived from its SiO2 value.

    Rows without a usable SiO2 value get ``None`` so the caller can treat
    them however it likes (typically: keep them under "Don't filter").
    """
    col, _ = _resolve_sio2(df)
    if col is None:
        return pd.Series([None] * len(df), index=df.index, dtype="object")
    sio2 = pd.to_numeric(df[col], errors="coerce")
    labels = pd.Series([None] * len(df), index=df.index, dtype="object")
    labels[sio2 < ULTRABASIC_MAX] = "ultrabasic"
    labels[(sio2 >= ULTRABASIC_MAX) & (sio2 < BASIC_MAX)] = "basic"
    labels[(sio2 >= BASIC_MAX) & (sio2 < INTERMEDIATE_MAX)] = "intermediate"
    labels[sio2 >= INTERMEDIATE_MAX] = "acid"
    return labels


def filter_by_composition(df: pd.DataFrame, target: Optional[str]
                          ) -> Tuple[pd.DataFrame, dict]:
    """Filter *df* to rows whose composition matches *target*.

    Returns ``(filtered_df, info)`` where ``info`` is a small dict the
    GUI can use for status messages:

    * ``info["target"]``     — the requested composition
    * ``info["kept"]``       — number of rows kept
    * ``info["dropped"]``    — number of rows excluded
    * ``info["sio2_source"]`` — ``"adj"``, ``"raw"`` or ``"missing"``
    * ``info["range"]``      — e.g. ``"45 ≤ SiO₂ < 52"``

    When *target* is ``None`` (universal diagram) the dataframe is
    returned untouched.
    """
    info = {"target": target, "kept": len(df), "dropped": 0,
            "sio2_source": "n/a", "range": ""}
    if target is None or df is None or df.empty:
        return df, info

    col, src = _resolve_sio2(df)
    info["sio2_source"] = src
    if col is None:
        # No SiO2 column → can't filter.  Keep everything and tell the
        # caller via info so it can warn.
        return df, info

    sio2 = pd.to_numeric(df[col], errors="coerce")
    if target == "ultrabasic":
        mask = sio2 < ULTRABASIC_MAX
        info["range"] = f"SiO₂ < {ULTRABASIC_MAX:g}"
    elif target == "basic":
        mask = (sio2 >= ULTRABASIC_MAX) & (sio2 < BASIC_MAX)
        info["range"] = f"{ULTRABASIC_MAX:g} ≤ SiO₂ < {BASIC_MAX:g}"
    elif target == "basic+ultrabasic":
        mask = sio2 < BASIC_MAX
        info["range"] = f"SiO₂ < {BASIC_MAX:g}"
    elif target == "intermediate":
        mask = (sio2 >= BASIC_MAX) & (sio2 < INTERMEDIATE_MAX)
        info["range"] = f"{BASIC_MAX:g} ≤ SiO₂ < {INTERMEDIATE_MAX:g}"
    elif target == "acid":
        mask = sio2 >= INTERMEDIATE_MAX
        info["range"] = f"SiO₂ ≥ {INTERMEDIATE_MAX:g}"
    elif target == "high-mg":
        # Komatiite / picrite / boninite — basic + ultrabasic SiO2 AND
        # MgO ≥ 8 wt%.
        mgo_col = _resolve(df, _MGO_ALIASES)
        if mgo_col is None:
            return df, {**info, "range": "high-Mg requires MgO column"}
        mgo = pd.to_numeric(df[mgo_col], errors="coerce")
        mask = (sio2 < BASIC_MAX) & (mgo >= 8.0)
        info["range"] = "SiO₂ < 52 AND MgO ≥ 8"
    else:
        # Unknown target → don't filter
        return df, info

    mask = mask.fillna(False)
    kept = int(mask.sum())
    filtered = df[mask].copy()
    info["kept"] = kept
    info["dropped"] = len(df) - kept
    return filtered, info


def filter_by_rock_type(df: pd.DataFrame, family: Optional[str]
                        ) -> Tuple[pd.DataFrame, dict]:
    """Filter *df* to rows whose ``Rock_Type`` column matches *family*.

    *family* is ``"volcanic"`` or ``"plutonic"``; anything else returns
    the dataframe unchanged.  Samples whose ``Rock_Type`` is blank /
    unknown are **kept** (the user may have left the column empty by
    accident — it's safer to plot than to drop).

    Returns ``(filtered_df, info)`` with:

    * ``info["family"]``    — the requested family
    * ``info["kept"]``      — number of matching + blank rows
    * ``info["dropped"]``   — number of rows excluded (wrong family)
    * ``info["blank"]``     — number of rows with empty Rock_Type
    * ``info["source"]``    — column name actually used, or ``None``
    """
    info = {"family": family, "kept": len(df), "dropped": 0,
            "blank": 0, "source": None}
    if family not in ("volcanic", "plutonic") or df is None or df.empty:
        return df, info

    col = _resolve(df, _ROCK_TYPE_ALIASES)
    if col is None:
        # No Rock_Type column → can't filter. Keep all and tell caller.
        return df, info
    info["source"] = col

    # A blank cell is missing in the column itself, not only the text
    # "nan": pandas 3 keeps NaN as NaN through astype(str), where pandas
    # 2 wrote "nan" -- so an all-blank Rock_Type column, as a template
    # left unfilled arrives, used to drop every sample on both families.
    values = df[col].astype(str).str.strip().str.lower()
    blank_mask = df[col].isna() | values.isna() | values.isin(("", "nan",
                                                               "none"))
    target_set = VOLCANIC_VALUES if family == "volcanic" else PLUTONIC_VALUES
    match_mask = values.isin(target_set)
    keep_mask = match_mask | blank_mask

    info["blank"] = int(blank_mask.sum())
    info["kept"] = int(keep_mask.sum())
    info["dropped"] = len(df) - info["kept"]
    return df[keep_mask].copy(), info
