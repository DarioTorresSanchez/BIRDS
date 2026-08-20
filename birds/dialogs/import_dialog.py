"""Modal dialog for importing geochemical data with a preview."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..detection_limits import POLICIES, POLICY_LABELS, scan_and_convert
from ..io_utils import list_excel_sheets, read_tabular


# Heuristic to detect the most likely "bulk", "isotope" and "petrography"
# sheets in an arbitrary workbook. The B.I.R.D.S template uses ``Data``,
# ``Isotopes`` and ``Petrography``; we also match a few common variants
# so user-renamed files still work. All comparisons are case-insensitive
# (see :func:`_first_match`).
_BULK_NAMES = ("Data", "Bulk", "Geochemistry", "Majors", "Samples")
_ISO_NAMES = ("Isotopes", "Isotope", "Iso", "Sr-Nd-Pb", "Radiogenic")
_PETRO_NAMES = ("Petrography", "Petrology", "Modal", "Modes",
                "Thin-section", "Thin sections", "Mineralogy")
_SKIP_NAMES = ("Instructions", "Reference", "Glossary", "README", "Help",
               "Notes", "Metadata")


def _first_match(candidates, preferred) -> Optional[str]:
    """Return the first candidate (case-insensitive) appearing in *preferred*."""
    wanted = {n.lower() for n in preferred}
    return next((c for c in candidates if c.lower() in wanted), None)


class ImportDialog(QDialog):
    """Pick a file, preview it, then return the loaded ``DataFrame``."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Import geochemical dataset")
        self.resize(960, 620)

        self._path: Optional[Path] = None
        self._df: Optional[pd.DataFrame] = None
        # Per-sheet DataFrame cache so flipping the combos doesn't
        # re-read the workbook every time.
        self._sheet_cache: dict[str, pd.DataFrame] = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QLabel(
            "Select a CSV, TSV or Excel file containing your geochemical "
            "data. Each row should correspond to one sample, each column "
            "to an element / oxide concentration."
        )
        intro.setWordWrap(True)
        intro.setStyleSheet("color: #444;")
        layout.addWidget(intro)

        # File picker -------------------------------------------------------
        picker = QGroupBox("File")
        picker_layout = QHBoxLayout(picker)
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("No file selected")
        self.path_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        picker_layout.addWidget(self.path_edit, stretch=1)
        picker_layout.addWidget(browse_btn)
        layout.addWidget(picker)

        # Excel options -----------------------------------------------------
        self.excel_box = QGroupBox("Excel options")
        excel_layout = QFormLayout(self.excel_box)
        self.sheet_combo = QComboBox()
        self.sheet_combo.currentIndexChanged.connect(self._on_sheet_changed)
        excel_layout.addRow("Bulk sheet (samples × oxides / traces / REE):",
                            self.sheet_combo)

        self.iso_chk = QCheckBox(
            "Also import an Isotopes sheet and join it by Sample_Name"
        )
        self.iso_chk.toggled.connect(self._on_extra_toggle)
        excel_layout.addRow("", self.iso_chk)

        self.iso_combo = QComboBox()
        self.iso_combo.setEnabled(False)
        self.iso_combo.currentIndexChanged.connect(self._on_sheet_changed)
        excel_layout.addRow("Isotopes sheet:", self.iso_combo)

        self.petro_chk = QCheckBox(
            "Also import a Petrography sheet (modal mineralogy) and "
            "join it by Sample_Name"
        )
        self.petro_chk.toggled.connect(self._on_extra_toggle)
        excel_layout.addRow("", self.petro_chk)

        self.petro_combo = QComboBox()
        self.petro_combo.setEnabled(False)
        self.petro_combo.currentIndexChanged.connect(self._on_sheet_changed)
        excel_layout.addRow("Petrography sheet:", self.petro_combo)
        self.excel_box.setVisible(False)
        layout.addWidget(self.excel_box)

        # Detection limits ----------------------------------------------------
        bdl_box = QGroupBox("Below-detection values")
        bdl_layout = QFormLayout(bdl_box)
        self.bdl_combo = QComboBox()
        for pol in POLICIES:
            self.bdl_combo.addItem(POLICY_LABELS[pol], pol)
        self.bdl_combo.currentIndexChanged.connect(self._on_sheet_changed)
        bdl_layout.addRow("Values like '<0.5' or 'b.d.l.':", self.bdl_combo)
        layout.addWidget(bdl_box)

        # Preview -----------------------------------------------------------
        preview_box = QGroupBox("Preview (first 20 rows)")
        preview_layout = QVBoxLayout(preview_box)
        self.preview_table = QTableWidget(0, 0)
        self.preview_table.setAlternatingRowColors(True)
        preview_layout.addWidget(self.preview_table)
        self.summary_label = QLabel("No file loaded.")
        self.summary_label.setStyleSheet("color: #666;")
        preview_layout.addWidget(self.summary_label)
        layout.addWidget(preview_box, stretch=1)

        # Buttons -----------------------------------------------------------
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setText("Import")
        self.ok_button.setEnabled(False)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ------------------------------------------------------------------ API
    @property
    def path(self) -> Optional[Path]:
        return self._path

    @property
    def dataframe(self) -> Optional[pd.DataFrame]:
        return self._df

    @property
    def isotopes_dataframe(self) -> Optional[pd.DataFrame]:
        """Standalone Isotopes sheet (None if the user didn't pick one)."""
        return getattr(self, "_iso_df", None)

    @property
    def petrography_dataframe(self) -> Optional[pd.DataFrame]:
        """Standalone Petrography sheet (None if the user didn't pick one)."""
        return getattr(self, "_petro_df", None)

    @property
    def bdl_masks(self) -> dict:
        """Boolean masks marking cells substituted for below-detection
        markers, keyed ``"main"`` / ``"isotopes"`` / ``"petrography"``.
        Sheets without censored values are absent from the dict."""
        return getattr(self, "_bdl_masks", {})

    @property
    def bdl_limits(self) -> dict:
        """Reported detection limits behind those flags, same keys.  Kept
        so Data → Detection limits… can switch the substitution policy
        without a re-import."""
        return getattr(self, "_bdl_limits", {})

    @property
    def bdl_policy(self) -> str:
        return self.bdl_combo.currentData() or "half"

    # -------------------------------------------------------------- helpers
    def _browse(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self,
            "Select dataset",
            "",
            "Tabular data (*.csv *.tsv *.txt *.xls *.xlsx);;All files (*)",
        )
        if not path_str:
            return
        self._path = Path(path_str)
        self.path_edit.setText(str(self._path))
        suffix = self._path.suffix.lower()
        if suffix in {".xls", ".xlsx"}:
            self._load_excel()
        else:
            self.excel_box.setVisible(False)
            try:
                raw = read_tabular(self._path)
            except Exception as exc:  # noqa: BLE001
                QMessageBox.critical(self, "Read error", str(exc))
                self._df = None
                self.ok_button.setEnabled(False)
                return
            # Below-detection handling for the flat-file path.
            self._sheet_cache = {"__csv__": raw}
            self._iso_df = None
            self._petro_df = None
            self._apply_bdl_and_preview(raw, None, None)

    def _load_excel(self) -> None:
        if self._path is None:
            return
        try:
            sheets = list_excel_sheets(self._path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Read error", str(exc))
            return
        # New file → drop any cached sheet data from the previous one.
        self._sheet_cache.clear()
        # Drop documentation-only sheets from every selector (case-insensitive)
        skip = {n.lower() for n in _SKIP_NAMES}
        useful = [s for s in sheets if s.lower() not in skip]
        bulk_pick = _first_match(useful, _BULK_NAMES) or (
            useful[0] if useful else "")
        iso_pick = _first_match(useful, _ISO_NAMES)
        petro_pick = _first_match(useful, _PETRO_NAMES)

        for combo in (self.sheet_combo, self.iso_combo, self.petro_combo):
            combo.blockSignals(True)
            combo.clear()
            combo.addItems(useful)
            combo.blockSignals(False)
        if bulk_pick:
            self.sheet_combo.setCurrentText(bulk_pick)
        # Auto-enable each optional sheet when a matching candidate exists
        # and isn't already the bulk pick.
        has_iso = iso_pick is not None and iso_pick != bulk_pick
        self.iso_chk.setEnabled(has_iso)
        self.iso_chk.setChecked(has_iso)
        if iso_pick:
            self.iso_combo.setCurrentText(iso_pick)
        self.iso_combo.setEnabled(self.iso_chk.isChecked())

        has_petro = petro_pick is not None and petro_pick != bulk_pick
        self.petro_chk.setEnabled(has_petro)
        self.petro_chk.setChecked(has_petro)
        if petro_pick:
            self.petro_combo.setCurrentText(petro_pick)
        self.petro_combo.setEnabled(self.petro_chk.isChecked())

        self.excel_box.setVisible(True)
        self._on_sheet_changed(0)

    def _on_extra_toggle(self, _checked: bool) -> None:
        """Sync optional-sheet combo enabled state and refresh the preview."""
        self.iso_combo.setEnabled(self.iso_chk.isChecked())
        self.petro_combo.setEnabled(self.petro_chk.isChecked())
        self._on_sheet_changed(0)

    def _read_sheet_cached(self, sheet: str) -> pd.DataFrame:
        """Read *sheet* through :func:`read_tabular`, memoised per file."""
        cached = self._sheet_cache.get(sheet)
        if cached is not None:
            return cached
        df = read_tabular(self._path, sheet=sheet)
        self._sheet_cache[sheet] = df
        return df

    def _on_sheet_changed(self, _index: int) -> None:
        if self._path is None:
            return
        # Flat files (CSV/TSV) have no sheets — a policy-combo change
        # still lands here, so re-apply BDL on the cached raw table.
        if self._path.suffix.lower() not in {".xls", ".xlsx"}:
            raw = self._sheet_cache.get("__csv__")
            if raw is not None:
                self._iso_df = None
                self._petro_df = None
                self._apply_bdl_and_preview(raw, None, None)
            return
        bulk_sheet = self.sheet_combo.currentText()
        if not bulk_sheet:
            return
        try:
            joined = self._read_sheet_cached(bulk_sheet)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Read error", str(exc))
            self._df = None
            self.ok_button.setEnabled(False)
            return

        # Optional sheets (Isotopes, Petrography) are kept as independent
        # dataframes — NOT merged into the bulk frame by Sample_Name.
        # Each view reads its own sheet so a sample missing from the
        # bulk Data sheet still plots in Isotopes / Petrography.
        notes: list[str] = []
        self._iso_df: Optional[pd.DataFrame] = None
        self._petro_df: Optional[pd.DataFrame] = None
        for chk, combo, label in (
            (self.iso_chk,   self.iso_combo,   "Isotopes"),
            (self.petro_chk, self.petro_combo, "Petrography"),
        ):
            if not chk.isChecked():
                continue
            sheet_name = combo.currentText()
            if not sheet_name or sheet_name == bulk_sheet:
                continue
            try:
                extra = self._read_sheet_cached(sheet_name)
            except Exception as exc:                       # noqa: BLE001
                QMessageBox.warning(
                    self, f"{label} sheet",
                    f"Could not read '{sheet_name}': {exc}.\n"
                    "Continuing without it.",
                )
                continue
            extra = _clean_sheet(extra)
            if label == "Isotopes":
                self._iso_df = extra
            else:
                self._petro_df = extra
            n_rows = len(extra)
            n_cols = len(extra.columns)
            notes.append(
                f"{label}: {n_rows} row{'s' if n_rows != 1 else ''} × "
                f"{n_cols} columns (independent of Data sheet)."
            )

        self._apply_bdl_and_preview(joined, self._iso_df, self._petro_df,
                                     extra_notes=notes)

    def _apply_bdl_and_preview(
        self,
        bulk: pd.DataFrame,
        iso: Optional[pd.DataFrame],
        petro: Optional[pd.DataFrame],
        extra_notes: Optional[list] = None,
    ) -> None:
        """Run below-detection conversion on every loaded sheet under the
        currently selected policy, store the masks, refresh the preview."""
        policy = self.bdl_policy
        notes = list(extra_notes or [])
        self._bdl_masks: dict = {}
        self._bdl_limits: dict = {}

        bulk_conv, bulk_mask, report = scan_and_convert(bulk, policy)
        self._df = bulk_conv
        if bulk_mask is not None:
            self._bdl_masks["main"] = bulk_mask
            self._bdl_limits["main"] = report.limits

        total = report.total
        for key, sheet_df in (("isotopes", iso), ("petrography", petro)):
            if sheet_df is None:
                continue
            conv, mask, rep = scan_and_convert(sheet_df, policy)
            if key == "isotopes":
                self._iso_df = conv
            else:
                self._petro_df = conv
            if mask is not None:
                self._bdl_masks[key] = mask
                self._bdl_limits[key] = rep.limits
            total += rep.total

        if total:
            notes.append(
                f"⚠ {total} below-detection value{'s' if total != 1 else ''} "
                f"converted ({POLICY_LABELS.get(policy, policy)})."
            )
        self._populate_preview(extra_note="  ·  ".join(notes))

    def _populate_preview(self, extra_note: str = "") -> None:
        if self._df is None:
            return
        df = self._df
        preview = df.head(20)
        self.preview_table.clear()
        self.preview_table.setColumnCount(len(preview.columns))
        self.preview_table.setRowCount(len(preview.index))
        self.preview_table.setHorizontalHeaderLabels([str(c) for c in preview.columns])
        for r in range(len(preview.index)):
            for c in range(len(preview.columns)):
                value = preview.iloc[r, c]
                text = "" if pd.isna(value) else str(value)
                self.preview_table.setItem(r, c, QTableWidgetItem(text))
        self.preview_table.resizeColumnsToContents()

        numeric_n = len(df.select_dtypes(include="number").columns)
        summary = (f"{len(df)} rows × {len(df.columns)} columns "
                   f"— {numeric_n} numeric column"
                   f"{'s' if numeric_n != 1 else ''}.")
        if extra_note:
            summary += "  •  " + extra_note
        self.summary_label.setText(summary)
        self.ok_button.setEnabled(True)


# ---------------------------------------------------------------------------
# Helpers (module-level — easier to unit-test)
# ---------------------------------------------------------------------------

def _merge_extra_sheet(base: pd.DataFrame, extra: pd.DataFrame,
                        label: str) -> tuple[pd.DataFrame, str]:
    """Left-join *extra* into *base* using ``Sample_Name`` as the key.

    Returns ``(merged_df, note)`` where *note* summarises how many
    samples picked up the new data — useful for the preview footer.
    Falls back gracefully when ``Sample_Name`` is absent (no merge done,
    the optional sheet is silently ignored). *label* is the user-facing
    name shown in the message (``"Isotopes"`` or ``"Petrography"``).

    Identifier columns (``Sample_Label``, ``Group``) are *coalesced*
    instead of overwritten: a non-empty value on the Data sheet wins,
    but if Data leaves them blank the value from the extra sheet fills
    in.  That way the user can declare Group / Label on whichever sheet
    is most convenient and every view (Isotopes, Petrography, …) gets
    the same labels.
    """
    if "Sample_Name" not in base.columns or "Sample_Name" not in extra.columns:
        return (base,
                f"⚠  {label} sheet ignored: 'Sample_Name' key missing.")

    # Columns that should be coalesced rather than overwritten.  These
    # are the user-visible identifiers Edit-plot uses to colour/legend
    # samples.  Anything else from the extra sheet that already exists
    # in base is dropped to keep the merge clean.
    coalesce_cols = {"Sample_Label", "Group"}
    overlap = set(base.columns) & set(extra.columns) - {"Sample_Name"}
    drop_cols = overlap - coalesce_cols
    extra_clean = extra.drop(columns=list(drop_cols), errors="ignore")
    # Drop empty rows in the extra sheet (otherwise the merge would
    # overwrite Sample_Label / Group with NaN for samples that lack a
    # row in extra).
    extra_clean = extra_clean[extra_clean["Sample_Name"].notna()].copy()

    # For the coalesce columns, rename the extra version so the merge
    # gives us both copies side by side, then fillna() from extra.
    rename_map = {c: f"{c}__extra" for c in coalesce_cols & set(extra_clean.columns)}
    if rename_map:
        extra_clean = extra_clean.rename(columns=rename_map)

    merged = base.merge(extra_clean, on="Sample_Name", how="left",
                         suffixes=("", "_extra"))

    filled_msg = ""
    for col, extra_col in rename_map.items():
        if extra_col not in merged.columns:
            continue
        if col not in merged.columns:
            # Base didn't have it at all — promote the extra column.
            merged[col] = merged[extra_col]
        else:
            # Treat empty strings as missing too (Excel cells often
            # come back as "" rather than NaN).
            def _empty(s):
                return s.isna() | (s.astype(str).str.strip() == "")
            base_empty = _empty(merged[col])
            extra_has = ~_empty(merged[extra_col])
            base_series = merged[col].where(~base_empty)
            filled = base_series.fillna(merged[extra_col])
            n_filled = int((base_empty & extra_has).sum())
            if n_filled:
                filled_msg += f", {n_filled} '{col}' filled"
            merged[col] = filled
        merged = merged.drop(columns=[extra_col])

    matched = extra_clean["Sample_Name"].isin(base["Sample_Name"]).sum()
    new_cols = len(extra_clean.columns) - 1 - len(rename_map)  # exclude key + renamed
    return (merged,
            f"{label}: {matched} sample"
            f"{'s' if matched != 1 else ''} matched, "
            f"+{new_cols} column{'s' if new_cols != 1 else ''}"
            f"{filled_msg}.")


def _clean_sheet(df: pd.DataFrame) -> pd.DataFrame:
    """Drop fully empty rows from an imported sheet.

    Excel templates always come with a couple of trailing blank rows;
    leaving them in inflates ``len(df)`` and pollutes ``get_groups``
    with anonymous NaN entries.  We treat a row as empty when every
    cell is NaN or the empty string.
    """
    if df is None or df.empty:
        return df
    mask = df.apply(
        lambda row: any(
            pd.notna(v) and (not isinstance(v, str) or v.strip() != "")
            for v in row
        ),
        axis=1,
    )
    return df[mask].reset_index(drop=True)
