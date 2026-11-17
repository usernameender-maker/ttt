import hashlib
import json
import random
import tempfile
import unittest
from pathlib import Path

from fault_tolerance import (
    Decision,
    RecoveryError,
    RetryExhausted,
    ValidatorResult,
    load_checkpoint,
    quorum_decision,
    recovery_gate,
    retry_idempotent,
    save_checkpoint,
)

DIGEST = hashlib.sha256(b"test-input").hexdigest()
SPEC = hashlib.sha256(b"test-spec").hexdigest()


def vote(name, domain, outcome=True, *, input_digest=DIGEST, spec_digest=SPEC):
    return ValidatorResult(name, domain, outcome, input_digest, spec_digest)


class FaultToleranceTests(unittest.TestCase):
    def test_independent_quorum_accepts(self):
        result = quorum_decision([
            vote("validator-a", "host-a"),
            vote("validator-b", "host-b"),
            vote("validator-c", "host-c"),
        ], quorum=2, required_domains=2)
        self.assertEqual(result["decision"], Decision.ACCEPT.value)

    def test_negative_quorum_rejects(self):
        result = quorum_decision([
            vote("validator-a", "host-a", False),
            vote("validator-b", "host-b", False),
        ], quorum=2)
        self.assertEqual(result["decision"], Decision.REJECT.value)

    def test_duplicate_identity_is_conflict(self):
        result = quorum_decision([
            vote("validator-a", "host-a"),
            vote("validator-a", "host-b"),
        ], quorum=2)
        self.assertEqual(result["decision"], Decision.CONFLICT.value)

    def test_shared_failure_domain_is_conflict(self):
        result = quorum_decision([
            vote("validator-a", "host-a"),
            vote("validator-b", "host-a"),
        ], quorum=2)
        self.assertEqual(result["decision"], Decision.CONFLICT.value)

    def test_different_input_digest_is_conflict(self):
        result = quorum_decision([
            vote("validator-a", "host-a"),
            vote("validator-b", "host-b", input_digest=hashlib.sha256(b"other").hexdigest()),
        ], quorum=2)
        self.assertEqual(result["decision"], Decision.CONFLICT.value)

    def test_different_specification_digest_is_conflict(self):
        result = quorum_decision([
            vote("validator-a", "host-a"),
            vote("validator-b", "host-b", spec_digest=hashlib.sha256(b"other spec").hexdigest()),
        ], quorum=2)
        self.assertEqual(result["decision"], Decision.CONFLICT.value)

    def test_disagreement_does_not_promote(self):
        result = quorum_decision([
            vote("validator-a", "host-a", True),
            vote("validator-b", "host-b", False),
        ], quorum=2)
        self.assertEqual(result["decision"], Decision.CONFLICT.value)

    def test_simultaneous_quorums_are_conflict(self):
        result = quorum_decision([
            vote("a", "host-a", True), vote("b", "host-b", True),
            vote("c", "host-c", False), vote("d", "host-d", False),
        ], quorum=2)
        self.assertEqual(result["decision"], Decision.CONFLICT.value)

    def test_missing_votes_are_insufficient(self):
        result = quorum_decision([vote("a", "host-a")], quorum=2)
        self.assertEqual(result["decision"], Decision.INSUFFICIENT.value)

    def test_empty_votes_are_insufficient(self):
        self.assertEqual(quorum_decision([])["decision"], Decision.INSUFFICIENT.value)

    def test_invalid_result_digest_is_rejected(self):
        with self.assertRaises(ValueError):
            ValidatorResult("a", "host-a", True, "not-a-digest", SPEC)

    def test_non_boolean_vote_is_rejected(self):
        with self.assertRaises(TypeError):
            ValidatorResult("a", "host-a", 1, DIGEST, SPEC)

    def test_quorum_arguments_are_validated(self):
        with self.assertRaises(ValueError):
            quorum_decision([], quorum=0)

    def test_retry_exhaustion_is_bounded(self):
        calls = []

        def fail():
            calls.append(1)
            raise OSError("simulated outage")

        with self.assertRaises(RetryExhausted):
            retry_idempotent(
                fail, attempts=3, base_delay=0,
                sleep=lambda _: None, rng=random.Random(1),
            )
        self.assertEqual(len(calls), 3)

    def test_retry_recovers(self):
        calls = []

        def temporary_failure():
            calls.append(1)
            if len(calls) < 2:
                raise OSError("temporary")
            return "recovered"

        result = retry_idempotent(
            temporary_failure, attempts=3, base_delay=0, sleep=lambda _: None
        )
        self.assertEqual(result, "recovered")
        self.assertEqual(len(calls), 2)

    def test_retry_does_not_catch_unconfigured_exception(self):
        with self.assertRaises(ValueError):
            retry_idempotent(lambda: (_ for _ in ()).throw(ValueError("stop")))

    def test_checkpoint_round_trip_and_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            digest = save_checkpoint(path, {"sequence": 12, "state": 65535})
            self.assertEqual(len(digest), 64)
            self.assertEqual(load_checkpoint(path), {"sequence": 12, "state": 65535})

    def test_checkpoint_corruption_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            save_checkpoint(path, {"state": 100})
            path.write_text("corrupted", encoding="utf-8")
            with self.assertRaises(RecoveryError):
                load_checkpoint(path)

    def test_checkpoint_payload_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            save_checkpoint(path, {"state": 100})
            envelope = json.loads(path.read_text(encoding="utf-8"))
            envelope["payload"]["state"] = 101
            path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaises(RecoveryError):
                load_checkpoint(path)

    def test_checkpoint_unsupported_schema_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            save_checkpoint(path, {"state": 1})
            envelope = json.loads(path.read_text(encoding="utf-8"))
            envelope["schema_version"] = 2
            path.write_text(json.dumps(envelope), encoding="utf-8")
            with self.assertRaises(RecoveryError):
                load_checkpoint(path)

    def test_checkpoint_non_object_payload_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "checkpoint.json"
            path.write_text(json.dumps({
                "payload": [], "payload_sha256": hashlib.sha256(b"[]").hexdigest(),
                "schema_version": 1,
            }), encoding="utf-8")
            with self.assertRaises(RecoveryError):
                load_checkpoint(path)

    def test_recovery_gate_quarantines_failed_invariant(self):
        result = recovery_gate(
            ledger_valid=True, checkpoint_valid=True, replay_valid=True,
            invariants_valid=False, independent_review=True,
        )
        self.assertEqual(result["status"], "QUARANTINED")
        self.assertFalse(result["allow_external_actions"])

    def test_successful_recovery_never_authorizes_action(self):
        result = recovery_gate(
            ledger_valid=True, checkpoint_valid=True, replay_valid=True,
            invariants_valid=True, independent_review=True,
        )
        self.assertEqual(result["status"], "RECOVERED_RESTRICTED")
        self.assertFalse(result["allow_external_actions"])

    def test_recovery_gate_rejects_truthy_non_boolean(self):
        with self.assertRaises(TypeError):
            recovery_gate(
                ledger_valid="yes", checkpoint_valid=True, replay_valid=True,
                invariants_valid=True, independent_review=True,
            )


if __name__ == "__main__":
    unittest.main()
