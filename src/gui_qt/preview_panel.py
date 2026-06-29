from __future__ import annotations

from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.manifest import summarize_scan

from .theme import SPOTIFY_WHITE, get_section_font


class PreviewPanel(QWidget):
    """Preview panel showing local audio files in a table."""

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Preview")
        title.setFont(get_section_font())
        title.setStyleSheet(
            f"color: {SPOTIFY_WHITE.name() if hasattr(SPOTIFY_WHITE, 'name') else '#FFFFFF'};"
        )
        layout.addWidget(title)

        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(
            ["Title", "Artist", "Album", "Duration", "Bitrate", "Size", "File"]
        )
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setStyleSheet("""
            QTableWidget {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 6px;
                gridline-color: #333333;
                alternate-background-color: #181818;
            }
            QTableWidget::item { padding: 4px 8px; }
            QHeaderView::section {
                background-color: #181818;
                color: #B3B3B3;
                border: none;
                border-bottom: 1px solid #333333;
                padding: 6px 8px;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self._table)

        # Summary label
        self._summary_label = QLabel("")
        self._summary_label.setStyleSheet("color: #6A6A6A; font-size: 9pt;")
        self._summary_label.setWordWrap(True)
        layout.addWidget(self._summary_label)

    def render(
        self,
        tracks,
        duplicate_groups,
        track_state,
        output_folder: str,
    ) -> None:
        self._table.setRowCount(len(tracks))

        for i, track in enumerate(tracks):
            title = track.title or track.filename
            artist = track.artist or ""
            album = track.album or ""
            duration = self._format_duration(track.duration) if track.duration else ""
            bitrate = f"{track.bitrate // 1000}k" if track.bitrate else ""
            size = self._format_size(track.size)
            filename = track.path.name

            self._table.setItem(i, 0, QTableWidgetItem(title))
            self._table.setItem(i, 1, QTableWidgetItem(artist))
            self._table.setItem(i, 2, QTableWidgetItem(album))
            self._table.setItem(i, 3, QTableWidgetItem(duration))
            self._table.setItem(i, 4, QTableWidgetItem(bitrate))
            self._table.setItem(i, 5, QTableWidgetItem(size))
            self._table.setItem(i, 6, QTableWidgetItem(filename))

        summary = summarize_scan(tracks, duplicate_groups)
        summary_text = (
            f"Output: {output_folder} | "
            f"Files: {summary['files']} | "
            f"Unique: {summary['unique_tracks']} | "
            f"Duplicates: {summary['duplicate_groups']} | "
            f"Possible dupes: {summary['possible_duplicate_groups']}"
        )
        self._summary_label.setText(summary_text)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        if seconds < 60:
            return f"{int(seconds)}s"
        m = int(seconds // 60)
        s = int(seconds % 60)
        return f"{m}:{s:02d}"

    @staticmethod
    def _format_size(bytes_val: int) -> str:
        if bytes_val < 1024:
            return f"{bytes_val} B"
        if bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        return f"{bytes_val / (1024 * 1024):.1f} MB"
