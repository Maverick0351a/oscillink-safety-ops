# Security Policy

Oscillink Safety Ops is an independent safety and risk-mitigation supervisor for AI-controlled
industrial equipment. The current package implements deterministic closed-file simulation/replay,
latched recovery state, and local simulated one-way protective-stop and inhibit request records. It
has no machine, controller, PLC, robot, actuator, live-network, remote-reset, or reverse command path.

## Reporting

Do not report a vulnerability in a public issue. While the repository remains private, use its
confidential maintainer collaboration route. Publication remains blocked until GitHub private
vulnerability reporting or another tested confidential route is enabled and read back. Do not attach
credentials, customer or employee data, facility details, production logs, private prompts, hidden
evaluation material, incident evidence, or licensed standards text. Prefer a minimal synthetic
reproduction.

## High-priority boundaries

Reports are especially important if they show:

- production-originated configuration, acknowledgment, suppression, reset, or recovery authority;
- a simulated request escaping the closed local output boundary;
- stale, missing, contradictory, malformed, or unauthenticated input failing open;
- configuration identity, signature, revision, or persistence confusion;
- arbitrary file, shell, network, process, or service access;
- source, applicability, review, correction, or supersession confusion;
- fabricated citations or silent conflict resolution;
- confidential-data, credential, private-prompt, or hidden-label exposure; or
- automatic compliance, certification, safe-operation, permit, or work-authorization conclusions.

## Assurance and deployment boundary

Simulation, replay, synthetic benchmark results, TLA+ model checking, fuzz/property tests, and CI are
software evidence only. They do not establish field performance, stopping time, hardware behavior,
application validation, certification, PL/SIL achievement, or safe operation. Connecting this alpha
to real equipment or a production safety function is unsupported and unauthorized.

## Supported versions

No version is currently supported for production or operational deployment. Security fixes apply to
the development line until a release and support policy are separately approved.
