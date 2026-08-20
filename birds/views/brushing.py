"""Cross-view brushing helpers (Alt/Cmd+click sample selection).

Gesture
-------
* **Alt+click** (or Cmd/Ctrl+click) near a plotted point toggles that
  sample in the shared :class:`~birds.selection.SelectionBus`.
* The same modifier-click far from every point, or the **Esc** key,
  clears the selection.

Plain clicks are untouched — the annotation toolkit keeps owning them.

Wiring a view
-------------
A view participates by

1. implementing ``_resolve_sample(x, y) -> (px, py, label) | None``
   (all diagram views already have this for Identify-sample), and
2. implementing ``_selection_points(names) -> [(ax, [(x, y), …]), …]``
   returning the plotted coordinates of the given sample names, and
3. calling :func:`draw_selection_overlay` at the end of its
   ``update_plot`` (just before ``canvas.draw()``), and
4. being registered once via :func:`wire_brushing`.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

# Modifier keys (as reported by matplotlib's key attribute on click
# events) that turn a left-click into a selection gesture.
SELECT_KEYS = {"alt", "cmd", "super", "ctrl", "control"}

# Name columns, in priority order — must match nearest_sample() in
# annotation_controller so resolver labels and overlay lookups agree.
NAME_COLUMNS = ("Sample_Name", "Sample_Label", "Sample", "No.", "id")

_RING = dict(s=210, facecolors="none", edgecolors="#f2b02c",
             linewidths=2.4, zorder=9)
_RING_INNER = dict(s=70, facecolors="none", edgecolors="#7a5410",
                   linewidths=1.0, zorder=9)


def names_series(df: Optional[pd.DataFrame]) -> Optional[pd.Series]:
    """String series of user-facing sample names for *df* (or None)."""
    if df is None or df.empty:
        return None
    for col in NAME_COLUMNS:
        if col in df.columns:
            return df[col].astype(str)
    return pd.Series([str(i) for i in df.index], index=df.index)


def is_select_click(event) -> bool:
    """True when the mpl mouse event is a modifier+left-click."""
    if getattr(event, "button", None) != 1 or event.inaxes is None:
        return False
    key = (getattr(event, "key", None) or "").lower()
    # Combined modifiers arrive like "ctrl+alt" — accept if any part
    # is one of ours.
    return any(part in SELECT_KEYS for part in key.split("+"))


def wire_brushing(view, bus) -> None:
    """Connect *view* to the shared selection *bus*.

    Idempotent per view (guards on an attribute).  The view must have
    ``canvas``, ``_resolve_sample`` and ``update_plot``.
    """
    if getattr(view, "_brushing_wired", False):
        return
    view._brushing_wired = True
    view._selection_bus = bus

    def on_click(event):
        if not is_select_click(event):
            return
        hit = view._resolve_sample(event.xdata, event.ydata)
        if hit is None:
            bus.clear()
            return
        px, py, label = hit
        ax = event.inaxes
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        nx = (px - event.xdata) / max(abs(xlim[1] - xlim[0]), 1e-9)
        ny = (py - event.ydata) / max(abs(ylim[1] - ylim[0]), 1e-9)
        if (nx * nx + ny * ny) ** 0.5 > 0.06:
            # Nearest point is still far away — treat as empty-space
            # click and clear instead of grabbing a random sample.
            bus.clear()
            return
        bus.toggle(label)

    def on_key(event):
        if (event.key or "").lower() == "escape":
            bus.clear()

    view.canvas.mpl_connect("button_press_event", on_click)
    view.canvas.mpl_connect("key_press_event", on_key)
    bus.changed.connect(view.update_plot)


def draw_selection_overlay(view) -> None:
    """Ring every selected sample on the view's axes.

    Called by each participating view at the end of ``update_plot``.
    Safe no-op when nothing is selected or the view lacks a bus /
    ``_selection_points`` implementation.
    """
    bus = getattr(view, "_selection_bus", None)
    if bus is None or len(bus) == 0:
        return
    points_fn = getattr(view, "_selection_points", None)
    if points_fn is None:
        return
    try:
        groups = points_fn(bus.names) or []
    except Exception:
        return
    for ax, pts in groups:
        if not pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        ax.scatter(xs, ys, **_RING)
        ax.scatter(xs, ys, **_RING_INNER)
