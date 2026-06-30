from __future__ import annotations

import contextlib
import json
import os
import time
from typing import Any

from PySide6.QtCore import QSettings, QTimer, Slot
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from src.manifest import group_duplicates, scan_output_folder
from src.spotdl_tools import is_valid_spotify_url
from src.state import (
    HISTORY_FILE,
    SETTINGS_FILE,
    load_track_state,
    save_json_secure,
)

from .duplicates_panel import DuplicatesPanel
from .history_panel import HistoryPanel
from .home_panel import HomePanel
from .log_panel import LogPanel
from .preview_panel import PreviewPanel
from .settings_panel import SettingsPanel
from .sidebar import Sidebar
from .tour import TourOverlay
from .workers import SpotDLWorker


class MainWindow(QWidget):
    """Main application window with sidebar navigation."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Spotify Playlist Downloader")
        self.setMinimumSize(960, 640)
        self.resize(1280, 800)

        self._settings = self._load_settings()
        self._history = self._load_history()
        self._track_state = load_track_state()
        self._failed_tracks: list[str] = []
        self._worker: SpotDLWorker | None = None
        self._download_start_time = 0.0

        # Persistence: track if tour has been shown
        self._settings_store = QSettings("SpotifyDownloader", "App")
        self._tour_shown = self._settings_store.value("tourShown", False, type=bool)

        # Defer expensive UI refreshes so rapid updates collapse into one render.
        self._preview_refresh_timer = QTimer(self)
        self._preview_refresh_timer.setSingleShot(True)
        self._preview_refresh_timer.timeout.connect(self._refresh_preview)
        self._pending_history_render = False

        self._build_ui()
        self._apply_settings_to_ui()
        self._render_history()
        self._schedule_preview_refresh()

        # Show tour on first launch
        if not self._tour_shown:
            QTimer.singleShot(500, self._show_tour)

    def _build_ui(self) -> None:
        # Main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self._sidebar = Sidebar()
        self._sidebar.section_changed.connect(self._on_section_changed)
        main_layout.addWidget(self._sidebar)

        # Content area
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background-color: #0A0A0A;")

        # Panels
        self._home_panel = HomePanel()
        self._home_panel.download_clicked.connect(self._on_download)
        self._home_panel.fresh_clicked.connect(self._on_fresh)
        self._home_panel.retry_clicked.connect(self._on_retry)
        self._home_panel.browse_output_clicked.connect(self._browse_output)

        self._sidebar.cancel_clicked.connect(self._on_cancel)
        self._sidebar.quit_clicked.connect(self._on_quit)

        self._settings_panel = SettingsPanel(self._settings)
        self._settings_panel.settings_changed.connect(self._on_settings_changed)

        self._history_panel = HistoryPanel()
        self._preview_panel = PreviewPanel()
        self._duplicates_panel = DuplicatesPanel()
        self._log_panel = LogPanel()

        self._stack.addWidget(self._home_panel)
        self._stack.addWidget(self._settings_panel)
        self._stack.addWidget(self._history_panel)
        self._stack.addWidget(self._preview_panel)
        self._stack.addWidget(self._duplicates_panel)
        self._stack.addWidget(self._log_panel)

        content_layout.addWidget(self._stack)

        # Status bar
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("background-color: #181818; color: #6A6A6A; font-size: 9pt;")
        self._status_label = QLabel("Ready")
        self._status_bar.addPermanentWidget(self._status_label)
        content_layout.addWidget(self._status_bar)

        main_layout.addWidget(content_container, 1)

    def _on_section_changed(self, section_id: str) -> None:
        section_map = {
            "home": 0,
            "settings": 1,
            "history": 2,
            "preview": 3,
            "duplicates": 4,
            "log": 5,
        }
        idx = section_map.get(section_id, 0)
        self._stack.setCurrentIndex(idx)

        # Update sidebar icon colors
        for sid, _, _ in Sidebar.SECTIONS:
            self._sidebar.set_active_icon_color(sid, sid == section_id)

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
        self._request_history_render()

    def _render_history(self) -> None:
        self._history_panel.render(self._history)

    def _request_history_render(self) -> None:
        if not self._pending_history_render:
            self._pending_history_render = True
            QTimer.singleShot(200, self._render_history)

    def _schedule_preview_refresh(self) -> None:
        self._preview_refresh_timer.start(200)

    def _apply_settings_to_ui(self) -> None:
        self._settings = self._settings_panel.get_settings()

    def _on_settings_changed(self, settings: dict[str, str]) -> None:
        self._settings = settings
        self._save_settings()

    def _refresh_preview(self) -> None:
        output_folder = self._home_panel.get_output_folder() or "./downloads"
        tracks = scan_output_folder(output_folder)
        duplicate_groups = group_duplicates(tracks)
        self._preview_panel.render(tracks, duplicate_groups, self._track_state, output_folder)
        self._duplicates_panel.render(duplicate_groups)

    def _on_download(self) -> None:
        url = self._home_panel.get_url()
        if not url or not is_valid_spotify_url(url):
            self._log_panel.write("Invalid URL. Must be a Spotify playlist or track URL.")
            return
        output_folder = self._home_panel.get_output_folder() or "./downloads"
        self._start_worker(url, output_folder, fresh=False)

    def _on_fresh(self) -> None:
        url = self._home_panel.get_url()
        if not url or not is_valid_spotify_url(url):
            self._log_panel.write("Invalid URL. Must be a Spotify playlist or track URL.")
            return
        output_folder = self._home_panel.get_output_folder() or "./downloads"
        self._start_worker(url, output_folder, fresh=True)

    def _start_worker(self, url: str, output_folder: str, fresh: bool) -> None:
        self._failed_tracks.clear()
        if self._worker is not None:
            self._worker.cancel()
            self._worker.wait(timeout=3000)
        self._worker = SpotDLWorker(self._settings, output_folder)
        self._home_panel.set_busy(True)
        self._sidebar.set_busy(True)
        self._download_start_time = time.monotonic()

        # Connect signals
        self._worker.log_emitted.connect(self._on_worker_log)
        self._worker.status_emitted.connect(self._on_worker_status)
        self._worker.progress_emitted.connect(self._on_worker_progress)
        self._worker.track_emitted.connect(self._on_worker_track)
        self._worker.failed_emitted.connect(self._on_worker_failed)
        self._worker.history_emitted.connect(self._on_worker_history)
        self._worker.done_emitted.connect(self._on_worker_done)
        self._worker.error_emitted.connect(self._on_worker_error)

        if fresh:
            self._worker.start_download(url, fresh=True)
        else:
            self._worker.start_download(url, fresh=False)

    def _on_retry(self) -> None:
        if not self._failed_tracks:
            self._log_panel.write("No failed tracks to retry.")
            return
        output_folder = self._home_panel.get_output_folder() or "./downloads"
        if self._worker is not None:
            self._worker.cancel()
            self._worker.terminate()
            self._worker.wait(timeout=3000)
        self._worker = SpotDLWorker(self._settings, output_folder)
        urls = list(self._failed_tracks)
        self._failed_tracks.clear()
        self._home_panel.set_busy(True)
        self._sidebar.set_busy(True)
        self._download_start_time = time.monotonic()

        self._worker.log_emitted.connect(self._on_worker_log)
        self._worker.status_emitted.connect(self._on_worker_status)
        self._worker.progress_emitted.connect(self._on_worker_progress)
        self._worker.track_emitted.connect(self._on_worker_track)
        self._worker.failed_emitted.connect(self._on_worker_failed)
        self._worker.history_emitted.connect(self._on_worker_history)
        self._worker.done_emitted.connect(self._on_worker_done)
        self._worker.error_emitted.connect(self._on_worker_error)

        self._worker.start_retry(urls)

    def _on_cancel(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self._home_panel.update_status("Cancelled", progress=0.0)

    def closeEvent(self, event) -> None:
        self._on_quit()
        event.accept()

    def _on_quit(self) -> None:
        if self._worker is not None:
            self._worker.cancel()
            self._worker.wait(timeout=5000)
        self.close()

    def _browse_output(self) -> None:
        directory = QFileDialog.getExistingDirectory(self, "Select output folder")
        if directory:
            self._home_panel.set_output_folder(directory)

    @Slot(str)
    def _on_worker_log(self, message: str) -> None:
        self._log_panel.write(message)

    @Slot(dict)
    def _on_worker_status(self, data: dict) -> None:
        self._home_panel.update_status(
            data.get("status", ""),
            data.get("track", "\u2014"),
            data.get("progress", 0.0),
        )
        self._status_label.setText(data.get("status", "Ready"))

    @Slot(dict)
    def _on_worker_progress(self, data: dict) -> None:
        total = data.get("total", 0)
        done = data.get("done", 0)
        if total > 0:
            self._home_panel._progress_bar.setValue(int(done / total * 100))

    @Slot(str)
    def _on_worker_track(self, track: str) -> None:
        current_status = self._home_panel._status_indicator.text()
        self._home_panel.update_status(
            current_status, track, self._home_panel.get_progress_fraction()
        )

    @Slot(str)
    def _on_worker_failed(self, url: str) -> None:
        if url not in self._failed_tracks:
            self._failed_tracks.append(url)
        self._home_panel.set_retry_enabled(True)

    @Slot(dict)
    def _on_worker_history(self, data: dict) -> None:
        self._append_history(
            data["url"],
            data["output_folder"],
            data["tracks_downloaded"],
            data["status"],
        )

    @Slot(dict)
    def _on_worker_done(self, data: dict) -> None:
        self._track_state = load_track_state()
        self._home_panel.set_busy(False)
        self._sidebar.set_busy(False)
        self._home_panel.set_retry_enabled(bool(self._failed_tracks))
        self._render_history()
        self._schedule_preview_refresh()

    @Slot(str)
    def _on_worker_error(self, error: str) -> None:
        self._log_panel.write(f"Error: {error}")
        self._home_panel.set_busy(False)
        self._sidebar.set_busy(False)
        self._home_panel.set_retry_enabled(bool(self._failed_tracks))
        self._schedule_preview_refresh()
        self._request_history_render()

    def _show_tour(self) -> None:
        overlay = TourOverlay(self)

        steps = [
            {
                "target": self._home_panel._url_input,
                "title": "Welcome to Spotify Downloader",
                "text": "Paste a Spotify playlist or track URL here to get started.",
                "position": "right",
            },
            {
                "target": self._home_panel._download_btn,
                "title": "Download",
                "text": "Click Download to start downloading the playlist. Click Fresh to overwrite existing files.",
                "position": "bottom",
            },
            {
                "target": self._home_panel._output_input,
                "title": "Output Folder",
                "text": "Choose where downloaded files will be saved. Click Browse to select a folder.",
                "position": "bottom",
            },
            {
                "target": self._sidebar._list,
                "title": "Navigation",
                "text": "Use the sidebar to switch between Home, Settings, History, Preview, Duplicates, and Log panels.",
                "position": "right",
            },
            {
                "target": self._settings_panel,
                "title": "Settings",
                "text": "Configure audio format, bitrate, proxy, cookies, and more in the Settings panel.",
                "position": "right",
            },
        ]

        overlay.set_steps(steps)
        overlay.show()
        self._settings_store.setValue("tourShown", True)
