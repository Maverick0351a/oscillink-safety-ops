# Publication checklist

This checklist is fail-closed. An unchecked item blocks its external action. Completion does not
authorize a commit, push, tag, release, visibility change, deployment, or announcement.

## Claims and product boundary

- [x] Approved headline is used in README, package metadata, and release notes.
- [x] Implemented runtime status says closed-file simulation/replay and local simulated one-way
      request records only.
- [x] Synthetic benchmark, TLA+ abstraction, property/fuzz tests, and CI are labeled software evidence.
- [x] No real machine/control/network output, certification, PL/SIL achievement, safe-operation,
      field-validation, or production-readiness claim is made.
- [x] Apache-2.0 public core, separate commercial layers, and retained trademark boundary are stated.

## Source, data, privacy, and rights

- [x] Public fixtures are project-authored synthetic or explicitly permissively licensed and pinned.
- [x] No credential, customer/employee record, facility layout, production export, private prompt,
      protected label, incident data, or licensed standards text is intentionally tracked.
- [x] Licensed standards remain metadata-only.
- [x] Transitive dependency licenses receive independent review across all 23 locked third-party
      packages; see `docs/audits/transitive-license-review-2026-09-03.md`.

## Reachable-history and dependency audit

- [x] Gitleaks 8.30.1 archive checksum is pinned and verified.
- [x] Baseline `2943db23ceb075e8955867903069cd5e043fee45` audit records 28 commits, 657 objects,
      423 blob revisions, zero findings, zero risky filenames, and zero blobs over 10 MiB.
- [x] Public-key, negative private-key-marker, deterministic test signing-seed, and URL-path indicators
      are explicitly classified without treating indicators as secrets.
- [x] `cryptography` was updated from vulnerable 46.0.7 to 50.0.1 and pip-audit 2.10.1 reports zero
      known vulnerabilities for the resolved runtime requirements.
- [ ] Final exact-candidate reachable history is scanned externally after the candidate commit exists.

## Repository trust surface

- [x] Issue forms, pull-request template, contribution, conduct, security, support, trademark,
      changelog, citation, Dependabot, release notes, and release process are structurally tested.
- [x] Workflow actions are immutable-SHA pinned with minimal permissions, no secrets, safe events,
      concurrency controls, and no publish/deploy step.
- [ ] GitHub private vulnerability reporting is enabled and read back before public visibility.
- [ ] Branch protection and security settings are configured and read back in Batch 8.

## Exact candidate and artifacts

- [ ] Batch 7 changes are committed and exact candidate SHA recorded.
- [ ] Clean exact-SHA Windows canonical verifier and both direct pytest forms pass.
- [ ] Detached independent Linux Buildbox verification passes on the exact candidate.
- [ ] Hosted Windows/Linux verification, CodeQL, dependency audit, and Gitleaks pass on that SHA.
- [x] Release tooling requires wheel, source distribution, CycloneDX SBOM, unsigned provenance,
      benchmark metrics, formal result, basename-only checksums, and isolated verification.
- [ ] Exact candidate artifacts are built and verified after the candidate commit exists.
- [ ] Published assets, if separately authorized, are downloaded and verified in isolation.

## Promotion

- [ ] No unresolved blocker remains.
- [ ] Owner gives separate explicit authorization for the exact push, tag, release, visibility, or
      external action.
- [ ] Batch 8 verifies public API visibility, anonymous clone, community rendering, release download,
      and fresh-clone quickstart without credentials.
