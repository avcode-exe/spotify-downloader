from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.models import DUPLICATE_POLICY_OPTIONS
from src.state import STATE_FILE

from .theme import (
    get_button_font,
    get_label_font,
    get_section_font,
    get_small_font,
)

BROWSER_OPTIONS: list[tuple[str, str]] = [
    ("Auto (try all)", "auto"),
    ("Chrome", "chrome"),
    ("Firefox", "firefox"),
    ("Edge", "edge"),
    ("Brave", "brave"),
    ("Vivaldi", "vivaldi"),
]

_DUPLICATE_POLICY_MAP = {code: label for label, code in DUPLICATE_POLICY_OPTIONS}


class SettingsPanel(QWidget):  # type: ignore[misc]
    """Settings panel with form layout for all download configuration."""

    settings_changed = Signal(dict)

    def __init__(self, initial_settings: dict[str, str] | None = None) -> None:
        super().__init__()
        self._settings = dict(initial_settings or {})
        self._loading = True
        self._build_ui()
        self._loading = False

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("Settings")
        title.setFont(get_section_font())
        title.setStyleSheet("color: #1DB954;")
        layout.addWidget(title)

        layout.addSpacing(8)

        # Format
        self._format_combo = self._make_combo_row(
            layout, ["mp3", "m4a", "flac", "opus", "ogg", "wav"], "Format"
        )
        self._format_combo.setCurrentText(self._settings.get("format", "mp3"))
        self._format_combo.currentTextChanged.connect(self._on_change)

        # Bitrate
        self._bitrate_combo = self._make_combo_row(
            layout,
            ["auto", "disable", "64k", "96k", "128k", "160k", "192k", "256k", "320k"],
            "Bitrate",
        )
        self._bitrate_combo.setCurrentText(self._settings.get("bitrate", "auto"))
        self._bitrate_combo.currentTextChanged.connect(self._on_change)

        # Audio Provider
        self._provider_combo = self._make_combo_row(
            layout,
            ["youtube-music", "youtube", "soundcloud", "bandcamp", "piped"],
            "Audio source",
        )
        self._provider_combo.setCurrentText(self._settings.get("audio_provider", "youtube-music"))
        self._provider_combo.currentTextChanged.connect(self._on_change)

        # Duplicate Policy
        policy_display = self._settings.get("duplicate_policy", "skip")
        policy_label = _DUPLICATE_POLICY_MAP.get(policy_display, "skip")
        self._policy_combo = self._make_combo_row(
            layout, [opt[1] for opt in DUPLICATE_POLICY_OPTIONS], "Duplicate policy"
        )
        self._policy_combo.setCurrentText(policy_label)
        self._policy_combo.currentTextChanged.connect(self._on_change)

        layout.addSpacing(8)

        # Proxy
        self._proxy_input = self._make_input_row(layout, "Proxy")
        self._proxy_input.setText(self._settings.get("proxy", ""))
        self._proxy_input.textChanged.connect(self._on_change)

        # Cookie file
        self._cookie_input = self._make_input_row(layout, "Cookie file")
        self._cookie_input.setText(self._settings.get("cookie_file", ""))
        self._cookie_input.textChanged.connect(self._on_change)

        # Cookie browser + extract button row
        cookie_row = QHBoxLayout()
        cookie_row.setSpacing(8)

        self._browser_combo = self._make_combo_row(
            cookie_row,
            [opt[0] for opt in BROWSER_OPTIONS],
            "Browser",
            is_inline=True,
        )
        browser_val = self._settings.get("browser", "auto")
        display_browser = {v: k for k, v in BROWSER_OPTIONS}.get(browser_val, "Auto (try all)")
        idx = self._browser_combo.findText(display_browser)
        if idx >= 0:
            self._browser_combo.setCurrentIndex(idx)
        self._browser_combo.currentTextChanged.connect(self._on_change)
        cookie_row.addWidget(self._browser_combo, 1)

        self._extract_btn = QPushButton("Extract")
        self._extract_btn.setObjectName("extractBtn")
        self._extract_btn.setFont(get_button_font())
        self._extract_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._extract_btn.clicked.connect(self._on_extract)
        cookie_row.addWidget(self._extract_btn)

        self._browse_cookie_btn = QPushButton("Browse\u2026")
        self._browse_cookie_btn.setObjectName("ghost")
        self._browse_cookie_btn.setFont(get_button_font())
        self._browse_cookie_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._browse_cookie_btn.clicked.connect(self._browse_cookie_file)
        cookie_row.addWidget(self._browse_cookie_btn)

        layout.addLayout(cookie_row)

        layout.addSpacing(16)

        # Divider
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #333333;")
        layout.addWidget(divider)

        # Active settings summary
        status = self._status_text()
        self._status_label = QLabel(status)
        self._status_label.setFont(get_label_font())
        self._status_label.setStyleSheet("color: #6A6A6A;")
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        # State file info
        state_label = QLabel(f"State: {STATE_FILE}")
        state_label.setFont(get_small_font())
        state_label.setStyleSheet("color: #555555;")
        state_label.setWordWrap(True)
        layout.addWidget(state_label)

        layout.addStretch()

    def _make_combo_row(
        self,
        parent_layout: QVBoxLayout | QHBoxLayout,
        options: list[str],
        label_text: str,
        *,
        is_inline: bool = False,
    ) -> QComboBox:
        """Create a labeled combo box and add it to the layout.

        If is_inline is True, the combo is added to a horizontal layout
        (for the Browser row which shares space with buttons). Otherwise
        it's added to a vertical layout as a full-width row.
        """
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        label = QLabel(label_text)
        label.setStyleSheet("color: #B3B3B3;")
        label.setFixedWidth(100)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(label)

        combo = QComboBox()
        combo.addItems(options)
        combo.setStyleSheet("""
            QComboBox {
                background-color: #282828;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 4px 12px;
                font-size: 11pt;
                min-height: 36px;
                color: #FFFFFF;
            }
            QComboBox::drop-down { border: none; width: 24px; }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #B3B3B3;
            }
            QComboBox QAbstractItemView {
                background-color: #1A1A1A;
                border: 1px solid #333333;
                selection-background-color: #282828;
                selection-color: #FFFFFF;
                outline: none;
                padding: 4px;
            }
        """)
        combo.setObjectName("settingsCombo")
        row.addWidget(combo, 1)

        if is_inline:
            parent_layout.addWidget(container, 1)
        else:
            parent_layout.addWidget(container)

        return combo

    def _make_input_row(self, layout: QVBoxLayout, tooltip: str) -> QLineEdit:
        """Create a labeled input field and add it to the layout."""
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)

        label = QLabel(tooltip)
        label.setStyleSheet("color: #B3B3B3;")
        label.setFixedWidth(100)
        label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        row.addWidget(label)

        input_field = QLineEdit()
        input_field.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #282828;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11pt;
                color: #FFFFFF;
            }
            QLineEdit:focus { border: 2px solid #1DB954; }
        """)
        input_field.setToolTip(tooltip)
        row.addWidget(input_field, 1)

        layout.addWidget(container, 0, Qt.AlignmentFlag.AlignLeft)
        return input_field

    def _browse_cookie_file(self) -> None:
        dialog = QFileDialog(self, "Select cookies.txt")
        dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        dialog.setNameFilters(["Cookie files (*.txt)", "All files (*)"])
        if dialog.exec():
            filename = dialog.selectedFiles()[0]
            self._cookie_input.setText(filename)
            self._on_change()

    def _on_extract(self) -> None:
        QMessageBox.information(
            self,
            "Cookie Extraction",
            "Cookie extraction is handled by spotDL internally.\n\n"
            "Open a terminal and run:\n"
            "  spotdl --extract-cookies\n\n"
            "Or use the browser extension method described in the README.",
        )

    def _on_change(self) -> None:
        if self._loading:
            return

        settings: dict[str, str] = {}
        format_text = self._format_combo.findText(self._format_combo.currentText())
        if format_text >= 0:
            settings["format"] = self._format_combo.itemText(format_text)

        bitrate_idx = self._bitrate_combo.findText(self._bitrate_combo.currentText())
        if bitrate_idx >= 0:
            settings["bitrate"] = self._bitrate_combo.itemText(bitrate_idx)

        provider_idx = self._provider_combo.findText(self._provider_combo.currentText())
        if provider_idx >= 0:
            settings["audio_provider"] = self._provider_combo.itemText(provider_idx)

        policy_idx = self._policy_combo.findText(self._policy_combo.currentText())
        if policy_idx >= 0:
            settings["duplicate_policy"] = self._policy_combo.itemText(policy_idx)

        settings["proxy"] = self._proxy_input.text().strip()
        settings["cookie_file"] = self._cookie_input.text().strip()

        browser_idx = self._browser_combo.findText(self._browser_combo.currentText())
        if browser_idx >= 0:
            browser_display = self._browser_combo.itemText(browser_idx)
            settings["browser"] = {v: k for k, v in BROWSER_OPTIONS}.get(
                browser_display, browser_display
            )

        self._settings.update(settings)
        self._status_label.setText(self._status_text())
        self.settings_changed.emit(dict(self._settings))

    def _status_text(self) -> str:
        settings = self._settings
        source = settings.get("audio_provider", "youtube-music").replace("-", " ").title()
        duplicate_policy = settings.get("duplicate_policy", "skip")
        if duplicate_policy not in _DUPLICATE_POLICY_MAP:
            duplicate_policy = "skip"
        parts = [
            settings.get("format", "mp3").upper(),
            settings.get("bitrate", "auto"),
            source,
            _DUPLICATE_POLICY_MAP[duplicate_policy],
        ]
        if settings.get("proxy"):
            parts.append("Proxy set")
        if settings.get("cookie_file"):
            parts.append("Cookies set")
        return "  \u2022  ".join(parts)

    def get_settings(self) -> dict[str, str]:
        self._on_change()
        return dict(self._settings)
