"""The three Saccani (2015) discriminants.

Saccani admits in section 7 that the boundaries of his Figures 5, 8 and
9 "were drawn by eye in order to obtain the best discrimination between
different basaltic types", so there is no analysis here to reproduce.
What he does do is print the coordinates of every line on the figure
itself, in brackets beside an arrow pointing at the end they belong to.
Those printed numbers are what the three diagrams now carry, and what
this file pins.

Three things were wrong before, and each has a test below:

* **The normaliser.**  Figures 8 and 9 are chondrite-normalised -- both
  captions say so and both run to Dy_N = 25 -- and all three diagrams
  were drawn against N-MORB.  That is a factor of 17.9 on Dy and Yb, so
  every sample fell off the bottom-left corner of a frame it should
  have filled.  The statistics table reached the same quantities by its
  own route and had the same fault.
* **The axis order.**  Figure 8 plots (Dy/Yb)_N against (Ce/Yb)_N and
  Figure 9 plots Yb_N against Dy_N; both pairs were the other way up.
* **The scales.**  Both are linear, and both were logarithmic.

The ratio (Dy/Yb)_N is the one quantity the old code got nearly right,
within 0.15 %, because N-MORB and chondrite have almost the same Dy/Yb.
That coincidence is asserted below too: it is the reason the fault was
easy to miss in the one row where it did not show.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.diagrams.registry import get_diagram
from birds.diagrams.templates.tectonic_bivariate import (
    _NMORB_SUN,
    _SACCANI_BONINITE_DY_N,
    _SACCANI_CE_YB_LINE,
    _SACCANI_CHONDRITE,
    _SACCANI_DY_YB_LINE,
    _SACCANI_PM,
    _SACCANI_TH_NB_LINES,
)
from birds.normalizations import REE_CHONDRITES
from birds.tectonic_results import DISCRIMINATORS


# ---------------------------------------------------------------------------
# The normalisers
# ---------------------------------------------------------------------------

def test_figures_8_and_9_normalise_to_chondrite():
    """Sun & McDonough (1989) CI, the values both captions cite."""
    assert _SACCANI_CHONDRITE["Ce"] == pytest.approx(0.612)
    assert _SACCANI_CHONDRITE["Dy"] == pytest.approx(0.254)
    assert _SACCANI_CHONDRITE["Yb"] == pytest.approx(0.17)


def test_chondrite_is_the_shared_table_not_a_copy():
    """So that editing the spider normaliser cannot silently move these."""
    assert _SACCANI_CHONDRITE is REE_CHONDRITES["Sun & McDonough (1989) – CI"]


def test_figure_5_normalises_to_n_morb():
    """Figure 5 is the one that does use N-MORB, and keeps it."""
    nb, th = _NMORB_SUN["Nb"], _NMORB_SUN["Th"]
    assert (nb, th) == pytest.approx((2.33, 0.12))
    x, y = get_diagram("saccani2015_nb_th")._compute_xy(
        pd.DataFrame({"Nb": [nb], "Th": [th]}))
    # N-MORB normalised to N-MORB is the "+ N-MORB" cross at (1, 1).
    assert (float(x.iloc[0]), float(y.iloc[0])) == pytest.approx((1.0, 1.0))


def test_dy_over_yb_is_why_the_wrong_normaliser_hid_in_that_one_row():
    """N-MORB and chondrite have nearly the same Dy/Yb -- within 0.15 %.

    So (Dy/Yb)_N barely moved when the normaliser was wrong, while
    (Ce/Yb)_N was 46 % high and Dy_N and Yb_N were 17.9 times low.
    """
    chondritic = _SACCANI_CHONDRITE["Dy"] / _SACCANI_CHONDRITE["Yb"]
    n_morb = _NMORB_SUN["Dy"] / _NMORB_SUN["Yb"]
    assert chondritic == pytest.approx(n_morb, rel=2e-3)
    assert chondritic != n_morb          # near, but not a licence to swap

    # Dividing by the smaller Ce/Yb of N-MORB gave the larger ratio.
    ce_shift = ((_SACCANI_CHONDRITE["Ce"] / _SACCANI_CHONDRITE["Yb"])
                / (_NMORB_SUN["Ce"] / _NMORB_SUN["Yb"]))
    assert ce_shift == pytest.approx(1.46, abs=0.01)
    assert _NMORB_SUN["Dy"] / _SACCANI_CHONDRITE["Dy"] == pytest.approx(
        17.9, abs=0.05)


# ---------------------------------------------------------------------------
# The frames, which are the ones the figures are drawn on
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key, x_label, y_label, x_range, y_range, logs", [
    ("saccani2015_nb_th", "Nb", "Th", (0.01, 100), (0.01, 1000), True),
    ("saccani2015_ce_dy_yb", "Ce/Yb", "Dy/Yb", (0, 2.5), (0.5, 2), False),
    ("saccani2015_dy_yb", "Dy", "Yb", (0, 25), (0, 25), False),
])
def test_frame_matches_the_published_figure(key, x_label, y_label,
                                            x_range, y_range, logs):
    d = get_diagram(key)
    assert x_label in d.x_label and y_label in d.y_label
    assert tuple(d.x_range) == x_range
    assert tuple(d.y_range) == y_range
    assert d.log_x is logs and d.log_y is logs


# ---------------------------------------------------------------------------
# Figure 5a -- the four printed segments
# ---------------------------------------------------------------------------

def test_figure_5a_prints_these_four_segments():
    assert _SACCANI_PM == (0.306, 0.708)
    assert _SACCANI_TH_NB_LINES == (
        ((0.306, 0.708), (100.0, 1000.0)),
        ((0.01, 0.1), (0.306, 0.708)),
        ((0.01, 20.0), (2.2, 8.0)),
        ((0.306, 0.708), (0.5, 0.01)),
    )


def test_three_segments_meet_at_the_printed_pm():
    """PM anchors three of the four; a junction has to be one point."""
    touching = [seg for seg in _SACCANI_TH_NB_LINES if _SACCANI_PM in seg]
    assert len(touching) == 3


def test_printed_pm_is_sun_and_mcdonough_pm_over_their_n_morb():
    """Nb 0.713 and Th 0.0850 ppm, which is where (0.306, 0.708) is from.

    The project's own primitive-mantle tables are McDonough & Sun (1995)
    and Palme & O'Neill (2014), neither of which reproduces it, so the
    printed pair is used as printed rather than recomputed.
    """
    assert _SACCANI_PM[0] == pytest.approx(0.713 / _NMORB_SUN["Nb"], abs=5e-4)
    assert _SACCANI_PM[1] == pytest.approx(0.0850 / _NMORB_SUN["Th"], abs=5e-4)


def test_the_arc_array_segment_stops_just_short_of_the_main_one():
    """(0.01, 20) to (2.2, 8.0) ends 4.8 % below the PM -> (100, 1000) line.

    On the figure the two meet.  Their printed coordinates do not quite:
    the main segment passes through Th_N = 8.38 at Nb_N = 2.2, where the
    upper one is printed as ending at 8.0.  Across five decades of Th_N
    that gap is a fiftieth of the frame height -- thinner than the lines
    are drawn, which is why it is invisible and why it is there at all.
    Saccani drew these by eye and read the numbers back off them.  The
    printed 8.0 is kept as printed; nothing here is worth "correcting"
    to make a junction close that the author never claimed was one.
    """
    (x0, y0), (x1, y1) = _SACCANI_TH_NB_LINES[0]
    slope = ((np.log10(y1) - np.log10(y0))
             / (np.log10(x1) - np.log10(x0)))
    at = 10 ** (np.log10(y0) + slope * (np.log10(2.2) - np.log10(x0)))
    assert at == pytest.approx(8.38, abs=0.01)
    assert _SACCANI_TH_NB_LINES[2][1] == (2.2, 8.0)
    gap_in_frame_heights = abs(np.log10(at / 8.0)) / np.log10(1000 / 0.01)
    assert gap_in_frame_heights < 0.005


# ---------------------------------------------------------------------------
# Figure 5a -- which side of the main segment a basalt falls
# ---------------------------------------------------------------------------

def _th_nb(nb, th):
    x, y = get_diagram("saccani2015_nb_th")._compute_xy(
        pd.DataFrame({"Nb": [nb], "Th": [th]}))
    return float(x.iloc[0]), float(y.iloc[0])


def _above_main_array(x, y):
    (x0, y0), (x1, y1) = _SACCANI_TH_NB_LINES[0]
    slope = ((np.log10(y1) - np.log10(y0))
             / (np.log10(x1) - np.log10(x0)))
    return np.log10(y) > np.log10(y0) + slope * (np.log10(x) - np.log10(x0))


@pytest.mark.parametrize("name, nb, th, subduction_related", [
    # Sun & McDonough (1989), the two crosses Figure 5a draws by name.
    ("N-MORB", 2.33, 0.12, False),
    ("E-MORB", 8.30, 0.60, False),
    # Arc rocks: low Nb against their Th, which is the whole point.
    ("boninite", 0.35, 0.20, True),
    ("island-arc tholeiite", 0.90, 0.45, True),
    ("calc-alkaline basalt", 2.0, 4.0, True),
])
def test_main_segment_sorts_the_two_arrays(name, nb, th, subduction_related):
    """">99 %" either way, per the text, so these five must all land right."""
    assert _above_main_array(*_th_nb(nb, th)) == subduction_related, name


# ---------------------------------------------------------------------------
# Figure 8 -- (Dy/Yb)N against (Ce/Yb)N
# ---------------------------------------------------------------------------

def test_figure_8_prints_this_separation_line():
    assert _SACCANI_CE_YB_LINE == ((0.4, 1.5), (2.0, 0.9))


def test_figure_8_line_ends_inside_its_own_frame():
    d = get_diagram("saccani2015_ce_dy_yb")
    for x, y in _SACCANI_CE_YB_LINE:
        assert d.x_range[0] <= x <= d.x_range[1]
        assert d.y_range[0] <= y <= d.y_range[1]


def test_figure_8_puts_ce_yb_on_x():
    """The axes were swapped; Saccani has (Ce/Yb)_N across the bottom."""
    d = get_diagram("saccani2015_ce_dy_yb")
    # Ce enters x only, so moving Ce alone may not move y.
    base = pd.DataFrame({"Ce": [7.5], "Dy": [4.55], "Yb": [3.05]})
    more_ce = pd.DataFrame({"Ce": [15.0], "Dy": [4.55], "Yb": [3.05]})
    x0, y0 = d._compute_xy(base)
    x1, y1 = d._compute_xy(more_ce)
    assert float(x1.iloc[0]) > float(x0.iloc[0])
    assert float(y1.iloc[0]) == pytest.approx(float(y0.iloc[0]))


def _ce_dy_yb(ce, dy, yb):
    x, y = get_diagram("saccani2015_ce_dy_yb")._compute_xy(
        pd.DataFrame({"Ce": [ce], "Dy": [dy], "Yb": [yb]}))
    return float(x.iloc[0]), float(y.iloc[0])


def test_n_morb_lands_in_the_n_morb_field():
    """Sun & McDonough's N-MORB, below the line where Figure 8 puts it."""
    x, y = _ce_dy_yb(7.50, 4.55, 3.05)
    (x0, y0), (x1, y1) = _SACCANI_CE_YB_LINE
    at = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    assert y < at
    # and in the middle of the blue cloud, not off in a corner
    assert 0.3 < x < 1.3 and 0.85 < y < 1.3


