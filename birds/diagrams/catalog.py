"""Catalogue of menu entries grouped by family and composition.

Each entry is a tuple ``(display label, key)``. Keys are stable identifiers
consumed by the view widgets to dispatch the plotting routine.

References (see README for full citations):
  * Rollinson & Pease (2021), chapters 3 & 5
  * Pearce (2008)
  * Verma & co-authors (2006-2017)
  * Yang et al. (2019)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Classification diagrams
# ---------------------------------------------------------------------------

CLASSIFICATION_VOLCANIC = [
    ("TAS - Le Bas et al. 1986 / Le Maitre 2002", "tas_volcanic"),
    ("K2O vs SiO2 - Peccerillo & Taylor 1976", "k2o_sio2"),
    ("Th vs Co (altered arc rocks) - Hastie et al. 2007", "hastie_2007_thco"),
    ("Zr/TiO2 vs Nb/Y (altered rocks) - Winchester & Floyd 1977", "winchester_floyd_1977"),
    ("Alkalic / Sub-alkalic boundary - Irvine & Baragar 1971", "ib1971"),
    ("AFM - Irvine & Baragar 1971 / Kuno 1968 / new (Rollinson 2021)", "afm"),
    ("Jensen cation plot (Al-(Fe+Ti)-Mg) - Jensen 1976", "jensen"),
    ("Hanski high-Mg plot - Hanski et al. 2001", "hanski"),
    ("High-Mg subdivision on TAS - Le Maitre 2002", "highmg_tas"),
]

CLASSIFICATION_PLUTONIC = [
    ("TAS plutonic - Middlemost (1994)", "tas_plutonic"),
    ("Normative An-Ab-Or - Barker 1979", "barker_anaborn"),
    ("Frost et al. 2001 / Frost & Frost 2008 (Fe-index, MALI, ASI, AI, FSSI)", "frost"),
    ("A/CNK vs A/NK - Maniar & Piccoli (1989)", "maniar_piccolli"),
    ("Ab-Or-Q haplogranite system - Tuttle & Bowen 1958", "haplogranite"),
]


# ---------------------------------------------------------------------------
# Tectonic discrimination diagrams
# ---------------------------------------------------------------------------

TECTONIC_VOLCANIC: dict[str, list[tuple[str, str]]] = {
    "Mafic": [
        ("Th/Yb vs Nb/Yb - Pearce 2008", "pearce2008_thyb_nbyb"),
        ("TiO2/Yb vs Nb/Yb - Pearce 2008", "pearce2008_tiyb_nbyb"),
        ("Nb/Yb vs Th/Nb - Li et al. 2025 (mafic to felsic)", "li2025_nbyb_thnb"),
        ("ThN vs NbN - Saccani 2015", "saccani2015_nb_th"),
        ("YbN vs DyN - Saccani 2015 (Boninite vs IAT)", "saccani2015_dy_yb"),
        ("(Dy/Yb)N vs (Ce/Yb)N - Saccani 2015 (N-MORB vs G-MORB)", "saccani2015_ce_dy_yb"),
        ("Zr/Y vs Ti/Y - Pearce & Gale 1977", "pearce_gale_1977"),
        ("Ti vs V - Shervais 1982 / Vermeesch 2006", "shervais_1982_TiV"),
        ("Zr vs Ti - Pearce & Cann 1973 / Vermeesch 2006", "pearce_cann_1973_ZrTi"),
        ("Na/100 - 25Nb - Sr (ternary) - Vermeesch 2006", "vermeesch_NaNbSr"),
        ("Si/1000 - Ti/40 - Sr (ternary) - Vermeesch 2006", "vermeesch_SiTiSr"),
        ("100Eu - 500Lu - Sr (ternary) - Vermeesch 2006", "vermeesch_EuLuSr"),
        ("V - Ti/50 - 5Sc (ternary) - Vermeesch 2006", "vermeesch_VTiSc"),
        ("50Sm - Ti/50 - V (ternary) - Vermeesch 2006", "vermeesch_SmTiV"),
        ("Th - Hf/3 - Ta (ternary) - Wood 1980 / Vermeesch 2006", "wood_1980_ThHfTa"),
        ("La/10 - Y/15 - Nb/8 (ternary) - Cabanis & Lecolle 1989", "cabanis_lecolle_1989"),
        ("Major elements DF (no FeO) - Pearce 1976 / Vermeesch 2006", "pearce_1976_DF"),
        ("TiO2-Zr-Y-Sr DF - Butler & Woronow / Vermeesch 2006", "butler_woronow_DF"),
        ("TiO2-Nb-V-Y-Zr DF set (5 panels) - Verma & Agrawal 2011", "verma_agrawal_2011"),
        ("FCMS source proxy (ln FeO/CaO vs ln MgO/SiO2) - Yang et al. 2019", "yang_2019_fcms"),
        ("FCKANTMS source proxy - Yang et al. 2019", "yang_2019_fckantms"),
    ],
    "Intermediate": [
        ("Sr/Y vs Y (adakite) - Defant & Drummond 1990", "defant_drummond_YSrY"),
        ("La/Yb vs Yb (adakite) - Defant & Drummond 1990", "defant_drummond_YbLaYb"),
        ("Nb/Yb vs Th/Nb - Li et al. 2025 (mafic to felsic)", "li2025_nbyb_thnb"),
        ("Majors DF set (5 panels) - Verma & Verma 2013", "verma_verma_2013_major"),
        ("Immobile majors + traces DF set (5 panels) - Verma & Verma 2013", "verma_verma_2013_imint"),
        ("Immobile traces DF set (5 panels) - Verma & Verma 2013", "verma_verma_2013_trace"),
    ],
    "Acid": [
        ("Ta vs Yb - Pearce et al. 1984", "pearce1984_YbTa"),
        ("Nb vs Y - Pearce et al. 1984", "pearce1984_YNb"),
        ("Rb vs (Yb+Ta) - Pearce et al. 1984", "pearce1984_YbTaRb"),
        ("Rb vs (Y+Nb) - Pearce et al. 1984", "pearce1984_YNbRb"),
        ("Rb/30 - Hf - 3Ta (ternary) - Harris et al. 1986", "harris_1986_HfRbTa"),
        ("Nb/Yb vs Th/Nb - Li et al. 2025 (mafic to felsic)", "li2025_nbyb_thnb"),
        ("Majors DF set (5 panels) - Verma et al. 2012", "verma_2012_acid"),
        ("Majors DF set (5 panels) - Verma et al. 2013", "verma_2013_acid_macid"),
        ("Immobile mj + traces DF set (5 panels) - Verma et al. 2013", "verma_2013_acid_mtacid"),
        ("Immobile traces DF set (5 panels) - Verma et al. 2013", "verma_2013_acid_tacid"),
    ],
}

# For plutonic rocks the immobile-element discriminants of Verma & co-authors
# apply equally well. We replicate the relevant entries here so the menu
# structure follows the user-requested layout.
TECTONIC_PLUTONIC: dict[str, list[tuple[str, str]]] = {
    "Mafic": [
        ("Major elements DF (no FeO) - Pearce 1976 / Vermeesch 2006", "pearce_1976_DF"),
        ("TiO2-Zr-Y-Sr DF - Butler & Woronow / Vermeesch 2006", "butler_woronow_DF"),
        ("TiO2-Nb-V-Y-Zr DF set (5 panels) - Verma & Agrawal 2011", "verma_agrawal_2011"),
        ("Nb/Yb vs Th/Nb - Li et al. 2025 (mafic to felsic)", "li2025_nbyb_thnb"),
    ],
    "Intermediate": [
        ("Nb/Yb vs Th/Nb - Li et al. 2025 (mafic to felsic)", "li2025_nbyb_thnb"),
        ("Majors DF set - Verma & Verma 2013", "verma_verma_2013_major"),
        ("Immobile majors + traces DF set - Verma & Verma 2013", "verma_verma_2013_imint"),
        ("Immobile traces DF set - Verma & Verma 2013", "verma_verma_2013_trace"),
    ],
    "Acid": [
        ("Ta vs Yb - Pearce et al. 1984", "pearce1984_YbTa"),
        ("Nb vs Y - Pearce et al. 1984", "pearce1984_YNb"),
        ("Rb vs (Yb+Ta) - Pearce et al. 1984", "pearce1984_YbTaRb"),
        ("Rb vs (Y+Nb) - Pearce et al. 1984", "pearce1984_YNbRb"),
        ("Rb/30 - Hf - 3Ta (ternary) - Harris et al. 1986", "harris_1986_HfRbTa"),
        ("Nb/Yb vs Th/Nb - Li et al. 2025 (mafic to felsic)", "li2025_nbyb_thnb"),
        ("Majors DF set (5 panels) - Verma et al. 2012", "verma_2012_acid"),
        ("Majors DF set (5 panels) - Verma et al. 2013", "verma_2013_acid_macid"),
        ("Immobile mj + traces DF set (5 panels) - Verma et al. 2013", "verma_2013_acid_mtacid"),
        ("Immobile traces DF set (5 panels) - Verma et al. 2013", "verma_2013_acid_tacid"),
    ],
}
