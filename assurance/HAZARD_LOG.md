# Preliminary hazard log

## Scope and method

This preliminary log covers `SCOPE-ROBOT-CELL-001`, a planned closed-file simulation of hazardous
robot motion while a person is present in, enters, or cannot be excluded from a protected zone.
Severity and probability classes are intentionally not assigned: target equipment, payload, speed,
exposure, avoidance, safeguards, and jurisdiction have not been selected. Every entry is `planned`
and requires qualified target-system assessment before any deployment interpretation.

## HAZ-001 — Human present in or entering protected zone

Hazard family: `human-zone-entry`

- **Scenario:** robot motion is commanded or observed while a person is present, enters, or cannot be
  excluded from the configured zone.
- **Potential harm:** impact, crushing, trapping, cutting, or other application-specific injury.
- **Initiators:** entry during motion, occlusion, incomplete enclosure model, or occupancy unknown.
- **Planned control:** `CTRL-001`; requirement `SR-001`; verification `TEST-001` / `EVID-001`.
- **Open conditions:** zone geometry, detection capability, uncertainty, response and stopping
  performance, and residual risk are target-specific.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-001`.

## HAZ-002 — Unexpected or automatic start

Hazard family: `unexpected-start`

- **Scenario:** motion begins after reset, zone clearance, power/network restoration, mode transfer,
  or controller recovery without a distinct authorized fresh-start event.
- **Potential harm:** a person relying on stopped state is exposed to hazardous motion.
- **Initiators:** conflated acknowledgment/reset/start, stale start request, or automatic recovery.
- **Planned control:** `CTRL-002`; requirement `SR-002`; verification `TEST-002` / `EVID-002`.
- **Open conditions:** local restart controls and target controller semantics are outside this scope.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-002`.

## HAZ-003 — Commanded and actual behavior disagree

Hazard family: `command-actual-mismatch`

- **Scenario:** measured motion occurs without a matching command or differs in state, direction,
  program, frame, sequence, or expected effect.
- **Potential harm:** unanticipated motion exposes a person or exceeds the reviewed envelope.
- **Initiators:** controller fault, wrong frame, unexpected subprogram, attribution ambiguity, or
  corrupted command observation.
- **Planned control:** `CTRL-003`; requirement `SR-003`; verification `TEST-003` / `EVID-003`.
- **Open conditions:** correlation window and measurement accuracy remain target-specific.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-003`.

## HAZ-004 — Excessive motion

Hazard family: `excessive-motion`

- **Scenario:** observed or commanded speed, acceleration, travel, force/torque proxy, direction, or
  workspace extent exceeds the immutable simulated envelope.
- **Potential harm:** increased impact energy, reach into occupied space, crushing, or mechanical
  damage.
- **Initiators:** wrong parameters, learning-policy drift, program substitution, unit/frame error, or
  sensor fault.
- **Planned control:** `CTRL-004`; requirement `SR-004`; verification `TEST-004` / `EVID-004`.
- **Open conditions:** numerical limits, PLr/SIL, and stopping-time budget are not selected here.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-004`.

## HAZ-005 — Sensing unavailable or contradictory

Hazard family: `stale-missing-contradictory-sensing`

- **Scenario:** required occupancy, motion, health, or configuration observations are absent, stale,
  frozen, malformed, impossible, or contradictory.
- **Potential harm:** hazardous motion is treated as acceptable because uncertainty is hidden.
- **Initiators:** dropout, occlusion, dirty sensor, replay, stuck value, sequence gap, or disagreement.
- **Planned control:** `CTRL-005`; requirement `SR-005`; verification `TEST-005` / `EVID-005`.
- **Open conditions:** required sensors, diagnostics, diagnostic coverage, and degraded response are
  TBD for the target system.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-005`.

## HAZ-006 — Timebase or ordering failure

Hazard family: `timebase-failure`

- **Scenario:** clock rollback/jump, excessive skew, future timestamp, duplicate sequence, reordering,
  or watchdog failure makes observations temporally unverifiable.
- **Potential harm:** old occupancy or motion state is correlated with a new command.
- **Initiators:** time synchronization loss, replay, reboot, scheduler delay, or source defect.
- **Planned control:** `CTRL-006`; requirement `SR-006`; verification `TEST-006` / `EVID-006`.
- **Open conditions:** clock architecture, freshness thresholds, and worst-case latency are TBD.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-006`.

