"""Robust tabular-data loader.

Handles the common quirks of real-world geochemical datasets:

* Excel files (.xls, .xlsx) including multi-sheet workbooks.
* CSV files with delimiter ``,``, ``;``, ``\\t`` or ``|`` (auto-detected).
* Encodings UTF-8 (with or without BOM), Latin-1 and Windows-1252.
* European number format (decimal comma) — string columns that look numeric
  after replacing ``,`` with ``.`` are converted to ``float``.
* Stray whitespace around column names is stripped.
* Comment lines beginning with ``#`` at the top of the file are skipped.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Optional

import pandas as pd


# Encodings tried in order. The BOM-aware variant comes first because Excel on
# Windows often saves CSV with a UTF-8 BOM.
ENCODINGS = ("utf-8-sig", "utf-8", "latin-1", "cp1252")

# Candidate delimiters tried during sniffing.
DELIMITERS = (",", ";", "\t", "|")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_excel_sheets(path: str | Path) -> list[str]:
    """Return the sheet names of an Excel workbook."""
    return pd.ExcelFile(path).sheet_names


def read_tabular(path: str | Path,
                 sheet: Optional[str] = None) -> pd.DataFrame:
    """Read *path* into a :class:`pandas.DataFrame`.

    Excel, CSV, TSV and plain text files are supported. The function tries
    multiple delimiters and encodings until a non-empty, multi-column frame is
    produced; it also attempts to convert object columns containing European
    decimal commas to ``float``.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in {".xls", ".xlsx"}:
        df = (pd.read_excel(path, sheet_name=sheet)
              if sheet else pd.read_excel(path))
    elif suffix == ".tsv":
        df = _read_csv_text(path, default_sep="\t")
    else:
        df = _read_csv_text(path)

    return _clean_dataframe(df)


# ---------------------------------------------------------------------------
# Internals
# ---------------------------------------------------------------------------

def _read_csv_text(path: Path,
                   default_sep: Optional[str] = None) -> pd.DataFrame:
    """Try several (encoding, delimiter) combinations until one succeeds."""
    last_error: Optional[Exception] = None

    for enc in ENCODINGS:
        try:
            with open(path, encoding=enc, errors="strict") as fh:
                sample = fh.read(32768)
        except UnicodeDecodeError as exc:
            last_error = exc
            continue
        except OSError as exc:
            raise exc

        sep = default_sep
        if sep is None:
            sep = _sniff_delimiter(sample)

        # First attempt with the (sniffed or default) delimiter
        try:
            df = pd.read_csv(
                path,
                sep=sep,
                encoding=enc,
                engine="python",
                comment="#",
                skip_blank_lines=True,
            )
            if df.shape[1] > 1 or default_sep is not None:
                return df
        except Exception as exc:  # noqa: BLE001
            last_error = exc

        # Fallback: brute-force the remaining delimiter candidates
        for alt in DELIMITERS:
            if alt == sep:
                continue
            try:
                df = pd.read_csv(
                    path,
                    sep=alt,
                    encoding=enc,
                    engine="python",
                    comment="#",
                    skip_blank_lines=True,
                )
                if df.shape[1] > 1:
                    return df
            except Exception as exc:  # noqa: BLE001
                last_error = exc

    if last_error is not None:
        raise ValueError(
            f"Could not read {path.name}: {last_error}. Try saving the file "
            "as UTF-8 CSV with comma or semicolon separators."
        )
    raise ValueError(f"Could not read {path.name}: unknown error.")


def _sniff_delimiter(sample: str) -> str:
    """Return the most likely delimiter for *sample* (defaults to ``,``)."""
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(DELIMITERS))
        return dialect.delimiter
    except csv.Error:
        # Fall back to the delimiter that splits the first line into the most
        # fields; ties prefer comma, then semicolon, then tab.
        first_line = sample.splitlines()[0] if sample else ""
        counts = {d: first_line.count(d) for d in DELIMITERS}
        ordered = sorted(counts.items(), key=lambda kv: (-kv[1], DELIMITERS.index(kv[0])))
        best = ordered[0]
        return best[0] if best[1] > 0 else ","


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Strip column names; convert decimal-comma columns to numeric."""
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]

    for col in df.columns:
        # Skip columns that are already numeric.
        if pd.api.types.is_numeric_dtype(df[col]):
            continue
        as_str = df[col].astype("string").str.strip()
        contains_comma = as_str.str.contains(",", na=False).any()
        # Two candidates: keep dots (US format) or convert comma -> dot.
        candidates = []
        candidates.append(("as-is", pd.to_numeric(as_str, errors="coerce")))
        if contains_comma:
            normalised = as_str.str.replace(",", ".", regex=False)
            candidates.append(("comma->dot", pd.to_numeric(normalised, errors="coerce")))
        # Pick the candidate that converted the most non-null values.
        non_null = as_str.notna().sum()
        if non_null == 0:
            continue
        best = max(candidates, key=lambda kv: kv[1].notna().sum())
        if best[1].notna().sum() >= 0.7 * non_null:
            df[col] = best[1]

    return df
