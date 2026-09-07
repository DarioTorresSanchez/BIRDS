"""Geospatial sample-location map view.

A matplotlib-based map that plots the position of every sample on top
of a web basemap (Esri WorldImagery, Esri WorldTopoMap or CartoDB
Positron). Samples are coloured per group using the shared
:class:`PlotStyle`, so the visual identity matches every other plot in
B.I.R.D.S.

Why matplotlib (and not Folium / Leaflet)?
    The Map view is meant to live alongside the publication-grade
    plots (TAS, REE, tectonic DFs). Keeping it as a matplotlib figure
    lets the user export it through the existing Export-plot pipeline
    (PNG / PDF / SVG with the chosen DPI). For an interactive
    "Google-Earth-style" view the user can still export a Folium HTML
    later, but the default is consistent with the rest of the app.
"""

from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
import pandas as pd
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
    QVBoxLayout,
    QWidget,
)

from .. import coords as _coords
from ..diagrams.templates.base import get_groups, resolve_column
from .annotation_controller import AnnotationController, nearest_sample
from .plot_canvas import PlotCanvas


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


# ---------------------------------------------------------------------------
# contextily is optional — we let the view fall back to "no basemap"
# silently when it (or internet) is unavailable.
# ---------------------------------------------------------------------------

try:
    import contextily as _cx
    _HAS_CTX = True
except ImportError:                                          # pragma: no cover
    _cx = None
    _HAS_CTX = False


# Friendly labels → contextily provider object
def _basemap_provider(name: str):
    if not _HAS_CTX or name == "None":
        return None
    table = {
        "Satellite (Esri WorldImagery)":  _cx.providers.Esri.WorldImagery,
        "Topographic (Esri WorldTopoMap)": _cx.providers.Esri.WorldTopoMap,
        "Light grayscale (CartoDB Positron)": _cx.providers.CartoDB.Positron,
    }
    return table.get(name)


_BASEMAPS = (
    "Satellite (Esri WorldImagery)",
    "Topographic (Esri WorldTopoMap)",
    "Light grayscale (CartoDB Positron)",
    "None",
)


# ---------------------------------------------------------------------------
# Geographic helpers
# ---------------------------------------------------------------------------

# Earth radius used by EPSG:3857 (sphere, not WGS-84 ellipsoid)
_R_EARTH = 6_378_137.0


def _wgs84_to_web_mercator(lon: pd.Series, lat: pd.Series
                           ) -> Tuple[pd.Series, pd.Series]:
    """Transform WGS-84 lon/lat (deg) into Web Mercator (EPSG:3857) metres."""
    lat = lat.clip(-85.05112878, 85.05112878)  # Web Mercator limit
    x = _R_EARTH * np.radians(lon)
    y = _R_EARTH * np.log(np.tan(np.pi / 4.0 + np.radians(lat) / 2.0))
    return x, y


_LAT_ALIASES = ("Latitude", "Lat", "lat", "LAT", "Y", "y_coord",
                "Latitud", "latitud", "y")
_LON_ALIASES = ("Longitude", "Lon", "lon", "Lng", "lng", "LONG", "LON",
                "X", "x_coord", "Longitud", "longitud", "x")


def _resolve_latlon(df: pd.DataFrame
                    ) -> Tuple[Optional[str], Optional[str]]:
    """Return (lat_col, lon_col) using a generous list of synonyms."""
    return (resolve_column(df, _LAT_ALIASES),
            resolve_column(df, _LON_ALIASES))


def _mercator_cos_phi(y_centre: float) -> float:
    """Latitude-contraction factor at Web-Mercator y-coordinate *y_centre*.

    Inverse of the EPSG:3857 forward projection: 1° of longitude at
    latitude φ corresponds to ``cos(φ) × 1° × R_EARTH`` metres of
    ground distance. Floor at 0.05 to avoid singularities near the
    polar clip (±85°).
    """
    return max(np.cos(np.arctan(np.sinh(y_centre / _R_EARTH))), 0.05)


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


def _auto_scale_length_km(x_min: float, x_max: float,
                          y_centre: float, *,
                          target_fraction: float = 0.20) -> float:
    """Compute a tidy scale-bar length from the current axes extent."""
    width_km = (x_max - x_min) * _mercator_cos_phi(y_centre) / 1000.0
    return _nice_round(width_km * target_fraction)


