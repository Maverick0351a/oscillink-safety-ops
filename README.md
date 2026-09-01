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
PYTHONPATH= uv run safety-ops envelope validate \
  --envelope tests/fixtures/synthetic_press/envelope.json \
  --root tests/fixtures/synthetic_press
PYTHONPATH= uv run safety-ops audit \
  --packet tests/fixtures/synthetic_press/packet.json \
  --plan tests/fixtures/synthetic_press/plan.json \
  --manifest tests/fixtures/synthetic_press/manifest.json \
  --envelope tests/fixtures/synthetic_press/envelope.json \
  --root tests/fixtures/synthetic_press
PYTHONPATH= uv run safety-ops episode-evaluate \
  --packet tests/fixtures/synthetic_press/safety-evidence-packet-v1.json \
  --episode tests/fixtures/synthetic_press/episode.json \
  --envelope tests/fixtures/synthetic_press/episode-envelope.json \
  --root tests/fixtures/synthetic_press
PYTHONPATH= uv run safety-ops operational normalize \
  --input tests/fixtures/operational_evidence/synthetic-operational.jsonl \
  --batch-id batch:synthetic-operational-001 \
  --source-revision export:synthetic-operational-001 \
  --adapter-config-sha256 sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --store-root runtime/operational-evidence
PYTHONPATH= uv run python scripts/verify.py
```

The CLI reads immutable local inputs and emits cited evidence findings as JSON. Audit reports bind
the exact platform, adapter configuration, source revision, and payload hash from the validated
envelope. The audit path has no network, robotics, permit, control, or physical-action integration.
The recorded-episode evaluator verifies exact local payload bytes, binds the packet revision and
packet hash, and emits the same closed evidence states for observed episode evidence. Its fixed output
is `evidence_findings_only` with no interpretation, applicability, compliance, or operational
authority.

## Safety Evidence Packet v1

The frozen [`SafetyEvidencePacket`](schemas/safety-evidence-packet-v1.schema.json) wraps one exact
Safety Memory Packet in an identified asset/task context. It preserves jurisdiction, site,
model/serial, task and role context, explicit applicability unknowns, packet/configuration identity,
and separately typed unresolved evidence. Every issue must reference sources and constraints inside
the exact nested memory packet. Duplicate or dangling identities fail closed.

The deterministic
[`safety-evidence-packet-v1.json`](tests/fixtures/synthetic_press/safety-evidence-packet-v1.json)
fixture is synthetic and reproducible with `scripts/generate_packet_fixture.py`. Its fixed state is
`reviewable_evidence_packet`; interpretation and applicability authority remain `none`, compliance
remains `no_conclusion`, and operational authority remains `none`. Constraint-level synthetic review
records do not turn the packet into a permit, certification, safe-work decision, or approval to act.

## Licensed-standard metadata

The [`LicensedStandardRegistry`](schemas/licensed-standard-registry.schema.json) records publisher,
designation, edition, publication metadata, official metadata URL, observation time, and explicit
supersession for NFPA 70E and ISO 10218 metadata. No licensed standard bytes, extracts, storage paths,
or derived requirements are present. Content access is `not_supplied`; storage and processing rights
are `not_confirmed`; applicability remains `undetermined`; and review remains `not_reviewed`.

The registry is metadata-only and has no interpretation, applicability, compliance, or operational
authority. Full-text intake remains blocked until lawful access and compatible storage/processing
rights are separately confirmed.

## Physical Intelligence Evidence Envelope

The provider-neutral
[`PhysicalIntelligenceEvidenceEnvelope`](schemas/physical-intelligence-evidence-envelope.schema.json)
binds one exported platform artifact to:

- exact platform, adapter, version, and adapter-configuration identities;
- artifact type, portable source/payload references, immutable source revision, and content hash;
- timezone-aware observation time plus optional asset, task, run, episode, and simulation identities;
- portable provenance references and explicit missing or unsupported fields; and
- fixed `read_only` access and `untrusted_data` treatment.

Unknown fields are rejected. The envelope cannot carry a write token, callback, command method, or
operational authorization, and `verify_envelope_payload` fails closed if the referenced local bytes
escape the supplied root, are absent, or no longer match the declared SHA-256. Platform adapters
remain replaceable readers; they do not define safety-memory semantics or gain approval authority.

## Read-only operational evidence

The experimental provider-neutral JSONL adapter reads synthetic fire-suppression, ammonia-
detection, and autonomous-system exports through one bounded contract. It:

- preserves system, component, source-tag, timestamp, quality, calibration, missing, and unsupported
  field evidence;
- reports bounded per-stream sequence gaps, duplicate/out-of-order sequence values, missing sequence
  identity, and out-of-order observation times without filling or reordering records;
- hashes the exact source artifact and each normalized source record;
- stores the immutable raw export separately under a caller-controlled, content-addressed root;
- rejects unknown fields, including attempted alarm, controller, or robot command surfaces; and
- permits exact event-code rules to emit deterministic interpretation candidates only.

Interpretation candidates bind the exact raw-record hash, rule, interpreter identity, version, and
configuration hash. Their fixed states are `candidate` and `no_operational_authority`; they cannot
acknowledge an alarm, alter a policy, approve a constraint, establish a safety conclusion, or send a
command back to the source system. The committed fixture is project-authored synthetic data, not a
validated facility or autonomous-system integration.

`adapter_warnings` is reserved for adapter-derived evidence and cannot be supplied by the source.
Sequence findings retain previous/current record identities and bounded missing ranges, remain
`observational_evidence`, and carry no operational authority. They do not prove data loss, equipment
state, alarm state, or unsafe operation.

External interpretation reviews bind the exact candidate SHA-256 plus reviewer identity, role,
authority reference, time, decision, and correction/retraction lineage. Accepting an interpretation
does not approve a constraint or operation. Deterministic change-impact assessment marks every
dependent review lineage when its source record disappears, its record bytes change, its enclosing
artifact changes, or its source revision changes; it never silently carries a review onto new bytes.
The operational fixture bytes are pinned by
[`tests/fixtures/operational_evidence/manifest.json`](tests/fixtures/operational_evidence/manifest.json).

Review ledgers and current-source impact can be validated offline with:

```bash
PYTHONPATH= uv run safety-ops operational review-validate \
  --ledger runtime/operational-review-ledger.json
