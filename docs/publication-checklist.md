# Publication checklist

This checklist records the completed public-alpha promotion gates. It does not authorize a future
release, deployment, announcement, or other external-system mutation.

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
- [x] Final exact-candidate reachable history was scanned externally with Gitleaks 8.30.1 after the
      candidate commit existed; zero findings were reported across all reachable commits.

## Repository trust surface

- [x] Issue forms, pull-request template, contribution, conduct, security, support, trademark,
      changelog, citation, Dependabot, release notes, and release process are structurally tested.
- [x] Workflow actions are immutable-SHA pinned with minimal permissions, no secrets, safe events,
      concurrency controls, and no publish/deploy step.
- [x] GitHub private vulnerability reporting is enabled and read back immediately after public
      visibility (GitHub exposes this feature only for public repositories).
- [x] Branch protection, Dependabot alerts/updates, secret scanning, push protection, Issues, and
      Discussions were configured and read back in Batch 8.

## Exact candidate and artifacts

- [x] Release tag `v0.1.0-alpha.1` resolves to exact candidate
      `fd560f8290d4f503aadd03f42c2e572d64921d2b`.
- [x] Clean exact-SHA Windows canonical verifier and both direct pytest forms passed.
- [x] Detached independent Linux Buildbox verification passed on the exact candidate.
- [x] Hosted Windows/Linux verification, CodeQL, dependency audit, and Gitleaks passed on that SHA.
- [x] Release tooling requires wheel, source distribution, CycloneDX SBOM, unsigned provenance,
      benchmark metrics, formal result, basename-only checksums, and isolated verification.
- [x] Exact-candidate artifacts were built by the tag-triggered workflow and verified after the
      candidate commit existed.
- [x] All eight published release assets were downloaded without credentials and verified in an
      isolated directory against the manifest and basename-only checksums.

## Promotion

- [x] No unresolved publication blocker remains.
- [x] Owner gave separate explicit authorization for the exact push, tag, release, visibility, and
      external action.
- [x] Batch 8 verified public API visibility, anonymous clone, community rendering, release download,
      and fresh-clone quickstart without credentials.
