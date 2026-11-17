"""Fail-closed quorum, retry, checkpoint, and recovery primitives.

These primitives provide integrity checks and recovery gates; they do not
provide authenticated validator identities, distributed consensus, trusted
storage, or authorization for external actions.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import tempfile
import time
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, TypeVar

T = TypeVar("T")


class Decision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICT = "CONFLICT"


class RecoveryError(RuntimeError):
    """Raised when a checkpoint cannot safely be used for recovery."""


class RetryExhausted(RuntimeError):
    """Raised when an idempotent operation fails every permitted attempt."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: object) -> bytes:
    """Serialize JSON deterministically; reject non-standard NaN/Infinity."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _require_sha256(value: object, field_name: str) -> None:
    if not isinstance(value, str) or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character SHA-256 hex string")
    try:
        bytes.fromhex(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be hexadecimal") from exc


@dataclass(frozen=True)
class ValidatorResult:
    """One validator's result, bound to input and specification digests.

    ``failure_domain`` is an asserted label, not a cryptographically verified
    identity or proof of independence. A deployment must authenticate and
    independently establish these properties.
    """

    validator_id: str
    failure_domain: str
    outcome: bool
    input_digest: str
    specification_digest: str

    def __post_init__(self) -> None:
        for field_name in ("validator_id", "failure_domain"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
        if type(self.outcome) is not bool:
            raise TypeError("outcome must be bool")
        _require_sha256(self.input_digest, "input_digest")
        _require_sha256(self.specification_digest, "specification_digest")


def quorum_decision(
    results: list[ValidatorResult],
    *,
    quorum: int = 2,
    required_domains: int = 2,
) -> dict[str, object]:
    """Return a conservative decision for votes over identical inputs.

    Duplicate identities or failure-domain labels, mismatched digests, and
    simultaneous positive and negative quorums produce CONFLICT. A missing
    vote never counts as approval. This is not a distributed-consensus
    protocol and does not authenticate validator claims.
    """
    if type(quorum) is not int or type(required_domains) is not int:
        raise TypeError("quorum and required_domains must be integers")
    if quorum < 1 or required_domains < 1:
        raise ValueError("quorum and required_domains must be positive")
    if not isinstance(results, list):
        raise TypeError("results must be a list")
    if any(not isinstance(result, ValidatorResult) for result in results):
        raise TypeError("every result must be a ValidatorResult")
    if not results:
        return {"decision": Decision.INSUFFICIENT.value, "reason": "no validator results"}

    identities = [result.validator_id for result in results]
    duplicates = sorted(
        identity for identity, count in Counter(identities).items() if count > 1
    )
    if duplicates:
        return {
            "decision": Decision.CONFLICT.value,
            "reason": "duplicate validator identity",
            "duplicates": duplicates,
        }

    domains = [result.failure_domain for result in results]
    if len(set(domains)) != len(domains):
        return {
            "decision": Decision.CONFLICT.value,
            "reason": "correlated failure domain",
        }

    if len({result.input_digest for result in results}) != 1 or len(
        {result.specification_digest for result in results}
    ) != 1:
        return {
            "decision": Decision.CONFLICT.value,
            "reason": "validators assessed different inputs or specifications",
        }

    accepted = sum(result.outcome for result in results)
    rejected = len(results) - accepted
    common = {
        "accepted_votes": accepted,
        "rejected_votes": rejected,
        "independent_domains": len(set(domains)),
        "required_quorum": quorum,
        "required_domains": required_domains,
    }
    if len(results) < quorum or len(set(domains)) < required_domains:
        return {"decision": Decision.INSUFFICIENT.value, **common}
    if accepted >= quorum and rejected >= quorum:
        return {"decision": Decision.CONFLICT.value, "reason": "conflicting quorums", **common}
    if accepted >= quorum:
        return {"decision": Decision.ACCEPT.value, **common}
    if rejected >= quorum:
        return {"decision": Decision.REJECT.value, **common}
    return {"decision": Decision.CONFLICT.value, "reason": "no outcome reached quorum", **common}


def retry_idempotent(
    operation: Callable[[], T],
    *,
    attempts: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 2.0,
    retry_on: tuple[type[Exception], ...] = (OSError,),
    sleep: Callable[[float], None] = time.sleep,
    rng: random.Random | None = None,
) -> T:
    """Retry a caller-guaranteed idempotent operation with bounded jitter.

    Do not use for non-idempotent external actions unless the remote service
    enforces an idempotency key and the caller handles unknown completion.
    """
    if type(attempts) is not int or attempts < 1:
        raise ValueError("attempts must be an integer >= 1")
    if base_delay < 0 or max_delay < 0:
        raise ValueError("delays cannot be negative")
    if not isinstance(retry_on, tuple) or not retry_on or any(
        not isinstance(exc_type, type) or not issubclass(exc_type, Exception)
        for exc_type in retry_on
    ):
        raise TypeError("retry_on must be a non-empty tuple of Exception types")
    if not callable(operation) or not callable(sleep):
        raise TypeError("operation and sleep must be callable")

    rng = rng or random.Random()
    delay = min(base_delay, max_delay)
    last_error: Exception | None = None
    for index in range(attempts):
        try:
            return operation()
        except retry_on as exc:
            last_error = exc
            if index + 1 == attempts:
                break
            sleep(rng.uniform(0, delay))
            delay = min(delay * 2, max_delay)
    raise RetryExhausted(
        f"operation failed after {attempts} attempts: {last_error}"
    ) from last_error


def save_checkpoint(path: str | Path, payload: dict) -> str:
    """Atomically replace a checkpoint and return its encoded SHA-256 digest.

    Atomic replacement is guaranteed only to the extent provided by the
    filesystem when the temporary file and destination share a filesystem.
    The digest detects corruption relative to a trusted expected digest; it
    does not authenticate the checkpoint's origin.
    """
    if not isinstance(payload, dict):
        raise TypeError("checkpoint payload must be a dict")
    payload_bytes = canonical_json(payload)
    envelope = {
        "payload": payload,
        "payload_sha256": sha256(payload_bytes),
        "schema_version": 1,
    }
    encoded = canonical_json(envelope)
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
    )
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
        if hasattr(os, "O_DIRECTORY"):
            directory_fd = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except Exception:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
    return sha256(encoded)


def load_checkpoint(path: str | Path) -> dict:
    """Load a checkpoint only after strict envelope and digest verification."""
    try:
        envelope = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(envelope, dict):
            raise RecoveryError("checkpoint envelope must be an object")
        payload = envelope["payload"]
        expected = envelope["payload_sha256"]
        version = envelope["schema_version"]
    except RecoveryError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise RecoveryError(f"checkpoint unreadable: {exc}") from exc

    if type(version) is not int or version != 1:
        raise RecoveryError("unsupported checkpoint schema")
    if not isinstance(payload, dict):
        raise RecoveryError("checkpoint payload must be an object")
    try:
        _require_sha256(expected, "payload_sha256")
        actual = sha256(canonical_json(payload))
    except (TypeError, ValueError) as exc:
        raise RecoveryError(f"checkpoint payload is not canonicalizable: {exc}") from exc
    if actual != expected:
        raise RecoveryError("checkpoint integrity failure")
    return payload


def recovery_gate(
    *,
    ledger_valid: bool,
    checkpoint_valid: bool,
    replay_valid: bool,
    invariants_valid: bool,
    independent_review: bool,
) -> dict[str, object]:
    """Fail closed; even successful recovery cannot authorize external action."""
    checks = {
        "ledger_valid": ledger_valid,
        "checkpoint_valid": checkpoint_valid,
        "replay_valid": replay_valid,
        "invariants_valid": invariants_valid,
        "independent_review": independent_review,
    }
    if any(type(value) is not bool for value in checks.values()):
        raise TypeError("all recovery checks must be bool values")
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        return {
            "status": "QUARANTINED",
            "allow_external_actions": False,
            "failed_checks": failed,
        }
    return {
        "status": "RECOVERED_RESTRICTED",
        "allow_external_actions": False,
        "failed_checks": [],
        "next_gate": "human or separately authorized release decision",
    }
