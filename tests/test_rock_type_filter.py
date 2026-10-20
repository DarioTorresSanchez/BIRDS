"""The volcanic / plutonic filter of the Classification and Tectonic views.

Blank Rock_Type cells are kept on both families.  Under pandas 3 a blank
cell stays NaN through ``astype(str)`` (pandas 2 wrote "nan"), and the
filter only knew the text: an all-blank Rock_Type column -- the data
template left unfilled, as four of the user's six sessions have it --
dropped every sample, and every classification and tectonic diagram
drew nothing.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.composition import filter_by_rock_type


@pytest.mark.parametrize("blank", [
    pd.Series([np.nan] * 3),                       # an empty Excel column
    pd.Series([pd.NA] * 3, dtype="string"),
    pd.Series([None] * 3, dtype=object),
    pd.Series(["", " ", "nan"]),
])
@pytest.mark.parametrize("family", ["volcanic", "plutonic"])
def test_blank_rock_types_are_kept(blank, family):
    df = pd.DataFrame({"Rock_Type": blank, "SiO2": [50.0, 60.0, 70.0]})
    kept, info = filter_by_rock_type(df, family)
    assert len(kept) == 3
    assert info["blank"] == 3 and info["dropped"] == 0


def test_the_family_is_matched_and_the_rest_dropped():
    df = pd.DataFrame({"Rock_Type": ["Volcanic", "PLUTONIC", np.nan,
                                     "extrusive", "dyke?"]})
    kept, info = filter_by_rock_type(df, "volcanic")
    assert list(kept.index) == [0, 2, 3]
    assert (info["kept"], info["dropped"], info["blank"]) == (3, 2, 1)
    kept, _ = filter_by_rock_type(df, "plutonic")
    assert list(kept.index) == [1, 2]


def test_a_blank_rock_type_column_still_plots_every_sample(qapp, full_df):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    df = full_df.copy()
    df["Rock_Type"] = np.nan
    w.data.df = df
    w.on_dataset_replaced()
    for family in ("volcanic", "plutonic"):
        w._open_classification_family(family)
        report = w.classification.count_label._report
        assert report.filtered == 0, family
        assert report.plotted + report.missing + report.offframe == len(df)
    w._open_tectonic("pearce2008_thyb_nbyb", "volcanic", "Mafic")
    assert w.tectonic.count_label._report.filtered == 0
