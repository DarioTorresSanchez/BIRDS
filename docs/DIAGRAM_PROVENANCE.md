# Diagram provenance and verification status

Where every diagram boundary in BIRDS comes from, and how far it has been
checked against the source. Written 2026-09-25; the summary brought up
to date 2026-10-10.

A boundary is one of three kinds of thing, and each needs a different
kind of check:

| Kind | What it is | How to verify |
|---|---|---|
| **Rule** | A definition, e.g. A/CNK = 1 | Nothing to measure — the rule *is* the boundary — but check the arithmetic under it and whatever else is drawn |
| **Equation / table** | Published coefficients or vertex list | Compare the numbers with the paper |
| **Drawn envelope** | A hand-drawn field with no equation | Measure the published figure |

Tracing an equation off a redrawing of it replaces an exact value with a
worse one, so the third method is used only where the first two do not
apply. This was the lesson of the Pb NHRL: the drawn line in the source
figure sits 5–7 px off Hart's published equation, which is the
redrawing's error, not the equation's.

The catalogue holds **54 unique diagrams**. The menus list 85 entries,
but all 26 plutonic tectonic-discrimination entries re-use volcanic keys.
The six modal diagrams of the Petrography view are outside these
counts; they have their own section at the end, *The Petrography
view*.

---

## Summary

| Status | Count | Section |
|---|---|---|
| Measured from the figure, or checked against the centroids it prints | 16 | *Measured, or checked against printed centroids* |
| Equation or table, compared with the published numbers | 9 | *Equation or table* |
| Verma's group, 2004–2008: functions and caption coordinates, checked against the authors' sheet | 3 | *Verma's group, 2004–2008* |
| TAS, volcanic and plutonic, vertex by vertex | 2 | *Retracted findings*, *Middlemost (1994)* |
| Rule, with the arithmetic under it checked | 1 | *Maniar & Piccoli (1989)* |
| Drawn envelope, now measured, computed or read from printed coordinates | 21 | *Drawn envelope* to *Vermeesch (2006a) — the two QDA ternaries* |
| A plane computed from printed equations, with no fields to check | 1 | *Yang et al. (2019)* |
| **Known wrong — fix first** | **0** | |
| Still drawn by eye, blocked on sources | 1 | *Still drawn by eye* |
| **Total** | **54** | |

The Irvine & Baragar (1971) overlay on `afm`, the one curve this summary
used to call unverified, is now Rickwood's (1989) measurement of their
figure (see *Equation or table*).
The Butler & Woronow disagreement this summary used to flag is resolved:
two minus signs the PDF text layer drops (see below).

Every entry that this triage first called "known wrong" turned out to be
sound once it was checked properly — both TAS diagrams and the Verma
major-element set. The two retractions below record why, because each
came from a different bad method and both are easy to repeat.

---

## Measured, or checked against printed centroids (16)

**Measured from the published figure**, with the measurement pinned as
tests and the method recorded in each module's *Provenance* section:

- `hastie_2007_thco` — Hastie et al. (2007) Th–Co
- `winchester_floyd_1977` — Winchester & Floyd (1977)
- `hanski` — Hanski et al. (2001) high-Mg, including the olivine projection
- `highmg_tas` — Le Maitre (2002) high-Mg subdivision
- `barker_anaborn` — Barker (1979) An–Ab–Or
- `li2025_nbyb_thnb` — Li, Godang & Saputro (2025) Nb/Yb vs Th/Nb; see
  *Li et al. (2025)* below
- `godang2024_nbzr_thnb` — Godang, Saputro & Li (2024) Nb/Zr vs Th/Nb;
  see *Godang et al. (2024)* below
- `martin_1986_LaYbN` — Martin (1986) (La/Yb)N vs YbN, Archean TTG and
  post-Archean granitoids; see *Martin (1986)* below

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
| `verma_verma_2013_imint` | 6 of 80, found against the authors' sheet | 10/10 centroids, residual ≤ 0.042 |
| `verma_verma_2013_trace` | 2 of 80, found against the authors' sheet | 10/10 centroids, residual ≤ 0.009 |
| `verma_2012_acid` | 7 of 110 | pinned digit-by-digit; centroids from the authors' sheet, 5/5 triple points within 0.004 |
| `verma_2013_acid_macid` | 2 of 98 | centroids match, less the CR column (below) |
| `verma_2013_acid_mtacid` | 1 of 58 | 10/10 centroids |
| `verma_2013_acid_tacid` | 1 of 78 | 10/10 centroids |

### Against the authors' own sheet (2026-10-22)

`MGV_DB_4.sta` is the Statistica worksheet in which Verma's group
computed all of these diagrams: it defines every function of the eight
sets, most to 17 figures, and stores the scores and probabilities of
518 samples. A paper prints the sheet's value rounded or cut short, so
`tests/test_verma_statistica_sheet.py` requires each coefficient to be
exactly that, and every exception was read on the rendered page.

It found **eight more wrong coefficients**, all in Verma & Verma (2013)
and all copying slips — the page agrees with the sheet each time. One
mattered: P₂O₅ of eq (19), −1.1082014 for −1.082014, moved DF1 of the
major + trace set by up to 0.19 on real samples. With them corrected,
the program reproduces the sheet's scores on its 518 samples to 3 ×
10⁻⁵ for the intermediate sets and 10⁻¹⁴ for `verma_2012_acid`, and
its probabilities exactly for all three intermediate sets.

Three printed values are neither the sheet's rounded nor truncated —
eq (7) of Verma & Verma (2013) and the constants of eqs (1) and (16)
of Verma et al. (2013) — and stay as printed. The sheet also settles
the sign of Nb in eq (16) of Verma et al. (2013): −0.38213, as the
program uses, not the printed +0.382 (*Known issues* in the
CHANGELOG).

The sheet also supplies the centroids two papers do not print, and
the program now uses them: Verma & Agrawal (2011), whose own are in a
supplement not to hand — the sheet's put the published triple points
within 0.002, where those derived from the Table 2 means were off by up
to 0.012 — and Verma et al. (2012), which prints none, so that set now
gives probabilities too (within 0.004 of every triple point, each
centroid inside its own field, and the sheet's probabilities matched
exactly on its 518 samples).

The sheet is not without faults of its own. Its probabilities for
panels (b)–(e) of Verma & Agrawal (2011) take the third group's
distance in DF2 from DF1 (`Y32 = Sdf12 − MdfG322`, and likewise in the
other three); the program does not, and agrees with the sheet once
that is corrected.

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

**Rule, nothing to measure:**

