from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QFrame,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .icons import create_svg_icon
from .theme import get_button_font


class Sidebar(QWidget):
    """Left sidebar with navigation items."""

    section_changed = Signal(str)
    cancel_clicked = Signal()
    quit_clicked = Signal()

    SECTIONS = [
        ("home", "Home", "Home \u2014 Download playlists and tracks"),
        ("settings", "Settings", "Configure format, bitrate, proxy, cookies"),
        ("history", "History", "View past download sessions"),
        ("preview", "Preview", "Scan local folder for files and duplicates"),
        ("duplicates", "Duplicates", "Review and manage duplicate files"),
        ("log", "Log", "Real-time download progress and status"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(200)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.setStyleSheet("#sidebar { background-color: #181818; }")
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # App title
        title_frame = QFrame()
        title_layout = QVBoxLayout(title_frame)
        title_layout.setContentsMargins(16, 16, 16, 12)
        title_layout.setSpacing(2)

        from PySide6.QtWidgets import QLabel

        name_lbl = QLabel("Spotify Downloader")
        name_lbl.setStyleSheet("font-size: 13pt; font-weight: bold; color: #FFFFFF;")
        name_lbl.setObjectName("appName")
        title_layout.addWidget(name_lbl)

        ver_lbl = QLabel("v0.1.1")
        ver_lbl.setStyleSheet("font-size: 8pt; color: #6A6A6A;")
        title_layout.addWidget(ver_lbl)

        layout.addWidget(title_frame)

        # Divider
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #333333;")
        layout.addWidget(divider)

        # Navigation list
        from PySide6.QtWidgets import QListWidget, QListWidgetItem

        self._list = QListWidget()
        self._list.setObjectName("sidebar")
        self._list.setSpacing(4)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        for section_id, display_name, tooltip in self.SECTIONS:
            item = QListWidgetItem(
                create_svg_icon(section_id, color="#B3B3B3", size=18), display_name
            )
            item.setData(Qt.ItemDataRole.UserRole, section_id)
            item.setToolTip(tooltip)
            item.setSizeHint(item.sizeHint())
            self._list.addItem(item)

        self._list.setCurrentRow(0)
        self._list.currentRowChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list, 1)

        # Bottom actions
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(8, 8, 8, 8)
        btn_layout.setSpacing(4)

        # Cancel button
        self._cancel_btn = QPushButton("⏹  Cancel")
        self._cancel_btn.setFont(get_button_font())
        self._cancel_btn.setProperty("type", "ghost")
        self._cancel_btn.setEnabled(False)
        self._cancel_btn.setMinimumHeight(34)
        self._cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #333333;
                border-radius: 6px;
                color: #555555;
                padding: 8px 16px;
            }
            QPushButton:enabled {
                background-color: #333333;
                color: #B3B3B3;
                border-color: #555555;
            }
            QPushButton:hover:enabled {
                background-color: #444444;
                color: #FFFFFF;
            }
        """)
        btn_layout.addWidget(self._cancel_btn)

        # Quit button
        self._quit_btn = QPushButton("✕  Quit")
        self._quit_btn.setFont(get_button_font())
        self._quit_btn.setMinimumHeight(34)
        pal = self._quit_btn.palette()
        pal.setColor(QPalette.ColorRole.Button, QColor("#E91429"))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor("#FFFFFF"))
        self._quit_btn.setPalette(pal)
        self._quit_btn.setStyleSheet("""
            QPushButton {
                background-color: #E91429;
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
            }
        """)
        self._quit_btn.clicked.connect(lambda: self.quit_clicked.emit())
        btn_layout.addWidget(self._quit_btn)

        layout.addWidget(btn_container)

    def _on_selection_changed(self, row: int) -> None:
        item = self._list.item(row)
        if item is not None:
            section_id = item.data(Qt.ItemDataRole.UserRole)
            if section_id:
                self.section_changed.emit(section_id)

    def select_section(self, section_id: str) -> None:
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == section_id:
                self._list.setCurrentRow(i)
                break

    def set_active_icon_color(self, section_id: str, active: bool) -> None:
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item and item.data(Qt.ItemDataRole.UserRole) == section_id:
                color = "#1DB954" if active else "#B3B3B3"
                item.setIcon(create_svg_icon(section_id, color=color, size=18))
                break

    def set_busy(self, busy: bool) -> None:
        self._cancel_btn.setEnabled(busy)
