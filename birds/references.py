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
        ("Verma, S. P. (2020). *Road from geochemistry to "
         "geochemometrics*. Springer Nature Singapore. "
         "https://doi.org/10.1007/978-981-13-9278-8",
         "Log-ratio techniques for compositional data (Ch. 11); "
         "multidimensional tectonic discrimination diagrams (Ch. 12)."),
        ("Aitchison, J. (1986). *The statistical analysis of "
         "compositional data*. Chapman and Hall. "
         "https://doi.org/10.1007/978-94-009-4109-0",
         "Theoretical basis for alr/clr log-ratio transforms."),
    ]),
    # ----------------------------------------------------------------------
    ("Classification diagrams", [
        ("Le Bas, M. J., Le Maitre, R. W., Streckeisen, A., & Zanettin, B. "
         "(1986). A chemical classification of volcanic rocks based on the "
         "total alkali-silica diagram. *Journal of Petrology*, *27*(3), "
         "745-750. https://doi.org/10.1093/petrology/27.3.745",
         "TAS volcanic diagram."),
        ("Le Maitre, R. W. (Ed.) (2002). *Igneous rocks: A "
         "classification and glossary of terms* (2nd ed.). Cambridge "
         "University Press. https://doi.org/10.1017/CBO9780511535581",
         "TAS plutonic, QAPF, IUGS recommendations."),
        ("Le Maitre, R. W. (Ed.) (1989). *A classification of igneous "
         "rocks and glossary of terms*. Blackwell.",
         "The low-, medium- and high-K lines of the K2O-SiO2 diagram."),
        ("Middlemost, E. A. K. (1985). *Magmas and magmatic rocks*. "
         "Longman.",
         "K2O-SiO2 fields (low/medium/high-K series)."),
        ("Middlemost, E. A. K. (1994). Naming materials in the "
         "magma/igneous rock system. *Earth-Science Reviews*, *37*(3-4),"
         " 215-224. https://doi.org/10.1016/0012-8252(94)90029-9",
         "TAS plutonic diagram and its rock naming."),
        ("Maniar, P. D., & Piccoli, P. M. (1989). Tectonic "
         "discrimination of granitoids. *Geological Society of America "
         "Bulletin*, *101*(5), 635-643. "
         "https://doi.org/10.1130/0016-7606(1989)101<0635:TDOG>2.3.CO;2",
         "A/CNK vs A/NK aluminium-saturation diagram."),
        ("Shand, S. J. (1943). *Eruptive rocks: Their genesis, "
         "composition, classification, and their relation to "
         "ore-deposits* (2nd ed.). John Wiley.",
         "The aluminium-saturation index Maniar & Piccoli plot."),
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
         "rocks of basaltic composition* (Vol. 2, pp. 623-688). "
         "Interscience.",
         "AFM tholeiitic-calc-alkaline boundary (Kuno line)."),
        ("Kuno, H. (1966). Lateral variation of basalt magma type across "
         "continental margins and island arcs. *Bulletin Volcanologique*, "
         "*29*(1), 195-222. https://doi.org/10.1007/BF02597153",
         "One of the alkaline / sub-alkaline lines of the TAS diagram."),
        ("MacDonald, G. A. (1968). Composition and origin of Hawaiian "
         "lavas. In R. R. Coats, R. L. Hay & C. A. Anderson (Eds.), "
         "*Studies in volcanology: A memoir in honor of Howel Williams* "
         "(Geological Society of America Memoir 116, pp. 477-522). "
         "https://doi.org/10.1130/MEM116-p477",
         "One of the alkaline / sub-alkaline lines of the TAS diagram."),
        ("Rickwood, P. C. (1989). Boundary lines within petrologic "
         "diagrams which use oxides of major and minor elements. "
         "*Lithos*, *22*(4), 247-263. "
         "https://doi.org/10.1016/0024-4937(89)90028-5",
         "K2O-SiO2 bands; measured TAS, AFM and Jensen boundary lines."),
        ("Jensen, L. S. (1976). *A new cation plot for classifying "
         "sub-alkalic volcanic rocks* (Misc. Pap. No. 66). Ontario "
         "Division of Mines.",
         "Jensen cation plot."),
        ("Jensen, L. S., & Pyke, D. R. (1982). Komatiites in the Ontario "
         "portion of the Abitibi belt. In N. T. Arndt & E. G. Nisbet "
         "(Eds.), *Komatiites* (pp. 147-157). George Allen and Unwin.",
         "The komatiite fields of the Jensen cation plot."),
        ("Frost, B. R., Barnes, C. G., Collins, W. J., Arculus, R. J., "
         "Ellis, D. J., & Frost, C. D. (2001). A geochemical "
         "classification for granitic rocks. *Journal of Petrology*, "
         "*42*(11), 2033-2048. https://doi.org/10.1093/petrology/42.11.2033",
         "Frost et al. 4-panel granite classification."),
        ("Frost, B. R., & Frost, C. D. (2008). A geochemical "
         "classification for feldspathic igneous rocks. *Journal of "
         "Petrology*, *49*(11), 1955-1969. "
         "https://doi.org/10.1093/petrology/egn054",
         "The FSSI panel and the frames of the Frost diagram."),
        ("Hanski, E., Huhma, H., Rastas, P., & Kamenetsky, V. S. (2001). "
         "The Palaeoproterozoic komatiite-picrite association of Finnish "
         "Lapland. *Journal of Petrology*, *42*(5), 855-876. "
         "https://doi.org/10.1093/petrology/42.5.855",
         "Hanski high-Mg [Al2O3]-[TiO2] diagram."),
        ("Hanski, E. (1992). *Petrology of the Pechenga ferropicrites and "
         "cogenetic, Ni-bearing gabbro-wehrlite intrusions, Kola "
         "Peninsula, Russia* (Bulletin 367). Geological Survey of "
         "Finland.",
         "The olivine projection behind the Hanski diagram."),
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
         "dacites, and related rocks* (pp. 1-12). Elsevier. "
         "https://doi.org/10.1016/B978-0-444-41765-7.50006-X",
         "Barker An-Ab-Or trondhjemite ternary."),
        ("O'Connor, J. T. (1965). A classification for quartz-rich igneous "
         "rocks based on feldspar ratios. *U.S. Geological Survey "
         "Professional Paper*, *525-B*, 79-84.",
         "Original An-Ab-Or fields modified by Barker (1979)."),
        ("Tuttle, O. F., & Bowen, N. L. (1958). *Origin of granite in "
         "the light of experimental studies in the system "
         "NaAlSi3O8-KAlSi3O8-SiO2-H2O* (Memoir 74). Geological Society "
         "of America. https://doi.org/10.1130/MEM74-p1",
         "Haplogranite Ab-Or-Q diagram."),
        ("Johannes, W., & Holtz, F. (1996). *Petrogenesis and "
         "experimental petrology of granitic rocks*. Springer. "
         "https://doi.org/10.1007/978-3-642-61049-3",
         "Updated cotectic curves on Ab-Or-Q."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — bivariate", [
        ("Pearce, J. A. (2008). Geochemical fingerprinting of oceanic "
         "basalts with applications to ophiolite classification and the "
         "search for Archean oceanic crust. *Lithos*, *100*(1-4), 14-48. "
         "https://doi.org/10.1016/j.lithos.2007.06.016",
         "Th/Yb-Nb/Yb, Ti/Yb-Nb/Yb arrays."),
        ("Pearce, J. A., & Cann, J. R. (1973). Tectonic setting of basic"
         " volcanic rocks determined using trace element analyses. "
         "*Earth and Planetary Science Letters*, *19*(2), 290-300. "
         "https://doi.org/10.1016/0012-821X(73)90129-5",
         "Original Zr-Ti tectonic diagram."),
        ("Pearce, J. A., & Gale, G. H. (1977). Identification of "
         "ore-deposition environment from trace-element geochemistry of "
         "associated igneous host rocks. *Geological Society, London, "
         "Special Publications*, *7*(1), 14-24. "
         "https://doi.org/10.1144/GSL.SP.1977.007.01.03",
         "Zr/Y vs Ti/Y."),
        ("Shervais, J. W. (1982). Ti-V plots and the petrogenesis of "
         "modern and ophiolitic lavas. *Earth and Planetary Science "
         "Letters*, *59*(1), 101-118. "
         "https://doi.org/10.1016/0012-821X(82)90120-0",
         "Ti-V."),
        ("Saccani, E. (2015). A new method of discriminating different "
         "types of post-Archean ophiolitic basalts and their tectonic "
         "significance using Th-Nb and Ce-Dy-Yb systematics. *Geoscience"
         " Frontiers*, *6*(4), 481-501. "
         "https://doi.org/10.1016/j.gsf.2014.03.006",
         "Nb-Th, Dy-Yb, Ce/Yb-Dy/Yb."),
        ("Defant, M. J., & Drummond, M. S. (1990). Derivation of some "
         "modern arc magmas by melting of young subducted lithosphere. "
         "*Nature*, *347*(6294), 662-665. "
         "https://doi.org/10.1038/347662a0",
         "Adakite Y-Sr/Y, and the Yb <= 1.9 ppm limit."),
        ("Drummond, M. S., & Defant, M. J. (1990). A model for "
         "trondhjemite-tonalite-dacite genesis and crustal growth via "
         "slab melting: Archean to modern comparisons. *Journal of "
         "Geophysical Research: Solid Earth*, *95*(B13), 21503-21521. "
         "https://doi.org/10.1029/JB095iB13p21503",
         "(La/Yb)N-YbN, Figure 10: Archean TTG, post-Archean granitic "
         "rocks, MORB."),
        ("Martin, H. (1986). Effect of steeper Archean geothermal "
         "gradient on geochemistry of subduction-zone magmas. *Geology*,"
         " *14*(9), 753-756. "
         "https://doi.org/10.1130/0091-7613(1986)14<753:EOSAGG>2.0.CO;2",
         "(La/Yb)N-YbN: Archean TTG against post-Archean granitoids."),
        ("Jahn, B.-M., Glikson, A. Y., Peucat, J. J., & Hickman, A. H. "
         "(1981). REE geochemistry and isotopic data of Archean silicic "
         "volcanics and granitoids from the Pilbara Block, Western "
         "Australia: Implications for the early crustal evolution. "
         "*Geochimica et Cosmochimica Acta*, *45*(9), 1633-1652. "
         "https://doi.org/10.1016/S0016-7037(81)80002-6",
         "With Martin (1986), what Drummond & Defant's Figure 10 is "
         "drawn after."),
        ("Pearce, J. A., Harris, N. B. W., & Tindle, A. G. (1984). Trace "
         "element discrimination diagrams for the tectonic interpretation "
         "of granitic rocks. *Journal of Petrology*, *25*(4), 956-983. "
         "https://doi.org/10.1093/petrology/25.4.956",
         "Yb-Ta, Y-Nb, (Yb+Ta)-Rb, (Y+Nb)-Rb."),
        ("Yang, Z.-F., Li, J., Jiang, Q.-B., Xu, F., Guo, S.-Y., Li, Y., & "
         "Zhang, J. (2019). Using major element logratios to recognize "
         "compositional patterns of basalt: Implications for source "
         "lithological and compositional heterogeneities. *Journal of "
         "Geophysical Research: Solid Earth*, *124*(4), 3458-3490. "
         "https://doi.org/10.1029/2018JB016145",
         "FCMS and FCKANTMS source proxies."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — Th-Nb-Yb and Th-Nb-Zr (Li, Godang et al.)", [
        ("Li, H., Godang, S., & Saputro, S. P. (2025). Revealing "
         "unmapped tectonic settings through geochemical "
         "fingerprinting of Th-Nb-Yb. *Lithosphere*, *2025*(2), "
         "lithosphere_2025_125. "
         "https://doi.org/10.2113/2025/lithosphere_2025_125",
         "Nb/Yb vs Th/Nb, nine tectonic settings, mafic to felsic."),
        ("Godang, S., Saputro, S. P., & Li, H. (2024). The slab failure "
         "in Central Java (Indonesia): New insight into its tectonic "
         "setting and origin. *Solid Earth Sciences*, *9*(3), 100199. "
         "https://doi.org/10.1016/j.sesci.2024.100199",
         "Nb/Zr vs Th/Nb, as drawn in Li et al. (2025) Figure 5."),
        ("Saputro, S. P., Godang, S., Priadi, B., Basuki, N. I., & "
         "Himawan, B. (2022). Geochemical study of Al-Fe-Ti enrichment "
         "in rock weathering: Implications for the recognizing of "
         "igneous protolith and the enrichment of REE in soil profile. "
         "*Applied Geochemistry*, *140*, 105259. "
         "https://doi.org/10.1016/j.apgeochem.2022.105259",
         "Nb/Zr vs Th/Nb: the rift field and its La/Yb = 20."),
        ("Sun, S. Q., Zhang, C. J., & Huang, R. Q. (2006). The tectonic "
         "settings discrimination of the basalts in the convergent "
         "margin of plate by Th, Nb, and Zr. *Advances in Earth "
         "Science*, *21*(6), 593-598.",
         "Nb/Zr vs Th/Nb: Nb/Zr = 0.15, mantle plume basalts."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — ternary", [
        ("Wood, D. A. (1980). The application of a Th-Hf-Ta diagram to "
         "problems of tectonomagmatic classification and to establishing"
         " the nature of crustal contamination of basaltic lavas of the "
         "British Tertiary volcanic province. *Earth and Planetary "
         "Science Letters*, *50*(1), 11-30. "
         "https://doi.org/10.1016/0012-821X(80)90116-8",
         "Th-Hf/3-Ta ternary."),
        ("Cabanis, B., & Lecolle, M. (1989). Le diagramme La/10-Y/15-Nb/8: "
         "Un outil pour la discrimination des séries volcaniques et la "
         "mise en évidence des processus de mélange et/ou de "
         "contamination crustale. *Comptes Rendus de l'Académie des "
         "Sciences, Série II*, *309*(20), 2023-2029.",
         "La/10-Y/15-Nb/8 ternary."),
        ("Verma, S. P. (2010). Statistical evaluation of bivariate, "
         "ternary and discriminant function tectonomagmatic "
         "discrimination diagrams. *Turkish Journal of Earth Sciences*, "
         "*19*(2), 185-238. https://doi.org/10.3906/yer-0901-6",
         "Success rates of Pearce & Gale (1977) and Cabanis & Lecolle "
         "(1989) on ~4000 analyses."),
        ("Vermeesch, P. (2006a). Tectonic discrimination diagrams "
         "revisited. *Geochemistry, Geophysics, Geosystems*, *7*(6). "
         "https://doi.org/10.1029/2005GC001092",
         "Multiple ternaries (Na-Nb-Sr, Si-Ti-Sr, Eu-Lu-Sr, V-Ti-Sc, "
         "Sm-Ti-V)."),
        ("Harris, N. B. W., Pearce, J. A., & Tindle, A. G. (1986). "
         "Geochemical characteristics of collision-zone magmatism. "
         "*Geological Society, London, Special Publications*, *19*(1), "
         "67-81. https://doi.org/10.1144/GSL.SP.1986.019.01.04",
         "Hf-Rb/10-3Ta collision-zone ternary."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — multidimensional (single-axis DF)", [
        ("Pearce, J. A. (1976). Statistical analysis of major element "
         "patterns in basalts. *Journal of Petrology*, *17*(1), 15-43. "
         "https://doi.org/10.1093/petrology/17.1.15",
         "Pearce 1976 majors-only DF."),
        ("Butler, J. C., & Woronow, A. (1986). Discrimination among "
         "tectonic settings using trace element abundances of basalts. "
         "*Journal of Geophysical Research: Solid Earth*, *91*(B10), "
         "10289-10300. https://doi.org/10.1029/JB091iB10p10289",
         "TiO2-Zr-Y-Sr single-axis DF (re-cast by Vermeesch 2006)."),
    ]),
    # ----------------------------------------------------------------------
    ("Tectonic discrimination — multidimensional (Verma & co-authors)", [
        ("Agrawal, S., Guevara, M., & Verma, S. P. (2004). Discriminant "
         "analysis applied to establish major-element field boundaries "
         "for tectonic varieties of basic rocks. *International Geology "
         "Review*, *46*(7), 575-594. "
         "https://doi.org/10.2747/0020-6814.46.7.575",
         "5-panel DF set on the adjusted major oxides, basic rocks."),
        ("Verma, S. P., Guevara, M., & Agrawal, S. (2006). "
         "Discriminating four tectonic settings: Five new geochemical "
         "diagrams for basic and ultrabasic volcanic rocks based on "
         "log-ratio transformation of major-element data. *Journal of "
         "Earth System Science*, *115*(5), 485-528. "
         "https://doi.org/10.1007/BF02702907",
         "5-panel DF set on ln(oxide/SiO2), basic + ultrabasic rocks."),
        ("Agrawal, S., Guevara, M., & Verma, S. P. (2008). Tectonic "
         "discrimination of basic and ultrabasic volcanic rocks through "
         "log-transformed ratios of immobile trace elements. "
         "*International Geology Review*, *50*(12), 1057-1079. "
         "https://doi.org/10.2747/0020-6814.50.12.1057",
         "5-panel DF set on ln(La, Sm, Yb, Nb / Th), basic + ultrabasic "
         "rocks."),
        ("Verma, S. P., & Agrawal, S. (2011). New tectonic discrimination "
         "diagrams for basic and ultrabasic volcanic rocks through "
         "log-transformed ratios of high field strength elements and "
         "implications for petrogenetic processes. *Revista Mexicana de "
         "Ciencias Geológicas*, *28*(1), 24-44.",
         "5-panel Nb-V-Y-Zr/TiO2 DF set for basic + ultrabasic rocks."),
        ("Verma, S. K., Pandarinath, K., & Verma, S. P. (2012). "
         "Statistical evaluation of tectonomagmatic discrimination "
         "diagrams for granitic rocks and proposal of new "
         "discriminant-function-based multi-dimensional diagrams for acid "
         "rocks. *International Geology Review*, *54*(3), 325-347. "
         "https://doi.org/10.1080/00206814.2010.543784",
         "5-panel DF for acid rocks (Eqs 1-10)."),
        ("Verma, S. P., & Verma, S. K. (2013). First 15 probability-based "
         "multidimensional tectonic discrimination diagrams for "
         "intermediate magmas and their robustness against "
         "postemplacement compositional changes and petrogenetic "
         "processes. *Turkish Journal of Earth Sciences*, *22*(6), "
         "931-995. https://doi.org/10.3906/yer-1204-6",
         "5+5+5-panel DF for intermediate rocks (majors, immobile+trace, "
         "trace)."),
        ("Verma, S. P., Pandarinath, K., Verma, S. K., & Agrawal, S. "
         "(2013). Fifteen new discriminant-function-based multi-"
         "dimensional robust diagrams for acid rocks and their "
         "application to Precambrian rocks. *Lithos*, *168-169*, "
         "113-123. https://doi.org/10.1016/j.lithos.2013.01.014",
         "5+5+5-panel DF for acid rocks (majors, immobile majors + "
         "traces, traces)."),
        ("Verma, S. P. (2015). Origin, evolution, and tectonic setting "
         "of the eastern part of the Mexican Volcanic Belt and "
         "comparison with the Central American Volcanic Arc from "
         "conventional multielement normalised and multi-dimensional "
         "discrimination diagrams and discordancy and significance "
         "tests. *Turkish Journal of Earth Sciences*, *24*(2), 111-164. "
         "https://doi.org/10.3906/yer-1412-31",
         "Nb/Nb*, Ta/Ta* canonical anomaly equations (Verma 2015b)."),
    ]),
    # ----------------------------------------------------------------------
    ("Petrography (IUGS)", [
        ("Streckeisen, A. (1973). Plutonic rocks: Classification and "
         "nomenclature recommended by the IUGS Subcommission on the "
         "Systematics of Igneous Rocks. *Geotimes*, *18*(10), 26-30.",
         "Ultramafic Ol-Opx-Cpx classification."),
        ("Streckeisen, A. (1976). To each plutonic rock its proper name. "
         "*Earth-Science Reviews*, *12*(1), 1-33. "
         "https://doi.org/10.1016/0012-8252(76)90052-0",
         "QAPF plutonic; gabbroic Pl-Px-Ol classification."),
        ("Streckeisen, A. (1978). IUGS Subcommission on the Systematics "
         "of Igneous Rocks. Classification and nomenclature of volcanic "
         "rocks, lamprophyres, carbonatites and melilitic rocks. "
         "*Neues Jahrbuch für Mineralogie, Abhandlungen*, *134*, 1-14.",
         "QAPF volcanic."),
        ("Streckeisen, A. (1979). Classification and nomenclature of "
         "volcanic rocks, lamprophyres, carbonatites, and melilitic "
         "rocks: Recommendations and suggestions of the IUGS "
         "Subcommission on the Systematics of Igneous Rocks. *Geology*, "
         "*7*(7), 331-335. "
         "https://doi.org/10.1130/0091-7613(1979)7<331:CANOVR>2.0.CO;2",
         "QAPF volcanic update."),
        ("Schmid, R. (1981). Descriptive nomenclature and classification"
         " of pyroclastic deposits and fragments: Recommendations of the"
         " IUGS Subcommission on the Systematics of Igneous Rocks. "
         "*Geology*, *9*(1), 41-43. "
         "https://doi.org/10.1130/0091-7613(1981)9<41:DNACOP>2.0.CO;2",
         "Tuff classification: vitric, crystal or lithic by the dominant "
         "component."),
        ("Fisher, R. V. (1966). Rocks composed of volcanic fragments and "
         "their classification. *Earth-Science Reviews*, *1*(4), "
         "287-298. https://doi.org/10.1016/0012-8252(66)90010-9",
         "Pyroclastic rocks by fragment size: blocks and bombs, lapilli, "
         "ash (Figure 1)."),
        ("Gillespie, M. R., & Styles, M. T. (1999). *BGS rock "
         "classification scheme, Volume 1: Classification of igneous "
         "rocks* (2nd ed.; British Geological Survey Research Report RR "
         "99-06). British Geological Survey.",
         "Reproduces the IUGS modal diagrams; every boundary of the "
         "Petrography view was checked against its Figures 7, 11-13, 16 "
         "and 19."),
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
         "CI chondrite and primitive mantle (Tables 2, 4, 5): REE, "
         "multi-element and Ni-Cu-PGE normalisation, mantle reservoir."),
        ("Boynton, W. V. (1984). Cosmochemistry of the rare earth "
         "elements: Meteorite studies. In P. Henderson (Ed.), *Rare "
         "earth element geochemistry* (pp. 63-114). Elsevier. "
         "https://doi.org/10.1016/B978-0-444-42148-7.50008-3",
         "REE chondrite normalisation."),
        ("Anders, E., & Grevesse, N. (1989). Abundances of the elements: "
         "Meteoritic and solar. *Geochimica et Cosmochimica Acta*, "
         "*53*(1), 197-214. https://doi.org/10.1016/0016-7037(89)90286-X",
         "CI chondrite reference (REE)."),
        ("Taylor, S. R., & McLennan, S. M. (1985). *The continental crust: "
         "Its composition and evolution*. Blackwell.",
         "NASC, post-Archean shale normalisations."),
        ("Rudnick, R. L., & Gao, S. (2003). Composition of the continental "
         "crust. In R. L. Rudnick (Ed.), *The crust* (Treatise on "
         "Geochemistry, Vol. 3, pp. 1-64). Elsevier-Pergamon. "
         "https://doi.org/10.1016/B0-08-043751-6/03016-4",
         "Upper, middle, lower and bulk continental crust (Table 11): "
         "normalisers and reservoirs."),
        ("Rudnick, R. L., & Gao, S. (2014). Composition of the continental "
         "crust. In *Treatise on Geochemistry* (2nd ed., Vol. 4, pp. "
         "1-51). Elsevier. "
         "https://doi.org/10.1016/B978-0-08-095975-7.00301-6",
         "The edition Rollinson & Pease cite; its upper crust is the "
         "2003 table's."),
        ("Gromet, L. P., Dymek, R. F., Haskin, L. A., & Korotev, R. L. "
         "(1984). The 'North American shale composite': Its compilation,"
         " major and trace element characteristics. *Geochimica et "
         "Cosmochimica Acta*, *48*(12), 2469-2482. "
         "https://doi.org/10.1016/0016-7037(84)90298-9",
         "NASC reference."),
        ("Becker, H., Horan, M. F., Walker, R. J., Gao, S., Lorand, "
         "J.-P., & Rudnick, R. L. (2006). Highly siderophile element "
         "composition of the Earth's primitive upper mantle: Constraints "
         "from new data on peridotite massifs and xenoliths. *Geochimica "
         "et Cosmochimica Acta*, *70*(17), 4528-4550. "
         "https://doi.org/10.1016/j.gca.2006.06.004",
         "Primitive upper mantle HSE (Os, Ir, Ru, Pt, Pd, Re, Au)."),
        ("Fischer-Gödde, M., Becker, H., & Wombacher, F. (2010). Rhodium, "
         "gold and other highly siderophile element abundances in "
         "chondritic meteorites. *Geochimica et Cosmochimica Acta*, "
         "*74*, 356-379. https://doi.org/10.1016/j.gca.2009.09.024",
         "CI chondrite HSE values (Table 3, mean CI)."),
        ("Fischer-Gödde, M., Becker, H., & Wombacher, F. (2011). Rhodium, "
         "gold and other highly siderophile elements in orogenic "
         "peridotites and peridotite xenoliths. *Chemical Geology*, "
         "*280*, 365-383. "
         "https://doi.org/10.1016/j.chemgeo.2010.11.024",
         "Rh and Au completing the primitive-mantle HSE set."),
        # Pages 5-20 as printed on the paper; Crossref's record gives
        # 27-42, which is not where the article is.
        ("Horan, M. F., Walker, R. J., Morgan, J. W., Grossman, J. N., & "
         "Rubin, A. E. (2003). Highly siderophile elements in chondrites. "
         "*Chemical Geology*, *196*, 5-20. "
         "https://doi.org/10.1016/S0009-2541(02)00405-9",
         "CI chondrite analyses within Fischer-Gödde et al.'s (2010) "
         "mean."),
        ("Salters, V. J. M., & Stracke, A. (2004). Composition of the "
         "depleted mantle. *Geochemistry, Geophysics, Geosystems*, *5*(5), "
         "Q05B07. https://doi.org/10.1029/2003GC000597",
         "Depleted MORB mantle metals (Table 6) for oceanic sulphide "
         "settings."),
        ("Barnes, S.-J., & Ripley, E. M. (2016). Highly siderophile and "
         "strongly chalcophile elements in magmatic ore deposits. "
         "*Reviews in Mineralogy and Geochemistry*, *81*(1), 725-774. "
         "https://doi.org/10.2138/rmg.2016.81.12",
         "Metal ordering by compatibility with sulphide liquid."),
        ("Nakamura, N. (1974). Determination of REE, Ba, Fe, Mg, Na and "
         "K in carbonaceous and ordinary chondrites. *Geochimica et "
         "Cosmochimica Acta*, *38*(5), 757-775. "
         "https://doi.org/10.1016/0016-7037(74)90149-5",
         "Early chondrite REE normalisation (still used)."),
        ("Wakita, H., Rey, P., & Schmitt, R. A. (1971). Abundances of "
         "the 14 rare-earth elements and 12 other trace elements in "
         "Apollo 12 samples: five igneous and one breccia rocks and four "
         "soils. *Proceedings of the Second Lunar Science Conference*, "
         "*2*, 1319-1329.",
         "Ordinary-chondrite REE; the normalisation of Drummond & Defant "
         "(1990)."),
        ("Pourmand, A., Dauphas, N., & Ireland, T. J. (2012). A novel "
         "extraction chromatography and MC-ICP-MS technique for rapid "
         "analysis of REE, Sc and Y: Revising CI-chondrite and "
         "Post-Archean Australian Shale (PAAS) abundances. *Chemical "
         "Geology*, *291*, 38-54. "
         "https://doi.org/10.1016/j.chemgeo.2011.08.011",
         "CI chondrite and PAAS REE normalisers."),
        ("Barrat, J. A., Zanda, B., Moynier, F., Bollinger, C., Liorzou, "
         "C., & Bayon, G. (2012). Geochemistry of CI chondrites: Major "
         "and trace elements, and Cu and Zn isotopes. *Geochimica et "
         "Cosmochimica Acta*, *83*, 79-92. "
         "https://doi.org/10.1016/j.gca.2011.12.011",
         "Orgueil CI chondrite REE normaliser."),
        ("McLennan, S. M. (1989). Rare earth elements in sedimentary "
         "rocks: Influence of provenance and sedimentary processes. In "
         "B. R. Lipin & G. A. McKay (Eds.), *Geochemistry and mineralogy "
         "of rare earth elements* (Reviews in Mineralogy 21, pp. "
         "169-200). Mineralogical Society of America. "
         "https://doi.org/10.1515/9781501509032-010",
         "NASC REE normaliser."),
        ("Kamber, B. S., Greig, A., & Collerson, K. D. (2005). A new "
         "estimate for the composition of weathered young upper "
         "continental crust from alluvial sediments, Queensland, "
         "Australia. *Geochimica et Cosmochimica Acta*, *69*(4), "
         "1041-1058. https://doi.org/10.1016/j.gca.2004.08.020",
         "MUQ shale normaliser."),
        ("Bau, M., Schmidt, K., Pack, A., Bendel, V., & Kraemer, D. "
         "(2018). The European Shale: An improved data set for "
         "normalisation of rare earth element and yttrium concentrations "
         "in environmental and biological samples from Europe. *Applied "
         "Geochemistry*, *90*, 142-149. "
         "https://doi.org/10.1016/j.apgeochem.2018.01.008",
         "European Shale and World Shale Average normalisers."),
        ("Palme, H., & O'Neill, H. St. C. (2014). Cosmochemical estimates "
         "of mantle composition. In H. D. Holland & K. K. Turekian "
         "(Eds.), *Treatise on geochemistry* (2nd ed., Vol. 3, pp. "
         "1-39). Elsevier. "
         "https://doi.org/10.1016/B978-0-08-095975-7.00201-1",
         "Primitive-mantle normaliser."),
        ("Arevalo, R., Jr., & McDonough, W. F. (2010). Chemical "
         "variations and regional diversity observed in MORB. *Chemical "
         "Geology*, *271*(1-2), 70-85. "
         "https://doi.org/10.1016/j.chemgeo.2009.12.013",
         "Global MORB, log-normal mean normaliser."),
    ]),
    # ----------------------------------------------------------------------
    ("Reservoirs (overlays on bivariate plots)", [
        ("Hofmann, A. W., Jochum, K. P., Seufert, M., & White, W. M. "
         "(1986). Nb and Pb in oceanic basalts: New constraints on "
         "mantle evolution. *Earth and Planetary Science Letters*, "
         "*79*(1-2), 33-45. https://doi.org/10.1016/0012-821X(86)90038-5",
         "Nb/U and Ce/Pb, about constant in oceanic basalts and low in "
         "continental crust (Statistics → Trace ratios)."),
        ("Workman, R. K., & Hart, S. R. (2005). Major and trace element "
         "composition of the depleted MORB mantle (DMM). *Earth and "
         "Planetary Science Letters*, *231*(1-2), 53-72. "
         "https://doi.org/10.1016/j.epsl.2004.12.005",
         "Depleted MORB mantle: majors from Table 3, traces from "
         "Table 2."),
        ("Hirose, K., & Kushiro, I. (1993). Partial melting of dry "
         "peridotites at high pressures: Determination of compositions "
         "of melts segregated from peridotite using aggregates of "
         "diamond. *Earth and Planetary Science Letters*, *114*(4), "
         "477-489. https://doi.org/10.1016/0012-821X(93)90077-M",
         "Spinel lherzolite KLB-1 (Table 2)."),
        ("Walter, M. J. (1998). Melting of garnet peridotite and the "
         "origin of komatiite and depleted lithosphere. *Journal of "
         "Petrology*, *39*(1), 29-60. "
         "https://doi.org/10.1093/petroj/39.1.29",
         "Garnet lherzolite KR4003 (Table 1)."),
        ("Hirschmann, M. M., Kogiso, T., Baker, M. B., & Stolper, E. M. "
         "(2003). Alkalic magmas generated by partial melting of garnet "
         "pyroxenite. *Geology*, *31*(6), 481-484. "
         "https://doi.org/10.1130/0091-7613(2003)031<0481:AMGBPM>2.0.CO;2",
         "Garnet pyroxenite MIX1G (Table 1)."),
    ]),
    # ----------------------------------------------------------------------
    ("Isotopes", [
        ("Zindler, A., & Hart, S. R. (1986). Chemical geodynamics. "
         "*Annual Review of Earth and Planetary Sciences*, *14*, "
         "493-571. https://doi.org/10.1146/annurev.ea.14.050186.002425",
         "Sr-Nd mantle reservoirs; bulk silicate Earth 87Sr/86Sr = 0.7051, "
         "the reference for εSr."),
        ("Hart, S. R. (1984). A large-scale isotope anomaly in the "
         "Southern Hemisphere mantle. *Nature*, *309*, 753-757. "
         "https://doi.org/10.1038/309753a0",
         "Northern Hemisphere Reference Line (NHRL)."),
        ("Hofmann, A. W. (2003). Sampling mantle heterogeneity through "
         "oceanic basalts: Isotopes and trace elements. *Treatise on "
         "Geochemistry*, *2*, 61-101.",
         "Mantle end-member fields."),
        ("Jacobsen, S. B., & Wasserburg, G. J. (1980). Sm-Nd isotopic "
         "evolution of chondrites. *Earth and Planetary Science "
         "Letters*, *50*, 139-155. "
         "https://doi.org/10.1016/0012-821X(80)90125-9",
         "CHUR, the reference for εNd."),
        # 1968, as Crossref and the journal date volume 5; often cited
        # as 1969.
        ("Papanastassiou, D. A., & Wasserburg, G. J. (1968). Initial "
         "strontium isotopic abundances and the resolution of small time"
         " differences in the formation of planetary objects. *Earth and"
         " Planetary Science Letters*, *5*, 361-376. "
         "https://doi.org/10.1016/S0012-821X(68)80066-4",
         "BABI, the start of the Sr reference reservoir."),
        ("Steiger, R. H., & Jäger, E. (1977). Subcommission on "
         "geochronology: Convention on the use of decay constants in "
         "geo- and cosmochronology. *Earth and Planetary Science "
         "Letters*, *36*, 359-362. "
         "https://doi.org/10.1016/0012-821X(77)90060-7",
         "87Rb and 147Sm decay constants."),
    ]),
    # ----------------------------------------------------------------------
    ("Statistics & anomalies", [
        ("Eu/Eu*: Boynton, W. V. (1984), Henderson, P. (Ed.) (1984). "
         "*Rare earth element geochemistry*. Elsevier.",
         "Eu/Eu* = Eu_N / sqrt(Sm_N · Gd_N)."),
        ("Ce/Ce*: Wright, J., Schrader, H., & Holser, W. T. (1987). "
         "Paleoredox variations in ancient oceans recorded by rare earth"
         " elements in fossil apatite. *Geochimica et Cosmochimica "
         "Acta*, *51*(3), 631-644. "
         "https://doi.org/10.1016/0016-7037(87)90075-5",
         "Ce/Ce* = Ce_N / sqrt(La_N · Pr_N)."),
        ("Nb/Nb*, Ta/Ta* (Pearce 2008): Pearce, J. A. (2008). "
         "Geochemical fingerprinting of oceanic basalts with "
         "applications to ophiolite classification and the search for "
         "Archean oceanic crust. *Lithos*, *100*(1-4), 14-48. "
         "https://doi.org/10.1016/j.lithos.2007.06.016",
         "Nb/Nb* = Nb_N / sqrt(Th_N · La_N) — see citation above."),
        ("Verma 2015 anomalies (Nb/Nb*_V, Ta/Ta*_V): Verma, S. P. "
         "(2015). Origin, evolution, and tectonic setting of the eastern"
         " part of the Mexican Volcanic Belt... *Turkish Journal of "
         "Earth Sciences*, *24*(2), 111-164. "
         "https://doi.org/10.3906/yer-1412-31",
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
        ("Cross, W., Iddings, J. P., Pirsson, L. V., & Washington, H. S."
         " (1902). A quantitative chemico-mineralogical classification "
         "and nomenclature of igneous rocks. *Journal of Geology*, "
         "*10*(6), 555-690. https://doi.org/10.1086/621030",
         "Original CIPW algorithm."),
        ("Kelsey, C. H. (1965). Calculation of the C.I.P.W. norm. "
         "*Mineralogical Magazine*, *34*(268), 276-282. "
         "https://doi.org/10.1180/minmag.1965.034.268.23",
         "Classical CIPW computational recipe."),
    ]),
    # ----------------------------------------------------------------------
    ("Pre-process / Fe partition", [
        ("Middlemost, E. A. K. (1989). Iron oxidation ratios, norms and "
         "the classification of volcanic rocks. *Chemical Geology*, "
         "*77*(1), 19-26. https://doi.org/10.1016/0009-2541(89)90011-9",
         "Middlemost Fe2O3/FeO partition by rock type."),
        ("Le Maitre, R. W. (1976). Some problems of the projection of "
         "chemical data into mineralogical classifications. "
         "*Contributions to Mineralogy and Petrology*, *56*(2), 181-189."
         " https://doi.org/10.1007/BF00399603",
         "Le Maitre Fe-oxidation correction."),
    ]),
    # ----------------------------------------------------------------------
    ("Map / Coordinate reference systems", [
        ("Snyder, J. P. (1987). *Map projections — A working manual* "
         "(Professional Paper 1395). U.S. Geological Survey. "
         "https://doi.org/10.3133/pp1395",
         "UTM forward / inverse formulas (Snyder series)."),
        ("National Geospatial-Intelligence Agency. (2014). *World "
         "Geodetic System 1984 (WGS-84): Its definition and "
         "relationships with local geodetic systems* (NGA.STND.0036_1.0.0_"
         "WGS84). NGA Office of Geomatics.",
         "WGS-84 datum (EPSG:4326) and ellipsoid, used for all map "
         "coordinates and for the lengths of a degree behind the scale "
         "bar and the map's aspect ratio."),
        ("Defense Mapping Agency. (1990). *The universal grids: Universal "
         "Transverse Mercator (UTM) and Universal Polar Stereographic "
         "(UPS)* (TM 8358.2). Department of Defense.",
         "MGRS grid-reference convention."),
    ]),
    # ----------------------------------------------------------------------
    ("Geostatistics — kriging in the Map view", [
        ("Matheron, G. (1963). Principles of geostatistics. *Economic "
         "Geology*, *58*(8), 1246-1266. "
         "https://doi.org/10.2113/gsecongeo.58.8.1246",
         "Variogram and ordinary kriging."),
        ("Dubrule, O. (1983). Cross validation of kriging in a unique "
         "neighborhood. *Mathematical Geology*, *15*(6), 687-699. "
         "https://doi.org/10.1007/BF01033232",
         "Leave-one-out cross-validation from a single matrix inverse."),
        ("Webster, R., & Oliver, M. A. (1992). Sample adequately to "
         "estimate variograms of soil properties. *Journal of Soil "
         "Science*, *43*(1), 177-192. "
         "https://doi.org/10.1111/j.1365-2389.1992.tb00128.x",
         "Sample sizes behind the variogram's reliability warning."),
        ("Pebesma, E. J. (2004). Multivariable geostatistics in S: The "
         "gstat package. *Computers & Geosciences*, *30*, 683-691. "
         "https://doi.org/10.1016/j.cageo.2004.03.012",
         "Variogram fit weighted by N(h)/h², gstat's default."),
    ]),
    # ----------------------------------------------------------------------
    ("Software & libraries used by B.I.R.D.S", [
        ("Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. "
         "*Computing in Science & Engineering*, *9*(3), 90-95. "
         "https://doi.org/10.1109/MCSE.2007.55",
         "Plot rendering."),
        ("McKinney, W. (2010). Data structures for statistical computing"
         " in Python. *Proceedings of the 9th Python in Science "
         "Conference*, 56-61. "
         "https://doi.org/10.25080/Majora-92bf1922-00a",
         "pandas — DataFrame operations."),
        ("Harris, C. R., Millman, K. J., van der Walt, S. J., et al. "
         "(2020). Array programming with NumPy. *Nature*, *585*, "
         "357-362. https://doi.org/10.1038/s41586-020-2649-2",
         "NumPy — numerical arrays."),
        ("Virtanen, P., Gommers, R., Oliphant, T. E., et al. (2020). "
         "SciPy 1.0: Fundamental algorithms for scientific computing in "
         "Python. *Nature Methods*, *17*(3), 261-272. "
         "https://doi.org/10.1038/s41592-019-0686-2",
         "Convex hulls for group envelopes; the linear algebra and "
         "least squares behind the kriging."),
        ("The Qt Company. (2024). *Qt for Python (PySide6) documentation*. "
         "https://doc.qt.io/qtforpython-6/",
         "GUI framework."),
        ("Whitaker, J. (2024). *pyproj: Python interface to PROJ*. "
         "https://pyproj4.github.io/pyproj/",
         "UTM to latitude/longitude, when installed."),
    ]),
]


def all_references() -> List[Section]:
    """Return the complete bibliography for the References dialog."""
    return REFERENCES


def total_count() -> int:
    """Number of individual references across all sections."""
    return sum(len(items) for _, items in REFERENCES)
