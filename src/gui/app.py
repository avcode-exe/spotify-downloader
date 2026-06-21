from __future__ import annotations

import json
import os
import time
from typing import Any

import customtkinter as ctk

from src.manifest import group_duplicates, scan_output_folder
from src.state import (
    HISTORY_FILE,
    SETTINGS_FILE,
    load_track_state,
    summarize_track_state,
)

from .duplicates_frame import DuplicatesFrame
from .history_frame import HistoryFrame
from .home_frame import HomeFrame
from .log_frame import LogFrame
from .preview_frame import PreviewFrame
from .settings_frame import SettingsFrame
from .workers import SpotDLWorker, WorkerResult


class SpotifyDownloaderGUI(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Spotify Playlist Downloader")
        self.geometry("1200x700")
        self.minsize(900, 600)

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
            scrollbar_button_hover_color="#1db954",
            scrollbar_button_color="#1db954",
        )
        self._scroll_frame.grid(row=0, column=0, sticky="nsew")
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
        self._home_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self._settings_frame = SettingsFrame(
            self._scroll_frame, self._settings, on_change=self._on_settings_changed
        )
        self._settings_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=(10, 5))

        self._preview_frame = PreviewFrame(self._scroll_frame)
        self._preview_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self._duplicates_frame = DuplicatesFrame(self._scroll_frame)
        self._duplicates_frame.grid(
            row=1, column=1, sticky="nsew", padx=10, pady=(0, 10)
        )

        self._history_frame = HistoryFrame(self._scroll_frame)
        self._history_frame.grid(
            row=2, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10)
        )

        self._log_frame = LogFrame(self._scroll_frame)
        self._log_frame.grid(
            row=3, column=0, columnspan=2, sticky="nsew", padx=10, pady=(0, 10)
        )

    def _load_settings(self) -> dict[str, str]:
        defaults = {
            "format": "mp3",
            "bitrate": "auto",
            "audio_provider": "youtube-music",
            "proxy": "",
            "cookie_file": "",
            "browser": "auto",
            "duplicate_policy": "skip",
        }
        try:
            if os.path.isfile(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    defaults.update(
                        {k: str(v) for k, v in saved.items() if k in defaults}
                    )
        except (json.JSONDecodeError, OSError):
            pass
        return defaults

    def _save_settings(self) -> None:
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def _load_history(self) -> list[dict[str, Any]]:
        try:
            if os.path.isfile(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
        return []

    def _save_history(self) -> None:
        try:
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
        except OSError:
            pass

    def _append_history(
        self, url: str, output_folder: str, tracks_downloaded: int, status: str
    ) -> None:
        self._history.insert(
            0,
            {
                "url": url,
                "output_folder": output_folder,
                "tracks_downloaded": tracks_downloaded,
                "status": status,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            },
        )
        self._history = self._history[:100]
        self._save_history()
        self._render_history()

    def _render_history(self) -> None:
        self._history_frame.render(
            self._history, summarize_track_state(self._track_state)
        )

    def _apply_settings_to_ui(self) -> None:
        self._settings_frame._on_setting_changed()
        self._settings_frame._loading = False

    def _on_settings_changed(self, settings: dict[str, str]) -> None:
        self._settings = settings
        self._save_settings()

    def _refresh_preview(self) -> None:
        output_folder = self._home_frame.output_entry.get().strip() or "./downloads"
        tracks = scan_output_folder(output_folder)
        duplicate_groups = group_duplicates(tracks)
        self._preview_frame.render(
            tracks, duplicate_groups, self._track_state, output_folder
        )
        self._duplicates_frame.render(duplicate_groups)

    def _on_preview(self) -> None:
        self._refresh_preview()
        self._log_frame.write("🔎 Preview refreshed")

    def _on_duplicates(self) -> None:
        self._refresh_preview()
        self._log_frame.write("📋 Duplicates list refreshed")

    def _on_download(self) -> None:
        url = self._home_frame.url_entry.get().strip()
        if not url:
            self._log_frame.write(
                "Invalid URL. Must start with https://open.spotify.com/playlist/ or spotify:playlist:"
            )
            return
        output_folder = self._home_frame.output_entry.get().strip() or "./downloads"
        self._start_worker(url, output_folder, fresh=False)

    def _on_fresh(self) -> None:
        url = self._home_frame.url_entry.get().strip()
        if not url:
            self._log_frame.write(
                "Invalid URL. Must start with https://open.spotify.com/playlist/ or spotify:playlist:"
            )
            return
        output_folder = self._home_frame.output_entry.get().strip() or "./downloads"
        self._start_worker(url, output_folder, fresh=True)

    def _start_worker(self, url: str, output_folder: str, fresh: bool) -> None:
        self._worker = SpotDLWorker(
            self._settings, output_folder, self._on_worker_event
        )
        self._home_frame.set_busy(True)
        self._worker.start_download(url, fresh=fresh)
        self._download_start_time = time.monotonic()

    def _on_retry(self) -> None:
        if self._worker is None or not self._worker._failed_tracks:
            self._log_frame.write("No failed tracks to retry.")
            return
        self._home_frame.set_busy(True)
        self._worker.start_retry()
        self._download_start_time = time.monotonic()

    def _on_cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self._home_frame.update_status("Cancelled", progress=0.0)

    def _on_worker_event(self, result: WorkerResult) -> None:
        if result.kind == "log":
            self._log_frame.write(result.data["message"])
        elif result.kind == "status":
            self._home_frame.update_status(
                result.data["status"],
                result.data.get("track", "—"),
                result.data.get("progress", 0.0),
            )
        elif result.kind == "track":
            self._home_frame.update_status(
                self._home_frame.status_var.get(),
                result.data["track"],
                self._home_frame.progress.get(),
            )
        elif result.kind == "history":
            self._append_history(
                result.data["url"],
                result.data["output_folder"],
                result.data["tracks_downloaded"],
                result.data["status"],
            )
        elif result.kind == "done":
            self._home_frame.set_busy(False)
            self._refresh_preview()
        elif result.kind == "error":
            self._log_frame.write(f"✗ {result.error}")
            self._home_frame.set_busy(False)

    def _check_dependency_updates(self) -> None:
        self._log_frame.write("✓ Ready")