# ---------------------------------------------------------------------------
# Figure 9 -- YbN against DyN
# ---------------------------------------------------------------------------

def test_figure_9_prints_this_separation_line():
    assert _SACCANI_DY_YB_LINE == ((7.0, 25.0), (9.5, 0.0))


def test_figure_9_line_spans_the_whole_frame_height():
    """It is drawn corner to corner in y, which is what makes it a split."""
    d = get_diagram("saccani2015_dy_yb")
    ys = sorted(y for _x, y in _SACCANI_DY_YB_LINE)
    assert (ys[0], ys[1]) == (d.y_range[0], d.y_range[1])


def test_figure_9_puts_dy_on_x():
    """The axes were swapped; Saccani has Dy_N across the bottom."""
    d = get_diagram("saccani2015_dy_yb")
    x, y = d._compute_xy(pd.DataFrame({"Dy": [2.54], "Yb": [1.70]}))
    assert float(x.iloc[0]) == pytest.approx(10.0)
    assert float(y.iloc[0]) == pytest.approx(10.0)
    x, y = d._compute_xy(pd.DataFrame({"Dy": [5.08], "Yb": [1.70]}))
    assert float(x.iloc[0]) == pytest.approx(20.0)
    assert float(y.iloc[0]) == pytest.approx(10.0)


