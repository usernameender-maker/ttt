"""Content-addressed evidence records with explicit provenance fields.

A digest supports integrity checking relative to a trusted expected digest;
it does not establish source authenticity or truth.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .serialization import canonical_json, sha256_hex

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


class EvidenceStatus(str, Enum):
    UNASSESSED = "UNASSESSED"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    REJECTED = "REJECTED"
    CONFIRMED = "CONFIRMED"
    ARTIFACT = "ARTIFACT"


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    source_id: str
    timestamp: str
    classification: str
    status: EvidenceStatus
    payload: dict[str, Any]
    parent_hashes: tuple[str, ...] = ()
    schema_version: int = 1

    def __post_init__(self) -> None:
        for name in ("evidence_id", "source_id", "timestamp", "classification"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.status, EvidenceStatus):
            raise TypeError("status must be an EvidenceStatus")
        if not isinstance(self.payload, dict):
            raise TypeError("payload must be a JSON object")
        if type(self.schema_version) is not int or self.schema_version < 1:
            raise ValueError("schema_version must be a positive integer")
        if not isinstance(self.parent_hashes, tuple):
            raise TypeError("parent_hashes must be a tuple")
        for digest in self.parent_hashes:
            if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
                raise ValueError("each parent hash must be lowercase SHA-256 hex")
        # Fail at construction if payload cannot be deterministically serialized.
        canonical_json(self.payload)

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "source_id": self.source_id,
            "timestamp": self.timestamp,
            "classification": self.classification,
            "status": self.status.value,
            "parent_hashes": list(self.parent_hashes),
            "payload": self.payload,
        }

    @property
    def digest(self) -> str:
        return sha256_hex(canonical_json(self.as_dict()))

    def verify_digest(self, expected: str) -> bool:
        return isinstance(expected, str) and _DIGEST_RE.fullmatch(expected) is not None and self.digest == expected
