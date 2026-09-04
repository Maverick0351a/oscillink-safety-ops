# Assurance claims

## Scope and status

This assurance set applies only to `SCOPE-ROBOT-CELL-001`: a closed-file simulation of one fenced
industrial robot cell. The repository implements strict runtime records, exact-byte Ed25519
configuration verification, immutable run binding, freshness/order evaluation, deterministic
correlation and policy, a persistent intervention/recovery state model, and construction of local
in-memory **simulated requests**, deterministic closed-file replay, and atomic local report
publication. It does not connect to or control machinery, deliver requests to an external
controller, or establish that motion stopped.

## Controlled claims

### CLM-001 — Bounded safety concept

The artifacts define a preliminary hazard analysis for hazardous robot motion when a person is
present in, enters, or cannot be excluded from a configured protected zone. The twelve hazards
`HAZ-001` through `HAZ-012` cover the mandatory families and trace to planned requirements,
controls, allocations, tests, and evidence records.

**Current status:** the lifecycle concept and deterministic closed-record supervisor are implemented
through local simulated-request construction, persisted state, four frozen replay scenarios, a
36-case exact-byte synthetic benchmark, property/fuzz tests, and an abstract finite-state TLC check.
The generated static monitor only displays those benchmark records. Live output transport and
target-system behavior remain unimplemented.

### CLM-002 — Independent decision boundary

The planned deterministic supervisor will treat production-AI intent as untrusted and will compare
it with independently modeled occupancy, motion, source-health, timebase, and configuration
observations. Production AI is not allocated configuration, reset, acknowledgment, evidence
suppression, clock, identity, credential, or policy authority.

**Current status:** production-input schemas enforce an untrusted-observation-only boundary and
reject administrative fields; deterministic correlation and policy use the independently modeled
observations. Physical independence and common-cause behavior of any target system remain
unvalidated.

### CLM-003 — Conservative simulated response

For a prohibited or unverifiable simulated condition, the planned behavior is to create and latch a
local simulated inhibit or protective-stop request. Missing acknowledgment or unavailable output
must remain an explicit fault; neither a request nor an acknowledgment is evidence of successful
physical stopping.

**Current status:** deterministic logic creates and latches a simulated request record, publishes it
only as a content-addressed local artifact with an immutable request-ID binding, handles untrusted
fixture acknowledgments conservatively, and persists exact-byte state. Explicit-time timeout keeps
the request latched and unresolved, including across process restart; a late acknowledgment cannot
resolve that fault. The benchmark and static monitor keep request, acknowledgment, and
`not_established` physical-stop state distinct. No logic delivers a request to an external system or
verifies physical stopping.

### CLM-004 — Recovery separation

The planned state model separates acknowledgment, reset eligibility, reset, rearm, controller
recovery, and a later fresh start. Process restart and production-AI input cannot clear a latch.
Reset never commands motion.

**Current status:** the pure state model separates these stages, denies invalid/replayed recovery
events, preserves latches in content-addressed state, and never creates motion authority. A local
canonical verifier now crosses a fresh operating-system process before each represented recovery
transition. It preserves pending or unresolved output without inferring acknowledgment or stopping,
denies invalid recovery-sequence probes, and fails closed on missing, corrupt, partially published,
stale, conflicting, nonlatched, or identity-mismatched restart state. Stale/conflicting detection
requires a trusted expected state identity supplied outside the persisted candidate. External
authorization, controller recovery, and target-system validation are not implemented.

## Claims explicitly not made

The frozen scenarios, 36-case benchmark, generated demo, Hypothesis properties, fuzz regressions,
and TLA+ result are maintainer-run synthetic software evidence. They do not establish refinement to
the Python implementation or target-system behavior. The demo is an inspection surface only and
adds no runtime, command, reset, rearm, acknowledgment, stop, or control authority.

This set does not claim machine control, incident prevention, safe operation, compliance,
certification, field effectiveness, a safety-rated component, successful stopping, or approval to
operate. Simulation and planned tests do not validate real sensing, dynamics, communication,
hardware, brakes, drives, controllers, or final elements.

The following remain open and cannot be inferred from this assurance set: PLr, SIL, total stopping
time, diagnostic coverage, application validation, and unresolved common-cause assumptions. Each
is TBD pending qualified target-system assessment using the exact equipment, architecture,
configuration, installation, operating environment, applicable requirements, and validation
evidence.
