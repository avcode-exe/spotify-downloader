from __future__ import annotations

from pathlib import Path


from src.gui.utils import (
    format_download_status,
    format_elapsed,
    format_track_line,
    safe_path_name,
    strip_ansi,
    summarize_local_scan,
    truncate_text,
)
from src.models import LocalTrack


class TestStripAnsi:
    def test_plain_text(self) -> None:
        assert strip_ansi("hello world") == "hello world"

    def test_removes_color_codes(self) -> None:
        assert strip_ansi("\x1b[31mred\x1b[0m") == "red"

    def test_removes_multiple_codes(self) -> None:
        assert strip_ansi("\x1b[1;31mbold red\x1b[0m normal") == "bold red normal"

    def test_empty_string(self) -> None:
        assert strip_ansi("") == ""


class TestFormatElapsed:
    def test_under_one_minute(self) -> None:
        assert format_elapsed(5.0) == "5s"

    def test_exactly_one_minute(self) -> None:
        assert format_elapsed(60.0) == "1m 0s"

    def test_under_one_hour(self) -> None:
        assert format_elapsed(125.0) == "2m 5s"

    def test_over_one_hour(self) -> None:
        assert format_elapsed(3661.0) == "1h 1m"

    def test_zero(self) -> None:
        assert format_elapsed(0.0) == "0s"


class TestFormatDownloadStatus:
    def test_no_rate_info_below_two_done(self) -> None:
        assert "processed" in format_download_status(0, 10, 0.0)
        assert "processed" in format_download_status(1, 10, 5.0)

    def test_rate_info_after_two_done(self) -> None:
        result = format_download_status(2, 10, 2.0)
        assert "tracks/min" in result

    def test_includes_eta_when_incomplete(self) -> None:
        result = format_download_status(2, 10, 2.0)
        assert "left" in result

    def test_no_eta_when_complete(self) -> None:
        result = format_download_status(10, 10, 5.0)
        assert "left" not in result

    def test_zero_elapsed_no_division(self) -> None:
        result = format_download_status(2, 10, 0.0)
        assert "tracks/min" not in result


class TestSummarizeLocalScan:
    def test_merges_scan_and_state(self, tmp_path: Path) -> None:
        p = tmp_path / "song.mp3"
        p.write_text("fake", encoding="utf-8")
        track = LocalTrack(
            path=p,
            filename="song.mp3",
            normalized_name="song",
            title="Song",
            artist="Artist",
        )
        result = summarize_local_scan([track], [])
        assert result["files"] == 1
        assert result["unique_tracks"] == 1


class TestFormatTrackLine:
    def test_with_artist(self) -> None:
        track = LocalTrack(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
            normalized_name="song",
            title="Song",
            artist="Artist",
        )
        line = format_track_line(track)
        assert "Song" in line
        assert "Artist" in line

    def test_without_artist(self) -> None:
        track = LocalTrack(
            path=Path("/music/song.mp3"),
            filename="song.mp3",
            normalized_name="song",
            title="Song",
        )
        line = format_track_line(track)
        assert "Song" in line
        assert " — " not in line

    def test_falls_back_to_filename(self) -> None:
        track = LocalTrack(
            path=Path("/music/file.mp3"),
            filename="file.mp3",
            normalized_name="song",
        )
        line = format_track_line(track)
        assert "file.mp3" in line


class TestTruncateText:
    def test_short_text_unchanged(self) -> None:
        assert truncate_text("hello", 10) == "hello"

    def test_long_text_truncated(self) -> None:
        assert truncate_text("hello world", 8) == "hello w…"

    def test_exact_length_unchanged(self) -> None:
        assert truncate_text("hello", 5) == "hello"


class TestSafePathName:
    def test_resolves_to_absolute_path(self) -> None:
        result = safe_path_name("relative/path/song.mp3")
        assert result.endswith("relative/path/song.mp3")

    def test_expands_user(self, tmp_path: Path) -> None:
        import os
        os.makedirs(tmp_path / "sub")
        (tmp_path / "sub" / "file.mp3").write_text("x")
        result = safe_path_name(str(tmp_path / "sub" / "file.mp3"))
        assert result.endswith("sub/file.mp3")
