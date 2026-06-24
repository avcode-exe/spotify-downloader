from __future__ import annotations

import struct
from pathlib import Path


from generate_icon import _create_minimal_ico


class TestCreateMinimalIco:
    def test_creates_file(self, tmp_path: Path) -> None:
        icon_path = tmp_path / "icon.ico"
        _create_minimal_ico(str(icon_path))
        assert icon_path.exists()
        assert icon_path.stat().st_size > 0

    def test_file_starts_with_ico_header(self, tmp_path: Path) -> None:
        icon_path = tmp_path / "icon.ico"
        _create_minimal_ico(str(icon_path))
        with open(icon_path, "rb") as f:
            reserved, image_type, count = struct.unpack("<HHH", f.read(6))
        assert reserved == 0
        assert image_type == 1
        assert count == 1

    def test_creates_expected_size(self, tmp_path: Path) -> None:
        icon_path = tmp_path / "icon.ico"
        _create_minimal_ico(str(icon_path))
        with open(icon_path, "rb") as f:
            data = f.read()
        assert len(data) == 6 + 16 + 40 + 4  # header + ICONDIRENTRY + BITMAPINFO + pixel
