"""Geospatial view: sample locations and their spatial analysis.

Plots every sample at its longitude and latitude, coloured per group
with the shared :class:`PlotStyle`, so the visual identity matches
every other plot in B.I.R.D.S.  There is no background map: the axes
are the coordinates themselves, and nothing is fetched from anywhere.

On the same axes the view kriges one variable -- ordinary kriging, each
group on its own unless the user pools them -- and shows the estimate,
its uncertainty, the variogram behind it and how well it predicts the
samples it was built from.  The arithmetic is in :mod:`birds.geostats`
and the drawing in :mod:`birds.views.spatial_plots`; this module is the
widget that wires them to the data.

Why plain longitude/latitude rather than a projection?
    Plotting degrees directly, with the aspect ratio fixed at the centre
    latitude, *is* a projection -- the equirectangular one, with that
    latitude as its standard parallel.  Distances come out true along
    every meridian and along that parallel, which over the tens to
    hundreds of kilometres a field area spans is as good as any
    projection gets, and the axes read in the units the data were
    recorded in.  Anything that needs real distances -- the scale bar,
    and every distance the kriging uses -- works them out on the
    WGS-84 ellipsoid rather than reading them off the axes.

Why matplotlib (and not Folium / Leaflet)?
    The Map view lives alongside the publication-grade plots (TAS, REE,
    tectonic DFs) and exports through the same pipeline (PNG / PDF / SVG
    at the chosen DPI).
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from matplotlib.colors import LogNorm, Normalize
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTabBar,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from ..plot_style import legend_columns
from .. import coords as _coords
from ..coords import km_per_degree_lat, km_per_degree_lon
from ..diagrams.templates.base import get_groups
from ..geostats import (
    MIN_SAMPLES,
    MODELS,
    VariogramModel,
    analyse_groups,
    make_grid,
)
from .annotation_controller import AnnotationController, nearest_sample
from .plot_canvas import PlotCanvas
from .spatial_plots import (
    ESTIMATE_CMAP,
    attach_colorbar,
    draw_cross_validation,
    draw_surface,
    draw_variogram,
    kriged_name,
    safe_file_name,
    summary_html,
    surface_label,
    surface_layers,
    write_kriged_grids,
)
from .deferral import defer_while_hidden


# Coordinate-format keys used internally and in the format dropdown.
_FMT_DECIMAL = "decimal"
_FMT_UTM     = "utm"
_FMT_DMS     = "dms"
_FMT_SUFFIX  = "suffix"
_FMT_MGRS    = "mgrs"
_FMT_LABELS = (
    (_FMT_DECIMAL, "Decimal degrees (e.g. 19.4326, -99.1332)"),
    (_FMT_UTM,     "UTM — Easting / Northing / Zone / Hemisphere"),
    (_FMT_DMS,     "DMS strings (e.g. 19°25'57\"N)"),
    (_FMT_SUFFIX,  "Decimal with N/S/E/W suffix (e.g. 19.42N)"),
    (_FMT_MGRS,    "MGRS grid (e.g. 14QMG5780012345)"),
)

# What the canvas can show, in tab order.  The first three are maps --
# longitude against latitude -- and carry the scale bar, the north
# arrow, the annotations and the brushing; the other two are graphs.
_DISPLAYS = (
    ("samples",     "Samples"),
    ("estimate",    "Kriged estimate"),
    ("uncertainty", "Uncertainty"),
    ("variogram",   "Variogram"),
    ("cv",          "Cross-validation"),
)
_MAP_DISPLAYS = ("samples", "estimate", "uncertainty")

#: Smallest sill the parameter boxes accept: a variogram that is zero
#: everywhere makes the kriging system singular.
_MIN_SILL = 1e-6


# ---------------------------------------------------------------------------
# Lengths of a degree, for drawing
# ---------------------------------------------------------------------------
#
# The scale bar, the smallest frame drawn and the aspect ratio all need
# to know how long a degree is at a given latitude.  They take it from
# the WGS-84 ellipsoid in birds.coords, not from 111 km: a degree of
# latitude and a degree of longitude differ, and both vary with
# latitude.

#: For drawing, a degree of longitude is never taken as shorter than
#: this fraction of a degree of latitude.  It goes to nothing at the
#: poles, where an aspect ratio or a scale bar built on it would blow up.
_POLAR_FLOOR = 0.05


def _drawn_km_per_degree_lon(lat_deg: float) -> float:
    """km_per_degree_lon, floored near the poles for drawing."""
    return max(float(km_per_degree_lon(lat_deg)),
               _POLAR_FLOOR * float(km_per_degree_lat(lat_deg)))


def map_aspect(lat0_deg: float) -> float:
    """Axes aspect that draws a ground square at *lat0_deg* as a square.

    matplotlib's aspect is how much longer one y unit is on screen than
    one x unit.  A degree of latitude is km_per_degree_lat long on the
    ground and a degree of longitude km_per_degree_lon, so their ratio
    is the stretch.  On a sphere it is 1/cos(lat0); the ellipsoid moves
    it by under 0.7 %, which costs nothing to get right.
    """
    return float(km_per_degree_lat(lat0_deg)) / _drawn_km_per_degree_lon(
        lat0_deg)


#: Smallest frame drawn, in km each way, so a single sample or a tight
#: cluster still gets a frame wide enough to read and to carry a scale
#: bar that means something.
MIN_FRAME_KM = 5.0


def map_frame(lons, lats, *, pad: float):
    """Axis limits for samples at *lons*, *lats*, and the standard parallel.

    Returns ``(lon_min, lon_max, lat_min, lat_max, lat0)``.  Each span is
    first widened, about its centre, to at least ``MIN_FRAME_KM`` on the
    ground -- measured on the ellipsoid, so the minimum is the same
    distance east-west as north-south -- and then padded by *pad* of
    itself on either side.  *lat0* is the frame's centre latitude.
    """
    lon_lo, lon_hi = float(np.min(lons)), float(np.max(lons))
    lat_lo, lat_hi = float(np.min(lats)), float(np.max(lats))
    lat0 = (lat_lo + lat_hi) / 2.0
    min_dlon = MIN_FRAME_KM / _drawn_km_per_degree_lon(lat0)
    min_dlat = MIN_FRAME_KM / float(km_per_degree_lat(lat0))
    if lon_hi - lon_lo < min_dlon:
        mid = (lon_lo + lon_hi) / 2.0
        lon_lo, lon_hi = mid - min_dlon / 2.0, mid + min_dlon / 2.0
    if lat_hi - lat_lo < min_dlat:
        mid = (lat_lo + lat_hi) / 2.0
        lat_lo, lat_hi = mid - min_dlat / 2.0, mid + min_dlat / 2.0
    dlon, dlat = lon_hi - lon_lo, lat_hi - lat_lo
    return (lon_lo - pad * dlon, lon_hi + pad * dlon,
            lat_lo - pad * dlat, lat_hi + pad * dlat, lat0)


# ---------------------------------------------------------------------------
# Scale bar, north arrow, tick labels
# ---------------------------------------------------------------------------

def _nice_round(value: float) -> float:
    """Round *value* to the closest 1 / 2 / 5 × 10ⁿ "tidy" number.

    Used so the auto-length scale bar reports e.g. 100 km, 50 km, 200 km
    instead of 87.4 km.
    """
    if value <= 0:
        return 1.0
    import math
    mag = 10 ** math.floor(math.log10(value))
    base = value / mag
    if base < 1.5:
        return mag
    if base < 3.5:
        return 2 * mag
    if base < 7.5:
        return 5 * mag
    return 10 * mag


def auto_scale_length_km(lon_min: float, lon_max: float, lat0: float, *,
                         target_fraction: float = 0.20) -> float:
    """A tidy scale-bar length, about a fifth of the frame's width."""
    width_km = (lon_max - lon_min) * _drawn_km_per_degree_lon(lat0)
    return _nice_round(width_km * target_fraction)


def _add_scale_bar(ax, *, length_km: float, lat0: float,
                   fraction_pad: float = 0.04) -> tuple:
    """Draw a horizontal scale bar and return ``(line, text)`` so the
    caller can remove them on the next redraw.

    The bar is measured along the parallel *lat0*, the standard parallel
    the aspect ratio was set for, which is where an east-west length on
    this map is exactly true.
    """
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    bar_deg = length_km / _drawn_km_per_degree_lon(lat0)
    x_start = x_min + fraction_pad * (x_max - x_min)
    y_pos = y_min + 0.05 * (y_max - y_min)
    line, = ax.plot([x_start, x_start + bar_deg], [y_pos, y_pos],
                    color="black", linewidth=3, solid_capstyle="butt",
                    zorder=10)
    label = f"{length_km:g} km" if length_km < 10 else f"{int(length_km)} km"
    # Lifted off the bar by a fixed distance on screen.  As a fraction of
    # the axes height it collapsed on a shallow frame, and the label's
    # white box sat on top of the bar it was labelling.
    text = ax.annotate(label, xy=(x_start + bar_deg / 2.0, y_pos),
                       xytext=(0, 4), textcoords="offset points",
                       ha="center", va="bottom", fontsize=9, color="black",
                       bbox=dict(facecolor="white", edgecolor="none",
                                 alpha=0.75, pad=1.4), zorder=11)
    return line, text


