from __future__ import annotations

import customtkinter as ctk

from src.models import DuplicateGroup


class DuplicatesFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)
        self._build_ui()

    def _build_ui(self) -> None:
        header = ctk.CTkLabel(
            self, text="📋 Duplicates", font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(anchor="w", padx=12, pady=(12, 6))

        self._text = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self._text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

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
