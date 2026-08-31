# Oscillink Safety Ops execution plan

## Goal

Validate and build the smallest governed safety-evidence product that physical-intelligence and
industrial-operations teams will run on real local documents and tasks without granting it
operational authority.

## Stage 0 — Problem validation

Interview at least:

- two EHS/safety professionals;
- two maintenance/reliability practitioners;
- two industrial robot integrators;
- two physical-AI/robotics data engineers; and
- two technical-publication, compliance, or equipment-manual owners.

Ask which documents govern one real task, how applicability/revisions are matched, how conflicts are
resolved, what requires an authorized person, what remains paper/PDF/image, and what local read-only
report they would run this week.

**Gate:** At least five practitioners recognize the proposed bundle; at least two can provide a
sanitized/local-only example; at least one identifies an owner and recurring budget/workflow.

## Stage 1 — Safety Memory Packet contract

A bounded synthetic contract slice may be built to test authority and portability without claiming
workflow validation. Promotion beyond that slice still requires the Stage 0 evidence gate:

- versioned JSON schema;
- source/artifact/revision identities;
- exact page/frame/bounding-box citations;
- raw extraction separated from normalized candidate fields;
- applicability, ambiguity, stale, conflict, missing, and unsupported states;
- external review, correction, retraction, and supersession records;
- deterministic policy/configuration hash; and
- explicit no-control/no-certification fields.

Use a synthetic fixture containing an asset label, manual excerpt, site LOTO SOP, work order/task
plan, and public OSHA excerpt. Keep expected answers outside agent-readable inputs.

**Gate:** adversarial RED→GREEN tests prove unapproved content cannot become approved constraints,
source changes stale derived packets, conflicts remain unresolved, and ambiguous OCR abstains.

## Stage 2 — Replaceable OCR/document adapters

Audit candidate extractors such as PaddleOCR, Docling, Marker, and a lightweight baseline. Record
exact versions, licenses, model/data rights, hashes, local/cloud data paths, bounding-box semantics,
confidence behavior, resource requirements, and uninstall/reversal paths.

Adapters emit candidates only. The packet schema and governance remain project-owned.

**Gate:** changing extractors does not change authority semantics; every output remains source-region
cited; unreadable/ambiguous fixture fields abstain.

## Stage 3 — Offline task/episode evaluator

Compare one symbolic task plan or recorded episode with an approved packet. Emit exact cited
matches, missing evidence, conflicts, and `requires_authorized_review` findings.

No plan execution, work-permit issuance, compliance score, or physical command.

**Gate:** deterministic hidden-label evaluation; equal budgets; explicit false-positive/false-
negative review costs; no unsupported “safe/compliant” output.

## Stage 4 — Private local pilot

Run with at least three organizations/users on their own local evidence. Measure:

- setup and ingestion time;
- source matching and review time;
- actionable mismatches;
- false positives/abstentions;
- stale revision/change impact;
- review authority and cleanup burden; and
- requested connectors/operated capabilities.

**Gate:** at least two users receive an actionable mismatch and review cost is lower than avoided
manual reconciliation burden.

## Deferred

- public launch;
- generic CMMS/checklists;
- work-instruction authoring;
- legal/compliance certification;
- employee authorization decisions;
- live sensors/robot runtime integration;
- policy training/promotion;
- permits, lockout control, PLC/interlock/E-stop integration; and
- any actuator command.

## Current next action

Complete the first five practitioner interviews using `docs/interview-protocol.md`. Do not begin the
runtime until the Stage 0 gate is evaluated honestly.
