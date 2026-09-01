# Viewer-surface baseline

**Evidence state:** observed
**Observed at:** 2026-09-01T18:11:03Z through 2026-09-01T18:11:31Z
**Scope:** local repository, live GitHub repository, and public DNS/HTTPS path

This is a point-in-time viewer-surface record. It does not establish release readiness, public-history
safety, market validation, practitioner value, compliance, certification, or production fitness.

## Local repository

| Field | Observed value |
|---|---|
| Working branch | `main` |
| Local HEAD | `081fb1179e68d7fd70d57b6309344eab5fc14da1` |
| Remote-tracking HEAD | `88d08b326e9fdf005529d26ef616e8fff1c81f00` |
| Ahead/behind | 10 ahead, 0 behind |
| Remote | `https://github.com/Maverick0351a/oscillink-safety-ops.git` |
| Tracked GitHub workflow | `.github/workflows/ci.yml` |
| Existing trust files | `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md` |

The local maturation work is not visible to a GitHub viewer because it has not been pushed. Local
polish must not be described as live GitHub state.

Internal Hermes plans are excluded through `.gitignore`. They may contain private strategy and are not
part of the product, public roadmap, release artifacts, or public-history surface.

## Live GitHub repository

Direct source: GitHub CLI/API for `Maverick0351a/oscillink-safety-ops`.

| Field | Observed value |
|---|---|
| Visibility | private |
| Default branch | `main` |
| Remote default-branch SHA | `88d08b326e9fdf005529d26ef616e8fff1c81f00` |
| Description | Governed safety evidence and offline evaluation for physical intelligence. |
| Homepage URL | empty |
| Topics | none |
| License detected | Apache License 2.0 |
| Issues | enabled |
| Discussions | disabled |
| Wiki | disabled |
| Latest release | none |
| Stars/forks | 0/0; not treated as product evidence |
| Community-profile health | 71% |
| Latest hosted CI | success on remote SHA `88d08b326e9fdf005529d26ef616e8fff1c81f00` |

### Present community files

- README;
- Apache-2.0 license;
- contribution guidance;
- security policy.

### Missing or incomplete viewer-facing files

- code of conduct;
- issue templates/forms;
- pull-request template;
- support policy;
- changelog/release notes;
- citation metadata;
- trademark boundary;
- repository social-preview image;
- repository topics and homepage URL.

### Security/settings observations

- GitHub returned HTTP 403 for branch protection on the private repository and stated that GitHub Pro
  or public visibility is required for the feature in the current configuration.
- Dependency vulnerability alerts are disabled according to the repository API.
- No conclusion was drawn about secret scanning, push protection, or private vulnerability reporting
  because those settings were not all established by the inspected endpoints.
- Hosted CI has not evaluated the ten local commits.

## README first-impression baseline

The local README already provides:

- a bounded category statement;
- explicit experimental/private status;
- a working local demonstration;
- Safety Evidence Packet v1;
- regulatory, operational, and episode evidence behavior;
- strong authority and no-control boundaries;
- security, licensing, research, and execution-plan links.

Viewer-facing gaps:

- implementation detail appears before a concise product walkthrough;
- no architecture image;
- no packet visualization;
- no repository social card;
- no short demo capture;
- the implemented/validating/not-claimed states are distributed across long sections rather than one
  compact matrix;
- deep technical detail is not separated into focused product documents.

The README should be reorganized, not stripped of its evidence and authority limits.

## Domain and HTTPS baseline

Direct sources: local DNS resolver, HTTPS response headers, and TLS certificate inspection.

| Field | Observed value |
|---|---|
| `oscillink.com` addresses | `192.0.79.156`, `192.0.79.173` |
| `www.oscillink.com` addresses | `192.0.79.156`, `192.0.79.173` |
| HTTPS response | `404 Not Found` |
| Server path | WordPress/nginx infrastructure |
| Certificate subject | `CN=wordpress.com` |
| Certificate SANs | `*.wordpress.com`, `wordpress.com` |
| Certificate validity | 2026-07-06 through 2026-10-04 |

The certificate does not cover `oscillink.com`; strict HTTPS hostname validation fails. The current
public destination is not a usable landing page.

These observations do not identify the complete Porkbun DNS zone. MX, TXT, SPF, DKIM, DMARC,
verification, and unknown records must be exported from the authoritative DNS control plane before any
future web-record mutation.

## Current proof available for future viewer material

The repository currently supports truthful statements about:

- deterministic local/offline evidence processing;
- exact content, source-revision, task, episode, and asset identity;
- explicit unknown, stale, conflict, correction, and retraction states;
- read-only operational evidence intake;
- Safety Evidence Packet v1;
- narrowly bounded official-source reconciliation;
- metadata-only licensed-standard governance;
- offline plan and recorded-episode findings;
- no operational command channel;
- Windows and detached Linux engineering verification.

These are technical proof points, not proof of compliance, legal correctness, safety, workflow value,
production readiness, or external practitioner validation.

## Reproduction commands

The following read-only command classes produced this baseline:

```bash
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git rev-list --left-right --count origin/main...HEAD
gh repo view Maverick0351a/oscillink-safety-ops --json ...
gh api repos/Maverick0351a/oscillink-safety-ops/community/profile
gh run list --repo Maverick0351a/oscillink-safety-ops ...
nslookup oscillink.com
nslookup www.oscillink.com
curl -I https://oscillink.com/
openssl s_client -connect oscillink.com:443 -servername oscillink.com
```

The abbreviated `--json ...` notation documents the command class rather than serving as a
copy-paste command. Refresh direct sources before any consequential launch decision.
