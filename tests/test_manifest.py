from __future__ import annotations

from pathlib import Path

import pytest

from src.manifest import (
    SAFE_MOVE_REASONS,
    group_duplicates,
    normalize_name,
    scan_output_folder,
    summarize_scan,
)
from src.models import DuplicateGroup, LocalTrack


@pytest.fixture()
def fake_track_factory(tmp_path: Path) -> callable:
    def _factory(
        name: str,
        *,
        title: str | None = None,
        artist: str | None = None,
        bitrate: int | None = None,
        size: int = 1000,
        subdir: str = "",
    ) -> LocalTrack:
        base = tmp_path / subdir if subdir else tmp_path
        base.mkdir(parents=True, exist_ok=True)
        path = base / f"{name}.mp3"
        path.write_text("fake", encoding="utf-8")
        return LocalTrack(
            path=path,
            filename=path.name,
            normalized_name=normalize_name(name),
            title=title or name,
            artist=artist,
            bitrate=bitrate,
            size=size,
        )
    return _factory


class TestNormalizeName:
    @pytest.mark.parametrize(
        "input_name,expected",
        [
            ("Hello World", "hello world"),
            ("  Spaces  ", "spaces"),
            ("UPPERCASE", "uppercase"),
            ("Track - Artist", "track - artist"),
            ("", ""),
        ],
    )
    def test_normalize_name(self, input_name: str, expected: str) -> None:
        assert normalize_name(input_name) == expected


class TestScanOutputFolder:
    def test_empty_folder(self, tmp_path: Path) -> None:
        assert scan_output_folder(tmp_path) == []

    def test_nonexistent_folder(self, tmp_path: Path) -> None:
        assert scan_output_folder(tmp_path / "does-not-exist") == []

    def test_scans_audio_files(self, tmp_path: Path) -> None:
        (tmp_path / "song.mp3").write_text("fake", encoding="utf-8")
        (tmp_path / "track.m4a").write_text("fake", encoding="utf-8")
        (tmp_path / "doc.txt").write_text("fake", encoding="utf-8")

        tracks = scan_output_folder(tmp_path)
        assert len(tracks) == 2
        names = {t.filename for t in tracks}
        assert names == {"song.mp3", "track.m4a"}

    def test_skips_duplicates_subfolder(self, tmp_path: Path) -> None:
        dup_dir = tmp_path / "duplicates"
        dup_dir.mkdir()
        (dup_dir / "song.mp3").write_text("fake", encoding="utf-8")
        (tmp_path / "song.mp3").write_text("fake", encoding="utf-8")

        tracks = scan_output_folder(tmp_path)
        assert len(tracks) == 1
        assert tracks[0].path.parent == tmp_path

    def test_tracks_sorted_by_name(self, tmp_path: Path) -> None:
        (tmp_path / "b.mp3").write_text("fake", encoding="utf-8")
        (tmp_path / "a.mp3").write_text("fake", encoding="utf-8")
        tracks = scan_output_folder(tmp_path)
        assert tracks[0].filename == "a.mp3"
        assert tracks[1].filename == "b.mp3"


class TestGroupDuplicates:
    def test_no_duplicates(self, fake_track_factory: callable) -> None:
        tracks = [
            fake_track_factory("song-a"),
            fake_track_factory("song-b"),
        ]
        groups = group_duplicates(tracks)
        assert len(groups) == 0

    def test_same_normalized_filename(self, fake_track_factory: callable) -> None:
        tracks = [
            fake_track_factory("My Song", subdir="a"),
            fake_track_factory("My Song", subdir="b"),
        ]
        groups = group_duplicates(tracks)
        assert len(groups) == 2
        safe_groups = [g for g in groups if g.safe_to_move]
        assert len(safe_groups) == 1
        assert safe_groups[0].reason == "same normalized filename"

    def test_metadata_title_artist_match(self, fake_track_factory: callable) -> None:
        tracks = [
            fake_track_factory("file-a", title="Hello", artist="World", subdir="a"),
            fake_track_factory("file-b", title="Hello", artist="World", subdir="b"),
        ]
        groups = group_duplicates(tracks)
        assert len(groups) == 1
        assert groups[0].reason == "possible metadata title/artist"
        assert groups[0].safe_to_move is False

    def test_mixed_groups_sorted_safe_first(self, fake_track_factory: callable) -> None:
        tracks = [
            fake_track_factory("A Song", title="A Song", artist="X", subdir="a1"),
            fake_track_factory("A Song", title="A Song", artist="X", subdir="a2"),
            fake_track_factory("B Song", title="B Song", artist="Y", subdir="b1"),
            fake_track_factory("B Song", title="B Song", artist="Y", subdir="b2"),
        ]
        groups = group_duplicates(tracks)
        assert len(groups) == 4
        safe_groups = [g for g in groups if g.safe_to_move]
        unsafe_groups = [g for g in groups if not g.safe_to_move]
        assert len(safe_groups) == 2
        assert len(unsafe_groups) == 2
        assert groups[0].safe_to_move is True


class TestSummarizeScan:
    def test_summary_counts(self, fake_track_factory: callable) -> None:
        tracks = [
            fake_track_factory("a", bitrate=320, size=5000),
            fake_track_factory("b", bitrate=128, size=2000),
            fake_track_factory("a", bitrate=192, size=3000),
        ]
        groups = group_duplicates(tracks)
        summary = summarize_scan(tracks, groups)
        assert summary["files"] == 3
        assert summary["duplicate_groups"] == 1
        assert summary["duplicate_copies"] == 1
        assert summary["unique_tracks"] == 2

    def test_no_groups(self, fake_track_factory: callable) -> None:
        tracks = [fake_track_factory("unique")]
        summary = summarize_scan(tracks, [])
        assert summary["duplicate_groups"] == 0
        assert summary["unique_tracks"] == 1
