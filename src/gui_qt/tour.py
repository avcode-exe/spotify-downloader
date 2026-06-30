from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class TourOverlay(QWidget):  # type: ignore[misc]
    """Overlay that guides users through the app on first launch."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._steps: list[dict[str, Any]] = []
        self._current_step = 0
        self._build_ui()

    def set_steps(self, steps: list[dict[str, Any]]) -> None:
        self._steps = steps
        self._current_step = 0
        self._show_step(0)

    def _show_step(self, index: int) -> None:
        if index >= len(self._steps):
            self.close()
            return

        step = self._steps[index]
        target = step.get("target")
        title = step.get("title", "")
        text = step.get("text", "")

        self._current_step = index

        # Update content
        self._title_label.setText(title)
        self._text_label.setText(text)

        # Position tooltip near target
        if target is not None:
            geo = target.geometry()
            parent_geo = self.geometry()
            x = parent_geo.x() + geo.x()
            y = parent_geo.y() + geo.y()

            pos = step.get("position", "right")
            if pos == "right":
                x += geo.width() + 16
            elif pos == "left":
                x -= 300
            else:
                y += geo.height() + 16

            self.setGeometry(x, y, 280, 150)
        else:
            parent = self.parent()
            assert parent is not None
            self.setGeometry(
                parent.geometry().width() // 2 - 150,
                parent.geometry().height() // 2 - 80,
                300,
                160,
            )

        # Show/hide navigation buttons
        self._prev_btn.setVisible(index > 0)
        self._next_btn.setText("Finish" if index == len(self._steps) - 1 else "Next")

    def _next(self) -> None:
        self._show_step(self._current_step + 1)

    def _prev(self) -> None:
        self._show_step(self._current_step - 1)

    def _close(self) -> None:
        self.close()
        self.setParent(None)
        self.deleteLater()

    def _build_ui(self) -> None:
        from .theme import get_button_font, get_label_font

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._title_label = QLabel()
        self._title_label.setFont(get_label_font())
        self._title_label.setStyleSheet("font-weight: bold; color: #FFFFFF;")
        layout.addWidget(self._title_label)

        self._text_label = QLabel()
        self._text_label.setFont(get_label_font())
        self._text_label.setStyleSheet("color: #B3B3B3;")
        self._text_label.setWordWrap(True)
        layout.addWidget(self._text_label)

        # Spacer
        spacer = QWidget()
        spacer.setFixedHeight(8)
        layout.addWidget(spacer)

        # Navigation
        nav = QVBoxLayout()
        nav.setSpacing(4)

        self._prev_btn = QPushButton("Previous")
        self._prev_btn.setFont(get_button_font())
        self._prev_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._prev_btn.setObjectName("ghost")
        self._prev_btn.clicked.connect(self._prev)
        nav.addWidget(self._prev_btn)

        btn_row = QHBoxLayout()
        self._next_btn = QPushButton("Next")
        self._next_btn.setFont(get_button_font())
        self._next_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._next_btn.setObjectName("primary")
        self._next_btn.clicked.connect(self._next)
        btn_row.addWidget(self._next_btn)

        self._skip_btn = QPushButton("Skip Tour")
        self._skip_btn.setFont(get_button_font())
        self._skip_btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self._skip_btn.setObjectName("ghost")
        self._skip_btn.clicked.connect(self._close)
        btn_row.addWidget(self._skip_btn)

        nav.addLayout(btn_row)
        layout.addLayout(nav)

        self.setStyleSheet("""
            QWidget {
                background-color: #181818;
                border: 1px solid #333333;
                border-radius: 10px;
            }
        """)
