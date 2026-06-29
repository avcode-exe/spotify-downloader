from __future__ import annotations

from PySide6.QtGui import QColor, QFont

from src.gui_qt.theme import (
    SPOTIFY_BLACK,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_DISABLED_GRAY,
    SPOTIFY_GREEN,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_WHITE,
    get_button_font,
    get_font,
    get_label_font,
    get_mono_font,
    get_section_font,
    get_subtitle_font,
    get_title_font,
)


class TestThemeConstants:
    def test_all_color_constants_are_qcolor(self) -> None:
        colors = [
            SPOTIFY_GREEN,
            SPOTIFY_BLACK,
            SPOTIFY_DARK_GRAY,
            SPOTIFY_LIGHT_GRAY,
            SPOTIFY_WHITE,
            SPOTIFY_DISABLED_GRAY,
            SPOTIFY_BORDER_COLOR,
        ]
        for color in colors:
            assert isinstance(color, QColor)
            assert color.isValid()

    def test_color_values_match_hex(self) -> None:
        assert SPOTIFY_GREEN.name() == "#1db954"
        assert SPOTIFY_BLACK.name() == "#0a0a0a"
        assert SPOTIFY_WHITE.name() == "#ffffff"
        assert SPOTIFY_BORDER_COLOR.name() == "#333333"

    def test_font_constants_are_qfonts(self) -> None:
        fonts = [
            (get_title_font(), "Segoe UI"),
            (get_subtitle_font(), "Segoe UI"),
            (get_label_font(), "Segoe UI"),
            (get_button_font(), "Segoe UI"),
            (get_section_font(), "Segoe UI"),
            (get_mono_font(), "Cascadia Code"),
        ]
        for font, expected_family in fonts:
            assert isinstance(font, QFont)
            assert font.family() == expected_family

    def test_font_title_bold(self) -> None:
        font = get_title_font()
        assert font.weight() == QFont.Weight.Bold

    def test_font_button_bold(self) -> None:
        font = get_button_font()
        assert font.weight() == QFont.Weight.Bold

    def test_get_font_caches(self) -> None:
        font1 = get_font("Segoe UI", 10, QFont.Weight.Normal, False, "test_cache")
        font2 = get_font("Segoe UI", 10, QFont.Weight.Normal, False, "test_cache")
        assert font1 is font2


class TestFontHelpers:
    def test_get_font_default_family(self) -> None:
        font = get_font()
        assert font.family() == "Segoe UI"

    def test_get_font_custom_family(self) -> None:
        font = get_font("Consolas", 12, QFont.Weight.Bold, True, "custom")
        assert font.family() == "Consolas"
        assert font.pointSize() == 12
        assert font.weight() == QFont.Weight.Bold
        assert font.italic() is True

    def test_get_mono_font(self) -> None:
        font = get_mono_font()
        assert font.family() == "Cascadia Code"
        assert font.pointSize() == 10
