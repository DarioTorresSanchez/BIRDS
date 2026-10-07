"""Coordinate format parsers for the Map view.

Every public function returns a ``(lat, lon)`` tuple of float ``pd.Series``
in **decimal degrees, WGS-84**.  Bad / unparseable rows become ``NaN`` so
the caller can mask them downstream — no exceptions for individual rows.

Supported formats:

* ``decimal``  — already lat/lon decimal degrees (signed).  Pass-through.
* ``utm``      — Easting (m), Northing (m), Zone (1–60), Hemisphere (N/S).
                 Uses :mod:`pyproj` for the projection.
* ``dms``      — strings like ``19°25'10"N`` or ``19 25 10 N``.  Robust
                 regex parser, accepts ``°``, ``º``, ``deg``, ``'``, ``"``
                 separators and ``N/S/E/W`` suffix.
* ``suffix``   — decimal degrees with a trailing letter, e.g. ``19.42N``,
                 ``99.13W``.  Sign inferred from the suffix.
* ``mgrs``     — Military Grid Reference System (e.g. ``14QMG5780012345``).
                 Uses :mod:`mgrs` if installed.

Each function tolerates a single column being missing — it just returns
NaN-filled series of the right length.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

import numpy as np
import pandas as pd

# Optional deps — imported lazily so the module loads even without them.
try:
    import pyproj
    _HAS_PYPROJ = True
except ImportError:
    _HAS_PYPROJ = False

try:
    import mgrs as _mgrs_lib
    _MGRS = _mgrs_lib.MGRS()
    _HAS_MGRS = True
except ImportError:
    _HAS_MGRS = False


# Canonical alias lists kept here so the column auto-detector can reach
# them without re-importing the map view.
LAT_ALIASES = ("Latitude", "Lat", "lat", "LAT",
               "Latitud", "latitud", "LATITUD",
               "Y", "y_coord", "y")
LON_ALIASES = ("Longitude", "Lon", "lon", "Lng", "lng",
               "LONG", "LON", "long",
               "Longitud", "longitud", "LONGITUD",
               "X", "x_coord", "x")
EASTING_ALIASES = ("Easting", "easting", "UTM_E", "UTM_Easting",
                   "X_UTM", "Este", "este")
NORTHING_ALIASES = ("Northing", "northing", "UTM_N", "UTM_Northing",
                    "Y_UTM", "Norte", "norte")
ZONE_ALIASES = ("Zone", "zone", "UTM_Zone", "Zona", "zona", "UTM_zona")
HEMISPHERE_ALIASES = ("Hemisphere", "hemisphere", "Hem", "hem",
                      "Hemisferio", "hemisferio", "N/S")
MGRS_ALIASES = ("MGRS", "mgrs", "MGRS_Grid", "Grid")
DMS_LAT_ALIASES = ("Lat_DMS", "Latitude_DMS", "Latitud_DMS")
DMS_LON_ALIASES = ("Lon_DMS", "Longitude_DMS", "Longitud_DMS",
                   "Lng_DMS", "Long_DMS")


# ---------------------------------------------------------------------------
# The WGS-84 ellipsoid
# ---------------------------------------------------------------------------
#
# One definition for the whole program.  The UTM fallback below, the Map
# view's aspect ratio and scale bar, and the distances the geostatistics
# work on all read these; they used to be typed out in two places.

#: Defining constants: semi-major axis (m) and flattening.
WGS84_A_M = 6378137.0
WGS84_F = 1.0 / 298.257223563
#: First eccentricity squared, derived rather than typed.
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)


def km_per_degree_lat(lat_deg):
    """Length of one degree of latitude along the meridian at *lat_deg*.

    (π/180)·M(φ), with M the meridional radius of curvature: 110.57 km
    at the equator, 111.69 km at the poles.  Accepts arrays.
    """
    s2 = np.sin(np.radians(lat_deg)) ** 2
    m_km = (WGS84_A_M / 1000.0) * (1.0 - WGS84_E2) \
        / (1.0 - WGS84_E2 * s2) ** 1.5
    return np.radians(1.0) * m_km


def km_per_degree_lon(lat_deg):
    """Length of one degree of longitude along the parallel at *lat_deg*.

    (π/180)·N(φ)·cos φ, with N the prime-vertical radius of curvature:
    111.32 km at the equator, 55.80 km at 60°, nothing at the poles.
    Accepts arrays.
    """
    phi = np.radians(lat_deg)
    n_km = (WGS84_A_M / 1000.0) / np.sqrt(1.0 - WGS84_E2 * np.sin(phi) ** 2)
    return np.radians(1.0) * n_km * np.cos(phi)


def geodetic_to_ecef_km(lon_deg, lat_deg) -> np.ndarray:
    """Earth-centred Cartesian coordinates, in km, of points on the ellipsoid.

    Returns an ``(n, 3)`` array.  The straight-line distance between two
    of these is the chord through the Earth, which differs from the
    distance along the surface by under one part in 10⁵ at 100 km and
    one in 10³ at 1000 km -- and, unlike a map projection, distorts
    nothing anywhere on the globe.
    """
    lon = np.radians(np.asarray(lon_deg, dtype=float).ravel())
    lat = np.radians(np.asarray(lat_deg, dtype=float).ravel())
    n_km = (WGS84_A_M / 1000.0) / np.sqrt(1.0 - WGS84_E2 * np.sin(lat) ** 2)
    x = n_km * np.cos(lat) * np.cos(lon)
    y = n_km * np.cos(lat) * np.sin(lon)
    z = n_km * (1.0 - WGS84_E2) * np.sin(lat)
    return np.column_stack([x, y, z])


def _empty(df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
    nan = pd.Series([np.nan] * len(df), index=df.index, dtype=float)
    return nan.copy(), nan.copy()


# ---------------------------------------------------------------------------
# Decimal degrees (pass-through with coercion)
# ---------------------------------------------------------------------------

def from_decimal(df: pd.DataFrame, lat_col: str,
                 lon_col: str) -> Tuple[pd.Series, pd.Series]:
    """Parse signed decimal degree columns.  ``lat`` clipped to ±90,
    ``lon`` to ±180; out-of-range values are NaN'd."""
    if lat_col not in df.columns or lon_col not in df.columns:
        return _empty(df)
    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lon = pd.to_numeric(df[lon_col], errors="coerce")
    lat = lat.where(lat.between(-90, 90))
    lon = lon.where(lon.between(-180, 180))
    return lat, lon


