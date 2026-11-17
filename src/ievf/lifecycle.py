from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from .serialization import canonical_json, sha256_hex


class ValidationOutcome(str, Enum):
    CONFIRMED = "CONFIRMED"
    SUPPORTED = "SUPPORTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    CONTRADICTED = "CONTRADICTED"
    ARTIFACT = "ARTIFACT"


class RecordType(str, Enum):
    SOURCE = "SOURCE"
    EVIDENCE = "EVIDENCE"
    KNOWLEDGE = "KNOWLEDGE"
    ANALYSIS = "ANALYSIS"
    HYPOTHESIS = "HYPOTHESIS"
    VALIDATION = "VALIDATION"
    DECISION = "DECISION"
    ACTION = "ACTION"
    AUDIT = "AUDIT"


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _validate_iso8601(value: str) -> None:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO-8601 timestamp: {value!r}") from exc


def _normalise_record_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise TypeError("record payload must be a dict")
    return json.loads(json.dumps(data, sort_keys=True))


@dataclass(frozen=True)
class BaseRecord:
    record_id: str
    record_type: RecordType
    schema_version: str = "1.0.0"
    timestamp: str = field(default_factory=utc_timestamp)
    producer: str = "system"
    parent_id: Optional[str] = None
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, str) or not self.record_id.strip():
            raise ValueError("record_id must be a non-empty string")
        if not isinstance(self.producer, str) or not self.producer.strip():
            raise ValueError("producer must be a non-empty string")
        _validate_iso8601(self.timestamp)
        if type(self.schema_version) is not str or not self.schema_version.strip():
            raise ValueError("schema_version must be a non-empty string")
        object.__setattr__(self, "payload", _normalise_record_dict(self.payload))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type.value,
            "schema_version": self.schema_version,
            "timestamp": self.timestamp,
            "producer": self.producer,
            "parent_id": self.parent_id,
            "payload": self.payload,
        }

    @property
    def digest(self) -> str:
        return sha256_hex(canonical_json(self.as_dict()))


@dataclass(frozen=True)
class SourceRecord(BaseRecord):
    record_type: RecordType = RecordType.SOURCE


@dataclass(frozen=True)
class EvidenceRecord(BaseRecord):
    record_type: RecordType = RecordType.EVIDENCE


@dataclass(frozen=True)
class KnowledgeRecord(BaseRecord):
    record_type: RecordType = RecordType.KNOWLEDGE


@dataclass(frozen=True)
class AnalysisRecord(BaseRecord):
    record_type: RecordType = RecordType.ANALYSIS


@dataclass(frozen=True)
class HypothesisRecord(BaseRecord):
    record_type: RecordType = RecordType.HYPOTHESIS


@dataclass(frozen=True)
class ValidationRecord(BaseRecord):
    record_type: RecordType = RecordType.VALIDATION


@dataclass(frozen=True)
class DecisionRecord(BaseRecord):
    record_type: RecordType = RecordType.DECISION


@dataclass(frozen=True)
class ActionRecord(BaseRecord):
    record_type: RecordType = RecordType.ACTION


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    event_type: str
    timestamp: str
    actor: str
    subject_id: str
    previous_event_digest: str
    current_event_digest: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    sequence_number: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise ValueError("event_id must be non-empty")
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("event_type must be non-empty")
        if not isinstance(self.actor, str) or not self.actor.strip():
            raise ValueError("actor must be non-empty")
        if not isinstance(self.subject_id, str) or not self.subject_id.strip():
            raise ValueError("subject_id must be non-empty")
        _validate_iso8601(self.timestamp)
        object.__setattr__(self, "metadata", _normalise_record_dict(self.metadata))

    def as_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "subject_id": self.subject_id,
            "previous_event_digest": self.previous_event_digest,
            "current_event_digest": self.current_event_digest,
            "sequence_number": self.sequence_number,
            "metadata": self.metadata,
        }


