"""Isotope diagrams view — Sr-Nd and Pb isotope systems.

Two sections are bundled into a single widget:

* **Sr-Nd**: ⁸⁷Sr/⁸⁶Sr  vs  ¹⁴³Nd/¹⁴⁴Nd, optional age correction to
  initial ratios, optional εNd / εSr secondary axes, six mantle
  end-member fields (DM, PREMA, HIMU, BSE, EMI, EMII), the mantle-array
  lines and the CHUR / BSE rules.  The fields and lines are measured
  from the published figure — see :mod:`birds.isotope_fields`.

  εSr is referred to the bulk silicate Earth of Zindler & Hart (1986),
  0.7051 -- the vertical rule the figure draws -- so εSr = 0 falls on
  it.  εNd is referred to CHUR (Jacobsen & Wasserburg 1980).  Initial
  ε values are taken against the reservoir as it was at the sample's
  age, not as it is today.
* **Pb**: ²⁰⁶Pb/²⁰⁴Pb  vs  ²⁰⁷Pb/²⁰⁴Pb and  ²⁰⁶Pb/²⁰⁴Pb  vs
  ²⁰⁸Pb/²⁰⁴Pb, carrying the Northern Hemisphere Reference Line
  (NHRL; Hart 1984) and nothing else.  Hart publishes it for both
  planes, so it is offered on both.

References
----------
- Zindler, A. & Hart, S.R. (1986). Chemical geodynamics. *Annu. Rev. Earth Planet. Sci.* 14, 493-571.
- Hart, S.R. (1984). A large-scale isotope anomaly in the Southern Hemisphere mantle. *Nature* 309, 753-757.
- Hofmann, A.W. (2003). Sampling mantle heterogeneity through oceanic basalts. *Treatise on Geochemistry* 2, 61-101.
- DePaolo, D.J. & Wasserburg, G.J. (1976). Nd isotopic variations and petrogenetic models. *GRL* 3, 249-252.
- Jacobsen, S.B. & Wasserburg, G.J. (1980). Sm-Nd isotopic evolution of chondrites. *EPSL* 50, 139-155.
- Papanastassiou, D.A. & Wasserburg, G.J. (1969). Initial strontium isotopic abundances and the resolution of small time differences in the formation of planetary objects. *EPSL* 5, 361-376.
- Steiger, R.H. & Jäger, E. (1977). Subcommission on geochronology: convention on the use of decay constants. *EPSL* 36, 359-362.
"""

from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

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
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..plot_style import legend_columns
from ..diagrams.templates.base import get_groups, resolve_column
from ..isotope_fields import (
    BSE_SR_87_86,
    CHUR_ND_143_144,
    CHUR_SM_147_144,
    MANTLE_ARRAY,
    MANTLE_ARRAY_LABEL,
    SR_ND_FIELDS,
    SR_ND_WINDOW,
    nhrl,
    pb_window,
    resolve_field,
)
from .annotation_controller import AnnotationController, nearest_sample
from .plot_canvas import PlotCanvas
from .deferral import defer_while_hidden


# ---------------------------------------------------------------------------
# Geochemical constants
# ---------------------------------------------------------------------------

# Decay constants (Steiger & Jäger 1977)
LAMBDA_RB = 1.42e-11    # /yr  - 87Rb -> 87Sr
LAMBDA_SM = 6.54e-12    # /yr  - 147Sm -> 143Nd

# Reference reservoirs for ε, today.  One definition each, in
# isotope_fields, shared with the lines the Sr-Nd figure draws.
SR_UR_87_86 = BSE_SR_87_86          # Zindler & Hart (1986) BSE
ND_CHUR     = CHUR_ND_143_144       # Jacobsen & Wasserburg (1980)
SM_ND_CHUR  = CHUR_SM_147_144

# Basaltic achondrite best initial ⁸⁷Sr/⁸⁶Sr (Papanastassiou & Wasserburg
# 1969) and the age of the Earth it is taken at.
BABI_SR_87_86 = 0.69899
AGE_EARTH_YR  = 4.55e9

