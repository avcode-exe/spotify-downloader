from __future__ import annotations

from PySide6.QtGui import QColor, QFont

# ── Color Palette ──────────────────────────────────────────────────────────────

SPOTIFY_GREEN = QColor("#1DB954")
SPOTIFY_GREEN_LIGHT = QColor("#1ED760")
SPOTIFY_GREEN_DARK = QColor("#1AA34A")

SPOTIFY_BLACK = QColor("#0A0A0A")
SPOTIFY_SURFACE = QColor("#121212")
SPOTIFY_CARD = QColor("#181818")
SPOTIFY_DARK_GRAY = QColor("#1A1A1A")
SPOTIFY_MID_GRAY = QColor("#282828")
SPOTIFY_BORDER_COLOR = QColor("#333333")
SPOTIFY_LIGHT_GRAY = QColor("#B3B3B3")
SPOTIFY_TEXT_SECONDARY = QColor("#A0A0A0")
SPOTIFY_TEXT_MUTED = QColor("#6A6A6A")
SPOTIFY_WHITE = QColor("#FFFFFF")

SPOTIFY_DISABLED_GRAY = QColor("#404040")
SPOTIFY_DISABLED_TEXT = QColor("#555555")

# Semantic accent colors
SPOTIFY_SUCCESS = QColor("#1DB954")
SPOTIFY_ERROR = QColor("#E91429")
SPOTIFY_ERROR_LIGHT = QColor("#FF1F3A")
SPOTIFY_WARNING = QColor("#F59E0B")
SPOTIFY_INFO = QColor("#3B82F6")

# ── Font Helpers ───────────────────────────────────────────────────────────────

_FONT_CACHE: dict[str, QFont] = {}


def get_font(
    family: str = "Segoe UI",
    size: int = 10,
    weight: QFont.Weight = QFont.Weight.Normal,
    italic: bool = False,
    cache_key: str | None = None,
) -> QFont:
    key = cache_key or f"{family}:{size}:{weight.value}:{italic}"
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = QFont(family, size, weight, italic)
    return _FONT_CACHE[key]


def get_title_font() -> QFont:
    return get_font("Segoe UI", 20, QFont.Weight.Bold)


def get_heading_font() -> QFont:
    return get_font("Segoe UI", 15, QFont.Weight.Bold)


def get_subtitle_font() -> QFont:
    return get_font("Segoe UI", 11)


def get_label_font() -> QFont:
    return get_font("Segoe UI", 11)


def get_button_font() -> QFont:
    return get_font("Segoe UI", 11, QFont.Weight.Bold)


def get_section_font() -> QFont:
    return get_font("Segoe UI", 13, QFont.Weight.Bold)


def get_mono_font() -> QFont:
    return get_font("Cascadia Code", 10)


def get_small_font() -> QFont:
    return get_font("Segoe UI", 9)


def get_caption_font() -> QFont:
    font = get_font("Segoe UI", 9)
    font.setItalic(True)
    return font
