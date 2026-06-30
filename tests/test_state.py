import json
import os
from pathlib import Path

import pytest

from src.state import (
    ensure_data_dir,
    save_json_secure,
    save_track_state,
    summarize_track_state,
    update_paths_from_scan,
    upsert_track_state,
)


@pytest.fixture()
def empty_state() -> list[dict]:
    return []


@pytest.fixture()
def sample_state() -> list[dict]:
    return [
        {
            "key": "track-one",
            "title": "Track One",
            "artist": "Artist A",
            "status": "downloaded",
            "path": "/music/track-one.mp3",
            "source": "spotdl-output",
            "first_seen": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        },
        {
            "key": "track-two",
            "title": "Track Two",
            "status": "failed",
            "source": "spotify-url",
            "error": "Failed to download",
            "first_seen": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        },
        {
            "key": "track-three",
            "title": "Track Three",
            "status": "quarantined",
            "path": "/music/duplicates/20240101/track-three.mp3",
            "source": "duplicate-cleaner",
            "first_seen": "2024-01-01T00:00:00+00:00",
            "updated_at": "2024-01-01T00:00:00+00:00",
        },
    ]


class TestUpsertTrackState:
    def test_insert_new_entry(self, empty_state: list[dict]) -> None:
        upsert_track_state(
            empty_state,
            key="new-track",
            title="New Track",
            artist="New Artist",
            status="downloaded",
            path="/music/new.mp3",
            source="local-scan",
        )
        assert len(empty_state) == 1
        entry = empty_state[0]
        assert entry["key"] == "new-track"
        assert entry["title"] == "New Track"
        assert entry["artist"] == "New Artist"
        assert entry["status"] == "downloaded"
        assert entry["path"] == "/music/new.mp3"
        assert entry["source"] == "local-scan"
        assert "first_seen" in entry
        assert "updated_at" in entry

    def test_update_existing_entry(self, sample_state: list[dict]) -> None:
        original_first_seen = sample_state[0]["first_seen"]
        upsert_track_state(
            sample_state,
            key="track-one",
            title="Track One Updated",
            status="skipped",
            source="spotdl-output",
        )
        assert len(sample_state) == 3
        entry = sample_state[0]
        assert entry["title"] == "Track One Updated"
        assert entry["status"] == "skipped"
        assert entry["source"] == "spotdl-output"
        assert entry["first_seen"] == original_first_seen
        assert entry["updated_at"] != original_first_seen

    def test_empty_key_is_ignored(self, empty_state: list[dict]) -> None:
        upsert_track_state(empty_state, key="   ", title="Noop", status="downloaded")
        assert len(empty_state) == 0

    def test_key_is_normalized_and_case_insensitive(self, empty_state: list[dict]) -> None:
        upsert_track_state(empty_state, key="My-Track", title="Original", status="downloaded")
        upsert_track_state(empty_state, key="my-track", title="Updated", status="skipped")
        assert len(empty_state) == 1
        assert empty_state[0]["title"] == "Updated"
        assert empty_state[0]["status"] == "skipped"

    def test_caps_at_1000_entries(self) -> None:
        state: list[dict] = []
        for i in range(1005):
            upsert_track_state(state, key=f"track-{i}", status="downloaded")
        assert len(state) == 1000
        assert state[0]["key"] == "track-1004"
        assert state[-1]["key"] == "track-5"


class TestSummarizeTrackState:
    def test_empty_state(self) -> None:
        assert summarize_track_state([]) == {
            "downloaded": 0,
            "skipped": 0,
            "failed": 0,
            "quarantined": 0,
            "other": 0,
        }

    def test_mixed_statuses(self, sample_state: list[dict]) -> None:
        summary = summarize_track_state(sample_state)
        assert summary["downloaded"] == 1
        assert summary["failed"] == 1
        assert summary["quarantined"] == 1
        assert summary["skipped"] == 0
        assert summary["other"] == 0

    def test_unknown_status_counts_as_other(self) -> None:
        state = [{"key": "x", "status": "pending"}]
        assert summarize_track_state(state)["other"] == 1


