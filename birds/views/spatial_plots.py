"""Drawing the Map view's spatial analysis on plain matplotlib axes.

Surfaces, variograms and cross-validation plots, the summary that goes
under them, and the grid files a GIS reads.  Nothing here touches Qt,
so all of it is tested on a bare ``Figure`` and a temporary folder.

Every group kriged on its own shares one colour scale -- the same
variable in the same units -- or the colours would not compare between
groups, which is the point of putting them on one map.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from matplotlib.colors import LogNorm, Normalize
from matplotlib.ticker import (
    FuncFormatter,
    LogLocator,
    MaxNLocator,
    NullFormatter,
)

from ..plot_style import legend_columns
from ..geostats import RELIABLE_N, Grid, hull_mask, write_esri_ascii

#: Colours for the two surfaces.  Uncertainty runs the other way round
#: so that "worse" reads as darker.
ESTIMATE_CMAP = "viridis"
UNCERTAINTY_CMAP = "magma_r"

#: A kriging matrix this ill-conditioned gives weights worth doubting.
ILL_CONDITIONED = 1e10

_FALLBACK_COLOURS = ("#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e",
                     "#8c564b", "#e377c2", "#17becf")


def group_colour(style, index: int) -> str:
    colour = getattr(style, "color", None)
    return colour or _FALLBACK_COLOURS[index % len(_FALLBACK_COLOURS)]


def kriged_name(variable: str, transform: str) -> str:
    """What was actually kriged: ln(Cu), or Cu itself."""
    return f"ln({variable})" if transform == "log" else variable


# ---------------------------------------------------------------------------
# Surfaces
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SurfaceLayer:
    """One group's kriged surface on the shared grid; NaN where masked."""

    label: str
    estimate: np.ndarray
    sd: np.ndarray
    lower: np.ndarray
    upper: np.ndarray


def surface_layers(results, grid: Grid, *, clip: bool = True,
                   buffer_km: float = 0.0):
    """Predict every analysed group on *grid*.

    Returns ``(layers, overlaps)``.  With *clip*, each group's surface is
    cut to its own samples' hull -- plus *buffer_km* -- since outside it
    kriging only extrapolates.  *overlaps* lists the pairs of groups
    whose clipped surfaces share cells: the later one is drawn on top,
    and the user needs to be told so.
    """
    glon, glat = grid.mesh()
    layers, masks = [], []
    for r in results:
        a = r.analysis
        if a is None:
            continue
        p = a.predict(glon, glat)
        if clip:
            mask = hull_mask(a.lon, a.lat, glon, glat, buffer_km=buffer_km)
        else:
            mask = np.ones(glon.shape, dtype=bool)

        def cut(v, _m=mask):
            return np.where(_m, v, np.nan)

        layers.append(SurfaceLayer(r.label, cut(p.estimate), cut(p.sd),
                                   cut(p.lower), cut(p.upper)))
        masks.append(mask)
    overlaps = [(layers[i].label, layers[j].label)
                for i in range(len(layers)) for j in range(i + 1, len(layers))
                if np.any(masks[i] & masks[j])]
    return layers, overlaps


def _edges(grid: Grid):
    lon = grid.west + np.arange(grid.ncols + 1) * grid.cell_deg
    lat = grid.south + np.arange(grid.nrows + 1) * grid.cell_deg
    return lon, lat


def surface_norm(layers, *, which: str, transform: str):
    """One colour scale for every layer, or None if nothing is finite.

    Logarithmic for an estimate kriged in logarithms, where values run
    over orders of magnitude; linear otherwise.
    """
    finite = [v[np.isfinite(v)] for v in
              (getattr(layer, which) for layer in layers)]
    finite = [f for f in finite if f.size]
    if not finite:
        return None
    allv = np.concatenate(finite)
    lo, hi = float(allv.min()), float(allv.max())
    if hi <= lo:
        hi = lo + (abs(lo) or 1.0) * 1e-6
    if which == "estimate" and transform == "log" and lo > 0:
        return LogNorm(vmin=lo, vmax=hi)
    return Normalize(vmin=lo, vmax=hi)


