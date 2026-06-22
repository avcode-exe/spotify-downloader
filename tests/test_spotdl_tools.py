from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from src.spotdl_tools import (
    build_spotdl_args,
    ensure_deno,
    find_spotdl,
    is_rate_limit_error,
)


class TestFindSpotdl:
    def test_returns_command_when_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/spotdl")
        result = find_spotdl()
        assert result == ["/usr/bin/spotdl"]

    def test_returns_fallback_when_not_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("shutil.which", lambda name: None)
        result = find_spotdl()
        assert result == [sys.executable, "-m", "spotdl"]


class TestIsRateLimitError:
    @pytest.mark.parametrize(
        "text",
        [
            "HTTP error 403: Forbidden",
            "HTTP error 429: Too Many Requests",
            "Sign in to confirm you're not a bot",
            "Sign in to verify your identity",
            "Confirm you're not a bot",
            "Confirm you are not a bot",
            "Too many requests",
            "Please log in",
        ],
    )
    def test_detects_rate_limit_patterns(self, text: str) -> None:
        assert is_rate_limit_error(text) is True

    @pytest.mark.parametrize(
        "text",
        [
            "Download complete",
            "Network timeout",
            "File not found",
            "",
        ],
    )
    def test_returns_false_for_non_rate_limit(self, text: str) -> None:
        assert is_rate_limit_error(text) is False


class TestBuildSpotdlArgs:
    def test_basic_args(self) -> None:
        cmd = build_spotdl_args(
            ["spotdl"], ["https://open.spotify.com/playlist/123"], "/downloads", {}
        )
        assert cmd == [
            "spotdl",
            "--format", "mp3",
            "--audio", "youtube-music",
            "--output", "/downloads",
            "https://open.spotify.com/playlist/123",
        ]

    def test_all_options(self, tmp_path: Path) -> None:
        cookie_file = tmp_path / "cookies.txt"
        cookie_file.write_text("cookies", encoding="utf-8")
        settings = {
            "format": "flac",
            "bitrate": "320k",
            "audio_provider": "youtube",
            "proxy": "http://proxy:8080",
            "cookie_file": str(cookie_file),
        }
        cmd = build_spotdl_args(
            ["spotdl"],
            ["url1", "url2"],
            str(tmp_path),
            settings,
            add_download_op=True,
            overwrite="force",
            scan_for_songs=True,
            extra_args=["--threads", "4"],
        )
        assert "download" in cmd
        assert "--format" in cmd
        assert "flac" in cmd
        assert "--bitrate" in cmd
        assert "320k" in cmd
        assert "--audio" in cmd
        assert "youtube" in cmd
        assert "--proxy" in cmd
        assert "http://proxy:8080" in cmd
        assert "--cookie-file" in cmd
        assert "--output" in cmd
        assert str(tmp_path) in cmd
        assert "--overwrite" in cmd
        assert "force" in cmd
        assert "--scan-for-songs" in cmd
        assert "--threads" in cmd
        assert "4" in cmd
        assert "url1" in cmd
        assert "url2" in cmd

    def test_missing_cookie_file_is_skipped(self, tmp_path: Path) -> None:
        settings = {"cookie_file": str(tmp_path / "nonexistent.txt")}
        cmd = build_spotdl_args(["spotdl"], ["url"], str(tmp_path), settings)
        assert "--cookie-file" not in cmd

    def test_bitrate_auto_skipped(self) -> None:
        settings = {"bitrate": "auto"}
        cmd = build_spotdl_args(["spotdl"], ["url"], "/out", settings)
        assert "--bitrate" not in cmd

    def test_empty_proxy_skipped(self) -> None:
        settings = {"proxy": ""}
        cmd = build_spotdl_args(["spotdl"], ["url"], "/out", settings)
        assert "--proxy" not in cmd


class TestEnsureDeno:
    def test_returns_true_when_deno_on_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("shutil.which", lambda name: "/usr/bin/deno")
        assert asyncio.run(ensure_deno(["spotdl"])) is True

    def test_returns_true_when_deno_in_spotdl_home(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spotdl_home = tmp_path / ".spotdl"
        spotdl_home.mkdir()
        deno_path = spotdl_home / "deno"
        deno_path.write_text("", encoding="utf-8")
        monkeypatch.setattr("shutil.which", lambda name: None)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.setattr("os.path.expanduser", lambda path: str(tmp_path) if path == "~" else path)
        assert asyncio.run(ensure_deno(["spotdl"])) is True

    def test_returns_true_on_install_failure(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spotdl_home = tmp_path / ".spotdl"
        spotdl_home.mkdir()
        monkeypatch.setattr("shutil.which", lambda name: None)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.setattr("os.path.expanduser", lambda path: str(tmp_path) if path == "~" else path)

        async def fake_create_subprocess_exec(*args: str, **kwargs: Any) -> _FakeProc:
            return _FakeProc(returncode=1, stdout=b"")

        with patch("asyncio.create_subprocess_exec", side_effect=fake_create_subprocess_exec):
            assert asyncio.run(ensure_deno(["spotdl"])) is True

    def test_returns_true_on_exception(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        spotdl_home = tmp_path / ".spotdl"
        spotdl_home.mkdir()
        monkeypatch.setattr("shutil.which", lambda name: None)
        monkeypatch.setenv("HOME", str(tmp_path))
        monkeypatch.setenv("USERPROFILE", str(tmp_path))
        monkeypatch.setattr("os.path.expanduser", lambda path: str(tmp_path) if path == "~" else path)

        async def failing_create_subprocess_exec(*args: str, **kwargs: Any) -> None:
            raise OSError("permission denied")

        with patch("asyncio.create_subprocess_exec", side_effect=failing_create_subprocess_exec):
            assert asyncio.run(ensure_deno(["spotdl"])) is True


class _FakeProc:
    def __init__(self, returncode: int, stdout: bytes) -> None:
        self.returncode = returncode
        self.stdout = _FakeStream(stdout)
        self.stderr = _FakeStream(b"")

    async def communicate(self) -> tuple[bytes, bytes]:
        return self.stdout.read(), self.stderr.read()

    async def wait(self) -> int:
        return self.returncode


class _FakeStream:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._index = 0

    async def readline(self) -> bytes:
        if self._index >= len(self._data):
            return b""
        chunk = self._data[self._index : self._index + 1]
        self._index += 1
        return chunk

    def read(self) -> bytes:
        return self._data
