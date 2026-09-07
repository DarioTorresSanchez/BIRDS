"""Every registered diagram, against every dataset shape a lab produces.

This is the sweep that catches a template broken by a refactor: it
renders all of them and checks the sample tally stays self-consistent,
which is the pair of properties the GUI actually depends on.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import _REGISTRY, get_diagram
from birds.diagrams.templates.base import PlotOptions
from birds.plot_style import GroupStyle, PlotStyle
from birds.views.sample_counts import count_for_diagram
from conftest import MAJORS, MODAL, TRACES

ALL_KEYS = sorted(_REGISTRY)
ELEMENTS = MAJORS + TRACES + MODAL


def _figure():
    from matplotlib.figure import Figure
    return Figure(figsize=(6, 5))


@pytest.fixture(params=[
    "normal", "with_nan", "hidden_groups", "majors_only",
    "all_nan", "single_row", "negative", "zeros", "huge", "tiny",
])
def dataset(request, full_df):
    """One dataset per pathological shape, with its plot style."""
    kind = request.param
    style = PlotStyle()
    style.group_columns = ["Group"]
    visible = kind != "hidden_groups"
    style.groups = [GroupStyle(name="A", visible=visible),
                    GroupStyle(name="B", visible=visible)]

    df = full_df
    if kind == "with_nan":
        df = full_df.assign(Nb=full_df["Nb"].mask(full_df.index % 3 == 0))
    elif kind == "majors_only":
        df = full_df[["Sample_Name", "SiO2", "Group"]]
    elif kind == "all_nan":
        df = full_df.assign(**{c: np.nan for c in ELEMENTS})
    elif kind == "single_row":
        df = full_df.head(1)
    elif kind == "negative":
        df = full_df.assign(**{c: -full_df[c] for c in MAJORS})
    elif kind == "zeros":
        df = full_df.assign(**{c: 0.0 for c in ELEMENTS})
    elif kind == "huge":
        df = full_df.assign(**{c: full_df[c] * 1e12 for c in ELEMENTS})
    elif kind == "tiny":
        df = full_df.assign(**{c: full_df[c] * 1e-12 for c in ELEMENTS})
    return kind, df, style


def test_registry_is_populated():
    assert len(ALL_KEYS) > 40, "diagram registry looks truncated"


@pytest.mark.parametrize("key", ALL_KEYS)
def test_diagram_renders(key, dataset, qapp):
    """No template may raise, whatever the data looks like."""
    _kind, df, style = dataset
    diagram = get_diagram(key)
    assert diagram is not None, f"{key} is registered but does not resolve"
    fig = _figure()
    try:
        diagram.plot(fig, df, style, PlotOptions())
    finally:
        fig.clf()


@pytest.mark.parametrize("key", ALL_KEYS)
def test_tally_is_self_consistent(key, dataset, qapp):
    """plotted + filtered + hidden + missing == total, always."""
    kind, df, style = dataset
    diagram = get_diagram(key)
    report = count_for_diagram(diagram, df, df, style)
    assert report.plotted + report.dropped == report.total
    for category in ("plotted", "filtered", "hidden", "missing"):
        assert len(report.names_for(category)) == getattr(report, category), (
            f"{key}/{kind}: {category} names do not match the count")
    report.html()          # must not raise on any combination


@pytest.mark.parametrize("key", ALL_KEYS)
def test_hidden_groups_plot_nothing(key, full_df, qapp):
    """A tally that ignores visibility silently misreports the figure."""
    style = PlotStyle()
    style.group_columns = ["Group"]
    style.groups = [GroupStyle(name="A", visible=False),
                    GroupStyle(name="B", visible=False)]
    report = count_for_diagram(get_diagram(key), full_df, full_df, style)
    assert report.plotted == 0


def test_every_catalog_entry_resolves():
    """A menu entry pointing at a missing template is a dead menu item."""
    from birds.diagrams import catalog
    keys = {k for _, k in catalog.CLASSIFICATION_VOLCANIC}
    keys |= {k for _, k in catalog.CLASSIFICATION_PLUTONIC}
    for family in (catalog.TECTONIC_VOLCANIC, catalog.TECTONIC_PLUTONIC):
        for entries in family.values():
            keys |= {k for _, k in entries}
    missing = sorted(k for k in keys if get_diagram(k) is None)
    assert not missing, f"catalogue points at missing templates: {missing}"