def draw_surface(ax, layers, grid: Grid, *, which: str = "estimate",
                 transform: str = "log", contours: bool = False):
    """Draw *which* ("estimate" or "sd") for every layer; return the mesh.

    The returned artist carries the shared norm, ready for a colorbar.
    """
    norm = surface_norm(layers, which=which, transform=transform)
    if norm is None:
        return None
    cmap = ESTIMATE_CMAP if which == "estimate" else UNCERTAINTY_CMAP
    lon_e, lat_e = _edges(grid)
    mesh = None
    for layer in layers:
        values = np.ma.masked_invalid(getattr(layer, which))
        mesh = ax.pcolormesh(lon_e, lat_e, values, cmap=cmap, norm=norm,
                             shading="flat", zorder=1)
        if contours and which == "estimate" and values.count() > 3:
            if isinstance(norm, LogNorm):
                levels = LogLocator(subs=(1.0, 2.0, 5.0)).tick_values(
                    norm.vmin, norm.vmax)
            else:
                levels = MaxNLocator(8).tick_values(norm.vmin, norm.vmax)
            levels = [lv for lv in levels if norm.vmin < lv < norm.vmax]
            if levels:
                cs = ax.contour(grid.lon_centres, grid.lat_centres, values,
                                levels=levels, colors="black",
                                linewidths=0.5, alpha=0.7, zorder=2)
                ax.clabel(cs, fmt="%g", fontsize=7)
    return mesh


def attach_colorbar(ax, mappable, label: str):
    """A colorbar exactly as tall as *ax*, just right of it.

    A map's axes keep their aspect, so they rarely fill the height the
    figure gives them; a colorbar stolen from the figure in the usual
    way then runs well past the map at both ends.  As an inset of the
    axes it follows their box, whatever shape it settles to.
    """
    cax = ax.inset_axes([1.03, 0.0, 0.035, 1.0])
    cbar = ax.figure.colorbar(mappable, cax=cax)
    if isinstance(mappable.norm, LogNorm):
        plain_log_ticks(cbar.ax.yaxis)
    cbar.set_label(label, fontsize=9)
    cbar.ax.tick_params(labelsize=8)
    return cbar


def plain_log_ticks(axis) -> None:
    """Ticks at 1, 2, 5 × 10ⁿ on a log axis, labelled 20 or 0.5.

    Concentrations kriged in logarithms rarely span more than a decade
    or two over a field area, and matplotlib's default then labels a
    single 10¹ and leaves the rest of the bar unread.  Over a wider span
    only the powers of ten are kept, or the labels would collide.  Call
    it once the axis has its limits.
    """
    lo, hi = sorted(axis.get_view_interval())
    wide = lo > 0 and hi / lo > 10 ** 2.5
    axis.set_major_locator(LogLocator(subs=(1.0,) if wide
                                      else (1.0, 2.0, 5.0)))
    axis.set_major_formatter(FuncFormatter(lambda v, _pos: f"{v:g}"))
    axis.set_minor_formatter(NullFormatter())


def surface_label(variable: str, *, which: str, transform: str) -> str:
    """The colorbar's caption."""
    if which == "estimate":
        return (f"{variable} — median estimate" if transform == "log"
                else f"{variable} — kriged estimate")
    if transform == "log":
        return f"Kriging SD of ln({variable})  (0.1 ≈ ±10 %)"
    return f"Kriging SD of {variable}"


# ---------------------------------------------------------------------------
# Variogram
# ---------------------------------------------------------------------------

