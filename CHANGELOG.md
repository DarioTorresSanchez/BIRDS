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
  whole. The plutonic TAS has no equivalent yet — its outlines do not
  tile and Middlemost (1994) is not to hand.
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

#### Interface

- **Samples off the frame were counted as plotted.** Thirty-two of the
  52 templates fix their limits to the frame their source figure is
  drawn on — the TAS is 35–78 wt.% SiO₂ by 0–16 wt.% alkalis, the Verma
  panels run −8 to +8 — and matplotlib clips anything beyond. The tally
  under the canvas counted those samples as plotted, so "n = 12" could
  mean eleven points on screen with no way to find the twelfth. They
  are now a category of their own, clickable like the others to list
  which ones, and a hollow triangle on the frame edge points the way
  each one went. The frames are untouched: widening one would move
  boundaries that are only defined inside it.
- **The Map view froze** on a slow basemap. contextily fetches tiles one
  at a time through `requests.get` with no timeout, from the redraw, on
  the GUI thread; one measured CartoDB Positron fetch took 1204 s
  against 3.5 s for Esri on the same extent. The download now runs on a
  worker thread behind a 25 s deadline and takes eight tiles at a time,
  which also cut the healthy path from 3.5 s to 1.3 s.
- A joblib cache warning from contextily, harmless but alarming, is
  filtered.
- **Correlation heatmap**: axis labels were dropped once the matrix
  passed 30 elements, and a full analysis runs to 34, so in practice
  the axes came out with no element names at all.

### Changed

- **CIPW simplified to the classical Cross–Iddings–Pirsson–Washington
  (1903) norm.** The SINCLAS, Verma & Rivera-Gómez (2013) and Hutchison
  variants are gone, with the titanite/perovskite chain and the
  sulphide, carbonate, halide and fluoride minerals.

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
- **FCMS is computed but never plotted.** Yang *et al.* (2019) give two
  parameters and the statistics table reports both, but only the
  FCKANTMS diagram exists, so there is no figure to read an FCMS value
  against. Found by the sweep, which pairs rows with diagrams: this one
  has no partner.
- **Nothing gates a Verma diagram on rock type.** Those papers require
  the type to be fixed first, with SINCLAS or IgRoCS; fed a basalt, the
  intermediate-magma set answers arc at better than even odds with no
  warning.
- **5 diagrams still have boundaries drawn by eye** rather than measured
  or computed — Vermeesch ×2 (the quadratic ones), Pearce & Gale,
  Cabanis & Lecolle and Harris. Three of the five are blocked rather
  than pending: the Vermeesch pair, being QDA, need per-class
  covariance matrices that the paper does not publish, and
  `defant_drummond_YbLaYb` needs a source that has not been identified,
  since the paper it cites does not contain that diagram.
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
- **Ni-Cu-PGE reference values** come from the usual compilations and
  have not been checked page by page against the original papers.
  Pattern shapes are robust; verify the absolute normalised level
  before publishing.

## [0.1.0-alpha] – 2026-08-20

Initial version: a PySide6 desktop application for whole-rock igneous
geochemistry, with classification, Harker bivariates, REE and
multi-element spider diagrams, tectonic discrimination, Sr–Nd–Pb
isotopes, statistics, a sample-location map, CIPW norm and petrography
views, session save and restore, and Word/PDF export.