# ⁸⁷Rb/⁸⁶Sr of the Sr reference reservoir: the ratio that carries it from
# BABI at 4.55 Ga to 0.7051 today as a closed system.  The same
# construction gives 0.0826 for the older 0.7045 -- the 0.0827 that
# reservoir is quoted with -- so the pair stays consistent; it is ≈0.0916.
RB_SR_UR = ((SR_UR_87_86 - BABI_SR_87_86)
            / (np.exp(LAMBDA_RB * AGE_EARTH_YR) - 1.0))

# Approximate elemental → parent-isotope-ratio conversions used when the
# user only provides Rb / Sr / Sm / Nd concentrations (ppm).
RB_SR_TO_87_86 = 2.894    # 87Rb/86Sr ≈ this × (Rb/Sr)
SM_ND_TO_147_144 = 0.6043 # 147Sm/144Nd ≈ this × (Sm/Nd)

# The mantle end-members are compositional ranges, so they are drawn as the
# published fields rather than as single points.  Their outlines, the two
# array lines and the CHUR / BSE reference lines are in isotope_fields,
# measured from the source figure.



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

#: Million years per unit of the template's Age_Unit column.
_MA_PER_UNIT = {"ma": 1.0, "myr": 1.0, "my": 1.0, "ka": 1e-3, "kyr": 1e-3,
                "ga": 1e3, "gyr": 1e3, "yr": 1e-6, "y": 1e-6, "a": 1e-6}


# ---------------------------------------------------------------------------
# Calculations
# ---------------------------------------------------------------------------

def ages_in_ma(df: pd.DataFrame, col: str) -> pd.Series:
    """The ages in *col* in Ma, whatever unit each row gives.

    The template pairs ``Age`` with ``Age_Unit`` (Ma, ka, Ga or yr), on
    the Data sheet and the Isotopes sheet alike; read as Ma, an age of
    450 ka became 450 Ma.  A column whose name says Ma (``Age_Ma``) or a
    row with no unit is taken as Ma; an unknown unit gives no age.
    """
    ages = pd.to_numeric(df[col], errors="coerce")
    unit_col = next((c for c in df.columns
                     if str(c).strip().lower() in ("age_unit", "age unit")),
                    None)
    if unit_col is None or "ma" in str(col).lower().replace("age", ""):
        return ages
    units = df[unit_col].astype("string").str.strip().str.lower()
    factor = units.map(_MA_PER_UNIT).astype("float64")
    factor = factor.where(units.notna() & (units != ""), 1.0)
    return ages * factor

def compute_initial_ratio(measured: pd.Series, parent: pd.Series,
                          age_Ma: pd.Series, lam: float) -> pd.Series:
    """Apply the age correction:  R_i = R_m - P × (e^{λ t} - 1)."""
    t = age_Ma * 1.0e6   # Ma → yr
    return measured - parent * (np.exp(lam * t) - 1.0)


def epsilon_nd(nd_ratio, age_Ma=0.0):
    """εNd against CHUR as it was *age_Ma* ago (today, by default).

    An initial ratio has to be compared with CHUR at the same time:
    against today's CHUR, a rock 1 Ga old that evolved exactly as CHUR
    would read about −25 εNd instead of 0.
    """
    chur = compute_initial_ratio(ND_CHUR, SM_ND_CHUR, age_Ma, LAMBDA_SM)
    return (nd_ratio / chur - 1.0) * 1.0e4


def _widen(window: Tuple[float, float], values, pad: float
           ) -> Tuple[float, float]:
    """*window*, extended to hold *values* with a margin when they escape.

    The published window is the default view; it only grows, so the
    reference fields keep the same place on screen whatever the dataset.
    """
    lo, hi = window
    if not len(values):
        return lo, hi
    return min(lo, min(values) - pad), max(hi, max(values) + pad)


def _around(values, fallback: Tuple[float, float], min_pad: float
            ) -> Tuple[float, float]:
    """A range holding *values* with a margin, or *fallback* if empty.

    The margin is a tenth of the spread, never less than *min_pad*, so
    a tight cluster still gets room around it instead of sitting on the
    frame.
    """
    if not len(values):
        return fallback
    lo, hi = min(values), max(values)
    pad = max((hi - lo) * 0.10, min_pad)
    return lo - pad, hi + pad


