"""Per-diagram sample accounting — "why isn't my sample showing?".

Every diagram silently drops samples for four quite different reasons,
and until now the user had no way to tell them apart:

* an **active filter** removed the row (rock-type filter, Verma's
  compositional pre-filter, …);
* the group was **hidden** with its visibility checkbox in Edit plot;
* the sample simply **lacks the elements** the diagram needs, so its
  x/y came out non-finite;
* the sample plots **outside the published frame**.  Twenty-four of the
  52 templates fix their limits to the frame their source figure is
  drawn on -- the TAS is 35-78 wt.% SiO2 by 0-16 wt.% alkalis, the
  Verma panels are -8 to +8 -- and a sample beyond that is drawn but
  clipped away.  It used to be counted as plotted, which is the worst
  of both: invisible on the figure and accounted for as if it were
  there.  The frame itself stays as published; widening it would move
  boundaries that are only defined inside it.

:func:`count_samples` measures all three and :class:`CountLabel` shows
the tally under the canvas, colour-coded so a large silent drop is
impossible to miss.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QListWidget, QPushButton, QVBoxLayout,
)


@dataclass
class CountReport:
    """Sample tally for one rendered diagram.

    Alongside the counts it keeps the sample **names** behind each
    category, so "3 missing data" can answer the obvious follow-up —
    *which three?* — without the user hunting through the table.
    """

    total: int = 0        # rows in the source dataframe
    plotted: int = 0      # rows that produced a finite (x, y)
    filtered: int = 0     # rows dropped by an active filter
    hidden: int = 0       # rows in groups toggled invisible
    missing: int = 0      # rows kept + visible but lacking the elements
    offframe: int = 0     # rows with real coordinates outside the frame

    names: dict = field(default_factory=dict)   # category -> [sample names]

    @property
    def dropped(self) -> int:
        return self.filtered + self.hidden + self.missing + self.offframe

    def names_for(self, category: str) -> list:
        return list(self.names.get(category, ()))

    def html(self) -> str:
        """Rich-text summary for a QLabel.

        Each non-zero category is an ``<a href="…">`` so the label can
        turn it into a click that lists the samples.
        """
        if self.total == 0:
            return "<span style='color:#6c7388;'>No data loaded.</span>"
        parts = [self._link("plotted", f"<b>n = {self.plotted}</b> plotted",
                            "#3a5a8a")]
        if self.filtered:
            parts.append(self._link(
                "filtered", f"{self.filtered} filtered", "#8a6d1a"))
        if self.hidden:
            parts.append(self._link(
                "hidden", f"{self.hidden} hidden", "#5b6478"))
        if self.missing:
            parts.append(self._link(
                "missing", f"{self.missing} missing data", "#a04c2e"))
        if self.offframe:
            parts.append(self._link(
                "offframe", f"{self.offframe} off the frame", "#7a4ea0"))
        body = "  ·  ".join(parts)
        if self.plotted == 0 and self.total:
            body += ("  <span style='color:#a04c2e;'>— nothing to show; "
                     "check the filters and required elements.</span>")
        plural = "s" if self.total != 1 else ""
        return (f"<span style='color:#5b6478;'>{body}"
                f"  (of {self.total} sample{plural})</span>")

    def _link(self, category: str, text: str, colour: str) -> str:
        """Wrap *text* in a link when we know the names behind it."""
        if not self.names.get(category):
            return f"<span style='color:{colour};'>{text}</span>"
        return (f"<a href='{category}' style='color:{colour}; "
                f"text-decoration:none; border-bottom:1px dotted {colour};'>"
                f"{text}</a>")


def _visible_mask(df: pd.DataFrame, plot_style) -> pd.Series:
    """Boolean mask of rows belonging to a *visible* group.

    Falls back to all-True when the view has no grouping configured or
    the style carries no per-group visibility flags.

    ``get_groups`` *drops* hidden groups rather than flagging them, so
    the emptiness of its result is ambiguous: it means "nothing is
    grouped" **and** "everything is switched off".  The visibility flags
    are therefore read from the style itself first, and ``get_groups``
    is only consulted to find out which rows the surviving groups own.
    """
    all_true = pd.Series(True, index=df.index)
    if plot_style is None:
        return all_true
    groups = list(getattr(plot_style, "groups", None) or [])
    if not groups or all(getattr(g, "visible", True) for g in groups):
        return all_true
    try:
        from ..diagrams.templates.base import get_groups
        visible = pd.Series(False, index=df.index)
        for _label, sub, _gs in get_groups(df, plot_style):
            visible.loc[sub.index] = True
        return visible
    except Exception:
        return all_true


def diagram_coords(diagram, df: Optional[pd.DataFrame]):
    """Resolve a diagram's single-axis (x, y) mapping.

    Returns ``(xs, ys, single_axis)``.  ``single_axis`` is False only
    for templates that have **no single mapping to count against** —
    multi-panel ones (Verma multidimensional, Frost's 2×2 grid) and
    those that never override the base-class ``_compute_xy`` stub.  For
    those the caller must not read the absent coordinates as missing
    data.

    A template that *does* own a ``_compute_xy`` but returns ``None``
    is the opposite case: the dataset lacks the elements the diagram
    needs, so nothing is drawn and every surviving sample is
    missing-data.  It keeps ``single_axis=True`` and ``xs=ys=None``,
    which :func:`count_samples` already tallies correctly.
    """
    if diagram is None or df is None or df.empty:
        return None, None, False
    if hasattr(diagram, "panels") or hasattr(diagram, "_compute_xy_for_panel"):
        return None, None, False
    compute = getattr(diagram, "_compute_xy", None)
    if compute is None or not _owns_compute_xy(type(diagram)):
        return None, None, False
    try:
        xs, ys = compute(df)
    except Exception:                                      # noqa: BLE001
        # The mapping exists but blew up on this dataset — still nothing
        # plotted, so report it as missing data rather than as success.
        return None, None, True
    return xs, ys, True


def _owns_compute_xy(cls) -> bool:
    """True when *cls* overrides ``Diagram._compute_xy`` with its own."""
    try:
        from ..diagrams.templates.base import Diagram
        return getattr(cls, "_compute_xy", None) is not Diagram._compute_xy
    except Exception:                                      # noqa: BLE001
        return True


def panel_coords(diagram, df: Optional[pd.DataFrame]):
    """Coordinates of a multi-panel template's **first** panel.

    Every panel of a Verma discriminant set is built from the same list
    of elements, so whether a sample lands on panel (a) answers the
    question for the whole set.

    Returns ``(xs, ys, countable)``.  ``countable`` is False only when
    the template is not multi-panel at all; a multi-panel template whose
    panel *fails* to evaluate stays countable with ``xs = ys = None``,
    which reads as "the dataset lacks the elements this set needs".
    """
    compute = getattr(diagram, "_compute_xy_for_panel", None)
    panels = list(getattr(diagram, "panels", ()) or ())
    if compute is None or not panels or df is None or df.empty:
        return None, None, False
    try:
        xs, ys = compute(panels[0], df)
    except Exception:                                      # noqa: BLE001
        return None, None, True
    return xs, ys, True


def count_for_diagram(diagram, source_df, filtered_df, plot_style):
    """Convenience wrapper: resolve the coordinates then tally.

    Multi-panel templates are tallied against their first panel, which
    shares its element list with all the others.  Only templates with
    no computable mapping at all fall back to a filter/visibility-only
    tally, where every visible surviving sample counts as plotted.
    """
    xs, ys, single = diagram_coords(diagram, filtered_df)
    if single:
        return count_samples(source_df, filtered_df, xs, ys, plot_style,
                             getattr(diagram, "x_range", None),
                             getattr(diagram, "y_range", None))
    pxs, pys, countable = panel_coords(diagram, filtered_df)
    if countable:
        # Panels carry their own limits; the tally follows the first
        # one, which is the panel its coordinates came from.
        panels = getattr(diagram, "panels", None) or ()
        first = panels[0] if panels else None
        return count_samples(source_df, filtered_df, pxs, pys, plot_style,
                             getattr(first, "x_range", None),
                             getattr(first, "y_range", None))
    rep = CountReport(total=len(source_df) if source_df is not None else 0)
    if filtered_df is None or filtered_df.empty:
        rep.filtered = rep.total
        rep.names["filtered"] = _names_of(source_df, getattr(
            source_df, "index", []))
        return rep
    rep.filtered = max(rep.total - len(filtered_df), 0)
    if source_df is not None:
        rep.names["filtered"] = _names_of(
            source_df, source_df.index.difference(filtered_df.index))
    visible = _visible_mask(filtered_df, plot_style)
    rep.hidden = int((~visible).sum())
    rep.plotted = int(visible.sum())
    rep.names["hidden"] = _names_of(filtered_df, visible.index[~visible])
    rep.names["plotted"] = _names_of(filtered_df, visible.index[visible])
    return rep


def _within(values: pd.Series, limits) -> pd.Series:
    """Mask of the values inside *limits*, or all True when unbounded.

    The limits are taken as given and sorted, because a template may
    run its axis backwards -- Hastie's Th-Co diagram goes from 70 down
    to 0 -- and a literal ``lo <= v <= hi`` would then exclude
    everything.
    """
    if not limits:
        return pd.Series(True, index=values.index)
    low, high = sorted(limits)
    return values.between(low, high)


def count_samples(
    source_df: Optional[pd.DataFrame],
    filtered_df: Optional[pd.DataFrame],
    xs: Optional[pd.Series],
    ys: Optional[pd.Series],
    plot_style=None,
    x_range=None,
    y_range=None,
) -> CountReport:
    """Tally the fate of every sample for one diagram render.

    * *source_df*   — the full dataset before any diagram-level filter;
    * *filtered_df* — what the diagram actually received (pass the same
      object as *source_df* when the view has no filter);
    * *xs*, *ys*    — the computed plot coordinates for *filtered_df*
      (``None`` when the diagram could not compute them at all, which
      counts every surviving sample as missing-data);
    * *plot_style*  — used to subtract samples in hidden groups.
    """
    rep = CountReport()
    if source_df is None or source_df.empty:
        return rep
    rep.total = len(source_df)
    if filtered_df is None or filtered_df.empty:
        rep.filtered = rep.total
        rep.names["filtered"] = _names_of(source_df, source_df.index)
        return rep
    rep.filtered = max(rep.total - len(filtered_df), 0)
    dropped_idx = source_df.index.difference(filtered_df.index)
    rep.names["filtered"] = _names_of(source_df, dropped_idx)

    visible = _visible_mask(filtered_df, plot_style)
    rep.hidden = int((~visible).sum())
    rep.names["hidden"] = _names_of(filtered_df, visible.index[~visible])

    if xs is None or ys is None:
        rep.missing = int(visible.sum())
        rep.names["missing"] = _names_of(filtered_df, visible.index[visible])
        return rep
    xs = pd.Series(xs).reindex(filtered_df.index)
    ys = pd.Series(ys).reindex(filtered_df.index)
    finite = xs.notna() & ys.notna()
    # A sample with real coordinates that land outside the frame is
    # drawn and then clipped, so it is absent from the figure however
    # good its analysis was.  Separated from "plotted" rather than from
    # "missing": the data is there, the diagram just does not reach it.
    inside = _within(xs, x_range) & _within(ys, y_range)
    ok = finite & visible & inside
    missing = visible & ~finite
    offframe = visible & finite & ~inside
    rep.plotted = int(ok.sum())
    rep.missing = int(missing.sum())
    rep.offframe = int(offframe.sum())
    rep.names["plotted"] = _names_of(filtered_df, ok.index[ok])
    rep.names["missing"] = _names_of(filtered_df, missing.index[missing])
    rep.names["offframe"] = _names_of(filtered_df,
                                      offframe.index[offframe])
    return rep


def _names_of(df: Optional[pd.DataFrame], index) -> list:
    """User-facing sample names for the rows at *index*."""
    if df is None or df.empty or len(index) == 0:
        return []
    try:
        from .brushing import names_series
        series = names_series(df)
        if series is None:
            return [f"row {i}" for i in index]
        # A blank name (a row just added in the data table) is more
        # useful reported by its position than as an em dash.
        values = series.reindex(index)
        return [str(v).strip() if pd.notna(v) and str(v).strip()
                else f"(unnamed, row {i})"
                for i, v in zip(index, values)]
    except Exception:                                      # noqa: BLE001
        return [f"row {i}" for i in index]


_CATEGORY_TITLES = {
    "plotted":  "Samples plotted",
    "filtered": "Samples removed by a filter",
    "hidden":   "Samples in hidden groups",
    "missing":  "Samples lacking the required elements",
    "offframe": "Samples outside the diagram's frame",
}

_CATEGORY_HINTS = {
    "plotted":  "These produced a finite coordinate and are on the canvas.",
    "filtered": "An active filter (rock type, compositional range) dropped "
                "these before the diagram saw them.",
    "hidden":   "Their group is switched off in Data → Edit plot; turn it "
                "back on to plot them.",
    "missing":  "The diagram needs an element these samples do not carry, "
                "or the value is blank / non-numeric.",
    "offframe": "Their composition is fine and the coordinates are real, "
                "but they fall outside the axes this diagram is published "
                "on, so the canvas clips them. Read their values in the "
                "Statistics view instead.",
}


class CountLabel(QLabel):
    """Thin status strip that sits under a diagram canvas.

    Every non-zero category is a link: clicking it lists the samples
    behind the number, which is the question the tally always raises.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTextFormat(Qt.TextFormat.RichText)
        self.setStyleSheet("padding: 2px 4px; font-size: 11px;")
        self.setWordWrap(True)
        self.setToolTip(
            "How many samples reached this diagram — click a number to "
            "list them.\n"
            "• filtered — removed by an active filter (rock type, "
            "composition range)\n"
            "• hidden — group switched off in Data → Edit plot\n"
            "• missing data — the sample lacks one of the elements this "
            "diagram needs"
        )
        self._report: Optional[CountReport] = None
        self.linkActivated.connect(self._on_link)
        self.clear_report()

    def clear_report(self) -> None:
        self._report = None
        self.setText("")

    def show_report(self, report: CountReport) -> None:
        self._report = report
        self.setText(report.html())

    def _on_link(self, category: str) -> None:
        if self._report is None:
            return
        names = self._report.names_for(category)
        if not names:
            return
        SampleListDialog(category, names, self).exec()


class SampleListDialog(QDialog):
    """Lists the sample names behind one tally category."""

    def __init__(self, category: str, names: list, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(_CATEGORY_TITLES.get(category, "Samples"))
        self.resize(360, 420)
        self._names = list(names)

        layout = QVBoxLayout(self)
        header = QLabel(
            f"<b>{len(self._names)} sample"
            f"{'s' if len(self._names) != 1 else ''}</b><br>"
            f"<span style='color:#5b6478;'>"
            f"{_CATEGORY_HINTS.get(category, '')}</span>")
        header.setWordWrap(True)
        layout.addWidget(header)

        self.list_widget = QListWidget()
        self.list_widget.addItems(self._names)
        layout.addWidget(self.list_widget, 1)

        buttons = QHBoxLayout()
        copy_btn = QPushButton("⧉ Copy list")
        copy_btn.clicked.connect(self._copy)
        buttons.addWidget(copy_btn)
        buttons.addStretch(1)
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    def _copy(self) -> None:
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText("\n".join(self._names))
