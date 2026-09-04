# Abstract supervisor model

This directory contains a finite TLA+ model of the simulated Oscillink Safety Ops supervisor state machine. It is maintainer-run synthetic software evidence, not a refinement proof, hardware validation, field validation, functional-safety assessment, or certification result.

## Files

- `Supervisor.tla` defines the abstract transition system and invariants.
- `Supervisor.cfg` fixes the finite fault-event set and invariant list.
- `formal-result.json` records one exhaustive TLC run and binds the exact model, configuration, and pinned TLC tool identity.

The model checks these abstract properties:

1. production-originated activity cannot gain administrative or recovery authority;
2. a latch can clear only after reset, rearm, recovery confirmation, and fresh start;
3. acknowledgment is not reset;
4. reset is not fresh start;
5. reboot preserves an existing latch;
6. recovery transitions never command motion; and
7. configuration change, output uncertainty, and source faults enter the latched intervention state; and
8. abstract attribution identity reuse, response-before-command, and late-response faults fail closed.

The model intentionally disables deadlock checking because terminal or stuttering states are represented through `[Next]_vars`. It uses one TLC worker, a fixed fingerprint polynomial index, bounded heap and set size, and a bounded process timeout.

## Reproduce

Supply exact local paths to Java and the pinned `tla2tools.jar`:

```bash
PYTHONPATH= uv run python scripts/verify_tla.py \
  --check \
  --java /path/to/java \
  --jar /path/to/tla2tools-1.7.4.jar
```

The runner rejects any JAR whose SHA-256 is not:

```text
936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88
```

The recorded run used TLC 2.19, revision `5a47802`, from TLA+ tools v1.7.4. TLC generated 422 states, found 43 distinct states, reached search depth 10, left zero states queued, and reported no invariant violation.

`--write` is a maintainer evidence-generation operation. Review model/configuration changes and rerun TLC before replacing the committed result.

## Limits

The model is an abstraction and is not mechanically refined against the Python implementation. It does not establish response time, stopping performance, diagnostic coverage, common-cause independence, PLr/SIL, application validation, hardware behavior, or conformity. Those remain target-system work for qualified assessment.
