"""Session persistence for B.I.R.D.S — the ``.birds`` file format.

A *session* captures the entire user-visible state of the application:

* the imported dataset (and the optional Isotopes / Petrography sheets);
* the shared :class:`birds.plot_style.PlotStyle` (groups, colours,
  visibility, ordering);
* the per-view UI state (selected diagrams, axis labels, font sizes,
  reservoirs, expressions, …) — collected via each view's
  :py:meth:`serialize` method;
* optional cached results (CIPW table, statistics, anomalies) so the
  user doesn't have to recompute when reopening;
* the window geometry + splitter sizes + currently active view.

On disk it is a single ZIP file with the ``.birds`` extension:

.. code-block:: text

    mi_proyecto.birds
    ├── manifest.json
    ├── data/
    │   ├── main.parquet
    │   ├── isotopes.parquet     (optional)
    │   └── petrography.parquet  (optional)
    ├── style/plot_style.json
    ├── views/<view-name>.json   ×9
    ├── results/                 (optional)
    │   ├── cipw.parquet
    │   ├── anomalies.parquet
    │   ├── ratios.parquet
    │   └── tectonic.parquet
    └── ui/window.json

Design choices
--------------
*ZIP* — single file the user can email / archive / cite, inspectable
with any unzip tool, future-proof via the ``version`` field of
``manifest.json``.

*Parquet* for DataFrames — 5-10× smaller than CSV, preserves dtypes
exactly (no string-to-datetime drift), accepted by every modern
pandas install.

*JSON* for settings — human readable, easy to diff, no security risk
from arbitrary code execution (unlike pickle).

*Atomic write* — the file is written to ``<path>.tmp`` first and then
moved with :func:`os.replace`, so a crash mid-write leaves the previous
file untouched.
"""

from __future__ import annotations

import io
import json
import os
import platform
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

# Bump this whenever the on-disk schema changes in a non-backward-
# compatible way; ``load_session`` calls :func:`_migrate` to upgrade
# older files in-memory before handing them back.
SESSION_VERSION = 1

# File extension used for B.I.R.D.S session files.
SESSION_EXT = ".birds"

# The list of view modules that participate in session save / restore.
# Keys must match the module name; values are the file name used inside
# the ZIP (without the .json suffix).  Adding a new view here is a 1-line
# change and the rest of the machinery picks it up automatically.
VIEW_FILES: tuple[str, ...] = (
    "bivariate",
    "spider",
    "classification",
    "tectonic",
    "petrography",
    "isotopes",
    "norm",
    "map",
    "statistics",
)

# Same idea for cached result DataFrames.
RESULT_FILES: tuple[str, ...] = (
    "cipw",
    "anomalies",
    "ratios",
    "tectonic",
)


class SessionError(RuntimeError):
    """Raised when a session file cannot be opened or written."""


@dataclass
class SessionState:
    """In-memory snapshot of the application state.

    Attributes
    ----------
    version
        Schema version that *produced* this state (not necessarily the
        current ``SESSION_VERSION`` — handy when migrating).
    data
        Mapping of sheet name → DataFrame.  Always contains ``"main"``
        for an actually-saved session; ``"isotopes"`` and
        ``"petrography"`` are present only when the user imported them.
    plot_style
        Output of :py:meth:`PlotStyle.to_dict`.
    views
        Mapping of view-module name → per-view state ``dict``.  See each
        view's ``serialize()`` for the schema.
    results
        Optional cached result tables keyed by name (e.g. ``"cipw"``).
        Skipped when ``None`` to keep the file small.
    ui
        Window geometry, splitter sizes, active view, etc.
    saved_at
        ISO-8601 UTC timestamp set on write.
    app_version
        Version string of the running app, recorded for diagnostics.
    """

    version: int = SESSION_VERSION
    data: Dict[str, pd.DataFrame] = field(default_factory=dict)
    plot_style: dict = field(default_factory=dict)
    views: Dict[str, dict] = field(default_factory=dict)
    results: Dict[str, pd.DataFrame] = field(default_factory=dict)
    ui: dict = field(default_factory=dict)
    saved_at: str = ""
    app_version: str = "B.I.R.D.S 1.0"


# ---------------------------------------------------------------------------
# Public save / load API
# ---------------------------------------------------------------------------

