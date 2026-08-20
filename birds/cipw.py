"""CIPW normative-mineral calculation with three published variants.

This module computes the normative mineralogy of an igneous rock from
its bulk major-element analysis following the classical
Cross-Iddings-Pirsson-Washington (1903) recipe. Three variants are
exposed via :func:`compute_cipw`:

============  =====================================================
``classical`` Original 1903 algorithm — 18 main normative minerals
              (Q, Or, Ab, An, Ne, Lc, Di, Hy, Ol, Wo, Mt, Hm, Ilm, Ap,
              C, Cm, Ru, Tn). Validates cleanly against textbook
              examples (Hollocher; Best 2003).
``sinclas``   Verma, Torres-Alvarado & Sotelo-Rodríguez (2002).
              Identical mineral set as Classical, plus an integrated
              TAS rock-name classification on the post-allocation
              composition.
``hutchison`` Hutchison (1974) / Verma (2003) extension — adds Pyrite
              (Py), Calcite (Cc), Halite (Hl) and Fluorite (Fl) to
              the allocation order. Useful when the analysis reports
              S, CO₂, Cl or F.
============  =====================================================

The implementation is intentionally a *single core routine* that takes
flags for the variant-specific minerals; this guarantees that the three
variants agree on the shared minerals.

References
----------
- Cross, W., Iddings, J.P., Pirsson, L.V. & Washington, H.S. (1903).
  *Quantitative Classification of Igneous Rocks*. Univ. of Chicago Press.
- Kelsey, C.H. (1965). Calculation of the CIPW norm.
  *Mineral. Mag.* 34, 276-282.
- Hutchison, C.S. (1974). Laboratory Handbook of Petrographic
  Techniques. Wiley.
- Le Bas, M.J., Le Maitre, R.W., Streckeisen, A. & Zanettin, B. (1986).
  A chemical classification of volcanic rocks based on the total
  alkali-silica diagram. *J. Petrol.* 27, 745-750.
- Verma, S.P., Torres-Alvarado, I.S. & Sotelo-Rodríguez, Z.T. (2002).
  SINCLAS. *Comput. Geosci.* 28, 711-715.
- Verma, S.P. (2003). Hutchison's CIPW norm extended. *Geol. Soc. India.*
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .preprocess import FE2O3_TO_FEO, get_feot


# ---------------------------------------------------------------------------
# Oxide molecular weights (g/mol) — IUPAC 2021
# ---------------------------------------------------------------------------

MW_OXIDE: Dict[str, float] = {
    "SiO2":   60.0843,
    "TiO2":   79.8658,
    "Al2O3": 101.9613,
    "Fe2O3": 159.6882,
    "FeO":    71.8444,
    "MnO":    70.9374,
    "MgO":    40.3044,
    "CaO":    56.0774,
    "Na2O":   61.9789,
    "K2O":    94.1960,
    "P2O5":  141.9445,
    "Cr2O3": 151.9904,
    "NiO":    74.6928,
    "CO2":    44.0095,
    "SO3":    80.0632,
    "S":      32.0650,
    "Cl":     35.4530,
    "F":      18.9984,
    "ZrO2":  123.2228,
}


# ---------------------------------------------------------------------------
# CIPW unit molecular weights (g per "CIPW unit" of each mineral)
# Each unit consumes integer moles of input oxides as listed in
# ``MIN_STOICH`` below.
# ---------------------------------------------------------------------------

MW_MIN: Dict[str, float] = {
    "Q":   60.0843,      # Quartz                  SiO2
    "C":  101.9613,      # Corundum                Al2O3
    "Ap": 328.8612,      # Apatite (3.333 CaO + P2O5)
    "Z":  183.3071,      # Zircon                  ZrO2 + SiO2
    "Or": 556.6646,      # Orthoclase              K2O + Al2O3 + 6 SiO2
    "Ab": 524.4464,      # Albite                  Na2O + Al2O3 + 6 SiO2
    "An": 278.2073,      # Anorthite               CaO + Al2O3 + 2 SiO2
    "Ne": 284.1085,      # Nepheline               Na2O + Al2O3 + 2 SiO2
    "Lc": 436.4961,      # Leucite                 K2O + Al2O3 + 4 SiO2
    "Kp": 316.3275,      # Kaliophilite            K2O + Al2O3 + 2 SiO2
    "Ac": 461.9954,      # Acmite                  Na2O + Fe2O3 + 4 SiO2
    "Ns": 122.0625,      # Sodium metasilicate     Na2O + SiO2
    "DiMg": 216.5530,    # Diopside-Mg (CaMgSi2O6) CaO + MgO + 2 SiO2
    "DiFe": 248.0930,    # Diopside-Fe (Hd)        CaO + FeO + 2 SiO2
    "Wo": 116.1617,      # Wollastonite            CaO + SiO2
    "HyMg": 100.3887,    # Hypersthene-Mg (En)     MgO + SiO2
    "HyFe": 131.9287,    # Hypersthene-Fe (Fs)     FeO + SiO2
    "OlMg": 140.6931,    # Forsterite              2 MgO + SiO2
    "OlFe": 203.7731,    # Fayalite                2 FeO + SiO2
    "Mt":  231.5326,     # Magnetite               FeO + Fe2O3
    "Hm":  159.6882,     # Hematite                Fe2O3
    "Il":  151.7102,     # Ilmenite                FeO + TiO2
    "Ru":   79.8658,     # Rutile                  TiO2
    "Tn":  196.0282,     # Titanite (Sphene)       CaO + TiO2 + SiO2
    "Cm":  223.8348,     # Chromite                FeO + Cr2O3
    "Pf":  135.9432,     # Perovskite              CaO + TiO2
    "Py":  119.967,      # Pyrite                  FeO + 2 S − O  (oxygen-deficient)
    "Cc":  100.0867,     # Calcite                 CaO + CO2
    "Hl":   58.443,      # Halite                  ½ Na2O + Cl − ½ O
    "Fl":   78.074,      # Fluorite                CaO + 2 F − O
}


# ---------------------------------------------------------------------------
# Internal options
# ---------------------------------------------------------------------------

@dataclass
class CipwOptions:
    """Per-variant feature flags."""
    include_sulfide: bool = False      # Pyrite
    include_carbonate: bool = False    # Calcite
    include_halide: bool = False       # Halite
    include_fluoride: bool = False     # Fluorite
    titanite_priority: bool = False    # Verma & Rivera-Gómez (2013) —
                                       # divert TiO2 to titanite / perovskite
                                       # before the classical ilmenite step.
    classify_tas: bool = False         # SINCLAS-style TAS classification

    @classmethod
    def for_variant(cls, variant: str) -> "CipwOptions":
        variant = variant.lower()
        if variant == "classical":
            return cls()
        if variant == "sinclas":
            return cls(classify_tas=True)
        if variant == "hutchison":
            return cls(include_sulfide=True, include_carbonate=True,
                       include_halide=True, include_fluoride=True)
        if variant in ("verma_rg_2013", "verma-rg-2013"):
            # Verma & Rivera-Gómez (2013) — refined SINCLAS with sphene
            # (titanite) and perovskite in the allocation chain, and the
            # full Hutchison-style sulphide / carbonate / halide /
            # fluoride extension turned on.
            return cls(include_sulfide=True, include_carbonate=True,
                       include_halide=True, include_fluoride=True,
                       titanite_priority=True, classify_tas=True)
        raise ValueError(
            f"Unknown CIPW variant {variant!r}. Expected 'classical', "
            f"'sinclas', 'hutchison' or 'verma_rg_2013'.")


# ---------------------------------------------------------------------------
# Mineral output order — used for column ordering in the result DataFrame
# ---------------------------------------------------------------------------

OUTPUT_MINERALS: Tuple[str, ...] = (
    "Q",  "C",  "Or", "Ab", "An", "Ne", "Lc", "Kp", "Ac", "Ns",
    "Di", "Wo", "Hy", "Ol", "Mt", "Hm", "Il", "Ru", "Tn", "Cm",
    "Ap", "Pf", "Z",  "Py", "Cc", "Hl", "Fl",
)

# Mg/Fe end-members that get combined into a single output mineral name
INTERNAL_MINERALS: Tuple[str, ...] = (
    "DiMg", "DiFe", "HyMg", "HyFe", "OlMg", "OlFe",
)


# ---------------------------------------------------------------------------
# Core single-sample allocator
# ---------------------------------------------------------------------------

def _empty_minerals() -> Dict[str, float]:
    out = {m: 0.0 for m in OUTPUT_MINERALS}
    for m in INTERNAL_MINERALS:
        out[m] = 0.0
    return out


def _moles_from_wt(row: pd.Series) -> Dict[str, float]:
    """Convert wt-percent oxides → moles per 100 g of rock."""
    m: Dict[str, float] = {}
    for ox, mw in MW_OXIDE.items():
        v = row.get(ox, np.nan)
        if pd.isna(v) or v == 0:
            m[ox] = 0.0
        else:
            m[ox] = float(v) / mw
    return m


def _allocate(row: pd.Series, options: CipwOptions
              ) -> Tuple[Dict[str, float], Dict[str, float], str]:
    """Run the CIPW allocation for one sample.

    Returns
    -------
    minerals      : dict mineral-symbol → moles of that CIPW unit
    leftovers     : oxide moles that could not be allocated (should be ≈ 0
                    after a successful run, except SiO₂ which can be ≠ 0
                    and is reported as Quartz or as a deficit handled by
                    olivine/nepheline substitution).
    saturation    : "oversaturated" | "saturated" | "undersaturated"
    """
    mol = _moles_from_wt(row)
    min_: Dict[str, float] = _empty_minerals()

    # ----- pre-silicate minerals --------------------------------------------
    # 1. Apatite — 1 mol P2O5 + 3.333 mol CaO
    if mol["P2O5"] > 0:
        ap = mol["P2O5"]
        consume = 3.3333 * ap
        if consume > mol["CaO"]:                            # rare
            ap = mol["CaO"] / 3.3333
            consume = mol["CaO"]
        min_["Ap"] = ap
        mol["CaO"] -= consume
        mol["P2O5"] -= ap

    # 1bis. Zircon — 1 mol ZrO2 + 1 mol SiO2
    if mol.get("ZrO2", 0) > 0:
        z = min(mol["ZrO2"], mol["SiO2"])
        min_["Z"] = z
        mol["SiO2"] -= z
        mol["ZrO2"] -= z

    # 2. Pyrite (Hutchison) — 1 mol FeS2 = 1 FeO + 2 S (+ ½ O₂ released)
    if options.include_sulfide and mol["S"] > 0:
        py = min(mol["S"] / 2.0, mol["FeO"])
        min_["Py"] = py
        mol["FeO"] -= py
        mol["S"] -= 2.0 * py

    # 3. Calcite (Hutchison) — 1 mol CO2 + 1 mol CaO
    if options.include_carbonate and mol["CO2"] > 0:
        cc = min(mol["CO2"], mol["CaO"])
        min_["Cc"] = cc
        mol["CaO"] -= cc
        mol["CO2"] -= cc

    # 4. Halite (Hutchison) — ½ Na2O + 1 Cl
    if options.include_halide and mol["Cl"] > 0:
        hl = min(mol["Cl"], 2.0 * mol["Na2O"])
        min_["Hl"] = hl
        mol["Na2O"] -= hl / 2.0
        mol["Cl"] -= hl

    # 5. Fluorite (Hutchison) — 1 CaO + 2 F
    if options.include_fluoride and mol["F"] > 0:
        fl = min(mol["F"] / 2.0, mol["CaO"])
        min_["Fl"] = fl
        mol["CaO"] -= fl
        mol["F"] -= 2.0 * fl

    # 6. Chromite — 1 FeO + 1 Cr2O3
    if mol["Cr2O3"] > 0:
        cm = min(mol["Cr2O3"], mol["FeO"])
        min_["Cm"] = cm
        mol["FeO"] -= cm
        mol["Cr2O3"] -= cm

    # 7. Ilmenite (provisional) — 1 FeO + 1 TiO2.
    # In SINCLAS / classical CIPW we consume all TiO2 here and any
    # leftover (when FeO runs out first) becomes rutile. In the
    # Verma & Rivera-Gómez (2013) chain titanite has priority over
    # ilmenite — we defer the whole step until after anorthite so the
    # free CaO is known.
    if not options.titanite_priority:
        il = min(mol["TiO2"], mol["FeO"])
        min_["Il"] = il
        mol["FeO"] -= il
        mol["TiO2"] -= il

    # 8. Magnetite — 1 FeO + 1 Fe2O3 ; remainder of Fe2O3 → Hematite
    mt = min(mol["FeO"], mol["Fe2O3"])
    min_["Mt"] = mt
    mol["FeO"] -= mt
    mol["Fe2O3"] -= mt
    if mol["Fe2O3"] > 0:
        min_["Hm"] = mol["Fe2O3"]
        mol["Fe2O3"] = 0.0

    # ----- silicate minerals (provisional) ----------------------------------
    # 9. Orthoclase (provisional) — K2O + Al2O3 + 6 SiO2 (silica counted later)
    or_prov = min(mol["K2O"], mol["Al2O3"])
    mol["K2O"] -= or_prov
    mol["Al2O3"] -= or_prov

    # 10. Albite (provisional) — Na2O + Al2O3 + 6 SiO2
    ab_prov = min(mol["Na2O"], mol["Al2O3"])
    mol["Na2O"] -= ab_prov
    mol["Al2O3"] -= ab_prov

    # 11. Acmite — uses leftover Na2O (Na > Al) with Fe2O3
    ac = 0.0
    if mol["Na2O"] > 0 and min_["Hm"] > 0:
        ac = min(mol["Na2O"], min_["Hm"])
        mol["Na2O"] -= ac
        min_["Hm"] -= ac
        min_["Ac"] = ac

    # 12. Sodium metasilicate Ns — extremely Na-rich, Al-poor rocks
    ns = mol["Na2O"]
    if ns > 0:
        min_["Ns"] = ns
        mol["Na2O"] = 0.0

    # 13. Anorthite — uses remaining Al2O3 with CaO
    an = min(mol["Al2O3"], mol["CaO"])
    min_["An"] = an
    mol["Al2O3"] -= an
    mol["CaO"] -= an

    # 14. Corundum — remaining Al2O3 if any
    if mol["Al2O3"] > 0:
        min_["C"] = mol["Al2O3"]
        mol["Al2O3"] = 0.0

    # 14b. Verma & Rivera-Gómez (2013) — titanite / ilmenite /
    # perovskite / rutile chain.  Titanite (CaTiSiO5) only forms when
    # the rock is silica-saturated enough to spare 1 mol SiO2 per Tn
    # unit; otherwise ilmenite stays on its classical SINCLAS path and
    # any leftover TiO2 falls back to perovskite (silica-deficient
    # alkaline rocks) or rutile (rare).
    if options.titanite_priority:
        # Provisional SiO2 demand assuming Tn = 0. Approximates the
        # final balance closely enough to decide whether the rock can
        # afford titanite without going silica-undersaturated.
        prov_di = min(mol["CaO"], mol["MgO"] + mol["FeO"])
        prov_wo = max(0.0, mol["CaO"] - (mol["MgO"] + mol["FeO"]))
        prov_hy = (mol["MgO"] + mol["FeO"]) - prov_di
        sio2_demand_provisional = (
            6.0 * or_prov + 6.0 * ab_prov + 2.0 * an
            + 4.0 * ac + 1.0 * ns
            + 2.0 * prov_di + 1.0 * prov_wo + 1.0 * prov_hy
        )
        sio2_excess = mol["SiO2"] - sio2_demand_provisional

        if sio2_excess > 1e-9:
            tn = min(mol["TiO2"], mol["CaO"], sio2_excess)
            if tn > 1e-9:
                min_["Tn"] = tn
                mol["TiO2"] -= tn
                mol["CaO"] -= tn
        # Ilmenite consumes the remaining TiO2 / FeO pair as in SINCLAS.
        il = min(mol["TiO2"], mol["FeO"])
        if il > 1e-9:
            min_["Il"] = il
            mol["TiO2"] -= il
            mol["FeO"] -= il
        # Silica-deficient leftover TiO2 → perovskite (CaO + TiO2, no Si)
        pf = min(mol["TiO2"], mol["CaO"])
        if pf > 1e-9:
            min_["Pf"] = pf
            mol["TiO2"] -= pf
            mol["CaO"] -= pf
        # Anything still left becomes rutile.
        if mol["TiO2"] > 1e-9:
            min_["Ru"] = mol["TiO2"]
            mol["TiO2"] = 0.0

    # 15. Diopside — CaO + (Mg,Fe)O + 2 SiO2
    di = 0.0
    di_mg_frac = 0.0
    mf = mol["MgO"] + mol["FeO"]
    if mf > 0 and mol["CaO"] > 0:
        di = min(mol["CaO"], mf)
        di_mg_frac = mol["MgO"] / mf if mf > 0 else 0.0
        mol["CaO"] -= di
        mol["MgO"] -= di * di_mg_frac
        mol["FeO"] -= di * (1.0 - di_mg_frac)
        min_["DiMg"] = di * di_mg_frac
        min_["DiFe"] = di * (1.0 - di_mg_frac)

    # 16. Wollastonite — CaO leftover
    if mol["CaO"] > 0:
        min_["Wo"] = mol["CaO"]
        mol["CaO"] = 0.0

    # 17. Hypersthene (provisional) — (Mg,Fe)O + SiO2
    hy_prov = mol["MgO"] + mol["FeO"]
    hy_mg_frac = mol["MgO"] / hy_prov if hy_prov > 0 else 0.0
    mol["MgO"] = 0.0
    mol["FeO"] = 0.0

    # ----- silica balance ---------------------------------------------------
    # Silica demanded by each provisional silicate (per unit):
    #   Or 6, Ab 6, An 2, Ac 4, Ns 1, Di 2, Wo 1, Hy 1, Tn 1
    # Titanite (CaTiSiO5) carries one SiO2 per unit; perovskite and
    # rutile are silica-free and don't enter this balance.
    sio2_demand = (
        6.0 * or_prov + 6.0 * ab_prov + 2.0 * an
        + 4.0 * ac + 1.0 * ns
        + 2.0 * di + 1.0 * min_["Wo"]
        + 1.0 * hy_prov
        + 1.0 * min_["Tn"]
    )

    sio2_avail = mol["SiO2"] - sio2_demand
    # sio2_avail > 0  ⇒ over-saturated (Quartz appears)
    # sio2_avail < 0  ⇒ under-saturated (Ol replaces Hy, Ne replaces Ab, ...)

    sat = "saturated"
    if sio2_avail > 1e-9:
        min_["Q"] = sio2_avail
        min_["Or"] = or_prov
        min_["Ab"] = ab_prov
        min_["Hy"] = hy_prov
        sat = "oversaturated"
        # store Hy Mg# for later
        _hy_mg = hy_mg_frac
    else:
        # 17.a   Convert Hy → Ol  (each mole Hy → 0.5 mole Ol releases 0.5 SiO2)
        deficit = -sio2_avail
        hy_to_ol = min(hy_prov, 2.0 * deficit)   # mol Hy converted
        ol_added = hy_to_ol / 2.0                # mol Ol produced
        hy_left = hy_prov - hy_to_ol
        deficit -= 0.5 * hy_to_ol

        # Distribute Ol into Mg/Fe ends with the same fraction as Hy
        ol_mg = ol_added * hy_mg_frac
        ol_fe = ol_added * (1.0 - hy_mg_frac)
        min_["OlMg"] = ol_mg
        min_["OlFe"] = ol_fe
        hy_mg = hy_left * hy_mg_frac
        hy_fe = hy_left * (1.0 - hy_mg_frac)
        min_["HyMg"] = hy_mg
        min_["HyFe"] = hy_fe

        if deficit > 1e-9:
            # 17.b   Convert Ab → Ne  (releases 4 SiO2 per mole Ab)
            ab_to_ne = min(ab_prov, deficit / 4.0)
            ab_prov -= ab_to_ne
            min_["Ne"] = ab_to_ne
            deficit -= 4.0 * ab_to_ne
        if deficit > 1e-9:
            # 17.c   Convert Or → Lc  (releases 2 SiO2 per mole Or)
            or_to_lc = min(or_prov, deficit / 2.0)
            or_prov -= or_to_lc
            min_["Lc"] = or_to_lc
            deficit -= 2.0 * or_to_lc
        if deficit > 1e-9:
            # 17.d   Convert Lc → Kp  (releases 2 SiO2 per mole Lc)
            lc_to_kp = min(min_["Lc"], deficit / 2.0)
            min_["Lc"] -= lc_to_kp
            min_["Kp"] = lc_to_kp
            deficit -= 2.0 * lc_to_kp

        min_["Or"] = or_prov
        min_["Ab"] = ab_prov
        sat = "undersaturated"

    # If we never went into the deficit branch, Hy is mono-block; otherwise
    # already split.
    if min_["HyMg"] == 0.0 and min_["HyFe"] == 0.0 and sat == "oversaturated":
        min_["HyMg"] = hy_prov * hy_mg_frac
        min_["HyFe"] = hy_prov * (1.0 - hy_mg_frac)

    # Refine saturation label using the actual mineral assemblage:
    #   Q > 0        ⇒ oversaturated
    #   Ne > 0       ⇒ undersaturated  (true Ne-norm)
    #   otherwise    ⇒ saturated       (Hy ± Ol with no Ne)
    if min_["Q"] > 1e-9:
        sat = "oversaturated"
    elif min_["Ne"] > 1e-9 or min_["Lc"] > 1e-9 or min_["Kp"] > 1e-9:
        sat = "undersaturated"
    else:
        sat = "saturated"

    return min_, mol, sat


# ---------------------------------------------------------------------------
# Convert per-sample mineral moles → wt % and TAS classification
# ---------------------------------------------------------------------------

def _to_weights(min_: Dict[str, float]) -> Dict[str, float]:
    """Multiply each mineral's moles by its CIPW-unit molecular weight."""
    out: Dict[str, float] = {}
    # Combine Mg/Fe end-members where the convention is a single mineral name
    out["Di"] = (min_["DiMg"] * MW_MIN["DiMg"]
                 + min_["DiFe"] * MW_MIN["DiFe"])
    out["Hy"] = (min_["HyMg"] * MW_MIN["HyMg"]
                 + min_["HyFe"] * MW_MIN["HyFe"])
    out["Ol"] = (min_["OlMg"] * MW_MIN["OlMg"]
                 + min_["OlFe"] * MW_MIN["OlFe"])
    # Single-member minerals
    for m in OUTPUT_MINERALS:
        if m in ("Di", "Hy", "Ol"):
            continue
        out[m] = min_.get(m, 0.0) * MW_MIN[m]
    return out


