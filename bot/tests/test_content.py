"""Showcase content path and paging contracts."""

from pathlib import Path

import pytest

import leads
from content import ADMIN_PHONE, ALBUM_MAX, about_photos, clamp_page, pages, review_photos


@pytest.mark.parametrize("finder", (review_photos, about_photos))
def test_photo_discovery(tmp_path: Path, finder) -> None:
    assert finder(tmp_path / "missing") == []
    for name in ("10.jpg", "02.jpg", "01.jpg", "03.png", "04.JPG", "05.txt"):
        (tmp_path / name).touch()
    assert [path.name for path in finder(tmp_path)] == ["01.jpg", "02.jpg", "10.jpg"]


@pytest.mark.parametrize(
    "count,expected_sizes",
    ((0, []), (10, [10]), (11, [10, 1]), (27, [10, 10, 7])),
)
def test_pages(count: int, expected_sizes: list[int]) -> None:
    items = [Path(f"{index}.jpg") for index in range(count)]
    result = pages(items)
    assert [len(page) for page in result] == expected_sizes
    assert [item for page in result for item in page] == items
    assert ALBUM_MAX == 10


@pytest.mark.parametrize(
    "raw,total,expected",
    ((None, 3, 1), ("abc", 3, 1), (0, 3, 1), (-1, 3, 1),
     (4, 3, 1), ("2", 3, 2), (2, 3, 2), (1, 0, 1)),
)
def test_clamp_page(raw: str | int | None, total: int, expected: int) -> None:
    assert clamp_page(raw, total) == expected


def test_admin_phone_is_valid() -> None:
    assert leads._valid_phone(ADMIN_PHONE) == ADMIN_PHONE
