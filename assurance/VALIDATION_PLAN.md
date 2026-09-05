# Validation plan

## Status and interpretation

All tests below apply to `SCOPE-ROBOT-CELL-001`. Batches 3 through 6 implement adversarial unit and
property-test portions of `TEST-001` through `TEST-011` for runtime contracts, configuration,
provenance, freshness/order, correlation, policy, latch/recovery state, in-memory simulated-request
creation, state persistence, deterministic replay, local report publication, and abstract TLA+
invariants. Four frozen synthetic replay cases cover nominal, zone-entry, stale-source, and
contradictory-source behavior. A separate generated 36-case exact-byte synthetic benchmark expands
represented boundary, integrity, authority, persistence, simultaneous-fault, and staged-recovery
cases. Its generated static monitor is display-only. Live request delivery, output timeouts, hardware
response, and common-cause campaigns remain planned. A passing result demonstrates only software
behavior for the exact tested bytes, configuration, inputs, and platform. It does not validate a real
robot cell or prove stopping, risk reduction, compliance, or certification.

## Common evidence protocol

For each test retain exact source revision, locked dependencies, platform, test command, collected
test identity, configuration/scenario bytes and SHA-256, initial persisted state, ordered inputs,
expected output bytes, actual output bytes, state transitions, first-out reason, duration, and full
pass/fail diagnostics. Failure is retained and never overwritten. `EVID-001` through `EVID-012`
index the complete planned specifications; `EVID-013` onward index implemented maintainer-run
software evidence.

## Batch 6 synthetic benchmark and demo evidence

`EVID-025` binds 36 canonical case inputs to 36 exact expected-result records, mechanically derived
metrics, generated schemas and field guide, exact source/configuration/runtime identities, and three
byte-identical executions per case. It exercises implemented portions of `TEST-001` through
`TEST-011`; it does not complete those application-level tests or exercise `TEST-012` common-cause
campaigns. It intentionally reports no wall-clock latency.

`EVID-026` binds the dependency-free static monitor to every expected result and metric. Verification
checks semantic landmarks, accessible selection, required boundary copy, local-only resources,
generated-byte repeatability, and absence of command/form/network/dynamic-HTML surfaces. Display
correctness is not a safety function and does not establish request delivery, acknowledgment truth,
or physical stopping.

### TEST-001 — Occupied/unknown zone during motion

- **Implemented portion:** present, entering, and unknown occupancy with commanded or measured
  motion produce deterministic conservative policy and a latched in-memory simulated request in
  `tests/runtime/test_correlator.py`, `test_policy.py`, and `test_supervisor.py`. The frozen
  `zone-entry` replay exercises this path end to end through canonical report generation.

- **Requirement:** `SR-001`; hazard/control: `HAZ-001` / `CTRL-001`.
- **Stimuli:** commanded motion with occupied zone; entry during measured motion; unknown occupancy;
  zone clear control case.
- **Planned oracle:** each occupied/entry/unknown case creates and latches a local simulated request;
  clear nominal input creates no positive safety verdict. Verify `EVID-001`.

### TEST-002 — No unexpected start after recovery events

- **Implemented portion:** acknowledgment, reset, rearm, recovery confirmation, and fresh start are
  distinct pure state transitions; only the final explicit fresh-start event clears the simulated
  latch to `initializing`, and every recovery action is `none`.

- **Requirement:** `SR-002`; hazard/control: `HAZ-002` / `CTRL-002`.
- **Stimuli:** acknowledgment, reset, rearm, zone clear, source restoration, communications recovery,
  power/restart epoch, and stale pre-stop start event in every relevant order.
- **Planned oracle:** none is interpreted as a fresh start; a later separately authorized start event
  is represented distinctly and does not command motion. Verify `EVID-002`.

### TEST-003 — Command/actual mismatch matrix

- **Implemented portion:** orphan motion, commanded/measured state mismatch, contradictory command
  observations, and direction/frame/program attribution are explicit and fail closed. Missing,
  ambiguous, contradictory, or cross-source mismatched attributes produce stable reason codes;
  conflicting physical calibration identities are also explicit. Physical motion attribution now
  binds command identity and sequence together and checks response chronology against an immutable
  signed maximum delay. Missing, mismatched, non-motion, ambiguous, early, and late attribution fail
  closed. A bounded persistent command ledger carries exact command identity across evaluations and
  process restart, records consumed attributions, rejects identity reuse, and fails closed at
  capacity. No represented attribute establishes physical independence or measurement accuracy.

- **Requirement:** `SR-003`; hazard/control: `HAZ-003` / `CTRL-003`.
- **Stimuli:** orphan motion, wrong direction/frame/program/state, missing expected response,
  late response, and ambiguous multiple-command attribution.
