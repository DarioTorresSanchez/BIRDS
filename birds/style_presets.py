"""Reusable plot-style presets (``.birdstyle`` files).

A session (``.birds``) carries the data, the diagrams and the styling
all together — great for resuming work, useless for keeping the same
symbology across *different* projects.  A style preset is the styling
alone: point size, transparency, grouping columns and the per-group
colour / marker / visibility flags, in a small JSON file you can drop
next to a manuscript so every figure in the paper matches.

Applying a preset to a dataset whose groups differ is intentionally
forgiving — see :func:`apply_preset`.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .plot_style import PlotStyle

STYLE_EXT = ".birdstyle"
_FORMAT = "birds-style"
_VERSION = 1


class StylePresetError(RuntimeError):
    """Raised when a preset file cannot be read or is not a preset."""


def save_preset(path: str | Path, style: PlotStyle,
                name: str = "") -> Path:
    """Write *style* to *path* as a ``.birdstyle`` JSON file."""
    path = Path(path)
    if path.suffix.lower() != STYLE_EXT:
        path = path.with_suffix(STYLE_EXT)
    payload = {
        "format": _FORMAT,
        "version": _VERSION,
        "name": name or path.stem,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "style": style.to_dict(),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False),
                    encoding="utf-8")
    return path


def load_preset(path: str | Path) -> tuple[PlotStyle, str]:
    """Read a ``.birdstyle`` file.  Returns ``(style, preset_name)``."""
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StylePresetError(f"Could not read '{path.name}': {exc}") from exc
    if not isinstance(payload, dict) or payload.get("format") != _FORMAT:
        raise StylePresetError(
            f"'{path.name}' is not a B.I.R.D.S style preset.")
    data = payload.get("style")
    if not isinstance(data, dict):
        raise StylePresetError(f"'{path.name}' carries no style block.")
    return PlotStyle.from_dict(data), str(payload.get("name") or path.stem)


def apply_preset(target: PlotStyle, preset: PlotStyle,
                 keep_group_columns: bool = False) -> str:
    """Apply *preset* onto the live *target* style, in place.

    The live style object is mutated (never rebound) so every view's
    reference stays valid, exactly like session loading does.

    *keep_group_columns* preserves the grouping columns already chosen
    for the current dataset — the usual case when the new project uses
    a differently-named group column but you still want the preset's
    colours.  In that mode the preset's group **looks** are matched to
    the existing groups **by position**, and any extra groups the
    preset defines are appended so their colours are available if the
    dataset later grows.

    Returns a short human-readable summary of what happened.
    """
    if not keep_group_columns:
        target.copy_from(preset)
        return (f"Applied preset: {len(preset.groups)} group styles, "
                f"grouping by {', '.join(preset.group_columns) or '—'}.")

    columns = list(target.group_columns)
    names = [g.name for g in target.groups]
    target.copy_from(preset)
    target.group_columns = columns
    # Re-attach the dataset's own group names to the preset's looks.
    for i, original_name in enumerate(names):
        if i < len(target.groups):
            target.groups[i].name = original_name
    kept = min(len(names), len(preset.groups))
    extra = max(len(preset.groups) - len(names), 0)
    msg = (f"Applied preset colours to {kept} existing group"
           f"{'s' if kept != 1 else ''}")
    if extra:
        msg += f" (+{extra} spare style{'s' if extra != 1 else ''} kept)"
    return msg + "; grouping columns left unchanged."


def preset_dir() -> Path:
    """Default folder offered by the save / load dialogs."""
    home = Path.home() / ".birds" / "styles"
    home.mkdir(parents=True, exist_ok=True)
    return home
