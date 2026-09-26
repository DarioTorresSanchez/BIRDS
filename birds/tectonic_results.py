"""Catalogue and per-sample evaluator for the tectonic-discrimination
results displayed in the Statistics view and bundled into the save
report.

The diagrams in :mod:`birds.diagrams.templates` know how to *render*
their own background and field labels but they do not — by design —
expose the numeric values they compute. This module wraps every
relevant discriminator (ratios, single-axis DFs and multi-panel DFs)
into a flat catalogue of :class:`Discriminator` objects with a stable
``key``, a human label, a family category and a ``compute(df)`` that
returns one pandas ``Series`` per sample.

Use :func:`compute_results` to evaluate any subset of discriminators
on a DataFrame and obtain a tidy ``samples × discriminators`` table.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, List, Mapping, Optional

import numpy as np
import pandas as pd

from .diagrams.templates.base import resolve_column
from .diagrams.templates.major_df import (
    butler_woronow_df1,
    butler_woronow_df2,
    pearce_1976_df1,
    pearce_1976_df2,
)
from .diagrams.templates.tectonic_bivariate import (
    _NMORB_SUN,
    _yang_fckantms,
    _yang_fcms,
)
from .diagrams.templates.verma_coefficients import (
    DFCoefSet,
    V12_ACID,
    VA11,
    VV13_MAJOR,
    VV13_TRACE,
)
from .diagrams.templates.verma_multidim import (
    _apply_df as _verma_apply_df,
    _logratios_for_coef as _verma_logratios,
)


# ---------------------------------------------------------------------------
# Public dataclass
# ---------------------------------------------------------------------------

ComputeFn = Callable[[pd.DataFrame], Optional[pd.Series]]


@dataclass(frozen=True)
class Discriminator:
    """One per-sample tectonic-discrimination scalar.

    Attributes
    ----------
    key
        Stable identifier (used by the UI to remember user selections).
    label
        Display name for the table header and the selector tree.
    category
        Family the discriminator belongs to (used to group entries in
        the selector tree).
    compute
        Callable ``df → Series`` (indexed like ``df``). Returns
        ``None`` when the input is missing the required columns.
    """
    key: str
    label: str
    category: str
    compute: ComputeFn


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def _to_numeric(df: pd.DataFrame, name: str) -> Optional[pd.Series]:
    col = resolve_column(df, (name,))
    if col is None:
        return None
    return pd.to_numeric(df[col], errors="coerce")


def _ti_ppm(df: pd.DataFrame) -> Optional[pd.Series]:
    """Return Ti in ppm — direct column or computed from TiO₂ wt %."""
    ti = _to_numeric(df, "Ti")
    if ti is not None:
        return ti
    tio2 = _to_numeric(df, "TiO2")
    if tio2 is None:
        return None
    return tio2 * 5995.0


def _ratio(df: pd.DataFrame, num: str, den: str) -> Optional[pd.Series]:
    n = _to_numeric(df, num)
    d = _to_numeric(df, den)
    if n is None or d is None:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        return n / d


def _saccani_normed(df: pd.DataFrame, element: str) -> Optional[pd.Series]:
    if element not in _NMORB_SUN:
        return None
    raw = _to_numeric(df, element)
    if raw is None:
        return None
    return raw / _NMORB_SUN[element]


def _make_verma_df(coef: DFCoefSet) -> ComputeFn:
    """Return a compute(df) that evaluates *coef* using the Verma engine."""
    def _fn(df: pd.DataFrame) -> Optional[pd.Series]:
        lr = _verma_logratios(df, coef)
        if lr is None:
            return None
        return _verma_apply_df(lr, coef)
    return _fn


def _ti_yb(df: pd.DataFrame) -> Optional[pd.Series]:
    ti = _ti_ppm(df)
    yb = _to_numeric(df, "Yb")
    if ti is None or yb is None:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        return ti / yb


def _ti_y(df: pd.DataFrame) -> Optional[pd.Series]:
    ti = _ti_ppm(df)
    y = _to_numeric(df, "Y")
    if ti is None or y is None:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        return ti / y


def _ti_v(df: pd.DataFrame) -> Optional[pd.Series]:
    ti = _ti_ppm(df)
    v = _to_numeric(df, "V")
    if ti is None or v is None:
        return None
    with np.errstate(divide="ignore", invalid="ignore"):
        return ti / v


def _saccani_ce_yb(df):
    ce_n = _saccani_normed(df, "Ce")
    yb_n = _saccani_normed(df, "Yb")
    if ce_n is None or yb_n is None:
        return None
    return ce_n / yb_n


def _saccani_dy_yb(df):
    dy_n = _saccani_normed(df, "Dy")
    yb_n = _saccani_normed(df, "Yb")
    if dy_n is None or yb_n is None:
        return None
    return dy_n / yb_n


# ---------------------------------------------------------------------------
# Catalogue
# ---------------------------------------------------------------------------

def _verma_pairs(table: Mapping[str, DFCoefSet], category: str,
                 prefix: str) -> List[Discriminator]:
    """Expand a full Verma coefficient table (DF1/DF2 × N pairs) into a
    flat list of :class:`Discriminator`."""
    out: List[Discriminator] = []
    # The coefficient tables follow the convention DF1_IAB_MORB,
    # DF2_IAB_MORB, DF1_IAB_OIB, … — preserve insertion order.
    for name, coef in table.items():
        # Pretty-print the suffix: ``DF1_IAB_MORB`` → ``DF1 (IAB-MORB)``
        df_part, _, pair = name.partition("_")
        pair_label = pair.replace("_", "-")
        label = f"{df_part} ({pair_label})"
        out.append(Discriminator(
            key=f"{prefix}.{name.lower()}",
            label=label,
            category=category,
            compute=_make_verma_df(coef),
        ))
    return out


DISCRIMINATORS: List[Discriminator] = [
    # ----- Bivariate ratios (Pearce 2008) -------------------------------
    Discriminator("pearce2008.th_yb", "Th/Yb",
                  "Pearce (2008) — mafic crustal proxy",
                  lambda df: _ratio(df, "Th", "Yb")),
    Discriminator("pearce2008.nb_yb", "Nb/Yb",
                  "Pearce (2008) — mafic crustal proxy",
                  lambda df: _ratio(df, "Nb", "Yb")),
    Discriminator("pearce2008.ti_yb", "Ti/Yb",
                  "Pearce (2008) — mafic crustal proxy", _ti_yb),
    # ----- Pearce & Gale (1977) -----------------------------------------
    Discriminator("pearcegale.zr_y", "Zr/Y",
                  "Pearce & Gale (1977) — within-plate vs plate margin",
                  lambda df: _ratio(df, "Zr", "Y")),
    Discriminator("pearcegale.ti_y", "Ti/Y",
                  "Pearce & Gale (1977) — within-plate vs plate margin",
                  _ti_y),
    # ----- Shervais (1982) ----------------------------------------------
    Discriminator("shervais.ti_v", "Ti/V",
                  "Shervais (1982) — IAB / MORB / OIB", _ti_v),
    Discriminator("shervais.v", "V (ppm)",
                  "Shervais (1982) — IAB / MORB / OIB",
                  lambda df: _to_numeric(df, "V")),
    # ----- Defant & Drummond (1990) -------------------------------------
    Discriminator("dd.sr_y", "Sr/Y",
                  "Defant & Drummond (1990) — adakite vs ADR",
                  lambda df: _ratio(df, "Sr", "Y")),
    Discriminator("dd.la_yb", "La/Yb",
                  "Defant & Drummond (1990) — adakite vs ADR",
                  lambda df: _ratio(df, "La", "Yb")),
    # ----- Saccani (2015) N-MORB normalised ----------------------------
    Discriminator("saccani.nb_n", "Nb_N (N-MORB)",
                  "Saccani (2015) — N-MORB normalised",
                  lambda df: _saccani_normed(df, "Nb")),
    Discriminator("saccani.th_n", "Th_N (N-MORB)",
                  "Saccani (2015) — N-MORB normalised",
                  lambda df: _saccani_normed(df, "Th")),
    Discriminator("saccani.dy_n", "Dy_N (N-MORB)",
                  "Saccani (2015) — N-MORB normalised",
                  lambda df: _saccani_normed(df, "Dy")),
    Discriminator("saccani.yb_n", "Yb_N (N-MORB)",
                  "Saccani (2015) — N-MORB normalised",
                  lambda df: _saccani_normed(df, "Yb")),
    Discriminator("saccani.ce_yb_n", "Ce_N/Yb_N",
                  "Saccani (2015) — N-MORB normalised", _saccani_ce_yb),
    Discriminator("saccani.dy_yb_n", "Dy_N/Yb_N",
                  "Saccani (2015) — N-MORB normalised", _saccani_dy_yb),
    # ----- Yang et al. (2019) -------------------------------------------
    Discriminator("yang.fcms", "FCMS",
                  "Yang et al. (2019) — high-Mg source proxy",
                  _yang_fcms),
    Discriminator("yang.fckantms", "FCKANTMS",
                  "Yang et al. (2019) — high-Mg source proxy",
                  _yang_fckantms),
    # ----- Pearce et al. (1984) ratios ----------------------------------
    Discriminator("pearce1984.y_nb", "Y + Nb",
                  "Pearce et al. (1984) — granitoid discriminants",
                  lambda df: (_to_numeric(df, "Y")
                              + _to_numeric(df, "Nb"))
                              if (_to_numeric(df, "Y") is not None
                                  and _to_numeric(df, "Nb") is not None)
                              else None),
    Discriminator("pearce1984.yb_ta", "Yb + Ta",
                  "Pearce et al. (1984) — granitoid discriminants",
                  lambda df: (_to_numeric(df, "Yb")
                              + _to_numeric(df, "Ta"))
                              if (_to_numeric(df, "Yb") is not None
                                  and _to_numeric(df, "Ta") is not None)
                              else None),
    # ----- Oceanic-basalt DFs (Vermeesch 2006a) -------------------------
    # Two axes each: these are DF1-DF2 binary diagrams, not single-axis
    # scores, so both axes are needed to place a sample.
    Discriminator("df.pearce_1976.df1", "DF1 — Pearce 1976 (IAB-MORB-OIB)",
                  "Oceanic-basalt DFs (Vermeesch 2006a)", pearce_1976_df1),
    Discriminator("df.pearce_1976.df2", "DF2 — Pearce 1976 (IAB-MORB-OIB)",
                  "Oceanic-basalt DFs (Vermeesch 2006a)", pearce_1976_df2),
    Discriminator("df.butler_woronow.df1", "DF1 — Butler & Woronow (Zr-Y-Sr-Ti)",
                  "Oceanic-basalt DFs (Vermeesch 2006a)",
                  butler_woronow_df1),
    Discriminator("df.butler_woronow.df2", "DF2 — Butler & Woronow (Zr-Y-Sr-Ti)",
                  "Oceanic-basalt DFs (Vermeesch 2006a)",
                  butler_woronow_df2),
]

# Verma multi-panel DFs (5 / 5 / 5 / 3 / 4 / 4 = 26 DFs)
DISCRIMINATORS += _verma_pairs(
    VA11,        "Verma & Agrawal (2011) — mafic immobile traces",
    "va11")
DISCRIMINATORS += _verma_pairs(
    VV13_MAJOR,  "Verma & Verma (2013) — intermediate majors",
    "vv13_maj")
DISCRIMINATORS += _verma_pairs(
    VV13_TRACE,  "Verma & Verma (2013) — intermediate immobile traces",
    "vv13_tr")
DISCRIMINATORS += _verma_pairs(
    V12_ACID,    "Verma et al. (2012) — acid rocks",
    "v12_acid")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def discriminator_catalog() -> Dict[str, List[Discriminator]]:
    """Return the catalogue grouped by category (preserves order)."""
    grouped: Dict[str, List[Discriminator]] = {}
    for d in DISCRIMINATORS:
        grouped.setdefault(d.category, []).append(d)
    return grouped


def by_key() -> Dict[str, Discriminator]:
    return {d.key: d for d in DISCRIMINATORS}


def compute_results(df: pd.DataFrame,
                     selected_keys: Iterable[str]) -> pd.DataFrame:
    """Run the selected discriminators on *df* and return a tidy table.

    Parameters
    ----------
    df
        Bulk-rock dataset; only the columns required by each discriminator
        are read.
    selected_keys
        Iterable of :class:`Discriminator` keys to include. Unknown keys
        are silently ignored.

    Returns
    -------
    pandas.DataFrame
        Indexed like *df*; one column per successfully-computed
        discriminator. Failed computations (missing input columns) are
        skipped without raising.
    """
    if df is None or df.empty:
        return pd.DataFrame(index=df.index if df is not None else None)
    catalog = by_key()
    out = pd.DataFrame(index=df.index)
    for key in selected_keys:
        disc = catalog.get(key)
        if disc is None:
            continue
        try:
            series = disc.compute(df)
        except Exception:                                  # noqa: BLE001
            continue
        if series is None:
            continue
        out[disc.label] = pd.to_numeric(series, errors="coerce").round(4)
    return out
