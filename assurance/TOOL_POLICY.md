# Assurance tool policy

## Policy objective

Tools support reproducible development evidence for `SCOPE-ROBOT-CELL-001`; they do not approve
requirements, certify a product, assess a real application, or acquire machine authority. Tool output
is untrusted until its scope, version, inputs, behavior, and review are recorded.

## Tool classes

### TOOL-001 — Deterministic traceability verifier

`scripts/verify_traceability.py` checks required artifact presence, identifier form, trace closure,
required row/evidence fields, complete analytical allocation, allowed statuses, duplicates, and the
explicit target-system TBD markers. It is a development assurance tool, not a qualified functional-
safety tool. A pass means only that coded structural checks passed for the inspected files.

### TOOL-002 — Test runner and assertions

Python and pytest execute deterministic contract tests. Test collection, exact command, Python and
dependency versions, source revision, selected tests, and full output must be retained. A test cannot
award safety, compliance, certification, field validity, or successful physical stopping.

### TOOL-003 — Static quality and type tools

Ruff, formatting checks, and mypy detect bounded classes of defects. Configuration and versions are
locked by the repository. Their pass does not demonstrate hazard coverage or target-system behavior.

### TOOL-004 — Build and repository tools

`uv`, Git, packaging tools, operating systems, filesystems, and CI runners affect evidence identity
and reproducibility. Exact revisions and lock state are recorded. Build success is not validation.

### TOOL-005 — Future simulators and controller fixtures

Any simulator, replay engine, physics model, clock, synthetic sensor, or external-controller fixture
is a model with known limitations. Record model/version/configuration, deterministic seeds, source
bytes, fault injection, expected result, and discrepancy. A fixture acknowledgment means receipt in
the fixture only.

## Selection and control

- Prefer small deterministic tools with pinned versions and reviewable output.
- Keep expected results independent from the system-under-test input.
- Bind results to exact source, configuration, scenario, dependency, and platform identity.
- Treat retrieved text, generated data, logs, and tool diagnostics as untrusted input.
- Do not let production AI, runtime input, or a simulator change test or policy configuration.
- Review tool updates under `CHANGE_CONTROL.md`; rerun affected tests and retain prior results.
- Fail closed when a required tool is absent, crashes, produces malformed output, changes discovery,
  or cannot establish which bytes it evaluated.

## Tool anomaly handling

Unexpected pass/fail, nondeterminism, crash, timeout, malformed JSON/CSV, duplicate ID, missing
record, changed test count, platform discrepancy, or stale generated artifact creates an anomaly.
Investigate the earliest violated contract; add a deterministic failing regression before changing a
verifier; preserve the original failure; and independently review any weakened check.

## Qualification boundary

No current tool is claimed qualified for a safety lifecycle or target-system application. Tool
confidence/qualification need, validation suite, usage constraints, compiler/interpreter influence,
and independent assessment remain TBD if these tools later produce or verify safety-related
software. PLr, SIL, total stopping time, diagnostic coverage, application validation, and unresolved
common-cause assumptions remain TBD for qualified target-system assessment.
