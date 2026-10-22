"""Posterior probability of each tectonic setting in a Verma DF diagram.

Verma & Agrawal (2011), "Probability calculations for individual
samples", eqs (1)-(12).  Every other paper in the family refers back to
it: "the posterior probability calculations for individual samples are
similar to those described recently by Verma and Agrawal (2011)".

For a sample at ``(df1s, df2s)`` in a three-group panel:

    sd_gi = sqrt((df1s - mdf1_gi)^2 + (df2s - mdf2_gi)^2)      (1)-(3)
    sg_i  = exp(-(sd_gi)^2 / 2)                                 (4)-(6)
    P_i   = sg_i / (sg1 + sg2 + sg3)                            (7)-(9)
    P_i % = P_i * 100                                          (10)-(12)

That is the ordinary linear-discriminant posterior with equal priors:
in canonical space the within-group covariance is the identity, so the
only thing that matters is the distance to each group centroid.

Two properties of the published figures follow from it, and this module
is tested against both:

* A boundary between two fields is where those two are equally likely,
  which the paper puts at "about 50% (0.50) probability".
* At the triple point all three distances are equal, so each group gets
  1/3 -- "as one approaches the triple point ... the probability reaches
  to about 33.3% for any given field".

The second is a strong check on the centroids, because the triple point
is published independently of them: equal distances to three points
means the triple point is their circumcentre.

Centroids from the authors' sheet
---------------------------------
Two sets take theirs from the Statistica worksheet in which Verma's
group computed these diagrams (``MGV_DB_4.sta``), because the papers do
not print them:

* Verma & Agrawal (2011) put theirs in an electronic supplement that is
  not to hand.  The program used to derive them from the group means of
  Table 2; the sheet's put the published triple points within 0.002,
  where the derived ones were off by up to 0.012.
* Verma S.K., Pandarinath K. & Verma S.P. (2012) print neither centroids
  nor group means.  The sheet's put every published triple point
  within 0.004 and each lies in its own published field.

The 2004, 2006 and 2008 basic-rock sets have no centroids anywhere, and
report scores and fields only.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from .diagrams.templates.verma_coefficients import (
    V12_ACID,
    V13A_MACID,
    V13A_MTACID,
    V13A_TACID,
    VA11,
    VV13_IMINT,
    VV13_MAJOR,
    VV13_TRACE,
)

#: Which three groups each panel discriminates, in the panel's own order.
PANEL_GROUPS: Dict[str, Tuple[str, str, str]] = {
    # Verma & Agrawal (2011) — basic and ultrabasic
    "IAB_CRBOIB_MORB": ("IAB", "CRB+OIB", "MORB"),
    "IAB_CRB_OIB": ("IAB", "CRB", "OIB"),
    "IAB_CRB_MORB": ("IAB", "CRB", "MORB"),
    "IAB_OIB_MORB": ("IAB", "OIB", "MORB"),
    "CRB_OIB_MORB": ("CRB", "OIB", "MORB"),
    # Verma et al. (2012) — acid, CR without OI
    "IACA_CR_COL": ("IA+CA", "CR", "Col"),
    "IA_CA_CR": ("IA", "CA", "CR"),
    "IA_CR_COL": ("IA", "CR", "Col"),
    "CA_CR_COL": ("CA", "CR", "Col"),
    # Verma & Verma (2013) and Verma et al. (2013) — intermediate and acid
    "IACA_CROI_COL": ("IA+CA", "CR+OI", "Col"),
    "IA_CA_CROI": ("IA", "CA", "CR+OI"),
    "IA_CA_COL": ("IA", "CA", "Col"),
    "IA_CROI_COL": ("IA", "CR+OI", "Col"),
    "CA_CROI_COL": ("CA", "CR+OI", "Col"),
}

# ---------------------------------------------------------------------------
# Published group centroids
# ---------------------------------------------------------------------------
# Read from each paper's figure caption.  Verma & Verma (2013) prints ten
# significant figures; the 2013 acid papers print one or two decimals.

VV13_MAJOR_CENTROIDS = {
    "IACA_CROI_COL": {"IA+CA": (0.8054338548, -0.2585540725),
                      "CR+OI": (-1.964671917, -0.6277101314),
                      "Col": (-0.4642378707, 1.836804090)},
    "IA_CA_CROI": {"IA": (0.7455503041, -0.3210198532),
                   "CA": (0.6646759663, 0.7065892584),
                   "CR+OI": (-2.065048896, -0.01859066688)},
    "IA_CA_COL": {"IA": (0.6581080574, 0.2819229794),
                  "CA": (0.2861131966, -0.6975830163),
                  "Col": (-2.0761856179, 0.1163864964)},
    "IA_CROI_COL": {"IA": (1.069154781, -0.3163633417),
                    "CR+OI": (-1.764731542, -0.7005214343),
                    "Col": (-0.4360327298, 1.7689356843)},
    "CA_CROI_COL": {"CA": (0.8905493277, 0.99156690835),
                    "CR+OI": (-1.4673931178, 0.005642657408),
                    "Col": (0.8759650737, -1.223577442)},
}

VV13_IMINT_CENTROIDS = {
    "IACA_CROI_COL": {"IA+CA": (0.8717919136, 0.1836538565),
                      "CR+OI": (-2.4119835116, 0.9301323744),
                      "Col": (-0.9487745230, -1.4004245813)},
    "IA_CA_CROI": {"IA": (0.7875504506, 0.2520734663),
                   "CA": (0.3148863535, -0.7498501616),
                   "CR+OI": (-2.666419140, 0.1170769090)},
    "IA_CA_COL": {"IA": (-0.6826446433, -0.2400902940),
                  "CA": (-0.2296800482, 0.7483231874),
                  "Col": (1.8880671989, -0.1255771906)},
    "IA_CROI_COL": {"IA": (-1.0703369201, 0.2441771424),
                    "CR+OI": (2.2277092202, 0.8896913710),
                    "Col": (0.7578341279, -1.3397609987)},
    "CA_CROI_COL": {"CA": (-1.7443803369, 0.5101687902),
                    "CR+OI": (1.5687968044, 1.0025551371),
                    "Col": (0.3517867418, -1.3227417914)},
}

VV13_TRACE_CENTROIDS = {
    "IACA_CROI_COL": {"IA+CA": (-0.9774289603, -0.1013788344),
                      "CR+OI": (2.0410269070, -0.5841593120),
                      "Col": (1.1079374566, 1.9556336665)},
    "IA_CA_CROI": {"IA": (-1.1051018735, 0.2721190917),
                   "CA": (-0.3503347313, -0.7829225361),
                   "CR+OI": (2.2466156797, 0.1407633232)},
    "IA_CA_COL": {"IA": (-0.6933875947, 0.2346902936),
                  "CA": (0.1696340466, -0.7135732664),
                  "Col": (2.5411240984, 0.3515850688)},
    "IA_CROI_COL": {"IA": (-1.2898249628, 0.1152106837),
                    "CR+OI": (1.8477651525, 0.5874997038),
                    "Col": (1.0359821323, -1.8330905346)},
    "CA_CROI_COL": {"CA": (-1.5332986559, -0.4569150582),
                    "CR+OI": (1.2333855428, -0.4396529035),
                    "Col": (-0.02124818532, 1.8606170376)},
}

V13A_MACID_CENTROIDS = {
    "IACA_CROI_COL": {"IA+CA": (1.5, 0.1), "CR+OI": (-1.2, 0.6),
                      "Col": (-0.8, -1.7)},
    "IA_CA_CROI": {"IA": (-1.9, 0.7), "CA": (-0.8, -0.9),
                   "CR+OI": (1.4, 0.2)},
    "IA_CA_COL": {"IA": (-1.6, -0.6), "CA": (-0.3, 0.8), "Col": (2.0, -0.3)},
    "IA_CROI_COL": {"IA": (-2.6, 0.05), "CR+OI": (0.8, -0.7),
                    "Col": (0.9, 1.4)},
    "CA_CROI_COL": {"CA": (1.7, -0.3), "CR+OI": (-0.9, -0.5),
                    "Col": (-0.2, 1.5)},
}

V13A_MTACID_CENTROIDS = {
    "IACA_CROI_COL": {"IA+CA": (-1.2, 0.4), "CR+OI": (1.3, 0.4),
                      "Col": (0.04, -1.4)},
    "IA_CA_CROI": {"IA": (-2.0, 0.7), "CA": (-0.6, -0.9),
                   "CR+OI": (1.3, 0.2)},
    "IA_CA_COL": {"IA": (-1.72, 0.39), "CA": (0.05, -0.69),
                  "Col": (1.39, 0.43)},
    "IA_CROI_COL": {"IA": (-2.3, 0.2), "CR+OI": (0.8, 0.6),
                    "Col": (0.4, -1.3)},
    "CA_CROI_COL": {"CA": (-1.2, 0.7), "CR+OI": (1.0, 0.2),
                    "Col": (-0.6, -1.0)},
}

V13A_TACID_CENTROIDS = {
    "IACA_CROI_COL": {"IA+CA": (-1.0, -0.5), "CR+OI": (1.9, -0.7),
                      "Col": (0.2, 1.0)},
    "IA_CA_CROI": {"IA": (-2.3, 1.3), "CA": (-0.4, -1.0),
                   "CR+OI": (2.2, 0.7)},
    "IA_CA_COL": {"IA": (-2.9, 0.3), "CA": (-0.1, -0.4), "Col": (1.3, 0.2)},
    "IA_CROI_COL": {"IA": (-3.7, -0.5), "CR+OI": (0.4, 1.8),
                    "Col": (1.3, -0.9)},
    "CA_CROI_COL": {"CA": (-0.9, -0.8), "CR+OI": (1.8, -0.4),
                    "Col": (-0.2, 0.9)},
}

# ---------------------------------------------------------------------------
# Centroids from the authors' Statistica sheet (MGV_DB_4.sta)
# ---------------------------------------------------------------------------
# Its MdfG constants, in each panel's group order.  Checked against what
# the papers do print: the circumcentre of each panel's three falls on
# its published triple point -- within 0.002 for Verma & Agrawal (2011),
# 0.004 for Verma et al. (2012) -- and each lies in its own field.

#: Verma & Agrawal (2011), whose own are in a supplement not to hand.
VA11_CENTROIDS = {
    "IAB_CRBOIB_MORB": {
        "IAB": (3.1811, 0.52226),
        "CRB+OIB": (-1.80906, 0.09548),
        "MORB": (1.72886, -1.44601),
    },
    "IAB_CRB_OIB": {
        "IAB": (3.43726, -0.06394),
        "CRB": (-1.35254, 0.70692),
        "OIB": (-1.73941, -0.76481),
    },
    "IAB_CRB_MORB": {
        "IAB": (2.41306544, 0.464585166),
        "CRB": (-2.36861391, 0.179370517),
        "MORB": (0.890298225, -1.33809654),
    },
    "IAB_OIB_MORB": {
        "IAB": (2.6924287, 0.599253932),
        "OIB": (-3.24439681, 0.17628963),
        "MORB": (1.30665513, -1.53450743),
    },
    "CRB_OIB_MORB": {
        "CRB": (-0.566446254, 0.817982615),
        "OIB": (-0.919384937, -0.874756488),
        "MORB": (3.21361453, -0.16593782),
    },
}

#: Verma, Pandarinath & Verma (2012), which prints none.
V12_ACID_CENTROIDS = {
    "IACA_CR_COL": {
        "IA+CA": (1.031605, 0.191096),
        "CR": (-1.47289, 1.33749),
        "Col": (-0.82488, -1.42141),
    },
    "IA_CA_CR": {
        "IA": (-1.25273, -0.55069),
        "CA": (-0.388329, 0.801597),
        "CR": (2.042011, -0.247561),
    },
    "IA_CA_COL": {
        "IA": (-1.51021, 0.35464),
        "CA": (-0.234425, -0.619003),
        "Col": (1.719259, 0.233037),
    },
    "IA_CR_COL": {
        "IA": (2.061511, -0.173425),
        "CR": (-0.869467, 1.50485),
        "Col": (-1.36925, -1.01286),
    },
    "CA_CR_COL": {
        "CA": (-0.589027, 1.145966),
        "CR": (1.612233, -0.078004),
        "Col": (-0.72481, -1.00119),
    },
}

# ---------------------------------------------------------------------------
# Verma & Agrawal (2011) centroids, derived -- kept as a check
# ---------------------------------------------------------------------------
# Before the sheet was to hand these came from Table 2, the group mean
# log-ratios of the training set: a DF is linear in those, so evaluating
# it at a group's means gives that group's centroid.  The means are
# printed to two or three decimals, which puts the derived centroids
# within 0.015 of the sheet's and their triple points within 0.012 of
# the published ones; the tests keep both comparisons.

#: Verma & Agrawal (2011) Table 2 — training-set mean log-ratios over
#: (TiO2)adj, with both terms in ug/g as the paper requires.
VA11_GROUP_MEANS = {
    "IAB": {"Nb": -8.18, "V": -3.464, "Y": -6.094, "Zr": -4.967},
    "CRB": {"Nb": -6.19, "V": -4.669, "Y": -6.721, "Zr": -4.700},
    "OIB": {"Nb": -6.78, "V": -4.690, "Y": -6.994, "Zr": -4.900},
    "MORB": {"Nb": -8.13, "V": -4.043, "Y": -6.146, "Zr": -4.974},
}


def _df_at_means(coef, means: Dict[str, float]) -> float:
    return coef.intercept + sum(c * means[p]
                                for p, c in zip(coef.parts, coef.coefs))


def _va11_centroids() -> Dict[str, Dict[str, Tuple[float, float]]]:
    out: Dict[str, Dict[str, Tuple[float, float]]] = {}
    for panel, groups in PANEL_GROUPS.items():
        if f"DF1_{panel}" not in VA11:
            continue
        df1, df2 = VA11[f"DF1_{panel}"], VA11[f"DF2_{panel}"]
        here: Dict[str, Tuple[float, float]] = {}
        for group in groups:
            # "CRB+OIB" is one group in panel (a); the paper gives no
            # sample counts, so the two means are combined unweighted.
            members = group.split("+") if "+" in group else [group]
            xs = [_df_at_means(df1, VA11_GROUP_MEANS[m]) for m in members]
            ys = [_df_at_means(df2, VA11_GROUP_MEANS[m]) for m in members]
            here[group] = (sum(xs) / len(xs), sum(ys) / len(ys))
        out[panel] = here
    return out


VA11_DERIVED_CENTROIDS = _va11_centroids()

#: Every set that can report probabilities, keyed as the coefficient
#: tables are, with the citation used for the statistics category.
CENTROIDS: Dict[str, Dict[str, Dict[str, Tuple[float, float]]]] = {
    "VA11": VA11_CENTROIDS,
    "V12_ACID": V12_ACID_CENTROIDS,
    "VV13_MAJOR": VV13_MAJOR_CENTROIDS,
    "VV13_IMINT": VV13_IMINT_CENTROIDS,
    "VV13_TRACE": VV13_TRACE_CENTROIDS,
    "V13A_MACID": V13A_MACID_CENTROIDS,
    "V13A_MTACID": V13A_MTACID_CENTROIDS,
    "V13A_TACID": V13A_TACID_CENTROIDS,
}

#: The coefficient table each centroid set belongs to.
TABLES = {
    "VA11": VA11,
    "V12_ACID": V12_ACID,
    "VV13_MAJOR": VV13_MAJOR,
    "VV13_IMINT": VV13_IMINT,
    "VV13_TRACE": VV13_TRACE,
    "V13A_MACID": V13A_MACID,
    "V13A_MTACID": V13A_MTACID,
    "V13A_TACID": V13A_TACID,
}

#: Chance level when three groups are equally likely, as a percentage.
BY_CHANCE_PERCENT = 100.0 / 3.0


def posterior_percent(df1, df2,
                      centroids: Dict[str, Tuple[float, float]]
                      ) -> Dict[str, pd.Series]:
    """Probability of each group, in percent, for samples at (df1, df2).

    Implements eqs (1)-(12).  Returns one Series per group, indexed like
    the inputs; a sample missing either score gets NaN for every group.

    The exponentials are computed relative to the smallest squared
    distance.  Subtracting a constant from every exponent leaves the
    normalised ratios untouched, and it keeps ``exp`` from underflowing
    to zero for a sample far from all three centroids -- which would
    otherwise divide 0 by 0 and lose the very samples a user most wants
    to see flagged.
    """
    df1 = pd.Series(df1, dtype=float)
    df2 = pd.Series(df2, dtype=float)
    names = list(centroids)
    squared = {}
    for name in names:
        cx, cy = centroids[name]
        squared[name] = (df1 - cx) ** 2 + (df2 - cy) ** 2

    smallest = None
    for name in names:
        smallest = squared[name] if smallest is None else np.minimum(
            smallest, squared[name])

    weights = {name: np.exp(-(squared[name] - smallest) / 2.0)
               for name in names}
    total = sum(weights.values())
    total = total.where(total > 0)
    return {name: 100.0 * weights[name] / total for name in names}


def panel_probabilities(df: pd.DataFrame, table_key: str, panel: str
                        ) -> Optional[Dict[str, pd.Series]]:
    """Probabilities for one panel, straight from a sample table.

    ``None`` when the analysis lacks a column the panel's DFs need.
    """
    from .diagrams.templates.verma_multidim import (_apply_df,
                                                    _logratios_for_coef)

    table = TABLES[table_key]
    df1, df2 = table.get(f"DF1_{panel}"), table.get(f"DF2_{panel}")
    if df1 is None or df2 is None:
        return None
    ratios = _logratios_for_coef(df, df1)
    if ratios is None:
        return None
    return posterior_percent(_apply_df(ratios, df1), _apply_df(ratios, df2),
                             CENTROIDS[table_key][panel])


def circumcentre(points) -> Optional[Tuple[float, float]]:
    """Centre of the circle through three points, or None if collinear.

    The point equidistant from all three centroids is where the three
    posterior probabilities are equal, so this is where a panel's triple
    point has to be.
    """
    (ax, ay), (bx, by), (cx, cy) = points
    d = 2.0 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-12:
        return None
    a2, b2, c2 = ax * ax + ay * ay, bx * bx + by * by, cx * cx + cy * cy
    return ((a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d,
            (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d)


def equal_probability_radius(percent: float) -> float:
    """How far a sample sits from a centroid at a given probability.

    Only meaningful against a single competing group at the same
    distance on the other side; used to sanity-check the 50 % boundary.
    """
    if not 0.0 < percent < 100.0:
        raise ValueError("percent must lie strictly between 0 and 100")
    return math.sqrt(-2.0 * math.log(percent / 100.0))
