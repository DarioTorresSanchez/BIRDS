"""εSr and εNd: which reservoir, and at what time.

εSr is referred to the bulk silicate Earth of Zindler & Hart (1986),
0.7051, the vertical line the Sr-Nd figure draws, so that εSr = 0 falls
on it.  Initial ε values are taken against the reservoir as it was at
the sample's age: they used to be taken against today's, which puts a
1 Ga rock that evolved exactly as CHUR at about −25 εNd instead of 0.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from birds.isotope_fields import BSE_SR_87_86
from birds.views.isotopes import (
    AGE_EARTH_YR,
    BABI_SR_87_86,
    LAMBDA_RB,
    LAMBDA_SM,
    ND_CHUR,
    RB_SR_UR,
    SM_ND_CHUR,
    SR_UR_87_86,
    compute_initial_ratio,
    epsilon_nd,
    epsilon_sr,
)


def test_epsilon_sr_is_zero_on_the_line_the_figure_draws():
    assert SR_UR_87_86 == BSE_SR_87_86 == 0.7051
    assert epsilon_sr(0.7051) == pytest.approx(0.0, abs=1e-12)


def test_the_strontium_reservoir_starts_at_babi():
    """Closed since 4.55 Ga: it must run back to BABI."""
    then = compute_initial_ratio(SR_UR_87_86, RB_SR_UR,
                                 AGE_EARTH_YR / 1e6, LAMBDA_RB)
    assert then == pytest.approx(BABI_SR_87_86, abs=1e-12)


def test_the_same_construction_gives_the_classic_pair():
    """0.7045 is quoted with 87Rb/86Sr = 0.0827; built the same way from
    BABI it gets 0.0826, which is what makes 0.0916 the right partner
    for 0.7051 rather than a number picked to fit."""
    classic = (0.7045 - BABI_SR_87_86) / (
        np.exp(LAMBDA_RB * AGE_EARTH_YR) - 1.0)
    assert classic == pytest.approx(0.0827, abs=0.0005)
    assert RB_SR_UR == pytest.approx(0.0916, abs=0.0005)


def test_chur_back_in_time_matches_the_textbook():
    """Rollinson & Pease (2021), worked example: CHUR at 3.54 Ga is
    0.512638 − 0.1967 (e^(6.54e-12 × 3.54e9) − 1) = 0.508031."""
    chur = compute_initial_ratio(ND_CHUR, SM_ND_CHUR, 3540.0, LAMBDA_SM)
    assert chur == pytest.approx(0.508031, abs=1e-6)


@pytest.mark.parametrize("age_Ma", [0.0, 100.0, 1000.0, 3000.0])
def test_a_rock_that_evolved_as_chur_reads_zero_at_any_age(age_Ma):
    nd_then = compute_initial_ratio(ND_CHUR, SM_ND_CHUR, age_Ma, LAMBDA_SM)
    assert epsilon_nd(nd_then, age_Ma) == pytest.approx(0.0, abs=1e-9)


@pytest.mark.parametrize("age_Ma", [0.0, 100.0, 1000.0, 3000.0])
def test_a_rock_that_evolved_as_the_reservoir_reads_zero_in_sr(age_Ma):
    sr_then = compute_initial_ratio(SR_UR_87_86, RB_SR_UR, age_Ma,
                                    LAMBDA_RB)
    assert epsilon_sr(sr_then, age_Ma) == pytest.approx(0.0, abs=1e-9)


def test_against_todays_chur_the_same_rock_would_read_minus_25():
    """The size of what was wrong."""
    nd_then = compute_initial_ratio(ND_CHUR, SM_ND_CHUR, 1000.0, LAMBDA_SM)
    assert epsilon_nd(nd_then) == pytest.approx(-25.2, abs=0.2)


def test_ages_can_differ_from_sample_to_sample():
    ages = pd.Series([0.0, 500.0, 2000.0])
    nd = compute_initial_ratio(ND_CHUR, SM_ND_CHUR, ages, LAMBDA_SM)
    assert epsilon_nd(nd, ages).to_numpy() == pytest.approx(np.zeros(3),
                                                             abs=1e-9)


# ---------------------------------------------------------------------------
# Through the view
# ---------------------------------------------------------------------------

@pytest.fixture
def view(qapp):
    from birds.data_manager import DataManager
    from birds.plot_style import PlotStyle
    from birds.views.isotopes import IsotopesView

    age = 1000.0
    data = DataManager()
    # Two samples that evolved as the reservoirs did: today they sit at
    # the reservoirs' present ratios with the reservoirs' parent ratios.
    data.df = pd.DataFrame({
        "Sample": ["A", "B"],
        "87Sr/86Sr": [SR_UR_87_86] * 2,
        "143Nd/144Nd": [ND_CHUR] * 2,
        "87Rb/86Sr": [RB_SR_UR] * 2,
        "147Sm/144Nd": [SM_ND_CHUR] * 2,
        "Age": [age, age],
    })
    v = IsotopesView(data, PlotStyle())
    v._populate_columns()
    v.age_box.setChecked(True)
    v.age_value.setValue(age)
    return v


def test_the_view_reports_initial_epsilon_against_the_reservoir_then(view):
    derived = view._initials_and_eps(view.data.df)
    assert derived["eps_nd_i"].to_numpy() == pytest.approx([0.0, 0.0],
                                                           abs=1e-9)
    assert derived["eps_sr_i"].to_numpy() == pytest.approx([0.0, 0.0],
                                                           abs=1e-9)


def test_the_epsilon_axes_follow_the_age(view):
    view.eps_axes_chk.setChecked(True)
    view.update_plot()
    secondary = view.canvas.figure.axes[0].child_axes
    labels = [a.get_xlabel() for a in secondary] + [
        a.get_ylabel() for a in secondary]
    assert "εSr  (t = 1000 Ma)" in labels
    assert "εNd  (t = 1000 Ma)" in labels


def test_with_an_age_per_sample_there_is_no_single_epsilon_axis(view):
    view.age_source.setCurrentIndex(1)            # "Use a column"
    i = view.age_column.findData("Age")
    view.age_column.setCurrentIndex(i)
    view.eps_axes_chk.setChecked(True)
    view.update_plot()
    ax = view.canvas.figure.axes[0]
    assert any("single age" in t.get_text() for t in ax.texts)
    assert not ax.child_axes
