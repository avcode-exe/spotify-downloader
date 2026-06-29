from __future__ import annotations

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap


def _points(*coords: tuple[float, float]) -> list[QPoint]:
    """Convert float (x, y) pairs to QPoint list."""
    return [QPoint(int(round(x)), int(round(y))) for x, y in coords]


def _polygon(*coords: tuple[float, float]):
    """Create a QPoint list for drawPolygon."""
    return _points(*coords)


def _pen_width(p: QPainter, color: QColor | str, width: float) -> None:
    """Set pen color and width on a QPainter (PySide6 compat)."""
    p.setPen(QPen(QColor(color), width))


def create_svg_icon(name: str, color: str = "#FFFFFF", size: int = 24) -> QIcon:
    """Create an icon from inline SVG data."""
    svg_map = {
        "home": _svg_home,
        "settings": _svg_settings,
        "history": _svg_history,
        "preview": _svg_preview,
        "duplicates": _svg_duplicates,
        "log": _svg_log,
        "download": _svg_download,
        "fresh": _svg_refresh,
        "retry": _svg_retry,
        "cancel": _svg_cancel,
        "quit": _svg_quit,
        "browse": _svg_browse,
        "extract": _svg_extract,
        "play": _svg_play,
        "pause": _svg_pause,
        "search": _svg_search,
        "plus": _svg_plus,
        "minus": _svg_minus,
        "trash": _svg_trash,
        "check": _svg_check,
        "warning": _svg_warning,
        "error": _svg_error,
        "info": _svg_info,
        "chevron_right": _svg_chevron_right,
        "chevron_down": _svg_chevron_down,
        "close": _svg_close,
        "menu": _svg_menu,
        "copy": _svg_copy,
        "folder": _svg_folder,
    }
    svg_fn = svg_map.get(name)
    if svg_fn is None:
        return QIcon()
    return QIcon(svg_fn(color, size))


def _svg_home(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(color))
    p.drawPolygon(_polygon(
        (size * 0.15, size * 0.55),
        (size * 0.5, size * 0.15),
        (size * 0.85, size * 0.55),
        (size * 0.75, size * 0.55),
        (size * 0.75, size * 0.85),
        (size * 0.25, size * 0.85),
        (size * 0.25, size * 0.55),
    ))
    p.end()
    return pm