def _left_of_boninite_line(x, y):
    (x0, y0), (x1, y1) = _SACCANI_DY_YB_LINE
    at = x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return x < at


@pytest.mark.parametrize("name, dy, yb, boninite", [
    ("boninite", 1.4, 1.3, True),
    ("depleted boninite", 0.9, 0.8, True),
    ("island-arc tholeiite", 3.4, 3.0, False),
    ("evolved IAT", 4.6, 4.1, False),
])
def test_the_line_and_the_dy_rule_agree(name, dy, yb, boninite):
    """Saccani gives two rules, and ordinary samples fall under both.

    The line of Figure 9, and the text's "99.5% of boninites have DyN <
    8.5 and 99% of IATs have DyN > 8.5".  These four sit well clear of
    the band where the two part company; that band has a test of its
    own below.
    """
    x, y = get_diagram("saccani2015_dy_yb")._compute_xy(
        pd.DataFrame({"Dy": [dy], "Yb": [yb]}))
    x, y = float(x.iloc[0]), float(y.iloc[0])
    assert _left_of_boninite_line(x, y) == boninite, name
    assert (x < _SACCANI_BONINITE_DY_N) == boninite, name


def test_the_dy_rule_sits_between_the_two_ends_of_the_line():
    """8.5 is a vertical standing in for a line that runs 7.0 to 9.5."""
    assert _SACCANI_BONINITE_DY_N == 8.5
    xs = sorted(x for x, _y in _SACCANI_DY_YB_LINE)
    assert xs[0] < _SACCANI_BONINITE_DY_N < xs[1]


