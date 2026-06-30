from __future__ import annotations

from unittest.mock import MagicMock

from src.gui_qt.workers import SpotDLWorker, WorkerResult


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
    def test_init_stores_settings(self) -> None:
        settings = {"format": "mp3", "bitrate": "auto"}
        worker = SpotDLWorker(settings=settings, output_folder="/out")
        assert worker._settings == settings
        assert worker._output_folder == "/out"
        assert worker._cancel_requested is False
        assert worker._cancelled is False
        assert worker._is_retry is False
        assert worker._url == ""
        assert worker._fresh is False
        assert worker._retry_urls == []
        assert worker._track_state_dirty is False
        assert worker._process is None
        assert worker._log_buffer == []
        assert worker._last_flush == 0.0
        assert worker._last_scan == []
        assert worker._scan_index == {}


class TestSpotDLWorkerStart:
    def test_start_download_sets_state(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        worker.start = MagicMock()  # type: ignore[method-assign]
        worker.start_download("https://example.com", fresh=True)
        assert worker._url == "https://example.com"
        assert worker._fresh is True
        assert worker._is_retry is False
        assert worker._cancel_requested is False
        assert worker._cancelled is False
        assert worker._log_buffer == []
        worker.start.assert_called_once()

    def test_start_retry_sets_state(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        worker.start = MagicMock()  # type: ignore[method-assign]
        worker.start_retry(["url1", "url2"])
        assert worker._retry_urls == ["url1", "url2"]
        assert worker._is_retry is True
        assert worker._cancel_requested is False
        assert worker._cancelled is False
        assert worker._log_buffer == []
        worker.start.assert_called_once()


class TestSpotDLWorkerCancel:
    def test_cancel_sets_flag(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        assert worker._cancel_requested is False
        worker.cancel()
        assert worker._cancel_requested is True

    def test_cancel_when_process_none(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        worker._process = None
        worker.cancel()  # should not raise
        assert worker._cancel_requested is True


class TestSpotDLWorkerEmitLog:
    def test_emit_log_appends_to_buffer(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        worker._last_flush = 1e9  # ensure the flush threshold is not crossed
        worker._emit_log("hello")
        assert "hello" in worker._log_buffer

    def test_emit_log_flushes_after_timeout(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        emitted: list[str] = []
        worker.log_emitted.connect(lambda batch: emitted.append(batch))
        worker._last_flush = 0.0
        worker._emit_log("msg1")
        assert worker._log_buffer == []
        assert len(emitted) == 1
        assert "msg1" in emitted[0]

    def test_flush_logs_clears_buffer(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        worker._log_buffer = ["a", "b"]
        worker._flush_logs()
        assert worker._log_buffer == []


class TestSpotDLWorkerRecordCompletedTrack:
    def test_records_downloaded_track(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        worker._track_state_dirty = False
        worker._scan_index = {}
        worker._record_completed_track("My Song", "downloaded")
        assert worker._track_state_dirty is True
        assert len(worker._track_state) == 1
        entry = worker._track_state[0]
        assert entry["key"] == "my song"
        assert entry["title"] == "My Song"
        assert entry["status"] == "downloaded"

    def test_records_skipped_track(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        worker._record_completed_track("Skip Me", "skipped")
        entry = worker._track_state[0]
        assert entry["status"] == "skipped"

    def test_updates_with_scan_index_match(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        from src.manifest import LocalTrack, normalize_name

        fake_track = LocalTrack(
            path="/tmp/song.mp3",
            filename="song.mp3",
            normalized_name=normalize_name("My Song"),
            title="My Song",
            artist="Artist",
        )
        worker._scan_index = {normalize_name("My Song"): fake_track}
        worker._record_completed_track("My Song", "downloaded")
        entry = worker._track_state[0]
        assert entry["artist"] == "Artist"
        assert entry["path"] == "/tmp/song.mp3"


class TestSpotDLWorkerRecordFailedTrack:
    def test_extracts_spotify_track_url(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        events: list[str] = []
        worker.failed_emitted.connect(lambda url: events.append(url))
        worker._record_failed_track("Failed to download https://open.spotify.com/track/abc123")
        assert events == ["https://open.spotify.com/track/abc123"]
        entry = worker._track_state[0]
        assert entry["key"] == "https://open.spotify.com/track/abc123"
        assert entry["status"] == "failed"

    def test_extracts_track_name(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        events: list[str] = []
        worker.failed_emitted.connect(lambda name: events.append(name))
        worker._record_failed_track("Failed to download  My Song")
        assert events == ["My Song"]
        entry = worker._track_state[0]
        assert entry["key"] == "my song"
        assert entry["status"] == "failed"

    def test_no_match_leaves_state_unchanged(self) -> None:
        worker = SpotDLWorker(settings={}, output_folder="/out")
        before = len(worker._track_state)
        worker._record_failed_track("Some random error")
        assert len(worker._track_state) == before
