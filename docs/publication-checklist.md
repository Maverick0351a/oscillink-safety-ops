# Publication checklist

This checklist is deliberately fail-closed. An unchecked item blocks the corresponding external
action. Completing the checklist does not itself authorize a push, release, visibility change,
deployment, DNS edit, or announcement.

## Public scope and claims

- [ ] Category, hero, supporting statement, and audience order remain owner-approved.
- [ ] Directions outside the approved public category are absent from repository files, metadata,
      visuals, navigation, social cards, release notes, website routes, and outreach.
- [ ] Implemented, in-validation, and not-claimed states match executable evidence.
- [ ] Compliance evidence is not described as a compliance determination.
- [ ] Tests and synthetic demonstrations are not described as practitioner, legal, operational,
      customer, safety, or production validation.
- [ ] No certification seal, approval mark, generic robot imagery, or misleading dashboard is used.

## Source, data, privacy, and rights

- [ ] Every public fixture is project-authored or permissively licensed and hash-pinned.
- [ ] No customer SOP, permit, incident record, employee data, facility layout, equipment secret,
      production export, runtime database, credential, or private prompt is tracked.
- [ ] Hidden evaluation prompts, expected answers, and protected labels are absent.
- [ ] Licensed standards remain metadata-only unless lawful access and processing rights are recorded.
- [ ] Third-party notices and license metadata have been reviewed.
- [ ] No analytics, form, or contact-data collection exists without approved privacy, retention,
      access, deletion, and incident-response terms.

## Full-history audit

- [ ] A pinned scanner from its canonical publisher has been checksum-verified.
- [ ] Every reachable commit has been scanned for high-confidence credentials.
- [ ] Historical risky filenames, large blobs, binary artifacts, dumps, databases, keys, and local
      runtime paths have been reviewed.
- [ ] Findings are recorded in redacted form and every finding is classified.
- [ ] Personal absolute paths and environment identifiers have been reviewed.
- [ ] Locked dependencies and known advisories have been reviewed.
- [ ] Audit limitations and the exact scanned Git object scope are recorded.

## Repository trust surface

- [ ] README, license, contribution, conduct, security, support, trademark, citation, issue, and pull
      request files render correctly.
- [ ] Architecture and packet visuals are deterministic, accessible, visually inspected, and free of
      private, customer, and licensed content.
- [ ] Every quickstart command has been exercised from committed synthetic fixtures.
- [ ] Repository description, topics, homepage, Issues, and Discussions settings are owner-approved.
- [ ] A tested private vulnerability-reporting route exists.
- [ ] Dependency alerts, security updates, secret scanning, and push protection are enabled where
      supported.
- [ ] Branch protection uses exact observed hosted-CI check names and preserves a safe owner path.

## Exact candidate verification

- [ ] Worktree is clean and the exact candidate SHA is recorded.
- [ ] `PYTHONPATH= uv run python scripts/verify.py` passes on the committed SHA.
- [ ] `git diff --check` passes.
- [ ] Built source and wheel contents contain no excluded paths or data.
- [ ] Independent Linux Buildbox verification passes on the exact SHA.
- [ ] Source-distribution and wheel-payload comparisons are recorded accurately.
- [ ] The candidate is pushed while the repository remains private.
- [ ] Hosted Windows and Linux CI pass on the exact pushed SHA.

## Release identity and round-trip

- [ ] Package, citation, changelog, tag, release-note, and runtime versions agree.
- [ ] Annotated tag points to the exact verified commit.
- [ ] Release artifacts were built from a clean tag checkout.
- [ ] `SHA256SUMS.txt` contains basenames only.
- [ ] Published assets were downloaded into an isolated directory.
- [ ] Downloaded checksums verify without access to original artifacts.

## Visibility and external verification

- [ ] Owner explicitly approves the visibility change after reviewing this checklist.
- [ ] Public repository API reports the intended visibility and default-branch SHA.
- [ ] Unauthenticated clone succeeds without credentials.
- [ ] README, community files, issue forms, social preview, and release render correctly.
- [ ] Fresh-clone quickstart succeeds from an untrusted temporary directory.
- [ ] External smoke tests are labeled maintainer-run evidence, not external-user validation.

## Website and DNS

- [ ] A private, unindexed HTTPS preview has passed claims, accessibility, responsive, and link review.
- [ ] Current Porkbun DNS records have been exported without exposing credentials.
- [ ] MX, TXT, verification, and mail-related records are identified and preserved.
- [ ] Apex, `www`, TLS, canonical redirect, and rollback values are documented.
- [ ] Owner explicitly approves DNS cutover immediately before the change.
- [ ] Apex HTTPS, `www` redirect, certificate SAN coverage, and rollback path are verified after cutover.

## Final decision

- [ ] All blockers and residual limitations are recorded.
- [ ] Owner gives a separate explicit authorization for the exact external action.
- [ ] The action is performed without bundling any additional visibility, hosting, release, or DNS
      change.
