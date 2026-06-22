from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_FILE = os.path.join(os.path.expanduser("~"), ".spotdl", "track_state.json")
HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".spotdl", "download_history.json")
SETTINGS_FILE = os.path.join(os.path.expanduser("~"), ".spotdl", "settings.json")


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
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except OSError as exc:
        log = logging.getLogger("spotify_downloader")
        log.warning("Could not save track state | error=%s", exc)


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
    del state[1000:]


def summarize_track_state(state: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "downloaded": 0,
        "skipped": 0,
        "failed": 0,
        "quarantined": 0,
        "other": 0,
    }
    for entry in state:
        status = str(entry.get("status", "other"))
        if status in summary:
            summary[status] += 1
        else:
            summary["other"] += 1
    return summary


def update_paths_from_scan(state: list[dict[str, Any]], tracks: list[Any]) -> None:
    for track in tracks:
        key = (
            getattr(track, "normalized_name", None)
            or Path(getattr(track, "filename", "")).stem.lower()
        )
        existing = next(
            (e for e in state if str(e.get("key", "")).strip().lower() == str(key).strip().lower()),
            None,
        )
        current_status = existing.get("status") if existing else None
        if current_status in {"failed", "quarantined"}:
            continue
        upsert_track_state(
            state,
            key=str(key),
            title=getattr(track, "title", None),
            artist=getattr(track, "artist", None),
            status="downloaded",
            path=str(getattr(track, "path")),
            source="local-scan",
        )
