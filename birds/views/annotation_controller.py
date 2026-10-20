"""Reusable annotation controller for any single-axis view.

The bivariate view pioneered the toolkit (lines / arrows / text / sample
identifier) but every plotting view in B.I.R.D.S can benefit from it.
This module exposes a small composable controller that any QWidget-based
view can drop in:

* Add ``ctl.group`` to your controls panel.
* Call ``ctl.bind_canvas(self.canvas)`` once at construction.
* At the end of every ``update_plot``, call ``ctl.draw(ax)`` on the
  primary axis.
* In ``serialize()``, store ``ctl.serialize()``; in ``restore()`` call
  ``ctl.restore(state.get("annotations"))``.

The "Identify sample" tool relies on a per-view callback that finds the
nearest sample given a click in data coordinates and returns
``(px, py, label)``.  Pass ``sample_resolver=None`` to hide that button
on views where there is no clear sample-to-point mapping.
"""

from __future__ import annotations

from typing import Callable, Optional

import pandas as pd

from .. import annotations as _ann
from .widgets import (
    ANN_MODE_ARROW,
    ANN_MODE_LINE,
    ANN_MODE_NONE,
    ANN_MODE_SAMPLE,
    ANN_MODE_TEXT,
    AnnotationGroup,
)


# Type alias — the sample resolver's signature.
SampleResolver = Callable[[float, float], Optional[tuple]]


class AnnotationController:
    """Composable annotation toolkit.

    Parameters
    ----------
    view : QWidget
        The owning view.  Used for dialogs (parent) and for triggering
        a redraw after the user adds an annotation.
    sample_resolver : callable, optional
        ``(x, y) -> (px, py, label) | None``.  Given a click in data
        coordinates, return the matching sample's coordinates and a
        human-readable label.  When omitted, the Identify-sample tool
        is hidden from the toolbar.
    redraw_method : str, default 'update_plot'
        Name of the view method to call when annotations change.  Most
        views use ``update_plot``; Statistics uses ``_render_stat_plot``,
        etc.
    """

    def __init__(self, view, *,
                 sample_resolver: Optional[SampleResolver] = None,
                 redraw_method: str = "update_plot") -> None:
        self.view = view
        self.sample_resolver = sample_resolver
        self.redraw_method = redraw_method
        # Annotations sit in a diagram's data coordinates, so they belong
        # to that diagram: one list per context (the diagram's key), the
        # current one shown.  A view with a single diagram never sets a
        # context and keeps one list, as before.
        self._by_context: dict = {"": []}
        self._context = ""
        #: False while the view shows axes the annotations do not belong
        #: to -- a map view's variogram, say -- so a click there neither
        #: adds nor deletes anything.
        self.enabled = True
        self._mode = ANN_MODE_NONE
        self._pending: Optional[tuple[float, float]] = None
        self.group = AnnotationGroup()
        if sample_resolver is None:
            self.group.btn_sample.setVisible(False)
        self.group.mode_requested.connect(self._on_mode)
        self.group.clear_requested.connect(self.clear)
        self.group.delete_index.connect(self.delete_index)

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------
    def bind_canvas(self, canvas) -> None:
        """Hook ``button_press_event`` so user clicks get routed here."""
        canvas.mpl_connect("button_press_event", self._on_click)

    def draw(self, ax) -> None:
        """Replay every annotation onto *ax*.  Call at the end of every
        plot path."""
        _ann.draw_all(ax, self.annotations)

    @property
    def annotations(self) -> list:
        """The annotations of the current context (diagram)."""
        return self._by_context.setdefault(self._context, [])

    @annotations.setter
    def annotations(self, value) -> None:
        self._by_context[self._context] = list(value)

    def set_context(self, key) -> None:
        """Show the annotations of diagram *key*.  A view with many
        diagrams calls this whenever the diagram changes; an arrow drawn
        on TAS used to reappear, at TAS's coordinates, on every other
        diagram of the view."""
        key = key or ""
        if key == self._context:
            return
        self._context = key
        self._pending = None
        self.group.refresh(self.annotations)

    # ------------------------------------------------------------------
    # Session persistence
    # ------------------------------------------------------------------
    def serialize(self):
        """A list, for a view with one diagram (as sessions always had
        it); ``{"by_diagram": {key: list}}`` once there are several."""
        stored = {key: _ann.serialize(items)
                  for key, items in self._by_context.items() if items}
        if set(stored) <= {""}:
            return stored.get("", [])
        return {"by_diagram": stored}

    def restore(self, data, legacy_context=None) -> None:
        """Bring back :meth:`serialize`'s output.  A plain list -- a
        session from before annotations were kept per diagram -- goes to
        *legacy_context*, the diagram the session was saved on."""
        self._by_context = {}
        if isinstance(data, dict) and "by_diagram" in data:
            for key, items in (data.get("by_diagram") or {}).items():
                self._by_context[str(key)] = _ann.deserialize(items)
        else:
            target = (self._context if legacy_context is None
                      else (legacy_context or ""))
            self._by_context[target] = _ann.deserialize(data)
        self.group.refresh(self.annotations)

    # ------------------------------------------------------------------
    # User actions
    # ------------------------------------------------------------------
    def clear(self) -> None:
        if not self.annotations:
            return
        self.annotations = []
        self.group.refresh(self.annotations)
        self._redraw()

    def delete_index(self, idx: int) -> None:
        if 0 <= idx < len(self.annotations):
            del self.annotations[idx]
            self.group.refresh(self.annotations)
            self._redraw()

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    def _on_mode(self, mode: str) -> None:
        self._mode = mode
        self._pending = None

    def _on_click(self, event) -> None:
        if event.inaxes is None or not self.enabled:
            return
        # Modifier+left-click belongs to cross-view brushing (see
        # birds/views/brushing.py) — never treat it as an annotation.
        from .brushing import is_select_click
        if is_select_click(event):
            return
        x, y = event.xdata, event.ydata
        if x is None or y is None:
            return
        # Right-click — delete nearest, regardless of current tool.
        if event.button == 3:
            xlim = event.inaxes.get_xlim()
            ylim = event.inaxes.get_ylim()
            tol = 0.04 * max(abs(xlim[1] - xlim[0]),
                             abs(ylim[1] - ylim[0]))
            idx = _ann.closest(self._annotations_safe(), x, y, tol)
            if idx is not None:
                del self.annotations[idx]
                self.group.refresh(self.annotations)
                self._redraw()
            return
        if event.button != 1 or self._mode == ANN_MODE_NONE:
            return

        mode = self._mode
        if mode == ANN_MODE_LINE:
            if self._pending is None:
                self._pending = (x, y)
                return
            x1, y1 = self._pending
            self._add(_ann.LineAnnotation(x1=x1, y1=y1, x2=x, y2=y))
            self._pending = None
        elif mode == ANN_MODE_ARROW:
            if self._pending is None:
                self._pending = (x, y)
                return
            x1, y1 = self._pending
            self._add(_ann.ArrowAnnotation(x1=x1, y1=y1, x2=x, y2=y))
            self._pending = None
        elif mode == ANN_MODE_TEXT:
            text, ok = self._ask_text("Annotation text", "Text to display:")
            if not ok or not text:
                self.group.cancel_mode()
                self._mode = ANN_MODE_NONE
                return
            self._add(_ann.TextAnnotation(x=x, y=y, text=text))
        elif mode == ANN_MODE_SAMPLE:
            if self.sample_resolver is None:
                return
            resolved = self.sample_resolver(x, y)
            if resolved is None:
                self.group.cancel_mode()
                self._mode = ANN_MODE_NONE
                return
            try:
                px, py, label = resolved
            except (TypeError, ValueError):
                return
            xlim = event.inaxes.get_xlim()
            ylim = event.inaxes.get_ylim()
            self._add(_ann.SampleAnnotation(
                px=px, py=py,
                dx=0.04 * (xlim[1] - xlim[0]),
                dy=0.04 * (ylim[1] - ylim[0]),
                label=str(label),
            ))

    def _annotations_safe(self) -> list:
        return list(self.annotations)

    def _add(self, ann_obj) -> None:
        self.annotations.append(ann_obj)
        self.group.refresh(self.annotations)
        self.group.cancel_mode()
        self._mode = ANN_MODE_NONE
        self._redraw()

    def _ask_text(self, title: str, prompt: str) -> tuple[str, bool]:
        from PySide6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self.view, title, prompt)
        return text.strip(), ok

    def _redraw(self) -> None:
        method = getattr(self.view, self.redraw_method, None)
        if callable(method):
            method()


