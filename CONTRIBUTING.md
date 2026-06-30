# Contributing to Spotify Playlist Downloader

Thank you for your interest in contributing! This guide will help you set up a
development environment and get started.

## Prerequisites

- **Python 3.11+**
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
python -m pytest tests/ -v --tb=short
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

# Verify tests pass
python -m pytest tests/ -v --tb=short
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

# Verify tests pass
python -m pytest tests/ -v --tb=short
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

# Verify tests pass
python -m pytest tests/ -v --tb=short
```

### Linux (Fedora/RHEL)

```bash
sudo dnf install python3 python3-pip ffmpeg git
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v --tb=short
```

### Linux (Arch/Manjaro)

```bash
sudo pacman -S python python-pip ffmpeg git
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests/ -v --tb=short
```

## Running the Apps

The project ships with **two** front-ends:

| App | Entry point | Framework |
|-----|-------------|-----------|
| **TUI** (terminal UI) | `python spotify_downloader.py` | [Textual](https://textual.textualize.io/) |
| **GUI** (desktop UI) | `python gui_app.py` | [PySide6](https://pyside.org/) (Qt 6) |

Both share the same core logic in `src/`. Changes to `src/` affect both front-ends.

## Project Structure

```
spotify_downloader/
├── scripts/
│   ├── __init__.py
│   └── write_version_include.py   # Generates installer/_version.iss
├── src/
│   ├── gui_qt/                    # Active PySide6 desktop GUI
│   │   ├── main_window.py         # QMainWindow with sidebar + stacked widget
│   │   ├── home_panel.py          # Playlist URL and download controls
│   │   ├── settings_panel.py      # Settings panel
│   │   ├── history_panel.py       # Download history
│   │   ├── preview_panel.py       # Local file preview
│   │   ├── duplicates_panel.py    # Duplicate group display
│   │   ├── log_panel.py           # Live log output
│   │   ├── workers.py             # QThread-based spotDL worker
│   │   ├── tour.py                # Guided onboarding tour
│   │   ├── theme.py               # Shared theme (colors, fonts)
│   │   ├── icons.py               # Icon helpers (SVG → QPixmap)
│   │   └── utils.py               # Formatting helpers
│   ├── gui/                       # Legacy CustomTkinter GUI (kept for reference)
│   │   ├── app.py                 # Main GUI application
│   │   ├── home_frame.py          # Playlist URL and download controls
│   │   ├── settings_frame.py      # Settings panel
│   │   ├── preview_frame.py       # Local file preview
│   │   ├── duplicates_frame.py    # Duplicate group display
│   │   ├── history_frame.py       # Download history
│   │   ├── log_frame.py           # Live log output
│   │   ├── workers.py             # Background spotDL execution
│   │   ├── utils.py               # Formatting helpers
│   │   └── theme.py               # Shared theme (colors, fonts)
│   ├── models.py                  # Shared dataclasses and constants
│   ├── state.py                   # Per-track state persistence
│   ├── spotdl_tools.py            # spotDL command and dependency helpers
│   ├── manifest.py                # Local scan and duplicate grouping
│   └── duplicates.py              # Duplicate move/quarantine logic
├── gui_app.py                     # GUI entry point
├── spotify_downloader.py          # TUI entry point
├── installer.iss                  # Inno Setup script for Windows installer
├── build.ps1 / build.bat          # Windows EXE build scripts
├── requirements.txt
├── tests/                         # 271 pytest unit tests
└── README.md
```

## Code Style

- **Formatter:** [ruff](https://docs.astral.sh/ruff/) (configured for black-compatible formatting)
- **Linter:** ruff
- **Type checker:** [mypy](https://mypy.readthedocs.io/)
- **Tests:** [pytest](https://docs.pytest.org/) (271 tests, 2 skipped on Windows)
- **Type hints:** Use Python 3.11+ syntax (`list[str]`, `str | None`, etc.)
- **Docstrings:** Google-style for public methods and modules
- **Imports:** Group in order: stdlib, third-party, local. Alphabetical within groups.
- **Naming:** `snake_case` for functions/variables, `PascalCase` for classes.

### Recommended tooling

```bash
# Install dev tools
pip install ruff mypy pytest

