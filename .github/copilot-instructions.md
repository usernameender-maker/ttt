# IEVF-CORE — Repository Instructions for GitHub Copilot
## Project mission
Develop and validate the IEVF Adaptive State Engine as a reproducible, evidence-driven software architecture.
Preserve the distinction:
SOURCE != EVIDENCE != KNOWLEDGE != ANALYSIS != HYPOTHESIS != DECISION != ACTION.
Never invent test results, scientific findings, integrations, benchmarks, citations, or deployment status.
## Architecture
- Preserve the 16-bit state representation and its 65,536 possible states.
- Keep binary frame handling, evidence records, hashing, reachability, pipeline orchestration, and security gates modular.
- Preserve deterministic serialization and reproducible execution.
- Keep provenance and validation status attached to evidence.
- Treat GNSS, IMU, solar, KEGG, Bio Anchor, and HOPS adapters as templates unless actual integrations and tests demonstrate otherwise.
- Do not conflate the 65,536-state model with the separate 65,536 x 33 mathematical embedding.
- Do not claim quantum error correction, quantum advantage, or new physics without independent evidence.
## Required development procedure
1. Inspect README.md, CODE_REVIEW.md, source files, and existing tests before changing code.
2. Identify the requirement and affected modules.
3. Preserve existing working behavior.
4. Make small, reviewable changes.
5. Add tests for normal operation, edge cases, invalid inputs, and failure paths.
6. Run the complete test suite after changes.
7. Review the complete Git diff.
8. Update documentation and the code review when implementation or risk changes.
## Test commands
Run from the repository root:
    PYTHONPATH=src python -m unittest discover -s tests -v
Run the CLI:
    PYTHONPATH=src python -m ievf_state --state 65535
Verify an evidence ledger:
    PYTHONPATH=src python -m ievf_state --verify-ledger PATH
Do not report a test as passed unless the command actually ran and returned successfully.
## Security requirements
- Never commit credentials, API keys, private keys, tokens, or sensitive telemetry.
- A SHA-256 hash alone does not establish source authenticity.
- Do not describe caller-supplied approval booleans as cryptographic authorization.
- Identify replay protection, key management, trusted timestamps, and durable audit storage as incomplete unless implemented and tested.
- Never weaken security validation simply to make tests pass.
- Do not represent this research prototype as certified or production-ready safety-critical equipment.
## GitHub workflow
- Work on a feature branch.
- Do not push directly to main without explicit authorization.
- Inspect the diff before committing.
- Never force-push or rewrite shared history.
- Do not claim remote changes succeeded unless GitHub confirms them.
- Stop and report permission failures rather than bypassing them.
## Completion report
For each task report:
1. What changed.
2. Files changed.
3. Commands executed.
4. Exact test results.
5. Remaining defects and risks.
6. Whether any GitHub operation actually succeeded.