- **Planned oracle:** every mismatch remains explicit and the hazardous/unverifiable cases latch a
  local simulated request with deterministic first-out reason. Verify `EVID-003`.

### TEST-004 — Excessive motion boundary cases

- **Implemented portion:** exact synthetic speed and acceleration boundaries, unavailable
  acceleration during represented motion, strict numeric contracts, and non-finite rejection are
  covered. Travel, direction, workspace, and force/torque proxies remain planned.

- **Requirement:** `SR-004`; hazard/control: `HAZ-004` / `CTRL-004`.
- **Stimuli:** values below, exactly at, and above each configured synthetic speed, acceleration,
  travel, direction, workspace, and force/torque-proxy boundary; wrong units/frame; non-finite input.
- **Planned oracle:** configured boundary semantics are exact; out-of-range or invalid values latch a
  request; input cannot change the limit. This does not set a real limit. Verify `EVID-004`.

### TEST-005 — Missing/stale/frozen/malformed/contradictory sensing

- **Implemented portion:** freshness/source-state rejection plus deterministic fail-closed policy,
  contributing reasons, latch outcomes, hostile replay parsing, and frozen stale/contradictory
  source reports are covered in the runtime tests and corpus. Physical calibration hashes must now
  appear in the exact signed configuration's sorted approval set; cross-source conflicts and
  unapproved identities remain explicit.

- **Requirement:** `SR-005`; hazard/control: `HAZ-005` / `CTRL-005`.
- **Stimuli:** remove each required source; freeze a value; exceed freshness; inject sequence gap,
  impossible transition, malformed record, contradictory occupancy, and calibration/config mismatch.
- **Planned oracle:** no case silently enters monitoring-normal; hazardous or unknown motion state
  latches a simulated request and preserves contributing conditions. Verify `EVID-005`.

### TEST-006 — Timebase and order faults

- **Implemented portion:** explicit-time future/rollback/freshness and sequence rejection cases
  implemented in `tests/runtime/test_freshness.py`; watchdog/restart behavior remains planned.

- **Requirement:** `SR-006`; hazard/control: `HAZ-006` / `CTRL-006`.
- **Stimuli:** source/receive clock rollback and jump, future timestamp, skew at/either side of the
  configured boundary, duplicate/reordered sequence, gap, watchdog expiry, and restart epoch.
- **Planned oracle:** deterministic explicit fault at the defined boundary; stale data is never
  correlated as current. Target timing adequacy is not assessed. Verify `EVID-006`.

### TEST-007 — Output request and acknowledgment faults

- **Implemented portion:** provenance-bearing non-authoritative output contracts, in-memory request
  creation, latch recording, and false/replayed fixture-acknowledgment handling are covered. Local
  simulated request artifacts are atomically published under exact content addresses with immutable
  request-ID bindings, bounded exact-byte reload, canonical-form validation, and collision rejection.
  Explicit-time timeout transitions preserve the request and latch, mark output unresolved at the
  deadline, reject time rollback/non-finite durations, and prevent late acknowledgment from resolving
  the timeout. Cross-process replay verifies the timed-out state. Live delivery remains unimplemented.

- **Requirement:** `SR-007`; hazard/control: `HAZ-007` / `CTRL-007`.
- **Stimuli:** local write failure, partial/corrupt request, reused identity with changed bytes,
  duplicate delivery, wrong/stale/false acknowledgment, timeout, and recovery.
- **Planned oracle:** intervention remains latched and output state unresolved; no result reports
  successful physical stop. Assert no live address, credential, protocol writer, or callback exists.
  Verify `EVID-007`.

### TEST-008 — Configuration integrity

- **Implemented portion:** exact-byte loading, Ed25519 verification, authority/revision/ceiling checks,
  path confinement, and immutable run binding implemented in `tests/runtime/test_configuration.py`.
  Mid-run substitution also produces deterministic fail-closed policy and a latch. Replay tests
  reject forged, changed, expired, wrong-scope, and source-role-substituted artifacts.

- **Requirement:** `SR-008`; hazard/control: `HAZ-008` / `CTRL-008`.
- **Stimuli:** changed bytes under reused identity, unauthorized/revoked signer, rollback, path escape,
  special/symlink input, partial write, collision, threshold widening, and mid-run substitution.
- **Planned oracle:** reject before normal evaluation or latch on detected mid-run change; bind every
  decision to one exact configuration identity. Verify `EVID-008`.

### TEST-009 — Restart persistence

