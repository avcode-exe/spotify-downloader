param(
    [switch]$SkipInstaller,
    [switch]$Clean
)

$ErrorActionPreference = 'Stop'

function Invoke-Clean {
    Write-Host ""
    Write-Host "Cleaning build artifacts..." -ForegroundColor Yellow
    $paths = @(
        "build",
        "dist",
        "SpotifyDownloader.spec",
        "SpotifyDownloader_Installer.exe",
        "installer\SpotifyDownloader_Setup.exe",
        "installer\SpotifyDownloader_Setup_files"
    )
    foreach ($p in $paths) {
        if (Test-Path $p) {
            Remove-Item $p -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  Removed: $p" -ForegroundColor Gray
        }
    }
    Write-Host "Clean complete." -ForegroundColor Green
}

if ($Clean) {
    Write-Host "================================____________" -ForegroundColor Cyan
    Write-Host "Spotify Downloader - Clean" -ForegroundColor Cyan
    Write-Host "================================____________" -ForegroundColor Cyan
    Invoke-Clean
    exit 0
}

Write-Host "================================____________" -ForegroundColor Cyan
Write-Host "Spotify Downloader - Build Script" -ForegroundColor Cyan
Write-Host "================================____________" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Checking Python..." -ForegroundColor Yellow
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "ERROR: Python is not installed or not in PATH." -ForegroundColor Red
    exit 1
}
python --version

Write-Host ""
Write-Host "[2/4] Installing build dependencies..." -ForegroundColor Yellow
pip install -q pyinstaller

Write-Host ""
Write-Host "[3/4] Cleaning previous build..." -ForegroundColor Yellow
Invoke-Clean

Write-Host ""
Write-Host "[4/5] Building executable..." -ForegroundColor Yellow
$iconPath = "assets\icon.ico"
if (Test-Path $iconPath) {
    Write-Host "  Note: icon file exists but PyInstaller icon embedding can be brittle; building without --icon for reliability." -ForegroundColor Yellow
}

$pyinstallerArgs = @(
    "--noconfirm"
    "--clean"
    "--name", "SpotifyDownloader"
    "--add-data", "src;src"
    "gui_app.py"
)

pyinstaller @pyinstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build complete!" -ForegroundColor Green
Write-Host "Output: dist\SpotifyDownloader\" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

if (-not $SkipInstaller) {
    Write-Host ""
    Write-Host "[5/5] Building installer with Inno Setup..." -ForegroundColor Yellow
    $iscc = $null
    $candidates = @(
        "C:\Program\ISCC.exe",
        "C:\Program Files\Inno Setup 6\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        "C:\Program Files\Inno Setup 5\ISCC.exe",
        "C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) {
            $iscc = $c
            break
        }
    }
    if (-not $iscc) {
        $cmd = Get-Command ISCC.exe -ErrorAction SilentlyContinue
        if ($cmd) { $iscc = $cmd.Source }
    }
    if (-not $iscc) {
        Write-Host "ERROR: Inno Setup compiler (ISCC.exe) not found." -ForegroundColor Red
        Write-Host "  Searched common locations:" -ForegroundColor Gray
        $candidates | ForEach-Object { Write-Host "    $_" -ForegroundColor Gray }
        exit 1
    }
    Write-Host "  Using: $iscc" -ForegroundColor Gray
    & $iscc "installer.iss"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Inno Setup compilation failed." -ForegroundColor Red
        exit 1
    }
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Installer complete!" -ForegroundColor Green
    Write-Host "Output: installer\SpotifyDownloader_Setup.exe" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
}
