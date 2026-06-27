from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from .theme import (
    FONT_LABEL,
    FONT_SECTION,
    FONT_SUBTITLE,
    FONT_TITLE,
    SPOTIFY_DARK_GRAY,
    SPOTIFY_GREEN,
    SPOTIFY_GREEN_LIGHT,
    SPOTIFY_LIGHT_GRAY,
    SPOTIFY_MID_GRAY,
    SPOTIFY_TEXT_MUTED,
    SPOTIFY_WHITE,
    button_kwargs,
    entry_kwargs,
    frame_kwargs,
    GAP_ACTION,
    GAP_CARD_INNER,
    GAP_ROW,
    GAP_SECTION,
    PAD_CARD_INNER,
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
        inner.pack(fill="both", expand=True, padx=GAP_CARD_INNER, pady=GAP_CARD_INNER)

        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(inner, fg_color="transparent")
        header.pack(fill="x", pady=(0, GAP_SECTION))

        title = ctk.CTkLabel(
            header,
            text="Spotify Playlist Downloader",
            font=FONT_TITLE,
            text_color=SPOTIFY_WHITE,
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            header,
            text="Paste a public playlist or track URL and press Download",
            font=FONT_SUBTITLE,
            text_color=SPOTIFY_TEXT_MUTED,
        )
        subtitle.pack(anchor="w", pady=(4, 0))

        # ── Input Card ────────────────────────────────────────────────────
        input_card = ctk.CTkFrame(inner, **frame_kwargs())
        input_card.pack(fill="x", pady=(GAP_SECTION, GAP_ROW))

        self._add_field(input_card, "Playlist or Track URL", 0)

        self.url_entry = ctk.CTkEntry(
            input_card,
            placeholder_text="https://open.spotify.com/playlist/... or /track/...",
            **entry_kwargs(),
        )
        self.url_entry.pack(fill="x", padx=PAD_CARD_INNER, pady=(0, GAP_ROW))

        self._add_field(input_card, "Output folder", GAP_ROW)

        output_row = ctk.CTkFrame(input_card, fg_color="transparent")
        output_row.pack(fill="x", padx=PAD_CARD_INNER, pady=(0, PAD_CARD_INNER))

        self.output_entry = ctk.CTkEntry(
            output_row, placeholder_text="./downloads", **entry_kwargs()
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            output_row,
            text="Browse",
            width=90,
            command=self._browse_output,
            **button_kwargs("ghost"),
        )
        browse_btn.pack(side="right")

        # ── Actions Card ──────────────────────────────────────────────────
        actions_card = ctk.CTkFrame(inner, **frame_kwargs())
        actions_card.pack(fill="x", pady=(GAP_ROW, GAP_ROW))

        actions_title = ctk.CTkLabel(
            actions_card,
            text="Actions",
            font=FONT_SECTION,
            text_color=SPOTIFY_WHITE,
        )
        actions_title.pack(
            anchor="w", padx=PAD_CARD_INNER, pady=(PAD_CARD_INNER, GAP_ACTION)
        )

        # Primary actions row
        primary_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        primary_row.pack(fill="x", padx=PAD_CARD_INNER, pady=(0, GAP_ACTION))

        self.download_btn = ctk.CTkButton(
            primary_row,
            text="Download",
            width=130,
            command=self._on_download,
            **button_kwargs("primary"),
        )
        self.download_btn.pack(side="left", padx=(0, 8))

        self.fresh_btn = ctk.CTkButton(
            primary_row,
            text="Fresh",
            width=100,
            command=self._on_fresh,
            **button_kwargs("secondary"),
        )
        self.fresh_btn.pack(side="left", padx=(0, 8))

        self.retry_btn = ctk.CTkButton(
            primary_row,
            text="Retry Failed",
            width=120,
            command=self._on_retry,
            state="disabled",
            **button_kwargs("secondary"),
        )
        self.retry_btn.pack(side="left")

        # Secondary actions row
        secondary_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        secondary_row.pack(fill="x", padx=PAD_CARD_INNER, pady=(0, PAD_CARD_INNER))

        self.preview_btn = ctk.CTkButton(
            secondary_row,
            text="Preview",
            width=110,
            command=self._on_preview,
            **button_kwargs("ghost"),
        )
        self.preview_btn.pack(side="left", padx=(0, 8))

        self.duplicates_btn = ctk.CTkButton(
            secondary_row,
            text="Duplicates",
            width=110,
            command=self._on_duplicates,
            **button_kwargs("ghost"),
        )
        self.duplicates_btn.pack(side="left")

        # ── Status Card ───────────────────────────────────────────────────
        status_card = ctk.CTkFrame(inner, **frame_kwargs())
        status_card.pack(fill="x", pady=(GAP_ROW, 0))

        status_header = ctk.CTkFrame(status_card, fg_color="transparent")
        status_header.pack(fill="x", padx=PAD_CARD_INNER, pady=(PAD_CARD_INNER, 8))

        status_label = ctk.CTkLabel(
            status_header,
            text="Progress",
            font=FONT_SECTION,
            text_color=SPOTIFY_WHITE,
        )
        status_label.pack(side="left")

        self.status_var = ctk.StringVar(value="Ready")
        self.status_indicator = ctk.CTkLabel(
            status_header,
            textvariable=self.status_var,
            font=FONT_LABEL,
            text_color=SPOTIFY_GREEN,
        )
        self.status_indicator.pack(side="right")

        self.progress = ctk.CTkProgressBar(
            status_card,
            height=6,
            corner_radius=3,
            progress_color=SPOTIFY_GREEN,
            border_color=SPOTIFY_DARK_GRAY,
            fg_color=SPOTIFY_MID_GRAY,
        )
        self.progress.pack(fill="x", padx=PAD_CARD_INNER, pady=(0, GAP_ACTION))
        self.progress.set(0)

        self.track_var = ctk.StringVar(value="\u2014")
        self.track_label = ctk.CTkLabel(
            status_card,
            textvariable=self.track_var,
            font=FONT_LABEL,
            text_color=SPOTIFY_LIGHT_GRAY,
        )
        self.track_label.pack(anchor="w", padx=PAD_CARD_INNER, pady=(0, GAP_ACTION))

        # ── Footer ────────────────────────────────────────────────────────
        footer = ctk.CTkFrame(inner, fg_color="transparent")
        footer.pack(fill="x", pady=(GAP_SECTION, 0))

        self.cancel_btn = ctk.CTkButton(
            footer,
            text="Cancel",
            width=110,
            command=self._on_cancel,
            state="disabled",
            **button_kwargs("danger"),
        )
        self.cancel_btn.pack(side="left")

        quit_btn = ctk.CTkButton(
            footer,
            text="Quit",
            width=90,
            command=self._quit,
            **button_kwargs("ghost"),
        )
        quit_btn.pack(side="right")

    def _add_field(self, parent: ctk.CTk, label_text: str, top_pad: int = 0) -> None:
        lbl = ctk.CTkLabel(
            parent,
            text=label_text,
            font=FONT_LABEL,
            text_color=SPOTIFY_LIGHT_GRAY,
        )
        lbl.pack(anchor="w", padx=PAD_CARD_INNER, pady=(top_pad, 4))

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
        if busy:
            self.progress.configure(progress_color=SPOTIFY_GREEN_LIGHT)
        else:
            self.progress.configure(progress_color=SPOTIFY_GREEN)

    def update_status(
        self, status: str, track: str = "\u2014", progress: float = 0.0
    ) -> None:
        self.status_var.set(status)
        self.track_var.set(track)
        self.progress.set(progress)
