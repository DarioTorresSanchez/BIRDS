"""The Map view, drawn on longitude/latitude axes with no background map.

The view used to draw samples over web map tiles.  Those are gone,
along with everything that existed to serve them -- the tile download,
its timeout and worker thread, the joblib warning filter, and the Web
Mercator projection the axes were drawn in only because tiles come in
it.  What is left plots longitude against latitude with the aspect
ratio fixed at the centre latitude: the equirectangular projection,
with that latitude as its standard parallel.

Lengths of a degree come from the WGS-84 ellipsoid, not from 111 km,
and are checked against the standard table to the table's own rounding.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from birds.views.map_view import (
    AXES_CRS,
    MIN_FRAME_KM,
    _add_scale_bar,
    _nice_round,
    auto_scale_length_km,
    km_per_degree_lat,
    km_per_degree_lon,
    map_aspect,
    map_frame,
    migrate_annotations_to_lonlat,
)

ROOT = Path(__file__).resolve().parents[1]

#: Standard WGS-84 table: length of one degree, km, as (latitude, longitude).
WGS84_TABLE = {
    0: (110.574, 111.320),
    15: (110.649, 107.551),
    30: (110.852, 96.486),
    45: (111.133, 78.847),
    60: (111.412, 55.800),
    75: (111.618, 28.902),
}


# ---------------------------------------------------------------------------
# Lengths on the ellipsoid
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lat, expected", sorted(WGS84_TABLE.items()))
def test_a_degree_is_as_long_as_the_wgs84_table_says(lat, expected):
    """To the table's own rounding: the worst case is 1.2 m at 45°."""
    want_lat, want_lon = expected
    assert km_per_degree_lat(lat) == pytest.approx(want_lat, abs=0.0015)
    assert km_per_degree_lon(lat) == pytest.approx(want_lon, abs=0.0015)


def test_a_degree_of_latitude_lengthens_toward_the_pole():
    """The ellipsoid is flattened, so the meridian curves less there."""
    lats = np.linspace(0, 90, 19)
    lengths = [km_per_degree_lat(x) for x in lats]
    assert lengths == sorted(lengths)
    assert km_per_degree_lat(90) == pytest.approx(111.694, abs=0.001)


def test_a_degree_of_longitude_never_reaches_zero():
    """It does on the ground, at the pole; the floor keeps the aspect
    ratio and the scale bar finite."""
    assert km_per_degree_lon(90) > 0
    assert np.isfinite(map_aspect(90))
    assert map_aspect(90) == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# The aspect ratio
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lat0", [0.0, 19.43, -33.9, 45.0, 60.0])
def test_a_ground_square_draws_as_a_square(lat0):
    """The whole point of the aspect ratio, checked as stated.

    A 10 km square at lat0 spans different numbers of degrees east-west
    and north-south; with the aspect applied its drawn width and height
    have to come out equal.
    """
    side_km = 10.0
    dlon = side_km / km_per_degree_lon(lat0)
    dlat = side_km / km_per_degree_lat(lat0)
    drawn_width = dlon
    drawn_height = dlat * map_aspect(lat0)
    assert drawn_height == pytest.approx(drawn_width, rel=1e-12)


@pytest.mark.parametrize("lat0", [0.0, 19.43, 45.0, 60.0])
def test_the_aspect_is_close_to_the_spherical_one(lat0):
    """1/cos(lat0) on a sphere; the ellipsoid moves it by under 0.7 %."""
    spherical = 1.0 / np.cos(np.radians(lat0))
    assert map_aspect(lat0) == pytest.approx(spherical, rel=0.007)


# ---------------------------------------------------------------------------
# The frame
# ---------------------------------------------------------------------------

def test_a_single_sample_gets_a_frame_of_the_minimum_size():
    """Both ways, on the ground -- not the same number of degrees."""
    lon_lo, lon_hi, lat_lo, lat_hi, lat0 = map_frame(
        [-99.1332], [19.4326], pad=0.0)
    assert lat0 == pytest.approx(19.4326)
    assert (lon_hi - lon_lo) * km_per_degree_lon(lat0) == pytest.approx(
        MIN_FRAME_KM)
    assert (lat_hi - lat_lo) * km_per_degree_lat(lat0) == pytest.approx(
        MIN_FRAME_KM)
    assert (lon_lo + lon_hi) / 2 == pytest.approx(-99.1332)


