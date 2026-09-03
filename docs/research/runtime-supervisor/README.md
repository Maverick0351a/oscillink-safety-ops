# Runtime-supervisor research corpus

This directory preserves the dated research used to choose the independent safety and
risk-mitigation supervisor direction. Research findings inform architecture, hazards, tests, and
market hypotheses; they are not implementation evidence, field validation, legal advice, a safety
assessment, or certification.

## Reports

| Report | Scope | Citation evidence |
|---|---|---|
| [Standards path](standards-path-2026-09-02.md) | Machinery, robot, functional-safety, electrical, cybersecurity, and conformity path | Inline numbered sources and short public catalogue/official-source quotations; no machine-readable ledger was produced |
| [Hazards and incidents](hazards-incidents-2026-09-02.md) | Conventional automation incidents, AI/autonomy evidence, independence, restart, and fault-test implications | Inline numbered sources and quotations; no machine-readable ledger was produced |
| [Community voice](community-voice-2026-09-02.md) | Practitioner anecdotes about diagnosis, reset/recovery, bypass pressure, and safety/standard-layer separation | [Evidence ledger](citations/community-voice-ledger.json) with one or more verbatim quotations for every source |
| [Competitor map](competitor-map-2026-09-02.md) | Certified safety incumbents, runtime assurance, V&V, and architecture-level competitors | [Evidence ledger](citations/competitor-map-ledger.json) with one or more verbatim quotations for every source |
| [Public demo strategy](public-demo-strategy-2026-09-02.md) | Open-source maturity, benchmark, simulation, release, and public-proof strategy | [Citation-mapping ledger](citations/public-demo-strategy-ledger.json); this ledger maps citations but contains no stored evidence quotations |

## Evidence labels and limits

The reports retain their own evidence labels, including official source, vendor claim,
certificate/declaration, live product, paper, preprint, practitioner anecdote, and inference. A vendor
or author claim is not converted into an independently verified outcome. Community reports are
qualitative and selection-biased. Public standards catalogue text is not a substitute for controlled,
licensed normative requirements.

No licensed standards text is included. The standards report uses only short quotations from public
catalogue or official pages and explicitly identifies normative material that was not reproduced.
No customer documents, facility data, employee records, credentials, private prompts, hidden
expected answers, or protected evaluation labels belong in this corpus.

## Product interpretation

The repository currently implements the governed evidence and offline-evaluation plane only. The
runtime supervisor, command/state correlation, intervention latch, robot-cell replay, and local
simulated protective requests remain planned. Research recommendations that discuss eventual
hardware, certification, or field integration do not describe current Oscillink capability or
operational authority.

All proposed public scenarios and results are synthetic or simulated until explicitly proven
otherwise. They must not be presented as field results, incident-prevention evidence, an achieved
Performance Level or Safety Integrity Level, or validation of a real safety function.

## Citation verification

The citation ledgers use the grounded-citations ledger format. Run the citation-mapping gate for all
three ledger-backed reports. Add `--evidence` only to the community and competitor reports, whose
ledgers contain verbatim evidence quotations. The public-demo ledger supports citation mapping but not
the evidence-quote gate.

Repository-surface tests additionally verify that each report cites exactly the source IDs and URLs
recorded in its associated ledger.
