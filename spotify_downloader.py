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

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Button, Input, Label, ProgressBar, RichLog, Select


HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".spotdl", "download_history.json")
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".spotdl", "settings.json")
LOG_DIR = os.path.join(os.path.expanduser("~"), ".spotdl")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

DEFAULT_SETTINGS: dict[str, str] = {
    "format": "mp3",
    "bitrate": "auto",
    "audio_provider": "youtube-music",
    "proxy": "",
    "cookie_file": "",
    "browser": "auto",
}
BROWSER_OPTIONS: list[tuple[str, str]] = [
    ("Auto (try all)", "auto"),
    ("Chrome", "chrome"),
    ("Firefox", "firefox"),
    ("Edge", "edge"),
    ("Brave", "brave"),
    ("Vivaldi", "vivaldi"),
]
# Browsers to try in order when "auto" is selected.  Firefox first because
# it doesn't lock its cookie database on Windows (unlike Chromium browsers).
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
# Patterns that match spotDL's internal logging noise (Python logging traceback)
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
    r")",
    re.IGNORECASE,
)

_SPOTDL_URL_ERROR = (
    "[bold red]✗[/] Invalid URL. Must start with "
    "[cyan]https://open.spotify.com/playlist/[/] or [cyan]spotify:playlist:[/]"
)


def _setup_logger() -> logging.Logger:
    """Configure and return the application logger."""
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("spotify_downloader")
    logger.setLevel(logging.DEBUG)

    # Avoid duplicate handlers on re-import
    if logger.handlers:
        return logger

    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


log = logging.getLogger("spotify_downloader")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


