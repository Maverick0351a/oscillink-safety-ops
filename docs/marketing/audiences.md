# Viewer audiences and positioning

**Decision state:** approved by owner
**Observed/drafted:** 2026-09-01
**Approved:** 2026-09-01

## Public category

> **Oscillink builds governed compliance-evidence infrastructure for physical intelligence.**

Compliance is the problem domain. The product does not determine or guarantee compliance. It makes
the source, revision, asset context, review lineage, unresolved evidence, and offline findings around
physical-intelligence work inspectable.

## Hero candidate

> **Compliance evidence for the physical-intelligence era.**

## Supporting statement

As physical intelligence moves from research and pilots toward real-world operations, Oscillink
helps teams make the surrounding regulations, procedures, asset context, reviews, and operational
evidence inspectable and traceable.

## Product expression

Oscillink Safety Ops is the first product expression. It creates governed, reviewable evidence
connecting regulations, procedures, manuals, exact asset identity, plans, exported observations, and
recorded episodes. Its initial artifact is a Safety Evidence Packet accompanied by deterministic
offline findings.

The product remains outside compliance determinations, legal conclusions, certification, work
permits, lockout/tagout authorization, safety-rated controls, and physical actuation.

## Priority audiences

### 1. Physical-intelligence technical leaders

**Context:** Preparing robotics, autonomous systems, embodied AI, or industrial AI for bounded
real-world deployment.

**Problem to communicate:** The system's models, plans, logs, and datasets do not carry the external
regulatory, procedural, asset-specific, or review authority needed to understand the surrounding
compliance evidence.

**Relevant product evidence:**

- exact platform, adapter, source-revision, task, run, episode, asset/model/serial, and payload-hash
  binding;
- read-only exported-plan, log, observation, and episode intake;
- deterministic offline evaluation;
- explicit missing, stale, ambiguous, conflicting, corrected, and retracted states;
- no command channel.

**Desired next action:** Inspect the architecture or request a private technical walkthrough.

### 2. Safety, compliance, assurance, and operational-risk professionals

**Context:** Evaluating how established evidence and review practices should surround emerging
physical-intelligence systems.

**Problem to communicate:** Relevant regulations, standards metadata, manuals, procedures, permits,
asset evidence, and operational records are fragmented and can silently lose revision,
applicability, or review context when moved into AI workflows.

**Relevant product evidence:**

- preserved source class, jurisdiction, edition, effective date, supersession, and exact bytes;
- source candidates separated from authorized review;
- unresolved source conflicts remain unresolved;
- metadata-only rights handling for licensed standards;
- Safety Evidence Packet with fixed no-compliance and no-operational-authority states.

**Desired next action:** Review a synthetic packet and evaluate whether its evidence structure
reflects real review work.

### 3. Robotics, autonomous-system, and industrial-AI engineers

**Context:** Producing or consuming plans, datasets, simulations, logs, and episode evidence.

**Problem to communicate:** Technical artifacts can be internally consistent while missing exact
asset identity, source revision, approved constraints, or external review lineage.

**Relevant product evidence:**

- provider-neutral evidence envelopes;
- exact content hashes and bounded local loading;
- sequence-gap, duplicate, ordering, timestamp, and parser-warning evidence;
- offline plan and recorded-episode findings;
- no mutation of source systems or plans.

**Desired next action:** Run the synthetic demonstration from a clean clone.

### 4. Technical design partners

**Context:** Qualified teams willing to examine one bounded workflow without sharing sensitive
material publicly.

**Problem to communicate:** Product value and workflow fit remain unvalidated until a real reviewer
can assess one sanitized or local-only document/task bundle and its reconciliation burden.

**Desired next action:** Request a private discussion under explicit data, rights, privacy, and
authority boundaries.

## Audiences not targeted in this phase

- consumers;
- teams seeking a generic checklist, CMMS, document-search, or training product;
- buyers seeking an automated compliance determination or certification;
- users seeking robot, machine, PLC, interlock, emergency-stop, permit, or work-authorization
  control;
- organizations unwilling to identify an authorized external reviewer;
- teams that cannot lawfully provide or locally retain necessary source material.

## Message hierarchy

A viewer should encounter claims in this order:

1. Physical intelligence is moving toward real-world operations.
2. Compliance-relevant evidence remains external to model weights and operational telemetry.
3. Oscillink makes that evidence and its review state inspectable and traceable.
4. Safety Ops produces a bounded packet and offline findings today.
5. Applicability, interpretation, compliance, certification, and operational authorization remain
   external human decisions.

## Approved claim classes

Public material may describe implemented deterministic behavior:

- local and offline operation;
- provider-neutral contracts;
- exact source, revision, asset, task, episode, and hash binding;
- explicit missing, stale, ambiguous, conflicting, corrected, and retracted evidence;
- Safety Evidence Packet v1;
- read-only operational-export intake;
- narrowly supported official-source regulatory reconciliation with abstention;
- metadata-only rights governance for licensed standards;
- deterministic Windows/Linux engineering verification;
- no equipment command channel.

Tests and builds establish engineering behavior only. They are not compliance, safety, market,
practitioner, or production evidence.

## Claims requiring qualification

Use **candidate**, **experimental**, **designed to**, **under validation**, or equally explicit
language for:

- workflow fit;
- reviewer usefulness;
- reduced reconciliation effort;
- real integration coverage;
- portability outside verified hosts;
- regulatory interpretation;
- standards applicability;
- production deployment;
- market demand.

## Prohibited public claims

Do not say or imply that Oscillink or Safety Ops:

- ensures or guarantees compliance;
- certifies safety or conformity;
- legally verifies regulations;
- authorizes work, permits, LOTO, or operation;
- replaces qualified EHS, legal, maintenance, integration, or safety professionals;
- prevents incidents;
- is production proven or practitioner validated;
- controls equipment or forms part of a real-time safety-control loop.

## Public-scope exclusion

Directions outside the approved compliance-evidence category are intentionally omitted. Public
website copy, repository narrative, GitHub metadata, social cards, release notes, roadmaps, examples,
and outreach must stay within the category and product boundaries defined here.

## Evidence references

The current authority boundary is defined in:

- `AGENTS.md`;
- `docs/product-boundary.md`;
- `schemas/safety-evidence-packet-v1.schema.json`;
- `schemas/physical-intelligence-evidence-envelope.schema.json`;
- `docs/hidden-evaluation-protocol.md`.

Approved Project Memory records recalled for this draft:

- `mem_V1K4QHQ9M9CE4979CWNYTXHC1N` — read-only physical-intelligence retrieval;
- `mem_PGPS2E6GC2D1R24ZPET2JXP66H` — physical authority boundary;
- `mem_3X1K6GFW7TZTFWQ01DQMPBWGZ5` — read-only auditor product expression.

Repository and direct-source evidence take precedence over stale memory. The initial-state memory
record was not used for current repository facts because the live repository has advanced.
