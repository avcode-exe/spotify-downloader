#!/usr/bin/env python3
"""Generate a minimal valid Windows icon file (1x1 black pixel)."""

from __future__ import annotations

import struct
import zlib


def _create_minimal_ico(path: str) -> None:
    width = 1
    height = 1
    bmp_size = 40 + width * height * 4
    icon_size = 6 + 16 + bmp_size
    data = bytearray(icon_size)

    # ICONDIR header
    struct.pack_into("<HHH", data, 0, 0, 1, 1)

    # ICONDIRENTRY
    offset = 6
    data[offset] = width
    data[offset + 1] = height
    struct.pack_into("<HHII", data, offset + 2, 1, 32, bmp_size, 16)

    # BMP header (BITMAPINFOHEADER)
    struct.pack_into("<IiiHHIIiiII", data, 16, 40, width, -height, 1, 32, 0, 0, 0, 0, 0, 0)

    # Pixel data (BGRA, black with full alpha)
    struct.pack_into("<BBBB", data, 56, 0, 0, 0, 255)

    # PNG-like compression for ICO (keep raw BMP for simplicity)
    # Many Windows versions accept raw BMP in ICO for small sizes.
    with open(path, "wb") as f:
        f.write(data)


if __name__ == "__main__":
    import os
    from pathlib import Path

    assets = Path("assets")
    assets.mkdir(exist_ok=True)
    icon_path = assets / "icon.ico"
    if not icon_path.exists():
        _create_minimal_ico(str(icon_path))
        print(f"Created minimal icon at {icon_path}")
    else:
        print(f"Icon already exists at {icon_path}")
