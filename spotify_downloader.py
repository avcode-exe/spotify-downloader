#!/usr/bin/env python3
"""
Spotify Playlist Downloader — a terminal-based UI for downloading Spotify
playlists by matching tracks to YouTube Music via spotDL.
"""

from __future__ import annotations

import asyncio
import importlib.metadata
import json
import logging
import os
import re
import shutil
import sys
import time
import urllib.request
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, ProgressBar, RichLog, Select

from src.duplicates import format_quarantine_summary, quarantine_duplicate_copies
from src.manifest import (
    group_duplicates,
    normalize_name,
    scan_output_folder,
    summarize_scan,
)
from src.models import DUPLICATE_POLICY_OPTIONS, LocalTrack
from src.spotdl_tools import (
    build_spotdl_args,
    ensure_deno,
    find_spotdl,
    is_rate_limit_error,
    validate_spotdl,
)
from src.state import (
    HISTORY_FILE,
    SETTINGS_FILE,
    STATE_FILE,
    load_track_state,
    save_track_state,
    summarize_track_state,
    update_paths_from_scan,
    upsert_track_state,
)


LOG_DIR = os.path.join(os.path.expanduser("~"), ".spotdl")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

DEFAULT_SETTINGS: dict[str, str] = {
    "format": "mp3",
    "bitrate": "auto",
    "audio_provider": "youtube-music",
    "proxy": "",
    "cookie_file": "",
    "browser": "auto",
    "duplicate_policy": "skip",
}
BROWSER_OPTIONS: list[tuple[str, str]] = [
    ("Auto (try all)", "auto"),
    ("Chrome", "chrome"),
    ("Firefox", "firefox"),
    ("Edge", "edge"),
    ("Brave", "brave"),
    ("Vivaldi", "vivaldi"),
]
_BROWSER_FALLBACK_ORDER: list[str] = ["firefox", "chrome", "edge", "brave", "vivaldi"]
AUDIO_PROVIDER_OPTIONS: list[tuple[str, str]] = [
    ("YouTube Music (default)", "youtube-music"),
    ("YouTube", "youtube"),
    ("SoundCloud", "soundcloud"),
    ("Bandcamp", "bandcamp"),
    ("Piped", "piped"),
]
FORMAT_OPTIONS: list[tuple[str, str]] = [
    ("MP3 (default)", "mp3"),
    ("M4A (AAC)", "m4a"),
    ("FLAC (lossless)", "flac"),
    ("Opus (efficient)", "opus"),
    ("OGG Vorbis", "ogg"),
    ("WAV (uncompressed)", "wav"),
]
BITRATE_OPTIONS: list[tuple[str, str]] = [
    ("Auto (default)", "auto"),
    ("Disable conversion", "disable"),
    ("64k", "64k"),
    ("96k", "96k"),
    ("128k", "128k"),
    ("160k", "160k"),
    ("192k", "192k"),
    ("256k", "256k"),
    ("320k", "320k"),
]

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")
NOISE_RE = re.compile(
    r"(?:"
    r"^\s*(?:self\.|hdlr\.|File\s+\".*logging.*\"|handleError|callHandlers|emit\(record\)|Arguments:\s*\()"
    r"|^\s*File\s+\".*\""
    r"|^\s*result\s*=\s*self\.fn"
    r"|^\s*display_progress_tracker\.notify_error"
    r"|^\s*Message:\s"
    r"|^\s*logger\.error\("
    r"|^\s*traceback\.__class__"
    r"|in (?:handle|emit|callHandlers)$"
    ")",
    re.IGNORECASE,
)

_SPOTDL_URL_ERROR = (
    "[bold red]✗[/] Invalid URL. Must start with "
    "[cyan]https://open.spotify.com/playlist/[/] or [cyan]spotify:playlist:[/]"
)


def _setup_logger() -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger("spotify_downloader")
    logger.setLevel(logging.DEBUG)
    if logger.handlers:
        return logger
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    return logger


log = logging.getLogger("spotify_downloader")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


class DuplicateManagerScreen(ModalScreen):
    CSS = """
    Screen {
        align: center middle;
    }

    #manager-container {
        width: 90%;
        height: 80%;
        background: #16213e;
        border: solid #1db954;
        padding: 1 2;
    }

    #manager-title {
        text-style: bold;
        color: #1db954;
        text-align: center;
    }

    #manager-log {
        height: 1fr;
        background: #0a0a1a;
        color: #c0c0c0;
        padding: 0 1;
    }

    #manager-buttons {
        height: auto;
        align: center middle;
        margin: 1 0 0 0;
    }

    #manager-move-btn {
        background: #d4890e;
        color: #000000;
        text-style: bold;
        margin: 0 1 0 0;
    }

    #manager-close-btn {
        background: #2a2a3e;
        color: #ffffff;
        text-style: bold;
        margin: 0 0 0 1;
    }
    """

    def __init__(self, duplicate_groups: list[Any]) -> None:
        super().__init__()
        self.duplicate_groups = duplicate_groups

    def compose(self) -> ComposeResult:
        with Container(id="manager-container"):
            yield Label("Duplicate Manager", id="manager-title")
            yield RichLog(id="manager-log", highlight=True, markup=True, max_lines=200)
            with Horizontal(id="manager-buttons"):
                yield Button("Move duplicate copies", id="manager-move-btn")
                yield Button("Close", id="manager-close-btn")

    def on_mount(self) -> None:
        widget = self.query_one("#manager-log", RichLog)
        if not self.duplicate_groups:
            widget.write("[dim]No duplicate groups found. Run Preview first.[/]")
            return
        for group in self.duplicate_groups:
            for line in group.to_log_lines():
                widget.write(line)
            widget.write("")

    @on(Button.Pressed, "#manager-move-btn")
    def on_move(self) -> None:
        self.dismiss("move")

    @on(Button.Pressed, "#manager-close-btn")
    def on_close(self) -> None:
        self.dismiss("close")


