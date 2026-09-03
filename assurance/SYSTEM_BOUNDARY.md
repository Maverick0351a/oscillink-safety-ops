# System boundary

## Item under consideration

`SCOPE-ROBOT-CELL-001` is the assurance scope for a deterministic supervisor evaluated with closed
records representing one simulated fenced robot cell. The implemented runtime validates and
correlates records, evaluates deterministic policy, maintains persistent latch/recovery state, and
constructs an in-memory simulated request record. Deterministic replay may publish a verified local
report file. A generated dependency-free static monitor may display all 36 exact expected benchmark
results for scenario selection and evidence inspection. No machine interface or live request
transport is in scope.

## Logical flow

```text
UNTRUSTED PRODUCTION DOMAIN
  recorded production-AI intent (read-only observation)
                         |
INDEPENDENT OBSERVATION DOMAIN
  simulated occupancy, motion, source health, timebase and configuration identity
                         |
                         v
OSCILLINK DETERMINISTIC LOGIC (implemented for closed records)
  validate -> align -> correlate -> evaluate -> latch -> record
                         |
                         v
LOCAL ONE-WAY OUTPUT BOUNDARY
  canonical local replay report or in-memory simulated request only
                         |
                         v
EXTERNAL SAFETY DOMAIN (represented, not implemented or validated)
  external safety controller -> drive/brake/final element
```

## Inside the Oscillink scope

- exact replay input identity and provenance;
- deterministic validation, freshness, ordering, correlation, and policy evaluation;
- a persistent simulated intervention latch and recovery-state record;
- in-memory construction of a one-way local simulated request record;
- deterministic signed-configuration replay and atomic local report publication;
- frozen synthetic scenarios, property/fuzz regressions, and abstract TLA+ model evidence;
- a 36-case exact-byte synthetic benchmark and generated static read-only inspection demo;
- visibility of acknowledgment absence, output-path faults, restart, and recovery state; and
- configuration control, traceability, planned verification, and change impact.

## Outside the Oscillink scope

- real sensors, scanners, guards, interlocks, safety PLCs, robot controllers, drives, brakes,
  emergency-stop devices, and final elements;
- transport to a live controller, equipment credentials, controller addresses, ROS publishers,
  fieldbus writers, reverse control callbacks, and remote reset;
- UI commands, form submission, reset, rearm, acknowledgment, stop, control, external resources, or
  browser network clients in the static demo;
- selection or calculation of PLr, PL, SIL, PFH, category, architecture, diagnostic coverage,
  common-cause score, proof-test interval, or stopping distance/time;
- application risk assessment, electrical or mechanical integration, commissioning, validation,
  conformity assessment, certification, and operating authorization; and
- work permits, lockout/tagout authority, legal conclusions, and personnel authorization.

## Trust and authority boundaries

Production-AI records are untrusted observations. They cannot select policy, alter limits, change
source identities, provide reset authority, acknowledge the simulated request, or suppress evidence.
The governance plane controls reviewed configuration and evidence but cannot command physical or
simulated motion. Implemented outputs are an in-memory simulated request record and a canonical local
report file only; the external safety controller and final element remain solely responsible for any
physical response in a future target system.

A controller acknowledgment, if represented in simulation, means only that a fixture reported
receipt. It does not prove that a controller is safety-rated, that a final element acted, or that a
machine stopped.

## Open target-system assumptions

Independence is not established merely by drawing separate boxes. Shared power, network, sensor,
time, compute, software supply chain, credentials, update channel, enclosure, communications, or
final element may defeat both production and supervisory paths. These common-cause assumptions,
along with PLr, SIL, total stopping time, diagnostic coverage, and application validation, remain
TBD for qualified assessment of the exact target system.