def _svg_settings(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    cx, cy = size / 2, size / 2
    r_outer = size * 0.4
    r_inner = size * 0.25
    p.drawEllipse(int(cx - r_outer), int(cy - r_outer), int(r_outer * 2), int(r_outer * 2))
    p.setBrush(Qt.GlobalColor.transparent)
    _pen_width(p, color, size * 0.08)
    p.drawEllipse(int(cx - r_inner), int(cy - r_inner), int(r_inner * 2), int(r_inner * 2))
    p.end()
    return pm


def _svg_history(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    cx, cy = size / 2, size / 2
    r = size * 0.35
    p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
    _pen_width(p, color, size * 0.08)
    p.setBrush(Qt.GlobalColor.transparent)
    p.drawLine(int(cx), int(cy), int(cx), int(cy - r * 0.7))
    p.drawLine(int(cx), int(cy), int(cx + r * 0.5), int(cy))
    p.end()
    return pm


def _svg_preview(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.15)
    p.setBrush(Qt.GlobalColor.transparent)
    p.drawEllipse(int(size * 0.2), int(size * 0.35), int(size * 0.6), int(size * 0.3))
    p.setBrush(QColor(color))
    p.drawEllipse(int(size * 0.4), int(size * 0.45), int(size * 0.2), int(size * 0.2))
    p.end()
    return pm


def _svg_duplicates(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    r = size * 0.3
    p.drawRect(int(size * 0.15), int(size * 0.2), int(r), int(r))
    p.setBrush(QColor("#888888"))
    p.drawRect(int(size * 0.35), int(size * 0.4), int(r), int(r))
    p.end()
    return pm


def _svg_log(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    w, h = size * 0.6, size * 0.7
    x, y = size * 0.2, size * 0.15
    p.drawRect(int(x), int(y), int(w), int(h))
    p.setBrush(QColor("#121212"))
    p.drawRect(int(x + w * 0.15), int(y + h * 0.2), int(w * 0.7), int(h * 0.08))
    p.drawRect(int(x + w * 0.15), int(y + h * 0.4), int(w * 0.7), int(h * 0.08))
    p.drawRect(int(x + w * 0.15), int(y + h * 0.6), int(w * 0.5), int(h * 0.08))
    p.end()
    return pm


def _svg_download(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    cx, cy = size / 2, size / 2
    p.drawPolygon(_polygon(
        (cx, cy - size * 0.35),
        (cx - size * 0.15, cy - size * 0.15),
        (cx - size * 0.15, cy + size * 0.15),
        (cx - size * 0.35, cy + size * 0.15),
        (cx + size * 0.35, cy + size * 0.15),
        (cx + size * 0.15, cy + size * 0.15),
        (cx + size * 0.15, cy - size * 0.15),
    ))
    p.setBrush(c)
    p.drawRect(int(cx - size * 0.3), int(cy + size * 0.35), int(size * 0.6), int(size * 0.08))
    p.end()
    return pm


def _svg_refresh(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.12)
    p.setBrush(Qt.GlobalColor.transparent)
    cx, cy = size / 2, size / 2
    r = size * 0.3
    p.drawArc(int(cx - r), int(cy - r), int(r * 2), int(r * 2), 30 * 16, 270 * 16)
    p.drawLine(int(cx + r * 0.86), int(cy - r * 0.5), int(cx + r * 0.86 + size * 0.12), int(cy - r * 0.5 + size * 0.12))
    p.drawLine(int(cx + r * 0.86), int(cy - r * 0.5), int(cx + r * 0.86 + size * 0.12), int(cy - r * 0.5 - size * 0.12))
    p.end()
    return pm


def _svg_retry(color: str, size: int) -> QPixmap:
    return _svg_refresh(color, size)


def _svg_cancel(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    s = size * 0.35
    p.drawRect(int(size / 2 - s), int(size / 2 - s), int(s * 2), int(s * 2))
    p.end()
    return pm


def _svg_quit(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.12)
    p.setBrush(Qt.GlobalColor.transparent)
    cx, cy = size / 2, size / 2
    r = size * 0.3
    p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
    p.drawLine(int(cx - r * 0.6), int(cy - r * 0.6), int(cx + r * 0.6), int(cy + r * 0.6))
    p.drawLine(int(cx + r * 0.6), int(cy - r * 0.6), int(cx - r * 0.6), int(cy + r * 0.6))
    p.end()
    return pm


def _svg_browse(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    p.drawPolygon(_polygon(
        (size * 0.1, size * 0.35),
        (size * 0.3, size * 0.35),
        (size * 0.35, size * 0.45),
        (size * 0.9, size * 0.45),
        (size * 0.9, size * 0.85),
        (size * 0.1, size * 0.85),
    ))
    p.end()
    return pm


def _svg_extract(color: str, size: int) -> QPixmap:
    return _svg_download(color, size)


def _svg_play(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    cx, cy = size / 2, size / 2
    p.drawPolygon(_polygon(
        (cx - size * 0.1, cy - size * 0.3),
        (cx - size * 0.1, cy + size * 0.3),
        (cx + size * 0.3, cy),
    ))
    p.end()
    return pm


def _svg_pause(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    w = size * 0.12
    h = size * 0.35
    p.drawRect(int(size / 2 - w * 1.5 - h / 2), int(size / 2 - h / 2), int(w), int(h))
    p.drawRect(int(size / 2 + w * 0.5 - h / 2), int(size / 2 - h / 2), int(w), int(h))
    p.end()
    return pm


def _svg_search(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.12)
    p.setBrush(Qt.GlobalColor.transparent)
    cx, cy = size / 2, size / 2
    r = size * 0.28
    p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
    p.drawLine(int(cx + r * 0.5), int(cy + r * 0.5), int(cx + r * 0.85), int(cy + r * 0.85))
    p.end()
    return pm


def _svg_plus(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.15)
    p.setBrush(Qt.GlobalColor.transparent)
    cx, cy = size / 2, size / 2
    p.drawLine(int(cx), int(cy - size * 0.3), int(cx), int(cy + size * 0.3))
    p.drawLine(int(cx - size * 0.3), int(cy), int(cx + size * 0.3), int(cy))
    p.end()
    return pm


def _svg_minus(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.15)
    p.setBrush(Qt.GlobalColor.transparent)
    cx, cy = size / 2, size / 2
    p.drawLine(int(cx - size * 0.3), int(cy), int(cx + size * 0.3), int(cy))
    p.end()
    return pm


def _svg_trash(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.1)
    p.setBrush(Qt.GlobalColor.transparent)
    p.drawLine(int(size * 0.2), int(size * 0.3), int(size * 0.8), int(size * 0.3))
    p.drawLine(int(size * 0.3), int(size * 0.3), int(size * 0.3), int(size * 0.85))
    p.drawLine(int(size * 0.7), int(size * 0.3), int(size * 0.7), int(size * 0.85))
    p.drawLine(int(size * 0.35), int(size * 0.3), int(size * 0.35), int(size * 0.2))
    p.drawLine(int(size * 0.65), int(size * 0.3), int(size * 0.65), int(size * 0.2))
    p.drawLine(int(size * 0.5), int(size * 0.2), int(size * 0.5), int(size * 0.85))
    p.end()
    return pm


def _svg_check(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.15)
    p.setBrush(Qt.GlobalColor.transparent)
    p.drawLines(_points(
        (size * 0.15, size * 0.5),
        (size * 0.35, size * 0.7),
        (size * 0.85, size * 0.3),
    ))
    p.end()
    return pm


def _svg_warning(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    cx, cy = size / 2, size / 2
    r = size * 0.38
    p.drawPolygon(_polygon(
        (cx, cy - r),
        (cx - r * 0.9, cy + r * 0.6),
        (cx + r * 0.9, cy + r * 0.6),
    ))
    p.setBrush(Qt.GlobalColor.transparent)
    _pen_width(p, "#0A0A0A", size * 0.08)
    p.drawLine(int(cx), int(cy - r * 0.4), int(cx), int(cy + r * 0.2))
    p.end()
    return pm


def _svg_error(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    cx, cy = size / 2, size / 2
    r = size * 0.35
    p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
    p.setBrush(Qt.GlobalColor.transparent)
    _pen_width(p, "#FFFFFF", size * 0.12)
    p.drawLine(int(cx - r * 0.5), int(cy - r * 0.5), int(cx + r * 0.5), int(cy + r * 0.5))
    p.drawLine(int(cx + r * 0.5), int(cy - r * 0.5), int(cx - r * 0.5), int(cy + r * 0.5))
    p.end()
    return pm


def _svg_info(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    cx, cy = size / 2, size / 2
    r = size * 0.35
    p.drawEllipse(int(cx - r), int(cy - r), int(r * 2), int(r * 2))
    p.setBrush(Qt.GlobalColor.transparent)
    _pen_width(p, "#FFFFFF", size * 0.12)
    p.drawLine(int(cx), int(cy - r * 0.5), int(cx), int(cy + r * 0.1))
    p.end()
    return pm


def _svg_chevron_right(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.15)
    p.setBrush(Qt.GlobalColor.transparent)
    p.drawLines(_points(
        (size * 0.35, size * 0.2),
        (size * 0.65, size * 0.5),
        (size * 0.35, size * 0.8),
    ))
    p.end()
    return pm


def _svg_chevron_down(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.15)
    p.setBrush(Qt.GlobalColor.transparent)
    p.drawLines(_points(
        (size * 0.2, size * 0.35),
        (size * 0.5, size * 0.65),
        (size * 0.8, size * 0.35),
    ))
    p.end()
    return pm


def _svg_close(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.15)
    p.setBrush(Qt.GlobalColor.transparent)
    p.drawLines(_points(
        (size * 0.2, size * 0.2),
        (size * 0.8, size * 0.8),
        (size * 0.8, size * 0.2),
        (size * 0.2, size * 0.8),
    ))
    p.end()
    return pm


def _svg_menu(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    _pen_width(p, color, size * 0.12)
    p.setBrush(Qt.GlobalColor.transparent)
    for i in range(3):
        y = size * 0.25 + i * size * 0.25
        p.drawLine(int(size * 0.15), int(y), int(size * 0.85), int(y))
    p.end()
    return pm


def _svg_copy(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    p.drawRect(int(size * 0.25), int(size * 0.25), int(size * 0.5), int(size * 0.55))
    p.setBrush(QColor("#888888"))
    p.drawRect(int(size * 0.2), int(size * 0.2), int(size * 0.5), int(size * 0.55))
    p.end()
    return pm


def _svg_folder(color: str, size: int) -> QPixmap:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setPen(Qt.PenStyle.NoPen)
    c = QColor(color)
    p.setBrush(c)
    p.drawPolygon(_polygon(
        (size * 0.1, size * 0.35),
        (size * 0.3, size * 0.35),
        (size * 0.35, size * 0.45),
        (size * 0.9, size * 0.45),
        (size * 0.9, size * 0.85),
        (size * 0.1, size * 0.85),
    ))
    p.end()
    return pm
