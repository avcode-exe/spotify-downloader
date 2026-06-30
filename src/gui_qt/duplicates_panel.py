from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QHeaderView,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from src.models import DuplicateGroup

from .theme import SPOTIFY_WHITE, get_section_font


class DuplicatesPanel(QWidget):
    """Duplicates panel showing duplicate groups in a tree view."""

    def __init__(self) -> None:
        super().__init__()
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Duplicates")
        title.setFont(get_section_font())
        title.setStyleSheet(
            f"color: {SPOTIFY_WHITE.name() if hasattr(SPOTIFY_WHITE, 'name') else '#FFFFFF'};"
        )
        layout.addWidget(title)

        self._tree = QTreeWidget()
        self._tree.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._tree.setHeaderLabels(["Reason", "Key", "Action", "File"])
        self._tree.setColumnWidth(0, 180)
        self._tree.setColumnWidth(1, 200)
        self._tree.setColumnWidth(2, 80)
        self._tree.header().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                border-radius: 6px;
                gridline-color: #333333;
            }
            QTreeWidget::item { padding: 4px 0; }
            QTreeWidget::item:selected {
                background-color: #282828;
                color: #FFFFFF;
            }
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
        layout.addWidget(self._tree)

    def render(self, duplicate_groups: list[DuplicateGroup]) -> None:
        self._tree.clear()

        if not duplicate_groups:
            empty_item = QTreeWidgetItem(self._tree)
            empty_item.setText(0, "No duplicate groups found. Run Preview first.")
            empty_item.setForeground(0, Qt.GlobalColor.gray)
            return

        for group in duplicate_groups:
            keep = group.keep
            action = "Move" if group.safe_to_move else "Review"
            action_color = Qt.GlobalColor.green if group.safe_to_move else Qt.GlobalColor.yellow

            # Group header
            group_item = QTreeWidgetItem(self._tree)
            group_item.setText(0, group.reason)
            group_item.setText(1, group.key)
            group_item.setText(2, action)
            group_item.setForeground(2, action_color)
            group_item.setExpanded(True)

            # Child items
            for track in group.tracks:
                if track is keep:
                    keep_item = QTreeWidgetItem(group_item)
                    keep_item.setText(0, "keep")
                    keep_item.setText(3, track.path.name)
                    keep_item.setForeground(0, Qt.GlobalColor.green)
                else:
                    child = QTreeWidgetItem(group_item)
                    child.setText(0, action.lower())
                    child.setText(3, track.path.name)
                    child.setForeground(0, Qt.GlobalColor.gray)
