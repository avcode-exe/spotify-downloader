from __future__ import annotations

import customtkinter as ctk

from src.manifest import summarize_scan
from src.models import DuplicateGroup, LocalTrack
from src.state import summarize_track_state

from .theme import (
    FONT_LABEL,
    FONT_SECTION,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_WHITE,
    frame_kwargs,
)


class PreviewFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, **frame_kwargs())
        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkLabel(
            inner,
            text="🔎 Preview",
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

    def render(
        self,
        tracks: list[LocalTrack],
        duplicate_groups: list[DuplicateGroup],
        track_state: list[dict],
        output_folder: str,
    ) -> None:
        summary = summarize_scan(tracks, duplicate_groups)
        state_summary = summarize_track_state(track_state)

        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert(
            "end",
            f"Output folder: {output_folder}\n"
            f"Local audio files: {summary['files']}\n"
            f"Unique tracks: {summary['unique_tracks']}\n"
            f"Duplicate groups: {summary['duplicate_groups']}\n"
            f"Possible duplicate groups: {summary['possible_duplicate_groups']}\n"
            f"Duplicate copies to move: {summary['duplicate_copies']}\n"
            f"Possible duplicate copies: {summary['possible_duplicate_copies']}\n\n"
            "Track state:\n"
            f"  downloaded: {state_summary['downloaded']}\n"
            f"  skipped: {state_summary['skipped']}\n"
            f"  failed: {state_summary['failed']}\n"
            f"  quarantined: {state_summary['quarantined']}\n",
        )

        if duplicate_groups:
            self._text.insert("end", "\nDuplicate groups:\n")
            for group in duplicate_groups:
                keep = group.keep
                keep_name = keep.path.name if keep else "unknown"
                self._text.insert("end", f"\n{group.reason} {group.key}\n")
                self._text.insert("end", f"  keep: {keep_name}\n")
                for track in group.tracks:
                    if track is keep:
                        continue
                    action = "move" if group.safe_to_move else "review"
                    self._text.insert("end", f"  {action}: {track.path.name}\n")
        else:
            self._text.insert("end", "\nNo duplicate groups detected.\n")

        self._text.configure(state="disabled")
