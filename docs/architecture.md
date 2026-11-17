# Architecture and implementation status

## Implemented prototype modules

- `ievf.state`: strict 16-bit state encoding/decoding.
- `ievf.serialization`: deterministic JSON serialization and SHA-256.
- `ievf.evidence`: evidence record structure, status validation, parent digest format, and content digest.
- `ievf.audit`: JSONL hash chaining, sequence/link verification, duplicate event-ID detection.
- `fault_tolerance`: validator vote aggregation, bounded retry helper, checkpoint checks, and restricted recovery gate.

## Not implemented

The Registry/Knowledge/Analysis/Hypothesis/Decision/Action pipeline, binary frame protocol, tensor engine, authenticated validator identities, signatures, key management, replay cache, inter-process ledger locking, crash-recovery replay, checkpoint trust anchoring, external integrations, agent orchestration, and production authorization are absent. Do not infer completion from the presence of a design document or unit tests.

## Data and trust boundaries

Source artifacts should remain distinct from derived evidence and interpretations. SHA-256 supports integrity checks relative to a trusted digest, not truth/authenticity. The local ledger is tamper-evident only under the assumption that a trusted head digest or independent copy is retained; it is not immutable. Caller-supplied identity and failure-domain labels are not authenticated.

## Package boundary

The `ievf` package and legacy `fault_tolerance` module use the standard library only. Research, numerical, network, cryptographic, and database libraries are not dependencies until an implemented feature requires them and the need is tested.
