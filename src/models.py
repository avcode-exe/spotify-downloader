from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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
        label = "duplicate" if self.safe_to_move else "possible duplicate"
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