# ---------------------------------------------------------------------------
# UTM — Easting / Northing / Zone / Hemisphere
# ---------------------------------------------------------------------------

def from_utm(df: pd.DataFrame, easting_col: str, northing_col: str,
             zone_col: Optional[str] = None,
             hemisphere_col: Optional[str] = None,
             fixed_zone: Optional[int] = None,
             fixed_hemisphere: str = "N") -> Tuple[pd.Series, pd.Series]:
    """Convert UTM (Easting, Northing, Zone, Hemisphere) → lat/lon WGS-84.

    Zone and hemisphere may come either from columns OR be fixed for the
    whole dataset (e.g. all samples in zone 14N).  ``fixed_*`` overrides
    the column choice.
    """
    if not _HAS_PYPROJ:
        # No pyproj — fall back to Snyder series expansion (≈1 m accuracy
        # within the zone).  Good enough for sample-plot maps.
        return _from_utm_fallback(df, easting_col, northing_col,
                                  zone_col, hemisphere_col,
                                  fixed_zone, fixed_hemisphere)
    if easting_col not in df.columns or northing_col not in df.columns:
        return _empty(df)
    e = pd.to_numeric(df[easting_col], errors="coerce")
    n = pd.to_numeric(df[northing_col], errors="coerce")
    # Resolve per-row zone + hemisphere
    if fixed_zone is not None:
        zone_series = pd.Series([fixed_zone] * len(df), index=df.index)
    elif zone_col and zone_col in df.columns:
        zone_series = pd.to_numeric(df[zone_col], errors="coerce")
    else:
        return _empty(df)
    if fixed_hemisphere:
        hem_series = pd.Series([fixed_hemisphere.upper()] * len(df),
                               index=df.index)
    elif hemisphere_col and hemisphere_col in df.columns:
        hem_series = df[hemisphere_col].astype(str).str.upper().str[0]
    else:
        hem_series = pd.Series(["N"] * len(df), index=df.index)

    lat_out = pd.Series(np.nan, index=df.index, dtype=float)
    lon_out = pd.Series(np.nan, index=df.index, dtype=float)
    # Build one Transformer per (zone, hemisphere) combo — typical
    # datasets have ≤ 2-3, so caching is cheap.
    cache: dict = {}
    for idx in df.index:
        try:
            ee = float(e.loc[idx])
            nn = float(n.loc[idx])
            zz = int(zone_series.loc[idx])
            hh = str(hem_series.loc[idx]).upper()
        except (ValueError, TypeError):
            continue
        if not np.isfinite(ee) or not np.isfinite(nn):
            continue
        if not (1 <= zz <= 60):
            continue
        if hh not in ("N", "S"):
            continue
        key = (zz, hh)
        if key not in cache:
            south = (hh == "S")
            crs_src = pyproj.CRS.from_dict({
                "proj": "utm", "zone": zz,
                "south": south, "datum": "WGS84",
            })
            cache[key] = pyproj.Transformer.from_crs(
                crs_src, "EPSG:4326", always_xy=True)
        lon_v, lat_v = cache[key].transform(ee, nn)
        lat_out.loc[idx] = lat_v
        lon_out.loc[idx] = lon_v
    return lat_out, lon_out


