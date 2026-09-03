# System boundary

## Item under consideration

`SCOPE-ROBOT-CELL-001` is the assurance scope for a planned deterministic supervisor evaluated with
closed files representing one simulated fenced robot cell. This batch creates assurance documents
only. A later runtime batch may consume replay records and write a local simulated request artifact;
no machine interface is in scope.

## Logical flow

```text
UNTRUSTED PRODUCTION DOMAIN
  recorded production-AI intent (read-only observation)
                         |
INDEPENDENT OBSERVATION DOMAIN
  simulated occupancy, motion, source health, timebase and configuration identity
                         |
                         v
OSCILLINK DETERMINISTIC LOGIC (planned, not implemented in this batch)
  validate -> align -> correlate -> evaluate -> latch -> record
                         |
                         v
LOCAL ONE-WAY OUTPUT BOUNDARY
  simulated request file or in-memory fixture only
                         |
                         v
EXTERNAL SAFETY DOMAIN (represented, not implemented or validated)
  external safety controller -> drive/brake/final element
```

## Inside the Oscillink scope

- exact replay input identity and provenance;
- deterministic validation, freshness, ordering, correlation, and policy evaluation as later
  requirements;
- a persistent simulated intervention latch and causal incident record as later requirements;
- construction of a one-way local simulated request;
- visibility of acknowledgment absence, output-path faults, restart, and recovery state; and
- configuration control, traceability, planned verification, and change impact.

## Outside the Oscillink scope

- real sensors, scanners, guards, interlocks, safety PLCs, robot controllers, drives, brakes,
  emergency-stop devices, and final elements;
- transport to a live controller, equipment credentials, controller addresses, ROS publishers,
  fieldbus writers, reverse control callbacks, and remote reset;
- selection or calculation of PLr, PL, SIL, PFH, category, architecture, diagnostic coverage,
  common-cause score, proof-test interval, or stopping distance/time;
- application risk assessment, electrical or mechanical integration, commissioning, validation,
  conformity assessment, certification, and operating authorization; and
- work permits, lockout/tagout authority, legal conclusions, and personnel authorization.

## Trust and authority boundaries

Production-AI records are untrusted observations. They cannot select policy, alter limits, change
source identities, provide reset authority, acknowledge the simulated request, or suppress evidence.
The governance plane controls reviewed configuration and evidence but cannot command physical or
simulated motion. The planned Oscillink output can request an action only; the external safety
controller and final element remain solely responsible for any physical response in a future target
system.

A controller acknowledgment, if represented in simulation, means only that a fixture reported
receipt. It does not prove that a controller is safety-rated, that a final element acted, or that a
machine stopped.

## Open target-system assumptions

Independence is not established merely by drawing separate boxes. Shared power, network, sensor,
time, compute, software supply chain, credentials, update channel, enclosure, communications, or
final element may defeat both production and supervisory paths. These common-cause assumptions,
along with PLr, SIL, total stopping time, diagnostic coverage, and application validation, remain
TBD for qualified assessment of the exact target system.
