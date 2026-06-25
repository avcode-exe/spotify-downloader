from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .theme import (
    FONT_BUTTON,
    FONT_LABEL,
    FONT_SUBTITLE,
    FONT_TITLE,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_GREEN,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_WHITE,
    button_kwargs,
    frame_kwargs,
)


class HomeFrame(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk,
        on_download: Callable[[], None],
        on_fresh: Callable[[], None],
        on_preview: Callable[[], None],
        on_duplicates: Callable[[], None],
        on_retry: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        super().__init__(
            master,
            **frame_kwargs(),
        )
        self._on_download = on_download
        self._on_fresh = on_fresh
        self._on_preview = on_preview
        self._on_duplicates = on_duplicates
        self._on_retry = on_retry
        self._on_cancel = on_cancel
        self._build_ui()

    def _build_ui(self) -> None:
        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=16, pady=16)

        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))

        title = ctk.CTkLabel(
            header,
            text="🎵 Spotify Playlist Downloader",
            font=FONT_TITLE,
            text_color=SPOTIFY_WHITE,
        )
        title.pack(anchor="center")

        subtitle = ctk.CTkLabel(
            header,
            text="Paste a public playlist URL and press Download",
            font=FONT_SUBTITLE,
            text_color=SPOTIFY_LIGHT_GRAY,
        )
        subtitle.pack(anchor="center", pady=(6, 0))

        input_card = ctk.CTkFrame(inner, **frame_kwargs())
        input_card.pack(fill="x", pady=(0, 16))

        url_label = ctk.CTkLabel(
            input_card,
            text="Playlist or Track URL",
            font=FONT_BUTTON,
            text_color=SPOTIFY_WHITE,
        )
        url_label.pack(anchor="w", padx=16, pady=(16, 6))

        self.url_entry = ctk.CTkEntry(
            input_card,
            placeholder_text="https://open.spotify.com/playlist/... or /track/...",
            height=40,
            font=FONT_BUTTON,
            corner_radius=6,
        )
        self.url_entry.pack(fill="x", padx=16, pady=(0, 14))

        output_label = ctk.CTkLabel(
            input_card, text="Output folder", font=FONT_BUTTON, text_color=SPOTIFY_WHITE
        )
        output_label.pack(anchor="w", padx=16, pady=(0, 6))

        output_row = ctk.CTkFrame(input_card, fg_color="transparent")
        output_row.pack(fill="x", padx=16, pady=(0, 16))

        self.output_entry = ctk.CTkEntry(
            output_row,
            placeholder_text="./downloads",
            height=40,
            font=FONT_BUTTON,
            corner_radius=6,
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            output_row,
            text="Browse",
            width=100,
            height=40,
            command=self._browse_output,
            **button_kwargs("secondary"),
        )
        browse_btn.pack(side="right")

        actions_card = ctk.CTkFrame(inner, **frame_kwargs())
        actions_card.pack(fill="x", pady=(0, 16))

        actions_label = ctk.CTkLabel(
            actions_card,
            text="Actions",
            font=FONT_BUTTON,
            text_color=SPOTIFY_WHITE,
        )
        actions_label.pack(anchor="w", padx=16, pady=(16, 10))

        primary_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        primary_row.pack(fill="x", padx=16, pady=(0, 12))

        self.download_btn = ctk.CTkButton(
            primary_row,
            text="▶  Download",
            width=140,
            height=44,
            command=self._on_download,
            **button_kwargs("primary"),
        )
        self.download_btn.pack(side="left", padx=(0, 8))

        self.fresh_btn = ctk.CTkButton(
            primary_row,
            text="⟳  Fresh",
            width=120,
            height=44,
            command=self._on_fresh,
            **button_kwargs("secondary"),
        )
        self.fresh_btn.pack(side="left", padx=(0, 8))

        self.retry_btn = ctk.CTkButton(
            primary_row,
            text="🔄  Retry Failed",
            width=140,
            height=44,
            command=self._on_retry,
            **button_kwargs("secondary"),
        )
        self.retry_btn.pack(side="left", padx=(0, 8))

        secondary_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        secondary_row.pack(fill="x", padx=16, pady=(0, 16))

        self.preview_btn = ctk.CTkButton(
            secondary_row,
            text="🔎  Preview",
            width=120,
            height=40,
            command=self._on_preview,
            **button_kwargs("secondary"),
        )
        self.preview_btn.pack(side="left", padx=(0, 8))

        self.duplicates_btn = ctk.CTkButton(
            secondary_row,
            text="📋  Duplicates",
            width=130,
            height=40,
            command=self._on_duplicates,
            **button_kwargs("secondary"),
        )
        self.duplicates_btn.pack(side="left", padx=(0, 8))

        status_card = ctk.CTkFrame(inner, **frame_kwargs())
        status_card.pack(fill="x", pady=(0, 0))

        status_label = ctk.CTkLabel(
            status_card,
            text="Status",
            font=FONT_BUTTON,
            text_color=SPOTIFY_WHITE,
        )
        status_label.pack(anchor="w", padx=16, pady=(16, 8))

        self.progress = ctk.CTkProgressBar(
            status_card,
            height=6,
            corner_radius=3,
            progress_color=SPOTIFY_GREEN,
            border_color=SPOTIFY_DARK_GRAY,
        )
        self.progress.pack(fill="x", padx=16, pady=(0, 12))
        self.progress.set(0)

        self.status_var = ctk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(
            status_card,
            textvariable=self.status_var,
            font=FONT_LABEL,
            text_color=SPOTIFY_WHITE,
        )
        self.status_label.pack(anchor="w", padx=16, pady=(0, 4))

        self.track_var = ctk.StringVar(value="—")
        self.track_label = ctk.CTkLabel(
            status_card,
            textvariable=self.track_var,
            font=FONT_LABEL,
            text_color=SPOTIFY_LIGHT_GRAY,
        )
        self.track_label.pack(anchor="w", padx=16, pady=(0, 16))

        footer = ctk.CTkFrame(inner, fg_color="transparent")
        footer.pack(fill="x", pady=(16, 0))

        self.cancel_btn = ctk.CTkButton(
            footer,
            text="⏹  Cancel",
            width=120,
            height=40,
            command=self._on_cancel,
            state="disabled",
            **button_kwargs("danger"),
        )
        self.cancel_btn.pack(side="left")

        quit_btn = ctk.CTkButton(
            footer,
            text="✕  Quit",
            width=120,
            height=40,
            command=self._quit,
            **button_kwargs("secondary"),
        )
        quit_btn.pack(side="right")

    def _browse_output(self) -> None:
        directory = ctk.filedialog.askdirectory(title="Select output folder")
        if directory:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, directory)

    def _quit(self) -> None:
        top = self.winfo_toplevel()
        top.quit()
        top.destroy()

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.download_btn.configure(state=state)
        self.fresh_btn.configure(state=state)
        self.retry_btn.configure(state=state)
        self.preview_btn.configure(state=state)
        self.duplicates_btn.configure(state=state)
        self.cancel_btn.configure(state="normal" if busy else "disabled")

    def update_status(
        self, status: str, track: str = "—", progress: float = 0.0
    ) -> None:
        self.status_var.set(status)
        self.track_var.set(track)
        self.progress.set(progress)
