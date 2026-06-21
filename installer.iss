; Inno Setup script for Spotify Downloader
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isdl.php

#define MyAppName "Spotify Downloader"
#define MyAppVersion "1.0"
#define MyAppPublisher "Your Name"
#define MyAppURL "https://github.com/avcode-exe/spotify-downloader"
#define MyAppExeName "SpotifyDownloader.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".spotifydownloader"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Uncomment the line below to require admin rights
; PrivilegesRequired=admin
OutputDir=installer
OutputBaseFilename=SpotifyDownloader_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
; SetupIconFile requires a valid .ico file; omit until a real icon is provided
; SetupIconFile=assets\icon.ico
; Uncomment below if you have a license file
; LicenseFile=LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode
Name: "installtui"; Description: "Install TUI dependencies (textual)"; GroupDescription: "Optional components:"; Flags: unchecked

[Files]
Source: "dist\SpotifyDownloader\SpotifyDownloader.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\SpotifyDownloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "spotify_downloader.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "src\*"; DestDir: "{app}\src"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
// Optional: Install TUI dependencies if the user selected the task
function InitializeSetup(): Boolean;
begin
  Result := true;
end;

function ShouldInstallTUI(): Boolean;
begin
  Result := IsTaskSelected('installtui');
end;
