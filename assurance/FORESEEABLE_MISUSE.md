# Foreseeable misuse

This document identifies misuse of `SCOPE-ROBOT-CELL-001`; it does not authorize deployment or
assign blame to an operator. Each misuse must remain prevented by product boundaries, review, tests,
and clear documentation.

| Misuse | Related hazard | Required disposition |
|---|---|---|
| Connect the simulated output to a real PLC, robot, drive, interlock, emergency-stop circuit, or actuator. | `HAZ-007` | Prohibited. No live transport, address, credential, or machine writer belongs in the current scope. |
| Treat a local request or fixture acknowledgment as proof that hazardous motion stopped. | `HAZ-007` | Prohibited. Stopping requires independent target-system feedback and validation outside this scope. |
| Use production-AI occupancy, confidence, or self-report as the sole observation. | `HAZ-001`, `HAZ-005`, `HAZ-011` | Prohibited. Production inputs remain untrusted and cannot authorize continued motion. |
| Interpret absence of a request as an `allow`, `safe`, or `approved_to_operate` verdict. | `HAZ-001`–`HAZ-012` | Prohibited. The planned API makes no positive safety conclusion. |
| Configure PLr, SIL, stopping time, or diagnostic coverage from public summaries or simulated timing. | `HAZ-004`, `HAZ-007`, `HAZ-012` | Prohibited. Values remain TBD for qualified target-system assessment. |
| Clear a latch by restarting the process, deleting state, restoring power, or replaying an acknowledgment. | `HAZ-009`, `HAZ-010` | Reject as a fault and preserve the unresolved state. |
| Let production AI reset, rearm, acknowledge, suppress evidence, raise limits, change time, or select policy. | `HAZ-010`, `HAZ-011` | Reject at the contract and authority boundary. |
| Automatically restart motion after reset, communications restoration, sensor recovery, or zone clearance. | `HAZ-002`, `HAZ-009`, `HAZ-010` | Prohibited. Reset only permits a separately authorized later start; it never commands motion. |
| Continue nominal evaluation when sensing is missing, stale, contradictory, reordered, or malformed. | `HAZ-005`, `HAZ-006` | Produce a degraded/intervention state; never silently normalize uncertainty. |
| Assume process, network, power, sensor, clock, or software separation without common-cause evidence. | `HAZ-012` | Keep assumptions open and block target-system claims. |
| Present synthetic scenarios, test counts, or traceability as field validation or certification. | `HAZ-001`–`HAZ-012` | Prohibited claim; label evidence as synthetic and configuration-specific. |
| Use these artifacts to issue a permit, authorize lockout/tagout, certify personnel, or resolve legal applicability. | `HAZ-002`, `HAZ-010` | Outside scope and prohibited. |

Maintenance, setup, cleaning, jam clearing, fault recovery, and bypass pressure are foreseeable
contexts for these misuses. A target system must assess them with qualified personnel and exact
site/equipment evidence; the simulated lifecycle set does not resolve them.