def _add_north_arrow(ax) -> None:
    """Draw a small north arrow in the upper-right corner.

    Its length is fixed on screen.  As a fraction of the axes it shrank
    with the frame's height, and a wide, shallow map flattened it to a
    smudge.
    """
    ax.annotate(
        "N", xy=(0.95, 0.96), xytext=(0, -30),
        xycoords="axes fraction", textcoords="offset points",
        ha="center", va="center", fontsize=12, fontweight="bold",
        color="black",
        arrowprops=dict(facecolor="black", edgecolor="black",
                        width=2.2, headwidth=10, headlength=10),
        bbox=dict(facecolor="white", edgecolor="none", alpha=0.8, pad=2),
        zorder=11,
    )


def _format_deg(value: float, *, axis: str) -> str:
    """Format a tick value as decimal degrees with N/S/E/W hemisphere."""
    if axis == "lon":
        h = "E" if value >= 0 else "W"
    else:
        h = "N" if value >= 0 else "S"
    return f"{abs(value):.2f}° {h}"


# ---------------------------------------------------------------------------
# Reading sessions saved before the view plotted plain degrees
# ---------------------------------------------------------------------------
#
# Earlier versions drew this view in spherical Mercator (EPSG:3857), in
# metres, and stored every map annotation in those metres.  Read as
# degrees they would land thousands of degrees off the frame and simply
# vanish, so they are converted once, when such a session is restored.
# New sessions are marked ``axes_crs = "lonlat"`` and never converted.

AXES_CRS = "lonlat"
_LEGACY_SPHERE_R_M = 6_378_137.0


def _legacy_metres_to_lonlat(x, y) -> Tuple[float, float]:
    lon = np.degrees(float(x) / _LEGACY_SPHERE_R_M)
    lat = np.degrees(2.0 * np.arctan(np.exp(float(y) / _LEGACY_SPHERE_R_M))
                     - np.pi / 2.0)
    return float(lon), float(lat)


def migrate_annotations_to_lonlat(entries):
    """Convert serialised map annotations from legacy metres to degrees.

    Works on the plain dicts a session stores, before they are rebuilt
    into annotation objects.  A sample label's offset is converted by
    converting the label position and subtracting, since a fixed offset
    in metres is not a fixed offset in degrees.  An entry that will not
    convert is passed through untouched rather than dropped.
    """
    if not entries:
        return entries
    out = []
    for entry in entries:
        if not isinstance(entry, dict):
            out.append(entry)
            continue
        e = dict(entry)
        kind = e.get("kind")
        try:
            if kind in ("line", "arrow"):
                e["x1"], e["y1"] = _legacy_metres_to_lonlat(e["x1"], e["y1"])
                e["x2"], e["y2"] = _legacy_metres_to_lonlat(e["x2"], e["y2"])
            elif kind == "text":
                e["x"], e["y"] = _legacy_metres_to_lonlat(e["x"], e["y"])
            elif kind == "sample":
                px, py = float(e["px"]), float(e["py"])
                tx = px + float(e.get("dx", 0.0))
                ty = py + float(e.get("dy", 0.0))
                plon, plat = _legacy_metres_to_lonlat(px, py)
                tlon, tlat = _legacy_metres_to_lonlat(tx, ty)
                e["px"], e["py"] = plon, plat
                e["dx"], e["dy"] = tlon - plon, tlat - plat
        except (KeyError, TypeError, ValueError):
            e = dict(entry)
        out.append(e)
    return out


# ---------------------------------------------------------------------------
# MapView widget
# ---------------------------------------------------------------------------

