from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import re
import signal
import subprocess
import time
from dataclasses import dataclass
from typing import Any

from PySide6.QtCore import QThread, Signal

from src.manifest import normalize_name, scan_output_folder
from src.models import TrackStatus
from src.spotdl_tools import (
    DONE_RE,
    DOWNLOADING_RE,
    ERROR_RE,
    FOUND_RE,
    SKIPPED_RE,
    build_spotdl_args,
    find_spotdl,
    is_rate_limit_error,
    validate_and_ensure_deno,
)
from src.state import (
    load_track_state,
    save_track_state,
    upsert_track_state,
)

from .utils import format_download_status, format_elapsed, strip_ansi

_RATE_LIMIT_HINT = (
    "This may be YouTube rate limiting. Try setting a cookie file in Settings to reduce failures."
)
_COMPLETE_TIP = "Tip: Some tracks failed. Try updating: pip install -U spotdl yt-dlp"
_RETRY_HINT = "{failed} track(s) failed. Press Retry Failed to try again."


@dataclass
class WorkerResult:
    kind: str
    data: Any = None
    error: str | None = None


class SpotDLWorker(QThread):
    """Background worker that runs spotDL and emits signals for UI updates."""

    # Signals
    log_emitted = Signal(str)
    status_emitted = Signal(dict)
    progress_emitted = Signal(dict)
    track_emitted = Signal(str)
    failed_emitted = Signal(str)
    history_emitted = Signal(dict)
    done_emitted = Signal(dict)
    error_emitted = Signal(str)

    def __init__(
        self,
        settings: dict[str, str],
        output_folder: str,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._output_folder = output_folder
        self._url: str = ""
        self._fresh: bool = False
        self._retry_urls: list[str] = []
        self._is_retry: bool = False
        self._cancel_requested = False
        self._cancelled = False
        self._track_state = load_track_state()
        self._track_state_dirty = False
        self._process: asyncio.subprocess.Process | None = None
        self._log_buffer: list[str] = []
        self._last_flush: float = 0.0
        self._last_scan: list[Any] = []
        self._scan_index: dict[str, Any] = {}

    def start_download(self, url: str, fresh: bool = False) -> None:
        self._url = url
        self._fresh = fresh
        self._is_retry = False
        self._cancel_requested = False
        self._cancelled = False
        self._track_state = load_track_state()
        self._track_state_dirty = False
        self._log_buffer.clear()
        self.start()

    def start_retry(self, track_urls: list[str]) -> None:
        self._retry_urls = list(track_urls)
        self._is_retry = True
        self._cancel_requested = False
        self._cancelled = False
        self._track_state = load_track_state()
        self._track_state_dirty = False
        self._log_buffer.clear()
        self.start()

    def cancel(self) -> None:
        self._cancel_requested = True
        if self._process is not None:
            with contextlib.suppress(ProcessLookupError):
                self._process.terminate()
            try:
                pid = self._process.pid
                if pid:
                    if os.name == "nt":
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                    else:
                        if hasattr(os, "killpg") and hasattr(os, "getpgid"):
                            os.killpg(os.getpgid(pid), signal.SIGTERM)  # type: ignore[attr-defined]
            except (ProcessLookupError, OSError):
                pass

    def _emit_log(self, message: str) -> None:
        self._log_buffer.append(message)
        now = time.monotonic()
        if now - self._last_flush > 0.1:
            batch = "\n".join(self._log_buffer)
            self._log_buffer.clear()
            self._last_flush = now
            if batch:
                self.log_emitted.emit(batch)

    def _flush_logs(self) -> None:
        if self._log_buffer:
            batch = "\n".join(self._log_buffer)
            self._log_buffer.clear()
            self.log_emitted.emit(batch)

    def run(self) -> None:
        if self._is_retry:
            self._run_retry()
        else:
            self._run_download()

    def _run_download(self) -> None:
        try:
            self._log_buffer.append(f"Starting download: {self._url}")
            self.status_emitted.emit(
                {
                    "status": "Downloading\u2026",
                    "track": "\u2014",
                    "progress": 0.0,
                }
            )

            spotdl_cmd = find_spotdl()
            spotdl_ok, deno_ok = asyncio.run(validate_and_ensure_deno(spotdl_cmd))
            if not spotdl_ok:
                self.error_emitted.emit("spotDL is not installed")
                return

            if not deno_ok:
                self._log_buffer.append(
                    "Deno could not be installed. Age-restricted videos may fail; "
                    "most downloads still work."
                )

            try:
                import pathlib

                pathlib.Path(self._output_folder).expanduser().resolve()
                os.makedirs(self._output_folder, exist_ok=True)
            except (OSError, ValueError):
                self.error_emitted.emit(f"Cannot create output folder: {self._output_folder}")
                return

            try:
                self._last_scan = scan_output_folder(self._output_folder)
                self._scan_index = {t.normalized_name: t for t in self._last_scan}
            except Exception as exc:
                logging.getLogger("spotify_downloader").warning(
                    "Scan index build failed | error=%s", exc
                )

            policy = self._settings.get("duplicate_policy", "skip")
            if policy not in {"skip", "metadata"}:
                policy = "skip"

            overwrite = "force" if self._fresh else ("skip" if policy == "skip" else "metadata")
            cmd = build_spotdl_args(
                spotdl_cmd,
                [self._url],
                self._output_folder,
                self._settings,
                overwrite=overwrite,
                scan_for_songs=True,
            )

            self._run_spotdl(cmd, url=self._url, output_folder=self._output_folder)
            self.done_emitted.emit(
                {
                    "url": self._url,
                    "output_folder": self._output_folder,
                }
            )
        except Exception as exc:
            self.error_emitted.emit(str(exc))
        finally:
            self._flush_logs()

    def _run_retry(self) -> None:
        try:
            self._log_buffer.append("Retrying failed tracks\u2026")
            self.status_emitted.emit(
                {
                    "status": "Retrying failed tracks\u2026",
                    "track": "\u2014",
                    "progress": 0.0,
                }
            )

            spotdl_cmd = find_spotdl()
            spotdl_ok, deno_ok = asyncio.run(validate_and_ensure_deno(spotdl_cmd))
            if not spotdl_ok:
                self.error_emitted.emit("spotDL is not installed")
                return

            if not deno_ok:
                self._log_buffer.append(
                    "Deno could not be installed. Age-restricted videos may fail; "
                    "most downloads still work."
                )

            try:
                import pathlib

                pathlib.Path(self._output_folder).expanduser().resolve()
                os.makedirs(self._output_folder, exist_ok=True)
            except (OSError, ValueError):
                self.error_emitted.emit(f"Cannot create output folder: {self._output_folder}")
                return

            try:
                self._last_scan = scan_output_folder(self._output_folder)
                self._scan_index = {t.normalized_name: t for t in self._last_scan}
            except Exception as exc:
                logging.getLogger("spotify_downloader").warning(
                    "Scan index build failed | error=%s", exc
                )

            if not self._retry_urls:
                self._log_buffer.append("No failed tracks to retry.")
                self.done_emitted.emit(
                    {
                        "url": "",
                        "output_folder": self._output_folder,
                    }
                )
                return

            cmd = build_spotdl_args(
                spotdl_cmd,
                self._retry_urls,
                self._output_folder,
                self._settings,
                overwrite="skip",
                scan_for_songs=True,
            )

            self._run_spotdl(cmd, url="", output_folder=self._output_folder)
            self.done_emitted.emit(
                {
                    "url": "",
                    "output_folder": self._output_folder,
                }
            )
        except Exception as exc:
            self.error_emitted.emit(str(exc))
        finally:
            self._flush_logs()

    def _run_spotdl(self, cmd: list[str], url: str = "", output_folder: str = "") -> None:
        downloaded = 0
        skipped = 0
        failed = 0
        total = 0
        start_time = time.monotonic()
        pending_done = False
        in_traceback = False
        rate_limit_hint_shown = False

        sub_env = dict(os.environ)
        sub_env["PYTHONIOENCODING"] = "utf-8"
        sub_env["PYTHONLEGACYWINDOWSSTDIO"] = "1"

        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            proc = loop.run_until_complete(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT,
                    env=sub_env,
                )
            )
            self._process = proc

            assert proc.stdout is not None
            while True:
                if self._cancel_requested:
                    self._cancelled = True
                    break
                raw = loop.run_until_complete(proc.stdout.readline())
                if not raw:
                    break

                chunk = strip_ansi(raw.decode("utf-8", errors="replace"))
                for text in chunk.splitlines():
                    text = text.strip()
                    if not text:
                        continue

                    m = DOWNLOADING_RE.search(text)
                    if m:
                        in_traceback = False
                        pending_done = False
                        track_name = m.group(1).strip()
                        self.track_emitted.emit(track_name)
                        self._emit_log(f"Downloading: {track_name}")
                        continue

                    m = SKIPPED_RE.search(text)
                    if m:
                        in_traceback = False
                        track_name = m.group(1).strip()
                        skipped += 1
                        pending_done = True
                        self.track_emitted.emit(track_name)
                        self._record_completed_track(track_name, TrackStatus.SKIPPED)
                        self._emit_log(f"Skipped (duplicate): {track_name}")
                        continue

                    m = DONE_RE.search(text)
                    if m:
                        in_traceback = False
                        track_name = m.group(1).strip()
                        if "%s" in track_name or "song." in track_name:
                            pending_done = True
                            continue
                        downloaded += 1
                        pending_done = True
                        self.track_emitted.emit(track_name)
                        self._record_completed_track(track_name, TrackStatus.DOWNLOADED)
                        continue

                    if pending_done:
                        pending_done = False
                        elapsed = time.monotonic() - start_time
                        status_text = format_download_status(downloaded + skipped, total, elapsed)
                        self.status_emitted.emit(
                            {
                                "status": status_text,
                                "track": "\u2014",
                                "progress": min((downloaded + skipped) / total, 1.0)
                                if total > 0
                                else 0.0,
                            }
                        )

                    m = FOUND_RE.search(text)
                    if m:
                        in_traceback = False
                        total = int(m.group(1))
                        self.progress_emitted.emit({"total": total, "done": 0})
                        continue

                    if "--- Logging error ---" in text or text.startswith("Traceback"):
                        in_traceback = True
                        continue

                    if in_traceback:
                        if (
                            DOWNLOADING_RE.search(text)
                            or DONE_RE.search(text)
                            or FOUND_RE.search(text)
                            or ERROR_RE.search(text)
                        ):
                            in_traceback = False
                        else:
                            continue

                    if ERROR_RE.search(text):
                        failed += 1
                        self._record_failed_track(text)
                        self._emit_log(text)
                        if not rate_limit_hint_shown and is_rate_limit_error(text):
                            rate_limit_hint_shown = True
                            self._emit_log(_RATE_LIMIT_HINT)
                        continue

                    text_lower = text.lower()
                    if "error" in text_lower or "fail" in text_lower:
                        self._emit_log(text)
                    else:
                        self._emit_log(text)

            if self._cancelled:
                self.status_emitted.emit(
                    {
                        "status": "Cancelled",
                        "track": "\u2014",
                        "progress": 0.0,
                    }
                )
                if url:
                    self.history_emitted.emit(
                        {
                            "url": url,
                            "output_folder": output_folder,
                            "tracks_downloaded": downloaded + skipped,
                            "status": "cancelled",
                        }
                    )
            else:
                return_code = loop.run_until_complete(proc.wait())
                elapsed_final = time.monotonic() - start_time

                if return_code == 0:
                    self.status_emitted.emit(
                        {
                            "status": f"Complete! ({format_elapsed(elapsed_final)})",
                            "track": "\u2014",
                            "progress": 1.0,
                        }
                    )
                    summary_parts = []
                    if downloaded > 0:
                        summary_parts.append(f"{downloaded} new download(s)")
                    if skipped > 0:
                        summary_parts.append(f"{skipped} duplicate skip(s)")
                    if failed > 0:
                        summary_parts.append(f"{failed} failed")
                    summary = ", ".join(summary_parts) if summary_parts else "nothing to do"
                    self.log_emitted.emit(
                        f"Complete! {summary} in {format_elapsed(elapsed_final)}\n"
                        f"   Files saved to: {output_folder}"
                    )
                    if failed > 0:
                        self._emit_log(_COMPLETE_TIP)
                    if url:
                        self.history_emitted.emit(
                            {
                                "url": url,
                                "output_folder": output_folder,
                                "tracks_downloaded": downloaded + skipped,
                                "status": "completed",
                            }
                        )
                    if failed > 0:
                        self._emit_log(_RETRY_HINT.format(failed=failed))
                else:
                    self.status_emitted.emit(
                        {
                            "status": f"Failed (exit {return_code})",
                            "track": "\u2014",
                            "progress": 0.0,
                        }
                    )
                    self._emit_log(f"spotDL exited with code {return_code}")
                    if failed > 0:
                        self._emit_log(f"{failed} track(s) failed to download")
                    if url:
                        self.history_emitted.emit(
                            {
                                "url": url,
                                "output_folder": output_folder,
                                "tracks_downloaded": downloaded + skipped,
                                "status": "failed",
                            }
                        )
                    if failed > 0:
                        self._emit_log(_RETRY_HINT.format(failed=failed))
        except Exception as exc:
            self.error_emitted.emit(str(exc))
        finally:
            self._process = None
            if self._track_state_dirty:
                try:
                    save_track_state(self._track_state)
                except OSError as exc:
                    log = logging.getLogger("spotify_downloader")
                    log.error("Could not save track state | error=%s", exc)
            if loop is not None:
                loop.close()

    def _record_completed_track(self, track_name: str, status: str) -> None:
        self._track_state_dirty = True
        key = normalize_name(track_name)
        upsert_track_state(
            self._track_state,
            key=key,
            title=track_name,
            status=status,
            source="spotdl-output",
        )
        try:
            match = self._scan_index.get(key)
            if match is not None:
                upsert_track_state(
                    self._track_state,
                    key=key,
                    title=match.title or track_name,
                    artist=match.artist,
                    status=status,
                    path=str(match.path),
                    source="local-scan",
                )
        except (KeyError, AttributeError, TypeError) as exc:
            logging.getLogger(__name__).warning(
                "Track state update failed for %r: %s", track_name, exc
            )

    def _record_failed_track(self, text: str) -> None:
        self._track_state_dirty = True
        track_url_m = re.search(r"(https?://open\.spotify\.com/track/[A-Za-z0-9]+)", text)
        if track_url_m:
            track_url = track_url_m.group(1)
            self.failed_emitted.emit(track_url)
            upsert_track_state(
                self._track_state,
                key=track_url.lower(),
                title=text,
                status=TrackStatus.FAILED,
                source="spotify-url",
                error=text,
            )
            return
        track_name_m = re.search(r"Failed to download\s+(.+)", text, re.IGNORECASE)
        if track_name_m:
            track_name = track_name_m.group(1).strip()
            self.failed_emitted.emit(track_name)
            key = normalize_name(track_name)
            upsert_track_state(
                self._track_state,
                key=key,
                title=track_name,
                status=TrackStatus.FAILED,
                source="track-name",
                error=text,
            )
