# Publication-readiness audit — 2026-09-01

**State:** local pre-publication evidence; publication remains blocked

This audit records the repository and reachable-history checks performed while the GitHub repository
remained private. It does not authorize a push, release, visibility change, deployment, DNS edit, or
announcement.

## Audited state

- Repository: `Maverick0351a/oscillink-safety-ops`
- Local baseline at audit start: `1c6648c360cde59af8fcf7832d7844f762fba208`
- Reachable commits at history scan: 15
- Unique historical blobs: 176
- Remote visibility: private
- Remote default branch: `main`
- Local branch at audit start: 12 commits ahead of `origin/main`
- Live release: none
- Live topics: none
- Live homepage: unset
- Discussions: disabled
- Vulnerability alerts: disabled
- GitHub community-profile health: 71%

Remote values are point-in-time observations. Local files added by this milestone will not affect the
live GitHub surface until an explicitly authorized push.

## Secret-history scan

The scanner was obtained from the canonical `gitleaks/gitleaks` GitHub release:

- Tool: Gitleaks
- Version: `8.30.1`
- Release tag: `v8.30.1`
- Published by upstream: `2026-03-21T02:17:58Z`
- Windows x64 archive: `gitleaks_8.30.1_windows_x64.zip`
- Verified SHA-256: `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`
- Archive members inspected before extraction: `LICENSE`, `README.md`, `gitleaks.exe`
- Scan mode: complete reachable Git history
- Redaction: 100%
- Report location: temporary directory outside the repository

Result:

```text
15 commits scanned
approximately 675 KB scanned
0 findings
```

No secret value was printed, copied into this document, or stored in the repository.

## Historical path and blob review

A separate Git-object scan reported:

- risky historical credential, environment, key, database, or dump filenames: 0;
- blobs larger than 1 MB: 0;
- absolute Windows user-path markers: 0;
- absolute Linux home-path markers: 0;
- owner-designated public-scope exclusion hits: 0; and
- private hidden-evaluation bank path hits: 0.

The largest historical blob was below 41 KB. The scan classified paths and markers only; it did not
print candidate sensitive values.

## Dependency advisory review

A `pip-audit` scan of the installed locked environment initially found one development dependency
advisory:

- Package: `pytest 8.4.2`
- Advisory: `PYSEC-2026-1845`
- Summary: vulnerable temporary-directory handling
- Direct advisory source: OSV API record
- Affected range: all versions before `9.0.3`

The project previously constrained pytest to `<9`, which blocked the fixed version. The remediation
used a RED-GREEN policy test, changed the development range to `pytest>=9.0.3,<10`, regenerated the
lockfile, and installed pytest `9.1.1`.

The post-remediation audit result was:

```text
dependencies scanned: 19
known vulnerabilities: 0
```

This is an advisory-database result at one point in time. It is not proof that the dependency graph
contains no vulnerability.

## Community and release surface prepared locally

The milestone adds local candidate files for:

- conduct, support, security, contribution, and trademark policies;
- bug, read-only integration, and private-alpha issue forms;
- pull request verification and data-boundary checks;
- citation metadata and an unreleased changelog;
- release procedure and publication checklist; and
- deterministic repository-surface verification in the canonical gate.

These files have not been pushed or rendered by GitHub.

## Remaining blockers

Publication remains blocked until all applicable items in
[`docs/publication-checklist.md`](../publication-checklist.md) are complete. Current blockers include:

1. Re-run complete history and current-tree scans on the final exact candidate commit.
2. Verify the exact candidate independently on Linux.
3. Obtain explicit authorization to push while the repository remains private.
4. Require hosted Windows and Linux CI on the exact pushed SHA.
5. Enable and test a confidential vulnerability-reporting route.
6. Review and explicitly approve security settings, branch protection, topics, homepage, Issues, and
   Discussions.
7. Complete license, third-party-content, privacy, and artifact round-trip review.
8. Obtain a separate explicit authorization before any visibility change or release.

## Limitations

- Gitleaks and filename-pattern scans cannot prove the absence of every sensitive or proprietary
  value.
- The dependency audit covers advisories known to its databases at scan time.
- No hosted CI ran because nothing was pushed.
- No GitHub form, Markdown, citation, or social-preview rendering was inspected on the live remote.
- No independent legal, practitioner, engineering, regulatory, or OT-owner review occurred.
- No public clone, external-user test, release round-trip, website deployment, or DNS change occurred.

## Decision

Continue private local maturation. Do not push, publish, release, deploy, change visibility, or edit
DNS under this audit alone.