- `maniar_piccolli` — A/CNK = 1 and A/NK = 1 (Shand's definition); the
  molar arithmetic and what else is drawn are checked too, and one
  label was wrong. See *Maniar & Piccoli (1989)* below.

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

## Verma's group, 2004–2008 — three basic-rock sets

| Diagram | Paper | Functions | Fields |
|---|---|---|---|
| `agrawal_2004_basic` | Agrawal, Guevara & Verma (2004), IGR 46 | Tables 6, 7: the adjusted oxides themselves | Figure 2 and 3 captions |
| `verma_2006_basic` | Verma, Guevara & Agrawal (2006), J Earth Syst Sci 115 | Tables 6, 7: ten ln(oxide/SiO₂) | Figure 5 and 6 captions |
| `agrawal_2008_basic` | Agrawal, Guevara & Verma (2008), IGR 50 | Table 6: ln(La, Sm, Yb, Nb / Th) | Figure 1 and 2 captions |

Five panels each over IAB, CRB, OIB and MORB. The papers print every
boundary as two end points, so the fields are those segments; in the
two four-group panels (2004 Fig. 2, 2006 Fig. 5) they meet at two
triple points. All thirty functions are the authors' sheet digit for
digit and reproduce its scores on 518 samples to 10⁻¹⁴; each field
lies where the figure names it (`tests/test_verma_basic_sets.py`).
None of the three prints centroids, so they give scores and fields, not
probabilities. One caption slip: 2004 Fig. 2 ends the IAB–CRB boundary
at (−0.52, −0.99) where the other two through that point end at
(−0.52, −1.03); it is closed at the triple point.

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

`afm` also draws the Irvine & Baragar (1971) and Kuno (1968) dividing
curves, which the caption does not print. Rickwood (1989, *Lithos* 22,
Table 3) measured both on the original figures, and the diagram now
carries his points: its Irvine & Baragar curve had been an
approximation up to 8 units of F off theirs, and Kuno, cited, was not
drawn. Rickwood's Table 1 confirms `ib1971` point for point (Irvine &
Baragar, Kuno 1966, MacDonald 1968), his section 2.2 the `k2o_sio2`
bands, and his Table 4 six of the eight `jensen` points as printed and
the other two through misprints of his own that do not sum to 100
(`tests/test_rickwood_1989.py`).
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
  the published ones are curves. Measured from Fig. 3.9b and replaced
  — and since 2026-10-12 computed from the fits Frost *et al.* (2001)
  print, see below.
  Being definitional did not make the ASI right: it was computed on a
  mixed basis that put anorthite at 2. See *Frost et al. (2001)* below.
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

## Drawn envelope — 21 done, 1 blocked

Twelve are in the three subsections below; Saccani, Defant & Drummond,
Pearce & Gale, Cabanis & Lecolle, Harris and the two Vermeesch QDA
ternaries have a section each after them; the one still drawn by eye is
listed last.

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

The four **Pearce, Harris & Tindle (1984)** granitoid discriminants —
`pearce1984_YNb`, `pearce1984_YbTa`, `pearce1984_YNbRb` and
`pearce1984_YbTaRb` — are
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

## Saccani (2015) — three diagrams, every coordinate printed

`Sacanni_2014.pdf` — Saccani, E. (2015) *Geoscience Frontiers* **6**,
481–501. Keys `saccani2015_nb_th`, `saccani2015_ce_dy_yb`,
`saccani2015_dy_yb`.

Section 7 says the boundaries of Figures 5, 8 and 9 "were drawn by eye
in order to obtain the best discrimination between different basaltic
types", so there is no analysis to reproduce. But every line has its end
coordinates printed on the figure itself, in brackets beside an arrow
pointing at the end they belong to. Those are what the three diagrams
carry; nothing here is measured off a figure.

**Figure 5a**, Th_N vs Nb_N, N-MORB-normalised (Sun & McDonough 1989),
log–log, 0.01–100 by 0.01–1000. Four segments:

| From | To | What it bounds |
| --- | --- | --- |
| PM `(0.306, 0.708)` | `(100, 1000)` | MORB–OIB array below, volcanic arc array above |
| `(0.01, 0.1)` | PM | its continuation below PM |
| `(0.01, 20)` | `(2.2, 8.0)` | upper bound, inside the arc array |
| PM | `(0.5, 0.01)` | the near-vertical one, down from PM |

The first is the one that discriminates, and the text quantifies it both
ways: ">99% of the analyzed basaltic rocks from oceanic,
subduction-unrelated settings plot below" it, and ">99% of
subduction-related basaltic rocks plot above". PM is the printed
`(0.306, 0.708)`, which is Sun & McDonough's primitive mantle over their
N-MORB — Nb 0.713/2.33 and Th 0.0850/0.12. Neither primitive mantle in
this project's own tables (McDonough & Sun 1995, Palme & O'Neill 2014)
reproduces it, so the printed pair is used as printed.

Two things are deliberately left as the source has them:

- The segment `(0.01,20) → (2.2,8.0)` does not quite reach the main one,
  which passes through Th_N = 8.38 at Nb_N = 2.2. The gap is 4.8 %, a
  fiftieth of the frame height, thinner than the lines are drawn. Lines
  drawn by eye with their coordinates read back off them do not close
  exactly, and nothing is adjusted to make a junction that the author
  never claimed was one.
- **Figure 12a's named sub-fields** (CAB, BABB, IAT & boninite, MTB &
  SSZ D-MORB, and so on) are not drawn. They carry no coordinates, they
  overlap heavily, and the paper measures that overlap itself — 261 of
  1097 samples, 25 %, fall in the wrong sub-type. The two arrays, which
  the text puts at better than 99 % each, are what the diagram draws.

**Figure 8**, (Dy/Yb)_N vs (Ce/Yb)_N, and **Figure 9**, Yb_N vs Dy_N,
are both **chondrite**-normalised — both captions say so — both linear,
and both carry one separation line with its ends printed:

| Figure | Frame | Line | Fields |
| --- | --- | --- | --- |
| 8 | x 0–2.5, y 0.5–2 | `(0.4, 1.5) → (2, 0.9)` | G-MORB above (96 %), N-MORB below (99 %) |
| 9 | x 0–25, y 0–25 | `(7, 25) → (9.5, 0)` | boninite left (100 %), IAT right (99 %) |

All three were wrong before, in the same three ways. They were drawn
against **N-MORB**, which on Figures 8 and 9 is a factor of 17.9 on Dy
and Yb, so every sample fell off the bottom-left corner of a frame it
should have filled. Both had their **axes swapped**. Both were
**logarithmic** where the source is linear. The boundaries themselves
were invented: Figure 5a's four segments had been two rays at
Th_N/Nb_N = 1 and 0.1, and Figures 8 and 9 carried shaded rectangles and
a hand-drawn boninite blob.

The statistics table reached the same quantities by its own route and
had the same fault: four of its six Saccani rows normalised to N-MORB.
`Dy_N` and `Yb_N` were 17.9 times low and `(Ce/Yb)_N` 46 % high.
`(Dy/Yb)_N` was the one row that survived, within 0.15 %, because N-MORB
and chondrite happen to have nearly the same Dy/Yb — which is why the
fault was easy to miss in the row where it did not show. All six rows
now say which normaliser they used.

One caveat is the source's own. Saccani gives **two** rules for
boninite against IAT: the line of Figure 9, and "99.5% of boninites have
DyN < 8.5 and 99% of IATs have DyN > 8.5". The vertical at 8.5 cuts the
sloping line, at Yb_N = 10, so away from that one crossing the two rules
call a band of samples differently — a full unit of Dy_N at the foot of
the frame, one and a half at the top. Neither is adjusted to meet the
other; the diagram draws the line, because that is what Figure 9 is, and
both rules are quoted in the citation so a user landing in the band can
see there are two answers.

`tests/test_saccani_2015.py` pins every published coordinate, the
normaliser of each figure, the axis order, the linear scales, and the
band where Saccani's two rules disagree.

## Defant & Drummond (1990) — one diagram measured, one not in the paper

`Defant_Drummond 1990.pdf` — *Nature* **347**, 662–665. Keys
`defant_drummond_YSrY`, `defant_drummond_YbLaYb`. The file is a scan
with no text layer, so everything here was read off rendered pages.

The paper has exactly three figures: Y or Yb against the age of the
subducting lithosphere, Sr/Y against Y, and a chondrite spider. Two
things follow, and both diagrams were wrong because of them.

