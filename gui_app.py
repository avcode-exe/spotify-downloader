#!/usr/bin/env python3
"""
Spotify Playlist Downloader — lightweight modern GUI
"""

from __future__ import annotations

import customtkinter as ctk

from src.gui.app import SpotifyDownloaderGUI


def main() -> None:
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    app = SpotifyDownloaderGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
