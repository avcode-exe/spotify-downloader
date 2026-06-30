from __future__ import annotations

import contextlib
import importlib.metadata
import json
import logging
import os
import time
import urllib.request
from threading import Thread
from typing import Any

import customtkinter as ctk
from packaging.version import parse as parse_version

from src.manifest import group_duplicates, scan_output_folder
from src.models import TrackStatus
from src.spotdl_tools import is_valid_spotify_url
from src.state import (
    HISTORY_FILE,
    SETTINGS_FILE,
    load_track_state,
    save_json_secure,
    summarize_track_state,
)

from .duplicates_frame import DuplicatesFrame
from .history_frame import HistoryFrame
from .home_frame import HomeFrame
from .log_frame import LogFrame
from .preview_frame import PreviewFrame
from .settings_frame import SettingsFrame
from .theme import SPOTIFY_BLACK, SPOTIFY_GREEN, apply_theme
from .workers import SpotDLWorker, WorkerResult


class SpotifyDownloaderGUI(ctk.CTk):
    def __init__(self) -> None:
        apply_theme()
        super().__init__()
        self.title("Spotify Playlist Downloader")
        self.geometry("1280x860")
        self.minsize(1024, 720)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        default_bg = SPOTIFY_BLACK
        self.configure(fg_color=default_bg)

        self._settings = self._load_settings()
        self._history = self._load_history()
        self._track_state = load_track_state()
        self._failed_tracks = [
            e["key"] for e in self._track_state if e.get("status") == TrackStatus.FAILED
        ]
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

        # Main scrollable container
        self._scroll_frame = ctk.CTkScrollableFrame(
            self,
            scrollbar_button_hover_color=SPOTIFY_GREEN,
            scrollbar_button_color=SPOTIFY_GREEN,
            corner_radius=0,
            fg_color=SPOTIFY_BLACK,
        )
        self._scroll_frame.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        self._scroll_frame.columnconfigure(0, weight=1)
        self._scroll_frame.columnconfigure(1, weight=1)
        self._scroll_frame.rowconfigure(0, weight=0)
        self._scroll_frame.rowconfigure(1, weight=1)
        self._scroll_frame.rowconfigure(2, weight=1)
        self._scroll_frame.rowconfigure(3, weight=0)

        # Row 0: Home (left) + Settings (right)
        self._home_frame = HomeFrame(
            self._scroll_frame,
            on_download=self._on_download,
            on_fresh=self._on_fresh,
            on_preview=self._on_preview,
            on_duplicates=self._on_duplicates,
            on_retry=self._on_retry,
            on_cancel=self._on_cancel,
        )
        self._home_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))

        self._settings_frame = SettingsFrame(
            self._scroll_frame, self._settings, on_change=self._on_settings_changed
        )
        self._settings_frame.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=(0, 12))

        # Row 1: Preview (left) + Duplicates (right) - initially hidden
        self._preview_frame = PreviewFrame(self._scroll_frame)
        self._preview_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 12), pady=(0, 12))

        self._duplicates_frame = DuplicatesFrame(self._scroll_frame)
        self._duplicates_frame.grid(row=1, column=1, sticky="nsew", padx=(12, 0), pady=(0, 12))

        # Row 2: History (full width)
        self._history_frame = HistoryFrame(self._scroll_frame)
        self._history_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 12))

        # Row 3: Log (full width)
        self._log_frame = LogFrame(self._scroll_frame)
        self._log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=0, pady=(0, 0))

        self._preview_visible = False
        self._duplicates_visible = False
        self._preview_frame.grid_remove()
        self._duplicates_frame.grid_remove()

    def _toggle_preview(self) -> None:
        self._preview_visible = not self._preview_visible
        if self._preview_visible:
            self._preview_frame.grid()
            self._home_frame.preview_btn.configure(text="Hide Preview")
        else:
            self._preview_frame.grid_remove()
            self._home_frame.preview_btn.configure(text="Preview")

    def _toggle_duplicates(self) -> None:
        self._duplicates_visible = not self._duplicates_visible
        if self._duplicates_visible:
            self._duplicates_frame.grid()
            self._home_frame.duplicates_btn.configure(text="Hide Duplicates")
        else:
            self._duplicates_frame.grid_remove()
            self._home_frame.duplicates_btn.configure(text="Duplicates")

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
                with open(SETTINGS_FILE, encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    defaults.update({k: str(v) for k, v in saved.items() if k in defaults})
        except (json.JSONDecodeError, OSError):
            pass
        return defaults

    def _save_settings(self) -> None:
        with contextlib.suppress(OSError):
            save_json_secure(SETTINGS_FILE, self._settings)

    def _load_history(self) -> list[dict[str, Any]]:
        try:
            if os.path.isfile(HISTORY_FILE):
                with open(HISTORY_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
        return []

    def _save_history(self) -> None:
        with contextlib.suppress(OSError):
            save_json_secure(HISTORY_FILE, self._history)

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
        self._history_frame.render(self._history, summarize_track_state(self._track_state))

    def _apply_settings_to_ui(self) -> None:
        self._settings = self._settings_frame.get_settings()

    def _on_settings_changed(self, settings: dict[str, str]) -> None:
        self._settings = settings
        self._save_settings()

    def _refresh_preview(self) -> None:
        output_folder = self._home_frame.output_entry.get().strip() or "./downloads"
        tracks = scan_output_folder(output_folder)
        duplicate_groups = group_duplicates(tracks)
        self._preview_frame.render(tracks, duplicate_groups, self._track_state, output_folder)
        self._duplicates_frame.render(duplicate_groups)

    def _on_preview(self) -> None:
        self._toggle_preview()
        if self._preview_visible:
            self._refresh_preview()
            self._log_frame.write("Preview refreshed")
        else:
            self._log_frame.write("Preview hidden")

    def _on_duplicates(self) -> None:
        self._toggle_duplicates()
        if self._duplicates_visible:
            self._refresh_preview()
            self._log_frame.write("Duplicates list refreshed")
        else:
            self._log_frame.write("Duplicates hidden")

    def _on_download(self) -> None:
        url = self._home_frame.url_entry.get().strip()
        if not url or not is_valid_spotify_url(url):
            self._log_frame.write(
                "Invalid URL. Must be a Spotify playlist or track URL: "
                "https://open.spotify.com/playlist/<id>, "
                "https://open.spotify.com/track/<id>, "
                "spotify:playlist:<id>, or spotify:track:<id>"
            )
            return
        self._check_cookie_file()
        output_folder = self._home_frame.output_entry.get().strip() or "./downloads"
        self._start_worker(url, output_folder, fresh=False)

    def _on_fresh(self) -> None:
        url = self._home_frame.url_entry.get().strip()
        if not url or not is_valid_spotify_url(url):
            self._log_frame.write(
                "Invalid URL. Must be a Spotify playlist or track URL: "
                "https://open.spotify.com/playlist/<id>, "
                "https://open.spotify.com/track/<id>, "
                "spotify:playlist:<id>, or spotify:track:<id>"
            )
            return
        self._check_cookie_file()
        output_folder = self._home_frame.output_entry.get().strip() or "./downloads"
        self._start_worker(url, output_folder, fresh=True)

    def _start_worker(self, url: str, output_folder: str, fresh: bool) -> None:
        self._failed_tracks.clear()
        self._worker = SpotDLWorker(
            self._settings, output_folder, self._on_worker_event, tk_root=self
        )
        self._home_frame.set_busy(True)
        self._worker.start_download(url, fresh=fresh)
        self._download_start_time = time.monotonic()

    def _on_retry(self) -> None:
        if not self._failed_tracks:
            self._log_frame.write("No failed tracks to retry.")
            return
        output_folder = self._home_frame.output_entry.get().strip() or "./downloads"
        if self._worker is None:
            self._worker = SpotDLWorker(
                self._settings,
                output_folder,
                self._on_worker_event,
                tk_root=self,
            )
        urls = list(self._failed_tracks)
        self._failed_tracks.clear()
        self._home_frame.set_busy(True)
        self._worker.start_retry(urls)
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
                result.data.get("track", "\u2014"),
                result.data.get("progress", 0.0),
            )
        elif result.kind == "progress":
            total = result.data.get("total", 0)
            done = result.data.get("done", 0)
            if total > 0:
                self._home_frame.progress.set(done / total)
        elif result.kind == "track":
            self._home_frame.update_status(
                self._home_frame.status_var.get(),
                result.data["track"],
                self._home_frame.progress.get(),
            )
        elif result.kind == "failed":
            url = result.data.get("url")
            if url and url not in self._failed_tracks:
                self._failed_tracks.append(url)
        elif result.kind == "history":
            self._append_history(
                result.data["url"],
                result.data["output_folder"],
                result.data["tracks_downloaded"],
                result.data["status"],
            )
        elif result.kind == "done":
            self._track_state = load_track_state()
            self._home_frame.set_busy(False)
            self._reflect_failed_state()
            self._refresh_preview()
            self._render_history()
        elif result.kind == "error":
            self._log_frame.write(f"\u2717 {result.error}")
            self._home_frame.set_busy(False)
            self._reflect_failed_state()

    def _reflect_failed_state(self) -> None:
        self._home_frame.retry_btn.configure(state="normal" if self._failed_tracks else "disabled")

    def _check_cookie_file(self) -> None:
        cookie_file = self._settings.get("cookie_file", "").strip()
        if cookie_file and not os.path.isfile(cookie_file):
            self._log_frame.write(
                f"Cookie file not found: {cookie_file}\n"
                "   Downloads may fail due to YouTube rate limiting. "
                "Update the path in Settings or re-export cookies from your browser."
            )

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        return is_valid_spotify_url(url)

    def _on_close(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            thread = getattr(self._worker, "_thread", None)
            if thread is not None and thread.is_alive():
                thread.join(timeout=5)
        self.destroy()

    _CHECKED_PACKAGES: list[tuple[str, str]] = [
        ("spotdl", "spotdl"),
        ("yt-dlp", "yt-dlp"),
        ("mutagen", "mutagen"),
    ]

    def _check_dependency_updates(self) -> None:
        def _check() -> None:
            updates: list[str] = []
            for display_name, pkg_name in self._CHECKED_PACKAGES:
                try:
                    installed = importlib.metadata.version(pkg_name)
                except importlib.metadata.PackageNotFoundError:
                    continue
                try:
                    req = urllib.request.Request(
                        f"https://pypi.org/pypi/{pkg_name}/json",
                        headers={"Accept": "application/json"},
                    )
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        data = json.loads(resp.read().decode())
                    latest = data["info"]["version"]
                    if parse_version(latest) > parse_version(installed):
                        updates.append(f"{display_name} {installed} \u2192 {latest}")
                except (urllib.error.URLError, json.JSONDecodeError, KeyError) as exc:
                    logging.getLogger(__name__).debug(
                        "Update check failed for %s: %s", pkg_name, exc
                    )
            if updates:
                pkgs = " ".join(pkg for _, pkg in self._CHECKED_PACKAGES)
                msg = (
                    "Updates available:\n"
                    + "\n".join(f"   \u2022 {u}" for u in updates)
                    + f"\n   Run: pip install -U {pkgs}"
                )
                self.after(0, self._log_frame.write, msg)

        Thread(target=_check, daemon=True).start()
