"""Base classes and helpers used by every classification diagram template."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from ...plot_style import legend_columns


# ---------------------------------------------------------------------------
# Style dataclasses (filled in from the controls panel)
# ---------------------------------------------------------------------------

@dataclass
class AxisStyle:
    label: Optional[str] = None
    font_size: int = 12
    font_family: str = "DejaVu Sans"
    font_weight: str = "normal"   # "normal" or "bold"
    font_style: str = "normal"    # "normal" or "italic"

    def label_kwargs(self) -> dict:
        return dict(
            fontsize=self.font_size,
            fontfamily=self.font_family,
            fontweight=self.font_weight,
            fontstyle=self.font_style,
        )


@dataclass
class LegendStyle:
    visible: bool = True
    location: str = "best"
    font_size: int = 10
    title: Optional[str] = None


@dataclass
class PlotOptions:
    x_axis: AxisStyle = field(default_factory=AxisStyle)
    y_axis: AxisStyle = field(default_factory=AxisStyle)
    legend: LegendStyle = field(default_factory=LegendStyle)
    facet_by_group: bool = False
    shaded_ranges: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def resolve_column(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    if df is None:
        return None
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        actual = lookup.get(cand.lower())
        if actual is not None:
            return actual
    return None


#: Column names a dataset may give its own normative minerals.
NORMATIVE_NAMES: Dict[str, Tuple[str, ...]] = {
    "Q": ("Q", "Qz", "Quartz"),
    "Or": ("Or", "Orthoclase"),
    "Ab": ("Ab", "Albite"),
    "An": ("An", "Anorthite"),
    "Ne": ("Ne", "Nepheline"),
    "Lc": ("Lc", "Leucite"),
    "Kp": ("Kp", "Kaliophilite"),
}


def _brings_own_norm(df: pd.DataFrame, required: Sequence[str]) -> bool:
    return all(resolve_column(df, NORMATIVE_NAMES[m]) for m in required)


def normative(df: pd.DataFrame, required: Sequence[str],
              optional: Sequence[str] = ()) -> Optional[pd.DataFrame]:
    """The normative minerals a diagram plots, one column each (wt %).

    A norm the dataset brings -- columns named Q, Ab, An, ... -- is used
    as it stands when it has every *required* mineral; an *optional* one
    it lacks counts as 0.  Otherwise the CIPW norm is computed from the
    majors in *df*, as the Norm view computes it: the diagram needs no
    visit to that view, and follows the adjusted-majors switch.  The
    ``norm_*`` columns that view can write into the dataset are not
    read, since they keep whichever majors were in use when it ran.

    A row the norm cannot be computed for is NaN, so it is left off
    rather than drawn at a corner (:func:`birds.cipw.norm_gaps`).
    ``None`` when there are no majors to compute from either.
    """
    minerals = (*required, *optional)
    if _brings_own_norm(df, required):
        own = {m: resolve_column(df, NORMATIVE_NAMES[m]) for m in minerals}
        return pd.DataFrame(
            {m: (pd.to_numeric(df[own[m]], errors="coerce") if own[m]
                 else 0.0) for m in minerals}, index=df.index)
    if "SiO2" not in df.columns:
        return None
    from ...cipw import compute_cipw
    norm = compute_cipw(df)
    return pd.DataFrame({m: norm[f"norm_{m}"] for m in minerals},
                        index=df.index)


def normative_note(df: Optional[pd.DataFrame],
                   required: Sequence[str]) -> Optional[str]:
    """One sentence on the samples :func:`normative` leaves without a
    norm, and why; ``None`` when every sample has one."""
    if df is None or df.empty or _brings_own_norm(df, required):
        return None
    if "SiO2" not in df.columns:
        return ("No normative minerals: the dataset has neither its own "
                f"({', '.join(required)}) nor the majors to compute the "
                "CIPW norm from.")
    from ...cipw import norm_gaps
    gaps = norm_gaps(df)
    lacking = gaps[gaps != ""]
    if lacking.empty:
        return None
    n, total = len(lacking), len(df)
    head = (f"None of the {total} samples has a CIPW norm" if n == total
            else f"{n} of {total} samples {'has' if n == 1 else 'have'} "
                 f"no CIPW norm")
    tail = f"missing {lacking.value_counts().index[0]}"
    if lacking.nunique() > 1:
        tail += ", among other gaps"
    text = f"{head}: {tail}."
    if any("only as a total" in gap for gap in lacking.unique()):
        text += ("\nSplit the iron in Data → Pre-process majors… and use "
                 "the adjusted majors.")
    return text


def draw_note(ax, text: str) -> None:
    """Write *text* in the top-left corner of *ax*, where it says why
    samples are missing without hiding the ones that are drawn."""
    ax.text(0.01, 0.99, text, transform=ax.transAxes, ha="left", va="top",
            fontsize=8, color="#a02020", wrap=True, zorder=10,
            bbox=dict(facecolor="white", edgecolor="#a02020", alpha=0.92,
                      boxstyle="round,pad=0.3"))


#: Without a renderer to measure with, a legend this long is assumed to
#: cover something.
LEGEND_ENTRIES_OUTSIDE = 6


def _hides_field_names(ax, legend) -> bool:
    """Would *legend*, where it sits, cover any text drawn on *ax*?"""
    get_renderer = getattr(ax.figure.canvas, "get_renderer", None)
    if get_renderer is None:
        return len(legend.get_texts()) > LEGEND_ENTRIES_OUTSIDE
    renderer = get_renderer()
    box = legend.get_window_extent(renderer)
    for text in ax.texts:
        if text.get_text().strip() and text.get_visible() \
                and box.overlaps(text.get_window_extent(renderer)):
            return True
    return False


def get_groups(df: pd.DataFrame, plot_style) -> List[Tuple[str, pd.DataFrame, object]]:
    """Split *df* into (label, sub_df, GroupStyle) tuples.

    The order of ``plot_style.groups`` dictates the **draw order** of
    the result — earlier styles render first (behind), later styles on
    top — and the legend reads in the same order. The user controls
    this from the Edit-plot dialog (↑ / ↓ buttons).

    Matching of styles to data labels is done in two passes:

    1. **By name.**  Every ``GroupStyle`` whose ``name`` matches a
       unique value of the grouping column(s) claims that data label.
       This is the common case after the dialog's auto-populate step.
    2. **By position.**  Any remaining (un-named or renamed) styles
       pick up the leftover data labels in their order of first
       appearance.

    Extra data labels beyond the number of defined styles fall back to
    a cyclic style and use their raw data label as the legend entry.
    Groups marked ``visible=False`` are dropped silently.

    Up to three grouping columns are supported through
    ``PlotStyle.group_columns``.
    """
    if df is None or df.empty:
        return []
    cols = [c for c in getattr(plot_style, "group_columns", []) if c and c in df.columns]
    if not cols:
        gs = plot_style.groups[0] if plot_style.groups else None
        if gs is not None and not getattr(gs, "visible", True):
            return []
        label = gs.name if gs and gs.name.strip() else "All samples"
        return [(label, df, gs)]

    # Per-row label string from one or more grouping columns.
    if len(cols) == 1:
        labels = df[cols[0]].astype("string")
    else:
        labels = (
            df[cols].astype("string").fillna("NA")
            .agg(" | ".join, axis=1)
        )
    label_str = labels.astype(str).str.strip()

    # Unique data values, in order of first appearance.
    seen: list[str] = []
    for value in labels:
        if pd.isna(value):
            continue
        sv = str(value).strip()
        if sv and sv not in seen:
            seen.append(sv)

    n_styles = len(plot_style.groups)
    seen_set = set(seen)

    # Pass 1 — bind each style to a data label by exact name match.
    bindings: dict[int, str] = {}      # style index → data label
    claimed: set[str] = set()
    for i, gs in enumerate(plot_style.groups):
        name = gs.name.strip()
        if name and name in seen_set and name not in claimed:
            bindings[i] = name
            claimed.add(name)

    # Pass 2 — fill the unbound styles with the leftover data labels in
    # appearance order. This is what makes manually-renamed groups
    # still pick up data even when the name no longer matches.
    leftover_labels = [s for s in seen if s not in claimed]
    leftover_styles = [i for i in range(n_styles) if i not in bindings]
    for i, raw_label in zip(leftover_styles, leftover_labels):
        bindings[i] = raw_label
        claimed.add(raw_label)

    # Assemble the result in PlotStyle.groups order.
    result: List[Tuple[str, pd.DataFrame, object]] = []
    for i, gs in enumerate(plot_style.groups):
        raw_label = bindings.get(i)
        if raw_label is None:
            continue
        if not getattr(gs, "visible", True):
            continue
        sub = df[label_str == raw_label]
        if sub.empty:
            continue
        display_label = gs.name.strip() or raw_label
        result.append((display_label, sub, gs))

    # Pass 3 — data labels with no matching style (extras beyond N_styles)
    # reuse a style cyclically and keep the raw label.
    if n_styles > 0:
        extras = [s for s in seen if s not in claimed]
        for j, raw_label in enumerate(extras):
            gs = plot_style.groups[j % n_styles]
            if not getattr(gs, "visible", True):
                continue
            sub = df[label_str == raw_label]
            if sub.empty:
                continue
            result.append((raw_label, sub, gs))
    return result


def _should_shade(gs: object, options: "PlotOptions") -> bool:
    """Decide whether to draw a convex-hull background for *gs*.

    Per-group ``gs.shaded`` is the primary control. ``options.shaded_ranges``
    is kept as a legacy "shade everything" master toggle for callers that
    haven't been migrated to per-group flags yet.
    """
    if gs is not None and getattr(gs, "shaded", False):
        return True
    return bool(getattr(options, "shaded_ranges", False))


def inverse_logratio(x, y):
    """``(ln(B/A), ln(C/A))`` back to ternary ``(A, B, C)`` summing to 1.

    The softmax of ``(0, x, y)``, computed against the largest exponent
    so a boundary walked far from the triple point does not overflow.
    """
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    top = np.maximum(np.maximum(x, y), 0.0)
    ea, eb, ec = np.exp(-top), np.exp(x - top), np.exp(y - top)
    total = ea + eb + ec
    return ea / total, eb / total, ec / total


def ternary_to_xy(a: pd.Series, b: pd.Series, c: pd.Series
                  ) -> Tuple[pd.Series, pd.Series]:
    """Project ternary coordinates (apex A at top, B left, C right) into
    Cartesian (x, y). Inputs are renormalised to a + b + c = 1."""
    a = pd.to_numeric(a, errors="coerce")
    b = pd.to_numeric(b, errors="coerce")
    c = pd.to_numeric(c, errors="coerce")
    total = a + b + c
    a_n = a / total
    c_n = c / total
    x = 0.5 * (2 * c_n + a_n)
    y = (np.sqrt(3) / 2.0) * a_n
    return x, y


def draw_ternary_frame(ax, apex_labels: tuple[str, str, str],
                       axis_style: AxisStyle,
                       grid: bool = True) -> None:
    """Draw the outer triangle, optional 10 % grid and apex labels.

    apex_labels = (A_top, B_left, C_right).
    """
    A = (0.5, np.sqrt(3) / 2.0)
    B = (0.0, 0.0)
    C = (1.0, 0.0)
    ax.plot([A[0], B[0], C[0], A[0]], [A[1], B[1], C[1], A[1]],
            color="#333", linewidth=1.0)
    if grid:
        for f in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9):
            # lines parallel to BC (rows of constant A)
            x1, y1 = ternary_to_xy(pd.Series([1 - f]), pd.Series([f]), pd.Series([0]))
            x2, y2 = ternary_to_xy(pd.Series([1 - f]), pd.Series([0]), pd.Series([f]))
            ax.plot([x1.iloc[0], x2.iloc[0]], [y1.iloc[0], y2.iloc[0]],
                    color="#dcdcdc", linewidth=0.5, zorder=0)
            # lines parallel to AC (rows of constant B)
            x1, y1 = ternary_to_xy(pd.Series([f]), pd.Series([1 - f]), pd.Series([0]))
            x2, y2 = ternary_to_xy(pd.Series([0]), pd.Series([1 - f]), pd.Series([f]))
            ax.plot([x1.iloc[0], x2.iloc[0]], [y1.iloc[0], y2.iloc[0]],
                    color="#dcdcdc", linewidth=0.5, zorder=0)
            # lines parallel to AB (rows of constant C)
            x1, y1 = ternary_to_xy(pd.Series([f]), pd.Series([0]), pd.Series([1 - f]))
            x2, y2 = ternary_to_xy(pd.Series([0]), pd.Series([f]), pd.Series([1 - f]))
            ax.plot([x1.iloc[0], x2.iloc[0]], [y1.iloc[0], y2.iloc[0]],
                    color="#dcdcdc", linewidth=0.5, zorder=0)

    ax.text(A[0], A[1] + 0.04, apex_labels[0], ha="center", va="bottom",
            **axis_style.label_kwargs())
    ax.text(B[0] - 0.03, B[1] - 0.03, apex_labels[1], ha="right", va="top",
            **axis_style.label_kwargs())
    ax.text(C[0] + 0.03, C[1] - 0.03, apex_labels[2], ha="left", va="top",
            **axis_style.label_kwargs())
    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(-0.1, 1.0)
    ax.set_aspect("equal")
    ax.axis("off")


# ---------------------------------------------------------------------------
# Diagram base
# ---------------------------------------------------------------------------

class Diagram:
    """Base class for all classification diagrams."""

    key: str = ""
    title: str = ""
    citation: str = ""
    x_label: str = ""
    y_label: str = ""
    x_range: Optional[Tuple[float, float]] = None
    y_range: Optional[Tuple[float, float]] = None
    log_x: bool = False
    log_y: bool = False

    # Field polygons (name -> list of (x, y))
    field_polygons: dict = {}
    # Optional label positions overrides (name -> (x, y))
    field_label_pos: dict = {}
    field_label_fontsize: float = 7.5

    # ------------------------------------------------------------------ API
    def plot(self, figure: Figure, df: Optional[pd.DataFrame],
             plot_style, options: PlotOptions) -> None:
        figure.clear()
        ax = figure.add_subplot(111)
        self._draw_background(ax, options)
        self._draw_data(ax, df, plot_style, options)
        self._apply_axes(ax, options)
        self._apply_legend(ax, options)
        figure.tight_layout()

    # ----------------------------------------------------------- to override
    def _compute_xy(self, df: pd.DataFrame
                    ) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        """Return (x, y) numeric series ready to scatter."""
        return None, None

    def _draw_background(self, ax, options: PlotOptions) -> None:
        self._draw_fields(ax)

    # ----------------------------------------------------------------- impl
    def _draw_fields(self, ax) -> None:
        overrides = self.field_label_pos or {}
        for name, verts in self.field_polygons.items():
            poly = Polygon(verts, closed=True, fill=False,
                           edgecolor="#444", linewidth=0.9, alpha=0.9, zorder=1)
            ax.add_patch(poly)
            if name in overrides:
                px, py = overrides[name]
            else:
                px = sum(v[0] for v in verts) / len(verts)
                py = sum(v[1] for v in verts) / len(verts)
            ax.text(px, py, name, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#333",
                    alpha=0.95, zorder=2)

    def _draw_data(self, ax, df: Optional[pd.DataFrame], plot_style,
                   options: PlotOptions) -> None:
        if df is None or df.empty:
            return
        xs_all, ys_all = self._compute_xy(df)
        if xs_all is None or ys_all is None:
            return
        for label, sub, gs in get_groups(df, plot_style):
            # Master visibility switch — Grouping checkbox in the side
            # panel flips this.  When off, the group is dropped entirely
            # (no scatter, no hull, no legend entry).
            if gs is not None and not getattr(gs, "visible", True):
                continue
            xs, ys = self._compute_xy(sub)
            if xs is None or ys is None:
                continue
            mask = pd.Series(xs).notna() & pd.Series(ys).notna()
            xs = pd.Series(xs)[mask]
            ys = pd.Series(ys)[mask]
            if xs.empty:
                continue
            color = gs.color if gs else "#1f77b4"
            marker = gs.marker if gs else "o"
            show_markers = getattr(gs, "show_markers", True) if gs else True
            shade = _should_shade(gs, options)
            # If the user turned the symbols off we still want the group
            # to appear in the legend — let the hull fill carry the label
            # instead of the scatter.
            scatter_label = label if show_markers else None
            fill_label = label if (shade and not show_markers) else None
            if show_markers:
                ax.scatter(xs, ys,
                           s=(plot_style.point_size ** 2),
                           alpha=plot_style.alpha,
                           c=color, marker=marker,
                           label=scatter_label, edgecolors="black",
                           linewidths=0.4, zorder=4)
            if shade and len(xs) >= 3:
                try:
                    from scipy.spatial import ConvexHull
                    pts = np.column_stack([xs.to_numpy(), ys.to_numpy()])
                    hull = ConvexHull(pts)
                    hull_pts = pts[hull.vertices]
                    ax.fill(hull_pts[:, 0], hull_pts[:, 1],
                            color=color, alpha=0.18 if not show_markers else 0.12,
                            label=fill_label, zorder=3)
                except Exception:
                    pass

    @staticmethod
    def _mark_offframe(ax) -> None:
        """Flag, at the edge, every sample that plots outside the frame.

        Call once the limits are final.  A sample beyond them is drawn
        and then clipped, so without this it is simply absent, and the
        reader cannot tell an analysis the diagram does not cover from
        one that was never loaded.  The tally under the canvas counts
        them; this says which way they went.

        Only artists carrying a legend label are considered.  Templates
        label their sample scatter with the group name, while reference
        points -- the Sun & McDonough compositions on Pearce's diagrams,
        say -- are drawn unlabelled and come back from matplotlib as
        ``_child3``.  Marking one of those as a stray sample would be a
        worse lie than the silence this replaces.

        The marker is a hollow triangle pointing the way out, in the
        group's own colour, so it reads as a direction rather than as a
        datum sitting on the boundary.
        """
        import numpy as _np

        x_lo, x_hi = sorted(ax.get_xlim())
        y_lo, y_hi = sorted(ax.get_ylim())
        x_span = x_hi - x_lo
        y_span = y_hi - y_lo
        if not (_np.isfinite(x_span) and _np.isfinite(y_span)):
            return

        for collection in list(ax.collections):
            label = collection.get_label() or ""
            if label.startswith("_"):
                continue
            offsets = collection.get_offsets()
            if offsets is None or len(offsets) == 0:
                continue
            try:
                colour = collection.get_facecolor()[0]
            except (IndexError, TypeError):                 # pragma: no cover
                colour = "#444444"

            for x, y in _np.asarray(offsets, dtype=float):
                if not (_np.isfinite(x) and _np.isfinite(y)):
                    continue
                # +1 off the low edge, -1 off the high one, 0 inside.
                # int() first: numpy booleans refuse to be subtracted.
                over_x = int(x < x_lo) - int(x > x_hi)
                over_y = int(y < y_lo) - int(y > y_hi)
                if not (over_x or over_y):
                    continue
                # Which edge it left by, as a fraction of the span, so
                # the two axes are comparable whatever their units.
                out_x = (max(x_lo - x, x - x_hi) / x_span) if (
                    over_x and x_span > 0) else 0.0
                out_y = (max(y_lo - y, y - y_hi) / y_span) if (
                    over_y and y_span > 0) else 0.0
                if out_x >= out_y:
                    marker = "<" if over_x > 0 else ">"
                else:
                    marker = "v" if over_y > 0 else "^"
                ax.plot(min(max(x, x_lo), x_hi), min(max(y, y_lo), y_hi),
                        marker=marker, markersize=7,
                        markerfacecolor="none", markeredgecolor=colour,
                        markeredgewidth=1.4, linestyle="none",
                        clip_on=False, zorder=6, label="_offframe")

    def _apply_axes(self, ax, options: PlotOptions) -> None:
        x_label = options.x_axis.label or self.x_label
        y_label = options.y_axis.label or self.y_label
        ax.set_xlabel(x_label, **options.x_axis.label_kwargs())
        ax.set_ylabel(y_label, **options.y_axis.label_kwargs())
        tick_size = max(options.x_axis.font_size - 2, 6)
        for t in ax.get_xticklabels() + ax.get_yticklabels():
            t.set_fontsize(tick_size)
            t.set_fontfamily(options.x_axis.font_family)
        if self.x_range:
            ax.set_xlim(*self.x_range)
        if self.y_range:
            ax.set_ylim(*self.y_range)
        if self.log_x:
            ax.set_xscale("log")
        if self.log_y:
            ax.set_yscale("log")
        if self.x_range or self.y_range:
            # Only a fixed frame can leave a sample outside it; an
            # auto-scaled axis is built around the data by definition.
            self._mark_offframe(ax)

    def _apply_legend(self, ax, options: PlotOptions) -> None:
        if not options.legend.visible:
            return
        handles, labels = ax.get_legend_handles_labels()
        if not handles:
            return
        kwargs: dict = {"fontsize": options.legend.font_size,
                        "ncol": legend_columns(len(handles))}
        if options.legend.title:
            kwargs["title"] = options.legend.title
        outside = options.legend.location == "outside"
        if not outside:
            legend = ax.legend(loc=options.legend.location, **kwargs)
            # "best" only steers clear of the samples.  With many groups
            # the box grows over the field names, so the default moves
            # it out to the right instead; a place the user picked stays.
            if (options.legend.location == "best"
                    and _hides_field_names(ax, legend)):
                legend.remove()
                outside = True
        if outside:
            ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0),
                      borderaxespad=0.0, **kwargs)


# ---------------------------------------------------------------------------
# Ternary diagrams
# ---------------------------------------------------------------------------

def ternary_xy(abc) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
    """Where ``(apex, left, right)`` values put each sample on a triangle.

    NaN for a sample lacking any of the three or summing to nothing, so a
    caller can tell drawn from not; ``(None, None)`` when *abc* is
    ``None``, i.e. the columns are absent.
    """
    if abc is None:
        return None, None
    a, b, c = (pd.to_numeric(v, errors="coerce") for v in abc)
    placed = a.notna() & b.notna() & c.notna() & (a + b + c > 0)
    return ternary_to_xy(a.where(placed), b.where(placed), c.where(placed))


def scatter_groups(ax, df: Optional[pd.DataFrame], plot_style,
                   xy_fn) -> None:
    """Scatter each group of *df* where ``xy_fn(group)`` puts it,
    leaving off the samples it returns as NaN."""
    if df is None or df.empty:
        return
    for label, sub, gs in get_groups(df, plot_style):
        x, y = xy_fn(sub)
        if x is None or y is None:
            continue
        keep = x.notna() & y.notna()
        if not keep.any():
            continue
        ax.scatter(x[keep], y[keep], s=plot_style.point_size ** 2,
                   alpha=plot_style.alpha,
                   c=gs.color if gs else "#1f77b4",
                   marker=gs.marker if gs else "o",
                   label=label, edgecolors="black", linewidths=0.4,
                   zorder=4)


class TernaryDiagram(Diagram):
    """A triangle whose samples ``_abc`` places, as (apex, left, right).

    ``_compute_xy`` is derived from ``_abc`` here, once, so the plot,
    the sample tally, Identify-sample and brushing all read the same
    mapping.  Without it the tally fell back to counting every sample as
    plotted -- on a triangle that could be empty -- and a click on a
    point identified nothing.
    """

    def _abc(self, df: pd.DataFrame):
        raise NotImplementedError

    def _compute_xy(self, df: pd.DataFrame
                    ) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        return ternary_xy(self._abc(df))

    def _scatter_samples(self, ax, df: Optional[pd.DataFrame],
                         plot_style) -> None:
        scatter_groups(ax, df, plot_style, self._compute_xy)


# ---------------------------------------------------------------------------
# Compositional-data helpers (Verma-style log-ratio discriminant functions)
# ---------------------------------------------------------------------------

def _positive_numeric(series: pd.Series) -> pd.Series:
    """Coerce to numeric and mask non-positive values as NaN (log domain)."""
    s = pd.to_numeric(series, errors="coerce")
    return s.where(s > 0)


def build_logratios(df: pd.DataFrame, parts: Sequence[str],
                    denominator: str,
                    aliases: Optional[Dict[str, Iterable[str]]] = None,
                    scale: Optional[Dict[str, float]] = None
                    ) -> Optional[pd.DataFrame]:
    """Return a DataFrame of ``ln(part_i / denominator)`` for every part.

    Missing parts (or the denominator) cause the function to return
    ``None`` so the caller can short-circuit the plot with a friendly
    message. Zero/negative values are masked so the logarithm stays
    defined (Aitchison's positive simplex constraint).

    aliases maps a canonical part name to extra column names that should
    be accepted (e.g. ``"FeOt"`` → ``["FeO_T", "FeO*", "FeO(T)"]``).

    scale maps a canonical part name to a divisor applied before the
    ratio, for the case where a part and the denominator are reported
    in different units — a trace element in ppm over a major oxide in
    wt.%, say, which needs ``1e4``. A log-ratio of unlike units is off
    by ``ln(divisor)`` per term, which is a large constant, not a
    rounding difference.
    """
    if df is None or df.empty:
        return None
    al = aliases or {}
    cols: Dict[str, str] = {}
    for name in list(parts) + [denominator]:
        candidates = [name] + list(al.get(name, ()))
        actual = resolve_column(df, candidates)
        if actual is None:
            return None
        cols[name] = actual

    den = _positive_numeric(df[cols[denominator]])
    factors = scale or {}
    out = pd.DataFrame(index=df.index)
    for name in parts:
        num = _positive_numeric(df[cols[name]])
        divisor = factors.get(name)
        if divisor:
            num = num / divisor
        out[name] = np.log(num / den)
    return out


def missing_logratio_columns(df: pd.DataFrame, parts: Sequence[str],
                             denominator: str,
                             aliases: Optional[Dict[str, Iterable[str]]] = None
                             ) -> list[str]:
    """Return the canonical names of every part / denominator that is
    NOT present in *df* (after alias resolution).

    Used by the multi-panel diagrams (Verma DF sets, Frost, …) to write
    a "missing columns: …" diagnostic on a panel that would otherwise
    be silently empty.
    """
    names = list(parts) + ([denominator] if denominator else [])
    if df is None or df.empty:
        return names
    al = aliases or {}
    missing: list[str] = []
    for name in names:
        candidates = [name] + list(al.get(name, ()))
        if resolve_column(df, candidates) is None:
            missing.append(name)
    return missing


def feot_from_oxides(df: pd.DataFrame) -> Optional[pd.Series]:
    """Return total iron as FeO (FeOt).

    Thin compatibility wrapper around :func:`birds.preprocess.get_feot`,
    which is the single source of truth for the FeO/Fe₂O₃/FeOt alias
    table and the row-wise fallback logic.
    """
    from ...preprocess import get_feot
    return get_feot(df)


# ---------------------------------------------------------------------------
# Multi-panel diagram base (Verma DF sets, Frost et al. 4-panel, etc.)
# ---------------------------------------------------------------------------

@dataclass
class PanelSpec:
    """Specification for a single panel inside a multi-panel diagram."""
    key: str
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    x_range: Optional[Tuple[float, float]] = None
    y_range: Optional[Tuple[float, float]] = None
    log_x: bool = False
    log_y: bool = False
    horizontal_lines: Sequence[float] = ()
    vertical_lines: Sequence[float] = ()
    # Optional bespoke straight-line boundaries: list of (m, b, label_left, label_right)
    boundary_lines: Sequence[Tuple[float, float, str, str]] = ()
    # Optional polygonal fields keyed by name (verts already projected)
    field_polygons: Dict[str, Sequence[Tuple[float, float]]] = field(default_factory=dict)
    field_label_pos: Dict[str, Tuple[float, float]] = field(default_factory=dict)


class MultiPanelDiagram(Diagram):
    """Diagram that draws ``N`` sub-panels in a grid (rows × cols).

    Subclasses must:

    * fill ``panels`` (list of :class:`PanelSpec`) — at least one item;
    * implement :py:meth:`_compute_xy_for_panel` returning ``(xs, ys)``
      for a given panel key and DataFrame.

    The base implementation handles grid layout, legend (de-duplicated
    across panels), field polygons, and per-panel axis styling.
    """

    panels: Sequence[PanelSpec] = ()
    n_rows: int = 1
    n_cols: int = 1
    grid_figsize_hint: Tuple[float, float] = (10.0, 7.5)
    suptitle_fontsize: int = 13
    panel_title_fontsize: int = 10

    # ------------------------------------------------------------------ API
    def plot(self, figure: Figure, df: Optional[pd.DataFrame],
             plot_style, options: PlotOptions) -> None:
        figure.clear()
        if not self.panels:
            ax = figure.add_subplot(111)
            ax.text(0.5, 0.5, "No panels defined.", ha="center", va="center")
            ax.axis("off")
            return

        n = len(self.panels)
        rows = self.n_rows or 1
        cols = self.n_cols or n
        axes = []
        for i, spec in enumerate(self.panels):
            ax = figure.add_subplot(rows, cols, i + 1)
            self._draw_panel_background(ax, spec, options)
            self._draw_panel_data(ax, spec, df, plot_style, options)
            self._apply_panel_axes(ax, spec, options)
            if spec.title:
                ax.set_title(spec.title, fontsize=self.panel_title_fontsize)
            # If the panel ended up empty of scatter points (typically
            # because required columns are missing from the dataset),
            # ask the subclass for a diagnostic message and write it.
            msg = self._panel_diagnostic(spec, df, ax)
            if msg:
                ax.text(
                    0.5, 0.5, msg, transform=ax.transAxes,
                    ha="center", va="center", color="#a02020",
                    fontsize=9, fontweight="bold", wrap=True,
                    bbox=dict(facecolor="white", edgecolor="#a02020",
                              alpha=0.92, boxstyle="round,pad=0.4"),
                    zorder=10,
                )
            axes.append(ax)

        # Single shared legend: in the grid's spare cell when there is
        # one (Verma's five panels leave the sixth free), else below the
        # grid with room kept for it -- it used to hang below the figure,
        # over the last x labels and cut off at the canvas edge.
        spare = None
        if rows * cols > n:
            spare = figure.add_subplot(rows, cols, n + 1)
            spare.axis("off")
        reserve = self._apply_shared_legend(figure, axes, options, spare)
        if self.title:
            figure.suptitle(self.title, fontsize=self.suptitle_fontsize,
                            fontweight="bold")
        figure.tight_layout(rect=(0, reserve, 1, 1))

    # -------------------------------------------------- to override per diagram
    def _compute_xy_for_panel(self, panel: PanelSpec, df: pd.DataFrame
                              ) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        return None, None

    def _panel_diagnostic(self, panel: PanelSpec,
                          df: Optional[pd.DataFrame], ax) -> Optional[str]:
        """Return a human-readable explanation when a panel is empty.

        Default implementation: only fires when there's no data at all.
        Subclasses (e.g. ``_BinaryPairsDF``) override this to detect
        the much more common case of *missing columns* and tell the
        user exactly which ones are needed.
        """
        if df is None or df.empty:
            return "Load a dataset via Data → Import."
        # Has scatter / fill collections?
        try:
            has_data = any(
                getattr(c, "get_offsets", lambda: [])() is not None
                and len(c.get_offsets()) > 0
                for c in ax.collections
            )
        except Exception:
            has_data = True
        if has_data:
            return None
        return None  # Subclass should provide a more specific message.

    # ----------------------------------------------------------------- impl
    def _draw_panel_background(self, ax, panel: PanelSpec,
                               options: PlotOptions) -> None:
        # Polygonal fields
        for name, verts in panel.field_polygons.items():
            poly = Polygon(verts, closed=True, fill=False,
                           edgecolor="#444", linewidth=0.9, alpha=0.9, zorder=1)
            ax.add_patch(poly)
            if name in panel.field_label_pos:
                px, py = panel.field_label_pos[name]
            else:
                px = sum(v[0] for v in verts) / len(verts)
                py = sum(v[1] for v in verts) / len(verts)
            ax.text(px, py, name, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#333",
                    alpha=0.95, zorder=2)
        # Straight boundary lines
        for y in panel.horizontal_lines:
            ax.axhline(y, color="#444", linewidth=0.9, linestyle="--",
                       alpha=0.8, zorder=1)
        for x in panel.vertical_lines:
            ax.axvline(x, color="#444", linewidth=0.9, linestyle="--",
                       alpha=0.8, zorder=1)
        # The two label slots are part of the PanelSpec contract but are
        # not rendered yet, and no template populates boundary_lines
        # today — the Verma panels carry their own field geometry.
        for m, b, _lab_lo, _lab_hi in panel.boundary_lines:
            if panel.x_range is None:
                continue
            xs = np.linspace(panel.x_range[0], panel.x_range[1], 50)
            ys = m * xs + b
            ax.plot(xs, ys, color="#444", linewidth=0.9, linestyle="--",
                    alpha=0.8, zorder=1)

    def _draw_panel_data(self, ax, panel: PanelSpec,
                         df: Optional[pd.DataFrame],
                         plot_style, options: PlotOptions) -> None:
        if df is None or df.empty:
            return
        groups = get_groups(df, plot_style)
        for label, sub, gs in groups:
            xs, ys = self._compute_xy_for_panel(panel, sub)
            if xs is None or ys is None:
                continue
            mask = pd.Series(xs).notna() & pd.Series(ys).notna()
            xs = pd.Series(xs)[mask]
            ys = pd.Series(ys)[mask]
            if xs.empty:
                continue
            color = gs.color if gs else "#1f77b4"
            marker = gs.marker if gs else "o"
            show_markers = getattr(gs, "show_markers", True) if gs else True
            shade = _should_shade(gs, options)
            scatter_label = label if show_markers else None
            fill_label = label if (shade and not show_markers) else None
            if show_markers:
                ax.scatter(xs, ys,
                           s=(plot_style.point_size ** 2),
                           alpha=plot_style.alpha,
                           c=color, marker=marker,
                           label=scatter_label, edgecolors="black",
                           linewidths=0.4, zorder=4)
            if shade and len(xs) >= 3:
                try:
                    from scipy.spatial import ConvexHull
                    pts = np.column_stack([xs.to_numpy(), ys.to_numpy()])
                    hull = ConvexHull(pts)
                    hull_pts = pts[hull.vertices]
                    ax.fill(hull_pts[:, 0], hull_pts[:, 1],
                            color=color,
                            alpha=0.18 if not show_markers else 0.12,
                            label=fill_label, zorder=3)
                except Exception:
                    pass

    def _apply_panel_axes(self, ax, panel: PanelSpec,
                          options: PlotOptions) -> None:
        ax.set_xlabel(panel.x_label, fontsize=options.x_axis.font_size - 1)
        ax.set_ylabel(panel.y_label, fontsize=options.y_axis.font_size - 1)
        # The PanelSpec range is the canonical frame of the diagram (e.g.
        # (−8, +8) for Verma multidim DFs). Disable autoscale so samples
        # that fall outside it are clipped — matching the published
        # figures — instead of stretching the axes.
        if panel.x_range:
            ax.set_xlim(*panel.x_range)
            ax.set_autoscalex_on(False)
        if panel.y_range:
            ax.set_ylim(*panel.y_range)
            ax.set_autoscaley_on(False)
        if panel.log_x:
            ax.set_xscale("log")
        if panel.log_y:
            ax.set_yscale("log")
        for t in ax.get_xticklabels() + ax.get_yticklabels():
            t.set_fontsize(max(options.x_axis.font_size - 3, 6))
        ax.grid(True, which="major", linestyle=":", linewidth=0.4,
                color="#bcbcbc", alpha=0.7)
        if panel.x_range or panel.y_range:
            Diagram._mark_offframe(ax)

    def _apply_shared_legend(self, figure, axes, options: PlotOptions,
                             spare=None) -> float:
        """Draw the legend; return the fraction of the figure's height
        to keep free at the bottom for it (0 when it sits in *spare*)."""
        if not options.legend.visible:
            return 0.0
        handles, labels = [], []
        seen = set()
        for ax in axes:
            for handle, label in zip(*ax.get_legend_handles_labels()):
                if label in seen or label.startswith("_"):
                    continue
                seen.add(label)
                handles.append(handle)
                labels.append(label)
        if not handles:
            return 0.0
        if spare is not None:
            spare.legend(handles, labels, loc="center",
                         ncol=1 if len(labels) <= 10 else 2,
                         fontsize=options.legend.font_size, frameon=True)
            return 0.0
        ncol = min(len(labels), 6)
        legend_rows = -(-len(labels) // ncol)
        figure.legend(handles, labels, loc="lower center", ncol=ncol,
                      fontsize=options.legend.font_size,
                      bbox_to_anchor=(0.5, 0.0))
        return min(0.3, 0.02 + 0.04 * legend_rows)