def draw_variogram(ax, results, styles, *, variable: str,
                   transform: str) -> None:
    """Experimental points, sized by their pairs, and the fitted model.

    With one group the sample variance and the range are marked too,
    and each point carries its pair count; with several that would be a
    thicket, so the legend does the work instead.
    """
    analysed = [r for r in results if r.analysis is not None]
    single = len(analysed) == 1
    top_x = 0.0
    top_y = 0.0
    for i, r in enumerate(analysed):
        a = r.analysis
        emp = a.variogram
        colour = group_colour(styles.get(r.label), i)
        sizes = 18 + 70 * emp.pairs / emp.pairs.max()
        ax.scatter(emp.lag_km, emp.gamma, s=sizes, color=colour,
                   edgecolors="black", linewidths=0.4, zorder=3,
                   label=f"{r.label}  ({a.model.kind})")
        h = np.linspace(emp.max_lag_km / 400.0, emp.max_lag_km, 300)
        ax.plot(h, a.model(h), color=colour, linewidth=1.6, zorder=2)
        top_x = max(top_x, emp.max_lag_km)
        top_y = max(top_y, float(emp.gamma.max()), a.model.sill,
                    emp.variance)
        if single:
            ax.axhline(emp.variance, linestyle=":", color="#777",
                       linewidth=1.0, zorder=1, label="sample variance")
            if a.model.range_km <= emp.max_lag_km:
                ax.axvline(a.model.range_km, linestyle="--", color="#999",
                           linewidth=0.8, zorder=1)
                ax.annotate(f"range {a.model.range_km:.3g} km",
                            (a.model.range_km, 0), xytext=(4, 4),
                            textcoords="offset points", fontsize=8,
                            color="#555")
            for x, y, n in zip(emp.lag_km, emp.gamma, emp.pairs):
                ax.annotate(str(int(n)), (x, y), xytext=(0, 7),
                            textcoords="offset points", ha="center",
                            fontsize=7, color="#555")
    ax.set_xlim(0, top_x * 1.02 if top_x else 1.0)
    ax.set_ylim(0, top_y * 1.12 if top_y else 1.0)
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel(f"Semivariance of {kriged_name(variable, transform)}")
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)
    if analysed:
        ax.legend(fontsize=8, loc="lower right", framealpha=0.85,
                  ncol=legend_columns(len(ax.get_legend_handles_labels()[0])))


# ---------------------------------------------------------------------------
# Cross-validation
# ---------------------------------------------------------------------------

def draw_cross_validation(ax, results, styles, *, variable: str,
                          transform: str) -> None:
    """Each sample against its prediction from all the others.

    Under "log" both are back-transformed and drawn on logarithmic axes,
    so the plot reads in the data's own units while staying the
    comparison that was actually made.
    """
    analysed = [r for r in results if r.analysis is not None]
    lo, hi = np.inf, -np.inf
    for i, r in enumerate(analysed):
        cv = r.analysis.cross_validation
        obs, pred = cv.observed, cv.predicted
        if transform == "log":
            obs, pred = np.exp(obs), np.exp(pred)
        colour = group_colour(styles.get(r.label), i)
        ax.scatter(obs, pred, s=26, color=colour, edgecolors="black",
                   linewidths=0.4, zorder=3,
                   label=f"{r.label}  (skill {cv.skill:.2f})")
        lo = min(lo, float(np.min(obs)), float(np.min(pred)))
        hi = max(hi, float(np.max(obs)), float(np.max(pred)))
    if not analysed:
        return
    if transform == "log":
        ax.set_xscale("log")
        ax.set_yscale("log")
        pad = (hi / lo) ** 0.05
        lo, hi = lo / pad, hi * pad
    else:
        pad = 0.05 * (hi - lo or 1.0)
        lo, hi = lo - pad, hi + pad
    ax.plot([lo, hi], [lo, hi], color="#555", linewidth=0.9,
            linestyle="--", zorder=1, label="1 : 1")
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    if transform == "log":
        plain_log_ticks(ax.xaxis)
        plain_log_ticks(ax.yaxis)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(f"Observed {variable}")
    ax.set_ylabel(f"{variable} predicted from the other samples")
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)
    ax.legend(fontsize=8, loc="upper left", framealpha=0.85,
              ncol=legend_columns(len(ax.get_legend_handles_labels()[0])))


# ---------------------------------------------------------------------------
# The summary under the plot
# ---------------------------------------------------------------------------