**Figure 2 draws no adakite field.** Its adakites are plotted as
crosses and nothing encloses them. What it draws is a boninite field,
an island-arc andesite-dacite-rhyolite field, a MORB bar, four model
melting curves and an AFC trend arrow. The dashed "adakite boundary"
this diagram carried, and the `Sr/Y > 40` its citation asserted, are in
neither the figure nor the text. The frame was wrong too — `(0, 50)` by
`(0, 200)` against a published `(0, 25)` by `(0, 500)`, so a sample sat
at less than half its real Y and more than twice its real Sr/Y relative
to anything drawn around it.

What the paper does give for adakites is a list of numbers, on page
663: "low Y and HREE relative to island-arc ADRs (for example, Y and
Yb ≤ 18 and 1.9 p.p.m., respectively), high Sr relative to island-arc
ADR (rarely <400 p.p.m.)". Those two thresholds are exact and quotable
and are what both diagrams now draw.

Measured off Figure 2, after calibrating the axes on their own tick
labels (residuals 1.5 px in Y and 1.7 px in Sr/Y, against 83 px per
unit of Y and 3.1 px per unit of Sr/Y):

| Field | Extent | How |
| --- | --- | --- |
| MORB | Y 20 → 25 (frame edge), Sr/Y 0 → 15 | exact: it is filled, so the edges are the longest unbroken runs of ink — Y 19.97–25.01, Sr/Y −1.8 to 15.2, the overshoots being the axis line's thickness |
| Island-arc ADR | left edge Y 17.9, dome Sr/Y 59.6 at Y 20.0, falling to Sr/Y 21 at Y 25 | dashes located as connected components and their centroids converted; good to about 0.3 in Y and 3 in Sr/Y |

**The check worth recording**: the island-arc field's left edge
measured **Y = 17.9**, and the paper's stated adakite limit, written in
the text and nowhere drawn on the figure, is **Y ≤ 18**. Those come
from independent places — a dashed outline on a half-tone scan and a
sentence on page 663 — and agree to 0.1, a third of the measurement's
own uncertainty. Nothing in reading the dashes used the number 18.

**The boninite field is deliberately not drawn.** Its outline does not
resolve unambiguously in the scan: the long dashed line at Sr/Y ≈ 49
running right from about Y = 2 may be its top edge or may be a separate
boundary, and the two readings give fields of quite different extent.
Guessing would be inventing a boundary, which is the fault the diagram
already had.

**There is no Yb against La/Yb figure in this paper at all.** Rollinson
& Pease (2021) list one in their table of discrimination diagrams,
under this reference and marked *unevaluated*, and that is where the
attribution came from. It cannot be reproduced from a source that does
not contain it. `defant_drummond_YbLaYb` therefore draws only the
Yb ≤ 1.9 ppm threshold the paper does state, says so in its citation,
and **has given up its frame**: its limits were `(0, 6)` by `(0, 80)`,
which clipped samples and came from nowhere, and the axes now follow
the data. To complete it, the real source is needed — most likely
Drummond & Defant (1990, *J. Geophys. Res.* **95**, 21503–21521),
Defant & Drummond (1993, *Geology*) or Martin (1986, *Geology* **14**,
753–756); none is on disk.

`tests/test_defant_drummond_1990.py` pins both thresholds, Figure 2's
frame, the two measured fields, the agreement between the measured
field edge and the stated threshold, and that the adakite side of the
frame is left empty of drawn boundaries.

## Pearce & Gale (1977) — the coordinates were already in the file

`Pearce_Gale_1977.pdf` — *Geol. Soc. London Spec. Publ.* **7**, 14–24,
Figure 3. Key `pearce_gale_1977`.

The boundary coordinates were never in doubt. Rollinson & Pease (2021)
print them in the caption of their Figure 5.2a — "Boundary coordinates:
**(513, 0) and (313, 7.5)**" — as (Ti/Y, Zr/Y), and a comment in this
file already quoted them. They were then drawn as if they were
(Zr/Y, Ti/Y) pairs, which put a line from (1, 513) to (30, 313) on the
plot: a thing unrelated to either reading. Everything around them was
wrong too, in the same four ways Saccani's Figures 8 and 9 were:

| | Published | Was |
| --- | --- | --- |
| x axis | Ti/Y | Zr/Y |
| y axis | Zr/Y | Ti/Y |
| scales | linear, both | logarithmic, both |
| frame | Ti/Y 0–1118 by Zr/Y 0–7.9 (Fig. 3) | (1, 30) by (100, 1000) |
| within-plate field | to the **right**, at high Ti/Y | above |

**The check**: Pearce & Gale's own Figure 3 was measured, with its axes
calibrated on their tick labels. The drawn line fits a straight line to
an rms of **0.3 in Ti/Y over 144 sampled rows** and gives
**(521.6, 0) and (303.3, 7.5)** — 1.7 % and 3.1 % from the printed
pair, against a calibration uncertainty of about 4 units in Ti/Y. The
printed pair is what is used, being published and citable where the
measurement is one person's reading of a 1977 half-tone; the
measurement is kept in the code as the record that the two agree.

**The frame is Rollinson's, not Pearce & Gale's.** Figure 3 reaches
only Zr/Y ≈ 7.9, which clips an ordinary ocean-island basalt — Sun &
McDonough's OIB sits at Zr/Y 9.7. Figure 5.2a redraws the same diagram
on 0–1200 by 0–18, and that is also the frame the printed coordinates
come with. A fixed frame clips, so the one that does not clip the rock
the diagram exists to identify is the one to draw on.

**The boundary is not extrapolated.** Figure 5.2a stops it at
Zr/Y = 7.5 and Figure 3's own frame ends just above it, so neither
source says where it goes higher and neither does the code.

Figure 5.2a also labels the two fields with Verma's (2010) rates over
~4000 analyses: **plate margin >90 %, within-plate >89 %** — better
than the "<11 % misclassified" the old citation carried, and both hold
only with E-MORB excluded. That exclusion is not cosmetic: Sun &
McDonough's E-MORB lands at Ti/Y 273 against their N-MORB at 271, so
the diagram cannot separate them at all. The citation says so.

`tests/test_pearce_gale_1977.py` pins the printed coordinates, the
agreement with the measurement, the axis assignment by arithmetic
rather than by label, the linear scales, the frame, which side is
which, and the E-MORB overlap.

## Cabanis & Lecolle (1989) — the apexes were wrong

`Cabanis_Lecolle_1989.jpg` plus Rollinson & Pease (2021) Figure 5.4d.
Key `cabanis_lecolle_1989`. *C. R. Acad. Sci.* **309** (II), 2023–2029.

**The apexes were wrong**, and that is the error that mattered: La/10
sat at the top where both sources put **Y/15**, so every sample was
placed by the wrong pair of coordinates. `ternary_to_xy` takes
(apex, left, right) and `_abc` returned La first. The published order
is Y/15 at the apex, La/10 bottom left, Nb/8 bottom right. Under it
were seven quadrilaterals typed in ternary percent, approximating by
eye a figure whose real structure is wedges from the apex.

The two boundaries were measured twice, from two independent figures by
two different pipelines, as La/10 and Nb/8 percent where each meets the
base:

| Source | left (IAB\|CRB) | right (CRB\|OIB+MORB) |
| --- | --- | --- |
| Rollinson & Pease Fig. 5.4d (vector art) | 61.9 / 38.1 | 37.9 / 62.1 |
| the 1989 diagram as reproduced (JPEG) | 62.0 / 38.0 | 38.1 / 61.9 |

They agree to **0.2 %**, and the pair is symmetric about the median
from the apex to 0.1 % before any rounding, so **62/38 and 38/62** are
used. Each fits a straight line to about 1 px rms over 182 sampled
rows.

