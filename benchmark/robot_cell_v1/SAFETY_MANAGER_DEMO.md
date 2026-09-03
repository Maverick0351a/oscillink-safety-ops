# Safety manager benchmark field guide

**SYNTHETIC EVIDENCE — SOFTWARE BEHAVIOR ONLY**

This closed-file robot-cell corpus helps a safety manager inspect deterministic supervisor evidence,
not operate equipment. It has no network, controller, machine, reset, rearm, acknowledgment, stop,
or command interface. Every request and receipt is represented synthetic data; physical stop remains `not_established`.

## Verified corpus at a glance

- 36/36 exact byte matches across 3 runs per case
- 12/12 required fault families represented
- 108 deterministic executions; no wall-clock latency claim
- actions: `inhibit_request` 12, `none` 4, `protective_stop_request` 20

## Inspection sequence

1. Confirm exact `case_id`, title, scenario identity, case hash, configuration hash, authority hash,
   runtime-format hash, and input hashes.
2. Compare production intent with independent occupancy, measured motion, and source health.
3. Read the deterministic policy state and action, then preserve first-out separately from the sorted
   set of all contributing reasons.
4. Keep request state, fixture acknowledgment, and physical stopping distinct. An acknowledgment is
   receipt evidence only. No physical stop is established.
5. Inspect latch, recovery stage, fresh-start requirement, and reset sequence. Displayed recovery
   events are records from a represented independent safety authority, never UI commands.

## High-value cases

- `case:simultaneous-priority-faults`: first-out `configuration_changed_mid_run` with sorted reasons
  `command_actual_mismatch, configuration_changed_mid_run, excessive_acceleration, excessive_speed, human_present_with_measured_motion, orphan_motion, output_uncertain, unexpected_motion`.
- `case:false-acknowledgment`: a mismatched receipt does not resolve the output path or prove stop.
- `case:restart-latch-preservation`: process restart preserves the intervention latch.
- `case:production-reset-attempt`: production-AI reset authority is rejected.
- `case:valid-staged-recovery`: ends at `initializing`, latched
  `false`, fresh-start required
  `false`, reset sequence `1`.

## What this evidence cannot establish

This synthetic benchmark does not establish a physical stop, safe operation, field effectiveness,
certification, compliance, or target-system integrity. PLr, SIL, total stopping time, diagnostic
coverage, application validation, and common-cause target values remain TBD pending qualified
assessment of an exact machine and installation.
