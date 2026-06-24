from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

import pytest

from src.duplicates import (
    _unique_path,
    format_quarantine_summary,
    quarantine_duplicate_copies,
)
from src.manifest import DuplicateGroup, LocalTrack, normalize_name


@pytest.fixture()
def output_dir(tmp_path: Path) -> Path:
    return tmp_path / "output"


@pytest.fixture()
def track_factory(tmp_path: Path) -> Callable[..., LocalTrack]:
    def _factory(
        name: str, bitrate: int = 320, size: int = 1000, *, subdir: str = ""
    ) -> LocalTrack:
        base = tmp_path / subdir if subdir else tmp_path
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"{name}.mp3"
        path.write_text("fake", encoding="utf-8")
        return LocalTrack(
            path=path,
            filename=path.name,
            normalized_name=normalize_name(name),
            title=name,
            artist="Artist",
            bitrate=bitrate,
            size=size,
        )

    return _factory


class TestUniquePath:
    def test_returns_same_path_when_not_existing(self, tmp_path: Path) -> None:
        p = tmp_path / "new.mp3"
        assert _unique_path(p) == p

    def test_increments_counter_when_path_exists(self, tmp_path: Path) -> None:
        p1 = tmp_path / "song.mp3"
        p1.write_text("1", encoding="utf-8")
        p2 = _unique_path(p1)
        assert p2 == tmp_path / "song (1).mp3"
        assert not p2.exists()

    def test_multiple_collisions(self, tmp_path: Path) -> None:
        base = tmp_path / "song.mp3"
        base.write_text("1", encoding="utf-8")
        (tmp_path / "song (1).mp3").write_text("2", encoding="utf-8")
        (tmp_path / "song (2).mp3").write_text("3", encoding="utf-8")
        result = _unique_path(base)
        assert result == tmp_path / "song (3).mp3"


class TestQuarantineDuplicateCopies:
    def test_no_groups_returns_zero(self, output_dir: Path) -> None:
        count, dest = quarantine_duplicate_copies([], output_dir)
        assert count == 0
        assert dest.parent == output_dir / "duplicates"

    def test_unsafe_groups_skipped(
        self, output_dir: Path, track_factory: Callable[..., LocalTrack]
    ) -> None:
        unsafe = DuplicateGroup(
            reason="possible metadata title/artist",
            key="song",
            tracks=[track_factory("s1"), track_factory("s2")],
            safe_to_move=False,
        )
        count, dest = quarantine_duplicate_copies([unsafe], output_dir)
        assert count == 0
        assert not dest.exists()

    def test_safe_groups_moved(
        self, output_dir: Path, track_factory: Callable[..., LocalTrack]
    ) -> None:
        t1 = track_factory("a", bitrate=320, size=5000)
        t2 = track_factory("a", bitrate=128, size=2000)
        group = DuplicateGroup(
            reason="same normalized filename",
            key="a",
            tracks=[t1, t2],
            safe_to_move=True,
        )
        count, dest = quarantine_duplicate_copies([group], output_dir)
        assert count == 1
        assert dest.exists()
        assert dest.parent == output_dir / "duplicates"
        assert not t2.path.exists()

    def test_manifest_written(
        self, output_dir: Path, track_factory: Callable[..., LocalTrack]
    ) -> None:
        t1 = track_factory("x", bitrate=320, size=5000)
        t2 = track_factory("x", bitrate=128, size=2000)
        group = DuplicateGroup(
            reason="same normalized filename",
            key="x",
            tracks=[t1, t2],
            safe_to_move=True,
        )
        quarantine_duplicate_copies([group], output_dir)
        manifest_files = list((output_dir / "duplicates").glob("*/manifest.json"))
        assert len(manifest_files) == 1
        manifest = json.loads(manifest_files[0].read_text(encoding="utf-8"))
        assert "created_at" in manifest
        assert len(manifest["moved"]) == 1
        assert manifest["moved"][0]["normalized_name"] == "x"

    def test_missing_source_file_skipped(
        self, output_dir: Path, track_factory: Callable[..., LocalTrack]
    ) -> None:
        t1 = track_factory("gone", bitrate=320, size=5000, subdir="src1")
        t1.path.unlink()
        t2 = track_factory("gone", bitrate=128, size=2000, subdir="src2")
        group = DuplicateGroup(
            reason="same normalized filename",
            key="gone",
            tracks=[t1, t2],
            safe_to_move=True,
        )
        count, _ = quarantine_duplicate_copies([group], output_dir)
        assert count == 1


class TestFormatQuarantineSummary:
    def test_zero_count(self) -> None:
        assert (
            format_quarantine_summary(0, Path("/out"))
            == "No duplicate copies were moved."
        )

    def test_positive_count(self) -> None:
        result = format_quarantine_summary(3, Path("/out/duplicates"))
        assert "3" in result
        assert str(Path("/out/duplicates")) in result
