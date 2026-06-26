#!/usr/bin/env python3
"""
Spotify Playlist Downloader — lightweight modern GUI
"""

from __future__ import annotations

from src.gui.app import SpotifyDownloaderGUI


def main() -> None:
    app = SpotifyDownloaderGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
