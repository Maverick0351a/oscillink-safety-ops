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

The frozen Safety Evidence Packet v1 now binds one exact Safety Memory Packet to asset/task context,
explicit applicability unknowns, deterministic configuration identity, and separately typed
unresolved evidence with source/constraint reference validation. The committed packet is synthetic,
reviewable evidence only; its schema fixes interpretation/applicability authority to none,
compliance to no conclusion, and operational authority to none.

The offline recorded-episode evaluator now verifies an exact provider-neutral episode envelope and
payload, binds packet revision/hash and source-record hashes, and emits deterministic cited evidence
states only. It cannot claim compliance, authorize operation, mutate a plan, or control equipment.

## Stage 1A — Governed authority-source verification

Build a source-verification layer before promoting extracted requirements:

- reconcile dated eCFR XML with the official annual CFR baseline, Federal Register amendments, and
  the List of CFR Sections Affected;
- preserve exact package identities, publication dates, section-level citations, source bytes, and
  SHA-256 hashes;
- distinguish `unreviewed_source`, `verified_regulatory_source`, extraction candidate, and approved
  constraint states;
- require an external reviewer identity, role, decision, and time before source promotion;
- preserve unexplained differences, corrections, delayed effective dates, supersession, and stale
  status; and
- add metadata-only records for licensed standards such as NFPA 70E until properly licensed content
  is available.

Source verification confirms publication fidelity only. It does not establish jurisdiction,
applicability, interpretation, compliance, or operational approval.

The first contract slice now models exact annual-CFR, dated-eCFR, Federal Register, and LSA evidence;
section-level reconciliation findings; external source-review identity; candidate-hash binding; and
source-only promotion. It is exercised with synthetic metadata and hashes only.

The next implemented contract slice adds 16-MiB bounded and root-contained local artifact
verification, exact byte-count/SHA-256 checks, DTD/entity rejection, deterministic extraction for the
currently observed eCFR and GovInfo annual-CFR XML section shapes, and conservative normalized-text
comparison. A mismatch remains unresolved; no heuristic or parser can explain it without cited
Federal Register and LSA evidence. Current parser coverage is intentionally narrow and synthetic.

The next contract slices add normalized Federal Register action/effective-date/page candidates, exact
LSA status and Federal Register page-coverage candidates, deterministic source-change bundles, and
external reviews bound to exact bundle hashes. Narrow versioned parsers recognize observed GovInfo
Federal Register issue XML amendment paragraphs and monthly LSA HTML section entries only after exact
artifact verification. Explicit correction, delayed-date, and withdrawal links produce deterministic
publication chains while unsupported and withdrawn states remain non-explainable. Exact verified-
source impact reports mark missing roles, changed artifact hashes, changed package identities, and
changed dated-eCFR dates stale. Bounded CLI commands verify artifacts, extract supported XML sections,
and conservatively compare snapshots. Pinned redistributable official fixtures, broader publication
shape coverage, and Linux/hosted-CI evidence remain required before any real source revision can be
considered for promotion.

**Gate:** every promoted source revision is reproducible from pinned official publications; every
difference is explained by cited amendment evidence or remains explicitly unresolved; no source or
parser can promote its own requirements.

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

## Stage 3A — Read-only operational evidence connectors

Extend the provider-neutral envelope to facility monitoring evidence without entering a safety or
control loop. Begin with synthetic or sanitized exports for:

- fire-alarm, suppression, supervisory, trouble, impairment, inspection, and test records;
- ammonia and hazardous-gas detector events, calibration, communication, and quality states;
- refrigeration, ventilation, pressure, temperature, level, and emergency-shutdown event history;
- historian tag inventories and configuration revisions; and
- management-of-change, mechanical-integrity, procedure, and authorized-review records.
- autonomous-system event logs, run/episode identity, component versions, sequence gaps, parser
  warnings, and source-declared protective-event history.

Implement connectors in three bounded steps:

1. offline CSV/JSON/XML exports;
2. read-only historian replicas, vendor reporting APIs, file drops, or broker subscriptions in an
   approved OT/IT boundary; and
3. near-real-time evidence discrepancy monitoring only after practitioner, vendor, OT-security, and
   change-management review.

Every observation must preserve facility/system/device identity, source tag, units, timestamps,
quality, calibration revision, adapter/configuration hash, immutable payload hash, communication
gaps, and explicit missing/unsupported fields. Telemetry remains observational evidence and cannot
establish safe entry, acceptable concentration, system readiness, or permission to operate.

Autonomous-system logs must preserve exact raw bytes separately from normalized records and derived
interpretations. Interpretations remain cited candidates under external review; they cannot update
the autonomous policy, change a task plan, issue a protective action, or create a reverse command
channel.

Adapters must expose no alarm acknowledge/silence/reset, suppression release/abort, zone disable,
detector inhibit, threshold/calibration write, PLC/BACnet write, OPC UA method, valve/fan/pump/
compressor command, emergency-shutdown reset, generic protocol pass-through, or credential
forwarding.

**Gate:** adversarial tests prove the adapter surface is read-only; undeclared tags and methods fail
closed; bad-quality or missing values never normalize to zero/normal/safe; source changes stale all
dependent findings; existing listed/certified systems retain all alarm and protective authority.

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
- direct field-device, fire-panel, safety-controller, or robot-runtime integration;
- replacement or duplication of listed/certified alarms and protective functions;
- alarm acknowledgement, reset, silence, inhibit, bypass, setpoint, or calibration writes;
- policy training/promotion;
- permits, lockout control, PLC/interlock/E-stop integration; and
- any actuator command.

## Current next action

Bounded tracks may proceed without conflating technical evidence with product validation:

1. Complete the first five practitioner interviews using `docs/interview-protocol.md` and evaluate
   the Stage 0 gate honestly.
2. Preserve the frozen Safety Evidence Packet v1 and leakage-controlled hidden evaluation design.
   The private 12-task bank is balanced across six classes, hash-bound by the public manifest, and
   intentionally unexecuted. Same-model authorship is not independent evaluation.
3. Preserve the metadata-only NFPA 70E and ISO 10218 registry. Licensed bytes, excerpts, requirement
   extraction, and applicability conclusions remain blocked until access, storage/processing rights,
   and authorized review are established.
4. Extend the experimental generic JSONL adapter, now covered by manifest-bound synthetic fire-
   suppression, ammonia-monitoring, and autonomous-system exports plus typed external-review and
   stale-impact contracts, with sequence-gap and parser-warning behavior before considering any
   historian, reporting-system, broker, or robot-runtime integration.

The existing envelope, deterministic CLI validation, operational JSONL normalization and storage,
candidate-only event interpretation, external review ledger, stale-impact assessment,
envelope-bound audit report, and OSHA source catalog are experimental contracts. They do not satisfy
the Stage 0 market gate and do not justify workflow promotion, operational authorization,
practitioner-value, compliance, or safety claims.