def _from_utm_fallback(df, easting_col, northing_col,
                       zone_col, hemisphere_col,
                       fixed_zone, fixed_hemisphere):
    """Pure-Python UTM → lat/lon using Snyder (1987) series.  Used only
    if pyproj is missing — accuracy is ~1 m, good enough for maps."""
    if easting_col not in df.columns or northing_col not in df.columns:
        return _empty(df)
    e = pd.to_numeric(df[easting_col], errors="coerce")
    n = pd.to_numeric(df[northing_col], errors="coerce")
    if fixed_zone is not None:
        zones = pd.Series([fixed_zone] * len(df), index=df.index)
    elif zone_col and zone_col in df.columns:
        zones = pd.to_numeric(df[zone_col], errors="coerce")
    else:
        return _empty(df)
    if fixed_hemisphere:
        hems = pd.Series([fixed_hemisphere.upper()] * len(df), index=df.index)
    elif hemisphere_col and hemisphere_col in df.columns:
        hems = df[hemisphere_col].astype(str).str.upper().str[0]
    else:
        hems = pd.Series(["N"] * len(df), index=df.index)

    a = WGS84_A_M
    k0 = 0.9996
    e2 = WGS84_E2
    ep2 = e2 / (1 - e2)

    lat_out = pd.Series(np.nan, index=df.index, dtype=float)
    lon_out = pd.Series(np.nan, index=df.index, dtype=float)
    for idx in df.index:
        try:
            ee = float(e.loc[idx])
            nn = float(n.loc[idx])
            zz = int(zones.loc[idx])
            hh = str(hems.loc[idx]).upper()
        except (ValueError, TypeError):
            continue
        if not np.isfinite(ee) or not np.isfinite(nn) or not (1 <= zz <= 60):
            continue
        if hh == "S":
            nn -= 10_000_000.0
        x = ee - 500_000.0
        m = nn / k0
        mu = m / (a * (1 - e2/4 - 3*e2**2/64 - 5*e2**3/256))
        e1 = (1 - np.sqrt(1 - e2)) / (1 + np.sqrt(1 - e2))
        phi1 = (mu
                + (3*e1/2 - 27*e1**3/32) * np.sin(2*mu)
                + (21*e1**2/16 - 55*e1**4/32) * np.sin(4*mu)
                + (151*e1**3/96) * np.sin(6*mu))
        c1 = ep2 * np.cos(phi1)**2
        t1 = np.tan(phi1)**2
        n1 = a / np.sqrt(1 - e2 * np.sin(phi1)**2)
        r1 = a * (1 - e2) / (1 - e2 * np.sin(phi1)**2)**1.5
        d = x / (n1 * k0)
        lat = (phi1
               - (n1 * np.tan(phi1) / r1)
                 * (d**2/2 - (5 + 3*t1 + 10*c1 - 4*c1**2 - 9*ep2)*d**4/24
                    + (61 + 90*t1 + 298*c1 + 45*t1**2 - 252*ep2 - 3*c1**2)
                    * d**6/720))
        lon_origin = np.radians((zz - 1) * 6 - 180 + 3)
        lon = lon_origin + (d - (1 + 2*t1 + c1)*d**3/6
                            + (5 - 2*c1 + 28*t1 - 3*c1**2 + 8*ep2 + 24*t1**2)
                            * d**5/120) / np.cos(phi1)
        lat_out.loc[idx] = np.degrees(lat)
        lon_out.loc[idx] = np.degrees(lon)
    return lat_out, lon_out


# ---------------------------------------------------------------------------
# DMS — degrees / minutes / seconds in a single string
# ---------------------------------------------------------------------------

# Matches things like 19°25'10"N, 19º 25' 10.5" N, 19 25 10 N, -19 25 10
_DMS_RE = re.compile(
    r"""
    ^\s*
    (?P<sign>[+-]?)                         # optional leading sign
    \s*(?P<deg>\d+(?:\.\d+)?)               # degrees
    [\s°ºdeg]+
    (?:(?P<min>\d+(?:\.\d+)?)[\s'm]+)?     # optional minutes
    (?:(?P<sec>\d+(?:\.\d+)?)[\s"s]*)?     # optional seconds
    \s*(?P<hem>[NnSsEeWw])?                 # optional hemisphere letter
    \s*$
    """,
    re.VERBOSE,
)


