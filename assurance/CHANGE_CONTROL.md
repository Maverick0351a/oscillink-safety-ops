# Assurance change control

## Scope

All changes to `SCOPE-ROBOT-CELL-001` hazards, requirements, controls, allocations, tests, evidence,
configuration assumptions, output boundary, or claims require impact analysis before merge or
promotion. This process controls a synthetic demonstrator; it is not a machinery modification or
certification process.

## Workflow

1. Open a change record with one stable `CI-*` ID and identify proposer, rationale, affected files
   and stable IDs, target revision, and rollback/retirement intent.
2. Classify impact on hazard coverage, safety requirement meaning, interfaces/allocations, authority,
   timing, configuration, evidence, cybersecurity/common cause, test oracle, and public claims.
3. Obtain review from `ROLE-SAFETY-OWNER`; require `ROLE-INDEPENDENT-REVIEWER` when a requirement is
   weakened, retired, reinterpreted, or affects an unresolved target-system assumption.
4. Add a failing test before changing verifier or runtime behavior. Preserve failed evidence and
   anomaly links.
5. Update all affected trace rows and evidence records atomically. Stable IDs are never silently
   reused for changed meaning; create a new ID and mark the old item retired with rationale.
6. Run focused tests, the canonical verifier, and repository diff hygiene. Record exact command,
   source revision, environment, output, and reviewer disposition.
7. Block promotion if evidence is missing, malformed, stale, contradictory, or scoped to different
   bytes/configuration.

## Change-impact records

| Change impact ID | Controlled subject | Mandatory impact review | Owner/status |
|---|---|---|---|
| `CI-001` | Occupancy-motion exclusion | zone definition; unknown occupancy; observation independence; request/latch oracle | `ROLE-SAFETY-OWNER`; planned |
| `CI-002` | Unexpected start | reset/rearm/recovery/start transitions; stale start; controller recovery assumptions | `ROLE-SAFETY-OWNER`; planned |
| `CI-003` | Command/actual correlation | frames; units; sequence attribution; correlation windows; orphan motion | `ROLE-SAFETY-OWNER`; planned |
| `CI-004` | Motion envelope | limits; units; coordinate frames; configuration authority; stopping implications | `ROLE-SAFETY-OWNER`; planned |
| `CI-005` | Observation health | required sources; missing/stale/frozen/contradictory semantics; diagnostics | `ROLE-SAFETY-OWNER`; planned |
| `CI-006` | Timebase/order | clock ownership; freshness; skew; sequence; watchdog; restart epochs | `ROLE-SAFETY-OWNER`; planned |
| `CI-007` | Output path | one-way local boundary; request identity; acknowledgment semantics; no stopping claim | `ROLE-SAFETY-OWNER`; planned |
| `CI-008` | Configuration integrity | exact bytes; authority; rollback/revocation; partial publication; mid-run change | `ROLE-SAFETY-OWNER`; planned |
| `CI-009` | Restart persistence | durable state; corruption; missing state; epoch identity; fail-closed recovery | `ROLE-SAFETY-OWNER`; planned |
| `CI-010` | Reset/rearm | role authority; prerequisites; event separation; no automatic or remote start | `ROLE-SAFETY-OWNER`; planned |
| `CI-011` | Production-AI isolation | accepted input schema; credentials; administration attempts; evidence suppression | `ROLE-SAFETY-OWNER`; planned |
| `CI-012` | Common cause | power; network; sensor; time; compute; updates; credentials; final elements | `ROLE-SAFETY-OWNER`; planned |

## Baseline and evidence rules

A baseline binds exact source revision, artifact bytes, configuration/scenario identities, tool and
dependency versions, test inventory, outputs, open anomalies, and reviewer identity/scope. Passing
results do not overwrite failed results. Generated evidence is immutable or content-addressed when
introduced; a changed byte produces a new identity.

Every `TRACEABILITY.csv` row must contain owner, status, and one change-impact ID. Every
`evidence-index.json` record must identify owner, status, requirements, tests, and change impact.
The traceability verifier rejects orphaned or duplicate safety/evidence identities and malformed
records.

## Claims and target-system changes

Any proposal to connect to live equipment, add an address/credential/protocol writer, enable remote
reset, or claim PL/SIL, stopping performance, diagnostic coverage, application validation,
independence, field effectiveness, certification, compliance, or operating authority is outside
this batch and requires a separately approved program. PLr, SIL, total stopping time, diagnostic
coverage, application validation, and unresolved common-cause assumptions remain TBD for qualified
target-system assessment.
