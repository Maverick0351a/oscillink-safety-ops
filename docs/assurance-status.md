# Assurance status and limitations

Oscillink Safety Ops is being developed as an independent safety and risk-mitigation supervisor for
AI-controlled industrial equipment. This page separates implemented evidence from planned behavior
and from claims that require configuration-specific engineering and independent assessment.

## Current status

**Current runtime-supervisor status: planned, not implemented.**

The repository currently implements deterministic exact-byte evidence, provenance, source-change,
external-review, and offline plan/recorded-episode evaluation contracts. Those contracts produce
evidence findings only. They do not emit runtime intervention requests or participate in a machine
control loop.

## Planned public demonstrator

Later batches plan a deterministic, closed-file robot-cell replay that correlates untrusted machine
intent with independently modeled observations and immutable configuration. Planned outputs include
local simulated inhibit or protective-stop requests, latching, recovery evidence, and a static
safety-manager timeline. Until that code and its tests exist, these remain design intent rather than
implemented capability.

The planned public benchmark and demonstrations will use project-authored synthetic data and
simulation. Their results will not be field results, incident-prevention evidence, or validation of a
real machine's sensors, dynamics, communications, stopping time, final elements, or failure modes.

## No real machine control

No real machine control is implemented or authorized. The current package has no robot, vehicle,
machine, PLC, safety PLC, interlock, emergency-stop, drive, actuator, live ROS graph, or remote-reset
interface. Runtime work in later batches remains limited to simulation, replay, shadow/advisory
evaluation, and local closed-file requests. Established safety-rated controllers and final elements
remain outside Oscillink authority.

## Dedicated assurance status

- No Oscillink release is certified or safety-rated.
- No completed Performance Level (PL), Safety Integrity Level (SIL), diagnostic-coverage,
  common-cause, response-time, or stopping-time assessment exists.
- No conformity assessment, CE declaration, NRTL listing, approval to operate, work authorization,
  compliance conclusion, or legal opinion is claimed.
- No external practitioner, functional-safety assessor, legal, regulatory, engineering, OT-owner, or
  field validation has been completed for the planned supervisor.
- Local and independent Buildbox tests establish only the documented deterministic software behavior
  for the exact tested commits. Hosted CI has not evaluated the current local commit range.

Deployment authority would depend on the complete configured safety function: target equipment and
hazards, sensors, logic, communications, hardware, final elements, independence and common-cause
analysis, configuration, response and stopping times, applicable law and standards, validation,
operating organization, jurisdiction, and independent qualified assessment.

## Permitted interpretation

The approved public direction describes the product category and intended architecture. It does not
retroactively describe unimplemented runtime behavior. Current claims must remain tied to current
evidence; future capabilities must remain marked as planned until their release-bound tests and
artifacts exist.