class SpotifyDownloader(App):
    """A TUI app that downloads Spotify playlists using spotDL."""

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

    #button-row {
        height: auto;
        margin: 1 0 0 0;
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

    #cancel-btn {
        background: #c0392b;
        color: #ffffff;
        text-style: bold;
        min-width: 20;
        margin: 0 0 0 1;
    }

    #cancel-btn:hover {
        background: #e74c3c;
    }

    #cancel-btn:disabled {
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

    #history-log {
        height: auto;
        max-height: 10;
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
        width: 16;
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
        self._cancel_requested: bool = False
        self._in_traceback: bool = False
        self._failed_tracks: list[str] = []  # Spotify track URLs that failed
        self._download_start_time: float = 0.0
        self._track_timestamps: list[float] = []  # timestamps when tracks completed
        self._rate_limit_hint_shown: bool = False
        self._history_visible: bool = False
        self._settings_visible: bool = False
        self._settings_loading: bool = (
            True  # guard against saving during _apply_settings_to_ui
        )
        self._settings: dict[str, str] = self._load_settings()
        self._history: list[dict] = self._load_history()
        log.info(
            "App initialized | history=%d settings=%s",
            len(self._history),
            self._settings,
        )

    # ── Lifecycle ──────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Container(id="main-container"):
            # Header
            with Container(id="header-section"):
                yield Label("🎵  Spotify Playlist Downloader", id="app-title")
                yield Label(
                    "Paste a public playlist URL and press Download", id="app-subtitle"
                )

            # Inputs
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

                with Horizontal(id="button-row"):
                    yield Button("▶  Download", id="download-btn", variant="success")
                    yield Button("🔄 Retry Failed", id="retry-btn", disabled=True)
                    yield Button("⟳  Fresh", id="fresh-btn")
                    yield Button("📜 History", id="history-btn")
                    yield Button("⚙ Settings", id="settings-btn")
                    yield Button(
                        "⏹  Cancel", id="cancel-btn", variant="error", disabled=True
                    )
                    yield Button("✕  Quit", id="quit-btn")

            # Settings panel (hidden by default)
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

            # Download history (hidden by default)
            with Container(id="history-section"):
                yield Label("📜 Download History", id="history-header")
                yield RichLog(
                    id="history-log",
                    highlight=True,
                    markup=True,
                    max_lines=50,
                    auto_scroll=False,
                )

            # Status / progress
            with Container(id="status-section"):
                yield ProgressBar(total=100, id="progress-bar", show_percentage=True)
                with Horizontal(classes="stat-row"):
                    yield Label("Status:", classes="stat-label")
                    yield Label("Ready", id="status-value", classes="stat-value")
                with Horizontal(classes="stat-row"):
                    yield Label("Track:", classes="stat-label")
                    yield Label("—", id="track-value", classes="stat-value")

            # Log output
            yield RichLog(
                id="log", highlight=True, markup=True, max_lines=200, auto_scroll=False
            )

    def on_mount(self) -> None:
        """Cache widget references and show a welcome message."""
        log.info("App mounted — UI widgets ready")
        self._progress_bar = self.query_one("#progress-bar", ProgressBar)
        self._status_label = self.query_one("#status-value", Label)
        self._track_label = self.query_one("#track-value", Label)
        self._log_widget = self.query_one("#log", RichLog)
        self._history_widget = self.query_one("#history-log", RichLog)

        # Apply saved settings to UI widgets
        self._apply_settings_to_ui()

        self._log_widget.write("[bold green]✓[/] Ready!")
        self._log_widget.write(
            "[dim]Enter a Spotify playlist URL above and press Download to begin.[/]"
        )
        self._render_history()
        self.query_one("#url-input", Input).focus()

        # Check for dependency updates in the background (non-blocking)
        self.run_worker(self._check_dependency_updates(), exclusive=True)

    # ── Settings persistence ───────────────────────────────────────

    @staticmethod
    def _load_settings() -> dict[str, str]:
        """Load settings from disk, falling back to defaults."""
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
        """Persist current settings to disk."""
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
        """Sync saved settings into the UI widgets (called on mount)."""
        self._settings_loading = True
        try:
            fmt = self._settings.get("format", "mp3")
            bitrate = self._settings.get("bitrate", "auto")
            proxy = self._settings.get("proxy", "")
            cookie_file = self._settings.get("cookie_file", "")

            self.query_one("#format-select", Select).value = fmt
            self.query_one("#bitrate-select", Select).value = bitrate
            audio_provider = self._settings.get("audio_provider", "youtube-music")
            self.query_one("#audio-provider-select", Select).value = audio_provider
            self.query_one("#proxy-input", Input).value = proxy
            self.query_one("#cookie-file-input", Input).value = cookie_file
            browser = self._settings.get("browser", "chrome")
            self.query_one("#browser-select", Select).value = browser

            self._update_settings_status()
            log.debug(
                "Settings applied to UI | format=%s bitrate=%s proxy=%s",
                fmt,
                bitrate,
                bool(proxy),
            )
        finally:
            self._settings_loading = False

    def _update_settings_status(self) -> None:
        """Update the settings status label with current config."""
        fmt = self._settings.get("format", "mp3")
        bitrate = self._settings.get("bitrate", "auto")
        proxy = self._settings.get("proxy", "")
        cookie_file = self._settings.get("cookie_file", "")
        audio_provider = self._settings.get("audio_provider", "youtube-music")
        provider_label = audio_provider.replace("-", " ").title()
        parts = [
            f"Format: {fmt.upper()}",
            f"Bitrate: {bitrate}",
            f"Source: {provider_label}",
        ]
        if proxy:
            parts.append(f"Proxy: {proxy}")
        browser = self._settings.get("browser", "auto")
        browser_label = "Auto" if browser == "auto" else browser.title()
        if cookie_file:
            parts.append(f"Cookies: {browser_label} → {os.path.basename(cookie_file)}")
        self.query_one("#settings-status", Label).update(" · ".join(parts))

    # ── Settings toggle ────────────────────────────────────────────

    @on(Button.Pressed, "#settings-btn")
    def on_settings_toggle(self) -> None:
        """Toggle the settings panel."""
        self._settings_visible = not self._settings_visible
        section = self.query_one("#settings-section")
        if self._settings_visible:
            section.add_class("visible")
        else:
            section.remove_class("visible")
        log.debug("Settings panel toggled | visible=%s", self._settings_visible)

    @on(Select.Changed, "#format-select")
    def on_format_changed(self, event: Select.Changed) -> None:
        """Handle output format selection change."""
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "mp3"
        if self._settings.get("format") == value:
            return  # no change (e.g. async event after mount)
        self._settings["format"] = value
        self._save_settings()
        self._update_settings_status()
        log.info("Setting changed | format=%s", value)

    @on(Select.Changed, "#bitrate-select")
    def on_bitrate_changed(self, event: Select.Changed) -> None:
        """Handle bitrate selection change."""
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "auto"
        if self._settings.get("bitrate") == value:
            return  # no change (e.g. async event after mount)
        self._settings["bitrate"] = value
        self._save_settings()
        self._update_settings_status()
        log.info("Setting changed | bitrate=%s", value)

    @on(Select.Changed, "#audio-provider-select")
    def on_audio_provider_changed(self, event: Select.Changed) -> None:
        """Handle audio provider selection change."""
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "youtube-music"
        if self._settings.get("audio_provider") == value:
            return
        self._settings["audio_provider"] = value
        self._save_settings()
        self._update_settings_status()
        log.info("Setting changed | audio_provider=%s", value)

    @on(Input.Submitted, "#proxy-input")
    def on_proxy_submitted(self, event: Input.Submitted) -> None:
        """Handle proxy input submission (Enter key)."""
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
        log.info("Setting changed | proxy=%s", bool(proxy))

    @on(Input.Submitted, "#cookie-file-input")
    def on_cookie_file_submitted(self, event: Input.Submitted) -> None:
        """Handle cookie file input submission (Enter key)."""
        cookie_file = event.value.strip()
        if cookie_file and not os.path.isfile(cookie_file):
            self._log(
                f"[bold yellow]⚠[/] Cookie file not found: [bold]{cookie_file}[/]"
            )
            log.warning("Cookie file not found | path=%s", cookie_file)
        self._settings["cookie_file"] = cookie_file
        self._save_settings()
        self._update_settings_status()
        log.info("Setting changed | cookie_file=%s", bool(cookie_file))

    @on(Select.Changed, "#browser-select")
    def on_browser_changed(self, event: Select.Changed) -> None:
        """Handle browser selection change."""
        if self._settings_loading:
            return
        value = event.value if event.value is not Select.BLANK else "auto"
        if self._settings.get("browser") == value:
            return
        self._settings["browser"] = value
        self._save_settings()
        self._update_settings_status()
        log.info("Setting changed | browser=%s", value)

    async def _extract_from_browser(
        self,
        ytdlp: str,
        browser: str,
        cookie_path: str,
    ) -> tuple[bool, str]:
        """Try to extract cookies from a single browser.  Returns (success, output)."""
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
        """Extract cookies from the selected browser using yt-dlp.

        When the browser setting is "auto", tries Firefox first (doesn't lock
        its cookie DB on Windows) then falls back through other browsers.
        """
        chosen_browser = self._settings.get("browser", "auto")
        cookie_dir = os.path.join(os.path.expanduser("~"), ".spotdl")
        cookie_path = os.path.join(cookie_dir, "cookies.txt")

        # Find yt-dlp
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

            # Determine which browsers to try
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
                    return  # success — stop trying other browsers

                # Check WHY it failed — if it's the "database locked" error,
                # keep trying other browsers silently.  Only report at the end.
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
                    # Non-locked failure on an explicit browser choice — stop
                    break

            # All browsers failed — show a helpful summary
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
        """Display a helpful error message after all extraction attempts failed."""
        output_lower = output.lower() if output else ""
        is_locked = (
            "could not copy" in output_lower or "permission denied" in output_lower
        )

        if is_locked:
            # Database-locked error
            tried_names = ", ".join(b.title() for b in browsers_tried)
            self._log(
                f"[bold red]✗[/] Cookie extraction failed — all browsers lock their database while running.\n"
                f"   [dim]Tried: {tried_names}[/]\n\n"
                "   [bold]Workarounds:[/]\n"
                "   1. Close [bold]all browser windows[/] and try again\n"
                "   2. Install [bold]Firefox[/] (doesn't lock its cookie DB) — then select it in Settings\n"
                "   3. Use a browser extension to export cookies manually:\n"
                "      [bold cyan]Get cookies.txt LOCALLY[/] extension for Chrome/Edge\n"
                "      Export → save as cookies.txt → paste path in Cookie file field\n"
                "   More info: [bold cyan]https://github.com/yt-dlp/yt-dlp/issues/7271[/][/]"
            )
        else:
            self._log(
                f"[bold red]✗[/] Cookie extraction failed.\n"
                f"   [dim]{output[:200] if output else 'No output'}[/]"
            )
        log.error(
            "Cookie extraction failed | browsers=%s output=%s",
            browsers_tried,
            output[:200],
        )

    # ── Dependency version checks ─────────────────────────────────

    _CHECKED_PACKAGES: list[tuple[str, str]] = [
        ("spotdl", "spotdl"),
        ("yt-dlp", "yt-dlp"),
    ]

    @staticmethod
    def _get_installed_version(package_name: str) -> str | None:
        """Return the installed version of *package_name*, or None."""
        try:
            return importlib.metadata.version(package_name)
        except importlib.metadata.PackageNotFoundError:
            return None

    @staticmethod
    async def _get_latest_version(package_name: str) -> str | None:
        """Query PyPI JSON API for the latest version of *package_name*."""
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
        """Return True if version string *a* is strictly newer than *b*.

        Falls back to a simple tuple-of-ints comparison when the segments
        are all numeric; otherwise uses string comparison.
        """
        try:
            # packaging.version.Version is the gold standard, but it adds a
            # dependency.  Try it first, fall back to tuple comparison.
            from packaging.version import Version

            return Version(a) > Version(b)
        except Exception:
            pass

        # Fallback: split on '.' and compare segments as integers where possible
        def _parse(v: str) -> list[int]:
            parts: list[int] = []
            for seg in v.split("."):
                try:
                    parts.append(int(re.sub(r"[^0-9]", "", seg) or "0"))
                except ValueError:
                    parts.append(0)
            return parts

        return _parse(a) > _parse(b)

    async def _check_dependency_updates(self) -> None:
        """Check for newer versions of key dependencies and notify the user."""
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

    # ── Helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check whether *url* is a supported Spotify playlist URL."""
        return url.startswith("https://open.spotify.com/playlist/") or url.startswith(
            "spotify:playlist:"
        )

    @staticmethod
    def _is_valid_proxy(proxy: str) -> bool:
        """Check whether *proxy* looks like a valid proxy URL."""
        return proxy.startswith(("http://", "https://", "socks4://", "socks5://"))

    def _check_cookie_file(self) -> None:
        """Warn if cookie file is configured but missing."""
        cookie_file = self._settings.get("cookie_file", "").strip()
        if cookie_file and not os.path.isfile(cookie_file):
            self._log(
                f"[bold yellow]⚠[/] Cookie file not found: [bold]{cookie_file}[/]\n"
                "   [dim]Downloads may fail due to YouTube rate limiting. "
                "Update the path in Settings or re-export cookies from your browser.[/]"
            )
            log.warning("Cookie file missing | path=%s", cookie_file)

    # ── Download history ───────────────────────────────────────────

    @staticmethod
    def _load_history() -> list[dict]:
        """Load download history from disk."""
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
        """Persist download history to disk."""
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
        """Record a completed download session."""
        entry = {
            "url": url,
            "output_folder": output_folder,
            "tracks_downloaded": tracks_downloaded,
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._history.insert(0, entry)  # newest first
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
        """Render the history panel content."""
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

    @staticmethod
    def _is_rate_limit_error(error_text: str) -> bool:
        """Detect YouTube rate-limiting / bot-detection error messages."""
        rate_limit_patterns = (
            "sign in to confirm",
            "sign in to verify",
            "confirm you're not a bot",
            "confirm you are not a bot",
            "http error 403",
            "http error 429",
            "too many requests",
            "please log in",
        )
        text_lower = error_text.lower()
        return any(pat in text_lower for pat in rate_limit_patterns)

    async def _find_spotdl(self) -> list[str] | None:
        """Locate the spotDL binary. Returns command list or None on failure."""
        spotdl = shutil.which("spotdl") or shutil.which("spotdl.exe")
        log.debug("spotDL lookup | which=%s", spotdl)
        fallback = None
        if not spotdl:
            fallback = [sys.executable, "-m", "spotdl"]
            log.debug(
                "spotDL not on PATH, trying fallback | cmd=%s", " ".join(fallback)
            )
            result = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "spotdl",
                "--help",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            rc = await result.wait()
            if rc != 0:
                log.error(
                    "spotDL not installed (fallback check failed) | exit_code=%d", rc
                )
                self._log(
                    "[bold red]✗[/] [bold]spotDL[/] is not installed.\n"
                    "  Install it with:  [bold cyan]pip install spotdl[/]\n"
                    "  Then run:          [bold cyan]spotdl --download-ffmpeg[/]"
                )
                return None
            log.info("spotDL found via fallback | cmd=%s", " ".join(fallback))
        else:
            log.info("spotDL found on PATH | path=%s", spotdl)
        return fallback or [spotdl]

    async def _ensure_deno(self, spotdl_cmd: list[str]) -> bool:
        """Check if Deno is available; if not, try to install it via spotDL."""
        if shutil.which("deno") or shutil.which("deno.exe"):
            log.debug("Deno found on PATH")
            return True

        spotdl_home = os.path.join(os.path.expanduser("~"), ".spotdl")
        # Check common bundled names: deno (Linux/Mac) and deno.exe (Windows)
        for name in ("deno", "deno.exe"):
            if os.path.isfile(os.path.join(spotdl_home, name)):
                log.debug(
                    "Deno found bundled | path=%s", os.path.join(spotdl_home, name)
                )
                return True

        log.info("Deno not found — attempting install via spotDL")
        self._log("[bold yellow]⟳[/] Deno not found — installing for YouTube support …")
        try:
            proc = await asyncio.create_subprocess_exec(
                *spotdl_cmd,
                "--download-deno",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
            )
            stdout, _ = await proc.communicate()
            output = stdout.decode("utf-8", errors="replace").strip()
            if proc.returncode == 0:
                log.info("Deno installed successfully | output=%s", output)
                self._log("[bold green]✓[/] Deno installed successfully")
                return True
            log.error(
                "Deno install failed | exit_code=%d output=%s", proc.returncode, output
            )
            self._log(
                "[bold red]✗[/] Could not install Deno. Some downloads may fail.\n"
                "  Install manually: [bold cyan]spotdl --download-deno[/]"
            )
            return True
        except Exception as exc:
            log.error("Deno install exception | error=%s", exc, exc_info=True)
            self._log(f"[bold red]✗[/] Deno install failed: {exc}")
            return True

    # ── UI helpers ───────────────────────────────────────────────

    def _lock_ui(self) -> None:
        """Disable interactive buttons while a download is running."""
        self.query_one("#download-btn", Button).disabled = True
        self.query_one("#retry-btn", Button).disabled = True
        self.query_one("#fresh-btn", Button).disabled = True
        self.query_one("#cancel-btn", Button).disabled = False

    def _unlock_ui(self) -> None:
        """Re-enable interactive buttons after a download finishes."""
        self.query_one("#download-btn", Button).disabled = False
        self.query_one("#fresh-btn", Button).disabled = False
        self.query_one("#cancel-btn", Button).disabled = True
        # Only re-enable retry if there are failed tracks
        self.query_one("#retry-btn", Button).disabled = not self._failed_tracks

    def _kill_process(self) -> None:
        """Terminate the running spotDL subprocess, if any."""
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
    ) -> list[str]:
        """Build the full spotDL command line from user settings."""
        cmd = list(base_cmd)

        # Only add explicit "download" operation for multi-URL retry commands.
        # For single-URL downloads, omitting the operation avoids argparse
        # confusion where flags between "download" and the URL cause
        # "unrecognized arguments" errors.
        if add_download_op:
            cmd.append("download")

        fmt = self._settings.get("format", "mp3")
        bitrate = self._settings.get("bitrate", "auto")
        audio_provider = self._settings.get("audio_provider", "youtube-music")
        proxy = self._settings.get("proxy", "").strip()
        cookie_file = self._settings.get("cookie_file", "").strip()

        cmd.extend(["--format", fmt])
        if bitrate and bitrate != "auto":
            cmd.extend(["--bitrate", bitrate])
        cmd.extend(["--audio", audio_provider])
        if proxy:
            cmd.extend(["--proxy", proxy])
        if cookie_file and os.path.isfile(cookie_file):
            cmd.extend(["--cookie-file", cookie_file])
        cmd.extend(["--output", output_folder])

        # Append the URL(s) at the end
        cmd.extend(urls)
        return cmd

    # ── Core download logic ────────────────────────────────────────

    async def _run_spotdl(
        self,
        cmd: list[str],
        url: str = "",
        output_folder: str = "",
    ) -> None:
        """Execute spotDL as a subprocess, parsing output for progress."""
        downloading_re = re.compile(r"Downloading\s+(.+)", re.IGNORECASE)
        done_re = re.compile(r"(?:Downloaded|✓)\s+(.+)", re.IGNORECASE)
        skipped_re = re.compile(
            r"Skipping\s+(.+)\s+as it is already downloaded", re.IGNORECASE
        )
        error_re = re.compile(
            r"(?:AudioProviderError|Failed to download)", re.IGNORECASE
        )
        # Count total songs from "Found N songs" line in spotDL output
        found_re = re.compile(r"Found\s+(\d+)\s+songs", re.IGNORECASE)

        done = 0
        failed = 0
        total = 0
        pending_done = False  # True after "Downloaded" line, waiting for URL line
        self._download_start_time = time.monotonic()
        self._track_timestamps.clear()

        log.info("spotDL subprocess starting | cmd=%s", " ".join(cmd))

        try:
            # Force UTF-8 in subprocess to avoid GBK encoding errors on Windows
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
                        done += 1
                        pending_done = True
                        self._track_timestamps.append(time.monotonic())
                        self._track_label.update(track_name)
                        self._log(f"[dim]⏭  Skipped (duplicate): {track_name}[/]")
                        log.info(
                            "Track skipped (duplicate) | track=%s done=%d total=%d",
                            track_name,
                            done,
                            total,
                        )
                        continue

                    m = done_re.search(text)
                    if m:
                        self._in_traceback = False
                        track_name = m.group(1).strip()
                        # If the track name contains raw format strings (%s, variable
                        # names) it means spotDL hit a GBK encoding error and the
                        # logger fell back to printing the format string.  Suppress
                        # these corrupted entries so they don't pollute the TUI.
                        if "%s" in track_name or "song." in track_name:
                            pending_done = True  # still count it, skip display
                            continue
                        done += 1
                        pending_done = True
                        self._track_timestamps.append(time.monotonic())
                        self._track_label.update(track_name)
                        log.info(
                            "Track downloaded | track=%s done=%d total=%d",
                            track_name,
                            done,
                            total,
                        )
                        continue

                    # After a "Downloaded" line, the next non-empty line is
                    # usually the YouTube URL.  Update the status / progress
                    # bar now that we've seen both lines.
                    if pending_done:
                        pending_done = False
                        status_text = self._format_download_status(done, total)
                        self._status_label.update(status_text)
                        if total > 0:
                            self._progress_bar.progress = min(done, total)

                    m = found_re.search(text)
                    if m:
                        self._in_traceback = False
                        total = int(m.group(1))
                        self._progress_bar.update(total=total, progress=0)
                        log.info("Playlist metadata received | total_songs=%d", total)
                        continue

                    # --- Traceback block state machine ---
                    # spotDL emits "--- Logging error ---" followed by a full
                    # Python traceback whenever Rich can't encode a character
                    # (e.g. GBK on Windows).  Instead of trying to match every
                    # individual traceback line, we detect the block start/end
                    # and skip all lines inside it.
                    if "--- Logging error ---" in text or text.startswith("Traceback"):
                        self._in_traceback = True
                        log.debug("Traceback block started | line=%s", text)
                        continue
                    if self._in_traceback:
                        # End of traceback: real spotDL output lines
                        if (
                            downloading_re.search(text)
                            or done_re.search(text)
                            or found_re.search(text)
                            or error_re.search(text)
                        ):
                            self._in_traceback = False
                            # Fall through to normal processing below
                        else:
                            continue

                    if NOISE_RE.search(text):
                        continue

                    if error_re.search(text):
                        failed += 1
                        # Extract Spotify track URL from error line for retry
                        track_url_m = re.search(
                            r"(https?://open\.spotify\.com/track/[A-Za-z0-9]+)",
                            text,
                        )
                        if track_url_m:
                            track_url = track_url_m.group(1)
                            if track_url not in self._failed_tracks:
                                self._failed_tracks.append(track_url)
                        self._log(f"[bold red]✗ {text}[/]")
                        # Detect rate-limiting errors and suggest cookie file (once)
                        if (
                            not self._rate_limit_hint_shown
                            and self._is_rate_limit_error(text)
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

            # Flush any pending progress update (e.g. last track had no URL line)
            if pending_done:
                pending_done = False
                status_text = self._format_download_status(done, total)
                self._status_label.update(status_text)
                if total > 0:
                    self._progress_bar.progress = min(done, total)

            rc = self._process.returncode
            elapsed_final = time.monotonic() - self._download_start_time
            log.info(
                "spotDL process exited | exit_code=%d done=%d failed=%d total=%d elapsed=%.1fs",
                rc,
                done,
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
                if done > 0:
                    summary_parts.append(f"[bold green]{done} new download(s)[/]")
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
                    "Download session complete | done=%d failed=%d output=%s",
                    done,
                    failed,
                    output_path,
                )
                if url:
                    self._append_history(url, output_folder, done, "completed")
                if self._failed_tracks:
                    self._log(
                        f"   [dim]{len(self._failed_tracks)} track(s) failed. "
                        "Press [bold orange1]Retry Failed[/] to try again.[/]"
                    )
            else:
                self._status_label.update(f"Failed (exit {rc})")
                self._log(f"\n[bold red]✗ spotDL exited with code {rc}[/]")
                if failed > 0:
                    self._log(f"   [dim]{failed} track(s) failed to download[/]")
                log.error(
                    "Download session failed | exit_code=%d done=%d failed=%d",
                    rc,
                    done,
                    failed,
                )
                if url:
                    self._append_history(url, output_folder, done, "failed")
                if self._failed_tracks:
                    self._log(
                        f"   [dim]{len(self._failed_tracks)} track(s) failed. "
                        "Press [bold orange1]Retry Failed[/] to try again.[/]"
                    )

        except asyncio.CancelledError:
            log.warning("Download cancelled | done=%d failed=%d", done, failed)
            self._status_label.update("Cancelled")
            if url:
                self._append_history(url, output_folder, done, "cancelled")
        except Exception as exc:
            log.error(
                "Unexpected error in _run_spotdl | error=%s",
                exc,
                exc_info=True,
            )
            self._status_label.update("Error")
            self._log(f"[bold red]✗ Unexpected error: {exc}[/]")
            if url:
                self._append_history(url, output_folder, done, "error")
        finally:
            self._process = None

    # ── Download / Retry / Cancel handlers ──────────────────────

    @on(Button.Pressed, "#download-btn")
    async def on_download(self) -> None:
        """Handle the Download button press."""
        url = self.query_one("#url-input", Input).value.strip()
        if not url:
            self._log(_SPOTDL_URL_ERROR)
            return
        if not self._is_valid_url(url):
            self._log(_SPOTDL_URL_ERROR)
            log.warning("Invalid URL entered | url=%s", url)
            return

        out = self.query_one("#output-input", Input).value.strip() or "./downloads"

        spotdl_cmd = await self._find_spotdl()
        if spotdl_cmd is None:
            return
        if not await self._ensure_deno(spotdl_cmd):
            return

        os.makedirs(out, exist_ok=True)

        self._lock_ui()
        self._failed_tracks.clear()
        self._status_label.update("Downloading…")
        self._progress_bar.update(total=100, progress=0)
        self._log_widget.clear()
        self._log(f"[bold green]▶[/] Starting download: [bold]{url}[/]")
        self._cancel_requested = False
        self._rate_limit_hint_shown = False
        self._check_cookie_file()

        cmd = self._build_spotdl_args(spotdl_cmd, [url], out)

        log.info("Running spotDL | cmd=%s url=%s", " ".join(cmd), url)
        await self._run_spotdl(cmd, url=url, output_folder=out)

        self._unlock_ui()
        log.info("Download handler finished | url=%s", url)

    @on(Button.Pressed, "#cancel-btn")
    def on_cancel(self) -> None:
        """Handle the Cancel button press."""
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
        """Clear history and re-download from scratch."""
        url = self.query_one("#url-input", Input).value.strip()
        if not url:
            self._log(_SPOTDL_URL_ERROR)
            return
        if not self._is_valid_url(url):
            self._log(_SPOTDL_URL_ERROR)
            log.warning("Invalid URL entered for fresh download | url=%s", url)
            return

        out = self.query_one("#output-input", Input).value.strip() or "./downloads"

        spotdl_cmd = await self._find_spotdl()
        if spotdl_cmd is None:
            return
        if not await self._ensure_deno(spotdl_cmd):
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

        cmd = self._build_spotdl_args(spotdl_cmd, [url], out)
        cmd.extend(["--overwrite", "force"])

        log.info("Running spotDL (fresh) | cmd=%s url=%s", " ".join(cmd), url)
        await self._run_spotdl(cmd, url=url, output_folder=out)

        self._unlock_ui()
        log.info("Fresh download handler finished | url=%s", url)

    @on(Button.Pressed, "#history-btn")
    def on_history_toggle(self) -> None:
        """Toggle the download history panel."""
        self._history_visible = not self._history_visible
        section = self.query_one("#history-section")
        if self._history_visible:
            section.add_class("visible")
        else:
            section.remove_class("visible")
        log.debug("History panel toggled | visible=%s", self._history_visible)

    # ── Helpers ─────────────────────────────────────────────────────

    @on(Button.Pressed, "#retry-btn")
    async def on_retry_failed(self) -> None:
        """Re-run spotDL targeting only the failed track URLs."""
        if not self._failed_tracks:
            self._log("[dim]No failed tracks to retry.[/]")
            return

        out = self.query_one("#output-input", Input).value.strip() or "./downloads"
        spotdl_cmd = await self._find_spotdl()
        if spotdl_cmd is None:
            return
        if not await self._ensure_deno(spotdl_cmd):
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

        # Build command: spotdl download <track_url1> <track_url2> ... --output ...
        # Explicitly pass "download" operation to avoid argparse confusion with multiple URLs.
        cmd = self._build_spotdl_args(spotdl_cmd, track_urls, out, add_download_op=True)

        log.info("Running spotDL (retry) | cmd=%s", " ".join(cmd))
        await self._run_spotdl(cmd, url="", output_folder=out)

        self._unlock_ui()
        log.info(
            "Retry handler finished | remaining_failed=%d", len(self._failed_tracks)
        )

    @on(Button.Pressed, "#quit-btn")
    def on_quit(self) -> None:
        """Kill any running process and exit the application."""
        log.info("Quit requested")
        self._cancel_requested = True
        self._kill_process()
        self.exit()

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        """Format seconds into a human-readable string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"

    def _format_download_status(self, done: int, total: int) -> str:
        """Build a status string with count, rate, and ETA."""
        parts = [f"{done} downloaded"]
        elapsed = time.monotonic() - self._download_start_time
        if done >= 2 and elapsed > 0:
            rate = done / elapsed  # tracks per second
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
        """Convenience: write to the RichLog widget, auto-scroll if at bottom."""
        if self._log_widget is not None:
            at_bottom = self._log_widget.is_vertical_scroll_end
            self._log_widget.write(message)
            # Only auto-scroll if the user was already at the bottom
            if at_bottom:
                self._log_widget.scroll_end(animate=False)


def main() -> None:
    _setup_logger()  # initialize file handler before any log.info() calls
    log.info("=" * 60)
    log.info("Spotify Playlist Downloader starting")
    log.info("Python %s | %s", sys.version.split()[0], sys.platform)
    log.info("Log file: %s", LOG_FILE)
    log.info("=" * 60)
    app = SpotifyDownloader()
    app.run()
    log.info("Spotify Playlist Downloader shut down")


if __name__ == "__main__":
    main()