class LifecycleError(RuntimeError):
    """Raised when a lifecycle record or event violates integrity requirements."""


class AuthorizationGate:
    @staticmethod
    def authorize(
        *,
        evidence_present: bool,
        provenance_valid: bool,
        validation_outcome: ValidationOutcome,
        policy_approved: bool,
        actor_is_component: bool,
    ) -> tuple[bool, str]:
        if not evidence_present:
            return False, "Denied: evidence is missing."
        if not provenance_valid:
            return False, "Denied: provenance invalid."
        if validation_outcome in (
            ValidationOutcome.INCONCLUSIVE,
            ValidationOutcome.CONTRADICTED,
            ValidationOutcome.ARTIFACT,
        ):
            return False, f"Denied: validation outcome {validation_outcome.value} does not authorize action."
        if actor_is_component:
            return False, "Denied: a component cannot authorize its own privileged action."
        if not policy_approved:
            return False, "Denied: explicit policy approval missing."
        return True, "Authorized: explicit policy approval and validation permit action."


class LifecycleEngine:
    def __init__(self) -> None:
        self.records: Dict[str, BaseRecord] = {}
        self.events: List[AuditEvent] = []
        self._current_previous_digest = "0" * 64

    def add_record(self, record: BaseRecord) -> BaseRecord:
        if not isinstance(record, BaseRecord):
            raise TypeError("record must be a BaseRecord")
        if record.record_id in self.records:
            raise LifecycleError(f"duplicate record identifier: {record.record_id}")
        if record.parent_id is not None and record.parent_id not in self.records:
            raise LifecycleError(f"unknown parent_id: {record.parent_id}")
        self.records[record.record_id] = record
        self.append_audit_event(
            event_type="REGISTER_RECORD",
            actor=record.producer,
            subject_id=record.record_id,
            metadata={"record_type": record.record_type.value, "digest": record.digest},
        )
        return record

    def append_audit_event(
        self,
        *,
        event_type: str,
        actor: str,
        subject_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
    ) -> AuditEvent:
        seq = len(self.events) + 1
        previous = self._current_previous_digest
        actual_event_id = event_id or f"evt-{seq:04d}"
        now = utc_timestamp()
        payload = {
            "sequence_number": seq,
            "event_id": actual_event_id,
            "event_type": event_type,
            "timestamp": now,
            "actor": actor,
            "subject_id": subject_id,
            "previous_event_digest": previous,
            "metadata": metadata or {},
        }
        current = sha256_hex(canonical_json(payload))
        event = AuditEvent(
            event_id=actual_event_id,
            event_type=event_type,
            timestamp=now,
            actor=actor,
            subject_id=subject_id,
            previous_event_digest=previous,
            current_event_digest=current,
            metadata=metadata or {},
            sequence_number=seq,
        )
        self.events.append(event)
        self._current_previous_digest = current
        return event

    def verify_ledger(self) -> bool:
        expected_previous = "0" * 64
        seen_event_ids: set[str] = set()
        for index, event in enumerate(self.events):
            if event.sequence_number != index + 1:
                return False
            if event.previous_event_digest != expected_previous:
                return False
            if event.event_id in seen_event_ids:
                return False
            seen_event_ids.add(event.event_id)
            recomputed = {
                "sequence_number": event.sequence_number,
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "actor": event.actor,
                "subject_id": event.subject_id,
                "previous_event_digest": event.previous_event_digest,
                "metadata": event.metadata,
            }
            if sha256_hex(canonical_json(recomputed)) != event.current_event_digest:
                return False
            expected_previous = event.current_event_digest
        return True

    def replay_digest(self) -> str:
        snapshot = {
            "records": {rid: rec.as_dict() for rid, rec in sorted(self.records.items())},
            "events": [event.as_dict() for event in self.events],
        }
        return sha256_hex(canonical_json(snapshot))

    def build_demo(self) -> Dict[str, Any]:
        source = SourceRecord(
            record_id="source-001",
            producer="ingest-agent",
            payload={"source": "synthetic_demo_input", "note": "synthetic example only"},
        )
        self.add_record(source)

        ev1 = EvidenceRecord(
            record_id="evidence-001",
            producer="sensor-agent",
            parent_id=source.record_id,
            payload={"measurement": 98.6, "classification": "temperature"},
        )
        ev2 = EvidenceRecord(
            record_id="evidence-002",
            producer="sensor-agent",
            parent_id=source.record_id,
            payload={"measurement": 98.4, "classification": "temperature"},
        )
        self.add_record(ev1)
        self.add_record(ev2)

        knowledge = KnowledgeRecord(
            record_id="knowledge-001",
            producer="analyst",
            parent_id=ev1.record_id,
            payload={"statement": "Normal operating range is 97.5 to 99.5."},
        )
        self.add_record(knowledge)

        analysis = AnalysisRecord(
            record_id="analysis-001",
            producer="analyst",
            parent_id=knowledge.record_id,
            payload={"summary": "No drift observed in the synthetic window."},
        )
        self.add_record(analysis)

        h1 = HypothesisRecord(
            record_id="hypothesis-001",
            producer="researcher",
            parent_id=analysis.record_id,
            payload={"claim": "System remains in nominal operating window."},
        )
        h2 = HypothesisRecord(
            record_id="hypothesis-002",
            producer="researcher",
            parent_id=analysis.record_id,
            payload={"claim": "System is experiencing drift."},
        )
        self.add_record(h1)
        self.add_record(h2)

        validation_ok = ValidationRecord(
            record_id="validation-001",
            producer="validator",
            parent_id=h1.record_id,
            payload={"outcome": ValidationOutcome.CONFIRMED.value, "reason": "synthetic supporting evidence"},
        )
        self.add_record(validation_ok)

        decision = DecisionRecord(
            record_id="decision-001",
            producer="policy",
            parent_id=validation_ok.record_id,
            payload={"decision": "ALLOW", "authorized": True},
        )
        self.add_record(decision)

        allowed, reason = AuthorizationGate.authorize(
            evidence_present=True,
            provenance_valid=True,
            validation_outcome=ValidationOutcome.CONFIRMED,
            policy_approved=True,
            actor_is_component=False,
        )
        action_allowed = ActionRecord(
            record_id="action-001",
            producer="executor",
            parent_id=decision.record_id,
            payload={"status": "EXECUTED" if allowed else "BLOCKED", "reason": reason},
        )
        self.add_record(action_allowed)

        blocked = ActionRecord(
            record_id="action-002",
            producer="executor",
            parent_id=h2.record_id,
            payload={"status": "BLOCKED", "reason": "contradicted hypothesis does not authorize action"},
        )
        self.add_record(blocked)

        return {
            "source_id": source.record_id,
            "evidence_ids": [ev1.record_id, ev2.record_id],
            "knowledge_id": knowledge.record_id,
            "analysis_id": analysis.record_id,
            "hypothesis_ids": [h1.record_id, h2.record_id],
            "validation_id": validation_ok.record_id,
            "decision_id": decision.record_id,
            "actions": [action_allowed.record_id, blocked.record_id],
            "ledger_valid": self.verify_ledger(),
            "final_state_digest": self.replay_digest(),
        }


def build_demo() -> LifecycleEngine:
    engine = LifecycleEngine()
    engine.build_demo()
    return engine


__all__ = [
    "ActionRecord",
    "AnalysisRecord",
    "AuditEvent",
    "AuthorizationGate",
    "BaseRecord",
    "DecisionRecord",
    "EvidenceRecord",
    "HypothesisRecord",
    "KnowledgeRecord",
    "LifecycleEngine",
    "LifecycleError",
    "RecordType",
    "SourceRecord",
    "ValidationOutcome",
    "ValidationRecord",
    "build_demo",
]
