"""Classical CIPW normative-mineral calculation.

This module computes the normative mineralogy of an igneous rock from
its bulk major-element analysis following the classical
Cross-Iddings-Pirsson-Washington (1902) recipe, as codified by Kelsey
(1965). It produces the 19 main normative minerals:

    Q, C, Or, Ab, An, Ne, Lc, Kp, Ac, Ns, Di, Wo, Hy, Ol,
    Mt, Hm, Il, Ru, Cm, Ap, Z

and validates cleanly against textbook worked examples (Hollocher;
Best 2003).

Only the classical algorithm is implemented. Titanium left over after
ilmenite becomes rutile; the sphene (titanite) and perovskite steps of
the Verma variants are deliberately absent, as are the sulphide,
carbonate, halide and fluoride minerals of the extended schemes.

References
----------
- Cross, W., Iddings, J.P., Pirsson, L.V. & Washington, H.S. (1902).
  A quantitative chemico-mineralogical classification and nomenclature
  of igneous rocks. *J. Geol.* 10, 555-690.  Expanded the next year
  as the book *Quantitative Classification of Igneous Rocks* (Univ. of
  Chicago Press, 1903).
- Kelsey, C.H. (1965). Calculation of the CIPW norm.
  *Mineral. Mag.* 34, 276-282.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


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
    "Cm":  223.8348,     # Chromite                FeO + Cr2O3
}


# ---------------------------------------------------------------------------
# Mineral output order — used for column ordering in the result DataFrame
# ---------------------------------------------------------------------------

OUTPUT_MINERALS: Tuple[str, ...] = (
    "Q",  "C",  "Or", "Ab", "An", "Ne", "Lc", "Kp", "Ac", "Ns",
    "Di", "Wo", "Hy", "Ol", "Mt", "Hm", "Il", "Ru", "Cm",
    "Ap", "Z",
)

# Mg/Fe end-members that get combined into a single output mineral name
INTERNAL_MINERALS: Tuple[str, ...] = (
    "DiMg", "DiFe", "HyMg", "HyFe", "OlMg", "OlFe",
)


# ---------------------------------------------------------------------------
# What a norm needs
# ---------------------------------------------------------------------------

#: The oxides without which a norm means nothing.  A blank is read as 0 by
#: the allocation, so a missing Al2O3 leaves no feldspar and its silica
#: as quartz, and a missing MgO or iron leaves the silica the mafic
#: minerals would take as quartz too: a basalt comes out quartz-normative.
NORM_ESSENTIALS: Tuple[str, ...] = ("SiO2", "Al2O3", "MgO", "CaO",
                                    "Na2O", "K2O")


def norm_gaps(df: pd.DataFrame) -> pd.Series:
    """What each row lacks for a norm; an empty string when nothing.

    Missing means blank, not zero: a 0 is a value the analyst gave.  Iron
    counts when given as FeO or Fe2O3.  A total alone (FeOt, Fe2O3t) does
    not, since the norm needs the split; Data → Pre-process majors… makes
    it.
    """
    from .preprocess import get_feot

    def present(col: str) -> np.ndarray:
        if col not in df.columns:
            return np.zeros(len(df), dtype=bool)
        return pd.to_numeric(df[col], errors="coerce").notna().to_numpy()

    have = {ox: present(ox) for ox in NORM_ESSENTIALS}
    split_iron = present("FeO") | present("Fe2O3")
    total = get_feot(df)
    total_iron = (total.notna().to_numpy() if total is not None
                  else np.zeros(len(df), dtype=bool))

    gaps = []
    for i in range(len(df)):
        missing = [ox for ox in NORM_ESSENTIALS if not have[ox][i]]
        if not split_iron[i]:
            missing.append("FeO/Fe2O3 (iron given only as a total)"
                           if total_iron[i] else "iron")
        gaps.append(", ".join(missing))
    return pd.Series(gaps, index=df.index, dtype=object)


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


def _allocate(row: pd.Series
              ) -> Tuple[Dict[str, float], Dict[str, float], str, float]:
    """Run the CIPW allocation for one sample.

    Returns
    -------
    minerals      : dict mineral-symbol → moles of that CIPW unit
    leftovers     : oxide moles that could not be allocated (should be ≈ 0
                    after a successful run, except SiO₂ which can be ≠ 0
                    and is reported as Quartz or as a deficit handled by
                    olivine/nepheline substitution).
    saturation    : "oversaturated" | "saturated" | "undersaturated"
    deficit_mol   : SiO₂ (moles per 100 g) the desilication cascade could
                    not resolve — non-zero only for extremely
                    silica-poor rocks; see :func:`compute_cipw`.
    """
    mol = _moles_from_wt(row)
    min_: Dict[str, float] = _empty_minerals()

    # Mn²⁺ substitutes for Fe²⁺ in every ferromagnesian normative
    # mineral, so the classical norm folds MnO into FeO before any
    # allocation.  Skipping this silently drops the manganese from the
    # norm and leaves the total short by exactly the MnO content.
    if mol["MnO"] > 0:
        mol["FeO"] += mol["MnO"]
        mol["MnO"] = 0.0

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

    # 2. Chromite — 1 FeO + 1 Cr2O3
    if mol["Cr2O3"] > 0:
        cm = min(mol["Cr2O3"], mol["FeO"])
        min_["Cm"] = cm
        mol["FeO"] -= cm
        mol["Cr2O3"] -= cm

    # 3. Ilmenite — 1 FeO + 1 TiO2, then rutile for any TiO2 the FeO
    # could not pair with.  The rutile fallback only bites in very
    # Ti-rich / Fe-poor analyses, but without it that titanium simply
    # vanishes from the norm and the total under-reports.
    il = min(mol["TiO2"], mol["FeO"])
    min_["Il"] = il
    mol["FeO"] -= il
    mol["TiO2"] -= il
    if mol["TiO2"] > 1e-12:
        min_["Ru"] = mol["TiO2"]
        mol["TiO2"] = 0.0

    # 4. Magnetite — 1 FeO + 1 Fe2O3 ; remainder of Fe2O3 → Hematite
    mt = min(mol["FeO"], mol["Fe2O3"])
    min_["Mt"] = mt
    mol["FeO"] -= mt
    mol["Fe2O3"] -= mt
    if mol["Fe2O3"] > 0:
        min_["Hm"] = mol["Fe2O3"]
        mol["Fe2O3"] = 0.0

    # ----- silicate minerals (provisional) ----------------------------------
    # 5. Orthoclase (provisional) — K2O + Al2O3 + 6 SiO2 (silica counted later)
    or_prov = min(mol["K2O"], mol["Al2O3"])
    mol["K2O"] -= or_prov
    mol["Al2O3"] -= or_prov

    # 6. Albite (provisional) — Na2O + Al2O3 + 6 SiO2
    ab_prov = min(mol["Na2O"], mol["Al2O3"])
    mol["Na2O"] -= ab_prov
    mol["Al2O3"] -= ab_prov

    # 7. Acmite — uses leftover Na2O (Na > Al) with Fe2O3
    ac = 0.0
    if mol["Na2O"] > 0 and min_["Hm"] > 0:
        ac = min(mol["Na2O"], min_["Hm"])
        mol["Na2O"] -= ac
        min_["Hm"] -= ac
        min_["Ac"] = ac

    # 8. Sodium metasilicate Ns — extremely Na-rich, Al-poor rocks
    ns = mol["Na2O"]
    if ns > 0:
        min_["Ns"] = ns
        mol["Na2O"] = 0.0

    # 9. Anorthite — uses remaining Al2O3 with CaO
    an = min(mol["Al2O3"], mol["CaO"])
    min_["An"] = an
    mol["Al2O3"] -= an
    mol["CaO"] -= an

    # 10. Corundum — remaining Al2O3 if any
    if mol["Al2O3"] > 0:
        min_["C"] = mol["Al2O3"]
        mol["Al2O3"] = 0.0

    # 11. Diopside — CaO + (Mg,Fe)O + 2 SiO2
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

    # 12. Wollastonite — CaO leftover
    if mol["CaO"] > 0:
        min_["Wo"] = mol["CaO"]
        mol["CaO"] = 0.0

    # 13. Hypersthene (provisional) — (Mg,Fe)O + SiO2
    hy_prov = mol["MgO"] + mol["FeO"]
    hy_mg_frac = mol["MgO"] / hy_prov if hy_prov > 0 else 0.0
    mol["MgO"] = 0.0
    mol["FeO"] = 0.0

    # ----- silica balance ---------------------------------------------------
    # Silica demanded by each provisional silicate (per unit):
    #   Or 6, Ab 6, An 2, Ac 4, Ns 1, Di 2, Wo 1, Hy 1
    # Rutile is silica-free and does not enter this balance.
    sio2_demand = (
        6.0 * or_prov + 6.0 * ab_prov + 2.0 * an
        + 4.0 * ac + 1.0 * ns
        + 2.0 * di + 1.0 * min_["Wo"]
        + 1.0 * hy_prov
    )

    sio2_avail = mol["SiO2"] - sio2_demand
    # sio2_avail > 0  ⇒ over-saturated (Quartz appears)
    # sio2_avail < 0  ⇒ under-saturated (Ol replaces Hy, Ne replaces Ab, ...)

    sat = "saturated"
    unresolved = 0.0
    if sio2_avail > 1e-9:
        min_["Q"] = sio2_avail
        min_["Or"] = or_prov
        min_["Ab"] = ab_prov
        min_["Hy"] = hy_prov
        sat = "oversaturated"
        # store Hy Mg# for later
        _hy_mg = hy_mg_frac
    else:
        # 13.a  Convert Hy → Ol  (each mole Hy → 0.5 mole Ol releases 0.5 SiO2)
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
        # Anything still unresolved here means the rock is more
        # silica-poor than Hy→Ol, Ab→Ne, Or→Lc and Lc→Kp can absorb.
        # The classical recipe continues into the larnite (Cs) steps,
        # which are NOT implemented; rather than pretend the balance
        # closed — which silently inflates the norm total by the
        # residue — the leftover is reported so the caller can flag it.
        unresolved = max(deficit, 0.0)

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

    return min_, mol, sat, unresolved


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


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_cipw(df: pd.DataFrame) -> pd.DataFrame:
    """Compute the classical CIPW normative mineralogy for every row.

    Returns
    -------
    A new DataFrame with the same index as *df* and the following columns
    (wt-percent of each normative mineral, plus two diagnostics):

    ``norm_Q, norm_C, norm_Or, norm_Ab, norm_An, norm_Ne, norm_Lc,
    norm_Kp, norm_Ac, norm_Ns, norm_Di, norm_Wo, norm_Hy, norm_Ol,
    norm_Mt, norm_Hm, norm_Il, norm_Ru, norm_Cm, norm_Ap, norm_Z,
    norm_Total, silica_saturation, silica_deficit``

    The columns are populated with 0.0 (not NaN) when the corresponding
    mineral is not predicted, so the DataFrame can be summed / plotted
    immediately.

    A row lacking what the norm needs (:func:`norm_gaps`) gets no norm:
    every mineral, the total and the deficit are NaN and the saturation
    reads ``"incomplete"``.  Computed anyway, its blanks would count as
    zeros and give a norm that looks like any other but is wrong.

    ``silica_deficit`` is the wt % of SiO₂ the desilication cascade could
    not place.  It is 0 for every ordinary rock.  A non-zero value means
    the analysis is more silica-poor than Hy→Ol, Ab→Ne, Or→Lc and Lc→Kp
    can absorb — melilitites, nephelinites and kimberlites reach this —
    and that ``norm_Total`` is overstated by roughly that amount, because
    the larnite (Cs) steps of the full classical recipe are not
    implemented.  Callers should surface it rather than ignore it.
    """
    out_records: List[Dict[str, float]] = []
    sats: List[str] = []
    deficits: List[float] = []
    gaps = norm_gaps(df)

    for (_, row), gap in zip(df.iterrows(), gaps):
        if gap:
            out_records.append({f"norm_{m}": np.nan
                                for m in (*OUTPUT_MINERALS, "Total")})
            sats.append("incomplete")
            deficits.append(np.nan)
            continue
        min_, _leftover, sat, unresolved = _allocate(row)
        wts = _to_weights(min_)
        record = {f"norm_{k}": v for k, v in wts.items()}
        record["norm_Total"] = sum(wts.values())
        out_records.append(record)
        sats.append(sat)
        deficits.append(unresolved * MW_OXIDE["SiO2"])

    result = pd.DataFrame(out_records, index=df.index)
    # Re-order columns following OUTPUT_MINERALS for readability
    ordered = [f"norm_{m}" for m in OUTPUT_MINERALS] + ["norm_Total"]
    result = result[ordered]
    result["silica_saturation"] = sats
    result["silica_deficit"] = deficits
    return result


def normative_table(df: pd.DataFrame, *,
                    attach: bool = False) -> pd.DataFrame:
    """Like :func:`compute_cipw` but optionally **attaches** the resulting
    columns to *df* in place (useful for the Norm view auto-fill option).
    """
    result = compute_cipw(df)
    if attach:
        for col in result.columns:
            df[col] = result[col]
    return result
