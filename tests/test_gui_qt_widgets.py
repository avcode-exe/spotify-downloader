from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from src.gui_qt.duplicates_panel import DuplicatesPanel
from src.gui_qt.history_panel import HistoryPanel
from src.gui_qt.home_panel import HomePanel
from src.gui_qt.log_panel import LogPanel
from src.gui_qt.preview_panel import PreviewPanel
from src.gui_qt.settings_panel import SettingsPanel
from src.gui_qt.sidebar import Sidebar


class TestHomePanel:
    def test_construction(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        assert panel is not None

    def test_buttons_exist(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        assert panel._download_btn.text() == "▶  Download"
        assert panel._fresh_btn.text() == "⟳  Fresh"
        assert panel._retry_btn.text() == "🔄  Retry Failed"
        assert panel._browse_btn.text() == "Browse"

    def test_button_cursors(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        assert panel._download_btn.cursor().shape() == Qt.CursorShape.PointingHandCursor
        assert panel._fresh_btn.cursor().shape() == Qt.CursorShape.PointingHandCursor
        assert panel._retry_btn.cursor().shape() == Qt.CursorShape.PointingHandCursor
        assert panel._browse_btn.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_input_cursors(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        assert panel._url_input.cursor().shape() == Qt.CursorShape.IBeamCursor
        assert panel._output_input.cursor().shape() == Qt.CursorShape.IBeamCursor

    def test_get_url(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        panel._url_input.setText("https://open.spotify.com/playlist/123")
        assert panel.get_url() == "https://open.spotify.com/playlist/123"

    def test_get_output_folder(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        assert panel.get_output_folder() == "./downloads"
        panel._output_input.setText("/tmp/out")
        assert panel.get_output_folder() == "/tmp/out"

    def test_set_output_folder(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        panel.set_output_folder("/new/out")
        assert panel._output_input.text() == "/new/out"

    def test_set_busy_disables_controls(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        panel.set_busy(True)
        assert not panel._download_btn.isEnabled()
        assert not panel._fresh_btn.isEnabled()
        assert not panel._retry_btn.isEnabled()
        assert not panel._browse_btn.isEnabled()
        assert not panel._url_input.isEnabled()
        assert not panel._output_input.isEnabled()
        panel.set_busy(False)
        assert panel._download_btn.isEnabled()
        assert panel._url_input.isEnabled()

    def test_update_status(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        panel.update_status("Downloading", "Track A", 0.5)
        assert panel._status_indicator.text() == "Downloading"
        assert panel._track_label.text() == "Track A"
        assert panel._progress_bar.value() == 50

    def test_set_retry_enabled(self, qt_app: QApplication) -> None:
        panel = HomePanel()
        assert not panel._retry_btn.isEnabled()
        panel.set_retry_enabled(True)
        assert panel._retry_btn.isEnabled()


class TestSettingsPanel:
    def test_construction(self, qt_app: QApplication) -> None:
        panel = SettingsPanel()
        assert panel is not None

    def test_get_settings_returns_dict(self, qt_app: QApplication) -> None:
        panel = SettingsPanel()
        settings = panel.get_settings()
        assert isinstance(settings, dict)
        assert "format" in settings
        assert "bitrate" in settings

    def test_inputs_have_ibeam_cursor(self, qt_app: QApplication) -> None:
        panel = SettingsPanel()
        assert panel._proxy_input.cursor().shape() == Qt.CursorShape.IBeamCursor
        assert panel._cookie_input.cursor().shape() == Qt.CursorShape.IBeamCursor

    def test_combo_boxes_exist(self, qt_app: QApplication) -> None:
        panel = SettingsPanel()
        assert panel._format_combo.count() > 0
        assert panel._bitrate_combo.count() > 0
        assert panel._provider_combo.count() > 0


class TestSidebar:
    def test_construction(self, qt_app: QApplication) -> None:
        sidebar = Sidebar()
        assert sidebar is not None

    def test_sections_exist(self, qt_app: QApplication) -> None:
        sidebar = Sidebar()
        assert sidebar._list.count() == len(Sidebar.SECTIONS)

    def test_list_cursor(self, qt_app: QApplication) -> None:
        sidebar = Sidebar()
        assert sidebar._list.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_button_cursors(self, qt_app: QApplication) -> None:
        sidebar = Sidebar()
        assert sidebar._cancel_btn.cursor().shape() == Qt.CursorShape.PointingHandCursor
        assert sidebar._quit_btn.cursor().shape() == Qt.CursorShape.PointingHandCursor

    def test_select_section(self, qt_app: QApplication) -> None:
        sidebar = Sidebar()
        sidebar.select_section("settings")
        assert sidebar._list.currentRow() == 1


class TestHistoryPanel:
    def test_construction(self, qt_app: QApplication) -> None:
        panel = HistoryPanel()
        assert panel is not None

    def test_table_cursor(self, qt_app: QApplication) -> None:
        panel = HistoryPanel()
        assert panel._table.cursor().shape() == Qt.CursorShape.PointingHandCursor


class TestPreviewPanel:
    def test_construction(self, qt_app: QApplication) -> None:
        panel = PreviewPanel()
        assert panel is not None

    def test_table_cursor(self, qt_app: QApplication) -> None:
        panel = PreviewPanel()
        assert panel._table.cursor().shape() == Qt.CursorShape.PointingHandCursor


class TestDuplicatesPanel:
    def test_construction(self, qt_app: QApplication) -> None:
        panel = DuplicatesPanel()
        assert panel is not None

    def test_tree_cursor(self, qt_app: QApplication) -> None:
        panel = DuplicatesPanel()
        assert panel._tree.cursor().shape() == Qt.CursorShape.PointingHandCursor


class TestLogPanel:
    def test_construction(self, qt_app: QApplication) -> None:
        panel = LogPanel()
        assert panel is not None

    def test_text_edit_cursor(self, qt_app: QApplication) -> None:
        panel = LogPanel()
        assert panel._text_edit.cursor().shape() == Qt.CursorShape.IBeamCursor
