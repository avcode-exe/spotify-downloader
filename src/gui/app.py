from __future__ import annotations


import customtkinter as ctk

from src.state import (
    load_track_state,
)

from .theme import apply_theme
from .duplicates_frame import DuplicatesFrame
from .history_frame import HistoryFrame
from .home_frame import HomeFrame
from .log_frame import LogFrame
from .preview_frame import PreviewFrame
from .settings_frame import SettingsFrame
from .workers import SpotDLWorker


class SpotifyDownloaderGUI(ctk.CTk):
    def __init__(self) -> None:
        apply_theme()
        super().__init__()
        self.title("Spotify Playlist Downloader")
        self.geometry("1200x800")
        self.minsize(1024, 768)

        default_bg = ctk.ThemeManager.theme.get("CTk", {}).get(
            "fg_color", ["#191414", "#191414"]
        )
        self.configure(
            fg_color=default_bg[0] if isinstance(default_bg, list) else default_bg
        )

        self._settings = self._load_settings()
        self._history = self._load_history()
        self._track_state = load_track_state()
        self._worker: SpotDLWorker | None = None
        self._confirm_clean_until = 0.0
        self._download_start_time = 0.0

        self._build_ui()
        self._apply_settings_to_ui()
        self._render_history()
        self._refresh_preview()
        self._check_dependency_updates()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self._scroll_frame = ctk.CTkScrollableFrame(
            self,
            scrollbar_button_hover_color="#1DB954",
            scrollbar_button_color="#1DB954",
            corner_radius=8,
            fg_color="transparent",
        )
        self._scroll_frame.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
        self._scroll_frame.columnconfigure(0, weight=1)
        self._scroll_frame.columnconfigure(1, weight=1)
        self._scroll_frame.rowconfigure(0, weight=0)
        self._scroll_frame.rowconfigure(1, weight=1)
        self._scroll_frame.rowconfigure(2, weight=1)
        self._scroll_frame.rowconfigure(3, weight=0)

        self._home_frame = HomeFrame(
            self._scroll_frame,
            on_download=self._on_download,
            on_fresh=self._on_fresh,
            on_preview=self._on_preview,
            on_duplicates=self._on_duplicates,
            on_retry=self._on_retry,
            on_cancel=self._on_cancel,
        )
        self._home_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))

        self._settings_frame = SettingsFrame(
            self._scroll_frame, self._settings, on_change=self._on_settings_changed
        )
        self._settings_frame.grid(
            row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12)
        )

        self._preview_frame = PreviewFrame(self._scroll_frame)
        self._preview_frame.grid(
            row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12)
        )

        self._duplicates_frame = DuplicatesFrame(self._scroll_frame)
        self._duplicates_frame.grid(
            row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12)
        )

        self._history_frame = HistoryFrame(self._scroll_frame)
        self._history_frame.grid(
            row=2, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 12)
        )

        self._log_frame = LogFrame(self._scroll_frame)
        self._log_frame.grid(
            row=3, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 12)
        )
