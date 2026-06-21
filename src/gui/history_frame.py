from __future__ import annotations

from datetime import datetime
from typing import Any

import customtkinter as ctk


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)
        self._build_ui()

    def _build_ui(self) -> None:
        header = ctk.CTkLabel(
            self, text="📜 Download History", font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(anchor="w", padx=12, pady=(12, 6))

        self._text = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self._text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        clear_btn = ctk.CTkButton(buttons, text="Clear", width=100, command=self.clear)
        clear_btn.pack(side="right")

    def render(
        self, history: list[dict[str, Any]], track_state_summary: dict[str, int]
    ) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        if not history:
            self._text.insert("end", "No downloads yet.\n")
        else:
            for entry in history:
                ts = entry.get("timestamp", "")
                try:
                    dt = datetime.fromisoformat(ts)
                    time_str = dt.strftime("%Y-%m-%d %H:%M")
                except (ValueError, TypeError):
                    time_str = ts[:16] if ts else "unknown"

                url = entry.get("url", "")
                short_url = url.split("?")[0] if url else "(unknown)"
                if len(short_url) > 60:
                    short_url = short_url[:57] + "…"

                tracks = entry.get("tracks_downloaded", 0)
                status = entry.get("status", "unknown")
                folder = entry.get("output_folder", "")

                self._text.insert(
                    "end", f"{time_str}  {status}  {tracks} track(s)  {short_url}\n"
                )
                if folder:
                    self._text.insert("end", f"  → {folder}\n")
            self._text.insert("end", "\n")

        self._text.insert(
            "end",
            "Track state:\n"
            f"  downloaded: {track_state_summary.get('downloaded', 0)}\n"
            f"  skipped: {track_state_summary.get('skipped', 0)}\n"
            f"  failed: {track_state_summary.get('failed', 0)}\n"
            f"  quarantined: {track_state_summary.get('quarantined', 0)}\n",
        )
        self._text.configure(state="disabled")

    def clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")