# Check for lint issues
ruff check gui_app.py spotify_downloader.py installer.py src/ tests/

# Auto-fix lint issues
ruff check --fix gui_app.py spotify_downloader.py installer.py src/ tests/

# Format code
ruff format gui_app.py spotify_downloader.py installer.py src/ tests/

# Run full test suite
python -m pytest tests/ -v --tb=short

# Type check
python -m mypy scripts/ src/ gui_app.py installer.py --ignore-missing-imports
```

## Testing

This project has a comprehensive pytest suite covering URL validation, proxy handling,
state persistence, duplicate logic, Qt widgets, workers, and more.

```bash
# Run all tests
python -m pytest tests/ -v --tb=short

# Run a specific test file
python -m pytest tests/test_spotdl_tools.py -v --tb=short

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=term-missing
```

### Manual testing checklist

After running the automated tests, verify the following manually:

1. **TUI** — `python spotify_downloader.py`
   - Paste a public Spotify playlist URL
   - Click Download, watch progress
   - Test Fresh mode, Retry Failed, Cancel
   - Toggle Settings, Preview, and History panels
   - Extract cookies from browser

2. **GUI** — `python gui_app.py`
   - Same feature set as the TUI, verified via the desktop UI
   - Confirm settings persist across restarts

3. **Build** — `.\build.ps1` (Windows)
   - Verifies PyInstaller EXE and Inno Setup installer both compile

## Making Changes

1. **Create a branch** for your change:
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** — core logic lives in `src/`, TUI in `spotify_downloader.py`,
   GUI in `src/gui_qt/`.

3. **Run the linter and formatter:**
   ```bash
   ruff check . && ruff format .
   ```

4. **Run the test suite:**
   ```bash
   python -m pytest tests/ -v --tb=short
   ```

5. **Type-check:**
   ```bash
   python -m mypy src/ gui_app.py installer.py scripts/ --ignore-missing-imports
   ```

6. **Test manually** by running the TUI and/or GUI.

7. **Commit** with a clear message:
   ```bash
   git add -A
   git commit -m "Add: description of your change"
   ```

8. **Push** and open a Pull Request.

## Commit Messages

Use these prefixes:

| Prefix | Purpose |
|--------|---------|
| `Add:` | New feature or capability |
| `Fix:` | Bug fix |
| `Update:` | Improvement to existing feature |
| `Refactor:` | Code restructuring without behavior change |
| `Docs:` | Documentation only |
| `Remove:` | Removing code or features |

## Version Changes

The application version is the single source of truth in `src/__init__.py` (`__version__`).
The build scripts automatically propagate it to the Inno Setup installer. When changing the
version, edit only `src/__init__.py` and run the build script — no other files need updating.

## Pull Request Guidelines

- Keep PRs focused — one feature or fix per PR.
- Describe what changed and why in the PR description.
- Include screenshots if you changed UI elements.
- Ensure `ruff check .` and `ruff format --check .` pass.
- Ensure all 271 tests pass (`python -m pytest tests/ -v`).
- Test on at least one platform before submitting.
- If your change affects the installer or build scripts, verify `.\build.ps1` succeeds.

## Reporting Issues

When reporting a bug, include:

- Operating system and Python version
- spotDL version (`spotdl --version`)
- Steps to reproduce
- Relevant log output (from `~/.spotdl/app.log`)
- Screenshots if applicable

## Continuous Integration

The project runs a CI pipeline on every push and PR (`.github/workflows/ci.yml`) across
**Ubuntu**, **macOS**, and **Windows** with **Python 3.11**, **3.12**, and **3.13**.
Jobs include linting, formatting, full test suite, mypy type-checking, compile verification,
and import smoke tests.

## License

By contributing, you agree that your contributions will be licensed under the
same license as the project.
