from __future__ import annotations

import customtkinter as ctk

from src.models import DuplicateGroup

from .theme import (
    FONT_LABEL,
    FONT_SECTION,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_WHITE,
    frame_kwargs,
)


class DuplicatesFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, **frame_kwargs())
        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkLabel(
            inner,
            text="📋 Duplicates",
            font=FONT_SECTION,
            text_color=SPOTIFY_WHITE,
        )
        header.pack(anchor="w", pady=(0, 12))

        self._text = ctk.CTkTextbox(
            inner,
            state="disabled",
            wrap="word",
            font=FONT_LABEL,
            text_color=SPOTIFY_WHITE,
            fg_color=SPOTIFY_DARK_GRAY,
            border_width=1,
            border_color=SPOTIFY_BORDER_COLOR,
            corner_radius=6,
        )
        self._text.pack(fill="both", expand=True)

    def render(self, duplicate_groups: list[DuplicateGroup]) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        if not duplicate_groups:
            self._text.insert("end", "No duplicate groups found. Run Preview first.\n")
        else:
            for group in duplicate_groups:
                keep = group.keep
                keep_name = keep.path.name if keep else "unknown"
                action = "move" if group.safe_to_move else "review"
                self._text.insert("end", f"{group.reason} {group.key}\n")
                self._text.insert("end", f"  keep: {keep_name}\n")
                for track in group.tracks:
                    if track is keep:
                        continue
                    self._text.insert("end", f"  {action}: {track.path.name}\n")
                self._text.insert("end", "\n")

        self._text.configure(state="disabled")
