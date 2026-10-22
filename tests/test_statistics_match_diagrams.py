"""The statistics table and the diagrams must not answer differently.

Three faults in this project have had the same shape.  A quantity is
computed twice, once for the plot and once for the table under the same
heading, by two routes that do not share code.  A correction lands on
one route.  The two then disagree, under one name, with nothing to say
which is right:

* **Verma units.**  Three coefficient sets divide ppm traces by a wt.%
  oxide.  The conversion sat on the diagram classes, so the table read
  values 20 to 56 units out on axes the papers draw from -8 to +8.
* **Saccani normalisers.**  Figures 8 and 9 are chondrite-normalised.
  The diagrams used N-MORB and so did four rows of the table, each by
  its own route.
* **Pearce (2008) Ti/Yb.**  The diagram was corrected from Ti in ppm to
  TiO2 in wt.%, a factor of 5993, and the table's row was not.

None of those was caught by a test.  This file is the sweep that would
have caught all three: pair every discriminator with the diagram axis
plotting the same thing, and require them to be equal to the last bit.

The pairing is by source family, declared below.  Two diagrams by
different authors may well compute values a constant apart -- Saccani's
Yb_N is chondrite-normalised Yb and Pearce's axis is raw Yb, so one is
0.17 times the other -- and that is not a fault, it is two papers doing
different things.  Only a disagreement *within* one family is one.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import _REGISTRY, get_diagram
from birds.normalizations import OXIDE_TO_ELEMENT_PPM, TIO2_WT_TO_TI_PPM
from birds.tectonic_results import DISCRIMINATORS, _VERMA_SETS

N = 32
MAJORS = ["SiO2", "TiO2", "Al2O3", "Fe2O3", "FeO", "Fe2O3T", "MnO",
          "MgO", "CaO", "Na2O", "K2O", "P2O5"]
TRACES = ["Sc", "V", "Cr", "Co", "Ni", "Rb", "Sr", "Y", "Zr", "Nb",
          "Ba", "La", "Ce", "Pr", "Nd", "Sm", "Eu", "Gd", "Tb", "Dy",
          "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "Pb", "Th", "U",
          "Ga"]

#: discriminator key prefix -> the diagram keys of the same source.
#: A row whose family is listed here must agree with its family's
#: diagram wherever the two compute the same quantity.
FAMILIES = {
    "pearce2008": "pearce2008_",
    "pearcegale": "pearce_gale_",
    "shervais": "shervais_",
    "dd": "defant_drummond_",
    "saccani": "saccani2015_",
    "yang": "yang_2019_",
    "pearce1984": "pearce1984_",
    "df.pearce_1976": "pearce_1976_",
    "df.butler_woronow": "butler_woronow_",
}


@pytest.fixture(scope="module")
def df():
    """Log-uniform positive values, so no ratio is ill-conditioned.

    Every row has to be non-degenerate: a constant ratio between two
    quantities then really does mean they are the same quantity, not an
    accident of the sample.
    """
    rng = np.random.default_rng(20261003)
    data = {c: np.exp(rng.uniform(np.log(0.05), np.log(50.0), N))
            for c in MAJORS}
    data |= {c: np.exp(rng.uniform(np.log(0.05), np.log(300.0), N))
             for c in TRACES}
    return pd.DataFrame(data)


def _as_array(series):
    if series is None:
        return None
    a = np.asarray(pd.to_numeric(pd.Series(series), errors="coerce"), float)
    return a if a.shape == (N,) else None


@pytest.fixture(scope="module")
def axes(df):
    """{diagram key: axis: values} for every plain bivariate diagram."""
    out = {}
    for key in sorted(_REGISTRY):
        fn = getattr(get_diagram(key), "_compute_xy", None)
        if fn is None:
            continue
        try:
            x, y = fn(df)
        except Exception:                                   # noqa: BLE001
            continue
        for name, series in (("x", x), ("y", y)):
            a = _as_array(series)
            if a is not None:
                out[f"{key}:{name}"] = a
    return out


@pytest.fixture(scope="module")
def rows(df):
    out = {}
    for d in DISCRIMINATORS:
        try:
            a = _as_array(d.compute(df))
        except Exception:                                   # noqa: BLE001
            a = None
        if a is not None:
            out[d.key] = a
    return out


def _family(key):
    for prefix in sorted(FAMILIES, key=len, reverse=True):
        if key == prefix or key.startswith(prefix + "."):
            return prefix
    return None


def _constant_ratio(a, b):
    """The single number b/a, if it is the same on every row, else None."""
    ok = np.isfinite(a) & np.isfinite(b) & (np.abs(a) > 1e-12)
    if ok.sum() < N // 2:
        return None
    r = b[ok] / a[ok]
    if not np.all(np.isfinite(r)):
        return None
    med = float(np.median(r))
    if med == 0 or not np.isfinite(med):
        return None
    if np.max(np.abs(r / med - 1.0)) > 1e-9:
        return None
    return med


# ---------------------------------------------------------------------------
# The sweep
# ---------------------------------------------------------------------------

def test_no_row_disagrees_with_its_own_familys_diagram(rows, axes):
    """The whole point of the file.

    A discriminator and an axis of a diagram by the same author that
    track each other by a constant factor are the same quantity.  If
    that factor is not exactly 1, one of the two routes has been
    corrected and the other has not.
    """
    faults = []
    for dk, dv in rows.items():
        fam = _family(dk)
        if fam is None:
            continue
        for ak, av in axes.items():
            if not ak.startswith(FAMILIES[fam]):
                continue
            ratio = _constant_ratio(dv, av)
            if ratio is not None and abs(ratio - 1.0) > 1e-12:
                faults.append(f"{dk} is {ratio:.10g} x {ak}")
    assert not faults, (
        "statistics rows that track a diagram axis of the same source "
        "but do not equal it:\n  " + "\n  ".join(sorted(faults)))


@pytest.mark.parametrize("dk, ak", [
    # Every pair the sweep finds, written out, so that a row losing its
    # diagram shows up as a failure rather than as a silent gap.
    ("pearce2008.nb_yb", "pearce2008_thyb_nbyb:x"),
    ("pearce2008.th_yb", "pearce2008_thyb_nbyb:y"),
    ("pearce2008.ti_yb", "pearce2008_tiyb_nbyb:y"),
    # Pearce & Gale put Ti/Y across the bottom and Zr/Y up the side;
    # this pair was the other way round until the diagram was rebuilt
    # from the source, and these two rows are what caught the swap.
    ("pearcegale.ti_y", "pearce_gale_1977:x"),
    ("pearcegale.zr_y", "pearce_gale_1977:y"),
    ("shervais.v", "shervais_1982_TiV:y"),
    ("dd.sr_y", "defant_drummond_YSrY:y"),
    ("dd.la_yb", "defant_drummond_YbLaYb:y"),
    ("saccani.nb_n", "saccani2015_nb_th:x"),
    ("saccani.th_n", "saccani2015_nb_th:y"),
    ("saccani.dy_n", "saccani2015_dy_yb:x"),
    ("saccani.yb_n", "saccani2015_dy_yb:y"),
    ("saccani.ce_yb_n", "saccani2015_ce_dy_yb:x"),
    ("saccani.dy_yb_n", "saccani2015_ce_dy_yb:y"),
    ("yang.fckantms", "yang_2019_fckantms:y"),
    ("pearce1984.y_nb", "pearce1984_YNbRb:x"),
    ("pearce1984.yb_ta", "pearce1984_YbTaRb:x"),
    ("df.pearce_1976.df1", "pearce_1976_DF:x"),
    ("df.pearce_1976.df2", "pearce_1976_DF:y"),
    ("df.butler_woronow.df1", "butler_woronow_DF:x"),
    ("df.butler_woronow.df2", "butler_woronow_DF:y"),
])
def test_known_pair_is_identical(dk, ak, rows, axes):
    a, b = rows[dk], axes[ak]
    ok = np.isfinite(a) & np.isfinite(b)
    assert ok.sum() > N // 2
    np.testing.assert_allclose(a[ok], b[ok], rtol=0, atol=0)


def test_pearce_2008_reports_the_oxide_not_the_element(rows, df):
    """The fault this file was written for, pinned by its own arithmetic.

    Pearce plots TiO2 in wt.% over Yb in ppm.  Reporting Ti in ppm over
    Yb under the same heading is the same number times 5993.4.
    """
    expected = df["TiO2"] / df["Yb"]
    np.testing.assert_allclose(rows["pearce2008.ti_yb"], expected,
                               rtol=1e-12)
    as_element = df["TiO2"] * TIO2_WT_TO_TI_PPM / df["Yb"]
    assert np.median(as_element / rows["pearce2008.ti_yb"]) == (
        pytest.approx(TIO2_WT_TO_TI_PPM))


# ---------------------------------------------------------------------------
# The Verma panels, which are 175 of the 208 rows
# ---------------------------------------------------------------------------

def test_every_verma_row_equals_its_diagram_panel(df):
    """Paired by the identity of the DFCoefSet, which cannot be fooled.

    Panel keys such as IA_CA_COL repeat across every coefficient set,
    so pairing on the panel name alone compares a majors row against a
    traces diagram and reports nonsense.
    """
    owner = {id(coef): prefix
             for table, _cat, prefix, _c in _VERMA_SETS
             for coef in table.values()}
    rows = {d.key.lower(): d for d in DISCRIMINATORS}

    compared = 0
    for key in sorted(_REGISTRY):
        diagram = get_diagram(key)
        panels = getattr(diagram, "panels", None)
        fn = getattr(diagram, "_compute_xy_for_panel", None)
        table = getattr(diagram, "coef_table", None)
        if not panels or fn is None or not table:
            continue
        for panel in panels:
            x, y = fn(panel, df)
            for axis, series in (("df1", x), ("df2", y)):
                coef = table.get(f"{axis.upper()}_{panel.key}")
                if coef is None or series is None:
                    continue
                prefix = owner.get(id(coef))
                assert prefix is not None, (
                    f"{key}/{panel.key} plots a coefficient set that the "
                    f"statistics table does not publish")
                row = rows.get(f"{prefix}.{axis}_{panel.key}".lower())
                assert row is not None, (
                    f"{key}/{panel.key}/{axis} has no statistics row")
                got = _as_array(row.compute(df))
                assert got is not None
                a = np.asarray(series, float)
                ok = np.isfinite(a) & np.isfinite(got)
                np.testing.assert_allclose(a[ok], got[ok], rtol=0, atol=0)
                compared += 1

    assert compared == 110, f"expected 110 Verma panel axes, compared {compared}"


# ---------------------------------------------------------------------------
# The TiO2 -> Ti constant, which had three values in five places
# ---------------------------------------------------------------------------

def test_one_tio2_constant_for_the_whole_program():
    """Five places converted TiO2 to Ti; three of them said 5995.

    5995 is what the superseded atomic weight Ti = 47.90 gives. Every
    other factor in OXIDE_TO_ELEMENT_PPM is the current weight rounded
    to four figures, within 0.008 %; Ti alone had been left behind at
    0.025 % high, which is why it showed up as a diagram and a
    statistics row disagreeing rather than as a wrong number.
    """
    from birds.diagrams.templates import (
        major_df, tectonic_bivariate, tectonic_ternary,
    )
    import birds.tectonic_results as tr

    for module in (major_df, tectonic_bivariate, tectonic_ternary, tr):
        assert module.TIO2_WT_TO_TI_PPM is TIO2_WT_TO_TI_PPM, module.__name__
    assert OXIDE_TO_ELEMENT_PPM["Ti"] == ("TiO2", TIO2_WT_TO_TI_PPM)


def test_the_constant_is_the_mass_ratio():
    """Ti 47.867 over TiO2 79.865, per 10 000 to turn wt.% into ppm."""
    exact = 10000.0 * 47.867 / (47.867 + 2 * 15.999)
    assert TIO2_WT_TO_TI_PPM == pytest.approx(exact, rel=2e-5)
    # and the superseded value is outside that, which is the whole point
    assert 5995.0 != pytest.approx(exact, rel=2e-5)


@pytest.mark.parametrize("element, oxide, n_el, n_o", [
    ("K", "K2O", 2, 1), ("Ti", "TiO2", 1, 2), ("P", "P2O5", 2, 5),
    ("Si", "SiO2", 1, 2), ("Al", "Al2O3", 2, 3), ("Mg", "MgO", 1, 1),
    ("Ca", "CaO", 1, 1), ("Na", "Na2O", 2, 1), ("Mn", "MnO", 1, 1),
    ("Fe", "FeO", 1, 1),
])
def test_every_oxide_factor_is_its_mass_ratio(element, oxide, n_el, n_o):
    """Ti was the only one adrift; this says so of all ten."""
    weights = {"K": 39.0983, "Ti": 47.867, "P": 30.973761998,
               "Si": 28.085, "Al": 26.9815384, "Mg": 24.305,
               "Ca": 40.078, "Na": 22.98976928, "Mn": 54.938043,
               "Fe": 55.845}
    w = n_el * weights[element]
    exact = 10000.0 * w / (w + n_o * 15.999)
    got_oxide, got_factor = OXIDE_TO_ELEMENT_PPM[element]
    assert got_oxide == oxide
    assert got_factor == pytest.approx(exact, rel=1e-4)
