"""Keep the Python and Mini App catalogs in sync, including order and labels."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from catalog import (
    AGE_MAX,
    AGE_MIN,
    CALL_TIMES,
    COMMENT_MAX,
    DEEP_LINK_SOURCES,
    NAME_MAX,
    NAME_MIN,
    PAYLOAD_MAX_BYTES,
    PHONE_MAX_DIGITS,
    PHONE_MIN_DIGITS,
    PRIOR,
    REGIONS,
    SOURCES,
    TOPIC_MODULES,
    TOPICS,
)


DATA_JS = Path(__file__).resolve().parents[2] / "webapp" / "data.js"
NODE_EXPORTS = """
const data = await import(process.argv[1]);
const names = ['REGIONS', 'TOPICS', 'PRIOR', 'CALL_TIMES', 'SOURCES'];
const result = Object.fromEntries(names.map(name => [name, data[name].map(entry => ({
  code: entry.code, label: entry.label, ...(entry.modules ? { modules: entry.modules } : {}),
}))]));
result.DEEP_LINK_SOURCES = data.DEEP_LINK_SOURCES;
result.LIMITS = data.LIMITS;
console.log(JSON.stringify(result));
"""


def test_bot_and_mini_app_catalogs_match() -> None:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is unavailable")

    completed = subprocess.run(
        [node, "--input-type=module", "-e", NODE_EXPORTS, DATA_JS.as_uri()],
        capture_output=True,
        check=True,
        text=True,
        encoding="utf-8",
    )
    web = json.loads(completed.stdout)
    bot_tables = {
        "REGIONS": REGIONS,
        "TOPICS": TOPICS,
        "PRIOR": PRIOR,
        "CALL_TIMES": CALL_TIMES,
        "SOURCES": SOURCES,
    }
    for name, table in bot_tables.items():
        expected = [
            {"code": code, "label": labels, **(
                {"modules": list(TOPIC_MODULES[code])} if name == "TOPICS" else {}
            )}
            for code, labels in table.items()
        ]
        assert web[name] == expected, f"{name} differs between bot and Mini App"

    assert web["DEEP_LINK_SOURCES"] == list(DEEP_LINK_SOURCES)
    assert web["LIMITS"] == {
        "nameMin": NAME_MIN,
        "nameMax": NAME_MAX,
        "ageMin": AGE_MIN,
        "ageMax": AGE_MAX,
        "phoneMinDigits": PHONE_MIN_DIGITS,
        "phoneMaxDigits": PHONE_MAX_DIGITS,
        "commentMax": COMMENT_MAX,
        "payloadMaxBytes": PAYLOAD_MAX_BYTES,
    }
