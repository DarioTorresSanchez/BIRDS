"""Mg#, trace ratios, alteration indices and anomalies, sample by sample.

What the data table appends to the Data sheet as calculated columns.
Every value comes from the statistics engine -- the functions that fill
the Statistics view's per-sample tabs -- and the Mg# from the derived
variables the bivariate axes plot, so a number here, in Statistics and
on a diagram is always the same number.

Nothing is written into the dataset: the columns are worked out from
the data as they stand each time they are shown, so an edited cell can
never leave them stale, and a column of the user's own under the same
name (a Mg# of their own, say) is shown as theirs, not shadowed.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from .derived import DERIVED, DESCRIPTIONS as _MG_DESCRIPTIONS, derived_series
from .stats_engine import (
    ALTERATION_DESCRIPTIONS,
    ANOMALY_DESCRIPTIONS,
    available_normalisers,
    compute_alteration_indices,
    compute_anomalies_extended,
    compute_ratios,
    ratio_description,
)

#: The kinds of calculated column, in the order they are appended.
MG_NUMBER, RATIO, ALTERATION, ANOMALY = "mg", "ratio", "alteration", "anomaly"

#: Anomalies beyond these read as positive / negative, as the
#: Statistics view colours them: X/X* against 1, Y/Ho against chondrite.
ANOMALY_HIGH, ANOMALY_LOW = 1.05, 0.95
Y_HO_HIGH, Y_HO_LOW = 32.0, 24.0


def default_normaliser() -> str:
    """The chondrite the anomalies use unless another is picked -- the
    Statistics view's default."""
    return available_normalisers()[0]


def calculated_columns(data, normaliser_name: Optional[str] = None
                       ) -> pd.DataFrame:
    """Every calculated column for the Data sheet of *data* (a
    DataManager), indexed like it.

    Mg# as the derived variables (``Mg#``, ``Mg#_FeOt``, ``Mg#_adj``);
    then the trace ratios and the alteration indices, read from the
    majors the adjusted-majors switch selects (Ti from TiO2 where there
    is no Ti column); then the anomalies against *normaliser_name*.
    Columns the sheet already has are left out.
    """
    df = data.df
    if df is None or df.empty:
        return pd.DataFrame()
    majors = data.majors_df()
    parts = []

    mg = {}
    for name in DERIVED:
        series = derived_series(df, name)
        if series is not None and series.notna().any():
            mg[name] = series
    parts.append(pd.DataFrame(mg, index=df.index))

    ratios = compute_ratios(majors)
    alteration = compute_alteration_indices(majors)
    parts.append(ratios[[c for c in ratios.columns
                         if c not in alteration.columns
                         and not c.startswith("Mg#")]])
    parts.append(alteration)
    parts.append(compute_anomalies_extended(
        majors, normaliser_name or default_normaliser()))

    out = pd.concat(parts, axis=1)
    out = out.loc[:, ~out.columns.duplicated()]
    keep = [c for c in out.columns
            if c not in df.columns and out[c].notna().any()]
    return out[keep]


def kind(name: str) -> str:
    """Which kind of calculated column *name* is."""
    if name in DERIVED:
        return MG_NUMBER
    if name in ALTERATION_DESCRIPTIONS:
        return ALTERATION
    if name in ANOMALY_DESCRIPTIONS:
        return ANOMALY
    return RATIO


def describe(name: str, normaliser_name: Optional[str] = None) -> str:
    """What the calculated column *name* is, for its tooltip."""
    if name in _MG_DESCRIPTIONS:
        text = _MG_DESCRIPTIONS[name]
    elif name in ALTERATION_DESCRIPTIONS:
        text = ALTERATION_DESCRIPTIONS[name]
    elif name in ANOMALY_DESCRIPTIONS:
        text = ANOMALY_DESCRIPTIONS[name]
        if "chondrite-normalised" in text:
            text += (f" Chondrite: {normaliser_name or default_normaliser()}.")
    else:
        text = ratio_description(name) or name
    return text


def anomaly_sign(name: str, value: float) -> int:
    """+1 for a positive anomaly, -1 for a negative one, 0 otherwise --
    the Statistics view's colour key."""
    if value is None or pd.isna(value):
        return 0
    if name.endswith("*"):
        return 1 if value > ANOMALY_HIGH else -1 if value < ANOMALY_LOW else 0
    if name == "Y/Ho":
        return 1 if value > Y_HO_HIGH else -1 if value < Y_HO_LOW else 0
    return 0
