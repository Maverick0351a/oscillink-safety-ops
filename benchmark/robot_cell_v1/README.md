# Robot cell v1 exact-byte benchmark

This frozen corpus contains project-authored synthetic closed-file cases for deterministic software
behavior. It contains no customer, facility, hardware, incident, or field data. A passing verifier
does not establish a physical stop, safe operation, PLr, SIL, stopping time, diagnostic coverage,
application validation, common-cause independence, certification, or compliance.

## Files and exactness

`cases.jsonl` and `expected-results.jsonl` use canonical UTF-8 JSON: sorted object keys, compact
separators, one object per line, and LF endings. The strict machine-readable schemas describe their
records. `metrics.json` is mechanically derived from cases and exact expected outputs. The canonical
manifest binds every other regular file in this directory by SHA-256 and positive byte count, plus
the frozen runtime baseline, exact benchmark/generator source bytes and their source-tree hash,
runtime format, configuration, public authority, and scenario identities. Repository HEAD may move;
the exact source hashes may not. The manifest cannot hash itself without a circular identity. No
private key is included.

## Verify locally

```bash
PYTHONPATH= uv run safety-ops benchmark verify --root benchmark/robot_cell_v1
PYTHONPATH= uv run python scripts/verify_benchmark.py benchmark/robot_cell_v1
```

Verification is local and performs no network access. Reported counts are correctness and coverage
counts only; no wall-clock latency is collected or presented as safety evidence.
