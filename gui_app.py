from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# High-DPI is enabled by default in Qt 6; set rounding policy only
QApplication.setHighDpiScaleFactorRoundingPolicy(
    Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Spotify Playlist Downloader")
    app.setOrganizationName("SpotifyDownloader")

    from src.gui_qt.main_window import MainWindow

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
