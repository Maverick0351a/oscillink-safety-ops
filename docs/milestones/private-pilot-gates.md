# Private-pilot milestone gates

## Purpose

This ledger controls progression from the current engineering alpha to a bounded private pilot. A
completed gate records evidence; it does not authorize compliance conclusions, physical work,
repository publication, deployment, or equipment control.

## Active workflow

- **Asset:** one identified industrial asset or robot cell.
- **Task:** one bounded maintenance or integration task.
- **Evidence:** one rights-cleared manual/SOP/asset/task bundle with exact local bytes.
- **Reviewer:** one externally authorized reviewer whose identity and scope remain explicit.
- **Output:** a reviewable Safety Evidence Packet and deterministic offline findings.
- **Authority:** no compliance conclusion, permit, LOTO authorization, policy promotion, or physical
  command.

## Deferred work

Do not expand new OCR providers, jurisdictions, regulatory-publication shapes, facility or historian
connectors, CMMS integrations, robotics runtimes, near-real-time monitoring, hosted services, or user
interfaces before the technical-integrity and Stage 0 gates pass. Preserve the existing experimental
contracts without presenting them as validated workflows.

## Gate ledger

| Gate | Entry criterion | Exit criterion | Evidence location | Owner | State |
|---|---|---|---|---|---|
| M0 scope freeze | Current alpha baseline identified | One workflow active; expansion deferred | This document; `docs/execution-plan.md`; `docs/product-boundary.md` | Project owner | complete |
| M1 exact-byte integrity | Reproduced envelope substitution and poisoned-store defects | Adversarial tests pass; evaluated and persisted bytes match reported identities | Tests and exact-SHA verification record | Engineering | active |
| M2 evidence semantics | M1 complete | Compound states, prohibited conditions, byte counts, and lineage are explicit | Tests, schemas, technical overview | Engineering + authorized reviewer | blocked by M1 |
| M3 reviewer trust | M2 complete | Review metadata, authentication, and scope are distinct and fail closed | Trust-contract tests and security documentation | Engineering + authority owner | blocked by M2 |
| M4 private-alpha verification | M1–M3 complete | One exact SHA passes Windows, detached Buildbox, and authorized hosted CI | `docs/audits/` | Engineering | blocked by M3 |
| M5 Stage 0 validation | M4 candidate available | Practitioner recognition, local examples, authority owner, and budget gate pass | Sanitized validation summary | Product owner | blocked by M4 |
| M6 concierge pilots | Stage 0 passes | Three local runs; two confirmed actionable mismatches; lower review burden | Private pilot records and sanitized aggregate | Product owner + pilot reviewers | blocked by M5 |
| M7 commercial decision | Pilot gate passes | Proceed, narrow, integrate, or stop decision backed by buying evidence | Commercial gate record | Project owner | blocked by M6 |
| M8 public alpha | Explicit proceed decision | Publication/security/rights/CI gates and separate approvals pass | Publication checklist and release evidence | Project owner | conditional |

## Current finish line

The active milestone ends only when:

1. a plan or episode cannot be evaluated from bytes different from the bound envelope payload;
2. an existing content-addressed destination is re-verified and a mismatch fails closed;
3. the regression tests demonstrate RED before implementation and GREEN afterward;
4. the canonical verifier passes at the exact candidate state; and
5. the worktree contains only reviewed, intentional changes.

## Kill criteria

Stop or narrow the workflow if practitioners need ordinary work instructions or CMMS forms, simple
structured exports perform equivalently, rights prevent lawful processing, no qualified reviewer owns
decisions, review burden exceeds avoided reconciliation work, no recurring buyer appears, or value
requires compliance or operational authority.
