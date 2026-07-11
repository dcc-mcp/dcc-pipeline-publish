from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA = "dcc-mcp-publish/v1"
REQUIRED = {"schema", "project", "entity", "version", "files"}


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_record(path: str, role: str) -> dict[str, Any]:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    return {"path": str(source), "role": role, "size": source.stat().st_size, "sha256": checksum(source)}


def load(path: str) -> tuple[Path, dict[str, Any]]:
    source = Path(path).expanduser().resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    return source, json.loads(source.read_text(encoding="utf-8"))


def validate(data: dict[str, Any], verify_files: bool = True) -> list[str]:
    errors = [f"missing field: {key}" for key in sorted(REQUIRED - data.keys())]
    if data.get("schema") != SCHEMA:
        errors.append(f"schema must be {SCHEMA}")
    files = data.get("files")
    if not isinstance(files, list) or not files:
        errors.append("files must be a non-empty list")
        return errors
    for index, item in enumerate(files):
        if not isinstance(item, dict) or not {"path", "role", "sha256"}.issubset(item):
            errors.append(f"files[{index}] is incomplete")
            continue
        if verify_files:
            path = Path(item["path"])
            if not path.is_file():
                errors.append(f"files[{index}] is missing: {path}")
            elif checksum(path) != item["sha256"]:
                errors.append(f"files[{index}] hash changed: {path}")
    return errors

