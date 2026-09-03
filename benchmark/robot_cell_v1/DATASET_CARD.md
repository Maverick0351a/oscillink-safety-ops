---
pretty_name: Oscillink Synthetic Robot Cell Exact-Byte Benchmark v1
license: apache-2.0
language:
  - en
tags:
  - robotics
  - safety
  - synthetic
  - deterministic
size_categories:
  - n<1K
---

# Oscillink Synthetic Robot Cell Exact-Byte Benchmark v1

## Dataset summary

Project-authored synthetic cases and exact deterministic expected outputs for a closed-file
robot-cell safety-supervisor demonstrator. Inputs model production intent, independent observations,
source health, output uncertainty, authority probes, persistence, and staged recovery.

## Intended use

Offline software regression, exact-byte reproducibility, policy inspection, and safety-manager demo
fixtures. Verify the canonical manifest before use. No network, device, controller, or machine
interface is represented.

`SAFETY_MANAGER_DEMO.md` is the generated field guide. The dependency-free read-only monitor in
`demo/` is generated from all expected-result records and these metrics; it adds no hand-entered
score and exposes no command, reset, rearm, acknowledgment, or stop affordance.

## Limitations

This is synthetic maintainer evidence, not field or application validation. It does not select or
validate real limits, sensors, diagnostics, communications, controllers, final elements, stopping
performance, independence, cybersecurity, or residual risk. Request creation and simulated receipt
do not establish physical stopping. PLr, SIL, total stopping time, diagnostic coverage, application
validation, and unresolved common-cause assumptions remain TBD pending a qualified target-system
assessment.

## License and rights

Apache-2.0 for project-authored records and documentation. No private keys, customer data,
copyrighted standards text, or third-party equipment data are included. The canonical public Dataset
is `Maverick03511/safetyops-bench-v1`; its companion static monitor is
`Maverick03511/oscillink-safety-ops-demo`.
