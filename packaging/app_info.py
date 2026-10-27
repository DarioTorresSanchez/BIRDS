"""What the packaged application declares to the operating system.

Read by ``birds.spec`` (PyInstaller) and by the tests, so the bundle and
the checks cannot drift apart.

The bundle identifier and the session type identifier are how macOS
remembers which app owns ``.birds`` files.  Change them only before the
first public release: after it, a new identifier is a different app as
far as every installed copy is concerned.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ICONS = Path(__file__).resolve().parent / "icons"

APP_NAME = "BIRDS"                      # file names: BIRDS.app, BIRDS.exe
DISPLAY_NAME = "B.I.R.D.S"
BUNDLE_ID = "io.github.dariotorressanchez.birds"

#: Identifiers B.I.R.D.S was built under before, so that an installed
#: copy carrying one is still recognised as B.I.R.D.S and replaced.
PREVIOUS_BUNDLE_IDS = ("io.github.dariotorres.birds",)

SESSION_EXTENSION = "birds"             # birds.session.SESSION_EXT, no dot
SESSION_UTI = f"{BUNDLE_ID}.session"
SESSION_DESCRIPTION = "B.I.R.D.S session"
SESSION_MIME = "application/x-birds-session"

APP_ICON = "birds_app"
DOCUMENT_ICON = "birds_document"


def version() -> str:
    """The version in birds/__init__.py, read without importing Qt."""
    text = (ROOT / "birds" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else "0.0.0"


def bundle_version() -> str:
    """The version as macOS takes it: numbers and dots only, so a beta
    such as 0.1.0b1 is declared as 0.1.0."""
    return re.match(r"\d+(?:\.\d+)*", version()).group(0)


#: The bundled Qt needs macOS 13 (its frameworks are built for it); an
#: older Mac is told so by Finder instead of watching the app crash.
MINIMUM_MACOS = "13.0"


def info_plist() -> dict:
    """The keys macOS reads from BIRDS.app/Contents/Info.plist.

    ``UTExportedTypeDeclarations`` defines the session type -- a
    ``.birds`` file is data, not something to unzip, even though it is
    a zip inside -- and ``CFBundleDocumentTypes`` says this app opens
    it and that it is drawn with the document icon.
    """
    return {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": DISPLAY_NAME,
        "CFBundleIdentifier": BUNDLE_ID,
        "CFBundleShortVersionString": bundle_version(),
        "CFBundleVersion": bundle_version(),
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "MIT License",
        "LSMinimumSystemVersion": MINIMUM_MACOS,
        "CFBundleDocumentTypes": [{
            "CFBundleTypeName": SESSION_DESCRIPTION,
            "CFBundleTypeRole": "Editor",
            "LSHandlerRank": "Owner",
            "LSItemContentTypes": [SESSION_UTI],
            "CFBundleTypeIconFile": f"{DOCUMENT_ICON}.icns",
        }],
        "UTExportedTypeDeclarations": [{
            "UTTypeIdentifier": SESSION_UTI,
            "UTTypeDescription": SESSION_DESCRIPTION,
            "UTTypeConformsTo": ["public.data"],
            "UTTypeIconFile": f"{DOCUMENT_ICON}.icns",
            "UTTypeTagSpecification": {
                "public.filename-extension": [SESSION_EXTENSION],
                "public.mime-type": [SESSION_MIME],
            },
        }],
    }
