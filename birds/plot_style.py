"""Shared plot-style configuration consumed by every diagram view."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


DEFAULT_COLORS = (
    "#1f77b4",  # blue
    "#d62728",  # red
    "#2ca02c",  # green
    "#ff7f0e",  # orange
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#17becf",  # cyan
    "#bcbd22",  # olive
    "#7f7f7f",  # grey
)

DEFAULT_MARKERS = (
    "o",  # circle
    "s",  # square
    "^",  # triangle up
    "D",  # diamond
    "v",  # triangle down
    "*",  # star
    "P",  # plus
    "X",  # cross
    "p",  # pentagon
    "h",  # hexagon
)


@dataclass
class GroupStyle:
    """Visual style for one logical group of samples.

    Attributes
    ----------
    name, color, marker
        Display properties used by every plot in B.I.R.D.S.
    visible
        Master switch. When ``False``, the group is dropped entirely
        before plotting (no markers, no hull, no legend entry). Lets
        the user mute outliers / standards / reference samples without
        altering the dataset.
    show_markers
        When ``True`` (default), the individual sample points are
        scattered with ``marker`` and ``color``. Turn off to show only
        the convex-hull envelope (set ``shaded=True`` too).
    shaded
        When ``True``, a translucent convex hull is drawn around the
        group's points. Independent of ``show_markers``, so the four
        combinations are:

        * ☑ markers ☐ hull  → just the symbols (default)
        * ☑ markers ☑ hull  → symbols + envelope
        * ☐ markers ☑ hull  → only the envelope (e.g. background field)
        * ☐ markers ☐ hull  → group is muted but kept in legend memory
    """

    name: str
    color: str = "#1f77b4"
    marker: str = "o"
    visible: bool = True
    show_markers: bool = True
    shaded: bool = False


@dataclass
class PlotStyle:
    """Aggregate styling state held by the main window.

    ``group_columns`` may contain up to three column names. The groups are
    defined by the unique combinations of values found in those columns.
    """

    point_size: float = 8.0
    alpha: float = 0.85
    group_columns: List[str] = field(default_factory=list)
    groups: List[GroupStyle] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.groups:
            self.groups = [
                GroupStyle(
                    name=f"Group {i + 1}",
                    color=DEFAULT_COLORS[i % len(DEFAULT_COLORS)],
                    marker=DEFAULT_MARKERS[i % len(DEFAULT_MARKERS)],
                )
                for i in range(2)
            ]

    @property
    def n_groups(self) -> int:
        return len(self.groups)

    @property
    def group_column(self) -> str:
        """Backward-compat: first selected grouping column or empty string."""
        return self.group_columns[0] if self.group_columns else ""

    # ------------------------------------------------------------------
    # Session serialization
    # ------------------------------------------------------------------
    def to_dict(self) -> dict:
        """Return a JSON-safe representation of the plot style."""
        return {
            "point_size": self.point_size,
            "alpha": self.alpha,
            "group_columns": list(self.group_columns),
            "groups": [
                {
                    "name": g.name,
                    "color": g.color,
                    "marker": g.marker,
                    "visible": g.visible,
                    "show_markers": g.show_markers,
                    "shaded": g.shaded,
                }
                for g in self.groups
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlotStyle":
        """Rebuild a PlotStyle from :meth:`to_dict` output."""
        groups = [
            GroupStyle(
                name=g.get("name", f"Group {i + 1}"),
                color=g.get("color", DEFAULT_COLORS[i % len(DEFAULT_COLORS)]),
                marker=g.get("marker", DEFAULT_MARKERS[i % len(DEFAULT_MARKERS)]),
                visible=g.get("visible", True),
                show_markers=g.get("show_markers", True),
                shaded=g.get("shaded", False),
            )
            for i, g in enumerate(data.get("groups", []))
        ]
        style = cls(
            point_size=float(data.get("point_size", 8.0)),
            alpha=float(data.get("alpha", 0.85)),
            group_columns=list(data.get("group_columns", [])),
            groups=groups,
        )
        return style

    def copy_from(self, other: "PlotStyle") -> None:
        """Replace this style's contents IN-PLACE with values from *other*.

        Used by ``MainWindow.load_session`` so every view's reference to
        the shared PlotStyle object stays valid — we mutate the existing
        instance instead of swapping the binding.
        """
        self.point_size = other.point_size
        self.alpha = other.alpha
        self.group_columns = list(other.group_columns)
        self.groups = [
            GroupStyle(
                name=g.name, color=g.color, marker=g.marker,
                visible=g.visible, show_markers=g.show_markers, shaded=g.shaded,
            )
            for g in other.groups
        ]
