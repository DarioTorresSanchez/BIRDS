"""Every link to the repository names the same one.

Before the first push the README and INSTALL carried ``<your-username>``
and pyproject.toml a user that was not the project's.  All of them now
point at github.com/DarioTorresSanchez/BIRDS.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPO = "https://github.com/DarioTorresSanchez/BIRDS"
FILES = ("README.md", "INSTALL.md", "pyproject.toml", "CITATION.cff",
         "packaging/README.md")


@pytest.mark.parametrize("name", FILES)
def test_no_placeholder_is_left(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    assert "<your-username>" not in text


@pytest.mark.parametrize("name", FILES)
def test_every_github_link_is_the_projects(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    for url in re.findall(r"https://github\.com/[\w.-]+/[\w.-]+", text):
        assert url.removesuffix(".git") == REPO, (name, url)


def test_the_citation_file_names_the_repository():
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert f'repository-code: "{REPO}"' in text


AUTHOR = "Darío Torres Sánchez"


@pytest.mark.parametrize("name, expected", [
    ("pyproject.toml", f'name = "{AUTHOR}"'),
    ("LICENSE", f"Copyright (c) 2026 {AUTHOR}"),
    ("packaging/windows/birds.iss", f"AppPublisher={AUTHOR}"),
    ("README.md", "author  = {Torres Sánchez, Darío}"),
    ("README.md", "> Torres Sánchez, D. (2026)."),
])
def test_the_author_is_named_the_same_everywhere(name, expected):
    assert expected in (ROOT / name).read_text(encoding="utf-8")


def test_the_citation_file_author():
    text = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "given-names: Darío" in text
    assert "family-names: Torres Sánchez" in text
    assert "family-names: Torres\n" not in text
