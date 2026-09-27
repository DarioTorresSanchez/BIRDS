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

Why ``verma_2012_acid`` is absent
---------------------------------
Verma S.K., Pandarinath K. & Verma S.P. (2012) prints neither group
centroids nor group mean log-ratios, so there is nothing to measure the
distances from.  Its DF values are still reported; only the
probabilities are missing.  The three 2013 acid sets cover acid rocks.
"""

from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

from .diagrams.templates.verma_coefficients import (
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
# Verma & Agrawal (2011) centroids, derived
# ---------------------------------------------------------------------------
# That paper puts its centroids in Table A4 of an electronic supplement
# that is not to hand.  It does print, in Table 2, the group mean
# log-ratios of the training set, and a DF is linear in those, so
# evaluating it at a group's means gives that group's centroid exactly.
#
# The derivation is checked rather than assumed: the triple point of
# each panel, published in the Figure 1 caption and used nowhere in the
# derivation, must be the circumcentre of the three centroids it
# produces.  It is, to 0.01 on every panel.

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


VA11_CENTROIDS = _va11_centroids()

#: Every set that can report probabilities, keyed as the coefficient
#: tables are, with the citation used for the statistics category.
CENTROIDS: Dict[str, Dict[str, Dict[str, Tuple[float, float]]]] = {
    "VA11": VA11_CENTROIDS,
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
