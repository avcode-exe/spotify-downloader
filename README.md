# Spotify Playlist Downloader 🎵

A terminal-based UI that downloads Spotify playlists by matching tracks to
YouTube Music (via [spotDL](https://github.com/spotDL/spotify-downloader)).

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://www.python.org/) [![spotDL](https://img.shields.io/badge/spotDL-4.5+-green)](https://github.com/spotDL/spotify-downloader)

## Features

- **Terminal UI** — Rich, interactive interface built with [Textual](https://textual.textualize.io/)
- **Playlist Downloads** — Paste any public Spotify playlist URL and download all tracks
- **Fresh Download Mode** — Overwrite existing files for a clean re-download
- **Retry Failed** — Automatically retry tracks that failed to download
- **Download History** — View your past download sessions with status and timestamps
- **Progress Tracking** — Real-time progress bar, tracks/min rate, and ETA
- **Duplicate Detection** — Skipped (already downloaded) tracks count toward progress for consistency
- **Settings Panel** — Configure format, bitrate, proxy, and cookie file without leaving the app
- **Auto-Extract Cookies** — One-click cookie extraction with smart multi-browser fallback (tries Firefox first on Windows to avoid locked databases)
- **Cookie File Warnings** — Detects missing/expired cookies and YouTube rate-limiting, with actionable guidance
- **Rate-Limit Detection** — Warns when YouTube is blocking downloads and suggests setting a cookie file
- **Cancellation** — Cancel any in-progress download at any time
- **Cross-Platform** — Works on Windows, macOS, and Linux

## Requirements

- **Python 3.10+**
- **FFmpeg** — handles audio conversion (spotDL can auto-install it)
- **yt-dlp** — for audio sourcing and cookie extraction (installed with spotDL)

---

## Installation

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

## Usage

1. Paste a **public** Spotify playlist URL into the top field
   - Example: `https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M`
2. Choose an output folder (default: `./downloads`)
3. Click **Download** (or **⟳ Fresh** to overwrite existing files)
4. Watch the progress — spotDL will fetch metadata, find matching audio on
   YouTube Music, download it, and embed ID3 tags (title, artist, cover art)

## Buttons

| Button | Description |
|--------|-------------|
| ▶ **Download** | Download the playlist (skips already-downloaded tracks) |
| 🔄 **Retry Failed** | Re-download only the tracks that failed in the last session |
| ⟳ **Fresh** | Download everything, overwriting existing files |
| 📜 **History** | Toggle the download history panel |
| ⚙ **Settings** | Toggle the settings panel (format, bitrate, proxy, cookies) |
| ⏹ **Cancel** | Cancel the current download |
| ✕ **Quit** | Exit the application |

## Settings

Open the **⚙ Settings** panel to configure:

| Setting | Description |
|---------|-------------|
| **Format** | Output format: MP3, M4A, FLAC, Opus, OGG, WAV |
| **Bitrate** | Audio bitrate: Auto (default), 64k–320k, or disable conversion |
| **Audio source** | Audio provider: YouTube Music (default), YouTube, SoundCloud, Bandcamp, Piped |
| **Proxy** | HTTP/SOCKS5 proxy URL for bypassing regional restrictions |
| **Cookies from** | Select a browser or **Auto (try all)** — tries Firefox first, then Chrome, Edge, Brave, Vivaldi |
| **Extract** | Click to auto-extract cookies. In Auto mode, tries each browser until one succeeds |
| **Cookie file** | Path to a `cookies.txt` file (Netscape format) for authenticated YouTube access |

All settings are saved to `~/.spotdl/settings.json` and restored on restart.

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
2. Enter a proxy URL in the **Proxy** field (e.g., `http://host:port` or `socks5://host:port`)
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

---

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

- Only **public** playlists work (private playlists will fail).
- Audio quality depends on what YouTube Music offers (typically 128–256 kbps).
- Downloading copyrighted music may violate Spotify's ToS and local copyright laws in your country.
- YouTube cookies expire periodically (every few weeks) — re-extract when downloads start failing.

## Project Structure

```
spotify_downloader/
├── spotify_downloader.py   # Main application (TUI + download logic)
├── requirements.txt        # Python dependencies
├── README.md               # This file
└── downloads/              # Default output directory
```

## Data Files

The app stores data in `~/.spotdl/`:

| File | Description |
|------|-------------|
| `settings.json` | Persisted settings (format, bitrate, audio provider, proxy, cookies, browser) |
| `download_history.json` | Download session history (up to 100 entries) |
| `cookies.txt` | Auto-extracted browser cookies for YouTube authentication |
| `app.log` | Application log file (rotated, 5MB max) |
