"""Defant & Drummond (1993) Figure 2: the adakite field, drawn.

Geology 21, 547-550.  The Nature paper of 1990 describes adakites in
words and draws no field; this figure draws the adakite and island-arc
andesite-dacite-rhyolite fields, credited to that paper, with Juan de
Fuca Ridge basalt.  All three were followed along the ink of the scan.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure
from matplotlib.patches import Polygon

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import PlotOptions
from birds.diagrams.templates.tectonic_bivariate import (
    DD1993_ADAKITE,
    DD1993_ADR,
    DD1993_FIELDS,
    DD1993_JUAN_DE_FUCA,
    DD1993_X_RANGE,
    DD1993_Y_RANGE,
    DD_ADAKITE_Y_MAX,
    classify_dd1993,
)
from birds.plot_style import PlotStyle

KEY = "defant_drummond_1993_YSrY"


def test_the_frame_is_the_figures():
    d = get_diagram(KEY)
    assert tuple(d.x_range) == DD1993_X_RANGE == (0.0, 50.0)
    assert tuple(d.y_range) == DD1993_Y_RANGE == (0.0, 60.0)
    assert (d.x_label, d.y_label) == ("Y (ppm)", "Sr/Y")


@pytest.mark.parametrize("name, field", DD1993_FIELDS)
def test_every_field_is_inside_the_frame(name, field):
    for x, y in field:
        assert DD1993_X_RANGE[0] <= x <= DD1993_X_RANGE[1], name
        assert DD1993_Y_RANGE[0] <= y <= DD1993_Y_RANGE[1], name


@pytest.mark.parametrize("name, field", DD1993_FIELDS)
def test_a_measured_vertex_claims_one_decimal(name, field):
    for x, y in field:
        assert round(x, 1) == x and round(y, 1) == y


def test_the_adakite_field_is_closed_by_the_top_of_the_frame():
    """The loop runs off the top; its two branches are carried to 60."""
    tops = [p for p in DD1993_ADAKITE if p[1] == DD1993_Y_RANGE[1]]
    assert tops == [(3.4, 60.0), (14.0, 60.0)]


def test_the_adakite_field_ends_where_the_nature_paper_says():
    """Y <= 18 ppm in the text of 1990; the drawn field is widest at
    18.7 -- not designed in, and within a measurement of it."""
    widest = max(x for x, _ in DD1993_ADAKITE)
    assert widest == pytest.approx(DD_ADAKITE_Y_MAX, abs=0.8)


def test_the_adr_field_is_closed_by_the_axis_and_the_edge():
    assert DD1993_ADR[0] == (22.8, 0.0)
    assert DD1993_ADR[-2:] == ((50.0, 3.6), (50.0, 0.0))
    top = max(y for _, y in DD1993_ADR)
    assert top == 29.1                       # the arc's crest


def test_the_juan_de_fuca_box():
    assert DD1993_JUAN_DE_FUCA == (23.4, 46.6, 0.0, 5.6)


@pytest.mark.parametrize("y, sr_y, expected", [
    (9.0, 40.0, "adakite"),
    (30.0, 20.0, "island-arc ADR"),
    (40.0, 3.0, "island-arc ADR or Juan de Fuca Ridge basalt"),
    (16.0, 22.0, "adakite or island-arc ADR"),
    (5.0, 10.0, ""),                         # below the adakite loop
    (9.0, 100.0, ""),                        # above the frame
])
def test_classify(y, sr_y, expected):
    assert classify_dd1993(np.array([y]), np.array([sr_y]))[0] == expected


def test_classify_frame_reads_sr_and_y():
    df = pd.DataFrame({"Sr": [360.0, 0.0], "Y": [9.0, 0.0]})
    assert get_diagram(KEY).classify_frame(df).tolist() == ["adakite", ""]


def test_it_draws_the_three_fields():
    fig = Figure()
    get_diagram(KEY).plot(fig, pd.DataFrame({"Sr": [360.0], "Y": [9.0]}),
                          PlotStyle(), PlotOptions())
    ax = fig.axes[0]
    assert len([p for p in ax.patches if isinstance(p, Polygon)]) == 3
    texts = " ".join(t.get_text() for t in ax.texts)
    for word in ("Adakite", "Island-arc", "Juan de Fuca"):
        assert word in texts
    fig.clf()


def test_the_citation_says_what_is_not_drawn_and_what_is_cut():
    c = get_diagram(KEY).citation
    assert "Geology 21" in c and "Figure 2" in c
    assert "Sr/Y 60" in c and "not drawn" in c


def test_it_sits_beside_the_nature_diagram():
    from birds.diagrams.catalog import TECTONIC_VOLCANIC
    keys = [k for _label, k in TECTONIC_VOLCANIC["Intermediate"]]
    assert keys.index(KEY) == keys.index("defant_drummond_YSrY") + 1


def test_the_reference_is_in_the_bibliography():
    from birds.references import REFERENCES
    blob = " ".join(c for _, items in REFERENCES for c, _ in items)
    assert "10.1130/0091-7613(1993)021<0547:MSHPEO>2.3.CO;2" in blob
