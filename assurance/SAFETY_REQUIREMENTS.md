# Safety requirements

## Applicability and status

These requirements apply only to `SCOPE-ROBOT-CELL-001`, the closed-file simulated fenced robot-cell
demonstrator. Batches 3 and 4 implement the contract, configuration-authority, provenance,
freshness/order, deterministic correlation/policy, latch/recovery-state, simulated-request
construction, and state-persistence portions identified in the evidence index. “Shall” expresses
the complete requirement; untested scenario dimensions and every target-system behavior remain
planned. Each requirement has one accountable owner, status, change-impact rule, control, test, and
evidence record in `TRACEABILITY.csv`.

### SR-001 — Exclude motion with present or unknown occupancy

The planned supervisor shall create and latch a local simulated protective-stop or inhibit request
when protected-zone occupancy is present, enters during motion, or cannot be determined while motion
is commanded or observed. It shall not emit an affirmative motion-permission or safety verdict.

- Hazard/control: `HAZ-001` / `CTRL-001`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-001`
- Verification/evidence: `TEST-001` / `EVID-001`

### SR-002 — Prevent unexpected simulated restart semantics

Power, communications, source recovery, zone clearance, acknowledgment, reset, or rearm shall not be
interpreted as a fresh start. A fresh-start event shall be separate and shall be considered only
after all recovery prerequisites are represented; no supervisor event commands motion.

- Hazard/control: `HAZ-002` / `CTRL-002`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-002`
- Verification/evidence: `TEST-002` / `EVID-002`

### SR-003 — Detect command/actual mismatch

The planned supervisor shall deterministically detect measured motion without an attributable
command and mismatch in expected state, direction, frame, program, sequence, or bounded correlation
window. Missing or ambiguous attribution shall remain degraded and shall create a latched simulated
request when hazardous motion cannot be excluded.

- Hazard/control: `HAZ-003` / `CTRL-003`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-003`
- Verification/evidence: `TEST-003` / `EVID-003`

### SR-004 — Enforce immutable simulated motion envelope

The planned supervisor shall compare represented command and independent motion observations against
immutable reviewed limits for the exact configuration. Out-of-range speed, acceleration, travel,
direction, workspace, force/torque proxy, or an unverifiable value shall create and latch a local
simulated request. The actual limits are not selected by this requirement.

- Hazard/control: `HAZ-004` / `CTRL-004`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-004`
- Verification/evidence: `TEST-004` / `EVID-004`

### SR-005 — Fail explicitly on unavailable or contradictory sensing

Every required occupancy, motion, health, and configuration observation shall have valid identity,
sequence, quality, freshness, and configuration/calibration association. Missing, stale, frozen,
malformed, impossible, unsupported, or contradictory observations shall not produce
monitoring-normal and shall create a simulated request whenever hazardous motion cannot be excluded.

- Hazard/control: `HAZ-005` / `CTRL-005`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-005`
- Verification/evidence: `TEST-005` / `EVID-005`

### SR-006 — Detect timebase and ordering failure

The planned supervisor shall detect source/receive-time rollback, future time, excessive skew,
duplicate or reordered sequence, sequence gap, watchdog expiry, and clock-health loss according to
immutable configuration. Such conditions shall remain explicit and cannot be normalized into a
current observation.

- Hazard/control: `HAZ-006` / `CTRL-006`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-006`
- Verification/evidence: `TEST-006` / `EVID-006`

### SR-007 — Preserve output-path uncertainty

A planned action request shall be one-way, local, simulated, and bound to the exact decision and
configuration identity. Failure to create or preserve it, identity mismatch, corruption, duplicate
handling ambiguity, or missing/stale fixture acknowledgment shall keep the intervention latched and
record output state as unresolved. Neither request nor acknowledgment shall be reported as successful
physical stopping.

- Hazard/control: `HAZ-007` / `CTRL-007`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-007`
- Verification/evidence: `TEST-007` / `EVID-007`

### SR-008 — Lock configuration identity for a run

The planned supervisor shall load exact reviewed configuration bytes once for a run and bind every
decision to that identity. It shall reject malformed, unauthorized, revoked, substituted, partially
written, identity-reused, rolled-back, or mid-run configuration changes. Production input cannot
select or alter configuration.

- Hazard/control: `HAZ-008` / `CTRL-008`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-008`
- Verification/evidence: `TEST-008` / `EVID-008`

### SR-009 — Retain latch across process restart

The planned supervisor shall persist and recover intervention state across simulated process restart.
A prior latch, missing state, or corrupt state shall not initialize as monitoring-normal. Restart
shall be a distinct recorded event and shall not acknowledge, reset, rearm, recover, or start motion.

- Hazard/control: `HAZ-009` / `CTRL-009`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-009`
- Verification/evidence: `TEST-009` / `EVID-009`

### SR-010 — Gate reset and rearm

The planned supervisor shall reject reset/rearm from production AI and while represented motion,
occupancy, required-source health, configuration identity, output state, or authorized-review
prerequisites are unresolved. Acknowledgment, reset, rearm, recovery, and fresh start shall remain
distinct. Reset shall never command motion.

- Hazard/control: `HAZ-010` / `CTRL-010`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-010`
- Verification/evidence: `TEST-010` / `EVID-010`

### SR-011 — Deny production-AI administrative authority

The planned supervisor shall treat production-AI content only as untrusted observation. It shall
reject producer-originated policy, threshold, source identity, calibration, timebase, watchdog,
credential, output route, acknowledgment, reset, rearm, evidence deletion/suppression, and disable
fields or commands.

- Hazard/control: `HAZ-011` / `CTRL-011`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-011`
- Verification/evidence: `TEST-011` / `EVID-011`

### SR-012 — Expose unresolved common cause

The lifecycle and planned runtime evidence shall identify represented shared power, network, sensor,
time, compute, software/update, credential, enclosure, communication, and final-element dependencies.
Injected shared-dependency failure shall not be reported as independent-path success. Unassessed
common cause shall block any target-system integrity, certification, or deployment claim.

- Hazard/control: `HAZ-012` / `CTRL-012`
- Owner/status/change impact: `ROLE-SAFETY-OWNER`; planned; `CI-012`
- Verification/evidence: `TEST-012` / `EVID-012`

## Target-system values intentionally unresolved

PLr: TBD — qualified target-system assessment

SIL: TBD — qualified target-system assessment

Total stopping time: TBD — qualified target-system assessment

Diagnostic coverage: TBD — qualified target-system assessment

Application validation: TBD — qualified target-system assessment

Unresolved common-cause assumptions: TBD — qualified target-system assessment

These values require the exact target equipment, hazard/risk assessment, operating modes,
architecture, sensors, logic, communications, diagnostics, controller, drive/brake/final element,
environment, installation, maintenance, cybersecurity, and independent validation evidence. They
cannot be derived from this simulated request design, public standards summaries, or software test
results.
