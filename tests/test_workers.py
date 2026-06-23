from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from unittest.mock import ANY, MagicMock, patch

import pytest

from src.gui.workers import (
    DOWNLOADING_RE,
    DONE_RE,
    ERROR_RE,
    FOUND_RE,
    SKIPPED_RE,
    WorkerResult,
    SpotDLWorker,
)
from src.spotdl_tools import build_spotdl_args


@pytest.fixture()
def worker(tmp_path: Path) -> SpotDLWorker:
    settings: dict[str, str] = {
        "format": "mp3",
        "bitrate": "auto",
        "audio_provider": "youtube-music",
        "proxy": "",
        "cookie_file": "",
        "duplicate_policy": "skip",
        "browser": "auto",
    }
    events: list[WorkerResult] = []
    worker = SpotDLWorker(
        settings=settings,
        output_folder=str(tmp_path),
        on_event=events.append,
        tk_root=None,
    )
    worker._track_state = []
    return worker


class TestRegexPatterns:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Downloading  Hello World", "Hello World"),
            ("Downloading  Track - Artist", "Track - Artist"),
        ],
    )
    def test_downloading_re(self, text: str, expected: str) -> None:
        m = DOWNLOADING_RE.search(text)
        assert m is not None
        assert m.group(1) == expected

    @pytest.mark.parametrize(
        "text,expected",
        [
            ("Downloaded  Hello World", "Hello World"),
            ("✓  Hello World", "Hello World"),
        ],
    )
    def test_done_re(self, text: str, expected: str) -> None:
        m = DONE_RE.search(text)
        assert m is not None
        assert m.group(1) == expected

    def test_done_re_ignores_summary_line(self) -> None:
        assert DONE_RE.search("Downloaded %s song.") is not None
        m = DONE_RE.search("Downloaded %s song.")
        assert m is not None

    @pytest.mark.parametrize(
        "text",
        [
            "Skipping  Hello World  as it is already downloaded",
            "Skipping  Track - Artist  as it is already downloaded",
        ],
    )
    def test_skipped_re(self, text: str) -> None:
        m = SKIPPED_RE.search(text)
        assert m is not None
        assert m.group(1).strip() in {"Hello World", "Track - Artist"}

    @pytest.mark.parametrize(
        "text",
        [
            "AudioProviderError: something failed",
            "Failed to download track name",
        ],
    )
    def test_error_re(self, text: str) -> None:
        m = ERROR_RE.search(text)
        assert m is not None

    def test_found_re(self) -> None:
        m = FOUND_RE.search("Found  42  songs")
        assert m is not None
        assert m.group(1) == "42"


class TestWorkerResult:
    def test_create_result(self) -> None:
        r = WorkerResult(kind="log", data={"message": "hi"}, error=None)
        assert r.kind == "log"
        assert r.data == {"message": "hi"}
        assert r.error is None

    def test_default_values(self) -> None:
        r = WorkerResult(kind="status")
        assert r.data is None
        assert r.error is None


class TestSpotDLWorkerInit:
    def test_init_stores_settings(self, worker: SpotDLWorker) -> None:
        assert worker._settings["format"] == "mp3"
        assert worker._cancel_requested is False
        assert worker._failed_tracks == []

    def test_init_with_tk_root(self, tmp_path: Path) -> None:
        root = MagicMock()
        w = SpotDLWorker(
            settings={},
            output_folder=str(tmp_path),
            on_event=lambda r: None,
            tk_root=root,
        )
        assert w._tk_root is root


class TestSpotDLWorkerEmit:
    def test_emit_without_tk_root_calls_directly(self, worker: SpotDLWorker) -> None:
        results: list[WorkerResult] = []
        worker._on_event = results.append
        worker._tk_root = None
        worker._emit("log", {"message": "hello"})
        assert len(results) == 1
        assert results[0].kind == "log"
        assert results[0].data == {"message": "hello"}

    def test_emit_with_tk_root_schedules_on_main_thread(
        self, tmp_path: Path
    ) -> None:
        root = MagicMock()
        root.after = MagicMock()
        results: list[WorkerResult] = []
        w = SpotDLWorker(
            settings={},
            output_folder=str(tmp_path),
            on_event=results.append,
            tk_root=root,
        )
        w._emit("log", {"message": "hello"})
        root.after.assert_called_once_with(0, ANY)
        assert len(results) == 0


class TestSpotDLWorkerRecordFailedTrack:
    def test_extracts_spotify_track_url(self, worker: SpotDLWorker) -> None:
        worker._record_failed_track(
            "Failed to download https://open.spotify.com/track/abc123", "/out"
        )
        assert "https://open.spotify.com/track/abc123" in worker._failed_tracks
        state = worker._track_state
        assert state[0]["key"] == "https://open.spotify.com/track/abc123"
        assert state[0]["status"] == "failed"

    def test_extracts_track_name(self, worker: SpotDLWorker) -> None:
        worker._record_failed_track("Failed to download  My Song", "/out")
        state = worker._track_state
        assert state[0]["key"] == "my song"
        assert state[0]["status"] == "failed"

    def test_no_match_leaves_state_unchanged(self, worker: SpotDLWorker) -> None:
        before = len(worker._track_state)
        worker._record_failed_track("Some random error", "/out")
        assert len(worker._track_state) == before


class TestSpotDLWorkerCancel:
    def test_cancel_sets_flag(self, worker: SpotDLWorker) -> None:
        assert worker._cancel_requested is False
        worker.cancel()
        assert worker._cancel_requested is True
