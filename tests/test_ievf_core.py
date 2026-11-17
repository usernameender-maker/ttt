import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ievf.audit import LedgerError, append_event, verify_ledger
from ievf.evidence import EvidenceRecord, EvidenceStatus
from ievf.serialization import canonical_json
from ievf.state import decode_state, encode_state


class StateTests(unittest.TestCase):
    def test_round_trip_boundaries(self):
        for state in (0, 1, 255, 256, 65535):
            self.assertEqual(decode_state(encode_state(state)), state)

    def test_rejects_out_of_range_and_bool(self):
        for state in (-1, 65536):
            with self.assertRaises(ValueError):
                encode_state(state)
        with self.assertRaises(TypeError):
            encode_state(True)

    def test_rejects_wrong_width(self):
        for value in (b"", b"\x00", b"\x00\x00\x00"):
            with self.assertRaises(ValueError):
                decode_state(value)


class SerializationAndEvidenceTests(unittest.TestCase):
    def test_canonical_json_is_stable(self):
        self.assertEqual(canonical_json({"b": 1, "a": 2}), b'{"a":2,"b":1}')

    def test_rejects_non_json_nan(self):
        with self.assertRaises(ValueError):
            canonical_json({"bad": float("nan")})

    def test_evidence_digest_is_stable_and_status_explicit(self):
        record = EvidenceRecord(
            "ev-1", "source-1", "2026-01-01T00:00:00Z", "DATA",
            EvidenceStatus.UNASSESSED, {"value": 3},
        )
        self.assertEqual(record.digest, record.digest)
        self.assertTrue(record.verify_digest(record.digest))
        self.assertFalse(record.verify_digest("f" * 64))

    def test_rejects_bad_parent_hash(self):
        with self.assertRaises(ValueError):
            EvidenceRecord(
                "ev-1", "s", "time", "DATA", EvidenceStatus.UNASSESSED,
                {}, ("not-a-digest",),
            )


class AuditLedgerTests(unittest.TestCase):
    def test_append_and_verify_chain(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            first = append_event(path, {"event_id": "e1", "kind": "created"})
            second = append_event(path, {"event_id": "e2", "kind": "checked"})
            entries = verify_ledger(path)
            self.assertEqual(len(entries), 2)
            self.assertEqual(entries[0]["entry_hash"], first)
            self.assertEqual(entries[1]["entry_hash"], second)
            self.assertEqual(entries[1]["previous_hash"], first)

    def test_detects_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            append_event(path, {"event_id": "e1", "value": "original"})
            entry = json.loads(path.read_text())
            entry["event"]["value"] = "altered"
            path.write_text(json.dumps(entry) + "\n")
            with self.assertRaises(LedgerError):
                verify_ledger(path)

    def test_rejects_truncated_record(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            path.write_bytes(b'{"sequence":')
            with self.assertRaises(LedgerError):
                verify_ledger(path)

    def test_rejects_duplicate_event_id(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ledger.jsonl"
            append_event(path, {"event_id": "same"})
            with self.assertRaises(LedgerError):
                append_event(path, {"event_id": "same"})


if __name__ == "__main__":
    unittest.main()
