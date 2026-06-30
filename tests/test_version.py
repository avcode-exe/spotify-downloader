from __future__ import annotations

import re
import sys
from importlib import import_module
from pathlib import Path

import pytest

from scripts.write_version_include import write_version_include
from src import __version__


class TestVersionConstant:
    def test_is_string(self) -> None:
        assert isinstance(__version__, str)

    def test_format_matches_semver(self) -> None:
        # Loose PEP 440 ``N.N.N`` so partial forms like ``0.1`` fail too.
        assert re.match(r"^\d+\.\d+\.\d+([\-+].+)?$", __version__), (
            f"unexpected version format: {__version__!r}"
        )


class TestWriteVersionInclude:
    def test_function_emits_isspp_define(self, tmp_path: pytest.TempPathFactory) -> None:
        target = tmp_path / "version.iss"
        write_version_include("9.9.9", target)
        content = target.read_text(encoding="utf-8")
        assert '#define MyAppVersion "9.9.9"' in content
        assert "Auto-generated" in content

    def test_function_creates_parent_dir(self, tmp_path: pytest.TempPathFactory) -> None:
        target = tmp_path / "nested" / "deeper" / "_version.iss"
        write_version_include("1.0.0", target)
        assert target.exists()

    def test_function_uses_current_version(self, tmp_path: pytest.TempPathFactory) -> None:
        target = tmp_path / "_version.iss"
        write_version_include(__version__, target)
        content = target.read_text(encoding="utf-8")
        assert f'#define MyAppVersion "{__version__}"' in content


class TestProjectConsistency:
    def test_installer_reads_generated_include(self) -> None:
        # installer.iss must `#include` the generated file rather than
        # hardcoding MyAppVersion, otherwise we drift from __version__.
        from pathlib import Path

        installer_iss = Path(__file__).resolve().parent.parent / "installer.iss"
        text = installer_iss.read_text(encoding="utf-8")
        assert '#include "installer\\_version.iss"' in text, (
            "installer.iss must include installer\\_version.iss so MyAppVersion "
            "stays in sync with src.__version__"
        )
        # Guard against reverting to a hardcoded literal MyAppVersion.
        assert not re.search(r"#define\s+MyAppVersion\b", text), (
            "MyAppVersion should be defined via the generated include, not inline"
        )

    def test_gitignore_excludes_generated_artifact(self) -> None:
        gitignore = Path(__file__).resolve().parent.parent / ".gitignore"
        text = gitignore.read_text(encoding="utf-8")
        # .gitignore uses Unix-style forward slashes (cross-platform convention).
        assert "installer/_version.iss" in text


def test_script_module_is_importable() -> None:
    # The build scripts invoke `python -m scripts.write_version_include`,
    # so the module must be discoverable as a regular package module.
    importlib_module = import_module("scripts.write_version_include")
    assert hasattr(importlib_module, "main")
    assert hasattr(importlib_module, "write_version_include")
    assert sys.modules["scripts.write_version_include"] is importlib_module