**Only the left boundary reaches the apex.** The right one branches off
it part of the way down — which is the one thing the two sources
disagree about, Y/15 = 89.4 % in Figure 5.4d against 80.9 % in the
original. It changes nothing below the branch, and Figure 5.4d's value
is used with the rest of its version.

**The seven fields are not drawn.** Cabanis & Lecolle subdivide the
three further — calc-alkaline and VAT on the left, continental in the
middle, N-MORB, E-MORB, alkaline and intercontinental rifts on the
right — with short cross-lines. Verma (2010) measured how well those
hold and the answer is: not well, outside the arc field. Rollinson &
Pease, redrawing the diagram with that reassessment in hand, show only
three. The cross-lines are also entangled with the labels in the JPEG
and do not separate cleanly, but the reason they are left out is the
first one, not the second.

**The collapse checks out against the original's own labels.** Placing
each of Cabanis & Lecolle's seven field names in ternary coordinates
and reading La/(La+Nb): calc-alkali 77.6 % and VAT 76.7 % fall in the
arc wedge, continental 49.9 % in the middle one, and E-MORB 23.7 %,
alkaline 20.2 % and intercontinental rifts 20.0 % in the right one —
exactly how Figure 5.4d groups them. Six of seven; the N-MORB label
sits outside the triangle on a leader and cannot be placed.

**A warning worth passing on.** Verma puts OIB + MORB at 29–62 %
correctly classified, and Sun & McDonough's own reference compositions
show what that means: their **N-MORB falls in the continental-rift
wedge** outright, at La/(La+Nb) = 46.2 % against a boundary at 38 %,
and their **OIB sits on the boundary** to a tenth of a percent. Only
E-MORB lands where it should. Those are pinned as tests so that nobody
later reads them as a transcription error and moves the boundaries to
suit them.

`tests/test_cabanis_lecolle_1989.py` pins the apex order by arithmetic
rather than by label, the measured boundaries, their symmetry, the
branch, the collapse against the original's labels, and the three
misplaced reference basalts.

## Yang *et al.* (2019) — the FCMS plane, and the diagram it does not get

`Using_Major_Element_Logratios_to_Recognize_Composi.pdf` — *JGR Solid
Earth* **124**, 3429–3480, Figure 1a. Key `yang_2019_fcms`.

FCMS was computed and reported in the statistics table and had no
diagram, so there was nothing to read the number against. That gap was
found by the two-routes sweep, by FCMS having no axis to pair with.

**It still gets no discrimination diagram, because the paper publishes
none.** Boundary coordinates appear in exactly one place in the whole
paper — the caption of Figure 7 — and those are for FCKANTMS against
ln(SiO₂/(CaO+Na₂O+TiO₂)), which is the diagram already implemented.
The conclusions say why FCMS has none: incorporating ln(K₂O/Al₂O₃),
ln(TiO₂/Na₂O) and ln(Na₂O/K₂O) gives "a more powerful parameter called
FCKANTMS", because it removes the temperature and pressure effects that
make lherzolite melts scatter in the FCMS plane. The paper's own text
notes that "the lherzolite melts mostly are not lie on the cubic
polynomial curve" for that reason.

**What is published is the plane and the trend through it**, and that
is what this draws. Figure 1a plots ln(FeO/CaO) against ln(MgO/SiO₂)
on −3.5 to 1 by −1.4 to 1.4, with the cubic printed beside the curve:

> y = 0.058x³ + 0.636x² + 1.850x + 1.170,  R² = 0.944

which is equation (2) of Table 1, repeated again in the conclusions —
three printings, so there is no room for doubt — and already the stored
`YANG_LHERZOLITE_TREND`.

The reason the plane is worth drawing is that **FCMS is the vertical
distance from that curve**. A sample's FCMS can be read straight off
the plot, a lherzolite melt sits on the line, and the sign says which
side. That identity is asserted against the statistics row, which
reaches the same number by the other route — the row evaluates
equation (2), the diagram plots the two log-ratios — so their agreeing
is a real cross-check and not a restatement.

The catalogue entry used to read "FCMS / FCKANTMS source proxy" and
point at the FCKANTMS diagram alone; the two are now listed
separately.

`tests/test_yang_2019_fcms.py` pins the cubic, the frame, the shape of
the trend, the axis order, the all-iron-as-FeO convention, the
distance identity, and that exactly one line is drawn on the plane.

## Middlemost (1994) — naming a plutonic rock from the TAS

`Middlemost_1994.pdf` — *Earth-Science Reviews* **37**, 215–224,
Figure 4. Key `tas_plutonic`.

`TASVolcanic` has had `classify()` for a while; the plutonic one did
not, and the reason recorded here was that its outlines do not tile.
They do not, as stored: **two of the sixteen are kept as the single
boundary segment each contributes to the drawing**, because the rest of
their edges belong to their neighbours and drawing them twice would
show. Closing those two is the whole of the fix. With them closed the
sixteen tile exactly — a 0.2 × 0.08 grid over the whole diagram finds
**no overlap and no interior gap**.

What says they may be closed that way is Middlemost's own text, which
sets the plutonic scheme out as the volcanic one renamed: gabbro for
basalt, diorite for andesite, granodiorite for dacite, syenite for
trachyte, granite for rhyolite, foid gabbro for tephrite, monzogabbro
for trachybasalt, and so on. The two fields in question are the
volcanic phonotephrite and tephriphonolite under plutonic names, and
take their vertices. Both closures were then checked against Figure 4
rather than taken on trust, and land on its drawn outlines.

**The classification takes no normative arguments and needs none.**
Middlemost gives foid gabbro one name where the volcanic plane splits
tephrite from basanite, and he *draws* the quartz monzonite field
rather than splitting a trachyte field at 20 % normative quartz — the
figure has a geometric boundary where the volcanic scheme has a
normative one.

**A false alarm worth recording.** Overlaying our stored polygons on
Figure 4 first showed them displaced by about 6 wt.% SiO₂, which looked
like a transcription error across the whole set. It was the
calibration: the leftmost tick is SiO₂ = **40**, not 30, the "30"
numeral having fallen outside the crop. Refitted, the overlay matches,
and the drawn verticals read 41.0, 44.9, 52.2 and 62.9 against stored
41, 45, 52 and 63. Nothing needed changing. The lesson is the project's
own: calibrate on labels you can see in the crop, and check a known
feature before believing a systematic offset.

**The two schemes are not the same diagram**, and 3.4 % of the shared
plane disagrees. All of it is Middlemost having redrawn rather than
traced, and it is pinned as tests so neither set gets "corrected" to
match the other:

- he closes **foid syenite** under a tawite/urtite/italite field that
  Le Bas has no equivalent of, where volcanic phonolite runs open to
  the top of the plane;
- he closes **granite** on the right, where volcanic rhyolite runs
  open, so the high-alkali corner above it is his syenite and quartz
  monzonite;
- his **granodiorite/granite** boundary meets the axis at SiO₂ **77.3**
  where Le Bas puts dacite/rhyolite at **77.0**. Measured off Figure 4
  the boundary extrapolates to 77.31, so the 0.3 is his.

Quartzolite and the tawite/urtite/italite group are in Figure 4 but are
not drawn here; Middlemost calls them "outside the main sequence of
plutonic rocks". A composition there is left unnamed rather than forced
into a neighbour.

`tests/test_tas_plutonic_classify.py` pins the tiling, the two
closures against their volcanic twins, a point inside each of the
sixteen fields, the names against the layout labels, and the three
places the two schemes part company.

## Harris, Pearce & Tindle (1986) — wrong apex and wrong divisor

`Harris_etal_1986.pdf` — *Geol. Soc. London Spec. Publ.* **19**, 67–81,
Figure 6. Key `harris_1986_HfRbTa`.

