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
         "data of igneous rocks. It bundles 56 plotting templates, a "
         "spider-diagram engine with 28 published normalisers "
         "(REE chondrites and shales, multi-element references and "
         "Ni-Cu-PGE metal references), a discrimination module with 36 "
         "tectonic diagrams, and a statistics dashboard with REE-anomaly "
         "indices, a correlation-matrix heat-map and 208 tectonic "
         "discrimination parameters. A map view plots every sample at "
         "its longitude and latitude and kriges any numeric column "
         "across them, with the uncertainty of the result, and exports "
         "the surface as grids a GIS can open."},
        {"type": "p", "text":
         "Every field boundary is transcribed, measured or recomputed "
         "from the original publication rather than redrawn by eye. "
         "docs/DIAGRAM_PROVENANCE.md records which of the three it was, "
         "diagram by diagram, together with the handful whose sources do "
         "not permit it and what each would need."},
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
            "library installation. Once installed, nothing in "
            "B.I.R.D.S uses the network.",
            "Installed as an application — BIRDS.app on macOS, or "
            "through the Windows installer — B.I.R.D.S needs no Python "
            "at all, and about 400 MB of disk.",
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
        {"type": "h2", "text": "3.5  The installer"},
        {"type": "p", "text":
         "B.I.R.D.S can also be packaged as a Windows installer. The "
         "installed program needs no Python, has a Start-menu entry, "
         "and registers .birds sessions: they carry the session icon "
         "and open with a double-click. The installer is built on a "
         "Windows computer from the source, with PyInstaller and Inno "
         "Setup 6, following packaging/README.md; check the built "
         "program with BIRDS.exe --self-test before sharing it."},
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
        {"type": "h2", "text": "4.5  The application: BIRDS.app"},
        {"type": "p", "text":
         "Packaged as BIRDS.app, B.I.R.D.S runs without Python, opens "
         "from Launchpad or the Dock like any other program, and macOS "
         "knows its sessions: every .birds file carries the session "
         "icon and opens in B.I.R.D.S with a double-click."},
        {"type": "bullet", "items": [
            "If you received BIRDS.app: drag it into Applications. The "
            "first time, right-click it and choose Open, then Open "
            "again — the app is not signed with an Apple developer "
            "certificate, so macOS asks once. After that it opens "
            "normally.",
            "To build it yourself, with the libraries of section 4.3 "
            "installed, add PyInstaller once and run the updater from "
            "the BIRDS folder:",
        ]},
        {"type": "code", "text": "python3 -m pip install pyinstaller"},
        {"type": "code", "text": "python3 packaging/update_mac_app.py"},
        {"type": "p", "text":
         "In about a minute it builds the app, checks it with its "
         "self-test and, only if that passes, puts it in Applications, "
         "replacing an older copy. Close B.I.R.D.S before running it."},
        {"type": "h2", "text": "4.6  Keeping the application up to date"},
        {"type": "p", "text":
         "BIRDS.app is a snapshot of the source as it was when built: "
         "changes to the source reach it only when it is rebuilt. Run "
         "python3 packaging/update_mac_app.py again — sessions, "
         "settings and the .birds association carry over. In the "
         "meantime python3 main.py always runs the source as it "
         "stands."},
        {"type": "note", "text":
         "If .birds files still show a plain page right after the "
         "first install, relaunch the Finder: hold Option, right-click "
         "its icon in the Dock and choose Relaunch. macOS draws a new "
         "document icon in the background and shows the plain page "
         "until it is ready."},
    ]),

    ("5. The B.I.R.D.S interface", [
        {"type": "p", "text":
         "When you launch B.I.R.D.S you are greeted by the welcome "
         "screen with the logo and a short tip. The menu bar at the top "
         "of the window holds eleven menus, from left to right:"},
        {"type": "bullet", "items": [
            "Data — sessions, data import, the data table, detection "
            "limits, plot style, pre-processing of the majors, and the "
            "export of reports and plots.",
            "Map — sample locations and kriging (section 12).",
            "Petrography — the IUGS modal diagrams: QAPF plutonic and "
            "volcanic (each with its own fields, numbered as the IUGS "
            "numbers them, with a key), gabbroic, ultramafic, and two "
            "tuff schemes — Schmid (1981), which the IUGS recommends, "
            "and a finer banded one.",
            "Norm — the classical CIPW norm.",
            "Classification diagrams — TAS, K2O–SiO2, AFM, Jensen, "
            "Frost and others, volcanic and plutonic.",
            "Bivariate diagrams — single and paired Harker-style plots.",
            "Spider diagrams — REE and multi-element patterns.",
            "Tectonic diagrams — 34 discrimination diagrams.",
            "Isotopes — Sr–Nd and Pb–Pb diagrams, and any isotope ratio, "
            "δ value or ε against SiO2.",
            "Statistics and Anomalies — descriptive statistics, REE "
            "anomalies, correlation matrix and tectonic discrimination "
            "parameters.",
            "References — the full bibliography.",
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
        {"type": "p", "text":
         "The template in the templates folder, BIRDS_data_template.xlsx, "
         "has a Data sheet for the bulk analyses and optional Isotopes "
         "and Petrography sheets, joined to Data by Sample_Name. The "
         "Isotopes sheet opens with the same columns, in the same order, "
         "as Data has before its major elements — identification, "
         "location, source, geology and analysis — so a sample's "
         "context can be copied across in one block; then comes SiO2, "
         "to read the isotopes against silica, and the isotope systems. "
         "Where a column is filled on both sheets, the Data value is "
         "kept, except that a blank Sample_Label or Group fills in from "
         "Isotopes. Age is read with its Age_Unit (Ma, ka, Ga or yr) "
         "for the initial-ratio correction."},
        {"type": "h2", "text": "6.3  Import dialog"},
        {"type": "bullet", "items": [
            "Click Data → Import data (.xls / .csv)…",
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
            "in those columns — up to 25 groups, each with its own colour "
            "and no two with the same colour and symbol. You can edit each "
            "name, colour and symbol. With many groups, set the legend "
            "to Outside so it does not cover the plot.",
            "Click OK. From now on every plot will respect those group "
            "styles.",
        ]},
        {"type": "h2", "text": "6.5  Adjusting the majors to 100 %"},
        {"type": "p", "text":
         "Data → Pre-process majors… recalculates the major oxides to "
         "100 wt % — anhydrous by default, removing LOI, H2O and CO2 — "
         "and splits total iron between Fe2O3 and FeO after Middlemost "
         "(1989), Le Maitre (1976) or a fixed ratio. A preview shows the "
         "values before and after."},
        {"type": "p", "text":
         "Applying keeps the analysed values and adds the adjusted ones "
         "as new columns with the suffix _adj: SiO2_adj, TiO2_adj, …, "
         "FeO_adj, Fe2O3_adj and FeOt_adj. An oxide that was not "
         "analysed stays empty in its _adj column rather than becoming "
         "0. Running the dialog again replaces the _adj columns, always "
         "starting from the analysed values."},
        {"type": "p", "text":
         "Every view that reads major elements — classification, "
         "tectonic, multi-element spider, the CIPW norm and the "
         "statistics — carries a Major elements panel with the switch "
         "Use majors adjusted to 100 %. It is one switch: ticking or "
         "unticking it in any view changes all of them, so no two "
         "views can disagree about which values they use. The panel "
         "says which values are in use and how they were adjusted. It "
         "turns on when the adjustment is applied, and it is saved "
         "with the session."},
        {"type": "note", "text":
         "The bivariate view has no switch: it lists the analysed and "
         "the adjusted columns side by side, so each axis shows which "
         "one it is by its name (section 8)."},
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
            "Th vs Co for altered arc rocks — Hastie et al. (2007).",
            "Zr/TiO2 vs Nb/Y for altered rocks — Winchester & Floyd "
            "(1977).",
            "Alkalic / Sub-alkalic boundary on TAS (Irvine & Baragar 1971).",
            "AFM — Tholeiitic vs Calc-alkaline (Irvine & Baragar 1971 + Rollinson 2021).",
            "Jensen cation plot — high-Mg discrimination.",
            "Hanski [Al2O3] vs [TiO2] for komatiites.",
            "High-Mg subdivision on TAS (Le Maitre et al. 2002).",
        ]},
        {"type": "h2", "text": "Available diagrams (plutonic)"},
        {"type": "bullet", "items": [
            "TAS plutonic — Middlemost (1994).",
            "Normative An–Ab–Or — Barker (1979).",
            "Frost et al. (2001) — Fe-index, MALI, ASI, AI vs FSSI.",
            "A/CNK vs A/NK aluminium saturation — Maniar & Piccoli "
            "(1989).",
            "Ab–Or–Q haplogranite — Tuttle & Bowen (1958).",
        ]},
        {"type": "h2", "text": "Diagrams drawn from the norm"},
        {"type": "p", "text":
         "Barker's An–Ab–Or, the haplogranite Ab–Or–Q and panel (d) of "
         "Frost, AI vs FSSI, plot normative minerals. They compute the "
         "CIPW norm themselves from the majors in use, the same norm as "
         "the Norm view and following the same switch, so there is no "
         "need to visit that view first. A dataset that brings its own "
         "norm, in columns named Q, Or, Ab, An, Ne, Lc and Kp, is "
         "plotted as it stands instead."},
        {"type": "p", "text":
         "A sample lacking SiO2, Al2O3, MgO, CaO, Na2O, K2O or the iron "
         "as FeO or Fe2O3 gets no norm and is left off: computed "
         "anyway, its blanks would count as zeros — without Al2O3 a "
         "granite has no feldspar and sits on the quartz apex. A note "
         "on the diagram says how many samples were left off and why, "
         "and the Norm view lists them as incomplete. Iron given only "
         "as a total (FeOt or Fe2O3t) must be split first: run Data → "
         "Pre-process majors… and tick Use majors adjusted to 100 %."},
        {"type": "h2", "text": "Naming a rock from the TAS"},
        {"type": "p", "text":
         "Both TAS diagrams can name a composition as well as plot it. "
         "The naming regions are built from the polygons the diagram "
         "draws, so the name and the picture cannot disagree."},
        {"type": "bullet", "items": [
            "Volcanic — Le Bas et al. (1986). Tephrite/basanite and "
            "trachyte/trachydacite are separated by normative olivine "
            "and quartz; without a CIPW norm the pair is returned "
            "whole rather than guessed at.",
            "Plutonic — Middlemost (1994), which renames the volcanic "
            "fields (gabbro for basalt, diorite for andesite, granite "
            "for rhyolite, foid gabbro for tephrite, and so on) and "
            "adds a quartz monzonite field between granite and syenite. "
            "It needs no normative input.",
        ]},
        {"type": "note", "text":
         "Both require the analysis recalculated to 100 % anhydrous, "
         "as the IUGS scheme does. A composition outside the published "
         "diagram is left unnamed rather than forced into the nearest "
         "field — on the plutonic TAS that includes quartzolite and the "
         "tawite/urtite/italite group, which Middlemost places outside "
         "the main sequence of plutonic rocks."},
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
        {"type": "h2", "text": "Adjusted majors and Mg#"},
        {"type": "p", "text":
         "Once the majors have been adjusted (section 6.5), each _adj "
         "column is listed right after the oxide it adjusts, in blue, "
         "so SiO2 and SiO2_adj sit side by side. After MgO come the "
         "magnesium numbers, in green, 100·Mg/(Mg+Fe²⁺) in molar "
         "proportions:"},
        {"type": "bullet", "items": [
            "Mg# — with the measured FeO. Offered only when FeO and "
            "Fe2O3 were reported separately.",
            "Mg#_FeOt — with all iron as Fe²⁺, what most papers mean "
            "when only total iron was measured. The 100 % adjustment "
            "does not change it.",
            "Mg#_adj — of the adjusted majors, with Fe²⁺ the FeO of the "
            "iron partition chosen when adjusting.",
        ]},
        {"type": "p", "text":
         "They are the same definitions as the statistics table uses, "
         "and they can be used inside an expression too, such as "
         "Mg#_FeOt/100. A column of your own named Mg# takes "
         "precedence over the computed one."},
        {"type": "h2", "text": "Optional overlays"},
        {"type": "bullet", "items": [
            "Linear regression line per group or overall, with optional "
            "95 % confidence band and printed equation + R² in the legend.",
            "Convex-hull shaded range per group.",
            "Reservoir overlays — tick reference compositions (Bulk CC, "
            "N-MORB, OIB, KLB-1, …) to add labelled stars at the "
            "corresponding (X, Y) coordinates.",
        ]},
        {"type": "h2", "text": "Annotations and Identify sample"},
        {"type": "p", "text":
         "Both sub-modes have the Annotations panel: lines, arrows, "
         "text and Identify sample, which labels the sample nearest the "
         "click. In Paired each annotation belongs to the panel clicked "
         "in — the sample is looked up on that panel's X and Y — and "
         "stays with that pair of variables when the grid is "
         "rearranged; a pair taken off the grid keeps its annotations "
         "for when it comes back. A line or arrow needs both clicks on "
         "the same panel. Right-click removes the nearest annotation, "
         "and samples of a group switched off cannot be identified. "
         "Alt / Cmd + click selects a sample here as in every other "
         "view, and in Paired it is ringed on every panel."},
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
            "5 Ni-Cu-PGE metal references (primitive mantle after "
            "McDonough & Sun 1995, Becker et al. 2006 and Fischer-Gödde "
            "et al. 2011; CI chondrite after Fischer-Gödde et al. 2010; "
            "depleted mantle after Salters & Stracke 2004), drawn on "
            "their own axis — Ni, the platinum-group metals, Au and Cu in "
            "order of compatibility with sulphide liquid.",
        ]},
        {"type": "note", "text":
         "Every Ni-Cu-PGE value has been checked page by page against "
         "its paper. The primitive mantle often cited as Barnes & Maier "
         "(1999) is McDonough & Sun's (1995), and is listed under their "
         "name."},
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
         "and the specific discriminator from the second combo. 36 "
         "published discriminators are implemented, each with the "
         "boundaries of its own source. Each plot prints its citation "
         "as a subtitle, and the entry in the combo names the axes in "
         "the order the published figure draws them — y first, then x."},
        {"type": "h2", "text": "Mafic"},
        {"type": "bullet", "items": [
            "Pearce (2008) Th/Yb vs Nb/Yb — crustal-input proxy.",
            "Pearce (2008) TiO2/Yb vs Nb/Yb — melting-depth proxy. "
            "The y axis is TiO2 in wt.% over Yb in ppm, as published.",
            "Saccani (2015) Th_N vs Nb_N — MORB-OIB array against "
            "volcanic arc array, N-MORB normalised.",
            "Saccani (2015) Yb_N vs Dy_N — boninite against island-arc "
            "tholeiite, chondrite normalised.",
            "Saccani (2015) (Dy/Yb)_N vs (Ce/Yb)_N — N-MORB against "
            "G-MORB, chondrite normalised.",
            "Pearce & Gale (1977) Zr/Y vs Ti/Y — within-plate against "
            "plate-margin.",
            "Shervais (1982) / Vermeesch (2006a) Ti vs V.",
            "Pearce & Cann (1973) / Vermeesch (2006a) Zr vs Ti.",
            "Five Vermeesch (2006a) ternaries: Na–25Nb–Sr, "
            "Si/1000–Ti/40–Sr, 100Eu–500Lu–Sr, V–Ti/50–5Sc and "
            "50Sm–Ti/50–V.",
            "Wood (1980) / Vermeesch (2006a) Th – Hf/3 – Ta ternary.",
            "Cabanis & Lecolle (1989) La/10 – Y/15 – Nb/8 ternary, "
            "with Y/15 at the apex.",
            "Pearce (1976) / Vermeesch (2006a) major-element DF, and "
            "Butler & Woronow (1986) / Vermeesch (2006a) Zr–Y–Sr–Ti DF.",
            "Verma & Agrawal (2011) — basic and ultrabasic rocks, five "
            "triplet DF panels.",
            "Yang et al. (2019) ln(FeO/CaO) vs ln(MgO/SiO2), the FCMS "
            "plane, and FCKANTMS vs ln(SiO2/(CaO+Na2O+TiO2)).",
            "Li, Godang & Saputro (2025) Nb/Yb vs Th/Nb — nine settings, "
            "from N-MORB to alkaline arc; for mafic to felsic rocks, so "
            "it is listed under all three compositions. The menu entry "
            "names its axes y first; on the plot Th/Nb runs across.",
            "Godang, Saputro & Li (2024) Nb/Zr vs Th/Nb, as Li et al. "
            "(2025) Figure 5 draws it — Nb/Zr sorts the mantle source "
            "(enriched above the primitive mantle's 0.0627, slightly "
            "enriched down to 0.04, depleted below) and Th/Nb the "
            "setting: the non-subduction array, the intracontinental "
            "rift, continental extension or alkaline arc, and the "
            "continental and island arcs either side of a diagonal "
            "from PM. Also under all three compositions.",
        ]},
        {"type": "h2", "text": "Intermediate"},
        {"type": "bullet", "items": [
            "Defant & Drummond (1990) Sr/Y vs Y — adakite.",
            "Defant & Drummond (1990) La/Yb vs Yb — adakite.",
            "Verma & Verma (2013) — three five-panel DF sets: majors, "
            "immobile majors + traces, and immobile traces.",
            "Li et al. (2025) Nb/Yb vs Th/Nb and Godang et al. (2024) "
            "Nb/Zr vs Th/Nb (see Mafic).",
        ]},
        {"type": "h2", "text": "Acid (granitoids)"},
        {"type": "bullet", "items": [
            "Pearce et al. (1984) Ta vs Yb, Nb vs Y, Rb vs (Yb+Ta) and "
            "Rb vs (Y+Nb).",
            "Harris et al. (1986) Rb/30 – Hf – Ta×3 ternary, with "
            "Rb/30 at the apex.",
            "Verma, Pandarinath & Rivera-Gómez (2012) — acid rocks, "
            "five triplet DF panels.",
            "Verma et al. (2013) — three further five-panel DF sets: "
            "majors, immobile majors + traces, and immobile traces.",
            "Li et al. (2025) Nb/Yb vs Th/Nb and Godang et al. (2024) "
            "Nb/Zr vs Th/Nb (see Mafic).",
        ]},
        {"type": "note", "text":
         "The Verma sets assume the rock type has already been fixed, "
         "with SINCLAS or IgRoCS. Nothing in B.I.R.D.S enforces that: "
         "fed a basalt, the intermediate-magma set will still answer, "
         "and confidently. Choose the set that matches your rocks."},
    ]),

    ("11. Statistics and Anomalies", [
        {"type": "p", "text":
         "Click Statistics and Anomalies → Open dashboard to compute "
         "every available statistic in one click. A “Refresh” button "
         "and a chondrite-reference selector live at the top of the "
         "window. Eight tabs hold the results:"},
        {"type": "bullet", "items": [
            "Descriptive — count, mean, std, percentiles, median, MAD, "
            "%RSD, skewness and kurtosis for every numeric column.",
            "By group — the same statistics broken down by your "
            "grouping column(s).",
            "Paper table — a publication-ready mean ± 1SD (n) per group, "
            "with the Mg# at the foot of the major elements and each "
            "adjusted oxide beside the analysed one.",
            "Anomalies & ratios — Eu/Eu*, Ce/Ce*, Pr/Pr*, Gd/Gd*, "
            "Y/Y*, Y/Ho (raw), and the normalised (La/Yb)_N, "
            "(La/Sm)_N, (Gd/Yb)_N, (Sm/Yb)_N per sample. Positive "
            "anomalies are highlighted in pink, negative in light blue.",
            "Trace-element ratios — 15 commonly used ratios per sample "
            "(La/Yb, Zr/Y, Th/Yb, Nb/Y, Ti/V, Ba/Nb, Rb/Sr, …).",
            "Correlation matrix — Pearson r heatmap, poolable, "
            "facetable per group or shown for one group alone, with "
            "cell annotations if the matrix fits on screen.",
            "Tectonic discrimination — 208 parameters, ticked from a "
            "tree and computed per sample. See below.",
            "Plots — the figures that go with the tables.",
        ]},
        {"type": "p", "text":
         "Mg#, Mg#_FeOt and, once the majors are adjusted, Mg#_adj are "
         "summarised like any oxide in the Descriptive, By group and "
         "Paper tables, and listed per sample with the trace ratios; "
         "the saved report carries them in the same places. The "
         "Major elements panel under the toolbar decides whether the "
         "ratios and the tectonic parameters read adjusted or analysed "
         "majors."},
        {"type": "h2", "text": "The tectonic discrimination tab"},
        {"type": "p", "text":
         "This is where the discriminant functions behind the Verma "
         "diagrams, and the simple ratios behind the others, are "
         "reported as numbers. Tick what you want in the tree on the "
         "left; the count in the tab title follows your selection."},
        {"type": "bullet", "items": [
            "For seven of the eight Verma coefficient sets the "
            "posterior probability of each tectonic setting is given "
            "as well as the discriminant score, following Verma & "
            "Agrawal (2011). Verma et al. (2012) publishes neither "
            "group centroids nor group means, so that set reports "
            "scores alone.",
            "33.3 % is the by-chance level for a three-group panel. A "
            "sample sitting near it is inconclusive, and seeing the "
            "number says so where a field name would not.",
        ]},
        {"type": "note", "text":
         "Every row here is checked against the diagram that plots the "
         "same quantity, and required to equal it exactly. The two "
         "reach the number by different code, so when a correction "
         "lands on one it has to land on the other."},
    ]),

    ("12. Map and spatial analysis", [
        {"type": "p", "text":
         "Map → Sample locations and kriging… plots every sample at its "
         "longitude and latitude and, on the same axes, interpolates one "
         "numeric column across the area by ordinary kriging. Nothing "
         "is downloaded: there is no background map, and the view works "
         "offline."},
        {"type": "h2", "text": "12.1  Coordinates"},
        {"type": "p", "text":
         "Pick the format under Coordinate columns, then the columns it "
         "needs. B.I.R.D.S guesses them from common names (Latitude, "
         "Lat, Easting, Zone, …)."},
        {"type": "bullet", "items": [
            "Decimal degrees — 19.4326 and −99.1332; negative is south "
            "and west.",
            "UTM — easting and northing in metres, with the zone and "
            "hemisphere fixed for the whole dataset or read row by row "
            "from columns.",
            "Degrees, minutes and seconds — strings such as 19°25'57\"N.",
            "Decimal with a hemisphere letter — 19.42N, 99.13W.",
            "MGRS grid references — 14QMG5780012345 (needs the optional "
            "mgrs package).",
        ]},
        {"type": "note", "text":
         "Every coordinate is taken as WGS-84. UTM is converted with "
         "pyproj when it is installed and with a built-in formula "
         "otherwise; the two agree to about a millimetre."},
        {"type": "h2", "text": "12.2  The sample map"},
        {"type": "p", "text":
         "The axes are longitude and latitude in degrees, with the "
         "aspect ratio fixed at the frame's centre latitude so that a "
         "square on the ground draws as a square there. This is the "
         "equirectangular projection, true along every meridian and "
         "along that parallel — as good as any projection over a field "
         "area. The scale bar is measured along that parallel on the "
         "WGS-84 ellipsoid."},
        {"type": "bullet", "items": [
            "Auto-fit to samples frames the data with the padding you "
            "set. Untick it to keep a zoomed or panned frame through "
            "updates; the kriging grid then covers that frame.",
            "Markers take their colour and symbol from Data → Edit "
            "plot. Tick Colour by the analysed variable to colour them "
            "by value instead; samples without a value are drawn hollow.",
            "The scale bar, north arrow, grid and legend can each be "
            "turned off, and the annotation tools (lines, arrows, text, "
            "sample labels) work in degrees.",
        ]},
        {"type": "h2", "text": "12.3  Kriging a variable"},
        {"type": "p", "text":
         "Choose the column under Spatial analysis → Variable and press "
         "Update map. The tabs above the plot switch between five "
         "displays:"},
        {"type": "bullet", "items": [
            "Samples — the locations, as above.",
            "Kriged estimate — the interpolated surface, with the samples "
            "over it as small white markers.",
            "Uncertainty — the kriging standard deviation. It is "
            "smallest at the samples and grows away from them; read it "
            "before trusting any part of the estimate.",
            "Variogram — semivariance against the distance between "
            "samples, each point sized by the number of pairs behind it, "
            "with the fitted model.",
            "Cross-validation — every sample against its value "
            "predicted from all the others. Points near the 1 : 1 line "
            "mean the spatial model predicts well.",
        ]},
        {"type": "p", "text": "The options:"},
        {"type": "bullet", "items": [
            "Transform — Logarithm (the default) kriges ln(value) and "
            "shows the median estimate. Concentrations are skewed and "
            "cannot be negative, which the logarithm respects; values at "
            "or below zero are left out and counted. Choose None for a "
            "variable that can be negative, such as εNd.",
            "Groups — Each group on its own (the default) kriges every "
            "group separately. A pluton and its host are not one "
            "continuous field, and kriging across the contact would "
            "draw a gradient that does not exist. Choose All groups "
            "pooled only when the groups are not separate bodies.",
            "Variogram model — spherical (the default), exponential or "
            "Gaussian. In all three the range is the effective range: "
            "the distance at which the model reaches 95 % of its sill.",
            "Lag classes and Maximum lag — how the experimental "
            "variogram is binned. Auto aims at about 30 pairs of "
            "samples per class, out to half the largest distance "
            "between two samples.",
            "Grid cells across — the resolution of the surface along the "
            "longer side of the frame.",
            "Clip to each group's sample hull — draw the surface only "
            "inside the outline of the samples, optionally with a buffer "
            "in km. Beyond it kriging can only extrapolate towards the "
            "mean.",
            "Contour lines on the estimate — labelled isolines over the "
            "surface.",
        ]},
        {"type": "note", "text":
         "Distances are computed through the Earth between points on "
         "the WGS-84 ellipsoid, never read off the map, so no projection "
         "distorts them. Every group shares one colour scale, so colours "
         "compare between groups. Where two clipped surfaces overlap, "
         "the later group is drawn on top and the summary says so."},
        {"type": "h2", "text": "12.4  Reading the summary"},
        {"type": "p", "text":
         "Below the plot a table gives, for each group, the samples used "
         "out of those available, the variogram model with its nugget, "
         "sill and range, and three cross-validation figures:"},
        {"type": "bullet", "items": [
            "Skill — the share of the error of simply guessing the mean "
            "that kriging removes. Near 1 the map adds a great deal; "
            "near 0 or below it adds nothing, whatever the surface looks "
            "like.",
            "RMSE — the typical prediction error, in the units kriged: "
            "natural logarithms under the default transform.",
            "MSSE — the mean squared standardised error. It is about 1 "
            "when the uncertainty map is honest; well above 1 it is too "
            "optimistic, well below 1 too cautious.",
        ]},
        {"type": "p", "text":
         "Notes under the table say in plain words what to doubt: too "
         "few samples for a reliable variogram (a variogram from fewer "
         "than 50 is of little value and about 100 are needed, after "
         "Webster & Oliver 1992); samples left out, or averaged because "
         "they share a location; a range that never levels off within "
         "the distances measured, which often means a regional trend; "
         "an ill-conditioned system; and overlapping surfaces. A group "
         "with fewer than five usable locations is not kriged, and the "
         "summary says why."},
        {"type": "h2", "text": "12.5  Setting the variogram by hand"},
        {"type": "bullet", "items": [
            "Pick the group under Variogram parameters → Group.",
            "Untick Fit automatically. The boxes start from the fitted "
            "values, so nothing moves until you change one.",
            "Type a nugget, sill or range and press Enter. The map, the "
            "variogram and the cross-validation all update, and the "
            "summary marks the model (by hand).",
            "Tick Fit automatically again to go back to fitting. Values "
            "set by hand belong to the variable and transform they were "
            "set for, and are dropped when either changes.",
        ]},
        {"type": "h2", "text": "12.6  Exporting the grid to a GIS"},
        {"type": "p", "text":
         "Export grid for a GIS (.asc)… writes, for every kriged group, "
         "two ESRI ASCII grids in WGS-84 degrees — the estimate and its "
         "kriging standard deviation — each with a .prj file, and one "
         "text file recording the variable, the transform, and each "
         "group's model and cross-validation figures. Saved as Cu.asc "
         "with groups Pluton and Host, the files are:"},
        {"type": "code", "text":
         "Cu_Pluton.asc   Cu_Pluton_sd.asc   (and a .prj for each)\n"
         "Cu_Host.asc     Cu_Host_sd.asc\n"
         "Cu.txt"},
        {"type": "p", "text":
         "With a single surface — one group, or all pooled — the group "
         "is left out of the names. Cells outside the clipped hull hold "
         "the no-data value −9999. QGIS opens the grids with Layer → "
         "Add Layer → Add Raster Layer; ArcGIS opens them too, or "
         "converts them with its ASCII To Raster tool. The .prj places "
         "them without further setting."},
        {"type": "note", "text":
         "Kriging interpolates; it does not explain. A surface is only "
         "as good as the variogram behind it and the spread of the "
         "samples it was built from. Check the Uncertainty tab and the "
         "cross-validation skill before using a kriged map as evidence, "
         "and prefer the clipped surface in a figure."},
    ]),

    ("13. Saving results", [
        {"type": "h2", "text": "13.1  Save the statistics report"},
        {"type": "bullet", "items": [
            "Click Data → Export → Save statistics report…",
            "Choose .xlsx (recommended — one sheet per section) or .csv.",
            "Tick the sections you want (original data, descriptive, "
            "by-group, anomalies, trace ratios, correlation).",
            "Click Save.",
        ]},
        {"type": "h2", "text": "13.2  Export a plot"},
        {"type": "bullet", "items": [
            "Make sure the plot you want is the one currently visible.",
            "Click Data → Export → Export plot… (or Copy plot to "
            "clipboard, to paste it straight into a document).",
            "Pick the format (.png, .jpg, .pdf, .svg) and the DPI "
            "(72–1200) and image dimensions in inches.",
            "Tick “Tight bounding box” to trim the margins and "
            "“Transparent background” for PNG / SVG figures meant for "
            "overlays.",
        ]},
        {"type": "h2", "text": "13.3  Save and reopen a session"},
        {"type": "bullet", "items": [
            "Data → Save session (Ctrl+S) writes everything to one "
            ".birds file: the data sheets, the groups and their styles, "
            "each view's settings, and results already computed such as "
            "the CIPW norm, so reopening needs no recalculation.",
            "Data → Save session as… (Ctrl+Shift+S) writes it under a "
            "new name.",
            "Data → Open session… (Ctrl+O), or Data → Recent sessions, "
            "reopens one. With the application installed (sections 3.5 "
            "and 4.5) a double-click on the .birds file does the same.",
            "B.I.R.D.S also saves your work on its own every five "
            "minutes. If it closes before you save, the next start "
            "offers to recover it — unless it was started by "
            "double-clicking a session, which is then the one opened.",
            "Opening a session draws only the page it was saved on; "
            "the other views are brought up to date the first time "
            "you open them, so a session with many views opens in "
            "well under a second.",
        ]},
    ]),

    ("14. Troubleshooting", [
        {"type": "h2", "text": "B.I.R.D.S closed on its own"},
        {"type": "p", "text":
         "Reopen it: the work of the last five minutes is offered back. "
         "Then send the file ~/.birds/crash.log (in Finder, Go → Go to "
         "Folder… and type ~/.birds). Every Python error, every Qt "
         "warning and, for a crash inside Qt itself, the Python stack "
         "it happened under are written there. macOS keeps its own "
         "report as well, in Console → Crash Reports, under BIRDS."},

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

        {"type": "h2", "text": "A normative diagram shows no samples"},
        {"type": "p", "text":
         "Barker, the haplogranite and Frost's FSSI panel need a CIPW "
         "norm for each sample, and the note in the corner of the "
         "diagram names what is missing. Most often the iron is given "
         "only as FeOt or Fe2O3t: split it in Data → Pre-process "
         "majors… and tick Use majors adjusted to 100 % (section 7, "
         "Diagrams drawn from the norm)."},

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

        {"type": "h2", "text": "The map says no samples could be parsed"},
        {"type": "p", "text":
         "The coordinate format or columns do not match the data. Check "
         "the format under Coordinate columns — UTM eastings read as "
         "decimal degrees fall far outside ±180° — and that latitude "
         "and longitude are not swapped."},

        {"type": "h2", "text": "The Variable list is empty"},
        {"type": "p", "text":
         "Only numeric columns with at least five values that are not "
         "all equal can be kriged, and the coordinate columns are left "
         "out. A column with a unit or a comment typed into its cells "
         "is read as text and has to be cleaned first. Values below "
         "detection (“<0.5”, “b.d.l.”) are not the problem: they are "
         "converted on import, under the policy in Data → Detection "
         "limits…"},

        {"type": "h2", "text": "A group says “not kriged”"},
        {"type": "p", "text":
         "It has fewer than five usable locations, or every value is "
         "the same. Under the logarithmic transform, values at or below "
         "zero do not count. The other groups are kriged regardless."},

        {"type": "h2", "text": "“The fitted range ran to its upper bound”"},
        {"type": "p", "text":
         "The variogram keeps rising across every distance measured "
         "instead of levelling off. Often the variable follows a "
         "regional trend, and ordinary kriging, which assumes a constant "
         "mean, describes it only roughly. Try a smaller maximum lag, "
         "or read the map as a smoothed picture of the trend."},
    ]),

    ("15. References", [
        {"type": "p", "text":
         "B.I.R.D.S implements diagrams and statistics from the "
         "following sources. Cite each one according to the diagram you "
         "used in your figures and tables — every plot prints its own "
         "citation as a subtitle, and References → Show full "
         "bibliography (APA) lists them all."},
        {"type": "bullet", "items": [
            "Rollinson, H.R., Pease, V. (2021). Using Geochemical Data "
            "to Understand Geological Processes (2nd ed.). Cambridge "
            "University Press.",
            "Le Bas, M.J., Le Maitre, R.W., Streckeisen, A., Zanettin, "
            "B. (1986). A chemical classification of volcanic rocks "
            "based on the total alkali-silica diagram. J. Petrol. 27, "
            "745–750.",
            "Middlemost, E.A.K. (1994). Naming materials in the "
            "magma/igneous rock system. Earth-Sci. Rev. 37, 215–224.",
            "Maniar, P.D., Piccoli, P.M. (1989). Tectonic discrimination "
            "of granitoids. GSA Bull. 101, 635–643.",
            "Pearce, J.A. (2008). Geochemical fingerprinting of oceanic "
            "basalts with applications to ophiolite classification and "
            "the search for Archean oceanic crust. Lithos 100, 14–48.",
            "Pearce, J.A., Gale, G.H. (1977). Identification of "
            "ore-deposition environment from trace-element geochemistry "
            "of associated igneous host rocks. GSL Sp. Pub. 7, 14–24.",
            "Pearce, J.A., Harris, N.B.W., Tindle, A.G. (1984). Trace "
            "element discrimination diagrams for the tectonic "
            "interpretation of granitic rocks. J. Petrol. 25, 956–983.",
            "Harris, N.B.W., Pearce, J.A., Tindle, A.G. (1986). "
            "Geochemical characteristics of collision-zone magmatism. "
            "GSL Sp. Pub. 19, 67–81.",
            "Cabanis, B., Lecolle, M. (1989). Le diagramme "
            "La/10-Y/15-Nb/8. C. R. Acad. Sci. 309 (II), 2023–2029.",
            "Defant, M.J., Drummond, M.S. (1990). Derivation of some "
            "modern arc magmas by melting of young subducted "
            "lithosphere. Nature 347, 662–665.",
            "Saccani, E. (2015). A new method of discriminating "
            "different types of post-Archean ophiolitic basalts. "
            "Geosci. Front. 6, 481–501.",
            "Vermeesch, P. (2006a). Tectonic discrimination diagrams "
            "revisited. G-cubed 7, Q06017.",
            "Verma, S.P. and co-authors (2006–2017). Multi-dimensional "
            "tectonomagmatic discrimination diagrams (multiple papers).",
            "Verma, S.P. (2010). Statistical evaluation of bivariate, "
            "ternary and discriminant function tectonomagmatic "
            "discrimination diagrams. Turk. J. Earth Sci. 19, 185–238.",
            "Yang, Z.-F. et al. (2019). Using major element logratios "
            "to recognize compositional patterns of basalt. J. Geophys. "
            "Res. Solid Earth 124, 3458–3490.",
            "Streckeisen, A. (1973). Plutonic rocks: classification and "
            "nomenclature recommended by the IUGS Subcommission. "
            "Geotimes 18, 26–30.",
            "Streckeisen, A. (1976). To each plutonic rock its proper "
            "name. Earth-Sci. Rev. 12, 1–33.",
            "Streckeisen, A. (1978). Classification and nomenclature of "
            "volcanic rocks, lamprophyres, carbonatites and melilitic "
            "rocks. N. Jb. Miner. Abh. 134, 1–14.",
            "Schmid, R. (1981). Descriptive nomenclature and "
            "classification of pyroclastic deposits and fragments. "
            "Geology 9, 41–43.",
            "Gillespie, M.R., Styles, M.T. (1999). BGS Rock "
            "Classification Scheme, Vol. 1: Classification of igneous "
            "rocks. British Geological Survey Research Report RR 99-06.",
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
            "Matheron, G. (1963). Principles of geostatistics. Econ. "
            "Geol. 58, 1246–1266.",
            "Dubrule, O. (1983). Cross validation of kriging in a unique "
            "neighborhood. Math. Geol. 15, 687–699.",
            "Webster, R., Oliver, M.A. (1992). Sample adequately to "
            "estimate variograms of soil properties. J. Soil Sci. 43, "
            "177–192.",
            "Pebesma, E.J. (2004). Multivariable geostatistics in S: the "
            "gstat package. Comput. Geosci. 30, 683–691.",
        ]},
    ]),
]
