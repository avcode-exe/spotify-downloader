from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .theme import SPOTIFY_WHITE, get_section_font


class HistoryPanel(QWidget):
    """History panel showing past download sessions in a table."""

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Download History")
        title.setFont(get_section_font())
        title.setStyleSheet(
            f"color: {SPOTIFY_WHITE.name() if hasattr(SPOTIFY_WHITE, 'name') else '#FFFFFF'};"
        )
        layout.addWidget(title)

        self._table = QTableWidget()
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ["Timestamp", "URL", "Tracks", "Status", "Folder"]
        )
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
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

    def render(self, history: list[dict], track_state_summary: dict[str, int]) -> None:
        self._table.setRowCount(len(history))

        for i, entry in enumerate(history):
            ts = entry.get("timestamp", "")
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(ts)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except (ValueError, TypeError):
                time_str = ts[:16] if ts else "unknown"

            url = entry.get("url", "")
            short_url = url.split("?")[0] if url else "(unknown)"
            if len(short_url) > 80:
                short_url = short_url[:77] + "\u2026"

            tracks = entry.get("tracks_downloaded", 0)
            status = entry.get("status", "unknown").upper()
            folder = entry.get("output_folder", "")

            self._table.setItem(i, 0, QTableWidgetItem(time_str))
            self._table.setItem(i, 1, QTableWidgetItem(short_url))
            self._table.setItem(i, 2, QTableWidgetItem(str(tracks)))
            self._table.setItem(i, 3, QTableWidgetItem(status))
            self._table.setItem(i, 4, QTableWidgetItem(folder))

            # Color-code status
            status_item = self._table.item(i, 3)
            if status == "COMPLETED":
                status_item.setForeground(Qt.GlobalColor.green)
            elif status == "FAILED":
                status_item.setForeground(Qt.GlobalColor.red)
            elif status == "CANCELLED":
                status_item.setForeground(Qt.GlobalColor.yellow)

        # Add track state summary row
        if history:
            pass  # separator not supported in QTableWidget

        state_row = len(history) + 1
        self._table.setRowCount(state_row)

        for j, label in enumerate(["downloaded", "skipped", "failed", "quarantined"]):
            count = track_state_summary.get(label, 0)
            self._table.setItem(state_row, j, QTableWidgetItem(str(count)))

        # Set label for state row
        state_labels = ["State:", "", "", "Sum", ""]
        for j, txt in enumerate(state_labels):
            item = QTableWidgetItem(txt)
            item.setForeground(Qt.GlobalColor.gray)
            self._table.setItem(state_row, j, item)
