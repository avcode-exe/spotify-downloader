from __future__ import annotations

import importlib.util
import sys
from unittest.mock import MagicMock

import pytest

from installer import (
    _ask_yes_no,
    _install_packages,
    _is_installed,
)


class TestIsInstalled:
    def test_detects_installed_package(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(importlib.util, "find_spec", lambda name: MagicMock())
        assert _is_installed("customtkinter>=5.2.0") is True

    def test_detects_missing_package(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(importlib.util, "find_spec", lambda name: None)
        assert _is_installed("customtkinter>=5.2.0") is False

    def test_strips_version_constraints(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []

        def fake_find_spec(name: str):
            calls.append(name)
            return MagicMock()

        monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
        _is_installed("customtkinter>=5.2.0")
        assert calls == ["customtkinter"]

    def test_strips_upper_bound(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[str] = []

        def fake_find_spec(name: str):
            calls.append(name)
            return MagicMock()

        monkeypatch.setattr(importlib.util, "find_spec", fake_find_spec)
        _is_installed("textual>=2.0.0,<3.0.0")
        assert calls == ["textual"]


class TestInstallPackages:
    def test_calls_pip_install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        calls: list[list[str]] = []

        def fake_call(cmd: list[str]) -> int:
            calls.append(cmd)
            return 0

        monkeypatch.setattr(sys, "executable", "/usr/bin/python")
        monkeypatch.setattr("subprocess.call", fake_call)
        result = _install_packages(["customtkinter>=5.2.0", "textual>=2.0.0"])
        assert result == 0
        assert len(calls) == 1
        assert calls[0][0:4] == ["/usr/bin/python", "-m", "pip", "install"]


class TestAskYesNo:
    def test_yes_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        inputs = ["y"]
        monkeypatch.setattr("builtins.input", lambda prompt="": inputs.pop(0))
        assert _ask_yes_no("Install?") is True

    def test_no_input(self, monkeypatch: pytest.MonkeyPatch) -> None:
        inputs = ["n"]
        monkeypatch.setattr("builtins.input", lambda prompt="": inputs.pop(0))
        assert _ask_yes_no("Install?") is False

    def test_empty_defaults_to_no(self, monkeypatch: pytest.MonkeyPatch) -> None:
        inputs = [""]
        monkeypatch.setattr("builtins.input", lambda prompt="": inputs.pop(0))
        assert _ask_yes_no("Install?") is False

    def test_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        for answer in ("Y", "YES", "n", "NO"):
            monkeypatch.setattr("builtins.input", lambda prompt="", ans=answer: ans)
            if answer in ("Y", "YES"):
                assert _ask_yes_no("Install?") is True
            else:
                assert _ask_yes_no("Install?") is False
