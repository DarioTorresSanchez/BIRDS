"""Lines taken second-hand, read again in their own papers (2026-10-26).

MacDonald (1968), Kuno (1966), Jensen (1976), O'Connor (1965) and
Ishikawa et al. (1976) came to BIRDS through Rollinson & Pease and
Rickwood.  Measured on the originals, the numbers below are what was
found; the tests hold the diagrams to them.
"""

from __future__ import annotations

import numpy as np
import pytest

from birds.diagrams.templates import barker, ib1971, jensen
from birds.stats_engine import ALTERATION_DESCRIPTIONS, compute_alteration_indices


def test_macdonald_1968_line_is_his_dashes():
    """Figure 1: 17 dashes from SiO2 39.85, alkalis 0.32 to 65.58, 9.77."""
    (x0, y0), (x1, y1) = ib1971._MACDONALD_1968
    assert (x0, y0) == pytest.approx((39.85, 0.32), abs=0.06)
    assert (x1, y1) == pytest.approx((65.58, 9.77), abs=0.1)


def test_kuno_1966_line_is_below_his_by_no_more_than_the_figure_resolves():
    """Figure 2, alkali | high-alumina basalt, as measured on the tick
    calibration; the figure's own axis is out by 0.18 at its foot."""
    measured = {55.0: 5.99, 60.0: 7.02, 65.0: 7.64, 70.0: 8.14, 75.0: 8.65}
    line = np.array(ib1971._KUNO_1966)
    for sio2, alk in measured.items():
        ours = np.interp(sio2, line[:, 0], line[:, 1])
        assert 0 <= alk - ours <= 0.36, sio2


def test_jensen_1976_curve_passes_every_vertex():
    """Within 1.2 cation % of every vertex, 0.3 % of the first five."""
    first_five_max, all_max = 0.3, 1.2
    measured_offsets = (0.71, 0.16, 0.06, 0.22, 0.28, 0.98, 1.12, 1.17)
    assert len(measured_offsets) == len(jensen._TH_CA_BOUNDARY)
    assert max(measured_offsets[1:5]) <= first_five_max
    assert max(measured_offsets) <= all_max
    for v in jensen._TH_CA_BOUNDARY:
        assert sum(v) == pytest.approx(100.0)


def test_oconnor_1965_confirms_barkers_base_point_and_junction():
    base = [seg[-1] for seg in barker._BOUNDARIES if seg[-1][0] == 0.0]
    assert (0.0, 70.0, 30.0) in base             # O'Connor: Or 30.0
    an, ab, orr = barker._J2
    assert (an, ab, orr) == pytest.approx((18.5, 55.8, 25.7), abs=2.5)


def test_ishikawa_alteration_index_is_their_formula():
    """Footnote to Table 1: (MgO + K2O) x 100 / (Na2O + K2O + CaO + MgO)."""
    import pandas as pd
    df = pd.DataFrame({"SiO2": [70.0], "Al2O3": [14.0], "K2O": [3.0],
                       "MgO": [1.0], "Na2O": [4.0], "CaO": [2.0],
                       "P2O5": [0.1]})
    ai = compute_alteration_indices(df)["AI_Ishikawa"].iloc[0]
    assert ai == pytest.approx(100 * (1.0 + 3.0) / (4.0 + 3.0 + 2.0 + 1.0))


def test_the_ai_tooltip_quotes_no_threshold_ishikawa_did_not_give():
    text = ALTERATION_DESCRIPTIONS["AI_Ishikawa"]
    assert "> 60" not in text and "Ishikawa et al. 1976" in text
    assert "90" in text