class SpotifyDownloader(App):
    TITLE = "Spotify Playlist Downloader"
    SUB_TITLE = "Powered by spotDL"

    CSS = """
    Screen {
        background: #1a1a2e;
    }

    #main-container {
        padding: 1 2;
        height: 100%;
    }

    #header-section {
        height: auto;
        content-align: center middle;
        background: #16213e;
        border: solid #0f3460;
        margin: 0 0 1 0;
        padding: 1 0;
    }

    #app-title {
        text-style: bold;
        color: #1db954;
        text-align: center;
        width: 100%;
    }

    #app-subtitle {
        color: #6b6b8d;
        text-align: center;
        width: 100%;
    }

    #input-section {
        height: auto;
        margin: 0 0 1 0;
        padding: 1 2;
        border: solid #0f3460;
        background: #16213e;
    }

    .input-label {
        color: #a0a0a0;
        margin: 0 0 0 2;
    }

    Input {
        margin: 0 0 1 0;
        background: #0f3460;
        color: #ffffff;
        border: none;
        padding: 0 1;
    }

    Input:focus {
        border: solid #1db954;
    }

    .groups-row {
        height: auto;
        margin-top: 1;
        align: center middle;
    }

    .button-group {
        height: auto;
        padding: 1;
        border: solid #0f3460;
        background: #16213e;
        margin: 0 1 0 0;
    }

    .button-group Horizontal {
        height: auto;
        align: center middle;
    }

    #download-btn {
        background: #1db954;
        color: #000000;
        text-style: bold;
        min-width: 20;
        margin: 0 1 0 0;
    }

    #download-btn:hover {
        background: #1ed760;
    }

    #download-btn:disabled {
        background: #2a2a3e;
        color: #555555;
    }

    #preview-btn {
        background: #2a5a2a;
        color: #88cc88;
        text-style: bold;
        min-width: 16;
        margin: 0 1;
    }

    #preview-btn:hover {
        background: #3a7a3a;
        color: #aaffaa;
    }

    #duplicates-btn {
        background: #2a2a3e;
        color: #8888cc;
        text-style: bold;
        min-width: 16;
        margin: 0 1;
    }

    #duplicates-btn:hover {
        background: #3a3a5e;
    }

    #clean-btn {
        background: #8a4b00;
        color: #ffffff;
        text-style: bold;
        min-width: 16;
        margin: 0 1;
    }

    #clean-btn:hover {
        background: #a86000;
    }

    #cancel-btn:disabled,
    #preview-btn:disabled,
    #duplicates-btn:disabled,
    #clean-btn:disabled {
        background: #2a2a3e;
        color: #555555;
    }

    #retry-btn {
        background: #2a2a3e;
        color: #ff9944;
        text-style: bold;
        min-width: 20;
        margin: 0 1;
    }

    #retry-btn:hover {
        background: #3a3a5e;
        color: #ffbb66;
    }

    #retry-btn:disabled {
        background: #2a2a3e;
        color: #555555;
    }

    #fresh-btn {
        background: #d4890e;
        color: #000000;
        text-style: bold;
        min-width: 20;
        margin: 0 1;
    }

    #fresh-btn:hover {
        background: #f0a020;
    }

    #fresh-btn:disabled {
        background: #2a2a3e;
        color: #555555;
    }

    #history-btn {
        background: #2a2a3e;
        color: #8888cc;
        text-style: bold;
        min-width: 20;
        margin: 0 1;
    }

    #history-btn:hover {
        background: #3a3a5e;
    }

    #settings-btn {
        background: #2a2a3e;
        color: #cccc88;
        text-style: bold;
        min-width: 20;
        margin: 0 1;
    }

    #settings-btn:hover {
        background: #3a3a5e;
    }

    #quit-btn {
        background: #2a2a3e;
        color: #cc4444;
        text-style: bold;
        min-width: 20;
        margin: 0 1;
    }

    #quit-btn:hover {
        background: #5a2a2e;
        color: #ff6666;
    }

    #history-section {
        height: auto;
        max-height: 12;
        margin: 0 0 1 0;
        padding: 1 2;
        border: solid #0f3460;
        background: #0d1117;
        overflow-y: auto;
        display: none;
    }

    #history-section.visible {
        display: block;
    }

    #history-header {
        text-style: bold;
        color: #8888cc;
        margin: 0 0 1 0;
    }

    #clear-history-btn {
        background: #5a2a2e;
        color: #ff6666;
        text-style: bold;
        min-width: 10;
        margin: 0 0 0 1;
    }

    #clear-history-btn:hover {
        background: #7a3a3e;
        color: #ff8888;
    }

    #history-log {
        height: auto;
        max-height: 10;
        background: #0d1117;
        color: #c0c0c0;
        padding: 0 1;
    }

    #preview-section {
        height: auto;
        max-height: 14;
        margin: 0 0 1 0;
        padding: 1 2;
        border: solid #2a5a2a;
        background: #0d1117;
        display: none;
    }

    #preview-section.visible {
        display: block;
    }

    #preview-header {
        text-style: bold;
        color: #88cc88;
        margin: 0 0 1 0;
    }

    #preview-log {
        height: auto;
        max-height: 12;
        background: #0d1117;
        color: #c0c0c0;
        padding: 0 1;
    }

    #settings-section {
        height: auto;
        margin: 0 0 1 0;
        padding: 1 2;
        border: solid #0f3460;
        background: #16213e;
        display: none;
    }

    #settings-section.visible {
        display: block;
    }

    #settings-header {
        text-style: bold;
        color: #cccc88;
        margin: 0 0 1 0;
    }

    .settings-row {
        height: auto;
        margin: 0 0 1 0;
    }

    .settings-label {
        color: #a0a0a0;
        width: 18;
    }

    Select {
        width: 30;
        background: #0f3460;
        color: #ffffff;
    }

    #proxy-input {
        width: 40;
        background: #0f3460;
        color: #ffffff;
        border: none;
        padding: 0 1;
    }

    #proxy-input:focus {
        border: solid #cccc88;
    }

    #cookie-file-input {
        width: 40;
        background: #0f3460;
        color: #ffffff;
        border: none;
        padding: 0 1;
    }

    #cookie-file-input:focus {
        border: solid #cccc88;
    }

    #browser-select {
        width: 20;
        background: #0f3460;
        color: #ffffff;
    }

    #duplicate-policy-select {
        width: 28;
        background: #0f3460;
        color: #ffffff;
    }

    #extract-cookies-btn {
        background: #2a5a2a;
        color: #88cc88;
        text-style: bold;
        min-width: 16;
        margin: 0 0 0 1;
    }

    #extract-cookies-btn:hover {
        background: #3a7a3a;
        color: #aaffaa;
    }

    #extract-cookies-btn:disabled {
        background: #2a2a3e;
        color: #555555;
    }

    #settings-status {
        color: #6b6b8d;
        margin: 1 0 0 0;
        text-style: italic;
    }

    #status-section {
        height: auto;
        margin: 0 0 1 0;
        padding: 1 2;
        border: solid #0f3460;
        background: #16213e;
    }

    #progress-bar {
        margin: 0 0 1 0;
    }

    .stat-row {
        height: auto;
        margin: 0 0 0 0;
    }

    .stat-label {
        color: #888888;
        width: 12;
    }

    .stat-value {
        color: #ffffff;
        width: 1fr;
    }

    #log {
        height: 1fr;
        min-height: 6;
        border: solid #0f3460;
        background: #0a0a1a;
        color: #c0c0c0;
        padding: 0 1;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self._process: asyncio.subprocess.Process | None = None
        self._progress_bar: ProgressBar | None = None
        self._status_label: Label | None = None
        self._track_label: Label | None = None
        self._log_widget: RichLog | None = None
        self._history_widget: RichLog | None = None
        self._preview_widget: RichLog | None = None
        self._cancel_requested: bool = False
        self._in_traceback: bool = False
        self._failed_tracks: list[str] = []
        self._download_start_time: float = 0.0
        self._track_timestamps: list[float] = []
        self._rate_limit_hint_shown: bool = False
        self._history_visible: bool = False
        self._settings_visible: bool = False
        self._preview_section_visible: bool = False
        self._settings_loading: bool = True
        self._settings: dict[str, str] = self._load_settings()
        self._history: list[dict] = self._load_history()
        self._track_state: list[dict] = load_track_state()
        self._duplicate_groups: list[Any] = []
        self._last_scan: list[LocalTrack] = []
        self._confirm_clean_until: float = 0.0
        log.info(
            "App initialized | history=%d settings=%s track_state=%s",
            len(self._history),
            self._settings,
            len(self._track_state),
        )

    def compose(self) -> ComposeResult:
        with ScrollableContainer(id="main-container"):
            with Container(id="header-section"):
                yield Label("🎵  Spotify Playlist Downloader", id="app-title")
                yield Label(
                    "Paste a public playlist URL and press Download", id="app-subtitle"
                )

            with Container(id="input-section"):
                yield Label("Playlist URL:", classes="input-label")
                yield Input(
                    placeholder="https://open.spotify.com/playlist/...",
                    id="url-input",
                )
                yield Label("Output folder:", classes="input-label")
                yield Input(
                    placeholder="./downloads", value="./downloads", id="output-input"
                )

            with Horizontal(classes="groups-row"):
                with Container(classes="button-group"):
                    with Horizontal():
                        yield Button(
                            "▶  Download", id="download-btn", variant="success"
                        )
                        yield Button("⟳  Fresh", id="fresh-btn")
                        yield Button("🔄 Retry Failed", id="retry-btn", disabled=True)
                with Container(classes="button-group"):
                    with Horizontal():
                        yield Button("🔎 Preview", id="preview-btn")
                        yield Button("📋 Duplicates", id="duplicates-btn")
                        yield Button("🧹 Clean", id="clean-btn")

            with Horizontal(classes="groups-row"):
                with Container(classes="button-group"):
                    with Horizontal():
                        yield Button("📜 History", id="history-btn")
                        yield Button("⚙ Settings", id="settings-btn")
                        yield Button("🗑  Clear History & Log", id="clear-history-btn")
                with Container(classes="button-group"):
                    with Horizontal():
                        yield Button(
                            "⏹  Cancel",
                            id="cancel-btn",
                            variant="error",
                            disabled=True,
                        )
                        yield Button("✕  Quit", id="quit-btn")

            with Container(id="settings-section"):
                yield Label("⚙  Settings", id="settings-header")
                with Horizontal(classes="settings-row"):
                    yield Label("Format:", classes="settings-label")
                    yield Select(
                        FORMAT_OPTIONS,
                        id="format-select",
                        prompt="Select format…",
                        value="mp3",
                    )
                with Horizontal(classes="settings-row"):
                    yield Label("Bitrate:", classes="settings-label")
                    yield Select(
                        BITRATE_OPTIONS,
                        id="bitrate-select",
                        prompt="Select bitrate…",
                        value="auto",
                    )
                with Horizontal(classes="settings-row"):
                    yield Label("Audio source:", classes="settings-label")
                    yield Select(
                        AUDIO_PROVIDER_OPTIONS,
                        id="audio-provider-select",
                        prompt="Select source…",
                        value="youtube-music",
                    )
                with Horizontal(classes="settings-row"):
                    yield Label("Duplicate:", classes="settings-label")
                    yield Select(
                        DUPLICATE_POLICY_OPTIONS,
                        id="duplicate-policy-select",
                        prompt="Select policy…",
                        value="skip",
                    )
                with Horizontal(classes="settings-row"):
                    yield Label("Proxy:", classes="settings-label")
                    yield Input(
                        placeholder="http://host:port (optional)",
                        id="proxy-input",
                        value="",
                    )
                with Horizontal(classes="settings-row"):
                    yield Label("Cookies from:", classes="settings-label")
                    yield Select(
                        BROWSER_OPTIONS,
                        id="browser-select",
                        prompt="Select browser…",
                        value="auto",
                    )
                    yield Button("⬇ Extract", id="extract-cookies-btn")
                with Horizontal(classes="settings-row"):
                    yield Label("Cookie file:", classes="settings-label")
                    yield Input(
                        placeholder="path/to/cookies.txt (optional)",
                        id="cookie-file-input",
                        value="",
                    )
                yield Label("", id="settings-status")

            with Container(id="history-section"):
                yield Label("📜 Download History", id="history-header")
                yield RichLog(
                    id="history-log",
                    highlight=True,
                    markup=True,
                    max_lines=50,
                    auto_scroll=False,
                )

            with Container(id="preview-section"):
                yield Label("🔎 Download Preview", id="preview-header")
                yield RichLog(
                    id="preview-log",
                    highlight=True,
                    markup=True,
                    max_lines=80,
                    auto_scroll=False,
                )

            with Container(id="status-section"):
                yield ProgressBar(total=100, id="progress-bar", show_percentage=True)
                with Horizontal(classes="stat-row"):
                    yield Label("Status:", classes="stat-label")
                    yield Label("Ready", id="status-value", classes="stat-value")
                with Horizontal(classes="stat-row"):
                    yield Label("Track:", classes="stat-label")
                    yield Label("—", id="track-value", classes="stat-value")

            yield RichLog(
                id="log", highlight=True, markup=True, max_lines=200, auto_scroll=False
            )

    def on_mount(self) -> None:
        log.info("App mounted — UI widgets ready")
        self._progress_bar = self.query_one("#progress-bar", ProgressBar)
        self._status_label = self.query_one("#status-value", Label)
        self._track_label = self.query_one("#track-value", Label)
        self._log_widget = self.query_one("#log", RichLog)
        self._history_widget = self.query_one("#history-log", RichLog)
        self._preview_widget = self.query_one("#preview-log", RichLog)
        self._apply_settings_to_ui()
        self._log_widget.write("[bold green]✓[/] Ready!")
        self._log_widget.write(
            "[dim]Enter a Spotify playlist URL above and press Preview or Download.[/]"
        )
        self._render_history()
        self.query_one("#url-input", Input).focus()
        self.run_worker(self._check_dependency_updates(), exclusive=True)

    @staticmethod
    def _load_settings() -> dict[str, str]:
        settings = dict(DEFAULT_SETTINGS)
        try:
            if os.path.isfile(SETTINGS_FILE):
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    settings.update(
                        {k: str(v) for k, v in saved.items() if k in DEFAULT_SETTINGS}
                    )
                    log.info(
                        "Settings loaded | file=%s settings=%s", SETTINGS_FILE, settings
                    )
                    return settings
                log.warning("Settings file has unexpected format, using defaults")
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Could not load settings: %s", exc)
        return settings

    def _save_settings(self) -> None:
        try:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2, ensure_ascii=False)
            log.info(
                "Settings saved | file=%s settings=%s", SETTINGS_FILE, self._settings
            )
        except OSError as exc:
            log.error("Could not save settings | error=%s", exc)
            self._log(f"[bold red]✗[/] Could not save settings: {exc}")

    def _apply_settings_to_ui(self) -> None:
        self._settings_loading = True
        try:
            fmt = self._settings.get("format", "mp3")
            bitrate = self._settings.get("bitrate", "auto")
            proxy = self._settings.get("proxy", "")
            cookie_file = self._settings.get("cookie_file", "")
            self.query_one("#format-select", Select).value = fmt
            self.query_one("#bitrate-select", Select).value = bitrate
            self.query_one("#audio-provider-select", Select).value = self._settings.get(
                "audio_provider", "youtube-music"
            )
            duplicate_policy = self._settings.get("duplicate_policy", "skip")
            if duplicate_policy not in dict(DUPLICATE_POLICY_OPTIONS):
                duplicate_policy = "skip"
                self._settings["duplicate_policy"] = duplicate_policy
            self.query_one("#duplicate-policy-select", Select).value = duplicate_policy
            self.query_one("#proxy-input", Input).value = proxy
            self.query_one("#cookie-file-input", Input).value = cookie_file
            self.query_one("#browser-select", Select).value = self._settings.get(
                "browser", "auto"
            )
            self._update_settings_status()
            log.debug("Settings applied to UI | format=%s bitrate=%s", fmt, bitrate)
        finally:
            self._settings_loading = False

    def _update_settings_status(self) -> None:
        fmt = self._settings.get("format", "mp3")
        bitrate = self._settings.get("bitrate", "auto")
        proxy = self._settings.get("proxy", "")
        cookie_file = self._settings.get("cookie_file", "")
        audio_provider = self._settings.get("audio_provider", "youtube-music")
        duplicate_policy = self._settings.get("duplicate_policy", "skip")
        if duplicate_policy not in dict(DUPLICATE_POLICY_OPTIONS):
            duplicate_policy = "skip"
        provider_label = audio_provider.replace("-", " ").title()
        policy_label = dict(DUPLICATE_POLICY_OPTIONS).get(
            duplicate_policy, duplicate_policy
        )
        parts = [
            f"Format: {fmt.upper()}",
            f"Bitrate: {bitrate}",
            f"Source: {provider_label}",
            f"Duplicate: {policy_label}",
        ]
        if proxy:
            parts.append(f"Proxy: {proxy}")
        browser = self._settings.get("browser", "auto")
        browser_label = "Auto" if browser == "auto" else browser.title()
        if cookie_file:
            parts.append(f"Cookies: {browser_label} → {os.path.basename(cookie_file)}")
        self.query_one("#settings-status", Label).update(" · ".join(parts))

    @on(Button.Pressed, "#settings-btn")
    def on_settings_toggle(self) -> None:
        self._settings_visible = not self._settings_visible
        section = self.query_one("#settings-section")
        if self._settings_visible:
            section.add_class("visible")
        else:
            section.remove_class("visible")
        log.debug("Settings panel toggled | visible=%s", self._settings_visible)

    @on(Select.Changed, "#format-select")
    def on_format_changed(self, event: Select.Changed) -> None:
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "mp3"
        if self._settings.get("format") == value:
            return
        self._settings["format"] = value
        self._save_settings()
        self._update_settings_status()

    @on(Select.Changed, "#bitrate-select")
    def on_bitrate_changed(self, event: Select.Changed) -> None:
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "auto"
        if self._settings.get("bitrate") == value:
            return
        self._settings["bitrate"] = value
        self._save_settings()
        self._update_settings_status()

    @on(Select.Changed, "#audio-provider-select")
    def on_audio_provider_changed(self, event: Select.Changed) -> None:
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "youtube-music"
        if self._settings.get("audio_provider") == value:
            return
        self._settings["audio_provider"] = value
        self._save_settings()
        self._update_settings_status()

    @on(Select.Changed, "#duplicate-policy-select")
    def on_duplicate_policy_changed(self, event: Select.Changed) -> None:
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "skip"
        if self._settings.get("duplicate_policy") == value:
            return
        self._settings["duplicate_policy"] = value
        self._save_settings()
        self._update_settings_status()

    @on(Input.Submitted, "#proxy-input")
    def on_proxy_submitted(self, event: Input.Submitted) -> None:
        proxy = event.value.strip()
        if proxy and not self._is_valid_proxy(proxy):
            self._log(
                "[bold yellow]⚠[/] Proxy must start with http://, https://, or socks5://"
            )
            log.warning("Invalid proxy format | proxy=%s", proxy)
            return
        self._settings["proxy"] = proxy
        self._save_settings()
        self._update_settings_status()

    @on(Input.Submitted, "#cookie-file-input")
    def on_cookie_file_submitted(self, event: Input.Submitted) -> None:
        cookie_file = event.value.strip()
        if cookie_file and not os.path.isfile(cookie_file):
            self._log(
                f"[bold yellow]⚠[/] Cookie file not found: [bold]{cookie_file}[/]"
            )
            log.warning("Cookie file not found | path=%s", cookie_file)
        self._settings["cookie_file"] = cookie_file
        self._save_settings()
        self._update_settings_status()

    @on(Select.Changed, "#browser-select")
    def on_browser_changed(self, event: Select.Changed) -> None:
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "auto"
        if self._settings.get("browser") == value:
            return
        self._settings["browser"] = value
        self._save_settings()
        self._update_settings_status()

    async def _extract_from_browser(
        self,
        ytdlp: str,
        browser: str,
        cookie_path: str,
    ) -> tuple[bool, str]:
        proc = await asyncio.create_subprocess_exec(
            ytdlp,
            "--cookies-from-browser",
            browser,
            "--cookies",
            cookie_path,
            "--skip-download",
            "https://www.youtube.com",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace").strip()
        return proc.returncode == 0 and os.path.isfile(cookie_path), output

    @on(Button.Pressed, "#extract-cookies-btn")
    async def on_extract_cookies(self) -> None:
        chosen_browser = self._settings.get("browser", "auto")
        cookie_dir = os.path.join(os.path.expanduser("~"), ".spotdl")
        cookie_path = os.path.join(cookie_dir, "cookies.txt")
        ytdlp = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
        if ytdlp is None:
            self._log(
                "[bold red]✗[/] [bold]yt-dlp[/] not found.\n"
                "  Install it with: [bold cyan]pip install yt-dlp[/]"
            )
            log.error("yt-dlp not found for cookie extraction")
            return
        self.query_one("#extract-cookies-btn", Button).disabled = True
        log.info(
            "Extracting cookies | browser=%s output=%s", chosen_browser, cookie_path
        )
        try:
            os.makedirs(cookie_dir, exist_ok=True)
            browsers_to_try: list[str]
            if chosen_browser == "auto":
                browsers_to_try = list(_BROWSER_FALLBACK_ORDER)
                self._log(
                    "[bold cyan]ℹ[/] Auto mode — trying browsers in order: "
                    f"[bold]{', '.join(b.title() for b in browsers_to_try)}[/]"
                )
            else:
                browsers_to_try = [chosen_browser]
                self._log(
                    f"[bold cyan]ℹ[/] Extracting cookies from [bold]{chosen_browser.title()}[/]…"
                )
            last_output = ""
            for browser in browsers_to_try:
                self._log(f"[dim]   Trying {browser.title()}…[/]")
                log.debug("Trying browser | browser=%s", browser)
                try:
                    success, output = await self._extract_from_browser(
                        ytdlp,
                        browser,
                        cookie_path,
                    )
                except Exception as exc:
                    log.warning(
                        "Browser extraction exception | browser=%s error=%s",
                        browser,
                        exc,
                    )
                    last_output = str(exc)
                    continue
                last_output = output
                if success:
                    self._settings["cookie_file"] = cookie_path
                    self._save_settings()
                    self.query_one("#cookie-file-input", Input).value = cookie_path
                    self._update_settings_status()
                    self._log(
                        f"[bold green]✓[/] Cookies extracted from "
                        f"[bold]{browser.title()}[/] → [bold]{cookie_path}[/]"
                    )
                    log.info(
                        "Cookie extraction successful | browser=%s path=%s",
                        browser,
                        cookie_path,
                    )
                    return
                output_lower = output.lower() if output else ""
                is_locked = (
                    "could not copy" in output_lower
                    or "permission denied" in output_lower
                )
                log.debug(
                    "Browser extraction failed | browser=%s locked=%s output=%s",
                    browser,
                    is_locked,
                    output[:120],
                )
                if not is_locked and chosen_browser != "auto":
                    break
            self._show_extraction_failed(chosen_browser, browsers_to_try, last_output)
        except Exception as exc:
            self._log(f"[bold red]✗[/] Cookie extraction error: {exc}")
            log.error("Cookie extraction exception | error=%s", exc, exc_info=True)
        finally:
            self.query_one("#extract-cookies-btn", Button).disabled = False

    def _show_extraction_failed(
        self,
        chosen_browser: str,
        browsers_tried: list[str],
        output: str,
    ) -> None:
        output_lower = output.lower() if output else ""
        is_locked = (
            "could not copy" in output_lower or "permission denied" in output_lower
        )
        if is_locked:
            tried_names = ", ".join(b.title() for b in browsers_tried)
            self._log(
                f"[bold red]✗[/] Cookie extraction failed — all browsers lock their database while running.\n"
                f"   [dim]Tried: {tried_names}[/]\n\n"
                "   [bold]Workarounds:[/]\n"
                "   1. Close [bold]all browser windows[/] and try again\n"
                "   2. Install [bold]Firefox[/] (doesn't lock its cookie DB) — then select it in Settings\n"
                "   3. Use a browser extension to export cookies manually\n"
                "      Export → save as cookies.txt → paste path in Cookie file field"
            )
        else:
            self._log(
                f"[bold red]✗[/] Cookie extraction failed.\n   [dim]{output[:200] if output else 'No output'}[/]"
            )
        log.error(
            "Cookie extraction failed | browsers=%s output=%s",
            browsers_tried,
            output[:200],
        )

    _CHECKED_PACKAGES: list[tuple[str, str]] = [
        ("spotdl", "spotdl"),
        ("yt-dlp", "yt-dlp"),
        ("mutagen", "mutagen"),
    ]

    @staticmethod
    def _get_installed_version(package_name: str) -> str | None:
        try:
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            return None

    @staticmethod
    async def _get_latest_version(package_name: str) -> str | None:
        url = f"https://pypi.org/pypi/{package_name}/json"
        try:
            req = urllib.request.Request(url, headers={"Accept": "application/json"})
            loop = asyncio.get_running_loop()
            resp = await loop.run_in_executor(
                None, lambda: urllib.request.urlopen(req, timeout=8)
            )
            data = json.loads(resp.read().decode())
            return data["info"]["version"]
        except Exception as exc:
            log.debug("Version check failed for %s | error=%s", package_name, exc)
            return None

    @staticmethod
    def _version_gt(a: str, b: str) -> bool:
        try:
            from packaging.version import Version

            return Version(a) > Version(b)
        except Exception:
            pass
        return False

    async def _check_dependency_updates(self) -> None:
        updates: list[str] = []
        for display_name, pkg_name in self._CHECKED_PACKAGES:
            installed = self._get_installed_version(pkg_name)
            if installed is None:
                continue
            latest = await self._get_latest_version(pkg_name)
            if latest and self._version_gt(latest, installed):
                updates.append(f"{display_name} {installed} → {latest}")
                log.info(
                    "Update available | package=%s installed=%s latest=%s",
                    pkg_name,
                    installed,
                    latest,
                )
        if updates:
            pkgs = " ".join(pkg for _, pkg in self._CHECKED_PACKAGES)
            self._log(
                "[bold cyan]⬆[/] [bold]Updates available:[/]\n"
                + "\n".join(f"   • [bold]{u}[/]" for u in updates)
                + f"\n   [dim]Run:[/] [bold cyan]pip install -U {pkgs}[/]"
            )

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        return url.startswith("https://open.spotify.com/playlist/") or url.startswith(
            "spotify:playlist:"
        )

    @staticmethod
    def _is_valid_proxy(proxy: str) -> bool:
        return proxy.startswith(("http://", "https://", "socks4://", "socks5://"))

    def _check_cookie_file(self) -> None:
        cookie_file = self._settings.get("cookie_file", "").strip()
        if cookie_file and not os.path.isfile(cookie_file):
            self._log(
                f"[bold yellow]⚠[/] Cookie file not found: [bold]{cookie_file}[/]\n"
                "   [dim]Downloads may fail due to YouTube rate limiting. "
                "Update the path in Settings or re-export cookies from your browser.[/]"
            )
            log.warning("Cookie file missing | path=%s", cookie_file)

    @staticmethod
    def _load_history() -> list[dict]:
        try:
            if os.path.isfile(HISTORY_FILE):
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    log.info(
                        "History loaded | entries=%d file=%s", len(data), HISTORY_FILE
                    )
                    return data
                log.warning("History file has unexpected format, ignoring")
        except (json.JSONDecodeError, OSError) as exc:
            log.warning("Could not load history: %s", exc)
        return []

    def _save_history(self) -> None:
        try:
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(self._history, f, indent=2, ensure_ascii=False)
            log.debug(
                "History saved | entries=%d file=%s", len(self._history), HISTORY_FILE
            )
        except OSError as exc:
            log.error("Could not save history | error=%s", exc)
            self._log(f"[bold red]✗[/] Could not save history: {exc}")

    def _append_history(
        self, url: str, output_folder: str, tracks_downloaded: int, status: str
    ) -> None:
        entry = {
            "url": url,
            "output_folder": output_folder,
            "tracks_downloaded": tracks_downloaded,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._history.insert(0, entry)
        self._history = self._history[:100]
        log.info(
            "History entry recorded | url=%s tracks=%d status=%s folder=%s",
            url,
            tracks_downloaded,
            status,
            output_folder,
        )
        self._save_history()
        self._render_history()

    def _render_history(self) -> None:
        if self._history_widget is None:
            return
        self._history_widget.clear()
        if not self._history:
            self._history_widget.write("[dim]No downloads yet.[/]")
            return
        for entry in self._history:
            ts = entry.get("timestamp", "")
            try:
                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                time_str = ts[:16] if ts else "unknown"
            url = entry.get("url", "")
            short_url = url.split("?")[0] if url else "(unknown)"
            if len(short_url) > 60:
                short_url = short_url[:57] + "…"
            tracks = entry.get("tracks_downloaded", 0)
            status = entry.get("status", "unknown")
            folder = entry.get("output_folder", "")
            status_color = (
                "green"
                if status == "completed"
                else "red"
                if status == "failed"
                else "yellow"
            )
            self._history_widget.write(
                f"[dim]{time_str}[/]  "
                f"[{status_color}]{status}[/]  "
                f"[bold]{tracks}[/] track(s)  "
                f"[cyan]{short_url}[/]"
            )
            if folder:
                self._history_widget.write(f"  [dim]→ {folder}[/]")
        self._history_widget.write("")
        state_summary = summarize_track_state(self._track_state)
        self._history_widget.write(
            "[dim]Track state:[/] "
            f"[green]{state_summary['downloaded']}[/] downloaded · "
            f"[yellow]{state_summary['skipped']}[/] skipped · "
            f"[red]{state_summary['failed']}[/] failed · "
            f"[orange1]{state_summary['quarantined']}[/] quarantined"
        )

    def _lock_ui(self) -> None:
        self.query_one("#download-btn", Button).disabled = True
        self.query_one("#preview-btn", Button).disabled = True
        self.query_one("#duplicates-btn", Button).disabled = True
        self.query_one("#clean-btn", Button).disabled = True
        self.query_one("#retry-btn", Button).disabled = True
        self.query_one("#fresh-btn", Button).disabled = True
        self.query_one("#cancel-btn", Button).disabled = False

    def _unlock_ui(self) -> None:
        self.query_one("#download-btn", Button).disabled = False
        self.query_one("#preview-btn", Button).disabled = False
        self.query_one("#duplicates-btn", Button).disabled = False
        self.query_one("#clean-btn", Button).disabled = False
        self.query_one("#fresh-btn", Button).disabled = False
        self.query_one("#cancel-btn", Button).disabled = True
        self.query_one("#retry-btn", Button).disabled = not self._failed_tracks

    def _kill_process(self) -> None:
        if self._process is not None:
            try:
                self._process.terminate()
                log.info("Terminated spotDL process | pid=%d", self._process.pid)
            except ProcessLookupError:
                log.debug("spotDL process already exited")
            except Exception as exc:
                log.warning("Error terminating spotDL process: %s", exc)

    def _build_spotdl_args(
        self,
        base_cmd: list[str],
        urls: list[str],
        output_folder: str,
        *,
        add_download_op: bool = False,
        overwrite: str | None = None,
        scan_for_songs: bool = False,
        extra_args: list[str] | None = None,
    ) -> list[str]:
        return build_spotdl_args(
            base_cmd,
            urls,
            output_folder,
            self._settings,
            add_download_op=add_download_op,
            overwrite=overwrite,
            scan_for_songs=scan_for_songs,
            extra_args=extra_args,
        )

    def _record_completed_track(
        self, track_name: str, output_folder: str, status: str
    ) -> None:
        key = normalize_name(track_name)
        upsert_track_state(
            self._track_state,
            key=key,
            title=track_name,
            status=status,
            source="spotdl-output",
        )
        try:
            matches = [
                track for track in self._last_scan if track.normalized_name == key
            ]
            if matches:
                upsert_track_state(
                    self._track_state,
                    key=key,
                    title=matches[0].title or track_name,
                    artist=matches[0].artist,
                    status=status,
                    path=str(matches[0].path),
                    source="local-scan",
                )
        except Exception:
            pass

    def _record_failed_track(self, text: str, output_folder: str) -> None:
        track_url_m = re.search(
            r"(https?://open\.spotify\.com/track/[A-Za-z0-9]+)", text
        )
        if track_url_m:
            track_url = track_url_m.group(1)
            if track_url not in self._failed_tracks:
                self._failed_tracks.append(track_url)
            upsert_track_state(
                self._track_state,
                key=track_url.lower(),
                title=text,
                status="failed",
                source="spotify-url",
                error=text,
            )
            return
        track_name_m = re.search(r"Failed to download\s+(.+)", text, re.IGNORECASE)
        if track_name_m:
            track_name = track_name_m.group(1).strip()
            key = normalize_name(track_name)
            upsert_track_state(
                self._track_state,
                key=key,
                title=track_name,
                status="failed",
                source="track-name",
                error=text,
            )

    def _refresh_track_state_from_local_scan(self, output_folder: str) -> None:
        self._last_scan = scan_output_folder(output_folder)
        update_paths_from_scan(self._track_state, self._last_scan)
        save_track_state(self._track_state)

    async def _run_spotdl(
        self,
        cmd: list[str],
        url: str = "",
        output_folder: str = "",
    ) -> None:
        downloading_re = re.compile(r"Downloading\s+(.+)", re.IGNORECASE)
        done_re = re.compile(r"(?:Downloaded|✓)\s+(.+)", re.IGNORECASE)
        skipped_re = re.compile(
            r"Skipping\s+(.+)\s+as it is already downloaded", re.IGNORECASE
        )
        error_re = re.compile(
            r"(?:AudioProviderError|Failed to download)", re.IGNORECASE
        )
        found_re = re.compile(r"Found\s+(\d+)\s+songs", re.IGNORECASE)

        downloaded = 0
        skipped = 0
        failed = 0
        total = 0
        pending_done = False
        self._download_start_time = time.monotonic()
        self._track_timestamps.clear()

        log.info("spotDL subprocess starting | cmd=%s", " ".join(cmd))
        try:
            sub_env = dict(os.environ)
            sub_env["PYTHONIOENCODING"] = "utf-8"
            sub_env["PYTHONLEGACYWINDOWSSTDIO"] = "1"
            self._process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=sub_env,
            )
            assert self._process.stdout is not None
            log.info("spotDL process launched | pid=%d", self._process.pid)

            async for raw in self._process.stdout:
                if self._cancel_requested:
                    log.info("Cancel flag detected — breaking read loop")
                    break
                chunk = strip_ansi(raw.decode("utf-8", errors="replace"))
                for text in chunk.splitlines():
                    text = text.strip()
                    if not text:
                        continue
                    m = downloading_re.search(text)
                    if m:
                        self._in_traceback = False
                        pending_done = False
                        track_name = m.group(1).strip()
                        self._track_label.update(track_name)
                        self._log(f"[bold yellow]↓[/] {track_name}")
                        log.info("Downloading track | track=%s", track_name)
                        continue
                    m = skipped_re.search(text)
                    if m:
                        self._in_traceback = False
                        track_name = m.group(1).strip()
                        skipped += 1
                        pending_done = True
                        self._track_timestamps.append(time.monotonic())
                        self._track_label.update(track_name)
                        self._record_completed_track(
                            track_name, output_folder, "skipped"
                        )
                        self._log(f"[dim]⏭  Skipped (duplicate): {track_name}[/]")
                        log.info(
                            "Track skipped (duplicate) | track=%s skipped=%d total=%d",
                            track_name,
                            skipped,
                            total,
                        )
                        continue
                    m = done_re.search(text)
                    if m:
                        self._in_traceback = False
                        track_name = m.group(1).strip()
                        if "%s" in track_name or "song." in track_name:
                            pending_done = True
                            continue
                        downloaded += 1
                        pending_done = True
                        self._track_timestamps.append(time.monotonic())
                        self._track_label.update(track_name)
                        self._record_completed_track(
                            track_name, output_folder, "downloaded"
                        )
                        log.info(
                            "Track downloaded | track=%s downloaded=%d total=%d",
                            track_name,
                            downloaded,
                            total,
                        )
                        continue
                    if pending_done:
                        pending_done = False
                        status_text = self._format_download_status(
                            downloaded + skipped, total
                        )
                        self._status_label.update(status_text)
                        if total > 0:
                            self._progress_bar.progress = min(
                                downloaded + skipped, total
                            )
                    m = found_re.search(text)
                    if m:
                        self._in_traceback = False
                        total = int(m.group(1))
                        self._progress_bar.update(total=total, progress=0)
                        log.info("Playlist metadata received | total_songs=%d", total)
                        continue
                    if "--- Logging error ---" in text or text.startswith("Traceback"):
                        self._in_traceback = True
                        log.debug("Traceback block started | line=%s", text)
                        continue
                    if self._in_traceback:
                        if (
                            downloading_re.search(text)
                            or done_re.search(text)
                            or found_re.search(text)
                            or error_re.search(text)
                        ):
                            self._in_traceback = False
                        else:
                            continue
                    if NOISE_RE.search(text):
                        continue
                    if error_re.search(text):
                        failed += 1
                        self._record_failed_track(text, output_folder)
                        self._log(f"[bold red]✗ {text}[/]")
                        if not self._rate_limit_hint_shown and is_rate_limit_error(
                            text
                        ):
                            self._rate_limit_hint_shown = True
                            self._log(
                                "   [dim]This may be YouTube rate limiting. "
                                "Try setting a cookie file in Settings to reduce failures.[/]"
                            )
                        log.warning(
                            "Download error | track_info=%s failed_count=%d",
                            text,
                            failed,
                        )
                        continue
                    text_lower = text.lower()
                    if "error" in text_lower or "fail" in text_lower:
                        self._log(f"[bold red]{text}[/]")
                        log.warning("spotDL error line | %s", text)
                    else:
                        self._log(text)
            await self._process.wait()
            if pending_done:
                pending_done = False
                status_text = self._format_download_status(downloaded + skipped, total)
                self._status_label.update(status_text)
                if total > 0:
                    self._progress_bar.progress = min(downloaded + skipped, total)
            rc = self._process.returncode
            elapsed_final = time.monotonic() - self._download_start_time
            log.info(
                "spotDL process exited | exit_code=%d downloaded=%d skipped=%d failed=%d total=%d elapsed=%.1fs",
                rc,
                downloaded,
                skipped,
                failed,
                total,
                elapsed_final,
            )
            if rc == 0:
                self._status_label.update(
                    f"Complete! ({self._format_elapsed(elapsed_final)})"
                )
                self._track_label.update("—")
                if total > 0:
                    self._progress_bar.progress = total
                try:
                    out_idx = cmd.index("--output")
                    output_path = cmd[out_idx + 1]
                except (ValueError, IndexError):
                    output_path = "(unknown)"
                summary_parts = []
                if downloaded > 0:
                    summary_parts.append(f"[bold green]{downloaded} new download(s)[/]")
                if skipped > 0:
                    summary_parts.append(f"[bold yellow]{skipped} duplicate skip(s)[/]")
                if failed > 0:
                    summary_parts.append(f"[bold red]{failed} failed[/]")
                summary = ", ".join(summary_parts) if summary_parts else "nothing to do"
                self._log(
                    f"\n[bold green]✓✓ Complete![/] {summary} in [bold]{self._format_elapsed(elapsed_final)}[/]"
                )
                self._log(f"   Files saved to: [bold underline]{output_path}[/]")
                if failed > 0:
                    self._log(
                        "   [dim]Tip: Some tracks failed. "
                        "Try updating: "
                        "[bold cyan]pip install -U spotdl yt-dlp[/][/]"
                    )
                log.info(
                    "Download session complete | downloaded=%d skipped=%d failed=%d output=%s",
                    downloaded,
                    skipped,
                    failed,
                    output_path,
                )
                if url:
                    self._append_history(
                        url, output_folder, downloaded + skipped, "completed"
                    )
                if self._failed_tracks:
                    self._log(
                        f"   [dim]{len(self._failed_tracks)} track(s) failed. Press [bold orange1]Retry Failed[/] to try again.[/]"
                    )
            else:
                self._status_label.update(f"Failed (exit {rc})")
                self._log(f"\n[bold red]✗ spotDL exited with code {rc}[/]")
                if failed > 0:
                    self._log(f"   [dim]{failed} track(s) failed to download[/]")
                log.error(
                    "Download session failed | exit_code=%d downloaded=%d skipped=%d failed=%d",
                    rc,
                    downloaded,
                    skipped,
                    failed,
                )
                if url:
                    self._append_history(
                        url, output_folder, downloaded + skipped, "failed"
                    )
                if self._failed_tracks:
                    self._log(
                        f"   [dim]{len(self._failed_tracks)} track(s) failed. Press [bold orange1]Retry Failed[/] to try again.[/]"
                    )
        except asyncio.CancelledError:
            log.warning(
                "Download cancelled | downloaded=%d skipped=%d failed=%d",
                downloaded,
                skipped,
                failed,
            )
            self._status_label.update("Cancelled")
            if url:
                self._append_history(
                    url, output_folder, downloaded + skipped, "cancelled"
                )
        except Exception as exc:
            log.error("Unexpected error in _run_spotdl | error=%s", exc, exc_info=True)
            self._status_label.update("Error")
            self._log(f"[bold red]✗ Unexpected error: {exc}[/]")
            if url:
                self._append_history(url, output_folder, downloaded + skipped, "error")
        finally:
            self._process = None
            if output_folder and self._preview_section_visible:
                self._refresh_track_state_from_local_scan(output_folder)
            save_track_state(self._track_state)

    def _refresh_preview(self) -> None:
        out = self.query_one("#output-input", Input).value.strip() or "./downloads"
        self._last_scan = scan_output_folder(out)
        self._duplicate_groups = group_duplicates(self._last_scan)
        summary = summarize_scan(self._last_scan, self._duplicate_groups)
        state_summary = summarize_track_state(self._track_state)
        policy = self._settings.get("duplicate_policy", "skip")
        if policy not in {"skip", "metadata"}:
            policy = "skip"
        policy_label = dict(DUPLICATE_POLICY_OPTIONS).get(policy, policy)
        lines = [
            f"Output folder: [bold]{out}[/]",
            f"Local audio files: [bold]{summary['files']}[/]",
            f"Unique tracks: [bold]{summary['unique_tracks']}[/]",
            f"Duplicate groups: [bold yellow]{summary['duplicate_groups']}[/]",
            f"Possible duplicate groups: [bold orange1]{summary['possible_duplicate_groups']}[/]",
            f"Duplicate copies to move: [bold yellow]{summary['duplicate_copies']}[/]",
            f"Possible duplicate copies: [bold orange1]{summary['possible_duplicate_copies']}[/]",
            f"Duplicate policy: [bold]{policy_label}[/]",
            "",
            "Track state:",
            f"  downloaded: [green]{state_summary['downloaded']}[/]",
            f"  skipped: [yellow]{state_summary['skipped']}[/]",
            f"  failed: [red]{state_summary['failed']}[/]",
            f"  quarantined: [orange1]{state_summary['quarantined']}[/]",
        ]
        if self._duplicate_groups:
            lines.extend(["", "[bold]Duplicate groups:[/]"])
            for group in self._duplicate_groups:
                lines.extend(group.to_log_lines())
                lines.append("")
        else:
            lines.extend(["", "[green]No duplicate groups detected.[/]"])
        if self._preview_widget is not None:
            self._preview_widget.clear()
            for line in lines:
                self._preview_widget.write(line)
        return summary

    def _show_preview_section(self, visible: bool) -> None:
        self._preview_section_visible = visible
        section = self.query_one("#preview-section")
        if visible:
            section.add_class("visible")
        else:
            section.remove_class("visible")

    @on(Button.Pressed, "#preview-btn")
    async def on_preview(self) -> None:
        if self._preview_section_visible:
            self._show_preview_section(False)
            return
        self._log("[bold cyan]🔎[/] Scanning local files for duplicates…")
        summary = self._refresh_preview()
        self._show_preview_section(True)
        self._log(
            f"[bold cyan]Preview:[/] {summary['files']} local audio file(s), "
            f"{summary['duplicate_groups']} safe duplicate group(s), "
            f"{summary['possible_duplicate_groups']} possible duplicate group(s), "
            f"{summary['duplicate_copies']} duplicate copy/copies to move."
        )

    @on(Button.Pressed, "#duplicates-btn")
    def on_duplicates(self) -> None:
        summary = self._refresh_preview()
        if not summary["duplicate_groups"]:
            self._log("[dim]No duplicate groups found.[/]")
        self.push_screen(
            DuplicateManagerScreen(self._duplicate_groups),
            self._handle_duplicate_manager_result,
        )

    def _handle_duplicate_manager_result(self, result: object) -> None:
        if result == "move":
            self._move_duplicate_copies()

    def _move_duplicate_copies(self) -> None:
        out = self.query_one("#output-input", Input).value.strip() or "./downloads"
        self._last_scan = scan_output_folder(out)
        self._duplicate_groups = group_duplicates(self._last_scan)
        self._duplicate_groups = [
            group
            for group in self._duplicate_groups
            if group.safe_to_move and group.copies
        ]
        if not self._duplicate_groups:
            self._log("[dim]No safe duplicate copies to move.[/]")
            return
        count, destination = quarantine_duplicate_copies(self._duplicate_groups, out)
        for group in self._duplicate_groups:
            for track in group.copies:
                if not track.path.exists():
                    continue
                upsert_track_state(
                    self._track_state,
                    key=track.normalized_name,
                    title=track.title,
                    artist=track.artist,
                    status="quarantined",
                    path=str(track.path),
                    source="duplicate-cleaner",
                )
        save_track_state(self._track_state)
        self._refresh_preview()
        self._show_preview_section(True)
        self._log(f"[bold orange1]{format_quarantine_summary(count, destination)}[/]")

    @on(Button.Pressed, "#clean-btn")
    def on_clean_duplicates(self) -> None:
        now = time.monotonic()
        if now > self._confirm_clean_until:
            self._confirm_clean_until = now + 5
            self._log(
                "[bold yellow]Press [bold]Clean[/] again within 5 seconds to move duplicate copies to ./downloads/duplicates/.[/]"
            )
            return
        self._confirm_clean_until = 0.0
        self._move_duplicate_copies()

    @on(Button.Pressed, "#download-btn")
    async def on_download(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        if not url:
            self._log(_SPOTDL_URL_ERROR)
            return
        if not self._is_valid_url(url):
            self._log(_SPOTDL_URL_ERROR)
            log.warning("Invalid URL entered | url=%s", url)
            return
        out = self.query_one("#output-input", Input).value.strip() or "./downloads"
        spotdl_cmd = find_spotdl()
        if spotdl_cmd is None:
            return
        if not await validate_spotdl(spotdl_cmd):
            self._log(
                "[bold red]✗[/] [bold]spotDL[/] is not installed.\n"
                "  Install it with:  [bold cyan]pip install spotdl[/]\n"
                "  Then run:          [bold cyan]spotdl --download-ffmpeg[/]"
            )
            return
        if not await ensure_deno(spotdl_cmd):
            return
        os.makedirs(out, exist_ok=True)
        policy = self._settings.get("duplicate_policy", "skip")
        if policy not in {"skip", "metadata"}:
            policy = "skip"
        self._lock_ui()
        self._failed_tracks.clear()
        self._status_label.update("Downloading…")
        self._progress_bar.update(total=100, progress=0)
        self._log_widget.clear()
        self._log(f"[bold green]▶[/] Starting download: [bold]{url}[/]")
        self._cancel_requested = False
        self._rate_limit_hint_shown = False
        self._check_cookie_file()
        scan_for_songs = True
        overwrite = "skip" if policy == "skip" else "metadata"
        cmd = self._build_spotdl_args(
            spotdl_cmd,
            [url],
            out,
            overwrite=overwrite,
            scan_for_songs=scan_for_songs,
        )
        log.info("Running spotDL | cmd=%s url=%s", " ".join(cmd), url)
        await self._run_spotdl(cmd, url=url, output_folder=out)
        self._unlock_ui()
        log.info("Download handler finished | url=%s", url)

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self) -> None:
        if self._process is not None:
            self._cancel_requested = True
            self._kill_process()
            self._status_label.update("Cancelled")
            self._log("[bold red]⏹[/] Download cancelled by user")
            log.info("Download cancelled by user")
            self._unlock_ui()
        else:
            self._log("[dim]Nothing to cancel.[/]")

    @on(Button.Pressed, "#fresh-btn")
    async def on_fresh(self) -> None:
        url = self.query_one("#url-input", Input).value.strip()
        if not url:
            self._log(_SPOTDL_URL_ERROR)
            return
        if not self._is_valid_url(url):
            self._log(_SPOTDL_URL_ERROR)
            log.warning("Invalid URL entered for fresh download | url=%s", url)
            return
        out = self.query_one("#output-input", Input).value.strip() or "./downloads"
        spotdl_cmd = find_spotdl()
        if spotdl_cmd is None:
            return
        if not await validate_spotdl(spotdl_cmd):
            self._log(
                "[bold red]✗[/] [bold]spotDL[/] is not installed.\n"
                "  Install it with:  [bold cyan]pip install spotdl[/]\n"
                "  Then run:          [bold cyan]spotdl --download-ffmpeg[/]"
            )
            return
        if not await ensure_deno(spotdl_cmd):
            return
        os.makedirs(out, exist_ok=True)
        self._lock_ui()
        self._failed_tracks.clear()
        self._status_label.update("Fresh download…")
        self._progress_bar.update(total=100, progress=0)
        self._log_widget.clear()
        self._log(
            f"[bold yellow]⟳[/] Fresh download (overwriting existing): [bold]{url}[/]"
        )
        self._cancel_requested = False
        self._rate_limit_hint_shown = False
        self._check_cookie_file()
        cmd = self._build_spotdl_args(
            spotdl_cmd, [url], out, overwrite="force", scan_for_songs=True
        )
        log.info("Running spotDL (fresh) | cmd=%s url=%s", " ".join(cmd), url)
        await self._run_spotdl(cmd, url=url, output_folder=out)
        self._unlock_ui()
        log.info("Fresh download handler finished | url=%s", url)

    @on(Button.Pressed, "#history-btn")
    def on_history_toggle(self) -> None:
        self._history_visible = not self._history_visible
        section = self.query_one("#history-section")
        if self._history_visible:
            section.add_class("visible")
        else:
            section.remove_class("visible")
        log.debug("History panel toggled | visible=%s", self._history_visible)

    @on(Button.Pressed, "#clear-history-btn")
    def on_clear_history(self) -> None:
        self._history.clear()
        self._save_history()
        self._render_history()
        if self._log_widget is not None:
            self._log_widget.clear()

    @on(Button.Pressed, "#retry-btn")
    async def on_retry_failed(self) -> None:
        if not self._failed_tracks:
            self._log("[dim]No failed tracks to retry.[/]")
            return
        out = self.query_one("#output-input", Input).value.strip() or "./downloads"
        spotdl_cmd = find_spotdl()
        if spotdl_cmd is None:
            return
        if not await validate_spotdl(spotdl_cmd):
            self._log(
                "[bold red]✗[/] [bold]spotDL[/] is not installed.\n"
                "  Install it with:  [bold cyan]pip install spotdl[/]\n"
                "  Then run:          [bold cyan]spotdl --download-ffmpeg[/]"
            )
            return
        if not await ensure_deno(spotdl_cmd):
            return
        os.makedirs(out, exist_ok=True)
        track_urls = list(self._failed_tracks)
        self._failed_tracks.clear()
        self.query_one("#retry-btn", Button).disabled = True
        self._lock_ui()
        self._status_label.update(f"Retrying {len(track_urls)} track(s)…")
        self._progress_bar.update(total=len(track_urls), progress=0)
        self._log_widget.clear()
        self._log(
            f"[bold orange1]🔄[/] Retrying [bold]{len(track_urls)}[/] failed track(s)…"
        )
        self._cancel_requested = False
        self._rate_limit_hint_shown = False
        self._check_cookie_file()
        cmd = self._build_spotdl_args(
            spotdl_cmd,
            track_urls,
            out,
            add_download_op=True,
            overwrite="skip",
            scan_for_songs=True,
        )
        log.info("Running spotDL (retry) | cmd=%s", " ".join(cmd))
        await self._run_spotdl(cmd, url="", output_folder=out)
        self._unlock_ui()
        log.info(
            "Retry handler finished | remaining_failed=%d", len(self._failed_tracks)
        )

    @on(Button.Pressed, "#quit-btn")
    def on_quit(self) -> None:
        log.info("Quit requested")
        self._cancel_requested = True
        self._kill_process()
        self.exit()

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"

    def _format_download_status(self, done: int, total: int) -> str:
        parts = [f"{done} processed"]
        elapsed = time.monotonic() - self._download_start_time
        if done >= 2 and elapsed > 0:
            rate = done / elapsed
            rate_per_min = rate * 60
            parts.append(f"{rate_per_min:.1f} tracks/min")
            if total > 0 and done < total:
                remaining = total - done
                eta_secs = remaining / rate
                if eta_secs < 60:
                    parts.append(f"~{int(eta_secs)}s left")
                elif eta_secs < 3600:
                    parts.append(f"~{int(eta_secs // 60)}m {int(eta_secs % 60)}s left")
                else:
                    h = int(eta_secs // 3600)
                    m = int((eta_secs % 3600) // 60)
                    parts.append(f"~{h}h {m}m left")
        return " · ".join(parts)

    def _log(self, message: str) -> None:
        if self._log_widget is not None:
            at_bottom = self._log_widget.is_vertical_scroll_end
            self._log_widget.write(message)
            if at_bottom:
                self._log_widget.scroll_end(animate=False)


def main() -> None:
    _setup_logger()
    log.info("=" * 60)
    log.info("Spotify Playlist Downloader starting")
    log.info("Python %s | %s", sys.version.split()[0], sys.platform)
    log.info("Log file: %s", LOG_FILE)
    log.info("Track state file: %s", STATE_FILE)
    log.info("=" * 60)
    app = SpotifyDownloader()
    app.run()
    log.info("Spotify Playlist Downloader shut down")


if __name__ == "__main__":
    main()
