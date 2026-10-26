"""Generate the B.I.R.D.S workflow flowchart for publication.

Produces a vector PDF (preferred for journals) and a 300-dpi PNG.

Every count in the figure is read from the program itself rather than
typed in: the earlier version said 14 tectonic diagrams and five
statistics tabs long after there were 34 and eight, and left out four
of the eleven menus.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


# Colour palette (soft, publication-friendly)
C_INPUT   = "#FCE7CB"  # peach
C_CORE    = "#D9E7F2"  # light blue
C_MODULE  = "#E1F0DE"  # light green
C_OUTPUT  = "#F2D7E2"  # rose
C_EDGE    = "#3B4252"


def _box(ax, x, y, w, h, text, *, fc=C_CORE, fontsize=10, weight="normal"):
    """Add a rounded box with centred text."""
    patch = FancyBboxPatch(
        (x - w / 2, y - h / 2), w, h,
        boxstyle="round,pad=0.06,rounding_size=0.12",
        linewidth=1.2, edgecolor=C_EDGE, facecolor=fc, zorder=2,
    )
    ax.add_patch(patch)
    ax.text(x, y, text, ha="center", va="center",
            fontsize=fontsize, color="#1c2237", weight=weight,
            linespacing=1.35, zorder=3)


def _arrow(ax, x1, y1, x2, y2, *, mut=14, lw=1.4):
    """Add a fancy arrow between two anchor points."""
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=mut, linewidth=lw,
        color=C_EDGE, zorder=1,
    ))


def program_counts() -> dict:
    """The numbers the figure quotes, taken from the code."""
    from birds.diagrams.catalog import (
        CLASSIFICATION_PLUTONIC,
        CLASSIFICATION_VOLCANIC,
        TECTONIC_PLUTONIC,
        TECTONIC_VOLCANIC,
    )
    from birds.normalizations import (
        CHALCOPHILE_NORMS,
        MULTIELEMENT_NORMS,
        REE_CHONDRITES,
        REE_SHALES,
    )
    from birds.reservoirs import RESERVOIRS
    from birds.tectonic_results import DISCRIMINATORS
    from birds.views import statistics
    from birds.views.petrography import _PETROGRAPHY_CATALOG

    tables = (REE_CHONDRITES, REE_SHALES, MULTIELEMENT_NORMS,
              CHALCOPHILE_NORMS)
    return {
        "classification": len({k for _l, k in CLASSIFICATION_VOLCANIC}
                              | {k for _l, k in CLASSIFICATION_PLUTONIC}),
        "tectonic": len({k for cat in (TECTONIC_VOLCANIC, TECTONIC_PLUTONIC)
                         for section in cat.values() for _l, k in section}),
        "normalisers": sum(len(t) for t in tables),
        "by_kind": tuple(len(t) for t in tables),
        "reservoirs": len(RESERVOIRS),
        "parameters": len(DISCRIMINATORS),
        "statistics_tabs": len(re.findall(
            r"self\._add_tab\(", Path(statistics.__file__).read_text(encoding="utf-8"))),
        "petrography": len(_PETROGRAPHY_CATALOG),
    }


def build_flowchart(out_pdf: Path, out_png: Path) -> None:
    n = program_counts()
    chondrite, shale, multi, metals = n["by_kind"]

    fig, ax = plt.subplots(figsize=(10.0, 12.6))
    fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13.4)
    ax.axis("off")

    # Title (above the diagram)
    ax.text(5.0, 13.0,
            "B.I.R.D.S — Broad Igneous Rocks · Diagrams & Statistics",
            ha="center", va="center", fontsize=15, weight="bold",
            color="#0d1b3d")
    ax.text(5.0, 12.55, "Application workflow",
            ha="center", va="center", fontsize=11, style="italic",
            color="#5b6478")

    # ── 1. Input ────────────────────────────────────────────────────────
    _box(ax, 5.0, 11.75, 6.6, 0.72,
         "Geochemical dataset\n"
         ".csv  ·  .tsv  ·  .xls  ·  .xlsx     or a saved session (.birds)",
         fc=C_INPUT, fontsize=10, weight="bold")
    _arrow(ax, 5.0, 11.33, 5.0, 11.12)

    # ── 2. Core layer ───────────────────────────────────────────────────
    core = (
        (10.7, "Import\n"
               "delimiter and encoding detected  ·  decimal comma → dot  ·  "
               "values below detection (<0.5, b.d.l.) converted"),
        (9.7, "Sample grouping\n"
              "up to three grouping columns  ·  names, colours and "
              "markers  ·  groups shown or hidden"),
        (8.7, "Reference catalogue\n"
              f"{n['reservoirs']} reservoirs  ·  {n['normalisers']} "
              f"normalisers (REE chondrite {chondrite}, shale {shale}, "
              f"multi-element {multi}, Ni-Cu-PGE {metals})"),
    )
    for i, (y, text) in enumerate(core):
        _box(ax, 5.0, y, 8.4, 0.62, text, fc=C_CORE, fontsize=8.8)
        if i < len(core) - 1:
            _arrow(ax, 5.0, y - 0.37, 5.0, y - 0.63)
    _arrow(ax, 5.0, 8.33, 5.0, 8.07)

    # ── 3. Analytical modules, one menu each ────────────────────────────
    ax.add_patch(FancyBboxPatch(
        (0.1, 2.95), 9.8, 5.03,
        boxstyle="round,pad=0.04,rounding_size=0.15", linewidth=1.0,
        linestyle=(0, (4, 3)), edgecolor="#8a93a6", facecolor="none",
        zorder=1))
    ax.text(0.3, 7.76, "Analytical modules — one menu each",
            ha="left", va="center", fontsize=8.5, style="italic",
            color="#5b6478")

    modules = (
        (f"Classification ({n['classification']})",
         "TAS volcanic & plutonic  ·  K₂O–SiO₂\n"
         "AFM · Jensen · Hanski · Barker · Frost\n"
         "A/CNK–A/NK  ·  Ab–Or–Q\n"
         "Th–Co · Zr/TiO₂–Nb/Y (altered rocks)"),
        ("Bivariate",
         "Individual and paired (Harker, matrix)\n"
         "OLS regression with 95 % band\n"
         "Reservoir overlays  ·  group hulls"),
        ("Spider diagrams",
         "REE and multi-element patterns\n"
         f"{n['normalisers']} normalisers, Ni-Cu-PGE included\n"
         "Sample lines or group medians"),
        (f"Tectonic discrimination ({n['tectonic']})",
         "Pearce · Saccani · Pearce & Gale\n"
         "Pearce et al. 1984 · Harris · Wood\n"
         "Defant & Drummond · Yang (FCMS)\n"
         "Vermeesch · Verma DF with probabilities"),
        (f"Statistics & anomalies ({n['statistics_tabs']} tabs)",
         "Descriptive · by group · paper table\n"
         "Eu/Eu*, Ce/Ce* …  ·  trace ratios\n"
         "Correlation matrix\n"
         f"{n['parameters']} tectonic parameters"),
        ("Isotopes",
         "Sr–Nd with εNd, εSr\n"
         "and initial ratios\n"
         "Pb–Pb (²⁰⁷Pb, ²⁰⁸Pb) with the NHRL"),
        (f"Petrography ({n['petrography']})",
         "QAPF plutonic and volcanic\n"
         "Gabbroic  ·  ultramafic\n"
         "Pyroclastic tuffs"),
        ("CIPW norm",
         "Classical CIPW (1903)\n"
         "Normative minerals as new columns,\n"
         "ready for any diagram"),
        ("Map & kriging",
         "Decimal · DMS · UTM · MGRS\n"
         "Ordinary kriging, per group\n"
         "Variogram · cross-validation\n"
         "Grids for a GIS (.asc)"),
    )
    xs = (1.78, 5.0, 8.22)
    ys = (6.8, 5.3, 3.8)
    for i, (head, body) in enumerate(modules):
        x, y = xs[i % 3], ys[i // 3]
        _box(ax, x, y, 2.9, 1.25, "", fc=C_MODULE)
        ax.text(x, y + 0.42, head, ha="center", va="center", fontsize=8.8,
                weight="bold", color="#1c2237", zorder=3)
        ax.text(x, y - 0.14, body, ha="center", va="center", fontsize=7.9,
                color="#1c2237", linespacing=1.35, zorder=3)

    # ── 4. Output ───────────────────────────────────────────────────────
    _arrow(ax, 5.0, 2.98, 5.0, 2.66)
    _box(ax, 5.0, 2.1, 9.0, 0.95,
         "Outputs\n"
         "Plots: .png · .jpg · .pdf · .svg (72–1200 dpi)   ·   "
         "statistics report: .xlsx · .csv\n"
         "Kriged grids for a GIS: .asc + .prj   ·   sessions: .birds",
         fc=C_OUTPUT, fontsize=9, weight="bold")

    # ── 5. Footer ───────────────────────────────────────────────────────
    ax.text(5.0, 1.22,
            "Implemented in Python 3 with PySide6, matplotlib, pandas, "
            "NumPy and SciPy. Nothing is downloaded once installed.",
            ha="center", va="center", fontsize=8.5, color="#5b6478",
            style="italic")
    ax.text(5.0, 0.9,
            "References: Rollinson & Pease (2021)  ·  Pearce (2008)  ·  "
            "Vermeesch (2006)  ·  Verma & co-authors (2006–2017)  ·  "
            "Yang et al. (2019)  ·  Matheron (1963)",
            ha="center", va="center", fontsize=8, color="#5b6478")

    # ── Legend ──────────────────────────────────────────────────────────
    legend_y = 0.4
    legend_items = (
        (C_INPUT, "Input"),
        (C_CORE, "Core layer"),
        (C_MODULE, "Analytical module"),
        (C_OUTPUT, "Output"),
    )
    legend_x = 1.0
    for color, label in legend_items:
        _box(ax, legend_x, legend_y, 0.32, 0.32, "", fc=color, fontsize=8)
        ax.text(legend_x + 0.28, legend_y, label,
                ha="left", va="center", fontsize=8, color="#1c2237")
        legend_x += 2.2

    fig.savefig(out_pdf, format="pdf", bbox_inches="tight")
    fig.savefig(out_png, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    out_pdf = HERE / "birds_flowchart.pdf"
    out_png = HERE / "birds_flowchart.png"
    build_flowchart(out_pdf, out_png)
    print(f"PDF: {out_pdf} ({out_pdf.stat().st_size} bytes)")
    print(f"PNG: {out_png} ({out_png.stat().st_size} bytes)")
