# Preliminary safety concept

## Concept boundary

For `SCOPE-ROBOT-CELL-001`, the planned supervisor evaluates closed synthetic observations and may
create a local one-way simulated request to an external safety-controller fixture. It does not
control motion, implement an emergency stop, replace guarding or safety controls, acknowledge its
own output, reset a controller, or establish that a final element acted.

The conservative principle is: a prohibited or unverifiable state cannot become normal merely
because data is missing or a producer reports confidence. A simulated request remains latched until
separate recovery prerequisites and authority events are represented. No state is an `allow`,
`safe`, `certified`, or `approved_to_operate` conclusion.

## Planned controls

### CTRL-001 — Occupancy-motion exclusion

Correlate independent protected-zone occupancy with command and measured motion. Present, entering,
or unknown occupancy during motion produces and latches a simulated protective request. Addresses
`HAZ-001` through `SR-001`.

### CTRL-002 — Restart separation

Require reset eligibility, a separate authorized reset, rearm/recovery evaluation, and a later fresh
start as distinct events. Restoration of power, communications, sensing, or zone-clear state does
not create motion permission. Addresses `HAZ-002` through `SR-002`.

### CTRL-003 — Command/actual correlation

Detect orphan motion and mismatches in expected state, direction, frame, program, sequence, and
bounded correlation time. Ambiguous attribution remains degraded. Addresses `HAZ-003` through
`SR-003`.

### CTRL-004 — Immutable motion envelope

Compare commanded and independently observed motion attributes with immutable reviewed limits and
configuration identity. Out-of-envelope or unverifiable values produce a latched simulated request.
Actual target limits remain TBD. Addresses `HAZ-004` through `SR-004`.

### CTRL-005 — Fail-explicit observation health

Validate required source presence, freshness, sequence, quality, consistency, plausibility, and
configuration/calibration identity. Missing, stale, frozen, malformed, impossible, or contradictory
inputs cannot become monitoring-normal. Addresses `HAZ-005` through `SR-005`.

### CTRL-006 — Independent time/order checks

Use deterministic receive/source timing rules, monotonic sequence expectations, watchdog state, and
explicit clock-health observations. Rollback, jump, future time, reordering, duplication, excessive
skew, or timeout produces degraded/intervention state. Target timing values remain TBD. Addresses
`HAZ-006` through `SR-006`.

### CTRL-007 — Output uncertainty and acknowledgment discipline

Create only a local simulated request bound to decision/configuration identity. A write failure,
corruption, identity mismatch, or missing/stale acknowledgment remains a latched output fault.
Acknowledgment means receipt in the fixture only and never successful stopping. Addresses `HAZ-007`
through `SR-007`.

### CTRL-008 — Configuration identity lock

Load reviewed exact configuration bytes once per run; bind decisions to their identity; reject
unauthorized, malformed, substituted, revoked, partially written, or mid-run changes. Production AI
has no configuration authority. Addresses `HAZ-008` through `SR-008`.

### CTRL-009 — Persistent latch across restart

Recover a latched or uncertain state after process restart. Missing or corrupt persistence cannot
initialize as normal. Restart is recorded separately and never acts as acknowledgment, reset, rearm,
or fresh start. Addresses `HAZ-009` through `SR-009`.

### CTRL-010 — Reset/rearm authority and prerequisites

Reject reset or rearm from production AI and reject it while motion, occupancy, source health,
configuration identity, output state, or authorization prerequisites are unresolved. Reset only
advances recovery state and never commands motion. Addresses `HAZ-010` through `SR-010`.

### CTRL-011 — Production-domain least authority

Treat all production-originated fields as untrusted observations. Reject administration, policy,
threshold, identity, clock, credential, acknowledgment, reset, rearm, evidence-retention, and output
routing authority from that domain. Addresses `HAZ-011` through `SR-011`.

### CTRL-012 — Common-cause visibility

Inventory and fault-inject modeled shared power, network, sensor, time, compute, software/update,
credential, enclosure, and final-element dependencies. A logical diagram is not proof of
independence. Unresolved common cause blocks target-system assurance claims. Addresses `HAZ-012`
through `SR-012`.

## Defense layers and allocation

Every trace path spans `ALLOC-OBS-001`, `ALLOC-LOGIC-001`, `ALLOC-OUTPUT-001`,
`ALLOC-EXTCTRL-001`, and `ALLOC-FINAL-001`. Oscillink owns only the planned deterministic logic and
local simulated request construction. The external controller and final element are represented to
make the complete function boundary visible; they are not implemented, selected, validated, or
controlled here.

## Open integrity targets

PLr, SIL, total stopping time, diagnostic coverage, application validation, and unresolved
common-cause assumptions are all TBD pending qualified target-system assessment. This preliminary
concept supplies no certification or risk-acceptance conclusion.
