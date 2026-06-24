from __future__ import annotations

from pathlib import Path

import pytest

from src.models import (
    AUDIO_EXTENSIONS,
    DUPLICATE_POLICY_OPTIONS,
    DuplicateGroup,
    LocalTrack,
    TrackStatus,
    redact_proxy,
    redact_settings_for_log,
)


@pytest.fixture()
def track(tmp_path: Path) -> LocalTrack:
    p = tmp_path / "song.mp3"
    p.write_text("fake", encoding="utf-8")
    return LocalTrack(
        path=p,
        filename="song.mp3",
        normalized_name="song",
        title="Song",
        artist="Artist",
        album="Album",
        duration=180.5,
        bitrate=320,
        size=5000,
        modified=1700000000.0,
        tags={"genre": "Rock"},
    )


class TestLocalTrack:
    def test_quality_score_sorting(self, tmp_path: Path) -> None:
        low = LocalTrack(
            path=tmp_path / "low.mp3",
            filename="low.mp3",
            normalized_name="low",
            bitrate=128,
            size=2000,
            duration=180.0,
            modified=1000.0,
        )
        high = LocalTrack(
            path=tmp_path / "high.mp3",
            filename="high.mp3",
            normalized_name="high",
            bitrate=320,
            size=5000,
            duration=200.0,
            modified=2000.0,
        )
        tracks = [low, high]
        assert sorted(tracks, key=lambda t: t.quality_score, reverse=True) == [high, low]

    def test_defaults(self, tmp_path: Path) -> None:
        p = tmp_path / "x.mp3"
        p.write_text("fake", encoding="utf-8")
        track = LocalTrack(path=p, filename="x.mp3", normalized_name="x")
        assert track.title is None
        assert track.artist is None
        assert track.album is None
        assert track.duration is None
        assert track.bitrate is None
        assert track.size == 0
        assert track.modified == 0.0
        assert track.tags == {}


class TestDuplicateGroup:
    def test_copies_returns_lower_quality_tracks(self, tmp_path: Path) -> None:
        keep = LocalTrack(
            path=tmp_path / "keep.mp3",
            filename="keep.mp3",
            normalized_name="song",
            bitrate=320,
            size=5000,
            duration=200.0,
            modified=2000.0,
        )
        copy = LocalTrack(
            path=tmp_path / "copy.mp3",
            filename="copy.mp3",
            normalized_name="song",
            bitrate=128,
            size=2000,
            duration=180.0,
            modified=1000.0,
        )
        group = DuplicateGroup(
            reason="same normalized filename",
            key="song",
            tracks=[keep, copy],
            safe_to_move=True,
        )
        copies = group.copies
        assert len(copies) == 1
        assert copies[0] is copy

    def test_copies_empty_when_unsafe(self, tmp_path: Path) -> None:
        t = LocalTrack(
            path=tmp_path / "a.mp3",
            filename="a.mp3",
            normalized_name="a",
            bitrate=320,
            size=5000,
        )
        group = DuplicateGroup(
            reason="possible metadata title/artist",
            key="a",
            tracks=[t],
            safe_to_move=False,
        )
        assert group.copies == []

    def test_copies_empty_when_single_track(self, tmp_path: Path) -> None:
        t = LocalTrack(
            path=tmp_path / "a.mp3",
            filename="a.mp3",
            normalized_name="a",
            bitrate=320,
            size=5000,
        )
        group = DuplicateGroup(
            reason="same normalized filename",
            key="a",
            tracks=[t],
            safe_to_move=True,
        )
        assert group.copies == []

    def test_keep_returns_best_track(self, tmp_path: Path) -> None:
        t1 = LocalTrack(
            path=tmp_path / "1.mp3",
            filename="1.mp3",
            normalized_name="a",
            bitrate=128,
            size=2000,
            duration=100.0,
            modified=1000.0,
        )
        t2 = LocalTrack(
            path=tmp_path / "2.mp3",
            filename="2.mp3",
            normalized_name="a",
            bitrate=320,
            size=5000,
            duration=200.0,
            modified=2000.0,
        )
        group = DuplicateGroup(
            reason="same normalized filename",
            key="a",
            tracks=[t1, t2],
            safe_to_move=True,
        )
        assert group.keep is t2

    def test_keep_none_when_empty(self) -> None:
        group = DuplicateGroup(reason="x", key="x", tracks=[])
        assert group.keep is None

    def test_to_log_lines(self, tmp_path: Path) -> None:
        keep = LocalTrack(
            path=tmp_path / "keep.mp3",
            filename="keep.mp3",
            normalized_name="song",
            bitrate=320,
            size=5000,
        )
        copy = LocalTrack(
            path=tmp_path / "copy.mp3",
            filename="copy.mp3",
            normalized_name="song",
            bitrate=128,
            size=2000,
        )
        group = DuplicateGroup(
            reason="same normalized filename",
            key="song",
            tracks=[keep, copy],
            safe_to_move=True,
        )
        lines = group.to_log_lines()
        assert len(lines) == 3
        assert "keep" in lines[1]
        assert "move" in lines[2]


class TestConstants:
    def test_audio_extensions(self) -> None:
        assert ".mp3" in AUDIO_EXTENSIONS
        assert ".flac" in AUDIO_EXTENSIONS
        assert ".wav" in AUDIO_EXTENSIONS
        assert ".txt" not in AUDIO_EXTENSIONS

    def test_duplicate_policy_options(self) -> None:
        assert DUPLICATE_POLICY_OPTIONS == [
            ("Skip existing", "skip"),
            ("Update metadata", "metadata"),
        ]


class TestTrackStatus:
    def test_summary_buckets_cover_core_statuses(self) -> None:
        # Guard against drift: every bucket summarize_track_state reports on
        # must be a known status constant.
        for name in ("DOWNLOADED", "SKIPPED", "FAILED", "QUARANTINED", "OTHER"):
            assert getattr(TrackStatus, name) in TrackStatus.SUMMARY_BUCKETS

    def test_values_are_stable_strings(self) -> None:
        # The on-disk JSON contract depends on these exact values.
        assert TrackStatus.DOWNLOADED == "downloaded"
        assert TrackStatus.FAILED == "failed"
        assert TrackStatus.QUARANTINED == "quarantined"


class TestRedaction:
    @pytest.mark.parametrize(
        "proxy,expected",
        [
            ("", ""),
            ("http://host:8080", "http://host:8080"),
            ("socks5://host:1080", "socks5://host:1080"),
            (
                "http://user:secret@host:8080",
                "http://***@host:8080",
            ),
            (
                "socks5://u:p@10.0.0.1:1080",
                "socks5://***@10.0.0.1:1080",
            ),
        ],
    )
    def test_redact_proxy(self, proxy: str, expected: str) -> None:
        assert redact_proxy(proxy) == expected

    def test_redact_settings_for_log_masks_credentials(self) -> None:
        settings = {
            "format": "mp3",
            "proxy": "http://user:secret@host:8080",
            "cookie_file": "/x/cookies.txt",
        }
        out = redact_settings_for_log(settings)
        assert "secret" not in out["proxy"]
        assert out["proxy"] == "http://***@host:8080"
        # non-sensitive fields are untouched
        assert out["format"] == "mp3"
        assert out["cookie_file"] == "/x/cookies.txt"
        # original dict is not mutated
        assert settings["proxy"] == "http://user:secret@host:8080"