class TestUpdatePathsFromScan:
    def test_updates_downloaded_status(self, empty_state: list[dict]) -> None:
        from pathlib import Path

        track = Path("/music/song.mp3")
        track_obj = type(
            "Track",
            (),
            {"normalized_name": "song", "title": "Song", "artist": "A", "path": track},
        )()
        update_paths_from_scan(empty_state, [track_obj])
        assert len(empty_state) == 1
        assert empty_state[0]["status"] == "downloaded"
        assert empty_state[0]["path"] == str(track)

    def test_preserves_failed_status(self, sample_state: list[dict]) -> None:
        from pathlib import Path

        track = Path("/music/track-two.mp3")
        track_obj = type(
            "Track",
            (),
            {
                "normalized_name": "track-two",
                "title": "Track Two",
                "artist": None,
                "path": track,
            },
        )()
        update_paths_from_scan(sample_state, [track_obj])
        entry = next(e for e in sample_state if e["key"] == "track-two")
        assert entry["status"] == "failed"
        assert entry.get("path") is None

    def test_preserves_quarantined_status(self, sample_state: list[dict]) -> None:
        from pathlib import Path

        track = Path("/music/track-three.mp3")
        track_obj = type(
            "Track",
            (),
            {
                "normalized_name": "track-three",
                "title": "Track Three",
                "artist": None,
                "path": track,
            },
        )()
        update_paths_from_scan(sample_state, [track_obj])
        entry = next(e for e in sample_state if e["key"] == "track-three")
        assert entry["status"] == "quarantined"

    def test_empty_track_list_does_nothing(self, sample_state: list[dict]) -> None:
        update_paths_from_scan(sample_state, [])
        assert len(sample_state) == 3

    def test_inserts_new_entry_when_track_not_found(self, empty_state: list[dict]) -> None:
        track = type(
            "Track",
            (),
            {
                "normalized_name": "new-song",
                "title": "New Song",
                "artist": "A",
                "path": Path("/music/new.mp3"),
            },
        )()
        update_paths_from_scan(empty_state, [track])
        assert len(empty_state) == 1
        assert empty_state[0]["status"] == "downloaded"

    def test_falls_back_to_filename_when_normalized_name_missing(
        self, empty_state: list[dict]
    ) -> None:
        track = type(
            "Track",
            (),
            {
                "filename": "fallback.mp3",
                "title": "Fallback",
                "artist": None,
                "path": Path("/music/fallback.mp3"),
            },
        )()
        update_paths_from_scan(empty_state, [track])
        assert len(empty_state) == 1
        assert empty_state[0]["key"] == "fallback"

    def test_key_matching_is_case_insensitive(self, empty_state: list[dict]) -> None:
        track_path = Path("/music/my.mp3")
        upsert_track_state(empty_state, key="My Song", status="downloaded", title="My Song")
        track = type(
            "Track",
            (),
            {
                "normalized_name": "my song",
                "title": "My Song",
                "artist": "A",
                "path": track_path,
            },
        )()
        update_paths_from_scan(empty_state, [track])
        assert len(empty_state) == 1
        assert empty_state[0]["path"] == str(track_path)


class TestSaveTrackState:
    def test_saves_to_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        state_file = tmp_path / "track_state.json"
        monkeypatch.setattr("src.state.STATE_FILE", str(state_file))
        state: list[dict] = [{"key": "x", "status": "downloaded"}]
        save_track_state(state)
        assert state_file.exists()
        loaded = json.loads(state_file.read_text(encoding="utf-8"))
        assert loaded == state


class TestSecureJsonWrite:
    def test_writes_atomically_and_readably(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        target = tmp_path / "nested" / "data.json"
        save_json_secure(str(target), {"k": "v"})
        assert target.exists()
        assert json.loads(target.read_text(encoding="utf-8")) == {"k": "v"}
        # the temp file must not be left behind
        assert not Path(str(target) + ".tmp").exists()

    def test_overwrites_existing_atomically(self, tmp_path: Path) -> None:
        target = tmp_path / "data.json"
        target.write_text("old", encoding="utf-8")
        save_json_secure(str(target), {"k": "new"})
        assert json.loads(target.read_text(encoding="utf-8")) == {"k": "new"}

    @pytest.mark.skipif(os.name == "nt", reason="POSIX permissions not enforced on Windows")
    def test_restricts_file_permissions_on_posix(self, tmp_path: Path) -> None:
        target = tmp_path / "secret.json"
        save_json_secure(str(target), {"cookie": "x"})
        mode = target.stat().st_mode & 0o777
        assert mode == 0o600

    @pytest.mark.skipif(os.name == "nt", reason="POSIX permissions not enforced on Windows")
    def test_ensure_data_dir_restricts_directory_on_posix(self, tmp_path: Path) -> None:
        nested = tmp_path / "sensitive" / "deeper" / "f.json"
        ensure_data_dir(str(nested))
        mode = nested.parent.stat().st_mode & 0o777
        assert mode == 0o700