class MapView(QWidget):
    """Sample locations on longitude/latitude axes, and their kriging."""

    def __init__(self, data_manager, plot_style,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style

        # Spatial analysis.  Results are recomputed on every update --
        # a few hundred samples krige in well under a second -- so they
        # can never be stale.  ``_overrides`` holds variogram parameters
        # set by hand, label -> (nugget, sill, range_km), for the
        # (variable, transform) in ``_overrides_for``; they mean nothing
        # for another variable and are dropped when it changes.
        self._results: list = []
        self._styles: dict = {}
        self._overrides: dict = {}
        self._overrides_for: tuple = ("", "")
        self._pending_param_group = ""
        # The columns the selectors were last filled from, so that
        # re-entering the view keeps the user's choices.
        self._populated_for: tuple = ()
        # The last map frame drawn, kept for when auto-fit is off.
        self._last_map_limits: Optional[tuple] = None

        # Artists for the live scale bar; cleared on every redraw so the
        # zoom-/pan-triggered callback can replace them without leaking.
        # _cid_x / _cid_y are the axes-callback IDs for the live-update
        # hook; we disconnect them before every redraw to keep their
        # count bounded (otherwise N updates would queue N callbacks).
        self._scale_artists: list = []
        self._ax = None
        self._cid_x: int | None = None
        self._cid_y: int | None = None
        # Standard parallel of the current frame: the latitude the
        # aspect ratio was set for, and the one the scale bar is true at.
        self._lat0: float = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ----- Left: controls --------------------------------------------------
        controls = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # Sideways only when a control cannot fit -- with larger fonts,
        # as on Windows -- rather than cutting it off out of reach.
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self._build_controls(controls)

        # Sticky action bar (Update + Export) outside the scroll
        self.update_btn = QPushButton("Update map")
        self.update_btn.setMinimumHeight(34)
        self.update_btn.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 6px 12px; }"
        )
        self.update_btn.clicked.connect(self.update_plot)
        self.export_btn = QPushButton("Export…")
        self.export_btn.setMinimumHeight(28)
        self.export_btn.clicked.connect(self.export_plot)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_layout.addWidget(scroll, stretch=1)
        sep_left = QFrame()
        sep_left.setFrameShape(QFrame.Shape.HLine)
        sep_left.setStyleSheet("color: #ccc;")
        left_layout.addWidget(sep_left)
        btn_pad = QWidget()
        btn_pad_l = QVBoxLayout(btn_pad)
        btn_pad_l.setContentsMargins(8, 6, 8, 8)
        btn_pad_l.setSpacing(4)
        btn_pad_l.addWidget(self.update_btn)
        btn_pad_l.addWidget(self.export_btn)
        left_layout.addWidget(btn_pad)
        left_panel.setMinimumWidth(380)
        left_panel.setMaximumWidth(540)
        splitter.addWidget(left_panel)

        # ----- Right: canvas --------------------------------------------------
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(6)
        self.title_label = QLabel("Sample locations")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.subtitle_label = QLabel(
            "Geographic distribution of the imported samples. Each "
            "marker is coloured by group (Edit plot → Group columns)."
        )
        self.subtitle_label.setStyleSheet("color: #5b6478;")
        self.subtitle_label.setWordWrap(True)
        rl.addWidget(self.title_label)
        rl.addWidget(self.subtitle_label)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        rl.addWidget(sep)

        self.display_tabs = QTabBar()
        self.display_tabs.setExpanding(False)
        self.display_tabs.setDrawBase(False)
        for _key, label in _DISPLAYS:
            self.display_tabs.addTab(label)
        self.display_tabs.currentChanged.connect(
            lambda _i: self.update_plot())
        rl.addWidget(self.display_tabs)

        self.canvas = PlotCanvas()
        rl.addWidget(self.canvas, stretch=1)

        # What the analysis found, and what to doubt about it.
        self.summary = QTextBrowser()
        self.summary.setOpenLinks(False)
        self.summary.setMaximumHeight(170)
        self.summary.setStyleSheet("QTextBrowser { font-size: 11px; }")
        self.summary.setVisible(False)
        rl.addWidget(self.summary)
        splitter.addWidget(right)
        splitter.setSizes([460, 820])
        self.annotation_ctl.bind_canvas(self.canvas)

    # ------------------------------------------------------------------ UI
    def _build_controls(self, parent: QWidget) -> None:
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        def _compact_form() -> QFormLayout:
            f = QFormLayout()
            f.setContentsMargins(0, 0, 0, 0)
            f.setHorizontalSpacing(8)
            f.setVerticalSpacing(4)
            f.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow
            )
            return f

        def _wrap(box: QGroupBox) -> QVBoxLayout:
            v = QVBoxLayout(box)
            v.setContentsMargins(8, 12, 8, 8)
            v.setSpacing(4)
            return v

        # ---- Coordinate columns ------------------------------------------
        # A format dropdown picks the parser; the QStackedWidget below
        # swaps the right inputs (Lat/Lon, E/N/Zone/Hem, MGRS, …).
        coord_box = QGroupBox("Coordinate columns")
        cv = _wrap(coord_box)
        fmt_form = _compact_form()
        self.format_combo = QComboBox()
        for key, label in _FMT_LABELS:
            self.format_combo.addItem(label, key)
        fmt_form.addRow("Format:", self.format_combo)
        cv.addLayout(fmt_form)

        self._coord_stack = QStackedWidget()
        cv.addWidget(self._coord_stack)

        # Page 0 — Decimal degrees
        self.lat_combo = QComboBox()
        self.lon_combo = QComboBox()
        self._coord_stack.addWidget(self._build_two_col_page(
            "Latitude (°):", self.lat_combo,
            "Longitude (°):", self.lon_combo,
        ))

        # Page 1 — UTM
        self.utm_e_combo = QComboBox()
        self.utm_n_combo = QComboBox()
        self.utm_zone_combo = QComboBox()
        self.utm_hem_combo = QComboBox()
        self.utm_zone_fixed = QSpinBox()
        self.utm_zone_fixed.setRange(1, 60)
        self.utm_zone_fixed.setValue(14)  # default: Central Mexico
        self.utm_hem_fixed = QComboBox()
        self.utm_hem_fixed.addItems(["N", "S"])
        self.utm_zone_source = QComboBox()
        self.utm_zone_source.addItems(["Fixed for whole dataset",
                                        "From column (per-row)"])
        self.utm_hem_source = QComboBox()
        self.utm_hem_source.addItems(["Fixed for whole dataset",
                                       "From column (per-row)"])
        self._coord_stack.addWidget(self._build_utm_page())

        # Page 2 — DMS
        self.dms_lat_combo = QComboBox()
        self.dms_lon_combo = QComboBox()
        self._coord_stack.addWidget(self._build_two_col_page(
            "Latitude column:", self.dms_lat_combo,
            "Longitude column:", self.dms_lon_combo,
            help_text=("Strings like 19°25'57\"N or "
                       "'19 25 57 N' are auto-parsed."),
        ))

        # Page 3 — Suffix decimal
        self.suffix_lat_combo = QComboBox()
        self.suffix_lon_combo = QComboBox()
        self._coord_stack.addWidget(self._build_two_col_page(
            "Latitude column:", self.suffix_lat_combo,
            "Longitude column:", self.suffix_lon_combo,
            help_text="Strings like '19.42N' or '99.13W'.",
        ))

        # Page 4 — MGRS
        self.mgrs_combo = QComboBox()
        page = QWidget()
        pl = QFormLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setHorizontalSpacing(8)
        pl.setVerticalSpacing(4)
        pl.addRow("MGRS column:", self.mgrs_combo)
        mgrs_help = QLabel("Strings like '14QMG5780012345'.")
        mgrs_help.setStyleSheet("color: #6c7388; font-size: 10px;")
        mgrs_help.setWordWrap(True)
        pl.addRow("", mgrs_help)
        if not getattr(_coords, "_HAS_MGRS", False):
            warn = QLabel("⚠ 'mgrs' package not installed — parsing disabled.")
            warn.setStyleSheet("color: #d62728; font-size: 10px;")
            warn.setWordWrap(True)
            pl.addRow("", warn)
        self._coord_stack.addWidget(page)

        # Wire format dropdown to swap pages
        self.format_combo.currentIndexChanged.connect(
            lambda i: self._coord_stack.setCurrentIndex(i)
        )

        layout.addWidget(coord_box)

        # ---- Spatial analysis ---------------------------------------------
        layout.addWidget(self._build_spatial_box(_wrap, _compact_form))

        # ---- Markers ------------------------------------------------------
        mark_box = QGroupBox("Markers")
        mv = _wrap(mark_box)
        mf = _compact_form()
        self.marker_size = QSpinBox()
        self.marker_size.setRange(2, 30)
        self.marker_size.setValue(8)
        mf.addRow("Size:", self.marker_size)
        self.marker_alpha = QDoubleSpinBox()
        self.marker_alpha.setRange(0.1, 1.0)
        self.marker_alpha.setSingleStep(0.05)
        self.marker_alpha.setValue(0.95)
        mf.addRow("Opacity:", self.marker_alpha)
        self.marker_edge_chk = QCheckBox("Black outline around markers")
        self.marker_edge_chk.setChecked(True)
        mf.addRow("", self.marker_edge_chk)
        self.colour_by_value_chk = QCheckBox(
            "Colour by the analysed variable")
        self.colour_by_value_chk.setToolTip(
            "On the Samples tab, colour each marker by its value of the "
            "variable chosen under Spatial analysis instead of by group. "
            "Samples without a value are drawn hollow.")
        mf.addRow("", self.colour_by_value_chk)
        mv.addLayout(mf)
        layout.addWidget(mark_box)

        # ---- Extent -------------------------------------------------------
        ext_box = QGroupBox("Map extent")
        ev = _wrap(ext_box)
        ef = _compact_form()
        self.auto_extent_chk = QCheckBox("Auto-fit to samples")
        self.auto_extent_chk.setChecked(True)
        self.auto_extent_chk.setToolTip(
            "Off: keep the frame as it is now — zoomed or panned — when "
            "the map is updated. The kriging grid covers that frame.")
        ef.addRow("", self.auto_extent_chk)
        self.padding_pct = QSpinBox()
        self.padding_pct.setRange(0, 200)
        self.padding_pct.setSuffix(" %")
        self.padding_pct.setValue(15)
        ef.addRow("Padding around data:", self.padding_pct)
        ev.addLayout(ef)
        layout.addWidget(ext_box)

        # ---- Annotations --------------------------------------------------
        ann_box = QGroupBox("Annotations")
        av = _wrap(ann_box)
        af = _compact_form()
        self.grid_chk = QCheckBox("Show lat/lon grid")
        self.grid_chk.setChecked(True)
        af.addRow("", self.grid_chk)
        self.scale_chk = QCheckBox("Show scale bar")
        self.scale_chk.setChecked(True)
        af.addRow("", self.scale_chk)
        self.scale_auto_chk = QCheckBox(
            "Auto length — updates live on zoom / pan"
        )
        self.scale_auto_chk.setChecked(True)
        self.scale_auto_chk.toggled.connect(self._on_scale_auto_toggled)
        af.addRow("", self.scale_auto_chk)
        self.scale_length = QSpinBox()
        self.scale_length.setRange(1, 5000)
        self.scale_length.setValue(100)
        self.scale_length.setSuffix(" km")
        self.scale_length.setEnabled(False)        # auto by default
        af.addRow("Scale bar length:", self.scale_length)
        self.north_chk = QCheckBox("Show north arrow")
        self.north_chk.setChecked(True)
        af.addRow("", self.north_chk)
        self.legend_chk = QCheckBox("Show legend")
        self.legend_chk.setChecked(True)
        af.addRow("", self.legend_chk)
        av.addLayout(af)
        layout.addWidget(ann_box)

        # Annotation toolkit (lines / arrows / text / sample identifier).
        # Clicks arrive in degrees, the same units the axes are drawn in.
        self.annotation_ctl = AnnotationController(
            self, sample_resolver=self._resolve_sample)
        layout.addWidget(self.annotation_ctl.group)

        layout.addStretch(1)

    def _build_spatial_box(self, _wrap, _compact_form) -> QGroupBox:
        """Controls of the kriging: what, how, and on what grid."""
        box = QGroupBox("Spatial analysis — ordinary kriging")
        v = _wrap(box)

        f = _compact_form()
        self.variable_combo = QComboBox()
        self.variable_combo.setToolTip(
            "The numeric column to interpolate. Coordinate columns are "
            "left out of the list.")
        f.addRow("Variable:", self.variable_combo)
        self.transform_combo = QComboBox()
        self.transform_combo.addItem("Logarithm — concentrations", "log")
        self.transform_combo.addItem("None — krige the values as they are",
                                     "none")
        self.transform_combo.setToolTip(
            "Concentrations are skewed and cannot go below zero, so they "
            "are kriged as ln(value) and brought back as the median "
            "estimate. Values at or below zero are left out. Use None "
            "for a variable that can be negative, such as an isotope "
            "ratio in epsilon units.")
        f.addRow("Transform:", self.transform_combo)
        self.pooling_combo = QComboBox()
        self.pooling_combo.addItem("Each group on its own", False)
        self.pooling_combo.addItem("All groups pooled", True)
        self.pooling_combo.setToolTip(
            "Samples from two units — a pluton and its host, two lava "
            "sequences — are not one random field, and kriging across "
            "the contact draws a gradient that is not there. Pool them "
            "only when the groups are not separate bodies.")
        f.addRow("Groups:", self.pooling_combo)
        self.model_combo = QComboBox()
        for kind in MODELS:
            self.model_combo.addItem(kind.capitalize(), kind)
        self.model_combo.setToolTip(
            "Shape of the variogram model fitted to every group. The "
            "range is the effective one, where the model reaches 95 % "
            "of its sill.")
        f.addRow("Variogram model:", self.model_combo)
        self.lags_spin = QSpinBox()
        self.lags_spin.setRange(0, 40)
        self.lags_spin.setSpecialValueText("Auto")
        self.lags_spin.setToolTip(
            "Distance classes of the experimental variogram. Auto aims "
            "for about 30 pairs of samples in each.")
        f.addRow("Lag classes:", self.lags_spin)
        self.max_lag_spin = QDoubleSpinBox()
        self.max_lag_spin.setRange(0.0, 20000.0)
        self.max_lag_spin.setDecimals(1)
        self.max_lag_spin.setSuffix(" km")
        self.max_lag_spin.setSpecialValueText("Auto")
        self.max_lag_spin.setToolTip(
            "Longest distance the variogram is computed to. Auto is half "
            "the largest distance between two samples.")
        f.addRow("Maximum lag:", self.max_lag_spin)
        v.addLayout(f)

        # Variogram parameters, fitted or set by hand, one group at a time.
        params = QGroupBox("Variogram parameters")
        pv = _wrap(params)
        pf = _compact_form()
        self.param_group_combo = QComboBox()
        self.param_group_combo.setToolTip(
            "The group whose parameters are shown below. The list fills "
            "once the map has been updated with a variable chosen.")
        pf.addRow("Group:", self.param_group_combo)
        self.auto_fit_chk = QCheckBox("Fit automatically")
        self.auto_fit_chk.setChecked(True)
        self.auto_fit_chk.setEnabled(False)
        self.auto_fit_chk.setToolTip(
            "Untick to set nugget, sill and range by hand for this group, "
            "starting from the fitted values.")
        pf.addRow("", self.auto_fit_chk)
        self.nugget_spin = QDoubleSpinBox()
        self.sill_spin = QDoubleSpinBox()
        for spin in (self.nugget_spin, self.sill_spin):
            spin.setRange(0.0, 1e9)
            spin.setDecimals(6)
            spin.setSingleStep(0.01)
        self.range_spin = QDoubleSpinBox()
        self.range_spin.setRange(0.001, 1e5)
        self.range_spin.setDecimals(3)
        self.range_spin.setSuffix(" km")
        pf.addRow("Nugget:", self.nugget_spin)
        pf.addRow("Sill:", self.sill_spin)
        pf.addRow("Range:", self.range_spin)
        for spin in (self.nugget_spin, self.sill_spin, self.range_spin):
            spin.setEnabled(False)
            spin.setKeyboardTracking(False)
            spin.editingFinished.connect(self._on_parameter_edited)
        pv.addLayout(pf)
        v.addWidget(params)
        self.param_group_combo.currentIndexChanged.connect(
            lambda _i: self._sync_parameter_spins())
        self.auto_fit_chk.toggled.connect(self._on_auto_fit_toggled)

        # The surface: grid, where it is drawn, and how.
        sf = _compact_form()
        self.cells_spin = QSpinBox()
        self.cells_spin.setRange(20, 400)
        self.cells_spin.setValue(100)
        self.cells_spin.setToolTip(
            "Cells along the longer side of the frame. More cells, a "
            "smoother picture and a slower update.")
        sf.addRow("Grid cells across:", self.cells_spin)
        self.clip_chk = QCheckBox("Clip to each group's sample hull")
        self.clip_chk.setChecked(True)
        self.clip_chk.setToolTip(
            "Beyond the outermost samples kriging only extrapolates, "
            "drifting back to the mean. Clipped, the surface shows only "
            "where there are data around it.")
        sf.addRow("", self.clip_chk)
        self.buffer_spin = QDoubleSpinBox()
        self.buffer_spin.setRange(0.0, 1000.0)
        self.buffer_spin.setDecimals(2)
        self.buffer_spin.setSuffix(" km")
        self.buffer_spin.setToolTip(
            "Let the clipped surface run this far past the hull.")
        sf.addRow("Hull buffer:", self.buffer_spin)
        self.clip_chk.toggled.connect(self.buffer_spin.setEnabled)
        self.contours_chk = QCheckBox("Contour lines on the estimate")
        sf.addRow("", self.contours_chk)
        v.addLayout(sf)

        self.export_grid_btn = QPushButton("Export grid for a GIS (.asc)…")
        self.export_grid_btn.setToolTip(
            "Write the kriged estimate and its standard deviation as "
            "ESRI ASCII grids in WGS-84 degrees, one pair per group, "
            "with a .prj each and a text file describing them. QGIS and "
            "ArcGIS open them directly.")
        self.export_grid_btn.clicked.connect(self.export_grid)
        v.addWidget(self.export_grid_btn)
        return box

    # ------------------------------------------------------------------
    # Coordinate-page builders (used inside _build_controls above)
    # ------------------------------------------------------------------
    def _build_two_col_page(self, lab1: str, w1: QComboBox,
                             lab2: str, w2: QComboBox,
                             help_text: str = "") -> QWidget:
        """A page with two labelled QComboBoxes (lat + lon style)."""
        page = QWidget()
        f = QFormLayout(page)
        f.setContentsMargins(0, 0, 0, 0)
        f.setHorizontalSpacing(8)
        f.setVerticalSpacing(4)
        f.addRow(lab1, w1)
        f.addRow(lab2, w2)
        if help_text:
            h = QLabel(help_text)
            h.setStyleSheet("color: #6c7388; font-size: 10px;")
            h.setWordWrap(True)
            f.addRow("", h)
        return page

    def _build_utm_page(self) -> QWidget:
        """The UTM page is more complex — zone & hemisphere can each be
        a fixed value or a per-row column."""
        page = QWidget()
        v = QVBoxLayout(page)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)
        f1 = QFormLayout()
        f1.setContentsMargins(0, 0, 0, 0)
        f1.setHorizontalSpacing(8)
        f1.setVerticalSpacing(4)
        f1.addRow("Easting (m):", self.utm_e_combo)
        f1.addRow("Northing (m):", self.utm_n_combo)
        v.addLayout(f1)

        zone_row = QHBoxLayout()
        zone_row.setContentsMargins(0, 0, 0, 0)
        zone_row.addWidget(QLabel("Zone:"))
        zone_row.addWidget(self.utm_zone_source, stretch=2)
        zone_row.addWidget(self.utm_zone_fixed, stretch=1)
        zone_row.addWidget(self.utm_zone_combo, stretch=2)
        v.addLayout(zone_row)

        hem_row = QHBoxLayout()
        hem_row.setContentsMargins(0, 0, 0, 0)
        hem_row.addWidget(QLabel("Hem.:"))
        hem_row.addWidget(self.utm_hem_source, stretch=2)
        hem_row.addWidget(self.utm_hem_fixed, stretch=1)
        hem_row.addWidget(self.utm_hem_combo, stretch=2)
        v.addLayout(hem_row)

        def _refresh_zone():
            from_col = self.utm_zone_source.currentIndex() == 1
            self.utm_zone_fixed.setVisible(not from_col)
            self.utm_zone_combo.setVisible(from_col)
        def _refresh_hem():
            from_col = self.utm_hem_source.currentIndex() == 1
            self.utm_hem_fixed.setVisible(not from_col)
            self.utm_hem_combo.setVisible(from_col)
        self.utm_zone_source.currentIndexChanged.connect(_refresh_zone)
        self.utm_hem_source.currentIndexChanged.connect(_refresh_hem)
        _refresh_zone()
        _refresh_hem()

        if not getattr(_coords, "_HAS_PYPROJ", False):
            warn = QLabel(
                "ℹ pyproj not installed — using built-in fallback "
                "(~1 m accuracy, still good for sample maps)."
            )
            warn.setStyleSheet("color: #6c7388; font-size: 10px;")
            warn.setWordWrap(True)
            v.addWidget(warn)
        return page

    # ------------------------------------------------------------------ API
    def show_map(self) -> None:
        """Repopulate coordinate selectors from the current dataframe and
        draw the map. Called by main_window when entering the view."""
        self._populate_coords()
        self.update_plot()

    def _display(self) -> str:
        return _DISPLAYS[max(self.display_tabs.currentIndex(), 0)][0]

    def _variable(self) -> str:
        return self.variable_combo.currentText().strip()

    def _transform(self) -> str:
        return self.transform_combo.currentData() or "log"

    def _pooled(self) -> bool:
        return bool(self.pooling_combo.currentData())

    def _model_kind(self) -> str:
        return self.model_combo.currentData() or "spherical"

    def update_plot(self) -> None:
        if defer_while_hidden(self):
            return      # drawn when its page is shown
        fig = self.canvas.figure
        display = self._display()
        is_map = display in _MAP_DISPLAYS
        kept = self._kept_view()
        self._disconnect_view_callbacks()
        fig.clear()
        # ``fig.clear()`` invalidates every artist on the previous axes —
        # forget about the scale-bar pair so the live-update code never
        # tries to .remove() a dead artist.
        self._scale_artists = []
        self._ax = None
        ax = fig.add_subplot(111)
        # Annotations live in degrees; on a variogram they would land in
        # kilometres and semivariance, so they are off there.
        self.annotation_ctl.enabled = is_map
        self._set_titles(display)
        self.summary.setVisible(display != "samples")
        self.summary.clear()

        samples, message = self._collect()
        if message is not None:
            self._empty(ax, message)
            self.canvas.draw()
            return

        results = None
        if display != "samples":
            results = self._analysis(samples)
            if results is None:
                self._empty(ax, "Choose a variable to krige "
                                "(Spatial analysis → Variable).")
                self.canvas.draw()
                return

        overlaps = ()
        if is_map:
            lon_min, lon_max, lat_min, lat_max, lat0 = (
                kept if kept is not None else self._frame(samples))
            ax.set_xlim(lon_min, lon_max)
            ax.set_ylim(lat_min, lat_max)
            # Equirectangular, with the frame's centre latitude as the
            # standard parallel: a ground square there draws as a square.
            ax.set_aspect(map_aspect(lat0))
            self._lat0 = lat0
            self._last_map_limits = (lon_min, lon_max, lat_min, lat_max,
                                     lat0)

        if display == "samples":
            self._draw_samples(ax, samples)
        elif display in ("estimate", "uncertainty"):
            which = "estimate" if display == "estimate" else "sd"
            grid = make_grid(*ax.get_xlim(), *ax.get_ylim(),
                             cells_across=self.cells_spin.value())
            layers, overlaps = surface_layers(
                results, grid, clip=self.clip_chk.isChecked(),
                buffer_km=self.buffer_spin.value())
            mesh = draw_surface(ax, layers, grid, which=which,
                                transform=self._transform(),
                                contours=self.contours_chk.isChecked())
            if mesh is not None:
                attach_colorbar(ax, mesh, surface_label(
                    self._variable(), which=which,
                    transform=self._transform()))
            else:
                ax.text(0.5, 0.5, "No group could be kriged — see below.",
                        transform=ax.transAxes, ha="center", va="center",
                        color="#a04c2e", fontsize=10)
            self._draw_sample_markers(ax, samples)
        elif display == "variogram":
            draw_variogram(ax, results, self._styles,
                           variable=self._variable(),
                           transform=self._transform())
        else:
            draw_cross_validation(ax, results, self._styles,
                                  variable=self._variable(),
                                  transform=self._transform())

        if results is not None:
            self.summary.setHtml(summary_html(
                results, variable=self._variable(),
                transform=self._transform(), overlaps=overlaps,
                manual_labels=tuple(self._override_models())))
        if is_map:
            self._finish_map(ax)
        fig.tight_layout()
        if is_map:
            # Replay user annotations; their coordinates are degrees,
            # like the axes.
            self.annotation_ctl.draw(ax)
            from .brushing import draw_selection_overlay
            draw_selection_overlay(self)
        self.canvas.draw()

    # ------------------------------------------------------------------
    # Pieces of update_plot
    # ------------------------------------------------------------------
    def _utm_hint(self) -> str:
        """When decimal degrees fail on columns that hold UTM numbers --
        several of the user's sessions keep easting and northing in
        Latitude / Longitude -- say so, and how to read them."""
        if (self.format_combo.currentData() or _FMT_DECIMAL) != _FMT_DECIMAL:
            return ""
        df = self.data.df
        cols = [self.lat_combo.currentData(), self.lon_combo.currentData()]
        if df is None or not all(c in df.columns for c in cols):
            return ""
        values = [pd.to_numeric(df[c], errors="coerce").dropna() for c in cols]
        if any(v.empty for v in values):
            return self._utm_columns_hint(df)
        medians = [float(v.abs().median()) for v in values]
        if max(medians) <= 180:
            return ""
        east = next((m for m in medians if 100_000 <= m <= 900_000), None)
        north = next((m for m in medians
                      if 0 <= m <= 10_000_000 and m != east), None)
        if east is None or north is None:
            return ""
        return (f"“{cols[0]}” and “{cols[1]}” hold values like "
                f"{medians[0]:,.0f} and {medians[1]:,.0f}: those are not "
                "degrees.\nThey look like UTM easting and northing — pick "
                "UTM under Coordinates → Format, with the columns and the "
                "zone they belong to.")

    @staticmethod
    def _utm_columns_hint(df) -> str:
        """The data template has Easting / Northing beside Latitude /
        Longitude: when the degrees are empty and those are not, say
        where the location is."""
        east = _coords.resolve_column(df, _coords.EASTING_ALIASES)
        north = _coords.resolve_column(df, _coords.NORTHING_ALIASES)
        if not (east and north):
            return ""
        if (pd.to_numeric(df[east], errors="coerce").dropna().empty
                or pd.to_numeric(df[north], errors="coerce").dropna().empty):
            return ""
        return (f"The degree columns are empty, but “{east}” and "
                f"“{north}” hold UTM coordinates — pick UTM under "
                "Coordinates → Format.")

    def _collect(self):
        """``(samples, None)``, or ``(None, message)`` when there is nothing
        to draw.

        Each sample entry is ``(label, sub, style, lon, lat)`` for one
        visible group, with every row of the group kept -- coordinates
        that did not parse are NaN -- so the analysis can count them.
        """
        df = self.data.df
        if df is None or df.empty:
            return None, "Load a dataset (Data → Import) to plot a map."
        # Parse coordinates once for the whole dataset using the selected
        # format, then slice per group.
        lat_all, lon_all, err = self._resolve_coords()
        if err is not None:
            return None, err
        if lat_all is None or lat_all.dropna().empty:
            hint = self._utm_hint()
            if hint:
                return None, hint
            return None, ("No samples could be parsed in the selected "
                          "format.\nCheck the column choices and that "
                          "values are valid.")
        samples = []
        for label, sub, gs in get_groups(df, self.plot_style):
            if gs is not None and not getattr(gs, "visible", True):
                continue
            lat = lat_all.loc[sub.index]
            lon = lon_all.loc[sub.index]
            ok = (lat.notna() & lon.notna() & lat.between(-90, 90)
                  & lon.between(-180, 180))
            lat = lat.where(ok)
            lon = lon.where(ok)
            if ok.any():
                samples.append((label, sub, gs, lon, lat))
        if not samples:
            # The coordinate columns parsed, but nothing survived the
            # range check.  Name the columns when the parser labelled the
            # series (decimal degrees); the UTM and MGRS parsers build
            # unnamed series, so fall back to a generic phrase rather
            # than reaching for names that do not exist here.
            lat_name = getattr(lat_all, "name", None) or "latitude"
            lon_name = getattr(lon_all, "name", None) or "longitude"
            return None, (
                f"No usable coordinates in '{lat_name}' / '{lon_name}'.\n"
                "Make sure the values are numeric and inside "
                "[-90, 90] × [-180, 180].")
        return samples, None

    def _frame(self, samples):
        lons = np.concatenate([lon.dropna().to_numpy()
                               for _l, _s, _g, lon, _la in samples])
        lats = np.concatenate([lat.dropna().to_numpy()
                               for _l, _s, _g, _lo, lat in samples])
        return map_frame(lons, lats, pad=self.padding_pct.value() / 100.0)

    def _kept_view(self):
        """The current map frame, when the user has turned auto-fit off.

        Read before the figure is cleared, so a zoom or pan on the canvas
        survives the next update.  It used to be a checkbox that was saved
        and restored and that nothing read.
        """
        if self.auto_extent_chk.isChecked():
            return None
        if self._ax is not None:
            x0, x1 = self._ax.get_xlim()
            y0, y1 = self._ax.get_ylim()
            self._last_map_limits = (x0, x1, y0, y1, self._lat0)
        return self._last_map_limits

    def _analysis(self, samples):
        """Krige the chosen variable, per group or pooled; None if no
        variable is chosen."""
        variable = self._variable()
        if not variable:
            return None
        if (variable, self._transform()) != self._overrides_for:
            self._overrides.clear()
            self._overrides_for = (variable, self._transform())
        groups = []
        for label, sub, _gs, lon, lat in samples:
            if variable in sub.columns:
                values = pd.to_numeric(sub[variable], errors="coerce")
            else:
                values = pd.Series(np.nan, index=sub.index)
            groups.append((label, lon.to_numpy(float), lat.to_numpy(float),
                           values.to_numpy(float)))
        results = analyse_groups(
            groups, pooled=self._pooled(), model=self._model_kind(),
            transform=self._transform(),
            overrides=self._override_models(),
            n_lags=self.lags_spin.value() or None,
            max_lag_km=self.max_lag_spin.value() or None)
        self._results = results
        self._styles = {label: gs for label, _s, gs, _lo, _la in samples}
        self._refresh_parameter_selector(results)
        return results

    def _draw_samples(self, ax, samples) -> None:
        """Markers per group -- coloured by group, or by the variable."""
        edge = self.marker_edge_chk.isChecked()
        variable = self._variable()
        by_value = self.colour_by_value_chk.isChecked() and variable
        norm = None
        if by_value:
            pooled = pd.concat([pd.to_numeric(sub[variable], errors="coerce")
                                for _l, sub, _g, _lo, _la in samples
                                if variable in sub.columns])
            finite = pooled[np.isfinite(pooled)]
            if finite.empty:
                by_value = False
            elif self._transform() == "log" and finite.min() > 0:
                norm = LogNorm(vmin=finite.min(), vmax=finite.max())
            else:
                norm = Normalize(vmin=finite.min(), vmax=finite.max())
        mappable = None
        for label, sub, gs, lon, lat in samples:
            ok = lon.notna() & lat.notna()
            marker = gs.marker if gs else "o"
            # A group made larger in Edit plot is larger here too, in
            # proportion to this view's own Size.
            size = (self.marker_size.value()
                    * self.plot_style.size_scale(gs)) ** 2
            common = dict(s=size, alpha=self.marker_alpha.value(),
                          marker=marker, label=label, zorder=5,
                          edgecolors="black" if edge else "none",
                          linewidths=0.5 if edge else 0)
            if by_value:
                v = (pd.to_numeric(sub[variable], errors="coerce")
                     if variable in sub.columns
                     else pd.Series(np.nan, index=sub.index))
                has = ok & np.isfinite(v)
                # Colour is the value here, so the legend shows each
                # group's marker alone, uncoloured.
                common["label"] = "_nolegend_"
                mappable = ax.scatter(lon[has], lat[has], c=v[has],
                                      cmap=ESTIMATE_CMAP, norm=norm, **common)
                ax.scatter([], [], s=size, marker=marker, facecolors="white",
                           edgecolors="black", linewidths=0.6, label=label)
                gaps = ok & ~np.isfinite(v)
                if gaps.any():
                    ax.scatter(lon[gaps], lat[gaps], s=size, marker=marker,
                               facecolors="none", edgecolors="#999",
                               linewidths=0.8, zorder=5)
            else:
                ax.scatter(lon[ok], lat[ok],
                           c=gs.color if gs else "#1f77b4", **common)
        if mappable is not None:
            attach_colorbar(ax, mappable, variable)

    def _draw_sample_markers(self, ax, samples) -> None:
        """Where the data are, over a surface: small, white, outlined."""
        base = max(self.marker_size.value() - 2, 3)
        for label, _sub, gs, lon, lat in samples:
            ok = lon.notna() & lat.notna()
            size = (base * self.plot_style.size_scale(gs)) ** 2
            ax.scatter(lon[ok], lat[ok], s=size,
                       marker=gs.marker if gs else "o", facecolors="white",
                       edgecolors="black", linewidths=0.6, label=label,
                       zorder=5)

    def _finish_map(self, ax) -> None:
        """Ticks, grid, scale bar, north arrow and legend of a map display."""
        self._tick_in_degrees(ax)
        if self.grid_chk.isChecked():
            ax.grid(True, which="major", linestyle=":", linewidth=0.6,
                    color="#666", alpha=0.6)
        else:
            ax.grid(False)
        # matplotlib keeps axes callbacks on the axes, so the live
        # scale-bar hooks are re-bound to every new one.
        self._ax = ax
        if self.scale_chk.isChecked():
            self._redraw_scale_bar()
            self._cid_x = ax.callbacks.connect("xlim_changed",
                                               self._on_view_changed)
            self._cid_y = ax.callbacks.connect("ylim_changed",
                                               self._on_view_changed)
        if self.north_chk.isChecked():
            _add_north_arrow(ax)
        if self.legend_chk.isChecked():
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc="lower right", fontsize=9,
                          framealpha=0.85, facecolor="white",
                          edgecolor="#666",
                          ncol=legend_columns(len(handles)))
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")

    def _set_titles(self, display: str) -> None:
        variable = self._variable() or "—"
        kn = kriged_name(variable, self._transform())
        how = ("all groups pooled" if self._pooled()
               else "each group on its own")
        if not self.clip_chk.isChecked():
            clip = ""
        elif self._pooled():
            clip = ", clipped to the samples' hull"
        else:
            clip = ", clipped to each group's sample hull"
        title, subtitle = {
            "samples": (
                "Sample locations",
                "Geographic distribution of the imported samples, "
                + (f"coloured by {variable}."
                   if self.colour_by_value_chk.isChecked() and
                   self._variable()
                   else "coloured by group (Edit plot → Group columns).")),
            "estimate": (
                f"Kriged {variable}",
                ("Median estimate from ordinary kriging of " + kn
                 if self._transform() == "log"
                 else "Ordinary-kriging estimate of " + kn)
                + f", {how}{clip}."),
            "uncertainty": (
                f"Uncertainty of kriged {variable}",
                f"Kriging standard deviation of {kn}, {how}{clip}. It "
                "grows away from the samples, and says where the "
                "estimate can be trusted."),
            "variogram": (
                f"Variogram of {kn}",
                "Experimental semivariance by distance — point size by "
                "the number of pairs — with the fitted model."),
            "cv": (
                f"Cross-validation of {variable}",
                "Each sample predicted from all the others. Points near "
                "the 1 : 1 line mean the spatial model predicts well."),
        }[display]
        self.title_label.setText(title)
        self.subtitle_label.setText(subtitle)

    # ------------------------------------------------------------------
    # Variogram parameters set by hand
    # ------------------------------------------------------------------
    def _override_models(self) -> dict:
        """The hand-set parameters, as models of the kind chosen above."""
        out = {}
        for label, (nugget, sill, range_km) in self._overrides.items():
            try:
                out[label] = VariogramModel(self._model_kind(), nugget,
                                            sill, range_km)
            except ValueError:
                continue
        return out

    def _refresh_parameter_selector(self, results) -> None:
        labels = [r.label for r in results]
        current = (self.param_group_combo.currentText()
                   or self._pending_param_group)
        self.param_group_combo.blockSignals(True)
        self.param_group_combo.clear()
        self.param_group_combo.addItems(labels)
        if current in labels:
            self.param_group_combo.setCurrentText(current)
        self.param_group_combo.blockSignals(False)
        self._pending_param_group = ""
        self._sync_parameter_spins()

    def _selected_result(self):
        label = self.param_group_combo.currentText()
        for r in self._results:
            if r.label == label:
                return r
        return None

    def _sync_parameter_spins(self) -> None:
        """Show the selected group's parameters: fitted, or set by hand."""
        label = self.param_group_combo.currentText()
        manual = label in self._overrides
        widgets = (self.auto_fit_chk, self.nugget_spin, self.sill_spin,
                   self.range_spin)
        for w in widgets:
            w.blockSignals(True)
        self.auto_fit_chk.setChecked(not manual)
        if manual:
            nugget, sill, range_km = self._overrides[label]
        else:
            r = self._selected_result()
            m = r.analysis.model if r is not None and r.analysis else None
            nugget, sill, range_km = ((m.nugget, m.sill, m.range_km)
                                      if m is not None else (0.0, 0.0, 1.0))
        self.nugget_spin.setValue(nugget)
        self.sill_spin.setMinimum(max(nugget, _MIN_SILL))
        self.sill_spin.setValue(sill)
        self.range_spin.setValue(range_km)
        for spin in widgets[1:]:
            spin.setEnabled(manual)
        self.auto_fit_chk.setEnabled(bool(label))
        for w in widgets:
            w.blockSignals(False)

    def _on_auto_fit_toggled(self, checked: bool) -> None:
        label = self.param_group_combo.currentText()
        if not label:
            return
        if checked:
            self._overrides.pop(label, None)
            self.update_plot()
        else:
            # Start from exactly what was fitted, so nothing moves until
            # the user changes a number.
            r = self._selected_result()
            m = r.analysis.model if r is not None and r.analysis else None
            self._overrides[label] = (
                (m.nugget, m.sill, m.range_km) if m is not None else
                (self.nugget_spin.value(), self.sill_spin.value(),
                 self.range_spin.value()))
            self._overrides_for = (self._variable(), self._transform())
            self._sync_parameter_spins()

    def _on_parameter_edited(self) -> None:
        label = self.param_group_combo.currentText()
        if not label or label not in self._overrides:
            return
        self.sill_spin.setMinimum(max(self.nugget_spin.value(), _MIN_SILL))
        params = (self.nugget_spin.value(), self.sill_spin.value(),
                  self.range_spin.value())
        # A spin box shows the stored value rounded; unless the user
        # changed what it shows, keep the stored one.
        old = self._overrides[label]
        spins = (self.nugget_spin, self.sill_spin, self.range_spin)
        params = tuple(
            o if abs(p - o) <= 0.5 * 10.0 ** -s.decimals() else p
            for o, p, s in zip(old, params, spins))
        if params != self._overrides[label]:
            self._overrides[label] = params
            self.update_plot()

    # ------------------------------------------------------------------
    # Export of the kriged grid
    # ------------------------------------------------------------------
    def export_grid(self) -> None:
        """Write the kriged surfaces as ESRI ASCII grids for a GIS.

        One estimate and one standard-deviation grid per group -- or one
        pair, pooled -- on the frame and cell size the map shows, clipped
        the same way, with a .prj each and a text file saying what is in
        them.
        """
        from PySide6.QtWidgets import QFileDialog, QMessageBox

        samples, message = self._collect()
        if message is not None:
            QMessageBox.information(self, "Export grid", message)
            return
        results = self._analysis(samples)
        if results is None or not any(r.analysis for r in results):
            QMessageBox.information(
                self, "Export grid",
                "Nothing has been kriged yet: choose a variable, and check "
                "the summary under the Kriged estimate tab.")
            return
        variable = self._variable()
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Export kriged grid", f"{safe_file_name(variable)}_kriged.asc",
            "ESRI ASCII grid (*.asc)")
        if not path_str:
            return
        kept = self._kept_view()
        lon_min, lon_max, lat_min, lat_max, _lat0 = (
            kept if kept is not None else self._frame(samples))
        grid = make_grid(lon_min, lon_max, lat_min, lat_max,
                         cells_across=self.cells_spin.value())
        written = write_kriged_grids(
            Path(path_str), results, grid, variable=variable,
            transform=self._transform(), clip=self.clip_chk.isChecked(),
            buffer_km=self.buffer_spin.value(),
            manual_labels=tuple(self._override_models()))
        QMessageBox.information(
            self, "Export grid",
            "Written:\n" + "\n".join(p.name for p in written)
            + f"\n\nin {Path(path_str).parent}")

    # ------------------------------------------------------------------
    # Selection and identification work on the map displays only
    # ------------------------------------------------------------------
    def _selection_points(self, names):
        """(lon, lat) of the selected samples, in the axes' own units."""
        from .brushing import names_series
        df = self.data.df
        axes = self.canvas.figure.axes
        if (df is None or df.empty or not axes
                or self._display() not in _MAP_DISPLAYS):
            return []
        lat, lon, err = self._resolve_coords()
        if err is not None or lat is None or lon is None:
            return []
        nm = names_series(df)
        m = nm.isin(names) & lon.notna() & lat.notna()
        return [(axes[0], list(zip(lon[m], lat[m])))]

    def _resolve_sample(self, x: float, y: float):
        """The data row whose (lon, lat) lands closest to a click."""
        df = self.data.df
        if (df is None or df.empty
                or self._display() not in _MAP_DISPLAYS):
            return None
        lat, lon, err = self._resolve_coords()
        if err is not None or lat is None or lon is None:
            return None
        axes = self.canvas.figure.axes
        if not axes:
            return None
        return nearest_sample(df, lon, lat, x, y,
                              axes[0].get_xlim(), axes[0].get_ylim())

    # ---------------------------------------------------------- live scale
    def _on_scale_auto_toggled(self, checked: bool) -> None:
        self.scale_length.setEnabled(not checked)
        # If a map is already drawn, refresh the scale bar in place
        if self._ax is not None and self.scale_chk.isChecked():
            self._redraw_scale_bar()
            self.canvas.draw()

    def _on_view_changed(self, _ax) -> None:
        """Called by matplotlib when the user pans / zooms the canvas."""
        if self._ax is None or not self.scale_chk.isChecked():
            return
        self._redraw_scale_bar()
        # ``draw_idle`` coalesces redraws when the user is dragging
        self.canvas.draw()

    def _disconnect_view_callbacks(self) -> None:
        """Drop any previously-registered xlim/ylim callbacks."""
        if self._ax is None:
            return
        for attr in ("_cid_x", "_cid_y"):
            cid = getattr(self, attr)
            if cid is not None:
                try:
                    self._ax.callbacks.disconnect(cid)
                except (KeyError, AttributeError):
                    pass
                setattr(self, attr, None)

    def _redraw_scale_bar(self) -> None:
        """Replace the previous bar artists with one sized for the current
        axes extent. ``update_plot`` resets ``self._scale_artists`` after
        every ``fig.clear()`` so the artists we are about to remove here
        are always live on the current axes."""
        ax = self._ax
        if ax is None:
            return
        for artist in self._scale_artists:
            artist.remove()
        self._scale_artists = []

        if self.scale_auto_chk.isChecked():
            x_min, x_max = ax.get_xlim()
            length_km = auto_scale_length_km(x_min, x_max, self._lat0)
        else:
            length_km = float(self.scale_length.value())

        line, text = _add_scale_bar(ax, length_km=length_km, lat0=self._lat0)
        self._scale_artists = [line, text]

    def export_plot(self) -> None:
        from ._export_helpers import ask_export_path, save_figure
        path = ask_export_path(self, suggested_name="sample_map.pdf",
                              title="Export map")
        if path is None:
            return
        save_figure(self, self.canvas.figure, path)

    # ------------------------------------------------------------------ impl
    def _populate_coords(self) -> None:
        """Fill every coordinate combo box from the current dataframe and
        guess sensible defaults per format from column-name aliases.

        When the columns are the ones the boxes were last filled from,
        the choices already made are kept: re-entering the view, or a
        session restored before it, must not put the guesses back.
        """
        df = self.data.df
        columns = (tuple(str(c) for c in df.columns)
                   if df is not None and not df.empty else ())

        # Every combo gets every column — the user can pick anything.
        all_combos = (
            self.lat_combo, self.lon_combo,
            self.utm_e_combo, self.utm_n_combo,
            self.utm_zone_combo, self.utm_hem_combo,
            self.dms_lat_combo, self.dms_lon_combo,
            self.suffix_lat_combo, self.suffix_lon_combo,
            self.mgrs_combo,
        )
        same = bool(columns) and columns == self._populated_for
        previous = {c: c.currentText() for c in all_combos} if same else {}
        self._populated_for = columns
        for c in all_combos:
            c.blockSignals(True)
            c.clear()

        if df is None or df.empty:
            for c in all_combos:
                c.blockSignals(False)
            self._populate_variables(df, keep=False)
            return

        for col in df.columns:
            for c in all_combos:
                c.addItem(str(col), col)

        # Per-format auto-guesses
        def _select(combo: QComboBox, col: Optional[str]) -> None:
            if col is None:
                return
            i = combo.findData(col)
            if i >= 0:
                combo.setCurrentIndex(i)

        _select(self.lat_combo, _coords.resolve_column(df, _coords.LAT_ALIASES))
        _select(self.lon_combo, _coords.resolve_column(df, _coords.LON_ALIASES))
        _select(self.utm_e_combo,
                _coords.resolve_column(df, _coords.EASTING_ALIASES))
        _select(self.utm_n_combo,
                _coords.resolve_column(df, _coords.NORTHING_ALIASES))
        _select(self.utm_zone_combo,
                _coords.resolve_column(df, _coords.ZONE_ALIASES))
        _select(self.utm_hem_combo,
                _coords.resolve_column(df, _coords.HEMISPHERE_ALIASES))
        _select(self.dms_lat_combo, _coords.resolve_column(
            df, _coords.DMS_LAT_ALIASES + _coords.LAT_ALIASES))
        _select(self.dms_lon_combo, _coords.resolve_column(
            df, _coords.DMS_LON_ALIASES + _coords.LON_ALIASES))
        _select(self.suffix_lat_combo,
                _coords.resolve_column(df, _coords.LAT_ALIASES))
        _select(self.suffix_lon_combo,
                _coords.resolve_column(df, _coords.LON_ALIASES))
        _select(self.mgrs_combo,
                _coords.resolve_column(df, _coords.MGRS_ALIASES))
        for combo, text in previous.items():
            i = combo.findText(text)
            if i >= 0:
                combo.setCurrentIndex(i)

        for c in all_combos:
            c.blockSignals(False)
        self._populate_variables(df, keep=same)

    def _populate_variables(self, df, *, keep: bool) -> None:
        """Numeric columns that can be kriged, coordinates left out."""
        previous = self.variable_combo.currentText() if keep else ""
        self.variable_combo.blockSignals(True)
        self.variable_combo.clear()
        if df is not None and not df.empty:
            coordinate_columns = {
                _coords.resolve_column(df, aliases)
                for aliases in (_coords.LAT_ALIASES, _coords.LON_ALIASES,
                                _coords.EASTING_ALIASES,
                                _coords.NORTHING_ALIASES,
                                _coords.ZONE_ALIASES)}
            for col in df.columns:
                if col in coordinate_columns:
                    continue
                values = pd.to_numeric(df[col], errors="coerce")
                if values.notna().sum() >= MIN_SAMPLES and values.nunique() > 1:
                    self.variable_combo.addItem(str(col), col)
        i = self.variable_combo.findText(previous) if previous else -1
        self.variable_combo.setCurrentIndex(
            i if i >= 0 else (0 if self.variable_combo.count() else -1))
        self.variable_combo.blockSignals(False)

    def _resolve_coords(self) -> Tuple[Optional[pd.Series],
                                        Optional[pd.Series],
                                        Optional[str]]:
        """Run the selected coordinate parser and return ``(lat, lon, error)``.

        ``error`` is a user-facing message when the chosen combination of
        columns can't be parsed (e.g. missing column); ``None`` on
        success.  ``lat``/``lon`` are pandas Series in decimal degrees
        WGS-84.
        """
        df = self.data.df
        if df is None or df.empty:
            return None, None, "Load a dataset first."
        fmt = self.format_combo.currentData() or _FMT_DECIMAL

        if fmt == _FMT_DECIMAL:
            lc = self.lat_combo.currentData()
            mc = self.lon_combo.currentData()
            if not lc or not mc:
                return None, None, (
                    "Pick Latitude and Longitude columns.\n"
                    "Expected one of: Latitude / Lat / LAT and "
                    "Longitude / Lon / LON.")
            lat, lon = _coords.from_decimal(df, lc, mc)
            return lat, lon, None

        if fmt == _FMT_UTM:
            ec = self.utm_e_combo.currentData()
            nc = self.utm_n_combo.currentData()
            if not ec or not nc:
                return None, None, ("Pick Easting and Northing columns.")
            zone_from_col = self.utm_zone_source.currentIndex() == 1
            hem_from_col  = self.utm_hem_source.currentIndex()  == 1
            zone_col = self.utm_zone_combo.currentData() if zone_from_col else None
            hem_col  = self.utm_hem_combo.currentData()  if hem_from_col  else None
            fixed_zone = None if zone_from_col else int(self.utm_zone_fixed.value())
            fixed_hem  = "" if hem_from_col else self.utm_hem_fixed.currentText()
            lat, lon = _coords.from_utm(
                df, ec, nc,
                zone_col=zone_col, hemisphere_col=hem_col,
                fixed_zone=fixed_zone, fixed_hemisphere=fixed_hem,
            )
            return lat, lon, None

        if fmt == _FMT_DMS:
            lc = self.dms_lat_combo.currentData()
            mc = self.dms_lon_combo.currentData()
            if not lc or not mc:
                return None, None, "Pick Latitude and Longitude DMS columns."
            lat, lon = _coords.from_dms(df, lc, mc)
            return lat, lon, None

        if fmt == _FMT_SUFFIX:
            lc = self.suffix_lat_combo.currentData()
            mc = self.suffix_lon_combo.currentData()
            if not lc or not mc:
                return None, None, "Pick Latitude and Longitude columns."
            lat, lon = _coords.from_suffix(df, lc, mc)
            return lat, lon, None

        if fmt == _FMT_MGRS:
            col = self.mgrs_combo.currentData()
            if not col:
                return None, None, "Pick the MGRS column."
            if not getattr(_coords, "_HAS_MGRS", False):
                return None, None, (
                    "The 'mgrs' package is not installed.  Install it "
                    "with: pip install mgrs")
            lat, lon = _coords.from_mgrs(df, col)
            return lat, lon, None

        return None, None, f"Unknown coordinate format: {fmt}"

    @staticmethod
    def _tick_in_degrees(ax) -> None:
        """Label the degree ticks with their hemisphere (19.43° N)."""
        from matplotlib.ticker import FuncFormatter, MaxNLocator

        # "99.25° W" is a long label; at matplotlib's default density a
        # narrow frame ran them together.
        for axis, bins in ((ax.xaxis, 5), (ax.yaxis, 6)):
            axis.set_major_locator(
                MaxNLocator(nbins=bins, steps=[1, 2, 2.5, 5, 10]))
        ax.xaxis.set_major_formatter(
            FuncFormatter(lambda v, _pos: _format_deg(v, axis="lon")))
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda v, _pos: _format_deg(v, axis="lat")))
        # Horizontal on both axes.  Latitude labels used to be turned on
        # end, which on a wide, shallow frame -- the shape a true-scale
        # map takes when samples spread east-west -- ran them into each
        # other.  tick_params rather than the label objects, so it holds
        # for whatever ticks the layout settles on.
        ax.tick_params(axis="both", labelsize=8)

    def _empty(self, ax, message: str) -> None:
        ax.text(0.5, 0.5, message, ha="center", va="center",
                color="#6c7388", fontsize=11, wrap=True,
                transform=ax.transAxes)
        ax.axis("off")

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        from .. import widget_state as ws
        return {
            # Coordinate format + per-format column choices
            "fmt": self.format_combo.currentData() or _FMT_DECIMAL,
            "lat": self.lat_combo.currentText(),
            "lon": self.lon_combo.currentText(),
            "utm_e": self.utm_e_combo.currentText(),
            "utm_n": self.utm_n_combo.currentText(),
            "utm_zone_src": self.utm_zone_source.currentIndex(),
            "utm_zone_col": self.utm_zone_combo.currentText(),
            "utm_zone_fixed": ws.spin_state(self.utm_zone_fixed),
            "utm_hem_src": self.utm_hem_source.currentIndex(),
            "utm_hem_col": self.utm_hem_combo.currentText(),
            "utm_hem_fixed": self.utm_hem_fixed.currentText(),
            "dms_lat": self.dms_lat_combo.currentText(),
            "dms_lon": self.dms_lon_combo.currentText(),
            "suffix_lat": self.suffix_lat_combo.currentText(),
            "suffix_lon": self.suffix_lon_combo.currentText(),
            "mgrs": self.mgrs_combo.currentText(),
            # Units of every stored coordinate below -- see
            # migrate_annotations_to_lonlat for why this is recorded.
            "axes_crs": AXES_CRS,
            # Styling
            "marker_size": ws.spin_state(self.marker_size),
            "marker_alpha": ws.spin_state(self.marker_alpha),
            "marker_edge": ws.check_state(self.marker_edge_chk),
            "auto_extent": ws.check_state(self.auto_extent_chk),
            "padding_pct": ws.spin_state(self.padding_pct),
            "grid": ws.check_state(self.grid_chk),
            "scale": ws.check_state(self.scale_chk),
            "scale_auto": ws.check_state(self.scale_auto_chk),
            "scale_length": ws.spin_state(self.scale_length),
            "north": ws.check_state(self.north_chk),
            "legend": ws.check_state(self.legend_chk),
            "annotations": self.annotation_ctl.serialize(),
            "frame": self._current_frame(),
            # Spatial analysis
            "display": self._display(),
            "variable": self._variable(),
            "transform": self._transform(),
            "pooled": self._pooled(),
            "model": self._model_kind(),
            "overrides": {label: list(p)
                          for label, p in self._overrides.items()},
            # Listed only once kriging has run: until then the restored
            # group is pending, and must be saved as such.
            "param_group": (self.param_group_combo.currentText()
                            or self._pending_param_group),
            "lags": ws.spin_state(self.lags_spin),
            "max_lag_km": ws.spin_state(self.max_lag_spin),
            "cells": ws.spin_state(self.cells_spin),
            "clip": ws.check_state(self.clip_chk),
            "buffer_km": ws.spin_state(self.buffer_spin),
            "contours": ws.check_state(self.contours_chk),
            "colour_by_value": ws.check_state(self.colour_by_value_chk),
        }

    def _current_frame(self):
        """The map frame on screen, as (lon_min, lon_max, lat_min,
        lat_max, lat0) -- what auto-fit off keeps -- or None."""
        if self._ax is not None:
            x0, x1 = self._ax.get_xlim()
            y0, y1 = self._ax.get_ylim()
            return [float(x0), float(x1), float(y0), float(y1),
                    float(self._lat0)]
        if self._last_map_limits is not None:
            return [float(v) for v in self._last_map_limits]
        return None

    def restore(self, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
        # Fill the selectors from the data first, so the saved column
        # choices have something to be restored into.
        self._populate_coords()
        # The axes on screen belong to whatever was open before; their
        # frame must not stand in for the session's.
        self._disconnect_view_callbacks()
        self._ax = None
        # Coordinate format dropdown
        fmt = state.get("fmt", _FMT_DECIMAL)
        idx = self.format_combo.findData(fmt)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        ws.restore_combo(self.lat_combo, {"text": state.get("lat", "")})
        ws.restore_combo(self.lon_combo, {"text": state.get("lon", "")})
        ws.restore_combo(self.utm_e_combo, {"text": state.get("utm_e", "")})
        ws.restore_combo(self.utm_n_combo, {"text": state.get("utm_n", "")})
        if isinstance(state.get("utm_zone_src"), int):
            self.utm_zone_source.setCurrentIndex(int(state["utm_zone_src"]))
        ws.restore_combo(self.utm_zone_combo,
                         {"text": state.get("utm_zone_col", "")})
        ws.restore_spin(self.utm_zone_fixed, state.get("utm_zone_fixed"))
        if isinstance(state.get("utm_hem_src"), int):
            self.utm_hem_source.setCurrentIndex(int(state["utm_hem_src"]))
        ws.restore_combo(self.utm_hem_combo,
                         {"text": state.get("utm_hem_col", "")})
        ws.restore_combo(self.utm_hem_fixed,
                         {"text": state.get("utm_hem_fixed", "")})
        ws.restore_combo(self.dms_lat_combo,
                         {"text": state.get("dms_lat", "")})
        ws.restore_combo(self.dms_lon_combo,
                         {"text": state.get("dms_lon", "")})
        ws.restore_combo(self.suffix_lat_combo,
                         {"text": state.get("suffix_lat", "")})
        ws.restore_combo(self.suffix_lon_combo,
                         {"text": state.get("suffix_lon", "")})
        ws.restore_combo(self.mgrs_combo, {"text": state.get("mgrs", "")})
        ws.restore_spin(self.marker_size, state.get("marker_size"))
        ws.restore_spin(self.marker_alpha, state.get("marker_alpha"))
        ws.restore_check(self.marker_edge_chk, state.get("marker_edge"))
        ws.restore_check(self.auto_extent_chk, state.get("auto_extent"))
        ws.restore_spin(self.padding_pct, state.get("padding_pct"))
        ws.restore_check(self.grid_chk, state.get("grid"))
        ws.restore_check(self.scale_chk, state.get("scale"))
        ws.restore_check(self.scale_auto_chk, state.get("scale_auto"))
        ws.restore_spin(self.scale_length, state.get("scale_length"))
        ws.restore_check(self.north_chk, state.get("north"))
        ws.restore_check(self.legend_chk, state.get("legend"))
        annotations = state.get("annotations")
        if state.get("axes_crs") != AXES_CRS:
            annotations = migrate_annotations_to_lonlat(annotations)
        self.annotation_ctl.restore(annotations)
        frame = state.get("frame")
        try:
            self._last_map_limits = (tuple(float(v) for v in frame)
                                     if frame and len(frame) == 5 else None)
        except (TypeError, ValueError):
            self._last_map_limits = None

        # Spatial analysis.  Every key is optional: sessions saved before
        # the view kriged have none of them.
        ws.restore_combo(self.variable_combo,
                         {"text": state.get("variable", "")})
        for combo, key in ((self.transform_combo, "transform"),
                           (self.pooling_combo, "pooled"),
                           (self.model_combo, "model")):
            if key in state:
                i = combo.findData(state[key])
                if i >= 0:
                    combo.setCurrentIndex(i)
        overrides = {}
        for label, params in (state.get("overrides") or {}).items():
            try:
                nugget, sill, range_km = (float(p) for p in params)
            except (TypeError, ValueError):
                continue
            overrides[str(label)] = (nugget, sill, range_km)
        self._overrides = overrides
        self._overrides_for = (self._variable(), self._transform())
        self._pending_param_group = str(state.get("param_group") or "")
        ws.restore_spin(self.lags_spin, state.get("lags"))
        ws.restore_spin(self.max_lag_spin, state.get("max_lag_km"))
        ws.restore_spin(self.cells_spin, state.get("cells"))
        ws.restore_check(self.clip_chk, state.get("clip"))
        ws.restore_spin(self.buffer_spin, state.get("buffer_km"))
        ws.restore_check(self.contours_chk, state.get("contours"))
        ws.restore_check(self.colour_by_value_chk,
                         state.get("colour_by_value"))
        keys = [k for k, _label in _DISPLAYS]
        if state.get("display") in keys:
            # Quietly: the main window redraws once the session is in.
            self.display_tabs.blockSignals(True)
            self.display_tabs.setCurrentIndex(keys.index(state["display"]))
            self.display_tabs.blockSignals(False)
