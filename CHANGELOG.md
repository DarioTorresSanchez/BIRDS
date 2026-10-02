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
- **Butler & Woronow (1986)** disagrees with itself: reference basalts
  put through the printed equations land about 13 DF2 units below the
  printed field boundaries. Their relative arrangement is right, so the
  offset sits in the boundary coordinates. The diagram says so on
  screen and its axes follow the data. Settling it needs Vermeesch
  (2006a).
- **The CR column of Verma *et al.* (2013) Supplementary Table 5** is
  unusable: its log-ratios contradict the concentrations printed beside
  them and appear to have slipped a row. The panels that use it are
  verified against the printed equations only.
- **Nothing gates a Verma diagram on rock type.** Those papers require
  the type to be fixed first, with SINCLAS or IgRoCS; fed a basalt, the
  intermediate-magma set answers arc at better than even odds with no
  warning.
- **19 diagrams still have boundaries drawn by eye** rather than
  measured — Saccani ×3, Pearce *et al.* (1984) ×4, Vermeesch ×5,
  Defant & Drummond ×2, Pearce & Gale, Pearce & Cann, Wood, Cabanis &
  Lecolle and Harris. None of their sources is on disk.
- **Ni-Cu-PGE reference values** come from the usual compilations and
  have not been checked page by page against the original papers.
  Pattern shapes are robust; verify the absolute normalised level
  before publishing.
- **Fixed-range diagrams clip.** `x_range` / `y_range` set the limits
  hard, so a sample outside the window is drawn but invisible while the
  counter still reports it as plotted.

## [0.1.0-alpha] – 2026-08-20

Initial version: a PySide6 desktop application for whole-rock igneous
geochemistry, with classification, Harker bivariates, REE and
multi-element spider diagrams, tectonic discrimination, Sr–Nd–Pb
isotopes, statistics, a sample-location map, CIPW norm and petrography
views, session save and restore, and Word/PDF export.
