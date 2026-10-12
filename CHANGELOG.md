# Changelog

All notable changes to **B.I.R.D.S.** are recorded here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project aims at [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Nothing has been released or tagged yet: `pyproject.toml` carries
`0.1.0`, and everything below the `Unreleased` heading is work done on
top of the initial commit. The first tagged release is the point to
archive for a DOI.

Where a change touches a diagram, it says which published source it was
checked against. `docs/DIAGRAM_PROVENANCE.md` carries the full record,
including what is still unverified.

## [Unreleased]

### Added

- **Adjusted majors beside the analysed ones, and one switch to choose.**
  *Data → Pre-process majors…* used to overwrite the analysed oxides with
  the adjusted values; from then on every diagram plotted adjusted values
  with nothing on screen to say so, and the analysed values were gone. It
  now adds the adjusted values as `SiO2_adj`, `TiO2_adj`, …, `FeO_adj`,
  `Fe2O3_adj`, `FeOt_adj`, and leaves the analysed columns as they were.
  Every view that reads majors — classification, tectonic, multi-element
  spider, CIPW norm and statistics (the trace ratios, the Mg# and the 208
  tectonic parameters) — carries a **Major elements** panel with the
  switch *Use majors adjusted to 100 %*, saying which values are in use
  and how they were adjusted. It is one switch, held by the data, so
  every view follows it and the statistics table still equals the axis
  it is paired with. It turns on when the adjustment is applied and is
  saved with the session; new data reset it.
- **The Bivariate view lists the adjusted columns and the Mg#.** Each
  `*_adj` column follows the oxide it adjusts, in blue, so the analysed
  and adjusted values sit side by side. After MgO come, in green, `Mg#`
  (measured FeO, offered only with a reported FeO/Fe₂O₃ split),
  `Mg#_FeOt` (all iron as Fe²⁺) and `Mg#_adj` (Fe²⁺ from the iron
  partition) — the statistics table's definitions, so an axis and a row
  of the same name agree. They work inside expressions (`Mg#_FeOt/100`)
  and on the reservoir overlays, where Primitive Mantle gives 89.3, the
  value McDonough & Sun (1995) print. Reservoirs also plot on `*_adj`
  axes, being published volatile-free.
- **B.I.R.D.S can be built as an application, and `.birds` sessions get
  their own icon.** `packaging/` holds the PyInstaller recipe for a
  macOS `BIRDS.app` and a Windows build, an Inno Setup installer, Linux
  desktop and MIME files, and the icons: the application's, and a
  session-file icon — a page with the emblem small on it — drawn from
  the logo by `packaging/make_icons.py`. The app declares the `.birds`
  type, so every saved session shows that icon and opens in B.I.R.D.S
  on a double-click: macOS hands the file over as an event, Windows and
  Linux on the command line, and `birds/app.py` routes both to the
  window. A session opened that way is not covered by the offer to
  recover an earlier auto-save. `BIRDS --self-test` puts a diagram, the
  kriging, UTM and MGRS conversions, the CIPW norm, a session and an
  Excel file through the built program and exits non-zero if any fails —
  the first macOS build left out `mgrs`'s compiled library and would not
  start, which is how it earned its place. `packaging/update_mac_app.py`
  rebuilds the Mac app from the source and replaces the installed copy
  in one step — only when the new build passes the self-test, only if
  what it replaces is B.I.R.D.S, and swapping by renaming so a failure
  half-way still leaves a working app. Build steps in
  `packaging/README.md`.
- **Mg# in the statistics and in the saved report.** `Mg#`, `Mg#_FeOt`
  and `Mg#_adj` are summarised like any oxide in the Descriptive, By
  group and Paper tables — at the foot of the major elements in the
  paper table, ticked on first open — and the saved report carries them
  there too. Before, the Mg# reached the file only inside the
  trace-ratio sheet, which the save dialog described as "La/Yb, Zr/Y,
  Th/Yb, …".

- **Spatial analysis in the Map view: ordinary kriging of any numeric
  column.** Five tabs over the canvas — the samples, the kriged
  estimate, its uncertainty, the variogram, and the cross-validation —
  with the first three drawn as maps on the same longitude/latitude
  axes, scale bar and annotations as before. Each group is kriged on
  its own by default, because a pluton and its host are not one random
  field and kriging across the contact paints a gradient that is not
  there; pooling them is one choice away. Concentrations are kriged as
  logarithms and shown as the median; every group shares one colour
  scale; each surface is clipped to its own samples' hull, with an
  optional buffer, since beyond it kriging only extrapolates. The
  variogram can be fitted or set by hand per group, starting from the
  fitted values. Under the plot a summary gives each group's model,
  samples used and cross-validation skill, and says in plain words
  what to doubt: too few samples by Webster & Oliver (1992), samples
  left out or folded together, a range that never levels off, an
  ill-conditioned system, surfaces that overlap. **Export grid for a
  GIS** writes the estimate and its standard deviation per group as
  ESRI ASCII grids in WGS-84 degrees, each with its `.prj`, and a text
  file recording what they hold and how they were made. Samples can
  also be coloured by the variable instead of by group.
- **A geostatistics engine for the Map view** (`birds/geostats.py`):
  the experimental variogram, spherical, exponential and Gaussian
  models fitted by weighted least squares, ordinary kriging,
  leave-one-out cross-validation, a prediction grid clipped to the
  samples' convex hull, and export to an ESRI ASCII grid with its
  `.prj` for QGIS or ArcGIS. numpy and scipy only. Distances are
  taken through the Earth, between points on the WGS-84 ellipsoid, so
  no projection distorts them;
  "range" means the effective range in all three models;
  concentrations are kriged as logarithms by default and reported as
  the median with its 95 % interval; coincident samples are folded
  together; and the variogram's reliability is judged against Webster
  & Oliver's (1992) sample sizes. Checked against exact answers rather
  than another program: kriging honours the data, its weights sum to
  one, with no spatial structure it returns the mean with variance
  c₀(1 + 1/n), and with a linear variogram it reproduces the Brownian
  bridge to machine precision. The one-inverse cross-validation
  (Dubrule 1983) equals refitting n times to 10⁻¹⁵. On a smooth field
  it removes 98–100 % of the error of guessing the mean; on noise,
  none, and its variance says so.
- **Posterior probability of each tectonic setting** in the statistics
  table, for seven of the eight Verma coefficient sets, following Verma
  & Agrawal (2011) eqs (1)–(12). Verma et al. (2012) publishes neither
  group centroids nor group means, so it still reports discriminant
  scores alone. 33.3 % is the by-chance level, which makes an
  inconclusive sample visible as such instead of being given a field
  name it does not deserve.
- **Rock naming from the TAS**: `TASVolcanic.classify()` and a
  vectorised `classify_frame()`. The regions are derived from the
  polygons the diagram already draws, so the name and the picture
  cannot disagree. Tephrite/basanite and trachyte/trachydacite split on
  normative olivine and quartz; without them the pair is returned
  whole.
- **The user manual and the diagram menus had gone stale.** The manual
  still said "52 plotting templates", "33 tectonic diagrams", "14
  published discriminators" and "Five tabs", and attributed the
  plutonic TAS to Wilson (1989); it now says 53, 34, 34 and eight, and
  cites Middlemost. It has gained the TAS rock-naming section, the
  tectonic discrimination tab with its posterior probabilities, and
  nine references the diagrams had acquired without it. Eleven entries
  in the **tectonic menu** named their axes in the order they had
  before this autumn's corrections, so the combo offered "Ti/Y vs Zr/Y"
  and opened a plot titled "Zr/Y vs Ti/Y"; they now agree.
  `tests/test_manual_and_menu_are_current.py` recomputes every count
  from the registry and requires each menu entry to name the axes its
  own plot draws, because counts written in prose drift silently.
- **The manual covers the Map view, and the rest of it caught up.** A
  new section 12 explains the coordinate formats, the sample map, the
  five displays, every kriging option, how to read the summary, setting
  the variogram by hand and exporting the grids, with troubleshooting
  entries for the map. The menu list had six menus of eleven and said
  "14" tectonic diagrams; two menu paths no longer existed (`Data →
  Import`, `Data → Save`); the classification lists lacked Hastie et
  al., Winchester & Floyd and Maniar & Piccoli; the spider section
  lacked the Ni-Cu-PGE references and the caveat they carry. The
  manual-currency tests now also require the menu list to match the
  menu bar, the sections to be numbered in order, and every map tab
  and control the manual names to exist under that name. The workflow
  flowchart — the manual's Figure 1 and the README's — was redrawn
  with all eleven modules, and its counts are now read from the code
  instead of typed in.
- **The manual covers the installed application and sessions.** New
  sections on BIRDS.app (4.5: installing a received copy, building it
  with the updater, the first-open step for an unsigned app), keeping
  it up to date (4.6), the Windows installer (3.5) and saving and
  reopening sessions (13.3: the commands, double-click opening, the
  five-minute auto-save and its recovery offer), plus the diagrams drawn
  from the norm. A test requires the session commands to carry the
  names and shortcuts the Data menu shows and every script the manual
  says to run to exist.
- **`DIAGRAM_PROVENANCE.md`'s summary caught up with its body.** It
  still read 28 checked and 19 drawn envelopes to measure, flagged a
  Butler & Woronow disagreement resolved since, and counted 47 diagrams
  and 62 menu entries. Of 48 diagrams, 45 are now checked against their
  sources, none is known wrong, and three remain drawn by eye, blocked
  on sources; the table says which section covers each kind. Tests
  recompute those counts from the catalogue and require every diagram
  in the menus to have an entry.
- **`docs/SPATIAL_ANALYSIS.md`**, the method note for the kriging: the
  choices and their reasons, the equations, the data handling, how it
  was checked and where it stops. It is to the geostatistics what
  `DIAGRAM_PROVENANCE.md` is to the diagrams.
- **The FCMS plane, Yang *et al.* (2019) Fig. 1a.** FCMS was reported
  in the statistics table with no diagram to read it against — the gap
  the two-routes sweep found, by its having no partner to pair with.
  It still gets no *discrimination* diagram, because the paper
  publishes none: boundary coordinates appear in exactly one caption,
  Figure 7's, and those are FCKANTMS. What is published is the plane
  and the trend through it, so the diagram is ln(FeO/CaO) against
  ln(MgO/SiO₂) with the lherzolite cubic printed on Figure 1a drawn
  across it. FCMS **is** the vertical distance from that curve, which
  is what makes it worth plotting: the value can be read straight off,
  and a lherzolite melt sits on the line. The citation passes on the
  paper's own view that FCKANTMS supersedes it, having removed the
  temperature and pressure effects that scatter lherzolite melts here.
  The catalogue entry used to read "FCMS / FCKANTMS" and point at the
  FCKANTMS diagram alone; the two are now listed separately.
- **`TASPlutonic.classify()` and `classify_frame()`**, now that
  Middlemost (1994) is to hand. What stood in the way was that two of
  its sixteen outlines are stored as the single boundary segment each
  contributes to the drawing; closing those two makes the sixteen tile
  exactly, with no overlap and no interior gap. Middlemost's own text
  is what licenses the vertices — he sets the plutonic scheme out as
  the volcanic one renamed, so those two fields are the volcanic
  phonotephrite and tephriphonolite under plutonic names — and both
  closures were then checked against his Figure 4. It takes no
  normative arguments and needs none: he gives foid gabbro one name
  where the volcanic plane splits tephrite from basanite, and draws the
  quartz monzonite field rather than splitting a trachyte field at
  20 % normative quartz.
- **Validation against USGS reference materials** BHVO-2, BCR-2 and
  AGV-2 (`tests/test_usgs_reference_materials.py`), running the whole
  chain a user follows: pre-process, classify, norm, normalise,
  discriminate. Values from the USGS Information Sheets (June 2022),
  which take them from Jochum *et al.* (2016).
- **`docs/DIAGRAM_PROVENANCE.md`** — where every diagram's boundaries
  come from, diagram by diagram, including the ones still drawn by eye
  and the two retracted findings from the first pass.
- **Test suite, packaging and CI**: 2127 tests over the numerical core,
  the diagram registry, the shared GUI state and the session
  round-trip, plus `pyproject.toml`, a ruff configuration and a GitHub
  Actions matrix over Linux/macOS/Windows and Python 3.9/3.12.
- **Ni-Cu-PGE normalisers** with five mantle and chondrite references.
- **Statistics**: rows labelled by sample rather than by position, and
  every view splittable by the grouping set in *Data → Edit plot*. The
  correlation matrix can be pooled, faceted per group, or shown for one
  group alone.
- Four Verma sets that were implemented but never reachable from the
  statistics table — Verma & Verma (2013) Set 2 and all three 2013 acid
  sets — are now registered.

### Fixed

#### Diagrams measured or recomputed against their sources

- **Frost's grid, against Frost et al. (2001) and Frost & Frost
  (2008).** Panel (d) now has the frame of their Figure 11, FSSI −1.2
  to 0.6 and AI −0.10 to 0.16, instead of ±2.5 by ±1, where every rock
  crowded the centre. AI was on the cation basis, twice Frost's: their
  Figure 11c places plagioclase An10–An40 at 0.035–0.146, which the
  oxide basis, Al₂O₃ − (Na₂O + K₂O) molar, reproduces. The MALI
  boundaries are now the quadratics the 2001 Figure 2 caption prints,
  through MALI = 0 at Peacock's 51, 56 and 61 % SiO₂, drawn over
  51–75 as in 2008 Figure 6; the curves traced off Rollinson & Pease
  were within 0.25 of them. The Fe-index line starts at SiO₂ 48, where
  Frost & Frost say it applies. Panel (c) keeps ASI 0.5–1.6: the scheme
  fixes only ASI = 1.
- **The Petrography view's diagrams, checked against the IUGS
  definitions** (BGS RR 99-06, which reproduces them). The QAPF placed
  every sample at 0.5 A + P + 0.5 Q with A at x = 0 — half the alkali
  feldspar too far right, so a granite plotted on granodiorite and an
  alkali-feldspar syenite on monzonite — and drew its P/(A+P) lines
  through the quartz-rich fields and at 10/35/65/90 through the foid
  fields, where they are 10/50/90. The volcanic QAPF was the plutonic
  one renamed; it now has Streckeisen's (1978) fields: no names above
  Q 60, dacite over 65-100, basalt / andesite from Q 20 to F 10, and
  three foidites. Both are built from one table of fields, with IUGS
  field numbers and a key, and can name a mode; a sample carrying both
  quartz and a feldspathoid is left off with a note. The gabbroic and
  ultramafic strips are now the 5 % lines the IUGS draws, not openings
  of invented width; the gabbroic diagram reads the template's
  `P_mode`, and Opx + Cpx where `Px_mode` is blank. The tuff diagram
  cited Schmid (1981) for a scheme that is not his: Schmid's three-field
  triangle is added as `tuff_schmid_1981`, the banded one keeps an
  honest citation, and its dividers are now the lines of constant
  crystal content its figure draws rather than rays from the apex.
- **Frost's panel (d) drew its samples transposed.** Its axes read FSSI
  across and AI up, as published, but the samples went in as (AI,
  FSSI). A rock whose two signs differ crossed to the opposite quadrant:
  a nepheline syenite plotted as silica-saturated and Al-deficient, a
  peralkaline granite as undersaturated with Al to spare. The checks of
  the quadrant labels and of the signs passed throughout, since none
  looked at where a sample landed; `tests/test_frost_panels.py` does.
- **Hanski *et al.* (2001) olivine projection.** `[X] = X / (2/3 − MgO
  − FeO)` needs mole proportions normalised to unity; the code applied
  it to raw moles, whose sum is about 1.65, so the denominator came out
  negative. Validated by the property that defines the projection —
  adding olivine does not move the point — to 1 part in 10⁸.
- **Pearce (2008).** The MORB–OIB array was at Th/Nb 0.07–0.32; measured
  off Fig. 2a it is 0.043–0.096, and with the old values an N-MORB fell
  outside its own band. On the second panel the y-axis was the wrong
  quantity altogether: Pearce plots TiO₂ in wt.% over Yb in ppm, not Ti
  in ppm over Yb, a factor of 5993.
- **Yang *et al.* (2019).** FCMS and FCKANTMS are log-ratio residuals
  centred on zero, not sums of oxides in wt.% on ±20 axes. Rebuilt from
  the paper's Table 1.
- **Pearce (1976) and Butler & Woronow (1986).** Both are DF1–DF2
  diagrams and were implemented as one-axis strip charts with
  coefficients that matched nothing in the source. Rebuilt from
  Rollinson & Pease (2021) Appendix 5.1.
- **Butler & Woronow (1986)**: both Zr coefficients are negative in
  Vermeesch (2006a) eq. (7), and the minus signs live in the rendered
  page rather than in the PDF's text layer, so they were lost in
  transcription. A reference N-MORB moves from ld2 = −26.1 to −12.7
  against a triple point published at −12.23; all three reference
  basalts now sit within 2.4 units of it, each in its own field. This
  was the open question the diagram carried a warning about.
- **Vermeesch's three log-ratio LDA ternaries** — Si-Ti-Sr, Eu-Lu-Sr
  and Ti-V-Sc — were polygons typed in ternary percent, approximating
  by eye boundaries that can be computed. They are now built from the
  anchor points of his Table 6: an LDA is straight in log-ratio space
  and curves when mapped back to the ternary, which is what the paper
  says and what the printed figures show. Settled on the way: the
  logarithm is natural, not base ten, and the Si-Ti-Sr triangle had
  Si/1000 at the apex where Figure 42b has Ti/40. Reference N-MORB, OIB
  and IAB now land in their own field on all three, nine out of nine.
- **Wood (1980) Th–Hf/3–Ta and Pearce & Cann (1973) Zr–Ti** now carry
  Vermeesch's discriminant boundaries instead of, respectively, fields
  drawn by eye and two straight lines at Ti/Zr = 30 and 110 that a
  comment called "approximate refined boundaries" and that were neither
  his nor refined. Pearce & Cann's is two segments rather than three
  rays, which is why its row of Table 6 repeats its x values. One of
  Wood's anchor points is used with both signs reversed: the table
  places it diagonally opposite where the figure draws it, and
  measuring the figure — calibrated on the three anchors that do agree
  — gives the printed magnitudes back to a hundredth with the signs
  flipped.
- **The four Pearce, Harris & Tindle (1984) granitoid discriminants**
  were carrying hand-written line segments unrelated to the boundary
  coordinates their authors printed in the captions of Figures 3 and 4.
  They now carry those coordinates, with the two that are wrong used as
  Verma *et al.* (2012) corrected them: a Yb–Ta boundary whose printed
  endpoint points into the opposite quadrant from the fields it
  divides, and a Rb–(Yb+Ta) boundary printed as ending a decade above
  the junction its two neighbours share.
- **The three Saccani (2015) diagrams** were wrong in the same three
  ways each. Figures 8 and 9 are chondrite-normalised — both captions
  say so — and all three were drawn against N-MORB, a factor of 17.9 on
  Dy and Yb, so every sample fell off the bottom-left corner of frames
  that run to Dy_N = 25. Both had their axes swapped, and both were
  logarithmic where the source is linear. The boundaries were invented:
  Figure 5a's four segments had been two rays at Th_N/Nb_N = 1 and 0.1,
  and the other two carried shaded rectangles and a hand-drawn boninite
  blob. Saccani says he drew his lines by eye, but he printed the end
  coordinates of every one of them on the figures, and those are what
  the diagrams now carry.
- **Four of the six Saccani rows in the statistics table** normalised to
  N-MORB for the same reason. Dy_N and Yb_N were 17.9 times low and
  (Ce/Yb)_N was 46 % high. (Dy/Yb)_N was the one row that survived,
  within 0.15 %, because N-MORB and chondrite happen to have nearly the
  same Dy/Yb — which is why the fault was easy to miss in the row where
  it did not show. Every row now says which normaliser it used.
- **Harris, Pearce & Tindle (1986).** Two errors. The apexes were
  wrong — Hf at the top where Figure 6 puts **Rb/30**, with Hf bottom
  left and Ta×3 bottom right — and the divisor was wrong, `Rb/10`
  where the figure, its caption and Figure 7 all print **Rb/30**, in
  the menu text of both trees as well as in the code. Between them
  every sample was placed by the wrong pair of coordinates and with
  one of them three times too large. The five boundary segments are
  now measured: the dotted boundaries separate from the data because
  the two populations do not overlap in size, and RANSAC over the dots
  recovers them carrying 245 of 260, each straight to 0.5–4.3 px on a
  triangle 2008 px wide. Two things that turned up in the measuring:
  the near-vertical boundary curves, though only by 0.46 % of the
  triangle's width, and it has **no single triple point** — two
  branches leave it about four units apart with a short stem between,
  which is why fitting them as concurrent lines put their
  intersections up to 11 units apart.
- **Cabanis & Lecolle (1989).** The apexes were wrong: La/10 sat at the
  top where both the original and Rollinson & Pease (2021) Fig. 5.4d
  put **Y/15**, so every sample was placed by the wrong pair of
  coordinates. Under it were seven quadrilaterals typed in ternary
  percent, approximating a figure whose real structure is wedges from
  the apex. The two boundaries are now measured from both figures
  independently — 61.9/38.1 and 37.9/62.1 from one, 62.0/38.0 and
  38.1/61.9 from the other, agreeing to 0.2 % — and only the left one
  reaches the apex; the right branches off it. The finer subdivisions
  are not drawn, because Verma (2010) found they do not hold and
  Rollinson's redrawing drops them too. The collapse to three fields
  was checked by placing each of the original's own seven labels in
  ternary coordinates: all six that can be placed fall in the wedge
  that absorbs them.
- **Pearce & Gale (1977).** The boundary coordinates were already
  quoted in a comment in the file — Rollinson & Pease (2021) print
  them, "(513, 0) and (313, 7.5)", as Ti/Y–Zr/Y — and were drawn as if
  they were Zr/Y–Ti/Y, which put a line from (1, 513) to (30, 313) on
  the plot, unrelated to either reading. Around them the **axes were
  swapped**, **both were logarithmic** where the figure is linear, the
  frame was invented, and the within-plate field was placed above
  instead of to the right. Measuring Pearce & Gale's own Figure 3
  confirms the printed pair to 1.7 % and 3.1 %, within a few units of
  the calibration's own uncertainty. The frame is now Rollinson's
  0–1200 by 0–18 rather than Figure 3's own, which stops at Zr/Y ≈ 7.9
  and so clips an ordinary ocean-island basalt at 9.7. Verma's (2010)
  rates — plate margin >90 %, within-plate >89 % — replace the vaguer
  "<11 % misclassified", and the citation now says they hold only with
  E-MORB excluded, which matters: Sun & McDonough's E-MORB lands at
  Ti/Y 273 against their N-MORB at 271.
- **Defant & Drummond (1990).** Their Figure 2 draws no adakite field —
  its adakites are crosses and nothing encloses them — so the dashed
  "adakite boundary" here, and the `Sr/Y > 40` in its citation, were in
  neither the figure nor the text. The frame was `(0, 50)` by
  `(0, 200)` against a published `(0, 25)` by `(0, 500)`, which put a
  sample at less than half its real Y and more than twice its real
  Sr/Y relative to anything drawn around it. The island-arc ADR and
  MORB fields are now measured off the figure and the adakite
  threshold the paper does state, Y ≤ 18 ppm, is drawn in place of the
  invented curve. The measured left edge of the island-arc field came
  out at Y = 17.9 against that independently stated 18 — two unrelated
  parts of the paper agreeing to a third of the measurement's
  uncertainty. Figure 2's boninite field is not reproduced: its
  outline does not resolve in the scan, and guessing it would be the
  same fault again.
- **`defant_drummond_YbLaYb` is not in the paper it cites.** Defant &
  Drummond (1990) has three figures and none is Yb against La/Yb;
  Rollinson & Pease (2021) list one under this reference, marked
  *unevaluated*, which is where the attribution came from. It now
  draws only the Yb ≤ 1.9 ppm threshold the paper does state, says so
  on the plot, and has given up its invented `(0, 6)` by `(0, 80)`
  frame so the axes follow the data.
- **Maniar & Piccoli (1989): the "Peralkaline" label sat where nothing
  can plot.** The diagram draws a third line besides Shand's two, the
  diagonal A/NK = A/CNK, which is where CaO = 0 and below which no
  composition falls. It was stored as the peralkaline field and its
  label put at (1.25, 0.75), under that diagonal and right of
  A/CNK = 1; peralkaline rocks plot in the triangle above it, which had
  no label. The label is there now, the note under the plot says what
  the diagonal is, and nothing drawn has moved. The two boundaries and
  the molar arithmetic were checked against Shand's definitions and
  were right: every feldspar lands on A/CNK = 1, albite and orthoclase
  on both lines.
- **Frost *et al.* (2001): the ASI was not Shand's index.** Al, Na and
  K were doubled to cations and Ca was not, so anorthite came out at
  ASI 2 instead of 1 and a granite at A/CNK 1.03 at 1.23 —
  peraluminous on the Frost panel, metaluminous on Maniar & Piccoli.
  The line at ASI = 1 means Al just enough for feldspar (Rollinson &
  Pease 2021, p. 127), so every feldspar has to sit on it; all now do,
  and with no P₂O₅ the index equals A/CNK. P₂O₅'s molar mass was
  141.95 where the atomic weights give 141.94.
- **Frost *et al.* (2001), panel (d): both labels named the wrong
  quadrant.** "Metaluminous, silica-saturated" sat at FSSI < 0, which
  is undersaturated, and "peralkaline, silica-saturated" at AI > 0,
  which is not peralkaline; the lower half had no label. All four
  quadrants now carry the names Rollinson & Pease (2021) Figure 3.9d
  gives them.
- **A sweep of all 208 statistics rows against the diagrams**, looking
  for the fault that the Verma units and the Saccani normalisers both
  were: a quantity computed twice by two routes that do not share code,
  with a correction landing on only one of them. Every row was paired
  with the diagram axis plotting the same thing and required to equal
  it. The 175 Verma rows came out clean — they call the diagram
  module's own functions, so they cannot drift — and two faults turned
  up among the other 33.
- **Pearce (2008) Ti/Yb in the statistics table** reported Ti in ppm
  over Yb where the diagram of the same name plots TiO₂ in wt.% over
  Yb. The diagram had been corrected and this route to the same number
  had not, so the table and the plot disagreed by a factor of 5993
  under one heading.
- **The TiO₂ → Ti conversion existed in five places with three
  values.** Two said 5993.4, three said 5995 — which is what the
  superseded atomic weight Ti = 47.90 gives. It is now defined once and
  imported, which is what made Pearce & Gale's Ti/Y row disagree with
  its own diagram in the sixth decimal. Checking the other nine
  oxide-to-element factors the same way found P rounded upward from
  4364.27 to 4365; the rest were already right to within 0.008 %.
- **Ten Verma coefficients**, read back off the rendered pages because
  the equations are embedded objects the PDF text layer does not carry:
  seven of 110 in Verma *et al.* (2012) — including an Al₂O₃
  coefficient stored as +1.361050 where the paper prints −0.954629 —
  two in the 2013 acid majors, one in the acid immobile set and one in
  the acid traces.
- **Irvine & Baragar (1971) alkaline boundary**, of which `tas.py` kept
  a drifted private copy: (65.0, 8.8) against the published (65.0,
  9.6). The error reached 1 wt.% alkalis near SiO₂ 66, enough to call
  an alkaline trachyte sub-alkaline.
- **Le Maitre (2002)** high-Mg subdivision, **Barker (1979)** An–Ab–Or,
  **Hastie *et al.* (2007)** Th–Co, **Winchester & Floyd (1977)**,
  **K₂O–SiO₂** (one of Rickwood's three bands was drawn, as a line, and
  Le Maitre's vertical at SiO₂ 48 was missing) and the three **Frost
  *et al.* (2001)** MALI curves, which were invented straight lines.
- **Sr–Nd mantle end-members** drawn as the published polygons instead
  of star markers, with the mantle array as a measured band. **Pb**
  reduced to the NHRL alone, now on both planes.
- The **TAS Foidite label** never appeared, along with five plutonic
  labels, because the lookup keys did not match the polygon names.

#### Numerical core

- **The diagrams drawn from the norm drew nothing.** Barker's An–Ab–Or,
  the haplogranite Ab–Or–Q and Frost's AI–FSSI panel looked for columns
  named An, Ab, Or, Q, while the CIPW norm writes `norm_An`, `norm_Ab`,
  …: computing the norm, as the Norm view's own tooltip advised, left
  them empty. The sample tally hid it, counting every sample on Barker
  and the haplogranite as plotted. They now compute the norm themselves
  from the majors in use — no visit to the Norm view, and the
  adjusted-majors switch is followed — unless the dataset brings its own
  normative columns; the tally and Identify-sample read the same
  coordinates as the plot.
- **The norm read a blank oxide as zero.** Without Al2O3 a granite had
  no feldspar and its silica became quartz, putting it on the
  haplogranite's Q apex; with iron given only as FeOt or Fe2O3t, which
  the norm does not read, a basalt came out quartz-normative. A sample
  lacking SiO2, Al2O3, MgO, CaO, Na2O, K2O or FeO/Fe2O3 now gets no
  norm: the Norm view marks it `incomplete` and lists what each lacks,
  and the normative diagrams leave it off with a note saying why. Iron
  as a total is split by Data → Pre-process majors….
- **A broken `mgrs` install stopped B.I.R.D.S starting.** The package
  loads a compiled library with ctypes; when that file is missing the
  error is an `OSError`, which the optional import did not catch. It now
  costs the MGRS coordinate option only, as a missing package always
  did.
- **The saved statistics report ignored the adjustment that had been
  chosen.** Its "Adjusted data" and "CIPW norm" sheets recomputed their
  own adjustment — anhydrous, Fe after Middlemost — whatever had been
  chosen in *Pre-process majors…*, and its ratio sheet ignored the
  adjusted-majors switch. They now read the adjusted columns and the
  switch, as the screen does; "Original data" holds the analysed
  values only.
- **Pre-processing left total iron behind.** FeOt is not one of the
  oxides the 100 % rescale scales, so after it FeOt no longer equalled
  FeO + 0.8998 × Fe₂O₃: by about 0.15 % when the iron was partitioned,
  and by the whole volatile content — 1 to 5 % on an ordinary analysis —
  when it was not. It is now recomputed from FeO and Fe₂O₃ after the
  last rescale. And an oxide that was not analysed came out of the
  adjustment as 0.000 wt %; its adjusted value now stays missing.
- **Initial εNd and εSr were taken against today's reservoirs.** An
  initial ratio has to be compared with CHUR, or the Sr reservoir, as
  it was at the sample's age; the reservoirs' parent ratios were defined
  and never used. A 1 Ga rock that evolved exactly as CHUR read about
  −25 εNd instead of 0, and the error grows with age — about −2.5 units
  already at 100 Ma. Both are now taken at each sample's age, checked
  against the worked example in Rollinson & Pease (2021): CHUR at
  3.54 Ga is 0.508031. With one age for every sample the ε axes follow
  it and say so; with an age per sample no single ε axis exists, and
  none is drawn. The CHUR values, 0.512638 and 0.1967, were credited to
  Bouvier *et al.* (2008), whose CHUR is 0.512630 and 0.1960; they are
  Jacobsen & Wasserburg's (1980), and are now defined once, beside the
  lines the Sr–Nd figure draws. The bibliography gains an isotope
  section — Zindler & Hart (1986), Hart (1984), Hofmann (2003), Jacobsen
  & Wasserburg (1980), Papanastassiou & Wasserburg (1969), Steiger &
  Jäger (1977) — none of which it listed.
- **CIPW**: MnO was never allocated, so manganese vanished and the norm
  came up short by exactly the MnO content. Silica-deficient rocks had
  their residual deficit ignored, inflating the total by up to 8 wt.%
  with no indication. Excess TiO₂ now becomes rutile rather than
  disappearing.
- **Verma units.** Three sets divide trace elements in ppm by a major
  oxide in wt.%, and all three papers say to convert first. The
  conversion lived on the diagram classes, so the statistics tables —
  which reach the same coefficients by another route — reported values
  20 to 56 units high on axes the papers draw from −8 to +8. It now
  sits on the coefficient set, which both paths read.
- **Verma citations**: four were wrong in the bibliography and in the
  subtitles printed on the plots — wrong journal, wrong page range,
  reversed initials, a DOI one digit out.
- **Ni-Cu-PGE normalisers, checked against their papers.** The
  Fischer-Gödde *et al.* (2011) primitive mantle carried Au at 1.0 ng/g;
  their Table 3 and §5.3 give 1.7 ± 0.5. It also gains their Re. The CI
  chondrite was credited to Horan *et al.* (2003), but its numbers are
  not in that paper, which reports single analyses of Orgueil and Ivuna
  and no CI value; it is now the mean CI of Fischer-Gödde *et al.*
  (2010, Table 3), which takes Horan's analyses in, and goes by that
  name — sessions saved under the old one still find it. In the
  bibliography the Horan entry had the wrong title and pages, and the
  Fischer-Gödde chondrite paper was cited as GCA 75 (2011), 6027–6048:
  it is GCA 74 (2010), 356–379, and the primitive-mantle Rh and Au come
  from a second paper, Chem. Geol. 280 (2011), now listed too. Ir, Pt,
  Pd and Re of Becker *et al.* (2006) agree with the values Fischer-Gödde
  quote from it. Against McDonough & Sun (1995) itself: the primitive
  mantle credited to Barnes & Maier (1999) is McDonough & Sun's
  pyrolite (Table 5) to the last digit, and is now listed under their
  name, the old one still read from sessions — Barnes & Maier leave the
  bibliography, since nothing in the program comes from them any more;
  the CI Ni and Cu, 10910
  and 126 ppm, matched no column of their Table 2 and are now its 10500
  and 120; every primitive-mantle Ni and Cu is confirmed. So are all 73
  values of the REE and multi-element tables credited to them. The
  primitive-mantle reservoir's majors were not theirs — 44.95 SiO₂,
  0.20 TiO₂, 0.13 MnO, 37.78 MgO — and are now pyrolite model 1 of
  Table 4. Against Becker *et al.* (2006): their Os and Ru are right,
  and their primitive-mantle Au, 1.9 ± 0.6 ng/g, was missing — the
  entry said they gave none. Against Salters & Stracke (2004), Table 6:
  the depleted-mantle entry carried McDonough & Sun's *primitive*-mantle
  noble metals and Cu 24 ppm, seven of its nine values wrong; it now
  holds their depleted mantle, Re included. Every Ni-Cu-PGE value is now
  checked, and `tests/test_normalizations.py` pins each to its table and
  fails if a metal table holds a value tied to no page.

#### Interface

- **On the triangles the sample tally counted everything as plotted.**
  The ternary diagrams — the eight tectonic ones (Wood, Cabanis &
  Lecolle, Harris, Vermeesch ×5), AFM and Jensen — placed their samples
  inside their own plotting code and never told the tally where, so it
  fell back to calling every visible sample plotted: Wood reported a
  dataset with no Th, Hf or Ta as fully plotted on an empty triangle.
  Identify-sample and the selection highlight found nothing on them
  either. A shared `TernaryDiagram` now derives each sample's position
  once, for the plot and for everything that reads it, and Barker and
  the haplogranite use it too; every point drawn is where it was. Tests
  check the tally against the points actually drawn, on six dataset
  shapes, and fail if a new template draws samples without saying
  where.
- **Frost's grid is tallied across its four panels.** It had no mapping
  either, so every visible sample counted as plotted. Each panel needs
  its own elements — (d) the CIPW norm — so a sample now counts as
  plotted when any panel shows it, and a new category, *on some panels
  only*, names those another panel leaves off; a sample on none is
  missing data, or off the frame when it has coordinates but every one
  is clipped. Requiring all four panels would have called a dataset
  with no norm "nothing to show" with three panels full. Samples beyond
  a panel's frame are now flagged at its edge, as on the other
  fixed-frame templates.
- **Samples off the frame were counted as plotted.** Thirty-two of the
  53 templates fix their limits to the frame their source figure is
  drawn on — the TAS is 35–78 wt.% SiO₂ by 0–16 wt.% alkalis, the Verma
  panels run −8 to +8 — and matplotlib clips anything beyond. The tally
  under the canvas counted those samples as plotted, so "n = 12" could
  mean eleven points on screen with no way to find the twelfth. They
  are now a category of their own, clickable like the others to list
  which ones, and a hollow triangle on the frame edge points the way
  each one went. The frames are untouched: widening one would move
  boundaries that are only defined inside it.
- **Correlation heatmap**: axis labels were dropped once the matrix
  passed 30 elements, and a full analysis runs to 34, so in practice
  the axes came out with no element names at all.
- **Map view: "Auto-fit to samples" did nothing.** It was saved and
  restored with the session and read by nothing else. Unticked, it now
  keeps the frame on screen — zoomed or panned — through an update,
  and a session brings that frame back.
- **Map view: coordinate columns restored from a session were lost**
  as soon as the view was opened, which filled the selectors again
  from the column names. Choices are now kept while the columns are
  the same.
- **Maniar & Piccoli was spelt "Piccolli"** in the menu, the plot title
  and the citation printed under the plot, and was missing from the
  bibliography — as was Middlemost (1994), the source of the plutonic
  TAS and its rock naming. Both are now listed, with a new
  geostatistics section (Matheron 1963, Dubrule 1983, Webster & Oliver
  1992, Pebesma 2004). The pyproj entry still said it served Web
  Mercator.

### Changed

- **εSr is referred to the bulk silicate Earth of Zindler & Hart
  (1986), ⁸⁷Sr/⁸⁶Sr = 0.7051**, instead of the uniform reservoir of
  0.7045. The Sr–Nd figure draws its vertical line at that BSE, so
  εSr = 0 now falls on it. Taken back in time, the reservoir evolves
  with ⁸⁷Rb/⁸⁶Sr ≈ 0.0916, the ratio that runs it back to BABI at
  4.55 Ga as a closed system — the construction that gives the 0.0827
  quoted with 0.7045. εSr values are about 8.5 units lower than before.
- **CIPW simplified to the classical Cross–Iddings–Pirsson–Washington
  (1903) norm.** The SINCLAS, Verma & Rivera-Gómez (2013) and Hutchison
  variants are gone, with the titanite/perovskite chain and the
  sulphide, carbonate, halide and fluoride minerals.
- **The Map view plots longitude against latitude.** It used to draw on
  Web Mercator, and only because that is the projection the removed
  web map tiles come in. It now plots degrees directly with the aspect
  ratio fixed at the frame's centre latitude — the equirectangular
  projection, true along every meridian and along that parallel — and
  takes the length of a degree from the WGS-84 ellipsoid rather than
  from 111 km, for the scale bar, the aspect ratio and the smallest
  frame drawn. Annotations in sessions saved by the earlier view were
  stored in Mercator metres; they are converted on load instead of
  landing off the frame.
- **The WGS-84 ellipsoid is defined once**, in `birds.coords`. The UTM
  fallback and the Map view each carried their own copy of its
  constants; the fallback still agrees with pyproj to 10⁻⁹ degrees.

### Removed

- **Web basemaps, and everything that existed to serve them.** The
  satellite, topographic and grayscale backgrounds of the Map view
  came from third-party tile servers whose terms of use do not suit
  software registered and distributed by an institution, needed a
  network connection to draw at all, and changed under a figure from
  one export to the next. With them go the `contextily` dependency,
  the tile download with its timeout and worker thread, the warning
  filter for its cache, and the tests for all three. Nothing in
  B.I.R.D.S now needs the network once installed, and
  `tests/test_map_view.py` fails if any code, dependency or user
  document mentions a background map again. In place of the
  background, the view now kriges (see Added).

### Known issues

- **One coefficient departs from its printed source.** Eq (16) of Verma
  *et al.* (2013) prints the Nb term as +0.382 and it is used as
  −0.382. As printed, the three Fig. 3c centroids land about five units
  from where the same paper's caption puts them; the correction implied
  by any one term is −0.766, −0.768 and −0.765 across the three groups,
  and the panel's triple point moves from 5.06 away from the published
  one to 0.04. The reasoning is set out at the coefficient.
- **The CR column of Verma *et al.* (2013) Supplementary Table 5** is
  unusable: its log-ratios contradict the concentrations printed beside
  them and appear to have slipped a row. The panels that use it are
  verified against the printed equations only.
- **Nothing gates a Verma diagram on rock type.** Those papers require
  the type to be fixed first, with SINCLAS or IgRoCS; fed a basalt, the
  intermediate-magma set answers arc at better than even odds with no
  warning.
- **3 diagrams still have boundaries drawn by eye, and all three are
  blocked on sources rather than pending** — the two quadratic
  Vermeesch ternaries, which being QDA need per-class covariance
  matrices the paper does not publish, and `defant_drummond_YbLaYb`,
  which needs a source that has not been identified since the paper it
  cites does not contain that diagram. Nothing is left that a
  measurement could fix.
- **The La/10–Y/15–Nb/8 diagram misplaces reference MORB and OIB.** Not
  a fault in the code: Verma (2010) puts OIB + MORB at 29–62 %
  correctly classified, and Sun & McDonough's N-MORB duly falls in the
  continental-rift wedge while their OIB sits on the boundary. Only
  E-MORB lands where it should. Pinned as tests so the boundaries do
  not later get moved to suit them.
- **Figure 2's boninite field is not drawn.** Its outline does not
  resolve unambiguously in the scan: the long dashed line at Sr/Y ≈ 49
  may be its top edge or a separate boundary, and the two readings give
  fields of quite different extent.
- **Saccani gives two rules for boninite against island-arc tholeiite**
  and they do not agree everywhere. The vertical at Dy_N = 8.5 cuts the
  line of Figure 9 at Yb_N = 10, so either side of that crossing a band
  of samples is called differently — a unit of Dy_N at the foot of the
  frame, one and a half at the top. The diagram draws the line, which is
  what Figure 9 is; both rules are quoted on it so that a sample landing
  in the band is visibly a case with two answers.

## [0.1.0-alpha] – 2026-08-20

Initial version: a PySide6 desktop application for whole-rock igneous
geochemistry, with classification, Harker bivariates, REE and
multi-element spider diagrams, tectonic discrimination, Sr–Nd–Pb
isotopes, statistics, a sample-location map, CIPW norm and petrography
views, session save and restore, and Word/PDF export.
