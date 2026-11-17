# Shared Research Execution and Validation Contract

**Status:** Design proposal; not yet implemented or validated by software tests.  
**Scope:** A reusable, domain-neutral contract for recording research specifications, executions, validation, and controlled changes across independent project modules.

This document defines common record and review expectations. It does not claim that a registry, workflow engine, cryptographic signature system, or multi-agent implementation exists in this repository.

## 1. Core distinctions

Keep these artifact classes separate and link them with stable identifiers:

`SOURCE != EVIDENCE != KNOWLEDGE != ANALYSIS != HYPOTHESIS != DECISION != ACTION`

- **Source:** An original document, dataset, image, repository revision, instrument output, or external reference.
- **Evidence:** A preserved source artifact or observation with provenance and integrity metadata.
- **Knowledge:** A versioned, reviewable claim derived from evidence.
- **Analysis:** A method and its output, with inputs, assumptions, and execution details.
- **Hypothesis:** A falsifiable proposition with competing explanations and planned tests.
- **Decision:** A recorded disposition made against explicit criteria by an authorized reviewer.
- **Action:** A separately authorized operation resulting from a decision.

A hash can detect a mismatch against a trusted expected digest; it does not prove source authenticity, truth, or completeness. A document, visualization, simulation, or proposed design must not be represented as a demonstrated result without the corresponding evidence.

## 2. Shared record requirements

All records should have a stable ID, schema/version identifier, creation time, author or producing system, and links to related records. Preserve original inputs as immutable artifacts; create derived artifacts separately. Record timestamps with timezone information. Record unknown values as unknown rather than inventing them.

Domain modules may define additional fields and validation rules. They must not redefine the shared meanings of source, evidence, analysis, validation, decision, or action.

### 2.1 Experiment specification

Create and review this before examining outcome data where practical. Freeze the specification and record any later amendment as a new version, with rationale and timing.

```yaml
spec_id: "stable-id"
schema_version: "1.0"
project_id: "stable-project-id"
title: "Short experiment name"
question: "Falsifiable research question"
hypothesis: "Predicted observation or effect"
competing_explanations:
  - "Alternative explanation"
acceptance_criteria:
  - id: "criterion-1"
    measure: "Defined metric"
    rule: "Predeclared comparison or threshold"
inputs:
  - evidence_id: "evidence-id"
    expected_digest: "sha256:..."
method:
  source_revision: "commit or version"
  configuration_digest: "sha256:..."
  command: "Exact command or procedure"
controls:
  positive: "Control or not applicable with reason"
  negative: "Control or not applicable with reason"
  baseline: "Baseline and version"
metrics:
  - name: "metric-name"
    definition: "Operational definition and units"
    uncertainty_method: "Method or not yet specified"
exclusions: []
resource_limits:
  time: "Declared limit"
  compute: "Declared limit"
  safety_constraints: []
review:
  independent_reviewer_required: true
  status: "DRAFT"
```

The specification should state assumptions, data-selection rules, stopping conditions, statistical methods where applicable, and conditions that would falsify or leave the hypothesis inconclusive. Use `NOT_APPLICABLE` with an explanation rather than omitting required controls silently.

### 2.2 Reproducibility manifest

Create one manifest per execution. It records what actually ran, not what was intended to run.

```yaml
run_id: "stable-run-id"
spec_id: "stable-spec-id"
spec_digest: "sha256:..."
source_revision: "commit or immutable version"
input_artifacts:
  - evidence_id: "evidence-id"
    digest: "sha256:..."
software:
  runtime: "name and exact version"
  dependencies_lock_digest: "sha256:..."
  container_digest: "sha256:... or NOT_USED"
configuration_digest: "sha256:..."
random_seeds:
  - "seed or NOT_APPLICABLE"
hardware: "available identifying details; unknown values marked UNKNOWN"
command: "Exact command or procedure"
started_at: "RFC3339 timestamp with timezone"
completed_at: "RFC3339 timestamp with timezone or null"
exit_status: "integer or NOT_COMPLETED"
outputs:
  - artifact_id: "stable-output-id"
    digest: "sha256:..."
logs_digest: "sha256:... or NOT_AVAILABLE"
limitations: []
```

Do not put secrets or sensitive telemetry in manifests. Reference access-controlled artifacts by stable ID and digest when necessary. A digest alone does not provide access control or authenticity.

### 2.3 Validation report

Validation is a recorded assessment against the frozen specification, not a generic assertion that a run “worked.”

```yaml
validation_id: "stable-validation-id"
run_id: "stable-run-id"
spec_id: "stable-spec-id"
reviewer: "person or independently configured process"
reviewed_at: "RFC3339 timestamp with timezone"
status: "SUPPORTED | CONTRADICTED | INCONCLUSIVE | REJECTED | UNASSESSED"
criteria_results:
  - criterion_id: "criterion-1"
    result: "PASS | FAIL | INCONCLUSIVE | NOT_RUN"
    evidence_ids: ["artifact-id"]
    explanation: "What was checked and observed"
baseline_comparison: "Defined comparison, result, or reason unavailable"
controls: "Results of controls or explicit limitation"
uncertainty: "Method, estimate, or not assessed"
failures_and_deviations: []
independent_replication: "Reference or NOT_PERFORMED"
limitations: []
```

`SUPPORTED` applies only to the scoped claim and criteria assessed. It is not a general certification, proof of causality, or production-readiness approval. Validation must retain failed and inconclusive outcomes.

