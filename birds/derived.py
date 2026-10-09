"""Quantities computed from the analysis rather than read from a column.

For now the magnesium number, offered as an axis in the bivariate view.
It is not written into the dataset -- it is worked out whenever an axis
asks for it -- so it always follows the data as they stand.  The
definitions are those of the statistics table
(:func:`birds.stats_engine.compute_mg_number`), so an axis and a table
row with the same name always agree:

``Mg#``
    100 × Mg / (Mg + Fe²⁺), molar, with the *measured* FeO.  Offered only
    when FeO and Fe₂O₃ were reported separately.

``Mg#_FeOt``
    The same with all iron as Fe²⁺ (FeOt) -- what most papers mean when
    only total iron was measured.  A 100 % rescale divides MgO and FeOt
    by the same factor, so it is unchanged by adjustment.

``Mg#_adj``
    ``Mg#`` of the adjusted majors: Fe²⁺ is the FeO of the iron partition
    chosen in *Data → Pre-process majors…*.  Offered once the majors have
    been adjusted.

A column the user named the same way always wins over the derived one.
"""

from __future__ import annotations

from typing import Mapping, Optional

import pandas as pd

from .preprocess import adjusted_name, has_adjusted, with_adjusted_majors

MG_NUMBER = "Mg#"
MG_NUMBER_FEOT = "Mg#_FeOt"
MG_NUMBER_ADJ = adjusted_name(MG_NUMBER)

#: Every derived variable, in the order the variable lists offer them.
DERIVED = (MG_NUMBER, MG_NUMBER_FEOT, MG_NUMBER_ADJ)

#: What each one is, for tooltips.
DESCRIPTIONS = {
    MG_NUMBER: "Mg# = 100·Mg/(Mg+Fe²⁺), molar, with the measured FeO.",
    MG_NUMBER_FEOT: "Mg# with all iron as Fe²⁺ (FeOt). Unchanged by the "
                    "100 % adjustment.",
    MG_NUMBER_ADJ: "Mg# of the adjusted majors: Fe²⁺ is the FeO of the "
                   "iron partition chosen in Data → Pre-process majors….",
}

# Molar masses, as the statistics table uses them.
_MW_MGO = 40.304
_MW_FEO = 71.844


def derived_series(df: pd.DataFrame, name: str) -> Optional[pd.Series]:
    """The derived variable *name* for every row of *df*, or None when
    the columns it needs are not there."""
    from .stats_engine import compute_mg_number

    if name in (MG_NUMBER, MG_NUMBER_FEOT):
        table = compute_mg_number(df)
    elif name == MG_NUMBER_ADJ:
        if not has_adjusted(df):
            return None
        table = compute_mg_number(with_adjusted_majors(df)).rename(
            columns={MG_NUMBER: MG_NUMBER_ADJ})
    else:
        return None
    if name not in table.columns:
        return None
    return table[name].rename(name)


def available(df: Optional[pd.DataFrame]) -> list:
    """The derived variables *df* can provide, except any the user
    already has as a column of the same name."""
    if df is None or df.empty:
        return []
    return [name for name in DERIVED
            if name not in df.columns
            and derived_series(df, name) is not None]


def derived_scalar(values: Mapping[str, float], name: str
                   ) -> Optional[float]:
    """The derived variable for one composition -- a reservoir.

    Reference compositions give total iron, so every flavour reads as
    ``Mg#_FeOt`` for them: they have no measured FeO split and are not
    adjusted.
    """
    if name not in DERIVED:
        return None
    mgo = values.get("MgO")
    feo = None
    for key in ("FeOt", "FeOT", "FeO*", "FeO"):
        if values.get(key) is not None:
            feo = values[key]
            break
    if mgo is None or feo is None:
        return None
    mg = float(mgo) / _MW_MGO
    fe = float(feo) / _MW_FEO
    total = mg + fe
    return 100.0 * mg / total if total > 0 else None