Two errors, and the first is the one that mattered. **The apexes were
wrong**: Hf sat at the top with Rb bottom left, where Figure 6 puts
**Rb/30 at the apex**, Hf bottom left, Ta×3 bottom right. **And the
divisor was wrong**: `Rb/10` where the figure, its caption and Figure 7
all print **Rb/30** — in the menu text of both the volcanic and
plutonic trees as well as in the code. Between them every sample was
placed by the wrong pair of coordinates and with one of them three
times too large. The four fields under it were quadrilaterals typed in
ternary percent.

The measurement went cleanly, for a reason worth reusing: **the dotted
boundaries and the data symbols do not overlap in size.** The figure
has 241 connected components of 32–64 px, which are the dots of the
boundaries, and 133 of 256–4096 px, which are the open and closed
triangles and squares. Separating on that and running RANSAC over the
dots recovers five segments carrying 245 of 260 dots, each straight to
0.5–4.3 px rms against a triangle 2008 px wide. The triangle itself is
equilateral to **0.04 %** — fitted edges give a height of 1739.6 px
against 1738.9 for the measured width — which is what fixes the
calibration.

Two things the measurement turned up that eyeballing would not have:

- **The near-vertical boundary curves slightly.** Fitting its 69 dots
  with a parabola rather than a line improves the residual from 4.0 to
  2.8 px and bows by 9.3 px at most, which is 0.46 % of the triangle's
  width. It is drawn straight, with the number recorded so the choice
  is visible.
- **There is no single triple point.** Two branches leave the vertical
  boundary about four units apart — the VA|WP one at Rb/30 = 26.2 %,
  the III|WP one at 22.5 % — with a short stem between them. Fitting
  the three as concurrent lines put their pairwise intersections up to
  11 units apart, which is how the stem was noticed; enlarging the
  figure shows it plainly.

| Field | Meaning, from the paper's summary |
| --- | --- |
| VA | volcanic arc, pre-collision calc-alkaline |
| Group II | syn-collision peraluminous leucogranites |
| Group III | late or post-collision calc-alkaline |
| WP | within plate |

The paper notes that Group III "can only be distinguished from
volcanic-arc intrusions by their higher ratios of Ta/Hf and Ta/Zr",
which the citation passes on.

`tests/test_harris_1986.py` pins the apex order and the divisor by
arithmetic rather than by label, the five segments, their shared
vertices, the two separate branches, and the catalogue text.

## Vermeesch (2006a) — the two QDA ternaries, read from the vector figure

`VermeeschGCubed2006.pdf`, Figures 34 and 35 (with 45 and 46). Keys
`vermeesch_NaNbSr` and `vermeesch_SmTiV`. Checked 2026-10-21.

These were listed as blocked: a QDA gives each class its own
covariance, so the boundaries are conics in log-ratio space, and the
paper prints neither the covariances nor Table 6 anchor points for
them, as it does for the three LDA ternaries. They cannot be computed.
They can be **read**, though: Figures 34 and 35 are vector drawings,
and their decision boundaries are Bezier paths in the PDF — 12
segments for Na–Nb–Sr, 8 for Ti–V–Sm. Each control point was taken from
the path and turned into ternary fractions through the figure's own
triangle. A Bezier curve keeps its shape through that affine map, so
nothing is approximated beyond what the paper drew.

What was there before was wrong twice over: four quadrilaterals per
diagram typed in ternary percent, and the triangle the wrong way up —
Na/100 and 50 Sm at the top where the paper has **25 Nb and Ti/50**.
The real fields look nothing like quadrilaterals: on Na–Nb–Sr MORB is a
long closed loop from near the 25 Nb apex to the base and OIB a lobe
against its right side, with IAB on either side; on Ti–V–Sm OIB is a
dome against the 50 Sm – Ti/50 edge and MORB a small lens under its
right end, with IAB below.

Three checks, each against something the extraction did not use:

* **The log-ratio figures.** Figures 45a and 46a draw the same
  boundaries in log-ratio space, axes ln(left/top) and ln(right/top),
  calibrated on their own tick marks. Mapped back to the triangle with
  the **natural** logarithm they lie on the Figure 34/35 curves to a
  median 0.34 % and 0.23 % of the triangle's side (90th percentile
  under 1 %); with base ten they miss by 5–24 %. So "log" is ln here,
  as for the LDA ternaries, and the two drawings agree.
* **The paper's test samples.** Figures 45b and 46b plot the 61 and 85
  test samples with their true class, and the paper's table of test
  results says how its QDA classed each. Classified by the extracted
  fields, **Na–Nb–Sr gives the table exactly** — 21 IAB right; 7 of 12
  MORB right, 5 taken for IAB; 28 OIB right. **Ti–V–Sm gives 82 of
  85**; the other three, one in each row, lie on the drawn line, 0.05 %,
  0.19 % and 0.31 % of the side from it, about the stroke's width. The
  misclassified samples the paper counts — MORB taken for OIB, 1–9 %
  inside the OIB field — come out misclassified here too. The
  boundaries in Figures 45b/46b are the same drawing as 34/35, to the
  hundredth of a percent.
* **The orientation**, apex by apex, against the figures.

`tests/test_vermeesch_qda_ternaries.py` pins all three, with the test
samples' positions and the log-ratio curves read from the PDF in
`tests/data/vermeesch2006_qda_figures.json`; it also checks that every
part of the boundary the log-ratio figures can see lies on their curve,
and that each segment starts where the last ended. Swapping two digits
of any one control-point coordinate — 216 such typos — fails it every
time.

## Still drawn by eye (1) — blocked, none pending

Nothing is left that a measurement could fix. The one below is blocked
on a source, not on effort.

| Diagram | Source on disk | Why |
| --- | --- | --- |
| `defant_drummond_YbLaYb` | **not on disk** | the paper it cites does not contain that figure; see above |

The figure is in Drummond & Defant (1990, *J. Geophys. Res.* 95(B13),
21503–21521). Martin (1986, *Geology* 14, 753–756) is now on disk and
drawn as a diagram of its own, `martin_1986_LaYbN`, in (La/Yb)N–YbN with
his Archean TTG and post-Archean fields; Defant & Drummond's adakite
fields still need their 1990 paper.

## Maniar & Piccoli (1989) — the rules were right, one label was not

No source file: *GSA Bulletin* **101**, 635–643, is not on disk, and
nothing below needed it. Key `maniar_piccolli` — the old misspelling,
kept because saved sessions store the key; every string a user reads
says Piccoli.

This was listed as a rule with nothing to verify, and the rules do need
nothing: A/CNK = 1 and A/NK = 1 are Shand's (1943) definitions, so they
*are* the boundaries. What is built around a rule still has to be
checked — the arithmetic that places a sample, and anything else on the
plot — and one of those was wrong.

**The arithmetic is right.** Both ratios are molar, with Al₂O₃ 101.96,
CaO 56.08, Na₂O 61.98 and K₂O 94.20; the IUPAC atomic weights give
101.960, 56.077, 61.979 and 94.196, so all four are right to the two
decimals they carry. The check worth having is a composition the
boundaries are defined by. A/CNK = 1 is where Al is just enough to make
feldspar of the Ca, Na and K present, so every feldspar has to land on
it. With the wt.% built from atomic weights rather than from the
module's own masses, albite, orthoclase and Or₄₀Ab₆₀ come out at
(1, 1) to 3 × 10⁻⁵, and Ab–Or–An mixtures at A/CNK = 1 with
A/NK = 1 + An/(Ab + Or), counted as oxide-basis formula units. In wt.%,
albite would sit at A/NK = 1.64.

