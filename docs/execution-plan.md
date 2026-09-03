# Oscillink Safety Ops execution plan

## Goal

Build and publicly demonstrate the first credible Oscillink Safety Ops alpha as an independent
safety and risk-mitigation supervisor for AI-controlled industrial equipment while preserving the
existing governed evidence plane and forbidding real machine control.

## Approved public direction

The production AI runs the machine. Oscillink independently monitors whether commanded and observed
behavior remain within the approved operating envelope and requests a protective response when they
do not.

Batches 1-6 implemented exact-byte evidence, review lineage, offline evaluation, deterministic
closed-file replay/simulation, a persistent supervisor latch, local one-way simulated requests, a
synthetic benchmark, and a static monitor. Batch 7 prepares the private release candidate. Any real
integration remains a separate future decision and is not authorized by this plan.

Execution order is fail-closed:

1. normalize public scope, claims, assurance status, and runtime-safety research;
2. establish the hazard, lifecycle, requirements, function allocation, and traceability;
3. implement strict runtime contracts and immutable configuration;
4. implement deterministic correlation, policy, latch, recovery, and persistence;
5. add closed replay, adversarial tests, property/fuzz evidence, and formal analysis;
6. freeze a synthetic benchmark and static safety-manager demo;
7. verify the exact private candidate locally, on Buildbox, and in hosted CI; and
8. publish only after the separate public-release gates and explicit approval.

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

## Private-pilot scope freeze

The only active product workflow is one identified industrial asset or robot cell, one bounded
maintenance or integration task, one rights-cleared manual/SOP/asset/task evidence bundle, and one
externally authorized reviewer. Safety Ops may produce reviewable packets and offline findings only.

Until the private-pilot gates pass, preserve but do not expand the existing OCR research, regulatory
publication parsers, licensed-standard metadata, facility evidence adapters, robot-runtime seams,
hosted-service concepts, or user-interface concepts. The current milestone evidence and kill gates
are recorded in [`docs/milestones/private-pilot-gates.md`](milestones/private-pilot-gates.md).

## Deferred

- public visibility until the complete release gates pass;
- new jurisdictions or broader regulatory-publication parsers;
- additional OCR providers or generic document extraction;
- new facility, historian, CMMS, robotics-runtime, or near-real-time connectors;
- hosted services or production user interfaces;
- generic CMMS/checklists;
- work-instruction authoring;
- legal/compliance certification;
- employee authorization decisions;
- live field-device, fire-panel, safety-controller, or robot-runtime integration;
- replacement or duplication of listed/certified alarms and protective functions;
- alarm acknowledgement, reset, silence, inhibit, bypass, setpoint, or calibration writes;
- policy training/promotion;
- permits, lockout control, PLC/interlock/E-stop integration; and
- any actuator command.

Closed-file robot-cell replay, deterministic simulated intervention requests, and a static public
demonstrator are approved for later batches. They remain future work and must not be represented as
field, production, certification, or incident-prevention evidence.

## Current maturation state

The non-practitioner technical tracks are complete without conflating engineering evidence with
product validation:

1. Preserve the frozen Safety Evidence Packet v1 and leakage-controlled hidden evaluation design.
   The private 12-task bank is balanced across six classes, hash-bound by the public manifest, and
   intentionally unexecuted. Same-model authorship is not independent evaluation.
2. Preserve the metadata-only NFPA 70E and ISO 10218 registry. Licensed bytes, excerpts, requirement
   extraction, and applicability conclusions remain blocked until access, storage/processing rights,
   and authorized review are established.
3. Preserve the hardened generic JSONL adapter, now covered by manifest-bound synthetic fire-
   suppression, ammonia-monitoring, and autonomous-system exports, typed external-review and stale-
   impact contracts, plus sequence-gap, duplicate/out-of-order, missing-sequence, and parser-warning
   behavior. Historian, reporting-system, broker, and robot-runtime integrations remain later gates.
4. Preserve the narrowly versioned Federal Register/LSA extraction and correction/effective-date
   lineage, exact-source packet bindings, and offline plan/episode evaluator. Unsupported publication
   structures and unresolved evidence remain explicit.
5. Resume the first five practitioner interviews using `docs/interview-protocol.md` when access is
   available, then evaluate the Stage 0 gate honestly.

The canonical gate passed on Windows and Linux Buildbox for feature commit
`1337e2f72346966b9fdefae116f1c6f05633fd45` with 132 tests. The source distribution hash matched
across hosts and all wheel payload entries matched; platform-specific ZIP creator metadata caused the
outer wheel hashes to differ. Hosted CI still reflects `origin/main` because the maturation commits
remain local-only and no push was authorized. Passing local/Buildbox verification is reproducibility
evidence only.

The existing envelope, deterministic CLI validation, operational JSONL normalization and storage,
candidate-only event interpretation, external review ledger, stale-impact assessment,
envelope-bound audit report, and OSHA source catalog are experimental contracts. They do not satisfy
the Stage 0 market gate and do not justify workflow promotion, operational authorization,
practitioner-value, compliance, or safety claims.
