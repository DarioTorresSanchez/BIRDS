# Diagram provenance and verification status

Where every diagram boundary in BIRDS comes from, and how far it has been
checked against the source. Written 2026-09-25.

A boundary is one of three kinds of thing, and each needs a different
kind of check:

| Kind | What it is | How to verify |
|---|---|---|
| **Rule** | A definition, e.g. A/CNK = 1 | Nothing to verify — the rule *is* the boundary |
| **Equation / table** | Published coefficients or vertex list | Compare the numbers with the paper |
| **Drawn envelope** | A hand-drawn field with no equation | Measure the published figure |

Tracing an equation off a redrawing of it replaces an exact value with a
worse one, so the third method is used only where the first two do not
apply. This was the lesson of the Pb NHRL: the drawn line in the source
figure sits 5–7 px off Hart's published equation, which is the
redrawing's error, not the equation's.

The catalogue holds **47 unique diagrams**. The menus list 62 entries,
but all 15 plutonic tectonic-discrimination entries re-use volcanic keys.

---

## Summary

| Status | Count |
|---|---|
| Verified against the source | 28 |
| **Known wrong — fix first** | **0** |
| Drawn envelope, not yet measured | 19 |

One caveat remains inside the verified set: the Butler & Woronow field
boundaries disagree with their own equations. See below.

Every entry that this triage first called "known wrong" turned out to be
sound once it was checked properly — both TAS diagrams and the Verma
major-element set. The two retractions below record why, because each
came from a different bad method and both are easy to repeat.

---

## Verified (28)

**Measured from the published figure**, with the measurement pinned as
tests and the method recorded in each module's *Provenance* section:

- `hastie_2007_thco` — Hastie et al. (2007) Th–Co
- `winchester_floyd_1977` — Winchester & Floyd (1977)
- `hanski` — Hanski et al. (2001) high-Mg, including the olivine projection
- `highmg_tas` — Le Maitre (2002) high-Mg subdivision
- `barker_anaborn` — Barker (1979) An–Ab–Or

**Coefficients checked against the group centroids each paper prints.**
These papers publish, per panel, the group centroid in DF1–DF2 space and,
separately, the group mean log-ratios. The DF is linear in the
log-ratios, so evaluating it at a group's means must return that group's
published centroid. `tests/test_verma_centroids.py` asserts that for 60
centroids across six sets; `verma_agrawal_2011` prints boundaries rather
than centroids, so there its group means are required to fall in their
own fields instead.

That check found **ten wrong coefficients** across four sets, listed
below, and every one is now corrected and pinned.

| Diagram | Wrong coefficients found | Now |
|---|---|---|
| `verma_agrawal_2011` | none | 16/16 group means in their own field |
| `verma_verma_2013_major` | none | 10/10 centroids, residual ≤ 0.008 |
| `verma_verma_2013_imint` | none | 10/10 centroids, residual ≤ 0.042 |
| `verma_verma_2013_trace` | none | 10/10 centroids, residual ≤ 0.009 |
| `verma_2012_acid` | 7 of 110 | pinned digit-by-digit (no centroids published) |
| `verma_2013_acid_macid` | 2 of 98 | centroids match, less the CR column (below) |
| `verma_2013_acid_mtacid` | 1 of 58 | 10/10 centroids |
| `verma_2013_acid_tacid` | 1 of 78 | 10/10 centroids |

### Why the previous pass missed them

The earlier method matched every stored coefficient against every
decimal appearing *anywhere* in the paper and reported hit rates of
95–100 %. It recorded the handful of misses and dismissed them as
"consistent with rounding in the PDF's text layer". They were not
rounding; they were the errors. `verma_2012_acid` was scored 105/110
and actually had seven wrong values, including an Al₂O₃ coefficient
stored as +1.361050 where the paper prints −0.954629.

Two failures compounded:

1. **Presence is not position.** A coefficient in the wrong slot, or
   with a transposed digit that happens to appear elsewhere in a long
   supplementary table, scores as a hit.
2. **A miss was treated as noise.** Every one of them was a real defect.
   A check that reports misses and then explains them away is not a
   check.

Matching against the paper's *output* — its centroids — has neither
weakness: a coefficient in the wrong slot, of the wrong sign or off by a
digit all move the centroid, and the discrepancy localises the term.

### Two departures from the printed sources

