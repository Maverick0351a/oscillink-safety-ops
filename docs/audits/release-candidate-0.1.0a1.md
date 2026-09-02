# Release-candidate verification — 0.1.0 alpha 1

**Verification date:** 2026-09-01
**State:** private local release-candidate evidence; not published

This record covers the implementation candidate before this evidence document was committed. The
evidence-document tip requires its own exact-SHA verification because documentation changes alter the
source distribution.

## Candidate identity

- Implementation commit: `9ed5f47b6dff1e9be4a6821897ae3273b3562d39`
- Package version: `0.1.0a1`
- Intended human-facing tag: `v0.1.0-alpha.1`
- Git bundle SHA-256:
  `a76e1e6c1d2f4833d1e33c44ee6b84c5825c103ae9e6f1ec6256ae92ba23f4c8`
- Repository state during verification: private and unpushed

No tag or release was created.

## Host and verifier results

| Evidence | Windows authoring host | Linux Buildbox |
| --- | --- | --- |
| Python | CPython 3.11.15 | CPython 3.11.15 |
| uv | 0.12.0 | 0.12.0 |
| Git state | clean candidate commit | fresh detached candidate commit |
| Canonical verifier | passed | passed |
| Tests | 156 passed | 156 passed |
| Ruff | passed | passed |
| Formatting | passed | passed |
| Strict mypy | passed | passed |
| Package build | passed | passed |
| Isolated release verification | passed | passed |

The bundle digest was verified before the Linux checkout was created. The Linux checkout and
transport bundle were removed after artifacts were produced.

## Portable release directories

Each host produced an isolated directory containing exactly:

- `oscillink_safety_ops-0.1.0a1.tar.gz`
- `oscillink_safety_ops-0.1.0a1-py3-none-any.whl`
- `release-verification.json`
- `SHA256SUMS.txt`

The repository-owned verifier confirmed package name, package version, full commit identity,
basename-only artifact names, exact byte counts, SHA-256 values, regular-file status, checksum-file
agreement, and absence of extra files.

## Cross-platform artifact comparison

### Source distribution

Both hosts produced the same SHA-256:

```text
f0cd0abe62684b46dbcc8540d819a506fba4ee4213a8e7d54591f439c5c4ca44
```

The source distributions are byte-identical for this candidate.

### Wheel

Outer archive SHA-256 values differed:

```text
Windows: c1a0f95c8c39117a7cf02d6d3ad89faeb158159f150be1a3637e518da878030b
Linux:   cb36780f888667e74cbc09f8e2995dd3e06c94956c2a430a0a24846972d5108d
```

Layered inspection established:

- wheel member-name sets: identical;
- wheel members compared: 19;
- uncompressed member payload differences: 0;
- entries with ZIP metadata differences: 19; and
- differing metadata field: `create_system` only (`0` on Windows and `3` on Linux).

Therefore the wheel payload entries are identical, while the outer wheel archives are not
bit-identical. No stronger reproducible-wheel claim is made.

## Package inspection

The Windows-built wheel was installed into a fresh CPython 3.11 environment outside the repository.
The installed package reported runtime version `0.1.0a1`.

Wheel inspection confirmed:

- package name `oscillink-safety-ops`;
- version `0.1.0a1`;
- license expression `Apache-2.0`;
- `safety-ops = oscillink_safety_ops.cli:main` entry point; and
- no `.hermes`, hidden evaluation bank, runtime, or virtual-environment paths.

The source distribution was also inspected for those excluded paths.

## Security and dependency evidence

Against the implementation candidate:

- reachable commits scanned by checksum-verified Gitleaks 8.30.1: 18;
- redacted secret findings: 0;
- installed dependencies scanned by `pip-audit`: 19; and
- known dependency vulnerabilities reported: 0.

These tools cannot prove the absence of every secret or vulnerability. Results are bounded to their
rules and advisory databases at scan time.

## Authority and validation limits

This evidence establishes deterministic engineering behavior on two tested hosts. It does not
establish legal correctness, regulatory applicability, compliance, certification, safe operation,
production readiness, independent practitioner validation, work authorization, or equipment-control
authority.

Hosted CI has not evaluated this candidate because pushing was not authorized. Public clone,
external-user, release-download, website, deployment, and DNS verification have not occurred.

## Promotion decision

Keep the candidate private and unpushed. A push while private, hosted CI, tag, release, visibility
change, deployment, or announcement each remains separately approval-gated.
