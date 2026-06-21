from __future__ import annotations

import customtkinter as ctk

from .utils import strip_ansi


class LogFrame(ctk.CTkFrame):
    def __init__(self, master: ctk.CTk) -> None:
        super().__init__(master)
        self._build_ui()

    def _build_ui(self) -> None:
        header = ctk.CTkLabel(
            self, text="📜 Log", font=ctk.CTkFont(size=18, weight="bold")
        )
        header.pack(anchor="w", padx=12, pady=(12, 6))

        self._text = ctk.CTkTextbox(self, state="disabled", wrap="word")
        self._text.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(0, 12))

        clear_btn = ctk.CTkButton(buttons, text="Clear", width=100, command=self.clear)
        clear_btn.pack(side="right")

    def write(self, message: str) -> None:
        clean = strip_ansi(message)
        self._text.configure(state="normal")
        self._text.insert("end", clean + "\n")
        self._text.see("end")
        self._text.configure(state="disabled")

    def clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")
