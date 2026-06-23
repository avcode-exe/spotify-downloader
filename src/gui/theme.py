from __future__ import annotations

SPOTIFY_GREEN = "#1DB954"
SPOTIFY_BLACK = "#000000"
SPOTIFY_DARK_GRAY = "#111111"
SPOTIFY_LIGHT_GRAY = "#B3B3B3"
SPOTIFY_WHITE = "#FFFFFF"
SPOTIFY_HOVER_GREEN = "#1ED760"
SPOTIFY_DISABLED_GRAY = "#404040"
SPOTIFY_BORDER_COLOR = "#333333"

FONT_TITLE = ("Segoe UI", 22, "bold")
FONT_SUBTITLE = ("Segoe UI", 12)
FONT_LABEL = ("Segoe UI", 11)
FONT_BUTTON = ("Segoe UI", 11, "bold")
FONT_SECTION = ("Segoe UI", 13, "bold")
FONT_MONO = ("Consolas", 10)


def apply_theme() -> None:
    import customtkinter as ctk

    ctk.set_appearance_mode("dark")


def frame_kwargs() -> dict[str, str | int]:
    return {
        "fg_color": SPOTIFY_DARK_GRAY,
        "corner_radius": 8,
        "border_width": 1,
        "border_color": SPOTIFY_BORDER_COLOR,
    }


def button_kwargs(style: str = "primary") -> dict[str, str | tuple[str, ...] | None]:
    if style == "primary":
        return {
            "fg_color": SPOTIFY_GREEN,
            "hover_color": SPOTIFY_HOVER_GREEN,
            "text_color": SPOTIFY_BLACK,
            "border_color": SPOTIFY_GREEN,
            "border_width": 0,
            "font": FONT_BUTTON,
        }
    if style == "secondary":
        return {
            "fg_color": "transparent",
            "hover_color": SPOTIFY_DARK_GRAY,
            "text_color": SPOTIFY_WHITE,
            "border_color": SPOTIFY_BORDER_COLOR,
            "border_width": 1,
            "font": FONT_BUTTON,
        }
    if style == "danger":
        return {
            "fg_color": "#E91429",
            "hover_color": "#FF1F3A",
            "text_color": SPOTIFY_WHITE,
            "border_color": "#E91429",
            "border_width": 0,
            "font": FONT_BUTTON,
        }
    return {}