### 2.4 Evolution record

Every proposed change should identify its parent baseline and a rollback point. Predictions are not results.

```yaml
change_id: "stable-change-id"
parent_commit: "immutable revision"
project_id: "stable-project-id"
hypothesis: "Why the change is expected to help"
predicted_improvement: "Metric and direction, or NONE"
baseline_run_id: "run-id or NOT_AVAILABLE"
changed_components: []
tests: []
test_results: "UNRUN until executed; link reports when complete"
performance_delta: "UNMEASURED until benchmarked"
resource_cost: "Measured value or UNKNOWN"
security_review: "PENDING | result and evidence reference"
evidence_references: []
decision: "PROPOSED | ACCEPTED | REJECTED | DEFERRED"
reviewer: "Independent reviewer or PENDING"
rollback_commit: "revision or NOT_AVAILABLE"
```

A change is not automatically accepted because an agent produced it or unit tests pass. Compare it to the previous working baseline on relevant correctness, security, reproducibility, performance, and resource criteria.

## 3. Independent Builder / Skeptic / Validator workflow

The three roles are a workflow pattern, not a claim that three independent agents are currently configured.

1. **Builder** receives the frozen specification and permitted inputs; proposes an implementation or analysis and links outputs to run manifests.
2. **Skeptic** receives the specification, evidence, and candidate result; searches for confounders, counterexamples, leakage, unsupported assumptions, and alternative explanations. The Skeptic records findings rather than silently editing source evidence.
3. **Validator** independently executes or checks predeclared acceptance criteria and records the validation report. The Validator must not merely repeat the Builder’s assertions.
4. **Adjudication** resolves disagreements explicitly, with a named human decision-maker when the consequence or risk requires it. No worker approves its own result or authorizes consequential actions.
5. **Evolution** links the accepted or rejected decision to a change record, parent revision, tests, and rollback point.

Independence requires more than different role names: record separate task inputs, prompts/configurations, versions, permissions, and any shared data or dependencies that could create correlated errors. If independence cannot be established, disclose that limitation.

## 4. Validation states and promotion

Use explicit states, with transitions supported by records:

`DRAFT -> SPEC_REVIEWED -> EXECUTED -> VALIDATED -> DECIDED`

A run may instead end in `FAILED`, `INCONCLUSIVE`, or `ABORTED`. A result must not advance merely because a workflow completed successfully. Promotion requires links to the required specification, execution manifest, output evidence, validation report, and decision. The required proof package depends on the claim and risk.

Keep implementation maturity separate from scientific evidence status. For example, passing unit tests can support a software-correctness claim under tested conditions; it does not validate a scientific hypothesis or an external integration.

## 5. Efficient, dependency-aware testing

For each uncertainty, state the competing explanations and choose the smallest valid experiment that can distinguish them. Record why a cheaper test is sufficient or why escalation is needed. A test selector may prioritize tests by cost and information value, but must not skip mandatory safety, security, or release gates.

A useful test plan includes, where relevant:

- deterministic replay and reproducibility checks;
- malformed, boundary, and corrupted-input cases;
- positive, negative, and sham controls;
- baseline, ablation, and held-out comparisons;
- uncertainty and sensitivity analyses;
- failure, recovery, concurrency, and resource-bound tests;
- independent reproduction for consequential claims.

Never substitute mock data, simulated values, placeholder agents, or hard-coded benchmark outputs for real measurements without labeling them clearly as simulations or fixtures.

## 6. Security, privacy, and audit boundaries

- Treat raw source artifacts as read-only; transformations create new, linked artifacts.
- Use least privilege for workers and separate read, write, review, and action capabilities.
- Do not store credentials, private keys, tokens, or unnecessary sensitive data in records.
- Hashes provide integrity checks only relative to a trusted digest. Authenticity requires a separately defined and verified trust mechanism.
- Record replay protection, key management, timestamp trust, access control, and durable storage as incomplete until implemented and tested.
- Require explicit authorization for external or irreversible actions. Research records and a validation result do not themselves authorize deployment or physical actuation.
- Preserve audit history and make corrections through new linked records, not silent replacement of prior evidence.

## 7. Domain-module boundary

Mathematics, biology, agents, physical experiments, weather, materials, and engineering may use distinct methods, data types, and acceptance criteria. Each module should publish its schema/version, assumptions, test method, and outputs through the shared contract. Do not force one domain’s algorithm or evidentiary standard onto another.

For IEVF specifically, retain the distinction between the 16-bit state space and any separate mathematical embedding. Algebraic or computational properties must be scoped to their stated conventions; they do not by themselves establish physical effects, quantum error correction, or practical advantage.

## 8. Adoption and implementation gates

This contract is documentation only until code, schemas, tests, and CI demonstrate otherwise. Suggested implementation order:

1. Define versioned schemas for the four records and validate examples.
2. Add deterministic serialization and tests for stable digests.
3. Link immutable input/output evidence IDs and execution manifests.
4. Add validation-state transition checks and retain failed outcomes.
5. Add an independent review workflow with permission boundaries.
6. Add signed attestations, key lifecycle, durable audit storage, and replay defenses only with explicit threat models and tests.
7. Integrate domain modules incrementally; preserve their separate validation criteria.

For every gate, report files changed, commands actually run, exact test results, unimplemented requirements, and confirmed GitHub operations. Do not describe a proposed design as implemented capability.
