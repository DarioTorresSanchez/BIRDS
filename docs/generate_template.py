"""Generate the B.I.R.D.S data-entry template in both XLSX and CSV.

Single source of truth for the column layout, units and notes. Run::

    python3 docs/generate_template.py

to (re)create:

    templates/BIRDS_data_template.xlsx          - workbook (5 sheets)
    templates/BIRDS_data_template.csv           - main flat file (majors + traces + REE)
    templates/BIRDS_isotopes_template.csv       - companion flat file (isotopes only)
    templates/BIRDS_petrography_template.csv    - companion flat file (modal mineralogy)

The XLSX workbook ships five sheets:

    1. ``Data``         - the empty bulk-analysis table.
    2. ``Isotopes``     - empty isotope table (Sr-Nd-Pb-Hf-Os-Re-O-C-H).
                          Linked to the Data sheet via ``Sample_Name``.
    3. ``Petrography``  - modal mineralogy (Q-A-P-F, Ol-Opx-Cpx, tuff
                          Crystal-Vitric-Lithic, textures). Linked to
                          the Data sheet via ``Sample_Name``.
    4. ``Reference``    - one row per column with description, unit and
                          examples; doubles as a glossary for all
                          sheets.
    5. ``Instructions`` - one-page overview of how to use the template
                          and how it maps to B.I.R.D.S modules.

Because CSV files are single-sheet by definition, the isotopes and
petrography blocks go into separate companion CSVs that the user can
keep alongside the main file. All three share the same ``Sample_Name``
key so the rows can be joined.

Dropdown-validated columns: Rock_Type, Magmatic_Series, Alteration,
Analytical_Method, Age_Unit, TAS_Composition  (Data sheet),
Iso_Method (Isotopes sheet), Texture / Pyroclast_size /
Microscope_method (Petrography sheet).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from openpyxl import Workbook
from openpyxl.styles import (
    Alignment, Border, Font, PatternFill, Side,
)
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT_DIR = ROOT / "templates"


# ---------------------------------------------------------------------------
# Column specification (single source of truth)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Column:
    name: str           # exact header that goes into the file
    category: str       # group it belongs to (also used for header colouring)
    unit: str           # "", "wt%", "ppm", "°", "Ma", ...
    description: str
    example: str = ""
    options: Sequence[str] = ()       # allowed dropdown values (XLSX only)


# Header palette per category (subtle, publication-friendly)
CATEGORY_FILL = {
    "ID":         "FCE7CB",   # peach
    "Location":   "E1F0DE",   # light green
    "Source":     "EFEFEF",   # neutral grey
    "Geology":    "D9E7F2",   # light blue
    "Analysis":   "F2D7E2",   # rose
    "Majors":     "FFF2CC",   # soft yellow
    "Traces":     "DDEBF7",   # cooler blue
    "REE":        "E2EFDA",   # mint
    # Isotope categories — each radiogenic / stable system gets its own tint
    "Iso-ID":     "FCE7CB",   # peach (same as ID; doubles as the join key)
    "Iso-Sr":     "FBE0DC",   # warm pink
    "Iso-Nd":     "F4D7A8",   # soft amber
    "Iso-Pb":     "E0D9F0",   # lavender
    "Iso-Hf":     "DCEFE2",   # pale teal
    "Iso-Os":     "E8DACB",   # warm beige
    "Iso-Stable": "FFEFC2",   # cream (O, C, H, B)
    "Iso-Meta":   "F4F6FA",   # off-white
    # Petrography categories — modal mineralogy + textures
    "Petro-ID":     "FCE7CB",   # peach (shared with ID — join key)
    "Petro-QAPF":   "F4D7E2",   # rose (Q, A, P, F modal %)
    "Petro-Mafic":  "DCEFE2",   # pale teal (Ol, Opx, Cpx, Amph, Bt, Ms, Px)
    "Petro-Acc":    "E8DACB",   # warm beige (apatite, zircon, opaques, …)
    "Petro-Tuff":   "FFEFC2",   # cream (Crystal/Vitric/Lithic)
    "Petro-Texture": "D9E7F2",  # light blue (grain size, microscope)
    "Petro-Meta":   "F4F6FA",   # off-white (analyst, date, notes)
    "Other":      "F4F6FA",   # off-white
}


# --- Dropdown vocabularies --------------------------------------------------

ROCK_TYPES = ("Volcanic", "Plutonic", "Sub-volcanic", "Pyroclastic", "Vein")
MAGMATIC_SERIES = (
    "Tholeiitic", "Calc-alkaline", "High-K calc-alkaline",
    "Shoshonitic", "Alkaline", "Ultra-alkaline", "Boninitic",
)
ALTERATION = (
    "Fresh", "Slightly altered", "Moderately altered",
    "Strongly altered", "Metamorphosed",
)
ANALYTICAL_METHODS = (
    "XRF", "ICP-OES", "ICP-MS", "Solution ICP-MS", "LA-ICP-MS",
    "EMP / EPMA", "INAA", "Wet chemistry", "Mixed",
)
AGE_UNITS = ("Ma", "ka", "Ga", "yr")

# Isotope analytical techniques
ISO_METHODS = (
    "TIMS", "MC-ICP-MS", "Solution MC-ICP-MS", "LA-MC-ICP-MS",
    "SIMS", "SHRIMP", "N-TIMS (Os)", "Laser fluorination (δ¹⁸O)",
    "EA-IRMS (δ¹³C, δD)", "CRDS", "Mixed",
)

# Petrographic dropdown vocabularies
ROCK_TEXTURES = (
    "Phaneritic", "Aphanitic", "Porphyritic", "Glassy",
    "Vesicular", "Pyroclastic", "Cumulate", "Cataclastic",
    "Foliated / Gneissic", "Mixed",
)
PYROCLAST_SIZES = (
    "Ash (< 2 mm)", "Lapilli (2-64 mm)", "Block / Bomb (> 64 mm)",
    "Mixed",
)
MICROSCOPE_METHODS = (
    "Point-count (≥ 300 points)", "Point-count (100-300 points)",
    "Visual estimate", "Modal calculation (CIPW)",
    "Image analysis (software)", "SEM-EDS / EBSD", "Mixed",
)
TAS_COMPOSITIONS = (
    "Picro-basalt", "Basalt", "Basaltic andesite", "Andesite",
    "Dacite", "Rhyolite",
    "Trachy-basalt", "Basaltic trachy-andesite", "Trachy-andesite",
    "Trachyte", "Trachy-dacite",
    "Tephrite", "Phono-tephrite", "Tephri-phonolite", "Phonolite",
    "Foidite",
    # Plutonic equivalents
    "Gabbro", "Diorite", "Granodiorite", "Granite",
    "Monzogabbro", "Monzodiorite", "Monzonite", "Syenite",
    "Foid-syenite", "Foidolite",
)


# --- The column list ---------------------------------------------------------

def _major_columns() -> List[Column]:
    """Major-oxide columns (wt %). Order follows the conventional CIPW input."""
    parts = [
        ("SiO2",  "silicon dioxide"),
        ("TiO2",  "titanium dioxide"),
        ("Al2O3", "aluminium oxide"),
        ("Fe2O3", "ferric iron"),
        ("FeO",   "ferrous iron"),
        ("FeOt",  "total iron as FeO (used by Verma DFs)"),
        ("MnO",   "manganese oxide"),
        ("MgO",   "magnesium oxide"),
        ("CaO",   "calcium oxide"),
        ("Na2O",  "sodium oxide"),
        ("K2O",   "potassium oxide"),
        ("P2O5",  "phosphorus pentoxide"),
        ("Cr2O3", "chromium oxide"),
        ("NiO",   "nickel oxide"),
        ("LOI",   "loss on ignition (heating at 1000 °C)"),
        ("H2O+",  "structural water (above 110 °C)"),
        ("H2O-",  "absorbed water (below 110 °C)"),
        ("CO2",   "carbon dioxide"),
        ("Total", "sum of oxides (quality-control, target 99-101 wt%)"),
    ]
    return [Column(p, "Majors", "wt%", desc, example="")
            for p, desc in parts]


TRACE_ELEMENTS = (
    "Li", "Be", "Sc", "V", "Cr", "Co", "Ni", "Cu", "Zn", "Ga", "Rb",
    "Sr", "Y", "Zr", "Nb", "Mo", "Sn", "Sb", "Cs", "Ba", "Hf", "Ta",
    "W", "Tl", "Pb", "Bi", "Th", "U",
)

REE = (
    "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb",
    "Dy", "Ho", "Er", "Tm", "Yb", "Lu",
)


def build_columns() -> List[Column]:
    cols: List[Column] = []

    # 1) Identification
    cols += [
        Column("No.", "ID", "",
               "Sequential row number (1, 2, 3 ...).", "1"),
        Column("Sample_Name", "ID", "",
               "Unique short identifier for the sample (lab code / "
               "field number). Avoid spaces.", "VOL-2024-018"),
        Column("Sample_Label", "ID", "",
               "Free-text label used in plots if you don't want to "
               "expose the lab code.", "Mt. Pico flow 18"),
        Column("Group", "ID", "",
               "Optional user-defined group used by the legend "
               "(e.g. unit, eruption, age cluster).", "Lower flow"),
    ]

    # 2) Location
    cols += [
        Column("Latitude", "Location", "°",
               "Decimal degrees (WGS-84). Negative = south.",
               "-19.4250"),
        Column("Longitude", "Location", "°",
               "Decimal degrees (WGS-84). Negative = west.",
               "-69.1583"),
        Column("Elevation", "Location", "m",
               "Sampling elevation above sea level.", "4250"),
        Column("Country", "Location", "",
               "Country where the sample was collected.", "Chile"),
        Column("Region", "Location", "",
               "State / province / volcanic field.",
               "Arica y Parinacota"),
        Column("Locality", "Location", "",
               "Specific outcrop or feature.",
               "Taapaca Volcanic Complex"),
    ]

    # 3) Source
    cols += [
        Column("Reference", "Source", "",
               "Bibliographic reference for the analysis "
               "(author year, or DOI).",
               "Aguirre et al. (2022) Lithos 408"),
        Column("Dataset_DOI", "Source", "",
               "DOI of the original dataset, if published "
               "separately.", "10.5281/zenodo.1234567"),
    ]

    # 4) Geological context
    cols += [
        Column("Age", "Geology", "",
               "Numeric age (matched with AGE_UNIT). Leave empty if "
               "unknown.", "0.45"),
        Column("Age_Unit", "Geology", "",
               "Unit of the AGE column. Pick from the dropdown.",
               "Ma", options=AGE_UNITS),
        Column("Age_Method", "Geology", "",
               "Dating method (K-Ar, Ar-Ar, U-Pb, fission track, "
               "stratigraphic).", "Ar-Ar"),
        Column("Rock_Type", "Geology", "",
               "Volcanic vs. plutonic family — used by B.I.R.D.S to "
               "pick the right TAS panel and tectonic catalogue.",
               "Volcanic", options=ROCK_TYPES),
        Column("TAS_Composition", "Geology", "",
               "Rock name from the TAS diagram (Le Bas et al. 1986). "
               "Leave empty to let B.I.R.D.S compute it from SiO2 / "
               "alkalis.", "Basaltic andesite",
               options=TAS_COMPOSITIONS),
        Column("Lithology", "Geology", "",
               "Petrographic name beyond TAS (e.g. olivine basalt, "
               "biotite-amphibole granodiorite).",
               "Olivine basalt"),
        Column("Magmatic_Series", "Geology", "",
               "Magma series. Optional — also derivable from K2O-SiO2 "
               "and AFM diagrams.", "Calc-alkaline",
               options=MAGMATIC_SERIES),
        Column("Tectonic_Setting", "Geology", "",
               "Inferred tectonic environment "
               "(MORB, OIB, IAB, CRB, OP, ...).",
               "Continental arc"),
        Column("Texture", "Geology", "",
               "Porphyritic / aphanitic / glassy / phaneritic / "
               "vesicular / etc.", "Porphyritic"),
        Column("Mineral_Assemblage", "Geology", "",
               "Main minerals (plagioclase, olivine, clinopyroxene, "
               "amphibole, biotite, K-feldspar, quartz ...).",
               "Pl + Cpx + Ol ± Opx"),
        Column("Alteration", "Geology", "",
               "Visual / petrographic alteration grade.", "Fresh",
               options=ALTERATION),
    ]

    # 5) Analysis metadata
    cols += [
        Column("Analytical_Method", "Analysis", "",
               "Technique used for the bulk analysis.", "XRF + ICP-MS",
               options=ANALYTICAL_METHODS),
        Column("Laboratory", "Analysis", "",
               "Lab where the analysis was carried out.",
               "ALS Geochemistry (Vancouver)"),
        Column("Analysis_Date", "Analysis", "",
               "Year / date of the analysis (YYYY or YYYY-MM-DD).",
               "2023-04"),
        Column("Analyst", "Analysis", "",
               "Analyst initials or name (optional).", "JLF"),
        Column("Notes", "Analysis", "",
               "Free-text notes (anomalies, dilutions, repeated "
               "analyses, etc.).", ""),
    ]

    # 6) Majors
    cols += _major_columns()

    # 7) Trace elements
    cols += [Column(el, "Traces", "ppm",
                    f"Trace element {el} concentration.")
             for el in TRACE_ELEMENTS]

    # 8) Rare-earth elements
    cols += [Column(el, "REE", "ppm",
                    f"Rare-earth element {el} concentration.")
             for el in REE]

    return cols


# ---------------------------------------------------------------------------
# Isotope columns (separate sheet / separate CSV)
# ---------------------------------------------------------------------------

def build_isotope_columns() -> List[Column]:
    """Column spec for the Isotopes sheet.

    Covers the four standard radiogenic systems (Sr, Nd, Pb, Hf), the
    Os-Re system frequently used for mantle/mafic rocks, and the most
    common stable isotopes (O, C, H, B). Each isotope ratio has a 2σ
    column for the analytical uncertainty.
    """
    cols: List[Column] = []

    # ---- Link to the main Data sheet ----------------------------------
    cols += [
        Column("Sample_Name", "Iso-ID", "",
               "Must exactly match the Sample_Name in the Data sheet — "
               "this is how B.I.R.D.S joins the isotopic analysis back "
               "to the bulk composition.",
               "VOL-2024-018"),
        Column("Sample_Label", "Iso-ID", "",
               "Optional friendly label used in plots.  Leave blank to "
               "inherit the value from the Data sheet (B.I.R.D.S fills "
               "this column automatically at import time).",
               "Mt. Pico flow 18"),
        Column("Group", "Iso-ID", "",
               "Optional group for colouring / legend.  Like "
               "Sample_Label, B.I.R.D.S inherits this from the Data "
               "sheet at import time so you only need to set it once.",
               "Lower flow"),
        Column("Age", "Iso-ID", "Ma",
               "Crystallisation / eruption age used for the initial-"
               "ratio correction. Leave empty to plot only present-day "
               "ratios.", "0.45"),
        Column("Age_Method", "Iso-ID", "",
               "Method used to obtain the age (K-Ar, Ar-Ar, U-Pb, "
               "stratigraphic …).", "Ar-Ar"),
    ]

    # ---- Sr ------------------------------------------------------------
    cols += [
        Column("87Sr/86Sr", "Iso-Sr", "",
               "Measured ⁸⁷Sr/⁸⁶Sr ratio. Typical values: 0.7022 (DM), "
               "0.7045 (CHUR), 0.708-0.710 (arc/upper crust).",
               "0.70428"),
        Column("87Sr/86Sr_2σ", "Iso-Sr", "",
               "Analytical 2σ uncertainty of ⁸⁷Sr/⁸⁶Sr "
               "(absolute, e.g. 0.000010).", "0.00001"),
        Column("87Rb/86Sr", "Iso-Sr", "",
               "Parent ratio used for the initial-Sr correction. If "
               "missing, B.I.R.D.S derives it from Rb / Sr "
               "concentrations (~2.894 × Rb/Sr).", "0.045"),
        Column("Sr_iso", "Iso-Sr", "ppm",
               "Sr concentration measured on the same aliquot as the "
               "isotope ratio (optional; only needed if it differs from "
               "the bulk value in the Data sheet).", "385"),
        Column("Rb_iso", "Iso-Sr", "ppm",
               "Rb concentration measured on the same aliquot.", "11"),
        Column("εSr_initial", "Iso-Sr", "",
               "Computed by B.I.R.D.S — leave empty.", ""),
    ]

    # ---- Nd ------------------------------------------------------------
    cols += [
        Column("143Nd/144Nd", "Iso-Nd", "",
               "Measured ¹⁴³Nd/¹⁴⁴Nd ratio. CHUR = 0.512638 (Bouvier "
               "et al. 2008).", "0.51285"),
        Column("143Nd/144Nd_2σ", "Iso-Nd", "",
               "Analytical 2σ uncertainty.", "0.000007"),
        Column("147Sm/144Nd", "Iso-Nd", "",
               "Parent ratio for the initial-Nd correction. If missing, "
               "derived from Sm/Nd (~0.6043 × Sm/Nd).", "0.19"),
        Column("Sm_iso", "Iso-Nd", "ppm",
               "Sm concentration in the isotope aliquot.", "4.85"),
        Column("Nd_iso", "Iso-Nd", "ppm",
               "Nd concentration in the isotope aliquot.", "20.1"),
        Column("εNd_initial", "Iso-Nd", "",
               "Computed by B.I.R.D.S.", ""),
        Column("TDM_Nd", "Iso-Nd", "Ma",
               "Nd depleted-mantle model age (DePaolo 1981 or "
               "Goldstein 1984 — pick your convention).", "1250"),
    ]

    # ---- Pb ------------------------------------------------------------
    cols += [
        Column("206Pb/204Pb", "Iso-Pb", "",
               "Measured ²⁰⁶Pb/²⁰⁴Pb ratio.", "18.65"),
        Column("206Pb/204Pb_2σ", "Iso-Pb", "",
               "Analytical 2σ uncertainty.", "0.01"),
        Column("207Pb/204Pb", "Iso-Pb", "",
               "Measured ²⁰⁷Pb/²⁰⁴Pb ratio.", "15.55"),
        Column("207Pb/204Pb_2σ", "Iso-Pb", "",
               "Analytical 2σ uncertainty.", "0.01"),
        Column("208Pb/204Pb", "Iso-Pb", "",
               "Measured ²⁰⁸Pb/²⁰⁴Pb ratio.", "38.45"),
        Column("208Pb/204Pb_2σ", "Iso-Pb", "",
               "Analytical 2σ uncertainty.", "0.02"),
        Column("Pb_iso", "Iso-Pb", "ppm",
               "Pb concentration in the isotope aliquot.", "6.2"),
        Column("U_iso", "Iso-Pb", "ppm",
               "U concentration (for μ = ²³⁸U/²⁰⁴Pb).", "1.1"),
        Column("Th_iso", "Iso-Pb", "ppm",
               "Th concentration (for κ = ²³²Th/²³⁸U).", "3.6"),
    ]

    # ---- Hf ------------------------------------------------------------
    cols += [
        Column("176Hf/177Hf", "Iso-Hf", "",
               "Measured ¹⁷⁶Hf/¹⁷⁷Hf ratio. CHUR = 0.282785 (Bouvier "
               "et al. 2008).", "0.28298"),
        Column("176Hf/177Hf_2σ", "Iso-Hf", "",
               "Analytical 2σ uncertainty.", "0.000005"),
        Column("176Lu/177Hf", "Iso-Hf", "",
               "Parent ratio for initial-Hf correction.", "0.018"),
        Column("Hf_iso", "Iso-Hf", "ppm",
               "Hf concentration in the isotope aliquot.", "3.85"),
        Column("Lu_iso", "Iso-Hf", "ppm",
               "Lu concentration in the isotope aliquot.", "0.42"),
        Column("εHf_initial", "Iso-Hf", "",
               "Computed by B.I.R.D.S.", ""),
        Column("TDM_Hf", "Iso-Hf", "Ma",
               "Hf depleted-mantle model age.", "1100"),
    ]

    # ---- Os-Re --------------------------------------------------------
    cols += [
        Column("187Os/188Os", "Iso-Os", "",
               "Measured ¹⁸⁷Os/¹⁸⁸Os ratio. Primitive Upper Mantle "
               "(PUM) ≈ 0.1296.", "0.131"),
        Column("187Os/188Os_2σ", "Iso-Os", "",
               "Analytical 2σ uncertainty.", "0.001"),
        Column("187Re/188Os", "Iso-Os", "",
               "Parent ratio for the initial-Os correction.", "0.43"),
        Column("Os_iso", "Iso-Os", "ppb",
               "Os concentration (parts per billion).", "0.45"),
        Column("Re_iso", "Iso-Os", "ppb",
               "Re concentration.", "0.18"),
        Column("γOs_initial", "Iso-Os", "",
               "Computed by B.I.R.D.S.", ""),
    ]

    # ---- Stable isotopes ----------------------------------------------
    cols += [
        Column("δ18O", "Iso-Stable", "‰ VSMOW",
               "Oxygen isotope composition relative to VSMOW. Mantle "
               "olivine ≈ +5.2 ‰; crustal sediments commonly >+10 ‰.",
               "+5.8"),
        Column("δ18O_2σ", "Iso-Stable", "‰",
               "Analytical 2σ uncertainty.", "0.1"),
        Column("δD", "Iso-Stable", "‰ VSMOW",
               "Hydrogen isotope composition relative to VSMOW. Useful "
               "for hydrous phases (amphibole, biotite, melt "
               "inclusions).", "-65"),
        Column("δD_2σ", "Iso-Stable", "‰",
               "Analytical 2σ uncertainty.", "2"),
        Column("δ13C", "Iso-Stable", "‰ VPDB",
               "Carbon isotope composition relative to VPDB. Mantle "
               "CO₂ ≈ -5 ‰; biogenic carbon strongly negative.",
               "-6.2"),
        Column("δ13C_2σ", "Iso-Stable", "‰",
               "Analytical 2σ uncertainty.", "0.1"),
        Column("δ11B", "Iso-Stable", "‰",
               "Boron isotope composition. Slab fluids / sediments "
               "show very contrasted signatures.", "+3.5"),
    ]

    # ---- Iso analysis metadata ----------------------------------------
    cols += [
        Column("Iso_Method", "Iso-Meta", "",
               "Mass-spectrometry technique used for the isotope "
               "ratio(s).", "MC-ICP-MS", options=ISO_METHODS),
        Column("Iso_Laboratory", "Iso-Meta", "",
               "Lab where the isotope analysis was carried out.",
               "MIT Radiogenic Isotope Lab"),
        Column("Iso_Date", "Iso-Meta", "",
               "Year or full date of the isotope analysis.", "2024-03"),
        Column("Iso_Analyst", "Iso-Meta", "",
               "Analyst initials or name.", "MLG"),
        Column("Iso_Notes", "Iso-Meta", "",
               "Free-text notes (column chemistry, spike, repeated "
               "measurements, blanks).", ""),
    ]

    return cols


# ---------------------------------------------------------------------------
# Petrography columns (modal mineralogy — separate sheet)
# ---------------------------------------------------------------------------

def build_petrography_columns() -> List[Column]:
    """Column spec for the Petrography sheet.

    Modal-mineralogy percentages feed the five IUGS ternaries in the
    Petrography view: Streckeisen QAPF (plutonic / volcanic), gabbro
    Pl-Px-Ol, ultramafic Ol-Opx-Cpx and pyroclastic tuff
    Crystal-Vitric-Lithic. All modal columns are in volume %.
    """
    cols: List[Column] = []

    # ---- Link to the main Data sheet ----------------------------------
    cols += [
        Column("Sample_Name", "Petro-ID", "",
               "Must exactly match the Sample_Name in the Data sheet — "
               "this is the key B.I.R.D.S uses to join the modal "
               "mineralogy back to the bulk composition.",
               "VOL-2024-018"),
        Column("Sample_Label", "Petro-ID", "",
               "Optional friendly label used in plots.  Leave blank to "
               "inherit the value from the Data sheet — B.I.R.D.S fills "
               "this column automatically at import time.",
               "Mt. Pico flow 18"),
        Column("Group", "Petro-ID", "",
               "Optional group used for colouring / legend.  Inherited "
               "from the Data sheet at import time if left blank.",
               "Lower flow"),
        Column("Texture", "Petro-ID", "",
               "Overall rock fabric. Pick from the dropdown.",
               "Porphyritic", options=ROCK_TEXTURES),
    ]

    # ---- QAPF (Streckeisen) -------------------------------------------
    cols += [
        Column("Q_mode", "Petro-QAPF", "vol %",
               "Modal Quartz (Q apex of the Streckeisen QAPF "
               "diagram).", "28"),
        Column("A_mode", "Petro-QAPF", "vol %",
               "Modal Alkali feldspar (K-feldspar + albite component); "
               "A apex of QAPF.", "32"),
        Column("P_mode", "Petro-QAPF", "vol %",
               "Modal Plagioclase (calcic / sodic plagioclase); "
               "P apex of QAPF.", "35"),
        Column("F_mode", "Petro-QAPF", "vol %",
               "Modal Feldspathoid (nepheline, leucite, sodalite …); "
               "F apex of the bottom QAPF triangle. Mutually exclusive "
               "with Q (one rock can't have both).", "0"),
    ]

    # ---- Mafic minerals ------------------------------------------------
    cols += [
        Column("Ol_mode", "Petro-Mafic", "vol %",
               "Modal Olivine. Ol apex of the gabbro Pl-Px-Ol "
               "ternary and of the ultramafic Ol-Opx-Cpx ternary.",
               "5"),
        Column("Opx_mode", "Petro-Mafic", "vol %",
               "Modal Orthopyroxene (enstatite to ferrosilite). "
               "Opx apex of the ultramafic ternary.", "12"),
        Column("Cpx_mode", "Petro-Mafic", "vol %",
               "Modal Clinopyroxene (diopside, augite, pigeonite …). "
               "Cpx apex of the ultramafic ternary.", "8"),
        Column("Px_mode", "Petro-Mafic", "vol %",
               "Total pyroxene (Opx + Cpx) used by the gabbro Pl-Px-Ol "
               "ternary. Leave empty — B.I.R.D.S sums Opx + Cpx "
               "automatically if you fill those.", ""),
        Column("Amph_mode", "Petro-Mafic", "vol %",
               "Modal Amphibole (hornblende, actinolite, kaersutite …). "
               "Not used by QAPF but reported for completeness.",
               "3"),
        Column("Bt_mode", "Petro-Mafic", "vol %",
               "Modal Biotite.", "6"),
        Column("Ms_mode", "Petro-Mafic", "vol %",
               "Modal Muscovite.", "1"),
    ]

    # ---- Accessory phases ---------------------------------------------
    cols += [
        Column("Opaque_mode", "Petro-Acc", "vol %",
               "Modal Fe-Ti oxides (magnetite, ilmenite, hematite, "
               "chromite).", "1.5"),
        Column("Apatite_mode", "Petro-Acc", "vol %",
               "Modal Apatite.", "0.3"),
        Column("Zircon_mode", "Petro-Acc", "vol %",
               "Modal Zircon.", "0.1"),
        Column("Titanite_mode", "Petro-Acc", "vol %",
               "Modal Titanite / sphene.", "0.2"),
        Column("Carbonate_mode", "Petro-Acc", "vol %",
               "Modal Calcite, dolomite, ankerite (esp. in alteration / "
               "carbonatites).", "0"),
        Column("Other_acc_mode", "Petro-Acc", "vol %",
               "Modal other accessories (epidote, chlorite, sericite, "
               "garnet, tourmaline, monazite, …).", "0.5"),
        Column("Mode_Total", "Petro-Acc", "vol %",
               "Quality-control sum of every modal column above. Should "
               "fall between 99 and 101 vol %.", ""),
    ]

    # ---- Pyroclastic / tuff components --------------------------------
    cols += [
        Column("Crystal_pct", "Petro-Tuff", "vol %",
               "Crystal fragments — Crystal apex of the IUGS tuff "
               "ternary (Schmid 1981).", "30"),
        Column("Vitric_pct", "Petro-Tuff", "vol %",
               "Glass shards / pumice fragments — Vitric apex.", "55"),
        Column("Lithic_pct", "Petro-Tuff", "vol %",
               "Lithic / rock fragments — Lithic apex.", "15"),
        Column("Pyroclast_size", "Petro-Tuff", "",
               "Granulometric class. Pick from the dropdown.",
               "Lapilli (2-64 mm)", options=PYROCLAST_SIZES),
    ]

    # ---- Texture & grain-size metadata --------------------------------
    cols += [
        Column("Grain_size_mm", "Petro-Texture", "mm",
               "Average grain size (groundmass for porphyritic rocks).",
               "0.5"),
        Column("Phenocryst_pct", "Petro-Texture", "vol %",
               "Total phenocryst content (porphyritic rocks).", "12"),
        Column("Vesicle_pct", "Petro-Texture", "vol %",
               "Vesicle / vug content.", "5"),
        Column("Alteration_pct", "Petro-Texture", "vol %",
               "Secondary minerals / alteration overprint (sericite, "
               "chlorite, clay …).", "8"),
        Column("Texture_notes", "Petro-Texture", "",
               "Free-text observations (zoning, reaction rims, "
               "embayments, cumulate textures, mineral assemblage).",
               "Plg zoned; Cpx with sieve texture"),
    ]

    # ---- Analysis metadata --------------------------------------------
    cols += [
        Column("Microscope_method", "Petro-Meta", "",
               "How the modal proportions were obtained.",
               "Point-count (≥ 300 points)",
               options=MICROSCOPE_METHODS),
        Column("Microscope_lab", "Petro-Meta", "",
               "Lab / university where the thin section was studied.",
               "UNAM — Petrology lab"),
        Column("Petrography_date", "Petro-Meta", "",
               "Year / date of the petrographic analysis (YYYY or "
               "YYYY-MM-DD).", "2024-04"),
        Column("Petrographer", "Petro-Meta", "",
               "Analyst initials or name.", "MDC"),
        Column("Petrography_notes", "Petro-Meta", "",
               "Free-text notes (sample preservation, mounting, "
               "staining for K-feldspar, etc.).", ""),
    ]

    return cols


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

def write_csv(columns: List[Column], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow([c.name for c in columns])
        # Add 5 empty rows so the user just has to start typing
        for _ in range(5):
            writer.writerow([""] * len(columns))


# ---------------------------------------------------------------------------
# XLSX writer
# ---------------------------------------------------------------------------

_THIN = Side(border_style="thin", color="B7B7B7")
_BORDER = Border(left=_THIN, right=_THIN, top=_THIN, bottom=_THIN)


def _style_header(cell, fill_hex: str) -> None:
    cell.font = Font(name="Calibri", size=10, bold=True, color="1C2237")
    cell.fill = PatternFill("solid", fgColor=fill_hex)
    cell.alignment = Alignment(horizontal="center", vertical="center",
                               wrap_text=True)
    cell.border = _BORDER


def _style_unit(cell, fill_hex: str) -> None:
    cell.font = Font(name="Calibri", size=9, italic=True, color="5B6478")
    cell.fill = PatternFill("solid", fgColor=fill_hex)
    cell.alignment = Alignment(horizontal="center", vertical="center")
    cell.border = _BORDER


def _build_table_sheet(ws: Worksheet, columns: List[Column], *,
                       title: str, freeze: str = "E3",
                       text_cats: set | None = None,
                       wide_columns: set | None = None) -> None:
    """Generic data-entry sheet: row 1 = column name, row 2 = unit, then
    200 empty rows with dropdowns applied to validated columns.
    """
    ws.title = title
    ws.freeze_panes = freeze
    ws.sheet_view.zoomScale = 100
    if text_cats is None:
        text_cats = {"ID", "Location", "Source", "Geology", "Analysis",
                     "Iso-ID", "Iso-Meta"}
    if wide_columns is None:
        wide_columns = {"Sample_Name", "Locality", "Reference",
                        "Lithology", "Mineral_Assemblage", "Notes",
                        "Iso_Notes", "Iso_Laboratory"}

    # Row 1: column name; Row 2: unit
    for c_idx, col in enumerate(columns, start=1):
        fill = CATEGORY_FILL.get(col.category, "EFEFEF")
        h = ws.cell(row=1, column=c_idx, value=col.name)
        _style_header(h, fill)
        u = ws.cell(row=2, column=c_idx, value=col.unit)
        _style_unit(u, fill)

    # Column widths (heuristic: longer for text columns, shorter for elements)
    for c_idx, col in enumerate(columns, start=1):
        letter = get_column_letter(c_idx)
        if col.category in text_cats:
            ws.column_dimensions[letter].width = max(14, len(col.name) + 4)
        else:
            ws.column_dimensions[letter].width = max(9, len(col.name) + 2)

    # Override for explicitly-wide columns
    for c_idx, col in enumerate(columns, start=1):
        if col.name in wide_columns:
            ws.column_dimensions[get_column_letter(c_idx)].width = 22

    ws.row_dimensions[1].height = 32
    ws.row_dimensions[2].height = 16

    # 200 empty data rows so dropdowns can be applied to a stable range
    for r in range(3, 203):
        ws.row_dimensions[r].height = 16

    # Dropdown validations
    for c_idx, col in enumerate(columns, start=1):
        if not col.options:
            continue
        rng = f"{get_column_letter(c_idx)}3:{get_column_letter(c_idx)}1002"
        # Excel allows up to 255 chars in inline lists -- our vocabs fit
        formula = '"' + ",".join(col.options) + '"'
        dv = DataValidation(type="list", formula1=formula, allow_blank=True,
                            showErrorMessage=True,
                            errorTitle="Invalid value",
                            error=("Pick one of: "
                                   + ", ".join(col.options)))
        ws.add_data_validation(dv)
        dv.add(rng)


def _build_data_sheet(ws: Worksheet, columns: List[Column]) -> None:
    _build_table_sheet(ws, columns, title="Data", freeze="E3")


def _build_isotopes_sheet(ws: Worksheet, columns: List[Column]) -> None:
    # Freeze first column (Sample_Name, the join key) + 2 header rows
    _build_table_sheet(ws, columns, title="Isotopes", freeze="B3")


def _build_petrography_sheet(ws: Worksheet, columns: List[Column]) -> None:
    # Same layout as the Isotopes sheet: freeze Sample_Name + headers
    _build_table_sheet(ws, columns, title="Petrography", freeze="B3")


def _build_reference_sheet(ws: Worksheet,
                            data_columns: List[Column],
                            iso_columns: List[Column],
                            petro_columns: List[Column]) -> None:
    """Combined glossary for the Data, Isotopes and Petrography sheets.

    Each row is annotated with the sheet it belongs to so the user can
    sort / filter by sheet from inside Excel.
    """
    ws.title = "Reference"
    headers = ("#", "Sheet", "Column", "Category", "Unit",
               "Allowed values", "Example", "Description")
    fills = ("F4F6FA",) * len(headers)
    for c_idx, (h, f) in enumerate(zip(headers, fills), start=1):
        cell = ws.cell(row=1, column=c_idx, value=h)
        _style_header(cell, f)
    widths = (5, 12, 22, 14, 8, 32, 22, 60)
    for c_idx, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(c_idx)].width = w
    ws.freeze_panes = "A2"
    ws.row_dimensions[1].height = 28

    all_rows = ([("Data", c) for c in data_columns]
                + [("Isotopes", c) for c in iso_columns]
                + [("Petrography", c) for c in petro_columns])

    for i, (sheet, col) in enumerate(all_rows, start=1):
        ws.cell(row=i + 1, column=1, value=i).alignment = Alignment(
            horizontal="center")
        sheet_cell = ws.cell(row=i + 1, column=2, value=sheet)
        sheet_cell.font = Font(name="Calibri", size=10, bold=True,
                               color="1C2237")
        sheet_cell.alignment = Alignment(horizontal="center")
        ws.cell(row=i + 1, column=3, value=col.name).font = Font(
            name="Consolas", size=10, bold=True)
        ws.cell(row=i + 1, column=4, value=col.category).fill = PatternFill(
            "solid", fgColor=CATEGORY_FILL.get(col.category, "EFEFEF"))
        ws.cell(row=i + 1, column=5, value=col.unit).alignment = Alignment(
            horizontal="center")
        ws.cell(row=i + 1, column=6,
                value=", ".join(col.options) if col.options else "")
        ws.cell(row=i + 1, column=7, value=col.example)
        desc = ws.cell(row=i + 1, column=8, value=col.description)
        desc.alignment = Alignment(wrap_text=True, vertical="top")


def _build_instructions_sheet(ws: Worksheet, columns: List[Column]) -> None:
    ws.title = "Instructions"
    ws.sheet_view.showGridLines = False
    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 110

    def W(row, text, *, bold=False, italic=False, size=11, colour=None):
        cell = ws.cell(row=row, column=2, value=text)
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cell.font = Font(name="Calibri", size=size, bold=bold, italic=italic,
                         color=colour or "1C2237")
        ws.row_dimensions[row].height = max(16, 6 + 1.4 * (len(text) // 90 + 1) * 9)

    r = 1
    W(r, "B.I.R.D.S — Data-entry template", bold=True, size=18, colour="0D1B3D"); r += 1
    W(r, "Broad Igneous Rocks — Diagrams & Statistics", italic=True, size=11,
      colour="5B6478"); r += 2
    W(r, "How to use this workbook", bold=True, size=13); r += 1
    W(r, "1. Go to the 'Data' sheet — every row is one sample. The first two "
         "rows are the header (column name + unit) and are frozen so they "
         "stay visible while you scroll. Do not change the header text — "
         "B.I.R.D.S relies on the exact names listed in the 'Reference' "
         "sheet."); r += 1
    W(r, "2. Fill in only the columns you have data for. Empty cells are "
         "treated as missing values; they will not break the plots and they "
         "will not be counted in the statistics."); r += 1
    W(r, "3. Decimal separator: use a dot (1.234). If your laboratory "
         "report uses a comma (1,234), B.I.R.D.S' robust importer will "
         "convert it automatically — but exporting from Excel with the dot "
         "decimal is the safest path."); r += 1
    W(r, "4. The columns highlighted with dropdown arrows in the 'Data' "
         "sheet (Rock_Type, Magmatic_Series, Alteration, Analytical_Method, "
         "Age_Unit, TAS_Composition) are validated — only the values in the "
         "list are accepted. This keeps the legend and group filters tidy."); r += 1
    W(r, "5. Once you have at least one sample and SiO2 + Na2O + K2O "
         "filled in, you can save the file as .xlsx or .csv and open it from "
         "B.I.R.D.S → Data → Import."); r += 2

    W(r, "Isotopes sheet (optional)", bold=True, size=13); r += 1
    W(r, "6. The 'Isotopes' sheet is independent of the 'Data' sheet. "
         "Use it to record Sr-Nd-Pb-Hf-Os-Re-O-C-H-B isotopic analyses. "
         "Rows are joined back to the bulk composition through the "
         "'Sample_Name' column, which MUST match exactly between the "
         "two sheets (case-sensitive)."); r += 1
    W(r, "7. Common workflow:  (a) fill in the bulk analysis in 'Data', "
         "(b) for the subset of samples with isotopic data, paste the "
         "ratios in 'Isotopes' next to the matching 'Sample_Name'. "
         "B.I.R.D.S' Isotopes view (menu Isotopes → Sr-Nd, Pb-Pb…) "
         "automatically picks up these columns."); r += 1
    W(r, "8. CSV users: the companion file 'BIRDS_isotopes_template.csv' "
         "carries the same isotope columns in a flat file. Keep it side-"
         "by-side with the main CSV and join them by 'Sample_Name' when "
         "needed."); r += 2

    W(r, "Petrography sheet (optional)", bold=True, size=13); r += 1
    W(r, "9. The 'Petrography' sheet captures modal mineralogy from "
         "thin sections: Q-A-P-F (Streckeisen QAPF), Ol-Opx-Cpx "
         "(ultramafic rocks), Pl-Px-Ol (gabbroic rocks) and "
         "Crystal-Vitric-Lithic (pyroclastic tuffs). Rows are joined "
         "to the bulk dataset by 'Sample_Name'."); r += 1
    W(r, "10. The Petrography view (menu Petrography → QAPF, Gabbro, "
         "Ultramafic, Tuff …) reads these modal % columns and plots "
         "the IUGS classification ternaries. Modal values are in "
         "volume %; the Mode_Total column is a QC sum that should "
         "fall between 99 and 101."); r += 1
    W(r, "11. CSV users: a companion file "
         "'BIRDS_petrography_template.csv' is generated next to the "
         "bulk and isotope CSVs."); r += 2

    W(r, "What goes into each column?", bold=True, size=13); r += 1
    W(r, "See the 'Reference' sheet for the full glossary — every column "
         "has its unit, allowed values and a short description there. "
         "The 'Sheet' column tells you whether the entry belongs to "
         "Data or Isotopes."); r += 2

    W(r, "Minimum data B.I.R.D.S needs by module", bold=True, size=13); r += 1
    needs = (
        ("Classification (TAS, K2O-SiO2, AFM, ...)",
         "SiO2, Na2O, K2O (+FeOt, MgO, Al2O3 for AFM / Jensen)"),
        ("Bivariate diagrams (Harker, custom x-y)",
         "Whatever pair of columns you want to compare"),
        ("Spider diagrams (REE / multi-element)",
         "At least the elements asked by the chosen normaliser "
         "(e.g. La-Lu for chondrite-normalised REE)"),
        ("Tectonic — Pearce 2008",
         "Th, Nb, Yb (+Ti for Ti/Yb-Nb/Yb)"),
        ("Tectonic — Verma & Verma 2013 (majors)",
         "SiO2, TiO2, Al2O3, FeOt, MnO, MgO, CaO, Na2O, K2O, P2O5"),
        ("Tectonic — Verma & Agrawal 2011 (traces)",
         "La, Sm, Nb, Th, Zr, Y, Hf, Ti and Yb"),
        ("Statistics & Anomalies",
         "Any numeric column. REE columns enable Eu/Eu*, Ce/Ce*, "
         "Pr/Pr*, Gd/Gd*, Y/Y*, Y/Ho automatically."),
        ("Isotopes — Sr-Nd plot (with εNd/εSr and initials)",
         "87Sr/86Sr, 143Nd/144Nd (+87Rb/86Sr, 147Sm/144Nd and Age "
         "to compute initial ratios)"),
        ("Isotopes — Pb-Pb diagrams",
         "206Pb/204Pb, 207Pb/204Pb and 208Pb/204Pb"),
        ("Map (sample locations)",
         "Latitude and Longitude (decimal degrees, WGS-84)"),
        ("Petrography — Streckeisen QAPF (plutonic & volcanic)",
         "Q_mode, A_mode, P_mode, F_mode (modal %)"),
        ("Petrography — Gabbroic rocks (Pl-Px-Ol)",
         "Pl_mode, Px_mode (or Opx+Cpx), Ol_mode"),
        ("Petrography — Ultramafic rocks (Ol-Opx-Cpx)",
         "Ol_mode, Opx_mode, Cpx_mode"),
        ("Petrography — Pyroclastic tuffs",
         "Crystal_pct, Vitric_pct, Lithic_pct"),
    )
    for title, cols_needed in needs:
        W(r, f"• {title} → {cols_needed}", size=10); r += 1
    r += 1

    W(r, "Tips", bold=True, size=13); r += 1
    W(r, "• Keep 'No.' as a sequential integer so it can be used as a "
         "sample ID when 'Sample_Name' is missing."); r += 1
    W(r, "• If you only have FeO + Fe2O3 (and not FeOt), B.I.R.D.S will "
         "compute FeOt = FeO + 0.8998 × Fe2O3 automatically."); r += 1
    W(r, "• 'TAS_Composition' can be left empty — the TAS diagram will "
         "compute it from your SiO2 and alkalis. Filling it in is useful "
         "only if you want to colour samples by lithology in other "
         "diagrams."); r += 1
    W(r, "• Latitude / Longitude in decimal degrees, WGS-84. Negative "
         "values are south / west."); r += 1
    W(r, "• Always keep a backup of your original lab report. This "
         "template is meant for plotting, not for archiving primary data."); r += 1


def write_xlsx(data_columns: List[Column], iso_columns: List[Column],
               petro_columns: List[Column], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()

    # ----- Sheet 1: Data --------------------------------------------------
    # Must stay at index 0 so ``pd.read_excel(path)`` (no sheet_name)
    # picks up the actual data when the user feeds the file to B.I.R.D.S.
    ws_data = wb.active
    _build_data_sheet(ws_data, data_columns)

    # ----- Sheet 2: Isotopes ----------------------------------------------
    ws_iso = wb.create_sheet("Isotopes")
    _build_isotopes_sheet(ws_iso, iso_columns)

    # ----- Sheet 3: Petrography -------------------------------------------
    ws_petro = wb.create_sheet("Petrography")
    _build_petrography_sheet(ws_petro, petro_columns)

    # ----- Sheet 4: Instructions ------------------------------------------
    ws_doc = wb.create_sheet("Instructions")
    _build_instructions_sheet(ws_doc, data_columns)

    # ----- Sheet 5: Reference (combined glossary) --------------------------
    ws_ref = wb.create_sheet("Reference")
    _build_reference_sheet(ws_ref, data_columns, iso_columns, petro_columns)

    # When the user opens the workbook in Excel, land them on the
    # Instructions sheet. The active-sheet pointer is purely cosmetic and
    # does not affect ``pd.read_excel`` (which always uses sheet index 0).
    wb.active = wb.sheetnames.index("Instructions")

    wb.save(out_path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    data_columns = build_columns()
    iso_columns = build_isotope_columns()
    petro_columns = build_petrography_columns()

    xlsx_path = OUT_DIR / "BIRDS_data_template.xlsx"
    csv_path  = OUT_DIR / "BIRDS_data_template.csv"
    iso_csv_path = OUT_DIR / "BIRDS_isotopes_template.csv"
    petro_csv_path = OUT_DIR / "BIRDS_petrography_template.csv"

    write_xlsx(data_columns, iso_columns, petro_columns, xlsx_path)
    write_csv(data_columns, csv_path)
    write_csv(iso_columns, iso_csv_path)
    write_csv(petro_columns, petro_csv_path)

    print(f"XLSX       : {xlsx_path}")
    print(f"             ({xlsx_path.stat().st_size} bytes, "
          f"Data: {len(data_columns)} cols, "
          f"Isotopes: {len(iso_columns)} cols, "
          f"Petrography: {len(petro_columns)} cols)")
    print(f"CSV bulk   : {csv_path}  ({csv_path.stat().st_size} bytes)")
    print(f"CSV iso    : {iso_csv_path}  ({iso_csv_path.stat().st_size} bytes)")
    print(f"CSV petro  : {petro_csv_path}  ({petro_csv_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
