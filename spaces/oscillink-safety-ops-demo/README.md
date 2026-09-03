---
title: Oscillink Safety Ops Synthetic Monitor
emoji: 🛡️
colorFrom: indigo
colorTo: cyan
sdk: static
app_file: index.html
pinned: false
license: apache-2.0
short_description: Read-only inspection of 36 synthetic supervisor scenarios
---

# Oscillink Safety Ops Synthetic Monitor

**SYNTHETIC EVIDENCE — SOFTWARE BEHAVIOR ONLY**

This static Space is generated from `demo/` and mechanically binds all 36 expected results and derived
metrics from `benchmark/robot_cell_v1/`.

The interface is Monitor-primary and Inspect-secondary. It permits scenario selection and evidence
inspection only. It has no command, reset, rearm, acknowledgment, stop, form-submit, external-resource,
network-client, controller, robot, machine, PLC, interlock, or actuator surface.

## Evidence boundary

Displayed protective-stop and inhibit values are deterministic **request records**. A represented
acknowledgment is synthetic fixture-receipt evidence only. **No physical stop established.**

This benchmark and demo do not establish safe operation, field effectiveness, compliance,
certification, or operational authority. PLr, SIL, total stopping time, diagnostic coverage (DC),
application validation, and common-cause target values remain TBD pending qualified assessment of an
exact machine, architecture, installation, and operating environment.

## Reproduction and verification

Copy the exact generated `demo/index.html` and `demo/assets/` into the Space root, retain this
metadata, and run locally:

```bash
PYTHONPATH= uv run safety-ops benchmark verify --root benchmark/robot_cell_v1
PYTHONPATH= uv run python scripts/verify_demo.py demo
PYTHONPATH= uv run python scripts/verify.py
```

Hosted execution and cross-browser inspection are software checks only and do not replace qualified
safety review or application-specific validation.
