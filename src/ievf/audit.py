"""Append-only-by-convention hash-linked JSONL audit ledger.

This implementation detects broken links and record edits when the expected
head digest is trusted. It does not prevent rewriting/truncation, provide
inter-process locking, authenticate authors, or guarantee storage durability.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .serialization import canonical_json, sha256_hex

GENESIS = "0" * 64


class LedgerError(ValueError):
    """Raised when ledger structure or chain integrity is invalid."""


def _entry_digest(sequence: int, previous_hash: str, event: dict[str, Any]) -> str:
    return sha256_hex(canonical_json({
        "sequence": sequence,
        "previous_hash": previous_hash,
        "event": event,
    }))


def append_event(path: str | Path, event: dict[str, Any]) -> str:
    """Append one event after verifying the existing ledger; return new digest."""
    if not isinstance(event, dict):
        raise TypeError("event must be a JSON object")
    canonical_json(event)
    target = Path(path)
    entries = verify_ledger(target) if target.exists() else []
    sequence = len(entries)
    previous_hash = entries[-1]["entry_hash"] if entries else GENESIS
    entry = {
        "sequence": sequence,
        "previous_hash": previous_hash,
        "event": event,
    }
    entry["entry_hash"] = _entry_digest(sequence, previous_hash, event)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("ab") as stream:
        stream.write(canonical_json(entry) + b"\n")
        stream.flush()
    return entry["entry_hash"]


def verify_ledger(path: str | Path) -> list[dict[str, Any]]:
    """Verify JSONL syntax, sequence, previous links, and entry digests."""
    target = Path(path)
    try:
        raw_lines = target.read_bytes().splitlines()
    except OSError as exc:
        raise LedgerError(f"cannot read ledger: {exc}") from exc
    entries: list[dict[str, Any]] = []
    expected_previous = GENESIS
    seen_event_ids: set[str] = set()
    for index, line in enumerate(raw_lines):
        if not line:
            raise LedgerError(f"empty line at ledger record {index}")
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise LedgerError(f"malformed JSON at ledger record {index}") from exc
        if not isinstance(entry, dict) or set(entry) != {
            "sequence", "previous_hash", "event", "entry_hash"
        }:
            raise LedgerError(f"invalid entry fields at ledger record {index}")
        if type(entry["sequence"]) is not int or entry["sequence"] != index:
            raise LedgerError(f"invalid sequence at ledger record {index}")
        if entry["previous_hash"] != expected_previous:
            raise LedgerError(f"broken previous-hash link at ledger record {index}")
        if not isinstance(entry["event"], dict):
            raise LedgerError(f"event must be an object at ledger record {index}")
        event_id = entry["event"].get("event_id")
        if event_id is not None:
            if not isinstance(event_id, str) or not event_id:
                raise LedgerError(f"invalid event_id at ledger record {index}")
            if event_id in seen_event_ids:
                raise LedgerError(f"duplicate event_id at ledger record {index}")
            seen_event_ids.add(event_id)
        expected_hash = _entry_digest(index, expected_previous, entry["event"])
        if entry["entry_hash"] != expected_hash:
            raise LedgerError(f"digest mismatch at ledger record {index}")
        expected_previous = expected_hash
        entries.append(entry)
    return entries


def iter_events(path: str | Path) -> Iterable[dict[str, Any]]:
    return (entry["event"] for entry in verify_ledger(path))