def _parse_dms_one(text) -> float:
    """Parse a single DMS string into signed decimal degrees.  Returns
    ``NaN`` on failure."""
    if pd.isna(text):
        return float("nan")
    s = str(text).strip()
    if not s:
        return float("nan")
    m = _DMS_RE.match(s)
    if not m:
        # Last-ditch: maybe it's already a plain decimal number
        try:
            return float(s)
        except ValueError:
            return float("nan")
    deg = float(m.group("deg"))
    minutes = float(m.group("min") or 0)
    seconds = float(m.group("sec") or 0)
    value = deg + minutes / 60.0 + seconds / 3600.0
    sign = m.group("sign")
    hem = (m.group("hem") or "").upper()
    if sign == "-" or hem in ("S", "W"):
        value = -value
    return value


def from_dms(df: pd.DataFrame, lat_col: str,
             lon_col: str) -> Tuple[pd.Series, pd.Series]:
    """Parse DMS strings into decimal degrees."""
    if lat_col not in df.columns or lon_col not in df.columns:
        return _empty(df)
    lat = df[lat_col].map(_parse_dms_one)
    lon = df[lon_col].map(_parse_dms_one)
    lat = lat.where(lat.between(-90, 90))
    lon = lon.where(lon.between(-180, 180))
    return lat, lon


# ---------------------------------------------------------------------------
# Decimal with N/S/E/W suffix (e.g. "19.42N")
# ---------------------------------------------------------------------------

_SUFFIX_RE = re.compile(
    r"^\s*(?P<sign>[+-]?)\s*(?P<num>\d+(?:\.\d+)?)\s*"
    r"(?P<hem>[NnSsEeWw])?\s*$"
)


def _parse_suffix_one(text) -> float:
    if pd.isna(text):
        return float("nan")
    s = str(text).strip()
    if not s:
        return float("nan")
    m = _SUFFIX_RE.match(s)
    if not m:
        try:
            return float(s)
        except ValueError:
            return float("nan")
    value = float(m.group("num"))
    sign = m.group("sign")
    hem = (m.group("hem") or "").upper()
    if sign == "-" or hem in ("S", "W"):
        value = -value
    return value


def from_suffix(df: pd.DataFrame, lat_col: str,
                lon_col: str) -> Tuple[pd.Series, pd.Series]:
    """Parse decimal-with-suffix strings (e.g. ``19.42N``)."""
    if lat_col not in df.columns or lon_col not in df.columns:
        return _empty(df)
    lat = df[lat_col].map(_parse_suffix_one)
    lon = df[lon_col].map(_parse_suffix_one)
    lat = lat.where(lat.between(-90, 90))
    lon = lon.where(lon.between(-180, 180))
    return lat, lon


# ---------------------------------------------------------------------------
# MGRS — single string column (e.g. "14QMG5780012345")
# ---------------------------------------------------------------------------

def from_mgrs(df: pd.DataFrame,
              mgrs_col: str) -> Tuple[pd.Series, pd.Series]:
    """Parse an MGRS grid-reference column.  Requires the ``mgrs``
    package; returns NaNs if missing."""
    if mgrs_col not in df.columns:
        return _empty(df)
    lat_out = pd.Series(np.nan, index=df.index, dtype=float)
    lon_out = pd.Series(np.nan, index=df.index, dtype=float)
    if not _HAS_MGRS:
        return lat_out, lon_out
    for idx in df.index:
        v = df.at[idx, mgrs_col]
        if pd.isna(v):
            continue
        s = str(v).strip().replace(" ", "")
        if not s:
            continue
        try:
            la, lo = _MGRS.toLatLon(s)
        except Exception:
            continue
        lat_out.loc[idx] = la
        lon_out.loc[idx] = lo
    return lat_out, lon_out


# ---------------------------------------------------------------------------
# Column resolver helpers (shared with map_view's UI)
# ---------------------------------------------------------------------------

def resolve_column(df: pd.DataFrame, aliases: tuple) -> Optional[str]:
    """Return the first column in *df* matching one of the aliases
    (case-insensitive).  None if no match."""
    if df is None or df.empty:
        return None
    lowered = {c.lower(): c for c in df.columns}
    for a in aliases:
        if a in df.columns:
            return a
        if a.lower() in lowered:
            return lowered[a.lower()]
    return None
