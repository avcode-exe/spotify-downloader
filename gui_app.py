from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Spotify Playlist Downloader")
    app.setOrganizationName("SpotifyDownloader")

    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelIDW("SpotifyDownloader.App")
        except (OSError, AttributeError):
            pass

    icon_path = Path(__file__).resolve().parent / "assets" / "icon.ico"
    if not icon_path.exists():
        icon_path = Path(sys._MEIPASS or "") / "assets" / "icon.ico"
    icon = QIcon(str(icon_path))
    app.setWindowIcon(icon)

    from src.gui_qt.main_window import MainWindow

    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()

    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            LR_LOADFROMFILE = 0x00000010
            h_icon_small = ctypes.windll.user32.LoadImageW(
                None, str(icon_path), 1, 16, 16, LR_LOADFROMFILE
            )
            h_icon_big = ctypes.windll.user32.LoadImageW(
                None, str(icon_path), 1, 32, 32, LR_LOADFROMFILE
            )
            WM_SETICON = 0x80
            hwnd = wintypes.HWND(window.winId())
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 0, h_icon_small)
            ctypes.windll.user32.SendMessageW(hwnd, WM_SETICON, 1, h_icon_big)
        except (OSError, AttributeError):
            pass

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