**The two boundaries are right**, a vertical at A/CNK = 1 the full
height of the frame and a horizontal at A/NK = 1 the full width.

**The third line was filed as a field.** A diagonal from (0.5, 0.5) to
(2, 2) is drawn as well. It is not a boundary but arithmetic:

> A/NK ÷ A/CNK = (CaO + Na₂O + K₂O) / (Na₂O + K₂O)

is never below 1 while CaO ≥ 0 and is exactly 1 at CaO = 0. The
diagonal is the CaO-free limit and nothing plots under it — least of
all in the lower-right quadrant, which would have to be peraluminous and
peralkaline at once. It was stored under the name *Peralkaline*, so the
label that name carries sat at (1.25, 0.75): right of A/CNK = 1 and
under the diagonal, where no rock can go, while the module's docstring
said that quadrant was left unlabelled. The peralkaline rocks themselves
fall in the small triangle above the diagonal, left of A/CNK = 1 and
under A/NK = 1, and that had no label. A comendite-like rhyolite —
9.5 Al₂O₃, 0.3 CaO, 5.0 Na₂O, 4.5 K₂O — plots at (0.70, 0.73), inside
it and close to the diagonal, as low-Ca peralkaline rocks do.

Nothing drawn has moved: the same three lines at the same coordinates,
compared before and after on the rendered plot. The diagonal is now
drawn as what it is, the label sits in the triangle at (0.66, 0.88),
where it fits at both canvas sizes tried, and the note under the plot
says what the diagonal means.

**What needs the paper.** Whether Maniar & Piccoli draw the diagonal at
all, and on what frame, cannot be settled from the definitions. The
frame, 0.5–2.0 by 0.4–4.0, is not taken from their figure, and neither
is running both boundaries across the whole frame rather than stopping
them at the diagonal. None of it changes where a sample plots or which
field it falls in.

**Found along the way:** `frost` computed the same index differently,
and a Ca-bearing rock could be metaluminous here and peraluminous there.
Now fixed; see *Frost et al. (2001)* below.

`tests/test_maniar_piccoli_1989.py` pins the molar masses against the
atomic weights, the feldspars on the boundaries, the fields against the
mineralogy — Al left over is peraluminous, Ca left over metaluminous,
Na left over peralkaline — the diagonal as the CaO = 0 limit, exactly
three lines drawn, each label inside the field it names and above the
diagonal, and the spelling. Each was checked by putting a fault back:
the old label position, a wt.% computation, K₂O at 94.11, the boundary
at 1.1, and Ca counted twice, the last caught only by the plagioclase
mixtures.

## Frost *et al.* (2001) — the ASI was not Shand's index

Rollinson & Pease (2021) Figure 3.9 and Table 3.4, after Frost *et al.*
(2001) and Frost & Frost (2008). Both originals are on disk since
2026-10-12 (`Frost_etal_2001.pdf`, `Frost_2008.pdf`); see the end of
this section for what they changed. Key `frost`, panel (c).

The index is printed as molecular **Al/(Ca − 1.67P + Na + K)**, and
Rollinson & Pease say on p. 127 what its line at 1 means: peraluminous
rocks "have more Al than is needed to make feldspars", metaluminous
rocks lack it. That fixes the arithmetic without the originals. A
feldspar has exactly the Al it needs, so every feldspar — anorthite as
much as albite — has to come out at ASI = 1, which makes the index
Shand's A/CNK with apatite's Ca taken out.

**It was computed on a mixed basis.** Al, Na and K were doubled from
oxide moles to cations and Ca was not, so the index was
2A/(C + 2N + 2K) where Shand's is A/(C + N + K). The two agree only
without Ca:

| | A/CNK | ASI before | ASI now |
| --- | --- | --- | --- |
| albite | 1.000 | 1.000 | 1.000 |
| anorthite | 1.000 | 2.000 | 1.000 |
| An₅₀ plagioclase | 1.000 | 1.333 | 1.000 |
| granite, 14.5 Al₂O₃ / 2.5 CaO / 3.5 Na₂O / 3.5 K₂O | 1.029 | 1.227 | 1.029 |

Panel (c) calls everything above 1 peraluminous, so a Ca-bearing rock
near the line was peraluminous on this panel and metaluminous on
`maniar_piccolli` — the same index, reaching the user twice with two
answers. All four oxides are now molecular proportions; P stays counted
per atom, two per P₂O₅, so that 1.67, Frost's printed rounding of the
5/3 Ca per P in apatite, still applies to it. Read that way the printed
formula is exactly A/CNK less apatite, and with no P₂O₅ the two
diagrams now agree to rounding. P₂O₅ was also 141.95 g/mol where the
atomic weights give 141.94.

**AI is left on the cation basis**, Al − (Na + K) per atom. Only its
sign is read — AI < 0 is Al-deficient, peralkaline — and the sign is the
same on either basis; Figure 3.9d is a quadrant sketch with no scale on
its axes, so it cannot say which basis the magnitude should be on.

**Panel (d)'s labels were wrong by the definitions.** It carried two:
"metaluminous, silica-saturated" at FSSI = −2, which is
silica-*under*saturated, and "peralkaline, silica-saturated" at
AI = +0.4, which is not peralkaline — AI > 0 is Al adequate to
excessive. The lower half had none. Figure 3.9d names all four
quadrants, and those four names are what the panel now carries, one at
the centre of each quadrant. Nothing else in the panel moved.

Two misprints in Rollinson & Pease, noted so nobody copies them: the
Figure 3.9 caption gives the ASI formula for AI, and Table 3.4 prints
FSSI as Q − [Lc − 2(Ne + Kp)]/100 where the caption and the text both
have + inside the bracket. The code follows the text. Whether the /100
divides Q too changes nothing read off the panel: a CIPW norm never
carries quartz and a feldspathoid together, so one term is always zero
and the sign of FSSI is the same either way.

**The frames** were left open until the originals came (2026-10-12),
and are settled now — see *Against the originals* below.

`tests/test_frost_2001.py` pins the molar masses against the atomic
weights, ASI = 1 for albite, orthoclase, anorthite, An₅₀ and a ternary
feldspar, the agreement with `maniar_piccolli` over 200 random
compositions, the apatite correction — adding apatite to a feldspar
leaves it on 1 — and the granite above. Putting the cation basis back
fails seven of them; P₂O₅ at 141.95 and a halved apatite correction
fail one each. It also pins the signs of AI and FSSI and that each of
panel (d)'s four labels names the quadrant it sits in, which the old
labels fail.

**Panel (d) drew its data transposed** (found 2026-10-10). The axes
read FSSI across and AI up, as Figure 3.9d has them, and the labels sat
in the right quadrants — but the samples went in as (AI, FSSI). Every
check above passed, because each looked at the numbers or at the
labels, never at where a sample landed. A rock whose two signs agree
stayed in its quadrant, only misplaced; one whose signs differ crossed
to the opposite one: a nepheline syenite, FSSI −0.44 and AI +0.03,
plotted as silica-saturated and Al-deficient, and a peralkaline granite,
FSSI +0.36 and AI −0.07, as undersaturated with Al to spare. `PANELS`
in `frost.py` now says what each panel puts on which axis, the plot and
the sample tally both read it, and `tests/test_frost_panels.py` checks
the drawn positions and that each of those rocks lands in its own
quadrant.

### Against the originals (2026-10-12)

With Frost *et al.* (2001) and Frost & Frost (2008) on disk, both
vector PDFs, so the figures could be read as coordinates:

