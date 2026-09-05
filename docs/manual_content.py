"""Structured content for the B.I.R.D.S user manual.

The same content is rendered to DOCX and PDF by the sibling scripts so we
keep a single source of truth here.
"""

from __future__ import annotations


TITLE = "B.I.R.D.S — User Manual"
SUBTITLE = "Broad Igneous Rocks — Diagrams & Statistics · Version 0.1.0"


# Each section is a tuple: (title, list of paragraphs / structured blocks)
#
# Structured blocks: dicts of the form
#   {"type": "p",      "text": "..."}                  – paragraph
#   {"type": "h2",     "text": "..."}                  – sub-heading
#   {"type": "bullet", "items": ["...", "..."]}        – bullet list
#   {"type": "code",   "text": "..."}                  – fixed-width code block
#   {"type": "note",   "text": "..."}                  – call-out box

SECTIONS = [
    ("1. About B.I.R.D.S", [
        {"type": "p", "text":
         "B.I.R.D.S (Broad Igneous Rocks — Diagrams & Statistics) is a desktop "
         "application for plotting and analysing whole-rock geochemical "
         "data of igneous rocks. It bundles 52 plotting templates, a "
         "spider-diagram engine with 28 published normalisers "
         "(REE chondrites and shales, multi-element references and "
         "Ni-Cu-PGE metal references), a discrimination module with 33 "
         "tectonic diagrams, and a statistics dashboard with REE-anomaly "
         "indices and a correlation-matrix heat-map."},
        {"type": "p", "text":
         "The software is built on top of the open scientific Python "
         "stack (PySide6, matplotlib, pandas, NumPy, SciPy) and runs "
         "identically on Windows, macOS and Linux. No prior programming "
         "experience is required to use it."},
        {"type": "h2", "text": "Citation"},
        {"type": "p", "text":
         "If you use B.I.R.D.S in a publication, please cite the "
         "underlying references printed in each plot's subtitle, plus "
         "the software itself: Torres, D. (2026). B.I.R.D.S — Broad "
         "Igneous Rocks: Diagrams & Statistics (v0.1.0)."},
    ]),

    ("2. System requirements", [
        {"type": "bullet", "items": [
            "Operating system: Windows 10 or later, macOS 11 (Big Sur) "
            "or later, or any modern Linux distribution.",
            "Memory: at least 4 GB RAM (8 GB recommended for large "
            "datasets).",
            "Disk space: ~500 MB including Python + libraries.",
            "Python 3.9 or later (3.11 recommended).",
            "An internet connection is needed only for the initial "
            "library installation.",
        ]},
    ]),

    ("3. Installation — Windows", [
        {"type": "h2", "text": "3.1  Install Python"},
        {"type": "bullet", "items": [
            "Open your web browser and go to https://www.python.org/downloads/windows/",
            "Click the yellow “Download Python 3.x.x” button (3.11 or 3.12 are good choices).",
            "Run the downloaded installer. On the first screen, tick "
            "“Add python.exe to PATH” (this is important).",
            "Click “Install Now” and wait until it finishes. Click “Close”.",
        ]},
        {"type": "h2", "text": "3.2  Download B.I.R.D.S"},
        {"type": "bullet", "items": [
            "Open the BIRDS distribution (e.g. a ZIP file or a folder you received).",
            "Extract it to a memorable location — for instance C:\\Users\\<your-name>\\BIRDS",
        ]},
        {"type": "h2", "text": "3.3  Install the required libraries"},
        {"type": "bullet", "items": [
            "Open the Start menu, type cmd and press Enter to open the Command Prompt.",
            "Navigate to the BIRDS folder you just extracted, for example:",
        ]},
        {"type": "code", "text": "cd C:\\Users\\<your-name>\\BIRDS"},
        {"type": "bullet", "items": [
            "Install the required Python libraries by typing:",
        ]},
        {"type": "code", "text": "pip install -r requirements.txt"},
        {"type": "bullet", "items": [
            "Wait a few minutes while pip downloads PySide6, matplotlib, "
            "pandas, NumPy, SciPy and openpyxl.",
        ]},
        {"type": "h2", "text": "3.4  Launch the application"},
        {"type": "bullet", "items": [
            "From the same Command Prompt window, type:",
        ]},
        {"type": "code", "text": "python main.py"},
        {"type": "bullet", "items": [
            "The B.I.R.D.S welcome screen should appear within a few "
            "seconds.",
        ]},
        {"type": "note", "text":
         "Tip: to create a desktop shortcut, right-click an empty area "
         "of the desktop → New → Shortcut, paste the full path "
         "“C:\\Python311\\python.exe C:\\Users\\<your-name>\\BIRDS\\main.py” "
         "and name it B.I.R.D.S."},
    ]),

    ("4. Installation — macOS", [
        {"type": "h2", "text": "4.1  Install Python"},
        {"type": "bullet", "items": [
            "macOS comes with an old Python by default. Install a modern "
            "version from https://www.python.org/downloads/macos/",
            "Download the universal2 .pkg installer for Python 3.11 or 3.12.",
            "Run the installer and follow the on-screen instructions.",
            "Alternative: if you already use Homebrew, run `brew install python@3.11`.",
        ]},
        {"type": "h2", "text": "4.2  Download B.I.R.D.S"},
        {"type": "bullet", "items": [
            "Extract the BIRDS folder to ~/Documents/BIRDS or any other "
            "convenient location.",
        ]},
        {"type": "h2", "text": "4.3  Install the libraries"},
        {"type": "bullet", "items": [
            "Open Finder → Applications → Utilities → Terminal.",
            "Navigate to the BIRDS folder, e.g.:",
        ]},
        {"type": "code", "text": "cd ~/Documents/BIRDS"},
        {"type": "bullet", "items": [
            "Install the dependencies with pip:",
        ]},
        {"type": "code", "text": "python3 -m pip install --user -r requirements.txt"},
        {"type": "h2", "text": "4.4  Launch the application"},
        {"type": "code", "text": "python3 main.py"},
        {"type": "note", "text":
         "On Apple-silicon Macs (M1/M2/M3) make sure you use the "
         "universal2 Python installer; PySide6 wheels are not yet "
         "available for some older Intel-only builds."},
    ]),

    ("5. The B.I.R.D.S interface", [
        {"type": "p", "text":
         "When you launch B.I.R.D.S you are greeted by the welcome "
         "screen with the logo and a short tip. The menu bar at the top "
         "of the window contains six top-level menus:"},
        {"type": "bullet", "items": [
            "Data — import / save data, edit plot style, export plot, exit.",
            "Classification diagrams — TAS, AFM, Jensen, Frost, etc.",
            "Bivariate diagrams — single and paired Harker-style plots.",
            "Spider diagrams — REE and multi-element patterns.",
            "Tectonic diagrams — 14 discrimination diagrams.",
            "Statistics and Anomalies — descriptive statistics, REE "
            "anomalies, correlation matrix.",
        ]},
        {"type": "p", "text":
         "A persistent toolbar above the plotting area shows a “← Home” "
         "button that always returns you to the welcome screen, no "
         "matter which window you are in."},
    ]),

    ("6. Loading your data", [
        {"type": "h2", "text": "6.1  Supported formats"},
        {"type": "bullet", "items": [
            ".csv (comma, semicolon, tab or pipe delimited)",
            ".tsv (tab delimited)",
            ".xls and .xlsx (Microsoft Excel)",
        ]},
        {"type": "p", "text":
         "B.I.R.D.S auto-detects the delimiter and encoding "
         "(UTF-8 / Latin-1 / Windows-1252) and converts European "
         "decimal commas to dots automatically. Comment lines beginning "
         "with “#” at the top of the file are skipped."},
        {"type": "h2", "text": "6.2  Expected column names"},
        {"type": "p", "text":
         "Use standard element symbols and oxide formulas. Examples:"},
        {"type": "code", "text":
         "SiO2, TiO2, Al2O3, FeOT, MnO, MgO, CaO, Na2O, K2O, P2O5,\n"
         "La, Ce, Pr, Nd, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu, Y,\n"
         "Rb, Sr, Cs, Ba, Th, U, Nb, Ta, Zr, Hf, Pb, V, Sc, Co, Ni"},
        {"type": "p", "text":
         "Matching is case-insensitive (SiO2, sio2 and  SiO2 are "
         "equivalent). At least one numeric column is required."},
        {"type": "h2", "text": "6.3  Import dialog"},
        {"type": "bullet", "items": [
            "Click Data → Import (.xls / .csv).",
            "Browse to your file and select it.",
            "For Excel files, pick the sheet you want to load.",
            "A preview of the first 20 rows confirms the columns were "
            "parsed correctly.",
            "Click “Import” to load the data into B.I.R.D.S.",
        ]},
        {"type": "h2", "text": "6.4  Define groups (recommended)"},
        {"type": "bullet", "items": [
            "Open Data → Edit plot.",
            "Pick up to 3 grouping columns (for instance: Type, Locality, Age).",
            "B.I.R.D.S auto-fills the group names from the unique values "
            "in those columns. You can edit each name, colour and symbol.",
            "Click OK. From now on every plot will respect those group "
            "styles.",
        ]},
    ]),

    ("7. Classification diagrams", [
        {"type": "p", "text":
         "Open Classification diagrams → Volcanic (or → Plutonic). The "
         "window has two panels: controls on the left, the plot on the "
         "right."},
        {"type": "h2", "text": "Available diagrams (volcanic)"},
        {"type": "bullet", "items": [
            "TAS — Total Alkalis vs Silica (Le Bas et al. 1986).",
            "K2O vs SiO2 — Peccerillo & Taylor (1976).",
            "Alkalic / Sub-alkalic boundary on TAS (Irvine & Baragar 1971).",
            "AFM — Tholeiitic vs Calc-alkaline (Irvine & Baragar 1971 + Rollinson 2021).",
            "Jensen cation plot — high-Mg discrimination.",
            "Hanski [Al2O3] vs [TiO2] for komatiites.",
            "High-Mg subdivision on TAS (Le Maitre et al. 2002).",
        ]},
        {"type": "h2", "text": "Available diagrams (plutonic)"},
        {"type": "bullet", "items": [
            "TAS plutonic — Wilson (1989) / Cox et al. (1979).",
            "Normative An–Ab–Or — Barker (1979).",
            "Frost et al. (2001) — Fe-index, MALI, ASI, AI vs FSSI.",
            "Ab–Or–Q haplogranite — Tuttle & Bowen (1958).",
        ]},
        {"type": "p", "text":
         "Use the controls on the left to edit axis labels, font, "
         "legend location, and to enable a convex-hull shaded range "
         "per group."},
    ]),

    ("8. Bivariate diagrams", [
        {"type": "p", "text":
         "Two sub-modes are available from the menu:"},
        {"type": "bullet", "items": [
            "Individual — single bivariate plot. Pick any two numeric "
            "columns for X and Y.",
            "Paired — multi-panel Harker / matrix plot. Select one X "
            "and several Y columns (or vice-versa) for a near-square "
            "grid; or several of both for a full X × Y matrix.",
        ]},
        {"type": "h2", "text": "Optional overlays"},
        {"type": "bullet", "items": [
            "Linear regression line per group or overall, with optional "
            "95 % confidence band and printed equation + R² in the legend.",
            "Convex-hull shaded range per group.",
            "Reservoir overlays — tick reference compositions (Bulk CC, "
            "N-MORB, OIB, KLB-1, …) to add labelled stars at the "
            "corresponding (X, Y) coordinates.",
        ]},
    ]),

    ("9. Spider diagrams", [
        {"type": "p", "text":
         "Choose Spider diagrams → REE for rare-earth patterns, or → "
         "Multi-elements for incompatible-element patterns. The "
         "reference combo on the left lets you pick:"},
        {"type": "bullet", "items": [
            "8 REE chondrite normalisers (Sun & McDonough 1989, "
            "McDonough & Sun 1995, Pourmand 2012, Barrat 2012, "
            "Boynton 1984, Anders & Grevesse 1989, Taylor & McLennan "
            "1985, Wakita 1971).",
            "6 REE shale composites (NASC, PAAS, MUQ, European Shale, "
            "World Shale Average, UCC).",
            "9 multi-element references (Primitive Mantle ×2, CI "
            "Chondrite, N-MORB ×2, E-MORB, UCC, Bulk CC, NASC).",
        ]},
        {"type": "h2", "text": "Plot modes"},
        {"type": "bullet", "items": [
            "Individual sample lines (default).",
            "Group summary — median + min–max envelope per group.",
        ]},
        {"type": "p", "text":
         "Reservoir patterns can be overlaid as dashed reference lines. "
         "Major elements K, Ti and P are auto-converted from wt.% oxide "
         "to ppm element so they sit on the same vertical scale as the "
         "trace data."},
    ]),

    ("10. Tectonic discriminators", [
        {"type": "p", "text":
         "Open Tectonic diagrams → Volcanic or → Plutonic. Inside the "
         "window, choose the composition (Mafic, Intermediate or Acid) "
         "and the specific discriminator from the second combo. 14 "
         "published discriminators are implemented with their original "
         "field boundaries:"},
        {"type": "h2", "text": "Mafic"},
        {"type": "bullet", "items": [
            "Pearce (2008) Th/Yb vs Nb/Yb — crustal-input proxy.",
            "Pearce (2008) Ti/Yb vs Nb/Yb — melting-depth proxy.",
            "Pearce & Gale (1977) Ti/Y vs Zr/Y.",
            "Shervais (1982) / Vermeesch (2006) Ti vs V.",
            "Pearce & Cann (1973) Zr vs Ti.",
            "Saccani (2015) Nb_N vs Th_N.",
            "Wood (1980) Th – Hf/3 – Ta ternary.",
            "Cabanis & Lecolle (1989) La/10 – Y/15 – Nb/8 ternary.",
        ]},
        {"type": "h2", "text": "Intermediate"},
        {"type": "bullet", "items": [
            "Defant & Drummond (1990) Y vs Sr/Y — adakite.",
            "Defant & Drummond (1990) Yb vs La/Yb — adakite.",
        ]},
        {"type": "h2", "text": "Acid (granitoids)"},
        {"type": "bullet", "items": [
            "Pearce et al. (1984) Ta vs Yb.",
            "Pearce et al. (1984) Nb vs Y.",
            "Pearce et al. (1984) Rb vs (Yb+Ta).",
            "Pearce et al. (1984) Rb vs (Y+Nb).",
        ]},
    ]),

    ("11. Statistics and Anomalies", [
        {"type": "p", "text":
         "Click Statistics and Anomalies → Open dashboard to compute "
         "every available statistic in one click. A “Refresh” button "
         "and a chondrite-reference selector live at the top of the "
         "window. Five tabs hold the results:"},
        {"type": "bullet", "items": [
            "Descriptive — count, mean, std, percentiles, median, MAD, "
            "%RSD, skewness and kurtosis for every numeric column.",
            "By group — the same statistics broken down by your "
            "grouping column(s).",
            "REE anomalies & ratios — Eu/Eu*, Ce/Ce*, Pr/Pr*, Gd/Gd*, "
            "Y/Y*, Y/Ho (raw), and the normalised (La/Yb)_N, "
            "(La/Sm)_N, (Gd/Yb)_N, (Sm/Yb)_N per sample. Positive "
            "anomalies are highlighted in pink, negative in light blue.",
            "Trace-element ratios — 15 commonly used ratios per sample "
            "(La/Yb, Zr/Y, Th/Yb, Nb/Y, Ti/V, Ba/Nb, Rb/Sr, …).",
            "Correlation matrix — Pearson r heatmap of up to 30 "
            "numeric columns, with cell annotations if the matrix fits "
            "on screen.",
        ]},
    ]),

    ("12. Saving results", [
        {"type": "h2", "text": "12.1  Save the statistics report"},
        {"type": "bullet", "items": [
            "Click Data → Save → Save file.",
            "Choose .xlsx (recommended — one sheet per section) or .csv.",
            "Tick the sections you want (original data, descriptive, "
            "by-group, anomalies, trace ratios, correlation).",
            "Click Save.",
        ]},
        {"type": "h2", "text": "12.2  Export a plot"},
        {"type": "bullet", "items": [
            "Make sure the plot you want is the one currently visible.",
            "Click Data → Save → Export plot.",
            "Pick the format (.png, .jpg, .pdf, .svg) and the DPI "
            "(72–1200) and image dimensions in inches.",
            "Tick “Tight bounding box” to trim the margins and "
            "“Transparent background” for PNG / SVG figures meant for "
            "overlays.",
        ]},
    ]),

    ("13. Troubleshooting", [
        {"type": "h2", "text": "“ModuleNotFoundError: No module named 'PySide6'”"},
        {"type": "p", "text":
         "The libraries are not installed yet. Run `pip install -r "
         "requirements.txt` from inside the BIRDS folder."},

        {"type": "h2", "text": "The CSV won't load"},
        {"type": "p", "text":
         "Open the file in a text editor and check that the first line "
         "contains the column headers, that there are no blank lines "
         "above them and that all rows have the same number of fields. "
         "If the file uses decimal commas (e.g. 50,5) B.I.R.D.S "
         "converts them automatically, but make sure the field "
         "separator is consistent (the same delimiter on every line)."},

        {"type": "h2", "text": "A diagram shows the background but no samples"},
        {"type": "p", "text":
         "The diagram needs specific elements that are not present in "
         "your data. Look at the diagram's subtitle for the required "
         "columns and either rename your columns to match or add the "
         "missing measurements."},

        {"type": "h2", "text": "Group names don't match the legend"},
        {"type": "p", "text":
         "The legend label uses the name you typed in Data → Edit plot, "
         "matched to the i-th unique value of the grouping column. If "
         "the order looks wrong, reopen Edit plot and re-tick the "
         "column — names auto-refill in the order the values appear in "
         "the file."},

        {"type": "h2", "text": "Plot export looks pixelated"},
        {"type": "p", "text":
         "Increase the DPI in the Export plot dialog (300 dpi for "
         "submitted manuscripts, 600 dpi for camera-ready figures). For "
         "lossless quality prefer .pdf or .svg, which are vector "
         "formats."},
    ]),

    ("14. References", [
        {"type": "p", "text":
         "B.I.R.D.S implements diagrams and statistics from the "
         "following sources. Cite each one according to the diagram you "
         "used in your figures and tables."},
        {"type": "bullet", "items": [
            "Rollinson, H.R., Pease, V. (2021). Using Geochemical Data "
            "to Understand Geological Processes (2nd ed.). Cambridge "
            "University Press.",
            "Pearce, J.A. (2008). Geochemical fingerprinting of oceanic "
            "basalts with applications to ophiolite classification and "
            "the search for Archean oceanic crust. Lithos 100, 14–48.",
            "Vermeesch, P. (2006a). Tectonic discrimination diagrams "
            "revisited. G-cubed 7, Q06017.",
            "Verma, S.P. and co-authors (2006–2017). Multi-dimensional "
            "tectonomagmatic discrimination diagrams (multiple papers).",
            "Yang, Z.-F. et al. (2019). Using major element logratios "
            "to recognize compositional patterns of basalt. J. Geophys. "
            "Res. Solid Earth 124, 3458–3490.",
            "Sun, S.-S., McDonough, W.F. (1989). Chemical and isotopic "
            "systematics of oceanic basalts. GSL Sp. Pub. 42, 313–345.",
            "McDonough, W.F., Sun, S.-S. (1995). The composition of the "
            "Earth. Chem. Geol. 120, 223–253.",
            "Rudnick, R.L., Gao, S. (2003). Composition of the "
            "continental crust. Treatise on Geochemistry 3, 1–64.",
            "Taylor, S.R., McLennan, S.M. (1985). The continental "
            "crust: its composition and evolution. Blackwell.",
            "Pourmand, A., Dauphas, N., Ireland, T.J. (2012). A novel "
            "extraction chromatography and MC-ICP-MS technique for "
            "rapid analysis of REE. Chem. Geol. 291, 38–54.",
        ]},
    ]),
]