def _add_scale_bar(ax, *, length_km: float, fraction_pad: float = 0.04
                    ) -> tuple:
    """Draw a horizontal scale bar and return ``(line_artist, text_artist)``
    so the caller can keep references and remove them on the next redraw.
    """
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    bar_metres = (length_km * 1000.0) / _mercator_cos_phi((y_min + y_max) / 2.0)
    x_start = x_min + fraction_pad * (x_max - x_min)
    y_pos = y_min + 0.05 * (y_max - y_min)
    line, = ax.plot([x_start, x_start + bar_metres], [y_pos, y_pos],
                    color="black", linewidth=3, solid_capstyle="butt",
                    zorder=10)
    label = f"{length_km:g} km" if length_km < 10 else f"{int(length_km)} km"
    text = ax.text(x_start + bar_metres / 2.0,
                   y_pos + 0.012 * (y_max - y_min),
                   label, ha="center", va="bottom",
                   fontsize=9, color="black",
                   bbox=dict(facecolor="white", edgecolor="none",
                             alpha=0.75, pad=1.4), zorder=11)
    return line, text


def _add_north_arrow(ax) -> None:
    """Draw a small north arrow in the upper-right corner."""
    ax.annotate(
        "N", xy=(0.95, 0.93), xytext=(0.95, 0.83),
        xycoords="axes fraction", textcoords="axes fraction",
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
# MapView widget
# ---------------------------------------------------------------------------

class MapView(QWidget):
    """Plot sample locations on a web basemap."""

    def __init__(self, data_manager, plot_style,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style

        # Artists for the live scale bar; cleared on every redraw so the
        # zoom-/pan-triggered callback can replace them without leaking.
        # _cid_x / _cid_y are the axes-callback IDs for the live-update
        # hook; we disconnect them before every redraw to keep their
        # count bounded (otherwise N updates would queue N callbacks).
        self._scale_artists: list = []
        self._ax = None
        self._cid_x: int | None = None
        self._cid_y: int | None = None

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
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
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

        self.canvas = PlotCanvas()
        rl.addWidget(self.canvas, stretch=1)
        splitter.addWidget(right)
        splitter.setSizes([460, 820])
        self.annotation_ctl.bind_canvas(self.canvas)

        if not _HAS_CTX:
            self.subtitle_label.setText(
                self.subtitle_label.text()
                + "  ⚠  contextily is not installed — the basemap will be "
                  "skipped (run: pip install contextily)."
            )

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

        # ---- Basemap ------------------------------------------------------
        base_box = QGroupBox("Basemap")
        bv = _wrap(base_box)
        bf = _compact_form()
        self.basemap_combo = QComboBox()
        for name in _BASEMAPS:
            self.basemap_combo.addItem(name)
        if not _HAS_CTX:
            for i in range(self.basemap_combo.count()):
                if self.basemap_combo.itemText(i) != "None":
                    self.basemap_combo.model().item(i).setEnabled(False)
            self.basemap_combo.setCurrentText("None")
        bf.addRow("Style:", self.basemap_combo)
        self.basemap_alpha = QDoubleSpinBox()
        self.basemap_alpha.setRange(0.0, 1.0)
        self.basemap_alpha.setSingleStep(0.05)
        self.basemap_alpha.setValue(1.0)
        bf.addRow("Basemap opacity:", self.basemap_alpha)
        bv.addLayout(bf)
        layout.addWidget(base_box)

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
        mv.addLayout(mf)
        layout.addWidget(mark_box)

        # ---- Extent -------------------------------------------------------
        ext_box = QGroupBox("Map extent")
        ev = _wrap(ext_box)
        ef = _compact_form()
        self.auto_extent_chk = QCheckBox("Auto-fit to samples")
        self.auto_extent_chk.setChecked(True)
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
        # Map clicks fire in Web-Mercator metres but the resolver maps
        # back to lat/lon transparently for the user-visible label.
        self.annotation_ctl = AnnotationController(
            self, sample_resolver=self._resolve_sample)
        layout.addWidget(self.annotation_ctl.group)

        layout.addStretch(1)

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

    def update_plot(self) -> None:
        df = self.data.df
        fig = self.canvas.figure
        fig.clear()
        # ``fig.clear()`` invalidates every artist on the previous axes —
        # forget about the scale-bar pair so the live-update code never
        # tries to .remove() a dead artist.
        self._scale_artists = []
        ax = fig.add_subplot(111)

        if df is None or df.empty:
            self._empty(ax, "Load a dataset (Data → Import) to plot a map.")
            self.canvas.draw()
            return

        # Parse coordinates once for the whole dataset using the selected
        # format.  This gives us lat/lon Series we then slice per group.
        lat_all, lon_all, err = self._resolve_coords()
        if err is not None:
            self._empty(ax, err)
            self.canvas.draw()
            return
        if lat_all is None or lat_all.dropna().empty:
            self._empty(
                ax,
                "No samples could be parsed in the selected format.\n"
                "Check the column choices and that values are valid.",
            )
            self.canvas.draw()
            return

        # Plot per group ----------------------------------------------------
        any_data = False
        all_x, all_y = [], []
        for label, sub, gs in get_groups(df, self.plot_style):
            if gs is not None and not getattr(gs, "visible", True):
                continue
            # Slice the pre-parsed series — preserves df.index alignment.
            lat = lat_all.loc[sub.index]
            lon = lon_all.loc[sub.index]
            mask = lat.notna() & lon.notna() & lat.between(-90, 90) \
                   & lon.between(-180, 180)
            lat = lat[mask]
            lon = lon[mask]
            if lat.empty:
                continue
            x, y = _wgs84_to_web_mercator(lon, lat)
            color = gs.color if gs else "#1f77b4"
            marker = gs.marker if gs else "o"
            ax.scatter(
                x, y,
                s=(self.marker_size.value() ** 2),
                alpha=self.marker_alpha.value(),
                c=color, marker=marker, label=label,
                edgecolors="black" if self.marker_edge_chk.isChecked() else "none",
                linewidths=0.5 if self.marker_edge_chk.isChecked() else 0,
                zorder=5,
            )
            all_x.extend(x.tolist())
            all_y.extend(y.tolist())
            any_data = True

        if not any_data:
            # The coordinate columns parsed, but nothing survived the
            # range check.  Name the columns when the parser labelled the
            # series (decimal degrees); the UTM and MGRS parsers build
            # unnamed series, so fall back to a generic phrase rather
            # than reaching for names that do not exist here.
            lat_name = getattr(lat_all, "name", None) or "latitude"
            lon_name = getattr(lon_all, "name", None) or "longitude"
            self._empty(
                ax,
                f"No usable coordinates in '{lat_name}' / '{lon_name}'.\n"
                "Make sure the values are numeric and inside "
                "[-90, 90] × [-180, 180].",
            )
            self.canvas.draw()
            return

        # Extent -----------------------------------------------------------
        x_min, x_max = float(min(all_x)), float(max(all_x))
        y_min, y_max = float(min(all_y)), float(max(all_y))
        dx = max(x_max - x_min, 1.0)
        dy = max(y_max - y_min, 1.0)
        pad = self.padding_pct.value() / 100.0
        # Guarantee a minimum size (~5 km) so the basemap zoom level is sane
        min_size = 5_000.0
        if dx < min_size:
            mid = (x_min + x_max) / 2.0
            x_min, x_max = mid - min_size / 2, mid + min_size / 2
            dx = x_max - x_min
        if dy < min_size:
            mid = (y_min + y_max) / 2.0
            y_min, y_max = mid - min_size / 2, mid + min_size / 2
            dy = y_max - y_min
        ax.set_xlim(x_min - pad * dx, x_max + pad * dx)
        ax.set_ylim(y_min - pad * dy, y_max + pad * dy)
        ax.set_aspect("equal")

        # Basemap ----------------------------------------------------------
        basemap_name = self.basemap_combo.currentText()
        provider = _basemap_provider(basemap_name)
        if provider is not None:
            try:
                _cx.add_basemap(
                    ax, source=provider, crs="EPSG:3857",
                    attribution_size=7, alpha=self.basemap_alpha.value(),
                )
            except Exception as exc:                       # noqa: BLE001
                # No internet, blocked CDN, etc. — just skip the basemap
                ax.text(
                    0.5, 0.97, f"⚠  Basemap unavailable ({type(exc).__name__})",
                    transform=ax.transAxes, ha="center", va="top",
                    fontsize=8, color="#a04c2e",
                    bbox=dict(facecolor="white", edgecolor="#a04c2e",
                              alpha=0.85, pad=2),
                )

        # Grid (lat/lon ticks in degrees on a Web-Mercator axes) -----------
        self._tick_in_degrees(ax)
        if self.grid_chk.isChecked():
            ax.grid(True, which="major", linestyle=":", linewidth=0.6,
                    color="#666", alpha=0.6)
        else:
            ax.grid(False)

        # Scale bar & north arrow ------------------------------------------
        # ``fig.clear()`` dropped the previous axes; bind the live-update
        # callbacks to the new one (matplotlib stores them on the axes,
        # not on the figure, so we have to re-connect after every redraw).
        # We track the CIDs so we can disconnect when the user toggles
        # the scale bar off or before the next redraw.
        self._ax = ax
        self._disconnect_view_callbacks()
        if self.scale_chk.isChecked():
            self._redraw_scale_bar()
            self._cid_x = ax.callbacks.connect("xlim_changed",
                                                self._on_view_changed)
            self._cid_y = ax.callbacks.connect("ylim_changed",
                                                self._on_view_changed)
        if self.north_chk.isChecked():
            _add_north_arrow(ax)

        # Legend -----------------------------------------------------------
        if self.legend_chk.isChecked():
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc="lower right", fontsize=9,
                          framealpha=0.85, facecolor="white",
                          edgecolor="#666")

        ax.set_xlabel("")
        ax.set_ylabel("")
        fig.tight_layout()
        # Replay user annotations on the map axis.  Note: their (x, y)
        # coordinates are in Web-Mercator metres, matching the axis.
        self.annotation_ctl.draw(ax)
        from .brushing import draw_selection_overlay
        draw_selection_overlay(self)
        self.canvas.draw()

    def _selection_points(self, names):
        """Web-Mercator coordinates of the selected samples."""
        from .brushing import names_series
        df = self.data.df
        axes = self.canvas.figure.axes
        if df is None or df.empty or not axes:
            return []
        lat, lon, err = self._resolve_coords()
        if err is not None or lat is None or lon is None:
            return []
        xs, ys = _wgs84_to_web_mercator(lon, lat)
        nm = names_series(df)
        m = nm.isin(names) & xs.notna() & ys.notna()
        return [(axes[0], list(zip(xs[m], ys[m])))]

    def _resolve_sample(self, x: float, y: float):
        """Sample resolver — finds the data row whose lat/lon, projected
        to Web-Mercator, lands closest to the user's click (also in
        Web-Mercator metres)."""
        df = self.data.df
        if df is None or df.empty:
            return None
        lat, lon, err = self._resolve_coords()
        if err is not None or lat is None or lon is None:
            return None
        # Project the dataset's lat/lon into Web-Mercator so distances
        # are in the same space as the click coordinates.
        xs, ys = _wgs84_to_web_mercator(lon, lat)
        axes = self.canvas.figure.axes
        if not axes:
            return None
        return nearest_sample(df, xs, ys, x, y,
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
            y_min, y_max = ax.get_ylim()
            length_km = _auto_scale_length_km(
                x_min, x_max, (y_min + y_max) / 2.0)
        else:
            length_km = float(self.scale_length.value())

        line, text = _add_scale_bar(ax, length_km=length_km)
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
        guess sensible defaults per format from column-name aliases."""
        df = self.data.df

        # Every combo gets every column — the user can pick anything.
        all_combos = (
            self.lat_combo, self.lon_combo,
            self.utm_e_combo, self.utm_n_combo,
            self.utm_zone_combo, self.utm_hem_combo,
            self.dms_lat_combo, self.dms_lon_combo,
            self.suffix_lat_combo, self.suffix_lon_combo,
            self.mgrs_combo,
        )
        for c in all_combos:
            c.blockSignals(True)
            c.clear()

        if df is None or df.empty:
            for c in all_combos:
                c.blockSignals(False)
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

        for c in all_combos:
            c.blockSignals(False)

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
        """Replace the EPSG:3857 metre ticks with the equivalent decimal-
        degree labels (no projection change, just a cosmetic relabel).
        """
        from matplotlib.ticker import FuncFormatter

        def _x_to_lon(x, _pos):
            lon = np.degrees(x / _R_EARTH)
            return _format_deg(lon, axis="lon")

        def _y_to_lat(y, _pos):
            lat = np.degrees(2.0 * np.arctan(np.exp(y / _R_EARTH))
                             - np.pi / 2.0)
            return _format_deg(lat, axis="lat")

        ax.xaxis.set_major_formatter(FuncFormatter(_x_to_lon))
        ax.yaxis.set_major_formatter(FuncFormatter(_y_to_lat))
        for t in ax.get_xticklabels():
            t.set_fontsize(8)
        for t in ax.get_yticklabels():
            t.set_fontsize(8)
            t.set_rotation(90)
            t.set_ha("center")

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
            # Styling
            "basemap": self.basemap_combo.currentText(),
            "basemap_alpha": ws.spin_state(self.basemap_alpha),
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
        }

    def restore(self, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
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
        ws.restore_combo(self.basemap_combo,
                         {"text": state.get("basemap", "")})
        ws.restore_spin(self.basemap_alpha, state.get("basemap_alpha"))
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
        self.annotation_ctl.restore(state.get("annotations"))
