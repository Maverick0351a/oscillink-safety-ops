# Changelog

All notable project changes are recorded here. The project follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses the package prerelease identity
`0.1.0a1` for the intended tag `v0.1.0-alpha.1`.

## [Unreleased]

## [0.1.0-alpha.1] — Unreleased

### Added

- Governed exact-byte evidence, source/revision lineage, external review, and offline evaluation.
- Deterministic runtime contracts, immutable signed configuration, command/state correlation,
  fail-closed policy, persistent intervention latch, and recovery authority separation.
- Closed-file robot-cell simulation/replay with local simulated one-way protective-stop and inhibit
  request records; no machine or network output.
- 36-case project-authored synthetic benchmark and read-only safety-manager demo.
- TLA+ finite abstraction, property tests, minimized fuzz-regression corpus, and traceability gates.
- SHA-pinned Windows/Linux verification, CodeQL, dependency audit, Gitleaks history scan, nightly
  assurance replay, and release-candidate workflows.
- CycloneDX SBOM, unsigned provenance metadata, hardened release manifest, package archive inspection,
  and isolated artifact verification.
- Community, security, support, citation, trademark, issue, contribution, and release-readiness files.

### Security

- Runtime and release inputs reject traversal, symlinks/nonregular files, changed bytes, duplicate
  identities, malformed/noncanonical JSON, untrusted authority, and incomplete artifact sets.
- Runtime dependency `cryptography` is constrained to `>=50.0.0,<51` after the 46.0.7 advisory gate.
- No physical-control, compliance-conclusion, certification, permit, or work-authorization surface.

### Verification status

Local Windows and independent Linux Buildbox verification establish deterministic software behavior
only. Hosted CI, final exact-candidate history scanning, tag creation, release publication, public
clone, field validation, practitioner review, and production deployment remain unperformed or gated.
No public version or release tag has been published.

[Unreleased]: https://github.com/Maverick0351a/oscillink-safety-ops/commits/main
