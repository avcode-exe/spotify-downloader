from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import TrackStatus

STATE_FILE = os.path.join(os.path.expanduser("~"), ".spotdl", "track_state.json")
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".spotdl", "download_history.json")
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".spotdl", "settings.json")


def ensure_data_dir(path: str) -> None:
    """Create the parent directory of ``path`` with restrictive permissions.

    The ``~/.spotdl`` directory holds authenticated cookies and session state,
    so we tighten it to owner-only (0o700) on POSIX. On Windows ``os.chmod``
    only honours the read-only bit, so the call is a safe no-op there.
    """
    directory = os.path.dirname(path)
    if not directory:
        return
    os.makedirs(directory, exist_ok=True)
    try:
        os.chmod(directory, 0o700)
    except OSError:
        pass


def save_json_secure(path: str, data: object) -> None:
    """Persist JSON atomically with owner-only file permissions.

    Writes to a temp file, sets 0o600, fsyncs for durability, then
    ``os.replace`` swaps it in place. Raises on failure so callers can
    surface the error to the user instead of silently corrupting state.
    """
    ensure_data_dir(path)
    tmp_path = f"{path}.tmp"
    try:
        fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            try:
                os.fsync(f.fileno())
            except OSError:
                pass
        os.replace(tmp_path, path)
    except OSError:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        raise


def _load_raw() -> list[dict[str, Any]]:
    try:
        if os.path.isfile(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
    except (json.JSONDecodeError, OSError):
        return []
    return []


def load_track_state() -> list[dict[str, Any]]:
    return _load_raw()


def save_track_state(state: list[dict[str, Any]]) -> None:
    save_json_secure(STATE_FILE, state)


def upsert_track_state(
    state: list[dict[str, Any]],
    *,
    key: str,
    title: str | None = None,
    artist: str | None = None,
    status: str,
    path: str | None = None,
    source: str | None = None,
    error: str | None = None,
) -> None:
    normalized_key = key.strip().lower()
    if not normalized_key:
        return
    now = datetime.now(timezone.utc).isoformat()
    for entry in state:
        if str(entry.get("key", "")).strip().lower() == normalized_key:
            entry.update(
                {
                    "title": title or entry.get("title"),
                    "artist": artist or entry.get("artist"),
                    "status": status,
                    "path": path or entry.get("path"),
                    "source": source or entry.get("source"),
                    "error": error,
                    "updated_at": now,
                }
            )
            entry.setdefault("first_seen", now)
            return
    state.insert(
        0,
        {
            "key": normalized_key,
            "title": title,
            "artist": artist,
            "status": status,
            "path": path,
            "source": source,
            "error": error,
            "first_seen": now,
            "updated_at": now,
        },
    )
    if len(state) > 1000:
        state.pop()


def summarize_track_state(state: list[dict[str, Any]]) -> dict[str, int]:
    summary = {bucket: 0 for bucket in TrackStatus.SUMMARY_BUCKETS}
    for entry in state:
        status = str(entry.get("status", TrackStatus.OTHER))
        if status in summary:
            summary[status] += 1
        else:
            summary[TrackStatus.OTHER] += 1
    return summary


def update_paths_from_scan(state: list[dict[str, Any]], tracks: list[Any]) -> None:
    index: dict[str, dict[str, Any]] = {}
    for entry in state:
        key = str(entry.get("key", "")).strip().lower()
        if key:
            index[key] = entry
    now = datetime.now(timezone.utc).isoformat()
    for track in tracks:
        key = (
            getattr(track, "normalized_name", None)
            or Path(getattr(track, "filename", "")).stem.lower()
        )
        key_str = str(key).strip().lower()
        existing = index.get(key_str)
        if existing is not None:
            current_status = existing.get("status")
            if current_status in {TrackStatus.FAILED, TrackStatus.QUARANTINED}:
                continue
            existing.update(
                {
                    "title": getattr(track, "title", None) or existing.get("title"),
                    "artist": getattr(track, "artist", None) or existing.get("artist"),
                    "status": TrackStatus.DOWNLOADED,
                    "path": str(getattr(track, "path")),
                    "source": "local-scan",
                    "updated_at": now,
                }
            )
            existing.setdefault("first_seen", now)
        else:
            new_entry: dict[str, Any] = {
                "key": key_str,
                "title": getattr(track, "title", None),
                "artist": getattr(track, "artist", None),
                "status": TrackStatus.DOWNLOADED,
                "path": str(getattr(track, "path")),
                "source": "local-scan",
                "first_seen": now,
                "updated_at": now,
            }
            state.insert(0, new_entry)
            index[key_str] = new_entry
    if len(state) > 1000:
        state.pop()
