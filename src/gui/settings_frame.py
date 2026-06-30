from __future__ import annotations

from collections.abc import Callable, Sequence

import customtkinter as ctk

from src.models import DUPLICATE_POLICY_OPTIONS
from src.state import STATE_FILE

from .theme import (
    FONT_BUTTON,
    FONT_CAPTION,
    FONT_LABEL,
    FONT_SECTION,
    GAP_ACTION,
    GAP_CARD_INNER,
    GAP_ROW,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_DISABLED_TEXT,
    SPOTIFY_GREEN,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_MID_GRAY,
    SPOTIFY_TEXT_MUTED,
    SPOTIFY_WHITE,
    frame_kwargs,
)

BROWSER_OPTIONS: list[tuple[str, str]] = [
    ("Auto (try all)", "auto"),
    ("Chrome", "chrome"),
    ("Firefox", "firefox"),
    ("Edge", "edge"),
    ("Brave", "brave"),
    ("Vivaldi", "vivaldi"),
]

_DUPLICATE_POLICY_MAP = {code: label for label, code in DUPLICATE_POLICY_OPTIONS}


class SettingsFrame(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(
        self,
        master: ctk.CTk,
        settings: dict[str, str],
        on_change: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        super().__init__(master, **frame_kwargs())
        self._settings = dict(settings)
        self._on_change = on_change
        self._loading = True
        self._value_maps: dict[str, dict[str, str]] = {}
        self._build_ui()
        self._loading = False

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=GAP_CARD_INNER, pady=GAP_CARD_INNER)

        # Title with accent
        title = ctk.CTkLabel(
            inner,
            text="Settings",
            font=FONT_SECTION,
            text_color=SPOTIFY_GREEN,
        )
        title.pack(anchor="w", pady=(0, GAP_ACTION))

        self._format_var = ctk.StringVar(value=self._settings.get("format", "mp3"))
        self._bitrate_var = ctk.StringVar(value=self._settings.get("bitrate", "auto"))
        self._provider_var = ctk.StringVar(
            value=self._settings.get("audio_provider", "youtube-music")
        )
        self._policy_var = ctk.StringVar(value=self._settings.get("duplicate_policy", "skip"))
        self._proxy_var = ctk.StringVar(value=self._settings.get("proxy", ""))
        self._cookie_file_var = ctk.StringVar(value=self._settings.get("cookie_file", ""))
        self._browser_var = ctk.StringVar(value=self._settings.get("browser", "auto"))

        format_options = ["mp3", "m4a", "flac", "opus", "ogg", "wav"]
        bitrate_options = [
            "auto",
            "disable",
            "64k",
            "96k",
            "128k",
            "160k",
            "192k",
            "256k",
            "320k",
        ]
        provider_options = [
            "youtube-music",
            "youtube",
            "soundcloud",
            "bandcamp",
            "piped",
        ]
        policy_options = [option[1] for option in DUPLICATE_POLICY_OPTIONS]

        self._add_select_row(inner, "Format", self._format_var, format_options)
        self._add_select_row(inner, "Bitrate", self._bitrate_var, bitrate_options)
        self._add_select_row(inner, "Audio source", self._provider_var, provider_options)
        self._add_select_row(inner, "Duplicate policy", self._policy_var, policy_options)
        self._add_select_row(inner, "Browser", self._browser_var, BROWSER_OPTIONS)
        self._add_entry_row(inner, "Proxy", self._proxy_var)
        self._add_entry_row(inner, "Cookie file", self._cookie_file_var)

        # Browse button for cookie file
        params = {
            "fg_color": "transparent",
            "hover_color": SPOTIFY_MID_GRAY,
            "text_color": SPOTIFY_WHITE,
            "border_color": SPOTIFY_BORDER_COLOR,
            "border_width": 1,
            "font": FONT_BUTTON,
            "height": 36,
            "corner_radius": 6,
        }
        browse_btn = ctk.CTkButton(
            inner, text="Browse\u2026", command=self._browse_cookie_file, **params
        )
        browse_btn.pack(fill="x", pady=(0, GAP_ACTION))

        # Divider
        divider = ctk.CTkFrame(inner, fg_color=SPOTIFY_BORDER_COLOR, height=1)
        divider.pack(fill="x", pady=(GAP_ACTION, GAP_ACTION))
        divider.pack()

        # Active settings summary
        status = self._status_text()
        self._status_var = ctk.StringVar(value=status)
        status_label = ctk.CTkLabel(
            inner,
            textvariable=self._status_var,
            font=FONT_LABEL,
            text_color=SPOTIFY_TEXT_MUTED,
            wraplength=400,
            anchor="w",
            justify="left",
        )
        status_label.pack(fill="x", pady=(GAP_ACTION, GAP_ACTION))

        # State file info
        state_label = ctk.CTkLabel(
            inner,
            text=f"State: {STATE_FILE}",
            font=FONT_CAPTION,
            text_color=SPOTIFY_DISABLED_TEXT,
            anchor="w",
            wraplength=400,
            justify="left",
        )
        state_label.pack(fill="x", pady=(0, 0))

    def _add_select_row(
        self,
        parent: ctk.CTkFrame,
        label: str,
        variable: ctk.StringVar,
        options: Sequence[str | tuple[str, str]],
    ) -> None:
        if options and isinstance(options[0], tuple):
            display_options = [opt[0] for opt in options]
            value_to_display = {opt[1]: opt[0] for opt in options}
            display_to_value = {opt[0]: opt[1] for opt in options}
        else:
            display_options = [str(opt) for opt in options]
            value_to_display = {str(opt): str(opt) for opt in options}
            display_to_value = {str(opt): str(opt) for opt in options}

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, GAP_ROW))

        label_widget = ctk.CTkLabel(
            row,
            text=label,
            font=FONT_LABEL,
            text_color=SPOTIFY_LIGHT_GRAY,
            width=90,
            anchor="w",
        )
        label_widget.pack(side="left", padx=(0, 12))

        current_value = variable.get()
        resolved_value = value_to_display.get(current_value, current_value)
        variable.set(resolved_value)

        var_name = variable._name.lstrip("!").removesuffix("_var")
        self._value_maps[var_name] = display_to_value

        def _make_callback(vm: dict[str, str], var: ctk.StringVar) -> Callable[[str], None]:
            def _callback(selected: str) -> None:
                internal = vm.get(selected, selected)
                var.set(internal)
                self._on_setting_changed(internal)

            return _callback

        option = ctk.CTkOptionMenu(
            row,
            variable=variable,
            values=display_options,
            command=_make_callback(display_to_value, variable),
            height=36,
            corner_radius=6,
            font=FONT_BUTTON,
            dropdown_font=FONT_BUTTON,
            fg_color=SPOTIFY_MID_GRAY,
            button_color=SPOTIFY_DARK_GRAY,
            button_hover_color=SPOTIFY_BORDER_COLOR,
            text_color=SPOTIFY_WHITE,
            dropdown_fg_color=SPOTIFY_DARK_GRAY,
            dropdown_hover_color=SPOTIFY_MID_GRAY,
            dropdown_text_color=SPOTIFY_WHITE,
        )
        option.pack(side="left", fill="x", expand=True)

    def _add_entry_row(self, parent: ctk.CTkFrame, label: str, variable: ctk.StringVar) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, GAP_ROW))

        label_widget = ctk.CTkLabel(
            row,
            text=label,
            font=FONT_LABEL,
            text_color=SPOTIFY_LIGHT_GRAY,
            width=90,
            anchor="w",
        )
        label_widget.pack(side="left", padx=(0, 12))

        entry = ctk.CTkEntry(
            row,
            textvariable=variable,
            height=36,
            corner_radius=6,
            font=FONT_BUTTON,
            fg_color=SPOTIFY_MID_GRAY,
            border_color=SPOTIFY_BORDER_COLOR,
            border_width=1,
            text_color=SPOTIFY_WHITE,
            placeholder_text_color=SPOTIFY_TEXT_MUTED,
        )
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self._on_setting_changed(variable.get()))

    def _browse_cookie_file(self) -> None:
        filename = ctk.filedialog.askopenfilename(
            title="Select cookies.txt",
            filetypes=[("Cookie files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            self._cookie_file_var.set(filename)
            self._on_setting_changed(filename)

    def _on_setting_changed(self, _value: str | None = None) -> None:
        if self._loading:
            return
        settings: dict[str, str] = {}
        for var_name in (
            "_format_var",
            "_bitrate_var",
            "_provider_var",
            "_policy_var",
            "_proxy_var",
            "_cookie_file_var",
            "_browser_var",
        ):
            var = getattr(self, var_name)
            display_val = var.get()
            setting_key = var_name.lstrip("_").removesuffix("_var")
            vmap = self._value_maps.get(setting_key, {})
            settings[setting_key] = vmap.get(display_val, display_val)
        settings["proxy"] = settings["proxy"].strip()
        settings["cookie_file"] = settings["cookie_file"].strip()
        self._settings.update(settings)
        self._status_var.set(self._status_text())
        if self._on_change:
            self._on_change(self._settings)

    def _status_text(self) -> str:
        settings = self._settings
        source = settings.get("audio_provider", "youtube-music").replace("-", " ").title()
        duplicate_policy = settings.get("duplicate_policy", "skip")
        if duplicate_policy not in _DUPLICATE_POLICY_MAP:
            duplicate_policy = "skip"
        parts = [
            f"{settings.get('format', 'mp3').upper()}",
            f"{settings.get('bitrate', 'auto')}",
            source,
            _DUPLICATE_POLICY_MAP[duplicate_policy],
        ]
        if settings.get("proxy"):
            parts.append("Proxy set")
        if settings.get("cookie_file"):
            parts.append("Cookies set")
        return "  \u2022  ".join(parts)

    def get_settings(self) -> dict[str, str]:
        self._on_setting_changed()
        return dict(self._settings)
