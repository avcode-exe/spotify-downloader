from __future__ import annotations

from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor
from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from .theme import SPOTIFY_WHITE, get_section_font


class LogPanel(QWidget):
    """Log panel showing real-time download progress and status."""

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()
        self._setup_colors()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Log")
        title.setFont(get_section_font())
        title.setStyleSheet(
            f"color: {SPOTIFY_WHITE.name() if hasattr(SPOTIFY_WHITE, 'name') else '#FFFFFF'};"
        )
        layout.addWidget(title)

        self._text_edit = QPlainTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px;
                color: #B3B3B3;
                font-family: "Cascadia Code", "Consolas";
                font-size: 10pt;
            }
            QPlainTextEdit:focus {
                border: 2px solid #1DB954;
            }
        """)
        layout.addWidget(self._text_edit)

    def _setup_colors(self) -> None:
        self._formats: dict[str, QTextCharFormat] = {}

        for name, color_str in [
            ("info", "#B3B3B3"),
            ("success", "#1DB954"),
            ("error", "#E91429"),
            ("warning", "#F59E0B"),
            ("track", "#3B82F6"),
            ("skipped", "#A0A0A0"),
        ]:
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color_str))
            self._formats[name] = fmt

    def write(self, message: str) -> None:
        cursor = self._text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        for line in message.split("\n"):
            line = line.strip()
            if not line:
                continue

            fmt = self._formats.get("info")
            if line.startswith(("Complete!", "\u2713")):
                fmt = self._formats.get("success")
            elif line.startswith(("Failed", "\u2717", "Error")):
                fmt = self._formats.get("error")
            elif line.startswith("\u26a0"):
                fmt = self._formats.get("warning")
            elif line.startswith(("Downloading:", "\u2193")):
                fmt = self._formats.get("track")
            elif line.startswith(("Skipped", "\u23ed")):
                fmt = self._formats.get("skipped")

            cursor.mergeCharFormat(fmt or self._formats["info"])
            cursor.insertBlock()
            cursor.insertText(line)

        self._text_edit.setTextCursor(cursor)
        self._text_edit.verticalScrollBar().setValue(
            self._text_edit.verticalScrollBar().maximum()
        )

    def clear(self) -> None:
        self._text_edit.clear()