* **Panel (d)'s frame is Frost & Frost (2008) Figure 11.** Figure 8,
  the classification diagram, marks only the signs. Figure 11 plots
  real suites on FSSI −1.2 to 0.6 and AI −0.10 to 0.16 (read: −1.21 to
  0.59 and −0.100 to 0.162). The panel ran ±2.5 by ±1. One AI tick of
  Figure 11 is printed 0.04 where 0.06 belongs; the ticks are evenly
  spaced 0.04 apart.
* **AI was twice Frost's.** Figure 11c draws plagioclase An10 to An40
  at AI 0.035, 0.073, 0.110 and 0.146. The oxide-molecule basis, Al₂O₃
  − (Na₂O + K₂O) in moles per 100 g, gives 0.038, 0.075, 0.112 and
  0.149; the cation basis the code used gives twice that. Harmless
  while only the sign was read, not with the published frame.
* **The MALI boundaries have published equations.** The caption of
  2001 Figure 2 prints all three as quadratics in SiO₂, and each passes
  through MALI = 0 at Peacock's 51, 56 and 61 % (−0.03, 0.02, 0.01), as
  Frost & Frost (2008) say they were built to. The curves traced off
  Rollinson & Pease came within 0.25 MALI of them. They are computed
  now, over SiO₂ 51–75 as 2008 Figure 6a draws them (51.0 to 74.9 on
  the vector figure).
* **The Fe-index line starts at SiO₂ 48**, where Frost & Frost (2008)
  say the boundary applies from; it was drawn from 45. The boundary
  itself, 0.46 + 0.005 SiO₂ with FeO* = FeO + 0.9 Fe₂O₃, is theirs; it
  revises the 0.486 + 0.0046 SiO₂ of 2001.
* **Panel (c) keeps ASI 0.5–1.6.** The scheme defines only ASI = 1;
  Frost's one plot of ASI against silica (2008 Figure 6c, 0.7–1.1) is
  of a single intrusion, not a classification frame. 0.5–1.6 keeps
  peraluminous leucogranites and peralkaline rocks inside, and anything
  beyond is flagged at the edge.
* **FSSI is as printed**: normative (Q − [Lc + 2(Ne + Kp)])/100, which
  runs from +1 for pure quartz to −2 for pure nepheline, the ends of
  2008 Figure 7.

`tests/test_frost_panels.py` pins the frame, the plagioclase AI values,
the MALI coefficients and their Peacock crossings, and the start of the
Fe-index line; putting any of the old values back fails it.

## Li et al. (2025) — Nb/Yb vs Th/Nb

`Lietal2025.pdf` — Li, Godang & Saputro (2025) *Lithosphere* 2025(2),
lithosphere_2025_125 (CC BY 4.0), Figure 1. Key `li2025_nbyb_thnb`.

The paper states most boundaries as ratios, used as stated: Th/Nb 0.04,
0.11 and 0.67; Nb/Yb 6 and 4; Th/Yb 0.35 and 0.65 (straight lines of
slope −1 on the log axes); La/Yb 20 inside the rift field; TiO₂ =
−1.1610 + 0.1935 Al₂O₃ between alkaline arc and continental extension.
Th/Nb runs across and Nb/Yb up, although the title names Nb/Yb first.

What the text leaves out was measured on Figure 1, a 2203 × 2317
raster, calibrated on the labelled lines Th/Nb 0.04, 0.11, 0.67 and the
frame at Nb/Yb 0.1 and 100 (717.7 and 718.7 px per decade; Nb/Yb 6 and
4 then land within 2 px of where they are drawn):

* the N-MORB | E-MORB horizontal at Nb/Yb 1.489 — the McDonough & Sun
  (1995) primitive mantle, 0.658/0.441 = 1.492, whose point the figure
  puts on it; it ends on Th/Yb = 0.35;
* the right side of the new sub-alkaline enriched tholeiitic field at
  Th/Nb 0.24, down to Nb/Yb 2.69 where Th/Yb = 0.65 takes over
  (0.65/0.24 = 2.71);
* the eleven 0–100 % points of Wei et al.'s interaction line, and the
  AFC and subduction vectors, as drawn.

Between Nb/Yb 1.49 and 2.71 nothing separates the enriched tholeiitic
field from the transitional band on the figure; the classification uses
Th/Nb 0.24 there. The reference stars land on Sun & McDonough's (1989)
N-MORB, E-MORB and OIB. The paper means the diagram for mafic to felsic
rocks (Section 2.1), a supporting tool only for continental collision
(2.3); it is offered under all three compositions.

`tests/test_li2025.py` pins the stated values, ties each measured one to
the primitive mantle or the Th/Yb line it meets, and classifies the
paper's own case studies by the ratios Section 3 prints.

## Martin (1986) — Archean TTG against post-Archean granitoids

`Martin_1986.pdf` — *Geology* **14**, 753–756, a scan with an OCR text
layer. Key `martin_1986_LaYbN`. Figure 1 plots (La/Yb)N against YbN,
linear, Yb_N 0–25 and (La/Yb)N 0–177, with two fields: Archean TTG,
"(La/Yb)N from 5 to more than 150 ... 0.3 < YbN < 8.5", and post-2.5 Ga
granitic rocks, "(La/Yb)N ≤ 20 ... 4.5 < YbN < 20".

Both fields were measured on Figure 1 (a 2566 × 3282 scan): the axes on
their ticks — YbN 0, 10, 20 (45.98 px per unit), (La/Yb)N 0, 50, 100,
150 (4.57 px per unit) — and each edge fitted to the ink along it, the
vertices being where neighbouring edges cross. The caption bounds what
was measured: TTG YbN 0.31–8.47 and (La/Yb)N up to 150; post-Archean
YbN 4.47–20.0.

Figure 4 draws the fields again, one per panel, and was measured the
same way as a check. Its post-Archean field (inset A, whose (La/Yb)N
ticks are unevenly spaced, so it was calibrated tick to tick) agrees
with Figure 1 within 0.5. Its TTG field (4B) is drawn a little
narrower — top at 148, steep edge up to 0.33 in YbN to the left — and
Figure 1, the one that sets the two groups against each other, is the
one used. `tests/test_martin_1986.py` pins both comparisons.

**Martin does not name his chondrite.** Boynton (1984) is used and the
citation says so; another chondrite moves YbN by up to a third, which
for a field defined in YbN is not a detail. The two fields overlap at
YbN 4.5–8.5, and a sample there is named as either.

## Godang et al. (2024) — Nb/Zr vs Th/Nb

Godang, Saputro & Li (2024) *Solid Earth Sciences* 9(3) 100199, after
Saputro et al. (2022) and Sun, Zhang & Huang (2006), as reproduced in
`Lietal2025.pdf`, Figure 5 (Figure 6 is the same diagram with other
data). Key `godang2024_nbzr_thnb`. The geometry comes from the 2025
reproduction. The 2024 paper's own Figure 7 (`Godang_etal_2024.pdf`, a
1895 × 1384 raster), measured afterwards on its own — 650.3 px per
decade on its lines Th/Nb 0.04, 0.11 and 0.67, the frame then landing
on 0.0150 and 5.01 — agrees: its Nb/Zr lines sit at 0.0625 and 0.0397,
each line spans what the template draws and no more, the PM dot is at
(0.121, 0.064), and the diagonal's slope is −0.4940 against −0.4936 on
the reproduction, reaching Nb/Zr 0.0100 at Th/Nb 5. The original also
draws Wei et al.'s (2014) mixing lines A and B and the source boxes
(PM, WAM, spinel- and garnet-DMM), which are interpretation, not field
boundaries, and are not drawn.

