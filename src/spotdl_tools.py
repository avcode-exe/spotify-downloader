from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sys


def find_spotdl() -> list[str] | None:
    spotdl = shutil.which("spotdl") or shutil.which("spotdl.exe")
    if spotdl:
        return [spotdl]
    fallback = [sys.executable, "-m", "spotdl"]
    return fallback


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


async def ensure_deno(spotdl_cmd: list[str]) -> bool:
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
        logging.getLogger("spotify_downloader").error(
            "Deno install failed | exit_code=%d output=%s", proc.returncode, output
        )
        return True
    except Exception as exc:
        logging.getLogger("spotify_downloader").error(
            "Deno install exception | error=%s", exc
        )
        return True


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
