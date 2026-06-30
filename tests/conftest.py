from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication


@pytest.fixture(scope="session")
def qt_app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def _isolate_state_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    state_file = tmp_path / "track_state.json"
    history_file = tmp_path / "download_history.json"
    settings_file = tmp_path / "settings.json"

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setattr("src.state.STATE_FILE", str(state_file))
    monkeypatch.setattr("src.state.HISTORY_FILE", str(history_file))
    monkeypatch.setattr("src.state.SETTINGS_FILE", str(settings_file))
