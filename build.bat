@echo off
setlocal

set CLEAN_ONLY=0
if /I "%~1"=="clean" set CLEAN_ONLY=1

echo ============================================
if %CLEAN_ONLY%==1 (
    echo Spotify Downloader - Clean
) else (
    echo Spotify Downloader - Build Script
)
echo ============================================
echo.

if %CLEAN_ONLY%==1 goto :clean

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    pause
    exit /b 1
)
python --version

echo.
echo [2/5] Installing build dependencies...
pip install -q -r requirements.txt pyinstaller

echo.
echo [3/5] Cleaning previous build...
goto :clean

:build
echo.
echo [4/5] Building executable...
set PYTHONOPTIMIZE=2
pyinstaller --noconfirm --clean ^
    --name "SpotifyDownloader" ^
    --add-data "src;src" ^
    --exclude-module numpy ^
    --exclude-module scipy ^
    --exclude-module sklearn ^
    --exclude-module pandas ^
    --exclude-module matplotlib ^
    --exclude-module IPython ^
    --exclude-module jupyter ^
    --exclude-module pytest ^
    --exclude-module mypy ^
    --exclude-module ruff ^
    -s -w ^
    gui_app.py

echo.
echo ============================================
echo Build complete!
echo Output: dist\SpotifyDownloader\
echo ============================================

echo.
echo [5/5] Building installer with Inno Setup...
set "ISCC="
if exist "C:\Program\ISCC.exe" set "ISCC=C:\Program\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not defined ISCC if exist "C:\Program Files\Inno Setup 5\ISCC.exe" set "ISCC=C:\Program Files\Inno Setup 5\ISCC.exe"
if not defined ISCC if exist "C:\Program Files (x86)\Inno Setup 5\ISCC.exe" set "ISCC=C:\Program Files (x86)\Inno Setup 5\ISCC.exe"
if not defined ISCC for /f "delims=" %%i in ('where ISCC.exe 2^>nul') do set "ISCC=%%i"
if not defined ISCC (
    echo ERROR: Inno Setup compiler (ISCC.exe) not found.
    echo   Searched common locations:
    echo     C:\Program\ISCC.exe
    echo     C:\Program Files\Inno Setup 6\ISCC.exe
    echo     C:\Program Files (x86)\Inno Setup 6\ISCC.exe
    echo     C:\Program Files\Inno Setup 5\ISCC.exe
    echo     C:\Program Files (x86)\Inno Setup 5\ISCC.exe
    echo   Also searched system PATH.
    pause
    exit /b 1
)
echo   Using: %ISCC%
"%ISCC%" installer.iss
if errorlevel 1 (
    echo ERROR: Inno Setup compilation failed.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Installer complete!
echo Output: installer\SpotifyDownloader_Setup.exe
echo ============================================

pause
goto :eof

:clean
echo Cleaning build artifacts...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist SpotifyDownloader.spec del /q SpotifyDownloader.spec
if exist SpotifyDownloader_Installer.exe del /q SpotifyDownloader_Installer.exe
if exist installer\SpotifyDownloader_Setup.exe del /q installer\SpotifyDownloader_Setup.exe
if exist installer\SpotifyDownloader_Setup_files rmdir /s /q installer\SpotifyDownloader_Setup_files
echo Clean complete.
echo.

if %CLEAN_ONLY%==1 (
    pause
    exit /b 0
) else (
    goto :build
)
