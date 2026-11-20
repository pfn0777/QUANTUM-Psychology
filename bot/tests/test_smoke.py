import importlib
import sys


def test_python_and_dependencies() -> None:
    assert sys.version_info >= (3, 11)
    assert importlib.import_module("aiogram")
    assert importlib.import_module("aiosqlite")