def _fmt(x: float) -> str:
    return f"{x:.3g}"


def _fmt_nugget(model, digits: int = 3) -> str:
    """The nugget, as 0 when the fit left only round-off (1e-22, say)."""
    nugget = model.nugget if model.nugget > 1e-9 * model.sill else 0.0
    return f"{nugget:.{digits}g}"


def summary_html(results, *, variable: str, transform: str,
                 overlaps=(), manual_labels=()) -> str:
    """A compact table per group, and plain sentences for what to doubt."""
    kn = html.escape(kriged_name(variable, transform))
    rows, notes = [], []
    for r in results:
        label = html.escape(r.label)
        if r.analysis is None:
            rows.append(f"<tr><td><b>{label}</b></td>"
                        f"<td colspan='6'><i>not kriged — "
                        f"{html.escape(r.error or '')}</i></td></tr>")
            continue
        a = r.analysis
        cv = a.cross_validation
        m = a.model
        by_hand = " (by hand)" if r.label in manual_labels else ""
        used = f"{a.n} of {r.n_input}"
        rows.append(
            f"<tr><td><b>{label}</b></td><td>{used}</td>"
            f"<td>{m.kind}{by_hand}</td>"
            f"<td>{_fmt_nugget(m)} / {_fmt(m.sill)} / "
            f"{_fmt(m.range_km)} km</td>"
            f"<td><b>{cv.skill:.2f}</b></td><td>{_fmt(cv.rmse)}</td>"
            f"<td>{cv.mean_squared_standardized_error:.2f}</td></tr>")
        if a.n_excluded:
            why = ("missing a coordinate or the value, or at or below "
                   "zero and so not loggable" if transform == "log"
                   else "missing a coordinate or the value")
            notes.append(f"{label}: {a.n_excluded} sample(s) left out — "
                         f"{why}.")
        if a.n_folded:
            notes.append(f"{label}: {a.n_folded} sample(s) shared a "
                         f"location with another and were averaged into "
                         f"it.")
        if a.n < RELIABLE_N:
            notes.append(f"{label}: {html.escape(a.reliability)}")
        if not a.fit.converged or "upper bound" in a.fit.message:
            notes.append(f"{label}: {html.escape(a.fit.message)}")
        if a.kriging.condition > ILL_CONDITIONED:
            notes.append(f"{label}: the kriging system is ill-conditioned "
                         f"(condition {a.kriging.condition:.1e}) — a "
                         f"Gaussian model without a nugget usually is. "
                         f"Add a small nugget.")
    for first, second in overlaps:
        notes.append(f"The surfaces of {html.escape(first)} and "
                     f"{html.escape(second)} overlap; {html.escape(second)} "
                     f"is drawn on top. Hide a group in Edit plot to see "
                     f"the other.")
    head = ("<tr><th>Group</th><th>Samples</th><th>Model</th>"
            "<th>Nugget / sill / range</th><th>Skill</th>"
            "<th>RMSE</th><th>MSSE</th></tr>")
    table = (f"<table cellspacing='0' cellpadding='3'>{head}"
             f"{''.join(rows)}</table>")
    legend = (f"<p style='color:#5b6478'>Kriged: {kn}. Nugget, sill and "
              f"RMSE in its units. <b>Skill</b>: share of the error of "
              f"guessing the mean that kriging removes, from leave-one-out "
              f"cross-validation — near 0 or below, the spatial model adds "
              f"nothing. <b>MSSE</b>: mean squared standardised error, "
              f"about 1 when the kriging variance is honest.</p>")
    body = "".join(f"<li>{n}</li>" for n in notes)
    return table + legend + (f"<ul>{body}</ul>" if notes else "")


# ---------------------------------------------------------------------------
# Grids for a GIS
# ---------------------------------------------------------------------------

def safe_file_name(text: str) -> str:
    """*text* cut down to letters, digits, '-' and '_' for a file name."""
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", str(text)).strip("_")
    return cleaned or "grid"