def test_saccanis_two_rules_contradict_each_other_in_a_bowtie():
    """The vertical at Dy_N = 8.5 cuts the sloping line, so they disagree.

    Figure 9's line runs Dy_N = 9.5 - 0.1 x Yb_N, which equals 8.5 only
    at Yb_N = 10.  Away from that one crossing the two rules the paper
    gives call a band of samples differently, and the band widens in
    both directions: a full unit of Dy_N at the foot of the frame and
    one and a half at the top, which is a fifth of the value there.  It
    is not a rounding difference and not a sliver.

    The diagram draws the line, because that is what Figure 9 is.  The
    disagreement is Saccani's own, so neither rule is adjusted to meet
    the other; both are quoted in the citation instead, so that a user
    landing in the band can see there are two answers.
    """
    # They cross at one point only.
    assert _SACCANI_DY_YB_LINE == ((7.0, 25.0), (9.5, 0.0))
    crossing_yb = (9.5 - _SACCANI_BONINITE_DY_N) / 0.1
    assert crossing_yb == pytest.approx(10.0)

    # Below the crossing: boninite by the line, IAT by the Dy_N rule.
    assert _left_of_boninite_line(9.0, 2.0)
    assert not 9.0 < _SACCANI_BONINITE_DY_N

    # Above it, the disagreement reverses.
    assert not _left_of_boninite_line(8.0, 22.0)
    assert 8.0 < _SACCANI_BONINITE_DY_N

    # The band is as wide as |9.5 - 0.1*Yb_N - 8.5| in Dy_N.
    for yb, width in ((0.0, 1.0), (10.0, 0.0), (25.0, 1.5)):
        line_x = 9.5 - 0.1 * yb
        assert abs(line_x - _SACCANI_BONINITE_DY_N) == pytest.approx(width)

    # Outside it the two agree, which is why both can be stated at all.
    for x in (3.0, 20.0):
        for yb in (0.0, 10.0, 25.0):
            assert _left_of_boninite_line(x, yb) == (
                x < _SACCANI_BONINITE_DY_N)


# ---------------------------------------------------------------------------
# The statistics table, which had the same fault by its own route
# ---------------------------------------------------------------------------

def _discriminator(key):
    found = [d for d in DISCRIMINATORS if d.key == key]
    assert len(found) == 1, key
    return found[0]


SACCANI_ROWS = {
    "saccani.nb_n": ("Nb", _NMORB_SUN["Nb"]),
    "saccani.th_n": ("Th", _NMORB_SUN["Th"]),
    "saccani.dy_n": ("Dy", _SACCANI_CHONDRITE["Dy"]),
    "saccani.yb_n": ("Yb", _SACCANI_CHONDRITE["Yb"]),
}


@pytest.mark.parametrize("key", sorted(SACCANI_ROWS))
def test_statistics_rows_use_the_same_normaliser_as_the_diagram(key):
    element, divisor = SACCANI_ROWS[key]
    df = pd.DataFrame({element: [divisor]})
    out = _discriminator(key).compute(df)
    assert out is not None
    assert float(out.iloc[0]) == pytest.approx(1.0)


def test_statistics_ratio_rows_match_the_diagram_exactly():
    """The table and Figure 8 must not answer differently."""
    df = pd.DataFrame({"Ce": [7.50], "Dy": [4.55], "Yb": [3.05]})
    x, y = get_diagram("saccani2015_ce_dy_yb")._compute_xy(df)
    assert float(_discriminator("saccani.ce_yb_n").compute(df).iloc[0]) == (
        pytest.approx(float(x.iloc[0])))
    assert float(_discriminator("saccani.dy_yb_n").compute(df).iloc[0]) == (
        pytest.approx(float(y.iloc[0])))


@pytest.mark.parametrize("key", sorted(SACCANI_ROWS) + [
    "saccani.ce_yb_n", "saccani.dy_yb_n"])
def test_statistics_rows_say_which_normaliser_they_used(key):
    """Four of the six changed normaliser; the label has to say so."""
    d = _discriminator(key)
    expected = "N-MORB" if key in ("saccani.nb_n", "saccani.th_n") \
        else "chondrite"
    assert expected in d.label or expected in d.group
