; Inno Setup script for the B.I.R.D.S Windows installer.
;
; Build the app first, on Windows, from the repository root:
;     pyinstaller packaging\birds.spec
; then compile this script (Inno Setup 6):
;     iscc packaging\windows\birds.iss
; The installer lands in dist\installer\.
;
; Besides installing the app it registers .birds sessions: they open
; in B.I.R.D.S on a double-click and are drawn with the session icon.
; Uninstalling removes the association again.

#define AppName "B.I.R.D.S"
#define AppExe "BIRDS.exe"
#define AppVersion "0.1.0b2"
#define ProgId "BIRDS.Session"

[Setup]
AppId={{6C1B7D2E-3F4A-4B8C-9D0E-B1A2C3D4E5F6}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=Darío Torres Sánchez
DefaultDirName={autopf}\BIRDS
DefaultGroupName={#AppName}
OutputDir=..\..\dist\installer
OutputBaseFilename=BIRDS-{#AppVersion}-setup
SetupIconFile=..\icons\birds_app.ico
UninstallDisplayIcon={app}\{#AppExe}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
; Tell Explorer to redraw the .birds icons after installing.
ChangesAssociations=yes
PrivilegesRequiredOverridesAllowed=dialog

[Files]
Source: "..\..\dist\BIRDS\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Registry]
; .birds -> BIRDS.Session, drawn with the session icon, opened by BIRDS.exe
Root: HKA; Subkey: "Software\Classes\.birds"; ValueType: string; ValueName: ""; ValueData: "{#ProgId}"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\{#ProgId}"; ValueType: string; ValueName: ""; ValueData: "B.I.R.D.S session"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\{#ProgId}\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\_internal\birds_document.ico"
Root: HKA; Subkey: "Software\Classes\{#ProgId}\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExe}"" ""%1"""

[Run]
Filename: "{app}\{#AppExe}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent
