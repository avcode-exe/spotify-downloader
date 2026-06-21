from __future__ import annotations

import customtkinter as ctk


class HomeFrame(ctk.CTkFrame):
    def __init__(
        self,
        master: ctk.CTk,
        on_download: callable,
        on_fresh: callable,
        on_preview: callable,
        on_duplicates: callable,
        on_retry: callable,
        on_cancel: callable,
    ) -> None:
        super().__init__(master)
        self._on_download = on_download
        self._on_fresh = on_fresh
        self._on_preview = on_preview
        self._on_duplicates = on_duplicates
        self._on_retry = on_retry
        self._on_cancel = on_cancel
        self._build_ui()

    def _build_ui(self) -> None:
        title = ctk.CTkLabel(
            self,
            text="🎵 Spotify Playlist Downloader",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(pady=(18, 6))

        subtitle = ctk.CTkLabel(
            self, text="Paste a public playlist URL and press Download"
        )
        subtitle.pack(pady=(0, 18))

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.pack(fill="x", padx=20, pady=(0, 12))

        url_label = ctk.CTkLabel(input_frame, text="Playlist URL:")
        url_label.pack(anchor="w", padx=(0, 8))
        self.url_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="https://open.spotify.com/playlist/...",
        )
        self.url_entry.pack(fill="x", pady=(0, 12))

        output_label = ctk.CTkLabel(input_frame, text="Output folder:")
        output_label.pack(anchor="w", padx=(0, 8))
        output_row = ctk.CTkFrame(input_frame, fg_color="transparent")
        output_row.pack(fill="x")
        self.output_entry = ctk.CTkEntry(output_row, placeholder_text="./downloads")
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        browse_btn = ctk.CTkButton(
            output_row, text="Browse", width=100, command=self._browse_output
        )
        browse_btn.pack(side="right")

        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=(12, 0))

        self.download_btn = ctk.CTkButton(
            button_frame, text="▶ Download", width=120, command=self._on_download
        )
        self.download_btn.pack(side="left", padx=(0, 8))

        self.fresh_btn = ctk.CTkButton(
            button_frame, text="⟳ Fresh", width=100, command=self._on_fresh
        )
        self.fresh_btn.pack(side="left", padx=(0, 8))

        self.retry_btn = ctk.CTkButton(
            button_frame, text="🔄 Retry Failed", width=120, command=self._on_retry
        )
        self.retry_btn.pack(side="left", padx=(0, 8))

        self.preview_btn = ctk.CTkButton(
            button_frame, text="🔎 Preview", width=100, command=self._on_preview
        )
        self.preview_btn.pack(side="right", padx=(0, 8))

        self.duplicates_btn = ctk.CTkButton(
            button_frame, text="📋 Duplicates", width=120, command=self._on_duplicates
        )
        self.duplicates_btn.pack(side="right", padx=(0, 8))

        status_frame = ctk.CTkFrame(self, fg_color="transparent")
        status_frame.pack(fill="x", padx=20, pady=(12, 0))

        self.progress = ctk.CTkProgressBar(status_frame)
        self.progress.pack(fill="x", pady=(0, 8))
        self.progress.set(0)

        self.status_var = ctk.StringVar(value="Ready")
        status_label = ctk.CTkLabel(status_frame, textvariable=self.status_var)
        status_label.pack(anchor="w")

        self.track_var = ctk.StringVar(value="—")
        track_label = ctk.CTkLabel(
            status_frame, textvariable=self.track_var, text_color="gray"
        )
        track_label.pack(anchor="w")

        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(12, 0))

        self.cancel_btn = ctk.CTkButton(
            action_frame,
            text="⏹ Cancel",
            width=100,
            command=self._on_cancel,
            state="disabled",
        )
        self.cancel_btn.pack(side="left")

        quit_btn = ctk.CTkButton(
            action_frame, text="✕ Quit", width=100, command=self._quit
        )
        quit_btn.pack(side="right")

    def _browse_output(self) -> None:
        directory = ctk.filedialog.askdirectory(title="Select output folder")
        if directory:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, directory)

    def _quit(self) -> None:
        self.winfo_toplevel().quit()

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
