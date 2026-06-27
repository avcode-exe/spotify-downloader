from __future__ import annotations

import customtkinter as ctk

from src.models import DuplicateGroup

from .theme import (
    FONT_SECTION,
    FONT_SMALL,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_WHITE,
    frame_kwargs,
    GAP_CARD_INNER,
    GAP_ROW,
)


class DuplicatesFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, **frame_kwargs())
        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=GAP_CARD_INNER, pady=GAP_CARD_INNER)

        header = ctk.CTkLabel(
            inner,
            text="Duplicates",
            font=FONT_SECTION,
            text_color=SPOTIFY_WHITE,
        )
        header.pack(anchor="w", pady=(0, GAP_ROW))

        self._text = ctk.CTkTextbox(
            inner,
            state="disabled",
            wrap="word",
            font=FONT_SMALL,
            text_color=SPOTIFY_LIGHT_GRAY,
            fg_color=SPOTIFY_DARK_GRAY,
            border_width=1,
            border_color=SPOTIFY_BORDER_COLOR,
            corner_radius=6,
        )
        self._text.pack(fill="both", expand=True)

    def render(self, duplicate_groups: list[DuplicateGroup]) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        lines: list[str] = []

        if not duplicate_groups:
            lines.append("No duplicate groups found. Run Preview first.")
        else:
            for group in duplicate_groups:
                keep = group.keep
                keep_name = keep.path.name if keep else "unknown"
                action = "move" if group.safe_to_move else "review"
                lines.append("")
                lines.append("  {}: {}".format(group.reason, group.key))
                lines.append("    keep: {}".format(keep_name))
                for track in group.tracks:
                    if track is keep:
                        continue
                    lines.append("    {}: {}".format(action, track.path.name))
                lines.append("")

        self._text.insert("end", "\n".join(lines) + "\n")
        self._text.configure(state="disabled")