- **Implemented portion:** canonical state bytes are content-addressed, root-confined, atomically
  published, exact-byte verified, and reloaded with latches preserved. A canonical process-level
  replay crosses a fresh operating-system process before acknowledgment, reset readiness, reset,
  rearm, recovery confirmation, and fresh start. Separate process cases preserve pending and
  unresolved output without inferring acknowledgment, stopping, or reset readiness. Missing,
  corrupt, partially published, stale, conflicting, nonlatched, run-mismatched, or
  trusted-state-ID-mismatched restart inputs fail closed. Process probes also deny sequence bypass
  after interrupted reset-not-permitted, rearm-pending, recovery-pending, and recovery-confirmed
  states. Exhaustive invalid-event permutations remain planned.

- **Requirement:** `SR-009`; hazard/control: `HAZ-009` / `CTRL-009`.
- **Stimuli:** restart from every latch/recovery state; missing, truncated, corrupt, stale, and
  conflicting persistence; restart during output uncertainty.
- **Planned oracle:** prior latch or uncertainty never initializes as normal; restart is recorded and
  cannot acknowledge/reset/rearm/start. Verify `EVID-009`.

### TEST-010 — Reset and rearm misuse

- **Implemented portion:** pure transitions deny production-AI authority, invalid stage, unresolved
  prerequisites, and replayed/future events; acknowledgment/reset/rearm/recovery/fresh start remain
  distinct and never command motion. Invalid reset after recovery confirmation returns a valid
  conservative state rather than carrying a fresh-start flag into an incompatible state.
  Deterministic Hypothesis cases, cross-process interruption probes, and the abstract TLA+ model
  check latch/recovery invariants. External authorization is represented, not implemented.

- **Requirement:** `SR-010`; hazard/control: `HAZ-010` / `CTRL-010`.
- **Stimuli:** reset/rearm from production AI, while occupied, moving, degraded, configuration-changed,
  output-unresolved, unauthorized, repeatedly requested, or supplied as acknowledgment.
- **Planned oracle:** every invalid transition is rejected with stable reason; valid reset only
  advances recovery and never commands motion. Verify `EVID-010`.

### TEST-011 — Production-AI compromise and authority probes

- **Implemented portion:** strict observation contracts reject producer-supplied administrative
  fields and fix no configuration/reset/output/evidence-suppression authority; runtime policy never
  consumes production data as configuration or recovery authority. A deterministic campaign now
  exercises privileged-field smuggling, authority escalation, forged fixture acknowledgment,
  production recovery, configuration/calibration substitution, command reuse/history exhaustion,
  evidence mutation surfaces, and all six modeled benchmark authority attempts. Every modeled
  attempt is rejected or fails closed without granting authority or establishing physical stopping.

- **Requirement:** `SR-011`; hazard/control: `HAZ-011` / `CTRL-011`.
- **Stimuli:** inject disable, policy, threshold, identity, clock, watchdog, credential, output-route,
  acknowledgment, reset, rearm, evidence-delete, and suppression fields plus spoofed observations.
- **Planned oracle:** administrative fields are rejected; spoofed content cannot grant authority;
  independently represented physical uncertainty remains conservative. Verify `EVID-011`.

### TEST-012 — Shared-dependency/common-cause campaign

- **Implemented portion:** signed dependency bindings identify represented shared power, network,
  sensor, clock, compute, software/update, credential, enclosure/environment, communications, and
  final-element dependencies. Exact dependency observations remain untrusted and explicitly state
  that independence is not established. Missing, ambiguous, unconfigured, configuration-mismatched,
  degraded, failed, or contradictory dependencies fail closed; a healthy affected-source claim
  during shared-dependency failure is reported as a contradiction. A canonical ten-family campaign
  and an end-to-end supervisor case are implemented.

- **Requirement:** `SR-012`; hazard/control: `HAZ-012` / `CTRL-012`.
- **Stimuli:** model loss/corruption of shared power, network, sensor, clock, compute, software/update,
  credentials, enclosure/environment, communications, controller fixture, and final-element status.
- **Planned oracle:** represented common failure is reported as unresolved/degraded rather than
  independent success. Document residual and unmodeled dependencies. Verify `EVID-012`.

## Application validation and target values

Application validation is not performed by this plan. A qualified target-system program must add
requirements and evidence for exact equipment and hazards, sensor coverage and diagnostics,
controller/final elements, communication, environmental limits, worst-case response and stopping,
installation, foreseeable misuse, maintenance/proof testing, cybersecurity, common cause, and
residual risk.

PLr, SIL, total stopping time, diagnostic coverage, application validation, and unresolved
common-cause assumptions remain TBD pending that qualified assessment.
