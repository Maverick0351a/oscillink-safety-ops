# Synthetic local demonstration

This demonstration uses only project-authored synthetic inputs. It exercises exact-byte validation, offline plan auditing, and recorded-episode evaluation without a network connection or equipment integration.

It provides deterministic engineering evidence. It does not establish legal applicability, compliance, certification, safe operation, practitioner validation, or production readiness.

## Prerequisites

- Python 3.11
- [`uv`](https://docs.astral.sh/uv/)
- a local clone of this repository

## 1. Install the locked environment

```bash
uv sync --locked --dev
```

## 2. Verify the repository

```bash
PYTHONPATH= uv run python scripts/verify.py
```

The verifier checks text hygiene, generated-schema drift, the OSHA catalog, synthetic fixtures, Ruff, formatting, strict mypy, source and wheel builds, and the full test suite.

## 3. Validate the synthetic source envelope

```bash
PYTHONPATH= uv run safety-ops envelope validate \
  --envelope tests/fixtures/synthetic_press/envelope.json \
  --root tests/fixtures/synthetic_press
```

The command verifies that the declared payload remains inside the supplied root and matches its exact declared bytes and SHA-256.

## 4. Audit a synthetic proposed plan

```bash
PYTHONPATH= uv run safety-ops audit \
  --packet tests/fixtures/synthetic_press/packet.json \
  --plan tests/fixtures/synthetic_press/plan.json \
  --manifest tests/fixtures/synthetic_press/manifest.json \
  --envelope tests/fixtures/synthetic_press/envelope.json \
  --root tests/fixtures/synthetic_press
```

The JSON report binds the packet, plan, policy, platform, adapter configuration, source revision, and payload hash. Findings retain exact citations and closed evidence states.

## 5. Evaluate a synthetic recorded episode

```bash
PYTHONPATH= uv run safety-ops episode-evaluate \
  --packet tests/fixtures/synthetic_press/safety-evidence-packet-v1.json \
  --episode tests/fixtures/synthetic_press/episode.json \
  --envelope tests/fixtures/synthetic_press/episode-envelope.json \
  --root tests/fixtures/synthetic_press
```

The committed fixture yields a cited mix of matched, missing, unreadable, conflicting, stale, asset-mismatch, unsupported-interpretation, and review-gate findings. Its top-level states remain:

```text
evaluation_state       evidence_findings_only
compliance_state       no_conclusion
operational_authority  none
```

## 6. Normalize a synthetic operational export

```bash
PYTHONPATH= uv run safety-ops operational normalize \
  --input tests/fixtures/operational_evidence/synthetic-operational.jsonl \
  --batch-id batch:synthetic-operational-001 \
  --source-revision export:synthetic-operational-001 \
  --adapter-config-sha256 sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa \
  --store-root runtime/operational-evidence
```

The command stores immutable raw bytes under the caller-controlled root and emits normalized observational evidence. It does not acknowledge, reset, command, or write to a source system.

## What to inspect

- Source and payload hashes match the committed manifests.
- Asset, serial, task, run, and episode identities remain explicit.
- Missing, stale, conflicting, ambiguous, and unreadable evidence remains visible.
- Findings cite exact source and constraint identities.
- Review authority is separate from extraction and evaluation.
- Every evaluation keeps compliance and operational authority closed.

## Cleanup

The operational command writes only beneath the supplied `runtime/operational-evidence` root, which Git ignores. Remove that directory when the local demonstration is complete.