def test_a_wide_spread_is_not_widened():
    lons, lats = [-100.0, -98.0], [18.0, 21.0]
    lon_lo, lon_hi, lat_lo, lat_hi, lat0 = map_frame(lons, lats, pad=0.0)
    assert (lon_lo, lon_hi, lat_lo, lat_hi) == pytest.approx(
        (-100.0, -98.0, 18.0, 21.0))
    assert lat0 == pytest.approx(19.5)


def test_padding_is_a_fraction_of_each_span():
    lon_lo, lon_hi, lat_lo, lat_hi, _ = map_frame(
        [-100.0, -98.0], [18.0, 21.0], pad=0.10)
    assert (lon_lo, lon_hi) == pytest.approx((-100.2, -97.8))
    assert (lat_lo, lat_hi) == pytest.approx((17.7, 21.3))


# ---------------------------------------------------------------------------
# The scale bar
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("lat0", [0.0, 19.43, 60.0])
def test_the_scale_bar_is_as_long_as_it_says(lat0):
    """Measured along the standard parallel, where east-west is true."""
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.set_xlim(-100.0, -98.0)
    ax.set_ylim(lat0 - 1.0, lat0 + 1.0)
    line, text = _add_scale_bar(ax, length_km=50.0, lat0=lat0)
    x0, x1 = line.get_xdata()
    assert (x1 - x0) * km_per_degree_lon(lat0) == pytest.approx(50.0)
    assert text.get_text() == "50 km"


def test_the_automatic_length_is_tidy_and_about_a_fifth_of_the_frame():
    for lat0 in (0.0, 19.43, 60.0):
        for width_deg in (0.05, 0.4, 2.0, 15.0):
            length = auto_scale_length_km(0.0, width_deg, lat0)
            mantissa = length / 10 ** np.floor(np.log10(length))
            assert round(mantissa, 9) in (1.0, 2.0, 5.0, 10.0)
            width_km = width_deg * km_per_degree_lon(lat0)
            assert 0.1 * width_km <= length <= 0.4 * width_km


def test_nice_round_picks_one_two_or_five():
    assert [_nice_round(v) for v in (0.9, 1.4, 2.6, 4.0, 8.0, 87.4)] == [
        1.0, 1.0, 2.0, 5.0, 10.0, 100.0]


# ---------------------------------------------------------------------------
# Sessions saved by the earlier, Mercator-based view
# ---------------------------------------------------------------------------

R = 6_378_137.0


def _legacy(lon, lat):
    """Forward spherical Mercator, as the old view stored coordinates."""
    return (R * np.radians(lon),
            R * np.log(np.tan(np.pi / 4 + np.radians(lat) / 2)))


def test_legacy_line_and_text_annotations_come_back_in_degrees():
    x1, y1 = _legacy(-99.1332, 19.4326)
    x2, y2 = _legacy(-98.2063, 19.0414)
    tx, ty = _legacy(-98.5, 19.2)
    out = migrate_annotations_to_lonlat([
        {"kind": "line", "x1": x1, "y1": y1, "x2": x2, "y2": y2},
        {"kind": "arrow", "x1": x2, "y1": y2, "x2": x1, "y2": y1},
        {"kind": "text", "x": tx, "y": ty, "text": "Popocatépetl"},
    ])
    assert (out[0]["x1"], out[0]["y1"]) == pytest.approx((-99.1332, 19.4326))
    assert (out[0]["x2"], out[0]["y2"]) == pytest.approx((-98.2063, 19.0414))
    assert (out[1]["x1"], out[1]["y1"]) == pytest.approx((-98.2063, 19.0414))
    assert (out[2]["x"], out[2]["y"]) == pytest.approx((-98.5, 19.2))
    assert out[2]["text"] == "Popocatépetl"


def test_a_sample_label_keeps_its_place_relative_to_the_sample():
    """An offset in metres is not an offset in degrees.

    So the label position is converted and the offset recomputed from
    it, rather than the offset being converted on its own.
    """
    px, py = _legacy(-99.0, 19.0)
    lx, ly = _legacy(-98.9, 19.05)
    out = migrate_annotations_to_lonlat([
        {"kind": "sample", "px": px, "py": py,
         "dx": lx - px, "dy": ly - py, "label": "BIRDS-01"},
    ])[0]
    assert (out["px"], out["py"]) == pytest.approx((-99.0, 19.0))
    assert (out["px"] + out["dx"], out["py"] + out["dy"]) == pytest.approx(
        (-98.9, 19.05))


