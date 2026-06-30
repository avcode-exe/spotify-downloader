"""Generate the application logo and Windows icon assets.

Produces:
  assets/logo.svg       - Vector logo for documentation / README
  assets/icon.ico       - Multi-resolution Windows icon (overwrites placeholder)
  assets/icon-256.png   - High-res preview PNG
"""

from __future__ import annotations

import io
import struct
from collections.abc import Iterable
from pathlib import Path


def _build_logo_svg() -> str:
    """Return an inline SVG for the Spotify Playlist Downloader logo.

    Design:
      - Spotify-green (#1DB954) circular badge
      - White download arrow (downward chevron + horizontal tray)
      - Works clearly down to 16×16 px
    """
    return """\
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1DB954"/>
      <stop offset="100%" stop-color="#1AA34A"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="4" stdDeviation="8" flood-color="#000000" flood-opacity="0.25"/>
    </filter>
  </defs>

  <!-- Outer rounded square background -->
  <rect x="4" y="4" width="504" height="504" rx="112" ry="112"
        fill="url(#bg)" filter="url(#shadow)"/>

  <!-- Inner subtle ring -->
  <circle cx="256" cy="210" r="130" fill="none" stroke="#FFFFFF" stroke-width="18" opacity="0.18"/>

  <!-- Download arrow group -->
  <g fill="#FFFFFF">
    <!-- Arrow shaft -->
    <rect x="178" y="290" width="156" height="36" rx="18" ry="18"/>
    <!-- Arrow head (chevron) -->
    <polygon points="256,120 382,260 330,260 330,370 182,370 182,260 130,260"/>
  </g>
</svg>
"""


def _render_png(size: int, dest: Path) -> None:
    """Render the logo at *size*×*size* pixels using only the stdlib + Pillow."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        raise SystemExit(
            "Pillow is required to generate the icon. Install it with: pip install Pillow"
        ) from None

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Scale factors (logo designed at 512×512)
    scale = size / 512.0
    pad = int(4 * scale)

    bg_size = size - pad * 2
    radius = int(112 * scale)

    # Draw rounded-square background
    draw.rounded_rectangle(
        [pad, pad, pad + bg_size, pad + bg_size],
        radius=radius,
        fill=(29, 185, 84),  # #1DB954
    )

    # Inner ring (subtle)
    inner_cx = size // 2
    inner_cy = int(210 * scale)
    inner_r = int(130 * scale)
    ring_width = max(1, int(18 * scale))
    draw.ellipse(
        [
            inner_cx - inner_r,
            inner_cy - inner_r,
            inner_cx + inner_r,
            inner_cy + inner_r,
        ],
        outline=(255, 255, 255, 46),  # ~18% opacity white
        width=ring_width,
    )

    # Arrow shaft
    shaft_x = int(178 * scale)
    shaft_y = int(290 * scale)
    shaft_w = int(156 * scale)
    shaft_h = max(1, int(36 * scale))
    shaft_radius = shaft_h // 2
    draw.rounded_rectangle(
        [shaft_x, shaft_y, shaft_x + shaft_w, shaft_y + shaft_h],
        radius=shaft_radius,
        fill=(255, 255, 255),
    )

    # Arrow head (chevron + top bar)
    # The chevron spans from roughly y=120 to y=260, x=130 to x=382
    # We draw it as a polygon
    head_points = [
        (int(256 * scale), int(120 * scale)),  # tip
        (int(382 * scale), int(260 * scale)),  # right shoulder
        (int(330 * scale), int(260 * scale)),  # right inner
        (int(330 * scale), int(370 * scale)),  # right bottom
        (int(182 * scale), int(370 * scale)),  # left bottom
        (int(182 * scale), int(260 * scale)),  # left inner
        (int(130 * scale), int(260 * scale)),  # left shoulder
    ]
    draw.polygon(head_points, fill=(255, 255, 255))

    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)


def _build_ico(png_sizes: Iterable[int], dest: Path) -> None:
    """Bundle multiple PNG sizes into a Windows .ico file.

    Constructs the ICO container manually so every requested resolution is
    preserved (Pillow's ICO saver silently drops non-standard sizes).
    """
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("Pillow is required: pip install Pillow") from None

    tmp_files: list[Path] = []
    try:
        for size in png_sizes:
            tmp = dest.with_suffix(f".tmp-{size}.png")
            _render_png(size, tmp)
            tmp_files.append(tmp)

        png_datas: list[bytes] = []
        for tmp in tmp_files:
            png_datas.append(tmp.read_bytes())

        # ICONDIR header: reserved(2) + type(2) + count(2)
        icondir = struct.pack("<HHH", 0, 1, len(png_datas))

        # Build ICONDIRENTRY list and collect image data
        entries = bytearray()
        image_data = bytearray()
        offset = 6 + 16 * len(png_datas)  # header + all entries

        for png_bytes in png_datas:
            img = Image.open(io.BytesIO(png_bytes))
            w, h = img.size
            # Width/height values: 0 means 256
            width_byte = 0 if w >= 256 else w
            height_byte = 0 if h >= 256 else h
            # ICONDIRENTRY: width(1) height(1) color(1) reserved(1) planes(2) bpp(2) size(4) offset(4)
            entry = struct.pack(
                "<BBBBHHII",
                width_byte,
                height_byte,
                0,  # color count (0 = truecolor)
                0,  # reserved
                1,  # planes
                32,  # bit count (RGBA)
                len(png_bytes),
                offset,
            )
            entries.extend(entry)
            image_data.extend(png_bytes)
            offset += len(png_bytes)

        dest.write_bytes(icondir + bytes(entries) + bytes(image_data))
    finally:
        for tmp in tmp_files:
            if tmp.exists():
                tmp.unlink()


def main() -> None:
    repo_root = Path(__file__).resolve().parent.parent
    assets_dir = repo_root / "assets"
    assets_dir.mkdir(exist_ok=True)

    svg_path = assets_dir / "logo.svg"
    svg_path.write_text(_build_logo_svg(), encoding="utf-8")
    print(f"Wrote {svg_path}")

    png_preview = assets_dir / "icon-256.png"
    _render_png(256, png_preview)
    print(f"Wrote {png_preview}")

    ico_path = assets_dir / "icon.ico"
    _build_ico((16, 32, 48, 64, 128, 256), ico_path)
    print(f"Wrote {ico_path}")


if __name__ == "__main__":
    main()
