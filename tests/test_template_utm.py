"""The data template carries UTM columns beside the degrees.

Easting, Northing, UTM_Zone and Hemisphere -- the four the map's UTM
format reads -- so a dataset kept in UTM fits the template as it is.
Their example row is the same place as the template's Latitude and
Longitude.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs"))

from generate_template import context_columns  # noqa: E402

UTM = ("Easting", "Northing", "UTM_Zone", "Hemisphere")


def _columns():
    return {c.name: c for c in context_columns()}


def test_the_four_utm_columns_follow_the_degrees():
    names = [c.name for c in context_columns()]
    at = names.index("Longitude")
    assert tuple(names[at + 1:at + 5]) == UTM
    assert tuple(_columns()["Hemisphere"].options) == ("N", "S")


def test_the_example_row_is_the_same_place_in_both():
    from birds import coords
    cols = _columns()
    row = pd.DataFrame({name: [cols[name].example] for name in UTM})
    lat, lon = coords.from_utm(row, "Easting", "Northing",
                               zone_col="UTM_Zone",
                               hemisphere_col="Hemisphere",
                               fixed_zone=None, fixed_hemisphere=None)
    assert lat.iloc[0] == pytest.approx(float(cols["Latitude"].example),
                                        abs=1e-4)
    assert lon.iloc[0] == pytest.approx(float(cols["Longitude"].example),
                                        abs=1e-4)


def test_the_written_templates_have_them():
    header = (ROOT / "templates" / "BIRDS_data_template.csv").read_text(
        encoding="utf-8").splitlines()[0]
    assert all(name in header for name in UTM)


def test_the_map_points_at_utm_when_the_degrees_are_empty(qapp, full_df):
    from birds.main_window import BirdsMainWindow
    w = BirdsMainWindow()
    df = full_df.copy()
    df["Latitude"] = np.nan
    df["Longitude"] = np.nan
    df["Easting"] = np.linspace(640_000, 680_000, len(df))
    df["Northing"] = np.linspace(2_090_000, 2_170_000, len(df))
    df["UTM_Zone"] = 14
    df["Hemisphere"] = "N"
    w.data.df = df
    w.on_dataset_replaced()
    w._open_map()
    samples, message = w.map._collect()
    assert samples is None
    assert "Easting" in message and "UTM" in message