- **`verma_2013_acid_mtacid`, eq (16), Nb.** Printed +0.382, used as
  −0.382. As printed, the three Fig. 3c centroids come out ~5 units
  below where the same paper's caption puts them, while eq (15) matches
  that caption's DF1 to 0.03; the implied single-term correction is
  −0.766, −0.768, −0.765 across the three groups (sd 0.001), which is a
  change of sign, not of magnitude. Independently, the triple point is
  the circumcentre of the three centroids in LDA canonical space: as
  printed it lands 5.06 away from the published one, with the sign
  flipped, 0.04. Full reasoning sits at the coefficient.
- **`verma_2013_acid_macid`, Supplementary Table 5, CR column.** Not a
  code change — that column of the paper is unusable. Its ln-ratios
  contradict the concentrations printed beside them in the same table
  (ln(Fe₂O₃/SiO₂) given as −1.693 where 1.10 wt.% over ~70 wt.% SiO₂
  needs ≈ −4.2), and the values line up one row below where they belong,
  so the column appears to have slipped in typesetting. The CR-bearing
  panels are therefore verified against the printed equations only.

### Posterior probabilities

The statistics table reports, per panel, the probability of each of the
three tectonic settings, following Verma & Agrawal (2011) eqs (1)–(12):
the distance from the sample to each group centroid, `exp(−d²/2)`, then
normalised. Every later paper in the family refers back to that one for
the calculation. 33.3 % is the by-chance level, and a boundary between
two fields is where those two reach 50 %.

The model is checked against figures it never saw. Equal probability for
three groups means equal distance to three centroids, so each panel's
triple point has to be the **circumcentre** of its centroids — and the
triple points come from the figure captions, the centroids from
elsewhere in the same papers. They agree to 0.000–0.009 on the three
intermediate sets, and each group comes out at exactly 33.3 % there. For
`verma_agrawal_2011`, whose centroids are derived from its Table 2 group
means because its Table A4 sits in a supplement not to hand, the
agreement is 0.001–0.012 — which validates the derivation, since the
triple points play no part in it. The 2013 acid sets, whose centroids
are printed to one or two decimals, agree to 0.13.

`verma_2012_acid` publishes neither centroids nor group means, so it
reports DF values only.

### Units

Three sets divide ppm trace elements by a wt.% major oxide:
`verma_agrawal_2011` (Nb, V, Y, Zr / TiO₂), `verma_verma_2013_imint`
(Nb, Ni, V, Y, Zr / TiO₂) and `verma_2013_acid_mtacid` (Nb, Y, Zr /
TiO₂). All three papers say to convert first — "all trace element data
(μg·g⁻¹) in these equations were first converted to wt.% before
calculating the trace to major element log-ratios".

That conversion used to live on the diagram classes, so the statistics
tables, which reach the same coefficient sets by a different route,
reported values 20 to 56 units out on axes that span ±8. It now lives on
`DFCoefSet.ppm_parts`, which both paths read, and a test asserts the two
paths return the same number.

**Rule, nothing to verify:**

