"""Small dotenv-compatible loader for the dependency-light LiveKit scripts."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def parse_env_value(raw: str) -> str:
    """Parse quotes and whitespace-prefixed inline comments from an env value."""
    value = raw.strip()
    if not value:
        return ""

    if value[0] in ("\"", "'"):
        quote = value[0]
        escaped = False
        for index in range(1, len(value)):
            character = value[index]
            if character == quote and not escaped:
                return value[1:index]
            escaped = character == "\\" and not escaped
            if character != "\\":
                escaped = False
        return value[1:]

    for index, character in enumerate(value):
        if character == "#" and (index == 0 or value[index - 1].isspace()):
            return value[:index].rstrip()
    return value


def load_env_files(paths: Iterable[Path]) -> None:
    """Load the first value for each key while preserving exported variables."""
    for path in paths:
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), parse_env_value(value))
