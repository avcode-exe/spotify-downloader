from __future__ import annotations

import asyncio
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
from typing import Any, Callable

from src.duplicates import quarantine_duplicate_copies
from src.manifest import group_duplicates, normalize_name, scan_output_folder
from src.spotdl_tools import (
    build_spotdl_args,
    ensure_deno,
    find_spotdl,
    is_rate_limit_error,
    validate_spotdl,
)
from src.state import (
    load_track_state,
    save_track_state,
    summarize_track_state,
    upsert_track_state,
)

from .utils import format_download_status, format_elapsed, strip_ansi


DOWNLOADING_RE = re.compile(r"Downloading\s+(.+)", re.IGNORECASE)
DONE_RE = re.compile(r"(?:Downloaded|✓)\s+(.+)", re.IGNORECASE)
SKIPPED_RE = re.compile(r"Skipping\s+(.+)\s+as it is already downloaded", re.IGNORECASE)
ERROR_RE = re.compile(r"(?:AudioProviderError|Failed to download)", re.IGNORECASE)
FOUND_RE = re.compile(r"Found\s+(\d+)\s+songs", re.IGNORECASE)


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
        self._failed_tracks: list[str] = []
        self._track_state = load_track_state()
        self._last_scan: list[Any] = []

    def start_download(self, url: str, fresh: bool = False) -> None:
        Thread(target=self._run_download, args=(url, fresh), daemon=True).start()

    def start_retry(self) -> None:
        Thread(target=self._run_retry, daemon=True).start()

    def cancel(self) -> None:
        self._cancel_requested = True
        if self._process is not None:
            try:
                self._process.terminate()
            except ProcessLookupError:
                pass

    def _emit(self, kind: str, data: Any = None, error: str | None = None) -> None:
        result = WorkerResult(kind=kind, data=data, error=error)
        if self._tk_root is not None:
            self._tk_root.after(0, lambda: self._on_event(result))
        else:
            self._on_event(result)

    def _run_download(self, url: str, fresh: bool) -> None:
        try:
            self._emit("log", {"message": f"▶ Starting download: {url}"})
            self._emit(
                "status", {"status": "Downloading…", "track": "—", "progress": 0.0}
            )

            spotdl_cmd = find_spotdl()
            if spotdl_cmd is None:
                self._emit("error", error="spotDL not found")
                return

            if not asyncio.run(validate_spotdl(spotdl_cmd)):
                self._emit("error", error="spotDL is not installed")
                return

            if not asyncio.run(ensure_deno(spotdl_cmd)):
                self._emit("error", error="Deno installation failed")
                return

            os.makedirs(self._output_folder, exist_ok=True)

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

    def _run_retry(self) -> None:
        try:
            self._emit("log", {"message": "🔄 Retrying failed tracks…"})
            self._emit(
                "status",
                {"status": "Retrying failed tracks…", "track": "—", "progress": 0.0},
            )

            spotdl_cmd = find_spotdl()
            if spotdl_cmd is None:
                self._emit("error", error="spotDL not found")
                return

            if not asyncio.run(validate_spotdl(spotdl_cmd)):
                self._emit("error", error="spotDL is not installed")
                return

            if not asyncio.run(ensure_deno(spotdl_cmd)):
                self._emit("error", error="Deno installation failed")
                return

            os.makedirs(self._output_folder, exist_ok=True)
            track_urls = list(self._failed_tracks)
            self._failed_tracks.clear()

            cmd = build_spotdl_args(
                spotdl_cmd,
                track_urls,
                self._output_folder,
                self._settings,
                add_download_op=True,
                overwrite="skip",
                scan_for_songs=True,
            )

            self._run_spotdl(cmd, url="", output_folder=self._output_folder)
            self._emit("done", data={"url": "", "output_folder": self._output_folder})
        except Exception as exc:
            self._emit("error", error=str(exc))

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
                        self._emit("log", {"message": f"↓ {track_name}"})
                        continue

                    m = SKIPPED_RE.search(text)
                    if m:
                        in_traceback = False
                        track_name = m.group(1).strip()
                        skipped += 1
                        pending_done = True
                        self._emit("track", {"track": track_name})
                        self._record_completed_track(
                            track_name, output_folder, "skipped"
                        )
                        self._emit(
                            "log", {"message": f"⏭ Skipped (duplicate): {track_name}"}
                        )
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
                        self._record_completed_track(
                            track_name, output_folder, "downloaded"
                        )
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
                        self._record_failed_track(text, output_folder)
                        self._emit("log", {"message": f"✗ {text}"})
                        if not rate_limit_hint_shown and is_rate_limit_error(text):
                            rate_limit_hint_shown = True
                            self._emit(
                                "log",
                                {
                                    "message": "This may be YouTube rate limiting. Try setting a cookie file in Settings to reduce failures."
                                },
                            )
                        continue

                    text_lower = text.lower()
                    if "error" in text_lower or "fail" in text_lower:
                        self._emit("log", {"message": text})
                    else:
                        self._emit("log", {"message": text})

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
                        "message": f"\n✓ Complete! {summary} in {format_elapsed(elapsed_final)}\n   Files saved to: {output_folder}"
                    },
                )
                if failed > 0:
                    self._emit(
                        "log",
                        {
                            "message": "Tip: Some tracks failed. Try updating: pip install -U spotdl yt-dlp"
                        },
                    )
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
                if self._failed_tracks:
                    self._emit(
                        "log",
                        {
                            "message": f"{len(self._failed_tracks)} track(s) failed. Press Retry Failed to try again."
                        },
                    )
            else:
                self._emit(
                    "status",
                    {
                        "status": f"Failed (exit {return_code})",
                        "track": "—",
                        "progress": 0.0,
                    },
                )
                self._emit(
                    "log", {"message": f"\n✗ spotDL exited with code {return_code}"}
                )
                if failed > 0:
                    self._emit(
                        "log", {"message": f"{failed} track(s) failed to download"}
                    )
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
                if self._failed_tracks:
                    self._emit(
                        "log",
                        {
                            "message": f"{len(self._failed_tracks)} track(s) failed. Press Retry Failed to try again."
                        },
                    )
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
            save_track_state(self._track_state)
            loop.close()

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

    def refresh_preview(self) -> dict[str, Any]:
        self._last_scan = scan_output_folder(self._output_folder)
        duplicate_groups = group_duplicates(self._last_scan)
        return {
            "tracks": self._last_scan,
            "duplicate_groups": duplicate_groups,
            "state_summary": summarize_track_state(self._track_state),
        }

    def move_duplicates(self) -> tuple[int, Path]:
        self._last_scan = scan_output_folder(self._output_folder)
        duplicate_groups = group_duplicates(self._last_scan)
        duplicate_groups = [
            group for group in duplicate_groups if group.safe_to_move and group.copies
        ]
        if not duplicate_groups:
            return 0, Path(self._output_folder) / "duplicates"

        count, destination = quarantine_duplicate_copies(
            duplicate_groups, self._output_folder
        )
        for group in duplicate_groups:
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
        return count, destination
