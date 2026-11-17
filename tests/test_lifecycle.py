import json
import unittest

from ievf.lifecycle import (
    ActionRecord,
    AnalysisRecord,
    AuthorizationGate,
    DecisionRecord,
    EvidenceRecord,
    HypothesisRecord,
    KnowledgeRecord,
    LifecycleEngine,
    LifecycleError,
    RecordType,
    SourceRecord,
    ValidationOutcome,
    ValidationRecord,
)


class LifecycleTests(unittest.TestCase):
    def test_demo_lifecycle_and_ledger(self):
        engine = LifecycleEngine()
        result = engine.build_demo()
        self.assertTrue(result["ledger_valid"])
        self.assertEqual(len(result["actions"]), 2)
        self.assertTrue(result["final_state_digest"])

    def test_validation_outcomes_are_explicit(self):
        self.assertEqual(ValidationOutcome.CONFIRMED.value, "CONFIRMED")
        self.assertEqual(ValidationOutcome.CONTRADICTED.value, "CONTRADICTED")
        self.assertEqual(ValidationOutcome.ARTIFACT.value, "ARTIFACT")

    def test_duplicate_id_is_rejected(self):
        engine = LifecycleEngine()
        source = SourceRecord(record_id="dup", producer="tester", payload={"value": 1})
        engine.add_record(source)
        with self.assertRaises(LifecycleError):
            engine.add_record(SourceRecord(record_id="dup", producer="tester", payload={"value": 2}))

    def test_rejects_invalid_parent_reference(self):
        engine = LifecycleEngine()
        with self.assertRaises(LifecycleError):
            engine.add_record(EvidenceRecord(record_id="e-1", producer="tester", parent_id="missing", payload={"k": 1}))

    def test_authorization_gate_fails_closed(self):
        allowed, _ = AuthorizationGate.authorize(
            evidence_present=True,
            provenance_valid=True,
            validation_outcome=ValidationOutcome.CONTRADICTED,
            policy_approved=True,
            actor_is_component=False,
        )
        self.assertFalse(allowed)

    def test_self_authorization_is_rejected(self):
        allowed, _ = AuthorizationGate.authorize(
            evidence_present=True,
            provenance_valid=True,
            validation_outcome=ValidationOutcome.CONFIRMED,
            policy_approved=True,
            actor_is_component=True,
        )
        self.assertFalse(allowed)

    def test_replay_digest_is_stable(self):
        first = LifecycleEngine()
        first.build_demo()
        second = LifecycleEngine()
        second.build_demo()
        self.assertEqual(first.replay_digest(), second.replay_digest())

    def test_invalid_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            SourceRecord(record_id="bad-ts", producer="tester", timestamp="not-a-time", payload={"x": 1})


if __name__ == "__main__":
    unittest.main()
