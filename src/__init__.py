"""Spotify Playlist Downloader package.

The single source of truth for the application version is :data:`__version__`.
The Windows installer reads it via :mod:`scripts.write_version_include`, which
emits ``installer/_version.iss`` before ISCC runs. Update this constant in
both this file and let the build regenerate the Inno Setup include.
"""

from __future__ import annotations

__version__ = "0.1.1"

__all__ = ["__version__"]
