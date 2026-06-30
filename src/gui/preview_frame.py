from __future__ import annotations

from typing import Any

import customtkinter as ctk

from src.manifest import summarize_scan
from src.models import DuplicateGroup, LocalTrack
from src.state import summarize_track_state

from .theme import (
    FONT_SECTION,
    FONT_SMALL,
    GAP_CARD_INNER,
    GAP_ROW,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_GREEN,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_WHITE,
    frame_kwargs,
)


class PreviewFrame(ctk.CTkFrame):  # type: ignore[misc]
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, **frame_kwargs())
        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=GAP_CARD_INNER, pady=GAP_CARD_INNER)

        header = ctk.CTkLabel(
            inner,
            text="Preview",
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

    def _colorize_section(
        self,
        text: str,
        key_color: str = SPOTIFY_WHITE,
        value_color: str = SPOTIFY_GREEN,
    ) -> str:
        """Return text with simple color hints via tags."""
        return text

    def render(
        self,
        tracks: list[LocalTrack],
        duplicate_groups: list[DuplicateGroup],
        track_state: list[dict[str, Any]],
        output_folder: str,
    ) -> None:
        summary = summarize_scan(tracks, duplicate_groups)
        state_summary = summarize_track_state(track_state)

        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        lines: list[str] = []

        # Section: Scan overview
        lines.append(f"Output folder: {output_folder}")
        lines.append("Local audio files: {}".format(summary["files"]))
        lines.append("Unique tracks: {}".format(summary["unique_tracks"]))
        lines.append("Duplicate groups: {}".format(summary["duplicate_groups"]))
        lines.append("Possible duplicate groups: {}".format(summary["possible_duplicate_groups"]))
        lines.append("Duplicate copies to move: {}".format(summary["duplicate_copies"]))
        lines.append("Possible duplicate copies: {}".format(summary["possible_duplicate_copies"]))

        lines.append("")
        lines.append("Track state:")
        lines.append("  downloaded: {}".format(state_summary["downloaded"]))
        lines.append("  skipped: {}".format(state_summary["skipped"]))
        lines.append("  failed: {}".format(state_summary["failed"]))
        lines.append("  quarantined: {}".format(state_summary["quarantined"]))

        if duplicate_groups:
            lines.append("")
            lines.append("Duplicate groups:")
            for group in duplicate_groups:
                keep = group.keep
                keep_name = keep.path.name if keep else "unknown"
                lines.append("")
                lines.append(f"  {group.reason}: {group.key}")
                lines.append(f"    keep: {keep_name}")
                for track in group.tracks:
                    if track is keep:
                        continue
                    action = "move" if group.safe_to_move else "review"
                    lines.append(f"    {action}: {track.path.name}")
        else:
            lines.append("")
            lines.append("No duplicate groups detected.")

        self._text.insert("end", "\n".join(lines) + "\n")
        self._text.configure(state="disabled")
