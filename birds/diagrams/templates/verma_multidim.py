"""Multidimensional discriminant diagrams of Verma & co-authors.

This module implements:

* ``verma_agrawal_2011``   - 5-panel DF set for **mafic** rocks
  (Verma & Agrawal 2011).
* ``verma_verma_2013_major`` - 5-panel major-element DF set for
  **intermediate** rocks (Verma & Verma 2013, Set 1, Eqs 1-10).
* ``verma_verma_2013_imint`` - 5-panel immobile majors + traces DF set
  for **intermediate** rocks (Verma & Verma 2013, Set 2, Eqs 11-20).
* ``verma_verma_2013_trace`` - 5-panel immobile trace-element DF set
  for **intermediate** rocks (Verma & Verma 2013, Set 3, Eqs 21-30).
* ``verma_2012_acid``      - 3-panel DF set for **acid (felsic)** rocks
  (Verma, Pandarinath & Rivera-Gomez 2012).

All discriminant functions are linear combinations of natural-log
ratios (Aitchison ``alr``); the coefficient tables live in
``verma_coefficients.py``.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from .base import (
    MultiPanelDiagram,
    PanelSpec,
    build_logratios,
    feot_from_oxides,
    resolve_column,
)
from .verma_coefficients import (
    A04,
    A04_FIELDS,
    A08,
    A08_FIELDS,
    DFCoefSet,
    V12_ACID,
    V12_ACID_FIELDS,
    V13A_MACID,
    V13A_MACID_FIELDS,
    V13A_MTACID,
    V13A_MTACID_FIELDS,
    V13A_TACID,
    V13A_TACID_FIELDS,
    V06,
    V06_FIELDS,
    VA11,
    VA11_FIELDS,
    VV13_IMINT,
    VV13_IMINT_FIELDS,
    VV13_MAJOR,
    VV13_MAJOR_FIELDS,
    VV13_TRACE,
    VV13_TRACE_FIELDS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Major + trace element aliases so the templates accept the spelling
# variants typically used in geochemical spreadsheets.  Verma & Verma
# (2013) uses Fe2O3 and FeO SEPARATELY (not lumped as FeOt), so both
# columns must be available to compute the Set 1 (mint) DFs.
_MAJOR_ALIASES = {
    "TiO2":  ("TiO2", "TiO₂"),
    "Al2O3": ("Al2O3", "Al₂O₃"),
    "Fe2O3": ("Fe2O3", "Fe₂O₃"),
    "FeO":   ("FeO",),
    "FeOt":  ("FeOt", "FeO_T", "FeO*", "FeOT", "FeO(T)"),
    "MnO":   ("MnO",),
    "MgO":   ("MgO",),
    "CaO":   ("CaO",),
    "Na2O":  ("Na2O", "Na₂O"),
    "K2O":   ("K2O", "K₂O"),
    "P2O5":  ("P2O5", "P₂O₅"),
    "SiO2":  ("SiO2", "SiO₂"),
    # Trace elements used by VV13 imint (Set 2) and itrint (Set 3).
    "Nb":    ("Nb",),
    "Ni":    ("Ni",),
    "V":     ("V",),
    "Y":     ("Y",),
    "Zr":    ("Zr",),
    "La":    ("La",),
    "Ce":    ("Ce",),
    "Sm":    ("Sm",),
    "Th":    ("Th",),
    "Yb":    ("Yb",),
}


def _apply_df(lr: pd.DataFrame, coef: DFCoefSet) -> pd.Series:
    """Evaluate ``DF = intercept + Σ c_i * ln(part_i/denom)`` for every row."""
    out = pd.Series(coef.intercept, index=lr.index, dtype=float)
    for name, c in zip(coef.parts, coef.coefs):
        if name not in lr.columns:
            continue
        out = out + c * lr[name]
    return out


#: ppm -> wt.%, for the sets whose traces sit over a major oxide.
PPM_PER_WT_PERCENT = 10_000.0


def _needed(coef: DFCoefSet) -> str:
    """The columns a function reads, as the diagnostics name them."""
    parts = ", ".join(coef.parts)
    return f"{parts} ÷ {coef.denominator}" if coef.denominator else parts


def _parts_as_given(df: pd.DataFrame, parts, aliases
                    ) -> Optional[pd.DataFrame]:
    """The parts themselves, for a function with no denominator.

    ``None`` when a column is missing, as :func:`build_logratios`
    answers.  A zero is a value here, not a gap: nothing is logged.
    """
    if df is None or df.empty:
        return None
    out = pd.DataFrame(index=df.index)
    for name in parts:
        col = resolve_column(df, [name] + list(aliases.get(name, ())))
        if col is None:
            return None
        out[name] = pd.to_numeric(df[col], errors="coerce")
    return out


def _logratios_for_coef(df: pd.DataFrame, coef: DFCoefSet,
                        aliases=None) -> Optional[pd.DataFrame]:
    """Return ``ln(parts/denominator)`` for a single DFCoefSet.

    This is the one place the Verma log-ratios are built, so the unit
    handling declared by ``coef.ppm_parts`` reaches the diagrams and
    the statistics tables alike.
    """
    if coef.denominator is None:
        return _parts_as_given(df, coef.parts, aliases or _MAJOR_ALIASES)
    # FeOt needs computation if not present directly
    if "FeOt" in coef.parts and resolve_column(df, _MAJOR_ALIASES["FeOt"]) is None:
        feo = feot_from_oxides(df)
        if feo is None:
            return None
        df = df.copy()
        df["FeOt"] = feo
    scale = {name: PPM_PER_WT_PERCENT for name in coef.ppm_parts}
    return build_logratios(df, coef.parts, coef.denominator,
                           aliases=aliases or _MAJOR_ALIASES,
                           scale=scale)


# ---------------------------------------------------------------------------
# Generic 5-panel binary-pair DF diagram
# ---------------------------------------------------------------------------

class _BinaryPairsDF(MultiPanelDiagram):
    """Generic 5-panel DF diagram showing pairs of tectonic settings.

    Each panel plots ``DF1(A,B)`` (x) vs ``DF2(A,B)`` (y) for one binary
    pair (e.g. IAB vs MORB). Samples with ``DF1 > 0`` plot toward the
    first field, ``DF1 < 0`` toward the second.
    """

    # Subclasses must fill these:
    coef_table: Dict[str, DFCoefSet] = {}
    pair_panels: Tuple[Tuple[str, str, str], ...] = ()  # (pair_id, field_a, field_b)
    n_rows = 2
    n_cols = 3
    suptitle_fontsize = 12

    def __init__(self):
        super().__init__()
        # Build PanelSpec list with the canonical Verma & co-authors axis
        # range — every DF panel in the multidimensional discrimination
        # literature is drawn on a (−8, +8) × (−8, +8) square so the
        # zero-isolines of DF1 and DF2 sit at the centre and the two
        # half-planes carry the whole discrimination.
        panels = []
        for pair_id, fa, fb in self.pair_panels:
            panels.append(PanelSpec(
                key=pair_id,
                title=f"{fa}  vs  {fb}",
                x_label=f"DF1 ({fa}-{fb})",
                y_label=f"DF2 ({fa}-{fb})",
                x_range=(-8, 8),
                y_range=(-8, 8),
                vertical_lines=(0.0,),
                horizontal_lines=(0.0,),
                # Each field is the full half-plane on its side of DF1=0,
                # spanning the entire y-range so the discrimination is
                # solely on DF1 (DF2 carries orthogonal info).
                field_polygons={
                    fa: [(0.05, 7.8), (7.8, 7.8), (7.8, -7.8), (0.05, -7.8)],
                    fb: [(-7.8, 7.8), (-0.05, 7.8), (-0.05, -7.8), (-7.8, -7.8)],
                },
                # Labels in the upper part of each half-plane so they don't
                # collide with the data cloud, which usually clusters near
                # the origin.
                field_label_pos={
                    fa: ( 4.5,  6.5),
                    fb: (-4.5,  6.5),
                },
            ))
        self.panels = tuple(panels)
        self.field_label_fontsize = 10

    # Override field-polygon style: outlines only as light dashed boxes
    def _draw_panel_background(self, ax, panel: PanelSpec, options) -> None:
        # Light shaded half-planes for the two fields
        for name, verts in panel.field_polygons.items():
            xs = [v[0] for v in verts]
            ys = [v[1] for v in verts]
            color = "#FFEBE0" if xs[0] > 0 else "#E0EAFB"
            ax.fill(xs, ys, color=color, alpha=0.55, zorder=0)
            px, py = panel.field_label_pos.get(name,
                (sum(xs) / len(xs), sum(ys) / len(ys)))
            ax.text(px, py, name, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2)
        for y in panel.horizontal_lines:
            ax.axhline(y, color="#888", linewidth=0.6, linestyle=":", zorder=1)
        for x in panel.vertical_lines:
            ax.axvline(x, color="#444", linewidth=1.0, linestyle="--", zorder=1)

    def _compute_xy_for_panel(self, panel: PanelSpec, df: pd.DataFrame
                              ) -> Tuple[Optional[pd.Series], Optional[pd.Series]]:
        df1 = self.coef_table.get(f"DF1_{panel.key}")
        df2 = self.coef_table.get(f"DF2_{panel.key}")
        if df1 is None or df2 is None:
            return None, None
        lr = _logratios_for_coef(df, df1)
        if lr is None:
            return None, None
        xs = _apply_df(lr, df1)
        ys = _apply_df(lr, df2)
        return xs, ys

    # ------------------------------------------------------------------
    # Diagnostic: tell the user EXACTLY which columns are needed when a
    # panel can't be computed.  Without this, an incomplete dataset
    # produces a blank diagram with no clue about what is missing.
    # ------------------------------------------------------------------
    def _panel_diagnostic(self, panel, df, ax):
        from .base import missing_logratio_columns
        if df is None or df.empty:
            return "Load a dataset via Data → Import."
        # Don't override an already-rendered scatter.
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

        df1 = self.coef_table.get(f"DF1_{panel.key}")
        if df1 is None:
            return f"Coefficient set missing for DF1_{panel.key}."

        # Check FeOt specially — it can be derived from FeO + Fe2O3 even
        # when no FeOt column is present.
        parts = list(df1.parts)
        denom = df1.denominator
        derivable_feot = False
        if "FeOt" in parts or denom == "FeOt":
            feo = feot_from_oxides(df)
            if feo is not None and not feo.isna().all():
                derivable_feot = True

        missing = missing_logratio_columns(df, parts, denom, _MAJOR_ALIASES)
        if derivable_feot:
            missing = [m for m in missing if m != "FeOt"]
        if not missing:
            # Columns are all there but the DF still couldn't be
            # computed — typically every value is non-positive (log
            # is undefined).
            return ("All required columns are present but every row "
                    "has zero / negative values.")
        return ("Missing columns for this DF:\n"
                + ", ".join(missing)
                + f"\n(needed: {_needed(df1)})")


# ---------------------------------------------------------------------------
# Concrete templates
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Generic 3-way (triplet) DF diagram — each panel splits the DF1-DF2
# plane into THREE coloured sectors with straight boundaries radiating
# from a common centre.  Used by Verma & Agrawal (2011) and any future
# triplet-style discrimination diagram.
# ---------------------------------------------------------------------------

# Canonical 3-sector layout in (DF1, DF2) space.  The first listed group
# lands on the right, the second top-left, the third bottom-left — this
# matches the canonical Fig 12.14 of Verma (2020) / Verma & Agrawal
# (2011) where IAB occupies the right wedge, MORB the bottom-left and
# the "extra" group (CRB / OIB / CRB+OIB) the top-left.
_TRIPLET_CENTROIDS = (
    (3.5, 0.0),    # group A — right
    (-2.0, 3.0),   # group B — top-left
    (-2.0, -3.0),  # group C — bottom-left
)


class _TripletDF(MultiPanelDiagram):
    """Generic 5-panel diagram of 3-way DF discrimination.

    Each panel takes three group labels ``(A, B, C)`` and a pair of DF
    coefficient sets ``(DF1_<key>, DF2_<key>)``.  Samples are scattered
    in the DF1-DF2 plane and the plane is split into three coloured
    sectors by straight rays from the origin, each ray running through
    the midpoint between two consecutive centroids.  Cleaner-looking
    than equiprobability curves but topologically equivalent for the
    canonical centroid arrangement.
    """

    coef_table: Dict[str, DFCoefSet] = {}
    triplet_panels: Tuple[Tuple[str, str, str, str], ...] = ()
    n_rows = 2
    n_cols = 3
    suptitle_fontsize = 12

    # Colours used by sector A / B / C.  Light enough that the data
    # points stay readable on top.
    _SECTOR_COLORS = ("#FFE7D8", "#DFEBFB", "#E2F4D8")

    def __init__(self):
        super().__init__()
        panels = []
        for panel_key, ga, gb, gc in self.triplet_panels:
            panels.append(PanelSpec(
                key=panel_key,
                title=f"{ga}  ·  {gb}  ·  {gc}",
                x_label=f"DF1 ({ga}-{gb}-{gc})",
                y_label=f"DF2 ({ga}-{gb}-{gc})",
                x_range=(-8, 8),
                y_range=(-8, 8),
                vertical_lines=(),
                horizontal_lines=(),
                field_polygons={ga: [], gb: [], gc: []},  # sentinel keys
                field_label_pos={
                    ga: _TRIPLET_CENTROIDS[0],
                    gb: _TRIPLET_CENTROIDS[1],
                    gc: _TRIPLET_CENTROIDS[2],
                },
            ))
        self.panels = tuple(panels)
        self.field_label_fontsize = 11

    # ------------------------------------------------------------------
    # Per-panel autoscale
    # ------------------------------------------------------------------
    # When the published DF equation produces values outside the
    # canonical (−8, +8) frame — as happens with Eq 12.83 (DF2 CRB-OIB-
    # MORB) of Verma & Agrawal (2011), which lands at DF2 ≈ −15 to −20
    # for typical basalts — we transparently expand the panel range so
    # the user can SEE the data without altering the equations.  The
    # centroid layout is re-anchored at the data centroid in that case.

    def plot(self, figure, df, plot_style, options) -> None:
        """Override the default plot() to re-target the (x_range, y_range)
        of any panel whose data spills outside the canonical (−8, +8)
        frame.  Equations stay verbatim; only the visual axes adapt.
        """
        if df is not None and not df.empty:
            new_panels = []
            for spec in self.panels:
                new_spec = self._maybe_rescale_panel(spec, df)
                new_panels.append(new_spec)
            self.panels = tuple(new_panels)
        super().plot(figure, df, plot_style, options)

    def _maybe_rescale_panel(self, spec, df):
        """Return a (possibly modified) PanelSpec whose range encloses
        the actual data plus a small margin.  If the data fits inside
        the canonical (−8, +8) frame nothing changes."""
        import dataclasses
        try:
            xs, ys = self._compute_xy_for_panel(spec, df)
        except Exception:
            return spec
        if xs is None or ys is None:
            return spec
        x_vals = [v for v in xs if pd.notna(v)]
        y_vals = [v for v in ys if pd.notna(v)]
        if not x_vals or not y_vals:
            return spec
        x_min, x_max = min(x_vals), max(x_vals)
        y_min, y_max = min(y_vals), max(y_vals)
        # Canonical range; only expand, never shrink.
        cx_min, cx_max = spec.x_range or (-8, 8)
        cy_min, cy_max = spec.y_range or (-8, 8)
        margin = 1.5
        new_x = (min(cx_min, x_min - margin), max(cx_max, x_max + margin))
        new_y = (min(cy_min, y_min - margin), max(cy_max, y_max + margin))
        # Re-anchor field labels at the data centroid when the panel had
        # to expand, so the three labels stay inside the new frame
        # instead of clipping at the canonical (3.5, ±3) positions.
        if (new_x != (cx_min, cx_max)) or (new_y != (cy_min, cy_max)):
            cx = (x_min + x_max) / 2
            cy = (y_min + y_max) / 2
            span = max(new_x[1] - new_x[0], new_y[1] - new_y[0])
            r = span * 0.30
            labels = list(spec.field_polygons.keys())
            new_label_pos = {
                labels[0]: (cx + r,        cy),
                labels[1]: (cx - 0.6 * r,  cy + 0.85 * r),
                labels[2]: (cx - 0.6 * r,  cy - 0.85 * r),
            }
            return dataclasses.replace(
                spec,
                x_range=new_x,
                y_range=new_y,
                field_label_pos=new_label_pos,
            )
        return spec

    def _draw_panel_background(self, ax, panel, options):
        # Three sectors radiating from a common center — the geometric
        # centroid of the three field-label positions.  For the
        # canonical (−8, +8) frame this centroid is ≈ (0, 0); for an
        # auto-rescaled panel it shifts to wherever the data cluster
        # sits, keeping the three sectors visually balanced.
        from matplotlib.patches import Polygon as _Poly
        import numpy as _np
        labels = list(panel.field_polygons.keys())
        centroids = [panel.field_label_pos[lab] for lab in labels]
        center = (
            sum(c[0] for c in centroids) / 3.0,
            sum(c[1] for c in centroids) / 3.0,
        )
        # Mid-points of the three consecutive centroid pairs define the
        # boundary directions FROM the common center.
        mids = [
            ((centroids[0][0] + centroids[1][0]) / 2,
             (centroids[0][1] + centroids[1][1]) / 2),  # between A & B
            ((centroids[1][0] + centroids[2][0]) / 2,
             (centroids[1][1] + centroids[2][1]) / 2),  # between B & C
            ((centroids[2][0] + centroids[0][0]) / 2,
             (centroids[2][1] + centroids[0][1]) / 2),  # between C & A
        ]
        # The "far" length must exceed the panel's diagonal so the
        # sector polygons fully cover the visible frame.
        xr, yr = panel.x_range or (-8, 8), panel.y_range or (-8, 8)
        far = 2.0 * _np.hypot(xr[1] - xr[0], yr[1] - yr[0])

        def _extend(mid):
            dx = mid[0] - center[0]
            dy = mid[1] - center[1]
            n = _np.hypot(dx, dy)
            if n < 1e-9:
                return (center[0] + dx, center[1] + dy)
            return (center[0] + dx / n * far, center[1] + dy / n * far)

        e_ab = _extend(mids[0])
        e_bc = _extend(mids[1])
        e_ca = _extend(mids[2])

        # Three sector polygons (A/B/C).  Each sector is a triangle
        # rooted at the common centre and bounded by two consecutive
        # extended midpoint rays.  The _corner_path helper picks up any
        # panel-corner vertices lying between the two rays so the sector
        # fully covers the visible frame (avoids leaving empty wedges).
        sectors = {
            labels[0]: [center, e_ca,
                        _corner_path(e_ca, e_ab, far, center), e_ab],
            labels[1]: [center, e_ab,
                        _corner_path(e_ab, e_bc, far, center), e_bc],
            labels[2]: [center, e_bc,
                        _corner_path(e_bc, e_ca, far, center), e_ca],
        }
        for i, (lab, verts) in enumerate(sectors.items()):
            # Flatten the nested corner-paths
            flat = []
            for v in verts:
                if isinstance(v, list):
                    flat.extend(v)
                else:
                    flat.append(v)
            poly = _Poly(flat, closed=True,
                         facecolor=self._SECTOR_COLORS[i], alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = panel.field_label_pos[lab]
            ax.text(cx, cy, lab, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.7, boxstyle="round,pad=0.25"))
        # Boundary lines — also rooted at the common centre, not origin.
        for end in (e_ab, e_bc, e_ca):
            ax.plot([center[0], end[0]], [center[1], end[1]],
                    color="#444", linewidth=0.9, linestyle="--",
                    alpha=0.8, zorder=1)

    def _compute_xy_for_panel(self, panel, df):
        df1 = self.coef_table.get(f"DF1_{panel.key}")
        df2 = self.coef_table.get(f"DF2_{panel.key}")
        if df1 is None or df2 is None:
            return None, None
        lr = _logratios_for_coef(df, df1)
        if lr is None:
            return None, None
        return _apply_df(lr, df1), _apply_df(lr, df2)

    def _panel_diagnostic(self, panel, df, ax):
        from .base import missing_logratio_columns
        if df is None or df.empty:
            return "Load a dataset via Data → Import."
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
        df1 = self.coef_table.get(f"DF1_{panel.key}")
        if df1 is None:
            return None
        missing = missing_logratio_columns(df, list(df1.parts),
                                            df1.denominator, _MAJOR_ALIASES)
        if not missing:
            return ("All required columns present but every row has zero "
                    "/ negative values (log undefined).")
        return ("Missing columns for this DF:\n"
                + ", ".join(missing)
                + f"\n(needed: {_needed(df1)})")


def _corner_path(start, end, far, center=(0.0, 0.0)):
    """Return panel-corner vertices that lie on the arc from *start*
    to *end* (going CCW), measured from *center*.  Used to make sector
    polygons cover the full visible frame even when the dividing rays
    don't reach the corners directly.
    """
    import numpy as _np
    cx, cy = center
    corners = [
        (cx + far, cy + far), (cx - far, cy + far),
        (cx - far, cy - far), (cx + far, cy - far),
    ]
    a0 = _np.arctan2(start[1] - cy, start[0] - cx)
    a1 = _np.arctan2(end[1] - cy, end[0] - cx)
    def _wrap(a):
        return a % (2 * _np.pi)
    a = _wrap(a0)
    a_end = _wrap(a1)
    out = []
    for c in corners:
        ac = _wrap(_np.arctan2(c[1] - cy, c[0] - cx))
        if a < a_end:
            inside = a < ac < a_end
        else:
            inside = ac > a or ac < a_end
        if inside:
            out.append(c)
    out.sort(key=lambda c: _wrap(_np.arctan2(c[1] - cy, c[0] - cx) - a))
    return out


class VermaAgrawal2011(_TripletDF):
    """Verma & Agrawal (2011) — basic + ultrabasic rocks, 5 triplet panels.

    Canonical implementation of the Verma & Agrawal (2011) discriminant
    function diagrams, Table 6 (PDF page 9 / journal page 32):

    * (a) IAB · CRB+OIB · MORB     Eqs (a1) (a2)
    * (b) IAB · CRB · OIB          Eqs (b1) (b2)
    * (c) IAB · CRB · MORB         Eqs (c1) (c2)
    * (d) IAB · OIB · MORB         Eqs (d1) (d2)
    * (e) CRB · OIB · MORB         Eqs (e1) (e2)

    Variables: Nb, V, Y, Zr divided by **(TiO2)adj** in µg/g (ppm).  The
    paper explicitly states *"(TiO2)adj has to be expressed in µg/g so
    that the ratio variables become simple numbers"*.  The internal
    convention is to express *both* numerator and denominator in the
    same units (here µg/g) so the ratio is dimensionless — equivalently,
    the trace elements (already ppm) are converted to wt% (÷10 000)
    while TiO2 stays in wt%.  Both conventions yield the same log-ratio.

    Field boundaries follow Figure 1 of the paper: in each panel three
    straight segments radiate from a single *triple-point* inside the
    (-8, +8) frame and terminate on its outer edge.  Coordinates of
    the triple-points and edge endpoints are taken verbatim from the
    Figure 1 caption (PDF page 8) and live in :data:`VA11_FIELDS`.
    """
    key = "verma_agrawal_2011"
    composition_filter = "basic+ultrabasic"  # SiO2 < 52 (Verma 2011 cal.)
    title = ("Verma & Agrawal (2011) — Basic + ultrabasic rocks "
             "(5 triplet DF panels)")
    citation = ("Verma S.P. & Agrawal S. (2011) Revista Mexicana de Ciencias "
                "Geológicas 28(1), 24-44. "
                "Discriminates IAB · CRB · OIB · MORB from log-ratios "
                "ln(Nb/TiO2), ln(V/TiO2), ln(Y/TiO2), ln(Zr/TiO2) on "
                "100 %-anhydrous adjusted compositions, with (TiO2)adj "
                "in µg/g.  Equations from Table 6 of the paper; field "
                "boundaries from Figure 1.  Each panel splits three of "
                "the four tectonic settings.")
    coef_table = VA11
    triplet_panels = (
        ("IAB_CRBOIB_MORB", "IAB",  "CRB+OIB", "MORB"),
        ("IAB_CRB_OIB",     "IAB",  "CRB",     "OIB"),
        ("IAB_CRB_MORB",    "IAB",  "CRB",     "MORB"),
        ("IAB_OIB_MORB",    "IAB",  "OIB",     "MORB"),
        ("CRB_OIB_MORB",    "CRB",  "OIB",     "MORB"),
    )

    # Nb, V, Y and Zr come in ppm and the denominator TiO2 in wt%; the
    # conversion is declared on the coefficient set itself, so the
    # statistics tables get it too.  See DFCoefSet.ppm_parts.

    # Lock the axes to the canonical (-8, +8) frame published in
    # Figure 1; disable the parent class's auto-rescale that used to
    # kick in when the buggy coefficients drove samples off the panel.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    # ------------------------------------------------------------------
    # Canonical field rendering (Figure 1 of Verma & Agrawal 2011)
    # ------------------------------------------------------------------
    _FIELD_COLORS = {
        "IAB":      "#FFE7D8",   # warm yellow-orange
        "CRB":      "#E7DFF6",   # lavender
        "OIB":      "#E2F4D8",   # pale green
        "MORB":     "#DFEBFB",   # pale blue
        "CRB+OIB":  "#EDE7DD",   # neutral beige
    }

    def _draw_panel_background(self, ax, panel, options):
        """Draw the three canonical boundary segments + colour the three
        regions defined by them.  Replaces the parent's sector approx
        with the exact Figure 1 geometry from :data:`VA11_FIELDS`."""
        from matplotlib.patches import Polygon as _Poly
        geom = VA11_FIELDS.get(panel.key)
        if geom is None:
            return super()._draw_panel_background(ax, panel, options)

        triple = geom["triple"]
        boundaries = geom["boundaries"]  # ((outer, (gA, gB)), ...)
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)

        # Sort boundaries CCW around the triple-point so we can walk the
        # region polygons in order.
        def _angle(b):
            (ox, oy), _ = b
            return np.arctan2(oy - triple[1], ox - triple[0])
        ordered = sorted(boundaries, key=_angle)

        # Walk region by region.  The "region between ray i and ray i+1"
        # (going CCW) corresponds to the group name that appears in BOTH
        # boundary tuples.
        regions = []
        n = len(ordered)
        for i in range(n):
            (outer_i, names_i) = ordered[i]
            (outer_j, names_j) = ordered[(i + 1) % n]
            common = set(names_i) & set(names_j)
            if not common:
                continue
            label = next(iter(common))
            corners = _frame_corners_between(outer_i, outer_j, x_range, y_range)
            verts = [triple, outer_i, *corners, outer_j]
            regions.append((label, verts))

        # Paint regions first (behind), then the boundary lines on top.
        for label, verts in regions:
            color = self._FIELD_COLORS.get(label, "#E0E0E0")
            poly = _Poly(verts, closed=True, facecolor=color, alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, label, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))

        # The three boundary segments — solid black, on top of the fills.
        for (outer, _names) in ordered:
            ax.plot([triple[0], outer[0]], [triple[1], outer[1]],
                    color="#1c2237", linewidth=1.2, zorder=1)
        # Small marker at the triple-point itself for clarity.
        ax.plot(triple[0], triple[1], marker="o", markersize=4,
                color="#1c2237", zorder=3)


# ---------------------------------------------------------------------------
# Helpers used by VermaAgrawal2011 only — keep them out of the parent class
# since other diagrams use different field-rendering logic.
# ---------------------------------------------------------------------------

def _perim_param(point, x_range, y_range):
    """Return the CCW perimeter parameter (in [0, 4)) of a point that
    lies on the rectangular frame.  The right edge maps to [0, 1), top
    to [1, 2), left to [2, 3), bottom to [3, 4)."""
    xmin, xmax = x_range
    ymin, ymax = y_range
    x, y = point
    eps = 1e-4 * max(xmax - xmin, ymax - ymin)
    if abs(x - xmax) < eps:
        return (y - ymin) / (ymax - ymin)
    if abs(y - ymax) < eps:
        return 1.0 + (xmax - x) / (xmax - xmin)
    if abs(x - xmin) < eps:
        return 2.0 + (ymax - y) / (ymax - ymin)
    if abs(y - ymin) < eps:
        return 3.0 + (x - xmin) / (xmax - xmin)
    # Point isn't on the frame — return NaN so callers skip it.
    return float("nan")


def _frame_corners_between(start, end, x_range, y_range):
    """Return the list of frame corner points strictly between *start*
    and *end* when walking CCW around the perimeter.  Both endpoints
    must lie on the frame.

    When the walk wraps around past t=4 (i.e. ``t1 < t0``), corners
    with ``tc > t0`` are emitted BEFORE corners with ``tc < t1``,
    preserving the CCW ordering of vertices in the returned polygon.
    """
    xmin, xmax = x_range
    ymin, ymax = y_range
    # Corners and their CCW parameters: top-right=1, top-left=2,
    # bottom-left=3, bottom-right=4 (≡0).
    corners = [
        (1.0, (xmax, ymax)),
        (2.0, (xmin, ymax)),
        (3.0, (xmin, ymin)),
        (4.0, (xmax, ymin)),
    ]
    t0 = _perim_param(start, x_range, y_range)
    t1 = _perim_param(end, x_range, y_range)
    if not (np.isfinite(t0) and np.isfinite(t1)):
        return []
    out = []
    if t1 > t0:
        for tc, pt in corners:
            if t0 < tc < t1:
                out.append(pt)
    else:
        # Wrap around past t=4 ≡ 0.  Emit tc>t0 corners FIRST (the
        # ones we hit before wrapping), then tc<t1 corners (the ones
        # after wrap).  Iterating in tc-ascending order would yield
        # a self-intersecting polygon when 2+ corners are walked.
        for tc, pt in corners:
            if tc > t0:
                out.append(pt)
        for tc, pt in corners:
            if tc < t1:
                out.append(pt)
    return out


def _polygon_centroid(verts):
    """Area-weighted centroid of a polygon given as a list of (x, y)."""
    n = len(verts)
    if n < 3:
        # Degenerate: just average.
        return (sum(v[0] for v in verts) / n,
                sum(v[1] for v in verts) / n)
    a = 0.0
    cx = 0.0
    cy = 0.0
    for i in range(n):
        x0, y0 = verts[i]
        x1, y1 = verts[(i + 1) % n]
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    a *= 0.5
    if abs(a) < 1e-12:
        return (sum(v[0] for v in verts) / n,
                sum(v[1] for v in verts) / n)
    return (cx / (6.0 * a), cy / (6.0 * a))


# ---------------------------------------------------------------------------
# Verma & Verma (2013) — Intermediate magmas, three canonical sets
# ---------------------------------------------------------------------------
# All three sets follow the same 5-panel triplet layout (see paper Figs 1-3):
#   (a) IA+CA · CR+OI · Col       — combined arcs vs combined rift-island vs Col
#   (b) IA · CA · CR+OI           — arc subdivisions vs combined rift-island
#   (c) IA · CA · Col             — arc subdivisions vs Col
#   (d) IA · CR+OI · Col          — IA vs combined rift-island vs Col
#   (e) CA · CR+OI · Col          — CA vs combined rift-island vs Col
# ---------------------------------------------------------------------------

_VV13_TRIPLET_PANELS = (
    ("IACA_CROI_COL",  "IA+CA",   "CR+OI",  "Col"),
    ("IA_CA_CROI",     "IA",      "CA",     "CR+OI"),
    ("IA_CA_COL",      "IA",      "CA",     "Col"),
    ("IA_CROI_COL",    "IA",      "CR+OI",  "Col"),
    ("CA_CROI_COL",    "CA",      "CR+OI",  "Col"),
)


class VermaVerma2013Major(_TripletDF):
    """Verma & Verma (2013) — intermediate rocks, Set 1 (majors).

    Five panels of 3-way discrimination among Island Arc (IA), Continental
    Arc (CA), Continental Rift + Ocean Island (CR+OI) and Collision (Col)
    based on log-ratios of 10 majors ÷ SiO2_adj.  Fe2O3 and FeO are used
    SEPARATELY (not lumped as FeOt) — the Middlemost (1989) Fe-oxidation
    correction must be applied before computing the DFs.

    Field boundaries follow Figure 1 of the paper: three straight segments
    radiate from a triple-point inside the (-8, +8) frame and end at the
    outer edge.  Coordinates verbatim from the Figure 1 caption (page 937
    of Turkish J Earth Sci 22; PDF page 8) and live in
    :data:`VV13_MAJOR_FIELDS`.
    """
    key = "verma_verma_2013_major"
    composition_filter = "intermediate"  # 52 ≤ SiO2 < 63 (Verma 2013 cal.)
    title = ("Verma & Verma (2013) — Intermediate rocks, Set 1: majors "
             "(5 triplet DF panels)")
    citation = ("Verma S.P. & Verma S.K. (2013) Turkish J Earth Sci 22, "
                "931–995.  Equations (1)–(10) on pp. 933–935; field "
                "boundaries from Figure 1 caption.  Discriminates IA · "
                "CA · CR+OI · Col using natural-log ratios of 10 major "
                "oxides (TiO2, Al2O3, Fe2O3, FeO, MnO, MgO, CaO, Na2O, "
                "K2O, P2O5) against SiO2 on 100 %-anhydrous Middlemost-"
                "adjusted compositions.  Each of the 5 panels (a–e) "
                "discriminates 3 of the 4 tectonic groups.")
    coef_table = VV13_MAJOR
    triplet_panels = _VV13_TRIPLET_PANELS

    # Lock the axes to the canonical (-8, +8) frame published in Figure 1.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    # Same canonical-region rendering as VA11 — share the colour palette.
    _FIELD_COLORS = {
        "IA":     "#FFE7D8",
        "CA":     "#FAE6B8",
        "CR+OI":  "#E2F4D8",
        "Col":    "#DFEBFB",
        "IA+CA":  "#FFD8B5",
    }

    def _draw_panel_background(self, ax, panel, options):
        """Draw the canonical Figure 1 boundary segments + colour the
        three regions defined by them.  Mirrors the VA11 override but
        uses :data:`VV13_MAJOR_FIELDS` for the geometry."""
        from matplotlib.patches import Polygon as _Poly
        geom = VV13_MAJOR_FIELDS.get(panel.key)
        if geom is None:
            return super()._draw_panel_background(ax, panel, options)

        triple = geom["triple"]
        boundaries = geom["boundaries"]
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)

        def _angle(b):
            (ox, oy), _ = b
            return np.arctan2(oy - triple[1], ox - triple[0])
        ordered = sorted(boundaries, key=_angle)

        regions = []
        n = len(ordered)
        for i in range(n):
            (outer_i, names_i) = ordered[i]
            (outer_j, names_j) = ordered[(i + 1) % n]
            common = set(names_i) & set(names_j)
            if not common:
                continue
            label = next(iter(common))
            corners = _frame_corners_between(outer_i, outer_j, x_range, y_range)
            verts = [triple, outer_i, *corners, outer_j]
            regions.append((label, verts))

        for label, verts in regions:
            color = self._FIELD_COLORS.get(label, "#E0E0E0")
            poly = _Poly(verts, closed=True, facecolor=color, alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, label, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))

        for (outer, _names) in ordered:
            ax.plot([triple[0], outer[0]], [triple[1], outer[1]],
                    color="#1c2237", linewidth=1.2, zorder=1)
        ax.plot(triple[0], triple[1], marker="o", markersize=4,
                color="#1c2237", zorder=3)


class VermaVerma2013ImMint(_TripletDF):
    """Verma & Verma (2013) — intermediate rocks, Set 2 (immobile mj+trace).

    Five panels of 3-way discrimination using log-ratios of 2 immobile
    majors (MgO, P2O5) and 5 immobile traces (Nb, Ni, V, Y, Zr) ÷ TiO2_adj.
    Trace elements are taken in ppm but TiO2 is in wt%, so the traces are
    converted ppm → wt% (÷ 10 000) BEFORE the log-ratio (same convention
    as Verma & Agrawal 2011).

    Field boundaries follow Figure 2 of the paper: three straight segments
    radiate from a triple-point inside the (-8, +8) frame and end at the
    outer edge.  Coordinates verbatim from the Figure 2 caption (PDF page
    12, journal page 941) and live in :data:`VV13_IMINT_FIELDS`.
    """
    key = "verma_verma_2013_imint"
    composition_filter = "intermediate"
    title = ("Verma & Verma (2013) — Intermediate rocks, Set 2: immobile "
             "majors + traces (5 triplet DF panels)")
    citation = ("Verma S.P. & Verma S.K. (2013) Turkish J Earth Sci 22, "
                "931–995.  Equations (11)–(20) on pp. 937–938; field "
                "boundaries from Figure 2 caption (p. 941).  Discriminates "
                "IA · CA · CR+OI · Col using natural-log ratios of MgO, "
                "P2O5 (wt%, adjusted) and Nb, Ni, V, Y, Zr (ppm → wt%) "
                "against TiO2 (wt%, adjusted).  Each of the 5 panels (a–e) "
                "discriminates 3 of the 4 tectonic groups.")
    coef_table = VV13_IMINT
    triplet_panels = _VV13_TRIPLET_PANELS

    # Nb, Ni, V, Y and Zr need the ppm -> wt% conversion; MgO and P2O5
    # are already wt%.  Declared on the coefficient set itself — see
    # DFCoefSet.ppm_parts.

    # Lock the axes to the canonical (-8, +8) frame published in Figure 2.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    # Share the field colour palette with VV13 Set 1.
    _FIELD_COLORS = {
        "IA":     "#FFE7D8",
        "CA":     "#FAE6B8",
        "CR+OI":  "#E2F4D8",
        "Col":    "#DFEBFB",
        "IA+CA":  "#FFD8B5",
    }

    def _draw_panel_background(self, ax, panel, options):
        """Draw the canonical Figure 2 boundaries + colour the three
        regions defined by them.  Mirrors VV13 Set 1 / VA11 overrides
        but uses :data:`VV13_IMINT_FIELDS` for the geometry."""
        from matplotlib.patches import Polygon as _Poly
        geom = VV13_IMINT_FIELDS.get(panel.key)
        if geom is None:
            return super()._draw_panel_background(ax, panel, options)

        triple = geom["triple"]
        boundaries = geom["boundaries"]
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)

        def _angle(b):
            (ox, oy), _ = b
            return np.arctan2(oy - triple[1], ox - triple[0])
        ordered = sorted(boundaries, key=_angle)

        regions = []
        n = len(ordered)
        for i in range(n):
            (outer_i, names_i) = ordered[i]
            (outer_j, names_j) = ordered[(i + 1) % n]
            common = set(names_i) & set(names_j)
            if not common:
                continue
            label = next(iter(common))
            corners = _frame_corners_between(outer_i, outer_j, x_range, y_range)
            verts = [triple, outer_i, *corners, outer_j]
            regions.append((label, verts))

        for label, verts in regions:
            color = self._FIELD_COLORS.get(label, "#E0E0E0")
            poly = _Poly(verts, closed=True, facecolor=color, alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, label, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))

        for (outer, _names) in ordered:
            ax.plot([triple[0], outer[0]], [triple[1], outer[1]],
                    color="#1c2237", linewidth=1.2, zorder=1)
        ax.plot(triple[0], triple[1], marker="o", markersize=4,
                color="#1c2237", zorder=3)


class VermaVerma2013Trace(_TripletDF):
    """Verma & Verma (2013) — intermediate rocks, Set 3 (immobile traces).

    Five panels of 3-way discrimination using log-ratios of 7 immobile
    traces (La, Ce, Sm, Nb, Th, Y, Zr) ÷ Yb.  Since both numerators and
    denominator are in ppm, no unit conversion is needed.

    Field boundaries follow Figure 3 of the paper: three straight segments
    radiate from a triple-point inside the (-8, +8) frame and end at the
    outer edge.  Coordinates verbatim from the Figure 3 caption (PDF page
    14, journal page 943) and live in :data:`VV13_TRACE_FIELDS`.
    """
    key = "verma_verma_2013_trace"
    composition_filter = "intermediate"
    title = ("Verma & Verma (2013) — Intermediate rocks, Set 3: immobile "
             "traces (5 triplet DF panels)")
    citation = ("Verma S.P. & Verma S.K. (2013) Turkish J Earth Sci 22, "
                "931–995.  Equations (21)–(30) on pp. 939, 941; field "
                "boundaries from Figure 3 caption (p. 943).  Discriminates "
                "IA · CA · CR+OI · Col using natural-log ratios of La, "
                "Ce, Sm, Nb, Th, Y, Zr against Yb (all in ppm).  Each of "
                "the 5 panels (a–e) discriminates 3 of the 4 tectonic "
                "groups.")
    coef_table = VV13_TRACE
    triplet_panels = _VV13_TRIPLET_PANELS

    # Lock axes to canonical (-8, +8) per Figure 3.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    _FIELD_COLORS = {
        "IA":     "#FFE7D8",
        "CA":     "#FAE6B8",
        "CR+OI":  "#E2F4D8",
        "Col":    "#DFEBFB",
        "IA+CA":  "#FFD8B5",
    }

    def _draw_panel_background(self, ax, panel, options):
        """Draw the canonical Figure 3 boundary segments + colour the
        three regions.  Mirrors VV13 Sets 1 & 2 / VA11 overrides but
        uses :data:`VV13_TRACE_FIELDS` for the geometry."""
        from matplotlib.patches import Polygon as _Poly
        geom = VV13_TRACE_FIELDS.get(panel.key)
        if geom is None:
            return super()._draw_panel_background(ax, panel, options)

        triple = geom["triple"]
        boundaries = geom["boundaries"]
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)

        def _angle(b):
            (ox, oy), _ = b
            return np.arctan2(oy - triple[1], ox - triple[0])
        ordered = sorted(boundaries, key=_angle)

        regions = []
        n = len(ordered)
        for i in range(n):
            (outer_i, names_i) = ordered[i]
            (outer_j, names_j) = ordered[(i + 1) % n]
            common = set(names_i) & set(names_j)
            if not common:
                continue
            label = next(iter(common))
            corners = _frame_corners_between(outer_i, outer_j, x_range, y_range)
            verts = [triple, outer_i, *corners, outer_j]
            regions.append((label, verts))

        for label, verts in regions:
            color = self._FIELD_COLORS.get(label, "#E0E0E0")
            poly = _Poly(verts, closed=True, facecolor=color, alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, label, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))

        for (outer, _names) in ordered:
            ax.plot([triple[0], outer[0]], [triple[1], outer[1]],
                    color="#1c2237", linewidth=1.2, zorder=1)
        ax.plot(triple[0], triple[1], marker="o", markersize=4,
                color="#1c2237", zorder=3)


class Verma2012Acid(_TripletDF):
    """Verma et al. (2012) — Acid (granitic / felsic) rocks, 5 triplet panels.

    Canonical implementation following Verma S.K., Pandarinath K. &
    Verma S.P. (2012) International Geology Review 54(3), 325–347,
    Table 3 (Eqs 1–10).  Each panel discriminates THREE of the 4 tectonic
    settings (IA, CA, CR, Col) — acid rocks are not produced in significant
    amounts in MORB or OIB settings, so those are absent here.

    * (A) IA+CA · CR · Col   — combined arcs vs CR vs Col
    * (B) IA · CA · CR
    * (C) IA · CA · Col
    * (D) IA · CR · Col
    * (E) CA · CR · Col

    Variables: 10 major oxides (TiO2, Al2O3, Fe2O3, FeO, MnO, MgO, CaO,
    Na2O, K2O, P2O5) ÷ SiO2 — all adjusted to 100 % anhydrous with the
    Middlemost (1989) Fe-oxidation correction, so Fe2O3 and FeO
    must be available SEPARATELY (not as FeOt).

    Field boundaries follow Figure 5 of the paper: three straight segments
    radiate from a triple-point inside the (-8, +8) frame and end at the
    outer edge.  Coordinates verbatim from the Figure 5 caption (PDF page
    14, journal page 337) and live in :data:`V12_ACID_FIELDS`.
    """
    key = "verma_2012_acid"
    composition_filter = "acid"  # SiO2 ≥ 63 (Verma et al. 2012 cal.)
    title = ("Verma, Pandarinath & Rivera-Gomez (2012) — Acid rocks "
             "(5 triplet DF panels)")
    citation = ("Verma S.K., Pandarinath K. & Verma S.P. (2012) "
                "International Geology Review 54(3), 325–347.  Table 3, "
                "Eqs (1)–(10) on pp. 335–336; field boundaries from "
                "Figure 5 caption (p. 337).  Discriminates IA · CA · CR · "
                "Col for granitic / acid rocks using natural-log ratios "
                "of 10 major oxides against SiO2 on 100 %-anhydrous "
                "Middlemost-adjusted compositions.  Each of the 5 panels "
                "(A–E) discriminates 3 of the 4 tectonic groups.")
    coef_table = V12_ACID
    triplet_panels = (
        ("IACA_CR_COL",  "IA+CA", "CR",  "Col"),
        ("IA_CA_CR",     "IA",    "CA",  "CR"),
        ("IA_CA_COL",    "IA",    "CA",  "Col"),
        ("IA_CR_COL",    "IA",    "CR",  "Col"),
        ("CA_CR_COL",    "CA",    "CR",  "Col"),
    )

    # Lock axes to canonical (-8, +8) per Figure 5.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    _FIELD_COLORS = {
        "IA":     "#FFE7D8",
        "CA":     "#FAE6B8",
        "CR":     "#E2F4D8",
        "Col":    "#DFEBFB",
        "IA+CA":  "#FFD8B5",
    }

    def _draw_panel_background(self, ax, panel, options):
        """Draw the canonical Figure 5 boundary segments + colour the
        three regions.  Mirrors VV13 / VA11 overrides but uses
        :data:`V12_ACID_FIELDS` for the geometry."""
        from matplotlib.patches import Polygon as _Poly
        geom = V12_ACID_FIELDS.get(panel.key)
        if geom is None:
            return super()._draw_panel_background(ax, panel, options)

        triple = geom["triple"]
        boundaries = geom["boundaries"]
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)

        def _angle(b):
            (ox, oy), _ = b
            return np.arctan2(oy - triple[1], ox - triple[0])
        ordered = sorted(boundaries, key=_angle)

        regions = []
        n = len(ordered)
        for i in range(n):
            (outer_i, names_i) = ordered[i]
            (outer_j, names_j) = ordered[(i + 1) % n]
            common = set(names_i) & set(names_j)
            if not common:
                continue
            label = next(iter(common))
            corners = _frame_corners_between(outer_i, outer_j, x_range, y_range)
            verts = [triple, outer_i, *corners, outer_j]
            regions.append((label, verts))

        for label, verts in regions:
            color = self._FIELD_COLORS.get(label, "#E0E0E0")
            poly = _Poly(verts, closed=True, facecolor=color, alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, label, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))

        for (outer, _names) in ordered:
            ax.plot([triple[0], outer[0]], [triple[1], outer[1]],
                    color="#1c2237", linewidth=1.2, zorder=1)
        ax.plot(triple[0], triple[1], marker="o", markersize=4,
                color="#1c2237", zorder=3)


# ---------------------------------------------------------------------------
# Verma, Pandarinath, Verma & Agrawal (2013) - Acid rocks, Set 1 (majors)
# ---------------------------------------------------------------------------

class Verma2013AcidMajor(_TripletDF):
    """Verma et al. (2013) — Acid rocks, Set 1: majors (5 triplet panels).

    Canonical implementation of Verma S.P., Pandarinath K., Verma S.K.,
    Agrawal S. (2013) "Fifteen new discriminant-function-based multi-
    dimensional robust diagrams for acid rocks and their application to
    Precambrian rocks", Lithos 168-169, 113-123.  Supplementary Table 5,
    Eqs. (1)–(10).

    Each panel discriminates THREE of the 4 tectonic settings (IA, CA,
    CR+OI, Col).  Unlike Verma et al. (2012) Acid, this paper uses
    log-ratios of *different subsets* of the 10 majors per equation —
    the LDA stepwise selection only retains variables that improve
    classification, so e.g. Eq (3) drops Al2O3 and Eq (7) drops Fe2O3,
    FeO and MgO.

    Field boundaries follow Figure 2 caption (PDF page 4); the
    coordinates published as "approximate" by the authors.
    """
    key = "verma_2013_acid_macid"
    composition_filter = "acid"
    title = ("Verma et al. (2013) — Acid rocks, Set 1: majors "
             "(5 triplet DF panels)")
    citation = ("Verma S.P., Pandarinath K., Verma S.K. & Agrawal S. "
                "(2013) Lithos 168-169, 113-123.  Supplementary Table 5, "
                "Eqs (1)–(10); field boundaries from Figure 2 caption "
                "(approximate per authors).  Discriminates IA · CA · "
                "CR+OI · Col for acid (felsic) rocks using natural-log "
                "ratios of major oxides against SiO2 on 100 %-anhydrous "
                "Middlemost-adjusted compositions.  LDA stepwise variable "
                "selection means each of the 5 panels (a–e) uses a "
                "different subset of the 10 majors.")
    coef_table = V13A_MACID
    triplet_panels = (
        ("IACA_CROI_COL", "IA+CA", "CR+OI", "Col"),
        ("IA_CA_CROI",    "IA",    "CA",    "CR+OI"),
        ("IA_CA_COL",     "IA",    "CA",    "Col"),
        ("IA_CROI_COL",   "IA",    "CR+OI", "Col"),
        ("CA_CROI_COL",   "CA",    "CR+OI", "Col"),
    )

    # Axes published as (-8, +8) in Figure 2.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    _FIELD_COLORS = {
        "IA":     "#FFE7D8",
        "CA":     "#FAE6B8",
        "CR+OI":  "#E2F4D8",
        "Col":    "#DFEBFB",
        "IA+CA":  "#FFD8B5",
    }

    def _draw_panel_background(self, ax, panel, options):
        """Same canonical-region rendering pattern as VV13 / V12_ACID,
        but uses :data:`V13A_MACID_FIELDS` for the Fig 2 geometry."""
        from matplotlib.patches import Polygon as _Poly
        geom = V13A_MACID_FIELDS.get(panel.key)
        if geom is None:
            return super()._draw_panel_background(ax, panel, options)

        triple = geom["triple"]
        boundaries = geom["boundaries"]
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)

        def _angle(b):
            (ox, oy), _ = b
            return np.arctan2(oy - triple[1], ox - triple[0])
        ordered = sorted(boundaries, key=_angle)

        regions = []
        n = len(ordered)
        for i in range(n):
            (outer_i, names_i) = ordered[i]
            (outer_j, names_j) = ordered[(i + 1) % n]
            common = set(names_i) & set(names_j)
            if not common:
                continue
            label = next(iter(common))
            corners = _frame_corners_between(outer_i, outer_j, x_range, y_range)
            verts = [triple, outer_i, *corners, outer_j]
            regions.append((label, verts))

        for label, verts in regions:
            color = self._FIELD_COLORS.get(label, "#E0E0E0")
            poly = _Poly(verts, closed=True, facecolor=color, alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, label, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))

        for (outer, _names) in ordered:
            ax.plot([triple[0], outer[0]], [triple[1], outer[1]],
                    color="#1c2237", linewidth=1.2, zorder=1)
        ax.plot(triple[0], triple[1], marker="o", markersize=4,
                color="#1c2237", zorder=3)


# ---------------------------------------------------------------------------
# Verma et al. (2013) - Acid rocks, Set 2 (immobile majors + trace)
# ---------------------------------------------------------------------------

class Verma2013AcidImMt(_TripletDF):
    """Verma et al. (2013) — Acid rocks, Set 2: immobile mj + traces.

    Five panels of 3-way discrimination using log-ratios of MgO, P2O5
    (wt%, adjusted) and Nb, Y, Zr (ppm → wt%) ÷ TiO2_adj.  Each panel
    uses a subset of these 5 variables (LDA stepwise selection).

    IMPORTANT unit convention (footnote of Supplementary Table 9):
        "all trace element concentrations must be converted to wt %
        by dividing the ppm or μg.g⁻¹ values by 10 000 before using
        these equations (11–20)".
    The Nb, Y, Zr numerators are scaled by 1/10 000 before the log-ratio.

    Field boundaries follow Figure 3 caption (Verma_Acid_2.pdf p. 5).
    """
    key = "verma_2013_acid_mtacid"
    composition_filter = "acid"
    title = ("Verma et al. (2013) — Acid rocks, Set 2: immobile mj + "
             "traces (5 triplet DF panels)")
    citation = ("Verma S.P., Pandarinath K., Verma S.K. & Agrawal S. "
                "(2013) Lithos 168-169, 113-123.  Supplementary Table 9, "
                "Eqs (11)–(20); field boundaries from Figure 3 caption.  "
                "Discriminates IA · CA · CR+OI · Col for acid rocks "
                "using natural-log ratios of MgO, P2O5 (wt%, adjusted) "
                "and Nb, Y, Zr (ppm → wt% by ÷10 000) against TiO2 "
                "(wt%, adjusted).  Each panel uses a different subset "
                "of these 5 variables (LDA stepwise selection).")
    coef_table = V13A_MTACID
    triplet_panels = (
        ("IACA_CROI_COL", "IA+CA", "CR+OI", "Col"),
        ("IA_CA_CROI",    "IA",    "CA",    "CR+OI"),
        ("IA_CA_COL",     "IA",    "CA",    "Col"),
        ("IA_CROI_COL",   "IA",    "CR+OI", "Col"),
        ("CA_CROI_COL",   "CA",    "CR+OI", "Col"),
    )

    # Nb, Y and Zr need the ppm -> wt% conversion; MgO and P2O5 are
    # already wt%.  Declared on the coefficient set — see
    # DFCoefSet.ppm_parts.

    # Axes fixed at (-8, +8) per Figure 3.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    _FIELD_COLORS = {
        "IA":     "#FFE7D8",
        "CA":     "#FAE6B8",
        "CR+OI":  "#E2F4D8",
        "Col":    "#DFEBFB",
        "IA+CA":  "#FFD8B5",
    }

    def _draw_panel_background(self, ax, panel, options):
        """Canonical Figure 3 geometry from :data:`V13A_MTACID_FIELDS`."""
        from matplotlib.patches import Polygon as _Poly
        geom = V13A_MTACID_FIELDS.get(panel.key)
        if geom is None:
            return super()._draw_panel_background(ax, panel, options)

        triple = geom["triple"]
        boundaries = geom["boundaries"]
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)

        def _angle(b):
            (ox, oy), _ = b
            return np.arctan2(oy - triple[1], ox - triple[0])
        ordered = sorted(boundaries, key=_angle)

        regions = []
        n = len(ordered)
        for i in range(n):
            (outer_i, names_i) = ordered[i]
            (outer_j, names_j) = ordered[(i + 1) % n]
            common = set(names_i) & set(names_j)
            if not common:
                continue
            label = next(iter(common))
            corners = _frame_corners_between(outer_i, outer_j, x_range, y_range)
            verts = [triple, outer_i, *corners, outer_j]
            regions.append((label, verts))

        for label, verts in regions:
            color = self._FIELD_COLORS.get(label, "#E0E0E0")
            poly = _Poly(verts, closed=True, facecolor=color, alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, label, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))

        for (outer, _names) in ordered:
            ax.plot([triple[0], outer[0]], [triple[1], outer[1]],
                    color="#1c2237", linewidth=1.2, zorder=1)
        ax.plot(triple[0], triple[1], marker="o", markersize=4,
                color="#1c2237", zorder=3)


# ---------------------------------------------------------------------------
# Verma et al. (2013) - Acid rocks, Set 3 (immobile traces only)
# ---------------------------------------------------------------------------

class Verma2013AcidTrace(_TripletDF):
    """Verma et al. (2013) — Acid rocks, Set 3: immobile traces only.

    Five panels of 3-way discrimination using log-ratios of seven trace
    elements (La, Ce, Sm, Nb, Th, Y, Zr) divided by Yb.  Panel (c) drops
    Y (LDA stepwise selection); the other 4 panels use all 7 traces.

    All numerators and the denominator (Yb) are in ppm, so units cancel
    and no ppm→wt% conversion is needed.

    Field boundaries follow Figure 4 caption (Verma_Acid_2.pdf p. 7).
    """
    key = "verma_2013_acid_tacid"
    composition_filter = "acid"
    title = ("Verma et al. (2013) — Acid rocks, Set 3: immobile traces "
             "(5 triplet DF panels)")
    citation = ("Verma S.P., Pandarinath K., Verma S.K. & Agrawal S. "
                "(2013) Lithos 168-169, 113-123.  Supplementary Table 13, "
                "Eqs (21)–(30); field boundaries from Figure 4 caption.  "
                "Discriminates IA · CA · CR+OI · Col for acid rocks "
                "using natural-log ratios of seven traces (La, Ce, Sm, "
                "Nb, Th, Y, Zr) against Yb (all ppm — units cancel).  "
                "Panel (c) IA·CA·Col uses only 6 of the 7 traces (drops "
                "Y) per LDA stepwise selection.")
    coef_table = V13A_TACID
    triplet_panels = (
        ("IACA_CROI_COL", "IA+CA", "CR+OI", "Col"),
        ("IA_CA_CROI",    "IA",    "CA",    "CR+OI"),
        ("IA_CA_COL",     "IA",    "CA",    "Col"),
        ("IA_CROI_COL",   "IA",    "CR+OI", "Col"),
        ("CA_CROI_COL",   "CA",    "CR+OI", "Col"),
    )

    # Axes fixed at (-8, +8) per Figure 4.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    _FIELD_COLORS = {
        "IA":     "#FFE7D8",
        "CA":     "#FAE6B8",
        "CR+OI":  "#E2F4D8",
        "Col":    "#DFEBFB",
        "IA+CA":  "#FFD8B5",
    }

    def _draw_panel_background(self, ax, panel, options):
        """Canonical Figure 4 geometry from :data:`V13A_TACID_FIELDS`."""
        from matplotlib.patches import Polygon as _Poly
        geom = V13A_TACID_FIELDS.get(panel.key)
        if geom is None:
            return super()._draw_panel_background(ax, panel, options)

        triple = geom["triple"]
        boundaries = geom["boundaries"]
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)

        def _angle(b):
            (ox, oy), _ = b
            return np.arctan2(oy - triple[1], ox - triple[0])
        ordered = sorted(boundaries, key=_angle)

        regions = []
        n = len(ordered)
        for i in range(n):
            (outer_i, names_i) = ordered[i]
            (outer_j, names_j) = ordered[(i + 1) % n]
            common = set(names_i) & set(names_j)
            if not common:
                continue
            label = next(iter(common))
            corners = _frame_corners_between(outer_i, outer_j, x_range, y_range)
            verts = [triple, outer_i, *corners, outer_j]
            regions.append((label, verts))

        for label, verts in regions:
            color = self._FIELD_COLORS.get(label, "#E0E0E0")
            poly = _Poly(verts, closed=True, facecolor=color, alpha=0.55,
                         edgecolor="none", zorder=0)
            ax.add_patch(poly)
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, label, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))

        for (outer, _names) in ordered:
            ax.plot([triple[0], outer[0]], [triple[1], outer[1]],
                    color="#1c2237", linewidth=1.2, zorder=1)
        ax.plot(triple[0], triple[1], marker="o", markersize=4,
                color="#1c2237", zorder=3)


# ---------------------------------------------------------------------------
# Fields from boundary segments — Agrawal et al. (2004), Verma et al.
# (2006), Agrawal et al. (2008)
# ---------------------------------------------------------------------------
# These papers print each boundary as two end points.  In a three-group
# panel the three meet at one triple point; in a four-group panel they
# meet at two, joined by a short boundary between them.  One routine
# covers both: a field is the stretch of frame between two consecutive
# boundary ends, closed back through the interior along the boundaries
# its group shares.

def field_segments(geom: Dict) -> Tuple:
    """Every boundary of *geom* as ``((x1, y1), (x2, y2), (g, g))``."""
    if "segments" in geom:
        return tuple(geom["segments"])
    triple = geom["triple"]
    return tuple((triple, outer, pair) for outer, pair in geom["boundaries"])


def _same_point(a, b, tol=1e-9):
    return abs(a[0] - b[0]) < tol and abs(a[1] - b[1]) < tol


def field_regions(geom: Dict, x_range=(-8, 8), y_range=(-8, 8)
                  ) -> Dict[str, list]:
    """Group name -> polygon vertices, for the fields *geom* draws."""
    segments = field_segments(geom)
    ends = []                                  # (point on frame, pair)
    for p, q, pair in segments:
        for point in (p, q):
            if np.isfinite(_perim_param(point, x_range, y_range)):
                ends.append((tuple(point), pair))
    ends.sort(key=lambda e: _perim_param(e[0], x_range, y_range))

    def interior_path(start, goal, group):
        """Nodes from *start* to *goal* along boundaries of *group*."""
        edges = [(tuple(p), tuple(q)) for p, q, pair in segments
                 if group in pair]
        frontier, seen = [[start]], {start}
        while frontier:
            path = frontier.pop(0)
            if _same_point(path[-1], goal):
                return path
            for p, q in edges:
                for a, b in ((p, q), (q, p)):
                    if _same_point(a, path[-1]) and b not in seen:
                        seen.add(b)
                        frontier.append(path + [b])
        return None

    regions: Dict[str, list] = {}
    for i, (end_a, pair_a) in enumerate(ends):
        end_b, pair_b = ends[(i + 1) % len(ends)]
        common = set(pair_a) & set(pair_b)
        if len(common) != 1:
            continue
        group = common.pop()
        back = interior_path(end_b, end_a, group)
        if back is None:
            continue
        corners = _frame_corners_between(end_a, end_b, x_range, y_range)
        regions[group] = [end_a, *corners, *back[:-1]]
    return regions


def field_of(geom: Dict, x, y, x_range=(-8, 8), y_range=(-8, 8)
             ) -> pd.Series:
    """The field each point ``(x, y)`` falls in; "" outside the frame or
    for a missing score."""
    from matplotlib.path import Path
    xs = pd.Series(x, dtype=float)
    ys = pd.Series(y, dtype=float).set_axis(xs.index)
    out = pd.Series("", index=xs.index, dtype=object)
    pts = np.column_stack([xs.to_numpy(), ys.to_numpy()])
    ok = np.isfinite(pts).all(axis=1)
    for group, verts in field_regions(geom, x_range, y_range).items():
        inside = Path(verts).contains_points(np.where(ok[:, None], pts, 0.0))
        out[ok & inside & (out == "").to_numpy()] = group
    return out


class _SegmentFieldsDF(_TripletDF):
    """Five panels whose fields come from printed boundary segments.

    ``panel_groups`` lists ``(panel key, group, group, ...)``; a panel
    may separate three groups or four.  ``fields`` maps the panel key
    to its geometry, which :func:`field_regions` turns into fields.
    """

    fields: Dict[str, Dict] = {}
    panel_groups: Tuple[Tuple[str, ...], ...] = ()

    _FIELD_COLORS = {
        "IAB":      "#FFE7D8",
        "CRB":      "#E7DFF6",
        "OIB":      "#E2F4D8",
        "MORB":     "#DFEBFB",
        "CRB+OIB":  "#EDE7DD",
    }

    def __init__(self):
        MultiPanelDiagram.__init__(self)
        panels = []
        for panel_key, *groups in self.panel_groups:
            names = "-".join(groups)
            panels.append(PanelSpec(
                key=panel_key,
                title="  ·  ".join(groups),
                x_label=f"DF1 ({names})",
                y_label=f"DF2 ({names})",
                x_range=(-8, 8),
                y_range=(-8, 8),
                field_polygons={g: [] for g in groups},
            ))
        self.panels = tuple(panels)
        self.field_label_fontsize = 11

    # The papers draw every panel on the (-8, +8) frame.
    def _maybe_rescale_panel(self, spec, df):
        return spec

    def classify_panel(self, df: pd.DataFrame, panel_key: str) -> pd.Series:
        """The field of every sample in one panel; "" where it cannot
        be placed."""
        spec = next(p for p in self.panels if p.key == panel_key)
        xs, ys = self._compute_xy_for_panel(spec, df)
        if xs is None:
            return pd.Series("", index=df.index, dtype=object)
        return field_of(self.fields[panel_key], xs, ys)

    def _draw_panel_background(self, ax, panel, options):
        from matplotlib.patches import Polygon as _Poly
        geom = self.fields[panel.key]
        x_range = panel.x_range or (-8, 8)
        y_range = panel.y_range or (-8, 8)
        for group, verts in field_regions(geom, x_range, y_range).items():
            ax.add_patch(_Poly(verts, closed=True,
                               facecolor=self._FIELD_COLORS.get(group, "#E0E0E0"),
                               alpha=0.55, edgecolor="none", zorder=0))
            cx, cy = _polygon_centroid(verts)
            ax.text(cx, cy, group, ha="center", va="center",
                    fontsize=self.field_label_fontsize, color="#1c2237",
                    fontweight="bold", zorder=2,
                    bbox=dict(facecolor="white", edgecolor="none",
                              alpha=0.75, boxstyle="round,pad=0.25"))
        junctions = []
        for p, q, _pair in field_segments(geom):
            ax.plot([p[0], q[0]], [p[1], q[1]], color="#1c2237",
                    linewidth=1.2, zorder=1)
            for point in (p, q):
                if not np.isfinite(_perim_param(point, x_range, y_range)):
                    junctions.append(point)
        for jx, jy in junctions:
            ax.plot(jx, jy, marker="o", markersize=4, color="#1c2237",
                    zorder=3)


class Agrawal2004(_SegmentFieldsDF):
    """Agrawal, Guevara & Verma (2004) — basic rocks, adjusted majors.

    The first of the group's discriminant-function schemes: functions
    of the SINCLAS-adjusted oxides themselves, not of log-ratios.
    Figure 2 separates all four settings; Figures 3A-3D take three at
    a time.  Coefficients from Tables 6 and 7, fields from the Figure 2
    and 3 captions (:data:`A04_FIELDS`).
    """
    key = "agrawal_2004_basic"
    composition_filter = "basic"
    title = "Agrawal et al. (2004) — Basic rocks, adjusted majors (5 DF panels)"
    citation = ("Agrawal S., Guevara M. & Verma S.P. (2004) International "
                "Geology Review 46, 575-594.  Discriminates IAB · CRB · OIB "
                "· MORB from the SINCLAS-adjusted major oxides (Middlemost "
                "1989 Fe2O3/FeO).  Functions from Tables 6 and 7, field "
                "boundaries from the Figure 2 and 3 captions.")
    coef_table = A04
    fields = A04_FIELDS
    panel_groups = (
        ("IAB_CRB_OIB_MORB", "IAB", "CRB", "OIB", "MORB"),
        ("IAB_CRB_OIB", "IAB", "CRB", "OIB"),
        ("IAB_CRB_MORB", "IAB", "CRB", "MORB"),
        ("IAB_OIB_MORB", "IAB", "OIB", "MORB"),
        ("CRB_OIB_MORB", "CRB", "OIB", "MORB"),
    )


class Verma2006(_SegmentFieldsDF):
    """Verma, Guevara & Agrawal (2006) — basic and ultrabasic rocks.

    The same four settings as Agrawal et al. (2004), now from ten
    log-ratios of the adjusted majors over SiO2.  Figure 5 separates all
    four; Figures 6a-6d take three at a time.  Coefficients from Tables
    6 and 7, fields from the Figure 5 and 6 captions
    (:data:`V06_FIELDS`).
    """
    key = "verma_2006_basic"
    composition_filter = "basic+ultrabasic"
    title = ("Verma et al. (2006) — Basic + ultrabasic rocks, major "
             "log-ratios (5 DF panels)")
    citation = ("Verma S.P., Guevara M. & Agrawal S. (2006) Journal of Earth "
                "System Science 115, 485-528.  Discriminates IAB · CRB · OIB "
                "· MORB from ln(oxide/SiO2) of the SINCLAS-adjusted majors.  "
                "Functions from Tables 6 and 7, field boundaries from the "
                "Figure 5 and 6 captions.")
    coef_table = V06
    fields = V06_FIELDS
    panel_groups = (
        ("IAB_CRB_OIB_MORB", "IAB", "CRB", "OIB", "MORB"),
        ("IAB_CRB_OIB", "IAB", "CRB", "OIB"),
        ("IAB_CRB_MORB", "IAB", "CRB", "MORB"),
        ("IAB_OIB_MORB", "IAB", "OIB", "MORB"),
        ("CRB_OIB_MORB", "CRB", "OIB", "MORB"),
    )


class Agrawal2008(_SegmentFieldsDF):
    """Agrawal, Guevara & Verma (2008) — basic and ultrabasic rocks.

    Four log-ratios of immobile traces over Th: ln(La/Th), ln(Sm/Th),
    ln(Yb/Th), ln(Nb/Th).  Figure 1 takes CRB and OIB together; Figures
    2A-2D take three settings at a time.  Equations from Table 6, fields
    from the Figure 1 and 2 captions (:data:`A08_FIELDS`).
    """
    key = "agrawal_2008_basic"
    composition_filter = "basic+ultrabasic"
    title = ("Agrawal et al. (2008) — Basic + ultrabasic rocks, "
             "La-Sm-Yb-Nb-Th (5 DF panels)")
    citation = ("Agrawal S., Guevara M. & Verma S.P. (2008) International "
                "Geology Review 50, 1057-1079.  Discriminates IAB · CRB · OIB "
                "· MORB from ln(La/Th), ln(Sm/Th), ln(Yb/Th) and ln(Nb/Th).  "
                "Equations from Table 6, field boundaries from the Figure 1 "
                "and 2 captions.")
    coef_table = A08
    fields = A08_FIELDS
    panel_groups = (
        ("IAB_CRBOIB_MORB", "IAB", "CRB+OIB", "MORB"),
        ("IAB_CRB_OIB", "IAB", "CRB", "OIB"),
        ("IAB_CRB_MORB", "IAB", "CRB", "MORB"),
        ("IAB_OIB_MORB", "IAB", "OIB", "MORB"),
        ("CRB_OIB_MORB", "CRB", "OIB", "MORB"),
    )
