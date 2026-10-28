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
| `update_mac_app.py` | Rebuilds the Mac app and replaces the installed copy. |
| `windows/birds.iss` | Inno Setup script: the Windows installer, with the `.birds` association. |
| `linux/` | Desktop entry, MIME type and `install.sh` for Linux. |

PyInstaller packages for the platform it runs on: build the macOS app on
a Mac and the Windows installer on Windows. GitHub Actions builds the
Windows installer and the Linux bundle (`.github/workflows/build.yml`);
see [Releasing](#releasing).

**After every build, run the self-test** of the built program. It puts a
diagram, its export to every format Export plot offers, the kriging, a
UTM and an MGRS conversion, the CIPW norm, a session and an Excel file
through the packaged code, and exits with 0 when all eight pass.
PyInstaller can leave out a library a package loads in an unusual way —
the first build left out `mgrs`'s, and the app would not start; the
first betas left out matplotlib's PDF, SVG and EPS writers, which it
imports only on saving (`EXPORT_BACKENDS` in `app_info.py`) — and this
finds it before anyone else does.

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

It needs macOS 13 or later, as the Qt inside it does
(`MINIMUM_MACOS` in `app_info.py`), and runs on the processor it was
built on — Apple silicon, from this project's Mac.

The app is not signed. A copy built on the Mac it runs on opens normally;
a copy received from someone else — downloaded, mailed, on a USB stick —
is refused the first time: macOS could not verify it. Click **Done**,
then **Open Anyway** under *System Settings → Privacy & Security*.
Distributing it without that step needs an Apple Developer ID to sign
and notarise it.

The Finder may keep drawing `.birds` files with the generic page for a
while after the first install: macOS renders a new document icon in the
background and shows the plain page meanwhile. Relaunching the Finder
(⌥-right-click its Dock icon → Relaunch) picks the new one up.

### Updating the installed app

Changes are made to the source, never to `BIRDS.app`: the app is a
snapshot of the source when it was built, and stays as it is until it is
rebuilt. During development run `python3 main.py`; when the installed
copy should catch up, run

```bash
python3 packaging/update_mac_app.py
```

It builds, runs the self-test on the new build, and only if that passes
replaces `/Applications/BIRDS.app` — and only if what is there is
B.I.R.D.S. The new copy is swapped in by renaming, so a failure part-way
leaves a working app. It stops if B.I.R.D.S is open. `--tests` runs the
test suite first; `--build-only` stops after the self-test; `--dest`
installs somewhere other than `/Applications`. PyInstaller's output goes
to `build/update_mac_app.log`. The identifier does not change between
builds, so the `.birds` association and icon carry over.

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
```

The bundle the build workflow packs, `BIRDS-<version>-linux-x86_64.tar.gz`,
holds `dist/BIRDS`, the contents of `linux/` and the two 256 px icons.
Unpacked, `BIRDS-linux/install.sh` installs it for the user who runs it,
with no administrator password: the program in `~/.local/share/BIRDS`, a
`BIRDS` command in `~/.local/bin`, the menu entry (pointing at the
program by its full path, so it works whatever the `PATH`), the `.birds`
MIME type and both icons. `install.sh --uninstall` removes all of it.

A bundle runs only where the C library is at least as new as the one it
was built against, so the workflow builds on Ubuntu 24.04 (glibc 2.39)
rather than on `ubuntu-latest`.

## Releasing

1. Set the version — `0.1.0`, or `0.1.0b1` for a beta — in
   `birds/__init__.py`, `pyproject.toml`, `windows/birds.iss`,
   `CITATION.cff` and the README; `tests/test_packaging.py` fails while
   they disagree. Give it its own heading in `CHANGELOG.md`.
2. Push, and wait for the tests to pass.
3. Tag the commit `v` + the version and push the tag:
   `git tag v0.1.0b1 && git push origin v0.1.0b1`. The build workflow
   builds Windows and Linux, refuses a tag that is not the version, and
   files both as a **draft** release — a beta as a pre-release.
4. Build the Mac app (`python3 packaging/update_mac_app.py`) and zip it,
   keeping its links and attributes:
   `ditto -c -k --sequesterRsrc --keepParent /Applications/BIRDS.app dist/BIRDS-0.1.0b1-macOS-arm64.zip`.
5. On GitHub, *Releases* → the draft → *Edit*: drop the zip under
   *Attach binaries*, check the notes, and *Publish release*. Nothing is
   public before this.

## Before the first public release

`BUNDLE_ID` in `app_info.py` is `io.github.dariotorressanchez.birds`,
after the project's GitHub account, settled on 2026-10-26 before the
first release. It is how macOS remembers which app owns `.birds`
files: after a release, a different identifier is a different app for
every installed copy. `PREVIOUS_BUNDLE_IDS` lists the one used before,
so `update_mac_app.py` still recognises an older install as B.I.R.D.S. The same goes for the installer's `AppId` in
`windows/birds.iss`.
