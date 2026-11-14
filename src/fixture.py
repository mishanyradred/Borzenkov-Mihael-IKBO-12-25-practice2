"""Load test repositories from JSON adjacency lists."""

import json
import re
from pathlib import Path

TEST_NAME = re.compile(r"[A-Z]+")


def load_fixture(path):
    """Read named test vertices and reject malformed references."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("test repository must be a JSON object")
    for name, targets in data.items():
        if not TEST_NAME.fullmatch(name) or not isinstance(targets, list):
            raise ValueError(f"invalid adjacency list for {name}")
        if any(not isinstance(target, str) for target in targets):
            raise ValueError(f"invalid dependency name for {name}")
        if missing := set(targets).difference(data):
            raise ValueError(f"undeclared test packages: {sorted(missing)}")
    return {
        (name, None): tuple((target, None) for target in targets)
        for name, targets in data.items()
    }
