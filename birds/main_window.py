"""Top-level B.I.R.D.S window with menu bar and stacked navigation."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import pandas as pd
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QStackedWidget,
    QStatusBar,
    QToolBar,
)

from .data_manager import DataManager
from .session import (
    SESSION_EXT,
    SessionError,
    SessionState,
    autosave_path,
    clear_autosave,
    load_session,
    rotate_autosave,
    save_session,
)
from .diagrams.catalog import (
    TECTONIC_PLUTONIC,
    TECTONIC_VOLCANIC,
)
from .dialogs.edit_plot_dialog import EditPlotDialog
from .dialogs.export_plot_dialog import ExportPlotDialog
from .dialogs.import_dialog import ImportDialog
from .dialogs.preprocess_dialog import PreprocessDialog
from .dialogs.save_file_dialog import SaveStatisticsDialog
from .cipw import compute_cipw
from .plot_style import PlotStyle
from .preprocess import pre_process
from .stats_engine import (
    compute_anomalies_extended,
    compute_correlation_matrix,
    compute_descriptive_by_group,
    compute_descriptive_full,
    export_sections,
)
from .views.bivariate import BivariateView
from .views.classification import ClassificationView
from .views.data_table import DataTableView
from .views.isotopes import IsotopesView
from .views.map_view import MapView
from .views.norm import NormView
from .views.petrography import PetrographyView
from .views.spider import SpiderView
from .views.statistics import StatisticsView
from .views.tectonic import TectonicView
from .views.welcome import WelcomeView


RESOURCES = Path(__file__).parent / "resources"


class BirdsMainWindow(QMainWindow):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("B.I.R.D.S — Broad Igneous Rocks · Diagrams & Statistics")
        self.resize(1280, 800)

        icon_path = RESOURCES / "LOGO-BIRDS.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # ---- shared state ---------------------------------------------------
        self.data = DataManager()
        self.style = PlotStyle()

        # ---- views ----------------------------------------------------------
        self.welcome = WelcomeView()
        self.classification = ClassificationView(self.data, self.style)
        self.bivariate = BivariateView(self.data, self.style)
        self.spider = SpiderView(self.data, self.style)
        self.tectonic = TectonicView(self.data, self.style)
        self.statistics = StatisticsView(self.data, self.style)
        self.map = MapView(self.data, self.style)
        self.isotopes = IsotopesView(self.data, self.style)
        self.norm = NormView(self.data, self.style)
        self.petrography = PetrographyView(self.data, self.style)
        self.data_table = DataTableView(self.data)
        self.data_table.set_dirty_callback(self.mark_dirty)

        self.stack = QStackedWidget()
        for view in (
            self.welcome,
            self.classification,
            self.bivariate,
            self.spider,
            self.tectonic,
            self.statistics,
            self.map,
            self.isotopes,
            self.norm,
            self.petrography,
            self.data_table,
        ):
            self.stack.addWidget(view)
        self.stack.setCurrentWidget(self.welcome)
        self.setCentralWidget(self.stack)
        # A page hidden behind another holds its redraws (see
        # views/deferral.py); draw it once, when it comes on screen.
        self.stack.currentChanged.connect(self._on_page_shown)

        # ---- cross-view brushing --------------------------------------------
        # Alt/Cmd+click a point in any wired view to select that sample
        # everywhere; Alt/Cmd+click on empty space (or Esc) clears.
        from .selection import SelectionBus
        from .views.brushing import wire_brushing
        self.selection = SelectionBus(self)
        for view in (self.classification, self.tectonic, self.spider,
                     self.map, self.bivariate, self.isotopes):
            wire_brushing(view, self.selection)

        # ---- session state -------------------------------------------------
        # Currently-open session file (None until first Save-as / Open).
        self._session_path: Optional[Path] = None
        # When True, mark_dirty() is a no-op — set during session loading
        # so the restore() calls don't immediately re-mark the freshly
        # loaded session as modified.
        self._loading: bool = False
        # QSettings for "Recent sessions" — keyed by org / app.  The
        # format is the default one, which is the platform's own (the
        # same file as always) unless set otherwise: the test suite
        # points it at a sandbox, where QSettings("BIRDS", "BIRDS") --
        # always native, and on macOS always the real preferences --
        # pushed pytest's temporary sessions into the user's list.
        self._qs = QSettings(QSettings.defaultFormat(),
                             QSettings.Scope.UserScope, "BIRDS", "BIRDS")

        # ---- chrome ---------------------------------------------------------
        self._build_menu_bar()
        self._build_toolbar()
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready - load a dataset to begin")
        self._refresh_window_title()

        # ---- auto-save -----------------------------------------------------
        # Rolls every 5 minutes; only fires when the window is modified.
        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(5 * 60 * 1000)
        self._autosave_timer.timeout.connect(self._on_autosave_tick)
        self._autosave_timer.start()

        # ---- crash recovery -----------------------------------------------
        # Deferred to after show() so the user sees the welcome screen
        # before any dialog appears.
        QTimer.singleShot(250, self._maybe_offer_recovery)

        # ---- dirty tracking ------------------------------------------------
        # Connect every state-changing widget across every view to
        # mark_dirty().  Done AFTER all views were constructed so we
        # catch every QComboBox / QLineEdit / QCheckBox the user can
        # touch — without polluting each view with manual emit() calls.
        self._wire_dirty_signals()

        # ---- per-view group visibility -------------------------------------
        # Every view's GroupingGroup gets the same PlotStyle so its
        # checkbox list reflects the current grouping, and any toggle
        # triggers the local view's update_plot().
        self._wire_grouping_groups()

        # ---- one anomaly reference --------------------------------------
        # The data table's per-sample anomalies and the Statistics view's
        # are normalised to the same chondrite: picking it in either
        # place picks it in both, so the two never show different values.
        self._link_anomaly_references()

    def _link_anomaly_references(self) -> None:
        """Keep the two chondrite pickers on the same entry.  The other
        one is set quietly: both pages recompute whenever they are
        opened, and recomputing Statistics behind the table took most
        of a second for each pick."""
        table = self.data_table.anomaly_combo
        stats = self.statistics.norm_combo

        def follow(source, target):
            def sync(*_args):
                idx = target.findData(source.currentData())
                if idx >= 0 and idx != target.currentIndex():
                    target.blockSignals(True)
                    target.setCurrentIndex(idx)
                    target.blockSignals(False)
            source.currentIndexChanged.connect(sync)
        follow(table, stats)
        follow(stats, table)

    # ----------------------------------------------------------------- toolbar
    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Navigation")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setStyleSheet(
            "QToolBar { background: #eef0f5; border-bottom: 1px solid #d4d8e1;"
            " padding: 4px; spacing: 6px; }"
            "QToolButton { padding: 4px 10px; border-radius: 4px; }"
            "QToolButton:hover { background: #d8def0; }"
        )
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        self.home_action = QAction("← Home", self)
        # No shortcut here: the Data menu's "Home" action already owns
        # Ctrl+H, and two actions sharing a sequence in one window make
        # it ambiguous, so Qt fires neither.
        self.home_action.setStatusTip("Return to the welcome screen (Ctrl+H)")
        self.home_action.triggered.connect(self.go_home)
        toolbar.addAction(self.home_action)

    def _on_page_shown(self, index: int) -> None:
        """Draw a page whose redraws were held while it was hidden."""
        from .views.deferral import draw_if_pending
        draw_if_pending(self.stack.widget(index))

    def go_home(self) -> None:
        """Switch back to the welcome screen."""
        self.stack.setCurrentWidget(self.welcome)
        self.statusBar().showMessage("Welcome to B.I.R.D.S")

    # ------------------------------------------------------------------ menu
    def _build_menu_bar(self) -> None:
        bar = self.menuBar()
        # Final menu order:
        #   1. Data            6. Bivariate diagrams
        #   2. Map             7. Spider diagrams
        #   3. Petrography     8. Tectonic diagrams
        #   4. Norm            9. Isotopes
        #   5. Classification  10. Statistics & Anomalies
        self._build_data_menu(bar)
        self._build_map_menu(bar)
        self._build_petrography_menu(bar)
        self._build_norm_menu(bar)
        self._build_classification_menu(bar)
        self._build_bivariate_menu(bar)
        self._build_spider_menu(bar)
        self._build_tectonic_menu(bar)
        self._build_isotopes_menu(bar)
        self._build_statistics_menu(bar)
        self._build_references_menu(bar)

    # ---- Norm menu ----------------------------------------------------------
    def _build_norm_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Norm")
        act = QAction("CIPW norm (classical)…", self)
        act.setShortcut("Ctrl+Shift+C")
        act.setStatusTip(
            "Compute the classical CIPW normative mineralogy "
            "(Cross-Iddings-Pirsson-Washington 1903). Auto-fills the "
            "normative columns into the dataset and exports a "
            "multi-sheet XLSX report."
        )
        act.triggered.connect(self._open_norm)
        menu.addAction(act)

    def _open_norm(self) -> None:
        self.stack.setCurrentWidget(self.norm)
        self.norm.plot_style = self.style
        self.norm.show_view()
        self.statusBar().showMessage("Norm — CIPW mineralogy")

    # ---- Petrography menu --------------------------------------------------
    def _build_petrography_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Petrography")
        entries: tuple[tuple[str, str], ...] = (
            ("Streckeisen QAPF — Plutonic", "streckeisen_qapf_plutonic"),
            ("Streckeisen QAPF — Volcanic", "streckeisen_qapf_volcanic"),
            ("Gabbroic rocks — Pl / Px / Ol", "gabbro_pl_px_ol"),
            ("Ultramafic rocks — Ol / Opx / Cpx", "ultramafic_ol_opx_cpx"),
            ("Pyroclastic tuffs — Schmid (1981)", "tuff_schmid_1981"),
            ("Pyroclastic tuffs — banded scheme",
             "tuff_crystal_vitric_lithic"),
        )
        for label, key in entries:
            act = QAction(label + "…", self)
            act.triggered.connect(
                lambda _checked=False, k=key: self._open_petrography(k))
            menu.addAction(act)

    def _open_petrography(self, key: str) -> None:
        self.stack.setCurrentWidget(self.petrography)
        self.petrography.plot_style = self.style
        self.petrography.show_diagram(key)
        self.statusBar().showMessage(f"Petrography — {key}")

    # ---- Isotopes menu ------------------------------------------------------
    def _build_isotopes_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Isotopes")
        act_snd = QAction("Sr-Nd  (⁸⁷Sr/⁸⁶Sr vs ¹⁴³Nd/¹⁴⁴Nd)…", self)
        act_snd.setStatusTip(
            "⁸⁷Sr/⁸⁶Sr vs ¹⁴³Nd/¹⁴⁴Nd with mantle reservoirs, mantle "
            "array and εNd/εSr secondary axes."
        )
        act_snd.triggered.connect(lambda: self._open_isotopes("sr_nd"))
        menu.addAction(act_snd)

        act_pb207 = QAction("Pb  (²⁰⁶Pb/²⁰⁴Pb vs ²⁰⁷Pb/²⁰⁴Pb)…", self)
        act_pb207.setStatusTip(
            "Pb-Pb diagram for crustal vs mantle source identification."
        )
        act_pb207.triggered.connect(lambda: self._open_isotopes("pb_207"))
        menu.addAction(act_pb207)

        act_pb208 = QAction("Pb  (²⁰⁶Pb/²⁰⁴Pb vs ²⁰⁸Pb/²⁰⁴Pb)…", self)
        act_pb208.setStatusTip(
            "Pb diagram with the Northern Hemisphere Reference Line "
            "(NHRL; Hart 1984)."
        )
        act_pb208.triggered.connect(lambda: self._open_isotopes("pb_208"))
        menu.addAction(act_pb208)

    def _open_isotopes(self, key: str) -> None:
        self.stack.setCurrentWidget(self.isotopes)
        self.isotopes.plot_style = self.style
        # Switch diagram, then refresh combos and replot
        i = self.isotopes.diagram_combo.findData(key)
        if i >= 0:
            self.isotopes.diagram_combo.setCurrentIndex(i)
        self.isotopes.show_diagram()
        self.statusBar().showMessage("Isotopes")

    # ---- Map menu ----------------------------------------------------------
    def _build_map_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Map")
        act_locations = QAction("Sample locations and kriging…", self)
        act_locations.setStatusTip(
            "Plot the geographic position of every sample on longitude/"
            "latitude axes, and krige any numeric column across them."
        )
        act_locations.triggered.connect(self._open_map)
        menu.addAction(act_locations)

    def _open_map(self) -> None:
        self.stack.setCurrentWidget(self.map)
        self.map.plot_style = self.style
        self.map.show_map()
        self.statusBar().showMessage("Map — sample locations and kriging")

    # ---- Data menu ----------------------------------------------------------
    def _build_data_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Data")

        # ---- Session ------------------------------------------------------
        act_new = QAction("New session", self)
        act_new.setShortcut("Ctrl+N")
        act_new.setStatusTip(
            "Reset the dataset, styling and every view to a blank state."
        )
        act_new.triggered.connect(self.on_new_session)
        menu.addAction(act_new)

        act_open_session = QAction("Open session…", self)
        act_open_session.setShortcut("Ctrl+O")
        act_open_session.setStatusTip(
            "Open a previously saved .birds session file."
        )
        act_open_session.triggered.connect(self.on_open_session)
        menu.addAction(act_open_session)

        self._recent_menu = menu.addMenu("Recent sessions")
        self._refresh_recent_menu()

        menu.addSeparator()

        act_save_session = QAction("Save session", self)
        act_save_session.setShortcut("Ctrl+S")
        act_save_session.setStatusTip(
            "Save the entire current state (data, styles, view "
            "settings) to the .birds file."
        )
        act_save_session.triggered.connect(self.on_save_session)
        menu.addAction(act_save_session)
        self._action_save_session = act_save_session

        act_save_as = QAction("Save session as…", self)
        act_save_as.setShortcut("Ctrl+Shift+S")
        act_save_as.triggered.connect(self.on_save_session_as)
        menu.addAction(act_save_as)

        menu.addSeparator()

        # ---- Existing dataset I/O ----------------------------------------
        act_import = QAction("Import data (.xls / .csv)…", self)
        act_import.setShortcut("Ctrl+I")
        act_import.triggered.connect(self.on_import)
        menu.addAction(act_import)

        act_table = QAction("View data table…", self)
        act_table.setShortcut("Ctrl+T")
        act_table.setStatusTip(
            "Inspect and edit the loaded sheets in an interactive grid.")
        act_table.triggered.connect(self.on_view_table)
        menu.addAction(act_table)

        act_bdl = QAction("Detection limits…", self)
        act_bdl.setStatusTip(
            "Change how below-detection values (<x) are substituted — "
            "x/2, x/√2 or blank — without re-importing.")
        act_bdl.triggered.connect(self.on_detection_limits)
        menu.addAction(act_bdl)

        act_edit = QAction("Edit plot…", self)
        act_edit.setShortcut("Ctrl+E")
        act_edit.triggered.connect(self.on_edit_plot)
        menu.addAction(act_edit)

        # Style presets — the symbology alone, reusable across projects.
        style_menu = menu.addMenu("Plot style preset")
        act_save_style = QAction("Save current style…", self)
        act_save_style.setStatusTip(
            "Save colours, markers and grouping as a reusable "
            ".birdstyle file — independent of the session.")
        act_save_style.triggered.connect(self.on_save_style_preset)
        style_menu.addAction(act_save_style)
        act_load_style = QAction("Load style…", self)
        act_load_style.setStatusTip(
            "Apply a saved .birdstyle so this project's figures match "
            "an earlier one.")
        act_load_style.triggered.connect(self.on_load_style_preset)
        style_menu.addAction(act_load_style)

        act_preprocess = QAction("Pre-process majors…", self)
        act_preprocess.setShortcut("Ctrl+Shift+P")
        act_preprocess.setStatusTip(
            "Add major oxides re-scaled to 100 wt %, with total iron "
            "partitioned between Fe₂O₃ and FeO, as SiO2_adj, TiO2_adj, … "
            "beside the analysed values."
        )
        act_preprocess.triggered.connect(self.on_preprocess)
        menu.addAction(act_preprocess)

        menu.addSeparator()
        save_menu = menu.addMenu("Export")
        act_save_file = QAction("Save statistics report…", self)
        act_save_file.setShortcut("Ctrl+Shift+R")
        act_save_file.triggered.connect(self.on_save_file)
        save_menu.addAction(act_save_file)
        act_export_plot = QAction("Export plot…", self)
        act_export_plot.setShortcut("Ctrl+Shift+E")
        act_export_plot.triggered.connect(self.on_export_plot)
        save_menu.addAction(act_export_plot)
        act_copy_plot = QAction("Copy plot to clipboard", self)
        # Ctrl+Shift+C is already the CIPW norm — use Ctrl+Shift+V, which
        # is free and sits next to it on the keyboard.
        act_copy_plot.setShortcut("Ctrl+Shift+V")
        act_copy_plot.triggered.connect(self.on_copy_plot)
        save_menu.addAction(act_copy_plot)

        menu.addSeparator()
        act_home = QAction("Home (welcome screen)", self)
        act_home.setShortcut("Ctrl+H")
        act_home.triggered.connect(self.go_home)
        menu.addAction(act_home)

        act_help = QAction("Help", self)
        act_help.setShortcut(QKeySequence.StandardKey.HelpContents)
        act_help.triggered.connect(self.on_help)
        menu.addAction(act_help)

        act_shortcuts = QAction("Keyboard shortcuts…", self)
        act_shortcuts.setShortcut("Ctrl+/")
        act_shortcuts.triggered.connect(self.on_show_shortcuts)
        menu.addAction(act_shortcuts)

        menu.addSeparator()
        act_exit = QAction("Exit", self)
        act_exit.setShortcut(QKeySequence.StandardKey.Quit)
        act_exit.triggered.connect(self.on_exit)
        menu.addAction(act_exit)

        # Hidden 'Update plot' action — no menu entry, but listens for
        # Ctrl+R and F5 globally and re-renders the active view.
        for seq in ("Ctrl+R", "F5"):
            act_update = QAction(self)
            act_update.setShortcut(seq)
            act_update.triggered.connect(self._update_active_view)
            self.addAction(act_update)

    # ---- Classification menu ------------------------------------------------
    def _build_classification_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Classification diagrams")

        act_vol = QAction("Volcanic", self)
        act_vol.triggered.connect(lambda: self._open_classification_family("volcanic"))
        menu.addAction(act_vol)

        act_plu = QAction("Plutonic", self)
        act_plu.triggered.connect(lambda: self._open_classification_family("plutonic"))
        menu.addAction(act_plu)

    def _open_classification_family(self, family: str) -> None:
        self.stack.setCurrentWidget(self.classification)
        self.classification.plot_style = self.style
        self.classification.set_family(family)

    # ---- Bivariate menu -----------------------------------------------------
    def _build_bivariate_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Bivariate diagrams")
        act_indiv = QAction("Individual", self)
        act_indiv.triggered.connect(lambda: self._open_bivariate("individual"))
        menu.addAction(act_indiv)
        act_paired = QAction("Paired", self)
        act_paired.triggered.connect(lambda: self._open_bivariate("paired"))
        menu.addAction(act_paired)

    def _open_bivariate(self, mode: str) -> None:
        self.stack.setCurrentWidget(self.bivariate)
        self.bivariate.plot_style = self.style
        self.bivariate.set_mode(mode)

    # ---- Spider menu --------------------------------------------------------
    def _build_spider_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Spider diagrams")
        act_ree = QAction("REE (chondrite-normalised)", self)
        act_ree.triggered.connect(lambda: self._open_spider("ree"))
        menu.addAction(act_ree)
        act_me = QAction("Multi-elements (PM / N-MORB / CI)", self)
        act_me.triggered.connect(lambda: self._open_spider("multielement"))
        menu.addAction(act_me)

    def _open_spider(self, mode: str) -> None:
        self.stack.setCurrentWidget(self.spider)
        self.spider.plot_style = self.style
        self.spider.set_mode(mode)

    # ---- Tectonic menu ------------------------------------------------------
    def _build_tectonic_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Tectonic diagrams")

        vol_menu = menu.addMenu("Volcanic")
        for composition, entries in TECTONIC_VOLCANIC.items():
            sub = vol_menu.addMenu(composition)
            for label, key in entries:
                act = QAction(label, self)
                act.triggered.connect(
                    lambda _checked=False, k=key, c=composition: self._open_tectonic(
                        k, "volcanic", c
                    )
                )
                sub.addAction(act)

        plu_menu = menu.addMenu("Plutonic")
        for composition, entries in TECTONIC_PLUTONIC.items():
            sub = plu_menu.addMenu(composition)
            for label, key in entries:
                act = QAction(label, self)
                act.triggered.connect(
                    lambda _checked=False, k=key, c=composition: self._open_tectonic(
                        k, "plutonic", c
                    )
                )
                sub.addAction(act)

    def _open_tectonic(self, key: str, family: str, composition: str) -> None:
        self.stack.setCurrentWidget(self.tectonic)
        self.tectonic.plot_style = self.style
        self.tectonic.show_diagram(key, family, composition)

    # ---- Statistics menu ----------------------------------------------------
    def _build_statistics_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&Statistics and Anomalies")
        act_open = QAction("Open dashboard", self)
        act_open.triggered.connect(self._open_statistics)
        menu.addAction(act_open)

    def _open_statistics(self) -> None:
        self.stack.setCurrentWidget(self.statistics)
        self.statistics.refresh()

    # ---- References menu -----------------------------------------------------
    def _build_references_menu(self, bar: QMenuBar) -> None:
        menu = bar.addMenu("&References")
        act = QAction("Show full bibliography (APA)…", self)
        act.setShortcut("Ctrl+Shift+B")
        act.setStatusTip(
            "Open the APA-7 reference list for every diagram, "
            "normalisation, algorithm and process implemented in BIRDS."
        )
        act.triggered.connect(self._open_references)
        menu.addAction(act)

    def _open_references(self) -> None:
        from .dialogs.references_dialog import ReferencesDialog
        # Keep a reference on self so the dialog isn't garbage-collected
        # the moment the slot returns (modeless = non-blocking).
        if getattr(self, "_references_dialog", None) is None:
            self._references_dialog = ReferencesDialog(self)
        self._references_dialog.show()
        self._references_dialog.raise_()
        self._references_dialog.activateWindow()

    # ============================================================== handlers
    def on_import(self) -> None:
        dlg = ImportDialog(self)
        if dlg.exec() != ImportDialog.DialogCode.Accepted:
            return
        if dlg.dataframe is None or dlg.path is None:
            return
        # Persist into the shared DataManager.  Isotopes / Petrography
        # sheets are stored INDEPENDENTLY (not merged into self.df) so
        # samples with no row in Data still plot in their own view.
        self.data.df = dlg.dataframe
        self.data.path = dlg.path
        self.data.isotopes_df = dlg.isotopes_dataframe
        self.data.petrography_df = dlg.petrography_dataframe
        self.data.bdl_masks = dlg.bdl_masks
        self.data.bdl_limits = dlg.bdl_limits
        self.data.bdl_policy = dlg.bdl_policy
        n = len(dlg.dataframe)
        parts = [f"{n} samples"]
        if self.data.isotopes_df is not None:
            parts.append(f"{len(self.data.isotopes_df)} isotope rows")
        if self.data.petrography_df is not None:
            parts.append(f"{len(self.data.petrography_df)} petrography rows")
        n_bdl = sum(int(m.to_numpy().sum()) for m in self.data.bdl_masks.values())
        if n_bdl:
            parts.append(f"{n_bdl} below-detection values")
        self.statusBar().showMessage(
            f"Loaded {' · '.join(parts)} from {dlg.path.name}"
        )
        self.on_dataset_replaced()
        self.mark_dirty()

    def refresh_variable_lists(self) -> None:
        """Re-read the dataset's columns into every view that lists them.

        Anything that *widens* the dataset must call this or the new
        columns stay invisible: the CIPW norm auto-filling its
        ``norm_*`` minerals, pre-processing adding FeOt, the data table
        gaining a column.  Without it the numbers are in ``data.df`` but
        cannot be picked in the Bivariate or Isotopes variable pickers,
        which reads as the feature simply not working.
        """
        for name in self._VIEW_ATTRS:
            view = getattr(self, name, None)
            if view is None:
                continue
            for hook in ("_refresh_variable_lists", "_populate_columns"):
                if hasattr(view, hook):
                    try:
                        getattr(view, hook)()
                    except Exception:                      # noqa: BLE001
                        pass

    def on_dataset_replaced(self) -> None:
        """Drop every piece of state that belonged to the *previous* data.

        Call this whenever ``data.df`` is swapped for a different table
        (import, session load).  Two things outlive the swap otherwise:

        * the **data table**, which keeps rendering the old rows until
          the user happens to reopen it — it caches its own frame;
        * the **brushing selection**, a set of sample *names*.  Stale
          names are usually invisible, but a name that also exists in
          the new dataset would come back highlighted for no reason.
        """
        self.selection.clear()
        self.data.realign_bdl_masks()
        # A new table brings its own adjusted columns or none: settings
        # recorded for the previous one no longer describe it.
        from .preprocess import has_adjusted
        if not has_adjusted(self.data.df):
            self.data.adjust_settings = None
        self.data.use_adjusted = True
        self.data_table.refresh_from_data()
        self.refresh_variable_lists()

    # ------------------------------------------------- style presets
    def on_save_style_preset(self) -> None:
        """Write the current PlotStyle to a reusable .birdstyle file."""
        from .style_presets import STYLE_EXT, preset_dir, save_preset
        suggested = str(preset_dir() / f"my_style{STYLE_EXT}")
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save plot style preset", suggested,
            f"B.I.R.D.S style (*{STYLE_EXT})")
        if not path_str:
            return
        try:
            path = save_preset(path_str, self.style)
        except OSError as exc:
            QMessageBox.critical(self, "Save style preset", str(exc))
            return
        self.statusBar().showMessage(f"Style preset saved: {path.name}")

    def on_load_style_preset(self) -> None:
        """Apply a saved .birdstyle to the running session."""
        from .style_presets import (
            STYLE_EXT, StylePresetError, apply_preset, load_preset, preset_dir,
        )
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Load plot style preset", str(preset_dir()),
            f"B.I.R.D.S style (*{STYLE_EXT});;All files (*)")
        if not path_str:
            return
        from .views.background import Cancelled, reading_label, run_in_background
        try:
            preset, name = run_in_background(
                self, "Load style preset", reading_label(path_str),
                load_preset, path_str)
        except Cancelled:
            return
        except StylePresetError as exc:
            QMessageBox.critical(self, "Load style preset", str(exc))
            return

        # A preset saved on another project usually groups by a column
        # this dataset doesn't have.  Ask which behaviour the user wants
        # instead of silently wiping their grouping.
        keep_columns = False
        current_cols = list(self.style.group_columns)
        preset_cols = list(preset.group_columns)
        if current_cols and preset_cols != current_cols:
            reply = QMessageBox.question(
                self, "Load style preset",
                f"This preset groups by "
                f"<b>{', '.join(preset_cols) or '(nothing)'}</b>, but the "
                f"current session groups by "
                f"<b>{', '.join(current_cols)}</b>.<br><br>"
                "Keep the current grouping and only take the preset's "
                "colours and markers?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            keep_columns = reply == QMessageBox.StandardButton.Yes

        summary = apply_preset(self.style, preset,
                               keep_group_columns=keep_columns)
        # Push the new styling into every view exactly like a session load.
        self._wire_grouping_groups()
        current = self.stack.currentWidget()
        for method in ("update_plot", "refresh", "refresh_from_data"):
            fn = getattr(current, method, None)
            if callable(fn):
                try:
                    fn()
                except Exception:                          # noqa: BLE001
                    pass
                break
        self.mark_dirty()
        self.statusBar().showMessage(f"Loaded style '{name}' — {summary}")

    def on_detection_limits(self) -> None:
        """Reassign the below-detection substitution policy in place."""
        from .dialogs.detection_limits_dialog import DetectionLimitsDialog
        if self.data.df is None or self.data.df.empty:
            QMessageBox.information(
                self, "Detection limits",
                "Import a dataset first (Data → Import).")
            return
        dlg = DetectionLimitsDialog(self.data, self)
        if dlg.exec() != DetectionLimitsDialog.DialogCode.Accepted:
            return
        self.data_table.refresh_from_data()
        # Values moved, so anything already on screen is stale.  The
        # lazily-rendered views (Map / Isotopes / Norm) catch up when the
        # user navigates to them, exactly as after an Edit-plot change.
        for view in (self.classification, self.bivariate,
                     self.spider, self.tectonic):
            view.update_plot()
        from .detection_limits import POLICY_LABELS
        label = POLICY_LABELS.get(dlg.policy, dlg.policy)
        if dlg.n_changed:
            self.statusBar().showMessage(
                f"Reassigned {dlg.n_changed} below-detection value"
                f"{'s' if dlg.n_changed != 1 else ''} — {label}.")
        else:
            self.statusBar().showMessage(
                f"Detection-limit policy set to {label} "
                "(no cell carried a reported limit).")
        self.mark_dirty()

    def on_view_table(self) -> None:
        """Show the interactive data-table view, refreshed from the
        current DataManager contents."""
        self.data_table.refresh_from_data()
        self.stack.setCurrentWidget(self.data_table)

    def on_preprocess(self) -> None:
        if self.data.df is None or self.data.df.empty:
            QMessageBox.information(
                self, "No data",
                "Import a dataset first (Data → Import).",
            )
            return
        dlg = PreprocessDialog(self.data, self)
        if dlg.exec() == PreprocessDialog.DialogCode.Accepted:
            n = len(self.data.df)
            # Same samples, so the brushing selection stays valid — but
            # the columns changed, so the masks, the table and every
            # variable picker must follow.
            self.data.realign_bdl_masks()
            self.data_table.refresh_from_data()
            self.refresh_variable_lists()
            # The view on screen now reads the adjusted majors.
            current = self.stack.currentWidget()
            if hasattr(current, "update_plot"):
                current.update_plot()
            self.statusBar().showMessage(
                f"Pre-processed {n} samples: adjusted majors added as "
                f"SiO2_adj, TiO2_adj, …, and now used by the diagrams. The "
                f"analysed values are kept."
            )
            self.mark_dirty()

    def on_edit_plot(self) -> None:
        # Pass a virtual "union" df that carries every column the user
        # might want to group by, even if it only lives in the Isotopes
        # or Petrography sheet.  Group / Sample_Label are now standard
        # columns in all three sheets, but the user might add custom
        # grouping columns later.
        union_df = self._union_columns_for_grouping()
        dlg = EditPlotDialog(self.style, union_df, self)
        if dlg.exec() == EditPlotDialog.DialogCode.Accepted:
            self.style = dlg.updated_style()
            # Push the new style reference into every view that holds its
            # own copy. Skipping any view here would leave it rendering
            # with the stale order / colours next time the user opens it.
            for view in (self.classification, self.bivariate, self.spider,
                         self.tectonic, self.statistics, self.map,
                         self.isotopes, self.norm, self.petrography):
                view.plot_style = self.style
            # Redraw the views that have an active plot. Map / Isotopes /
            # Norm refresh themselves the next time the user navigates
            # to them, so we don't force a render here.
            self.classification.update_plot()
            self.bivariate.update_plot()
            self.spider.update_plot()
            self.tectonic.update_plot()
            # Rebuild the per-group checkbox lists across every view so
            # they reflect the new group names / count.
            self._wire_grouping_groups()
            cols = ", ".join(self.style.group_columns) or "none"
            self.statusBar().showMessage(
                f"Plot style updated — {self.style.n_groups} groups "
                f"(by: {cols}); point size {self.style.point_size:g}, "
                f"α {self.style.alpha:.2f}"
            )
            self.mark_dirty()

    def _union_columns_for_grouping(self):
        """Return a tiny DataFrame whose columns are the union of all
        three sheets' columns.  Used to seed Edit plot's grouping
        dropdown so the user can pick a column that lives only on the
        Isotopes or Petrography sheet.
        """
        import pandas as pd
        frames = []
        for df in (self.data.df,
                   getattr(self.data, "isotopes_df", None),
                   getattr(self.data, "petrography_df", None)):
            if df is not None and not df.empty:
                frames.append(df)
        if not frames:
            return None
        # Preserve order: main sheet's columns first, then any new ones
        # from the extras.
        seen = []
        for df in frames:
            for c in df.columns:
                if c not in seen:
                    seen.append(c)
        # Concatenate row-wise so any sample with a Group value (in any
        # sheet) is visible to EditPlot's "unique values per column"
        # auto-populate routine.
        aligned = [df.reindex(columns=seen) for df in frames]
        return pd.concat(aligned, ignore_index=True)

    def on_save_file(self) -> None:
        if not self.data.is_loaded:
            QMessageBox.information(
                self,
                "Save file",
                "No dataset is loaded. Use Data → Import first.",
            )
            return
        suggested = (
            self.data.path.stem + "_birds_statistics" if self.data.path else "birds_statistics"
        )
        dlg = SaveStatisticsDialog(suggested, self)
        if dlg.exec() != SaveStatisticsDialog.DialogCode.Accepted:
            return

        sections_flags = dlg.sections
        norm_name = self.statistics.norm_combo.currentData()
        sections: dict[str, pd.DataFrame] = {}
        from .derived import with_derived
        from .preprocess import ADJ_SUFFIX, has_adjusted
        df = self.data.df
        twins = [c for c in df.columns if str(c).endswith(ADJ_SUFFIX)]
        if sections_flags["raw"]:
            # The analysed values only; the adjusted ones have a sheet
            # of their own.
            sections["Original data"] = df.drop(columns=twins)

        # The adjusted analyses are the ones Pre-process majors made, with
        # the settings chosen there.  A dataset never adjusted gets the
        # default treatment (anhydrous, Middlemost 1989) for the sheet.
        adjusted: Optional[pd.DataFrame] = None
        if sections_flags["adjusted"] or sections_flags["cipw"]:
            if has_adjusted(df):
                adjusted = self.data.majors_df()
            else:
                try:
                    adjusted = pre_process(df, "anhydrous", "middlemost")
                except Exception:                          # noqa: BLE001
                    adjusted = None
        if sections_flags["adjusted"] and adjusted is not None:
            if has_adjusted(df):
                identity = [c for c in df.columns if c not in twins
                            and not pd.api.types.is_numeric_dtype(df[c])]
                sections["Adjusted data (100% + Fe partition)"] = \
                    df[identity + twins]
            else:
                sections["Adjusted data (100% + Fe partition)"] = adjusted
        if sections_flags["cipw"] and adjusted is not None:
            try:
                sections["CIPW norm"] = compute_cipw(adjusted)
            except Exception:                              # noqa: BLE001
                pass
        # Mg# is reported like any oxide in the summary tables.
        stats_df = with_derived(df)
        if sections_flags["descriptive"]:
            sections["Descriptive statistics"] = compute_descriptive_full(
                stats_df)
            by_grp = compute_descriptive_by_group(
                stats_df, self.style.group_columns or [])
            if not by_grp.empty:
                sections["By group"] = by_grp
            # Publication-ready mean ± 1σ (n) summary, honouring the
            # variable picker and group order the user set in the view.
            try:
                from .stats_engine import compute_paper_table
                variables = None
                picker = getattr(self.statistics, "_paper_checked_variables",
                                 None)
                if callable(picker):
                    variables = picker() or None
                order = [g.name for g in (self.style.groups or [])
                         if getattr(g, "name", None)]
                paper = compute_paper_table(
                    stats_df,
                    group_columns=self.style.group_columns or [],
                    variables=variables,
                    group_order=order or None,
                )
                if not paper.empty:
                    sections["Paper table (mean ± 1SD)"] = paper
            except Exception:                              # noqa: BLE001
                pass
        if sections_flags["anomalies"]:
            sections["REE anomalies"] = compute_anomalies_extended(
                self.data.df, norm_name)
        if sections_flags["ratios"]:
            # The same table the Statistics view shows, following the
            # adjusted-majors switch.
            sections["Trace-element ratios"] = self.statistics.ratio_frame()
            corr = compute_correlation_matrix(self.data.df)
            if not corr.empty:
                sections["Correlation matrix"] = corr
        if sections_flags.get("tectonic"):
            # Read whatever the user has computed inside the Statistics
            # view's Tectonic-discrimination tab. If they haven't ticked
            # anything yet, the frame is empty and gets silently skipped
            # by export_sections.
            tect = getattr(self.statistics, "tectonic_frame", None)
            if tect is not None and not tect.empty:
                sections["Tectonic discrimination"] = tect

        try:
            export_sections(dlg.path, sections, dlg.fmt)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Save error", str(exc))
            return
        self.statusBar().showMessage(f"Saved statistics output to {dlg.path}")

    def on_export_plot(self) -> None:
        current = self.stack.currentWidget()
        canvas = getattr(current, "canvas", None)
        if canvas is None:
            QMessageBox.information(
                self,
                "Export plot",
                "Open a diagram first, then export it.",
            )
            return

        suggested = current.__class__.__name__.replace("View", "").lower() or "birds_plot"
        dlg = ExportPlotDialog(f"birds_{suggested}", self)
        if dlg.exec() != ExportPlotDialog.DialogCode.Accepted:
            return

        # Resize the figure — and optionally rescale every text element so
        # the labels land at the requested printed size — then restore both
        # afterwards so the on-screen view is untouched.
        from .dialogs.export_plot_dialog import (
            reference_font_size,
            restore_figure_fonts,
            scale_figure_fonts,
        )
        original_size = canvas.figure.get_size_inches()
        saved_fonts: list = []
        try:
            canvas.figure.set_size_inches(*dlg.figure_size)
            target_pt = dlg.target_font_pt
            if target_pt:
                reference = reference_font_size(canvas.figure)
                if reference > 0:
                    saved_fonts = scale_figure_fonts(
                        canvas.figure, target_pt / reference)
            canvas.figure.savefig(str(dlg.path), **dlg.render_kwargs)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export error", str(exc))
            return
        finally:
            restore_figure_fonts(saved_fonts)
            canvas.figure.set_size_inches(*original_size)
            canvas.draw()
        w_in, h_in = dlg.figure_size
        self.statusBar().showMessage(
            f"Exported plot to {dlg.path.name} "
            f"({w_in * 25.4:.0f} × {h_in * 25.4:.0f} mm)")

    def on_copy_plot(self) -> None:
        """Put the active diagram on the clipboard as a bitmap.

        The quick path to a manuscript or a slide: no dialog, no file
        on disk.  Rendered at 300 dpi on a white background — pasting a
        transparent figure into Word or PowerPoint produces black text
        on a dark slide, which is never what anyone wants.
        """
        from PySide6.QtGui import QImage
        from PySide6.QtWidgets import QApplication

        current = self.stack.currentWidget()
        canvas = getattr(current, "canvas", None)
        if canvas is None:
            QMessageBox.information(
                self, "Copy plot",
                "Open a diagram first, then copy it.")
            return
        fig = canvas.figure
        buf = io.BytesIO()
        original_facecolor = fig.get_facecolor()
        try:
            fig.set_facecolor("white")
            fig.savefig(buf, format="png", dpi=300,
                        facecolor="white", edgecolor="none",
                        bbox_inches="tight")
        except Exception as exc:                            # noqa: BLE001
            QMessageBox.critical(self, "Copy plot", str(exc))
            return
        finally:
            fig.set_facecolor(original_facecolor)
            canvas.draw()
        image = QImage.fromData(buf.getvalue(), "PNG")
        if image.isNull():
            QMessageBox.critical(
                self, "Copy plot", "The figure could not be rasterised.")
            return
        QApplication.clipboard().setImage(image)
        self.statusBar().showMessage(
            f"Plot copied to the clipboard "
            f"({image.width()} × {image.height()} px, 300 dpi).")

    def on_help(self) -> None:
        QMessageBox.about(
            self,
            "About B.I.R.D.S",
            (
                "<h3>B.I.R.D.S</h3>"
                "<p>Broad Igneous Rocks — Diagrams &amp; Statistics</p>"
                "<p>Implements classification, bivariate, spider and "
                "multidimensional tectonic discrimination diagrams from "
                "Rollinson &amp; Pease (2021), Pearce (2008), Verma and "
                "co-authors (2006-2017) and Yang et al. (2019).</p>"
                "<p><i>Version 0.1.0 (alpha)</i></p>"
            ),
        )

    def on_show_shortcuts(self) -> None:
        """Open a modeless dialog listing every keyboard shortcut."""
        shortcuts = (
            ("Session",
             (("New session",              "Ctrl+N"),
              ("Open session…",            "Ctrl+O"),
              ("Save session",             "Ctrl+S"),
              ("Save session as…",         "Ctrl+Shift+S"))),
            ("Data",
             (("Import data…",             "Ctrl+I"),
              ("View data table…",         "Ctrl+T"),
              ("Edit plot…",               "Ctrl+E"),
              ("Pre-process majors…",      "Ctrl+Shift+P"))),
            ("Data table",
             (("Undo last change",         "Ctrl+Z"),
              ("Redo",                     "Ctrl+Shift+Z"))),
            ("Export",
             (("Export plot…",             "Ctrl+Shift+E"),
              ("Copy plot to clipboard",   "Ctrl+Shift+V"),
              ("Save statistics report…",  "Ctrl+Shift+R"))),
            ("Compute",
             (("CIPW norm…",               "Ctrl+Shift+C"),
              ("Update plot (active view)", "Ctrl+R   /   F5"))),
            ("Navigation",
             (("Home (welcome screen)",    "Ctrl+H"),
              ("Help",                     "F1"),
              ("Keyboard shortcuts",       "Ctrl+/"),
              ("Exit",                     "Ctrl+Q"))),
        )
        rows = []
        for section, items in shortcuts:
            rows.append(
                f"<tr><td colspan='2' style='padding-top:10px;"
                f"font-weight:600;color:#1c2237;'>{section}</td></tr>"
            )
            for label, keys in items:
                rows.append(
                    f"<tr><td style='padding:2px 16px 2px 12px;'>{label}</td>"
                    f"<td style='padding:2px 0;font-family:monospace;"
                    f"color:#22416d;'>{keys}</td></tr>"
                )
        html = ("<h3 style='margin:0 0 8px 0;'>Keyboard shortcuts</h3>"
                "<table style='border-collapse:collapse;'>"
                + "".join(rows) + "</table>")
        box = QMessageBox(self)
        box.setWindowTitle("Keyboard shortcuts")
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(html)
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        box.exec()

    def _update_active_view(self) -> None:
        """Re-render the plot of whichever view is on top of the stack.
        Bound to Ctrl+R and F5."""
        current = self.stack.currentWidget()
        if current is None or current is self.welcome:
            return
        for method_name in ("update_plot", "refresh", "compute", "show_view"):
            method = getattr(current, method_name, None)
            if callable(method):
                method()
                self.statusBar().showMessage(
                    f"Refreshed {current.__class__.__name__}", 2000)
                return

    def on_exit(self) -> None:
        """Trigger the standard close — closeEvent() handles the prompt."""
        self.close()

    # ----------------------------------------------------------------------
    # Session save / load / auto-save
    # ----------------------------------------------------------------------

    _VIEW_ATTRS = (
        "bivariate", "spider", "classification", "tectonic",
        "petrography", "isotopes", "norm", "map", "statistics",
    )

    def _collect_session(self) -> SessionState:
        """Snapshot the running app into a :class:`SessionState`."""
        data: dict = {}
        if self.data.df is not None and not self.data.df.empty:
            data["main"] = self.data.df
        if (self.data.isotopes_df is not None
                and not self.data.isotopes_df.empty):
            data["isotopes"] = self.data.isotopes_df
        if (self.data.petrography_df is not None
                and not self.data.petrography_df.empty):
            data["petrography"] = self.data.petrography_df
        # Below-detection masks travel as extra boolean frames, and the
        # reported limits alongside them so the substitution policy can
        # still be changed after re-opening the session.
        for key, mask in self.data.bdl_masks.items():
            if mask is not None and not mask.empty:
                data[f"bdl_{key}"] = mask
        for key, limits in self.data.bdl_limits.items():
            if limits is not None and not limits.empty:
                data[f"bdllim_{key}"] = limits

        views: dict = {}
        for name in self._VIEW_ATTRS:
            view = getattr(self, name, None)
            if view is not None and hasattr(view, "serialize"):
                try:
                    views[name] = view.serialize()
                except Exception:
                    # A failing serializer mustn't take down the save.
                    pass

        # Cached results — only the CIPW table for now (the stats caches
        # are cheap to recompute and don't need to live in the file).
        results: dict = {}
        norm_result = getattr(self.norm, "_result", None)
        if norm_result is not None and not norm_result.empty:
            results["cipw"] = norm_result

        active = self.stack.currentWidget()
        active_name = next(
            (n for n in self._VIEW_ATTRS if getattr(self, n) is active),
            "welcome",
        )
        ui = {
            "window_size": [self.width(), self.height()],
            "active_view": active_name,
            "session_path": str(self._session_path) if self._session_path else "",
            # Which majors the diagrams read, and how the adjusted ones
            # were made (the *_adj columns travel with the data).
            "use_adjusted": bool(self.data.use_adjusted),
            "adjust_settings": self.data.adjust_settings,
        }

        return SessionState(
            data=data,
            plot_style=self.style.to_dict(),
            views=views,
            results=results,
            ui=ui,
        )

    def _apply_session(self, state: SessionState) -> None:
        """Push a freshly loaded :class:`SessionState` into the live app.

        Wrapped in a ``self._loading = True`` guard so the cascade of
        ``setCurrentText``, ``setChecked`` and ``setCurrentIndex`` calls
        triggered by :meth:`view.restore` doesn't immediately re-mark
        the session as dirty.

        Every view is restored hidden, behind the welcome page, so the
        redraws the restore sets off are held; the page the session was
        saved on (or, failing that, the one showing before) is drawn
        once at the end.
        """
        self._loading = True
        page_before = self.stack.currentWidget()
        page_after = None
        self.stack.setCurrentWidget(self.welcome)
        try:
            # Data — main bulk sheet plus the two independent extras.
            main_df = state.data.get("main")
            if main_df is not None and not main_df.empty:
                self.data.df = main_df
                self.data.path = None  # session is the new "source"
            iso_df = state.data.get("isotopes")
            self.data.isotopes_df = iso_df if (iso_df is not None
                                                and not iso_df.empty) else None
            petro_df = state.data.get("petrography")
            self.data.petrography_df = (petro_df if (petro_df is not None
                                                      and not petro_df.empty)
                                         else None)
            # Below-detection masks and limits (absent in older sessions,
            # in which case the policy simply can't be changed later).
            self.data.bdl_masks = {}
            self.data.bdl_limits = {}
            for key in ("main", "isotopes", "petrography"):
                mask = state.data.get(f"bdl_{key}")
                if mask is not None and not mask.empty:
                    self.data.bdl_masks[key] = mask.astype(bool)
                limits = state.data.get(f"bdllim_{key}")
                if limits is not None and not limits.empty:
                    self.data.bdl_limits[key] = limits.astype(float)

            # Style — mutate in place so views keep their reference.
            if state.plot_style:
                from .plot_style import PlotStyle
                self.style.copy_from(PlotStyle.from_dict(state.plot_style))

            # A session is a whole new dataset: clear the leftovers from
            # whatever was loaded before it.
            self.on_dataset_replaced()
            # Then the adjusted-majors switch as it was saved (absent in
            # sessions older than the switch).
            self.data.use_adjusted = bool(state.ui.get("use_adjusted", True))
            settings = state.ui.get("adjust_settings")
            self.data.adjust_settings = (dict(settings)
                                         if isinstance(settings, dict)
                                         else None)

            # Refresh views that depend on data (lat/lon combos, etc.)
            # before piping their state back in.
            for name in self._VIEW_ATTRS:
                view = getattr(self, name, None)
                if view is None:
                    continue
                for hook in ("_refresh_variable_lists", "_populate_columns"):
                    if hasattr(view, hook):
                        try:
                            getattr(view, hook)()
                        except Exception:
                            pass

            # Per-view state
            for name in self._VIEW_ATTRS:
                view = getattr(self, name, None)
                if view is not None and hasattr(view, "restore"):
                    try:
                        view.restore(state.views.get(name, {}))
                    except Exception as exc:
                        self._log_autosave_failure(f"restore:{name}", exc)

            # CIPW result cache (if it was saved)
            cipw = state.results.get("cipw")
            if cipw is not None and hasattr(self.norm, "restore_result"):
                try:
                    self.norm.restore_result(cipw)
                except Exception:
                    pass

            # UI niceties: window size + active view
            size = state.ui.get("window_size")
            if size and len(size) == 2:
                try:
                    self.resize(int(size[0]), int(size[1]))
                except (TypeError, ValueError):
                    pass
            active = state.ui.get("active_view")
            page_after = (getattr(self, active, None)
                          if active in self._VIEW_ATTRS else None)
        finally:
            self._loading = False
        self.stack.setCurrentWidget(page_after if page_after is not None
                                    else page_before)

        # Rebuild Grouping checkboxes for the freshly-loaded plot_style.
        self._wire_grouping_groups()
        self.setWindowModified(False)
        self._refresh_window_title()

    # -------------------------- Menu actions ------------------------------
    def on_new_session(self) -> None:
        if not self._confirm_discard_changes("start a new session"):
            return
        # Reset data + style; reinstantiate is overkill — just clear.
        # Guarded by self._loading so the cascade of clear()/refresh()
        # calls doesn't immediately re-dirty the new empty session.
        self._loading = True
        try:
            self.data.df = None
            self.data.path = None
            self.data.isotopes_df = None
            self.data.petrography_df = None
            from .plot_style import PlotStyle
            self.style.copy_from(PlotStyle())
            # Refresh views that re-populate combos / lists from the
            # (now empty) dataset, so stale entries from the previous
            # session disappear cleanly.
            for name in self._VIEW_ATTRS:
                view = getattr(self, name, None)
                if view is None:
                    continue
                for hook in ("_refresh_variable_lists", "_populate_columns"):
                    if hasattr(view, hook):
                        try:
                            getattr(view, hook)()
                        except Exception:
                            pass
        finally:
            self._loading = False
        self._session_path = None
        self.setWindowModified(False)
        self._refresh_window_title()
        self.go_home()
        self.statusBar().showMessage("New session — ready.")

    def on_open_session(self) -> None:
        if not self._confirm_discard_changes("open another session"):
            return
        path_str, _ = QFileDialog.getOpenFileName(
            self, "Open B.I.R.D.S session", "",
            f"BIRDS session (*{SESSION_EXT})",
        )
        if not path_str:
            return
        self._load_session_path(Path(path_str))

    def open_session_file(self, path: Path) -> None:
        """Open a session the system handed over: double-clicked in the
        Finder or Explorer, or named on the command line."""
        path = Path(path)
        # A file opened at launch is what the user asked for; offering
        # to recover last time's auto-save on top of it would not be.
        self._opened_from_file = True
        if (self._session_path is not None and path.exists()
                and self._session_path.exists()
                and path.resolve() == self._session_path.resolve()):
            self.raise_()
            self.activateWindow()
            return
        if not self._confirm_discard_changes("open another session"):
            return
        self._load_session_path(path)
        self.raise_()
        self.activateWindow()

    def _load_session_path(self, path: Path) -> None:
        # Read off the window's thread: a session kept online only in
        # Google Drive / iCloud downloads inside the read, and froze the
        # whole window for as long as that took.
        from .views.background import Cancelled, reading_label, run_in_background
        try:
            state = run_in_background(self, "Open session",
                                      reading_label(path), load_session, path)
        except Cancelled:
            self.statusBar().showMessage(
                f"Stopped waiting for {path.name}; nothing was changed.")
            return
        except SessionError as exc:
            QMessageBox.critical(self, "Open session", str(exc))
            return
        self._apply_session(state)
        self._session_path = path
        self._remember_recent(path)
        self._refresh_window_title()
        self.statusBar().showMessage(f"Opened session: {path.name}")

    def on_save_session(self) -> None:
        if self._session_path is None:
            self.on_save_session_as()
            return
        self._do_save(self._session_path)

    def on_save_session_as(self) -> None:
        suggested = (
            str(self._session_path) if self._session_path
            else f"session{SESSION_EXT}"
        )
        path_str, _ = QFileDialog.getSaveFileName(
            self, "Save B.I.R.D.S session", suggested,
            f"BIRDS session (*{SESSION_EXT})",
        )
        if not path_str:
            return
        path = Path(path_str)
        if path.suffix.lower() != SESSION_EXT:
            path = path.with_suffix(SESSION_EXT)
        self._session_path = path
        self._do_save(path)

    def _do_save(self, path: Path) -> None:
        try:
            save_session(path, self._collect_session())
        except Exception as exc:
            QMessageBox.critical(self, "Save session",
                                 f"Could not save session:\n{exc}")
            return
        self.setWindowModified(False)
        self._refresh_window_title()
        self._remember_recent(path)
        # User-initiated save supersedes any auto-saved recovery state —
        # delete the autosave so the recovery dialog does not appear
        # next launch.
        clear_autosave()
        self.statusBar().showMessage(f"Session saved: {path.name}")

    # -------------------------- Dirty tracking ----------------------------
    def mark_dirty(self, *_args) -> None:
        """Public hook — wired to every state-changing widget signal.

        Accepts any number of positional args so it can connect to Qt
        signals with different signatures (toggled(bool), valueChanged(int),
        currentIndexChanged(int), …) without an adapter lambda for each.
        Guarded by ``self._loading`` so applying a fresh session doesn't
        immediately re-mark it as modified.
        """
        if self._loading:
            return
        if not self.isWindowModified():
            self.setWindowModified(True)
            self._refresh_window_title()

    def _wire_grouping_groups(self) -> None:
        """Hand every view's GroupingGroup the shared PlotStyle and wire
        its visibility_changed signal to that view's update_plot().

        Idempotent — calling it again (e.g. after Edit plot) just
        rebuilds the checkboxes against the current group list.
        """
        # (view_attr, refresh_callable)
        # The refresh callable is what to fire when a group toggle
        # happens — usually the view's update_plot(), occasionally a
        # custom hook (Norm has compute()).
        targets = [
            ("classification", "update_plot"),
            ("bivariate",      "update_plot"),
            ("spider",         "update_plot"),
            ("tectonic",       "update_plot"),
            ("petrography",    "update_plot"),
            ("map",            "update_plot"),
            ("isotopes",       "update_plot"),
        ]
        for attr, slot_name in targets:
            view = getattr(self, attr, None)
            if view is None:
                continue
            # Walk every GroupingGroup the view contains (some views like
            # Bivariate keep two — one per Individual / Paired panel).
            from .views.widgets import GroupingGroup
            for gg in view.findChildren(GroupingGroup):
                gg.set_groups(self.style)
                slot = getattr(view, slot_name, None)
                if slot is not None:
                    # blockSignals during connect would be wrong here —
                    # we want every toggle to fire.  Track the slot we
                    # previously connected so we can disconnect *that
                    # specific* callable: calling ``disconnect()`` with
                    # no arguments when no slot was bound triggers a
                    # PySide6 ``libpyside`` runtime warning on stderr
                    # that ``try/except`` cannot catch (it's not raised).
                    prev_slot = getattr(gg, "_visibility_slot", None)
                    if prev_slot is not None:
                        try:
                            gg.visibility_changed.disconnect(prev_slot)
                        except (TypeError, RuntimeError):
                            pass  # already gone — fine.
                    gg.visibility_changed.connect(slot)
                    gg._visibility_slot = slot

    def _wire_dirty_signals(self) -> None:
        """Walk every view's widget tree and connect state-changing
        signals to :meth:`mark_dirty`.  Idempotent at the widget level —
        Qt happily dedups identical connections."""
        from PySide6.QtWidgets import (
            QCheckBox, QComboBox, QDoubleSpinBox, QLineEdit,
            QListWidget, QRadioButton, QSpinBox, QTreeWidget,
        )

        for name in self._VIEW_ATTRS:
            view = getattr(self, name, None)
            if view is None:
                continue

            for combo in view.findChildren(QComboBox):
                combo.currentIndexChanged.connect(self.mark_dirty)
                if combo.isEditable():
                    combo.editTextChanged.connect(self.mark_dirty)
            for edit in view.findChildren(QLineEdit):
                edit.textChanged.connect(self.mark_dirty)
            for spin in view.findChildren(QSpinBox):
                spin.valueChanged.connect(self.mark_dirty)
            for dspin in view.findChildren(QDoubleSpinBox):
                dspin.valueChanged.connect(self.mark_dirty)
            for chk in view.findChildren(QCheckBox):
                chk.toggled.connect(self.mark_dirty)
            for rad in view.findChildren(QRadioButton):
                rad.toggled.connect(self.mark_dirty)
            for lw in view.findChildren(QListWidget):
                lw.itemSelectionChanged.connect(self.mark_dirty)
            for tw in view.findChildren(QTreeWidget):
                tw.itemChanged.connect(self.mark_dirty)

    def _refresh_window_title(self) -> None:
        base = "B.I.R.D.S — Broad Igneous Rocks · Diagrams & Statistics"
        if self._session_path is not None:
            base += f" — {self._session_path.name}"
        # The trailing [*] is Qt's marker for setWindowModified().
        self.setWindowTitle(base + "[*]")

    def _confirm_discard_changes(self, action: str) -> bool:
        """Return True if the user is OK to lose unsaved changes."""
        if not self.isWindowModified():
            return True
        reply = QMessageBox.question(
            self, "Unsaved changes",
            f"You have unsaved changes. Save before you {action}?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if reply == QMessageBox.StandardButton.Cancel:
            return False
        if reply == QMessageBox.StandardButton.Save:
            self.on_save_session()
            return not self.isWindowModified()  # only proceed if save worked
        return True  # Discard

    # -------------------------- Auto-save ---------------------------------
    def _on_autosave_tick(self) -> None:
        """Fires every 5 minutes — write to ~/.birds/autosave.birds.

        Every step is wrapped in its own try/except so a failure in
        ``_collect_session`` (e.g. a Parquet-incompatible column from
        some new view) can't tear down the QTimer thread and the GUI
        with it.  Any failure is logged to ``~/.birds/crash.log`` and
        surfaced in the status bar; the app keeps running.
        """
        # Skip if nothing meaningful loaded yet, or nothing changed since
        # the last manual save.
        try:
            if self.data.df is None or self.data.df.empty:
                return
            if not self.isWindowModified():
                return
        except Exception:
            return  # data manager in some half-state — skip this tick

        try:
            state = self._collect_session()
        except Exception as exc:
            self._log_autosave_failure("collect", exc)
            self.statusBar().showMessage(
                f"Auto-save skipped (collect): {exc}", 6000)
            return

        try:
            rotate_autosave(state)
        except Exception as exc:
            self._log_autosave_failure("write", exc)
            self.statusBar().showMessage(
                f"Auto-save failed: {exc}", 6000)
            return

        self.statusBar().showMessage(
            f"Auto-saved at {pd.Timestamp.now().strftime('%H:%M:%S')}",
            4000,
        )

    @staticmethod
    def _log_autosave_failure(stage: str, exc: Exception) -> None:
        """Append an auto-save failure traceback to ~/.birds/crash.log."""
        import datetime as _dt
        import traceback as _tb
        from pathlib import Path as _Path
        try:
            log = _Path.home() / ".birds" / "crash.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            with log.open("a", encoding="utf-8") as f:
                ts = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n[{ts}] AUTOSAVE FAILED ({stage})\n")
                f.write(_tb.format_exc())
        except OSError:
            pass

    def _maybe_offer_recovery(self) -> None:
        """At startup, prompt to recover an unsaved auto-save if one
        exists and is newer than whatever the user has loaded so far."""
        if getattr(self, "_opened_from_file", False):
            return
        ap = autosave_path()
        if not ap.exists():
            return
        # Heuristic: only offer if a meaningful amount of state was saved
        # (file size > a few hundred bytes; tiny files mean we just
        # started and never had data).
        if ap.stat().st_size < 500:
            return
        reply = QMessageBox.question(
            self, "Recover session?",
            "An unsaved B.I.R.D.S session was found from a previous "
            "run.\n\nWould you like to recover it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self._apply_session(load_session(ap))
                self.statusBar().showMessage(
                    "Recovered unsaved session — use Save session to persist.",
                    8000,
                )
                self.setWindowModified(True)
                self._refresh_window_title()
            except Exception as exc:
                QMessageBox.warning(
                    self, "Recover session",
                    f"Could not recover the auto-saved session:\n{exc}",
                )

    # -------------------------- Recent sessions --------------------------
    def _recent_paths(self) -> list[Path]:
        raw = self._qs.value("recent_sessions", [], type=list) or []
        return [Path(p) for p in raw if p]

    def _remember_recent(self, path: Path) -> None:
        paths = [str(path)] + [str(p) for p in self._recent_paths()
                                if Path(p) != path]
        paths = paths[:8]  # cap at 8
        self._qs.setValue("recent_sessions", paths)
        self._refresh_recent_menu()

    def _refresh_recent_menu(self) -> None:
        if not hasattr(self, "_recent_menu"):
            return
        self._recent_menu.clear()
        recents = [p for p in self._recent_paths() if p.exists()]
        if not recents:
            placeholder = QAction("(no recent sessions)", self)
            placeholder.setEnabled(False)
            self._recent_menu.addAction(placeholder)
            return
        for p in recents:
            act = QAction(p.name, self)
            act.setStatusTip(str(p))
            act.triggered.connect(
                lambda _checked=False, path=p: self._load_session_path(path)
            )
            self._recent_menu.addAction(act)
        self._recent_menu.addSeparator()
        act_clear = QAction("Clear list", self)
        act_clear.triggered.connect(self._clear_recent)
        self._recent_menu.addAction(act_clear)

    def _clear_recent(self) -> None:
        self._qs.setValue("recent_sessions", [])
        self._refresh_recent_menu()

    # -------------------------- Window close -----------------------------
    def closeEvent(self, event) -> None:  # type: ignore[override]
        if not self._confirm_discard_changes("close B.I.R.D.S"):
            event.ignore()
            return
        # Stop the 5-min auto-save timer first so it can't fire mid-shutdown
        # and re-create the file we are about to delete.
        try:
            self._autosave_timer.stop()
        except Exception:
            pass
        # Clean exit: nothing pending (or user discarded / saved).  Drop
        # the autosave file so the next launch does NOT prompt to
        # "recover an unsaved session" that was already taken care of.
        try:
            clear_autosave()
        except Exception:
            pass
        event.accept()
