# Robot cell v1 synthetic replay corpus

This corpus is synthetic maintainer evidence for deterministic software behavior only. It is not
field validation, application validation, certification, stopping proof, or a PLr/SIL assessment.

## Strict files

- `configuration.json`: one compact UTF-8 JSON object plus LF. Its Ed25519 signature covers the
  canonical semantic configuration excluding `signature`.
- `authority.json`: public Ed25519 verification bytes, exact approved configuration SHA-256, scope,
  revision floor, and independent constraint ceilings. It contains no private key or secret.
- `*.jsonl`: compact UTF-8 JSON objects, exactly one observation per LF-terminated line. CRLF, blank
  lines, duplicate JSON names, non-finite values, embedded `input_sha256`, unknown fields, and a
  missing final LF are invalid. Each line's exact bytes, including LF, determine its input digest.
- `expected/*.report.json`: frozen canonical UTF-8 JSON (sorted keys, compact separators, one final
  LF). Every report binds the authority, configuration, complete JSONL bytes, individual line bytes,
  scenario format, runtime code-format descriptor, decisions, requests, and final state.
- `MANIFEST.json`: exact SHA-256 and byte count for every frozen source and expected output.

Observation batches contain exactly one record for every sorted required source. A batch's explicit
evaluation time is the maximum `received_at`; the runtime reads no clock. `clean.jsonl` is nominal.
`zone-entry.jsonl`, `stale-source.jsonl`, and `contradictory-source.jsonl` are fail-closed fault cases.

## Exact documented command

```bash
safety-ops runtime replay \
  --configuration scenarios/robot_cell_v1/configuration.json \
  --input scenarios/robot_cell_v1/zone-entry.jsonl \
  --output runtime-report.json
```

The command only publishes a root-confined local closed-file report. It has no network, device, ROS,
PLC, controller, remote-reset, or reverse-control interface. Remove a prior different output before
rerunning; an existing byte-identical output is accepted, while a collision fails closed.
