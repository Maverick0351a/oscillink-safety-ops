# Security Policy

Oscillink Safety Ops is being developed as an independent safety and risk-mitigation supervisor for
AI-controlled industrial equipment. The current package is an evidence and offline-evaluation plane;
the planned runtime supervisor is not implemented. It does not currently provide an operational
service and must not be connected to production equipment or safety systems.

## Reporting

Report security concerns through the repository's private GitHub collaboration channel. Do not use
a public issue. The repository must not become public until GitHub private vulnerability reporting
or another tested confidential route is enabled and documented.

Do not place credentials, customer procedures, employee information, facility data, equipment
secrets, private prompts, licensed standards, or sensitive incident evidence in an issue or pull
request. Provide the minimum synthetic reproduction needed to explain the boundary failure.

## High-priority boundaries

Reports are especially important if they show:

- unapproved extraction becoming approved evidence;
- source, revision, asset, jurisdiction, site, role, or applicability confusion;
- stale/superseded evidence presented as current;
- hidden conflict resolution or fabricated source citations;
- OCR/model content changing permissions or policy;
- customer SOP, manual, permit, employee, facility, or incident-data leakage;
- arbitrary file, shell, network, browser, process, or external-service access;
- work-permit, LOTO, compliance, certification, or legal conclusions generated automatically;
- robot, PLC, interlock, emergency-stop, machine, or actuator access; or
- evaluation labels or expected answers exposed to an evaluated system.

## Deployment boundary

Do not expose a service to an untrusted network. Do not ingest real customer safety documents
until authentication, workspace isolation, retention, deletion, export, audit, and incident
response are reviewed and tested.

### No real machine control

No real machine control is implemented or authorized. Simulation, replay, and shadow-mode work must
use closed local inputs and outputs with no controller address, controller credential, live ROS graph,
PLC write, remote reset, or reverse command path. A simulated intervention request is not evidence
that real equipment stopped or that a protective function is effective.

Safety Ops is not a safety-rated system, penetration-test report, regulatory approval, warranty, or
substitute for qualified safety engineering. Certification and deployment authority depend on the
exact configured safety function, hardware, integration, validation, jurisdiction, and independent
assessment.

## Supported versions

No version is currently supported for production or operational deployment. Security fixes apply to
the private development line until a release and support policy are explicitly approved.
