from __future__ import annotations

# ── Color Palette ──────────────────────────────────────────────────────────────
# Refined dark theme with richer depth, softer contrast, and a modern feel.

SPOTIFY_GREEN = "#1DB954"
SPOTIFY_GREEN_LIGHT = "#1ED760"
SPOTIFY_GREEN_DARK = "#1AA34A"

SPOTIFY_BLACK = "#0A0A0A"
SPOTIFY_SURFACE = "#121212"
SPOTIFY_CARD = "#181818"
SPOTIFY_DARK_GRAY = "#1A1A1A"
SPOTIFY_MID_GRAY = "#282828"
SPOTIFY_BORDER_COLOR = "#333333"
SPOTIFY_LIGHT_GRAY = "#B3B3B3"
SPOTIFY_TEXT_SECONDARY = "#A0A0A0"
SPOTIFY_TEXT_MUTED = "#6A6A6A"
SPOTIFY_WHITE = "#FFFFFF"

SPOTIFY_DISABLED_GRAY = "#404040"
SPOTIFY_DISABLED_TEXT = "#555555"

# Semantic accent colors
SPOTIFY_SUCCESS = "#1DB954"
SPOTIFY_ERROR = "#E91429"
SPOTIFY_ERROR_LIGHT = "#FF1F3A"
SPOTIFY_WARNING = "#F59E0B"
SPOTIFY_INFO = "#3B82F6"

# ── Typography ─────────────────────────────────────────────────────────────────
# Modern, clean type scale with consistent sizing.

FONT_TITLE = ("Segoe UI", 20, "bold")
FONT_HEADING = ("Segoe UI", 15, "bold")
FONT_SUBTITLE = ("Segoe UI", 11)
FONT_LABEL = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 11, "bold")
FONT_SECTION = ("Segoe UI", 13, "bold")
FONT_MONO = ("Cascadia Code", 10)
FONT_MONO_FALLBACK = ("Consolas", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_CAPTION = ("Segoe UI", 9, "italic")

# ── Spacing & Sizing ───────────────────────────────────────────────────────────
PAD_X = 20
PAD_Y = 20
PAD_CARD_INNER = 16
GAP_CARD_INNER = 16
GAP_ROW = 10
GAP_SECTION = 20
GAP_ACTION = 12
BORDER_RADIUS = 10
BORDER_RADIUS_SM = 6
PROGRESS_HEIGHT = 6
INPUT_HEIGHT = 40
BUTTON_HEIGHT = 42
BUTTON_WIDTH_PRIMARY = 140
BUTTON_WIDTH_SECONDARY = 120


def apply_theme() -> None:
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")


def frame_kwargs(
    cornerRadius: int | None = None, borderWidth: int | None = None
) -> dict[str, object]:
    return {
        "fg_color": SPOTIFY_CARD,
        "corner_radius": cornerRadius if cornerRadius is not None else BORDER_RADIUS,
        "border_width": borderWidth if borderWidth is not None else 1,
        "border_color": SPOTIFY_BORDER_COLOR,
    }


def button_kwargs(style: str = "primary") -> dict[str, object]:
    if style == "primary":
        return {
            "fg_color": SPOTIFY_GREEN,
            "hover_color": SPOTIFY_GREEN_LIGHT,
            "text_color": SPOTIFY_BLACK,
            "border_color": SPOTIFY_GREEN,
            "border_width": 0,
            "font": FONT_BUTTON,
            "height": BUTTON_HEIGHT,
            "corner_radius": BORDER_RADIUS_SM,
        }
    if style == "secondary":
        return {
            "fg_color": SPOTIFY_MID_GRAY,
            "hover_color": SPOTIFY_DARK_GRAY,
            "text_color": SPOTIFY_WHITE,
            "border_color": SPOTIFY_BORDER_COLOR,
            "border_width": 1,
            "font": FONT_BUTTON,
            "height": BUTTON_HEIGHT,
            "corner_radius": BORDER_RADIUS_SM,
        }
    if style == "ghost":
        return {
            "fg_color": "transparent",
            "hover_color": SPOTIFY_MID_GRAY,
            "text_color": SPOTIFY_LIGHT_GRAY,
            "border_color": SPOTIFY_MID_GRAY,
            "border_width": 1,
            "font": FONT_BUTTON,
            "height": BUTTON_HEIGHT,
            "corner_radius": BORDER_RADIUS_SM,
        }
    if style == "danger":
        return {
            "fg_color": SPOTIFY_ERROR,
            "hover_color": SPOTIFY_ERROR_LIGHT,
            "text_color": SPOTIFY_WHITE,
            "border_color": SPOTIFY_ERROR,
            "border_width": 0,
            "font": FONT_BUTTON,
            "height": BUTTON_HEIGHT,
            "corner_radius": BORDER_RADIUS_SM,
        }
    if style == "success":
        return {
            "fg_color": SPOTIFY_SUCCESS,
            "hover_color": SPOTIFY_GREEN_LIGHT,
            "text_color": SPOTIFY_BLACK,
            "border_color": SPOTIFY_SUCCESS,
            "border_width": 0,
            "font": FONT_BUTTON,
            "height": BUTTON_HEIGHT,
            "corner_radius": BORDER_RADIUS_SM,
        }
    return {}


def entry_kwargs() -> dict[str, object]:
    return {
        "height": INPUT_HEIGHT,
        "corner_radius": BORDER_RADIUS_SM,
        "font": FONT_LABEL,
        "fg_color": SPOTIFY_MID_GRAY,
        "border_color": SPOTIFY_BORDER_COLOR,
        "border_width": 1,
        "text_color": SPOTIFY_WHITE,
        "placeholder_text_color": SPOTIFY_TEXT_MUTED,
    }


def textbox_kwargs() -> dict[str, object]:
    return {
        "font": FONT_LABEL,
        "text_color": SPOTIFY_WHITE,
        "fg_color": SPOTIFY_DARK_GRAY,
        "border_width": 1,
        "border_color": SPOTIFY_BORDER_COLOR,
        "corner_radius": BORDER_RADIUS_SM,
    }


def label_kwargs(
    color: str | None = None, font: tuple | None = None
) -> dict[str, object]:
    kw: dict[str, object] = {}
    if color:
        kw["text_color"] = color
    if font:
        kw["font"] = font
    return kw
