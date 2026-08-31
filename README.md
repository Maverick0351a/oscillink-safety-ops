# Oscillink Safety Ops

**Governed safety evidence for physical intelligence.**

Oscillink Safety Ops connects workplace regulations, company SOPs, equipment manuals, asset
labels, risk assessments, work orders, and physical-intelligence plans or datasets through cited,
human-reviewed evidence.

> **Status:** Private product discovery with an experimental, read-only contract slice. The code
> performs deterministic offline evidence comparison only and makes no safety, compliance,
> certification, authorization, or deployment claim.

## First candidate outcome

Given one identified asset, a proposed maintenance task, and a bounded source set, produce a
reviewable **Safety Evidence Packet** showing:

- exact source bytes, revisions, pages/frames, and bounding boxes;
- asset/model/serial applicability;
- hazards, energy sources, prerequisites, roles, isolation, and verification evidence;
- stale procedures, source conflicts, missing evidence, ambiguity, and unreadable fields; and
- human review, correction, retraction, and supersession lineage.

The first workflow candidate is a read-only **LOTO/SOP Safety Evidence Reconciler**. A synthetic,
provider-neutral contract slice now tests its authority boundary; the workflow itself remains
unapproved pending practitioner validation.

## Local contract demonstration

Python 3.11 and `uv` are required. The fixture contains only project-authored synthetic bytes.

```bash
uv sync --dev
uv run safety-ops audit \
  --packet tests/fixtures/synthetic_press/packet.json \
  --plan tests/fixtures/synthetic_press/plan.json \
  --manifest tests/fixtures/synthetic_press/manifest.json
uv run python scripts/verify.py
```

The CLI reads immutable local inputs and emits cited evidence findings as JSON. It has no network,
robotics, permit, control, or physical-action integration.

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
- [2026-08-31 platform, market, and integration decision](docs/research/platform-market-integration-2026-08-31.md)
- [Execution plan](docs/execution-plan.md)
- [Practitioner interview protocol](docs/interview-protocol.md)
- [Security policy](SECURITY.md)

## Current gate

The synthetic contract slice may support technical risk reduction, but no workflow, adapter, or
commercial claim is approved before practitioner validation:

1. Interview at least five relevant practitioners.
2. Confirm the proposed document/task bundle reflects real work.
3. Obtain at least two sanitized or local-only example bundles.
4. Identify an authorized reviewer and measurable reconciliation burden.
5. Freeze a Safety Evidence Packet contract with hidden expected answers.

If users primarily need ordinary checklists, CMMS forms, document search, or certification, narrow
or stop this direction.

## Licensing

Oscillink Safety Ops is licensed under the [Apache License 2.0](LICENSE). The license applies to
the project-authored source and documentation in this repository unless a file states otherwise.
It does not grant rights to third-party standards, manuals, customer procedures, datasets, model
weights, services, or trademarks. A reviewed commercial boundary and document-rights policy are
still required before public release.
