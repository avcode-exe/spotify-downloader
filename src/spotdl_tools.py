from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import sys


_SPOTIFY_ID_RE = re.compile(r"^[A-Za-z0-9]{22}$")
DOWNLOADING_RE = re.compile(r"Downloading\s+(.+)", re.IGNORECASE)
DONE_RE = re.compile(r"(?:Downloaded|✓)\s+(.+)", re.IGNORECASE)
SKIPPED_RE = re.compile(r"Skipping\s+(.+)\s+as it is already downloaded", re.IGNORECASE)
ERROR_RE = re.compile(r"(?:AudioProviderError|Failed to download)", re.IGNORECASE)
FOUND_RE = re.compile(r"Found\s+(\d+)\s+songs?", re.IGNORECASE)


def is_valid_spotify_url(url: str) -> bool:
    if url.startswith("https://open.spotify.com/playlist/"):
        playlist_id = url[len("https://open.spotify.com/playlist/") :].split("?")[0]
        return bool(_SPOTIFY_ID_RE.match(playlist_id))
    if url.startswith("https://open.spotify.com/track/"):
        track_id = url[len("https://open.spotify.com/track/") :].split("?")[0]
        return bool(_SPOTIFY_ID_RE.match(track_id))
    if url.startswith("spotify:playlist:"):
        playlist_id = url[len("spotify:playlist:") :]
        return bool(_SPOTIFY_ID_RE.match(playlist_id))
    if url.startswith("spotify:track:"):
        track_id = url[len("spotify:track:") :]
        return bool(_SPOTIFY_ID_RE.match(track_id))
    return False


def find_spotdl() -> list[str]:
    """Resolve a spotDL command list.

    Prefers a standalone ``spotdl`` executable on PATH; otherwise falls back to
    invoking the module with the current interpreter. Always returns a list --
    the real "is spotDL usable?" check is delegated to :func:`validate_spotdl`.
    """
    spotdl = shutil.which("spotdl") or shutil.which("spotdl.exe")
    if spotdl:
        return [spotdl]
    return [sys.executable, "-m", "spotdl"]


async def validate_spotdl(spotdl_cmd: list[str]) -> bool:
    try:
        proc = await asyncio.create_subprocess_exec(
            *spotdl_cmd,
            "--help",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        return await proc.wait() == 0
    except Exception as exc:
        log = logging.getLogger("spotify_downloader")
        log.error(
            "spotDL validation failed | cmd=%s error=%s", " ".join(spotdl_cmd), exc
        )
        return False


async def _ensure_deno_inner(spotdl_cmd: list[str]) -> bool:
    """Best-effort installation of Deno (used for some age-restricted videos).

    Returns ``True`` when Deno is already available or is installed
    successfully, and ``False`` only when an install attempt fails.
    """
    if shutil.which("deno") or shutil.which("deno.exe"):
        return True
    spotdl_home = os.path.join(os.path.expanduser("~"), ".spotdl")
    for name in ("deno", "deno.exe"):
        if os.path.isfile(os.path.join(spotdl_home, name)):
            return True
    try:
        proc = await asyncio.create_subprocess_exec(
            *spotdl_cmd,
            "--download-deno",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        stdout, _ = await proc.communicate()
        output = stdout.decode("utf-8", errors="replace").strip()
        if proc.returncode == 0:
            return True
        logging.getLogger("spotify_downloader").warning(
            "Deno install failed | exit_code=%d output=%s", proc.returncode, output
        )
        return False
    except Exception as exc:
        logging.getLogger("spotify_downloader").warning(
            "Deno install skipped | error=%s", exc
        )
        return False


async def validate_and_ensure_deno(spotdl_cmd: list[str]) -> tuple[bool, bool]:
    """Validate spotDL and ensure Deno, returning (spotdl_ok, deno_ok).

    Runs both checks in a single event loop to avoid the overhead of
    creating/closing separate loops per call.
    """
    spotdl_ok = await validate_spotdl(spotdl_cmd)
    deno_ok = await _ensure_deno_inner(spotdl_cmd)
    return spotdl_ok, deno_ok


# Backward-compatible alias: tests and other callers that import ensure_deno
# individually still work.
ensure_deno = _ensure_deno_inner


def build_spotdl_args(
    base_cmd: list[str],
    urls: list[str],
    output_folder: str,
    settings: dict[str, str],
    *,
    add_download_op: bool = False,
    overwrite: str | None = None,
    scan_for_songs: bool = False,
    extra_args: list[str] | None = None,
) -> list[str]:
    cmd = list(base_cmd)
    if add_download_op:
        cmd.append("download")

    fmt = settings.get("format", "mp3")
    bitrate = settings.get("bitrate", "auto")
    audio_provider = settings.get("audio_provider", "youtube-music")
    proxy = settings.get("proxy", "").strip()
    cookie_file = settings.get("cookie_file", "").strip()

    cmd.extend(["--format", fmt])
    if bitrate and bitrate != "auto":
        cmd.extend(["--bitrate", bitrate])
    cmd.extend(["--audio", audio_provider])
    if proxy:
        cmd.extend(["--proxy", proxy])
    if cookie_file and os.path.isfile(cookie_file):
        cmd.extend(["--cookie-file", cookie_file])
    if settings.get("use_cache_file", "false").lower() != "false":
        cmd.append("--use-cache-file")
    cmd.extend(["--output", output_folder])
    if overwrite:
        cmd.extend(["--overwrite", overwrite])
    if scan_for_songs:
        cmd.append("--scan-for-songs")
    if extra_args:
        cmd.extend(extra_args)
    cmd.extend(urls)
    return cmd


def is_rate_limit_error(error_text: str) -> bool:
    rate_limit_patterns = (
        "sign in to confirm",
        "sign in to verify",
        "confirm you're not a bot",
        "confirm you are not a bot",
        "http error 403",
        "http error 429",
        "too many requests",
        "please log in",
    )
    text_lower = error_text.lower()
    return any(pat in text_lower for pat in rate_limit_patterns)
