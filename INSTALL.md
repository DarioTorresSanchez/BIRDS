# Installing B.I.R.D.S

Step-by-step instructions for **macOS**, **Windows** and **Linux**.

No programming experience is needed. You will type a handful of commands into
a terminal; each one is shown on its own line so it can be copied directly.

---

## Contents

- [System requirements](#system-requirements)
- [Before you start: what a virtual environment is](#before-you-start-what-a-virtual-environment-is)
- [macOS](#macos)
- [Windows](#windows)
- [Linux](#linux)
- [Running B.I.R.D.S after installation](#running-birds-after-installation)
- [Optional dependencies](#optional-dependencies)
- [Updating](#updating)
- [Uninstalling](#uninstalling)
- [Troubleshooting](#troubleshooting)

---

## System requirements

| | |
|---|---|
| **Operating system** | macOS 11 (Big Sur) or later · Windows 10 or later · any modern Linux distribution |
| **Python** | 3.9 or later (3.11 recommended) |
| **Memory** | 4 GB RAM minimum, 8 GB recommended for large datasets |
| **Disk space** | ~500 MB including Python and the scientific libraries |
| **Internet** | Needed only for installation, and for the Map view's basemap tiles |

---

## Before you start: what a virtual environment is

A *virtual environment* is a private folder holding the exact library versions
B.I.R.D.S needs, isolated from the rest of your system. It means installing
B.I.R.D.S can never break another Python program, and removing it is as simple
as deleting a folder.

Every instruction below creates one called `.venv` inside the project folder.
You activate it before running the application; your terminal prompt then
shows `(.venv)` at the start of the line.

---

## macOS

### 1. Open the Terminal

Press `Cmd + Space`, type `Terminal`, press `Enter`.

### 2. Check whether you already have Python 3

```bash
python3 --version
```

If it prints `Python 3.9.x` or higher, skip to step 4. If it says
*command not found* or shows an older version, continue.

### 3. Install Python 3

**Option A — official installer (simplest).** Download the macOS installer
from [python.org/downloads](https://www.python.org/downloads/), open the
`.pkg` file and follow the prompts. Then close and reopen the Terminal.

**Option B — Homebrew.** If you already use [Homebrew](https://brew.sh):

```bash
brew install python@3.11
```

### 4. Download B.I.R.D.S

If you have `git`:

```bash
git clone https://github.com/<your-username>/BIRDS.git
```

Otherwise download the ZIP from the repository page (green **Code** button →
**Download ZIP**), then double-click it to unpack.

### 5. Enter the project folder

```bash
cd BIRDS
```

> **Tip:** instead of typing the path, type `cd ` (with a space) and then drag
> the folder from Finder onto the Terminal window.

### 6. Create and activate the virtual environment

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

Your prompt should now begin with `(.venv)`.

### 7. Install the libraries

```bash
python3 -m pip install --upgrade pip
```

```bash
python3 -m pip install -r requirements.txt
```

This downloads roughly 400 MB and takes a few minutes on a normal connection.

### 8. Launch

```bash
python3 main.py
```

The B.I.R.D.S window should open.

> **If macOS blocks the app:** the first launch may show a security prompt
> because the libraries are unsigned. Go to **System Settings → Privacy &
> Security**, scroll to the bottom and click **Allow Anyway**, then run the
> command again.

> **Apple Silicon (M1/M2/M3/M4):** everything above works natively. Make sure
> you installed the **arm64** build of Python — the python.org installer picks
> it automatically on Apple Silicon Macs.

---

## Windows

### 1. Install Python 3

Download the Windows installer from
[python.org/downloads](https://www.python.org/downloads/) and run it.

> **Critical:** on the first screen of the installer, tick
> **“Add python.exe to PATH”** *before* clicking *Install Now*. Almost every
> installation problem on Windows traces back to this box being left unticked.

### 2. Open a terminal

Press `Win + R`, type `powershell`, press `Enter`.

### 3. Verify Python

```powershell
python --version
```

If it prints `Python 3.9.x` or higher you are set. If Windows opens the
Microsoft Store instead, Python was not added to PATH — reinstall it with the
box ticked, or use `py --version` instead of `python --version` throughout.

### 4. Download B.I.R.D.S

If you have [Git for Windows](https://git-scm.com/download/win):

```powershell
git clone https://github.com/<your-username>/BIRDS.git
```

Otherwise download the ZIP from the repository page (green **Code** button →
**Download ZIP**), right-click it and choose **Extract All**.

### 5. Enter the project folder

```powershell
cd BIRDS
```

> **Tip:** open the folder in File Explorer, click the address bar, type
> `powershell` and press `Enter` — a terminal opens already in that folder.

### 6. Create and activate the virtual environment

```powershell
python -m venv .venv
```

```powershell
.venv\Scripts\Activate.ps1
```

> **If PowerShell refuses with “running scripts is disabled”**, run this once
> and then repeat the activation command:
>
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> ```
>
> Alternatively, use the Command Prompt (`cmd`) instead of PowerShell, where
> the activation command is `.venv\Scripts\activate.bat`.

### 7. Install the libraries

```powershell
python -m pip install --upgrade pip
```

```powershell
python -m pip install -r requirements.txt
```

### 8. Launch

```powershell
python main.py
```

---

## Linux

Instructions cover the two largest families. Adapt the package manager
command to your distribution if it is neither.

### 1. Install Python and the Qt system libraries

Qt needs a few shared libraries that are not always present on a minimal
desktop install — installing them up front avoids the most common
`libGL.so.1` / `xcb plugin` errors.

**Debian, Ubuntu, Linux Mint, Pop!\_OS:**

```bash
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git libgl1 libegl1 libxkbcommon-x11-0 libdbus-1-3 libxcb-cursor0
```

**Fedora, RHEL, Rocky, AlmaLinux:**

```bash
sudo dnf install -y python3 python3-pip git mesa-libGL libxkbcommon-x11 dbus-libs xcb-util-cursor
```

**Arch, Manjaro:**

```bash
sudo pacman -S --needed python python-pip git libglvnd libxkbcommon-x11 dbus xcb-util-cursor
```

### 2. Verify Python

```bash
python3 --version
```

Python 3.9 or later is required.

### 3. Download B.I.R.D.S

```bash
git clone https://github.com/<your-username>/BIRDS.git
```

### 4. Enter the project folder

```bash
cd BIRDS
```

### 5. Create and activate the virtual environment

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

### 6. Install the libraries

```bash
python3 -m pip install --upgrade pip
```

```bash
python3 -m pip install -r requirements.txt
```

### 7. Launch

```bash
python3 main.py
```

> **Wayland:** if the window fails to appear or renders oddly, force the X11
> backend:
>
> ```bash
> QT_QPA_PLATFORM=xcb python3 main.py
> ```

---

## Running B.I.R.D.S after installation

Every time you want to use the application, open a terminal, go to the
project folder, activate the environment and launch it.

**macOS / Linux:**

```bash
cd path/to/BIRDS && source .venv/bin/activate && python3 main.py
```

**Windows (PowerShell):**

```powershell
cd path\to\BIRDS ; .venv\Scripts\Activate.ps1 ; python main.py
```

### Making a one-click launcher

**macOS / Linux.** Create a file called `birds.sh` next to `main.py`:

```bash
printf '#!/bin/bash\ncd "$(dirname "$0")"\nsource .venv/bin/activate\npython3 main.py\n' > birds.sh && chmod +x birds.sh
```

Double-click `birds.sh` (on macOS you may need to right-click → Open the first
time), or run `./birds.sh`.

**Windows.** Create a file called `birds.bat` next to `main.py` containing:

```bat
@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python main.py
```

Double-click `birds.bat` to launch. Right-click it → **Send to → Desktop
(create shortcut)** for a desktop icon.

---

## Optional dependencies

Everything in `requirements.txt` installs by default. Three entries matter
only for specific features, and the application degrades gracefully without
them:

| Package | Needed for | Without it |
|---|---|---|
| `contextily` | Basemap tiles in the Map view | The Map view cannot draw a background map |
| `pyproj` | UTM coordinate conversion | Falls back to a Snyder series expansion (~1 m accuracy) |
| `mgrs` | MGRS coordinate input | The MGRS option is disabled |

If any of them fails to build on your system, remove that line from
`requirements.txt` and reinstall — the rest of the application is unaffected.

---

## Updating

With the environment activated, inside the project folder:

```bash
git pull
```

```bash
python3 -m pip install -r requirements.txt --upgrade
```

Your sessions (`.birds`), style presets (`.birdstyle`) and settings live
outside the project folder, so updating never touches your work.

---

## Uninstalling

B.I.R.D.S installs nothing system-wide. To remove it completely:

1. Delete the project folder.
2. Delete the settings and crash-log folder:
   - **macOS / Linux:** `~/.birds/`
   - **Windows:** `C:\Users\<you>\.birds\`
3. If you installed Python only for this, uninstall it the usual way for your
   operating system.

---

## Troubleshooting

### The window opens and closes immediately

B.I.R.D.S writes every uncaught error to a rolling log. Open it:

**macOS / Linux:**

```bash
cat ~/.birds/crash.log
```

**Windows:**

```powershell
type $env:USERPROFILE\.birds\crash.log
```

The last entry names the failure. Include it in any bug report.

### `ModuleNotFoundError: No module named 'PySide6'`

The virtual environment is not active, or the libraries were installed into a
different Python. Re-activate it and reinstall:

```bash
source .venv/bin/activate && python3 -m pip install -r requirements.txt
```

On Windows the activation command is `.venv\Scripts\Activate.ps1`.

### `qt.qpa.plugin: Could not load the Qt platform plugin "xcb"` (Linux)

The Qt system libraries from [step 1](#linux) are missing. Install them, then:

```bash
QT_QPA_PLATFORM=xcb python3 main.py
```

### `ImportError: libGL.so.1: cannot open shared object file` (Linux)

```bash
sudo apt install -y libgl1        # Debian/Ubuntu
```

```bash
sudo dnf install -y mesa-libGL    # Fedora/RHEL
```

### `pip` is not recognised (Windows)

Use the launcher form instead:

```powershell
py -m pip install -r requirements.txt
```

### The installation fails while building a package

Upgrade the build tooling first, then retry:

```bash
python3 -m pip install --upgrade pip setuptools wheel
```

If a single optional package is the culprit — usually `contextily`, `pyproj`
or `mgrs` — remove its line from `requirements.txt` and reinstall. See
[Optional dependencies](#optional-dependencies).

### Fonts look wrong or matplotlib warns about a missing family

Harmless. Qt falls back to a system font. To silence it, install a common
font set — on Debian/Ubuntu:

```bash
sudo apt install -y fonts-dejavu
```

### Still stuck

Open an issue on the repository with:

- your operating system and version,
- the output of `python3 --version`,
- the last 20 lines of `~/.birds/crash.log`,
- the exact command you ran and the full error message.
