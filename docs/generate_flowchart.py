"""Generate the B.I.R.D.S workflow flowchart for publication.

Produces a vector PDF (preferred for journals) and a 300-dpi PNG.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


HERE = Path(__file__).resolve().parent


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
            wrap=True, zorder=3)


def _arrow(ax, x1, y1, x2, y2, *, mut=14, lw=1.4):
    """Add a fancy arrow between two anchor points."""
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>", mutation_scale=mut, linewidth=lw,
        color=C_EDGE, zorder=1,
    ))


def build_flowchart(out_pdf: Path, out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(10.0, 11.5), constrained_layout=True)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 13)
    ax.axis("off")

    # Title (above the diagram)
    ax.text(5.0, 12.6,
            "B.I.R.D.S — Broad Igneous Rocks · Diagrams & Statistics",
            ha="center", va="center", fontsize=15, weight="bold",
            color="#0d1b3d")
    ax.text(5.0, 12.15,
            "Application workflow",
            ha="center", va="center", fontsize=11, style="italic",
            color="#5b6478")

    # ── 1. Input ────────────────────────────────────────────────────────
    _box(ax, 5.0, 11.2, 6.0, 0.7,
         "Geochemical dataset\n(.csv  /  .tsv  /  .xls  /  .xlsx)",
         fc=C_INPUT, fontsize=10, weight="bold")
    _arrow(ax, 5.0, 10.83, 5.0, 10.45)

    # ── 2. Robust IO ─────────────────────────────────────────────────────
    _box(ax, 5.0, 10.0, 6.8, 0.85,
         "Robust I/O layer (io_utils.py)\n"
         "Auto-detect delimiter (, ; \\t |)  ·  UTF-8 / Latin-1 / CP1252  ·  "
         "decimal comma → dot",
         fc=C_CORE, fontsize=9)
    _arrow(ax, 5.0, 9.58, 5.0, 9.20)

    # ── 3. Sample grouping ───────────────────────────────────────────────
    _box(ax, 5.0, 8.75, 6.8, 0.85,
         "Sample grouping  ·  PlotStyle\n"
         "Up to 3 columns × 10 groups  ·  auto-fill from data  ·  "
         "editable names, colours, markers",
         fc=C_CORE, fontsize=9)
    _arrow(ax, 5.0, 8.33, 5.0, 7.95)

    # ── 4. Reservoir & normalisation catalogue ──────────────────────────
    _box(ax, 5.0, 7.5, 6.8, 0.85,
         "Reference catalogue\n"
         "16 reservoirs (R&G 2003, T&M 1985, S&M 1989, McDonough & Sun 1995, "
         "DMM, KLB-1, KR4003, MIX1G)  ·  25 normalisers",
         fc=C_CORE, fontsize=9)
    _arrow(ax, 5.0, 7.08, 5.0, 6.55)

    # ── 5. Five analytical modules ───────────────────────────────────────
    # Top row of three modules
    mods_top = [
        (1.45, 6.0,
         "Classification (11)\n"
         "TAS V/P  ·  K₂O–SiO₂  ·  AFM\n"
         "Jensen  ·  Hanski  ·  Barker\n"
         "Frost  ·  Haplogranite"),
        (5.00, 6.0,
         "Bivariate (Individual / Paired)\n"
         "Harker (1 X + n Y)  ·  matrix\n"
         "OLS regression with 95 % CI\n"
         "Reservoir overlays"),
        (8.55, 6.0,
         "Spider diagrams\n"
         "REE chondrite (8) / shale (6)\n"
         "Multi-element (PM, CI, MORB,\n"
         "UCC, BCC, NASC, …)"),
    ]
    for x, y, text in mods_top:
        _box(ax, x, y, 3.05, 1.3, text, fc=C_MODULE, fontsize=8.5)

    # Bottom row of two modules
    mods_bot = [
        (3.20, 4.30,
         "Tectonic discriminators (14)\n"
         "Pearce 2008 (Th/Yb, Ti/Yb)\n"
         "Shervais 1982  ·  Pearce & Cann 1973\n"
         "Pearce & Gale 1977  ·  Saccani 2015\n"
         "Defant & Drummond 1990 (×2)\n"
         "Pearce et al. 1984 (×4)\n"
         "Wood 1980  ·  Cabanis & Lecolle 1989"),
        (6.80, 4.30,
         "Statistics & Anomalies (5 tabs)\n"
         "Descriptive  +  median  /  MAD  /  %RSD\n"
         "skewness / kurtosis  ·  by group\n"
         "REE anomalies: Eu/Eu*, Ce/Ce*,\n"
         "Pr/Pr*, Gd/Gd*, Y/Y*, Y/Ho\n"
         "Normalised REE ratios\n"
         "Correlation matrix (Pearson heatmap)"),
    ]
    for x, y, text in mods_bot:
        _box(ax, x, y, 3.55, 1.85, text, fc=C_MODULE, fontsize=8.5)

    # Connector from row above into modules (vertical fan-out from y=6.55)
    for x_target in (1.45, 5.00, 8.55):
        _arrow(ax, 5.0, 6.55, x_target, 6.65, mut=12, lw=1.1)
    for x_target in (3.20, 6.80):
        _arrow(ax, 5.0, 6.55, x_target, 5.25, mut=12, lw=1.1)

    # ── 6. Output ───────────────────────────────────────────────────────
    _arrow(ax, 3.20, 3.38, 3.20, 2.95)
    _arrow(ax, 6.80, 3.38, 6.80, 2.95)
    _arrow(ax, 1.45, 5.35, 2.6, 2.95, mut=12, lw=1.1)
    _arrow(ax, 5.00, 5.35, 5.0, 2.95, mut=12, lw=1.1)
    _arrow(ax, 8.55, 5.35, 7.4, 2.95, mut=12, lw=1.1)

    _box(ax, 5.0, 2.45, 9.0, 1.0,
         "Outputs\n"
         "Publication-quality plots:  .png  ·  .jpg  ·  .pdf  ·  .svg  "
         "(72–1200 dpi, configurable size)\n"
         "Statistics report:  .xlsx  (one sheet per section)  ·  .csv  "
         "(concatenated)",
         fc=C_OUTPUT, fontsize=9, weight="bold")

    # ── 7. Footer ───────────────────────────────────────────────────────
    ax.text(5.0, 1.45,
            "Implemented in Python 3 with PySide6, matplotlib, pandas, "
            "NumPy and SciPy.",
            ha="center", va="center", fontsize=8.5, color="#5b6478",
            style="italic")
    ax.text(5.0, 1.10,
            "References: Rollinson & Pease (2021)  ·  Pearce (2008)  ·  "
            "Vermeesch (2006)  ·  Verma & co-authors (2006–2017)  ·  "
            "Yang et al. (2019)",
            ha="center", va="center", fontsize=8, color="#5b6478")

    # ── Legend ──────────────────────────────────────────────────────────
    legend_y = 0.5
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
