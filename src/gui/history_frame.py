from __future__ import annotations


import customtkinter as ctk

from .theme import (
    FONT_LABEL,
    FONT_SECTION,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_WHITE,
    frame_kwargs,
)


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, **frame_kwargs())
        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkLabel(
            inner,
            text="📜 Download History",
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

    def render(self, history: list[dict], track_state_summary: dict[str, int]) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        if not history:
            self._text.insert("end", "No downloads yet.\n")
        else:
            for entry in history:
                ts = entry.get("timestamp", "")
                try:
                    from datetime import datetime

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
