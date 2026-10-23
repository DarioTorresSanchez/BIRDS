"""The TAS field names stay legible and in their own fields.

The Irvine & Baragar (1971) curve drawn over both TAS diagrams ran
through Picrobasalt, Basaltic trachyandesite and Trachyte /
Trachydacite on the volcanic one, and through Peridot gabbro, Monzonite
and Quartz monzonite on the plutonic one, whose Alkaline / Sub-alkaline
captions also sat on Quartz monzonite.  The Peridot gabbro name was
outside its field altogether, at SiO2 40 for a field that starts at 41.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.base import PlotOptions
from birds.diagrams.templates.tas import TASPlutonic, TASVolcanic
from birds.plot_style import PlotStyle

SAMPLE = pd.DataFrame({"SiO2": [50.0], "Na2O": [3.0], "K2O": [1.0]})


def _label_boxes(key, size):
    fig = Figure(figsize=size)
    FigureCanvasAgg(fig)
    get_diagram(key).plot(fig, SAMPLE, PlotStyle(), PlotOptions())
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ax = fig.axes[0]
    inverse = ax.transData.inverted()
    boxes = {}
    for text in ax.texts:
        bb = text.get_window_extent(renderer)
        (x0, y0), (x1, y1) = inverse.transform([[bb.x0, bb.y0],
                                                [bb.x1, bb.y1]])
        boxes[text.get_text()] = (x0, y0, x1, y1)
    curves = [(np.asarray(line.get_xdata(), float),
               np.asarray(line.get_ydata(), float))
              for line in ax.lines if line.get_color() == "#1f3a93"]
    return boxes, curves


def _crosses(xs, ys, box):
    x0, y0, x1, y1 = box
    for i in range(len(xs) - 1):
        t = np.linspace(0, 1, 200)
        x = xs[i] + t * (xs[i + 1] - xs[i])
        y = ys[i] + t * (ys[i + 1] - ys[i])
        if np.any((x >= x0) & (x <= x1) & (y >= y0) & (y <= y1)):
            return True
    return False


@pytest.mark.parametrize("key", ["tas_volcanic", "tas_plutonic"])
@pytest.mark.parametrize("size", [(9, 7), (6.5, 5), (12, 8)])
def test_the_irvine_baragar_curve_crosses_no_name(key, size):
    boxes, curves = _label_boxes(key, size)
    crossed = [name for name, box in boxes.items()
               if any(_crosses(xs, ys, box) for xs, ys in curves)]
    assert not crossed, crossed


@pytest.mark.parametrize("key", ["tas_volcanic", "tas_plutonic"])
@pytest.mark.parametrize("size", [(9, 7), (6.5, 5), (12, 8)])
def test_no_two_names_overlap(key, size):
    boxes, _ = _label_boxes(key, size)
    names = list(boxes)
    clashes = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            p, q = boxes[a], boxes[b]
            if p[0] < q[2] and q[0] < p[2] and p[1] < q[3] and q[1] < p[3]:
                clashes.append((a, b))
    assert not clashes, clashes


@pytest.mark.parametrize("cls", [TASVolcanic, TASPlutonic])
def test_every_name_sits_in_its_own_field(cls):
    from birds.diagrams.templates.tas import _PLUTONIC_NAMES
    for key, (x, y) in cls.field_label_pos.items():
        want = (_PLUTONIC_NAMES[key] if cls is TASPlutonic
                else key.replace("\n", " "))
        assert cls.classify(x, y) == want, (key, (x, y))
