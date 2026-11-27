"""Paths and paging helpers for the bot showcase."""

from pathlib import Path

BOT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BOT_DIR / "assets"
REVIEWS_DIR = ASSETS_DIR / "reviews"
ABOUT_DIR = ASSETS_DIR / "about"
COACHING_VIDEO = ASSETS_DIR / "coaching12.mp4"
COACHING_VIDEO_WIDTH = 720
COACHING_VIDEO_HEIGHT = 1280
COACHING_VIDEO_DURATION = 137
ALBUM_MAX = 10
ADMIN_PHONE = "+998916628111"
ADMIN_CONTACT_NAME = "QUANTUM Psychology"
ADMIN_TELEGRAM_USERNAME = "aziza8111"
ADMIN_TELEGRAM_URL = "https://t.me/aziza8111"
SHOW_PREFIX = "show:"


def review_photos(dir: Path = REVIEWS_DIR) -> list[Path]:
    """Return JPEG review photos sorted by file name."""
    if not dir.is_dir():
        return []
    return sorted((path for path in dir.glob("*.jpg") if path.is_file() and path.suffix == ".jpg"), key=lambda path: path.name)


def about_photos(dir: Path = ABOUT_DIR) -> list[Path]:
    """Return JPEG coach photos sorted by file name."""
    if not dir.is_dir():
        return []
    return sorted((path for path in dir.glob("*.jpg") if path.is_file() and path.suffix == ".jpg"), key=lambda path: path.name)


def pages(items: list[Path], size: int = ALBUM_MAX) -> list[list[Path]]:
    """Split paths into album-sized pages."""
    if size <= 0:
        raise ValueError("page size must be positive")
    return [items[start:start + size] for start in range(0, len(items), size)]


def clamp_page(raw: str | int | None, total: int) -> int:
    """Return a valid one-based page, falling back to page one."""
    try:
        page = int(raw) if raw is not None else 1
    except ValueError:
        return 1
    return page if 1 <= page <= total else 1