def epsilon_sr(sr_ratio, age_Ma=0.0):
    """εSr against the Sr reference reservoir as it was *age_Ma* ago."""
    ur = compute_initial_ratio(SR_UR_87_86, RB_SR_UR, age_Ma, LAMBDA_RB)
    return (sr_ratio / ur - 1.0) * 1.0e4


# ---------------------------------------------------------------------------
# Helper: parent ratio either from a dedicated column or from concentrations
# ---------------------------------------------------------------------------

def _parent_from_pair(df: pd.DataFrame, pairs, factor: float
                      ) -> Optional[pd.Series]:
    """factor x daughter-element ratio, row by row from the first pair
    whose value is there: the isotope aliquot's concentrations
    (``Sm_iso`` / ``Nd_iso``, as the template names them) before the
    bulk ones, which may come from another aliquot."""
    out = None
    for num_names, den_names in pairs:
        num = resolve_column(df, num_names)
        den = resolve_column(df, den_names)
        if num is None or den is None:
            continue
        ratio = factor * (pd.to_numeric(df[num], errors="coerce")
                          / pd.to_numeric(df[den], errors="coerce"))
        out = ratio if out is None else out.fillna(ratio)
    return out


def _resolve_parent_rb_sr(df: pd.DataFrame) -> Optional[pd.Series]:
    col = resolve_column(df, _RB_SR_PARENT)
    pair = _parent_from_pair(df, ((("Rb_iso",), ("Sr_iso",)),
                                  (("Rb",), ("Sr",))), RB_SR_TO_87_86)
    if col is None:
        return pair
    given = pd.to_numeric(df[col], errors="coerce")
    return given if pair is None else given.fillna(pair)


def _resolve_parent_sm_nd(df: pd.DataFrame) -> Optional[pd.Series]:
    col = resolve_column(df, _SM_ND_PARENT)
    pair = _parent_from_pair(df, ((("Sm_iso",), ("Nd_iso",)),
                                  (("Sm",), ("Nd",))), SM_ND_TO_147_144)
    if col is None:
        return pair
    given = pd.to_numeric(df[col], errors="coerce")
    return given if pair is None else given.fillna(pair)


# ---------------------------------------------------------------------------
# IsotopesView widget
# ---------------------------------------------------------------------------

DIAGRAMS = (
    ("Sr-Nd:  ⁸⁷Sr/⁸⁶Sr  vs  ¹⁴³Nd/¹⁴⁴Nd",     "sr_nd"),
    ("Pb:      ²⁰⁶Pb/²⁰⁴Pb  vs  ²⁰⁷Pb/²⁰⁴Pb",   "pb_207"),
    ("Pb:      ²⁰⁶Pb/²⁰⁴Pb  vs  ²⁰⁸Pb/²⁰⁴Pb",   "pb_208"),
    ("vs SiO₂:  an isotope ratio or ε against silica", "vs_sio2"),
)

#: An isotope column worth offering against SiO2: a ratio such as
#: 87Sr/86Sr or 176Hf/177Hf, or a delta / epsilon / gamma value -- never
#: its 2-sigma uncertainty.
_ISOTOPE_COLUMN = re.compile(
    r"^(\d{1,3}[A-Z][a-z]?\s*/\s*\d{1,3}[A-Z][a-z]?|[δεγ].+)$")

