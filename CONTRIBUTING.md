# Contributing to Spotify Playlist Downloader

Thank you for your interest in contributing! This guide will help you set up a
development environment and get started.

## Prerequisites

- **Python 3.10+**
- **Git**
- **FFmpeg** (for audio conversion testing)
- **spotDL** (the core dependency)

## Quick Setup (All Platforms)

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/spotify_downloader.git
cd spotify_downloader

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (cmd):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies (including dev tools)
pip install -r requirements.txt

# 5. Verify everything works
python -m py_compile spotify_downloader.py
```

## Platform-Specific Setup

### Windows

```powershell
# Ensure Python is on PATH
python --version

# If using Anaconda, create a conda env instead:
conda create -n spotify-dev python=3.13
conda activate spotify-dev

# Install dependencies
pip install -r requirements.txt

# Verify compilation
python -m py_compile spotify_downloader.py
```

**Windows notes:**
- Use PowerShell or cmd; Git Bash works too but some path handling may differ.
- If you encounter GBK encoding errors, set `PYTHONIOENCODING=utf-8`.
- spotDL installs as `spotdl.exe` on PATH.

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python and FFmpeg
brew install python ffmpeg

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify compilation
python -m py_compile spotify_downloader.py
```

**macOS notes:**
- On Apple Silicon (M1/M2/M3/M4), ensure you're using native Python, not Rosetta.
- Safari is not supported for cookie extraction — use Chrome or Firefox for testing.

### Linux (Debian/Ubuntu)

```bash
# Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv ffmpeg git

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify compilation
python -m py_compile spotify_downloader.py
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install python3 python3-pip ffmpeg git
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m py_compile spotify_downloader.py
```

### Linux (Arch/Manjaro)

```bash
sudo pacman -S python python-pip ffmpeg git
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m py_compile spotify_downloader.py
```

## Running the App

```bash
python spotify_downloader.py
```

The app launches a Textual TUI. Use mouse or keyboard to navigate.

## Project Structure

```
spotify_downloader/
├── src/
│   ├── gui/               # CustomTkinter desktop GUI
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
│   ├── models.py
│   ├── state.py
│   ├── spotdl_tools.py
│   ├── manifest.py
│   └── duplicates.py
├── gui_app.py             # GUI entry point
├── spotify_downloader.py  # TUI entry point
├── requirements.txt
├── build.ps1 / build.bat  # Windows EXE build scripts
├── installer.iss          # Inno Setup script
└── README.md
```

## Code Style

- **Formatter:** We recommend [ruff](https://docs.astral.sh/ruff/) or
  [black](https://black.readthedocs.io/) for auto-formatting.
- **Linter:** [ruff](https://docs.astral.sh/ruff/) is recommended.
- **Type hints:** Use Python 3.10+ type hints (`list[str]`, `str | None`, etc.)
- **Docstrings:** Use Google-style docstrings for public methods.
- **Imports:** Group in order: stdlib, third-party, local. Alphabetical within groups.
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes.

### Recommended tooling

```bash
# Install dev tools
pip install ruff

# Check for lint issues
ruff check spotify_downloader.py

# Auto-fix lint issues
ruff check --fix spotify_downloader.py

# Format code
ruff format spotify_downloader.py
```

## Testing

This project currently relies on manual testing via the TUI. To verify your
changes compile and the app launches:

```bash
# 1. Verify no syntax errors
python -m py_compile spotify_downloader.py

# 2. Launch the app and test manually
python spotify_downloader.py

# 3. Test a download with a public playlist
#    - Paste a playlist URL
#    - Click Download
#    - Verify progress tracking works
#    - Check that files are saved to ./downloads

# 4. Test edge cases
#    - Cancel a download mid-progress
#    - Retry failed tracks
#    - Fresh download (overwrite mode)
#    - Toggle settings panel
#    - Extract cookies from browser
#    - Check download history
```

## Making Changes

1. **Create a branch** for your change:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** in `spotify_downloader.py`.

3. **Verify compilation:**
   ```bash
   python -m py_compile spotify_downloader.py
   ```

4. **Test manually** by running the app.

5. **Commit** with a clear message:
   ```bash
   git add spotify_downloader.py
   git commit -m "Add: description of your change"
   ```

6. **Push** and open a Pull Request.

## Commit Messages

Use these prefixes:
- `Add:` — new feature or capability
- `Fix:` — bug fix
- `Update:` — improvement to existing feature
- `Refactor:` — code restructuring without behavior change
- `Docs:` — documentation only
- `Remove:` — removing code or features

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR.
- Describe what changed and why in the PR description.
- Include screenshots if you changed UI elements.
- Make sure `python -m py_compile spotify_downloader.py` passes.
- Test on at least one platform before submitting.

## Reporting Issues

When reporting a bug, include:
- Operating system and Python version
- spotDL version (`spotdl --version`)
- Steps to reproduce
- Relevant log output (from `~/.spotdl/app.log`)
- Screenshots if applicable

## License

By contributing, you agree that your contributions will be licensed under the
same license as the project.
