from __future__ import annotations

import customtkinter as ctk

from .theme import (
    FONT_SECTION,
    FONT_SMALL,
    GAP_CARD_INNER,
    GAP_ROW,
    SPOTIFY_BORDER_COLOR,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_WHITE,
    frame_kwargs,
)


class HistoryFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master, **frame_kwargs())
        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=GAP_CARD_INNER, pady=GAP_CARD_INNER)

        header = ctk.CTkLabel(
            inner,
            text="Download History",
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

    def render(self, history: list[dict], track_state_summary: dict[str, int]) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")

        lines: list[str] = []

        if not history:
            lines.append("No downloads yet.")
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
                    short_url = short_url[:57] + "\u2026"

                tracks = entry.get("tracks_downloaded", 0)
                status = entry.get("status", "unknown")

                # Status indicator color
                status_tag = status.upper()
                lines.append(f"  {time_str}  {status_tag}  {tracks} track(s)")
                lines.append(f"    {short_url}")
                folder = entry.get("output_folder", "")
                if folder:
                    lines.append(f"      \u2192 {folder}")
                lines.append("")

        lines.append("")
        lines.append("Track state:")
        lines.append("  downloaded: {}".format(track_state_summary.get("downloaded", 0)))
        lines.append("  skipped: {}".format(track_state_summary.get("skipped", 0)))
        lines.append("  failed: {}".format(track_state_summary.get("failed", 0)))
        lines.append("  quarantined: {}".format(track_state_summary.get("quarantined", 0)))

        self._text.insert("end", "\n".join(lines) + "\n")
        self._text.configure(state="disabled")
