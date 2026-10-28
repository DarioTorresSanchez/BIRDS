"""The README's pictures are in the repository, light, and truthful.

Every local image the README shows must exist (a renamed file leaves a
broken picture on the project page), the screenshots stay small enough
for the page to load quickly, and the caption's count of mafic volcanic
schemes is the menu's.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")
LOCAL = [src for src in re.findall(r'<img src="([^"]+)"', README)
         if not src.startswith("http")]


def test_the_readme_shows_the_screenshots():
    shots = [s for s in LOCAL if s.startswith("docs/screenshots/")]
    assert len(shots) == 4


@pytest.mark.parametrize("src", LOCAL)
def test_every_local_image_exists(src):
    assert (ROOT / src).is_file(), src


@pytest.mark.parametrize("src", [s for s in LOCAL
                                 if s.startswith("docs/screenshots/")])
def test_screenshots_stay_light(src):
    assert (ROOT / src).stat().st_size < 400_000, src


def test_every_screenshot_in_the_folder_is_shown():
    shown = {Path(s).name for s in LOCAL}
    for path in (ROOT / "docs" / "screenshots").glob("*.png"):
        assert path.name in shown, path.name


def test_the_caption_counts_the_mafic_volcanic_schemes():
    from birds.diagrams.catalog import TECTONIC_VOLCANIC
    n = len(TECTONIC_VOLCANIC["Mafic"])
    assert f"{n} schemes for mafic volcanic rocks alone" in README
