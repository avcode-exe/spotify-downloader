from __future__ import annotations

import json
import logging
import shutil
from datetime import UTC, datetime
from pathlib import Path

from .manifest import DuplicateGroup

logger = logging.getLogger(__name__)


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def quarantine_duplicate_copies(
    duplicate_groups: list[DuplicateGroup],
    output_folder: str | Path,
) -> tuple[int, Path, list[str]]:
    root = Path(output_folder).expanduser().resolve()
    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    destination = root / "duplicates" / timestamp
    moved: list[dict[str, str]] = []

    for group in duplicate_groups:
        if not group.safe_to_move:
            continue
        for track in group.copies:
            if not track.path.exists():
                continue
            if not destination.exists():
                destination.mkdir(parents=True, exist_ok=True)
            target = _unique_path(destination / track.path.name)
            try:
                shutil.move(str(track.path), str(target))
                moved.append(
                    {
                        "source": str(track.path),
                        "destination": str(target),
                        "normalized_name": track.normalized_name,
                    }
                )
            except OSError as exc:
                logger.warning(
                    "Failed to move duplicate %s -> %s: %s",
                    track.path,
                    target,
                    exc,
                )

    if moved:
        manifest_path = destination / "manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "created_at": datetime.now(UTC).isoformat(),
                    "moved": moved,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    return len(moved), destination, [entry["normalized_name"] for entry in moved]


def format_quarantine_summary(count: int, destination: Path) -> str:
    if count <= 0:
        return "No duplicate copies were moved."
    return f"Moved {count} duplicate copy/copies to {destination}"
