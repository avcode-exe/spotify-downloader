from __future__ import annotations

import asyncio
import logging
import os
import re
import signal
import subprocess
import time
from dataclasses import dataclass
from threading import Thread
from typing import Any, Callable

from src.manifest import normalize_name, scan_output_folder
from src.models import TrackStatus
from src.spotdl_tools import (
    DONE_RE,
    DOWNLOADING_RE,
    ERROR_RE,
    FOUND_RE,
    SKIPPED_RE,
    build_spotdl_args,
    ensure_deno,
    find_spotdl,
    is_rate_limit_error,
    validate_spotdl,
)
from src.state import (
    load_track_state,
    save_track_state,
    upsert_track_state,
)

from .utils import format_download_status, format_elapsed, strip_ansi

_RATE_LIMIT_HINT = (
    "This may be YouTube rate limiting. Try setting a cookie file "
    "in Settings to reduce failures."
)
_COMPLETE_TIP = "Tip: Some tracks failed. Try updating: pip install -U spotdl yt-dlp"
_RETRY_HINT = "{failed} track(s) failed. Press 🔄 Retry Failed to try again."


@dataclass
class WorkerResult:
    kind: str
    data: Any = None
    error: str | None = None


class SpotDLWorker:
    def __init__(
        self,
        settings: dict[str, str],
        output_folder: str,
        on_event: Callable[[WorkerResult], None],
        tk_root: Any = None,
    ) -> None:
        self._settings = settings
        self._output_folder = output_folder
        self._on_event = on_event
        self._tk_root = tk_root
        self._process: asyncio.subprocess.Process | None = None
        self._cancel_requested = False
        self._track_state = load_track_state()
        self._track_state_dirty = False
        self._last_scan: list[Any] = []
        self._scan_index: dict[str, Any] = {}
        self._thread: Thread | None = None
        self._log_buffer: list[str] = []
        self._last_flush: float = 0.0

    def start_download(self, url: str, fresh: bool = False) -> None:
        self._thread = Thread(target=self._run_download, args=(url, fresh))
        self._thread.start()

    def start_retry(self, track_urls: list[str]) -> None:
        """Retry a specific list of failed track URLs (owned by the caller).

        The controller, not the worker, owns the failed-track list so retry
        keeps working even when a fresh worker is created for a new download.
        """
        self._thread = Thread(target=self._run_retry, args=(list(track_urls),))
        self._thread.start()

    def cancel(self) -> None:
        self._cancel_requested = True
        if self._process is not None:
            try:
                self._process.terminate()
            except ProcessLookupError:
                pass
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
                        os.killpg(os.getpgid(pid), signal.SIGTERM)
            except (ProcessLookupError, OSError):
                pass

    def _emit(self, kind: str, data: Any = None, error: str | None = None) -> None:
        result = WorkerResult(kind=kind, data=data, error=error)
        if self._tk_root is not None:
            self._tk_root.after(0, lambda: self._on_event(result))
        else:
            self._on_event(result)

    def _emit_log(self, message: str) -> None:
        self._log_buffer.append(message)
        now = time.monotonic()
        if now - self._last_flush > 0.1:
            batch = "\n".join(self._log_buffer)
            self._log_buffer.clear()
            self._last_flush = now
            if batch:
                self._emit("log", {"message": batch})

    def _flush_logs(self) -> None:
        if self._log_buffer:
            batch = "\n".join(self._log_buffer)
            self._log_buffer.clear()
            self._emit("log", {"message": batch})

    def _run_download(self, url: str, fresh: bool) -> None:
        try:
            self._log_buffer.append(f"▶ Starting download: {url}")
            self._emit(
                "status", {"status": "Downloading…", "track": "—", "progress": 0.0}
            )

            spotdl_cmd = find_spotdl()
            if not asyncio.run(validate_spotdl(spotdl_cmd)):
                self._emit("error", error="spotDL is not installed")
                return

            if not asyncio.run(ensure_deno(spotdl_cmd)):
                self._log_buffer.append(
                    "⚠ Deno could not be installed. "
                    "Age-restricted videos may fail; most downloads still work."
                )

            try:
                os.makedirs(self._output_folder, exist_ok=True)
            except PermissionError:
                self._emit(
                    "error", error=f"Cannot create output folder: {self._output_folder}"
                )
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

            overwrite = (
                "force" if fresh else ("skip" if policy == "skip" else "metadata")
            )
            cmd = build_spotdl_args(
                spotdl_cmd,
                [url],
                self._output_folder,
                self._settings,
                overwrite=overwrite,
                scan_for_songs=True,
            )

            self._run_spotdl(cmd, url=url, output_folder=self._output_folder)
            self._emit("done", data={"url": url, "output_folder": self._output_folder})
        except Exception as exc:
            self._emit("error", error=str(exc))
        finally:
            self._flush_logs()

    def _run_retry(self, track_urls: list[str]) -> None:
        try:
            self._log_buffer.append("🔄 Retrying failed tracks…")
            self._emit(
                "status",
                {"status": "Retrying failed tracks…", "track": "—", "progress": 0.0},
            )

            spotdl_cmd = find_spotdl()
            if not asyncio.run(validate_spotdl(spotdl_cmd)):
                self._emit("error", error="spotDL is not installed")
                return

            if not asyncio.run(ensure_deno(spotdl_cmd)):
                self._log_buffer.append(
                    "⚠ Deno could not be installed. "
                    "Age-restricted videos may fail; most downloads still work."
                )

            try:
                os.makedirs(self._output_folder, exist_ok=True)
            except PermissionError:
                self._emit(
                    "error", error=f"Cannot create output folder: {self._output_folder}"
                )
                return
            try:
                self._last_scan = scan_output_folder(self._output_folder)
                self._scan_index = {t.normalized_name: t for t in self._last_scan}
            except Exception as exc:
                logging.getLogger("spotify_downloader").warning(
                    "Scan index build failed | error=%s", exc
                )
            if not track_urls:
                self._log_buffer.append("No failed tracks to retry.")
                self._emit(
                    "done", data={"url": "", "output_folder": self._output_folder}
                )
                return

            cmd = build_spotdl_args(
                spotdl_cmd,
                track_urls,
                self._output_folder,
                self._settings,
                overwrite="skip",
                scan_for_songs=True,
            )

            self._run_spotdl(cmd, url="", output_folder=self._output_folder)
            self._emit("done", data={"url": "", "output_folder": self._output_folder})
        except Exception as exc:
            self._emit("error", error=str(exc))
        finally:
            self._flush_logs()

    def _run_spotdl(
        self, cmd: list[str], url: str = "", output_folder: str = ""
    ) -> None:
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
                        self._emit("track", {"track": track_name})
                        self._emit_log(f"↓ {track_name}")
                        continue

                    m = SKIPPED_RE.search(text)
                    if m:
                        in_traceback = False
                        track_name = m.group(1).strip()
                        skipped += 1
                        pending_done = True
                        self._emit("track", {"track": track_name})
                        self._record_completed_track(track_name, TrackStatus.SKIPPED)
                        self._emit_log(f"⏭ Skipped (duplicate): {track_name}")
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
                        self._emit("track", {"track": track_name})
                        self._record_completed_track(track_name, TrackStatus.DOWNLOADED)
                        continue

                    if pending_done:
                        pending_done = False
                        elapsed = time.monotonic() - start_time
                        status_text = format_download_status(
                            downloaded + skipped, total, elapsed
                        )
                        self._emit(
                            "status",
                            {
                                "status": status_text,
                                "track": "—",
                                "progress": min((downloaded + skipped) / total, 1.0)
                                if total > 0
                                else 0.0,
                            },
                        )

                    m = FOUND_RE.search(text)
                    if m:
                        in_traceback = False
                        total = int(m.group(1))
                        self._emit("progress", {"total": total, "done": 0})
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
                        self._emit_log(f"✗ {text}")
                        if not rate_limit_hint_shown and is_rate_limit_error(text):
                            rate_limit_hint_shown = True
                            self._emit_log(_RATE_LIMIT_HINT)
                        continue

                    text_lower = text.lower()
                    if "error" in text_lower or "fail" in text_lower:
                        self._emit_log(text)
                    else:
                        self._emit_log(text)

            return_code = loop.run_until_complete(proc.wait())
            elapsed_final = time.monotonic() - start_time

            if return_code == 0:
                self._emit(
                    "status",
                    {
                        "status": f"Complete! ({format_elapsed(elapsed_final)})",
                        "track": "—",
                        "progress": 1.0,
                    },
                )
                summary_parts = []
                if downloaded > 0:
                    summary_parts.append(f"{downloaded} new download(s)")
                if skipped > 0:
                    summary_parts.append(f"{skipped} duplicate skip(s)")
                if failed > 0:
                    summary_parts.append(f"{failed} failed")
                summary = ", ".join(summary_parts) if summary_parts else "nothing to do"
                self._emit(
                    "log",
                    {
                        "message": (
                            f"\n✓ Complete! {summary} in "
                            f"{format_elapsed(elapsed_final)}\n"
                            f"   Files saved to: {output_folder}"
                        )
                    },
                )
                if failed > 0:
                    self._emit_log(_COMPLETE_TIP)
                if url:
                    self._emit(
                        "history",
                        {
                            "url": url,
                            "output_folder": output_folder,
                            "tracks_downloaded": downloaded + skipped,
                            "status": "completed",
                        },
                    )
                if failed > 0:
                    self._emit_log(_RETRY_HINT.format(failed=failed))
            else:
                self._emit(
                    "status",
                    {
                        "status": f"Failed (exit {return_code})",
                        "track": "—",
                        "progress": 0.0,
                    },
                )
                self._emit_log(f"\n✗ spotDL exited with code {return_code}")
                if failed > 0:
                    self._emit_log(f"{failed} track(s) failed to download")
                if url:
                    self._emit(
                        "history",
                        {
                            "url": url,
                            "output_folder": output_folder,
                            "tracks_downloaded": downloaded + skipped,
                            "status": "failed",
                        },
                    )
                if failed > 0:
                    self._emit_log(_RETRY_HINT.format(failed=failed))
        except asyncio.CancelledError:
            self._emit("status", {"status": "Cancelled", "track": "—", "progress": 0.0})
            if url:
                self._emit(
                    "history",
                    {
                        "url": url,
                        "output_folder": output_folder,
                        "tracks_downloaded": downloaded + skipped,
                        "status": "cancelled",
                    },
                )
        except Exception as exc:
            self._emit("error", error=str(exc))
        finally:
            self._process = None
            if self._track_state_dirty:
                try:
                    save_track_state(self._track_state)
                except OSError as exc:
                    log = logging.getLogger("spotify_downloader")
                    log.error("Could not save track state | error=%s", exc)
            if self._log_buffer:
                batch = "\n".join(self._log_buffer)
                self._log_buffer.clear()
                self._emit("log", {"message": batch})
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
            # O(1) lookup into the cached scan index instead of a linear scan.
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
        except Exception:
            pass

    def _record_failed_track(self, text: str) -> None:
        self._track_state_dirty = True
        track_url_m = re.search(
            r"(https?://open\.spotify\.com/track/[A-Za-z0-9]+)", text
        )
        if track_url_m:
            track_url = track_url_m.group(1)
            # Surface the retryable URL to the controller so it can offer a
            # Retry that survives a fresh worker (see start_retry).
            self._emit("failed", {"url": track_url})
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
            key = normalize_name(track_name)
            upsert_track_state(
                self._track_state,
                key=key,
                title=track_name,
                status=TrackStatus.FAILED,
                source="track-name",
                error=text,
            )
