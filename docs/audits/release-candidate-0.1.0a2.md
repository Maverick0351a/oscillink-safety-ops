# Release-candidate evidence — 0.1.0 alpha 2

**Evidence class:** maintainer-generated software, formal-model, CI, packaging, and public-readback evidence

## Exact identity

- Package version: `0.1.0a2`
- Human tag: `v0.1.0-alpha.2`
- Tagged commit: `58cb8e494018481ac81810c56cdfffd20bb6c993`
- Annotated tag object: `c3de8600b6caa6d0b1d07c0f15f5e1184385f476`
- Pull request: [#2](https://github.com/Maverick0351a/oscillink-safety-ops/pull/2)

The tag remains fixed to the verified candidate. This post-publication record is a later documentation
commit and does not alter the release identity.

## Local and independent verification

The exact candidate passed the canonical verifier on Windows with 586 tests passed and 7 skipped.
A clean detached checkout created from an exact Git bundle passed on Buildbox Linux with 593 tests
passed. The platform difference is expected: Linux executes link/path cases that Windows skips.

Both hosts verified:

- 36/36 exact benchmark cases across 12 fault families and three runs per case;
- the ten-category shared-dependency/common-cause campaign;
- 29 rejected production-AI compromise attempts and zero runtime control-surface findings;
- restart, output uncertainty, attribution history, recovery, schemas, traceability, Ruff, formatting,
  strict mypy, wheel/source builds, and package identity;
- pinned TLA+ Tools v1.7.4, with 891 generated states, 82 distinct states, search depth 10, zero queued
  states, and no invariant violation.

## Hosted evidence

The exact candidate passed:

- [Ubuntu and Windows verification](https://github.com/Maverick0351a/oscillink-safety-ops/actions/runs/33942928435);
- [CodeQL, dependency audit, and full-history Gitleaks](https://github.com/Maverick0351a/oscillink-safety-ops/actions/runs/33942928496);
- [hosted TLC, property, fuzz, and benchmark replay](https://github.com/Maverick0351a/oscillink-safety-ops/actions/runs/33942594233); and
- [tag-triggered release artifact construction](https://github.com/Maverick0351a/oscillink-safety-ops/actions/runs/33942944854).

The tag-triggered workflow created six governed artifacts plus `release-verification.json` and
`SHA256SUMS.txt`. The downloaded artifact set was verified in an isolated directory against package
version `0.1.0a2` and the exact candidate commit.

## Public round-trip

- GitHub release: [v0.1.0-alpha.2](https://github.com/Maverick0351a/oscillink-safety-ops/releases/tag/v0.1.0-alpha.2)
- Hugging Face benchmark revision: `be77064fb545b03d4d77933b222fcfe0550b46b6`
- Hugging Face Space revision: `5fca4511be9c931f904c649c54d3875b74dcd22c`

All eight GitHub release assets were downloaded without credentials into a new directory and passed
isolated manifest and checksum verification. Twelve staged benchmark files and six staged Space
files were downloaded anonymously at their exact revisions and matched the staged bytes. The static
Space loaded 36 scenarios, loaded the exact governed logo, exposed no button/form/input control
surface, had no horizontal overflow, and changed only displayed evidence when its selector changed.

A credential-free shallow clone resolved to the exact tagged/default-branch candidate, installed
`0.1.0a2`, passed the documented benchmark and demo commands, and passed the canonical verifier with
583 tests passed and 10 explicit shallow-history/platform skips.

## Assurance limits

This evidence establishes reproducible software behavior and publication integrity for the exact
candidate. It does not establish field performance, physical stopping, target-system independence,
stopping time, diagnostic coverage, PLr/SIL, application validation, certification, compliance,
safe operation, or operational authority. TLA+ remains an abstract finite model without a mechanical
refinement proof to the Python runtime or physical equipment.
