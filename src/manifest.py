from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from typing import Any, cast

from .models import AUDIO_EXTENSIONS, DuplicateGroup, LocalTrack

_METADATA_CACHE: dict[Path, tuple[float, int, dict[str, Any]]] = {}

SAFE_MOVE_REASONS = {"same normalized filename"}


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value or "")
    normalized = re.sub(r"\s+", " ", normalized).strip().lower()
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _first_audio_value(audio: object, key: str) -> str | None:
    try:
        value = audio.get(key)  # type: ignore[attr-defined]
    except Exception:
        return None
    if isinstance(value, list):
        return str(value[0]).strip() if value else None
    if value:
        return str(value).strip()
    return None


def _read_audio_metadata(path: Path) -> dict[str, object]:
    try:
        stat = path.stat()
        mtime = stat.st_mtime
        size = stat.st_size
    except OSError:
        return {}

    cached = _METADATA_CACHE.get(path)
    if cached is not None and cached[0] == mtime and cached[1] == size:
        return cached[2]

    try:
        import mutagen

        audio = mutagen.File(str(path), easy=True)
    except Exception:
        audio = None

    metadata: dict[str, object] = {}
    if audio is not None:
        info = getattr(audio, "info", None)
        if info is not None:
            metadata["duration"] = getattr(info, "length", None)
            metadata["bitrate"] = getattr(info, "bitrate", None)
        metadata["title"] = _first_audio_value(audio, "title")
        metadata["artist"] = _first_audio_value(audio, "artist")
        metadata["album"] = _first_audio_value(audio, "album")
        metadata["albumartist"] = _first_audio_value(audio, "albumartist")
        metadata["genre"] = _first_audio_value(audio, "genre")
        metadata["date"] = _first_audio_value(audio, "date")
    _METADATA_CACHE[path] = (mtime, size, metadata)
    return metadata


def scan_output_folder(output_folder: str | Path) -> list[LocalTrack]:
    root = Path(output_folder).expanduser().resolve()
    if not root.exists():
        return []

    tracks: list[LocalTrack] = []
    for path in root.rglob("*"):
        if "duplicates" in path.relative_to(root).parts:
            continue
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        stat = path.stat()
        metadata = _read_audio_metadata(path)
        stem = path.stem
        tracks.append(
            LocalTrack(
                path=path,
                filename=path.name,
                normalized_name=normalize_name(stem),
                title=cast(str | None, metadata.get("title")),
                artist=cast(str | None, metadata.get("artist")),
                album=cast(str | None, metadata.get("album")),
                duration=cast(float | None, metadata.get("duration")),
                bitrate=cast(int | None, metadata.get("bitrate")),
                size=stat.st_size,
                modified=stat.st_mtime,
                tags={
                    key: value
                    for key, value in metadata.items()
                    if key not in {"duration", "bitrate"} and value is not None
                },
            )
        )
    tracks.sort(key=lambda track: track.path.name.lower())
    return tracks


def _add_group(
    groups: dict[tuple[str, str], list[LocalTrack]],
    reason: str,
    key: str,
    track: LocalTrack,
) -> None:
    if not key:
        return
    groups.setdefault((reason, key), []).append(track)


def group_duplicates(tracks: list[LocalTrack]) -> list[DuplicateGroup]:
    grouped: dict[tuple[str, str], list[LocalTrack]] = {}
    for track in tracks:
        _add_group(grouped, "same normalized filename", track.normalized_name, track)
        if track.title and track.artist:
            _add_group(
                grouped,
                "possible metadata title/artist",
                normalize_name(f"{track.title} - {track.artist}"),
                track,
            )
        elif track.title:
            _add_group(
                grouped, "possible metadata title", normalize_name(track.title), track
            )

    duplicate_groups: list[DuplicateGroup] = []
    for (reason, key), group_tracks in grouped.items():
        if len(group_tracks) < 2:
            continue
        duplicate_groups.append(
            DuplicateGroup(
                reason=reason,
                key=key,
                tracks=group_tracks,
                safe_to_move=reason in SAFE_MOVE_REASONS,
            )
        )
    duplicate_groups.sort(
        key=lambda group: (not group.safe_to_move, group.reason, group.key.lower())
    )
    return duplicate_groups


def summarize_scan(
    tracks: list[LocalTrack], duplicate_groups: list[DuplicateGroup]
) -> dict[str, int]:
    safe_copy_paths = {
        track.path for group in duplicate_groups for track in group.copies
    }
    possible_copies = 0
    for group in duplicate_groups:
        if not group.safe_to_move and len(group.tracks) >= 2:
            possible_copies += len(group.tracks) - 1
    return {
        "files": len(tracks),
        "duplicate_groups": sum(1 for group in duplicate_groups if group.safe_to_move),
        "duplicate_copies": len(safe_copy_paths),
        "possible_duplicate_groups": sum(
            1 for group in duplicate_groups if not group.safe_to_move
        ),
        "possible_duplicate_copies": possible_copies,
        "unique_tracks": max(len(tracks) - len(safe_copy_paths), 0),
    }
