from __future__ import annotations

import customtkinter as ctk

from .theme import (
    FONT_SECTION,
    GAP_CARD_INNER,
    GAP_ROW,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_WHITE,
    frame_kwargs,
)


class LogFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, **frame_kwargs())
        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=GAP_CARD_INNER, pady=GAP_CARD_INNER)

        header = ctk.CTkLabel(
            inner,
            text="Log",
            font=FONT_SECTION,
            text_color=SPOTIFY_WHITE,
        )
        header.pack(anchor="w", pady=(0, GAP_ROW))

        self._text = ctk.CTkTextbox(
            inner,
            state="disabled",
            wrap="word",
            font=("Cascadia Code", 10),
            text_color=SPOTIFY_LIGHT_GRAY,
            fg_color=SPOTIFY_DARK_GRAY,
            border_width=1,
            border_color=SPOTIFY_BORDER_COLOR,
            corner_radius=6,
        )
        self._text.pack(fill="both", expand=True)

    def write(self, message: str) -> None:
        self._text.configure(state="normal")
        self._text.insert("end", message + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")
