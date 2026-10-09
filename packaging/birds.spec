# PyInstaller recipe for B.I.R.D.S.
#
#   macOS:    pyinstaller packaging/birds.spec   ->  dist/BIRDS.app
#   Windows:  pyinstaller packaging\birds.spec   ->  dist\BIRDS\BIRDS.exe
#             (then the installer: packaging/windows/birds.iss)
#
# Run from the repository root.  See packaging/README.md.
# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

SPEC_DIR = Path(SPECPATH)                      # noqa: F821 (PyInstaller)
ROOT = SPEC_DIR.parent
sys.path.insert(0, str(SPEC_DIR))

import app_info  # noqa: E402

ICONS = app_info.ICONS
MAC = sys.platform == "darwin"
WINDOWS = sys.platform.startswith("win")

datas = [
    # The logo the main window and the welcome screen show.
    (str(ROOT / "birds" / "resources"), "birds/resources"),
    # The session document icon, next to the bundle's own resources:
    # Info.plist names it, and Windows' file association points at it.
    (str(ICONS / f"{app_info.DOCUMENT_ICON}.icns"), "."),
    (str(ICONS / f"{app_info.DOCUMENT_ICON}.ico"), "."),
]

# mgrs loads its compiled library with ctypes from the folder above its
# package, where PyInstaller does not look; put it where mgrs will.
binaries = []
try:
    import mgrs
    site = Path(mgrs.__file__).resolve().parent.parent
    binaries += [(str(lib), ".") for lib in site.glob("libmgrs*")
                 if lib.is_file()]
except ImportError:
    pass

a = Analysis(                                   # noqa: F821
    [str(ROOT / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=["matplotlib.backends.backend_qtagg"],
    # Used only to build the manual, never by the application.
    excludes=["docx", "reportlab", "pytest", "tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)                               # noqa: F821

icon = str(ICONS / (f"{app_info.APP_ICON}.icns" if MAC
                    else f"{app_info.APP_ICON}.ico"))

exe = EXE(                                      # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_info.APP_NAME,
    console=False,
    icon=icon,
    argv_emulation=False,
)

coll = COLLECT(                                 # noqa: F821
    exe,
    a.binaries,
    a.datas,
    name=app_info.APP_NAME,
)

if MAC:
    app = BUNDLE(                               # noqa: F821
        coll,
        name=f"{app_info.APP_NAME}.app",
        icon=icon,
        bundle_identifier=app_info.BUNDLE_ID,
        version=app_info.version(),
        info_plist=app_info.info_plist(),
    )