def write_kriged_grids(path, results, grid: Grid, *, variable: str,
                       transform: str, clip: bool = True,
                       buffer_km: float = 0.0, manual_labels=(),
                       nodata: float = -9999.0) -> list:
    """Write every kriged group as ESRI ASCII grids; return the files.

    For each analysed group ``<stem>_<group>.asc`` holds the estimate in
    the data's units -- the median, under "log" -- and
    ``<stem>_<group>_sd.asc`` the kriging standard deviation of what was
    kriged; with a single surface the group is left out of the names.
    Every grid gets a ``.prj``.  ``<stem>.txt`` says what the grids hold
    and how they were made, since a grid file carries only numbers.
    """
    from .. import __version__

    path = Path(path)
    if path.suffix.lower() != ".asc":
        path = path.with_name(path.name + ".asc")
    stem = path.with_suffix("")
    layers, _overlaps = surface_layers(results, grid, clip=clip,
                                       buffer_km=buffer_km)
    by_label = {r.label: r for r in results}
    kn = kriged_name(variable, transform)
    written, described, taken = [], [], set()
    for layer in layers:
        name = stem.name + ("" if len(layers) == 1
                            else "_" + safe_file_name(layer.label))
        base, k = name, 2
        while name in taken:
            name, k = f"{base}_{k}", k + 1
        taken.add(name)
        est = write_esri_ascii(stem.with_name(name + ".asc"), grid,
                               layer.estimate, nodata=nodata)
        sd = write_esri_ascii(stem.with_name(name + "_sd.asc"), grid,
                              layer.sd, nodata=nodata)
        written += [est, est.with_suffix(".prj"), sd, sd.with_suffix(".prj")]
        a = by_label[layer.label].analysis
        m, cv = a.model, a.cross_validation
        by_hand = " (set by hand)" if layer.label in manual_labels else ""
        described.append(
            f"  {layer.label}: {est.name}, {sd.name}\n"
            f"      {a.n} of {by_label[layer.label].n_input} samples; "
            f"{m.kind} model{by_hand}, nugget {_fmt_nugget(m, 6)}, "
            f"sill {m.sill:.6g}, range {m.range_km:.6g} km\n"
            f"      leave-one-out skill {cv.skill:.3f}, "
            f"RMSE {cv.rmse:.4g}, MSSE "
            f"{cv.mean_squared_standardized_error:.3f}")
    skipped = [f"  {r.label}: {r.error}" for r in results
               if r.analysis is None]

    if transform == "log":
        estimate = (f"the median, exp of the kriged ln({variable}), in "
                    f"the units of {variable}")
        spread = (f"kriging standard deviation of ln({variable}) "
                  f"(0.1 is about ±10 %)")
    else:
        estimate = f"the kriged {variable}, in its units"
        spread = f"kriging standard deviation of {variable}, in its units"
    if clip:
        blank = ("outside the group's sample hull"
                 + (f" plus {buffer_km:g} km" if buffer_km > 0 else ""))
    else:
        blank = "not predicted"
    text = [
        "B.I.R.D.S kriged grids",
        f"Written {datetime.now():%Y-%m-%d %H:%M} by B.I.R.D.S "
        f"{__version__}",
        "",
        f"Variable:   {variable}",
        f"Kriged:     {kn}, by ordinary kriging",
        f"Estimate:   {estimate}",
        f"_sd grids:  {spread}",
        "Grid:       WGS-84 geographic coordinates in degrees (EPSG:4326),",
        f"            {grid.ncols} x {grid.nrows} cells of "
        f"{grid.cell_deg:.6g} degrees; lower-left corner "
        f"{grid.west:.6f}, {grid.south:.6f}",
        f"No data:    {nodata:g}, {blank}",
        "",
        "Kriged",
        *described,
    ]
    if skipped:
        text += ["", "Not kriged", *skipped]
    meta = stem.with_name(stem.name + ".txt")
    meta.write_text("\n".join(text) + "\n", encoding="utf-8")
    return written + [meta]
