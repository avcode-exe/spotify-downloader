# Spotify Playlist Downloader v0.1.1 🎵

A terminal/GUI app that downloads Spotify playlists and individual tracks by matching to
YouTube Music (via [spotDL](https://github.com/spotDL/spotify-downloader)).

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/) [![spotDL](https://img.shields.io/badge/spotDL-4.5+-green)](https://github.com/spotDL/spotify-downloader)

## Features

- **Terminal UI** — Rich, interactive interface built with [Textual](https://textual.textualize.io/)
- **Modern GUI (optional)** — Desktop app built with [PySide6](https://pyside.org/) (Qt 6) featuring sidebar navigation, QSS dark theme, guided onboarding tour, and table/tree views — Windows/macOS/Linux
- **Playlist & Track Downloads** — Paste any public Spotify playlist or individual track URL
- **Fresh Download Mode** — Overwrite existing files for a clean re-download
- **Retry Failed** — Automatically retry tracks that failed to download (now tracks all failed tracks, not just playlist tracks)
- **Download History** — View your past download sessions with status and timestamps
- **Progress Tracking** — Real-time progress bar, tracks/min rate, and ETA
- **Duplicate Detection** — Skipped (already-downloaded) tracks count toward progress for consistency
- **Settings Panel** — Configure format, bitrate, proxy, and cookie file without leaving the app
- **Auto-Extract Cookies** — One-click cookie extraction with smart multi-browser fallback (tries Firefox first on Windows to avoid locked databases)
- **Cookie File Warnings** — Detects missing/expired cookies and YouTube rate-limiting, with actionable guidance
- **Rate-Limit Detection** — Warns when YouTube is blocking downloads and suggests setting a cookie file
- **Cancellation** — Cancel any in-progress download at any time (now kills the entire spotDL process tree)
- **Cross-Platform** — Works on Windows, macOS, and Linux
- **271 unit tests** — Full coverage of URL validation, proxy handling, state persistence, duplicate logic, and UI utilities
- **Improved error handling** — Folder creation catches `OSError` instead of just `PermissionError`
- **Safer metadata cache eviction** — Uses `pop(key, None)` to avoid race conditions during cache cleanup

## Requirements

- **Python 3.11+**
- **FFmpeg** — handles audio conversion (spotDL can auto-install it)
- **yt-dlp** — for audio sourcing and cookie extraction (installed with spotDL)
- **TUI (optional):** `textual`
- **GUI (optional):** `PySide6>=6.6.0`

---

## Installation Options

You can install and run this project in three ways:
1. **GUI app** — desktop app (recommended for Windows)
2. **TUI from source** — terminal UI from source
3. **Windows EXE** — classic installer or portable EXE

---

## Option 1: GUI App (Recommended for Windows)

### Prerequisites

- Python 3.11 or later
- FFmpeg (spotDL can auto-install it)
- PySide6 (installed via `pip install -r requirements.txt`)

### Install and run

```powershell
# 1. Install GUI dependencies
pip install -r requirements.txt

# 2. (Optional) Ensure FFmpeg is available
spotdl --download-ffmpeg

# 3. Launch the GUI
python gui_app.py
```

### GUI Features

- **Sidebar Navigation** — Left sidebar with icons for Home, Settings, History, Preview, Duplicates, and Log
- **Playlist or Track URL input** — paste any public Spotify playlist or track URL
- **Output folder picker** — choose where to save downloads with browse dialog
- **Download / Fresh / Retry Failed** — full download control
- **Preview** — table view of local audio files with metadata (title, artist, duration, bitrate, size)
- **Duplicates** — tree view of duplicate groups with expandable rows
- **Settings** — configure format, bitrate, audio source, proxy, and cookie file
- **History** — table view of past download sessions with status badges
- **Live log** — syntax-highlighted log viewer with color-coded severity levels
- **Guided tour** — multi-step walkthrough on first launch
- **Progress tracking** — real-time progress bar, tracks/min rate, and ETA

### Uninstall GUI dependencies

If you no longer need the GUI, uninstall its packages:

```powershell
pip uninstall pyside6 shiboken6
```

The TUI remains available and can be launched with `python spotify_downloader.py`.

---

## Option 2: TUI from Source

### Windows

```powershell
# 1. Install Python from https://www.python.org/downloads/
#    Make sure to check "Add Python to PATH" during installation

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Ensure FFmpeg is available
spotdl --download-ffmpeg

# 4. (Optional) Install Deno — helps with some YouTube age-restricted videos
spotdl --download-deno

# 5. Launch the TUI
python spotify_downloader.py
```

### macOS

```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install Python and FFmpeg
brew install python ffmpeg

# 3. Install Deno (optional, helps with age-restricted videos)
brew install deno

# 4. Clone or download this project
git clone https://github.com/YOUR_USERNAME/spotify_downloader.git
cd spotify_downloader

# 5. Install Python dependencies
pip install -r requirements.txt

# 6. Launch the TUI
python spotify_downloader.py
```

**macOS Notes:**
- If you get a "permission denied" error, use `pip install --user -r requirements.txt` instead
- On Apple Silicon (M1/M2/M3), ensure you're using the native Python build, not Rosetta
- FFmpeg installed via Homebrew works out of the box — no extra configuration needed
- For cookie extraction: Safari doesn't work — use Chrome, Firefox, or Edge

### Linux (Debian/Ubuntu)

```bash
# 1. Update package list and install dependencies
sudo apt update
sudo apt install python3 python3-pip ffmpeg

# 2. Install Deno (optional, helps with age-restricted videos)
curl -fsSL https://deno.land/install.sh | sh
# Add to PATH: echo 'export DENO_INSTALL="$HOME/.deno"' >> ~/.bashrc
#              echo 'export PATH="$DENO_INSTALL/bin:$PATH"' >> ~/.bashrc
#              source ~/.bashrc

# 3. Clone or download this project
git clone https://github.com/YOUR_USERNAME/spotify_downloader.git
cd spotify_downloader

# 4. Install Python dependencies (use --break-system-packages on Ubuntu 23.04+)
pip install --break-system-packages -r requirements.txt
# OR use a virtual environment (recommended):
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Launch the TUI
python3 spotify_downloader.py
```

### Linux (Fedora/RHEL)

```bash
# 1. Install dependencies
sudo dnf install python3 python3-pip ffmpeg

# 2. Install Deno (optional)
curl -fsSL https://deno.land/install.sh | sh
# Add to PATH: echo 'export DENO_INSTALL="$HOME/.deno"' >> ~/.bashrc
#              echo 'export PATH="$DENO_INSTALL/bin:$PATH"' >> ~/.bashrc
#              source ~/.bashrc

# 3. Clone or download this project
git clone https://github.com/YOUR_USERNAME/spotify_downloader.git
cd spotify_downloader

# 4. Install Python dependencies
pip install --user -r requirements.txt
# OR use a virtual environment (recommended):
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 5. Launch the TUI
python3 spotify_downloader.py
```

### Linux (Arch/Manjaro)

```bash
# 1. Install dependencies
sudo pacman -S python python-pip ffmpeg

# 2. Install Deno (optional)
curl -fsSL https://deno.land/install.sh | sh
# Add to PATH: echo 'export DENO_INSTALL="$HOME/.deno"' >> ~/.bashrc
#              echo 'export PATH="$DENO_INSTALL/bin:$PATH"' >> ~/.bashrc
#              source ~/.bashrc

# 3. Clone or download this project
git clone https://github.com/YOUR_USERNAME/spotify_downloader.git
cd spotify_downloader

# 4. Install Python dependencies
pip install --user -r requirements.txt

# 5. Launch the TUI
python spotify_downloader.py
```

---

## Option 3: Windows EXE / Installer

### Build from source

**Prerequisites:**
- Python 3.11+
- Windows OS
- Inno Setup 6+ (bundled at `C:\Program\ISCC.exe` for local builds)

**Steps:**

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Build portable EXE + official installer in one step
.\build.ps1

# Outputs:
#   dist\SpotifyDownloader\SpotifyDownloader.exe   (portable)
#   installer\SpotifyDownloader_Setup.exe          (official installer)
```

To skip the installer and only build the portable EXE:
```powershell
.\build.ps1 -SkipInstaller
```

To clean build artifacts without building:
```powershell
.\build.ps1 -Clean
```

### Inno Setup installer

`installer.iss` creates a modern `Setup.exe` with:
- Start Menu shortcut
- Optional Desktop shortcut
- Installs `gui_app.py`, `spotify_downloader.py`, `src/`, and `requirements.txt` under `%LOCALAPPDATA%\Spotify Downloader\`

---

## Usage

### TUI (Terminal UI)

1. Run `python spotify_downloader.py`
2. Paste a **public** Spotify playlist or track URL into the top field
   - Playlist: `https://open.spotify.com/playlist/<22-char-id>` (e.g. `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`)
   - Track: `https://open.spotify.com/track/<11-char-id>` (e.g. `https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT`)
   - URI format also accepted: `spotify:playlist:<22-char-id>` or `spotify:track:<11-char-id>`
3. Choose an output folder (default: `./downloads`)
4. Click **Download** (or **⟳ Fresh** to overwrite existing files)
5. Watch the progress — spotDL will fetch metadata, find matching audio on
   YouTube Music, download it, and embed ID3 tags (title, artist, cover art)

### GUI (Desktop App)

1. Run `python gui_app.py`
2. Paste a **public** Spotify playlist or track URL into the top field
   - Playlist: `https://open.spotify.com/playlist/<22-char-id>` (e.g. `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`)
   - Track: `https://open.spotify.com/track/<11-char-id>` (e.g. `https://open.spotify.com/track/4cOdK2wGLETKBW3PvgPWqT`)
   - URI format also accepted: `spotify:playlist:<22-char-id>` or `spotify:track:<11-char-id>`
3. Choose an output folder (default: `./downloads`)
4. Click **▶ Download** or **⟳ Fresh** to start
5. Use **🔎 Preview** and **📋 Duplicates** buttons to toggle panels
6. Watch the progress in the status bar and live log at the bottom

## Buttons

### TUI Buttons

| Button | Description |
|--------|-------------|
| ▶ **Download** | Download the playlist (skips already-downloaded tracks) |
| 🔄 **Retry Failed** | Re-download only the tracks that failed in the last session |
| ⟳ **Fresh** | Download everything, overwriting existing files |
| ⏹ **Cancel** | Cancel the current download (terminates the entire spotDL process tree) |
| ✕ **Quit** | Exit the application |

### GUI Buttons

| Button | Description |
|--------|-------------|
| ▶ **Download** | Download the playlist (skips already-downloaded tracks) |
| 🔄 **Retry Failed** | Re-download only the tracks that failed in the last session |
| ⟳ **Fresh** | Download everything, overwriting existing files |
| 🔎 **Preview** | Toggle the preview panel (shows local files and duplicates) |
| 📋 **Duplicates** | Toggle the duplicates panel (shows duplicate groups) |
| ⏹ **Cancel** | Cancel the current download (terminates the entire spotDL process tree) |
| ✕ **Quit** | Exit the application |

## Settings

### TUI Settings (⚙ Settings panel)

Open the **⚙ Settings** panel to configure:

| Setting | Description |
|---------|-------------|
| **Format** | Output format: MP3, M4A, FLAC, Opus, OGG, WAV |
| **Bitrate** | Audio bitrate: Auto (default), 64k–320k, or disable conversion |
| **Audio source** | Audio provider: YouTube Music (default), YouTube, SoundCloud, Bandcamp, Piped |
| **Proxy** | HTTP / HTTPS / SOCKS4 / SOCKS5 proxy URL for bypassing regional restrictions |
| **Browser** | Select a browser for cookie extraction: Auto (try all), Chrome, Firefox, Edge, Brave, Vivaldi |
| **Extract** | Click to auto-extract cookies. In Auto mode, tries each browser until one succeeds |
| **Cookie file** | Path to a `cookies.txt` file (Netscape format) for authenticated YouTube access |

All settings are saved to `~/.spotdl/settings.json` and restored on restart.

### GUI Settings

The GUI **Settings** panel provides the same options in a desktop-friendly layout:

| Setting | Description |
|---------|-------------|
| **Format** | Output format: MP3, M4A, FLAC, Opus, OGG, WAV |
| **Bitrate** | Audio bitrate: Auto, 64k–320k, or disable |
| **Audio source** | YouTube Music, YouTube, SoundCloud, Bandcamp, Piped |
| **Duplicate policy** | Skip or metadata-based duplicate handling |
| **Proxy** | HTTP / HTTPS / SOCKS4 / SOCKS5 proxy URL |
| **Browser** | Browser for cookie extraction: Auto, Chrome, Firefox, Edge, Brave, Vivaldi |
| **Cookie file** | Path to a `cookies.txt` file |

All settings are saved to `~/.spotdl/settings.json` and restored on restart.

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| **"spotDL not found"** | Run `pip install spotdl` or follow the Installation section above |
| **"FFmpeg not found"** | Run `spotdl --download-ffmpeg` (auto-installs) or install via your package manager |
| **"Permission denied" (Linux/macOS)** | Use `pip install --user -r requirements.txt` or a virtual environment |
| **Cookie extraction fails** | See "Reducing Rate Limiting" section above for browser-specific fixes |
| **"Could not copy Chrome cookie database"** | Close all Chrome/Edge windows, or switch to Firefox in Settings |
| **Downloads are slow** | YouTube may be rate-limiting you — extract cookies or use a proxy |
| **"No such file or directory" for cookies** | Check the path in Settings — use the full absolute path |

### Linux-Specific Issues

```bash
# If you get "externally-managed-environment" error (Ubuntu 23.04+):
pip install --break-system-packages -r requirements.txt
# OR use a virtual environment (recommended):
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# If yt-dlp can't find Chrome cookies:
export CHROMIUM_FLAGS="--password-store=basic"

# If you get "tkinter" errors (rare):
sudo apt install python3-tk   # Debian/Ubuntu
sudo dnf install python3-tkinter   # Fedora
```

### macOS-Specific Issues

```bash
# If you get "SSL: CERTIFICATE_VERIFY_FAILED":
/Applications/Python\ 3.x/Install\ Certificates.command

# If pip isn't found:
python3 -m pip install -r requirements.txt

# If you get "Operation not permitted" errors:
# Make sure you're running in Terminal, not a restricted environment
```

---

## Notes

- Only **public** playlists and tracks work (private playlists/tracks will fail).
- Audio quality depends on what YouTube Music offers (typically 128–256 kbps).
- Downloading copyrighted music may violate Spotify's ToS and local copyright laws in your country.
- YouTube cookies expire periodically (every few weeks) — re-extract when downloads start failing.
- The `~/.spotdl/` folder is protected with owner-only permissions (0o700 on POSIX) and state files are written atomically with `fsync` to prevent data loss on crash.

## Project Structure

```
spotify_downloader/
├── build.ps1              # PowerShell build script for Windows EXE
├── build.bat              # Batch build script for Windows EXE
├── installer.iss          # Inno Setup script for classic Setup.exe
├── generate_icon.py       # Helper script to create a default icon
├── scripts/
│   ├── __init__.py        # Build-time helper package
│   └── write_version_include.py  # Generates installer/_version.iss from src.__version__
├── assets/
│   └── icon.ico           # Default application icon
├── gui_app.py             # Modern GUI entry point (PySide6/Qt 6)
├── spotify_downloader.py  # TUI entry point (Textual) + download logic
├── src/
│   ├── gui_qt/            # Active PySide6 GUI package
│   │   ├── __init__.py
│   │   ├── main_window.py # QMainWindow with sidebar + stacked widget
│   │   ├── home_panel.py  # URL input, output folder, action buttons
│   │   ├── settings_panel.py
│   │   ├── history_panel.py
│   │   ├── preview_panel.py
│   │   ├── duplicates_panel.py
│   │   ├── log_panel.py
│   │   ├── workers.py     # QThread-based spotDL worker
│   │   ├── tour.py        # Guided onboarding tour
│   │   ├── theme.py       # Color/font constants
│   │   ├── icons.py       # Icon helpers (SVG → QPixmap)
│   │   └── utils.py       # Shared helpers
│   ├── gui/               # Legacy CustomTkinter GUI (kept for reference)
│   │   ├── app.py
│   │   ├── home_frame.py
│   │   ├── settings_frame.py
│   │   ├── preview_frame.py
│   │   ├── duplicates_frame.py
│   │   ├── history_frame.py
│   │   ├── log_frame.py
│   │   ├── workers.py
│   │   ├── utils.py
│   │   └── theme.py
│   ├── models.py          # Shared dataclasses and constants
│   ├── manifest.py        # Local scan and duplicate grouping
│   ├── duplicates.py      # Duplicate move/quarantine logic
│   ├── state.py           # Per-track state persistence
│   └── spotdl_tools.py    # spotDL command and dependency helpers
├── requirements.txt       # Python dependencies
├── README.md              # This file
└── downloads/             # Default output directory
```

## Data Files

The app stores data in `~/.spotdl/`:

| File | Description |
|------|-------------|
| `settings.json` | Persisted settings (format, bitrate, audio provider, proxy, cookies, browser) |
| `download_history.json` | Download session history (up to 100 entries) |
| `track_state.json` | Per-track state for retry and duplicate handling |
| `cookies.txt` | Auto-extracted browser cookies for YouTube authentication |
| `app.log` | Application log file (rotated, 5MB max) |

## Version Management

The application version is defined in a single place: `src/__version__`. The build process (`build.ps1` / `build.bat`) automatically generates `installer/_version.iss` from this value before compiling the Inno Setup installer. The generated file is excluded from version control (`.gitignore`).

To change the version, edit only `src/__init__.py` and run the build script — the installer will pick up the new version automatically.

## Continuous Integration

The project includes a CI workflow (`.github/workflows/ci.yml`) that runs on every push and pull request across **Ubuntu**, **macOS**, and **Windows** with **Python 3.11**, **3.12**, and **3.13**. The pipeline executes:

| Job | What it does |
|-----|-------------|
| `lint` | Ruff check + format check on all Python files |
| `test` | Full pytest suite (271 tests) |
| `typecheck` | mypy static type checking |
| `compile` | `compileall` verification of all `.py` files |
| `validate` | Import smoke tests for TUI, GUI, and installer modules |

## Reducing Rate Limiting

YouTube may block downloads from your IP if you hit it too hard. Here's how to reduce failures:

### Option 1: Extract Browser Cookies (Recommended)

1. Open **⚙ Settings**
2. Leave **Cookies from** on **Auto (try all)** (the default) or select a specific browser
3. Click **⬇ Extract** — the app will auto-generate `~/.spotdl/cookies.txt`
4. Future downloads will use your authenticated YouTube session (much higher rate limits)

**How Auto mode works:** By default, the app tries **Firefox first** (which doesn't lock its cookie database on Windows), then falls back through Chrome, Edge, Brave, and Vivaldi. It stops at the first browser that succeeds.

#### Platform-Specific Cookie Extraction Notes

| Platform | Best Browser | Notes |
|----------|--------------|-------|
| **Windows** | Firefox | Chrome/Edge lock their cookie DB while running — use Auto mode or install Firefox |
| **macOS** | Chrome or Firefox | Safari is not supported by yt-dlp; Chrome and Firefox both work reliably |
| **Linux** | Firefox | Most reliable; Chrome may require `--password-store=basic` flag |

**Linux users:** If Chrome cookie extraction fails with a "keyring" or "password store" error, try:
```bash
# Set the password store environment variable
export CHROMIUM_FLAGS="--password-store=basic"
# Or use Firefox instead (recommended)
```

> **Chrome / Edge users (Windows):** These Chromium-based browsers lock their cookie database while running. If extraction fails, either:
> 1. **Close all browser windows** and try again, or
> 2. **Install Firefox** — it doesn't lock its cookie DB and is the most reliable option, or
> 3. **Use a browser extension** — install [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) for Chrome/Edge, export cookies manually, and paste the file path in the **Cookie file** field

### Option 2: Use a Proxy

1. Open **⚙ Settings**
2. Enter a proxy URL in the **Proxy** field (e.g., `http://host:port`, `socks4://host:port`, or `socks5://host:port`)
3. Press **Enter** to save

### Option 3: Manual Cookie Export (Browser Extension)

If auto-extraction fails (e.g. Chrome locks its database), you can export cookies manually using a browser extension:

1. **Install the extension**
   - Chrome / Edge / Brave: [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Log in to YouTube** in your browser using the Google account you want to use for downloads

3. **Navigate to YouTube** (e.g. open any video on [youtube.com](https://www.youtube.com))

4. **Click the extension icon** in your browser toolbar

5. **Export cookies** — click **Export** or **Save** to download a `cookies.txt` file

6. **Point the app to the file**
   - Open **⚙ Settings** in the app
   - Paste the full path in the **Cookie file** field:
     - Windows: `C:\Users\You\Downloads\cookies.txt`
     - macOS: `/Users/You/Downloads/cookies.txt`
     - Linux: `/home/you/Downloads/cookies.txt`
   - Press **Enter** to save

> **Tip:** YouTube cookies expire every few weeks. Re-export when downloads start failing with rate-limit errors.

### Option 4: Retry Failed Tracks

After a download completes with failures, click **🔄 Retry Failed** to give the failed tracks another chance.