def _tas_name(row: pd.Series) -> str:
    """Return a coarse TAS rock name from SiO2 + (Na2O + K2O).

    Used by SINCLAS to attach a classification suffix; not exhaustive.
    """
    si = float(row.get("SiO2", np.nan))
    na = float(row.get("Na2O", 0.0))
    k = float(row.get("K2O", 0.0))
    if not np.isfinite(si):
        return ""
    alk = na + k
    # Foidite
    if si < 41:
        return "Foidite"
    # Picro-basalt
    if si < 45:
        return "Picro-basalt"
    if si < 52:
        if alk < 5: return "Basalt"
        if alk < 7: return "Trachy-basalt"
        return "Tephrite / Basanite"
    if si < 57:
        if alk < 6: return "Basaltic andesite"
        if alk < 8: return "Basaltic trachy-andesite"
        return "Phono-tephrite"
    if si < 63:
        if alk < 7.5: return "Andesite"
        if alk < 10:  return "Trachy-andesite"
        return "Tephri-phonolite"
    if si < 69:
        if alk < 8.5: return "Dacite"
        if alk < 12:  return "Trachyte / Trachy-dacite"
        return "Phonolite"
    return "Rhyolite"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cipw(df: pd.DataFrame, variant: str = "sinclas"
                 ) -> pd.DataFrame:
    """Compute the CIPW normative mineralogy for every row of *df*.

    Returns
    -------
    A new DataFrame with the same index as *df* and the following columns
    (wt-percent of each normative mineral, plus two diagnostics):

    ``norm_Q, norm_Or, norm_Ab, norm_An, norm_Ne, norm_Lc, norm_Kp,
    norm_Ac, norm_Ns, norm_Di, norm_Wo, norm_Hy, norm_Ol, norm_Mt,
    norm_Hm, norm_Il, norm_Ru, norm_Tn, norm_Cm, norm_Ap, norm_Pf,
    norm_Z, norm_Py, norm_Cc, norm_Hl, norm_Fl, norm_Total,
    silica_saturation, tas_field``

    The columns are populated with 0.0 (not NaN) when the corresponding
    mineral is not predicted, so the DataFrame can be summed / plotted
    immediately.
    """
    options = CipwOptions.for_variant(variant)
    out_records: List[Dict[str, float]] = []
    sats: List[str] = []
    tas: List[str] = []

    # Make sure FeOt exists if FeO/Fe2O3 are zero (the user can run the
    # preprocess dialog before; here we simply trust the inputs).
    for _, row in df.iterrows():
        min_, _leftover, sat = _allocate(row, options)
        wts = _to_weights(min_)
        record = {f"norm_{k}": v for k, v in wts.items()}
        record["norm_Total"] = sum(wts.values())
        out_records.append(record)
        sats.append(sat)
        tas.append(_tas_name(row) if options.classify_tas else "")

    result = pd.DataFrame(out_records, index=df.index)
    # Re-order columns following OUTPUT_MINERALS for readability
    ordered = [f"norm_{m}" for m in OUTPUT_MINERALS] + ["norm_Total"]
    result = result[ordered]
    result["silica_saturation"] = sats
    if options.classify_tas:
        result["tas_field"] = tas
    return result


def normative_table(df: pd.DataFrame, variant: str = "sinclas",
                    *, attach: bool = False) -> pd.DataFrame:
    """Like :func:`compute_cipw` but optionally **attaches** the resulting
    columns to *df* in place (useful for the Norm view auto-fill option).
    """
    result = compute_cipw(df, variant)
    if attach:
        for col in result.columns:
            df[col] = result[col]
    return result