PYTHONPATH= uv run safety-ops operational impact \
  --ledger runtime/operational-review-ledger.json \
  --current-input tests/fixtures/operational_evidence/synthetic-operational.jsonl \
  --batch-id batch:synthetic-operational-current \
  --source-revision export:synthetic-operational-current \
  --adapter-config-sha256 sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

The impact report binds the exact review-ledger file hash, current source-artifact hash, source
revision, adapter-configuration hash, and affected review IDs. A changed adapter configuration
stales prior interpretations even when the exported source bytes are unchanged.

## Starting OSHA source knowledge base

[`knowledge/osha/catalog.json`](knowledge/osha/catalog.json) catalogs all 67 parts in the reviewed
point-in-time snapshot of OSHA's official Regulations (Standards — 29 CFR) index. It includes
reserved parts and preserves one currently unavailable eCFR source (`70a`) explicitly rather than
silently omitting it. Available source XML can be reproduced into a gitignored, content-addressed
local cache with:

```bash
PYTHONPATH= uv run python scripts/sync_osha_knowledge.py --jobs 1
```

The catalog and retrieved regulation bytes remain untrusted source evidence. They do not establish
jurisdiction, applicability, interpretation, compliance, or an approved safety constraint. See the
[OSHA catalog notes](knowledge/osha/README.md) for snapshot, refresh, eCFR, and authority limits.

The initial official-source verification contract separately requires exact artifacts for all four
roles: a GovInfo annual CFR baseline, dated eCFR point-in-time bytes, Federal Register change
evidence, and the applicable GovInfo List of CFR Sections Affected. Each artifact preserves its
official package identity, URL, SHA-256, byte count, section citation, and retrieval time. Promotion
to `verified_regulatory_source` requires an external review bound to the exact candidate SHA-256 and
is blocked by missing evidence, unexplained differences, or findings that do not cover every source.

`verified_regulatory_source` means only that the reviewed source revision was reconciled against the
declared official evidence bundle. Its fixed states remain `interpretation_state = not_approved`,
`applicability_state = undetermined`, `constraint_state = not_approved`,
`compliance_state = no_conclusion`, and `operational_authority = none`. No real OSHA source revision
has been promoted by the synthetic contract tests.

The bounded regulatory-artifact slice verifies local source bytes under a caller-controlled root
before parsing: paths cannot escape the root, inputs are capped at 16 MiB, and declared byte counts
and SHA-256 hashes must match. Its deterministic XML extractor currently recognizes the dated eCFR
`TYPE="SECTION"`/`N` structure and GovInfo annual-CFR `SECTION`/`SECTNO`/`SUBJECT` structure. DTD and
entity declarations are rejected. Extracted text remains a `source_extraction_candidate` bound to
the exact artifact, locator, parser identity/configuration, and normalized-text hash.