#: Quantities computed from the Sr-Nd inputs, offered against SiO2:
#: key -> (label at present, label at the age, reference value).
_SIO2_DERIVED = {
    "derived:eps_nd": ("εNd", "εNd(t)", 0.0),
    "derived:eps_sr": ("εSr", "εSr(t)", 0.0),
    "derived:sr_i": (None, "(⁸⁷Sr/⁸⁶Sr)ᵢ", None),
    "derived:nd_i": (None, "(¹⁴³Nd/¹⁴⁴Nd)ᵢ", None),
}


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

        # ---- vs SiO2 controls ---------------------------------------------
        self.sio2_box = QGroupBox("Against SiO₂")
        sio2_v = _wrap(self.sio2_box)
        sio2_f = _compact_form()
        self.sio2_y_combo = QComboBox()
        self.sio2_y_combo.setToolTip(
            "Any isotope ratio or δ / ε / γ column of the sheet, plus εNd "
            "and εSr from the Sr-Nd inputs; with the age correction on, "
            "the initial ratios and ε at the age too.")
        self.sio2_y_combo.currentIndexChanged.connect(
            lambda _i: self.update_plot())
        sio2_f.addRow("Vertical axis:", self.sio2_y_combo)
        sio2_v.addLayout(sio2_f)
        self.sio2_ref_chk = QCheckBox(
            "Reference value (BSE ⁸⁷Sr/⁸⁶Sr, CHUR ¹⁴³Nd/¹⁴⁴Nd, ε = 0)")
        self.sio2_ref_chk.setChecked(True)
        self.sio2_ref_chk.toggled.connect(lambda _on: self.update_plot())
        sio2_v.addWidget(self.sio2_ref_chk)
        sio2_note = QLabel(
            "<i>SiO₂ is read from the Isotopes sheet; where it is blank "
            "or absent, from the Data sheet by Sample_Name.</i>")
        sio2_note.setStyleSheet("color: #6c7388; font-size: 11px;")
        sio2_note.setTextFormat(Qt.TextFormat.RichText)
        sio2_note.setWordWrap(True)
        sio2_v.addWidget(sio2_note)
        layout.addWidget(self.sio2_box)

        # ---- Reservoirs ---------------------------------------------------
        self.res_box = QGroupBox("Mantle reservoirs")
        rv = _wrap(self.res_box)
        self.res_checks: Dict[str, QCheckBox] = {}
        for fld in SR_ND_FIELDS:
            cb = QCheckBox(f"{fld.name} — {fld.long_name}")
            cb.setChecked(True)
            rv.addWidget(cb)
            self.res_checks[fld.name] = cb
        layout.addWidget(self.res_box)


        # ---- Reference lines ----------------------------------------------
        self.ref_box = QGroupBox("Reference lines")
        rrv = _wrap(self.ref_box)
        self.mantle_array_chk = QCheckBox("Mantle array (Sr-Nd)")
        self.mantle_array_chk.setChecked(True)
        rrv.addWidget(self.mantle_array_chk)
        self.nhrl_chk = QCheckBox(
            "NHRL — Northern Hemisphere Reference Line (Hart 1984)")
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
        is_sio2 = key == "vs_sio2"
        is_pb = not (is_snd or is_sio2)
        # Against SiO2, ε and initial ratios come from the Sr-Nd inputs
        # and the age correction, so those stay on show.
        self.snd_box.setVisible(is_snd or is_sio2)
        self.age_box.setVisible(is_snd or is_sio2)
        self.pb_box.setVisible(is_pb)
        self.sio2_box.setVisible(is_sio2)
        self.mantle_array_chk.setVisible(is_snd)
        self.eps_axes_chk.setVisible(is_snd)
        self.res_box.setVisible(is_snd)
        # Hart publishes the NHRL for both Pb planes, so it is offered
        # on both; the old code drew it only on ²⁰⁸Pb.
        self.nhrl_chk.setVisible(is_pb)

        if key == "vs_sio2":
            self.title_label.setText("Isotope ratio  vs  SiO₂")
            self.subtitle_label.setText(
                "An isotope ratio, δ value or ε against silica, to read "
                "isotopic change with differentiation — a rise of "
                "⁸⁷Sr/⁸⁶Sr or fall of εNd with SiO₂ points to crustal "
                "assimilation (AFC), a flat trend to closed-system "
                "fractional crystallisation. Turn on the age correction "
                "for initial ratios and ε at the age."
            )
        elif key == "sr_nd":
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
        self._populate_sio2_choices(df)

    def _populate_sio2_choices(self, df) -> None:
        """Fill the vertical-axis list of the SiO2 diagram, keeping the
        current choice when it is still on offer."""
        keep = self.sio2_y_combo.currentData()
        self.sio2_y_combo.blockSignals(True)
        self.sio2_y_combo.clear()
        if df is not None and not df.empty:
            for col in df.columns:
                name = str(col).strip()
                if _ISOTOPE_COLUMN.match(name) and "2σ" not in name \
                        and "2s" not in name.lower():
                    self.sio2_y_combo.addItem(name, col)
            for key, (label, label_t, _ref) in _SIO2_DERIVED.items():
                self.sio2_y_combo.addItem(
                    f"{label or label_t} (from the Sr-Nd inputs)", key)
        i = self.sio2_y_combo.findData(keep) if keep is not None else -1
        if i < 0:
            sr = resolve_column(df, _SR_RATIO_ALIASES) if df is not None \
                else None
            i = self.sio2_y_combo.findData(sr) if sr is not None else 0
        self.sio2_y_combo.setCurrentIndex(max(i, 0))
        self.sio2_y_combo.blockSignals(False)

    # ------------------------------------------------------------------ data
    def _silica(self, df: pd.DataFrame) -> Optional[pd.Series]:
        """SiO2 for every row of *df*: the sheet's own where given, else
        the Data sheet's for the same Sample_Name, so an Isotopes sheet
        without the column still plots."""
        own = resolve_column(df, ["SiO2"])
        sio2 = (pd.to_numeric(df[own], errors="coerce") if own
                else pd.Series(np.nan, index=df.index, dtype="float64"))
        main = getattr(self.data, "df", None)
        if (sio2.isna().any() and main is not None and main is not df
                and "Sample_Name" in df.columns
                and "Sample_Name" in main.columns):
            main_col = resolve_column(main, ["SiO2"])
            if main_col:
                lookup = (pd.to_numeric(main[main_col], errors="coerce")
                          .groupby(main["Sample_Name"].astype(str)).first())
                sio2 = sio2.fillna(
                    df["Sample_Name"].astype(str).map(lookup))
        return None if sio2.isna().all() else sio2

    def _sio2_y(self, df: pd.DataFrame):
        """``(values, axis label, reference value or None)`` for the
        vertical axis of the SiO2 diagram; ``values`` is None when the
        choice cannot be computed."""
        key = self.sio2_y_combo.currentData()
        if key is None:
            return None, "", None
        if isinstance(key, str) and key in _SIO2_DERIVED:
            label, label_t, ref = _SIO2_DERIVED[key]
            derived = self._initials_and_eps(df)
            at_age = self.age_box.isChecked()
            name = key.split(":", 1)[1]
            if name in ("eps_nd", "eps_sr"):
                values = derived.get(f"{name}_i") if at_age else None
                if values is None:
                    values, label_t = derived.get(f"{name}_now"), label
            else:
                values = derived.get(name)
            return values, label_t, ref
        if key not in df.columns:
            return None, str(key), None
        name = str(key)
        refs = {"87sr/86sr": SR_UR_87_86, "143nd/144nd": ND_CHUR}
        ref = refs.get(name.replace(" ", "").lower())
        if name.startswith(("ε", "γ")):
            ref = 0.0
        return pd.to_numeric(df[key], errors="coerce"), name, ref

    def _measured_sr_nd(self) -> Tuple[Optional[str], Optional[str]]:
        return self.sr_combo.currentData(), self.nd_combo.currentData()

    def _age_series(self, df: pd.DataFrame) -> Optional[pd.Series]:
        if self.age_source.currentData() == "single":
            return pd.Series(self.age_value.value(),
                             index=df.index, dtype="float64")
        col = self.age_column.currentData()
        if col is None or col not in df.columns:
            return None
        return ages_in_ma(df, col)

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
            out["eps_sr_i"] = epsilon_sr(sr_i, age)
        if parent_nd is not None:
            nd_i = compute_initial_ratio(
                pd.to_numeric(df[nd_col], errors="coerce"),
                parent_nd, age, LAMBDA_SM)
            out["nd_i"] = nd_i
            out["eps_nd_i"] = epsilon_nd(nd_i, age)
        return out

    # ------------------------------------------------------------------ plot
    def update_plot(self) -> None:
        if defer_while_hidden(self):
            return      # drawn when its page is shown
        # Annotations belong to the diagram they were drawn on.
        self.annotation_ctl.set_context(self.diagram_combo.currentData())
        df = self._active_df()
        if df is None or df.empty:
            self._empty("Load a dataset (Data → Import) to plot isotope diagrams.")
            return
        key = self.diagram_combo.currentData()
        if key == "sr_nd":
            self._plot_sr_nd(df)
        elif key == "vs_sio2":
            self._plot_vs_sio2(df)
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
        if key == "vs_sio2":
            ys, _label, _ref = self._sio2_y(df)
            xs = self._silica(df)
            if xs is None or ys is None:
                return None, None
            return xs, pd.Series(ys, index=df.index)
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

        self._draw_sr_nd_background(ax)

        # Axes
        ax.set_xlabel("⁸⁷Sr/⁸⁶Sr" + ("  (initial)" if use_initial else ""),
                      fontsize=12)
        ax.set_ylabel("¹⁴³Nd/¹⁴⁴Nd" + ("  (initial)" if use_initial else ""),
                      fontsize=12)
        ax.grid(True, which="major", linestyle=":", linewidth=0.5,
                color="#aaa", alpha=0.7)

        # Start from the published window and widen it only for data that
        # falls outside: a sample clipped off the plot would still be
        # counted as plotted, and the reference fields would shift about
        # from one dataset to the next.
        xs_data: list = []
        ys_data: list = []
        if any_data:
            if use_initial:
                xs_data = derived["sr_i"].dropna().tolist()
                ys_data = derived["nd_i"].dropna().tolist()
            else:
                xs_data = pd.to_numeric(df[sr_col],
                                        errors="coerce").dropna().tolist()
                ys_data = pd.to_numeric(df[nd_col],
                                        errors="coerce").dropna().tolist()
        ax.set_xlim(*_widen(SR_ND_WINDOW[0], xs_data, 0.0004))
        ax.set_ylim(*_widen(SR_ND_WINDOW[1], ys_data, 0.00004))

        # Secondary axes — εSr (top) and εNd (right).  Initial ratios
        # read against the reservoirs at the samples' age; with one age
        # per sample there is no single such axis, so none is drawn.
        if self.eps_axes_chk.isChecked():
            age = 0.0
            single = self.age_source.currentData() == "single"
            if use_initial and single:
                age = self.age_value.value()
            if use_initial and not single:
                ax.text(0.99, 1.01, "ε axes need a single age",
                        transform=ax.transAxes, ha="right", va="bottom",
                        fontsize=8, color="#6c7388")
            else:
                ur = float(compute_initial_ratio(
                    SR_UR_87_86, RB_SR_UR, age, LAMBDA_RB))
                chur = float(compute_initial_ratio(
                    ND_CHUR, SM_ND_CHUR, age, LAMBDA_SM))
                when = f"  (t = {age:g} Ma)" if use_initial else ""
                ax_top = ax.secondary_xaxis(
                    "top",
                    functions=(
                        lambda x, _r=ur: (x / _r - 1.0) * 1.0e4,
                        lambda eps, _r=ur: _r * (1.0 + eps / 1.0e4),
                    ),
                )
                ax_top.set_xlabel("εSr" + when, fontsize=11)
                ax_right = ax.secondary_yaxis(
                    "right",
                    functions=(
                        lambda y, _c=chur: (y / _c - 1.0) * 1.0e4,
                        lambda eps, _c=chur: _c * (1.0 + eps / 1.0e4),
                    ),
                )
                ax_right.set_ylabel("εNd" + when, fontsize=11)

        # Legend
        if self.legend_chk.isChecked():
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc="best", fontsize=8,
                          framealpha=0.85,
                          ncol=legend_columns(len(handles)))

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

    def _draw_sr_nd_background(self, ax) -> None:
        """Reference fields, the array band and the two marker lines.

        Everything here sits below the samples: the point of the plot is
        the data, and a filled field drawn over it would hide points.
        """
        # Fields first, as plain white outlines.  The source fills and
        # hatches them, which is legible on paper but turns busy once a
        # dataset is drawn on top, so only the boundary is kept.
        for fld in SR_ND_FIELDS:
            cb = self.res_checks.get(fld.name)
            if cb is not None and not cb.isChecked():
                continue
            if fld.is_drawn:
                # No legend entry: the field carries its name on the plot,
                # and the legend belongs to the user's own groups.
                ax.fill(
                    [v[0] for v in fld.vertices],
                    [v[1] for v in fld.vertices],
                    facecolor="white", edgecolor="#333", linewidth=0.8,
                    zorder=2,
                )

        # The rules go over the fields: a white field would otherwise
        # break the line it is meant to sit on.
        ax.axhline(ND_CHUR, color="#888", linewidth=0.8, zorder=3)
        ax.axvline(BSE_SR_87_86, color="#888", linewidth=0.8, zorder=3)

        if self.mantle_array_chk.isChecked():
            for (x0, y0), (x1, y1) in MANTLE_ARRAY:
                ax.plot([x0, x1], [y0, y1], color="#555", linewidth=1.0,
                        zorder=3)
            lx, ly = MANTLE_ARRAY_LABEL
            ax.text(lx, ly, "Mantle array", fontsize=8.5, style="italic",
                    color="#333", ha="center", va="center",
                    rotation=self._array_angle(ax), rotation_mode="anchor",
                    zorder=4,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.8, pad=1.0))

        for fld in SR_ND_FIELDS:
            cb = self.res_checks.get(fld.name)
            if cb is not None and not cb.isChecked():
                continue
            ax.text(fld.label[0], fld.label[1], fld.name, fontsize=8.5,
                    fontweight="bold", color="#222", ha="center",
                    va="center", zorder=4,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.8, pad=0.4))

    @staticmethod
    def _array_angle(ax) -> float:
        """Screen angle of the array band, so the label lies along it."""
        (x0, y0), (x1, y1) = MANTLE_ARRAY[0]
        (ax0, ax1), (ay0, ay1) = ax.get_xlim(), ax.get_ylim()
        if ax1 == ax0 or ay1 == ay0:
            return 0.0
        bbox = ax.get_window_extent()
        dx = (x1 - x0) / (ax1 - ax0) * max(bbox.width, 1.0)
        dy = (y1 - y0) / (ay1 - ay0) * max(bbox.height, 1.0)
        return float(np.degrees(np.arctan2(dy, dx)))

    def _draw_pb_background(self, ax, y_iso: str) -> None:
        """The NHRL, drawn right across whatever the axes now show."""
        if not self.nhrl_chk.isChecked():
            return
        xs = np.linspace(*ax.get_xlim(), 100)
        ax.plot(xs, nhrl(xs, y_iso), color="#b3261e", linewidth=1.2,
                zorder=2, label="NHRL (Hart 1984)")

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

        # Pb ratios span a narrow range, and nothing fixed is drawn here
        # but the NHRL, so the axes follow the data.  The published frame
        # is only the fallback for an empty panel.
        wx, wy = pb_window(y_iso)
        if any_data:
            xs_data = pd.to_numeric(df[x_col],
                                    errors="coerce").dropna().tolist()
            ys_data = pd.to_numeric(df[y_col],
                                    errors="coerce").dropna().tolist()
            x_lo, x_hi = _around(xs_data, wx, 0.05)
            ax.set_xlim(x_lo, x_hi)
            # Keep the NHRL on screen.  It is the only reference the
            # panel carries, and a suite that sits well off it would
            # otherwise push it out of view — losing exactly the
            # comparison the line is there to make.
            if self.nhrl_chk.isChecked():
                ys_data = ys_data + [nhrl(x_lo, y_iso), nhrl(x_hi, y_iso)]
            ax.set_ylim(*_around(ys_data, wy, 0.02))
        else:
            ax.set_xlim(*wx)
            ax.set_ylim(*wy)

        self._draw_pb_background(ax, y_iso)

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
                          framealpha=0.85,
                          ncol=legend_columns(len(handles)))
        fig.tight_layout()
        # Replay user annotations on the primary axis.
        if fig.axes:
            self.annotation_ctl.draw(fig.axes[0])
        self.canvas.draw()
        self.summary_label.setText("")

    # ------------------- vs SiO2
    def _plot_vs_sio2(self, df: pd.DataFrame) -> None:
        fig = self.canvas.figure
        fig.clear()
        sio2 = self._silica(df)
        values, label, ref = self._sio2_y(df)
        if sio2 is None:
            self._empty("No SiO₂ found: fill the SiO2 column of the "
                        "Isotopes sheet, or import a Data sheet with SiO2 "
                        "and matching Sample_Name values.")
            return
        if values is None:
            self._empty(f"“{label or 'This choice'}” cannot be computed "
                        "from the current inputs — pick the Sr-Nd columns "
                        "(and the parents and age for initial values).")
            return
        ys_all = pd.Series(values, index=df.index)
        ax = fig.add_subplot(111)
        plotted = 0
        for group, sub, gs in get_groups(df, self.plot_style):
            if gs is not None and not getattr(gs, "visible", True):
                continue
            xs, ys = sio2.loc[sub.index], ys_all.loc[sub.index]
            keep = xs.notna() & ys.notna()
            if not keep.any():
                continue
            ax.scatter(xs[keep], ys[keep], s=self.plot_style.point_size ** 2,
                       alpha=self.plot_style.alpha,
                       c=gs.color if gs else "#1f77b4",
                       marker=gs.marker if gs else "o", label=group,
                       edgecolors="black", linewidths=0.5, zorder=5)
            plotted += int(keep.sum())
        if ref is not None and self.sio2_ref_chk.isChecked():
            names = {SR_UR_87_86: "BSE", ND_CHUR: "CHUR"}
            ax.axhline(ref, color="#888", linewidth=0.9, linestyle="--",
                       zorder=1)
            ax.annotate(f"{names.get(ref, label.split('(')[0])} "
                        f"= {ref:g}", (0.995, ref),
                        xycoords=("axes fraction", "data"), ha="right",
                        va="bottom", fontsize=8, color="#666")
        ax.set_xlabel("SiO₂ (wt.%)", fontsize=12)
        ax.set_ylabel(label, fontsize=12)
        ax.grid(True, which="major", linestyle=":", linewidth=0.5,
                color="#aaa", alpha=0.7)
        if self.legend_chk.isChecked():
            handles, labels = ax.get_legend_handles_labels()
            if handles:
                ax.legend(handles, labels, loc="best", fontsize=9,
                          framealpha=0.85,
                          ncol=legend_columns(len(handles)))
        fig.tight_layout()
        if fig.axes:
            self.annotation_ctl.draw(fig.axes[0])
        self.canvas.draw()
        self.summary_label.setText(
            f"{plotted} of {len(df)} samples have both SiO₂ and {label}.")

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
            "sio2_y": self.sio2_y_combo.currentText(),
            "sio2_reference": ws.check_state(self.sio2_ref_chk),
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
            (self.pb208_combo, "pb208"), (self.sio2_y_combo, "sio2_y"),
        ]:
            ws.restore_combo(combo, {"text": state.get(key_name, "")})
        ws.restore_check(self.age_box, state.get("age_correction"))
        src = state.get("age_source")
        if src:
            i = self.age_source.findData(src)
            if i >= 0:
                self.age_source.setCurrentIndex(i)
        ws.restore_spin(self.age_value, state.get("age_value"))
        saved = state.get("reservoirs", {}) or {}
        # A session written before the fields were renamed to match the
        # figure (EM1/EM2 → EMI/EMII) still carries the old keys.
        for key, val in saved.items():
            fld = resolve_field(key)
            cb = self.res_checks.get(fld.name) if fld else None
            if cb is not None and val is not None:
                cb.setChecked(bool(val))
        ws.restore_check(self.mantle_array_chk, state.get("mantle_array"))
        ws.restore_check(self.nhrl_chk, state.get("nhrl"))
        ws.restore_check(self.eps_axes_chk, state.get("eps_axes"))
        ws.restore_check(self.legend_chk, state.get("legend"))
        ws.restore_check(self.sio2_ref_chk, state.get("sio2_reference"))
        self.annotation_ctl.restore(state.get("annotations"),
                                    legacy_context=self.diagram_combo.currentData())
