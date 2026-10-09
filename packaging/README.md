# Packaging B.I.R.D.S as an application

Run from source, B.I.R.D.S is a Python script, and the operating system
knows nothing about `.birds` files: they get the generic document icon
and a double-click does not open them. Packaged as an application, it
registers the session type, so every `.birds` file is drawn with the
session icon and opens in B.I.R.D.S — and colleagues can install it
without Python.

| File | What it is |
|---|---|
| `make_icons.py` | Draws both icons from `birds/resources/LOGO-BIRDS.png` into `icons/`. Run again after changing the logo. |
| `icons/birds_app.*` | The application icon (`.icns` macOS, `.ico` Windows, `.png`). |
| `icons/birds_document.*` | The session-file icon: a page with the emblem small on it. |
| `app_info.py` | Name, bundle identifier, version, and the session type the app declares. Read by the spec and by `tests/test_packaging.py`. |
| `birds.spec` | The PyInstaller recipe, for macOS and Windows. |
| `windows/birds.iss` | Inno Setup script: the Windows installer, with the `.birds` association. |
| `linux/` | Desktop entry and MIME type for Linux. |

PyInstaller packages for the platform it runs on: build the macOS app on
a Mac and the Windows installer on Windows.

**After every build, run the self-test** of the built program. It puts a
diagram, the kriging, a UTM and an MGRS conversion, the CIPW norm, a
session and an Excel file through the packaged code, and exits with 0
when all seven pass. PyInstaller can leave out a library a package
loads in an unusual way — the first build left out `mgrs`'s, and the app
would not start — and this finds it before anyone else does.

```bash
dist/BIRDS.app/Contents/MacOS/BIRDS --self-test      # macOS
dist\BIRDS\BIRDS.exe --self-test                     # Windows
```

## macOS

```bash
python3 -m pip install pyinstaller
pyinstaller packaging/birds.spec --noconfirm
```

The app is `dist/BIRDS.app`, about 370 MB — Qt, matplotlib and SciPy
travel inside it. Copy it to `/Applications` and open it once; from then
on `.birds` files carry the session icon and open on a double-click. Its
`Info.plist` declares the session type (`UTExportedTypeDeclarations`)
and that B.I.R.D.S owns it (`CFBundleDocumentTypes`).

The app is not signed. A copy built on the Mac it runs on opens normally;
a copy received from someone else — downloaded, mailed, on a USB stick —
is refused the first time as coming from an unidentified developer:
right-click it, choose **Open**, and confirm. Distributing it without
that step needs an Apple Developer ID to sign and notarise it.

## Windows

```bat
py -m pip install pyinstaller
pyinstaller packaging\birds.spec --noconfirm
iscc packaging\windows\birds.iss
```

`iscc` is the Inno Setup 6 compiler. The installer is
`dist\installer\BIRDS-<version>-setup.exe`; it installs the app, adds a
Start-menu entry and registers `.birds` sessions with their icon.
Uninstalling removes the association.

## Linux

```bash
pyinstaller packaging/birds.spec --noconfirm      # dist/BIRDS/BIRDS
xdg-mime install packaging/linux/birds-session.xml
xdg-icon-resource install --context mimetypes --size 256 \
    packaging/icons/birds_document_256.png application-x-birds-session
xdg-icon-resource install --size 256 packaging/icons/birds_app_256.png birds
desktop-file-install --dir ~/.local/share/applications packaging/linux/birds.desktop
```

with `dist/BIRDS/BIRDS` on the `PATH` as `BIRDS`.

## Before the first public release

`BUNDLE_ID` in `app_info.py` (now `io.github.dariotorres.birds`) is how
macOS remembers which app owns `.birds` files. Settle it before the
first release: after it, a different identifier is a different app for
every installed copy. The same goes for the installer's `AppId` in
`windows/birds.iss`.
