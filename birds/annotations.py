"""User-placed annotations for the Bivariate view.

Four annotation kinds:

* ``LineAnnotation``   — a straight line from (x1, y1) to (x2, y2)
* ``ArrowAnnotation``  — an arrow from tail (x1, y1) to head (x2, y2),
                         optional label at the head
* ``TextAnnotation``   — free-floating text at (x, y)
* ``SampleAnnotation`` — the ``Sample_Name`` of the data point nearest
                         (x, y), rendered as a label with a thin leader

Each subclass implements ``draw(ax)`` so the bivariate view can replay
the whole list on every plot redraw, and ``to_dict()`` / ``from_dict()``
for session round-trip.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import numpy as np


_KIND_REGISTRY: Dict[str, type] = {}


def _register(cls):
    _KIND_REGISTRY[cls.kind] = cls
    return cls


@dataclass
class _BaseAnnotation:
    """Common style fields.  ``kind`` is set by each subclass and used
    by the registry to round-trip via JSON."""
    kind: str = "base"
    color: str = "#222222"
    linewidth: float = 1.4

    def draw(self, ax) -> None:  # pragma: no cover - overridden
        raise NotImplementedError

    def hit_distance(self, x: float, y: float) -> float:
        """Distance from (x, y) to the annotation, in data units.  Used
        for right-click delete (smallest distance wins)."""
        return float("inf")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@_register
@dataclass
class LineAnnotation(_BaseAnnotation):
    kind: str = "line"
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 1.0
    y2: float = 1.0
    linestyle: str = "-"

    def draw(self, ax) -> None:
        ax.plot([self.x1, self.x2], [self.y1, self.y2],
                color=self.color, linewidth=self.linewidth,
                linestyle=self.linestyle, zorder=6,
                solid_capstyle="round")

    def hit_distance(self, x: float, y: float) -> float:
        # Perpendicular distance from (x, y) to the line segment.
        px, py = x - self.x1, y - self.y1
        dx, dy = self.x2 - self.x1, self.y2 - self.y1
        length2 = dx * dx + dy * dy
        if length2 < 1e-12:
            return float(np.hypot(px, py))
        t = max(0.0, min(1.0, (px * dx + py * dy) / length2))
        cx, cy = self.x1 + t * dx, self.y1 + t * dy
        return float(np.hypot(x - cx, y - cy))


@_register
@dataclass
class ArrowAnnotation(_BaseAnnotation):
    kind: str = "arrow"
    x1: float = 0.0
    y1: float = 0.0
    x2: float = 1.0
    y2: float = 1.0
    label: str = ""

    def draw(self, ax) -> None:
        ax.annotate(
            self.label, xy=(self.x2, self.y2), xytext=(self.x1, self.y1),
            arrowprops=dict(arrowstyle="->", color=self.color,
                            linewidth=self.linewidth, shrinkA=0, shrinkB=2),
            fontsize=10, color=self.color, ha="left", va="bottom",
            zorder=6,
        )

    def hit_distance(self, x: float, y: float) -> float:
        # Treat the arrow body as a line segment for hit-testing.
        return LineAnnotation.hit_distance(self, x, y)  # type: ignore


@_register
@dataclass
class TextAnnotation(_BaseAnnotation):
    kind: str = "text"
    x: float = 0.0
    y: float = 0.0
    text: str = ""
    fontsize: float = 10.0
    bbox: bool = True

    def draw(self, ax) -> None:
        kwargs = dict(fontsize=self.fontsize, color=self.color,
                      ha="left", va="bottom", zorder=6)
        if self.bbox:
            kwargs["bbox"] = dict(facecolor="white", edgecolor="#888",
                                   alpha=0.85, pad=2,
                                   boxstyle="round,pad=0.25")
        ax.text(self.x, self.y, self.text, **kwargs)

    def hit_distance(self, x: float, y: float) -> float:
        return float(np.hypot(x - self.x, y - self.y))


@_register
@dataclass
class SampleAnnotation(_BaseAnnotation):
    """Label a specific data row by its ``Sample_Name`` (or whatever the
    BivariateView passes as ``label``).  The arrow head sits at the
    sample's data coordinates (px, py); the text floats slightly above-
    right by ``dx``/``dy`` so the marker stays visible.
    """
    kind: str = "sample"
    px: float = 0.0      # data point coordinates (arrow head)
    py: float = 0.0
    dx: float = 0.0      # offset of the text label from (px, py)
    dy: float = 0.0
    label: str = ""

    def draw(self, ax) -> None:
        tx, ty = self.px + self.dx, self.py + self.dy
        ax.annotate(
            self.label, xy=(self.px, self.py), xytext=(tx, ty),
            arrowprops=dict(arrowstyle="-", color=self.color,
                            linewidth=0.6, alpha=0.7),
            fontsize=9, color=self.color, zorder=6,
            ha="left", va="bottom",
            bbox=dict(facecolor="white", edgecolor=self.color,
                       linewidth=0.6, alpha=0.85, pad=1.5,
                       boxstyle="round,pad=0.2"),
        )

    def hit_distance(self, x: float, y: float) -> float:
        return float(np.hypot(x - self.px, y - self.py))


# ---------------------------------------------------------------------------
# Helpers — list-level operations the GUI uses.
# ---------------------------------------------------------------------------

def draw_all(ax, annotations: List[_BaseAnnotation]) -> None:
    """Replay every annotation onto *ax*.  Called at the end of every
    plot() so annotations survive a redraw."""
    for ann in annotations:
        try:
            ann.draw(ax)
        except Exception:                                  # noqa: BLE001
            # An annotation with bogus data shouldn't break the whole
            # plot; just skip it.
            continue


def closest(annotations: List[_BaseAnnotation], x: float, y: float,
            max_distance: float) -> Optional[int]:
    """Return the index of the annotation closest to (x, y), or None if
    nothing falls within *max_distance* data units."""
    best_i, best_d = None, max_distance
    for i, ann in enumerate(annotations):
        d = ann.hit_distance(x, y)
        if d < best_d:
            best_i, best_d = i, d
    return best_i


def serialize(annotations: List[_BaseAnnotation]) -> List[Dict[str, Any]]:
    """JSON-safe list for session save."""
    return [ann.to_dict() for ann in annotations]


def deserialize(data: List[Dict[str, Any]]) -> List[_BaseAnnotation]:
    """Rebuild typed annotations from a serialised list."""
    out: List[_BaseAnnotation] = []
    if not data:
        return out
    for entry in data:
        if not isinstance(entry, dict):
            continue
        kind = entry.get("kind")
        cls = _KIND_REGISTRY.get(kind)
        if cls is None:
            continue
        # Drop unknown keys defensively so a future-version session
        # opened by an older B.I.R.D.S still loads what it can.
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in entry.items() if k in valid_keys}
        try:
            out.append(cls(**filtered))
        except Exception:                                  # noqa: BLE001
            continue
    return out
