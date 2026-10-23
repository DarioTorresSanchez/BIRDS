"""Map diagram keys -> Diagram instances ready to plot."""

from __future__ import annotations

from typing import Dict

from .templates.li2025 import Li2025NbYbThNb
from .templates.godang2024 import Godang2024NbZrThNb
from .templates.afm import AFM
from .templates.barker import BarkerAnAbOr
from .templates.frost import Frost
from .templates.hanski import HanskiHighMg
from .templates.hastie import Hastie2007ThCo
from .templates.winchester_floyd import WinchesterFloyd1977
from .templates.haplogranite import Haplogranite
from .templates.highmg_tas import HighMgTAS
from .templates.ib1971 import AlkalicSubAlkalicBoundary
from .templates.jensen import Jensen
from .templates.k2o_sio2 import K2OvsSiO2
from .templates.major_df import ButlerWoronowDF, Pearce1976DF
from .templates.maniar_piccolli import ManiarPiccolli1989
from .templates.petrography import (
    GabbroPlPxOl,
    PyroclasticFisher1966,
    StreckeisenQAPFPlutonic,
    StreckeisenQAPFVolcanic,
    TuffSchmid1981,
    UltramaficOlOpxCpx,
)
from .templates.tas import TASPlutonic, TASVolcanic
from .templates.tectonic_bivariate import (
    DefantDrummondYSrY,
    Pearce1984YbTa,
    Pearce1984YbTaRb,
    Pearce1984YNb,
    Pearce1984YNbRb,
    Pearce2008ThYbNbYb,
    Pearce2008TiYbNbYb,
    PearceCann1973ZrTi,
    PearceGale1977,
    Saccani2015CeDyYb,
    Saccani2015DyYb,
    Saccani2015NbTh,
    Shervais1982TiV,
    Yang2019FCKANTMS,
    Yang2019FCMS,
)
from .templates.tectonic_ternary import (
    CabanisLecolle1989,
    Harris1986HfRbTa,
    Vermeesch2006EuLuSr,
    Vermeesch2006NaNbSr,
    Vermeesch2006SiTiSr,
    Vermeesch2006SmTiV,
    Vermeesch2006VTiSc,
    Wood1980ThHfTa,
)
from .templates.martin1986 import Martin1986LaYbN
from .templates.drummond_defant1990 import DrummondDefant1990LaYbN
from .templates.verma_multidim import (
    Agrawal2004,
    Agrawal2008,
    Verma2006,
    Verma2012Acid,
    Verma2013AcidImMt,
    Verma2013AcidMajor,
    Verma2013AcidTrace,
    VermaAgrawal2011,
    VermaVerma2013ImMint,
    VermaVerma2013Major,
    VermaVerma2013Trace,
)


_REGISTRY: Dict[str, object] = {
    cls.key: cls()
    for cls in (
        # ----- Classification -------------------------------------------------
        TASVolcanic, TASPlutonic, K2OvsSiO2, AlkalicSubAlkalicBoundary,
        AFM, Jensen, HanskiHighMg, HighMgTAS, Hastie2007ThCo,
        WinchesterFloyd1977,
        BarkerAnAbOr, Frost, Haplogranite, ManiarPiccolli1989,
        # ----- Tectonic — bivariate ------------------------------------------
        Pearce2008ThYbNbYb, Pearce2008TiYbNbYb, PearceGale1977,
        Shervais1982TiV, PearceCann1973ZrTi,
        Saccani2015NbTh, Saccani2015DyYb, Saccani2015CeDyYb,
        DefantDrummondYSrY, DrummondDefant1990LaYbN, Martin1986LaYbN,
        Pearce1984YbTa, Pearce1984YNb, Pearce1984YbTaRb, Pearce1984YNbRb,
        Yang2019FCMS, Yang2019FCKANTMS,
        Li2025NbYbThNb, Godang2024NbZrThNb,
        # ----- Tectonic — ternary --------------------------------------------
        Wood1980ThHfTa, CabanisLecolle1989,
        Vermeesch2006NaNbSr, Vermeesch2006SiTiSr, Vermeesch2006EuLuSr,
        Vermeesch2006VTiSc, Vermeesch2006SmTiV,
        Harris1986HfRbTa,
        # ----- Tectonic — single-axis DFs ------------------------------------
        Pearce1976DF, ButlerWoronowDF,
        # ----- Tectonic — Verma multidimensional -----------------------------
        Agrawal2004, Verma2006, Agrawal2008, VermaAgrawal2011,
        VermaVerma2013Major, VermaVerma2013ImMint, VermaVerma2013Trace,
        Verma2012Acid,
        Verma2013AcidMajor, Verma2013AcidImMt, Verma2013AcidTrace,
        # ----- Petrography — IUGS modal ternaries ----------------------------
        StreckeisenQAPFPlutonic, StreckeisenQAPFVolcanic,
        GabbroPlPxOl, UltramaficOlOpxCpx, TuffSchmid1981,
        PyroclasticFisher1966,
    )
}


def get_diagram(key: str):
    return _REGISTRY.get(key)


def has_diagram(key: str) -> bool:
    return key in _REGISTRY
