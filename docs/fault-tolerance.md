# Fault-tolerance primitives: scope and limitations

This module provides a small, standard-library-only foundation for fail-closed
validation and recovery experiments:

- `ValidatorResult` binds a vote to input and specification SHA-256 digests.
- `quorum_decision` rejects duplicate validator IDs, repeated failure-domain
  labels, mixed input/specification digests, missing quorums, and conflicting
  quorums.
- `retry_idempotent` bounds attempts and backoff for caller-guaranteed
  idempotent operations.
- `save_checkpoint` writes a canonical JSON envelope through a same-directory
  temporary file and atomic replacement; `load_checkpoint` validates schema
  and payload digest before returning the payload.
- `recovery_gate` quarantines failed checks and never authorizes external
  actions, even when all checks pass.

## Important limits

These are local primitives, not a consensus protocol or a complete fault-
tolerant system. Validator identity and failure-domain strings are caller
assertions and are not authenticated. A SHA-256 digest detects a mismatch only
relative to a trusted expected value; it does not prove authenticity. The
checkpoint is not signed, externally anchored, protected against a malicious
filesystem owner, or coordinated across concurrent writers. Atomic replacement
and durability depend on filesystem and operating-system behavior. The retry
helper cannot determine whether a remote operation completed before a timeout;
use idempotency keys and query remote state before retrying consequential work.

The module does not implement a hash-linked ledger, locking, replay protection,
circuit breakers, independent worker orchestration, key management, or human
release authorization. Do not represent it as production-ready or safety-
critical. Run the tests with:

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```