The figure prints its ratios and they are used as printed: Th/Nb 0.04,
0.11 and 0.67; Nb/Zr 0.04, 0.0627 (PM) and 0.15; La/Yb 20 inside the
rift field. Th/Nb runs across on a log axis from 0.015 to 5, Nb/Zr up
from 0.01 to 1.

Measured on Figure 5, a 2205 × 1665 raster, calibrated on the labelled
lines Th/Nb 0.04, 0.11 and 0.67 (773.4 px per decade) and the frame at
Nb/Zr 0.01 and 1 (774 px per decade; the right edge lands on 4.985):

* where each line stops — Nb/Zr 0.15 only across the array (Th/Nb
  0.04–0.11), 0.0627 and 0.04 from Th/Nb 0.04 to the right edge, Th/Nb
  0.67 from 0.0627 to the top;
* the PM dot, at (0.1206, 0.0630): McDonough & Sun's (1995) primitive
  mantle, Th/Nb 0.0795/0.658 = 0.1208 and Nb/Zr 0.658/10.5 = 0.06267,
  the 0.0627 the figure prints;
* the diagonal between continental arc and island arc, straight on the
  log axes from the PM dot to the lower right corner (5, 0.01): fitted
  along its length the slope is −0.4936 against the −0.4930 those two
  points give, residuals under a pixel, and it crosses Nb/Zr 0.04 at
  Th/Nb 0.301 where the line through the two points does.

The right-hand brackets name the source for every setting: enriched
above 0.0627, slightly enriched (the transition) down to 0.04, depleted
below; arc samples carry it in their classification. The 0.04–0.0627
band of the array has no name on the figure and is classified as the
transition. Li et al. (2025, Section 4) use the diagram on basaltic and
rhyolitic rocks alike, so like theirs it is offered for every
composition, volcanic and plutonic.

`tests/test_godang2024.py` pins the printed ratios, ties the PM dot and
the diagonal to the primitive mantle and the corner, and classifies the
case studies Li et al. plot on it.

## The Petrography view — the IUGS modal diagrams (6)

Checked 2026-10-12. Every boundary is a definition, a percentage the
IUGS fixed, so nothing needed measuring except the one scheme that is
not IUGS's. The definitions were read off the BGS Rock Classification
Scheme, Volume 1 (Gillespie & Styles 1999, Research Report RR 99-06,
NERC Open Research Archive), which reproduces the IUGS figures: 11-12
for the plutonic QAPF (after Streckeisen 1976), 19 for the volcanic
one (after Streckeisen 1978), 13 for the gabbroic rocks, 16 for the
ultramafic ones (after Streckeisen 1973) and 7 for Schmid's (1981)
tuffs. None of these sources is on disk otherwise; Verma's book
discusses the QAPF without drawing it.

**QAPF placed every sample in the wrong spot.** Its position was
0.5 A + P + 0.5 Q with A at x = 0, which moves every sample right by
half its alkali feldspar: an alkali-feldspar syenite plotted on
monzonite, a granite of Q30 A40 P30 on granodiorite. Only rocks without
alkali feldspar — tonalites, gabbros — sat right. The lines were wrong
too: the P/(A+P) lines ran up through the quartzolite and quartz-rich
fields, where Figure 11 stops them at Q 60, and down through the foid
fields at 10/35/65/90, where they are 10/50/90 and foidolite is
undivided. Labels sat in the wrong fields (foid syenite where foid
monzosyenite is) and field 14 had none.

**The volcanic QAPF was the plutonic one renamed.** Figure 19 has its
own fields: no names above Q 60; dacite across P/(A+P) 65-100;
basalt / andesite from Q 20 down to F 10 with no line at 90; tephritic
phonolite and phonolitic tephrite / basanite in the foid band; and
three foidites. The old diagram drew the plutonic lines and used names
the IUGS does not, among them quartzolite, phonolitic trachyte,
tephritic latite and tephritic basalt.

Both QAPF diagrams are now tables of fields, each a box in (Q or F, P/
(A+P)), from which the lines, the IUGS field numbers, a key of the
names and the name a sample gets all come. A sample carrying both
quartz and a feldspathoid is left off with a note; a mineral left blank
counts as absent, where a blank F used to drop a granite.

**Gabbroic and ultramafic strips.** Gabbro / gabbronorite / norite is
under 5 % olivine and troctolite under 5 % pyroxene; harzburgite and
olivine orthopyroxenite are under 5 % Cpx, wehrlite and olivine
clinopyroxenite under 5 % Opx. These are strips of constant width
meeting at the middle of the 90 line — Figures 13 and 16 draw them so,
and measured on the reference figures in the project material the
inner lines keep 41-48 px from their side on every row, where rays of
constant ratio would grow from about 10 to 41. The old strips opened by
invented amounts ("~3 %", "~4 %"). The gabbroic diagram also never read
the template's plagioclase, `P_mode`, and a blank `Px_mode` hid rows
whose Opx and Cpx were filled.

**Tuffs.** Schmid (1981), the IUGS classification, is the three-field
triangle of Figure 7: glass, crystals, rock fragments, each tuff named
for its dominant component. The diagram that cited him draws a
different, finer scheme — lithic at the top, lines at 50, 25 and 10 %
— from a figure in the project material whose source is not
identified. Both are now offered: `tuff_schmid_1981` (new) and the
banded one, cited honestly. Measuring that figure showed its dividers
are lines of constant crystal content, parallel to the lithic-vitric
side (Crystal 25 % below Lithic 50, and 50 and 10 % in the base band),
each keeping 61-62, 114 and 24 px from that side; the code had rays
from the lithic apex, which put the upper divider at Crystal 12.5 % on
the Lithic 50 line.

`tests/test_petrography_iugs.py` pins the field tables against the
figures, checks that the fields tile each diagram, places the corners
and a granite, names a dozen modes, and fails on each of the old
errors put back.

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

### The two-routes sweep

A correct boundary is not enough on its own. The same quantity reaches
the user twice — once as an axis on a diagram, once as a row in the
statistics table — and the two are computed by different code. Three
faults in this project have been a correction landing on one route and
not the other: the Verma units, the Saccani normalisers, and Pearce
(2008)'s Ti/Yb. In each case the plot and the table disagreed under one
heading, with nothing on screen to say which was right.

So all 208 statistics rows were paired with the diagram axis plotting
the same thing and required to equal it exactly. The method is
mechanical: evaluate both on one synthetic dataset of log-uniform
positive values, then take the ratio row by row. A ratio that is
*constant across every row* means the two are the same quantity; if that
constant is not 1, one route has been corrected and the other has not.

Two cautions, both of which produced nonsense before being fixed:

- **Pair within a source family.** Saccani's Yb_N is chondrite-normalised
  and Pearce's axis is raw Yb, so one is reliably 0.17 times the other.
  That is two papers doing different things, not a fault.
- **Pair the Verma panels by the identity of the coefficient set, not by
  the panel name.** Keys such as `IA_CA_COL` repeat across all eight
  sets, so matching on the name compares a majors row against a traces
  diagram and reports 324 mismatches that are not there.

Done properly the sweep compares 80 Verma panel axes and 21 other pairs.
The Verma rows are clean, and structurally so: `tectonic_results.py`
imports the diagram module's own `_apply_df` and `_logratios_for_coef`,
so the two routes are one route. The two faults it found were both among
the hand-written rows, and both are described above.

The sweep is now `tests/test_statistics_match_diagrams.py`, and it was
checked by putting each fault back and confirming the failure. Worth
recording: it catches the two *quantity* faults but **not** a wrong
shared constant — change the one definition and both routes move
together, still agreeing. That is what the separate mass-ratio test is
for, and it is the reason the TiO₂ → Ti factor is checked against
47.867 / 79.865 rather than against itself.
