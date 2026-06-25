from __future__ import annotations

import os
from typing import Callable, Sequence

import customtkinter as ctk

from src.models import DUPLICATE_POLICY_OPTIONS
from src.state import STATE_FILE

from .theme import (
    FONT_BUTTON,
    FONT_LABEL,
    FONT_SECTION,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_GREEN,
    SPOTIFY_LIGHT_GRAY,
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


class SettingsFrame(ctk.CTkFrame):
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
        self._build_ui()
        self._loading = False

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        title = ctk.CTkLabel(
            inner,
            text="⚙ Settings",
            font=FONT_SECTION,
            text_color=SPOTIFY_GREEN,
        )
        title.pack(anchor="w", pady=(0, 16))

        self._format_var = ctk.StringVar(value=self._settings.get("format", "mp3"))
        self._bitrate_var = ctk.StringVar(value=self._settings.get("bitrate", "auto"))
        self._provider_var = ctk.StringVar(
            value=self._settings.get("audio_provider", "youtube-music")
        )
        self._policy_var = ctk.StringVar(
            value=self._settings.get("duplicate_policy", "skip")
        )
        self._proxy_var = ctk.StringVar(value=self._settings.get("proxy", ""))
        self._cookie_file_var = ctk.StringVar(
            value=self._settings.get("cookie_file", "")
        )
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
        self._add_select_row(
            inner, "Audio source", self._provider_var, provider_options
        )
        self._add_select_row(
            inner, "Duplicate policy", self._policy_var, policy_options
        )
        self._add_select_row(inner, "Browser", self._browser_var, BROWSER_OPTIONS)
        self._add_entry_row(inner, "Proxy", self._proxy_var)
        self._add_entry_row(inner, "Cookie file", self._cookie_file_var)

        params = {
            "fg_color": "transparent",
            "hover_color": SPOTIFY_DARK_GRAY,
            "text_color": SPOTIFY_WHITE,
            "border_color": SPOTIFY_BORDER_COLOR,
            "border_width": 1,
            "font": FONT_BUTTON,
            "height": 36,
        }
        browse_btn = ctk.CTkButton(
            inner, text="Browse", command=self._browse_cookie_file, **params
        )
        browse_btn.pack(fill="x", pady=(0, 12))

        status = self._status_text()
        self._status_var = ctk.StringVar(value=status)
        status_label = ctk.CTkLabel(
            inner,
            textvariable=self._status_var,
            font=FONT_LABEL,
            text_color=SPOTIFY_LIGHT_GRAY,
            wraplength=380,
            anchor="w",
            justify="left",
        )
        status_label.pack(fill="x", pady=(16, 10))

        state_label = ctk.CTkLabel(
            inner,
            text=f"State: {STATE_FILE}",
            font=("Segoe UI", 10),
            text_color="#777777",
            anchor="w",
            wraplength=380,
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
            value_map = {opt[0]: opt[1] for opt in options}
        else:
            display_options = [str(opt) for opt in options]
            value_map = {str(opt): str(opt) for opt in options}

        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

        label_widget = ctk.CTkLabel(
            row,
            text=label,
            font=FONT_LABEL,
            text_color=SPOTIFY_WHITE,
            width=90,
            anchor="w",
        )
        label_widget.pack(side="left", padx=(0, 12))

        current_value = variable.get()
        resolved_value = value_map.get(current_value, current_value)
        variable.set(resolved_value)

        option = ctk.CTkOptionMenu(
            row,
            variable=variable,
            values=display_options,
            command=lambda _value, vm=value_map: self._on_browser_changed(vm, _value),
            height=36,
            corner_radius=6,
            font=FONT_BUTTON,
            dropdown_font=FONT_BUTTON,
        )
        option.pack(side="left", fill="x", expand=True)

    def _on_browser_changed(self, value_map: dict[str, str], selected: str) -> None:
        actual_value = value_map.get(selected, selected)
        self._browser_var.set(actual_value)
        self._on_setting_changed(actual_value)

    def _add_entry_row(
        self, parent: ctk.CTkFrame, label: str, variable: ctk.StringVar
    ) -> None:
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(0, 10))

        label_widget = ctk.CTkLabel(
            row,
            text=label,
            font=FONT_LABEL,
            text_color=SPOTIFY_WHITE,
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
        self._settings.update(
            {
                "format": self._format_var.get(),
                "bitrate": self._bitrate_var.get(),
                "audio_provider": self._provider_var.get(),
                "duplicate_policy": self._policy_var.get(),
                "browser": self._browser_var.get(),
                "proxy": self._proxy_var.get().strip(),
                "cookie_file": self._cookie_file_var.get().strip(),
            }
        )
        self._status_var.set(self._status_text())
        if self._on_change:
            self._on_change(self._settings)

    def _status_text(self) -> str:
        settings = self._settings
        source = (
            settings.get("audio_provider", "youtube-music").replace("-", " ").title()
        )
        duplicate_policy = settings.get("duplicate_policy", "skip")
        if duplicate_policy not in _DUPLICATE_POLICY_MAP:
            duplicate_policy = "skip"
        parts = [
            f"Format: {settings.get('format', 'mp3').upper()}",
            f"Bitrate: {settings.get('bitrate', 'auto')}",
            f"Source: {source}",
            f"Duplicate: {_DUPLICATE_POLICY_MAP[duplicate_policy]}",
            f"Browser: {settings.get('browser', 'auto').title()}",
        ]
        if settings.get("proxy"):
            parts.append(f"Proxy: {settings['proxy']}")
        if settings.get("cookie_file"):
            parts.append(f"Cookies: {os.path.basename(settings['cookie_file'])}")
        return " · ".join(parts)

    def get_settings(self) -> dict[str, str]:
        self._on_setting_changed()
        return dict(self._settings)