def test_migration_leaves_what_it_cannot_read_alone():
    odd = [{"kind": "text"}, {"kind": "mystery", "x": 1.0}, "not a dict"]
    assert migrate_annotations_to_lonlat(odd) == odd
    assert migrate_annotations_to_lonlat([]) == []
    assert migrate_annotations_to_lonlat(None) is None


# ---------------------------------------------------------------------------
# The widget
# ---------------------------------------------------------------------------

@pytest.fixture
def view(qapp):
    from birds.data_manager import DataManager
    from birds.plot_style import PlotStyle
    from birds.views.map_view import MapView

    data = DataManager()
    data.df = pd.DataFrame({
        "Sample": ["A", "B", "C"],
        "Latitude": [19.43, 19.05, 18.90],
        "Longitude": [-99.13, -98.21, -98.62],
    })
    v = MapView(data, PlotStyle())
    v.show_map()
    return v


def test_the_map_is_drawn_in_degrees(view):
    ax = view.canvas.figure.axes[0]
    lo, hi = ax.get_xlim()
    assert lo < -99.13 and hi > -98.21          # longitudes, not metres
    lo, hi = ax.get_ylim()
    assert lo < 18.90 and hi > 19.43
    assert ax.get_xlabel() == "Longitude"
    assert ax.get_ylabel() == "Latitude"
    lat0 = (19.43 + 18.90) / 2
    assert ax.get_aspect() == pytest.approx(map_aspect(lat0))


def test_the_widget_carries_no_background_map_controls(view):
    assert not hasattr(view, "basemap_combo")
    assert not hasattr(view, "basemap_alpha")


def test_a_saved_session_records_its_units_and_nothing_else_of_old(view):
    state = view.serialize()
    assert state["axes_crs"] == AXES_CRS == "lonlat"
    assert not [k for k in state if "basemap" in k.lower()]


def test_an_old_session_is_restored_and_its_annotations_converted(view):
    x, y = _legacy(-98.5, 19.2)
    old = {
        "fmt": "decimal", "lat": "Latitude", "lon": "Longitude",
        "basemap": "Satellite (Esri WorldImagery)", "basemap_alpha": 0.8,
        "annotations": [{"kind": "text", "x": x, "y": y, "text": "old"}],
    }
    view.restore(old)                   # must not raise on the old keys
    ann = view.annotation_ctl.annotations[0]
    assert (ann.x, ann.y) == pytest.approx((-98.5, 19.2))


def test_a_new_session_is_never_converted_twice(view):
    """Save, restore, save: the coordinates must not move."""
    view.restore({"axes_crs": AXES_CRS, "annotations": [
        {"kind": "text", "x": -98.5, "y": 19.2, "text": "new"}]})
    first = view.serialize()["annotations"]
    view.restore(view.serialize())
    second = view.serialize()["annotations"]
    assert second == first
    assert (second[0]["x"], second[0]["y"]) == pytest.approx((-98.5, 19.2))


# ---------------------------------------------------------------------------
# Nothing of the background map left anywhere
# ---------------------------------------------------------------------------

#: Words that only ever meant the web map tiles.  "Mercator" is not on
#: the list: the session migration has to name the old units.
_GONE = re.compile(r"basemap|contextily|xyzservices|cartodb|worldimagery|"
                   r"worldtopomap", re.IGNORECASE)


def _shipped_text_files():
    files = sorted((ROOT / "birds").rglob("*.py"))
    files += [ROOT / name for name in (
        "requirements.txt", "pyproject.toml", "README.md", "INSTALL.md",
        "main.py")]
    files += [ROOT / "docs" / "manual_content.py"]
    return [f for f in files if f.exists()]


@pytest.mark.parametrize("path", _shipped_text_files(),
                         ids=lambda p: str(p.relative_to(ROOT)))
def test_no_background_map_is_left_in_what_ships(path):
    """Code, dependencies and the documents a user reads.

    The CHANGELOG is the one place the words may stay: it records that
    the feature was removed and why, which is what a changelog is for.
    """
    hits = [(n, line.strip()) for n, line in
            enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
            if _GONE.search(line)]
    assert not hits, f"{path.name}: {hits[:3]}"
