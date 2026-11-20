from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pytest


@dataclass
class FakeUser:
    id: int
    username: str | None
    full_name: str


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "leads.db"


@pytest.fixture
def fake_user_factory() -> Callable[[int, str | None, str], FakeUser]:
    def make_user(
        id: int = 1,
        username: str | None = "tester",
        full_name: str = "Test User",
    ) -> FakeUser:
        return FakeUser(id=id, username=username, full_name=full_name)

    return make_user
