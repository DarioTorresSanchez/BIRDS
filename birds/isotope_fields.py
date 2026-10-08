"""Reference fields and lines for the isotope diagrams.

The mantle end-member components are ranges, not points, so the Sr–Nd
plane draws them as fields, measured from the published figure.  The
Pb planes carry only the NHRL, which is a published equation and is
therefore computed rather than traced.

Sr–Nd fields
------------
======  =======================  ==============================
DM      Depleted MORB Mantle     hexagon, on the upper line
PREMA   Prevalent Mantle         small pentagon, on the upper line
HIMU    High-µ                   hatched box, on the lower line
BSE     Bulk Silicate Earth      solid box, on the upper line
EMI     Enriched Mantle I        hatched box, cut by the axis
EMII    Enriched Mantle II       named region, no field drawn
======  =======================  ==============================

The source labels EMII without enclosing it, so it is carried here as
a label-only entry: inventing an outline for it would put a boundary
on the plot that the figure does not claim.

Provenance
----------
Measured from the published figure.  The frame and both spines were
located as the rows and columns that are continuously dark across the
panel; the axes were then calibrated on the tick marks drawn inside
the frame, which fit a straight line to within 1.0 px in ⁸⁷Sr/⁸⁶Sr and
0.9 ppm in ¹⁴³Nd/¹⁴⁴Nd.

Two independent checks confirm that calibration:

* the labelled horizontal line lands on ¹⁴³Nd/¹⁴⁴Nd = 0.5126357, which
  is CHUR (0.512638) to within 0.4 px — and the figure marks that line
  "0 εNd", so it must be CHUR;
* the unlabelled vertical line lands on ⁸⁷Sr/⁸⁶Sr = 0.705126, within
  4 px of the Zindler & Hart (1986) BSE value and 32 px from the older
  uniform reservoir, 0.7045, and it passes through the centre of the
  BSE box.  εSr is referred to the same BSE, so εSr = 0 falls on it.

Field outlines came from the fill colours: each mask was closed to
bridge the hatching, hole-filled, reduced to its largest component and
its outline simplified by Douglas–Peucker at 1.8 px.  The two array
bounds were fitted by RANSAC over the grey ink left after removing the
coloured fields, the frame and both reference lines; each drew 440+
inliers over more than half the panel width with mean residuals of
0.65 px, and their drawn extents were then read back along the fit.

The outlines are schematic in the source — hand-drawn envelopes for
compositional ranges, not contours of a dataset.  They are reproduced
at the precision they were measured, which is not the precision they
were drawn with.
"""

from __future__ import annotations

from dataclasses import dataclass, field as _field

#: ¹⁴³Nd/¹⁴⁴Nd of CHUR today, the figure's εNd = 0 line, and the
#: reference for εNd: Jacobsen & Wasserburg (1980), normalised to
#: ¹⁴⁶Nd/¹⁴⁴Nd = 0.7219 (Rollinson & Pease 2021, Table 6.3b and their
#: worked example).  Bouvier et al. (2008) revise it to 0.512630, with
#: ¹⁴⁷Sm/¹⁴⁴Nd 0.1960 -- 0.16 εNd units lower.
CHUR_ND_143_144 = 0.512638

#: ¹⁴⁷Sm/¹⁴⁴Nd of CHUR today, Jacobsen & Wasserburg (1980).
CHUR_SM_147_144 = 0.1967

#: ⁸⁷Sr/⁸⁶Sr of the vertical reference line, measured at 0.705126: the
#: Zindler & Hart (1986) bulk silicate Earth.  εSr is referred to it,
#: so that εSr = 0 falls on the line the figure draws; the older uniform
#: reservoir of DePaolo & Wasserburg (1976), 0.7045, is not used.
BSE_SR_87_86 = 0.7051

#: The window the figure is drawn in, (x_range, y_range).  Used as the
#: default view; data outside it widens the axes rather than being cut.
#: The frame measures 0.70101-0.70899 and 0.51200-0.51365: the top runs
#: past the last labelled tick at 0.5135, which is where DM reaches, so
#: the range is the frame and not the tick.
SR_ND_WINDOW = ((0.701, 0.709), (0.5120, 0.51365))


@dataclass(frozen=True)
class IsotopeField:
    """One mantle component on the Sr–Nd plane.

    *vertices* is the drawn outline as (⁸⁷Sr/⁸⁶Sr, ¹⁴³Nd/¹⁴⁴Nd) pairs,
    or empty for a component the figure names without enclosing.
    *label* is where the figure writes the name.

    *colour* and *hatch* record how the source fills each field.  The
    view draws the fields as plain white outlines instead — a filled,
    hatched field reads well on its own but competes with the samples
    plotted over it — so these two are provenance, not style: they say
    what the figure did, and are kept so the measurement stays
    complete and auditable.
    """

    name: str
    long_name: str
    colour: str
    label: tuple
    vertices: tuple = ()
    hatch: str | None = None
    open_below: bool = False
    aliases: tuple = _field(default_factory=tuple)

    @property
    def is_drawn(self) -> bool:
        return bool(self.vertices)

    def bounds(self) -> tuple:
        """(sr_min, sr_max, nd_min, nd_max) of the outline."""
        if not self.vertices:
            return (self.label[0], self.label[0],
                    self.label[1], self.label[1])
        sr = [v[0] for v in self.vertices]
        nd = [v[1] for v in self.vertices]
        return (min(sr), max(sr), min(nd), max(nd))

    def centre(self) -> tuple:
        sr0, sr1, nd0, nd1 = self.bounds()
        return ((sr0 + sr1) / 2.0, (nd0 + nd1) / 2.0)


