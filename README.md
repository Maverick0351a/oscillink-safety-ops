# Oscillink Safety Ops

**Governed safety evidence for physical intelligence.**

Oscillink Safety Ops connects workplace regulations, company SOPs, equipment manuals, asset
labels, risk assessments, work orders, and physical-intelligence plans or datasets through cited,
human-reviewed evidence.

> **Status:** Private product discovery. This repository does not yet contain operational software
> and makes no safety, compliance, certification, or deployment claim.

## First candidate outcome

Given one identified asset, a proposed maintenance task, and a bounded source set, produce a
reviewable **Safety Evidence Packet** showing:

- exact source bytes, revisions, pages/frames, and bounding boxes;
- asset/model/serial applicability;
- hazards, energy sources, prerequisites, roles, isolation, and verification evidence;
- stale procedures, source conflicts, missing evidence, ambiguity, and unreadable fields; and
- human review, correction, retraction, and supersession lineage.

The first workflow candidate is a read-only **LOTO/SOP Safety Evidence Reconciler**. It will be
implemented only after practitioner validation and a contract-first fixture.

## Authority boundary

Automated extraction may emit evidence states such as:

- `matched`
- `missing_evidence`
- `asset_mismatch`
- `revision_stale`
- `source_conflict`
- `ambiguous`
- `unreadable`
- `unsupported_interpretation`
- `requires_authorized_review`

It must not emit or grant:

- `safe`
- `compliant`
- `certified`
- `approved_to_operate`
- a work permit
- lockout/tagout authorization
- safety PLC, interlock, or emergency-stop changes
- robot, machine, or actuator commands

Safety Ops is not a safety-rated control system, legal opinion, compliance certificate, or
replacement for qualified EHS, maintenance, integration, or safety engineering.

## Product structure

```text
Regulations / standards metadata / manuals / SOPs / labels / work orders
                                 |
                                 v
                    content-addressed source intake
                                 |
                                 v
                 OCR/parser candidates + exact source regions
                                 |
                                 v
                external human review and correction lineage
                                 |
                                 v
                       Safety Evidence Packet
                                 |
                   +-------------+-------------+
                   |                           |
                   v                           v
          offline plan evaluation      dataset/episode evidence
                   |
                   v
          authorized human review
```

No arrow terminates in physical control.

## Relationship to Oscillink Agent

[Oscillink Agent](https://github.com/Maverick0351a/oscillink-agent) remains the dogfooded,
model-neutral memory, provenance, correction, evaluation, and recovery engine. Safety Ops is the
focused product vertical. The repositories communicate through explicit contracts and local MCP
rather than making either repository's internal database schema the other's product API.

## Why this direction

Primary evidence shows that physical work depends on authority outside model weights and sensor
streams:

- OSHA hazardous-energy rules require documented procedures, authorization, training, inspection,
  isolation, and verification.
- Current industrial-robot standards cover design, integration, operation, maintenance,
  decommissioning, and information for use.
- EU machinery rules address digital instructions, model applicability, lifecycle risk, autonomous
  behavior, and safety-affecting physical or digital modifications.
- Robotics issues show metadata, calibration, timestamp, camera-pose, and task-association failures
  that can remain silent until training or deployment.

The market for OCR, CMMS, digital work instructions, checklists, and generic robot-data quality is
already crowded. Safety Ops will not recreate those products. Its candidate differentiation is
binding exact approved safety evidence to physical-intelligence tasks, plans, datasets, and offline
evaluations.

See:

- [Product and authority boundary](docs/product-boundary.md)
- [Initial evidence map](docs/research/initial-evidence-map.md)
- [Execution plan](docs/execution-plan.md)
- [Practitioner interview protocol](docs/interview-protocol.md)
- [Security policy](SECURITY.md)

## Current gate

Before runtime implementation:

1. Interview at least five relevant practitioners.
2. Confirm the proposed document/task bundle reflects real work.
3. Obtain at least two sanitized or local-only example bundles.
4. Identify an authorized reviewer and measurable reconciliation burden.
5. Freeze a Safety Evidence Packet contract with hidden expected answers.

If users primarily need ordinary checklists, CMMS forms, document search, or certification, narrow
or stop this direction.

## Licensing

This private discovery repository does not yet grant a public software license. A reviewed
open-source/commercial boundary and third-party document-rights policy are required before public
release.
