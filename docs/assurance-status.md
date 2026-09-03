# Assurance status and limitations

Oscillink Safety Ops is being developed as an independent safety and risk-mitigation supervisor for
AI-controlled industrial equipment. This page separates implemented simulation/replay behavior from
claims that require target-specific engineering and independent assessment.

## Current implemented status

The repository implements deterministic exact-byte evidence and review contracts plus a closed-file
runtime supervisor. The runtime correlates untrusted command intent, independently modeled physical
and source-health observations, and immutable signed configuration. It fails closed, creates local
simulated one-way protective-stop or inhibit request records, preserves a persistent latch, and keeps
acknowledgment, reset, rearm, recovery, and fresh start separate.

The 36-case benchmark and static monitor use project-authored synthetic robot-cell records. The TLA+
result is finite abstract model checking. Property, fuzz, local, Buildbox, and CI results establish
specified software behavior only.

## No real machine control

No real machine control is implemented or authorized. There is no robot, vehicle, machine, PLC,
safety PLC, interlock, emergency-stop, drive, actuator, live ROS graph, controller address or
credential, network output, remote reset, or reverse callback. A local simulated request is not
evidence that physical equipment stopped or that a protective function is effective.

## Unestablished assurance

- No release is certified or safety-rated.
- No completed PL, SIL, diagnostic-coverage, common-cause, response-time, or stopping-time assessment
  exists.
- No conformity assessment, approval to operate, work authorization, compliance conclusion, or legal
  opinion is claimed.
- No external practitioner, functional-safety assessor, legal, regulatory, engineering, OT-owner, or
  field validation has been completed.
- Hosted CI has not run the unpushed Batch 7 candidate.

Deployment authority depends on the complete configured safety function: target hazards and
equipment, sensors, communications, logic, final elements, independence/common-cause analysis,
configuration, timing, applicable law and standards, validation, operating organization,
jurisdiction, and qualified independent assessment.