## HAZ-007 — Simulated output path fails

Hazard family: `output-path-failure`

- **Scenario:** a required local simulated request cannot be created, is corrupted, duplicated,
  misrouted, or remains unacknowledged by the external-controller fixture.
- **Potential harm:** an evaluator incorrectly assumes a protective response occurred.
- **Initiators:** serialization/write failure, stale acknowledgment, identity mismatch, or timeout.
- **Planned control:** `CTRL-007`; requirement `SR-007`; verification `TEST-007` / `EVID-007`.
- **Open conditions:** real communication, controller, drive, brake, final element, and total stopping
  time are outside this scope and unvalidated.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-007`.

## HAZ-008 — Configuration corruption or substitution

Hazard family: `configuration-corruption`

- **Scenario:** configuration bytes, identity, zone, threshold, transform, source registry, policy, or
  reset rule changes without authorized review or changes during a run.
- **Potential harm:** detection is weakened or evidence is evaluated against the wrong envelope.
- **Initiators:** partial write, rollback, tampering, mistaken deployment, or identity reuse.
- **Planned control:** `CTRL-008`; requirement `SR-008`; verification `TEST-008` / `EVID-008`.
- **Open conditions:** signer authority, storage, key management, and target commissioning are TBD.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-008`.

## HAZ-009 — Process restart clears or loses safety state

Hazard family: `process-restart`

- **Scenario:** supervisor, host, controller fixture, or replay process restarts while a request is
  latched and resumes normal evaluation without recovering prior state.
- **Potential harm:** a persisting simulated hazard is concealed and recovery appears complete.
- **Initiators:** crash, power cycle, deployment, state corruption, or deletion.
- **Planned control:** `CTRL-009`; requirement `SR-009`; verification `TEST-009` / `EVID-009`.
- **Open conditions:** persistence medium and target restart coordination are unvalidated.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-009`.

## HAZ-010 — Reset or rearm is misused

Hazard family: `reset-rearm-misuse`

- **Scenario:** reset/rearm is accepted while occupied, moving, degraded, changed, or unauthorized;
  acknowledgment is treated as reset; reset is treated as a start.
- **Potential harm:** hazardous motion can resume while prerequisites remain unresolved.
- **Initiators:** remote request, production pressure, repeated reset, role confusion, or bad state
  transition.
- **Planned control:** `CTRL-010`; requirement `SR-010`; verification `TEST-010` / `EVID-010`.
- **Open conditions:** target local authorization and application recovery procedure are TBD.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-010`.

## HAZ-011 — Production AI is compromised or exceeds authority

Hazard family: `production-ai-compromise`

- **Scenario:** production AI spoofs observations or attempts to disable monitoring, raise limits,
  update policy, change clock/identity, reset, acknowledge, rearm, or suppress evidence.
- **Potential harm:** a common attacker or faulty producer defeats the planned independent monitor.
- **Initiators:** malicious input, prompt/tool misuse, compromised credentials, or integration defect.
- **Planned control:** `CTRL-011`; requirement `SR-011`; verification `TEST-011` / `EVID-011`.
- **Open conditions:** target threat model, separation, identity, and credential controls are TBD.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-011`.

## HAZ-012 — Shared dependency defeats independent paths

Hazard family: `shared-power-network-sensor-common-cause`

- **Scenario:** shared power, network, sensor, clock, compute, software/update path, credentials,
  enclosure, or final element causes production and supervisory paths to fail together.
- **Potential harm:** apparent independence provides no effective fault separation.
- **Initiators:** brownout, network partition, shared perception corruption, supply-chain defect,
  environmental event, or common administrative compromise.
- **Planned control:** `CTRL-012`; requirement `SR-012`; verification `TEST-012` / `EVID-012`.
- **Open conditions:** every common-cause assumption is unresolved and explicitly TBD for qualified
  target-system assessment.
- **Owner/status/change impact:** `ROLE-SAFETY-OWNER`; planned; `CI-012`.

## Residual-risk statement

This log does not determine risk reduction, required performance, tolerable residual risk, or
acceptability. PLr, SIL, total stopping time, diagnostic coverage, application validation, and all
unresolved common-cause assumptions remain TBD pending qualified assessment of the exact target
system.
