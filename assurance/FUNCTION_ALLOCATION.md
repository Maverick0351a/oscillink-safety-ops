# Function allocation

## Purpose

The allocation makes the complete sensor-to-final-element path visible for every planned requirement
without claiming that Oscillink implements or validates the complete safety function. Current Batch
2 output is documentation only. A later output, if implemented, remains a local one-way simulated
request.

| Allocation ID | Domain | Planned responsibility | Authority and unresolved boundary |
|---|---|---|---|
| `ALLOC-OBS-001` | Independent observation | Supply represented occupancy, robot motion/state, source health, timebase health, and configuration/calibration identity separately from production-AI intent. | Synthetic sources only in this scope. Real sensor selection, independence, diagnostics, coverage, installation, and validation are TBD. |
| `ALLOC-LOGIC-001` | Oscillink deterministic logic | Validate, align, correlate, evaluate immutable rules, manage explicit degraded states, latch intervention state, and record causal evidence. | Planned and not implemented in Batch 2. It never commands motion or emits a positive safety verdict. |
| `ALLOC-OUTPUT-001` | Oscillink local output boundary | Construct a decision/configuration-bound one-way local simulated inhibit or protective-stop request and expose write/acknowledgment uncertainty. | No network, ROS, PLC, fieldbus, machine credential, reverse callback, remote reset, or physical I/O. Request creation does not prove stopping. |
| `ALLOC-EXTCTRL-001` | External safety domain | Receive and evaluate a request and provide independently modeled status in the simulation fixture. In a future target this role belongs to an established configured safety controller. | Not implemented, selected, configured, qualified, or validated by Oscillink. A simulated acknowledgment means receipt only. |
| `ALLOC-FINAL-001` | External final element | In a future target, remove or control hazardous energy through application-selected drives, brakes, contactors, valves, or other final elements and provide appropriate feedback. | Represented only to close the allocation chain. No final element exists in the demonstrator and no stopping performance is claimed. |

## Allocation by requirement

Every requirement `SR-001` through `SR-012` traverses all five allocations because the hazard response
cannot be evaluated as a complete function by considering deterministic logic alone. The trace table
therefore includes:

`ALLOC-OBS-001;ALLOC-LOGIC-001;ALLOC-OUTPUT-001;ALLOC-EXTCTRL-001;ALLOC-FINAL-001`

for every row. This denotes analytical coverage of interfaces and assumptions, not implementation
ownership or certification of external equipment.

## Interface invariants

1. Production AI is an untrusted observed source and is never an allocation for policy,
   configuration, acknowledgment, reset, rearm, evidence retention, or final action.
2. Observation failures remain data-quality and health states; confidence cannot substitute for
   required evidence.
3. `ALLOC-OUTPUT-001` transmits no success claim. Missing acknowledgment and output fault remain
   visible and latched.
4. `ALLOC-EXTCTRL-001` and `ALLOC-FINAL-001` retain physical authority. Oscillink cannot bypass,
   reset, reconfigure, or report their success.
5. Restoring any allocation after a fault does not automatically restart motion.

## Open allocation decisions

Target sensor technology, logic architecture, communication protocol, controller, drive/brake/final
element, feedback, proof-test interval, fault exclusions, separation, and common-cause measures are
unselected. PLr, SIL, total stopping time, diagnostic coverage, application validation, and
unresolved common-cause assumptions remain TBD for qualified target-system assessment.
