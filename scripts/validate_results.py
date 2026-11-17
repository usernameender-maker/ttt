#!/usr/bin/env python3
"""Minimal validator for JSONL result files produced by the benchmark runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _load_schema() -> dict:
    schema_path = Path(__file__).resolve().parents[1] / "research-data" / "result.schema.json"
    return json.loads(schema_path.read_text(encoding="utf-8"))


def validate_jsonl(path: str | Path) -> None:
    schema = _load_schema()
    required = set(schema["required"])
    count = 0
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        missing = sorted(required - set(record))
        if missing:
            raise ValueError(f"Missing required fields in {path}: {missing}")
        count += 1
    if count == 0:
        raise ValueError(f"No result records found in {path}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-results.jsonl>")
        raise SystemExit(2)
    validate_jsonl(sys.argv[1])
    print(f"Validated {sys.argv[1]}")
