from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


AUDIO_EXTENSIONS: set[str] = {
    ".mp3",
    ".m4a",
    ".flac",
    ".opus",
    ".ogg",
    ".wav",
}

DUPLICATE_POLICY_OPTIONS: list[tuple[str, str]] = [
    ("Skip existing", "skip"),
    ("Update metadata", "metadata"),
]


class TrackStatus:
    """Canonical per-track status values.

    Centralised so the persistence layer (`state.py`) and both UIs cannot
    drift apart through typos in magic strings. The string values are part of
    the on-disk JSON contract, so they must remain stable.
    """

    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"
    FAILED = "failed"
    QUARANTINED = "quarantined"
    OTHER = "other"

    #: every bucket ``summarize_track_state`` reports on, in display order
    SUMMARY_BUCKETS: tuple[str, ...] = (
        DOWNLOADED,
        SKIPPED,
        FAILED,
        QUARANTINED,
        OTHER,
    )


def redact_proxy(proxy: str) -> str:
    """Hide credentials embedded in an authenticated proxy URL.

    ``http://user:pass@host:port`` -> ``http://***@host:port``. Leaves URLs
    without userinfo untouched so they remain useful in logs.
    """
    if not proxy:
        return proxy
    parsed = urlparse(proxy)
    if parsed.username and parsed.hostname:
        if parsed.port:
            return f"{parsed.scheme}://***@{parsed.hostname}:{parsed.port}"
        return f"{parsed.scheme}://***@{parsed.hostname}"
    return proxy


def redact_settings_for_log(settings: dict[str, str]) -> dict[str, str]:
    """Return a copy of ``settings`` safe to log (proxy credentials masked).

    Note: proxy credentials are redacted in logs but are still stored in
    plaintext in the on-disk settings file. Users on shared machines should
    be aware that ``~/.spotdl/settings.json`` may contain proxy passwords.
    """
    redacted = dict(settings)
    if "proxy" in redacted:
        redacted["proxy"] = redact_proxy(redacted.get("proxy", ""))
    return redacted


@dataclass(frozen=True)
class LocalTrack:
    path: Path
    filename: str
    normalized_name: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    duration: float | None = None
    bitrate: int | None = None
    size: int = 0
    modified: float = 0.0
    tags: dict[str, Any] = field(default_factory=dict)

    @property
    def quality_score(self) -> tuple[int, int, int, float]:
        return (
            self.bitrate or 0,
            self.size,
            int((self.duration or 0) * 1000),
            self.modified,
        )


@dataclass(frozen=True)
class DuplicateGroup:
    reason: str
    key: str
    tracks: list[LocalTrack] = field(default_factory=list)
    safe_to_move: bool = False

    @property
    def copies(self) -> list[LocalTrack]:
        if not self.safe_to_move or len(self.tracks) < 2:
            return []
        sorted_tracks = sorted(
            self.tracks,
            key=lambda track: track.quality_score,
            reverse=True,
        )
        return sorted_tracks[1:]

    @property
    def keep(self) -> LocalTrack | None:
        if not self.tracks:
            return None
        return max(self.tracks, key=lambda track: track.quality_score)

    def to_log_lines(self) -> list[str]:
        keep = self.keep
        keep_name = keep.path.name if keep else "unknown"
        action = "move" if self.safe_to_move else "review"
        lines = [f"[bold]{self.reason}[/] [dim]{self.key}[/]"]
        lines.append(f"  [green]keep[/] {keep_name}")
        for track in self.tracks:
            if track is keep:
                continue
            if self.safe_to_move:
                lines.append(f"  [yellow]move[/] {track.path.name}")
            else:
                lines.append(f"  [orange1]{action}[/] {track.path.name}")
        return lines
