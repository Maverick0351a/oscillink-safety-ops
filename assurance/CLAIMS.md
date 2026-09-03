# Assurance claims

## Scope and status

This assurance set applies only to `SCOPE-ROBOT-CELL-001`: a planned closed-file replay of one
simulated fenced industrial robot cell. The repository now implements strict runtime records,
exact-byte Ed25519 configuration verification, immutable run binding, and pure freshness/order
evaluation. It does not yet implement policy evaluation, latching, persistence, request creation,
or any intervention path. A later output in this scope may only be a local, one-way **simulated
request** to an external safety-controller fixture. It will not be a machine command and will not
establish that motion stopped.

## Controlled claims

### CLM-001 — Bounded safety concept

The artifacts define a preliminary hazard analysis for hazardous robot motion when a person is
present in, enters, or cannot be excluded from a configured protected zone. The twelve hazards
`HAZ-001` through `HAZ-012` cover the mandatory families and trace to planned requirements,
controls, allocations, tests, and evidence records.

**Current status:** the lifecycle concept is documented and Batch 3 contract/configuration/time
boundaries are implemented. Supervisory policy, recovery, output, and target-system behavior remain
unimplemented.

### CLM-002 — Independent decision boundary

The planned deterministic supervisor will treat production-AI intent as untrusted and will compare
it with independently modeled occupancy, motion, source-health, timebase, and configuration
observations. Production AI is not allocated configuration, reset, acknowledgment, evidence
suppression, clock, identity, credential, or policy authority.

**Current status:** the production-input schemas enforce an untrusted-observation-only boundary and
reject administrative fields. Physical independence and common-cause behavior of any target system
remain unvalidated.

### CLM-003 — Conservative simulated response

For a prohibited or unverifiable simulated condition, the planned behavior is to create and latch a
local simulated inhibit or protective-stop request. Missing acknowledgment or unavailable output
must remain an explicit fault; neither a request nor an acknowledgment is evidence of successful
physical stopping.

**Current status:** provenance-bearing decision, request, acknowledgment, and incident record
contracts exist, but no logic creates or delivers a request. Latching and output behavior remain
planned and unimplemented.

### CLM-004 — Recovery separation

The planned state model separates acknowledgment, reset eligibility, reset, rearm, controller
recovery, and a later fresh start. Process restart and production-AI input cannot clear a latch.
Reset never commands motion.

**Current status:** planned and subject to `TEST-009` and `TEST-010` after runtime implementation.

## Claims explicitly not made

This set does not claim machine control, incident prevention, safe operation, compliance,
certification, field effectiveness, a safety-rated component, successful stopping, or approval to
operate. Simulation and planned tests do not validate real sensing, dynamics, communication,
hardware, brakes, drives, controllers, or final elements.

The following remain open and cannot be inferred from this assurance set: PLr, SIL, total stopping
time, diagnostic coverage, application validation, and unresolved common-cause assumptions. Each
is TBD pending qualified target-system assessment using the exact equipment, architecture,
configuration, installation, operating environment, applicable requirements, and validation
evidence.
