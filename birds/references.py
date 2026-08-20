"""APA-7 bibliography for every diagram, normalisation, algorithm and
process implemented in B.I.R.D.S.

Each entry is a plain Python tuple ``(citation, used_for)`` so the
References dialog can render the citation and a one-line "Used for…"
hint next to it.  Citations follow APA 7th-edition rules:

* Journal articles  — Author(s) (Year). Title. *Journal*, *Vol*(Issue),
                       pages. DOI if available.
* Book / chapter    — Author(s) (Year). *Book title* (Edition). Publisher.

Sections are kept in display order (the order that makes sense in the
GUI menu structure, not alphabetical).  Edit / add references here; the
dialog picks the changes up automatically.
"""

from __future__ import annotations

from typing import List, Tuple

# Each section is (section_title, [(citation, used_for), ...])
Section = Tuple[str, List[Tuple[str, str]]]


REFERENCES: List[Section] = [
    # ----------------------------------------------------------------------
    ("Foundational textbooks", [
        ("Rollinson, H., & Pease, V. (2021). *Using geochemical data: To "
         "understand geological processes* (2nd ed.). Cambridge University "
         "Press. https://doi.org/10.1017/9781108777834",
         "General methodology, Chs. 2-6, 11-13."),
        ("Verma, S. P. (2021). *Road to geochemistry: Multidimensional "
         "data analysis*. Elsevier. https://doi.org/10.1016/C2019-0-04415-4",
         "Aitchison log-ratios, multidim. DF diagrams (Ch. 12-13)."),
        ("Aitchison, J. (1986). *The statistical analysis of compositional "
         "data*. Chapman and Hall.",
         "Theoretical basis for alr/clr log-ratio transforms."),
    ]),
    # ----------------------------------------------------------------------
    ("Classification diagrams", [
        ("Le Bas, M. J., Le Maitre, R. W., Streckeisen, A., & Zanettin, B. "
         "(1986). A chemical classification of volcanic rocks based on the "
         "total alkali-silica diagram. *Journal of Petrology*, *27*(3), "
         "745-750. https://doi.org/10.1093/petrology/27.3.745",
         "TAS volcanic diagram."),
        ("Le Maitre, R. W. (Ed.) (2002). *Igneous rocks: A classification "
         "and glossary of terms* (2nd ed.). Cambridge University Press.",
         "TAS plutonic, QAPF, IUGS recommendations."),
        ("Middlemost, E. A. K. (1985). *Magmas and magmatic rocks*. "
         "Longman.",
         "K2O-SiO2 fields (low/medium/high-K series)."),
        ("Peccerillo, A., & Taylor, S. R. (1976). Geochemistry of Eocene "
         "calc-alkaline volcanic rocks from the Kastamonu area, northern "
         "Turkey. *Contributions to Mineralogy and Petrology*, *58*(1), "
         "63-81. https://doi.org/10.1007/BF00384745",
         "K2O-SiO2 calc-alkaline / shoshonite series."),
        ("Irvine, T. N., & Baragar, W. R. A. (1971). A guide to the "
         "chemical classification of the common volcanic rocks. *Canadian "
         "Journal of Earth Sciences*, *8*(5), 523-548. "
         "https://doi.org/10.1139/e71-055",
         "Alkaline / sub-alkaline boundary; AFM diagram."),
        ("Kuno, H. (1968). Differentiation of basalt magmas. In H. H. Hess "
         "& A. Poldervaart (Eds.), *Basalts: The Poldervaart treatise on "
         "rocks of basaltic composition* (Vol. 2, pp. 623-688). Wiley.",
         "AFM tholeiitic-calc-alkaline boundary (Kuno line)."),
        ("Jensen, L. S. (1976). *A new cation plot for classifying "
         "sub-alkalic volcanic rocks* (Misc. Pap. No. 66). Ontario "
         "Division of Mines.",
         "Jensen cation plot."),
        ("Frost, B. R., Barnes, C. G., Collins, W. J., Arculus, R. J., "
         "Ellis, D. J., & Frost, C. D. (2001). A geochemical "
         "classification for granitic rocks. *Journal of Petrology*, "
         "*42*(11), 2033-2048. https://doi.org/10.1093/petrology/42.11.2033",
         "Frost et al. 4-panel granite classification."),
        ("Hanski, E., Walker, R. J., Huhma, H., & Suominen, I. (2001). "
         "The Os and Nd isotopic systematics of c. 2.44 Ga Akanvaara "
         "and Koitelainen mafic layered intrusions in northern Finland. "
         "*Precambrian Research*, *109*(1-2), 73-102.",
         "Hanski high-Mg projection."),
        ("Hastie, A. R., Kerr, A. C., Pearce, J. A., & Mitchell, S. F. "
         "(2007). Classification of altered volcanic island arc rocks "
         "using immobile trace elements: Development of the Th-Co "
         "discrimination diagram. *Journal of Petrology*, *48*(12), "
         "2341-2357. https://doi.org/10.1093/petrology/egm062",
         "Th-Co classification for altered arc rocks."),
        ("Ishikawa, Y., Sawaguchi, T., Iwaya, S., & Horiuchi, M. (1976). "
         "Delineation of prospecting targets for Kuroko deposits based "
         "on modes of volcanism of underlying dacite and alteration "
         "haloes. *Mining Geology*, *26*, 105-117.",
         "Alteration Index (AI) for hydrothermal alteration."),
        ("Winchester, J. A., & Floyd, P. A. (1977). Geochemical "
         "discrimination of different magma series and their "
         "differentiation products using immobile elements. *Chemical "
         "Geology*, *20*, 325-343. "
         "https://doi.org/10.1016/0009-2541(77)90057-2",
         "Zr/TiO2-Nb/Y classification of altered volcanic rocks."),
        ("Nesbitt, H. W., & Young, G. M. (1982). Early Proterozoic "
         "climates and plate motions inferred from major element "
         "chemistry of lutites. *Nature*, *299*(5885), 715-717. "
         "https://doi.org/10.1038/299715a0",
         "Chemical Index of Alteration (CIA)."),
        ("Le Bas, M. J. (2000). IUGS reclassification of the high-Mg and "
         "picritic volcanic rocks. *Journal of Petrology*, *41*(10), "
         "1467-1470. https://doi.org/10.1093/petrology/41.10.1467",
         "High-Mg TAS variant."),
        ("Barker, F. (1979). Trondhjemite: Definition, environment and "
         "hypotheses of origin. In F. Barker (Ed.), *Trondhjemites, "
         "dacites, and related rocks* (pp. 1-12). Elsevier.",
         "Barker An-Ab-Or trondhjemite ternary."),
        ("O'Connor, J. T. (1965). A classification for quartz-rich igneous "
         "rocks based on feldspar ratios. *U.S. Geological Survey "
         "Professional Paper*, *525-B*, 79-84.",
         "Original An-Ab-Or fields modified by Barker (1979)."),
        ("Tuttle, O. F., & Bowen, N. L. (1958). *Origin of granite in the "
         "light of experimental studies in the system NaAlSi3O8-KAlSi3O8-"
         "SiO2-H2O* (Memoir 74). Geological Society of America.",
         "Haplogranite Ab-Or-Q diagram."),
        ("Johannes, W., & Holtz, F. (1996). *Petrogenesis and experimental "
         "petrology of granitic rocks*. Springer.",
         "Updated cotectic curves on Ab-Or-Q."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — bivariate", [
        ("Pearce, J. A. (2008). Geochemical fingerprinting of oceanic "
         "basalts with applications to ophiolite classification and the "
         "search for Archean oceanic crust. *Lithos*, *100*(1-4), 14-48. "
         "https://doi.org/10.1016/j.lithos.2007.06.016",
         "Th/Yb-Nb/Yb, Ti/Yb-Nb/Yb arrays."),
        ("Pearce, J. A., & Cann, J. R. (1973). Tectonic setting of basic "
         "volcanic rocks determined using trace element analyses. *Earth "
         "and Planetary Science Letters*, *19*(2), 290-300.",
         "Original Zr-Ti tectonic diagram."),
        ("Pearce, J. A., & Gale, G. H. (1977). Identification of "
         "ore-deposition environment from trace element geochemistry. "
         "*Geological Society Special Publication*, *7*, 14-24.",
         "Zr/Y vs Ti/Y."),
        ("Shervais, J. W. (1982). Ti-V plots and the petrogenesis of "
         "modern and ophiolitic lavas. *Earth and Planetary Science "
         "Letters*, *59*(1), 101-118. "
         "https://doi.org/10.1016/0012-821X(82)90120-0",
         "Ti-V."),
        ("Saccani, E. (2015). A new method of discriminating different "
         "types of post-Archean ophiolitic basalts and their tectonic "
         "significance using Th-Nb and Ce-Dy-Yb systematics. "
         "*Geoscience Frontiers*, *6*(4), 481-501.",
         "Nb-Th, Dy-Yb, Ce/Yb-Dy/Yb."),
        ("Defant, M. J., & Drummond, M. S. (1990). Derivation of some "
         "modern arc magmas by melting of young subducted lithosphere. "
         "*Nature*, *347*(6294), 662-665. "
         "https://doi.org/10.1038/347662a0",
         "Adakite Y-Sr/Y and Yb-La/Yb."),
        ("Pearce, J. A., Harris, N. B. W., & Tindle, A. G. (1984). Trace "
         "element discrimination diagrams for the tectonic interpretation "
         "of granitic rocks. *Journal of Petrology*, *25*(4), 956-983. "
         "https://doi.org/10.1093/petrology/25.4.956",
         "Yb-Ta, Y-Nb, (Yb+Ta)-Rb, (Y+Nb)-Rb."),
        ("Yang, S.-Y., Jiang, S.-Y., Zhao, K.-D., Dai, B.-Z., & Yang, T. "
         "(2019). Re-evaluating geochemical and isotopic indicators of "
         "magma source: FCKANTMS proxy. *Lithos*, *342-343*, 484-497.",
         "FCKANTMS source proxy."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — ternary", [
        ("Wood, D. A. (1980). The application of a Th-Hf-Ta diagram to "
         "problems of tectonomagmatic classification and to establishing "
         "the nature of crustal contamination of basaltic lavas of the "
         "British Tertiary volcanic province. *Earth and Planetary Science "
         "Letters*, *50*(1), 11-30.",
         "Th-Hf/3-Ta ternary."),
        ("Cabanis, B., & Lecolle, M. (1989). Le diagramme La/10-Y/15-Nb/8: "
         "Un outil pour la discrimination des séries volcaniques et la "
         "mise en évidence des processus de mélange et/ou de "
         "contamination crustale. *Comptes Rendus de l'Académie des "
         "Sciences, Série II*, *309*(20), 2023-2029.",
         "La/10-Y/15-Nb/8 ternary."),
        ("Vermeesch, P. (2006a). Tectonic discrimination diagrams "
         "revisited. *Geochemistry, Geophysics, Geosystems*, *7*(6). "
         "https://doi.org/10.1029/2005GC001092",
         "Multiple ternaries (Na-Nb-Sr, Si-Ti-Sr, Eu-Lu-Sr, V-Ti-Sc, "
         "Sm-Ti-V)."),
        ("Harris, N. B. W., Pearce, J. A., & Tindle, A. G. (1986). "
         "Geochemical characteristics of collision-zone magmatism. "
         "*Geological Society, London, Special Publications*, *19*(1), "
         "67-81.",
         "Hf-Rb/10-3Ta collision-zone ternary."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — multidimensional (single-axis DF)", [
        ("Pearce, J. A. (1976). Statistical analysis of major element "
         "patterns in basalts. *Journal of Petrology*, *17*(1), 15-43.",
         "Pearce 1976 majors-only DF."),
        ("Butler, J. C., & Woronow, A. (1986). Discrimination among "
         "tectonic settings using trace element abundances of basalts. "
         "*Journal of Geophysical Research: Solid Earth*, *91*(B10), "
         "10289-10300.",
         "TiO2-Zr-Y-Sr single-axis DF (re-cast by Vermeesch 2006)."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — multidimensional (Verma & co-authors)", [
        ("Verma, S. P., & Agrawal, S. (2011). New tectonic discrimination "
         "diagrams for basic and ultrabasic volcanic rocks through "
         "log-transformed ratios of high field strength elements and "
         "implications for petrogenetic processes. *Journal of the "
         "Geological Society of India*, *79*(5), 519-525. "
         "https://doi.org/10.1007/s12594-012-0064-5",
         "5-panel Nb-V-Y-Zr/TiO2 DF set for basic + ultrabasic rocks."),
        ("Verma, S. K., Pandarinath, K., & Rivera-Gómez, M. A. (2012). "
         "Statistical evaluation of tectonomagmatic discrimination "
         "diagrams for granitic rocks and proposal of new "
         "discriminant-function-based multi-dimensional diagrams for acid "
         "magmas. *International Geology Review*, *54*(3), 325-347. "
         "https://doi.org/10.1080/00206814.2010.543783",
         "5-panel DF for acid rocks (Eqs 1-10)."),
        ("Verma, S. K., & Verma, S. P. (2013). Identification of "
         "paleotectonic settings of intermediate magmas through "
         "discriminant-function diagrams based on log-ratio "
         "transformations of major-element and immobile element "
         "compositions. *Turkish Journal of Earth Sciences*, *22*(6), "
         "931-948.",
         "5+5+5-panel DF for intermediate rocks (majors, immobile+trace, "
         "trace)."),
        ("Verma, S. P., Pandarinath, K., Verma, S. K., & Agrawal, S. "
         "(2015). Fifteen new discriminant-function-based multi-"
         "dimensional robust diagrams for acid rocks and their "
         "application to Precambrian rocks. *Lithos*, *216-217*, 80-94.",
         "MOR vs Ocean-Plateau single-axis DF (Verma et al. 2015a)."),
        ("Verma, S. P. (2015). Origin, evolution, and tectonic setting of "
         "the eastern part of the Mexican Volcanic Belt and comparison "
         "with the Central American Volcanic Arc from conventional "
         "multielement normalised and multi-dimensional discrimination "
         "diagrams and discordancy and significance tests. *Turkish "
         "Journal of Earth Sciences*, *24*(2), 111-164.",
         "Nb/Nb*, Ta/Ta* canonical anomaly equations (Verma 2015b)."),
        ("Verma, S. P., Rivera-Gómez, M. A., Díaz-González, L., "
         "Quiroz-Ruiz, A., Pandarinath, K., Amezcua-Valdez, A., "
         "Rosales-Rivera, M., Verma, S. K., Tapia-Crespo, L. M., "
         "Torres-Sánchez, D., Cruz-Huicochea, R., & Velasco-Tapia, F. "
         "(2016). Statistical evaluation of conventional and new "
         "discriminant-function diagrams for the classification of high-Mg "
         "rocks. *Lithos*, *264*, 250-263.",
         "Komatiite / Meimechite / Picrite / Boninite multidim."),
        ("Verma, S. P., Verma, S. K., Pandarinath, K., & Rivera-Gómez, M. "
         "A. (2017). UBIA: New discriminant-function-based "
         "multidimensional diagrams to classify intermediate, basic, "
         "ultrabasic and acid igneous rocks. *Geological Journal*, "
         "*52*(5), 815-833.",
         "Ultrabasic / Basic / Intermediate / Acid classification."),
        ("Verma, S. P., Torres-Alvarado, I. S., & Sotelo-Rodríguez, Z. T. "
         "(2002). SINCLAS: Standard igneous norm and volcanic rock "
         "classification system. *Computers & Geosciences*, *28*(5), "
         "711-715.",
         "SINCLAS pre-processor for Fe-oxidation adjustment."),
    ]),
    # ----------------------------------------------------------------------
    ("Petrography (IUGS)", [
        ("Streckeisen, A. (1976). To each plutonic rock its proper name. "
         "*Earth-Science Reviews*, *12*(1), 1-33. "
         "https://doi.org/10.1016/0012-8252(76)90052-0",
         "QAPF plutonic / volcanic."),
        ("Streckeisen, A. (1979). Classification and nomenclature of "
         "volcanic rocks, lamprophyres, carbonatites, and melilitic "
         "rocks: Recommendations and suggestions of the IUGS "
         "Subcommission on the Systematics of Igneous Rocks. *Geology*, "
         "*7*(7), 331-335.",
         "QAPF volcanic update."),
        ("Schmid, R. (1981). Descriptive nomenclature and classification "
         "of pyroclastic deposits and fragments: Recommendations of the "
         "IUGS Subcommission on the Systematics of Igneous Rocks. "
         "*Geology*, *9*(1), 41-43.",
         "Tuff classification (crystal/vitric/lithic ternary)."),
    ]),
    # ----------------------------------------------------------------------
    ("Spider diagrams & geochemical normalisations", [
        ("Sun, S.-s., & McDonough, W. F. (1989). Chemical and isotopic "
         "systematics of oceanic basalts: Implications for mantle "
         "composition and processes. In A. D. Saunders & M. J. Norry "
         "(Eds.), *Magmatism in the ocean basins* (Geological Society "
         "Special Publication No. 42, pp. 313-345). Geological Society "
         "of London.",
         "Primitive Mantle, N-MORB, E-MORB, OIB reference values."),
        ("McDonough, W. F., & Sun, S.-s. (1995). The composition of the "
         "Earth. *Chemical Geology*, *120*(3-4), 223-253. "
         "https://doi.org/10.1016/0009-2541(94)00140-4",
         "CI Chondrite multi-element reference."),
        ("Boynton, W. V. (1984). Cosmochemistry of the rare earth "
         "elements: Meteorite studies. In P. Henderson (Ed.), *Rare "
         "earth element geochemistry* (pp. 63-114). Elsevier.",
         "REE chondrite normalisation."),
        ("Anders, E., & Grevesse, N. (1989). Abundances of the elements: "
         "Meteoritic and solar. *Geochimica et Cosmochimica Acta*, "
         "*53*(1), 197-214. https://doi.org/10.1016/0016-7037(89)90286-X",
         "CI chondrite reference (REE)."),
        ("Taylor, S. R., & McLennan, S. M. (1985). *The continental crust: "
         "Its composition and evolution*. Blackwell.",
         "NASC, post-Archean shale normalisations."),
        ("Gromet, L. P., Dymek, R. F., Haskin, L. A., & Korotev, R. L. "
         "(1984). The 'North American shale composite': Its compilation, "
         "major and trace element characteristics. *Geochimica et "
         "Cosmochimica Acta*, *48*(12), 2469-2482.",
         "NASC reference."),
        ("Nakamura, N. (1974). Determination of REE, Ba, Fe, Mg, Na and "
         "K in carbonaceous and ordinary chondrites. *Geochimica et "
         "Cosmochimica Acta*, *38*(5), 757-775.",
         "Early chondrite REE normalisation (still used)."),
    ]),
    # ----------------------------------------------------------------------
    ("Statistics & anomalies", [
        ("Eu/Eu*: Boynton, W. V. (1984), Henderson, P. (Ed.) (1984). "
         "*Rare earth element geochemistry*. Elsevier.",
         "Eu/Eu* = Eu_N / sqrt(Sm_N · Gd_N)."),
        ("Ce/Ce*: Wright, J., Schrader, H., & Holser, W. T. (1987). "
         "Paleoredox variations in ancient oceans recorded by REEs in "
         "fossil apatite. *Geochimica et Cosmochimica Acta*, *51*(3), "
         "631-644.",
         "Ce/Ce* = Ce_N / sqrt(La_N · Pr_N)."),
        ("Nb/Nb*, Ta/Ta* (Pearce 2008): Pearce, J. A. (2008). Geochemical "
         "fingerprinting of oceanic basalts. *Lithos*, *100*, 14-48.",
         "Nb/Nb* = Nb_N / sqrt(Th_N · La_N) — see citation above."),
        ("Verma 2015 anomalies (Nb/Nb*_V, Ta/Ta*_V): Verma, S. P. (2015). "
         "Origin, evolution, and tectonic setting of the eastern part of "
         "the Mexican Volcanic Belt... *Turkish Journal of Earth "
         "Sciences*, *24*(2), 111-164.",
         "Alternative: 2·Nb_N / (Ba_N + La_N) and 2·Ta_N / (Ba_N + La_N)."),
        ("Dy/Dy* (HREE): Davidson, J., Turner, S., & Plank, T. (2013). "
         "Dy/Dy*: Variations arising from mantle sources and "
         "petrogenetic processes. *Journal of Petrology*, *54*(3), "
         "525-537. https://doi.org/10.1093/petrology/egs076",
         "Dy/Dy* = Dy_N / (La_N^(4/13) · Yb_N^(9/13))."),
        ("Ti/Ti*, ratios Zr/Hf, Nb/Ta, Dy/Y, Dy/Yb: Rollinson & Pease "
         "(2021), Ch. 4. See also Münker et al. (2003), *Science*, "
         "*301*, 84-87 (Nb/Ta).",
         "Standard trace-element ratios."),
    ]),
    # ----------------------------------------------------------------------
    ("CIPW normative mineralogy", [
        ("Cross, W., Iddings, J. P., Pirsson, L. V., & Washington, H. S. "
         "(1903). A quantitative chemico-mineralogical classification "
         "and nomenclature of igneous rocks. *Journal of Geology*, "
         "*11*(6), 555-690.",
         "Original CIPW algorithm."),
        ("Kelsey, C. H. (1965). Calculation of the CIPW norm. "
         "*Mineralogical Magazine*, *34*(268), 276-282.",
         "Classical CIPW computational recipe."),
        ("Hutchison, C. S. (1974). Laboratory handbook of petrographic "
         "techniques. Wiley.",
         "Hutchison CIPW variant."),
        ("Verma, S. P., Torres-Alvarado, I. S., & Sotelo-Rodríguez, Z. T. "
         "(2002). SINCLAS: Standard igneous norm and volcanic rock "
         "classification system. *Computers & Geosciences*, *28*(5), "
         "711-715.",
         "SINCLAS CIPW + Fe-oxidation adjustment."),
        ("Verma, S. P., & Rivera-Gómez, M. A. (2013). Computer program "
         "for the classification and nomenclature of igneous rocks. "
         "*Episodes*, *36*(2), 115-124.",
         "Updated CIPW (lite variant in BIRDS)."),
    ]),
    # ----------------------------------------------------------------------
    ("Pre-process / Fe partition", [
        ("Middlemost, E. A. K. (1989). Iron oxidation ratios, norms and "
         "the classification of volcanic rocks. *Chemical Geology*, "
         "*77*(1), 19-26.",
         "Middlemost Fe2O3/FeO partition by rock type."),
        ("Le Maitre, R. W. (1976). Some problems of the projection of "
         "chemical data into mineralogical classifications. "
         "*Contributions to Mineralogy and Petrology*, *56*(2), 181-189.",
         "Le Maitre Fe-oxidation correction."),
    ]),
    # ----------------------------------------------------------------------
    ("Map / Coordinate reference systems", [
        ("Snyder, J. P. (1987). *Map projections — A working manual* "
         "(Professional Paper 1395). U.S. Geological Survey.",
         "UTM forward / inverse formulas (Snyder series)."),
        ("National Geospatial-Intelligence Agency. (2014). *World "
         "Geodetic System 1984 (WGS-84): Its definition and "
         "relationships with local geodetic systems* (NGA.STND.0036_1.0.0_"
         "WGS84). NGA Office of Geomatics.",
         "WGS-84 datum (EPSG:4326), used for all map coordinates."),
        ("OGC. (2007). *OGC web map service — implementation specification "
         "WMS 1.3.0*. Open Geospatial Consortium.",
         "EPSG:3857 (Web Mercator) used for basemap rendering."),
        ("Defense Mapping Agency. (1990). *The universal grids: Universal "
         "Transverse Mercator (UTM) and Universal Polar Stereographic "
         "(UPS)* (TM 8358.2). Department of Defense.",
         "MGRS grid-reference convention."),
    ]),
    # ----------------------------------------------------------------------
    ("Software & libraries used by B.I.R.D.S", [
        ("Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. "
         "*Computing in Science & Engineering*, *9*(3), 90-95. "
         "https://doi.org/10.1109/MCSE.2007.55",
         "Plot rendering."),
        ("McKinney, W. (2010). Data structures for statistical computing "
         "in Python. *Proceedings of the 9th Python in Science "
         "Conference*, 56-61.",
         "pandas — DataFrame operations."),
        ("Harris, C. R., Millman, K. J., van der Walt, S. J., et al. "
         "(2020). Array programming with NumPy. *Nature*, *585*, "
         "357-362. https://doi.org/10.1038/s41586-020-2649-2",
         "NumPy — numerical arrays."),
        ("Virtanen, P., Gommers, R., Oliphant, T. E., et al. (2020). "
         "SciPy 1.0: Fundamental algorithms for scientific computing in "
         "Python. *Nature Methods*, *17*, 261-272.",
         "scipy.spatial.ConvexHull for shaded group envelopes."),
        ("The Qt Company. (2024). *Qt for Python (PySide6) documentation*. "
         "https://doi.org/10.5281/zenodo.7891302",
         "GUI framework."),
        ("Whitaker, J. (2024). *pyproj: Python interface to PROJ*. "
         "https://pyproj4.github.io/pyproj/",
         "Coordinate-system transforms (UTM, Web-Mercator)."),
    ]),
]


def all_references() -> List[Section]:
    """Return the complete bibliography for the References dialog."""
    return REFERENCES


def total_count() -> int:
    """Number of individual references across all sections."""
    return sum(len(items) for _, items in REFERENCES)