# ---------------------------------------------------------------------------
# Sample resolver helpers
# ---------------------------------------------------------------------------

def nearest_sample(df: pd.DataFrame, xs: pd.Series, ys: pd.Series,
                   x: float, y: float, xlim: tuple, ylim: tuple,
                   name_columns=("Sample_Name", "Sample_Label",
                                  "Sample", "No.", "id")
                   ) -> Optional[tuple]:
    """Find the row in *df* whose (xs, ys) is closest to (x, y).

    Distances are normalised by the current axis spans so a click on a
    log-scale plot doesn't bias toward the high-magnitude axis.  Returns
    ``(px, py, label)`` or None if no usable row exists.
    """
    if df is None or df.empty or xs is None or ys is None:
        return None
    sx = max(abs(xlim[1] - xlim[0]), 1e-9)
    sy = max(abs(ylim[1] - ylim[0]), 1e-9)
    dx = (xs - x) / sx
    dy = (ys - y) / sy
    dist = (dx ** 2 + dy ** 2) ** 0.5
    dist = dist.where(xs.notna() & ys.notna())
    if dist.dropna().empty:
        return None
    idx = dist.idxmin()
    label = None
    for col in name_columns:
        if col in df.columns:
            v = df.at[idx, col]
            if pd.notna(v):
                label = str(v)
                break
    if label is None:
        label = str(idx)
    return float(xs.loc[idx]), float(ys.loc[idx]), label
