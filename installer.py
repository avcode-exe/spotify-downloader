#!/usr/bin/env python3
"""
Installer for Spotify Playlist Downloader.

Offers optional TUI dependency installation while keeping the GUI app as the default.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys


GUI_REQUIREMENTS = ["customtkinter>=5.2.0"]
TUI_REQUIREMENTS = ["textual>=2.0.0"]
CORE_REQUIREMENTS = ["spotdl>=4.5.0", "mutagen>=1.45.0"]


def _is_installed(package: str) -> bool:
    return (
        importlib.util.find_spec(package.split("==")[0].split(">=")[0].split("<")[0])
        is not None
    )


def _install_packages(packages: list[str]) -> int:
    return subprocess.call([sys.executable, "-m", "pip", "install", *packages])


def _ask_yes_no(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} [y/N]: ").strip().lower()
        if answer in {"", "n", "no"}:
            return False
        if answer in {"y", "yes"}:
            return True
        print("Please answer y or n.")


def main() -> int:
    print("Spotify Playlist Downloader Installer")
    print("=" * 40)

    if not _ask_yes_no("Install TUI dependencies (textual) alongside the GUI?"):
        packages = [*GUI_REQUIREMENTS, *CORE_REQUIREMENTS]
        print("Installing GUI dependencies only...")
    else:
        packages = [*GUI_REQUIREMENTS, *TUI_REQUIREMENTS, *CORE_REQUIREMENTS]
        print("Installing GUI + TUI dependencies...")

    missing = [pkg for pkg in packages if not _is_installed(pkg)]
    if missing:
        return _install_packages(missing)

    print("All required dependencies are already installed.")
    print("\nUsage:")
    print("  GUI app: python gui_app.py")
    print("  TUI app: python spotify_downloader.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