- `maniar_piccolli` — A/CNK = 1 and A/NK = 1 (Shand's definition)

**Checked vertex-by-vertex against the published coordinate table**
(Le Bas et al. 1986, as tabulated in Rollinson & Pease 2021 Fig. 3.1b):

- `tas_volcanic`, `tas_plutonic`

---

## Retracted findings

### ~~`verma_verma_2013_major` — coefficients are not published~~ — RETRACTED

**This entry was wrong too**, and wrong for a specific, repeatable
reason: the check matched the code against numbers extracted from the
PDF's *text layer*, and equations (1)–(10) of that paper are set as
embedded objects that never reach it. Absence from the text layer was
taken as evidence of a mismatch. It is evidence of nothing.

Read off the rendered pages instead, and diffed value by value,
**102 of the 110 coefficients were already exact**. The eight that
differed were truncations of the final digits, not different numbers:

```
DF1_IACA_CROI_COL  MnO     -0.21204   ->  -0.212024
DF1_IA_CROI_COL    Na2O    -0.827429  ->  -0.8274299
DF1_IA_CROI_COL    K2O     -0.488469  ->  -0.4884699
DF2_IA_CROI_COL    TiO2    -0.736653  ->  -0.736658
DF2_IA_CROI_COL    Al2O3   -0.078809  ->  -0.0788099
DF2_IA_CROI_COL    CaO      0.681694  ->   0.6816946
DF2_IA_CROI_COL    Na2O    -1.32843   ->  -1.3284307
DF2_IA_CROI_COL    K2O      0.77094   ->   0.7709408
```

All eight are now the published values, and
`tests/test_verma_coefficients.py` pins all 110 so they stay that way.

**No sample was ever misclassified.** On a typical andesite the
truncations shifted a discriminant score by at most 1 × 10⁻⁴, on axes
that span −8 to +8 — six millionths of the range.

Two things in the module were genuinely wrong and are fixed: the
citation named the wrong authors, title and page range, and the
docstring claimed that "small numerical edits don't change the overall
topology". For a discriminant function that is false — the
coefficients *are* the boundary — and it is exactly the sort of licence
that lets a wrong digit survive review.

**Second lesson for this triage:** a negative result from text
extraction is not a finding. Confirm it by rendering the page.

### ~~`tas_volcanic` / `tas_plutonic` — malformed polygons~~ — RETRACTED

**This entry was wrong.** It was written from the shape of the data
structure without rendering the diagram, and every geometric complaint
in it was a false alarm. Checked against Rollinson & Pease (2021)
Fig. 3.1b — which tabulates Le Bas et al. (1986)'s plotting coordinates
vertex by vertex — **the TAS boundaries are correct**:

- The two-point entries are deliberate boundary *segments*. Fields are
  drawn as closed but **unfilled** outlines, so a field the frame bounds
  on one side needs only the edges the frame does not supply.
- `(63, 14.5)` is not an invented vertex: it is the published ray
  through `(57.6, 11.7)` and `(61, 13.5)` carried out to the frame.
  Slope 0.5294 gives 14.56 at SiO₂ = 63.
- The Phonolite "spur" exists in the vertex list but cannot be seen:
  `(50, 15.083)`, `(52.5, 14)` and `(57.6, 11.7)` are collinear to
  within 0.03 wt.%, so the closing edge hides under the real boundary.
- The foidite/phonolite line measured off Fig. 3.1b has slope −0.388
  against the code's −0.433; both leave the frame at SiO₂ ≈ 48, well
  inside the reading precision of a scanned figure.

What was genuinely wrong was one **missing label**, now fixed:
`Foidite`'s outline is drawn in full by its neighbours and the frame,
but its name never reached the plot because the label override was
keyed on a name no polygon used. Five plutonic label overrides had the
same defect (`Foid syenite` vs `Foid\nSyenite`, and four more), so those
labels fell back to polygon centroids.

`tests/test_tas.py` now pins every vertex to the published list.

`tas_volcanic` now also names compositions. `TASVolcanic.classify()`
takes SiO₂ and Na₂O + K₂O and returns the IUGS name;
`classify_frame()` does a whole table at once. The classification
regions are built **from the drawn outlines**, so a name cannot drift
away from the picture: eleven of the fourteen close on their own and
are reused verbatim, and only Rhyolite, Trachyte/Trachydacite,
Phonolite and Foidite get an explicit closed form, because those are
the ones the frame bounds. A test walks a 20 000-point grid and
asserts the regions tile the plane with no gap and no overlap, and a
second test asserts that every field label sits inside the field it
names — the labels were placed by eye and the regions derived by rule,
so agreeing is a real check rather than a tautology.

Tephrite/Basanite and Trachyte/Trachydacite are separated by normative
olivine and quartz, which are not axes of this plane. Pass
`normative_ol` / `normative_q` to split them; without those, the pair
is returned whole, the same convention `highmg_tas` uses for komatiite
versus meimechite.

`tas_plutonic` still has no `classify()`. Its outlines do not tile —
`Foid Monzodiorite` and `Foid Monzosyenite` are drawn as single
boundary segments, and several fields are open at the frame — and
Middlemost (1994) is **not** among the sources on disk, so the
closures cannot be derived from anything. Guessing them is exactly the
mistake this document exists to prevent. This needs the published
figure before it can be done.

**Lesson for the rest of this triage:** a diagram must be *rendered*
before its geometry is called wrong. Three of the four defects listed
above came from reading tuples instead of looking at the output.

---

## Equation or table — now checked (9)

All nine are settled. Rollinson & Pease (2021) prints the plotting
coordinates in its figure captions, tabulates the haplogranite minima
outright in Table 3.10, and gives the oceanic-basalt discriminant
functions in Appendix 5.1, so none of this needed measuring.

**Verified unchanged** — the code already carried the published numbers
exactly:

| Diagram | Source |
|---|---|
| `ib1971` | Fig. 3.3 caption — Irvine & Baragar, Kuno, MacDonald |
| `jensen` | Fig. 3.8b caption — the tholeiitic/calc-alkalic boundary |
| `afm` | Fig. 3.18b caption — the boundary the book recommends |
| `haplogranite` | Table 3.10, the eight water-saturated points |
| `shervais_1982_TiV` | Ti/V rays are arithmetic, and the arithmetic is right |

`afm` also draws an Irvine & Baragar (1971) overlay whose coordinates
the caption does not print; that one curve is still unverified.
`haplogranite` keeps one determination per pressure out of the twelve
water-saturated rows in Table 3.10 — a curation choice, now documented.

**Corrected**:

* **`k2o_sio2`** drew one of Rickwood's three bands, as a single line,
  with its first point rounded from 1.38 to 1.4, and called it the
  band's midpoint; it was the upper bound. The Le Maitre vertical at
  SiO₂ = 48 was missing too. All three bands are now drawn as bands,
  from the coordinates the Fig. 3.4 caption prints.
* **`frost`** had the Fe-index boundary right — it is the published
  `0.46 + 0.005·SiO₂` — and ASI, AI and FSSI are definitional. Its
  three MALI boundaries were straight lines between invented endpoints;
  the published ones are curves. Measured from Fig. 3.9b and replaced.
* **`pearce_1976_DF`** and **`butler_woronow_DF`** were the real find.
  Both are **DF1–DF2 binary diagrams** with three fields around a
  central point, and both were implemented as one-dimensional strip
  charts, which cannot make a three-way split at all. The coefficients
  matched nothing: the Pearce function carried an `Fe2O3t` term the
  published equation does not have, dropped its `MnO` term, and added
  an intercept; none of its seven coefficients was right. Butler &
  Woronow divided TiO₂ by SiO₂ and Zr and Y by Sr, where the published
  axes divide Zr, Y and Sr by Ti, and its "intercept" of −1.840 is in
  fact the published Sr coefficient of DF2. Both now use Appendix 5.1.

  Three reference basalts — N-MORB, OIB and IAB — put through the
  rebuilt Pearce function land in their own fields, which checks the
  equations, the boundary geometry and the implementation at once.

### ~~One open question~~ — RESOLVED

Butler & Woronow's panel used to disagree with its own equations:
reference basalts came out about 13 DF2 units below the printed field
boundaries, and no change of units closed the gap.

**Both Zr coefficients are negative.** Vermeesch (2006a) equation (7)
reads `ld1 = -0.016 log(Zr/Ti) - 2.961 log(Y/Ti) + 1.500 log(Sr/Ti)`
and `ld2 = -1.474 log(Zr/Ti) + ...`, and the minus signs are in the
rendered page but not in the characters behind it — the PDF text layer
gives back `ld1 ¼ 0:016 log Zr=Ti`. Rollinson & Pease print them
without the sign too, which is where the stored values came from.

With the signs right, a reference N-MORB moves from ld2 = −26.1 to
−12.7 against a triple point published at −12.23. All three reference
basalts now sit 1.8 to 2.4 units from it, each in its own field. The
on-screen caution is gone and `tests/test_published_coordinates.py`
pins both the signs and the distances.

The boundary coordinates were right all along — they are the anchor
points of Vermeesch's Table 6, which is also where Rollinson & Pease
took them from.

**Checked while in there, and left alone:** Vermeesch's equation (8),
for the Pearce (1976) major-element set, prints `0.555 log(TiO2/SiO2)
+ 3.822 log(Al2O3/SiO2)` while this code pairs 0.555 with Al2O3 and
3.822 with TiO2. The stored pairing is the one that works: it puts the
three reference basalts in three different sectors around the published
triple point, a mean 2.7 units away, where the paper's literal reading
bunches all three into one sector 12.8 units off. Either the equation's
first two coefficients or its first two element names are transposed in
print; the anchor points settle which.

### Also found along the way

`tas.py` kept its own copy of the Irvine & Baragar curve, which had
drifted to (65.0, 8.8) and (77.4, 10.0) against the published (65.0,
9.6) and (66.4, 10.0) — while a comment claimed the two lists were the
same. The error reached 1 wt.% alkalis near SiO₂ 66, enough to call an
alkaline trachyte sub-alkaline. It now imports the list instead of
copying it. The tail beyond SiO₂ 66.4 is an extrapolation and is drawn
faded to say so.

`Ti` was converted from TiO₂ with 5995 ppm per wt.% in four places;
the mass ratio gives 5993.4. Now a named constant, shared.

## Drawn envelope — twelve done, 10 to go

### Done (3)

**`pearce2008_thyb_nbyb` and `pearce2008_tiyb_nbyb`** — measured from
Pearce (2008) Fig. 2, the figure the paper calls "the two diagrams that
form the basis for this paper". The calibration is fixed by locating
the three Sun & McDonough (1989) markers the paper plots: they come out
within 1 % of the published ratios in Th/Yb and TiO₂/Yb.

Both panels were wrong before:

* The **Th/Yb array** was bounded at Th/Nb 0.07 and 0.32. Measured, it
  is **0.043 to 0.096** — and with the old bounds N-MORB (Th/Nb 0.0515)
  plotted *below* the MORB–OIB array it is supposed to sit in. Fitting
  the drawn bounds with a free slope gives 1.03 and 1.06 in log-log, so
  a constant-ratio band is right, which is also what Th/Nb being the
  crustal-input proxy implies. Pearce's own contamination filter,
  Th/Nb > 0.2, is now drawn too.
* The **second panel's y axis was the wrong quantity**. Pearce plots
  **TiO₂ in wt.% over Yb in ppm**; the module computed Ti in ppm over
  Yb, which differs by a factor of 5993. Its "MORB field" at Ti/Yb
  2000–4500 and "OIB above 5000" belonged to neither convention, and
  were flat where the published arrays rise. The three bounds are now
  fitted as TiO₂/Yb = a·(Nb/Yb)^b, with exponents agreeing to 0.006 —
  parallel bands. The tholeiitic/alkalic divide inside the OIB array
  and the N/E-MORB divide at Nb/Yb = 1.45 (the C1 chondrite value the
  caption states) are drawn as published.

**`yang_2019_fckantms`** — the source turned out to be the unidentified
`Using_Major_Element_Logratios_…pdf` already in the folder: Yang, Li,
Jiang, Xu, Guo, Li & Zhang (2019), *JGR Solid Earth* 124, 3429–3480.
Its Table 1 prints all eight equations, so nothing needed measuring.

This one was invented outright. FCMS and FCKANTMS are **log-ratio
residuals** — the measured ln(FeO/CaO) minus what a lherzolite melt of
the same ln(MgO/SiO₂) would have — so a peridotite melt sits at
0.00 ± 0.08 and a mafic-source melt above it. The module computed them
as plain sums of oxide wt.%, `FCMS = SiO₂ + 0.99·K₂O − 1.32·Al₂O₃ −
0.78·MgO`, on axes running to ±20. Neither expression is in the paper
and neither is a log-ratio. It also plotted FCMS against FCKANTMS,
which the paper notes are near-equivalent, so the pair carried almost
no discrimination; and it cited the wrong journal and authors.

Rebuilt on equations (2) and (8) as printed, plotted on the axes the
paper recommends — FCKANTMS against ln(SiO₂/(CaO+Na₂O+TiO₂)), its
Fig. 7b — with the three boundary polylines the caption gives as
coordinates. An internal check holds: equation (8)'s constant, 1.473,
equals equation (6)'s 0.271 plus equation (7)'s 1.201.

### Computed, not measured (5)

`vermeesch_SiTiSr`, `vermeesch_EuLuSr`, `vermeesch_VTiSc`,
`wood_1980_ThHfTa` and `pearce_cann_1973_ZrTi` were drawn
envelopes — polygons typed in ternary percent, approximating by eye
something that can be computed exactly. They are not any more.

Vermeesch runs a linear discriminant analysis in log-ratio space, where
the decision boundaries come out straight, and maps them back to the
ternary, where "the transformed decision boundaries are no longer
linear, but curved". His **Table 6** gives four anchor points per
diagram in log-ratio coordinates: node 3 is the triple point and nodes
1, 2 and 4 the three ray ends. Both axes divide by the top apex, so the
pair is an ordinary additive log-ratio and the inverse is a softmax.
The boundaries are now sampled along each ray and mapped back, which is
why they curve on screen.

Three things had to be settled that the paper does not state outright:

- **The logarithm is natural.** See `tests/test_vermeesch_lda_ternaries.py`,
  whose module docstring sets out the evidence from the published
  training clusters of Figure 42a.
- **Which apex is which.** Figures 42b, 43b and 44b put Ti/40, 500 Lu
  and Ti/50 at the top respectively. The previous implementation had
  Si/1000 at the top of the Si-Ti-Sr triangle, which permutes the
  corners and is a different diagram.
- **Which sector is which field**, read from panel (a) of each figure.

Reference N-MORB, OIB and IAB compositions now land in their own field
on all three, nine assignments out of nine.

**Wood (1980) Th–Hf/3–Ta** joins them, replacing the fields Wood drew by
eye with Vermeesch's LDA (his Figure 41b). One anchor point is used
against what Table 6 prints. The table gives node 2 as (1.43, −1.5),
which puts it diagonally opposite where the figure draws it and sends a
reference N-MORB into the OIB field. The figure was measured to settle
it: the four numbered discs were detected in a render of panel (b) and
the axes calibrated on nodes 1, 3 and 4, which do agree with the table.
That calibration reproduces node 3 as (−0.076, −0.864) against a
published (−0.07, −0.86) — so it is trustworthy — and puts node 2 at
(−1.44, +1.50): the printed magnitudes to a hundredth, both signs
reversed.

**Pearce & Cann (1973) Zr–Ti** was drawing two straight dotted lines at
Ti/Zr = 30 and 110, with a comment calling them "approximate refined
boundaries". They were neither Vermeesch's nor refined. His Figure 38
is not three rays from a triple point but **two separate segments**,
each given by its two endpoints, which is why that row of Table 6
repeats its x values as −13, −7, −13, −7. The axes are the additive
log-ratio of (Zr, Ti, everything else) in ppm, so mapping a boundary
back to Zr–Ti is the same softmax the ternaries use, scaled by 10⁶.

### Published coordinates, two of them corrected (4)

The four **Pearce, Harris & Tindle (1984)** granitoid discriminants are
among the rare diagrams of their era whose authors printed the boundary
coordinates outright, in the captions of their Figures 3 and 4. What
was here before was hand-written line segments bearing no relation to
those captions — one of them commented "approximate boundaries" — and
is now the published numbers.

Two of the printed coordinates are wrong. **Verma et al. (2012)**
corrected both while re-evaluating these diagrams against the original
authors' own database, and both corrections are checkable from the
geometry rather than taken on trust:

- **Yb–Ta, syn-COLG/WPG**, printed as `(55,20) to (3,2)`. The two
  fields it divides lie above and to either side of (3,2), so the
  boundary has to leave that point going up and to the left. (55,20) is
  down and to the right — the opposite quadrant, where WPG already is.
  Used as `(0.1,100) to (3,2)`, which is how Figure 3b draws it.
- **Rb–(Yb+Ta), syn-COLG/VAG**, printed as ending at `(6,2000)` where
  the other two boundaries of that junction both start at `(6,200)`. A
  triple point has to be one point, and Figure 4b draws the junction at
  Rb = 200, so the printed value is a factor of ten out.

`tests/test_pearce_1984.py` pins every published coordinate and, more
usefully, asserts that the boundaries sharing a field actually meet.
That junction check is exactly what the second error breaks, and it
would have caught it in the original.

### Still to measure (10)

- `saccani2015_nb_th`, `saccani2015_dy_yb`, `saccani2015_ce_dy_yb`
- `pearce_gale_1977`
- `defant_drummond_YSrY`, `defant_drummond_YbLaYb`
- `vermeesch_NaNbSr`, `vermeesch_SmTiV` — the two **QDA** ones, whose
  boundaries are conics in log-ratio space rather than rays from a
  triple point, so Table 6 has no anchor points for them
- `cabanis_lecolle_1989`, `harris_1986_HfRbTa`

None of their sources is on disk.

## Method

The coefficient check is reproducible: extract every decimal number from
the source PDF with PyMuPDF, then ask whether each coefficient in the
code matches one of them to 5 × 10⁻⁶. A control run on a hand-read
equation (Eq. 6, page 934) matched all eleven of its values, so the
method does not produce false negatives through text-extraction damage.

Comparing a set against the wrong paper gives 0 %, which is how the acid
and basic sets first appeared to fail — they were checked against the
intermediate-magma paper by mistake. Each set must be matched to its own
source before the number means anything.
