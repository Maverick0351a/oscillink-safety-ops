# Safety lifecycle plan

## Purpose

This plan governs assurance work for `SCOPE-ROBOT-CELL-001`. It begins before runtime implementation
and controls requirements, tests, evidence, anomalies, reviews, and changes. It is an engineering
plan for a synthetic demonstrator, not a certification plan or authorization to connect to machinery.

## Roles and independence

| Role ID | Responsibility | Independence rule |
|---|---|---|
| `ROLE-SAFETY-OWNER` | Owns hazard log, requirements, open assumptions, and acceptance recommendations. | Cannot approve their own implementation evidence as an independent assessment. |
| `ROLE-VERIFICATION-LEAD` | Specifies deterministic tests, preserves expected outcomes, and reports anomalies. | Must not silently weaken a requirement to make a test pass. |
| `ROLE-CONFIGURATION-CUSTODIAN` | Controls baseline identity, authorized changes, and evidence linkage. | Production AI and replay input producers cannot hold this authority. |
| `ROLE-SECURITY-OWNER` | Reviews production-domain separation, credentials, tamper paths, and common cause. | Must assess shared dependencies rather than infer independence from logical boundaries. |
| `ROLE-INDEPENDENT-REVIEWER` | Reviews hazard coverage, requirement rationale, evidence sufficiency, and open claims. | Must be organizationally and technically independent to the degree required by the eventual target assessment; that degree is TBD. |
| `ROLE-RELEASE-MANAGER` | Confirms exact source/evidence identity and blocks unsupported claims. | Cannot promote missing, malformed, stale, or failed evidence as passing. |

Trace rows use `ROLE-SAFETY-OWNER` as the accountable owner. Execution and review responsibilities
may be delegated, but accountability and independent-review status remain explicit.

## Lifecycle stages and gates

1. **Scope and hazard analysis:** freeze the simulated item boundary; record foreseeable misuse and
   all mandatory hazard families.
2. **Requirements:** assign stable `SR-*` IDs, rationales, controls, complete function allocation,
   test IDs, evidence IDs, owner, status, and change-impact rule.
3. **Implementation:** use vertical RED → GREEN → REFACTOR. Runtime source is forbidden in this
   batch and begins only under a later approved batch.
4. **Verification:** use deterministic closed-file fixtures; retain exact inputs, configuration,
   expected outcomes, software identity, and actual results.
5. **Independent review:** review unresolved assumptions, anomalies, trace completeness, and claim
   wording. Automated tools cannot approve their own outputs.
6. **Release decision:** fail closed for missing/stale/malformed evidence. A release decision covers
   the synthetic artifact only and confers no machine-control or certification status.

## Requirement status

Allowed statuses are `planned`, `implemented`, `verified`, `blocked`, and `retired`. All Batch 2
requirements are `planned`. `implemented` requires the corresponding runtime behavior and focused
unit/integration evidence. `verified` additionally requires the planned evidence record to be
replaced or supplemented by an immutable passing result reviewed against the exact baseline.

## Anomaly management

Any test failure, unclear requirement, nondeterminism, malformed evidence, trace orphan, unexpected
runtime state, or boundary violation becomes a tracked anomaly. The anomaly record must contain:
source and configuration identity; reproduction; affected IDs; first observed revision; safety and
claim impact; containment; owner; disposition; independent-review need; and closure evidence.
Failed evidence remains retained and cannot be overwritten by a later pass.

## Supplier and tool controls

Third-party libraries, simulators, operating systems, clocks, storage, CI services, and controller
fixtures are not trusted as proof of safety. Their versions and assumptions must be recorded. Tool
use follows `TOOL_POLICY.md`; a green verifier proves only the coded/documented gate.

## Release evidence

A later release baseline must include exact source revision, locked dependencies, configuration and
scenario hashes, test inventory/results, traceability verdict, anomaly disposition, platform
results, limitations, and reviewer identity/scope. Synthetic evidence must remain labeled synthetic.
No absent evidence may be represented as successful.

## Qualified assessment decision points

Before any target-system integration claim, qualified personnel must determine applicable law and
standards, machinery risk assessment, required risk reduction, architecture, PLr/SIL route, sensor
and diagnostic design, total response/stopping performance, common-cause measures, environmental and
cybersecurity assumptions, final elements, validation methods, and residual-risk acceptance.

PLr, SIL, total stopping time, diagnostic coverage, application validation, and unresolved
common-cause assumptions remain TBD for that assessment.
