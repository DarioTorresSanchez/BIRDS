"""Isotope diagrams view — Sr-Nd and Pb isotope systems.

Two sections are bundled into a single widget:

* **Sr-Nd**: ⁸⁷Sr/⁸⁶Sr  vs  ¹⁴³Nd/¹⁴⁴Nd, optional age correction to
  initial ratios, optional εNd / εSr secondary axes, six mantle
  reservoirs (DM, BSE/CHUR, PREMA, HIMU, EM1, EM2) and the mantle-array
  reference line.
* **Pb**: ²⁰⁶Pb/²⁰⁴Pb  vs  ²⁰⁷Pb/²⁰⁴Pb and  ²⁰⁶Pb/²⁰⁴Pb  vs
  ²⁰⁸Pb/²⁰⁴Pb. The Northern Hemisphere Reference Line (NHRL; Hart 1984)
  is drawn on the 208/204 panel only.

References
----------
- Zindler, A. & Hart, S.R. (1986). Chemical geodynamics. *Annu. Rev. Earth Planet. Sci.* 14, 493-571.
- Hart, S.R. (1984). A large-scale isotope anomaly in the Southern Hemisphere mantle. *Nature* 309, 753-757.
- Hofmann, A.W. (2003). Sampling mantle heterogeneity through oceanic basalts. *Treatise on Geochemistry* 2, 61-101.
- DePaolo, D.J. & Wasserburg, G.J. (1976). Nd isotopic variations and petrogenetic models. *GRL* 3, 249-252.
- Bouvier, A., Vervoort, J.D. & Patchett, P.J. (2008). The Lu-Hf and Sm-Nd isotopic composition of CHUR. *EPSL* 273, 48-57.
- Steiger, R.H. & Jäger, E. (1977). Subcommission on geochronology: convention on the use of decay constants. *EPSL* 36, 359-362.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..diagrams.templates.base import get_groups, resolve_column
from .annotation_controller import AnnotationController, nearest_sample
from .plot_canvas import PlotCanvas


# ---------------------------------------------------------------------------
# Geochemical constants
# ---------------------------------------------------------------------------

# Decay constants (Steiger & Jäger 1977)
LAMBDA_RB = 1.42e-11    # /yr  - 87Rb -> 87Sr
LAMBDA_SM = 6.54e-12    # /yr  - 147Sm -> 143Nd

# Bulk Silicate Earth / Uniform Reservoir / CHUR  (Bouvier et al. 2008)
SR_UR_87_86 = 0.7045
RB_SR_UR    = 0.0827
ND_CHUR     = 0.512638
SM_ND_CHUR  = 0.1967

# Approximate elemental → parent-isotope-ratio conversions used when the
# user only provides Rb / Sr / Sm / Nd concentrations (ppm).
RB_SR_TO_87_86 = 2.894    # 87Rb/86Sr ≈ this × (Rb/Sr)
SM_ND_TO_147_144 = 0.6043 # 147Sm/144Nd ≈ this × (Sm/Nd)

# ---------------------------------------------------------------------------
# Mantle reservoirs — present-day 87Sr/86Sr , 143Nd/144Nd  (Zindler & Hart
# 1986; Hofmann 2003). Colours match the conventional petrology palette.
# ---------------------------------------------------------------------------

RESERVOIRS: Dict[str, Tuple[float, float, str, str]] = {
    # name -> (87Sr/86Sr, 143Nd/144Nd, long_name, colour)
    "DM":    (0.70220, 0.51315, "Depleted MORB Mantle",        "#2a9d8f"),
    "BSE":   (0.70450, 0.51264, "Bulk Silicate Earth / CHUR",  "#264653"),
    "PREMA": (0.70330, 0.51298, "Prevalent Mantle",            "#e9c46a"),
    "HIMU":  (0.70290, 0.51285, "High-µ",                      "#f4a261"),
    "EM1":   (0.70500, 0.51240, "Enriched Mantle 1",           "#9d4edd"),
    "EM2":   (0.70800, 0.51260, "Enriched Mantle 2",           "#e63946"),
}

# Approximate mantle array (DM ↔ BSE ↔ EM, slope from Faure & Mensing 2005).
# Drawn as a dashed grey line on the Sr-Nd panel when the user toggles it on.
MANTLE_ARRAY_SR = (0.7020, 0.7090)        # (x_low, x_high)
MANTLE_ARRAY_ND = (0.51325, 0.51230)      # corresponding y at those x's

# NHRL (Hart 1984) — Northern Hemisphere Reference Line
NHRL_207_206 = (0.1084, 13.491)           # slope, intercept (drawn optionally)
NHRL_208_206 = (1.209,  15.627)           # slope, intercept


# ---------------------------------------------------------------------------
# Column resolution
# ---------------------------------------------------------------------------

_SR_RATIO_ALIASES = (
    "87Sr/86Sr", "Sr87/86Sr", "Sr87/Sr86", "Sr87_86Sr",
    "87Sr_86Sr", "87/86Sr", "Sr87/86",
)
_ND_RATIO_ALIASES = (
    "143Nd/144Nd", "Nd143/144Nd", "Nd143/Nd144", "Nd143_144Nd",
    "143Nd_144Nd", "143/144Nd",
)
_PB206_ALIASES = ("206Pb/204Pb", "Pb206/204Pb", "Pb206/Pb204",
                  "206Pb_204Pb", "206/204Pb")
_PB207_ALIASES = ("207Pb/204Pb", "Pb207/204Pb", "Pb207/Pb204",
                  "207Pb_204Pb", "207/204Pb")
_PB208_ALIASES = ("208Pb/204Pb", "Pb208/204Pb", "Pb208/Pb204",
                  "208Pb_204Pb", "208/204Pb")
_RB_SR_PARENT  = ("87Rb/86Sr", "Rb87/86Sr", "87Rb_86Sr")
_SM_ND_PARENT  = ("147Sm/144Nd", "Sm147/144Nd", "147Sm_144Nd")
_AGE_ALIASES   = ("Age", "AGE", "Age_Ma", "Age (Ma)", "age", "age_Ma")


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------

def compute_initial_ratio(measured: pd.Series, parent: pd.Series,
                          age_Ma: pd.Series, lam: float) -> pd.Series:
    """Apply the age correction:  R_i = R_m - P × (e^{λ t} - 1)."""
    t = age_Ma * 1.0e6   # Ma → yr
    return measured - parent * (np.exp(lam * t) - 1.0)


def epsilon_nd(nd_ratio: pd.Series) -> pd.Series:
    return (nd_ratio / ND_CHUR - 1.0) * 1.0e4


def epsilon_sr(sr_ratio: pd.Series) -> pd.Series:
    return (sr_ratio / SR_UR_87_86 - 1.0) * 1.0e4


# ---------------------------------------------------------------------------
# Helper: parent ratio either from a dedicated column or from concentrations
# ---------------------------------------------------------------------------

def _resolve_parent_rb_sr(df: pd.DataFrame) -> Optional[pd.Series]:
    col = resolve_column(df, _RB_SR_PARENT)
    if col is not None:
        return pd.to_numeric(df[col], errors="coerce")
    rb = resolve_column(df, ("Rb",))
    sr = resolve_column(df, ("Sr",))
    if rb is None or sr is None:
        return None
    rb_s = pd.to_numeric(df[rb], errors="coerce")
    sr_s = pd.to_numeric(df[sr], errors="coerce")
    return RB_SR_TO_87_86 * (rb_s / sr_s)


def _resolve_parent_sm_nd(df: pd.DataFrame) -> Optional[pd.Series]:
    col = resolve_column(df, _SM_ND_PARENT)
    if col is not None:
        return pd.to_numeric(df[col], errors="coerce")
    sm = resolve_column(df, ("Sm",))
    nd = resolve_column(df, ("Nd",))
    if sm is None or nd is None:
        return None
    sm_s = pd.to_numeric(df[sm], errors="coerce")
    nd_s = pd.to_numeric(df[nd], errors="coerce")
    return SM_ND_TO_147_144 * (sm_s / nd_s)


# ---------------------------------------------------------------------------
# IsotopesView widget
# ---------------------------------------------------------------------------

DIAGRAMS = (
    ("Sr-Nd:  ⁸⁷Sr/⁸⁶Sr  vs  ¹⁴³Nd/¹⁴⁴Nd",     "sr_nd"),
    ("Pb:      ²⁰⁶Pb/²⁰⁴Pb  vs  ²⁰⁷Pb/²⁰⁴Pb",   "pb_207"),
    ("Pb:      ²⁰⁶Pb/²⁰⁴Pb  vs  ²⁰⁸Pb/²⁰⁴Pb",   "pb_208"),
)


class IsotopesView(QWidget):
    """Top-level isotope plotting view (Sr-Nd & Pb)."""

    def __init__(self, data_manager, plot_style,
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.data = data_manager
        self.plot_style = plot_style

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # ---- Controls panel ---------------------------------------------------
        controls = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(controls)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._build_controls(controls)

        # Sticky action bar — 3 buttons always visible
        self.update_btn = QPushButton("Update plot")
        self.update_btn.setMinimumHeight(34)
        self.update_btn.setStyleSheet(
            "QPushButton { font-weight: 600; padding: 6px 12px; }"
        )
        self.update_btn.clicked.connect(self.update_plot)
        self.compute_btn = QPushButton("Compute initials & ε…")
        self.compute_btn.setMinimumHeight(28)
        self.compute_btn.clicked.connect(self.compute_initials_dialog)
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
        small_row = QHBoxLayout()
        small_row.setSpacing(4)
        small_row.addWidget(self.compute_btn)
        small_row.addWidget(self.export_btn)
        btn_pad_l.addLayout(small_row)
        left_layout.addWidget(btn_pad)
        left_panel.setMinimumWidth(380)
        left_panel.setMaximumWidth(540)
        splitter.addWidget(left_panel)

        # ---- Right: header + canvas ------------------------------------------
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(12, 12, 12, 12)
        rl.setSpacing(6)
        self.title_label = QLabel("Isotope diagrams")
        self.title_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        self.subtitle_label = QLabel("Select a diagram from the controls panel.")
        self.subtitle_label.setStyleSheet("color: #5b6478;")
        self.subtitle_label.setWordWrap(True)
        rl.addWidget(self.title_label)
        rl.addWidget(self.subtitle_label)
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        rl.addWidget(sep)
        self.canvas = PlotCanvas()
        rl.addWidget(self.canvas, stretch=1)

        # Small summary label shown below the canvas (mean ε etc.)
        # Wire the annotation toolkit's click handler now that the
        # AnnotationController and the canvas both exist.
        self.annotation_ctl.bind_canvas(self.canvas)

        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("color: #5b6478; font-family: 'Menlo', 'Monaco', 'Consolas', 'Courier New', monospace; font-size: 11px;")
        self.summary_label.setWordWrap(True)
        rl.addWidget(self.summary_label)

        splitter.addWidget(right)
        splitter.setSizes([460, 820])

        self._on_diagram_changed(0)

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

        # Diagram selector --------------------------------------------------
        sel_box = QGroupBox("Selection")
        sel_v = _wrap(sel_box)
        f = _compact_form()
        self.diagram_combo = QComboBox()
        for label, key in DIAGRAMS:
            self.diagram_combo.addItem(label, key)
        self.diagram_combo.currentIndexChanged.connect(self._on_diagram_changed)
        f.addRow("Diagram:", self.diagram_combo)
        sel_v.addLayout(f)
        layout.addWidget(sel_box)

        # ---- Sr-Nd controls -----------------------------------------------
        self.snd_box = QGroupBox("Sr-Nd inputs")
        snd_v = _wrap(self.snd_box)
        sf = _compact_form()
        self.sr_combo = QComboBox()
        self.nd_combo = QComboBox()
        sf.addRow("⁸⁷Sr/⁸⁶Sr column:", self.sr_combo)
        sf.addRow("¹⁴³Nd/¹⁴⁴Nd column:", self.nd_combo)
        snd_v.addLayout(sf)
        layout.addWidget(self.snd_box)

        # ---- Age correction (Sr-Nd) ---------------------------------------
        age_tooltip = (
            "If the parent columns are missing, B.I.R.D.S derives them "
            "from elemental Rb/Sr and Sm/Nd: "
            "⁸⁷Rb/⁸⁶Sr ≈ 2.894 × Rb/Sr; "
            "¹⁴⁷Sm/¹⁴⁴Nd ≈ 0.6043 × Sm/Nd."
        )
        self.age_box = QGroupBox("Age correction → initial ratios + ε")
        self.age_box.setCheckable(True)
        self.age_box.setChecked(False)
        self.age_box.setToolTip(age_tooltip)
        age_v = _wrap(self.age_box)
        af = _compact_form()
        self.age_source = QComboBox()
        self.age_source.addItem("Use the same age for every sample", "single")
        self.age_source.addItem("Use a column from the data", "column")
        self.age_source.currentIndexChanged.connect(self._on_age_source_changed)
        af.addRow("Source:", self.age_source)
        self.age_value = QDoubleSpinBox()
        self.age_value.setRange(0.0, 5000.0)
        self.age_value.setDecimals(2)
        self.age_value.setValue(0.0)
        self.age_value.setSuffix("  Ma")
        af.addRow("Single age:", self.age_value)
        self.age_column = QComboBox()
        self.age_column.setEnabled(False)
        af.addRow("Age column:", self.age_column)
        self.parent_sr_combo = QComboBox()
        self.parent_nd_combo = QComboBox()
        af.addRow("⁸⁷Rb/⁸⁶Sr (parent):", self.parent_sr_combo)
        af.addRow("¹⁴⁷Sm/¹⁴⁴Nd (parent):", self.parent_nd_combo)
        age_v.addLayout(af)
        note = QLabel(
            "<i>Missing parent ratios are derived from Rb/Sr and Sm/Nd "
            "— hover ⓘ for the constants.</i>"
        )
        note.setStyleSheet("color: #6c7388; font-size: 11px;")
        note.setTextFormat(Qt.TextFormat.RichText)
        note.setWordWrap(True)
        note.setToolTip(age_tooltip)
        age_v.addWidget(note)
        layout.addWidget(self.age_box)

        # ---- Pb controls --------------------------------------------------
        self.pb_box = QGroupBox("Pb inputs")
        pb_v = _wrap(self.pb_box)
        pbf = _compact_form()
        self.pb206_combo = QComboBox()
        self.pb207_combo = QComboBox()
        self.pb208_combo = QComboBox()
        pbf.addRow("²⁰⁶Pb/²⁰⁴Pb column:", self.pb206_combo)
        pbf.addRow("²⁰⁷Pb/²⁰⁴Pb column:", self.pb207_combo)
        pbf.addRow("²⁰⁸Pb/²⁰⁴Pb column:", self.pb208_combo)
        pb_v.addLayout(pbf)
        layout.addWidget(self.pb_box)

        # ---- Reservoirs ---------------------------------------------------
        self.res_box = QGroupBox("Mantle reservoirs")
        rv = _wrap(self.res_box)
        self.res_checks: Dict[str, QCheckBox] = {}
        for name in RESERVOIRS:
            cb = QCheckBox(f"{name} — {RESERVOIRS[name][2]}")
            cb.setChecked(True)
            rv.addWidget(cb)
            self.res_checks[name] = cb
        layout.addWidget(self.res_box)

        # ---- Reference lines ----------------------------------------------
        self.ref_box = QGroupBox("Reference lines")
        rrv = _wrap(self.ref_box)
        self.mantle_array_chk = QCheckBox("Mantle array (Sr-Nd)")
        self.mantle_array_chk.setChecked(True)
        rrv.addWidget(self.mantle_array_chk)
        self.nhrl_chk = QCheckBox(
            "NHRL — Northern Hemisphere Reference Line (Pb 208/204)")
        self.nhrl_chk.setChecked(True)
        rrv.addWidget(self.nhrl_chk)
        self.eps_axes_chk = QCheckBox("Show secondary εNd / εSr axes (Sr-Nd)")
        self.eps_axes_chk.setChecked(True)
        rrv.addWidget(self.eps_axes_chk)
        self.legend_chk = QCheckBox("Show legend")
        self.legend_chk.setChecked(True)
        rrv.addWidget(self.legend_chk)
        layout.addWidget(self.ref_box)

        # Annotation toolkit — Sr-Nd / Pb-Pb diagrams are single-axis,
        # so all four tools work out of the box.
        self.annotation_ctl = AnnotationController(
            self, sample_resolver=self._resolve_sample)
        layout.addWidget(self.annotation_ctl.group)

        layout.addStretch(1)

    # ------------------------------------------------------------------ API
    def show_diagram(self) -> None:
        """Refresh column combos from the current dataframe and replot."""
        self._populate_columns()
        self._on_diagram_changed(self.diagram_combo.currentIndex())

    # ------------------------------------------------------------ controls
    def _on_diagram_changed(self, _index: int) -> None:
        key = self.diagram_combo.currentData()
        is_snd = key == "sr_nd"
        is_pb208 = key == "pb_208"
        self.snd_box.setVisible(is_snd)
        self.age_box.setVisible(is_snd)
        self.pb_box.setVisible(not is_snd)
        self.mantle_array_chk.setVisible(is_snd)
        self.eps_axes_chk.setVisible(is_snd)
        self.nhrl_chk.setVisible(is_pb208)
        self.res_box.setVisible(is_snd)

        if key == "sr_nd":
            self.title_label.setText("⁸⁷Sr/⁸⁶Sr  vs  ¹⁴³Nd/¹⁴⁴Nd")
            self.subtitle_label.setText(
                "Classical mantle-source diagram with the six end-member "
                "reservoirs (Zindler & Hart 1986; Hofmann 2003) and the "
                "mantle array. Toggle the age-correction box to plot the "
                "initial ratios and compute εNd / εSr at the chosen age."
            )
        elif key == "pb_207":
            self.title_label.setText("²⁰⁶Pb/²⁰⁴Pb  vs  ²⁰⁷Pb/²⁰⁴Pb")
            self.subtitle_label.setText(
                "Classical Pb-Pb isochron-style diagram. Useful for "
                "identifying the contribution of upper crust vs lower "
                "crust/mantle reservoirs."
            )
        else:
            self.title_label.setText("²⁰⁶Pb/²⁰⁴Pb  vs  ²⁰⁸Pb/²⁰⁴Pb")
            self.subtitle_label.setText(
                "²⁰⁶Pb/²⁰⁴Pb vs ²⁰⁸Pb/²⁰⁴Pb diagram with the Northern "
                "Hemisphere Reference Line (NHRL; Hart 1984) shown as a "
                "dashed reference."
            )
        self.summary_label.setText("")
        self.update_plot()

    def _on_age_source_changed(self, _index: int) -> None:
        is_column = self.age_source.currentData() == "column"
        self.age_value.setEnabled(not is_column)
        self.age_column.setEnabled(is_column)

    # ------------------------------------------------------------------
    # Dataframe accessor — prefer the standalone Isotopes sheet, fall
    # back to the main Data sheet for backward compatibility (e.g. when
    # the user imports a single-sheet CSV).
    # ------------------------------------------------------------------
    def _active_df(self):
        df = getattr(self.data, "isotopes_df", None)
        if df is not None and not df.empty:
            return df
        return self.data.df

    # --------------------------------------------------------- populate combos
    def _populate_columns(self) -> None:
        df = self._active_df()
        combos = (
            (self.sr_combo,         _SR_RATIO_ALIASES),
            (self.nd_combo,         _ND_RATIO_ALIASES),
            (self.pb206_combo,      _PB206_ALIASES),
            (self.pb207_combo,      _PB207_ALIASES),
            (self.pb208_combo,      _PB208_ALIASES),
            (self.parent_sr_combo,  _RB_SR_PARENT),
            (self.parent_nd_combo,  _SM_ND_PARENT),
            (self.age_column,       _AGE_ALIASES),
        )
        for combo, _ in combos:
            combo.blockSignals(True)
            combo.clear()
        if df is None or df.empty:
            for combo, _ in combos:
                combo.blockSignals(False)
            return
        for col in df.columns:
            for combo, _ in combos:
                combo.addItem(str(col), col)
        for combo, aliases in combos:
            guess = resolve_column(df, aliases)
            if guess is not None:
                i = combo.findData(guess)
                if i >= 0:
                    combo.setCurrentIndex(i)
            combo.blockSignals(False)

    # ------------------------------------------------------------------ data
    def _measured_sr_nd(self) -> Tuple[Optional[str], Optional[str]]:
        return self.sr_combo.currentData(), self.nd_combo.currentData()

    def _age_series(self, df: pd.DataFrame) -> Optional[pd.Series]:
        if self.age_source.currentData() == "single":
            return pd.Series(self.age_value.value(),
                             index=df.index, dtype="float64")
        col = self.age_column.currentData()
        if col is None or col not in df.columns:
            return None
        return pd.to_numeric(df[col], errors="coerce")

    def _initials_and_eps(self, df: pd.DataFrame) -> dict:
        """Compute initial ratios + epsilons for every sample. Returns a
        dict with arrays aligned to df.index."""
        sr_col, nd_col = self._measured_sr_nd()
        out: dict = {"sr_i": None, "nd_i": None, "eps_sr_i": None,
                     "eps_nd_i": None, "eps_sr_now": None,
                     "eps_nd_now": None}
        if sr_col:
            sr_now = pd.to_numeric(df[sr_col], errors="coerce")
            out["eps_sr_now"] = epsilon_sr(sr_now)
        if nd_col:
            nd_now = pd.to_numeric(df[nd_col], errors="coerce")
            out["eps_nd_now"] = epsilon_nd(nd_now)

        if not self.age_box.isChecked():
            return out
        if not sr_col or not nd_col:
            return out
        age = self._age_series(df)
        if age is None:
            return out
        parent_sr = _resolve_parent_rb_sr(df)
        parent_nd = _resolve_parent_sm_nd(df)
        if parent_sr is not None:
            sr_i = compute_initial_ratio(
                pd.to_numeric(df[sr_col], errors="coerce"),
                parent_sr, age, LAMBDA_RB)
            out["sr_i"] = sr_i
            out["eps_sr_i"] = epsilon_sr(sr_i)
        if parent_nd is not None:
            nd_i = compute_initial_ratio(
                pd.to_numeric(df[nd_col], errors="coerce"),
                parent_nd, age, LAMBDA_SM)
            out["nd_i"] = nd_i
            out["eps_nd_i"] = epsilon_nd(nd_i)
        return out

    # ------------------------------------------------------------------ plot
    def update_plot(self) -> None:
        df = self._active_df()
        if df is None or df.empty:
            self._empty("Load a dataset (Data → Import) to plot isotope diagrams.")
            return
        key = self.diagram_combo.currentData()
        if key == "sr_nd":
            self._plot_sr_nd(df)
        elif key == "pb_207":
            self._plot_pb(df, y_iso="207")
        else:
            self._plot_pb(df, y_iso="208")
        # Cross-view brushing overlay on whatever the panel just drew.
        from .brushing import draw_selection_overlay
        draw_selection_overlay(self)
        self.canvas.draw()

    def _current_plot_xy(self, df):
        """(xs, ys) matching what the active diagram plots for *df*,
        or (None, None) when the required columns aren't configured.
        Shared by the identify resolver and the brushing overlay."""
        key = self.diagram_combo.currentData()
        if key == "sr_nd":
            sr_col, nd_col = self._measured_sr_nd()
            if not sr_col or not nd_col:
                return None, None
            use_initial = self.use_initial_chk.isChecked() \
                if hasattr(self, "use_initial_chk") else False
            if use_initial:
                derived = self._derive_initial(df, sr_col, nd_col)
                if "sr_i" not in derived or "nd_i" not in derived:
                    return None, None
                return derived["sr_i"], derived["nd_i"]
            return (pd.to_numeric(df[sr_col], errors="coerce"),
                    pd.to_numeric(df[nd_col], errors="coerce"))
        x_col = self.pb206_combo.currentData()
        y_col = (self.pb207_combo.currentData() if key == "pb_207"
                 else self.pb208_combo.currentData())
        if (not x_col or x_col not in df.columns
                or not y_col or y_col not in df.columns):
            return None, None
        return (pd.to_numeric(df[x_col], errors="coerce"),
                pd.to_numeric(df[y_col], errors="coerce"))

    def _resolve_sample(self, x: float, y: float):
        """Sample resolver — reads the same columns the active diagram
        plots, so the user can click near any point and get its name."""
        df = self._active_df()
        if df is None or df.empty:
            return None
        xs, ys = self._current_plot_xy(df)
        if xs is None or ys is None:
            return None
        axes = self.canvas.figure.axes
        if not axes:
            return None
        return nearest_sample(df, xs, ys, x, y,
                              axes[0].get_xlim(), axes[0].get_ylim())

    def _selection_points(self, names):
        """Coordinates of the selected samples on the active isotope
        diagram, for the cross-view brushing overlay."""
        from .brushing import names_series
        df = self._active_df()
        axes = self.canvas.figure.axes
        if df is None or df.empty or not axes:
            return []
        xs, ys = self._current_plot_xy(df)
        if xs is None or ys is None:
            return []
        nm = names_series(df)
        m = nm.isin(names) & xs.notna() & ys.notna()
        return [(axes[0], list(zip(xs[m], ys[m])))]

    # ------------------- Sr-Nd
    def _plot_sr_nd(self, df: pd.DataFrame) -> None:
        sr_col, nd_col = self._measured_sr_nd()
        fig = self.canvas.figure
        fig.clear()
        if not sr_col or not nd_col:
            self._empty(
                "Pick the ⁸⁷Sr/⁸⁶Sr and ¹⁴³Nd/¹⁴⁴Nd columns in the "
                "controls panel.\n\nExpected column names include "
                "'87Sr/86Sr', 'Sr87/86Sr', '143Nd/144Nd', etc."
            )
            return

        ax = fig.add_subplot(111)

        # Compute initials & ε
        derived = self._initials_and_eps(df)
        use_initial = (self.age_box.isChecked()
                       and derived["sr_i"] is not None
                       and derived["nd_i"] is not None)

        # Plot data per group
        any_data = False
        for label, sub, gs in get_groups(df, self.plot_style):
            if gs is not None and not getattr(gs, "visible", True):
                continue
            if use_initial:
                xs = derived["sr_i"].loc[sub.index]
                ys = derived["nd_i"].loc[sub.index]
            else:
                xs = pd.to_numeric(sub[sr_col], errors="coerce")
                ys = pd.to_numeric(sub[nd_col], errors="coerce")
            mask = xs.notna() & ys.notna()
            xs, ys = xs[mask], ys[mask]
            if xs.empty:
                continue
            color = gs.color if gs else "#1f77b4"
            marker = gs.marker if gs else "o"
            ax.scatter(xs, ys,
                       s=(self.plot_style.point_size ** 2),
                       alpha=self.plot_style.alpha,
                       c=color, marker=marker, label=label,
                       edgecolors="black", linewidths=0.5, zorder=5)
            any_data = True

        # Reservoirs as starred markers
        for name, (sr, nd, long_name, color) in RESERVOIRS.items():
            if not self.res_checks[name].isChecked():
                continue
            ax.scatter([sr], [nd], marker="*", s=260, c=color,
                       edgecolors="black", linewidths=0.9, zorder=6,
                       label=f"{name} ({long_name})")
            ax.annotate(name, (sr, nd), xytext=(8, 6),
                        textcoords="offset points", fontsize=9,
                        fontweight="bold", color="black",
                        bbox=dict(facecolor="white", edgecolor="none",
                                  alpha=0.7, pad=1.5), zorder=7)

        # Mantle array
        if self.mantle_array_chk.isChecked():
            ax.plot(MANTLE_ARRAY_SR, MANTLE_ARRAY_ND,
                    color="#444", linewidth=1.4, linestyle="--",
                    alpha=0.85, zorder=2, label="Mantle array")

        # Axes
        ax.set_xlabel("⁸⁷Sr/⁸⁶Sr" + ("  (initial)" if use_initial else ""),
                      fontsize=12)
        ax.set_ylabel("¹⁴³Nd/¹⁴⁴Nd" + ("  (initial)" if use_initial else ""),
                      fontsize=12)
        ax.grid(True, which="major", linestyle=":", linewidth=0.5,
                color="#aaa", alpha=0.7)

        # Auto-fit axes around data + reservoirs
        all_x = [sr for _, (sr, _, _, _) in RESERVOIRS.items()]
        all_y = [nd for _, (_, nd, _, _) in RESERVOIRS.items()]
        if any_data:
            if use_initial:
                all_x += derived["sr_i"].dropna().tolist()
                all_y += derived["nd_i"].dropna().tolist()
            else:
                all_x += pd.to_numeric(df[sr_col], errors="coerce").dropna().tolist()
                all_y += pd.to_numeric(df[nd_col], errors="coerce").dropna().tolist()
        if all_x and all_y:
            x_min, x_max = min(all_x), max(all_x)
            y_min, y_max = min(all_y), max(all_y)
            x_pad = max((x_max - x_min) * 0.10, 0.001)
            y_pad = max((y_max - y_min) * 0.10, 0.00005)
            ax.set_xlim(x_min - x_pad, x_max + x_pad)
            ax.set_ylim(y_min - y_pad, y_max + y_pad)

        # Secondary axes — εSr (top) and εNd (right)
        if self.eps_axes_chk.isChecked():
            x_min, x_max = ax.get_xlim()
            y_min, y_max = ax.get_ylim()
            ax_top = ax.secondary_xaxis(
                "top",
                functions=(
                    lambda x: (x / SR_UR_87_86 - 1.0) * 1.0e4,
                    lambda eps: SR_UR_87_86 * (1.0 + eps / 1.0e4),
                ),
            )
            ax_top.set_xlabel("εSr", fontsize=11)
            ax_right = ax.secondary_yaxis(
                "right",
                functions=(
                    lambda y: (y / ND_CHUR - 1.0) * 1.0e4,
                    lambda eps: ND_CHUR * (1.0 + eps / 1.0e4),
                ),
            )
            ax_right.set_ylabel("εNd", fontsize=11)

        # Legend
        if self.legend_chk.isChecked():
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc="best", fontsize=8,
                          framealpha=0.85)

        fig.tight_layout()
        # Replay user annotations on the primary axis.
        if fig.axes:
            self.annotation_ctl.draw(fig.axes[0])
        self.canvas.draw()

        # Summary label below the canvas
        if any_data:
            self._update_summary(derived, use_initial)
        else:
            self.summary_label.setText("")

    # ------------------- Pb
    def _plot_pb(self, df: pd.DataFrame, *, y_iso: str) -> None:
        x_col = self.pb206_combo.currentData()
        y_col = (self.pb207_combo.currentData() if y_iso == "207"
                 else self.pb208_combo.currentData())
        fig = self.canvas.figure
        fig.clear()
        if not x_col or not y_col:
            self._empty(
                f"Pick the ²⁰⁶Pb/²⁰⁴Pb and ²⁰{y_iso[-1]}Pb/²⁰⁴Pb "
                f"columns in the controls panel."
            )
            return
        ax = fig.add_subplot(111)

        # Data
        any_data = False
        for label, sub, gs in get_groups(df, self.plot_style):
            if gs is not None and not getattr(gs, "visible", True):
                continue
            xs = pd.to_numeric(sub[x_col], errors="coerce")
            ys = pd.to_numeric(sub[y_col], errors="coerce")
            mask = xs.notna() & ys.notna()
            xs, ys = xs[mask], ys[mask]
            if xs.empty:
                continue
            ax.scatter(xs, ys,
                       s=(self.plot_style.point_size ** 2),
                       alpha=self.plot_style.alpha,
                       c=gs.color if gs else "#1f77b4",
                       marker=gs.marker if gs else "o",
                       label=label, edgecolors="black",
                       linewidths=0.5, zorder=5)
            any_data = True

        # NHRL on 208/204 only
        if y_iso == "208" and self.nhrl_chk.isChecked():
            slope, intercept = NHRL_208_206
            x_lo, x_hi = ax.get_xlim() if any_data else (17.0, 21.0)
            # If no data yet, use a sensible default range
            xs = np.linspace(x_lo, x_hi, 50)
            ax.plot(xs, slope * xs + intercept,
                    color="#444", linewidth=1.4, linestyle="--",
                    alpha=0.9, label="NHRL (Hart 1984)", zorder=2)

        # Axes
        sup = {"207": "²⁰⁷Pb/²⁰⁴Pb", "208": "²⁰⁸Pb/²⁰⁴Pb"}[y_iso]
        ax.set_xlabel("²⁰⁶Pb/²⁰⁴Pb", fontsize=12)
        ax.set_ylabel(sup, fontsize=12)
        ax.grid(True, which="major", linestyle=":", linewidth=0.5,
                color="#aaa", alpha=0.7)

        if self.legend_chk.isChecked():
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc="best", fontsize=9,
                          framealpha=0.85)
        fig.tight_layout()
        # Replay user annotations on the primary axis.
        if fig.axes:
            self.annotation_ctl.draw(fig.axes[0])
        self.canvas.draw()
        self.summary_label.setText("")

    # ------------------------------------------------------------ epsilon UI
    def compute_initials_dialog(self) -> None:
        """Compute initials & ε on the full dataframe, attach them as new
        columns and show a summary dialog."""
        df = self._active_df()
        if df is None or df.empty:
            QMessageBox.information(self, "No data",
                                    "Load a dataset before computing.")
            return
        derived = self._initials_and_eps(df)
        new_cols = []
        if derived["sr_i"] is not None:
            df["(87Sr/86Sr)i"] = derived["sr_i"]
            new_cols.append("(87Sr/86Sr)i")
        if derived["nd_i"] is not None:
            df["(143Nd/144Nd)i"] = derived["nd_i"]
            new_cols.append("(143Nd/144Nd)i")
        if derived["eps_sr_i"] is not None:
            df["εSr_i"] = derived["eps_sr_i"]
            new_cols.append("εSr_i")
        if derived["eps_nd_i"] is not None:
            df["εNd_i"] = derived["eps_nd_i"]
            new_cols.append("εNd_i")
        if derived["eps_sr_now"] is not None:
            df["εSr_now"] = derived["eps_sr_now"]
            new_cols.append("εSr_now")
        if derived["eps_nd_now"] is not None:
            df["εNd_now"] = derived["eps_nd_now"]
            new_cols.append("εNd_now")

        if not new_cols:
            QMessageBox.warning(
                self, "Nothing computed",
                "B.I.R.D.S could not find the columns needed to compute "
                "the initial ratios. Check that the Sr-Nd columns and the "
                "parent ratios (87Rb/86Sr & 147Sm/144Nd — or Rb / Sr / "
                "Sm / Nd concentrations) are present."
            )
            return

        msg = "Added columns to the dataset:\n  • " + "\n  • ".join(new_cols)
        msg += "\n\nSummary (mean over all samples):\n"
        for c in new_cols:
            v = pd.to_numeric(df[c], errors="coerce").mean()
            msg += f"  {c:18s} = {v:.6g}\n"
        QMessageBox.information(self, "Initial ratios & epsilon", msg)
        self.update_plot()

    def _update_summary(self, derived: dict, use_initial: bool) -> None:
        parts = []
        if derived["eps_sr_now"] is not None:
            v = derived["eps_sr_now"].mean()
            parts.append(f"εSr (now) mean = {v:+.2f}")
        if derived["eps_nd_now"] is not None:
            v = derived["eps_nd_now"].mean()
            parts.append(f"εNd (now) mean = {v:+.2f}")
        if use_initial:
            if derived["eps_sr_i"] is not None:
                parts.append(f"εSr (i) mean = {derived['eps_sr_i'].mean():+.2f}")
            if derived["eps_nd_i"] is not None:
                parts.append(f"εNd (i) mean = {derived['eps_nd_i'].mean():+.2f}")
        self.summary_label.setText("   ·   ".join(parts) if parts else "")

    # ------------------------------------------------------------ utilities
    def _empty(self, message: str) -> None:
        fig = self.canvas.figure
        fig.clear()
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, message, ha="center", va="center",
                color="#6c7388", fontsize=11, wrap=True,
                transform=ax.transAxes)
        ax.axis("off")
        self.canvas.draw()
        self.summary_label.setText("")

    def export_plot(self) -> None:
        from ._export_helpers import ask_export_path, save_figure
        path = ask_export_path(self, suggested_name="isotopes.pdf")
        if path is None:
            return
        save_figure(self, self.canvas.figure, path)

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def serialize(self) -> dict:
        from .. import widget_state as ws
        return {
            "diagram_key": self.diagram_combo.currentData() or "",
            "sr": self.sr_combo.currentText(),
            "nd": self.nd_combo.currentText(),
            "age_correction": ws.check_state(self.age_box),
            "age_source": self.age_source.currentData() or "single",
            "age_value": ws.spin_state(self.age_value),
            "age_column": self.age_column.currentText(),
            "parent_sr": self.parent_sr_combo.currentText(),
            "parent_nd": self.parent_nd_combo.currentText(),
            "pb206": self.pb206_combo.currentText(),
            "pb207": self.pb207_combo.currentText(),
            "pb208": self.pb208_combo.currentText(),
            "reservoirs": {name: cb.isChecked()
                           for name, cb in self.res_checks.items()},
            "mantle_array": ws.check_state(self.mantle_array_chk),
            "nhrl": ws.check_state(self.nhrl_chk),
            "eps_axes": ws.check_state(self.eps_axes_chk),
            "legend": ws.check_state(self.legend_chk),
            "annotations": self.annotation_ctl.serialize(),
        }

    def restore(self, state: dict) -> None:
        from .. import widget_state as ws
        if not state:
            return
        # Diagram first — it triggers _on_diagram_changed and reveals
        # the right input boxes (Sr-Nd / Pb).
        key = state.get("diagram_key", "")
        if key:
            idx = self.diagram_combo.findData(key)
            if idx >= 0:
                self.diagram_combo.setCurrentIndex(idx)
        for combo, key_name in [
            (self.sr_combo, "sr"), (self.nd_combo, "nd"),
            (self.age_column, "age_column"),
            (self.parent_sr_combo, "parent_sr"),
            (self.parent_nd_combo, "parent_nd"),
            (self.pb206_combo, "pb206"), (self.pb207_combo, "pb207"),
            (self.pb208_combo, "pb208"),
        ]:
            ws.restore_combo(combo, {"text": state.get(key_name, "")})
        ws.restore_check(self.age_box, state.get("age_correction"))
        src = state.get("age_source")
        if src:
            i = self.age_source.findData(src)
            if i >= 0:
                self.age_source.setCurrentIndex(i)
        ws.restore_spin(self.age_value, state.get("age_value"))
        for name, cb in self.res_checks.items():
            val = state.get("reservoirs", {}).get(name)
            if val is not None:
                cb.setChecked(bool(val))
        ws.restore_check(self.mantle_array_chk, state.get("mantle_array"))
        ws.restore_check(self.nhrl_chk, state.get("nhrl"))
        ws.restore_check(self.eps_axes_chk, state.get("eps_axes"))
        ws.restore_check(self.legend_chk, state.get("legend"))
        self.annotation_ctl.restore(state.get("annotations"))
