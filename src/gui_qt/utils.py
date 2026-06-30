from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from src.models import DuplicateGroup, LocalTrack
from src.state import summarize_track_state

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def format_elapsed(seconds: float) -> str:
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    return f"{hours}h {minutes}m"


def format_download_status(done: int, total: int, elapsed: float) -> str:
    parts = [f"{done} processed"]
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
                hours = int(eta_secs // 3600)
                minutes = int((eta_secs % 3600) // 60)
                parts.append(f"~{hours}h {minutes}m left")
    return " \u00b7 ".join(parts)


def summarize_local_scan(
    tracks: list[LocalTrack],
    duplicate_groups: list[DuplicateGroup],
    track_state: list[dict[str, Any]],
) -> dict[str, int]:
    from src.manifest import summarize_scan

    scan_summary = summarize_scan(tracks, duplicate_groups)
    state_summary = summarize_track_state(track_state)
    return {**scan_summary, **state_summary}


def format_track_line(track: LocalTrack) -> str:
    title = track.title or track.filename
    artist = f" \u2014 {track.artist}" if track.artist else ""
    return f"{title}{artist} ({track.path.name})"


def truncate_text(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[: max_length - 1] + "\u2026"


def safe_path_name(path: str | Path) -> str:
    return Path(path).expanduser().resolve().as_posix()
