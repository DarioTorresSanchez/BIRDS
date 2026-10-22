"""Boundary lines against Rickwood (1989), who measured them all.

Rickwood, P.C. (1989) Boundary lines within petrologic diagrams which
use oxides of major and minor elements.  *Lithos* 22, 247-263.  He read
the published figures of each author and tabulated the lines; every
value below is from the rendered page.

The AFM curve of Irvine & Baragar (1971) was the one that did not agree:
it was an approximation running up to 8 units of F off theirs, and the
Kuno (1968) curve the diagram cited was not drawn at all.
"""

from __future__ import annotations

import pytest

from birds.diagrams.templates import afm, ib1971, jensen, k2o_sio2


def test_tas_alkaline_subalkaline_lines_are_table_1():
    assert ib1971._IRVINE_BARAGAR_1971 == [
        (39.2, 0.0), (40.0, 0.4), (43.2, 2.0), (45.0, 2.8), (48.0, 4.0),
        (50.0, 4.75), (53.7, 6.0), (55.0, 6.4), (60.0, 8.0), (65.0, 9.6),
        (66.4, 10.0)]
    assert ib1971._KUNO_1966 == [
        (45.85, 2.75), (46.85, 3.0), (50.0, 3.9), (50.3, 4.0), (53.1, 5.0),
        (55.0, 5.8), (55.6, 6.0), (60.0, 6.8), (61.5, 7.0), (65.0, 7.35),
        (70.0, 7.85), (71.6, 8.0), (75.0, 8.3), (76.4, 8.4)]
    assert ib1971._MACDONALD_1968 == [(39.8, 0.35), (65.5, 9.7)]


def test_k2o_bands_are_rickwoods():
    """Section 2.2: each division is a band, upper line then lower."""
    expected = [
        (((45, 1.38), (48, 1.7), (56, 3.3), (63, 4.20), (70, 5.1)),
         ((45, 1.37), (48, 1.6), (56, 2.98), (63, 3.87), (70, 4.61))),
        (((45, 0.98), (49, 1.28), (52, 1.5), (63, 2.48), (70, 3.1),
          (75, 3.43)),
         ((45, 0.92), (49, 1.1), (52, 1.35), (63, 2.32), (70, 2.86),
          (75, 3.25))),
        (((45, 0.2), (48, 0.41), (61, 0.97), (70, 1.38), (75, 1.51)),
         ((45, 0.15), (48, 0.3), (61, 0.8), (70, 1.23), (75, 1.44))),
    ]
    assert sorted(k2o_sio2.RICKWOOD_BANDS.values()) == sorted(expected)


def test_afm_curves_are_table_3():
    assert afm._IB_1971 == [
        (58.8, 36.2, 5), (47.6, 42.4, 10), (29.6, 52.6, 17.8),
        (25.4, 54.6, 20), (21.4, 54.6, 24), (19.4, 52.8, 27.8),
        (18.9, 51.1, 30), (16.6, 43.4, 40), (15, 35, 50)]
    assert afm._KUNO_1968 == [
        (72, 24, 4), (50, 39.5, 10.5), (34.5, 50, 15.5), (21.5, 57, 21.5),
        (16.5, 58, 25.5), (12.5, 55.5, 32), (9.5, 50.5, 40)]
    for curve in (afm._IB_1971, afm._KUNO_1968):
        assert all(sum(p) == pytest.approx(100, abs=0.05) for p in curve)


def test_afm_draws_both_curves_it_cites(full_df, plot_style):
    from matplotlib.figure import Figure

    from birds.diagrams.templates.base import PlotOptions
    fig = Figure()
    afm.AFM().plot(fig, full_df, plot_style, PlotOptions())
    labels = {line.get_label() for line in fig.axes[0].lines}
    assert {"Irvine & Baragar 1971", "Kuno 1968"} <= labels


def test_jensen_boundary_agrees_with_table_4():
    """Six of the eight points as printed; two more through misprints of
    Rickwood's own that do not sum to 100, (51.5, 29, 9.5) and
    (50.3, 25, 25.7).  The program keeps Rollinson & Pease's (2021)
    corrected Jensen & Pyke (1982) line, which has (52.5, 29, 18.5)
    where Rickwood has (50.7, 27.6, 21.7)."""
    table_4 = [(90, 10, 0), (53.5, 28.5, 18), (50.5, 27.5, 22),
               (50.8, 20, 29.2), (51.5, 12.5, 36)]
    misprinted = {(51.5, 29, 19.5): (51.5, 29, 9.5),
                  (50.3, 25, 24.7): (50.3, 25, 25.7)}
    ours = jensen._TH_CA_BOUNDARY
    assert all(p in ours for p in table_4)
    assert all(p in ours for p in misprinted)
    assert all(sum(p) != 100 for p in misprinted.values())
