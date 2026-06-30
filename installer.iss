; Inno Setup script for Spotify Downloader (PySide6 version)
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isdl.php
;
; MyAppVersion is generated from src/__version__ by
; scripts/write_version_include.py into installer/_version.iss.
; Run `python -m scripts.write_version_include` (or use build.ps1 / build.bat)
; before invoking ISCC.

#define MyAppName "Spotify Playlist Downloader"
#include "installer\_version.iss"
#define MyAppPublisher "Your Name"
#define MyAppURL "https://github.com/avcode-exe/spotify-downloader"
#define MyAppExeName "SpotifyDownloader.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".spotifydownloader"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt
; AppId must be a stable GUID so Windows can detect/upgrade existing installs.
#define MyAppId "{{9D76874D-FCC0-5857-A213-4AB2B409356D}}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer
OutputBaseFilename=SpotifyDownloader_Setup
Compression=lzma2/ultra64
LZMAUseSeparateProcess=yes
SolidCompression=yes
WizardStyle=modern
SetupIconFile=assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\SpotifyDownloader\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
