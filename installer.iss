; Inno Setup script for Spotify Downloader
; Requires Inno Setup 6.0 or later: https://jrsoftware.org/isdl.php
;
; MyAppVersion is generated from src/__version__ by
; scripts/write_version_include.py into installer/_version.iss.
; Run `python -m scripts.write_version_include` (or use build.ps1 / build.bat)
; before invoking ISCC.

#define MyAppName "Spotify Downloader"
#include "installer\_version.iss"
#define MyAppPublisher "Your Name"
#define MyAppURL "https://github.com/avcode-exe/spotify-downloader"
#define MyAppExeName "SpotifyDownloader.exe"
#define MyAppAssocName MyAppName + " File"
#define MyAppAssocExt ".spotifydownloader"
#define MyAppAssocKey StringChange(MyAppAssocName, " ", "") + MyAppAssocExt
; AppId must be a stable GUID so Windows can detect/upgrade existing installs.
; Generated once via uuid.uuid5(NAMESPACE_DNS, 'SpotifyDownloader-1.0.0').
; Inline `{{...}}` escapes the literal braces so the parser doesn't treat the
; value as a constant reference.
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
; Uncomment the line below to require admin rights
; PrivilegesRequired=admin
OutputDir=installer
OutputBaseFilename=SpotifyDownloader_Setup
Compression=lzma2/ultra64
LZMAUseSeparateProcess=yes
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
Name: "tui"; Description: "Install command-line TUI (Terminal UI) launcher and add spotify-downloader-tui to PATH"; GroupDescription: "Additional components"; Flags: unchecked

[Files]
Source: "dist\SpotifyDownloader\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "installer\spotify-downloader-tui.bat"; DestDir: "{app}"; Flags: ignoreversion; Tasks: tui

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autoprograms}\{#MyAppName} TUI"; Filename: "{app}\spotify-downloader-tui.bat"; Tasks: tui
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[Code]
procedure AddAppToPath();
var
  ResultCode: Integer;
  PsFile: string;
  PsCmd: string;
  AppPath: string;
begin
  AppPath := ExpandConstant('{app}');
  PsFile := ExpandConstant('{tmp}\add_to_path.ps1');
  PsCmd := Format('$escaped = [WildcardPattern]::Escape("%s")' + #13#10 +
    '$p = [Environment]::GetEnvironmentVariable("Path", "User")' + #13#10 +
    'if ($p -notlike "*$escaped*") {' + #13#10 +
    '  $newPath = $p + ";%s"' + #13#10 +
    '  if ($newPath.Length -lt 2048) {' + #13#10 +
    '    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")' + #13#10 +
    '  } else { Write-Host "PATH too long, skipping addition." }' + #13#10 +
    '}', [AppPath, AppPath]);
  SaveStringToFile(PsFile, PsCmd, False);
  Exec('powershell.exe', '-NoProfile -ExecutionPolicy Bypass -File "' + PsFile + '"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    if WizardIsTaskSelected('tui') then
    begin
      AddAppToPath();
    end;
  end;
end;
