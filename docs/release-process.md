# Release process

Oscillink Safety Ops has no published release. This process is a fail-closed candidate procedure; it
does not authorize a push, tag, release, visibility change, deployment, or announcement.

## Release identity

A release candidate must use one version across:

- `pyproject.toml` package metadata;
- the built wheel and source distribution;
- `CITATION.cff`;
- `CHANGELOG.md`;
- the annotated Git tag; and
- release notes and checksum manifest.

Runtime version behavior must be covered by a failing test before implementation changes. The current
`0.1.0` package version is development metadata, not evidence of a published release.

## Candidate sequence

### 1. Freeze scope

1. Choose the exact candidate commit range.
2. Confirm the approved public category and claims matrix.
3. Confirm all included fixtures are synthetic or permissively licensed and reproducible.
4. Confirm licensed standards remain metadata-only unless documented rights permit more.
5. Confirm private evaluation prompts, expected answers, customer data, and local artifacts are absent.

### 2. Audit the complete reachable history

Run a pinned high-confidence secret scanner across every reachable commit. Record:

- scanner name, version, canonical source, and verified checksum;
- exact Git object scope;
- redacted finding identifiers and paths;
- classification and remediation for every finding;
- risky historical filenames and large blobs;
- dependency and license review results; and
- limitations of the audit.

A clean current tree is insufficient if private history could become public.

### 3. Verify locally

From a clean worktree:

```bash
uv sync --locked --dev
uv run ruff format --check .
uv run ruff check .
uv run mypy
PYTHONPATH= uv run python scripts/verify.py
git diff --check
git status --short
```

Build artifacts into a fresh directory and inspect their embedded version, license, package contents,
and exclusion of private or runtime paths.

### 4. Commit the exact candidate

Record the full 40-character SHA. Re-run the complete gate after the candidate commit exists. Do not
rely on a pre-commit working-tree run as exact-SHA evidence.

### 5. Verify independently

Transfer an exact Git bundle to the independent Linux Buildbox. Verify the bundle checksum and commit
SHA, synchronize locked dependencies, run the canonical verifier, and compare source-distribution
hashes and wheel payloads.

This proves deterministic engineering behavior across the tested hosts. It does not prove legal,
practitioner, operational, or production validity.

### 6. Push while private

This step requires explicit owner authorization. Push the exact candidate while the repository is
still private, then require hosted CI on the exact SHA. Stop if either OS job fails or is canceled.

Do not change visibility before hosted CI passes.

### 7. Prepare portable release artifacts

Create an annotated tag on the verified SHA. Build artifacts from a clean tag checkout. Generate a
`SHA256SUMS.txt` containing basenames only. Verify a fresh download in an isolated directory that
cannot reach the original build outputs.

### 8. Publish only after a separate approval

A release, visibility change, GitHub settings change, website deployment, or announcement requires a
separate explicit approval after the [publication checklist](publication-checklist.md) is complete.

## Release notes template

Each release note must state:

- exact tag and full commit SHA;
- implemented evidence contracts;
- deterministic local, Buildbox, and hosted-CI results;
- artifact checksums;
- known unsupported inputs and parser shapes;
- rights and privacy limits;
- practitioner, legal, engineering, and OT-owner review that has not occurred; and
- the fixed no-compliance-conclusion and no-operational-authority boundary.

Do not translate tests, synthetic demonstrations, internal review, stars, downloads, or CI into claims
of safe operation, compliance, customer outcomes, practitioner validation, or production readiness.

## Rollback

Before publication, record how to:

- return the repository to private visibility if needed;
- withdraw or mark a release;
- revoke compromised artifacts and publish corrected checksums;
- remove a hosted preview;
- restore prior DNS records; and
- preserve correction and retraction lineage without rewriting public evidence history.

Git history must not be rewritten after publication unless a confirmed sensitive-data exposure makes
that necessary and the incident response documents the consequences.
