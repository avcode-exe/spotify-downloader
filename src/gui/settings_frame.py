from __future__ import annotations

import os
from typing import Callable

import customtkinter as ctk

from src.models import DUPLICATE_POLICY_OPTIONS
from src.state import STATE_FILE


class SettingsFrame(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk,
        settings: dict[str, str],
        on_change: Callable[[dict[str, str]], None] | None = None,
    ) -> None:
        super().__init__(master)
        self._settings = dict(settings)
        self._on_change = on_change
        self._loading = True
        self._build_ui()
        self._loading = False

    def _build_ui(self) -> None:
        title = ctk.CTkLabel(
            self, text="⚙ Settings", font=ctk.CTkFont(size=18, weight="bold")
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

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

        self._add_select_row(1, "Format", self._format_var, format_options)
        self._add_select_row(2, "Bitrate", self._bitrate_var, bitrate_options)
        self._add_select_row(3, "Audio source", self._provider_var, provider_options)
        self._add_select_row(4, "Duplicate policy", self._policy_var, policy_options)
        self._add_entry_row(5, "Proxy", self._proxy_var)
        self._add_entry_row(6, "Cookie file", self._cookie_file_var)

        browse_btn = ctk.CTkButton(
            self, text="Browse", width=100, command=self._browse_cookie_file
        )
        browse_btn.grid(row=6, column=2, padx=(8, 0), pady=6)

        status = self._status_text()
        self._status_var = ctk.StringVar(value=status)
        status_label = ctk.CTkLabel(
            self, textvariable=self._status_var, text_color="gray"
        )
        status_label.grid(row=7, column=0, columnspan=3, sticky="w", pady=(8, 0))

        state_label = ctk.CTkLabel(
            self,
            text=f"State: {STATE_FILE}",
            text_color="gray",
            font=ctk.CTkFont(size=11),
        )
        state_label.grid(row=8, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)

    def _add_select_row(
        self, row: int, label: str, variable: ctk.StringVar, options: list[str]
    ) -> None:
        label_widget = ctk.CTkLabel(self, text=label)
        label_widget.grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)

        option = ctk.CTkOptionMenu(
            self, variable=variable, values=options, command=self._on_setting_changed
        )
        option.grid(row=row, column=1, sticky="ew", pady=6)

    def _add_entry_row(self, row: int, label: str, variable: ctk.StringVar) -> None:
        label_widget = ctk.CTkLabel(self, text=label)
        label_widget.grid(row=row, column=0, sticky="w", padx=(0, 12), pady=6)

        entry = ctk.CTkEntry(self, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=6)
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
                "proxy": self._proxy_var.get().strip(),
                "cookie_file": self._cookie_file_var.get().strip(),
            }
        )
        self._status_var.set(self._status_text())
        if self._on_change:
            self._on_change(self._settings)

    def _status_text(self) -> str:
        parts = [
            f"Format: {self._settings.get('format', 'mp3').upper()}",
            f"Bitrate: {self._settings.get('bitrate', 'auto')}",
            f"Source: {self._settings.get('audio_provider', 'youtube-music').replace('-', ' ').title()}",
            f"Duplicate: {dict(DUPLICATE_POLICY_OPTIONS).get(self._settings.get('duplicate_policy', 'skip'), 'skip')}",
        ]
        if self._settings.get("proxy"):
            parts.append(f"Proxy: {self._settings['proxy']}")
        if self._settings.get("cookie_file"):
            parts.append(f"Cookies: {os.path.basename(self._settings['cookie_file'])}")
        return " · ".join(parts)

    def get_settings(self) -> dict[str, str]:
        self._on_setting_changed()
        return dict(self._settings)
