"""Lightweight container for the active geochemical dataset."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

from .io_utils import read_tabular


class DataManager:
    """Holds the currently loaded sample table and provides I/O helpers.

    Three independent dataframes:

    * ``df``             — main bulk-composition Data sheet
    * ``isotopes_df``    — standalone Isotopes sheet (if imported)
    * ``petrography_df`` — standalone Petrography sheet (if imported)

    The three sheets are NOT auto-merged by ``Sample_Name``; each view
    reads from its own dataframe.  This lets the user keep parallel
    sample lists in each sheet (e.g. a Sr-Nd analysis that doesn't
    correspond to a row in the bulk Data sheet still plots in the
    Isotopes view).
    """

    def __init__(self) -> None:
        self.path: Optional[Path] = None
        self.df: Optional[pd.DataFrame] = None
        # Standalone copies of the secondary sheets — independent of
        # ``df``.  Views fall back to ``df`` when these are None.
        self.isotopes_df: Optional[pd.DataFrame] = None
        self.petrography_df: Optional[pd.DataFrame] = None
        # Below-detection masks keyed "main" / "isotopes" / "petrography"
        # (boolean frames aligned to each sheet; see detection_limits.py).
        self.bdl_masks: dict[str, pd.DataFrame] = {}
        # Reported detection limits behind those flags, same keys — kept
        # so the substitution policy can be switched after the import.
        self.bdl_limits: dict[str, pd.DataFrame] = {}
        self.bdl_policy: str = "half"

    def realign_bdl_masks(self) -> None:
        """Trim the below-detection masks to the sheets as they stand now.

        Pre-processing rewrites ``df`` — it adds FeOt / adjusted columns
        and can drop others — which leaves the masks describing a table
        that no longer exists.  Nothing crashes (lookups are by column
        name) but the flag count reported at import time and stored in
        the session drifts away from what the data table can actually
        show.  Realigning keeps every mask a strict subset of its sheet.
        """
        sheets = {
            "main": self.df,
            "isotopes": self.isotopes_df,
            "petrography": self.petrography_df,
        }
        for key, mask in list(self.bdl_masks.items()):
            frame = sheets.get(key)
            if frame is None or mask is None:
                self.bdl_masks.pop(key, None)
                self.bdl_limits.pop(key, None)
                continue
            cols = [c for c in mask.columns if c in frame.columns]
            if not cols:
                self.bdl_masks.pop(key, None)
                self.bdl_limits.pop(key, None)
                continue
            trimmed = mask.loc[mask.index.isin(frame.index), cols]
            trimmed = trimmed.reindex(index=frame.index, fill_value=False)
            self.bdl_masks[key] = trimmed.astype(bool)
            limits = self.bdl_limits.get(key)
            if limits is not None:
                lim_cols = [c for c in limits.columns if c in frame.columns]
                self.bdl_limits[key] = (
                    limits.loc[limits.index.isin(frame.index), lim_cols]
                    .reindex(index=frame.index))

    def load(self, path: str | Path, sheet: Optional[str] = None) -> pd.DataFrame:
        df = read_tabular(path, sheet=sheet)
        self.df = df
        self.path = Path(path)
        return df

    def save(self, path: str | Path) -> None:
        if self.df is None:
            raise RuntimeError("No dataset is loaded.")
        path = Path(path)
        suffix = path.suffix.lower()
        if suffix in {".xls", ".xlsx"}:
            self.df.to_excel(path, index=False)
        else:
            self.df.to_csv(path, index=False)

    @property
    def is_loaded(self) -> bool:
        return self.df is not None and not self.df.empty