# --------------------------------------------------------------------------
# The fields, in the order the figure stacks them (high Nd first).
# --------------------------------------------------------------------------

SR_ND_FIELDS: tuple = (
    IsotopeField(
        name="DM", long_name="Depleted MORB Mantle",
        colour="#b97233", label=(0.70266, 0.513450),
        vertices=(
            (0.70173, 0.513535),
            (0.70175, 0.513553),
            (0.70210, 0.513541),
            (0.70234, 0.513424),
            (0.70236, 0.513307),
            (0.70228, 0.513272),
            (0.70202, 0.513278),
        ),
    ),
    IsotopeField(
        name="PREMA", long_name="Prevalent Mantle",
        colour="#892c2b", label=(0.70277, 0.513049),
        vertices=(
            (0.70329, 0.513014),
            (0.70341, 0.513043),
            (0.70353, 0.513008),
            (0.70347, 0.512961),
            (0.70333, 0.512961),
        ),
    ),
    IsotopeField(
        name="HIMU", long_name="High-µ",
        colour="#534a7a", label=(0.70275, 0.512773), hatch="||",
        vertices=(
            (0.70273, 0.512850),
            (0.70325, 0.512850),
            (0.70325, 0.512949),
            (0.70273, 0.512949),
        ),
    ),
    IsotopeField(
        name="BSE", long_name="Bulk Silicate Earth",
        colour="#111111", label=(0.70557, 0.512750),
        vertices=(
            (0.70479, 0.512533),
            (0.70546, 0.512533),
            (0.70546, 0.512691),
            (0.70479, 0.512691),
        ),
    ),
    IsotopeField(
        name="EMI", long_name="Enriched Mantle I",
        colour="#a9bed6", label=(0.70450, 0.512126), hatch="||",
        open_below=True, aliases=("EM1",),
        vertices=(
            (0.70397, 0.5120),
            (0.70569, 0.5120),
            (0.70569, 0.512252),
            (0.70397, 0.512252),
        ),
    ),
    IsotopeField(
        name="EMII", long_name="Enriched Mantle II",
        colour="#8c5a6e", label=(0.70771, 0.512243),
        aliases=("EM2",),
    ),
)

FIELDS_BY_NAME = {f.name: f for f in SR_ND_FIELDS}


def resolve_field(name: str):
    """Look a field up by its name or by a name an older session used."""
    if name in FIELDS_BY_NAME:
        return FIELDS_BY_NAME[name]
    for f in SR_ND_FIELDS:
        if name in f.aliases:
            return f
    return None


# --------------------------------------------------------------------------
# The mantle array
# --------------------------------------------------------------------------

# The figure draws two parallel lines and names the pair "Mantle array",
# setting the text along the upper one.  Both are reproduced as drawn,
# including their ends, which stop in mid-panel rather than at the frame.

#: The line the label is set against; it runs through DM, PREMA and BSE.
MANTLE_ARRAY_UPPER = ((0.70148, 0.513423), (0.70606, 0.512492))

#: Its parallel companion, which runs through HIMU.
MANTLE_ARRAY_LOWER = ((0.70134, 0.513213), (0.70579, 0.512306))

MANTLE_ARRAY = (MANTLE_ARRAY_UPPER, MANTLE_ARRAY_LOWER)

#: Where the figure writes "Mantle array" — just above the upper line.
MANTLE_ARRAY_LABEL = (0.70385, 0.513049)


def array_slope(bound=MANTLE_ARRAY_UPPER) -> float:
    """Δ(¹⁴³Nd/¹⁴⁴Nd) per unit ⁸⁷Sr/⁸⁶Sr along one bound.

    Both bounds measure −0.2035 ± 0.0005, i.e. they are parallel to
    within the reading precision of the figure.
    """
    (x0, y0), (x1, y1) = bound
    return (y1 - y0) / (x1 - x0)

# ==========================================================================
# Lead
# ==========================================================================
#
# Only the NHRL is drawn on the Pb planes.  It is a published equation,
# so it is kept exactly rather than traced off a redrawing of it, and
# the figure is used only to check it: the drawn line matches Hart's
# slope to 1.2 % on the 208Pb panel and sits 5-7 px below it, which is
# the redrawing's error, not the equation's.

#: Northern Hemisphere Reference Line (Hart 1984), (slope, intercept).
NHRL_207_206 = (0.1084, 13.491)
NHRL_208_206 = (1.209, 15.627)


def nhrl(x206, which: str = "207"):
    """207Pb/204Pb or 208Pb/204Pb on the NHRL."""
    slope, intercept = NHRL_207_206 if which == "207" else NHRL_208_206
    return slope * x206 + intercept


#: The frames of the source figure's two Pb panels, (x_range, y_range).
#: The plot scales to the data; these are the fallback when there is
#: none yet, so an empty panel still opens on a sensible window.
PB207_WINDOW = ((15.0, 22.5), (15.15, 16.00))
PB208_WINDOW = ((15.0, 22.5), (37.18, 41.81))


def pb_window(y_iso: str) -> tuple:
    return PB207_WINDOW if y_iso == "207" else PB208_WINDOW