def save_session(path: str | Path, state: SessionState) -> None:
    """Write *state* to *path* atomically.

    The file is created in the same directory as *path* with a
    ``.partial`` suffix, then moved into place with :func:`os.replace`
    on success.  A crash during the write therefore leaves any previous
    session file untouched.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Stamp the state with the current time / app version before writing.
    state.saved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    tmp = path.with_suffix(path.suffix + ".partial")
    try:
        _write_zip(tmp, state)
        os.replace(tmp, path)
    except Exception:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:
                pass
        raise


def load_session(path: str | Path) -> SessionState:
    """Read a ``.birds`` file from *path* and return its
    :class:`SessionState`.

    Older versions of the on-disk schema are migrated transparently via
    :func:`_migrate`.
    """
    path = Path(path)
    if not path.exists():
        raise SessionError(f"Session file not found: {path}")

    try:
        with zipfile.ZipFile(path, "r") as zf:
            return _read_zip(zf)
    except zipfile.BadZipFile as exc:
        raise SessionError(f"Not a valid .birds file: {path} ({exc})") from exc


# ---------------------------------------------------------------------------
# Low-level ZIP I/O
# ---------------------------------------------------------------------------

def _write_zip(path: Path, state: SessionState) -> None:
    with zipfile.ZipFile(
        path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
    ) as zf:
        # manifest.json — first entry, easy to find when inspecting
        manifest = {
            "version": SESSION_VERSION,
            "app": state.app_version,
            "saved_at": state.saved_at,
            "platform": f"{platform.system()} {platform.release()}",
            "python": sys.version.split()[0],
            "pandas": pd.__version__,
            "data_sheets": sorted(state.data.keys()),
            "result_sheets": sorted(state.results.keys()),
            "views": sorted(state.views.keys()),
        }
        _write_json(zf, "manifest.json", manifest)

        # Data sheets
        for name, df in state.data.items():
            if df is None or df.empty:
                continue
            _write_parquet(zf, f"data/{name}.parquet", df)

        # Plot style
        if state.plot_style:
            _write_json(zf, "style/plot_style.json", state.plot_style)

        # Per-view settings
        for name, view_state in state.views.items():
            if view_state:
                _write_json(zf, f"views/{name}.json", view_state)

        # Optional result caches
        for name, df in state.results.items():
            if df is None or df.empty:
                continue
            _write_parquet(zf, f"results/{name}.parquet", df)

        # Window geometry / UI state
        if state.ui:
            _write_json(zf, "ui/window.json", state.ui)


def _read_zip(zf: zipfile.ZipFile) -> SessionState:
    names = set(zf.namelist())

    # 1. Manifest — required, drives the rest.
    if "manifest.json" not in names:
        raise SessionError("manifest.json missing — file is not a .birds session.")
    manifest = _read_json(zf, "manifest.json")
    version = int(manifest.get("version", 1))

    state = SessionState(
        version=version,
        saved_at=manifest.get("saved_at", ""),
        app_version=manifest.get("app", "unknown"),
    )

    # 2. Data sheets — accept both .parquet AND .csv (the fallback path
    # of ``_write_parquet`` switches to .csv when pyarrow refuses the
    # DataFrame).
    for name in names:
        if name.startswith("data/") and (
            name.endswith(".parquet") or name.endswith(".csv")
        ):
            sheet = Path(name).stem
            state.data[sheet] = _read_parquet(zf, name)

    # 3. Plot style
    if "style/plot_style.json" in names:
        state.plot_style = _read_json(zf, "style/plot_style.json")

    # 4. Views
    for name in names:
        if name.startswith("views/") and name.endswith(".json"):
            view_name = Path(name).stem
            state.views[view_name] = _read_json(zf, name)

    # 5. Result caches — same .parquet OR .csv tolerance as data sheets.
    for name in names:
        if name.startswith("results/") and (
            name.endswith(".parquet") or name.endswith(".csv")
        ):
            key = Path(name).stem
            state.results[key] = _read_parquet(zf, name)

    # 6. UI
    if "ui/window.json" in names:
        state.ui = _read_json(zf, "ui/window.json")

    # 7. Migrate if needed.
    if version < SESSION_VERSION:
        state = _migrate(state, from_version=version)

    return state


# ---------------------------------------------------------------------------
# Format helpers (JSON / Parquet)
# ---------------------------------------------------------------------------

def _write_json(zf: zipfile.ZipFile, arcname: str, obj: dict) -> None:
    payload = json.dumps(obj, indent=2, ensure_ascii=False, default=_json_default)
    zf.writestr(arcname, payload.encode("utf-8"))


def _read_json(zf: zipfile.ZipFile, arcname: str) -> dict:
    with zf.open(arcname) as fh:
        return json.loads(fh.read().decode("utf-8"))


def _coerce_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    """Make a DataFrame safe for the strict pyarrow Parquet writer.

    PyArrow raises ``ArrowTypeError`` whenever an ``object``-dtype column
    contains values of more than one Python type (e.g. ``Sample_Name``
    that ends up with a mix of ``"S01"`` strings and bare ``5`` integers
    after a CSV / XLSX import).  The fix is simple: cast every value in
    such columns to ``str`` while preserving ``NaN``.  Pure-string and
    purely-numeric columns are left alone so dtypes are not lost.
    """
    out = df.copy()
    for col in out.columns:
        if out[col].dtype != object:
            continue
        # Inspect non-null entries to decide whether to coerce.
        non_null = out[col].dropna()
        if non_null.empty:
            continue
        types = {type(v) for v in non_null}
        # Coerce when more than one Python type lives in the column, or
        # when the lone type isn't already str / bytes (e.g. mix of
        # Timestamp + str, or Decimal + float).
        if len(types) > 1 or not types.issubset({str, bytes}):
            mask = out[col].notna()
            out.loc[mask, col] = out.loc[mask, col].astype(str)
    return out


def _write_parquet(zf: zipfile.ZipFile, arcname: str, df: pd.DataFrame) -> None:
    """Write a DataFrame as parquet into the ZIP archive.

    pandas' ``to_parquet`` doesn't accept a zip-file-handle directly, so
    we go through an in-memory buffer.  Falls back to CSV (uncompressed
    inside the already-compressed ZIP) when:

    * the user's pandas install has no parquet engine, OR
    * pyarrow / fastparquet refuse the data (``ArrowTypeError``,
      ``ArrowInvalid``, …).  Those inherit from ``Exception`` but not
      from ``ValueError``, so we deliberately use a broad except clause
      here.  A failed save is a much worse user experience than a CSV
      fallback that is otherwise indistinguishable to the reader.
    """
    arc = arcname
    buf = io.BytesIO()
    try:
        _coerce_for_parquet(df).to_parquet(buf, index=True)
    except Exception:
        # Anything wrong → fall back to CSV inside the ZIP.
        buf = io.BytesIO()
        df.to_csv(buf, index=True)
        arc = arcname.replace(".parquet", ".csv")
    zf.writestr(arc, buf.getvalue())


def _read_parquet(zf: zipfile.ZipFile, arcname: str) -> pd.DataFrame:
    with zf.open(arcname) as fh:
        data = fh.read()
    # The fallback path may have written .csv instead of .parquet.
    if arcname.endswith(".csv"):
        return pd.read_csv(io.BytesIO(data), index_col=0)
    try:
        return pd.read_parquet(io.BytesIO(data))
    except Exception:
        # Some old sessions might have CSV bytes stored under a
        # .parquet name; try that as a last resort.
        return pd.read_csv(io.BytesIO(data), index_col=0)


def _json_default(obj):
    """Make Path / numpy scalars / pandas Timestamps JSON-safe."""
    import numpy as np

    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.ndarray,)):
        return obj.tolist()
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# ---------------------------------------------------------------------------
# Schema migration
# ---------------------------------------------------------------------------

def _migrate(state: SessionState, from_version: int) -> SessionState:
    """Upgrade an older state in-memory to the current schema.

    Each ``if from_version < N`` block is one migration step.  We do
    nothing for v1 → v1 (current).  Add steps here as the schema evolves.
    """
    # Example for the future:
    # if from_version < 2:
    #     state.views.setdefault("statistics", {}).setdefault("normaliser", "Sun & McDonough (1989) – CI")
    state.version = SESSION_VERSION
    return state


# ---------------------------------------------------------------------------
# Auto-save support
# ---------------------------------------------------------------------------

def autosave_dir() -> Path:
    """Return the directory used for auto-saves, creating it if needed."""
    home = Path.home() / ".birds"
    home.mkdir(parents=True, exist_ok=True)
    return home


def autosave_path() -> Path:
    """Canonical location of the rolling auto-save file."""
    return autosave_dir() / f"autosave{SESSION_EXT}"


def autosave_backup_path() -> Path:
    """Backup of the previous auto-save (kept so a corrupt latest one
    doesn't lose the user's work)."""
    return autosave_dir() / f"autosave{SESSION_EXT}.bak"


def rotate_autosave(new_state: SessionState) -> None:
    """Write *new_state* to the autosave slot, rotating the previous
    file into the .bak slot first.  Atomic, like :func:`save_session`."""
    primary = autosave_path()
    backup = autosave_backup_path()

    # Rotate: move existing primary → backup
    if primary.exists():
        try:
            shutil.copy2(primary, backup)
        except OSError:
            pass  # not fatal — at worst we lose the previous .bak

    save_session(primary, new_state)


def clear_autosave() -> None:
    """Delete both the primary autosave file and the ``.bak`` backup.

    Called after a clean exit (no pending changes) or after a successful
    manual ``save_session`` so the recovery dialog does NOT appear on the
    next launch.  Missing files are silently ignored — clearing an
    already-clean state is a no-op.
    """
    for p in (autosave_path(), autosave_backup_path()):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass  # benign — recovery dialog will just skip a stale file
