from __future__ import annotations


from src.gui.theme import (
    FONT_BUTTON,
    FONT_LABEL,
    FONT_MONO,
    FONT_SECTION,
    FONT_SUBTITLE,
    FONT_TITLE,
    SPOTIFY_BLACK,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_DISABLED_GRAY,
    SPOTIFY_GREEN,
    SPOTIFY_HOVER_GREEN,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_WHITE,
    apply_theme,
    button_kwargs,
    frame_kwargs,
)


class TestThemeConstants:
    def test_all_color_constants_are_hex(self) -> None:
        colors = [
            SPOTIFY_GREEN,
            SPOTIFY_BLACK,
            SPOTIFY_DARK_GRAY,
            SPOTIFY_LIGHT_GRAY,
            SPOTIFY_WHITE,
            SPOTIFY_HOVER_GREEN,
            SPOTIFY_DISABLED_GRAY,
            SPOTIFY_BORDER_COLOR,
        ]
        for color in colors:
            assert color.startswith("#")
            assert len(color) in (7, 4)

    def test_font_constants_are_tuples(self) -> None:
        for font in (
            FONT_TITLE,
            FONT_SUBTITLE,
            FONT_LABEL,
            FONT_BUTTON,
            FONT_SECTION,
            FONT_MONO,
        ):
            assert isinstance(font, tuple)
            assert len(font) >= 2

    def test_font_title_bold(self) -> None:
        assert FONT_TITLE[2] == "bold"

    def test_font_button_bold(self) -> None:
        assert FONT_BUTTON[2] == "bold"


class TestFrameKwargs:
    def test_returns_dict(self) -> None:
        result = frame_kwargs()
        assert isinstance(result, dict)

    def test_expected_keys(self) -> None:
        result = frame_kwargs()
        assert "fg_color" in result
        assert "corner_radius" in result
        assert "border_width" in result
        assert "border_color" in result

    def test_corner_radius_is_int(self) -> None:
        assert isinstance(frame_kwargs()["corner_radius"], int)

    def test_border_width_is_int(self) -> None:
        assert isinstance(frame_kwargs()["border_width"], int)


class TestButtonKwargs:
    def test_primary_style(self) -> None:
        result = button_kwargs("primary")
        assert result["fg_color"] == SPOTIFY_GREEN
        assert result["text_color"] == SPOTIFY_BLACK
        assert result["border_width"] == 0
        assert result["font"] == FONT_BUTTON

    def test_secondary_style(self) -> None:
        result = button_kwargs("secondary")
        assert result["fg_color"] == "transparent"
        assert result["text_color"] == SPOTIFY_WHITE
        assert result["border_width"] == 1
        assert result["font"] == FONT_BUTTON

    def test_danger_style(self) -> None:
        result = button_kwargs("danger")
        assert result["fg_color"] == "#E91429"
        assert result["text_color"] == SPOTIFY_WHITE
        assert result["border_width"] == 0

    def test_unknown_style_returns_empty(self) -> None:
        assert button_kwargs("unknown") == {}


class TestApplyTheme:
    def test_apply_theme_runs_without_error(self) -> None:
        apply_theme()
