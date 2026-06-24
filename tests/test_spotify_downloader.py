from __future__ import annotations

import time

import pytest

from spotify_downloader import SpotifyDownloader


@pytest.fixture()
def app() -> SpotifyDownloader:
    instance = SpotifyDownloader()
    instance._download_start_time = time.monotonic()
    return instance


class TestIsValidUrl:
    VALID_ID = "ABCDEFGHIJKLMNOPQRSTUV"  # 22 chars

    def test_accepts_valid_http_url(self) -> None:
        assert (
            SpotifyDownloader._is_valid_url(
                f"https://open.spotify.com/playlist/{self.VALID_ID}"
            )
            is True
        )

    def test_rejects_short_id(self) -> None:
        assert (
            SpotifyDownloader._is_valid_url("https://open.spotify.com/playlist/short")
            is False
        )

    def test_rejects_invalid_chars(self) -> None:
        assert (
            SpotifyDownloader._is_valid_url(
                "https://open.spotify.com/playlist/!!!invalid!!!"
            )
            is False
        )

    def test_accepts_valid_spotify_uri(self) -> None:
        assert (
            SpotifyDownloader._is_valid_url(f"spotify:playlist:{self.VALID_ID}") is True
        )

    def test_rejects_invalid_uri_id(self) -> None:
        assert SpotifyDownloader._is_valid_url("spotify:playlist:short") is False

    def test_accepts_track_http_url(self) -> None:
        assert (
            SpotifyDownloader._is_valid_url(
                f"https://open.spotify.com/track/{self.VALID_ID}"
            )
            is True
        )

    def test_accepts_track_uri(self) -> None:
        assert SpotifyDownloader._is_valid_url(f"spotify:track:{self.VALID_ID}") is True

    def test_rejects_album_url(self) -> None:
        assert (
            SpotifyDownloader._is_valid_url(
                f"https://open.spotify.com/album/{self.VALID_ID}"
            )
            is False
        )

    def test_empty_string_rejected(self) -> None:
        assert SpotifyDownloader._is_valid_url("") is False

    def test_query_string_stripped(self) -> None:
        assert (
            SpotifyDownloader._is_valid_url(
                f"https://open.spotify.com/playlist/{self.VALID_ID}?si=123"
            )
            is True
        )

    def test_lower_and_upper_case_ids(self) -> None:
        assert (
            SpotifyDownloader._is_valid_url(
                f"https://open.spotify.com/playlist/{self.VALID_ID.lower()}"
            )
            is True
        )


class TestIsValidProxy:
    def test_accepts_http(self) -> None:
        assert SpotifyDownloader._is_valid_proxy("http://proxy:8080") is True

    def test_accepts_https(self) -> None:
        assert SpotifyDownloader._is_valid_proxy("https://proxy:8080") is True

    def test_accepts_socks4(self) -> None:
        assert SpotifyDownloader._is_valid_proxy("socks4://host:1080") is True

    def test_accepts_socks5(self) -> None:
        assert SpotifyDownloader._is_valid_proxy("socks5://host:1080") is True

    def test_rejects_empty(self) -> None:
        assert SpotifyDownloader._is_valid_proxy("") is False

    def test_rejects_ftp(self) -> None:
        assert SpotifyDownloader._is_valid_proxy("ftp://proxy:21") is False

    def test_accepts_authenticated(self) -> None:
        assert SpotifyDownloader._is_valid_proxy("http://user:pass@proxy:8080") is True


class TestFormatElapsed:
    def test_zero_seconds(self) -> None:
        assert SpotifyDownloader._format_elapsed(0.0) == "0s"

    def test_under_minute(self) -> None:
        assert SpotifyDownloader._format_elapsed(45.0) == "45s"

    def test_exactly_one_minute(self) -> None:
        assert SpotifyDownloader._format_elapsed(60.0) == "1m 0s"

    def test_under_hour(self) -> None:
        assert SpotifyDownloader._format_elapsed(125.0) == "2m 5s"

    def test_over_hour(self) -> None:
        assert SpotifyDownloader._format_elapsed(3661.0) == "1h 1m"

    def test_large_hours(self) -> None:
        assert SpotifyDownloader._format_elapsed(7384.0) == "2h 3m"


class TestFormatDownloadStatus:
    def test_zero_done(self, app: SpotifyDownloader) -> None:
        result = app._format_download_status(0, 10)
        assert "0 processed" in result

    def test_one_done_no_rate(self, app: SpotifyDownloader) -> None:
        result = app._format_download_status(1, 10)
        assert "tracks/min" not in result

    def test_two_done_shows_rate(self, app: SpotifyDownloader) -> None:
        app._download_start_time = time.monotonic() - 2.0
        result = app._format_download_status(2, 10)
        assert "tracks/min" in result
        assert "left" in result

    def test_complete_no_eta(self, app: SpotifyDownloader) -> None:
        result = app._format_download_status(10, 10)
        assert "left" not in result

    def test_fractional_progress(self, app: SpotifyDownloader) -> None:
        app._download_start_time = time.monotonic() - 10.0
        result = app._format_download_status(5, 10)
        assert "processed" in result


class TestVersionComparison:
    def test_newer_version_detected(self) -> None:
        assert SpotifyDownloader._version_gt("2.0.0", "1.0.0") is True

    def test_older_version_detected(self) -> None:
        assert SpotifyDownloader._version_gt("0.9.0", "1.0.0") is False

    def test_equal_versions(self) -> None:
        assert SpotifyDownloader._version_gt("1.0.0", "1.0.0") is False

    def test_invalid_input_returns_false(self) -> None:
        assert SpotifyDownloader._version_gt("not_a_version", "1.0.0") is False

    def test_pre_release_comparison(self) -> None:
        assert SpotifyDownloader._version_gt("1.0.0a1", "1.0.0") is False
