# Marketing and launch decision register

**Decision state:** public category, hero, supporting statement, and audience order approved; implementation decisions remain proposed
**Drafted:** 2026-09-01
**Positioning approved:** 2026-09-01

This register separates approved preparation work from consequential external actions. A local plan,
successful build, synthetic demonstration, or internal review does not authorize publication,
deployment, data collection, or DNS changes.

## Product and company decisions

| Decision | State | Rationale |
|---|---|---|
| Position Oscillink around governed compliance evidence for physical intelligence | Approved | Focuses the public story on an emerging, concrete governance gap. |
| Present Safety Ops as the first public product | Proposed | It has implemented, inspectable contracts and deterministic evidence. |
| Keep compliance determination external to the product | Required boundary | Repository and approved authority contracts prohibit automated compliance conclusions. |
| Omit directions outside the approved compliance-evidence category | Owner-directed | Public material stays focused on the current category and product. |
| Treat tests as engineering evidence only | Required boundary | Tests do not establish compliance, safety, market value, or practitioner validation. |
| Keep physical control outside the product | Required boundary | Safety Ops is read-only and may not command equipment or join a real-time safety loop. |

## Public narrative candidates

### Category

> **Oscillink builds governed compliance-evidence infrastructure for physical intelligence.**

### Hero

> **Compliance evidence for the physical-intelligence era.**

### Supporting statement

As physical intelligence moves from research and pilots toward real-world operations, Oscillink
helps teams make the surrounding regulations, procedures, asset context, reviews, and operational
evidence inspectable and traceable.

### Product statement

Safety Ops connects exact regulations, procedures, manuals, asset identity, reviews, plans, exported
observations, and recorded episodes into a reviewable Safety Evidence Packet and deterministic offline
findings.

### Mandatory qualifier

Safety Ops does not establish applicability, legal interpretation, compliance, certification, work
authorization, or authority to operate. It does not control equipment.

The category, hero, supporting statement, and audience order were approved by Maverick on
2026-09-01. The product statement remains bounded by the mandatory qualifier above.

## Repository decisions

| Decision | State | Notes |
|---|---|---|
| Improve Safety Ops as the technical trust surface | Approved to prepare locally | README, focused docs, visuals, community files, release evidence, and audit. |
| Keep internal `.hermes` plans outside Git | Approved to implement | Prevents private strategy from entering a future public history. |
| Keep the repository private during preparation | Current requirement | Visibility changes are a separate evidence-gated owner decision. |
| Do not push the ten local commits yet | Current requirement | The live remote must not change without explicit approval. |
| Require exact-SHA hosted CI before public visibility | Required gate | Local and Buildbox evidence alone are insufficient for launch. |
| Perform full-history audit before public visibility | Required gate | Current-tree cleanliness cannot establish historical publication safety. |
| Publish only a prerelease initially | Proposed | Any release remains deterministic engineering evidence, not product validation. |

## Website decisions

| Decision | State | Notes |
|---|---|---|
| Use `oscillink.com` as a compliance-focused company site | Proposed | Homepage explains the market transition and introduces Safety Ops. |
| Build the site in a separate `oscillink-web` repository | Proposed | Decouples company-site deployment from Python product releases. |
| Use Astro static output | Proposed | Small attack surface, portable hosting, no runtime server required. |
| Use Cloudflare Pages for the first preview | Proposed | Supports exact-SHA static previews; Vercel remains a fallback. |
| Keep the first preview unindexed | Required gate | Prevents accidental launch during review. |
| Start without CMS, analytics, forms, or cookies | Proposed | Avoids unnecessary operational and privacy scope. |
| Use a mail link only after a suitable company address exists | Proposed | Avoid publishing a personal address or collecting form data prematurely. |

Recommended public routes:

- `/` — physical-intelligence compliance-evidence problem and company narrative;
- `/safety-ops` — product artifact, workflow, proof, maturity, and limits;
- `/research` — regulatory evidence, standards metadata, provenance, and evaluation;
- `/about` — company purpose and contact;
- `/privacy` — privacy state before any analytics or collection.

Do not create a public platform page during this phase.

## Visual decisions

Proposed direction: human-clear industrial cyberpunk.

- near-black/navy foundation;
- cyan for provenance and exact identity;
- amber for unresolved or review-required states;
- red only for blocked or conflicting states;
- restrained motion that explains evidence flow;
- monospace for hashes, source identity, and revisions;
- readable editorial typography for safety/compliance material;
- every synthetic visual labeled `Synthetic demonstration — not facility evidence`.

Do not use robot stock art, shields, certification seals, fake dashboards, customer logos,
testimonials, fake usage counters, or decorative AI particles.

## Domain decisions

| Decision | State | Notes |
|---|---|---|
| Keep Porkbun as registrar | Proposed | Registrar migration is unnecessary for the initial site. |
| Build and verify preview before DNS changes | Required gate | Current domain is broken, but a blind cutover would add risk. |
| Use `https://oscillink.com` as canonical | Proposed | Redirect `www` to apex after both hostnames validate. |
| Export the complete DNS zone before mutation | Required gate | Web records cannot be safely changed without preserving mail/verification records. |
| Preserve MX/TXT/SPF/DKIM/DMARC and unknown records | Required gate | Avoid email or ownership-verification outages. |
| Maintain exact rollback values | Required gate | Rollback must remain possible until production is stable. |

The currently observed WordPress records and invalid hostname certificate are evidence that the public
path needs replacement. They are not authorization to delete any Porkbun record.

## Approval boundaries

### May proceed locally without another approval

- positioning drafts;
- claims matrix and audience definitions;
- README and documentation edits;
- synthetic product visuals;
- local website prototypes;
- local static website source;
- local tests and builds;
- read-only repository/domain inspection;
- full-history audit with redacted findings;
- Buildbox exact-SHA verification.

### Requires explicit approval immediately before action

- creating a remote website repository;
- pushing Safety Ops or website commits;
- connecting a private repository to a hosting provider;
- creating a hosted preview;
- publishing a GitHub release;
- changing repository visibility;
- enabling public Discussions;
- enabling analytics, forms, CRM, or email collection;
- entering registrar/hosting credentials;
- changing Porkbun or authoritative DNS;
- making `oscillink.com` indexable/public.

Credentials, API keys, recovery codes, private DNS exports, and secret values must never be stored in
source, screenshots, issue text, plan files, or chat summaries.

## Launch gates

### Repository gate

- product-first README and visuals;
- complete community/security surface;
- version and release identity agreement;
- full-history audit;
- clean local exact-SHA verification;
- detached exact-SHA Buildbox verification;
- push while still private;
- hosted Windows/Ubuntu CI on the exact SHA;
- unauthenticated clone and release round-trip only after public approval.

### Website preview gate

- approved information architecture and copy;
- mobile and desktop design review;
- accessibility and reduced-motion checks;
- static-output secret/private-term scan;
- valid HTTPS;
- exact preview SHA;
- `noindex`/`nofollow` enforced;
- no analytics or form collection;
- no broken link to a private repository.

### Production-domain gate

- complete DNS backup;
- exact host-provided records;
- preserved mail and verification records;
- apex and `www` certificate coverage;
- canonical redirect;
- external DNS/HTTP/browser verification;
- rollback values retained;
- explicit owner approval.

## Open owner decisions

1. Confirm `oscillink-web` as the separate website repository name before remote creation.
2. Confirm Cloudflare Pages as the preferred preview host before connecting a repository.
3. Confirm whether a company contact address should be established before the hosted preview.

These implementation decisions do not block local Milestone 1 repository work. Each remains gated
immediately before its corresponding external action.
