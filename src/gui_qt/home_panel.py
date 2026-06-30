from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from .theme import get_button_font, get_label_font, get_section_font


class HomePanel(QWidget):
    """Home panel with URL input, output folder, and download controls."""

    download_clicked = Signal()
    fresh_clicked = Signal()
    retry_clicked = Signal()
    browse_output_clicked = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._busy = False
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        title = QLabel("Spotify Playlist Downloader")
        title.setFont(get_section_font())
        title.setStyleSheet("color: #FFFFFF; font-size: 15pt; font-weight: bold;")
        layout.addWidget(title)

        subtitle = QLabel("Paste a public playlist or track URL and press Download")
        subtitle.setFont(get_label_font())
        subtitle.setStyleSheet("color: #6A6A6A;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        layout.addSpacing(4)

        # URL Input
        url_label = QLabel("Playlist or Track URL")
        url_label.setFont(get_label_font())
        url_label.setStyleSheet("color: #B3B3B3;")
        layout.addWidget(url_label)

        self._url_input = QLineEdit()
        self._url_input.setPlaceholderText("https://open.spotify.com/playlist/... or /track/...")
        self._url_input.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self._url_input.setStyleSheet("""
            QLineEdit {
                background-color: #282828;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11pt;
                color: #FFFFFF;
            }
            QLineEdit:focus { border: 2px solid #1DB954; }
            QLineEdit:disabled { background-color: #404040; color: #555555; border-color: #404040; }
        """)
        layout.addWidget(self._url_input)

        # Output Folder
        output_label = QLabel("Output folder")
        output_label.setFont(get_label_font())
        output_label.setStyleSheet("color: #B3B3B3;")
        layout.addWidget(output_label)

        output_row = QHBoxLayout()
        output_row.setSpacing(8)

        self._output_input = QLineEdit()
        self._output_input.setText("./downloads")
        self._output_input.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        self._output_input.setStyleSheet(self._url_input.styleSheet())
        output_row.addWidget(self._output_input, 1)

        self._browse_btn = QPushButton("Browse")
        self._browse_btn.setFont(get_button_font())
        self._browse_btn.setMinimumWidth(90)
        self._browse_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._browse_btn.clicked.connect(lambda: self.browse_output_clicked.emit())
        output_row.addWidget(self._browse_btn)

        layout.addLayout(output_row)

        layout.addSpacing(16)

        # Actions Card
        actions_card = QFrame()
        actions_card.setObjectName("card")
        actions_card_layout = QVBoxLayout(actions_card)
        actions_card_layout.setContentsMargins(16, 16, 16, 16)
        actions_card_layout.setSpacing(10)

        actions_title = QLabel("Actions")
        actions_title.setFont(get_section_font())
        actions_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        actions_card_layout.addWidget(actions_title)

        # Primary actions: Download | Fresh | Retry Failed
        primary_row = QHBoxLayout()
        primary_row.setSpacing(8)

        self._download_btn = QPushButton("▶  Download")
        self._download_btn.setFont(get_button_font())
        self._download_btn.setMinimumHeight(38)
        self._download_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._download_btn.setProperty("type", "primary")
        self._download_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._download_btn.clicked.connect(lambda: self.download_clicked.emit())
        primary_row.addWidget(self._download_btn)

        self._fresh_btn = QPushButton("⟳  Fresh")
        self._fresh_btn.setFont(get_button_font())
        self._fresh_btn.setMinimumHeight(38)
        self._fresh_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._fresh_btn.setProperty("type", "secondary")
        self._fresh_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._fresh_btn.clicked.connect(lambda: self.fresh_clicked.emit())
        primary_row.addWidget(self._fresh_btn)

        self._retry_btn = QPushButton("🔄  Retry Failed")
        self._retry_btn.setFont(get_button_font())
        self._retry_btn.setMinimumHeight(38)
        self._retry_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._retry_btn.setEnabled(False)
        self._retry_btn.setProperty("type", "secondary")
        self._retry_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._retry_btn.clicked.connect(lambda: self.retry_clicked.emit())
        primary_row.addWidget(self._retry_btn)

        actions_card_layout.addLayout(primary_row)
        layout.addWidget(actions_card)

        # Progress Card
        progress_card = QFrame()
        progress_card.setObjectName("card")
        progress_card_layout = QVBoxLayout(progress_card)
        progress_card_layout.setContentsMargins(16, 16, 16, 16)
        progress_card_layout.setSpacing(6)

        progress_header = QHBoxLayout()
        progress_header.setSpacing(8)

        progress_title = QLabel("Progress")
        progress_title.setFont(get_section_font())
        progress_title.setStyleSheet("color: #FFFFFF; background: transparent;")
        progress_header.addWidget(progress_title)

        self._status_indicator = QLabel("Ready")
        self._status_indicator.setFont(get_label_font())
        self._status_indicator.setStyleSheet("color: #1DB954; background: transparent;")
        progress_header.addWidget(self._status_indicator, 1)

        progress_card_layout.addLayout(progress_header)

        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedHeight(14)
        self._progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #282828;
                border: none;
                border-radius: 7px;
                text-align: center;
                padding: 0 8px;
                color: #FFFFFF;
                font-size: 9pt;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #1DB954;
                border-radius: 7px;
                padding: 0;
            }
        """)
        self._progress_bar.setValue(0)
        progress_card_layout.addWidget(self._progress_bar)

        self._track_label = QLabel("\u2014")
        self._track_label.setFont(get_label_font())
        self._track_label.setStyleSheet("color: #B3B3B3; background: transparent;")
        self._track_label.setWordWrap(True)
        progress_card_layout.addWidget(self._track_label)

        layout.addWidget(progress_card)

        layout.addStretch()

    def set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._download_btn.setEnabled(not busy)
        self._fresh_btn.setEnabled(not busy)
        self._retry_btn.setEnabled(not busy)
        self._browse_btn.setEnabled(not busy)
        self._url_input.setEnabled(not busy)
        self._output_input.setEnabled(not busy)

    def update_status(self, status: str, track: str = "\u2014", progress: float = 0.0) -> None:
        self._status_indicator.setText(status)
        self._track_label.setText(track)
        self._progress_bar.setValue(int(progress * 100))

    def set_retry_enabled(self, enabled: bool) -> None:
        self._retry_btn.setEnabled(enabled)

    def get_progress_fraction(self) -> float:
        return self._progress_bar.value() / 100.0

    def set_progress_fraction(self, fraction: float) -> None:
        self._progress_bar.setValue(int(fraction * 100))

    def get_url(self) -> str:
        return self._url_input.text().strip()

    def get_output_folder(self) -> str:
        return self._output_input.text().strip() or "./downloads"

    def set_output_folder(self, folder: str) -> None:
        self._output_input.setText(folder)