An exact annual-CFR/eCFR normalized-text hash match emits reconciliation evidence only. Any text
difference remains `unresolved_difference` until separately cited Federal Register and LSA evidence
is collected and accepted by an externally authorized source reviewer. The normalized Federal
Register candidate preserves document number, publication/effective date, Federal Register start
page, action, exact affected citations, raw instruction text and hash, source locator, and parser
configuration. The normalized LSA candidate preserves its exact citation, through-date, status text,
listed Federal Register page references, raw entry and hash, locator, and parser configuration. A
review bundle fails closed when the comparison is already matched, citations or official page/
document references do not align, effective dates are missing or later than the eCFR date, or LSA
coverage ends before the eCFR date.

Only an external review bound to the exact bundle SHA-256 can emit an
`explained_official_change` source finding. Unknown or withdrawn amendment actions cannot be marked
explained. This is source-review evidence only: no accepted bundle establishes legal meaning,
applicability, compliance, an approved constraint, or operational authority. Narrow, versioned
parsers now recognize GovInfo Federal Register issue XML amendment paragraphs and monthly LSA HTML
section entries only after exact artifact verification. Federal Register correction, delayed-date,
and withdrawal candidates require explicit prior-document links before deterministic chain
resolution; withdrawals and unsupported actions remain explicit and cannot become explained
findings. Parser fixtures are synthetic representations of observed official shapes. Broader official
publication coverage and pinned redistributable official fixtures remain required before real source
promotion.

Exact verified-source reviews are also reassessed against current official evidence. A missing
required role, changed artifact hash, changed official package identity, or changed dated-eCFR
`as_of` date marks the prior source verification stale and identifies every affected review. Reviews
never carry automatically onto new source bytes or revisions.

The bounded artifact and section commands are available offline:

```bash
PYTHONPATH= uv run safety-ops regulatory artifact-verify \
  --evidence runtime/regulatory/evidence.json \
  --artifact-ref source.xml \
  --root runtime/regulatory
PYTHONPATH= uv run safety-ops regulatory section-extract \
  --evidence runtime/regulatory/evidence.json \
  --artifact-ref source.xml \
  --root runtime/regulatory \
  --citation "29 CFR 1910.147" \
  --parser-config-sha256 sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
PYTHONPATH= uv run safety-ops regulatory section-compare \
  --annual runtime/regulatory/annual-section.json \
  --ecfr runtime/regulatory/ecfr-section.json
```

All paths above are illustrative. The commands consume caller-supplied local evidence and emit JSON;
they do not retrieve sources, review findings, promote sources, or contact equipment.

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
- log-derived policy promotion or autonomous-system commands
- automatic carry-forward of reviews after source bytes or revisions change

Safety Ops is not a safety-rated control system, legal opinion, compliance certificate, or
replacement for qualified EHS, maintenance, integration, or safety engineering.

## Product structure

```text
Regulations / standards metadata / manuals / SOPs / labels / work orders
Facility-monitoring exports / autonomous-system logs
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
- [Hidden evaluation protocol v1](docs/hidden-evaluation-protocol.md)
- [Practitioner interview protocol](docs/interview-protocol.md)
- [Security policy](SECURITY.md)

## Current gate

The canonical verifier passed on Windows and on the independent Linux Buildbox for immutable feature
commit `1337e2f72346966b9fdefae116f1c6f05633fd45`: Ruff, formatting, strict mypy, package builds,
schema/catalog/fixture checks, and 132 tests. The source distribution hash matched across hosts; wheel
payload entries matched, while ZIP creator metadata remained platform-specific. Hosted CI has not
evaluated the local-only maturation commits because they have not been pushed. This is reproducibility
evidence only, not release, safety, compliance, applicability, or practitioner validation.

The synthetic contract slice may support technical risk reduction, but no workflow, adapter, or
commercial claim is approved before practitioner validation:

1. Interview at least five relevant practitioners.
2. Confirm the proposed document/task bundle reflects real work.
3. Obtain at least two sanitized or local-only example bundles.
4. Identify an authorized reviewer and measurable reconciliation burden.
5. Independently review the frozen Safety Evidence Packet v1 and its hash-bound hidden task bank;
   the current bank has same-model authorship and has intentionally not been executed.

If users primarily need ordinary checklists, CMMS forms, document search, or certification, narrow
or stop this direction.

## Licensing

Oscillink Safety Ops is licensed under the [Apache License 2.0](LICENSE). The license applies to
the project-authored source and documentation in this repository unless a file states otherwise.
It does not grant rights to third-party standards, manuals, customer procedures, datasets, model
weights, services, or trademarks. A reviewed commercial boundary and document-rights policy are
still required before public release.
